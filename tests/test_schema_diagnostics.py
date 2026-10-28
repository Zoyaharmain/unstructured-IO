"""No provider calls: classified failures, safe logs, fallback and UI semantics."""
import json
import subprocess
from copy import deepcopy
from pathlib import Path
import pytest
from local_api.services.llm_schema_mapping import map_with_field_review
from local_api.services import llm_schema_mapping as service
from local_api.services.llm_section_review import ReviewError
from test_llm_schema_mapping import fixture, configured


@pytest.mark.parametrize('kind,category,code', [
    ('json', 'json_parsing', 'invalid_json'),
    ('shape', 'response_model_validation', 'field_not_array'),
    ('parent', 'parent_schema_validation', 'batch_section_mismatch'),
    ('subschema', 'subschema_validation', 'scalar_multiple_values'),
    ('fields', 'subschema_validation', 'missing_or_unknown_fields'),
    ('status', 'subschema_validation', 'missing_source_status'),
    ('quote', 'source_evidence_validation', 'invalid_or_cross_record_quote'),
    ('value', 'source_evidence_validation', 'unsupported_value'),
    ('ownership', 'record_ownership_validation', 'overlapping_records'),
    ('typed', 'response_model_validation', 'string_type'),
])
def test_failure_categories_and_original_failure_survive_fallback(kind, category, code, monkeypatch, caplog):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, payload = fixture(); first = payload['sections'][0]['records'][0]
    sentinel = 'SECRET_PRIVATE_RESUME_AND_API_KEY'
    if kind == 'shape': first['fields']['company'] = {'value': sentinel}
    if kind == 'parent': payload['sections'] = []
    if kind == 'subschema': first['fields']['role'] *= 2
    if kind == 'fields': first['fields'][sentinel] = []
    if kind == 'status': first['missing'] = {}
    if kind == 'quote':
        first['fields']['company'][0]['value'] = sentinel
        first['fields']['company'][0]['evidence'][0]['quote'] = sentinel
        first['fields']['company'][0]['evidence'][0]['source_id'] = payload['sections'][0]['records'][1]['source_ids'][0]
    if kind == 'value': first['fields']['company'][0]['value'] = sentinel
    if kind == 'ownership': payload['sections'][0]['records'][1]['source_ids'] = first['source_ids']
    if kind == 'typed': first['fields']['company'][0]['evidence'][0]['quote'] = {sentinel: sentinel}
    content = 'invalid ' + sentinel if kind == 'json' else json.dumps(payload)
    baseline = service.map_schema(request)
    out = map_with_field_review(request, settings=configured(recovery_attempts=0), transport=lambda *_: content)
    assert out.data == baseline.data
    review = out.meta['field_review']; diagnostic = review['diagnostic']
    assert review['status'] == 'failed'
    assert out.meta['mapping_result'] == dict(out.meta['mapping_result'], status='fallback_used', usable=True, requires_review=True, fallback_used=True)
    assert diagnostic['category'] == category
    assert diagnostic['code'] == code
    assert diagnostic['exception_type']
    assert diagnostic['path'].startswith('/')
    assert diagnostic['validation_message']
    assert sentinel not in json.dumps(diagnostic)
    assert sentinel not in caplog.text
    assert 'Acme Ltd' not in caplog.text and 'Engineer |' not in caplog.text
    assert 'schema_mapping_failure' in caplog.text
    assert diagnostic['id'] in caplog.text


def test_production_returns_safe_reason_but_server_keeps_sanitized_details(monkeypatch, caplog):
    monkeypatch.setenv('RESUME_APP_ENV', 'production')
    request, _ = fixture()
    out = map_with_field_review(request, settings=configured(recovery_attempts=0), transport=lambda *_: 'bad JSON private-text')
    diagnostic = out.meta['field_review']['diagnostic']
    assert set(diagnostic) == {'id', 'category', 'code', 'validation_message', 'recovered'}
    assert diagnostic['code'] == 'invalid_json'
    assert 'private-text' not in json.dumps(diagnostic)
    assert 'JSONDecodeError' in caplog.text and 'invalid_json' in caplog.text
    assert 'private-text' not in caplog.text


