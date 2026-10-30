import json
from copy import deepcopy
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionRequest
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.resume_sections import build_sections
from local_api.services.schema_mapping import map_schema
from local_api.services.llm_schema_mapping import map_with_field_review, local_section_payload, recover_literal_lists, parse_review
from local_api.services.llm_section_review import ReviewSettings
from local_api.schemas.sections import SectionBlock, SectionResponse


def fixture():
    texts=['Delivered global program improvements.', 'Reduced operating costs.', 'Skills: Program Governance · Vendor Management']
    elements=[ExtractedElement(type='ListItem' if i<2 else 'NarrativeText',text=t,page_number=1,metadata={}) for i,t in enumerate(texts)]
    blocks=[SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=1,lane='left',assignment='heading_context',reason='fixture') for i,t in enumerate(texts)]
    sections=SectionResponse(status='provisional',warnings=[],metadata={},needs_review=[],sections=build_sections({'awards':blocks[:2],'skills':blocks[2:]},elements))
    request=SchemaMappingRequest(elements=elements,sections=sections)
    return request,map_schema(request)


def test_actual_reviewed_path_keeps_source_lists_when_provider_returns_empty_fields():
    request,local=fixture()
    def transport(settings,messages):
        categories={s['category'] for s in json.loads(messages[1]['content'])['sections']}
        rows=local_section_payload(local,categories)
        for row in rows:
            for record in row['records']:
                for name in record['fields']:
                    record['fields'][name]=[]
                    record['missing'][name]='not_stated'
        return json.dumps({'sections':rows})
    mapped=map_with_field_review(request,settings=ReviewSettings(enabled=True,api_key='offline-test'),transport=transport)
    awards=next(s for s in mapped.section_schemas if s.category=='awards')
    assert len(awards.records)==2
    assert all(next(a for a in r.attributes if a.name=='name').items for r in awards.records)
    assert {'Program Governance','Vendor Management'} <= set(mapped.data.skills.all_skills)
    assert mapped.meta['field_review']['evidence_repairs']


def test_ambiguous_fields_are_not_overridden_and_foreign_sources_are_not_used():
    request,local=fixture()
    payload={'sections':local_section_payload(local,{'awards','skills'})}
    for row in payload['sections']:
        for record in row['records']:
            name='name' if row['category']=='awards' else 'all_skills'
            record['fields'][name]=[]
            record['missing'][name]='ambiguous'
    before=deepcopy(payload)
    assert recover_literal_lists(payload,request.sections,local)==[]
    assert payload==before
    parse_review(json.dumps(payload),request.sections)
