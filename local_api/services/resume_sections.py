"""Local Sentence-BERT + seeded K-means. Raw extraction is never rewritten."""
from collections import Counter
from dataclasses import dataclass
import json
import hashlib
import logging
import re
import os
from pathlib import Path
import threading

import numpy as np

_default_hf_home = Path(__file__).resolve().parents[2] / '.venv/model-cache'
if _default_hf_home.exists() and not os.environ.get('HF_HOME'):
    os.environ['HF_HOME'] = str(_default_hf_home)

from local_api.schemas.sections import SectionRequest, SectionResponse, ResumeSection, SectionBlock, ReadableGroup, SectionHighlight
from local_api.utils.file_validation import ExtractionError
from local_api.services.section_highlights import highlight_kind
from local_api.services.readable_resume import readable_groups
from local_api.services.resume_structure import heading_aliases, heading_boundary, entry_groups, RECORD_FIELDS, normalized_heading, employment_start, word_safe_cut

MODEL_CONFIG = json.loads((Path(__file__).parents[1] / 'data/section_model.json').read_text())
MODEL_ID = MODEL_CONFIG['model_id']
MODEL_REVISION = MODEL_CONFIG['revision']
ANCHORS = json.loads((Path(__file__).parents[1] / 'data/section_anchors.json').read_text())
ALIASES = heading_aliases(ANCHORS)
logger = logging.getLogger(__name__)
_load_lock = threading.Lock()
_engine = None


def build_sections(grouped, elements):
    from local_api.services.source_rows import refine_rows
    grouped = refine_rows(grouped, elements)
    sections = [ResumeSection(category=key, label=ANCHORS[key]['label'], blocks=blocks, entries=entry_groups(blocks, key, elements)) for key, blocks in grouped.items()]
    for section in sections:
        from local_api.services.record_relationships import annotate_relationships
        annotate_relationships(section)
        parts, previous, cursor = [], None, 0
        for block in section.blocks:
            separator = '' if previous is None or (previous.source_element_index == block.source_element_index and previous.end == block.start) else '\n'
            cursor += len(separator)
            kind=highlight_kind(section.category,block,elements[block.source_element_index])
            if kind:
                start=cursor+len(block.text)-len(block.text.lstrip())
                end=cursor+len(block.text.rstrip())
                if end>start:section.highlights.append(SectionHighlight(start=start,end=end,kind=kind))
            parts.append(separator + block.text)
            cursor += len(block.text)
            previous = block
        section.text = ''.join(parts)
        section.source_heading = next((block.text.strip().rstrip(':') for block in section.blocks
                                       if block.assignment in {'section_heading', 'structural_heading'}), None)
        section.readable_blocks = [ReadableGroup.model_validate(group) for group in readable_groups(section, elements)]
    return sections


@dataclass
class Unit:
    index: int
    start: int
    end: int
    text: str
    lane: str
    heading_style: bool = False
    margin_footer: bool = False


