"""Validate shapes before normalization; retain unsupported values for review."""
from copy import deepcopy
import math
from local_api.vendor.handoff_schema.models import ResumeSchema
from local_api.services.standardization.contracts import StandardizationWarning


EXTRA_SECTIONS = ('awards', 'achievements', 'publications', 'volunteering', 'interests', 'references', 'additional_sections')


def prepare_input(data):
    source = data.model_dump() if hasattr(data, 'model_dump') else deepcopy(data)
    warnings, retained = [], []
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Nonfinite JSON numbers are not supported')
        if isinstance(value, dict):
            for item in value.values(): finite(item)
        if isinstance(value, list):
            for item in value: finite(item)
    finite(source)
    if not isinstance(source, dict):
        raise ValueError('Resume data must be an object')

    def issue(path, value, message):
        warnings.append(StandardizationWarning(field=path, warning_type='invalid_input_type',
            severity='review_required', original_value=value, message=message))
        retained.append({'category': 'unresolved_input', 'path': path, 'value': value})

    schema = ResumeSchema.model_json_schema()
    definitions = schema.get('$defs', {})

    def convert(value, spec, path):
        if '$ref' in spec:
            spec = definitions[spec['$ref'].split('/')[-1]]
        if 'anyOf' in spec:
            spec = next((s for s in spec['anyOf'] if s.get('type') != 'null'), {})
        kind = spec.get('type')
        if kind == 'object':
            if value is None: value = {}
            if not isinstance(value, dict):
                issue(path, value, 'Expected an object; original retained for review.')
                value = {}
            properties = spec.get('properties', {})
            result = {key: convert(value.get(key), rule, f'{path}.{key}' if path else key)
                      for key, rule in properties.items()}
            consumer_fields = set()
            if path.startswith('experience[') and path.endswith(']'):
                consumer_fields = {'is_current', 'stated_duration', 'duration_months'}
                if 'stated_duration' in value:
                    result['duration'] = convert(value['stated_duration'], {'type': 'string'}, path + '.stated_duration')
                if 'is_current' in value:
                    if isinstance(value['is_current'], bool): result['is_current'] = value['is_current']
                    else: issue(path + '.is_current', value['is_current'], 'Expected a boolean current indicator.')
                if 'duration_months' in value:
                    result['provided_duration_months'] = convert(value['duration_months'], {'type': 'number'}, path + '.duration_months')
            for key, item in value.items():
                if key not in properties and key not in consumer_fields and item not in (None, '', [], {}):
                    retained.append({'category': 'additional_information', 'path': f'{path}.{key}' if path else key, 'value': item})
            return result
        if kind == 'array':
            if value is None: return []
            if not isinstance(value, list):
                issue(path, value, 'Expected an array; scalar was not split into characters or guessed as a record.')
                return []
            result = []
            item_spec = spec.get('items', {})
            for i, item in enumerate(value):
                item_path = f'{path}[{i}]'
                if '$ref' in item_spec and not isinstance(item, dict):
                    issue(item_path, item, 'Expected a record object; original retained for review.')
                    continue
                converted = convert(item, item_spec, item_path)
                if converted is not None: result.append(converted)
            return result
        if kind == 'number':
            if value is None: return None
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
                return value
            issue(path, value, 'Expected a finite nonnegative number; original retained for review.')
            return None
        if value is None: return None
        if isinstance(value, str): return value
        issue(path, value, 'Expected text; original retained for review.')
        return None

    # Consumer date names are accepted without changing the source-bound legacy schema.
    working = deepcopy(source)
    for category, aliases in {'education': {'start_date': 'start_year', 'end_date': 'graduation_year'},
                              'certifications': {'issue_date': 'issue_year'}}.items():
        records = working.get(category)
        if not isinstance(records, list): continue
        for i, row in enumerate(records):
            if not isinstance(row, dict): continue
            for new, old in aliases.items():
                if new in row:
                    if row.get(old) not in (None, row[new]):
                        issue(f'{category}[{i}].{new}', row[new], 'Conflicting date aliases; no date selected.')
                        row[old] = None
                    else: row[old] = row[new]
                    row.pop(new)
    # Exported totals are derived; retain the source claim on reprocessing.
    if 'stated_total_experience_years' in working:
        working['total_experience_years'] = working.pop('stated_total_experience_years')
    extras = {key: working.pop(key, []) for key in EXTRA_SECTIONS}
    result = convert(working, schema, '')
    # Legacy required strings remain compatible; consumer export uses null for blanks.
    for key in ('full_name', 'email', 'phone'): result['contact'][key] = result['contact'][key] or ''
    for category, required in {'experience': ('company', 'role'), 'education': ('institution', 'degree'),
                               'projects': ('name',), 'certifications': ('name',)}.items():
        for row in result[category]:
            for key in required: row[key] = row[key] or ''
    for key, value in extras.items():
        if value is None: value = []
        if not isinstance(value, list):
            issue(key, value, 'Expected an array of additional records; original retained for review.')
            value = []
        valid = []
        for i, item in enumerate(value):
            if isinstance(item, (str, dict)): valid.append(item)
            else: issue(f'{key}[{i}]', item, 'Expected a text or object record; original retained for review.')
        result[key] = valid
    result['additional_sections'].extend(retained)
    return result, warnings
