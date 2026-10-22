import copy,json,sys
from pathlib import Path
import pytest
HERE=Path(__file__).parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(HERE)]
from schema_gate import (
    validate,
    repair_confirmed_omissions,
    normalize_evidence_pointers,
    prepare_candidate_mapping,
    parse_strict_json_response,
    parse_response_with_quarantine,
)
from local_api.vendor.handoff_schema.models import ResumeSchema,ContactInfo,WorkExperience,Education
OLD=ROOT/'reports/deepseek-schema-pilot5-20261022'

def sample():
    blocks=[{'source_id':'e0:0:12','source_element':0,'text':'Alex Example'},
            {'source_id':'e1:0:13','source_element':1,'text':'Python Docker'}]
    data=ResumeSchema(contact=ContactInfo(full_name='Alex Example',email='',phone='')).model_dump(mode='json')
    return {'data':data,'evidence':{'/contact/full_name':[{'source_id':'e0:0:12','quote':'Alex Example'}]},'missing_information':[]},blocks

def test_valid_exact_leaf_evidence():
    raw,blocks=sample();out=validate(raw,blocks)
    assert out['accepted'] and out['citation_valid_fields']==1

@pytest.mark.parametrize('kind',['missing','wrong_block','wrong_quote','mismatch','parent'])
def test_rejects_bad_evidence_and_no_inheritance(kind):
    raw,blocks=sample()
    if kind=='missing':raw['evidence']={}
    if kind=='wrong_block':raw['evidence']['/contact/full_name'][0]['source_id']='e1:0:13'
    if kind=='wrong_quote':raw['evidence']['/contact/full_name'][0]['quote']='Alex Invented'
    if kind=='mismatch':raw['evidence']['/contact/full_name'][0]={'source_id':'e1:0:13','quote':'Python Docker'}
    if kind=='parent':raw['evidence']={'/contact':raw['evidence']['/contact/full_name']}
    assert not validate(raw,blocks)['accepted']

def test_every_list_item_needs_own_citation():
    raw,blocks=sample();raw['data']['skills']['all_skills']=['Python','Docker']
    raw['evidence']['/skills/all_skills']=[{'source_id':'e1:0:13','quote':'Python Docker'}]
    out=validate(raw,blocks)
    assert sum(i['kind']=='missing_field_evidence' for i in out['issues'])==2

@pytest.mark.parametrize('doc,expected',[(1,0),(2,0),(3,0),(4,1),(5,2)])
def test_saved_omissions_repaired_transparently(doc,expected):
    raw=json.loads((OLD/f'{doc:02d}/mapping-raw.json').read_text());blocks=json.loads((OLD/f'{doc:02d}/source-blocks.json').read_text())
    before=copy.deepcopy(raw);candidate,changes=repair_confirmed_omissions(raw,blocks)
    assert raw==before and len(changes)==expected
    for change in changes:
        fields={r['path']:r for r in validate(candidate,blocks)['fields']}
        assert fields[change['written_path']]['citation_valid']
    assert not validate(candidate,blocks)['completeness_findings']
    if doc==4:assert 'Worked on Tag Mapping to Element level mapping for IMPS.' in candidate['data']['experience'][3]['responsibilities']
    if doc==5:assert [r['field_of_study'] for r in candidate['data']['education']]==['Intelligent Systems','Electronics and Communication']


def test_omission_fix_does_not_repair_unrelated_bad_citations():
    raw=json.loads((OLD/'04/mapping-raw.json').read_text());blocks=json.loads((OLD/'04/source-blocks.json').read_text())
    candidate,changes=repair_confirmed_omissions(raw,blocks)
    assert candidate['evidence'].get('/skills/all_skills/0') is None
    assert not validate(candidate,blocks)['accepted']


def test_ambiguous_dates_and_expected_completion_are_flagged():
    raw=json.loads((OLD/'01/mapping-raw.json').read_text());blocks=json.loads((OLD/'01/source-blocks.json').read_text())
    raw['missing_information']=[]
    out=validate(raw,blocks);kinds={u['kind'] for u in out['uncertainties']}
    assert {'expected_completion_not_earned','date_precedes_employer_anchor'}<=kinds
    assert not out['accepted']


def test_training_and_detached_education_dates_are_flagged():
    for doc,kind in [(3,'training_or_research_classification'),(5,'detached_date_with_shared_degree_element')]:
        raw=json.loads((OLD/f'{doc:02d}/mapping-raw.json').read_text());blocks=json.loads((OLD/f'{doc:02d}/source-blocks.json').read_text())
        raw['missing_information']=[]
        assert kind in {u['kind'] for u in validate(raw,blocks)['uncertainties']}


def test_wrong_employer_association_cannot_pass_with_literal_quote():
    raw,blocks=sample()
    blocks += [{'source_id':'a','source_element':2,'text':'Company: Alpha | Engineer'},
               {'source_id':'b','source_element':3,'text':'Company: Beta | Analyst'}]
    raw['data']['experience']=[WorkExperience(company='Alpha',role='Analyst').model_dump(mode='json')]
    raw['evidence'].update({'/experience/0/company':[{'source_id':'a','quote':'Alpha'}],'/experience/0/role':[{'source_id':'b','quote':'Analyst'}]})
    assert 'field_evidence_outside_explicit_employer' in {i['kind'] for i in validate(raw,blocks)['issues']}


def test_source_supported_empty_email_is_not_accepted():
    raw,blocks=sample();blocks.append({'source_id':'email','source_element':2,'text':'alex@example.com'})
    assert 'source_email_unassigned' in {i['kind'] for i in validate(raw,blocks)['issues']}


