"""Project validated section content without inventing record associations."""
from copy import deepcopy
import re
from local_api.services.standardization.contracts import StandardizationWarning
from local_api.services.standardization.validation import finalize_status

EXTRA = {'awards', 'publications', 'volunteering', 'interests', 'references'}


def mapping_input(mapped):
    value = mapped.model_dump() if hasattr(mapped, 'model_dump') else mapped
    data = deepcopy(value['data'])
    artifacts = {row['source_id'] for row in value.get('meta', {}).get('source_accounting', {}).get('outcomes', [])
                 if row['outcome'] == 'non_content_artifact'}
    additional = list(data.get('additional_sections', []))
    def leaves(item):
        if isinstance(item, dict):
            return [v for child in item.values() for v in leaves(child)]
        if isinstance(item, list):
            return [v for child in item for v in leaves(child)]
        return [format(item, 'g') if isinstance(item, (int, float)) else item] if item is not None else []
    for section in value.get('section_schemas', []):
        category = section['category']
        represented_values = leaves(data.get({'personal_information': 'contact'}.get(category, category), {}))
        if category == 'personal_information': represented_values += leaves(data.get('professional_title'))
        if category == 'summary': represented_values += leaves(data.get('total_experience_years'))
        records = []
        consumed = {}
        for record in section['records']:
            fields = {}
            for attr in record['attributes']:
                items = [v['value'] for v in attr['items']]
                from local_api.schemas.subschema_spec import SUBSCHEMAS
                multiple = SUBSCHEMAS[category][attr['name']]['multiple']
                fields[attr['name']] = items if multiple else items[0] if items else None
                for item in attr['items']:
                    for ref in item['evidence']:
                        literal = format(item['value'], 'g') if isinstance(item['value'], (int, float)) else item['value']
                        projected = category in EXTRA or any(isinstance(v, str) and literal in v for v in represented_values)
                        if literal in ref['quote'] and projected:
                            consumed.setdefault(ref['source_id'], []).append(literal)
            if any(v not in (None, [], '') for v in fields.values()): records.append(fields)
        if category in EXTRA:
            data[category] = records
        # Keep text outside exact field quotes visible as unresolved information.
        for ref in section['residual_blocks']:
            if ref['source_id'] in artifacts: continue
            text = ref['quote']
            mask = [False] * len(text)
            for quote in consumed.get(ref['source_id'], []):
                start = text.find(quote)
                if start >= 0:
                    mask[start:start + len(quote)] = [True] * len(quote)
            remainder = ''.join(c if not mask[i] else ' ' for i, c in enumerate(text)).strip()
            from local_api.services.record_subfields import ALIASES
            from local_api.schemas.subschema_spec import SUBSCHEMAS
            labels = set(ALIASES.get(category, {})) | {k.replace('_', ' ') for k in SUBSCHEMAS[category]}
            meaningful = remainder
            if labels:
                meaningful = re.sub(r'(?<!\w)(?:' + '|'.join(re.escape(k) for k in sorted(labels, key=len, reverse=True))
                                    + r')\s*[:=]\s*', '', meaningful, flags=re.I)
            if not re.search(r'\w', meaningful): continue
            if remainder.casefold().strip(' :') in {category, section['label'].casefold().strip(' :')}:
                continue
            additional.append({'category': category, 'text': remainder, 'source_ids': [ref['source_id']],
                               'status': 'unresolved'})
    represented = {s['category'] for s in value.get('section_schemas', [])}
    for category, text in value.get('raw_sections', {}).items():
        if category not in represented and isinstance(text, str) and text.strip():
            additional.append({'category': category, 'text': text, 'status': 'unresolved'})
    data['additional_sections'] = additional
    return data


def attach_mapping_findings(mapped, warnings):
    result = mapped.meta.get('mapping_result', {})
    completeness = mapped.meta.get('completeness_check', {})
    if result.get('requires_review') or mapped.meta.get('missing_required_fields') or completeness.get('meaningful_unmapped_fragments') or completeness.get('conflicting_field_overlaps'):
        warnings.append(StandardizationWarning(field='mapping', warning_type='unresolved_mapping',
            severity='review_required', message='Source mapping has unresolved fields or associations; inspect mapping evidence.'))
    if mapped.standardized_data.additional_sections and not any(
            w.warning_type == 'unresolved_source_content' for w in warnings):
        warnings.append(StandardizationWarning(field='additional_sections', warning_type='unresolved_source_content',
            severity='review_required', message='Unassigned or partially mapped source content is retained in additional_sections.'))
    mapped.validation_status = finalize_status(warnings)
    mapped.warnings = warnings
