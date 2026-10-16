"""HTTP contract and parity against the installed Unstructured package."""
from io import BytesIO
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import local_api.app as api
from unstructured.partition.auto import partition

FIXTURES = Path(__file__).parent / 'fixtures'
client = TestClient(api.app)


def test_health():
    assert client.get('/health').json() == {'status': 'ok'}


def test_extraction_uses_installed_package():
    import inspect
    import sysconfig
    from importlib.metadata import distribution
    source = Path(inspect.getfile(inspect.unwrap(partition))).resolve()
    site_packages = Path(sysconfig.get_paths()['purelib']).resolve()
    assert source.is_relative_to(site_packages), source
    assert distribution('unstructured').version == '0.27.27'
    assert distribution('unstructured').read_text('direct_url.json') is None


@pytest.mark.parametrize('strategy', ['auto', 'fast', 'hi_res', 'ocr_only'])
def test_preserves_all_elements_and_passes_strategy(monkeypatch, strategy):
    class Element:
        def __init__(self, value): self.value = value
        def to_dict(self): return self.value
    original = [
        {'type':'PageBreak', 'element_id':'empty-id', 'text':'', 'metadata':{}},
        {'type':'Title', 'element_id':'fixed-id', 'text':'Unchanged\ntext', 'metadata':{'page_number':2,'custom':'preserve'}},
    ]
    def fake_partition(**kwargs):
        assert kwargs['strategy'] == strategy
        assert kwargs['file'].read().startswith(b'%PDF-')
        return [Element(e) for e in original]
    monkeypatch.setattr(api, 'partition', fake_partition)
    response = client.post('/v1/partition', files={'file': ('resume.pdf', b'%PDF-1.4\n', 'application/pdf')}, data={'strategy':strategy})
    assert response.status_code == 200, response.text
    result = response.json()
    assert set(result) == {'filename','requested_strategy','element_count','page_numbers','text','elements'}
    assert result['elements'] == original
    assert result['requested_strategy'] == strategy
    assert result['element_count'] == 2


@pytest.mark.parametrize('strategy', ['auto', 'fast', 'hi_res', 'ocr_only'])
@pytest.mark.parametrize('filename', ['Jayesh Yadav-CV.pdf', 'digital-multipage.pdf'])
def test_direct_extraction_parity(strategy, filename):
    payload = (FIXTURES / filename).read_bytes()
    settings = dict(metadata_filename=filename,
        strategy=strategy, languages=['eng'], hi_res_model_name='yolox',
        infer_table_structure=False, include_page_breaks=False,
        starting_page_number=1, pdf_image_dpi=200,
        metadata_last_modified='2026-10-15T00:00:00', password=None)
    direct = json.loads(json.dumps([e.to_dict() for e in partition(file=BytesIO(payload), **settings)]))
    response = client.post('/v1/partition', files={'file':(filename,payload,'application/pdf')},
        data=dict(strategy=strategy, languages='eng', hi_res_model_name='yolox',
                  metadata_last_modified='2026-10-15T00:00:00'))
    assert response.status_code == 200, response.text
    actual = response.json()
    assert actual['elements'] == direct
    assert actual['filename'] == filename
    assert actual['requested_strategy'] == strategy
    assert actual['element_count'] == len(direct)
    assert actual['text'] == '\n\n'.join(e.get('text', '') for e in direct)
    assert actual['page_numbers'] == sorted({e['metadata']['page_number'] for e in direct if e.get('metadata', {}).get('page_number') is not None})
    # Complete equality above includes IDs, empty objects, text, element types, coordinates,
    # metadata, and exact reading order. No fields are filtered or rounded.
    out = Path('reports/api-parity')
    out.mkdir(parents=True, exist_ok=True)
    (out / f'{Path(filename).stem}.{strategy}.direct.json').write_text(json.dumps(direct, indent=2)+'\n')
    (out / f'{Path(filename).stem}.{strategy}.api.json').write_text(json.dumps(actual, indent=2)+'\n')


@pytest.mark.parametrize('files', [None, {'file': ('', b'hello')}, {'file': ('   ', b'hello')}])
def test_missing_file_or_empty_filename(files):
    response = client.post('/v1/partition', files=files)
    assert response.status_code == 400
    assert isinstance(response.json()['detail'], str)


def test_invalid_strategy():
    response = client.post('/v1/partition', files={'file': ('x.pdf', b'%PDF-1.4')}, data={'strategy':'other'})
    assert response.status_code == 422


def test_upload_limit():
    assert api.MAX_UPLOAD_BYTES == 25 * 1024 * 1024
    response = client.post('/v1/partition', files={'file':('large.pdf', b'x' * (25 * 1024 * 1024 + 1))})
    assert response.status_code == 413