class SemanticClusters:
    """K-means learns centroids; labeled examples give clusters usable names."""
    def __init__(self, encoder, field):
        from sklearn.cluster import KMeans
        self.labels = list(ANCHORS)
        self.examples = [text for key in self.labels for text in ANCHORS[key][field]]
        owners = [key for key in self.labels for _ in ANCHORS[key][field]]
        self.vectors = encoder.encode(self.examples, normalize_embeddings=True, show_progress_bar=False)
        initial = np.stack([self.vectors[np.array(owners) == key].mean(axis=0) for key in self.labels])
        self.model = KMeans(n_clusters=len(self.labels), init=initial, n_init=1, random_state=42)
        self.model.fit(self.vectors)
        self.cluster_labels = {}
        for cluster in range(len(self.labels)):
            votes = Counter(owner for owner, assigned in zip(owners, self.model.labels_) if assigned == cluster)
            self.cluster_labels[cluster] = votes.most_common(1)[0][0] if votes else None
        self.purity = float(np.mean([self.cluster_labels[int(cluster)] == owner for cluster, owner in zip(self.model.labels_, owners)]))
        if set(self.cluster_labels.values()) != set(self.labels):
            raise ValueError('Anchor clusters do not provide distinct section labels')
        self.owners = owners

    def score(self, vectors, *, headings=False):
        centers = self.model.cluster_centers_
        norms = np.linalg.norm(centers, axis=1, keepdims=True)
        similarities = vectors @ (centers / np.maximum(norms, 1e-9)).T
        predicted = self.model.predict(vectors)
        results = []
        for i, cluster in enumerate(predicted):
            label = self.cluster_labels[int(cluster)]
            # Short heading synonyms are compared with heading anchor embeddings;
            # category selection still comes from the fitted K-means cluster.
            if headings:
                anchor_scores = vectors[i] @ self.vectors.T
                own = [float(value) for value, owner in zip(anchor_scores, self.owners) if owner == label]
                other = [float(value) for value, owner in zip(anchor_scores, self.owners) if owner != label]
                similarity, competing = max(own, default=-1), max(other, default=-1)
            else:
                similarity = float(similarities[i, cluster])
                competing = max((float(value) for c, value in enumerate(similarities[i]) if self.cluster_labels[c] != label), default=-1)
            results.append((label, int(cluster), similarity, similarity - competing))
        return results


