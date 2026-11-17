"""Hierarchical numbering-aware project record boundary detection.

Distinguishes top-level project headings from nested numbered description steps,
ensuring multi-step descriptions remain aggregated within their parent project
record, while genuinely separate projects produce distinct records.
"""
import json
import logging
import re
from local_api.services.record_subfields import ACTION, responsibility_fragment, ALIASES
from local_api.services.resume_structure import el_type, el_meta, normalized_heading, RECORD_FIELDS

logger = logging.getLogger(__name__)

PROJECT_KEYWORD_PAT = re.compile(
    r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?(?:'
    r'#?\s*(\d{1,3})[\s:.)-]*(?:project(?:\s+name|\s+title)?|academic\s+project)\b|'
    r'#(?:project(?:\s+name|\s+title)?)\b|'
    r'(?:academic\s+)?project\s*#?[\s\-]*(\d{1,3})?\b|'
    r'project\s+(?:name|title)\b'
    r')',
    re.IGNORECASE
)

PORTFOLIO_CONTEXT_PAT = re.compile(
    r'^\s*(?:(?:projects?|portfolio|client\s+projects?)\s*(?:worked\s+(?:in|on|at|for)|in|at|for)\b|worked\s+(?:in|on|at|for)\b)',
    re.IGNORECASE
)

PROJECT_METADATA_PAT = re.compile(
    r'^\s*(?:'
    r'technolog(?:y|ies)|tools?(?:\s+and\s+technolog(?:y|ies)|\s*&\s*technolog(?:y|ies))?|'
    r'tech\s+stack(?: used)?|core\s+technologies|environment(?:\s*/\s*tools)?|'
    r'role|job\s+role|designation|client|duration|period|tenure|team\s+size|'
    r'database(?:s)?|operating\s+systems?|os|programming\s+languages?|languages?|'
    r'frameworks?|cloud(?:\s+services|\s+platforms)?|domain|'
    r'description|project\s+description|project\s+(?:name|title)|project\s+details|'
    r'responsibilities|roles?\s+(?:and|&)\s+responsibilities|key\s+responsibilities|'
    r'duties|tasks|key\s+contributions?|contributions?|scope'
    r')\s*[:=-]',
    re.IGNORECASE
)

NUMBERED_PREFIX_PAT = re.compile(
    r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?(?:\(?\d{1,3}[.)\-]\s*|[a-z][.)]\s*)?'
)


def log_project_boundary(
    source_block_id: str,
    candidate_text: str,
    active_project_id: str | None,
    classification: str,
    boundary_accepted: bool,
    boundary_reason: str,
    resulting_parent_project_id: str | None
):
    entry = {
        'source_block_id': source_block_id,
        'candidate_text': candidate_text[:80] + ('...' if len(candidate_text) > 80 else ''),
        'active_project_id': active_project_id,
        'classification': classification,
        'boundary_accepted': boundary_accepted,
        'boundary_reason': boundary_reason,
        'resulting_parent_project_id': resulting_parent_project_id
    }
    logger.info("PROJECT_BOUNDARY_DECISION: %s", json.dumps(entry))


def log_project_boundary_decision(
    source_block_id: str,
    source_text: str,
    current_section_id: str,
    active_project_id: str | None,
    proposed_record_boundary: bool,
    boundary_reason: str,
    resulting_project_id: str | None,
    classification: str = "TOP_LEVEL_PROJECT_HEADING"
):
    log_project_boundary(
        source_block_id=source_block_id,
        candidate_text=source_text,
        active_project_id=active_project_id,
        classification=classification,
        boundary_accepted=proposed_record_boundary,
        boundary_reason=boundary_reason,
        resulting_parent_project_id=resulting_project_id
    )


