"""Apply the existing typed mapper within sections, using record-local evidence.

No extraction, reclustering, provider calls, or cross-record citation inheritance.
Unsupported values remain absent from the nested representation.
"""
import re
from local_api.schemas.subschema_spec import SUBSCHEMAS, REPEATED, valid_field_shape
from local_api.services.education_subfields import refine_education
from local_api.services.record_subfields import refine_record
from local_api.services.source_fragments import citations, contiguous_support
from local_api.services.list_fields import language_rows
from local_api.services.subschema_validation import validate_hierarchy
from local_api.schemas.subschemas import (
    SourceQuote, AttributeValue, Attribute, SubschemaRecord, SectionSchema,
)


def sid(block):
    return f'e{block.source_element_index}:{block.start}:{block.end}'


def build_subschemas(sections, data, scope):
    output = []
    inventory={sid(b):b.text for s in sections.sections for b in s.blocks}
    inventory.update({sid(b):b.text for b in sections.needs_review})
    grouped = REPEATED
    extra_fields = {k: tuple(v) for k, v in SUBSCHEMAS.items() if k not in grouped | {'personal_information', 'summary', 'skills', 'needs_review'}}
    for section in sections.sections:
        used = set()
        records = []
        category = section.category
        candidates = [b for b in section.blocks if b.text.strip() and b.assignment not in {'section_heading', 'structural_heading'}]

        def attribute(name, value, allowed, uncertain=False):
            items = []
            for item in value if isinstance(value, list) else [value]:
                if item is None or (isinstance(item, str) and not item.strip()):
                    continue
                # The legacy name helper can mistake an email/contact line for a
                # name. Keep legacy data intact, but do not propagate that error.
                if not valid_field_shape(category, name, item):
                    continue
                # Each scalar/list item gets its own exact source match and quote.
                literal = format(item, 'g') if isinstance(item, (int, float)) else str(item)
                refs = [SourceQuote(**ref) for ref in citations(item, allowed)]
                if refs and not any(str(item).casefold() in r.quote.casefold() for r in refs) and not contiguous_support(item,refs,inventory):refs=[]
                if refs:
                    # A cited fragment does not consume the rest of its source block.
                    used.update(sid(b) for b in allowed if any(
                        ref.source_id == sid(b) and ref.quote.strip() == b.text.strip() for ref in refs))
                    items.append(AttributeValue(value=item, evidence=refs,
                                 status='needs_review' if uncertain else 'source_supported'))
            return Attribute(name=name, items=items, status='mapped' if items else 'unresolved')

        if scope.get('candidate_resume') is not False:
            if category in grouped:
                for index, entry in enumerate(section.entries):
                    mapped = getattr(data, category)
                    if index >= len(mapped):
                        continue
                    record = mapped[index]
                    allowed = [section.blocks[i] for i in entry.block_indices]
                    uncertain = entry.relationship_status == 'needs_review' or bool(entry.review_reasons)
                    values = record.model_dump()
                    reasons = list(entry.review_reasons)
                    if category == 'education':
                        _, refinement_reasons = refine_education(values, allowed)
                        reasons.extend(refinement_reasons)
                    if category == 'experience' and re.search(r'\b(?:trainee|research|training)\b', '\n'.join(b.text for b in allowed), re.I):
                        reasons.append('Training/research content requires employment association review.')
                    _, refinement_reasons = refine_record(category, values, allowed, header_fields=(
                        {'company' if field == 'employer' else 'role' if field == 'title' else field for field in entry.fields}
                        if entry.fields else None))
                    reasons.extend(refinement_reasons)
                    uncertain = uncertain or bool(reasons)
                    attrs = [attribute(name, value, allowed, uncertain) for name, value in values.items()]
                    records.append(SubschemaRecord(record_id=entry.entry_id, source_ids=[sid(b) for b in allowed], attributes=attrs,
                                   review_reasons=reasons))
            elif category in {'personal_information', 'summary', 'skills'}:
                values = data.contact.model_dump() if category == 'personal_information' else (
                    data.skills.model_dump() if category == 'skills' else {'statements': [b.text for b in candidates], 'total_experience_years': data.total_experience_years})
                if category == 'personal_information':
                    values['professional_title'] = data.professional_title
                reasons = []
                if category == 'summary' and values['total_experience_years'] is not None and any(
                    re.search(r'\b(?:over|around|approximately|more than)\b|\d\s*\+', b.text, re.I) for b in candidates
                ):
                    reasons.append('Experience years are approximate or a lower bound; inspect the source qualifier.')
                if candidates:
                    records.append(SubschemaRecord(record_id=category, source_ids=[sid(b) for b in candidates],
                        attributes=[attribute(k, v, candidates, bool(reasons)) for k, v in values.items()], review_reasons=reasons))
            elif category == 'languages':
                for language, level, block in language_rows(candidates):
                    records.append(SubschemaRecord(record_id=f'languages-{len(records)+1}', source_ids=[sid(block)],
                        attributes=[attribute('language',language,[block]),attribute('proficiency',level,[block])],
                        review_reasons=[] if level else ['Proficiency is not stated; no level inferred.']))
                for block in candidates:
                    remainder = re.sub(r'^\s*(?:spoken\s+)?languages?\s*:\s*', '', block.text, flags=re.I)
                    for language, level, source in language_rows([block]):
                        for value in (language,level):
                            if value:remainder = re.sub(re.escape(value),'',remainder,count=1,flags=re.I)
                    if not re.sub(r'[\s\u2022\u25cf\u25aa*,:;|()\-\u2013\u2014]', '', remainder):used.add(sid(block))
            elif category in extra_fields:
                # Preserve supplied record boundaries. Without boundaries, each block is
                # an independent item; adjacency alone does not establish association.
                groups = [(entry.entry_id, [section.blocks[i] for i in entry.block_indices], list(entry.review_reasons), entry.relationship_status == 'needs_review') for entry in section.entries]
                if not groups:
                    groups = [(sid(b), [b], [], False) for b in candidates]
                for record_id, allowed, reasons, uncertain in groups:
                    fields = extra_fields[category]
                    values = {name: None for name in fields}
                    # A simple item is a literal statement; compound records need labels.
                    if category == 'interests':
                        values['interest'] = [b.text for b in allowed]
                    values, refinement_reasons = refine_record(category, values, allowed)
                    reasons.extend(refinement_reasons)
                    if any(v is None for v in values.values()):
                        reasons.append('Unlabelled compound information requires source review.')
                    records.append(SubschemaRecord(record_id=record_id, source_ids=[sid(b) for b in allowed],
                        attributes=[attribute(k, v, allowed, uncertain or bool(reasons)) for k, v in values.items()],
                        review_reasons=reasons))
        output.append(SectionSchema(category=category, label=section.label, records=records,
                      residual_blocks=[SourceQuote(source_id=sid(b), quote=b.text) for b in section.blocks if sid(b) not in used]))
    if sections.needs_review:
        output.append(SectionSchema(category='needs_review', label='Unassigned source blocks', records=[],
                      residual_blocks=[SourceQuote(source_id=sid(b), quote=b.text) for b in sections.needs_review]))
    return validate_hierarchy(output, sections)
