"""Recover explicit career-summary prose before employment without inventing identity."""
import re
from local_api.services.record_subfields import ROLE, employment_header_fields
from local_api.services.resume_structure import heading_boundary, employment_start


def recover_summary_preamble(result, elements):
    from local_api.services.resume_sections import ALIASES, build_sections
    from local_api.services.contact_sections import recover_contact_sections, contact_values, profile_values
    from local_api.services.review_resolution import document_scope
    from local_api.services.source_validation import validate_result
    if document_scope(elements)['candidate_resume'] is False: return result
    result = recover_contact_sections(result, elements)
    if not result.needs_review: return result
    boundaries = [i for i, el in enumerate(elements) if heading_boundary(el.text, ALIASES)[0]
                  in {'experience', 'education', 'projects', 'skills', 'certifications', 'references'}
                  or employment_start(el.text)]
    end = min(boundaries, default=min(len(elements), 15))
    pending = sorted([b for b in result.needs_review if b.source_element_index < end and b.page_number in {None, 1}],
                     key=lambda b: (b.source_element_index, b.start))
    start = next((b for b in pending if len(b.text.split()) >= 8 and
        re.match(r'^\s*(?:experienced|results[- ]driven|accomplished|motivated|dedicated|seasoned)\b', b.text, re.I)
        and not re.search(r'\b(?:required|must have|candidate should|we seek|hiring)\b', b.text, re.I)
        and (ROLE.search(b.text) or re.search(r'\b\d+\+?\s+years?\b', b.text, re.I))), None)
    if start is None: return result
    moved = []
    for b in pending:
        if (b.source_element_index, b.start) < (start.source_element_index, start.start): continue
        if heading_boundary(b.text, ALIASES)[0] or employment_header_fields(b.text): break
        if any(contact_values([b]).values()) or any(profile_values([b]).values()): break
        if b is not start and len(b.text.split()) < 6 and b.source_element_index != start.source_element_index: break
        if re.match(r'^\s*(?:[A-Za-z+#.]+\s*[,|]\s*){2,}', b.text): break
        moved.append(b)
    if not moved: return result
    grouped = {s.category: list(s.blocks) for s in result.sections}
    grouped.setdefault('summary', []).extend(b.model_copy(update={'assignment': 'local_preamble_summary',
        'reason': 'Explicit career-summary introduction and contiguous opening prose before employment/section boundaries.'}) for b in moved)
    for blocks in grouped.values(): blocks.sort(key=lambda b: (b.source_element_index, b.start))
    repaired = result.model_copy(deep=True)
    rebuilt = build_sections(grouped, elements, refine=False)
    old = {s.category: s for s in result.sections}
    repaired.sections = [s if s.category == 'summary' or s.category not in old else old[s.category].model_copy(deep=True) for s in rebuilt]
    keys = {(b.source_element_index, b.start, b.end) for b in moved}
    repaired.needs_review = [b for b in result.needs_review if (b.source_element_index, b.start, b.end) not in keys]
    repaired.metadata['preamble_summary_recovery'] = {'recovered_spans': len(moved)}
    repaired.metadata.update(assigned_units=sum(len(s.blocks) for s in repaired.sections), review_units=len(repaired.needs_review))
    total = sum(len(b.text.strip()) for s in repaired.sections for b in s.blocks) + sum(len(b.text.strip()) for b in repaired.needs_review)
    repaired.metadata['assigned_text_percent'] = round(100 * sum(len(b.text.strip()) for s in repaired.sections for b in s.blocks) / max(1, total), 1)
    repaired.status = 'needs_review' if repaired.needs_review else 'provisional'
    if validate_result(elements, repaired): raise ValueError('Invalid source binding after preamble recovery')
    return repaired
