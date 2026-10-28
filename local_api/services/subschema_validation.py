"""Source-aware hierarchy validation and deterministic record-preserving queries."""
import re
from local_api.services.source_fragments import contiguous_support, citations
from local_api.schemas.subschemas import SectionSchema
from local_api.schemas.subschema_spec import SUBSCHEMAS, REPEATED
from local_api.services.schema_diagnostics import fail


def source_id(block):
    return f'e{block.source_element_index}:{block.start}:{block.end}'


def validate_hierarchy(hierarchy, sections):
    """Fail closed on invalid structure, citations or cross-record evidence."""
    parsed = [SectionSchema.model_validate(s.model_dump() if isinstance(s, SectionSchema) else s) for s in hierarchy]
    if len({s.category for s in parsed}) != len(parsed):
        fail('parent_schema_validation', 'duplicate_parent', ('section_schemas',))
    parents = {s.category: s for s in sections.sections}
    global_inventory={source_id(b):b.text for s in sections.sections for b in s.blocks}
    global_inventory.update({source_id(b):b.text for b in sections.needs_review})
    for pi, parent in enumerate(parsed):
        parent_path = ('section_schemas', pi)
        section = parents.get(parent.category)
        blocks = section.blocks if section else sections.needs_review if parent.category == 'needs_review' else []
        inventory = {source_id(b): b.text for b in blocks}
        ownership = {e.entry_id: {source_id(section.blocks[i]) for i in e.block_indices} for e in section.entries} if section else {}
        for residual in parent.residual_blocks:
            if inventory.get(residual.source_id) != residual.quote:
                fail('source_evidence_validation', 'invalid_residual', parent_path)
        for ri, record in enumerate(parent.records):
            record_path = parent_path + ('records', ri)
            allowed = set(record.source_ids)
            if not allowed or not allowed <= inventory.keys():
                fail('record_ownership_validation', 'foreign_record_source', record_path + ('source_ids',))
            if parent.category in REPEATED and allowed != ownership.get(record.record_id):
                fail('record_ownership_validation', 'record_owner_mismatch', record_path + ('source_ids',))
            for ai, field in enumerate(record.attributes):
                field_path = record_path + ('attributes', ai)
                for vi, item in enumerate(field.items):
                    value_path = field_path + ('items', vi)
                    for ref in item.evidence:
                        if ref.source_id not in allowed or ref.quote not in inventory[ref.source_id]:
                            fail('source_evidence_validation', 'invalid_or_cross_record_quote', value_path + ('evidence',), field.name,
                                 evidence_analysis={'item_index': vi, 'value_length': len(str(item.value)),
                                     'evidence_count': len(item.evidence), 'all_quotes_valid': False,
                                     'literal_in_record': any(str(item.value).casefold() in inventory[sid].casefold() for sid in allowed),
                                     'evidence_source_ids': [q.source_id for q in item.evidence],
                                     'evidence_quote_lengths': [len(q.quote) for q in item.evidence]})
                    if isinstance(item.value, str):
                        if not any(item.value.casefold() in ref.quote.casefold() for ref in item.evidence) and not contiguous_support(item.value, item.evidence, global_inventory):
                            own_blocks = [b for b in blocks if source_id(b) in allowed]
                            fail('source_evidence_validation', 'unsupported_value', value_path + ('value',), field.name,
                                 evidence_analysis={'item_index': vi, 'value_length': len(item.value),
                                     'evidence_count': len(item.evidence), 'all_quotes_valid': True,
                                     'evidence_source_ids': [ref.source_id for ref in item.evidence],
                                     'evidence_quote_lengths': [len(ref.quote) for ref in item.evidence],
                                     'literal_in_record': bool(citations(item.value, own_blocks)),
                                     'whitespace_match_in_record': bool(citations(item.value, own_blocks, flexible_whitespace=True))})
                    else:
                        if not any(re.search(r'(?<![\d.])'+re.escape(format(item.value, 'g'))+r'(?![\d.])', ref.quote) for ref in item.evidence):
                            fail('source_evidence_validation', 'unsupported_number', value_path + ('value',), field.name)
    return parsed


def query_subschemas(hierarchy, path, record_id=None):
    """Resolve parent.child; each result represents one record, even when missing."""
    parts = path.split('.')
    if len(parts) != 2 or parts[0] not in SUBSCHEMAS or parts[1] not in SUBSCHEMAS[parts[0]]:
        raise ValueError('Unknown parent.child path')
    parent, child = parts
    matches = []
    for si, section in enumerate(hierarchy):
        if section.category != parent:
            continue
        for ri, record in enumerate(section.records):
            if record_id is not None and record.record_id != record_id:
                continue
            for ai, attribute in enumerate(record.attributes):
                if attribute.name != child:
                    continue
                pointer = f'/section_schemas/{si}/records/{ri}/attributes/{ai}'
                matches.append({'parent': parent, 'child': child, 'field_path': f'{parent}[{ri}].{child}',
                                'record_id': record.record_id, 'pointer': pointer,
                                'status': attribute.status, 'review_reasons': record.review_reasons,
                                'items': [dict(item.model_dump(), pointer=f'{pointer}/items/{ii}/value') for ii, item in enumerate(attribute.items)]})
    return matches


def build_field_index(hierarchy):
    """Stable predefined lookup keys, including absent parents and empty fields.

    Values retain record identity; pointers resolve against the full mapping
    response's section_schemas, never a flattened cross-record collection.
    """
    return {f'{parent}.{child}': query_subschemas(hierarchy, f'{parent}.{child}')
            for parent, children in SUBSCHEMAS.items() for child in children}
