"""Bounded, evidence-led recovery of locally recognizable source spans.

Classification is a proposal, not factual verification. Never rewrite text or
borrow record ownership across lanes, sections, pages or intervening headings.
"""
import re
from local_api.services.record_subfields import labelled_fields, employment_header_fields, ACTION, ROLE
from local_api.services.source_accounting import artifact_reason

HEADINGS = {'section_heading', 'structural_heading'}
LABELS = {
    'certifications': r'(?:certification(?: name)?|certificate|credential id|certificate id|issuing organization|issued by|expiry date|verification url)',
    'education': r'(?:qualification|university|college|institution|graduation year|year of passing|cgpa)',
    'projects': r'(?:project name|project title|project description|project url)',
    'awards': r'(?:award name|awarded by)',
    'publications': r'(?:publication title|published by)',
    'skills': r'(?:technical skills|core competencies|tools and platforms|programming languages)',
    'languages': r'(?:spoken languages|language proficiency)',
}


def explicit_category(text):
    matches = [category for category, label in LABELS.items()
               if re.match(r'^\s*(?:[•▪●*\-]\s*)?' + label + r'\s*[:=]\s*\S', text, re.I)]
    return matches[0] if len(matches) == 1 else None


def source_key(block): return (block.source_element_index, block.start, block.end)


def supported_new_entry(category, blocks):
    if category == 'experience':
        from local_api.services.resume_structure import employment_start
        return any(employment_header_fields(b.text) or employment_start(b.text)
                   or set(labelled_fields(category, [b])) & {'company', 'role'} for b in blocks)
    if category == 'education':
        from local_api.services.record_relationships import degree_families
        return any(degree_families(b.text) or labelled_fields(category, [b]).get('institution') for b in blocks)
    return True


