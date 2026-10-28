"""Conservative literal skill candidates and spoken-language records."""
import re
from local_api.services.source_fragments import texts, runs
from local_api.services.source_rows import SPOKEN


def unique(values):
    seen=set();result=[]
    for value in values:
        key=value.casefold()
        if key not in seen:result.append(value);seen.add(key)
    return result


def skill_candidates(blocks):
    result=[]
    sources=[b.text for b in blocks]
    # Complete parenthesized items across physical rows, but do not invent a
    # compound skill by concatenating two independently rendered list rows.
    for run in runs(blocks):
        pending='';depth=0
        for b in run:
            if pending or b.text.count('(')>b.text.count(')'):
                pending+=b.text;depth+=b.text.count('(')-b.text.count(')')
                if depth<=0:sources.append(pending);pending='';depth=0
    for source in sources:
        source=re.sub(r'^\s*[\u2022\u25cf\u25aa\u27a5*\-]\s*','',source).strip()
        if re.fullmatch(r'(?:US )?(?:HEALTHCARE DOMAIN EXPERTISE|TOOLS & TECHNOLOGIES|TECHNICAL SKILLS|CORE COMPETENCIES|Data & Infrastructure|Programming & Development|Core AI/ML & Agentic AI)',source,re.I):continue
        if ':' in source:
            label,body=source.split(':',1)
            if len(label.split())<=6:source=body.strip()
        depth=0;start=0;parts=[]
        for i,char in enumerate(source):
            if char=='(':depth+=1
            elif char==')':depth=max(0,depth-1)
            elif depth == 0 and (char in ',;|\n\u2022\u25cf' or
                    char == '/' and i > 0 and i + 1 < len(source) and source[i-1].isspace() and source[i+1].isspace()):
                parts.append(source[start:i].strip());start=i+1
        parts.append(source[start:].strip())
        for part in parts:
            part=part.rstrip('.')
            if part.count('(')!=part.count(')'):continue
            if not part or len(part.split())>30 or part.endswith('.') or re.search(r'\b(?:including|and|with|for|of|in)\s*$',part,re.I):continue
            if part.casefold() in {'including','validation','from','and','with','professional','beginner'}:continue
            if re.match(r'^(?:led|worked|built|conducted|developed|managed|supported|created|prepared|acted|implemented)\b',part,re.I):continue
            if any(c.isalpha() for c in part):result.append(part)
    return unique(result)


def language_rows(blocks):
    output=[]
    for block in blocks:
        text=re.sub(r'^\s*(?:[\u2022\u25cf*]\s*)?(?:spoken\s+)?languages?\s*:\s*','',block.text,flags=re.I)
        for piece in re.split(r'[,;\n\u2022\u25cf\u25aa]+',text):
            piece=re.sub(r'^\s*[-*]\s+','',piece).strip()
            if not piece or not any(c.isalpha() for c in piece):continue
            pair=re.fullmatch(r"([^\W\d_][^\d:|\n]{0,60}?)(?:\s+[-\u2013\u2014]\s*|\s*:\s*)(.+)",piece)
            if not pair:pair=re.fullmatch(r"([^\W\d_][^\d():|\n]{0,60}?)\s*\(([^()]+)\)",piece)
            language=pair.group(1).strip() if pair else piece
            level=pair.group(2).strip() if pair else None
            if not SPOKEN.fullmatch(language):continue
            output.append((language,level,block))
    seen=set()
    return [row for row in output if not ((row[0].casefold(),row[1]) in seen or seen.add((row[0].casefold(),row[1])))]
