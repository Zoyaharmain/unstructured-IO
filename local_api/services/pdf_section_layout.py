"""Read PDF layout as evidence; never replace or reorder extracted text."""
from collections import Counter
from io import BytesIO
import unicodedata


def compact(text):
    chars, offsets = [], []
    for index, char in enumerate(text):
        for value in unicodedata.normalize('NFKC', char):
            if not value.isspace() and value not in '•▪●○◦':
                chars.append(value)
                offsets.append(index)
    return ''.join(chars), offsets


def annotate_pdf_lines(payload, elements):
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTChar, LTTextLine, LTContainer, LAParams
    pages = {}
    def lines(item):
        if isinstance(item, LTTextLine):
            yield item
        elif isinstance(item, LTContainer):
            for child in item:
                yield from lines(child)
    for number, page in enumerate(extract_pages(BytesIO(payload), laparams=LAParams(all_texts=True)), 1):
        records, sizes = [], Counter()
        for line in lines(page):
            chars = [char for char in line if isinstance(char, LTChar)]
            if not chars:
                continue
            text = line.get_text().strip()
            key, _ = compact(text)
            if sum(char.isalnum() for char in key) < 3:
                continue
            size = sorted(char.size for char in chars)[len(chars) // 2]
            sizes[round(size, 1)] += len(chars)
            x0, y0, x1, y1 = line.bbox
            records.append({'key': key, 'bbox': [x0/page.width, 1-y1/page.height, x1/page.width, 1-y0/page.height],
                            'font_size': round(size, 2), 'bold': sum('bold' in char.fontname.lower() for char in chars) > len(chars)/2})
        body_size = sizes.most_common(1)[0][0] if sizes else 10
        for record in records:
            record['heading_style'] = record['bold'] and record['font_size'] >= body_size * 1.35
        pages[number] = records
    for element in elements:
        metadata = element['metadata']
        text = element.get('text', '')
        key, offsets = compact(text)
        matches = []
        for line in pages.get(metadata.get('page_number'), []):
            position = key.find(line['key'])
            while position >= 0:
                matches.append({'start': offsets[position], 'end': offsets[position + len(line['key']) - 1] + 1,
                                **{name:value for name,value in line.items() if name != 'key'}})
                position = key.find(line['key'], position + len(line['key']))
        if matches:
            # A short line elsewhere on the page (e.g. 'Engineer') must not
            # split a larger matching line ('Engineering Lead') into fragments.
            unique={}
            for match in sorted(matches,key=lambda item:(item['start'],-item['end'])):
                if not any(left<=match['start'] and right>=match['end'] for left,right in unique):
                    unique[(match['start'],match['end'])]=match
            metadata['pdf_source_lines'] = sorted(unique.values(), key=lambda item: (item['start'], item['end']))
