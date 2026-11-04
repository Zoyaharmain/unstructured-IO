"""Exact source-to-field accounting; coverage never certifies semantic accuracy."""
import re
from collections import defaultdict
from local_api.services.source_accounting import artifact_reason
from local_api.services.source_validation import validate_result


def compatible_claims(left, right):
    same_record = left[2:4] == right[2:4]
    related_dates = {left[4], right[4]} <= {'duration', 'start_date', 'end_date'}
    skill_union = left[2] == right[2] == 'skills' and 'all_skills' in {left[4], right[4]}
    summary_number = left[2] == right[2] == 'summary' and {left[4], right[4]} <= {'statements', 'total_experience_years'}
    return same_record and (left[4] == right[4] or related_dates or skill_union or summary_number)


def mapping_completeness(elements, sections, hierarchy):
    errors = validate_result(elements, sections)
    if errors: raise ValueError('Invalid source inventory in completeness check: ' + errors[0])
    inventory = {f'e{b.source_element_index}:{b.start}:{b.end}': (b, s.category)
                 for s in sections.sections for b in s.blocks}
    inventory.update({f'e{b.source_element_index}:{b.start}:{b.end}': (b, None) for b in sections.needs_review})
    covered = {sid: [False] * len(b.text) for sid, (b, _) in inventory.items()}
    claims = defaultdict(list)
    for section in hierarchy:
        for record in section.records:
            for attr in record.attributes:
                for index, item in enumerate(attr.items):
                    value = format(item.value, 'g') if isinstance(item.value, (int, float)) else item.value
                    path = f'{section.category}/{record.record_id}/{attr.name}/{index}'
                    parent=next((s for s in sections.sections if s.category==section.category),None)
                    entry=next((e for e in parent.entries if e.entry_id==record.record_id),None) if parent else None
                    context_ids={f'e{parent.blocks[i].source_element_index}:{parent.blocks[i].start}:{parent.blocks[i].end}' for i in entry.context_fields.get(attr.name,[])} if entry else set()
                    for ref in item.evidence:
                        if ref.source_id not in inventory: raise ValueError('Foreign source in completeness check')
                        block, owner = inventory[ref.source_id]
                        if owner != section.category: raise ValueError('Foreign section in completeness check')
                        quote_starts = [m.start() for m in re.finditer(re.escape(ref.quote), block.text)]
                        if not quote_starts: raise ValueError('Nonliteral completeness evidence')
                        # Quote context is not automatically a mapped field value.
                        starts = [m.start() for m in re.finditer(re.escape(value), ref.quote, re.I)] if value else []
                        length = len(value)
                        if not starts and ref.quote.casefold() in value.casefold():
                            starts, length = [0], len(ref.quote)
                        if not starts: continue
                        if ref.source_id in context_ids:continue
                        candidates = [(pos + start, pos + start + length, section.category, record.record_id, attr.name, path)
                                      for pos in quote_starts for start in starts]
                        def score(candidate):
                            overlapping = [old for old in claims[ref.source_id]
                                           if max(old[0], candidate[0]) < min(old[1], candidate[1])]
                            return (sum(not compatible_claims(old, candidate) for old in overlapping), len(overlapping), candidate[0])
                        chosen = min(candidates, key=score)
                        start = chosen[0]
                        end = start + length
                        covered[ref.source_id][start:end] = [True] * length
                        claims[ref.source_id].append((start, end, section.category, record.record_id, attr.name, path))
    unresolved, artifacts, headings = [], [], []
    for sid, (block, category) in inventory.items():
        artifact = artifact_reason(elements[block.source_element_index], block)
        if artifact: artifacts.append({'source_id': sid, 'reason': artifact}); continue
        if block.assignment in {'section_heading', 'structural_heading'}:
            headings.append(sid); continue
        mask = covered[sid]
        start = 0
        for end in range(len(mask) + 1):
            if end < len(mask) and not mask[end]: continue
            if start < end:
                text = block.text[start:end]
                # Field labels and separators are structure, not missing values.
                from local_api.services.record_subfields import ALIASES
                from local_api.schemas.subschema_spec import SUBSCHEMAS
                labels = set(ALIASES.get(category, {})) | {k.replace('_', ' ') for k in SUBSCHEMAS.get(category, {})}
                meaningful = text
                if labels:
                    meaningful = re.sub(r'(?<!\w)(?:' + '|'.join(re.escape(k) for k in sorted(labels, key=len, reverse=True))
                                        + r')\s*[:=]\s*', '', text, flags=re.I)
                if re.search(r'\w', meaningful):
                    from local_api.services.local_completion import explicit_category
                    recognizable = explicit_category(text)
                    unresolved.append({'source_id': sid, 'source_element_index': block.source_element_index,
                        'start': block.start + start, 'end': block.start + end, 'text': text, 'section': category,
                        'recognizable_category': recognizable,
                        'local_reason': block.reason,
                        'reason': 'section_unassigned' if category is None else
                                  'recognizable_field_not_mapped' if recognizable else 'record_or_field_association_not_established'})
            start = end + 1
    conflicts = []
    for sid, values in claims.items():
        for i, left in enumerate(values):
            for right in values[i+1:]:
                if max(left[0], right[0]) >= min(left[1], right[1]): continue
                if compatible_claims(left, right): continue
                conflicts.append({'source_id': sid, 'fields': [left[5], right[5]], 'reason': 'overlapping_values_in_unrelated_fields'})
    return {'version': 1, 'source_intervals_valid': True, 'semantic_correctness_verified': False,
            'mapped_intervals': [{'source_id': sid, 'source_element_index': inventory[sid][0].source_element_index,
                'start': inventory[sid][0].start + claim[0], 'end': inventory[sid][0].start + claim[1],
                'field': claim[5]} for sid, values in claims.items() for claim in values],
            'meaningful_unmapped_fragments': len(unresolved), 'unassigned_source_fragments': sum(r['section'] is None for r in unresolved),
            'recognized_but_unmapped_fragments': sum(bool(r['recognizable_category']) for r in unresolved),
            'conflicting_field_overlaps': conflicts, 'unmapped': unresolved,
            'non_content_artifacts': artifacts, 'heading_source_ids': headings,
            'all_meaningful_content_mapped': not unresolved and not conflicts,
            'all_meaningful_content_accounted_for': True,
            'interpretation': 'Every unmapped fragment retains exact source offsets and an explicit review reason; coverage is not proof of correct associations.'}