def test_exact_upload_limit_accepted(monkeypatch):
    monkeypatch.setattr(api, 'partition', lambda **kwargs: [])
    response = client.post('/v1/partition', files={'file':('large.pdf', b'x' * (25 * 1024 * 1024))})
    assert response.status_code == 200


def test_empty_input():
    assert client.post('/v1/partition', files={'file':('empty.pdf', b'')}).status_code == 422


@pytest.mark.parametrize('exc, status', [(ImportError('private dependency details'), 503),
    (ValueError('private malformed input details'), 422),
    (RuntimeError('secret internal token'), 500)])
def test_processing_errors(monkeypatch, exc, status):
    def fail(**kwargs): raise exc
    monkeypatch.setattr(api, 'partition', fail)
    response = client.post('/v1/partition', files={'file':('x.pdf', b'%PDF-1.4')})
    assert response.status_code == status
    assert 'private' not in response.text and 'secret' not in response.text
    assert isinstance(response.json()['detail'], str)


def test_empty_extraction_success(monkeypatch):
    monkeypatch.setattr(api, 'partition', lambda **kwargs: [])
    response = client.post('/v1/partition', files={'file':('blank.pdf', b'%PDF-1.4')})
    assert response.status_code == 200
    assert response.json() == dict(filename='blank.pdf', requested_strategy='auto',
        element_count=0, page_numbers=[], text='', elements=[])


def test_page_numbers_and_text_preserve_element_order(monkeypatch):
    class Element:
        def __init__(self, text, page): self.text, self.page = text, page
        def to_dict(self): return {'text': self.text, 'metadata': {} if self.page is None else {'page_number':self.page}}
    monkeypatch.setattr(api, 'partition', lambda **kwargs: [Element('third',3), Element('',None), Element('first',1), Element('again',3)])
    result = client.post('/v1/partition', files={'file':('x.pdf', b'%PDF-1.4')}).json()
    assert result['page_numbers'] == [1, 3]
    assert result['text'] == 'third\n\n\n\nfirst\n\nagain'
    assert result['element_count'] == 4


def test_non_pdf_text_matches_direct():
    payload = b'Hello world. This is an ordinary text document.'
    settings = dict(metadata_filename='note.txt', strategy='auto', languages=['eng'],
        hi_res_model_name=None, infer_table_structure=False, include_page_breaks=False,
        starting_page_number=1, pdf_image_dpi=200, metadata_last_modified=None, password=None)
    direct = json.loads(json.dumps([e.to_dict() for e in partition(file=BytesIO(payload), **settings)]))
    response = client.post('/v1/partition', files={'file':('note.txt', payload, 'text/plain')})
    assert response.status_code == 200, response.text
    assert response.json()['elements'] == direct


def test_malformed_pdf_real():
    response = client.post('/v1/partition', files={'file':('broken.pdf', b'%PDF-1.4\ninvalid PDF data')}, data={'strategy':'hi_res'})
    assert response.status_code == 422, response.text


def test_encrypted_pdf_real():
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt('test-password')
    output = BytesIO()
    writer.write(output)
    response = client.post('/v1/partition', files={'file':('locked.pdf', output.getvalue())}, data={'strategy':'hi_res'})
    assert response.status_code == 422, response.text


def test_unsupported_document(monkeypatch):
    from unstructured.partition.common import UnsupportedFileFormatError
    def fail(**kwargs): raise UnsupportedFileFormatError('unsupported input')
    monkeypatch.setattr(api, 'partition', fail)
    assert client.post('/v1/partition', files={'file':('unknown.bin', b'example')}).status_code == 422


def test_wrapped_missing_dependency(monkeypatch):
    def fail(**kwargs):
        try:
            raise ImportError('missing OCR package')
        except ImportError as exc:
            raise RuntimeError('OCR init failed') from exc
    monkeypatch.setattr(api, 'partition', fail)
    assert client.post('/v1/partition', files={'file':('x.pdf', b'%PDF-1.4')}).status_code == 503


def test_valid_blank_pdf_matches_direct():
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    direct = [e.to_dict() for e in partition(file=BytesIO(output.getvalue()), metadata_filename='blank.pdf',
        strategy='fast', languages=['eng'], hi_res_model_name=None, infer_table_structure=False,
        include_page_breaks=False, starting_page_number=1, pdf_image_dpi=200,
        metadata_last_modified=None, password=None)]
    direct = json.loads(json.dumps(direct))
    response = client.post('/v1/partition', files={'file':('blank.pdf', output.getvalue())}, data={'strategy':'fast'})
    assert response.status_code == 200, response.text
    assert response.json()['elements'] == direct == []
    assert response.json()['text'] == ''
    assert response.json()['page_numbers'] == []
    assert response.json()['element_count'] == 0
