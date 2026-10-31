"""Versioned consumer projection; full processing evidence is opt-in."""
from copy import deepcopy
from local_api.services.standardization.consumer import ConsumerResume

DIAGNOSTICS = ('duration_is_approximate', 'duration_as_of', 'duration_status',
               'start_date_iso', 'end_date_iso', 'start_date_precision', 'end_date_precision')


def standardized_export(response, *, include_audit=False):
    value = response.model_dump() if hasattr(response, 'model_dump') else response
    if not value.get('standardized_data'):
        raise ValueError('Standardized data is required for canonical export')
    def clean(item):
        if isinstance(item, dict):
            return {k: deepcopy(v) if k in {'details', 'additional_sections'} else clean(v) for k, v in item.items()}
        if isinstance(item, list): return [clean(v) for v in item]
        return None if isinstance(item, str) and not item.strip() else item
    raw = value['standardized_data']
    data = clean(deepcopy(raw))
    # Remove only known internal record fields, never arbitrary source detail keys.
    for category in ('contact', 'experience', 'education', 'certifications', 'projects'):
        records = [data[category]] if category == 'contact' else data[category]
        for record in records:
            for key in list(record):
                if key.startswith('raw_'): record.pop(key)
    metadata = deepcopy(value.get('standardization_metadata', {}))
    calculations = []
    for i, job in enumerate(data['experience']):
        calculations.append({'record_path': f'data.experience[{i}]',
                             **{key: job.pop(key) for key in DIAGNOSTICS if key in job}})
        job['stated_duration'] = raw['experience'][i].get('raw_duration')
    data['contact'].pop('phone_e164', None)
    for row in data['education']:
        row['start_date'] = row.pop('start_year')
        row['end_date'] = row.pop('graduation_year')
        row.pop('start_year_iso', None)
        row.pop('graduation_year_iso', None)
    for row in data['certifications']:
        row['issue_date'] = row.pop('issue_year')
        row.pop('issue_year_iso', None)
    metadata['experience_calculations'] = calculations
    metadata['experience_summary'] = {key: data.pop(key) for key in (
        'calculated_experience_years', 'calculated_experience_complete', 'calculated_experience_is_approximate', 'experience_overlap_detected')}
    data = ConsumerResume.model_validate(data).model_dump()
    result = {'export_type': 'standardized_resume', 'schema_version': '2.0.0',
              'source': value.get('source'), 'data': data,
              'validation_status': deepcopy(value.get('validation_status', {})),
              'standardization_metadata': metadata,
              'warnings': deepcopy(value.get('warnings', []))}
    if include_audit:
        # One source bundle, rather than duplicated field-index/raw-section/meta trees.
        result['audit'] = {'standardization_metadata': metadata,
                           'warnings': deepcopy(value.get('warnings', [])),
                           'source_evidence': {k: deepcopy(value[k]) for k in ('data', 'section_schemas', 'raw_sections', 'meta') if k in value}}
    return result
