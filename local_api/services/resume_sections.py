"""Local Sentence-BERT + seeded K-means. Raw extraction is never rewritten."""
from collections import Counter
from dataclasses import dataclass
import json
import hashlib
import logging
import re
from pathlib import Path
import threading

import numpy as np

from local_api.schemas.sections import SectionRequest, SectionResponse, ResumeSection, SectionBlock, ReadableGroup
from local_api.utils.file_validation import ExtractionError
from local_api.services.readable_resume import readable_groups
from local_api.services.resume_structure import heading_aliases, heading_boundary, entry_groups, RECORD_FIELDS, normalized_heading

MODEL_CONFIG = json.loads((Path(__file__).parents[1] / 'data/section_model.json').read_text())
MODEL_ID = MODEL_CONFIG['model_id']
MODEL_REVISION = MODEL_CONFIG['revision']
ANCHORS = json.loads((Path(__file__).parents[1] / 'data/section_anchors.json').read_text())
ALIASES = heading_aliases(ANCHORS)
logger = logging.getLogger(__name__)
_load_lock = threading.Lock()
_engine = None


@dataclass
class Unit:
    index: int
    start: int
    end: int
    text: str
    lane: str


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
                _, inline_cut = heading_boundary(line, ALIASES)
                cuts = sorted(set([0] + [offsets[i][0] for i in range(200, len(offsets), 200)] + ([inline_cut] if inline_cut else []) + [len(line)]))
                if not line:
                    cuts = [0, 0]
                for start, end in zip(cuts, cuts[1:]):
                    units.append(Unit(index, offset + start, offset + end, line[start:end], lanes[index]))
                offset += len(line)
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
        grouped, review, contexts = {}, [], {}
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
            context = contexts.get(unit.lane)
            short = len(unit.text.split()) <= 12
            structural_label, _ = heading_boundary(unit.text, ALIASES)
            record_field = ':' in unit.text and normalized_heading(unit.text.split(':', 1)[0]) in RECORD_FIELDS
            alternatives = sorted(compounds.get(position, set()))
            compound = len(alternatives) > 1
            is_heading = (structural_label is not None or (short and hscore >= .72 and hmargin >= .09 and (not context or not context[2] or element.type in {'Title', 'Header'}))) and not compound and not record_field and element.type not in {'Footer', 'PageBreak'}
            assignment, reason = 'semantic', 'BERT embedding assigned to a labeled K-means centroid'
            if compound:
                contexts.pop(unit.lane, None)
                if unit.lane == 'wide':
                    contexts.clear()
                candidate = None
                assignment, reason = 'needs_review', 'Combined heading contains multiple BERT-recognized section families'
            elif element.type in {'Footer', 'PageBreak'}:
                assignment, reason = 'needs_review', 'Layout footer or page separator retained outside semantic sections'
            elif is_heading:
                label, cluster, similarity, margin = heading
                label = structural_label or label
                contexts[unit.lane] = (label, unit.index, structural_label is not None)
                if unit.lane == 'wide':
                    for lane in set(item.lane for item in units):
                        contexts[lane] = (label, unit.index, structural_label is not None)
                candidate = hlabel
                assignment, reason = ('structural_heading', 'Explicit section heading; BERT/K-means candidate retained as evidence') if structural_label else ('section_heading', 'Distinct BERT heading match with a K-means section label')
            elif not context and position < first_heading and len(unit.text.split()) <= 18 and not unit.text.rstrip().endswith(('.', '!', '?')) and any(
                    re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', units[j].text)
                    for j in range(max(0, position - 2), min(first_heading, position + 3)) if units[j].lane == unit.lane):
                label = 'personal_information'
                assignment, reason = 'contact_context', 'Opening identity/headline adjacent to an explicit email address'
            elif not record_field and short and element.type in {'Title', 'Header'} and hscore >= .50 and (hmargin < .09 or similarity < .35):
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
            block = SectionBlock(source_element_index=unit.index, start=unit.start, end=unit.end,
                                 text=unit.text, page_number=element.page_number, cluster_id=cluster,
                                 candidate_section=candidate, alternatives=alternatives if compound else [], assignment=assignment,
                                 cluster_space='heading' if is_heading else 'content', context_source_element_index=context_source, similarity=round(similarity, 4),
                                 margin=round(margin, 4), lane=unit.lane, reason=reason)
            if assignment == 'needs_review' or label not in ANCHORS:
                review.append(block)
            else:
                grouped.setdefault(label, []).append(block)
        sections = [ResumeSection(category=key, label=ANCHORS[key]['label'], blocks=blocks, entries=entry_groups(blocks, key, request.elements)) for key, blocks in grouped.items()]
        for section in sections:
            section.source_heading = next((block.text.strip().rstrip(':') for block in section.blocks
                                           if block.assignment in {'section_heading', 'structural_heading'}), None)
            section.readable_blocks = [ReadableGroup.model_validate(group) for group in readable_groups(section, request.elements)]
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
                    'Extraction verification records caller confirmation; it is not an automatic proof of OCR accuracy.',
                    'Missing headings, merged columns and unusual layouts can require manual review.']
        if multicolumn:
            warnings.append('Multiple layout lanes detected with K-means; reading order and lane assignments need visual review.')
        return SectionResponse(status='needs_review' if review else 'provisional', sections=sections, needs_review=review,
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
