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
    raw=json.loads((ROOT/'reports/deepseek-schema-pilot5-v2-20261022/01/mapping-raw.json').read_text())
    blocks=json.loads((ROOT/'reports/deepseek-schema-pilot5-v2-20261022/01/source-blocks.json').read_text())
    out=validate(raw,blocks)
    assert out['citation_valid_fields']==0
    assert not out['citation_contract_valid']
    assert any(i['kind']=='evidence_not_for_populated_leaf' for i in out['issues'])


def test_second_pilot_invalid_json_is_rejected_without_salvage():
    envelope=json.loads((ROOT/'reports/deepseek-schema-pilot5-v2-20261022/04/response-envelope.json').read_text())
    with pytest.raises(json.JSONDecodeError):
        json.loads(envelope['choices'][0]['message']['content'])
    assert not (ROOT/'reports/deepseek-schema-pilot5-v2-20261022/04/accepted-mapping.json').exists()


def test_second_pilot_wrong_quotes_cannot_be_accepted():
    raw=json.loads((ROOT/'reports/deepseek-schema-pilot5-v2-20261022/02/mapping-raw.json').read_text())
    blocks=json.loads((ROOT/'reports/deepseek-schema-pilot5-v2-20261022/02/source-blocks.json').read_text())
    out=validate(raw,blocks)
    fields={f['path']:f for f in out['fields']}
    assert not fields['/skills/domain_and_functional/5']['citation_valid']
    assert 'quote_not_in_cited_block' in fields['/skills/domain_and_functional/5']['errors']
    assert not out['accepted']


def test_parse_strict_json_reproduces_karthiyayini_failure_and_quarantine():
    content = (ROOT / 'reports/deepseek-schema-pilot5-v2-20261022/04/response-content.txt').read_text()
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
    raw = json.loads((ROOT / 'reports/deepseek-schema-pilot5-v2-20261022/01/mapping-raw.json').read_text())
    blocks = json.loads((ROOT / 'reports/deepseek-schema-pilot5-v2-20261022/01/source-blocks.json').read_text())

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


def test_reproduce_selector_ambiguity_on_multiple_roles():
    """Reproduces why Acadecraft (Doc 09) and Wipro (Doc 10) were marked 'missing_or_ambiguous_record'."""
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'
    m9 = json.loads((p10 / '09/candidate-mapping.json').read_text())
    m10 = json.loads((p10 / '10/candidate-mapping.json').read_text())
    
    # 1. Acadecraft in Doc 09: 2 roles were extracted by the model
    acadecraft_roles = [e for e in m9['data']['experience'] if 'acadecraft' in (e.get('company') or '').lower()]
    assert len(acadecraft_roles) == 2, "Model actually extracted both Acadecraft roles"
    assert {r['role'] for r in acadecraft_roles} == {'Quality Analyst', 'Subject Matter Expert'}
    
    # Selector only specified company: 'Acadecraft Pvt. Ltd.', so candidates == 2
    from score import score_fact
    fact_acadecraft = {
        'collection': 'experience',
        'selector': {'company': 'Acadecraft Pvt. Ltd.'},
        'field': 'role',
        'expected': 'Quality Analyst',
    }
    res = score_fact(fact_acadecraft, m9['data'], {})
    assert res['status'] == 'missing_or_ambiguous_record', "Ambiguity guard triggered because len(candidates) == 2"

    # 2. Wipro in Doc 10: 4 roles were extracted by the model
    wipro_roles = [e for e in m10['data']['experience'] if 'wipro' in (e.get('company') or '').lower()]
    assert len(wipro_roles) == 4, "Model actually extracted all four Wipro roles"
    assert sum(r['role'] == 'Senior Project Engineer' for r in wipro_roles) == 2
    assert sum(r['role'] == 'Project Engineer' for r in wipro_roles) == 2

    fact_wipro = {
        'collection': 'experience',
        'selector': {'company': 'Wipro Technologies Ltd'},
        'field': 'company',
        'expected': 'Wipro Technologies Ltd',
    }
    res_w = score_fact(fact_wipro, m10['data'], {})
    assert res_w['status'] == 'missing_or_ambiguous_record', "Ambiguity guard triggered because len(candidates) == 4"


