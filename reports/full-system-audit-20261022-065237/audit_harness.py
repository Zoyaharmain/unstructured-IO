"""Local, provider-free evaluation harness for the full-system audit.

Runs the current production pipeline (extraction -> normalization -> segmentation
-> ML classification -> deterministic validation) on a selected set of original
PDFs, writes every intermediate artifact, and compares the result against the
preserved 350-document repair artifacts and against an independent PDF text
layer. No provider call is made and no historical artifact is modified.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DEEPSEEK_REVIEW_ENABLED', 'false')
os.environ.setdefault('UNSTRUCTURED_DISABLE_NOTICE', '1')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

from local_api.schemas.sections import SectionRequest
from local_api.services.resume_sections import get_engine
from local_api.services.section_recovery import recover_sections
from local_api.services.text_extraction_service import extract_text

TOKEN = re.compile(r"[A-Za-z0-9]+(?:[+#.'’-][A-Za-z0-9]+)*")


def tokens(text):
    return [t.casefold() for t in TOKEN.findall(text or '')]


def independent_text(pdf_path):
    out = subprocess.run(['pdftotext', '-layout', str(pdf_path), '-'],
                         capture_output=True, timeout=120)
    return out.stdout.decode('utf-8', 'replace')


def source_interval_check(elements, result):
    """Blocks must tile each element exactly once, in order, without overlap."""
    errors = []
    per_element = {}
    for section in result.sections:
        for block in section.blocks:
            per_element.setdefault(block.source_element_index, []).append(block)
    for section in result.sections:
        for block in section.needs_review if False else []:
            pass
    ledger = []
    for section in result.sections:
        ledger.extend((b.source_element_index, b.start, b.end) for b in section.blocks)
    ledger.extend((b.source_element_index, b.start, b.end) for b in result.needs_review)
    ledger.sort()
    for index, element in enumerate(elements):
        cursor = 0
        covered = [item for item in ledger if item[0] == index]
        for _, start, end in covered:
            if start != cursor:
                errors.append(f'gap_or_overlap:element{index}:{cursor}!={start}')
            if not 0 <= start <= end <= len(element.text):
                errors.append(f'out_of_range:element{index}')
            cursor = end
        if covered and cursor != len(element.text):
            errors.append(f'incomplete_coverage:element{index}:{cursor}!={len(element.text)}')
        if not covered and element.text:
            errors.append(f'element_not_covered:{index}')
    return errors, ledger


def audit_document(pdf_path, index_entry, saved_artifact, out_dir):
    payload = pdf_path.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    started = time.monotonic()
    record = {'file': pdf_path.name, 'sha256': sha,
              'index_sha256_match': sha == index_entry['sha256']}
    extraction = extract_text(payload, pdf_path.name, strategy='fast')
    elements = extraction.elements or []
    strategy_used = 'fast'
    if not elements and pdf_path.suffix.lower() == '.pdf':
        # No text layer produced by the fast strategy: retry with OCR before
        # declaring the document unreadable, mirroring the batch runner.
        extraction = extract_text(payload, pdf_path.name, strategy='ocr_only')
        elements = extraction.elements or []
        strategy_used = 'ocr_only'
    record['strategy'] = strategy_used
    if not elements:
        record['status'] = 'no_text_layer'
        record['character_count'] = len(extraction.text)
        return record
    request = SectionRequest(elements=elements, extraction_verified=False)
    result = recover_sections(request, get_engine().detect(request))
    record['seconds'] = round(time.monotonic() - started, 2)
    record['element_count'] = len(elements)
    record['character_count'] = len(extraction.text)
    record['pages'] = getattr(extraction.metadata, 'page_numbers', None)
    record['sections'] = [s.category for s in result.sections]
    record['needs_review_blocks'] = len(result.needs_review)
    record['assigned_text_percent'] = result.metadata.get('assigned_text_percent')
    quality = result.metadata.get('quality_assessment') or {}
    record['quality'] = quality
    record['document_scope'] = (quality.get('document_scope') or {})
    record['source_fidelity'] = quality.get('source_fidelity') or {}
    errors, ledger = source_interval_check(elements, result)
    record['source_interval_errors'] = errors
    record['span_count'] = len(ledger)
    record['duplicate_span_intervals'] = len(ledger) - len({(i, s, e) for i, s, e in ledger})
    damaged = sum(1 for e in elements if '\x00' in e.text or '\ufffd' in e.text)
    record['damaged_glyph_elements'] = damaged
    # Independent text-layer comparison.
    reference = independent_text(pdf_path)
    ref_tokens = tokens(reference)
    own_tokens = tokens(extraction.text)
    ref_counts, own_counts = {}, {}
    for token in ref_tokens:
        ref_counts[token] = ref_counts.get(token, 0) + 1
    for token in own_tokens:
        own_counts[token] = own_counts.get(token, 0) + 1
    recall = sum(min(c, own_counts.get(t, 0)) for t, c in ref_counts.items()) / max(1, sum(ref_counts.values()))
    precision = sum(min(c, ref_counts.get(t, 0)) for t, c in own_counts.items()) / max(1, sum(own_counts.values()))
    record['reference_token_recall'] = round(recall, 4)
    record['reference_token_precision'] = round(precision, 4)
    missing = [t for t in ref_counts if own_counts.get(t, 0) < ref_counts[t]][:25]
    extra = [t for t in own_counts if ref_counts.get(t, 0) < own_counts[t]][:25]
    record['reference_missing_tokens'] = missing
    record['reference_extra_tokens'] = extra
    # Word boundary diagnostics inside our own text.
    fused = re.findall(r'\b[A-Za-z]{2,}[A-Z][a-z]{2,}\b', extraction.text)[:20]
    record['possible_fused_words'] = fused
    record['possible_split_words'] = [
        w for w in re.findall(r'(?<=[A-Za-z])\s(?=[a-z]{2,}\b)', extraction.text)][:20]
    # Relationship grouping snapshot.
    relationships = (quality.get('relationship_correctness') or {}).get('sections') or {}
    record['relationship_summary'] = {
        category: {'proposed_entries': details.get('proposed_entries'),
                   'entries_needing_review': len(details.get('entries_needing_review') or []),
                   'unlinked_block_indices': len(details.get('unlinked_block_indices') or [])}
        for category, details in relationships.items()}
    # Comparison with the preserved 350 artifact.
    if saved_artifact:
        saved_elements = saved_artifact['extraction']['elements']
        saved_sections = saved_artifact.get('repaired_sections') or saved_artifact.get('reviewed_sections')
        record['saved_extraction_same_text'] = (
            [e['text'] for e in saved_elements] == [e.text for e in elements])
        record['saved_element_count'] = len(saved_elements)
        record['saved_sections'] = [s['category'] for s in saved_sections['sections']]
        record['saved_section_count'] = len(saved_sections['sections'])
        saved_result = saved_sections
        saved_q = (saved_sections.get('metadata') or {}).get('quality_assessment') or {}
        record['saved_quality'] = saved_q
        record['saved_relationship_summary'] = {
            category: {'proposed_entries': details.get('proposed_entries'),
                       'entries_needing_review': len(details.get('entries_needing_review') or []),
                       'unlinked_block_indices': len(details.get('unlinked_block_indices') or [])}
            for category, details in ((saved_q.get('relationship_correctness') or {}).get('sections') or {}).items()}
    # Persist every intermediate artifact for this document.
    target = out_dir / f'{sha[:20]}.json'
    target.write_text(json.dumps({
        'file': pdf_path.name, 'sha256': sha,
        'extraction': extraction.model_dump(),
        'sections': result.model_dump(),
    }, ensure_ascii=False))
    record['artifact'] = str(target.relative_to(ROOT))
    return record
