"""Header OCR requires both visible text and a matching candidate contact."""
from PIL import Image
import pytest

from local_api.services.pdf_source_recovery import recover_pdf_source
from local_api.services.pdf_visual_header import visual_name_line


@pytest.mark.parametrize(
    'words,email,confidence,expected',
    [
        (['Nora', 'Martínez'], 'martinez.nora@example.org', 94, 'Nora Martínez'),
        (['DEV', 'PATEL'], 'dev.patel@example.org', 94, 'DEV PATEL'),
        (['North', 'Systems'], 'nora.martinez@example.org', 94, None),
        (['Nora', 'Martínez'], 'martinez.nora@example.org', 63, None),
    ],
)
def test_recovered_pdf_header_has_visual_and_candidate_contact_evidence(monkeypatch, words, email, confidence, expected):
    monkeypatch.setattr('local_api.services.pdf_visual_header.shutil.which', lambda name: name)
    monkeypatch.setattr('pdf2image.convert_from_bytes', lambda *args, **kwargs: [Image.new('RGB', (600, 800))])

    def ocr(crop, **kwargs):
        assert crop.size == (600, 72)
        return {'text': words, 'conf': [confidence, confidence], 'block_num': [1, 1],
                'par_num': [1, 1], 'line_num': [1, 1], 'left': [200, 260], 'top': [30, 30],
                'width': [50, 75], 'height': [20, 20]}

    monkeypatch.setattr('unstructured_pytesseract.image_to_data', ocr)
    records = [
        {'text': 'Business Analyst', 'page': 1, 'bbox': [.2, .09, .8, .12]},
        {'text': email, 'page': 1, 'bbox': [.2, .18, .8, .20]},
    ]
    native = [{'type': 'UncategorizedText', 'text': row['text'], 'metadata': {'page_number': 1}}
              for row in records]

    elements, audit = recover_pdf_source(b'pdf', native, records, visual_header=True)

    if expected:
        assert elements[0]['text'] == expected
        assert elements[0]['metadata']['ocr_verification_required']
        assert elements[0]['metadata']['pdf_visual_header']['bbox'] == [200/600, 30/800, 335/600, 50/800]
        assert audit['events'][0]['action'] == 'recover_pdf_visual_header'
        assert [element['text'] for element in elements[1:]] == [row['text'] for row in records]
    else:
        assert [element['text'] for element in elements] == [row['text'] for row in records]
        assert not audit['events']


def test_text_layer_already_starts_in_header_does_not_trigger_ocr(monkeypatch):
    def render(*args, **kwargs):
        pytest.fail('A text-backed header should not need rendering')

    monkeypatch.setattr('pdf2image.convert_from_bytes', render)
    records = [
        {'text': 'Nora Martínez', 'page': 1, 'bbox': [.2, .04, .8, .07]},
        {'text': 'nora.martinez@example.org', 'page': 1, 'bbox': [.2, .18, .8, .20]},
    ]
    assert visual_name_line(b'pdf', records) is None