def test_reproduce_bits_pilani_degree_specialization_separation():
    """Reproduces why BITS Pilani (Doc 08) was marked 'missing_or_ambiguous_record'."""
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'
    m8 = json.loads((p10 / '08/candidate-mapping.json').read_text())
    
    # 1. The BITS Pilani record was actually extracted completely
    bits_entry = next((e for e in m8['data']['education'] if 'bits pilani' in (e.get('institution') or '').lower()), None)
    assert bits_entry is not None, "BITS Pilani record was extracted by model"
    assert bits_entry['degree'] == 'Masters'
    assert bits_entry['field_of_study'] == 'Telecommunication & Software Engineering'
    assert bits_entry['graduation_year'] == '2016'
    
    # 2. Selector expected composite degree string 'Masters in Telecommunication'
    from score import score_fact, contains
    fact_bits = {
        'collection': 'education',
        'selector': {'degree': 'Masters in Telecommunication'},
        'field': 'institution',
        'expected': 'BITS Pilani (WILP)',
    }
    res = score_fact(fact_bits, m8['data'], {})
    assert res['status'] == 'missing_or_ambiguous_record'
    # The reason contains() fails: 'in' is absent in model's 'Masters Telecommunication & Software Engineering'
    combined = (bits_entry['degree'] or '') + ' ' + (bits_entry['field_of_study'] or '')
    assert not contains('Masters in Telecommunication', combined)


def test_reproduce_total_experience_null_uncalculated():
    """Verifies that total_experience_years is null when unstated, per prompt contract 'No calculated tenure'."""
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'
    for doc in ['05', '09']:
        m = json.loads((p10 / f'{doc}/candidate-mapping.json').read_text())
        assert m['data']['total_experience_years'] is None, f"Doc {doc} correctly obeys prompt: no calculated tenure"


def test_align_array_evidence_recovers_shifted_technologies():
    """Verifies that intra-array index alignment recovers shifted items without mutating data."""
    from schema_gate import align_array_and_span_evidence, validate
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'
    raw = json.loads((p10 / '02/mapping-raw.json').read_text())
    blocks = json.loads((p10 / '02/source-blocks.json').read_text())
    
    cand, changes = align_array_and_span_evidence(raw, blocks)
    assert cand['data'] == raw['data'], "Data must remain immutable"
    
    # Tech 2 (Kafka), Tech 3 (Jenkins), Tech 4 (Bitbucket) were shifted in raw
    assert any(c['rule'] == 'intra_array_index_alignment' and '/experience/1/technologies/5' in c['normalized_path'] for c in changes)
    
    # Validating cand shows /experience/1/technologies/5 (Bitbucket) is now valid
    val = validate(cand, blocks)
    f_map = {f['path']: f for f in val['fields']}
    assert f_map['/experience/1/technologies/5']['citation_valid']
    assert f_map['/experience/1/technologies/5']['value'] == 'Bitbucket'


def test_align_sibling_spans_swaps_inverted_subblocks():
    """Verifies that inverted sibling sub-block spans (e8:0:118 vs e8:118:157) are swapped."""
    from schema_gate import prepare_candidate_mapping, validate
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'
    raw = json.loads((p10 / '09/mapping-raw.json').read_text())
    blocks = json.loads((p10 / '09/source-blocks.json').read_text())

    cand, changes, rejections = prepare_candidate_mapping(raw, blocks)
    assert cand['data'] == raw['data']
    assert any(c['rule'] == 'sibling_subblock_span_realignment' for c in changes)

    val = validate(cand, blocks)
    f_map = {f['path']: f for f in val['fields']}
    assert f_map['/skills/domain_and_functional/22']['citation_valid']
    assert f_map['/skills/domain_and_functional/22']['value'] == 'Cross-Functional Collaboration'