def recover_local_content(result, elements):
    from local_api.services.source_validation import validate_result
    from local_api.services.review_resolution import document_scope
    from local_api.services.resume_sections import build_sections, ALIASES
    from local_api.services.resume_structure import heading_boundary, entry_groups
    from local_api.schemas.sections import SectionEntry
    from local_api.services.record_relationships import annotate_relationships
    errors = validate_result(elements, result)
    if errors: raise ValueError('Invalid source binding before local completion: ' + errors[0])
    if document_scope(elements)['candidate_resume'] is False: return result
    from local_api.services.profile_url_recovery import recover_header_urls
    result = recover_header_urls(result,elements)
    from local_api.services.professional_headline import recover_professional_headline
    result = recover_professional_headline(result,elements)
    from local_api.services.target_preferences import recover_target_preferences
    result = recover_target_preferences(result, elements)
    from local_api.services.project_section_recovery import recover_project_sections
    result = recover_project_sections(result, elements)
    from local_api.services.dated_record_headers import recover_split_employment_headers
    result = recover_split_employment_headers(result,elements)
    from local_api.services.employment_integrity import repair_employment_entries
    result = repair_employment_entries(result, elements)
    from local_api.services.combined_credentials import recover_combined_credentials
    result = recover_combined_credentials(result,elements)
    from local_api.services.certification_integrity import recover_certification_cards
    result = recover_certification_cards(result, elements)
    assigned = [(b, s.category, next((e.entry_id for e in s.entries if i in e.block_indices), None))
                for s in result.sections for i, b in enumerate(s.blocks)]
    moved, events = {}, []
    owner_windows = {}

    def compatible(left, right):
        # Same-element fragments have authoritative source adjacency. Across
        # elements require the same lane; a wide row may match a unique owner.
        if left.page_number != right.page_number: return False
        if left.lane == right.lane or left.source_element_index == right.source_element_index: return True
        if 'wide' not in {left.lane, right.lane}: return False
        key = (left.page_number, left.source_element_index)
        if key not in owner_windows:
            owner_windows[key] = {(c, e) for b, c, e in assigned if e and b.page_number == left.page_number
                                 and abs(b.source_element_index - left.source_element_index) <= 2}
        return len(owner_windows[key]) == 1

    for block in sorted(result.needs_review, key=source_key):
        if artifact_reason(elements[block.source_element_index], block): continue
        if block.alternatives: continue
        heading, cut = heading_boundary(block.text, ALIASES)
        category, owner, reason = explicit_category(block.text) or heading, None, None
        # Literal field labels distinguish section families without semantic guesses.
        if category:
            reason = 'Exact section heading' if heading and cut is None else 'Explicit, category-specific source field label'
        neighbors = [(b, c, entry) for b, c, entry in assigned if b.assignment not in HEADINGS
                     and compatible(block, b) and abs(b.source_element_index - block.source_element_index) <= 2]
        before = sorted((x for x in neighbors if source_key(x[0]) < source_key(block)), key=lambda x: source_key(x[0]))
        after = sorted((x for x in neighbors if source_key(x[0]) > source_key(block)), key=lambda x: source_key(x[0]))
        if not category:
            siblings = [(b, c, e) for b, c, e in assigned if b.source_element_index == block.source_element_index
                        and not artifact_reason(elements[b.source_element_index], b) and b.assignment not in HEADINGS]
            families = {(c, e) for _, c, e in siblings}
            paragraph_parts = [b for b in result.needs_review if b.source_element_index == block.source_element_index]
            barriers = any(heading_boundary(b.text, ALIASES)[0] or employment_header_fields(b.text)
                           or explicit_category(b.text) for b in paragraph_parts)
            if len(families) == 1 and not barriers:
                candidate, entry = next(iter(families))
                if candidate in {'experience', 'projects', 'summary'} and any(
                        b.assignment in {'heading_context', 'local_record_continuation', 'paragraph_continuation'} for b, _, _ in siblings):
                    category, owner = candidate, entry
                    reason = 'Same source paragraph has one established section context; record association remains provisional'
        # An existing record is required before attaching duties or loose dates.
        if not category and before:
            anchor, candidate, entry = before[-1]
            barriers = [b for b, _, _ in assigned if b.assignment in HEADINGS and
                        source_key(anchor) < source_key(b) < source_key(block) and compatible(block, b)]
            barriers += [b for b in result.needs_review if source_key(anchor) < source_key(b) < source_key(block)
                         and compatible(block, b) and (heading_boundary(b.text, ALIASES)[0]
                             or employment_header_fields(b.text) or explicit_category(b.text))]
            same_element = anchor.source_element_index == block.source_element_index and anchor.end == block.start
            owners = {(c, e) for b, c, e in neighbors if b.source_element_index == block.source_element_index}
            supported = same_element and len(owners) == 1 or (entry and candidate in {'experience', 'projects'})
            if supported and not barriers and candidate in {'experience', 'projects', 'summary'}:
                action = bool(ACTION.search(block.text.strip()) or (len(block.text.split()) >= 6 and re.match(
                    r'^\s*(?:[•▪●*\-]\s*)?(?:integrate|automate|optimi[sz]e|maintain|improve|deliver|troubleshoot)\b', block.text, re.I)))
                continuation = same_element and (block.text.lstrip()[:1].islower() or action)
                if (action or continuation) and not employment_header_fields(block.text):
                    category, owner = candidate, entry
                    reason = 'Responsibility/paragraph continuation beside an established source owner'
        # A loose date can join only a unique same-element, already established record.
        if not category:
            from local_api.services.record_subfields import RANGE
            if RANGE.fullmatch(block.text.strip()):
                candidates = {(c, entry) for b, c, entry in neighbors
                              if b.source_element_index == block.source_element_index and entry
                              and c in {'experience', 'education'}}
                if len(candidates) == 1:
                    category, owner = next(iter(candidates))
                    reason = 'Date range inside a uniquely established source record'
        if not category: continue
        if owner is None:
            # Detail labels may extend an adjacent card, but never infer an owner
            # for a new project/credential/name boundary.
            detail = category == 'certifications' and 'name' not in labelled_fields(category, [block])
            owners = {(c, entry) for b, c, entry in before[-1:] if c == category and entry}
            if detail and len(owners) == 1: owner = next(iter(owners))[1]
        new = block.model_copy(update={'assignment': 'structural_heading' if heading and cut is None else
                                       'local_record_continuation' if owner and category in {'experience', 'projects'}
                                       else 'local_source_recovery', 'reason': reason,
                                       'llm_action': 'abstained_then_local_source_recovery' if block.reviewed_by_llm else block.llm_action})
        moved[source_key(block)] = (category, owner, new)
        events.append({'source_id': f'e{block.source_element_index}:{block.start}:{block.end}',
                       'category': category, 'record_id': owner, 'reason': reason})
        assigned.append((new, category, owner))
        owner_windows.clear()
    if not moved: return result
    grouped = {s.category: list(s.blocks) for s in result.sections}
    for category, _, block in moved.values(): grouped.setdefault(category, []).append(block)
    for blocks in grouped.values(): blocks.sort(key=source_key)
    updated = result.model_copy(deep=True)
    updated.sections = build_sections(grouped, elements, refine=False)
    # Keep previously established memberships; adding one source span must not
    # merge or split unrelated jobs/qualifications already reviewed by a caller.
    old_sections = {s.category: s for s in result.sections}
    affected = {category for category, _, _ in moved.values()}
    for i, section in enumerate(updated.sections):
        old = old_sections.get(section.category)
        if old and section.category not in affected:
            updated.sections[i] = old.model_copy(deep=True); continue
        if not old or not old.entries:
            section.entries = [e for e in section.entries if supported_new_entry(section.category,
                [section.blocks[n] for n in e.block_indices])]
            annotate_relationships(section)
            from local_api.services.readable_resume import readable_groups
            from local_api.schemas.sections import ReadableGroup
            section.readable_blocks = [ReadableGroup.model_validate(v) for v in readable_groups(section, elements)]
            continue
        indices = {source_key(b): n for n, b in enumerate(section.blocks)}
        entries = []
        used = set()
        for entry in old.entries:
            members = [indices[source_key(old.blocks[n])] for n in entry.block_indices]
            members += [indices[key] for key, (c, owner, _) in moved.items()
                        if c == section.category and owner == entry.entry_id]
            members = sorted(set(members)); used.update(members)
            entries.append(entry.model_copy(update={'block_indices': members, 'fields': {}}))
        remaining = [n for n, b in enumerate(section.blocks) if n not in used and b.assignment not in HEADINGS]
        identifiers = {e.entry_id for e in entries}
        number = 1
        for proposal in entry_groups([section.blocks[j] for j in remaining], section.category, elements):
            if not supported_new_entry(section.category, [section.blocks[remaining[j]] for j in proposal['block_indices']]):
                continue
            while f'{section.category}-local-{number}' in identifiers: number += 1
            identifier = f'{section.category}-local-{number}'; identifiers.add(identifier)
            entries.append(SectionEntry(**{**proposal, 'entry_id': identifier,
                'block_indices': [remaining[j] for j in proposal['block_indices']]}))
        section.entries = entries
        annotate_relationships(section)
        from local_api.services.readable_resume import readable_groups
        from local_api.schemas.sections import ReadableGroup
        section.readable_blocks = [ReadableGroup.model_validate(v) for v in readable_groups(section, elements)]
    updated.needs_review = [b for b in result.needs_review if source_key(b) not in moved]
    updated.status = 'needs_review' if updated.needs_review else 'provisional'
    updated.metadata['local_content_recovery'] = result.metadata.get('local_content_recovery', []) + events
    updated.metadata.update(assigned_units=sum(len(s.blocks) for s in updated.sections),
                            review_units=len(updated.needs_review))
    all_blocks = [b for s in updated.sections for b in s.blocks] + updated.needs_review
    updated.metadata['assigned_text_percent'] = round(100 * sum(len(b.text.strip()) for s in updated.sections for b in s.blocks)
        / max(1, sum(len(b.text.strip()) for b in all_blocks)), 1)
    errors = validate_result(elements, updated)
    if errors: raise ValueError('Invalid source binding after local completion: ' + errors[0])
    return updated
