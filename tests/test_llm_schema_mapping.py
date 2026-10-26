"""Grounded field repair, atomic rejection, and shared legacy/subschema values."""
import json
from copy import deepcopy
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse, ResumeSection, SectionBlock, SectionEntry
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.schemas.subschema_spec import SUBSCHEMAS
from local_api.services.llm_schema_mapping import map_with_field_review, parse_review
from local_api.services.llm_section_review import ReviewSettings
from local_api.services.schema_mapping import map_schema
from local_api.services.subschema_validation import validate_hierarchy


def fixture():
    lines = ['Engineer | Acme Ltd | 2020 - Present', 'Analyst | Beta Ltd | 2018 - 2020']
    elements = [ExtractedElement(type='NarrativeText', text=t, page_number=1, metadata={}) for t in lines]
    blocks = [SectionBlock(source_element_index=i, start=0, end=len(t), text=t, page_number=1,
                           lane='main', assignment='semantic', reason='fixture') for i, t in enumerate(lines)]
    section = ResumeSection(category='experience', label='Experience', blocks=blocks, text='\n'.join(lines),
        entries=[SectionEntry(entry_id='merged', block_indices=[0, 1], lane='main', boundary_reason='fixture')])
    req = SchemaMappingRequest(elements=elements, sections=SectionResponse(status='provisional', sections=[section], needs_review=[], metadata={}, warnings=[]))
    records = []
    for i, (role, company, start, end) in enumerate([('Engineer', 'Acme Ltd', '2020', 'Present'), ('Analyst', 'Beta Ltd', '2018', '2020')]):
        sid = f'e{i}:0:{len(lines[i])}'
        fields = {k: [] for k in SUBSCHEMAS['experience']}
        for name, value in [('role', role), ('company', company), ('start_date', start), ('end_date', end)]:
            fields[name] = [{'value': value, 'evidence': [{'source_id': sid, 'quote': value}]}]
        records.append({'record_id': f'job-{i}', 'source_ids': [sid], 'fields': fields,
                        'missing': {k: 'not_stated' for k, v in fields.items() if not v}})
    return req, {'sections': [{'category': 'experience', 'records': records}]}


def configured(**overrides):
    return ReviewSettings(enabled=True, api_key='test-key', **overrides)


def test_field_review_corrects_records_and_uses_one_value_for_both_contracts():
    req, reply = fixture(); before = deepcopy(req.model_dump()); calls = []
    def transport(settings, messages):
        calls.append(messages)
        assert settings.api_key not in json.dumps(messages)
        return json.dumps(reply)
    out = map_with_field_review(req, settings=configured(), transport=transport)
    assert req.model_dump() == before
    assert out.meta['field_review']['status'] == 'complete'
    assert out.meta['field_review']['provider_calls'] == len(calls) == 1
    assert [(r.company, r.role) for r in out.data.experience] == [('Acme Ltd', 'Engineer'), ('Beta Ltd', 'Analyst')]
    assert out.meta['record_bindings']['experience'] == {'job-0': 0, 'job-1': 1}
    assert out.section_schemas[0].records[0].attributes[1].items[0].value == out.data.experience[0].role
    assert next(a for a in out.section_schemas[0].records[0].attributes if a.name == 'location').status == 'not_stated'
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


