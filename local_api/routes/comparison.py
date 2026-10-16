"""Deterministic word comparison against user-supplied reference text."""
from difflib import SequenceMatcher
import re
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

router = APIRouter()


class ComparisonRequest(BaseModel):
    reference: Annotated[str, Field(min_length=1, max_length=100_000)]
    extracted: Annotated[str, Field(max_length=100_000)]
    ignore_case: bool = False


def compare_words(request: ComparisonRequest):
    reference, extracted = re.findall(r'\S+', request.reference), re.findall(r'\S+', request.extracted)
    if not reference:
        raise HTTPException(422, 'Paste reference text containing at least one word')
    if max(len(reference), len(extracted)) > 5000:
        raise HTTPException(422, 'Comparison supports up to 5,000 words per text')
    normalize = str.casefold if request.ignore_case else lambda value: value
    matcher = SequenceMatcher(None, list(map(normalize, reference)), list(map(normalize, extracted)), autojunk=False)
    segments = []
    matched = missing = extra = 0
    for kind, a, b, c, d in matcher.get_opcodes():
        if kind == 'equal':
            matched += b - a
        else:
            missing += b - a
            extra += d - c
        segments.append({'kind': kind, 'reference': ' '.join(reference[a:b]),
                         'extracted': ' '.join(extracted[c:d])})
    return {'reference_words': len(reference), 'extracted_words': len(extracted),
            'matched_words': matched, 'missing_words': missing, 'extra_words': extra,
            'reference_coverage': round(100 * matched / len(reference), 1), 'segments': segments}


@router.post('/api/v1/compare/text')
async def compare_text(request: ComparisonRequest):
    return await run_in_threadpool(compare_words, request)
