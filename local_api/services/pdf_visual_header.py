"""Recover a visible candidate header from mixed text and graphics PDFs."""
import re
import shutil
import unicodedata
from collections import defaultdict

from local_api.services.contact_sections import EMAIL

PROFILE_SLUG = re.compile(r'linkedin\.com/in/([\w-]+)', re.I)


def identity_key(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if c.isalnum())


def visual_name_line(payload, records):
    """Read the area above the first positioned text line, using local OCR."""
    opening = [row for row in records if row['page'] == 1 and row['bbox'][1] < .32]
    first_top = min((row['bbox'][1] for row in opening), default=0)
    if not .055 <= first_top <= .20:
        return None
    contact_keys = [
        identity_key(match.group(0).split('@', 1)[0])
        for row in opening for match in EMAIL.finditer(row['text'])
    ]
    contact_keys.extend(
        identity_key(match.group(1)) for row in opening for match in PROFILE_SLUG.finditer(row['text'])
    )
    if not contact_keys or not shutil.which('pdftoppm') or not shutil.which('tesseract'):
        return None

    from pdf2image import convert_from_bytes
    from pdf2image.exceptions import PDFPopplerTimeoutError, PDFPageCountError, PDFSyntaxError
    from unstructured_pytesseract import Output, TesseractError, image_to_data

    try:
        page, = convert_from_bytes(payload, dpi=180, first_page=1, last_page=1, timeout=10)
        with page, page.crop((0, 0, page.width, int(page.height * first_top))) as header:
            data = image_to_data(header, lang='eng', config='--psm 11', output_type=Output.DICT, timeout=5)
    except (OSError, RuntimeError, TesseractError, PDFPopplerTimeoutError, PDFPageCountError, PDFSyntaxError):
        return None

    rows = defaultdict(list)
    for i, word in enumerate(data['text']):
        if word.strip():
            rows[(data['block_num'][i], data['par_num'][i], data['line_num'][i])].append(i)

    candidates = []
    for indices in rows.values():
        words = [data['text'][i].strip() for i in indices]
        if not 2 <= len(words) <= 5 or any(float(data['conf'][i]) < 80 for i in indices):
            continue
        if any(not word[0].isupper() or not all(c.isalpha() or c in ".'’-‐" for c in word) for word in words):
            continue
        tokens = [identity_key(word) for word in words if len(identity_key(word)) > 1]
        if len(tokens) < 2 or not any(all(token in key for token in tokens) for key in contact_keys):
            continue
        x0 = min(data['left'][i] for i in indices)
        y0 = min(data['top'][i] for i in indices)
        x1 = max(data['left'][i] + data['width'][i] for i in indices)
        y1 = max(data['top'][i] + data['height'][i] for i in indices)
        candidates.append({'text': ' '.join(words), 'page': 1,
                           'bbox': [x0/page.width, y0/page.height, x1/page.width, y1/page.height]})

    return candidates[0] if len(candidates) == 1 else None
