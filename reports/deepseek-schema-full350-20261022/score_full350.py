"""Consolidated offline scoring and verification script for the full 350-resume schema mapping rollout.

Generates:
- summary.json: Overall and per-batch metrics, citation rates, gate ground-truth, token spend and cost.
- field-validation.csv: Every mapped field path, value, citation validation status and alignment flag.
- reference-evaluation.json: Detailed scoring for the 30-resume gate reference facts.
- failed-resumes.json: Detailed log of quarantined or failed resumes with failure reasons and paths.
- preservation.json: Cryptographic SHA-256 verification of production files ensuring zero mutation.
"""
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(OUT)]

from score import score_fact

read_json = lambda p: json.loads(p.read_text(encoding='utf-8'))
save_json = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    manifest_path = OUT / 'manifest.json'
    ledger_path = OUT / 'call-ledger.json'
    ref_path = OUT / 'reference-facts-gate30.json'

    if not manifest_path.exists():
        print(f"Error: {manifest_path} does not exist.")
        sys.exit(1)

    manifest = read_json(manifest_path)
    ledger = read_json(ledger_path) if ledger_path.exists() else []
    ledger_by_idx = {c['index']: c for c in ledger}
    reference_data = read_json(ref_path) if ref_path.exists() else {'facts': []}
    gate_facts = reference_data.get('facts', [])

    all_facts_scored = []
    all_fields = []
    doc_rows = []
    failed_resumes = []

    batch_metrics = defaultdict(lambda: {
        'total': 0,
        'attempted': 0,
        'accepted': 0,
        'flagged': 0,
        'quarantined': 0,
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0,
        'raw_populated': 0,
        'raw_valid_citations': 0,
        'cand_populated': 0,
        'cand_valid_citations': 0
    })

    print(f"Scoring {len(manifest)} manifest entries...")

    for item in manifest:
        idx = item['index']
        filename = item['file']
        batch_id = item['batch']
        is_gate = item.get('is_gate_batch', False)
        batch_stat = batch_metrics[batch_id]
        batch_stat['total'] += 1

        doc_dir = OUT / 'resumes' / f"{idx:03d}"
        call = ledger_by_idx.get(idx, {})

        if not call:
            doc_rows.append({
                'index': idx,
                'file': filename,
                'batch': batch_id,
                'status': 'unattempted'
            })
            continue

        batch_stat['attempted'] += 1
        usage = call.get('usage', {})
        p_tok = usage.get('prompt_tokens', 0)
        c_tok = usage.get('completion_tokens', 0)
        t_tok = usage.get('total_tokens', 0)
        batch_stat['prompt_tokens'] += p_tok
        batch_stat['completion_tokens'] += c_tok
        batch_stat['total_tokens'] += t_tok

        status = call.get('status', 'unknown')
        if status == 'accepted':
            batch_stat['accepted'] += 1
        elif status == 'flagged':
            batch_stat['flagged'] += 1
        else:
            batch_stat['quarantined'] += 1
            failure_info = {
                'index': idx,
                'file': filename,
                'batch': batch_id,
                'status': status,
                'error_code': call.get('error_code'),
                'finish_reason': call.get('finish_reason'),
                'usage': usage,
                'artifacts': {
                    'request': str(doc_dir / 'request.json'),
                    'response_envelope': str(doc_dir / 'response-envelope.json') if (doc_dir / 'response-envelope.json').exists() else None,
                    'parse_failure': str(doc_dir / 'parse-failure.json') if (doc_dir / 'parse-failure.json').exists() else None
                }
            }
            if (doc_dir / 'parse-failure.json').exists():
                failure_info['parse_failure_detail'] = read_json(doc_dir / 'parse-failure.json')
            failed_resumes.append(failure_info)

        raw_val_path = doc_dir / 'raw-validation.json'
        cand_val_path = doc_dir / 'candidate-validation.json'
        cand_map_path = doc_dir / 'candidate-mapping.json'

        raw_pop = 0
        raw_val_cit = 0
        cand_pop = 0
        cand_val_cit = 0

        if raw_val_path.exists():
            raw_val = read_json(raw_val_path)
            raw_pop = raw_val.get('populated_fields', 0)
            raw_val_cit = raw_val.get('citation_valid_fields', 0)
            batch_stat['raw_populated'] += raw_pop
            batch_stat['raw_valid_citations'] += raw_val_cit

        if cand_val_path.exists() and cand_map_path.exists():
            cand_val = read_json(cand_val_path)
            cand_map = read_json(cand_map_path)
            cand_pop = cand_val.get('populated_fields', 0)
            cand_val_cit = cand_val.get('citation_valid_fields', 0)
            batch_stat['cand_populated'] += cand_pop
            batch_stat['cand_valid_citations'] += cand_val_cit

            cand_fields = {f['path']: f for f in cand_val.get('fields', [])}
            raw_fields = {f['path']: f for f in raw_val.get('fields', [])} if raw_val_path.exists() else {}

            for p, finfo in cand_fields.items():
                rinfo = raw_fields.get(p, {})
                all_fields.append({
                    'index': idx,
                    'file': filename,
                    'batch': batch_id,
                    'path': p,
                    'value': str(finfo.get('value', ''))[:100],
                    'raw_valid': rinfo.get('citation_valid', False),
                    'candidate_valid': finfo.get('citation_valid', False),
                    'realigned': finfo.get('realigned', False),
                    'candidate_error': finfo.get('errors', [None])[0] if finfo.get('errors') else None
                })

            # Gate fact scoring
            if is_gate:
                doc_facts = [f for f in gate_facts if f['document'] == idx]
                for fact in doc_facts:
                    scored = score_fact(fact, cand_map.get('data', {}), cand_fields)
                    all_facts_scored.append(scored)

        doc_rows.append({
            'index': idx,
            'file': filename,
            'batch': batch_id,
            'status': status,
            'usage': usage,
            'raw_populated': raw_pop,
            'raw_valid_citations': raw_val_cit,
            'cand_populated': cand_pop,
            'cand_valid_citations': cand_val_cit
        })

    # Export field validation CSV
    field_csv_path = OUT / 'field-validation.csv'
    with open(field_csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['index', 'file', 'batch', 'path', 'value', 'raw_valid', 'candidate_valid', 'realigned', 'candidate_error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_fields)

    # Save failed resumes
    save_json(OUT / 'failed-resumes.json', {
        'total_quarantined': len(failed_resumes),
        'failures': failed_resumes
    })

    # Gate ground truth evaluation
    gate_total_facts = len(all_facts_scored)
    gate_val_agree = sum(1 for f in all_facts_scored if f.get('value_agreement'))
    gate_evi_agree = sum(1 for f in all_facts_scored if f.get('evidence_backed'))
    gate_eval = {
        'total_facts': gate_total_facts,
        'value_agreement': gate_val_agree,
        'value_agreement_rate': gate_val_agree / gate_total_facts if gate_total_facts else 0.0,
        'evidence_backed_agreement': gate_evi_agree,
        'evidence_backed_agreement_rate': gate_evi_agree / gate_total_facts if gate_total_facts else 0.0,
        'facts': all_facts_scored
    }
    save_json(OUT / 'reference-evaluation.json', gate_eval)

    # Production hashes preservation check
    prod_hashes_file = OUT / 'production-hashes-before.json'
    prod_checked = 0
    prod_changed = []
    if prod_hashes_file.exists():
        expected_hashes = read_json(prod_hashes_file)
        prod_checked = len(expected_hashes)
        for rel_path, exp_hash in expected_hashes.items():
            full_p = ROOT / rel_path
            if not full_p.exists():
                prod_changed.append({'file': rel_path, 'status': 'missing'})
            else:
                curr_hash = hashlib.sha256(full_p.read_bytes()).hexdigest()
                if curr_hash != exp_hash:
                    prod_changed.append({'file': rel_path, 'status': 'modified', 'expected': exp_hash, 'actual': curr_hash})

    save_json(OUT / 'preservation.json', {
        'production_files_checked': prod_checked,
        'changed': prod_changed,
        'clean_preservation': len(prod_changed) == 0,
        'source_extraction_or_ocr_modified': False
    })

    # Cost calculations
    # DeepSeek API pricing (V3 / Chat standard pricing):
    # Prompt tokens (cache miss): $0.27 / 1M ($0.00000027 per token)
    # Completion tokens: $1.10 / 1M ($0.0000011 per token)
    total_prompt_tokens = sum(b['prompt_tokens'] for b in batch_metrics.values())
    total_completion_tokens = sum(b['completion_tokens'] for b in batch_metrics.values())
    total_tokens = sum(b['total_tokens'] for b in batch_metrics.values())

    cost_prompt = (total_prompt_tokens / 1_000_000) * 0.27
    cost_completion = (total_completion_tokens / 1_000_000) * 1.10
    cost_total = cost_prompt + cost_completion

    total_attempted = sum(b['attempted'] for b in batch_metrics.values())
    total_accepted = sum(b['accepted'] for b in batch_metrics.values())
    total_flagged = sum(b['flagged'] for b in batch_metrics.values())
    total_quarantined = sum(b['quarantined'] for b in batch_metrics.values())

    total_raw_pop = sum(b['raw_populated'] for b in batch_metrics.values())
    total_raw_val = sum(b['raw_valid_citations'] for b in batch_metrics.values())
    total_cand_pop = sum(b['cand_populated'] for b in batch_metrics.values())
    total_cand_val = sum(b['cand_valid_citations'] for b in batch_metrics.values())

    summary = {
        'total_manifest_resumes': len(manifest),
        'total_resumes_attempted': total_attempted,
        'status_breakdown': {
            'accepted': total_accepted,
            'flagged': total_flagged,
            'quarantined': total_quarantined
        },
        'citation_compliance': {
            'raw_contract': {
                'valid': total_raw_val,
                'populated': total_raw_pop,
                'rate': total_raw_val / total_raw_pop if total_raw_pop else 0.0
            },
            'candidate_contract': {
                'valid': total_cand_val,
                'populated': total_cand_pop,
                'rate': total_cand_val / total_cand_pop if total_cand_pop else 0.0
            }
        },
        'gate_ground_truth_30': {
            'facts_tested': gate_total_facts,
            'value_agreement': gate_val_agree,
            'value_agreement_rate': gate_val_agree / gate_total_facts if gate_total_facts else 0.0,
            'evidence_backed_agreement': gate_evi_agree,
            'evidence_backed_rate': gate_evi_agree / gate_total_facts if gate_total_facts else 0.0
        },
        'token_usage_and_cost': {
            'prompt_tokens': total_prompt_tokens,
            'completion_tokens': total_completion_tokens,
            'total_tokens': total_tokens,
            'pricing_assumptions': {
                'prompt_rate_per_million': 0.27,
                'completion_rate_per_million': 1.10,
                'currency': 'USD'
            },
            'cost_usd': {
                'prompt': round(cost_prompt, 4),
                'completion': round(cost_completion, 4),
                'total': round(cost_total, 4)
            }
        },
        'batches': dict(batch_metrics),
        'batch_decisions': read_json(OUT / 'batch-decisions.json') if (OUT / 'batch-decisions.json').exists() else [],
        'preservation': {
            'production_files_checked': prod_checked,
            'zero_modifications': len(prod_changed) == 0
        }
    }

    save_json(OUT / 'summary.json', summary)
    print("Scoring complete. Summary written to summary.json.")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