@pytest.mark.parametrize('mutation', ['invented', 'foreign', 'overlap', 'unknown', 'omitted', 'missing_reason', 'scalar_list', 'heading', 'quote'])
def test_invalid_mapping_is_rejected_atomically(mutation):
    req, reply = fixture(); baseline = map_schema(req)
    first, second = reply['sections'][0]['records']
    if mutation == 'invented': first['fields']['company'][0]['value'] = 'Invented employer'
    if mutation == 'foreign':
        first['fields']['role'][0]['evidence'][0]['source_id'] = second['source_ids'][0]
        first['fields']['role'][0]['value'] = 'Analyst'
    if mutation == 'overlap': second['source_ids'] = first['source_ids']
    if mutation == 'unknown': first['fields']['invented'] = []
    if mutation == 'omitted': reply['sections'] = []
    if mutation == 'missing_reason': first['missing'] = {}
    if mutation == 'scalar_list': first['fields']['role'] *= 2
    if mutation == 'heading': req.sections.sections[0].blocks[0].assignment = 'structural_heading'
    if mutation == 'quote':
        first['fields']['company'][0]['evidence'][0]['quote'] = 'not in source'
        first['fields']['company'][0]['value'] = 'Absent employer'
    out = map_with_field_review(req, settings=configured(), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'failed'
    if mutation != 'heading': assert out.data == baseline.data


def test_disabled_and_budget_guard_do_not_call_provider():
    req, _ = fixture()
    def forbidden(*args): pytest.fail('Provider called')
    out = map_with_field_review(req, settings=ReviewSettings(), transport=forbidden)
    assert out.meta['field_review']['status'] == 'disabled'
    out = map_with_field_review(req, settings=configured(max_input_chars=10), transport=forbidden)
    assert out.meta['field_review']['status'] == 'failed'
    assert out.meta['field_review']['provider_calls'] == 0


def test_whole_source_section_cannot_disappear():
    req, reply = fixture(); reply['sections'][0]['records'] = []
    with pytest.raises(ValueError): parse_review(json.dumps(reply), req.sections)


def test_local_numeric_years_and_slash_competencies_keep_evidence():
    from local_api.services.resume_sections import build_sections
    from local_api.services.section_recovery import recover_sections
    from local_api.services.resume_structure import heading_boundary
    from local_api.services.resume_sections import ALIASES
    from local_api.services.list_fields import skill_candidates
    req, _ = fixture()
    block = req.sections.sections[0].blocks[0].model_copy(update={
        'text': '15 years of experience leading 100+ clients', 'end': 42})
    block.end = len(block.text)
    req.elements = [req.elements[0].model_copy(update={'text': block.text})]
    req.sections.sections = build_sections({'summary': [block]}, req.elements)
    out = map_schema(req)
    record = out.section_schemas[0].records[0]
    years = next(a for a in record.attributes if a.name == 'total_experience_years')
    assert years.items[0].value == 15
    assert record.review_reasons == []
    block.text = 'Lean Six Sigma / DMAIC / Minitab / CI/CD'
    assert skill_candidates([block]) == ['Lean Six Sigma', 'DMAIC', 'Minitab', 'CI/CD']


def test_explicit_missing_declaration_can_replace_an_empty_array():
    req, reply = fixture()
    for record in reply['sections'][0]['records']:
        record['fields'] = {name: values for name, values in record['fields'].items() if values}
    out = map_with_field_review(req, settings=configured(), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.data.experience[0].company == 'Acme Ltd'
    assert out.data.experience[0].duration == '2020 - Present'
    assert next(a for a in out.section_schemas[0].records[0].attributes if a.name == 'location').status == 'not_stated'


def test_unexplained_omitted_field_is_rejected():
    req, reply = fixture()
    del reply['sections'][0]['records'][0]['fields']['company']
    out = map_with_field_review(req, settings=configured(), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'failed'


def test_invalid_candidate_gets_bounded_correction_without_partial_commit():
    req, reply = fixture(); calls = []
    def transport(settings, messages):
        calls.append(messages)
        return '{}' if len(calls) == 1 else json.dumps(reply)
    out = map_with_field_review(req, settings=configured(recovery_attempts=1), transport=transport)
    assert out.meta['field_review']['status'] == 'complete'
    assert out.meta['field_review']['provider_calls'] == len(calls) == 2
    assert out.data.experience[1].company == 'Beta Ltd'
    assert len(calls[1]) > len(calls[0])


def test_record_local_literal_citation_repair_retains_original_diagnostic():
    req, reply = fixture()
    reply['sections'][0]['records'][0]['fields']['company'][0]['evidence'][0]['quote'] = 'Acme LTD (employer)'
    out = map_with_field_review(req, settings=configured(), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.meta['field_review']['provider_calls'] == 1
    assert out.data.experience[0].company == 'Acme Ltd'
    assert out.meta['field_review']['diagnostics'][0]['category'] == 'source_evidence_validation'
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_foreign_company_citation_still_rejected_and_retry_gets_exact_reason():
    req, reply = fixture(); calls = []
    first, second = reply['sections'][0]['records']
    first['fields']['company'][0]['evidence'][0]['source_id'] = second['source_ids'][0]
    first['fields']['company'][0]['value'] = 'Beta Ltd'
    def transport(settings, messages):
        calls.append(messages)
        return json.dumps(reply)
    out = map_with_field_review(req, settings=configured(recovery_attempts=1), transport=transport)
    assert out.meta['field_review']['status'] == 'failed'
    assert len(calls) == 2
    feedback = calls[1][-1]['content']
    assert 'invalid_or_cross_record_quote' in feedback
    assert 'company' in feedback
    assert '/section_schemas/0/records/0/' in feedback


def test_multiple_stale_skill_citations_are_rebuilt_without_changing_values_or_owners():
    req, _ = fixture()
    section = req.sections.sections[0]
    section.category = 'skills'; section.label = 'Skills'; section.entries = []
    fields = {name: [] for name in SUBSCHEMAS['skills']}
    # Several bad citations must be repaired together, including IDs from a
    # different block. Both literal values are still in this record's sources.
    fields['technical_skills'] = [
        {'value': 'Engineer', 'evidence': [{'source_id': 'e999:0:1', 'quote': 'ENGINEER'}]},
        {'value': 'Analyst', 'evidence': [{'source_id': 'e999:0:1', 'quote': 'Analyst (skill)'}]},
    ]
    ids = [f'e{i}:0:{len(b.text)}' for i, b in enumerate(section.blocks)]
    reply = {'sections': [{'category': 'skills', 'records': [{
        'record_id': 'skills-1', 'source_ids': ids, 'fields': fields,
        'missing': {k: 'not_stated' for k, v in fields.items() if not v}}]}]}
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.meta['field_review']['provider_calls'] == 1
    assert out.data.skills.technical_skills == ['Engineer', 'Analyst']
    assert len(out.meta['field_review']['evidence_repairs']) == 2
    assert out.section_schemas[0].records[0].source_ids == ids
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_citation_repair_cannot_hide_a_later_unsupported_value(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    req, reply = fixture()
    first = reply['sections'][0]['records'][0]
    first['fields']['company'][0]['evidence'][0]['quote'] = 'Acme LTD (employer)'
    first['fields']['role'][0]['value'] = 'Unsupported role'
    baseline = map_schema(req)
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'failed'
    assert out.data == baseline.data

    assert out.meta['field_review']['diagnostic']['code'] == 'unsupported_value'
    assert out.meta['field_review']['diagnostics'][0]['code'] == 'invalid_or_cross_record_quote'


@pytest.mark.parametrize('category', ['experience', 'education', 'skills', 'certifications'])
def test_unused_heading_owner_is_removed_but_retained_as_context(category):
    from local_api.services.llm_schema_mapping import messages
    req, reply = fixture()
    section = req.sections.sections[0]
    section.category = category
    heading = section.blocks[0].model_copy(update={
        'source_element_index': 2, 'start': 0, 'end': len(category),
        'text': category, 'assignment': 'section_heading'})
    req.elements.append(req.elements[0].model_copy(update={'text': category}))
    section.blocks.append(heading)
    section.text = '\n'.join(b.text for b in section.blocks)
    sid = f'e2:0:{len(category)}'
    fields = {k: [] for k in SUBSCHEMAS[category]}
    name = next(iter(fields))
    fields[name] = [{'value': 'Engineer', 'evidence': [{
        'source_id': reply['sections'][0]['records'][0]['source_ids'][0], 'quote': 'Engineer'}]}]
    owner = [reply['sections'][0]['records'][0]['source_ids'][0], sid]
    payload = {'sections': [{'category': category, 'records': [{
        'record_id': 'record-1', 'source_ids': owner, 'fields': fields,
        'missing': {k: 'not_stated' for k, v in fields.items() if not v}}]}]}
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(payload))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.section_schemas[0].records[0].source_ids == owner[:1]
    assert any(b.source_id == sid for b in out.section_schemas[0].residual_blocks)
    assert out.meta['field_review']['evidence_repairs'][0]['code'] == 'unused_heading_context_removed'
    prompt = json.loads(messages([section])[1]['content'])['sections'][0]
    assert category in prompt['heading_context']
    assert sid not in {b['source_id'] for b in prompt['blocks']}
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_heading_cannot_be_used_as_field_evidence_or_only_record_source():
    req, reply = fixture()
    req.sections.sections[0].blocks[0].assignment = 'section_heading'
    first = reply['sections'][0]['records'][0]
    first['source_ids'].extend(reply['sections'][0]['records'][1]['source_ids'])
    # Content remains, but this record still claims an actual field value from
    # the heading. Removing the owner ID would hide that invalid claim.
    reply['sections'][0]['records'] = [first]
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'failed'


def test_heading_repair_then_citation_repair_both_validate_before_commit():
    req, reply = fixture()
    # The second source acts as unused heading context for the first record.
    req.sections.sections[0].blocks[1].assignment = 'section_heading'
    first, second = reply['sections'][0]['records']
    first['source_ids'].extend(second['source_ids'])
    first['fields']['company'][0]['evidence'][0]['quote'] = 'incorrect citation'
    reply['sections'][0]['records'] = [first]
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert [r['code'] for r in out.meta['field_review']['evidence_repairs']] == [
        'unused_heading_context_removed', 'literal_record_local_citation_rebuilt']
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_valid_quote_for_wrong_field_is_recited_from_same_record():
    req, reply = fixture()
    first = reply['sections'][0]['records'][0]
    first['fields']['company'][0]['evidence'][0]['quote'] = 'Engineer'
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.data.experience[0].company == 'Acme Ltd'
    assert out.meta['field_review']['evidence_repairs']


def test_personal_email_owner_omitted_by_provider_is_recovered_within_singleton():
    req, reply = fixture()
    section = req.sections.sections[0]
    section.category = 'personal_information'; section.entries = []
    fields = {k: [] for k in SUBSCHEMAS['personal_information']}
    first, second = reply['sections'][0]['records']
    # Distinct contact blocks, with email cited to the name block by mistake.
    text = 'candidate@example.com'
    section.blocks[1] = section.blocks[1].model_copy(update={'text': text, 'end': len(text)})
    req.elements[1] = req.elements[1].model_copy(update={'text': text})
    section.text = '\n'.join(b.text for b in section.blocks)
    sid = first['source_ids'][0]
    fields['full_name'] = [{'value': 'Engineer', 'evidence': [{'source_id': sid, 'quote': 'Acme Ltd'}]}]
    fields['email'] = [{'value': text, 'evidence': [{'source_id': sid, 'quote': text}]}]
    payload = {'sections': [{'category': 'personal_information', 'records': [{
        'record_id': 'person-1', 'source_ids': [sid], 'fields': fields,
        'missing': {k: 'not_stated' for k,v in fields.items() if not v}}]}]}
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(payload))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.data.contact.email == text
    assert any(r['code'] == 'singleton_source_owner_completed' for r in out.meta['field_review']['evidence_repairs'])
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_whitespace_layout_citation_repair_uses_exact_source_quote():
    req, reply = fixture()
    section = req.sections.sections[0]
    block = section.blocks[0]
    text = block.text.replace('Acme Ltd', 'Acme  Ltd')
    section.blocks[0] = block.model_copy(update={'text':text, 'end':len(text)})
    req.elements[0] = req.elements[0].model_copy(update={'text':text})
    section.text = '\n'.join(b.text for b in section.blocks)
    record = reply['sections'][0]['records'][0]
    sid = f'e0:0:{len(text)}'; record['source_ids'] = [sid]
    for values in record['fields'].values():
        for value in values:
            value['evidence'][0]['source_id'] = sid
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_:json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    company = next(a for a in out.section_schemas[0].records[0].attributes if a.name=='company')
    assert company.items[0].evidence[0].quote == 'Acme  Ltd'


def test_unsupported_list_item_is_pruned_allowing_mapping_to_complete():
    req, reply = fixture()
    section = req.sections.sections[0]
    section.category = 'skills'
    section.entries = []
    fields = {k: [] for k in SUBSCHEMAS['skills']}
    sid = f'e0:0:{len(req.elements[0].text)}'
    # Provide one valid skill and one unsupported/hallucinated skill
    fields['technical_skills'] = [
        {'value': 'Engineer', 'evidence': [{'source_id': sid, 'quote': 'Engineer'}]},
        {'value': 'HallucinatedSkill', 'evidence': [{'source_id': sid, 'quote': 'Nonexistent'}]}
    ]
    fields['domain_and_functional'] = [
        {'value': 'UnbackedDomainSkill', 'evidence': [{'source_id': sid, 'quote': 'Engineer'}]}
    ]
    payload = {'sections': [{'category': 'skills', 'records': [{
        'record_id': 'skills-1', 'source_ids': [sid], 'fields': fields,
        'missing': {k: 'not_stated' for k, v in fields.items() if not v}}]}]}
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(payload))
    assert out.meta['field_review']['status'] == 'complete'
    assert 'Engineer' in out.data.skills.technical_skills
    assert 'HallucinatedSkill' not in out.data.skills.technical_skills
    assert out.data.skills.domain_and_functional == []
    assert any(r['code'] == 'unsupported_list_item_pruned' for r in out.meta['field_review']['evidence_repairs'])
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_section_system_prompt_contains_json():
    from local_api.services.review_chunking import SECTION_SYSTEM
    assert 'json' in SECTION_SYSTEM.lower()


def test_unowned_section_block_adopted_for_repeated_record_company():
    req, reply = fixture()
    section = req.sections.sections[0]
    # Add an unowned company block to the experience section
    comp_text = 'Societe Generale'
    from local_api.schemas.sections import SectionBlock
    new_elem_idx = len(req.elements)
    from local_api.schemas.extraction import ExtractedElement
    req.elements.append(ExtractedElement(type='Text', text=comp_text, page_number=1, metadata={}))
    unowned_block = SectionBlock(
        source_element_index=new_elem_idx, start=0, end=len(comp_text), text=comp_text,
        lane='main', assignment='heading_context', reason='preceding employer',
        page_number=1
    )
    section.blocks.append(unowned_block)
    section.text = '\n'.join(b.text for b in section.blocks)
    unowned_sid = f'e{new_elem_idx}:0:{len(comp_text)}'
    
    # Record has only original block in source_ids, but cites unowned_sid for company
    record = reply['sections'][0]['records'][0]
    record['fields']['company'] = [{'value': comp_text, 'evidence': [{'source_id': unowned_sid, 'quote': comp_text}]}]
    
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_: json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.data.experience[0].company == comp_text
    assert any(r['code'] == 'unowned_section_source_owner_completed' for r in out.meta['field_review']['evidence_repairs'])
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_transient_retry_and_permanent_error_behavior(monkeypatch):
    from local_api.services.llm_section_review import provider_json, ReviewError
    from urllib.error import HTTPError
    from io import BytesIO

    calls = []
    def mock_open_429(*args, **kwargs):
        calls.append('call')
        if len(calls) < 2:
            raise HTTPError('https://api.deepseek.com', 429, 'Rate limit', {}, BytesIO(b'rate limited'))
        resp = BytesIO(b'{"choices": [{"message": {"content": "ok"}}]}')
        resp.read = lambda *a: b'{"choices": [{"message": {"content": "ok"}}]}'
        return resp

    monkeypatch.setattr('local_api.services.llm_section_review.time.sleep', lambda *_: None)
    monkeypatch.setattr('urllib.request.OpenerDirector.open', mock_open_429)

    # Transient 429 retries and succeeds on attempt 2
    settings = configured()
    res = provider_json(settings, '/test')
    assert res == {"choices": [{"message": {"content": "ok"}}]}
    assert len(calls) == 2

    # Permanent 401 raises immediately with 1 call (no retry)
    calls.clear()
    def mock_open_401(*args, **kwargs):
        calls.append('call')
        raise HTTPError('https://api.deepseek.com', 401, 'Unauthorized', {}, BytesIO(b'invalid key'))

    monkeypatch.setattr('urllib.request.OpenerDirector.open', mock_open_401)
    with pytest.raises(ReviewError) as exc_info:
        provider_json(settings, '/test')
    assert str(exc_info.value) == 'authentication_failed'
    assert len(calls) == 1




def test_current_language_registry_accepts_multiple_source_backed_values():
    from local_api.services.llm_schema_mapping import messages
    req, _ = fixture()
    section = req.sections.sections[0]
    section.category = 'languages'; section.label = 'Languages'; section.entries = []
    lines = ['English', 'Hindi']
    for i, text in enumerate(lines):
        req.elements[i] = req.elements[i].model_copy(update={'text': text})
        section.blocks[i] = section.blocks[i].model_copy(update={'text': text, 'end': len(text)})
    section.text = '\n'.join(lines)
    ids = [f'e{i}:0:{len(text)}' for i, text in enumerate(lines)]
    payload = {'sections': [{'category': 'languages', 'records': [{
        'record_id': 'languages-1', 'source_ids': ids,
        'fields': {'language': [{'value':text, 'evidence':[{'source_id':sid, 'quote':text}]} for text,sid in zip(lines,ids)], 'proficiency':[]},
        'missing': {'proficiency':'not_stated'}}]}]}
    assert json.loads(messages([section])[1]['content'])['registry']['languages']['language']['multiple'] is True
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.meta['field_review']['provider_calls'] == 1
    values = next(a for a in out.section_schemas[0].records[0].attributes if a.name=='language')
    assert [v.value for v in values.items] == lines
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_retry_budget_exhaustion_reports_budget_instead_of_internal_schema_error(monkeypatch):
    monkeypatch.setenv('RESUME_APP_ENV', 'development')
    req, _ = fixture()
    calls = []
    def provider(*_):
        calls.append(1)
        return 'invalid JSON'
    out = map_with_field_review(req, settings=configured(recovery_attempts=1,
        max_document_requests=1, max_pass_requests=1, max_total_requests=1), transport=provider)
    assert len(calls) == 1
    assert out.meta['field_review']['diagnostic']['category'] == 'request_budget'
    assert out.meta['field_review']['diagnostics'][0]['category'] == 'json_parsing'


def test_redundant_missing_status_for_source_backed_field_is_revalidated():
    req, payload = fixture()
    payload['sections'][0]['records'][0]['missing']['company'] = 'not_stated'
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status'] == 'complete'
    assert out.data.experience[0].company == 'Acme Ltd'
    assert any(r['code'] == 'redundant_missing_status_removed' for r in out.meta['field_review']['evidence_repairs'])
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))