class SectionEngine:
    def __init__(self, *, local_files_only=True):
        from sentence_transformers import SentenceTransformer
        self.encoder = SentenceTransformer(MODEL_ID, revision=MODEL_REVISION, device='cpu',
                                           local_files_only=local_files_only, trust_remote_code=False)
        if self.encoder[0].auto_model.config.model_type != 'bert':
            raise RuntimeError('Expected the pinned BERT encoder architecture')
        self.headings = SemanticClusters(self.encoder, 'headings')
        self.content = SemanticClusters(self.encoder, 'examples')
        self.lock = threading.Lock()

    def units(self, elements):
        units = []
        lanes, multicolumn = layout_lanes(elements)
        for index, element in enumerate(elements):
            offset = 0
            for line in element.text.splitlines(keepends=True) or ['']:
                encoded = self.encoder.tokenizer(line, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
                offsets = encoded['offset_mapping']
                line_category, inline_cut = heading_boundary(line, ALIASES)
                line_hints = element.metadata.get('pdf_source_lines', [])
                hint_cuts = [max(0, min(len(line), hint[key] - offset)) for hint in line_hints for key in ('start', 'end') if isinstance(hint.get(key), int) and offset <= hint[key] <= offset + len(line)]
                recovery_cuts = [cut-offset for cut in element.metadata.get('recovery_cuts', []) if isinstance(cut,int) and offset <= cut <= offset+len(line)]
                # A known heading is one unit even when PDF hints split its words.
                if line_category and inline_cut is None:
                    hint_cuts = []
                    recovery_cuts = []
                mechanical_cuts = hint_cuts + [offsets[i][0] for i in range(200, len(offsets), 200)]
                project_cuts = [cut for match in re.finditer(r'(?<!\w)project\s*#?\s*\d+\s*:\s*\S',line,re.I) for cut in (match.start(),line.index(':',match.start())+1)]
                cuts = sorted(set(project_cuts + recovery_cuts + [word_safe_cut(line, cut) for cut in mechanical_cuts] + [0] + ([inline_cut] if inline_cut else []) + [len(line)]))
                if not line:
                    cuts = [0, 0]
                for start, end in zip(cuts, cuts[1:]):
                    matching = [hint for hint in line_hints if hint.get('start', -1) <= offset + start and hint.get('end', -1) >= offset + end]
                    hint = min(matching, key=lambda item: item['end']-item['start']) if matching else (min(line_hints, key=lambda item: abs(item['start'] - (offset + start))) if line_hints else None)
                    lane = lanes[index]
                    if hint and len(hint.get('bbox', [])) == 4:
                        lane = 'left' if hint['bbox'][0] < .32 else 'right'
                        if hint['bbox'][2] - hint['bbox'][0] > .65:
                            lane = 'wide'
                    units.append(Unit(index, offset + start, offset + end, line[start:end], lane, bool(hint and hint.get('heading_style')), bool(hint and len(hint.get('bbox', [])) == 4 and hint['bbox'][1] > .85)))
                offset += len(line)
        # PDF line hints can isolate spaces between adjacent physical lines.
        # Preserve them on a neighboring span instead of classifying whitespace.
        coalesced = []
        for unit in units:
            previous = coalesced[-1] if coalesced else None
            if previous and previous.index == unit.index and previous.end == unit.start and (not previous.text.strip() or not unit.text.strip()):
                if not previous.text.strip():
                    unit.start = previous.start
                    unit.text = previous.text + unit.text
                    coalesced[-1] = unit
                else:
                    previous.end = unit.end
                    previous.text += unit.text
            else:
                coalesced.append(unit)
        units = coalesced
        if len(units) > 2000:
            raise ExtractionError(422, 'Section detection supports up to 2,000 text units')
        return units, multicolumn

    def detect(self, request):
        with self.lock:
            return self._detect(request)

    def _detect(self, request):
        units, multicolumn = self.units(request.elements)
        texts = [unit.text.strip() or ' ' for unit in units]
        vectors = self.encoder.encode(texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False)
        headers = self.headings.score(vectors, headings=True)
        contents = self.content.score(vectors)
        # Generic phrase boundaries only; section names are never matched by regex.
        # This catches combined headings through their BERT/K-means labels.
        compounds = {}
        compound_parts = []
        part_owners = []
        for i, text in enumerate(texts):
            if len(text.split()) <= 12:
                parts = [part.strip() for part in re.split(r'\s+(?:and|&)\s+|[/|;]', text, flags=re.IGNORECASE) if part.strip()]
                if len(parts) > 1:
                    compound_parts.extend(parts)
                    part_owners.extend([i] * len(parts))
        if compound_parts:
            part_vectors = self.encoder.encode(compound_parts, normalize_embeddings=True, batch_size=16, show_progress_bar=False)
            for owner, (label, _, score, margin) in zip(part_owners, self.headings.score(part_vectors, headings=True)):
                if score >= .85 and margin >= .12:
                    compounds.setdefault(owner, set()).add(label)
        page_heading_lanes = {}
        for unit in units:
            if heading_boundary(unit.text, ALIASES)[0]:
                page_heading_lanes.setdefault(request.elements[unit.index].page_number, set()).add(unit.lane)
        grouped, review, contexts = {}, [], {}
        element_contexts = {}
        first_heading = next((i for i, (_, _, score, margin) in enumerate(headers)
                              if request.elements[units[i].index].type not in {'Footer', 'PageBreak'} and
                              (heading_boundary(units[i].text, ALIASES)[0] is not None or
                               (len(units[i].text.split()) <= 12 and score >= .72 and margin >= .09))), len(units))
        for position, (unit, heading, content) in enumerate(zip(units, headers, contents)):
            element = request.elements[unit.index]
            hlabel, hcluster, hscore, hmargin = heading
            label, cluster, similarity, margin = content
            candidate = label
            context_source = None
            context = element_contexts.get(unit.index) or contexts.get(unit.lane)
            if context is None and unit.lane == 'wide' and contexts:
                owners = {item[0] for item in contexts.values()}
                if len(owners) == 1:
                    context = next(iter(contexts.values()))
            short = len(unit.text.split()) <= 12
            structural_label, _ = heading_boundary(unit.text, ALIASES)
            # 'Languages' in a technology list means programming languages.
            if structural_label == 'languages' and re.search(
                    r'(?<!\w)(?:C\#|C\+\+|Java|Python|SQL|JavaScript|TypeScript|Linq)(?!\w)',
                    element.text, re.I):
                structural_label = 'skills'

            if unit.heading_style and re.search(r'\b(?:domain|technical) expertise$', normalized_heading(unit.text)):
                structural_label = 'skills'
            following = next((contents[j] for j in range(position+1,min(len(contents),position+6)) if units[j].text.strip()), None)
            if structural_label == 'languages' and context and context[0] == 'skills' and following and following[0] == 'skills' and following[2] >= .4:
                structural_label = 'skills'
            prefix = normalized_heading(unit.text.split(':', 1)[0])
            record_field = ':' in unit.text and (prefix in RECORD_FIELDS or (
                context and context[0] in {'experience', 'projects'} and prefix in {'objective', 'summary', 'skills', 'technologies used', 'tools and technology', 'tools and technologies', 'programming languages'}))
            if record_field:structural_label = None
            alternatives = sorted(compounds.get(position, set()))
            compound = len(alternatives) > 1 and structural_label is None
            from local_api.services.record_subfields import paired_employment_header
            next_unit = units[position+1] if position+1<len(units) else None
            paired_boundary = bool(next_unit and context and context[0] in {'experience','projects'} and paired_employment_header(unit.text,next_unit.text))
            employer_boundary = employment_start(unit.text) or paired_boundary
            # A labelled professional engagement may follow a skills sidebar
            # without a repeated Experience heading. Require role, project and
            # client evidence; do not treat a client as an employer.
            engagement_boundary = bool(context and context[0] == 'skills' and 'experience' in grouped and
                re.match(r'^\s*Role\s*:\s*\S', unit.text, re.I) and
                re.search(r'\bProject\s*:', element.text, re.I) and
                re.search(r'\bClient\s*:', element.text, re.I))
            page_artifact = element.type == 'PageBreak' or (element.type == 'Footer' and bool(re.fullmatch(r'\s*(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?\s*', unit.text, flags=re.I)))
            is_heading = (structural_label is not None or (short and hscore >= .72 and hmargin >= .09 and (not context or not context[2] or unit.heading_style))) and not compound and not record_field and not page_artifact and not employer_boundary
            assignment, reason = 'semantic', 'BERT embedding assigned to a labeled K-means centroid'
            if compound:
                contexts.pop(unit.lane, None)
                if unit.lane == 'wide':
                    contexts.clear()
                candidate = None
                assignment, reason = 'needs_review', 'Combined heading contains multiple BERT-recognized section families'
            elif page_artifact:
                assignment, reason = 'needs_review', 'Layout footer or page separator retained outside semantic sections'
            elif unit.margin_footer and re.match(r'\s*(?:place|date)\s*:', unit.text, re.I):
                label = 'personal_information'
                assignment, reason = 'personal_detail', 'Location/date signature in the document bottom margin'
            elif employer_boundary or engagement_boundary:
                label = 'experience'
                context_source = unit.index
                target_lanes = set(item.lane for item in units) if len(page_heading_lanes.get(element.page_number, set()) - {'wide', 'unknown'}) <= 1 else {unit.lane}
                for lane in target_lanes:
                    contexts[lane] = (label, unit.index, True)
                assignment, reason = 'employment_boundary', ('Explicit role, project and client resume employment context'
                    if engagement_boundary else 'Explicit dated employer starts or continues Experience across layout changes')
            elif is_heading:
                label, cluster, similarity, margin = heading
                label = structural_label or label
                contexts[unit.lane] = (label, unit.index, structural_label is not None)
                if unit.lane == 'wide' or len(page_heading_lanes.get(element.page_number, set()) - {'wide', 'unknown'}) <= 1:
                    for lane in set(item.lane for item in units):
                        contexts[lane] = (label, unit.index, structural_label is not None)
                candidate = hlabel
                assignment, reason = ('structural_heading', 'Explicit section heading; BERT/K-means candidate retained as evidence') if structural_label else ('section_heading', 'Distinct BERT heading match with a K-means section label')
            elif position < first_heading and len(unit.text.split()) <= 22 and any(heading_boundary(item.text, ALIASES)[0] == 'personal_information' for item in units[:20]):
                label = 'personal_information'
                assignment, reason = 'contact_context', 'Opening identity/headline before the contact section'
            elif not context and position < first_heading and len(unit.text.split()) <= 18 and not unit.text.rstrip().endswith(('.', '!', '?')) and any(
                    re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', units[j].text)
                    for j in range(max(0, position - 2), min(first_heading, position + 3))
                    if units[j].lane == unit.lane or (position <= 2 and request.elements[units[j].index].page_number == element.page_number)):
                label = 'personal_information'
                assignment, reason = 'contact_context', 'Opening identity/headline adjacent to an explicit email address'
            elif (not context or not context[2] or not element.metadata.get('pdf_source_lines')) and not record_field and short and element.type in {'Title', 'Header'} and hscore >= .50 and (hmargin < .09 or similarity < .35):
                contexts.pop(unit.lane, None)
                if unit.lane == 'wide':
                    contexts.clear()
                assignment, reason = 'needs_review', 'Possible ambiguous or unsupported heading; section context stopped'
            elif context:
                if not context[2] and not record_field and similarity >= .65 and margin >= .12 and label != context[0]:
                    assignment, reason = 'needs_review', 'Content conflicts with the active section; not forced into either block'
                else:
                    label, context_source = context[:2]
                    assignment, reason = 'heading_context', 'Follows a detected heading in the same layout lane; verify visually'
            elif not context and position < first_heading and len(unit.text.split()) <= 18 and not unit.text.rstrip().endswith(('.', '!', '?')) and (similarity < .44 or margin < .07):
                # Short preamble names/titles may be uninterpretable in isolation.
                # Use only adjacent BERT-detected contact text, never a name regex.
                neighbors = [contents[j] for j in range(max(0, position - 2), min(first_heading, position + 3))
                             if units[j].lane == unit.lane and contents[j][0] == 'personal_information'
                             and contents[j][2] >= .50 and contents[j][3] >= .12]
                if neighbors:
                    label, cluster, similarity, margin = max(neighbors, key=lambda item: item[2])
                    candidate = label
                    assignment, reason = 'contact_context', 'Short preamble beside BERT-detected contact details; verify visually'
                else:
                    assignment, reason = 'needs_review', 'Insufficient semantic evidence for this preamble text'
            elif similarity < .44 or margin < .07:
                assignment, reason = 'needs_review', 'Insufficient separation between semantic clusters'
            # Physical line hints can change lanes within one extracted paragraph.
            # Retain its explicit owning section until a new heading overrides it.
            if assignment == 'needs_review':
                element_contexts.pop(unit.index, None)
            elif assignment in {'structural_heading', 'section_heading', 'employment_boundary'}:
                element_contexts[unit.index] = (label, unit.index, True)
            elif context and context[2] and assignment == 'heading_context':
                element_contexts[unit.index] = context
            block = SectionBlock(source_element_index=unit.index, start=unit.start, end=unit.end,
                                 text=unit.text, page_number=element.page_number, cluster_id=cluster,
                                 candidate_section=candidate, alternatives=alternatives if compound else [], assignment=assignment,
                                 cluster_space='heading' if is_heading else 'content', context_source_element_index=context_source, similarity=round(similarity, 4),
                                 margin=round(margin, 4), lane=unit.lane, reason=reason)
            if assignment == 'needs_review' or label not in ANCHORS:
                review.append(block)
            else:
                grouped.setdefault(label, []).append(block)
        sections = build_sections(grouped, request.elements)
        all_blocks = [block for section in sections for block in section.blocks] + review
        # Conservation is an invariant, independent of semantic correctness.
        for index, element in enumerate(request.elements):
            parts = sorted((block for block in all_blocks if block.source_element_index == index), key=lambda block: block.start)
            cursor = 0
            for part in parts:
                if part.start != cursor or part.text != element.text[part.start:part.end]:
                    raise RuntimeError('Section source mapping is not contiguous')
                cursor = part.end
            if cursor != len(element.text) or ''.join(part.text for part in parts) != element.text:
                raise RuntimeError('Section source mapping lost text')
        assigned_chars = sum(len(block.text.strip()) for section in sections for block in section.blocks)
        total_chars = sum(len(block.text.strip()) for block in all_blocks)
        warnings = ['Section assignments are provisional, not guaranteed correct or calibrated probabilities.',
                    ('Caller marked extraction as checked; this is not proof of OCR accuracy.' if request.extraction_verified else 'Extraction has not been manually checked; grouping does not establish word accuracy.'),
                    'Missing headings, merged columns and unusual layouts can require manual review.']
        if multicolumn:
            warnings.append('Multiple layout lanes detected with K-means; reading order and lane assignments need visual review.')
        return SectionResponse(status='needs_review' if review else 'provisional', extraction_verified=request.extraction_verified, sections=sections, needs_review=review,
                               metadata={'model': MODEL_ID, 'revision': MODEL_REVISION, 'encoder': 'Sentence-BERT / MiniLM BertModel',
                                         'algorithm': 'structure-led boundaries + Sentence-BERT + seeded K-means', 'readable_grouping': 'pinned repository semantic_blocks.prepare_blocks + group_sections', 'structure_reference': 'Gopi088/knowledge-graph-resume@48376b8d8a0f64d1ab59b405ded3d9f38fc9ae48', 'anchor_sha256': hashlib.sha256(json.dumps(ANCHORS, sort_keys=True).encode()).hexdigest(), 'categories': len(ANCHORS), 'total_units': len(units),
                                         'assigned_units': sum(len(section.blocks) for section in sections), 'review_units': len(review),
                                         'assigned_text_percent': round(100 * assigned_chars / max(total_chars, 1), 1),
                                         'all_source_text_preserved': True, 'heading_seed_purity': round(self.headings.purity, 3),
                                         'content_seed_purity': round(self.content.purity, 3)}, warnings=warnings)


def layout_lanes(elements):
    """Separate clearly spaced columns using K-means on normalized X positions."""
    from sklearn.cluster import KMeans
    positions = []
    for element in elements:
        try:
            coordinates = element.metadata['coordinates']
            width = float(coordinates['layout_width'])
            xs = [float(point[0]) / width for point in coordinates['points']]
            left, right = min(xs), max(xs)
            positions.append((left, right) if width > 0 and 0 <= left <= right <= 1 else None)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            positions.append(None)
    def spans_columns(position):
        return position[1] - position[0] >= .65 and position[0] < .18

    candidates = [position[0] for position in positions if position and not spans_columns(position)]
    if len(candidates) < 6 or max(candidates) - min(candidates) < .20:
        return ['main'] * len(elements), False
    model = KMeans(n_clusters=2, n_init=10, random_state=42).fit(np.array(candidates).reshape(-1, 1))
    centers = sorted(model.cluster_centers_.ravel())
    if centers[1] - centers[0] < .20 or min(Counter(model.labels_).values()) < 2:
        return ['main'] * len(elements), False
    lanes = []
    for position in positions:
        if position is None:
            lanes.append('unknown')
        elif spans_columns(position):
            lanes.append('wide')
        else:
            lanes.append('left' if abs(position[0] - centers[0]) <= abs(position[0] - centers[1]) else 'right')
    return lanes, True


def get_engine():
    global _engine
    with _load_lock:
        if _engine is None:
            try:
                _engine = SectionEngine()
            except Exception as exc:
                logger.error('Section model unavailable: %s', type(exc).__name__)
                raise ExtractionError(503, 'Local BERT section model unavailable. Run scripts/warm_models.py --sections first.') from exc
    return _engine


def detect_sections(request: SectionRequest) -> SectionResponse:
    try:
        return get_engine().detect(request)
    except ExtractionError:
        raise
    except Exception as exc:
        logger.error('Section detection failed: %s', type(exc).__name__)
        raise ExtractionError(500, 'Resume section detection failed') from exc
