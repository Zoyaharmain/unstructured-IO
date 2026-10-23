"""Refine existing assigned blocks at exact PDF row offsets, preserving coverage."""
import re
from local_api.services.source_fragments import runs

SPOKEN = re.compile(r'\b(?:English|Hindi|French|Fran\u00e7ais|German|Spanish|Tamil|Telugu|Marathi|Kannada|Malayalam|Bengali|Arabic|Mandarin|Portuguese)\b', re.I)


def refine_rows(grouped, elements):
    from local_api.services.resume_structure import normalized_heading
    from local_api.services.review_resolution import document_scope
    if document_scope(elements).get('candidate_resume') is False:return grouped
    output = {}
    for category, blocks in grouped.items():
        for run in runs(blocks):
            first, last = run[0], run[-1]
            hints = elements[first.source_element_index].metadata.get('pdf_source_lines', [])
            if not hints:
                pieces = run
            else:
                cuts = sorted({first.start, last.end} | {h[k] for h in hints for k in ('start', 'end')
                    if isinstance(h.get(k), int) and first.start < h[k] < last.end})
                pieces = []
                for start, end in zip(cuts, cuts[1:]):
                    text = elements[first.source_element_index].text[start:end]
                    if not text.strip() and pieces:
                        prev = pieces[-1]; pieces[-1] = prev.model_copy(update={'end': end, 'text': prev.text + text});continue
                    original = next(b for b in run if b.start <= start < b.end)
                    assignment = original.assignment
                    if assignment in {'section_heading', 'structural_heading'} and normalized_heading(text) != normalized_heading(original.text):
                        assignment = 'semantic'
                    if normalized_heading(text) in {'education','languages','skills','technical skills','personal details','work experience','professional experience','summary','key projects','project highlights'}:
                        assignment = 'structural_heading'
                    pieces.append(original.model_copy(update={'start': start, 'end': end, 'text': text, 'assignment': assignment}))
            for block in pieces:
                target = category
                if re.match(r'\s*(?:[\u2022\u25cf]\s*)?(?:spoken\s+)?languages?\s*:', block.text, re.I) and SPOKEN.search(block.text):
                    target = 'languages'
                    block = block.model_copy(update={'assignment':'semantic'})
                output.setdefault(target, []).append(block)
    for blocks in output.values():blocks.sort(key=lambda b:(b.source_element_index, b.start))
    return output
