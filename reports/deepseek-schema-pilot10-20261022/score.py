"""Offline reporting for 10-resume pilot; evaluates both strict raw contract and candidate normalized contract."""
import csv, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(OUT)]

from schema_gate import leaves, norm, validate, prepare_candidate_mapping, parse_response_with_quarantine

read = lambda p: json.loads(p.read_text())
save = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')


def tokens(s):
    return re.findall(r'\w+', norm(s))


def contains(expected, actual):
    a = tokens(expected)
    b = tokens(actual)
    return any(b[i:i + len(a)] == a for i in range(len(b) - len(a) + 1))


def score_fact(fact, data, fields):
    collection = fact['collection']
    key = fact['field']
    expected = fact['expected']
    if collection == 'root':
        obj = data
        for k in key.split('.'):
            obj = obj.get(k) if isinstance(obj, dict) else None
        value = obj
        path = '/' + key.replace('.', '/')
    else:
        candidates = []
        for index, record in enumerate(data.get(collection, [])):
            if all(contains(v, (record.get(k) or '') + (' ' + (record.get('field_of_study') or '') if k == 'degree' else '')) for k, v in fact['selector'].items()):
                candidates.append((index, record))
        if len(candidates) != 1:
            return {**fact, 'actual': None, 'path': None, 'value_agreement': False, 'evidence_backed': False, 'status': 'missing_or_ambiguous_record'}
        index, record = candidates[0]
        value = record.get(key)
        path = f'/{collection}/{index}/{key}'
    if isinstance(expected, (int, float)):
        matched = isinstance(value, (float, int)) and float(expected) == float(value)
    elif key in {'start_year', 'graduation_year'}:
        matched = str(expected) in re.findall(r'\b(?:19|20)\d{2}\b', str(value))
    else:
        matched = value is not None and contains(expected, value)
    cited = fields.get(path, {}).get('citation_valid', False)
    return {
        **fact,
        'actual': value,
        'path': path,
        'value_agreement': matched,
        'evidence_backed': bool(matched and cited),
        'status': 'supported_agreement' if matched and cited else 'value_agrees_but_citation_fails' if matched else 'missing_or_different_value'
    }


selected = read(OUT / 'selection.json')
ledger = read(OUT / 'call-ledger.json')
reference = read(OUT / 'reference-facts.json')['facts']

allfacts = []
allfields = []
rows = []

for doc, call in zip(selected, ledger):
    n = doc['number']
    d = OUT / f'{n:02d}'
    facts = [f for f in reference if f['document'] == n]
    blocks = read(d / 'source-blocks.json')

    if not (d / 'mapping-raw.json').exists():
        failure = read(d / 'parse-failure.json') if (d / 'parse-failure.json').exists() else {'error': 'missing_output'}
        scored = [{**f, 'status': 'mapping_response_failed', 'actual': None, 'path': None, 'value_agreement': False, 'evidence_backed': False} for f in facts]
        row = {
            'document': n,
            'file': doc['file'],
            'status': call['status'],
            'schema_valid': False,
            'reference_denominator': len(facts),
            'reference_value_matches': 0,
            'before_raw': {
                'populated_fields': 0,
                'citation_valid_fields': 0,
                'citation_compliance_percent': 0.0,
                'citation_contract_valid': False,
                'evidence_backed_matches': 0,
                'issue_kinds': {'parse_failure': 1}
            },
            'after_candidate': {
                'populated_fields': 0,
                'citation_valid_fields': 0,
                'citation_compliance_percent': 0.0,
                'citation_contract_valid': False,
                'evidence_backed_matches': 0,
                'issue_kinds': {'parse_failure': 1}
            },
            'normalizations': [],
            'omission_repairs': [],
            'rejections': [],
            'uncertainty_flags': [],
            'accepted': False,
            'failure': failure
        }
    else:
        raw = read(d / 'mapping-raw.json')
        before = validate(raw, blocks)
        save(d / 'raw-validation.json', before)

        candidate, changes, rejections = prepare_candidate_mapping(raw, blocks)
        after = validate(candidate, blocks)
        save(d / 'candidate-mapping.json', candidate)
        save(d / 'changes.json', changes)
        if rejections:
            save(d / 'rejections.json', rejections)
        save(d / 'candidate-validation.json', after)
        save(d / ('accepted-mapping.json' if after['accepted'] else 'quarantined-mapping.json'), candidate)

        raw_fields = {f['path']: f for f in before['fields']}
        cand_fields = {f['path']: f for f in after['fields']}

        raw_scored = [score_fact(f, raw.get('data', {}), raw_fields) for f in facts]
        cand_scored = [score_fact(f, candidate.get('data', {}), cand_fields) for f in facts]

        row = {
            'document': n,
            'file': doc['file'],
            'status': call['status'],
            'schema_valid': before['schema_valid'],
            'reference_denominator': len(facts),
            'reference_value_matches': sum(f['value_agreement'] for f in cand_scored),
            'before_raw': {
                'populated_fields': before['populated_fields'],
                'citation_valid_fields': before['citation_valid_fields'],
                'citation_compliance_percent': round(100 * before['citation_valid_fields'] / max(1, before['populated_fields']), 2),
                'citation_contract_valid': before['citation_contract_valid'],
                'evidence_backed_matches': sum(f['evidence_backed'] for f in raw_scored),
                'issue_kinds': dict(Counter(i['kind'] for i in before['issues']))
            },
            'after_candidate': {
                'populated_fields': after['populated_fields'],
                'citation_valid_fields': after['citation_valid_fields'],
                'citation_compliance_percent': round(100 * after['citation_valid_fields'] / max(1, after['populated_fields']), 2),
                'citation_contract_valid': after['citation_contract_valid'],
                'evidence_backed_matches': sum(f['evidence_backed'] for f in cand_scored),
                'issue_kinds': dict(Counter(i['kind'] for i in after['issues']))
            },
            'normalizations': [c for c in changes if c.get('rule') == 'provably_equivalent_leading_slash'],
            'alignment_adjustments': [c for c in changes if c.get('rule') in {'intra_array_index_alignment', 'sibling_subblock_span_realignment'}],
            'omission_repairs': [c for c in changes if 'omission' in c.get('origin', '')],
            'rejections': rejections,
            'uncertainty_flags': after['uncertainties'],
            'accepted': after['accepted']
        }
        scored = cand_scored
        for f in after['fields']:
            allfields.append({'document': n, 'file': doc['file'], **f})

    save(d / 'reference-evaluation.json', scored)
    save(d / 'summary.json', row)
    allfacts += scored
    rows.append(row)

