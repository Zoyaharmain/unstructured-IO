"""Prepare a derivative for one MIME-prefixed PDF; never alter original bytes."""
import hashlib,json
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
OUT=Path(__file__).parent
manifest=json.loads((OUT/'manifest.json').read_text())
entry=next(r for r in manifest['inventory'] if r['file']=='EWM_Resume_Shailesh.pdf')
original=Path(entry['source']).read_bytes()
assert hashlib.sha256(original).hexdigest()==entry['sha256']
offset=original.find(b'%PDF-')
assert 0<offset<1024
normalized=original[offset:]
a=PdfReader(BytesIO(original));b=PdfReader(BytesIO(normalized))
assert len(a.pages)==len(b.pages)
assert [p.extract_text() for p in a.pages]==[p.extract_text() for p in b.pages]
folder=OUT/'normalized-inputs';folder.mkdir(exist_ok=True)
file=folder/entry['file'];file.write_bytes(normalized)
(OUT/'wrapped-pdf-preparation.json').write_text(json.dumps({'file':entry['file'],
    'original_source':entry['source'],'original_sha256':entry['sha256'],
    'normalized_source':str(file),'normalized_sha256':hashlib.sha256(normalized).hexdigest(),
    'removed_non_pdf_prefix_bytes':offset,'page_count':len(b.pages),
    'independent_parser_text_before_after_equal':True,'original_unchanged':True,
    'production_extraction_code_changed':False},indent=2))
print(str(file))
