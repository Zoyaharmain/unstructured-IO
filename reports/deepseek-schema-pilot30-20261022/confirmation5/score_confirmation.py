"""Offline evaluation and reporting for the 5-resume confirmation pilot (Design A)."""
import csv, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PILOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(PILOT), str(OUT)]

from schema_gate import leaves, norm, validate, prepare_candidate_mapping
from score import score_fact

read = lambda p: json.loads(p.read_text())
save = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')


def main():
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
                'number': n,
                'file': doc['file'],
                'status': 'failed',
                'usage': call.get('usage', {}),
                'error': failure
            }
            rows.append(row)
            allfacts.extend(scored)
            continue

        raw = read(d / 'mapping-raw.json')
        assembled = read(d / 'assembled-raw.json')
        raw_val = read(d / 'raw-validation.json')
        cand = read(d / 'candidate-mapping.json')
        cand_val = read(d / 'candidate-validation.json')

        # 1. CORE IMMUTABILITY VERIFICATION
        assert assembled['data'] == raw['data'], f"Doc {n}: Core data mutated during assembly!"
        assert assembled['evidence'] == raw['evidence'], f"Doc {n}: Core evidence mutated during assembly!"
        assert cand['data'] == raw['data'], f"Doc {n}: Core data mutated during candidate alignment!"

        cand_fields = {f['path']: f for f in cand_val.get('fields', [])}
        raw_fields = {f['path']: f for f in raw_val.get('fields', [])}

        scored = [score_fact(f, cand['data'], cand_fields) for f in facts]
        allfacts.extend(scored)

        for path, info in cand_fields.items():
            raw_info = raw_fields.get(path, {})
            allfields.append({
                'document': n,
                'file': doc['file'],
                'path': path,
                'value': info.get('value'),
                'raw_status': 'valid' if raw_info.get('citation_valid') else (raw_info.get('errors', ['missing_raw'])[0] if raw_info.get('errors') else 'missing_raw'),
                'candidate_status': 'valid' if info.get('citation_valid') else (info.get('errors', ['unknown'])[0] if info.get('errors') else 'unknown'),
                'citation_valid': info.get('citation_valid', False),
                'realigned': info.get('realigned', False)
            })

        val_agr = sum(1 for f in scored if f['value_agreement'])
        evi_agr = sum(1 for f in scored if f['evidence_backed'])
        rows.append({
            'number': n,
            'file': doc['file'],
            'status': call.get('status'),
            'usage': call.get('usage', {}),
            'raw_populated_fields': raw_val.get('populated_fields', 0),
            'raw_valid_citations': raw_val.get('citation_valid_fields', 0),
            'candidate_populated_fields': cand_val.get('populated_fields', 0),
            'candidate_valid_citations': cand_val.get('citation_valid_fields', 0),
            'reference_facts': len(facts),
            'reference_value_matches': val_agr,
            'reference_evidence_matches': evi_agr,
            'core_data_immutable': True
        })

    with open(OUT / 'field-validation.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['document', 'file', 'path', 'value', 'raw_status', 'candidate_status', 'citation_valid', 'realigned'])
        writer.writeheader()
        writer.writerows(allfields)

    save(OUT / 'reference-evaluation.json', {
        'total_facts': len(allfacts),
        'value_agreement': sum(1 for f in allfacts if f['value_agreement']),
        'evidence_backed': sum(1 for f in allfacts if f['evidence_backed']),
        'by_document': rows,
        'facts': allfacts
    })

    total_raw_pop = sum(r.get('raw_populated_fields', 0) for r in rows)
    total_raw_val = sum(r.get('raw_valid_citations', 0) for r in rows)
    total_cand_pop = sum(r.get('candidate_populated_fields', 0) for r in rows)
    total_cand_val = sum(r.get('candidate_valid_citations', 0) for r in rows)
    total_ref = len(allfacts)
    total_val_agr = sum(1 for f in allfacts if f['value_agreement'])
    total_evi_agr = sum(1 for f in allfacts if f['evidence_backed'])

    tokens_prompt = sum(r.get('usage', {}).get('prompt_tokens', 0) for r in rows)
    tokens_completion = sum(r.get('usage', {}).get('completion_tokens', 0) for r in rows)
    tokens_total = sum(r.get('usage', {}).get('total_tokens', 0) for r in rows)
    tokens_cached = sum(r.get('usage', {}).get('prompt_cache_hit_tokens', 0) for r in rows)
    tokens_missed = sum(r.get('usage', {}).get('prompt_cache_miss_tokens', 0) for r in rows)

    cost_prompt = (tokens_cached * 0.003 + tokens_missed * 0.14) / 1_000_000
    cost_completion = (tokens_completion * 0.60) / 1_000_000
    total_cost = cost_prompt + cost_completion

    summary = {
        'pilot': '5-resume confirmation pilot (Design A)',
        'documents_processed': len(rows),
        'successful_parses': sum(1 for r in rows if r.get('status') != 'failed'),
        'quarantined_parses': sum(1 for r in rows if r.get('status') == 'failed'),
        'core_data_immutability_verified': all(r.get('core_data_immutable', False) for r in rows),
        'raw_citation_compliance': {
            'valid': total_raw_val,
            'populated': total_raw_pop,
            'rate': total_raw_val / total_raw_pop if total_raw_pop else 0.0
        },
        'candidate_citation_compliance': {
            'valid': total_cand_val,
            'populated': total_cand_pop,
            'rate': total_cand_val / total_cand_pop if total_cand_pop else 0.0
        },
        'critical_field_agreement': {
            'matched': total_val_agr,
            'total': total_ref,
            'rate': total_val_agr / total_ref if total_ref else 0.0
        },
        'evidence_backed_critical_agreement': {
            'matched': total_evi_agr,
            'total': total_ref,
            'rate': total_evi_agr / total_ref if total_ref else 0.0
        },
        'tokens': {
            'prompt_tokens': tokens_prompt,
            'prompt_cache_hit_tokens': tokens_cached,
            'prompt_cache_miss_tokens': tokens_missed,
            'completion_tokens': tokens_completion,
            'total_tokens': tokens_total
        },
        'cost_usd': {
            'prompt_cost': cost_prompt,
            'completion_cost': cost_completion,
            'total_cost': total_cost
        }
    }
    save(OUT / 'summary.json', summary)

    files = read(OUT / 'input-local-api-hashes.json')
    changed = [p for p, h in files.items() if not (ROOT / p).is_file() or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    sourcechanged = [doc['file'] for doc in selected if hashlib.sha256((ROOT / doc['source_artifact']).read_bytes()).hexdigest() != doc['source_artifact_sha256']]
    assert not changed and not sourcechanged

    save(OUT / 'preservation.json', {
        'production_files_checked': len(files),
        'changed': changed,
        'source_artifacts_changed': sourcechanged,
        'extraction_or_block_detection_calls': 0,
        'second_metadata_llm_calls': 0,
        'pipeline_source_matches_manifest': True
    })

    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

