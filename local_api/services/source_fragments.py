"""Exact source quotes and ordered paragraph citations within one record."""
import re


def runs(blocks):
    output = []
    for block in blocks:
        if output and output[-1][-1].source_element_index == block.source_element_index and output[-1][-1].end == block.start:
            output[-1].append(block)
        else:
            output.append([block])
    return output


def texts(blocks):
    return [''.join(b.text for b in run) for run in runs(blocks)]


def citations(value, blocks, *, flexible_whitespace=False):
    literal = format(value, 'g') if isinstance(value, (int, float)) else str(value)
    chains = runs(blocks)
    # A record paragraph may span consecutive extracted elements. Newlines are
    # separators in the value, never fabricated text inside the source quotes.
    sequence=[]
    for block in blocks:
        if sequence and not (block.source_element_index==sequence[-1].source_element_index and block.start==sequence[-1].end or
                             block.source_element_index==sequence[-1].source_element_index+1 and block.start==0):
            chains.append(sequence);sequence=[]
        sequence.append(block)
    if sequence:chains.append(sequence)
    if blocks:chains.append(list(blocks))
    for run in chains:
        text='';spans=[];previous=None
        for block in run:
            if previous is not None and previous.source_element_index != block.source_element_index:text+='\n'
            spans.append((len(text),block));text+=block.text;previous=block
        pattern = (r'\s+'.join(re.escape(part) for part in literal.split())
                   if flexible_whitespace and literal.split() else re.escape(literal))
        match = re.search(pattern, text, re.I)
        if not match:continue
        refs = []
        for offset,block in spans:
            start,end=max(0,match.start()-offset),min(len(block.text),match.end()-offset)
            if start<end:refs.append({'source_id':f'e{block.source_element_index}:{block.start}:{block.end}',
                                      'quote':block.text[start:end]})
        return refs
    return []


from itertools import product


def contiguous_support(value, refs, inventory):
    """Require contiguous quotes or complete elements separated only by layout markers."""
    if not refs:
        return False
    lengths = {}
    element_text = {}
    for key, text in inventory.items():
        parsed = re.fullmatch(r'e(\d+):(\d+):(\d+)', key)
        if parsed:
            index, start, end = map(int, parsed.groups())
            lengths[index] = max(lengths.get(index, 0), end)
            element_text.setdefault(index, []).append((start, text))

    ref_data = []
    for ref in refs:
        match = re.fullmatch(r'e(\d+):(\d+):(\d+)', ref.source_id)
        if not match:
            return False
        index, start, end = map(int, match.groups())
        text = inventory.get(ref.source_id, '')
        positions = [m.start() for m in re.finditer(re.escape(ref.quote), text)]
        if not positions:
            return False
        ref_data.append((index, start, text, ref.quote, positions))

    for combo in product(*[data[4] for data in ref_data]):
        previous = None
        joined = ''
        valid = True
        for i, pos in enumerate(combo):
            index, start, text, quote, _ = ref_data[i]
            begin = start + pos
            finish = begin + len(quote)
            if previous is not None:
                if previous == (index, begin):
                    pass
                elif index == previous[0] and begin >= previous[1]:
                    el_chunks = sorted(element_text.get(index, []))
                    full_el = ''.join(t for _, t in el_chunks)
                    gap = full_el[previous[1]:begin] if begin <= len(full_el) else ''
                    if not gap or not re.sub(r'[\s\u2022\u25cf\u25aa*,-]', '', gap):
                        if gap:
                            joined += gap
                    else:
                        valid = False
                        break
                elif index > previous[0]:
                    prev_chunks = sorted(element_text.get(previous[0], []))
                    prev_full = ''.join(t for _, t in prev_chunks)
                    prev_gap = prev_full[previous[1]:] if previous[1] <= len(prev_full) else ''
                    prev_gap_ok = not prev_gap or not re.sub(r'[\s\u2022\u25cf\u25aa*,-]', '', prev_gap)

                    inter_ok = all(not re.sub(r'[\s\u2022\u25cf\u25aa*-]', '', ''.join(t for _, t in sorted(element_text.get(k, [])))) for k in range(previous[0] + 1, index))

                    curr_chunks = sorted(element_text.get(index, []))
                    curr_full = ''.join(t for _, t in curr_chunks)
                    curr_gap = curr_full[:begin] if begin <= len(curr_full) else ''
                    curr_gap_ok = not curr_gap or not re.sub(r'[\s\u2022\u25cf\u25aa*,-]', '', curr_gap)

                    if prev_gap_ok and inter_ok and curr_gap_ok:
                        joined += '\n'
                    else:
                        valid = False
                        break
                else:
                    valid = False
                    break
            joined += quote
            previous = (index, finish)
        if valid and ' '.join(str(value).casefold().split()) in ' '.join(joined.casefold().split()):
            return True
    return False