def is_date_line(text):
    """Check if text is purely or predominantly dates/ranges."""
    s = text.strip()
    return bool(re.search(r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s*[\'‘’]?\d{2}\b', s, re.I)) and not re.sub(
        r'(?i)\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|present|current|to|since|till)\b|[\d\s.,/|:–—\-\'‘’()]', '', s)


def is_project_metadata_line(text):
    """Check if a line is a metadata label (Technologies, Client, Role, Duration, etc.)."""
    s = text.strip()
    if not s:
        return False
    if PROJECT_METADATA_PAT.match(s):
        return True
    prefix = normalized_heading(s.split(':', 1)[0])
    proj_aliases = ALIASES.get('projects', {})
    if prefix in RECORD_FIELDS or prefix in proj_aliases:
        return True
    if normalized_heading(s) in RECORD_FIELDS or normalized_heading(s) in proj_aliases:
        return True
    return False


def is_title_phrase(text):
    """Check if text is predominantly a title-cased noun phrase without action verbs."""
    core = NUMBERED_PREFIX_PAT.sub('', text).strip()
    core_clean = re.sub(r'\(.*?\)', '', core).strip().rstrip('.;!?-').strip()
    words = [w for w in re.split(r'\s+', core_clean) if any(c.isalpha() for c in w)]
    if not words:
        return False
    if re.match(r'^\s*(?:' + ACTION.pattern + r')\b', core, re.I):
        return False
    ignore = {'and', 'or', 'for', 'the', 'of', 'in', '&', 'to', 'with', 'a', 'an', 'on', 'at', 'by', 'from', 'using', 'via'}
    cap = sum(1 for w in words if w[:1].isupper() or w.lower() in ignore)
    return (cap / len(words)) >= 0.75


def is_project_description_step(text, element=None, hints=None):
    """Check if a text block represents a project description statement or duty."""
    s = text.strip()
    if not s:
        return False

    # Explicit project headings (e.g. "Project 1: ...", "• Project: ...") are not duties
    if PROJECT_KEYWORD_PAT.match(s):
        core_kw = re.sub(
            r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?(?:'
            r'#?\s*(\d{1,3})[\s:.)-]*(?:project(?:\s+name|\s+title)?|academic\s+project)?\s*[:.)-]?\s*|'
            r'#(?:project(?:\s+name|\s+title)?)\s*[:.)-]?\s*|'
            r'(?:academic\s+)?project\s*#?[\s\-]*(\d{1,3})?\s*[:.)-]?\s*|'
            r'project\s+(?:name|title)\s*[:.)-]?\s*'
            r')',
            '', s, flags=re.I
        ).strip()
        if not re.match(r'^\s*(?:' + ACTION.pattern + r')\b', core_kw, re.I):
            return False

    core = NUMBERED_PREFIX_PAT.sub('', s).strip()
    if not core:
        return False

    # If it is a clear title-cased noun phrase without action verbs, it is a project title, not a duty
    if is_title_phrase(s):
        return False

    # Check common description words
    if re.search(r'\b(?:description|statement|responsibility|responsibilities|duty|duties|task|tasks|contribution|contributions|activity|activities|deliverable|deliverables|step|steps|implementation|requirement|requirements)\b', core, re.I):
        if not re.match(r'^(?:project|academic\s+project)\b', core, re.I):
            return True

    words = core.split()
    # A short title-cased noun phrase without terminal punctuation is a title, not a duty
    if 1 <= len(words) <= 6 and not core.endswith(('.', ';', '!', '?')):
        if all(w[:1].isupper() or w.lower() in {'and', 'or', 'for', 'the', 'of', 'in', '&', 'to', 'with'} for w in words):
            return False

    # Check if core starts with an action verb or duty fragment
    if re.match(r'^\s*(?:' + ACTION.pattern + r')\b', core, re.I) or responsibility_fragment(core):
        return True

    # Common task/responsibility starters
    if re.match(r'^(?:responsible\s+for|duties|responsibilities|tasks|activities|contributions?|scope)\b', core, re.I):
        return True

    # Punctuation and sentence length: narrative sentence ending in period or semicolon
    if len(words) > 3 and core.rstrip().endswith(('.', ';', '!', '?')):
        if not re.search(r'\b(?:ltd|inc|corp|co|pvt|dept|univ|portal|app)\.$', core, re.I):
            return True

    # List item with lowercase start or ending with punctuation
    if element is not None and el_type(element) == 'ListItem':
        if core[:1].islower() or core.rstrip().endswith(('.', ';')):
            return True

    return False


def extract_project_header_info(text):
    """Extract (is_header, number, title) from a candidate project header text."""
    s = text.strip()
    if not s:
        return False, None, ""

    m_kw = re.match(
        r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?(?:'
        r'#?\s*(\d{1,3})[\s:.)-]*(?:project(?:\s+name|\s+title)?|academic\s+project)?\s*[:.)-]?\s*|'
        r'#(?:project(?:\s+name|\s+title)?)\s*[:.)-]?\s*|'
        r'(?:academic\s+)?project\s*#?[\s\-]*(\d{1,3})?\s*[:.)-]?\s*|'
        r'project\s+(?:name|title)\s*[:.)-]?\s*'
        r')(\S.*)?$',
        s, re.I
    )
    if m_kw and PROJECT_KEYWORD_PAT.match(s):
        num_str = m_kw.group(1) or m_kw.group(2)
        num = int(num_str) if num_str else None
        rest = (m_kw.group(3) or "").strip()
        cand_title = re.split(r'\s+(?:Clients?|Tools|Technologies|Technology|Description|Duration)\s*:', rest, flags=re.I)[0].strip()
        return True, num, cand_title

    m_num = re.match(r'^\s*(?:[•▪●*✓✔\-\uf0b7]\s*)?#?\s*\.?\s*(\d{1,3})[.)\-]\s*(\S.*)$', s, re.DOTALL)
    if m_num:
        num = int(m_num.group(1))
        rest = m_num.group(2).strip()
        cand_title = re.split(r'\s+(?:Clients?|Tools|Technologies|Technology|Description|Duration)\s*:', rest, flags=re.I)[0].strip()
        return False, num, cand_title

    return False, None, ""


def detect_project_records(blocks, elements):
    """Detect hierarchical project records, distinguishing top-level projects from numbered steps."""
    if not blocks:
        return []

    # Check how many explicit project headers exist
    explicit_anchors = []
    for idx, b in enumerate(blocks):
        if not b.text.strip():
            continue
        if normalized_heading(b.text) in {'projects', 'project', 'academic projects', 'academic project'}:
            continue
        el = elements[b.source_element_index] if b.source_element_index < len(elements) else None
        is_explicit, num, cand_title = extract_project_header_info(b.text)
        is_desc = is_project_description_step(b.text, el)
        if is_explicit and not is_desc:
            explicit_anchors.append((idx, num, cand_title))

    # Single explicit project header at the start of a single-project section
    # Only if it appears near the beginning (<= 2) and there are no other numbered project titles
    if len(explicit_anchors) == 1 and explicit_anchors[0][0] <= 2:
        other_titles = False
        for i in range(explicit_anchors[0][0] + 1, len(blocks)):
            b = blocks[i]
            if not b.text.strip():
                continue
            if normalized_heading(b.text) in {'projects', 'project', 'academic projects', 'academic project'}:
                continue
            is_exp, num, cand = extract_project_header_info(b.text)
            if (num is not None and num > 1 and is_title_phrase(b.text)) or is_exp:
                other_titles = True
                break
        if not other_titles:
            start_idx = explicit_anchors[0][0]
            content_indices = [
                i for i, b in enumerate(blocks)
                if b.assignment not in {'section_heading', 'structural_heading'} and b.text.strip()
            ]
            entry_id = 'projects-1'
            for i in content_indices:
                sid = f'e{blocks[i].source_element_index}:{blocks[i].start}:{blocks[i].end}'
                is_start = (i == start_idx)
                classification = "TOP_LEVEL_PROJECT_HEADING" if is_start else "NESTED_DESCRIPTION_STEP"
                reason = "single explicit project marker" if is_start else "numbered description step/content belonging to single project"
                log_project_boundary(
                    source_block_id=sid,
                    candidate_text=blocks[i].text,
                    active_project_id=None if is_start else entry_id,
                    classification=classification,
                    boundary_accepted=is_start,
                    boundary_reason=reason,
                    resulting_parent_project_id=entry_id
                )
            return [{
                'entry_id': entry_id,
                'block_indices': content_indices,
                'lane': blocks[start_idx].lane,
                'boundary_reason': 'single project with numbered/bullet description steps'
            }]

    # Multiple explicit project headers or numbered project items
    records = []
    active_record = None
    last_top_num = 0
    parent_has_explicit_keyword = False
    in_child_list = False
    last_child_num = 0

    for idx, b in enumerate(blocks):
        sid = f'e{b.source_element_index}:{b.start}:{b.end}'
        if not b.text.strip():
            continue

        el = elements[b.source_element_index] if b.source_element_index < len(elements) else None
        text = b.text.strip()
        active_proj_id_before = active_record['entry_id'] if active_record else None

        # Section-level heading is a section boundary, not a project record
        if normalized_heading(text) in {'projects', 'project', 'academic projects', 'academic project'}:
            continue

        # If a block is marked structural_heading or section_heading, it can still serve as a project boundary anchor
        if b.assignment in {'section_heading', 'structural_heading'}:
            is_explicit, num, cand_title = extract_project_header_info(text)
            is_desc = is_project_description_step(text, el)
            if is_explicit and not is_desc:
                entry_id = f'projects-{len(records) + 1}'
                active_record = {
                    'entry_id': entry_id,
                    'block_indices': [],
                    'lane': b.lane,
                    'boundary_reason': f"explicit project keyword in structural heading (num={num})"
                }
                records.append(active_record)
                parent_has_explicit_keyword = True
                last_top_num = num if num is not None else (last_top_num + 1)
                in_child_list = False
                last_child_num = 0
                log_project_boundary(
                    source_block_id=sid,
                    candidate_text=text,
                    active_project_id=active_proj_id_before,
                    classification="TOP_LEVEL_PROJECT_HEADING",
                    boundary_accepted=True,
                    boundary_reason=f"explicit project keyword in structural heading (num={num})",
                    resulting_parent_project_id=entry_id
                )
            continue

        # Context line: "Projects Worked in Param Info..." or "Worked in Param Info..."
        if PORTFOLIO_CONTEXT_PAT.match(text):
            in_child_list = False
            parent_has_explicit_keyword = False
            log_project_boundary(
                source_block_id=sid,
                candidate_text=text,
                active_project_id=active_proj_id_before,
                classification='PORTFOLIO_CONTEXT_HEADER',
                boundary_accepted=False,
                boundary_reason='portfolio/employer context overview header',
                resulting_parent_project_id=active_proj_id_before
            )
            continue

        is_explicit, num, cand_title = extract_project_header_info(text)
        is_desc = is_project_description_step(text, el)
        is_meta = is_project_metadata_line(text) or is_date_line(text)

        hints = el_meta(el).get('pdf_source_lines', []) if el else []
        is_bold = any(h.get('bold') for h in hints)
        is_title_element = el is not None and el_type(el) in {'Title', 'Header'}

        starts_new_project = False
        boundary_reason = ""
        classification = "AMBIGUOUS_FRAGMENT"

        if is_explicit:
            if not is_desc:
                starts_new_project = True
                classification = "TOP_LEVEL_PROJECT_HEADING"
                boundary_reason = f"explicit project keyword header (num={num})"
                parent_has_explicit_keyword = True
                last_top_num = num if num is not None else (last_top_num + 1)
                in_child_list = False
                last_child_num = 0
            else:
                classification = "NESTED_DESCRIPTION_STEP"
                boundary_reason = "explicit project prefix on description action step"
        elif num is not None and not is_meta:
            words = cand_title.split()
            is_title_cased = (1 <= len(words) <= 8 and not cand_title.endswith(('.', ';', '!', '?'))
                              and all(w[:1].isupper() or w.lower() in {'and', 'or', 'for', 'the', 'of', 'in', '&', 'to', 'with', 'a', 'an'} for w in words))
            is_proj_title = is_title_phrase(cand_title) or is_title_cased

            if active_record is None:
                if is_proj_title or not is_desc:
                    starts_new_project = True
                    classification = "TOP_LEVEL_PROJECT_HEADING"
                    boundary_reason = f"first numbered project title (num={num})"
                    parent_has_explicit_keyword = False
                    last_top_num = num
                    in_child_list = False
                    last_child_num = 0
                else:
                    classification = "NESTED_DESCRIPTION_STEP" if is_desc else "AMBIGUOUS_FRAGMENT"
                    boundary_reason = "preamble numbered item before project heading"
            else:
                if parent_has_explicit_keyword:
                    # Parent project had "Project 1:"; a bare numbered line is a child description step!
                    starts_new_project = False
                    classification = "NESTED_DESCRIPTION_STEP"
                    boundary_reason = f"nested numbered description step (num={num}) under explicit project header"
                    in_child_list = True
                    last_child_num = num
                else:
                    if num == 1:
                        starts_new_project = False
                        classification = "NESTED_DESCRIPTION_STEP"
                        boundary_reason = "numbered description list restart (num=1)"
                        in_child_list = True
                        last_child_num = 1
                    elif in_child_list:
                        is_next_child = (num == last_child_num + 1)
                        if num == last_top_num + 1 and (is_proj_title or not is_next_child or not is_desc):
                            starts_new_project = True
                            classification = "TOP_LEVEL_PROJECT_HEADING"
                            boundary_reason = f"sequential numbered project title (num={num})"
                            last_top_num = num
                            in_child_list = False
                            last_child_num = 0
                        else:
                            starts_new_project = False
                            classification = "NESTED_DESCRIPTION_STEP"
                            boundary_reason = f"nested description step continuing child list (num={num})"
                            last_child_num = num
                    elif not in_child_list and (num == last_top_num + 1 or (is_proj_title and not is_desc)):
                        starts_new_project = True
                        classification = "TOP_LEVEL_PROJECT_HEADING"
                        boundary_reason = f"sequential numbered project title (num={num})"
                        last_top_num = num
                        in_child_list = False
                        last_child_num = 0
                    else:
                        starts_new_project = False
                        classification = "NESTED_DESCRIPTION_STEP"
                        boundary_reason = f"numbered description step under project (num={num})"
                        in_child_list = True
                        last_child_num = num
        elif num is None and not is_meta and not is_desc and not parent_has_explicit_keyword:
            words = text.split()
            if (is_bold or is_title_element) and 1 <= len(words) <= 12 and not text.rstrip().endswith(('.', ';', '!', '?')):
                if is_title_phrase(text) or (el is not None and el_type(el) in {'Title', 'Header'}):
                    starts_new_project = True
                    classification = "TOP_LEVEL_PROJECT_HEADING"
                    boundary_reason = "prominent unnumbered project title"
                    in_child_list = False
                    last_child_num = 0

        if not starts_new_project:
            if is_meta:
                classification = "PROJECT_METADATA"
                boundary_reason = "project metadata field/date"
            elif is_desc:
                classification = "NESTED_DESCRIPTION_STEP"
                if not boundary_reason:
                    boundary_reason = "nested description step/detail belonging to active project"
            else:
                if not boundary_reason:
                    classification = "AMBIGUOUS_FRAGMENT"
                    boundary_reason = "unstructured text/detail belonging to active project"

        if starts_new_project:
            entry_id = f'projects-{len(records) + 1}'
            active_record = {
                'entry_id': entry_id,
                'block_indices': [idx],
                'lane': b.lane,
                'boundary_reason': boundary_reason
            }
            records.append(active_record)
            log_project_boundary(
                source_block_id=sid,
                candidate_text=text,
                active_project_id=active_proj_id_before,
                classification=classification,
                boundary_accepted=True,
                boundary_reason=boundary_reason,
                resulting_parent_project_id=entry_id
            )
        else:
            if active_record is not None:
                active_record['block_indices'].append(idx)
                log_project_boundary(
                    source_block_id=sid,
                    candidate_text=text,
                    active_project_id=active_record['entry_id'],
                    classification=classification,
                    boundary_accepted=False,
                    boundary_reason=boundary_reason,
                    resulting_parent_project_id=active_record['entry_id']
                )
            else:
                log_project_boundary(
                    source_block_id=sid,
                    candidate_text=text,
                    active_project_id=None,
                    classification=classification,
                    boundary_accepted=False,
                    boundary_reason=boundary_reason,
                    resulting_parent_project_id=None
                )

    return records


def extract_project_numbered_anchors(blocks, elements, rows, contexts):
    """Identify indices of blocks that represent top-level numbered projects for geometric fallback."""
    records = detect_project_records(blocks, elements)
    if records:
        return [r['block_indices'][0] for r in records if r['block_indices']]
    return []


def resolve_ambiguous_project_span(span_text, context_text=None):
    """Classify an ambiguous span as NEW_PROJECT, PROJECT_DESCRIPTION_CONTINUATION, or UNRESOLVED."""
    if is_project_description_step(span_text):
        return 'PROJECT_DESCRIPTION_CONTINUATION'
    if PROJECT_KEYWORD_PAT.match(span_text):
        return 'NEW_PROJECT'

    try:
        from local_api.services.llm_section_review import ReviewSettings, call_deepseek
        settings = ReviewSettings.from_env()
        if not settings.enabled:
            return 'UNRESOLVED'

        prompt = (
            "Analyze the following resume line from a Projects section and determine whether it starts a "
            "NEW_PROJECT (a project title or independent project record) or is a PROJECT_DESCRIPTION_CONTINUATION "
            "(a description, responsibility, duty, or detail belonging to the active project).\n\n"
            f"Context: {context_text or 'None'}\n"
            f"Line: {span_text}\n\n"
            'Respond with JSON: {"classification": "NEW_PROJECT" | "PROJECT_DESCRIPTION_CONTINUATION" | "UNRESOLVED"}'
        )
        messages = [
            {"role": "system", "content": "You are a precise resume structure parser. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        raw = call_deepseek(settings, messages)
        data = json.loads(raw)
        cls = data.get("classification")
        if cls in {'NEW_PROJECT', 'PROJECT_DESCRIPTION_CONTINUATION', 'UNRESOLVED'}:
            return cls
        return 'UNRESOLVED'
    except Exception as exc:
        logger.debug("LLM ambiguous project classification abstained: %s", exc)
        return 'UNRESOLVED'


def recover_project_groups(result):
    """Promote existing portfolio context evidence to a source-owning parent.

    Reuse the detector's context classification; numbering alone never creates
    children here. Only already-established records in the same reading lane
    can be linked, and dates before the first child stay with the parent.
    """
    from local_api.schemas.sections import SectionEntry
    out = result.model_copy(deep=True)
    for section in out.sections:
        if section.category != 'projects' or any(e.record_kind == 'group' for e in section.entries):
            continue
        headers = [i for i, b in enumerate(section.blocks)
                   if PORTFOLIO_CONTEXT_PAT.match(b.text.strip())]
        for position, start in enumerate(headers):
            stop = headers[position + 1] if position + 1 < len(headers) else len(section.blocks)
            children = [e for e in section.entries if e.block_indices and start < min(e.block_indices) < stop
                        and e.lane == section.blocks[start].lane and e.parent_entry_id is None]
            if not children:
                continue
            first = min(min(e.block_indices) for e in children)
            indices = [i for i in range(start, first)
                       if i == start or is_project_metadata_line(section.blocks[i].text) or is_date_line(section.blocks[i].text)]
            # Content between the context heading and first child must be fully
            # explained as parent metadata; never merge unexplained prose.
            if indices != list(range(start, first)):
                continue
            parent_id = f'project-group@e{section.blocks[start].source_element_index}:{section.blocks[start].start}:{section.blocks[start].end}'
            for entry in section.entries:
                entry.block_indices = [i for i in entry.block_indices if i not in indices]
                entry.fields = {key: [i for i in values if i not in indices] for key, values in entry.fields.items()}
            section.entries = [e for e in section.entries if e.block_indices]
            section.entries.append(SectionEntry(entry_id=parent_id, block_indices=indices, lane=section.blocks[start].lane,
                boundary_reason='explicit portfolio context and established child records', record_kind='group',
                fields={'title': [start], 'dates': [i for i in indices if i != start and is_date_line(section.blocks[i].text)]}))
            for child in children:
                child.parent_entry_id = parent_id
            section.entries.sort(key=lambda e: min(e.block_indices))
    return out
