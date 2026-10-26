"""Describe missing mappings using source candidates, never inferred values."""
import re

from local_api.services.record_subfields import labelled_fields


def complete_field_statuses(statuses, sections, data, scope, bindings, reviews, warnings):
    all_blocks = [b for s in sections.sections for b in s.blocks] + sections.needs_review

    def state(value, name, blocks, category, reasons=()):
        if scope.get('candidate_resume') is False:
            return 'not_applicable'
        if value is not None and value != '' and value != []:
            return 'present_and_extracted'
        if any(f'Conflicting explicit labels for {name}.' in reason for reason in reasons):
            return 'present_but_ambiguous'
        if labelled_fields(category, blocks).get(name):
            return 'present_but_unmapped'
        if any('\x00' in b.text or '\ufffd' in b.text for b in blocks):
            return 'extraction_failed'
        return None

    contact = data.contact.model_dump() | {
        'professional_title': data.professional_title,
    }
    for name, value in contact.items():
        path = name if name == 'professional_title' else 'contact.' + name
        detected = state(value, name, all_blocks, 'personal_information', warnings)
        if detected:
            statuses[path] = detected
    # Track every child, including optional fields, within its owning entry.
    for section in sections.sections:
        category = section.category
        if category not in bindings:
            continue
        by_id = {r['entry_id']: r for r in reviews if r['category'] == category}
        for entry in section.entries:
            index = bindings[category].get(entry.entry_id)
            if index is None:
                continue
            blocks = [section.blocks[i] for i in entry.block_indices]
            reasons = by_id[entry.entry_id]['review_reasons']
            record = getattr(data, category)[index]
            for name, value in record.model_dump().items():
                path = f'{category}[{index}].{name}'
                statuses[path] = state(value, name, blocks, category, reasons) or 'absent_in_source'
            # A blank required child with unresolved source cannot establish
            # absence; its source card remains available for recovery/review.
            for name in ('company', 'role') if category == 'experience' else ('degree', 'institution') if category == 'education' else ():
                path = f'{category}[{index}].{name}'
                source_field = {'company': 'employer', 'role': 'title', 'degree': 'qualification'}.get(name, name)
                if statuses[path] == 'absent_in_source' and entry.fields.get(source_field):
                    statuses[path] = 'present_but_unmapped'
    for category, values in (('skills', data.skills.all_skills), ('languages', data.languages)):
        present = any(s.category == category and any(b.text.strip() and b.assignment not in {'section_heading', 'structural_heading'} for b in s.blocks) for s in sections.sections)
        statuses[category] = ('not_applicable' if scope.get('candidate_resume') is False else
                              'present_and_extracted' if values else
                              'present_but_unmapped' if present else 'absent_in_source')
    text = '\n'.join(b.text for b in all_blocks)
    if data.total_experience_years is None and re.search(r'\b\d+(?:\.\d+)?\s*\+?\s*years?\b', text, re.I):
        if scope.get('candidate_resume') is not False:
            statuses['total_experience_years'] = 'present_but_unmapped'
