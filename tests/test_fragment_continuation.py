from local_api.schemas.sections import SectionResponse
from local_api.schemas.extraction import ExtractedElement
from local_api.services.fragment_continuation import recover_fragment_continuations


def fixture():
    from local_api.schemas.sections import ResumeSection, SectionBlock
    texts = ['JANE DOE  City | jane@example.com',
             'Enterprise Voice Architect | Operations | Network Solutions | Support',
             'Experienced professional delivering reliable services. More summary context. Further expertise.']
    elements = [ExtractedElement(text=text, type='NarrativeText', page_number=1, metadata={}) for text in texts]
    def block(index, start, end):
        return SectionBlock(source_element_index=index, start=start, end=end,
                           text=texts[index][start:end], page_number=1, lane='left',
                           assignment='semantic', reason='test')
    sections = SectionResponse(warnings=[], status='needs_review', extraction_verified=False,
        sections=[ResumeSection(category='personal_information', label='Personal information',
            blocks=[block(0,0,10), block(0,10,len(texts[0])),block(1,0,29)]),
            ResumeSection(category='summary',label='Summary',blocks=[block(2,0,54)])],
        needs_review=[block(1,29,len(texts[1])),block(2,54,76),block(2,76,len(texts[2]))], metadata={})
    return sections, elements


def test_contiguous_summary_and_expertise_tails_preserve_source():
    sections, elements = fixture()
    repaired = recover_fragment_continuations(sections, elements)
    assert not repaired.needs_review
    assert len(sections.needs_review) == 3
    from local_api.services.source_validation import validate_result
    assert not validate_result(elements, repaired)
    skills = next(s for s in repaired.sections if s.category == 'skills')
    assert any(b.source_element_index == 1 and b.start == 29 for b in skills.blocks)
    summary = next(s for s in repaired.sections if s.category == 'summary')
    assert any(b.source_element_index == 2 and b.end == len(elements[2].text) for b in summary.blocks)


def test_mixed_source_ownership_is_not_guessed():
    sections, elements = fixture()
    sections.sections[0].blocks.append(sections.needs_review.pop(2))
    repaired = recover_fragment_continuations(sections, elements)
    assert any(b.source_element_index == 2 for b in repaired.needs_review)


def test_identity_is_not_taken_from_professional_headline():
    from local_api.schemas.mapping import SchemaMappingRequest
    from local_api.services.schema_mapping import map_schema
    sections, elements = fixture()
    repaired = recover_fragment_continuations(sections, elements)
    mapped = map_schema(SchemaMappingRequest(elements=elements, sections=repaired))
    assert mapped.data.contact.full_name == elements[0].text[:10].strip()
    assert mapped.data.professional_title.startswith('Enterprise Voice Architect')


def test_unlabelled_achievement_is_literal_and_issuer_is_not_invented():
    from local_api.schemas.sections import ResumeSection, SectionBlock
    from local_api.services.section_subschemas import build_subschemas
    from local_api.vendor.handoff_schema.models import ResumeSchema, ContactInfo
    sections, _ = fixture()
    text = 'Reduced service downtime by 30 percent.'
    sections.sections = [ResumeSection(category='awards', label='Awards and achievements', blocks=[
        SectionBlock(source_element_index=0,start=0,end=len(text),text=text,
                     page_number=1,lane='left',assignment='heading_context',reason='Explicit achievements heading')])]
    sections.needs_review = []
    data = ResumeSchema(contact=ContactInfo(full_name='', email='', phone=''))
    result = build_subschemas(sections,data,{'candidate_resume':True})
    attrs = {a.name:a for a in result[0].records[0].attributes}
    assert attrs['name'].items[0].value == text
    assert not attrs['issuer'].items and not attrs['date'].items