def test_recovered_retry_keeps_history_without_claiming_fallback(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, payload = fixture(); responses = iter(['broken JSON', json.dumps(payload)])
    out = map_with_field_review(request, settings=configured(), transport=lambda *_: next(responses))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.meta['field_review']['diagnostics'][0]['category'] == 'json_parsing'
    assert out.meta['field_review']['diagnostics'][0]['recovered'] is True
    assert out.meta['mapping_result']['fallback_used'] is False
    # Missing required contact fields are review findings, not exceptions.
    assert out.meta['mapping_result']['status'] == 'needs_review'


@pytest.mark.parametrize('stage,expected', [('provider', 'provider_error'), ('configuration', 'configuration_error'), ('budget', 'request_budget'), ('commit', 'parent_schema_validation')])
def test_other_failure_stages_are_not_mislabeled(monkeypatch, stage, expected):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, payload = fixture()
    settings = configured(recovery_attempts=0)
    transport = lambda *_: json.dumps(payload)
    if stage == 'provider':
        def transport(*args): raise ReviewError('provider_unavailable')
    elif stage == 'configuration': settings = configured(timeout=0)
    elif stage == 'budget': settings = configured(max_input_chars=10)
    else:
        from local_api.vendor.handoff_schema.models import WorkExperience
        def bad_commit(*args): return WorkExperience.model_validate({'company': 'private'})
        monkeypatch.setattr(service, 'commit_review', bad_commit)
    out = map_with_field_review(request, settings=settings, transport=transport)
    assert out.meta['field_review']['diagnostic']['category'] == expected
    assert out.meta['mapping_result']['status'] == 'fallback_used'


def test_frontend_status_does_not_hide_failed_review_or_color_usable_fallback_red():
    script = """
const {schemaOutcome} = require('./local_api/static/schema-status.js');
const assert = require('node:assert/strict');
const fallback={success:true,meta:{field_review:{status:'failed',diagnostic:{category:'json_parsing'}},mapping_result:{status:'fallback_used'}}};
assert.equal(schemaOutcome(fallback,true).status,'fallback_used');
assert.equal(schemaOutcome(fallback,true).className,'status warning');
assert.equal(schemaOutcome(fallback,true).diagnostic.category,'json_parsing');
assert.equal(schemaOutcome({success:false,meta:{mapping_result:{status:'failed'}}},true).className,'status error');
assert.equal(schemaOutcome({success:true,meta:{missing_required_fields:['contact.email']}},false).status,'needs_review');
assert.equal(schemaOutcome({success:true,meta:{field_review:{status:'complete'}}},true).status,'success');
"""
    subprocess.run(['node', '-e', script], check=True)


def test_saved_abhilash_fallback_keeps_employers_and_education_in_their_source_cards():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.schemas.sections import SectionResponse
    from local_api.services.resume_sections import build_sections
    from local_api.services.schema_mapping import map_schema
    frozen = Path('reports/hierarchical-schema-all1541-20261023/documents/cc95699a4846fe868d07/source.json')
    source = json.loads(frozen.read_text())
    # Use current, archived line geometry where available; the frozen extraction
    # contains the user's two original complete education paragraphs.
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock
    elements = [ExtractedElement.model_validate(e) for e in source['extraction']['elements']]
    paragraphs = [(51, 'Woxsen School of Business ', 'Post Graduate Diploma in Management (PGDM) | 2015 – 2017'),
                  (52, 'Guru Nanak Dev Engineering College ', 'Bachelor of Engineering (B.E.) | 2010 – 2014')]
    blocks = []
    for line, institution, degree in paragraphs:
        assert elements[line].text == institution + degree
        elements[line].metadata['pdf_source_lines'] = [
            {'start': 0, 'end': len(institution), 'bbox': [.1, .1 + (line-51)*.1, .5, .11 + (line-51)*.1]},
            {'start': len(institution), 'end': len(elements[line].text), 'bbox': [.1, .12+(line-51)*.1, .6, .13+(line-51)*.1]}]
        for start, end in [(0, len(institution)), (len(institution), len(elements[line].text))]:
            blocks.append(SectionBlock(source_element_index=line, start=start, end=end, text=elements[line].text[start:end], page_number=3,
                assignment='heading_context', lane='left', reason='Source row'))
    education = build_sections({'education': blocks}, elements)[0]
    assert len(education.entries) == 2
    first, second = education.entries
    assert first.block_indices == [0, 1] and second.block_indices == [2, 3]
    from local_api.services.education_subfields import refine_education
    values, reasons = refine_education({'degree':'','institution':'','field_of_study':None,'start_year':None,'graduation_year':None,'grade_or_gpa':None}, blocks[:2])
    assert values['degree'] == 'Post Graduate Diploma'
    assert values['field_of_study'] == 'Management'
    assert values['start_year'] == '2015' and values['graduation_year'] == '2017'
    assert not reasons
    from local_api.services.record_relationships import field_kinds
    assert 'employer' not in field_kinds('development, template creation, setting up account in internal systems. Cut average setup time by roughly', 'experience')


def test_dictionary_free_employer_headers_are_not_replaced_by_department_names():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock, SectionResponse
    from local_api.services.resume_sections import build_sections
    from local_api.services.schema_mapping import map_schema
    companies = ['Morgan Stanley', 'Goldman Sachs', 'JPMorgan Chase & Co.', 'Acuity Knowledge Partners']
    elements = []; blocks = []
    for i, company in enumerate(companies):
        title = 'Senior Analyst — Private Wealth Management Reporting'
        text = company + ' ' + title
        y = .1 + i * .15
        element = ExtractedElement(type='Title', text=text, page_number=1, metadata={'pdf_source_lines': [
            {'start':0,'end':len(company)+1,'bbox':[.1,y,.5,y+.01],'bold':True},
            {'start':len(company)+1,'end':len(text),'bbox':[.1,y+.015,.6,y+.025],'bold':True}]})
        index = len(elements); elements.append(element)
        for start, end in [(0,len(company)+1),(len(company)+1,len(text))]:
            blocks.append(SectionBlock(source_element_index=index,start=start,end=end,text=text[start:end],page_number=1,lane='left',assignment='heading_context',reason='Source header'))
    sections = SectionResponse(status='provisional', sections=build_sections({'experience':blocks}, elements), needs_review=[], metadata={}, warnings=[])
    out = map_schema(SchemaMappingRequest(elements=elements, sections=sections))
    assert [record.company for record in out.data.experience] == companies


def test_typed_diagnostic_preserves_numeric_indexes_and_named_field(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, payload = fixture()
    payload['sections'][0]['records'][0]['fields']['company'][0]['evidence'][0]['quote'] = 123
    out = map_with_field_review(request, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(payload))
    diagnostic = out.meta['field_review']['diagnostic']
    assert diagnostic['field'] == 'company'
    assert diagnostic['path'] == '/sections/0/records/0/fields/company/items/0/evidence/0/quote'


def test_provider_missing_company_claim_is_checked_against_its_source(monkeypatch):
    request, payload = fixture()
    first = payload['sections'][0]['records'][0]
    first['fields']['company'] = []
    first['missing']['company'] = 'not_stated'
    out = map_with_field_review(request, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(payload))
    assert out.meta['field_review']['status'] == 'complete'
    assert 'diagnostic' not in out.meta['field_review']
    assert out.meta['mapping_result']['status'] == 'needs_review'
    assert out.meta['mapping_result']['fallback_used'] is False
    assert out.data.experience[0].company == 'Acme Ltd'
    assert 'experience[0].company' not in out.meta['missing_required_fields']


def test_child_type_failure_names_the_field_without_logging_its_value(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    request, payload = fixture()
    payload['sections'][0]['records'][0]['fields']['company'][0]['value'] = 12345
    out = map_with_field_review(request, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(payload))
    diagnostic = out.meta['field_review']['diagnostic']
    assert diagnostic['category'] == 'subschema_validation'
    assert diagnostic['code'] == 'string_child_type'
    assert diagnostic['field'] == 'company'
    assert '12345' not in json.dumps(diagnostic)


def test_frontend_separates_recovered_history_from_active_failure_and_review_findings():
    script = r"""
const {schemaOutcome} = require('./local_api/static/schema-status.js');
const assert = require('node:assert/strict');
const resolved = {id:'f9f226',category:'subschema_validation',code:'missing_source_status',recovered:true};
const good = {success:true,meta:{field_review:{status:'complete',diagnostics:[resolved]},mapping_result:{status:'success'}}};
let out = schemaOutcome(good,true);
assert.equal(out.status,'success');
assert.equal(out.diagnostic,null);
assert.deepEqual(out.recoveredDiagnostics,[resolved]);
assert.deepEqual(out.reviewReasons,[]);
const pending = structuredClone(good);
pending.meta.mapping_result.status='needs_review';
pending.meta.missing_required_fields=['contact.email'];
out=schemaOutcome(pending,true);
assert.equal(out.status,'needs_review');
assert.equal(out.diagnostic,null);
assert.ok(out.reviewReasons[0].includes('required field'));
const failed = structuredClone(good);
const active = {id:'active',category:'source_evidence_validation',recovered:false};
failed.meta.mapping_result.status='fallback_used';
failed.meta.field_review.status='failed';
failed.meta.field_review.diagnostics.push(active);
out=schemaOutcome(failed,true);
assert.equal(out.diagnostic.id,'active');
assert.equal(out.status,'fallback_used');
assert.deepEqual(out.recoveredDiagnostics,[resolved]);
const fs=require('node:fs'), vm=require('node:vm');
const source=fs.readFileSync('local_api/static/schema.js','utf8');
const start=source.indexOf('function renderSchemaDiagnostic(');
const end=source.indexOf("$('map-schema').addEventListener",start);
function element(tag){return {tag,children:[],textContent:'',append(...children){this.children.push(...children);}};}
const root=element('root');
const context={document:{createElement:element},$:()=>root};
vm.createContext(context); vm.runInContext(source.slice(start,end),context);
context.renderSchemaDiagnostic(resolved);
assert.equal(root.children[0].open,false);
assert.match(root.children[0].children[0].textContent,/Resolved validation check/);
context.renderSchemaDiagnostic(active);
assert.equal(root.children[1].open,true);
assert.match(root.children[1].children[0].textContent,/failure details/);
context.renderSchemaHistory([resolved, {...resolved,id:'second'}]);
const group=root.children[2];
assert.equal(group.open,false);
assert.match(group.children[0].textContent,/2 automatic correction/);
assert.match(group.children[1].textContent,/final mapping was revalidated/);
assert.equal(group.children.length,4);
assert.equal(group.children[2].open,false);
assert.equal(group.children[3].open,false);
"""
    subprocess.run(['node', '-e', script], check=True)


@pytest.mark.parametrize('code,expected', [
    ('literal_record_local_citation_rebuilt', 'success'),
    ('redundant_missing_status_removed', 'success'),
    ('unsupported_list_item_pruned', 'needs_review'),
    ('unsupported_optional_scalar_pruned', 'needs_review'),
    ('scalar_multiple_values_truncated', 'needs_review'),
])
def test_processing_success_does_not_hide_dropped_provider_values(code, expected):
    from types import SimpleNamespace
    from local_api.services.schema_diagnostics import mapping_result
    out = SimpleNamespace(meta={'field_review': {'status': 'complete', 'evidence_repairs': [{'code':code}]}})
    assert mapping_result(out)['status'] == expected
