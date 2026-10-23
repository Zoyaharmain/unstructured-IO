"""Run the audit harness over the selected known-case set (provider-free)."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_harness import audit_document

OUT = Path(__file__).resolve().parent
DOCS = OUT / 'local-run' / 'documents'
DOCS.mkdir(parents=True, exist_ok=True)

R = ROOT / 'reports/repair-existing350-20261021'
index = {entry['file']: entry for entry in json.loads((R / 'repaired-350/current-results.json').read_text())}
paths = {}
for sub in ('source-geometry-repair/documents', 'repaired-350/provider-recoveries'):
    for path in (R / sub).glob('*.json'):
        paths[path.stem] = path

SELECTED = json.loads((OUT / 'selected-cases.json').read_text())
records = []
for item in SELECTED:
    name = item['file']
    entry = index.get(name)
    if entry is None:
        records.append({'file': name, 'status': 'not_in_350_index'})
        continue
    pdf = ROOT / item['pdf']
    if not pdf.is_file():
        records.append({'file': name, 'status': 'pdf_not_found', 'expected_path': str(pdf)})
        continue
    saved = json.loads(paths[entry['sha256']].read_text())
    try:
        record = audit_document(pdf, entry, saved, DOCS)
        record['status'] = 'processed'
    except Exception as exc:  # keep the batch alive and record the failure type
        record = {'file': name, 'status': 'error', 'error_type': type(exc).__name__,
                  'error': str(exc)[:200]}
    records.append(record)
    print(json.dumps({'file': name, 'status': record.get('status'),
                      'sections': record.get('sections'),
                      'needs_review': record.get('needs_review_blocks'),
                      'integrity_errors': len(record.get('source_interval_errors') or []),
                      'recall': record.get('reference_token_recall')}), flush=True)

(OUT / 'local-run' / 'results.json').write_text(json.dumps(records, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'documents': len(records)}, indent=1))