def test_unsupported_and_missing_citations_must_remain_rejected():
    """Verifies cases that MUST remain rejected under strict validation."""
    from schema_gate import prepare_candidate_mapping, validate
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'

    # 1. Un-evidenced tail items in Doc 07 MUST remain rejected
    raw7 = json.loads((p10 / '07/mapping-raw.json').read_text())
    b7 = json.loads((p10 / '07/source-blocks.json').read_text())
    cand7, _, _ = prepare_candidate_mapping(raw7, b7)
    val7 = validate(cand7, b7)
    f7 = {f['path']: f for f in val7['fields']}
    assert not f7['/skills/tools_and_platforms/16']['citation_valid']
    assert 'missing_field_evidence' in f7['/skills/tools_and_platforms/16']['errors']

    # 2. Fabricated quote ('June 2022' in Doc 08) MUST remain rejected
    raw8 = json.loads((p10 / '08/mapping-raw.json').read_text())
    b8 = json.loads((p10 / '08/source-blocks.json').read_text())
    cand8, _, _ = prepare_candidate_mapping(raw8, b8)
    val8 = validate(cand8, b8)
    f8 = {f['path']: f for f in val8['fields']}
    assert not f8['/experience/0/start_date']['citation_valid']
    assert 'quote_not_in_cited_block' in f8['/experience/0/start_date']['errors']

    # 3. Partial quote (Doc 01 project name) MUST remain rejected
    raw1 = json.loads((p10 / '01/mapping-raw.json').read_text())
    b1 = json.loads((p10 / '01/source-blocks.json').read_text())
    cand1, _, _ = prepare_candidate_mapping(raw1, b1)
    val1 = validate(cand1, b1)
    f1 = {f['path']: f for f in val1['fields']}
    assert not f1['/projects/6/name']['citation_valid']
    assert 'value_not_supported_by_quotes' in f1['/projects/6/name']['errors']


def test_align_array_evidence_rejects_duplicate_values_in_array():
    """Verifies that arrays with duplicate values reject ambiguous reassignment."""
    from schema_gate import align_array_and_span_evidence, validate
    blocks = [{'source_id': 'b1', 'text': 'Python Docker Python'}]
    raw = {
        'data': {
            'skills': {'all_skills': ['Python', 'Docker', 'Python']}
        },
        'evidence': {
            # shifted citation at index 1 quotes 'Python', which exists at index 0 and 2
            '/skills/all_skills/1': [{'source_id': 'b1', 'quote': 'Python'}]
        }
    }
    cand, changes = align_array_and_span_evidence(raw, blocks)
    # Target data must not change
    assert cand['data'] == raw['data']
    # Must NOT reassign because 'Python' has duplicate occurrences (ambiguous destination)
    assert len(changes) == 0
    assert cand['evidence'] == raw['evidence']


def test_align_array_evidence_rejects_ambiguous_citation_collision():
    """Verifies that if multiple citations claim the same destination index, both are rejected."""
    from schema_gate import align_array_and_span_evidence
    blocks = [
        {'source_id': 'b1', 'text': 'Docker containerization'},
        {'source_id': 'b2', 'text': 'Docker deployment'}
    ]
    raw = {
        'data': {
            'skills': {'all_skills': ['Python', 'Docker']}
        },
        'evidence': {
            # Two different citations claiming the same target index (Docker at index 1)
            '/skills/all_skills/5': [{'source_id': 'b1', 'quote': 'Docker'}],
            '/skills/all_skills/6': [{'source_id': 'b2', 'quote': 'Docker'}]
        }
    }
    cand, changes = align_array_and_span_evidence(raw, blocks)
    assert cand['data'] == raw['data']
    # Collision: both claim index 1, so NEITHER is reassigned
    assert len(changes) == 0


def test_align_array_evidence_never_crosses_different_parent_arrays():
    """Verifies that citations never leak between distinct parent arrays."""
    from schema_gate import align_array_and_span_evidence
    blocks = [{'source_id': 'b1', 'text': 'PostgreSQL'}]
    raw = {
        'data': {
            'skills': {
                'technical_skills': ['Python'],
                'tools_and_platforms': ['PostgreSQL']
            }
        },
        'evidence': {
            # A citation for PostgreSQL on technical_skills/1
            '/skills/technical_skills/1': [{'source_id': 'b1', 'quote': 'PostgreSQL'}]
        }
    }
    cand, changes = align_array_and_span_evidence(raw, blocks)
    # Must not reassign across parent array boundaries
    assert '/skills/tools_and_platforms/0' not in cand['evidence']
    assert len(changes) == 0


def test_raw_model_outputs_remain_strictly_immutable():
    """Verifies that mapping-raw.json files remain completely untouched."""
    p10 = ROOT / 'reports/deepseek-schema-pilot10-20261022'
    for i in range(1, 11):
        d = p10 / f'{i:02d}'
        raw = json.loads((d / 'mapping-raw.json').read_text())
        assert isinstance(raw, dict)
        assert set(raw.keys()) >= {'data', 'evidence'}




