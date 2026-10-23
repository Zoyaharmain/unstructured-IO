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


def citations(value, blocks):
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
        match = re.search(re.escape(literal), text, re.I)
        if not match:continue
        refs = []
        for offset,block in spans:
            start,end=max(0,match.start()-offset),min(len(block.text),match.end()-offset)
            if start<end:refs.append({'source_id':f'e{block.source_element_index}:{block.start}:{block.end}',
                                      'quote':block.text[start:end]})
        return refs
    return []


def contiguous_support(value, refs, inventory):
    """Require contiguous quotes or complete elements separated only by layout markers."""
    if not refs:return False
    previous = None;joined=''
    lengths={};element_text={}
    for key,text in inventory.items():
        parsed=re.fullmatch(r'e(\d+):(\d+):(\d+)',key)
        if parsed:
            index,start,end=map(int,parsed.groups());lengths[index]=max(lengths.get(index,0),end)
            element_text.setdefault(index,[]).append((start,text))
    for ref in refs:
        match = re.fullmatch(r'e(\d+):(\d+):(\d+)', ref.source_id)
        if not match:return False
        index,start,end=map(int,match.groups())
        text=inventory[ref.source_id]
        positions=[m.start() for m in re.finditer(re.escape(ref.quote),text)]
        if len(positions)!=1:return False
        begin=start+positions[0];finish=begin+len(ref.quote)
        if previous is not None:
            if previous==(index,begin):pass
            elif index>previous[0] and begin==0 and previous[1]==lengths[previous[0]] and all(not re.sub(r'[\s\u2022\u25cf\u25aa*-]','', ''.join(t for _,t in sorted(element_text.get(k,[])))) for k in range(previous[0]+1,index)):joined+='\n'
            else:return False
        joined+=ref.quote;previous=(index,finish)
    return ' '.join(str(value).casefold().split()) in ' '.join(joined.casefold().split())