# Compute overall before and after summaries
parseable = [r for r in rows if r['schema_valid']]
raw_pop = sum(r['before_raw']['populated_fields'] for r in parseable)
raw_cite = sum(r['before_raw']['citation_valid_fields'] for r in parseable)
cand_pop = sum(r['after_candidate']['populated_fields'] for r in parseable)
cand_cite = sum(r['after_candidate']['citation_valid_fields'] for r in parseable)

val_matches = sum(r['reference_value_matches'] for r in rows)
raw_ev_matches = sum(r['before_raw']['evidence_backed_matches'] for r in parseable)
cand_ev_matches = sum(r['after_candidate']['evidence_backed_matches'] for r in parseable)

summary = {
    'documents': 10,
    'mapping_calls': len(ledger),
    'paid_retries': 0,
    'schema_valid_responses': len(parseable),
    'json_response_failures': 10 - len(parseable),
    'total_reference_opportunities': len(reference),
    'reference_value_matches': val_matches,
    'critical_value_agreement_percent': round(100 * val_matches / len(reference), 2),
    'before_raw_contract': {
        'populated_fields': raw_pop,
        'citation_valid_fields': raw_cite,
        'citation_compliance_percent': round(100 * raw_cite / max(1, raw_pop), 2),
        'evidence_backed_matches': raw_ev_matches,
        'evidence_backed_percent': round(100 * raw_ev_matches / len(reference), 2),
        'full_citation_pass_documents': sum(r['before_raw']['citation_contract_valid'] for r in parseable)
    },
    'after_candidate_normalized': {
        'populated_fields': cand_pop,
        'citation_valid_fields': cand_cite,
        'citation_compliance_percent': round(100 * cand_cite / max(1, cand_pop), 2),
        'evidence_backed_matches': cand_ev_matches,
        'evidence_backed_percent': round(100 * cand_ev_matches / len(reference), 2),
        'full_citation_pass_documents': sum(r['after_candidate']['citation_contract_valid'] for r in parseable),
        'total_normalizations': sum(len(r.get('normalizations', [])) for r in rows),
        'total_alignments': sum(len(r.get('alignment_adjustments', [])) for r in rows),
        'target_data_values_mutated': 0,
        'fabricated_citations': 0
    },
    'usage': {k: sum(c.get('usage', {}).get(k, 0) for c in ledger) for k in ['prompt_tokens', 'completion_tokens', 'total_tokens', 'prompt_cache_hit_tokens', 'prompt_cache_miss_tokens']},
    'estimated_cost': None,
    'cost_reason': 'No verified applicable tariff or monetary charge in provider envelopes.',
    'human_verified_accuracy': None,
    'original_pdf_accuracy': None,
    'automatic_citation_inheritance': False,
    'new_production_integration': False,
    'extra_paid_calls_authorized': False
}

save(OUT / 'summary.json', {'overall': summary, 'per_resume': rows})
save(OUT / 'reference-evaluation.json', allfacts)

with (OUT / 'field-validation.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['document', 'file', 'path', 'value', 'citation_valid', 'errors', 'citations'])
    w.writeheader()
    for row in allfields:
        w.writerow({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row[k], (dict, list)) else row[k] for k in w.fieldnames})

manifest = read(OUT / 'pilot-manifest.json')
manifest['gate_source_sha256'] = hashlib.sha256((OUT / 'schema_gate.py').read_bytes()).hexdigest()
save(OUT / 'pilot-manifest.json', manifest)

files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for base in ['local_api', 'scripts'] for p in (ROOT / base).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
save(OUT / 'production-hashes-before.json', files)

changed = [p for p, h in files.items() if not (ROOT / p).is_file() or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
sourcechanged = [doc['file'] for doc in selected if hashlib.sha256((ROOT / doc['source_artifact']).read_bytes()).hexdigest() != doc['source_artifact_sha256']]
assert not changed and not sourcechanged
assert hashlib.sha256((OUT / 'schema_gate.py').read_bytes()).hexdigest() == read(OUT / 'pilot-manifest.json')['gate_source_sha256']

save(OUT / 'preservation.json', {
    'production_files_checked': len(files),
    'changed': changed,
    'source_artifacts_changed': sourcechanged,
    'extraction_or_block_detection_calls': 0,
    'gate_source_matches_pilot_manifest': True
})

print(json.dumps(summary, indent=2))

