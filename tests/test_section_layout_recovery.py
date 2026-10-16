from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,ArrayObject,NumberObject,DecodedStreamObject
from local_api.services.pdf_section_layout import annotate_pdf_lines
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock
from local_api.services.resume_sections import build_sections


def test_embedded_form_pdf_text_has_source_line_evidence():
    writer=PdfWriter();page=writer.add_blank_page(600,840)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    resources=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    form=DecodedStreamObject();form.set_data(b'BT /F1 14 Tf 20 760 Td (Technical Skills) Tj 0 -24 Td (Python SQL) Tj 0 -40 Td (Education) Tj 0 -24 Td (Bachelor of Science) Tj ET')
    form.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Form'),NameObject('/BBox'):ArrayObject([NumberObject(n) for n in [0,0,600,840]]),NameObject('/Resources'):resources})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Fm1'):writer._add_object(form)})})
    stream=DecodedStreamObject();stream.set_data(b'/Fm1 Do');page[NameObject('/Contents')]=writer._add_object(stream)
    data=BytesIO();writer.write(data)
    text='TechnicalSkillsPythonSQLEducationBachelorofScience'
    elements=[{'text':text,'metadata':{'page_number':1}}]
    annotate_pdf_lines(data.getvalue(),elements)
    assert elements[0]['text']==text
    hints=elements[0]['metadata']['pdf_source_lines']
    assert len(hints)==4
    assert [text[h['start']:h['end']] for h in hints]==['TechnicalSkills','PythonSQL','Education','BachelorofScience']


def test_company_project_and_education_emphasis_keeps_source_offsets():
    rows=[('experience','Engineer | Nova Systems | 2020 - Present'),('projects','Expense Tracker | Personal project'),('education','Bachelor of Science, Example University')]
    elements=[];grouped={}
    for i,(category,text) in enumerate(rows):
        elements.append(ExtractedElement(type='Title',text=text,metadata={}))
        grouped[category]=[SectionBlock(source_element_index=i,start=0,end=len(text),text=text,page_number=1,lane='main',assignment='semantic',reason='source')]
    sections=build_sections(grouped,elements)
    for section,(_,text),kind in zip(sections,rows,['company','project','education']):
        assert section.text==text
        assert section.highlights[0].kind==kind
        h=section.highlights[0];assert section.text[h.start:h.end]==text
