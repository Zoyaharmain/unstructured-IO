"""Canonical consumer export, kept separate from source-bound validation output."""
from copy import deepcopy


def standardized_export(response):
    value=response.model_dump() if hasattr(response,'model_dump') else response
    if not value.get('standardized_data'):
        raise ValueError('Standardized data is required for canonical export')
    def clean(item):
        if isinstance(item,dict):return {k:clean(v) for k,v in item.items() if not k.startswith('raw_')}
        if isinstance(item,list):return [clean(v) for v in item]
        return item
    data = clean(deepcopy(value['standardized_data']))
    metadata = deepcopy(value.get('standardization_metadata', {}))
    diagnostic_keys = ('duration_is_approximate', 'duration_as_of', 'duration_status',
                       'start_date_iso', 'end_date_iso', 'start_date_precision', 'end_date_precision')
    order = ('company', 'role', 'location', 'start_date', 'end_date', 'is_current',
             'duration', 'duration_months', 'responsibilities', 'technologies')
    calculations = []
    for index, job in enumerate(data.get('experience', [])):
        calculations.append({'record_path': f'data.experience[{index}]',
                             **{key: job.pop(key) for key in diagnostic_keys if key in job}})
        data['experience'][index] = {**{key: job[key] for key in order if key in job},
                                     **{key: item for key,item in job.items() if key not in order}}
    metadata['experience_calculations'] = calculations
    return {
        'export_type':'standardized_resume',
        'schema_version':value.get('standardization_metadata',{}).get('schema_version','1.1.0'),
        'source':value.get('source'),
        'data':data,
        'standardization_metadata':metadata,
        'validation_status':deepcopy(value.get('validation_status',{})),
        'warnings':deepcopy(value.get('warnings',[])),
        'source_evidence':{k:deepcopy(value[k]) for k in ('data','section_schemas','meta','raw_sections','field_index') if k in value},
    }