def test_second_pilot_missing_slashes_are_not_normalized():
    raw=json.loads((HERE/'01/mapping-raw.json').read_text())
    blocks=json.loads((HERE/'01/source-blocks.json').read_text())
    out=validate(raw,blocks)
    assert out['citation_valid_fields']==0
    assert not out['citation_contract_valid']
    assert any(i['kind']=='evidence_not_for_populated_leaf' for i in out['issues'])


def test_second_pilot_invalid_json_is_rejected_without_salvage():
    envelope=json.loads((HERE/'04/response-envelope.json').read_text())
    with pytest.raises(json.JSONDecodeError):
        json.loads(envelope['choices'][0]['message']['content'])
    assert not (HERE/'04/accepted-mapping.json').exists()


def test_second_pilot_wrong_quotes_cannot_be_accepted():
    raw=json.loads((HERE/'02/mapping-raw.json').read_text())
    blocks=json.loads((HERE/'02/source-blocks.json').read_text())
    out=validate(raw,blocks)
    fields={f['path']:f for f in out['fields']}
    assert not fields['/skills/domain_and_functional/5']['citation_valid']
    assert 'quote_not_in_cited_block' in fields['/skills/domain_and_functional/5']['errors']
    assert not out['accepted']


def test_parse_strict_json_reproduces_karthiyayini_failure_and_quarantine():
    content = (HERE / '04/response-content.txt').read_text()
    parsed, failure = parse_response_with_quarantine(content, finish_reason='stop')
    assert parsed is None
    assert failure is not None
    assert failure['error'] == 'invalid_json'
    assert 'Extra data' in failure['message']
    assert failure['offset'] == 35922
    assert failure['line'] == 1
    assert failure['column'] == 35923
    assert failure['automatic_repair_attempted'] is False
    assert failure['retry_performed'] is False

    with pytest.raises(ValueError) as excinfo:
        parse_strict_json_response(content)
    assert 'Strict JSON parsing failed: Extra data' in str(excinfo.value)
    assert 'char 35922' in str(excinfo.value)


def test_parse_strict_json_rejects_non_object():
    with pytest.raises(ValueError) as excinfo:
        parse_strict_json_response('["array", "not", "object"]')
    assert 'Response must be a JSON object' in str(excinfo.value)


def test_parse_strict_json_accepts_clean_response():
    sample_json = json.dumps({'data': {}, 'evidence': {}, 'missing_information': []})
    parsed = parse_strict_json_response(sample_json)
    assert isinstance(parsed, dict)
    assert 'data' in parsed


def test_lokhande_evidence_pointer_normalizer_recovers_provably_equivalent_citations():
    raw = json.loads((HERE / '01/mapping-raw.json').read_text())
    blocks = json.loads((HERE / '01/source-blocks.json').read_text())

    # 1. Raw validation strictly fails all citations
    raw_val = validate(raw, blocks)
    assert raw_val['citation_valid_fields'] == 0
    assert any(i['kind'] == 'non_standard_json_pointer' for i in raw_val['issues'])
    assert any(i['kind'] == 'evidence_not_for_populated_leaf' for i in raw_val['issues'])

    # 2. Local normalizer corrects provably equivalent missing leading slashes
    candidate, normalizations, rejections = normalize_evidence_pointers(raw, blocks)
    assert candidate['data'] == raw['data'], "Target data values must never be modified"
    assert len(normalizations) == 103
    assert len(rejections) == 0
    assert all(n['rule'] == 'provably_equivalent_leading_slash' for n in normalizations)
    # Exactly 102 of the 103 normalized pointers correspond to populated leaves
    from schema_gate import leaves
    assert sum(1 for n in normalizations if n['normalized_path'] in dict(leaves(raw['data']))) == 102

    # 3. Validation on normalized candidate recovers 93 valid citations without fabricating evidence
    cand_val = validate(candidate, blocks)
    assert cand_val['populated_fields'] == 102
    assert cand_val['citation_valid_fields'] == 93
    assert not any(i['kind'] == 'non_standard_json_pointer' for i in cand_val['issues'])

    # 4. Out-of-bounds pointer (/experience/1/technologies/6) was not normalized to any leaf
    assert any(i['kind'] == 'evidence_not_for_populated_leaf' and i['path'] == '/experience/1/technologies/6' for i in cand_val['issues'])


def test_pointer_normalizer_rejects_ambiguous_path_collision():
    raw, blocks = sample()
    # Create an ambiguous collision where both 'contact/full_name' and '/contact/full_name' exist
    raw['evidence']['contact/full_name'] = [{'source_id': 'e0:0:12', 'quote': 'Alex Example'}]
    candidate, normalizations, rejections = normalize_evidence_pointers(raw, blocks)
    assert len(rejections) == 2
    assert any(r['reason'] == 'ambiguous_path_collision' for r in rejections)
    # Target data values remain untouched
    assert candidate['data'] == raw['data']


def test_pointer_normalizer_never_modifies_data_values_or_fabricates_quotes():
    raw, blocks = sample()
    raw['evidence'] = {'contact/full_name': [{'source_id': 'e0:0:12', 'quote': 'Alex Example'}]}
    candidate, normalizations, rejections = normalize_evidence_pointers(raw, blocks)
    assert candidate['data'] == raw['data']
    assert candidate['evidence']['/contact/full_name'] == [{'source_id': 'e0:0:12', 'quote': 'Alex Example'}]

