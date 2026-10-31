"""Fixed supplemental record shape; unknown details are preserved explicitly."""
from copy import deepcopy
from local_api.services.standardization.contracts import StandardizationWarning


def normalize_additional(records, category, date_value, url_value, warnings):
    result = []
    for i, source in enumerate(records):
        record = {'name': None, 'description': None, 'organization': None,
                  'date': None, 'start_date': None, 'end_date': None, 'url': None,
                  'outcomes': [], 'details': {}}
        if isinstance(source, str):
            record['description'] = source.strip() or None
        else:
            values = deepcopy(source)
            existing_details = values.pop('details', {})
            if not isinstance(existing_details, dict): existing_details = {'original_details': existing_details}
            for key in ('name', 'title', 'organization', 'issuer', 'publisher', 'description', 'date', 'start_date', 'end_date', 'url'):
                if values.get(key) in (None, ''): values.pop(key, None)
            for target, aliases in {'name': ('name', 'title'), 'organization': ('organization', 'issuer', 'publisher'),
                                    'description': ('description',)}.items():
                populated = [(k, values[k]) for k in aliases if isinstance(values.get(k), str) and values[k].strip()]
                if len(populated) == 1:
                    key, item = populated[0]
                    record[target] = item.strip()
                    values.pop(key)
                elif len(populated) > 1:
                    if len({v.strip() for _, v in populated}) == 1:
                        record[target] = populated[0][1].strip()
                        for key, _ in populated: values.pop(key)
                    else:
                        warnings.append(StandardizationWarning(field=f'{category}[{i}].{target}',
                            warning_type='conflicting_field_values', severity='review_required',
                            original_value=dict(populated), message='Conflicting aliases retained in details; no value selected.'))
                # Conflicting aliases remain in details; never choose one silently.
            for key in ('date', 'start_date', 'end_date'):
                raw = values.get(key)
                if isinstance(raw, str):
                    record[key] = date_value(raw, f'{category}[{i}].{key}')
                    values.pop(key)
            if isinstance(values.get('url'), str):
                record['url'] = url_value(values.pop('url'), f'{category}[{i}].url')
            if isinstance(values.get('outcomes'), list) and all(isinstance(v, str) for v in values['outcomes']):
                record['outcomes'] = values.pop('outcomes')
            if any(key in existing_details and existing_details[key] != item for key, item in values.items()):
                record['details'] = {'original_details': existing_details, 'unprojected_fields': values}
            else:
                record['details'] = {**existing_details, **values}
        result.append(record)
    return result