def test_missing_status_repair_cannot_establish_an_unsupported_company():
    req, payload = fixture()
    record = payload['sections'][0]['records'][0]
    record['missing']['company'] = 'not_stated'
    record['fields']['company'][0]['value'] = 'Unsupported employer'
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status'] == 'failed'


def test_missing_status_cleanup_rejects_unknown_missing_fields():
    req, payload = fixture()
    payload['sections'][0]['records'][0]['missing']['unknown_field'] = 'not_stated'
    out = map_with_field_review(req, settings=configured(recovery_attempts=0), transport=lambda *_:json.dumps(payload))
    assert out.meta['field_review']['status'] == 'failed'


@pytest.mark.parametrize('second,code', [('Engineer','duplicate_scalar_items_deduplicated'), ('Acme Ltd','scalar_multiple_values_truncated')])
def test_certificate_name_repair_distinguishes_duplicate_from_conflicting_value(second, code):
    req, payload = fixture()
    section = req.sections.sections[0]
    section.category = 'certifications'; section.label = 'Certifications'
    section.entries = []
    ids = payload['sections'][0]['records'][0]['source_ids']
    fields = {k: [] for k in SUBSCHEMAS['certifications']}
    fields['name'] = [{'value':value, 'evidence':[{'source_id':ids[0], 'quote':value}]} for value in ['Engineer',second]]
    reply = {'sections':[{'category':'certifications','records':[{
        'record_id':'cert-1','source_ids':ids,'fields':fields,
        'missing':{k:'not_stated' for k,v in fields.items() if not v}}]}]}
    out = map_with_field_review(req,settings=configured(recovery_attempts=0),transport=lambda *_:json.dumps(reply))
    assert out.meta['field_review']['status'] == 'complete'
    assert len(out.section_schemas[0].records[0].attributes[0].items) == 1
    repairs=out.meta['field_review']['evidence_repairs']
    assert any(r['code']==code for r in repairs)
    if code=='scalar_multiple_values_truncated':
        assert out.meta['mapping_result']['status']=='needs_review'
    else:
        assert not any(r['code']=='scalar_multiple_values_truncated' for r in repairs)
    validate_hierarchy(out.section_schemas, SectionResponse.model_validate(out.meta['reviewed_sections']))
