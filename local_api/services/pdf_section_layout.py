"""Read PDF layout as evidence; never replace or reorder extracted text."""
from collections import Counter
from io import BytesIO
import unicodedata
import re


def compact(text):
    chars, offsets = [], []
    bullet=re.match(r'^\s*[–—-]\s+',text)
    for index, char in enumerate(text):
        for value in unicodedata.normalize('NFKC', char):
            if not value.isspace() and value not in '•▪●○◦\uf0b7' and not (bullet and index<bullet.end() and value in '–—-'):
                chars.append(value)
                offsets.append(index)
    return ''.join(chars), offsets


def line_occurrences(pattern,key,peers,line):
    """Pair repeated physical lines with repeated text occurrences in order.

    Without a unique one-to-one correspondence, omit geometry rather than
    mapping every occurrence onto the first identical PDF row.
    """
    found=list(re.finditer(pattern,key))
    if len(peers)>1:
        if len(found)!=len(peers):return []
        ordered=sorted(peers,key=lambda record:(record['bbox'][1],record['bbox'][0]))
        return [found[next(i for i,record in enumerate(ordered) if record is line)]]
    return found


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
        metadata.pop('pdf_source_lines',None)
        text = element.get('text', '')
        key, offsets = compact(text)
        matches = []
        source_box=None
        coordinates=metadata.get('coordinates',{})
        try:
            points=coordinates['points'];width=coordinates['layout_width'];height=coordinates['layout_height']
            source_box=[min(p[0] for p in points)/width,min(p[1] for p in points)/height,max(p[0] for p in points)/width,max(p[1] for p in points)/height]
        except (KeyError,TypeError,ValueError,ZeroDivisionError):
            pass
        page_lines=pages.get(metadata.get('page_number'), [])
        nearby=[line for line in page_lines if not source_box or not (line['bbox'][3]<source_box[1]-.01 or line['bbox'][1]>source_box[3]+.01 or line['bbox'][2]<source_box[0]-.01 or line['bbox'][0]>source_box[2]+.01)]
        for line in nearby:
            # Repeated words on a page (e.g. three Analyst titles) must match
            # their own source region, not the first identical physical line.
            if source_box and (line['bbox'][3]<source_box[1]-.01 or line['bbox'][1]>source_box[3]+.01 or line['bbox'][2]<source_box[0]-.01 or line['bbox'][0]>source_box[2]+.01):
                continue
            pattern=re.escape(line['key'])
            if metadata.get('pdf_glyph_recovery'):
                pattern=pattern.replace('\x00',r'[A-Za-z]{1,3}').replace('\ufffd',r'[A-Za-z]{1,3}')
            peers=[record for record in nearby if record['key']==line['key']]
            for found in line_occurrences(pattern,key,peers,line):
                matches.append({'start':offsets[found.start()],'end':offsets[found.end()-1]+1,
                                **{name:value for name,value in line.items() if name!='key'}})
        if matches:
            # A short line elsewhere on the page (e.g. 'Engineer') must not
            # split a larger matching line ('Engineering Lead') into fragments.
            unique={}
            for match in sorted(matches,key=lambda item:(item['start'],-item['end'])):
                if not any(left<=match['start'] and right>=match['end'] for left,right in unique):
                    unique[(match['start'],match['end'])]=match
            metadata['pdf_source_lines'] = sorted(unique.values(), key=lambda item: (item['start'], item['end']))
