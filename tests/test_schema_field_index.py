"""Named field lookup in serialized JSON retains definitions, records and quotes."""
import importlib.util
from pathlib import Path
from copy import deepcopy
from local_api.schemas.mapping import SchemaMappingResponse
from local_api.schemas.subschema_spec import SUBSCHEMAS
from local_api.services.schema_mapping import map_schema

spec=importlib.util.spec_from_file_location('field_index_fixture',Path(__file__).with_name('test_hierarchical_schema.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)


def test_serialized_fields_have_predefined_names_record_ids_and_resolvable_pointers():
    out=map_schema(fixture.example()).model_dump(mode='json')
    assert set(out['field_index'])=={f'{p}.{c}' for p,children in SUBSCHEMAS.items() for c in children}
    records=out['field_index']['education.institution']
    assert [r['record_id'] for r in records]==['education-0','education-1']
    assert records[0]['parent']=='education' and records[0]['child']=='institution'
    assert records[0]['field_path']=='education[0].institution'
    assert records[0]['items'][0]['value']=='Example University'
    assert records[0]['items'][0]['evidence'][0]['quote']=='Example University'
    for record in records:
        for item in record['items']:
            value=out
            for token in item['pointer'].split('/')[1:]:
                value=value[int(token)] if isinstance(value,list) else value[token]
            assert value==item['value']
    assert out['field_index']['experience.company']==[]
    assert out['subschema_definitions']['parents']==SUBSCHEMAS


def test_missing_fields_remain_named_and_unresolved():
    out=map_schema(fixture.education_request(['M.Sc. Computer Science'])).model_dump(mode='json')
    assert out['field_index']['education.institution'][0]['items']==[]
    assert out['field_index']['education.institution'][0]['status']=='unresolved'


def test_index_is_derived_and_cannot_override_data_or_registry():
    mapped=map_schema(fixture.example());before=deepcopy(mapped.data.model_dump())
    exported=mapped.model_dump(mode='json')
    exported['field_index']={'education.institution':'forged'}
    exported['subschema_definitions']['parents']['education']['invented']={}
    rebuilt=SchemaMappingResponse.model_validate(exported)
    assert rebuilt.data.model_dump()==before
    assert rebuilt.field_index['education.institution'][0]['items'][0]['value']=='Example University'
    assert 'invented' not in SUBSCHEMAS['education']
