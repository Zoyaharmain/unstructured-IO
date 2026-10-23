"""Source-aware hierarchy validation and deterministic record-preserving queries."""
import re
from local_api.services.source_fragments import contiguous_support
from local_api.schemas.subschemas import SectionSchema
from local_api.schemas.subschema_spec import SUBSCHEMAS, REPEATED


def source_id(block):
    return f'e{block.source_element_index}:{block.start}:{block.end}'


def validate_hierarchy(hierarchy, sections):
    """Fail closed on invalid structure, citations or cross-record evidence."""
    parsed = [SectionSchema.model_validate(s.model_dump() if isinstance(s, SectionSchema) else s) for s in hierarchy]
    if len({s.category for s in parsed}) != len(parsed):
        raise ValueError('Duplicate parent schema')
    parents = {s.category: s for s in sections.sections}
    global_inventory={source_id(b):b.text for s in sections.sections for b in s.blocks}
    global_inventory.update({source_id(b):b.text for b in sections.needs_review})
    for parent in parsed:
        section = parents.get(parent.category)
        blocks = section.blocks if section else sections.needs_review if parent.category == 'needs_review' else []
        inventory = {source_id(b): b.text for b in blocks}
        ownership = {e.entry_id: {source_id(section.blocks[i]) for i in e.block_indices} for e in section.entries} if section else {}
        for residual in parent.residual_blocks:
            if inventory.get(residual.source_id) != residual.quote:
                raise ValueError('Invalid residual source')
        for record in parent.records:
            allowed = set(record.source_ids)
            if not allowed or not allowed <= inventory.keys():
                raise ValueError('Record has foreign or missing source IDs')
            if parent.category in REPEATED and allowed != ownership.get(record.record_id):
                raise ValueError('Record does not preserve supplied entry ownership')
            for field in record.attributes:
                for item in field.items:
                    for ref in item.evidence:
                        if ref.source_id not in allowed or ref.quote not in inventory[ref.source_id]:
                            raise ValueError('Invalid or cross-record quote')
                    if isinstance(item.value, str):
                        if not any(item.value.casefold() in ref.quote.casefold() for ref in item.evidence) and not contiguous_support(item.value, item.evidence, global_inventory):
                            raise ValueError('Value is unsupported by its own evidence')
                    else:
                        if not any(re.search(r'(?<![\d.])'+re.escape(format(item.value, 'g'))+r'(?![\d.])', ref.quote) for ref in item.evidence):
                            raise ValueError('Number is unsupported by its own evidence')
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
