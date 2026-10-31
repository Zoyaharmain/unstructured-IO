"""Replay saved source-bound resume artifacts offline; never overwrite inputs."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sys
import subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_api.schemas.mapping import SchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.standardization.mapping import mapping_input, attach_mapping_findings
from local_api.services.standardization.service import standardize_resume_data
from local_api.services.standardization.export import standardized_export
from local_api.services.standardization.consumer import ConsumerResume


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline-mappings', type=Path)
    args = parser.parse_args()
    if args.output.exists(): parser.error('Output must be new; existing reports are immutable')
    def blocked(*a, **k): raise RuntimeError('Network forbidden during offline replay')
    socket.socket.connect = blocked
    socket.create_connection = blocked
    rows = []
    baseline = json.loads(args.baseline_mappings.read_text()) if args.baseline_mappings else {}
    source_paths = subprocess.run(['rg', '--files', '-g', '*.pdf', '-g', '*.docx'],
        cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    source_hashes = {r['file']: r.get('sha256') for r in json.loads((args.run / 'results.json').read_text())}
    from scripts.audit_saved_resume_outputs import original_text, normalized, literals
    args.output.mkdir(parents=True)
    before = {p: digest(p) for p in args.run.rglob('*') if p.is_file()}
    artifacts = sorted((args.run / 'documents').glob('*.schema.json'))
    for i, saved_path in enumerate(artifacts, 1):
        original_path = saved_path.with_name(saved_path.name.replace('.schema.json', '.json'))
        original = json.loads(original_path.read_text())
        previous = json.loads(saved_path.read_text())
        request = SchemaMappingRequest.model_validate({'elements': original['extraction']['elements'],
            'sections': original['sections'], 'source': original['file']})
        mapped = map_schema(request)
        data = mapping_input(mapped)
        snapshot = deepcopy(data)
        std, meta, status, warnings = standardize_resume_data(data,
            reference_date=datetime(2026, 10, 30, tzinfo=timezone.utc))
        assert data == snapshot
        mapped.standardized_data, mapped.standardization_metadata = std, meta
        mapped.validation_status, mapped.warnings = status, warnings
        attach_mapping_findings(mapped, warnings)
        audited = standardized_export(mapped, include_audit=True)
        ConsumerResume.model_validate(audited['data'])
        differences = []
        for category, identity in {'experience': ('company', 'role', 'responsibilities'),
                                   'education': ('institution', 'degree'),
                                   'projects': ('name', 'description'), 'certifications': ('name',)}.items():
            old, new = previous['data'].get(category, []), mapped.data.model_dump()[category]
            if len(old) != len(new): differences.append(category + '.record_count')
            for n, (left, right) in enumerate(zip(old, new)):
                for key in identity:
                    if left.get(key) != right.get(key): differences.append(f'{category}[{n}].{key}')
        baseline_differences = []
        if original['file'] in baseline:
            for category, keys in {'experience': ('company', 'role', 'responsibilities'),
                                   'education': ('institution', 'degree'), 'projects': ('name', 'description'),
                                   'certifications': ('name',)}.items():
                left, right = baseline[original['file']][category], mapped.data.model_dump()[category]
                if len(left) != len(right): baseline_differences.append(category + '.record_count')
                for n, (a, b) in enumerate(zip(left, right)):
                    baseline_differences.extend(f'{category}[{n}].{k}' for k in keys if a[k] != b[k])
        source_matches = [ROOT / p for p in source_paths if Path(p).name == original['file']
                          and digest(ROOT / p) == source_hashes.get(original['file'])]
        independent = {'original_available_with_matching_hash': bool(source_matches)}
        if source_matches:
            text = normalized(original_text(source_matches[0]))
            values = list(literals(mapped.data.model_dump()))
            independent.update(literal_checks=len(values),
                unconfirmed_paths=[path for path, literal in values if normalized(literal) not in text],
                reader='pdftotext -layout' if source_matches[0].suffix.lower() == '.pdf' else 'original DOCX XML')
        rows.append({'file': original['file'], 'source_format': Path(original['file']).suffix,
            'saved_mapping_sha256': before[saved_path], 'original_extraction_elements': len(request.elements),
            'prior_identity_or_responsibility_differences': differences,
            'before': {'candidate_sections': sorted(previous['data']),
                       'awards_in_candidate_data': len(previous['data'].get('awards', []))},
            'after': {'candidate_sections': sorted(audited['data']),
                      'awards_in_candidate_data': len(audited['data']['awards']),
                      'additional_content_records': len(audited['data']['additional_sections']),
                      'validation_status': audited['validation_status'],
                      'warning_types': dict(Counter(w.warning_type for w in warnings))},
            'source_bindings_validated': True, 'input_unchanged': True,
            'baseline_replay_identity_or_responsibility_differences': baseline_differences if baseline else None,
            'independent_original_comparison': independent})
        (args.output / f'{i:02d}.audit.json').write_text(json.dumps(audited, indent=2, ensure_ascii=False) + '\n')
    assert all(digest(p) == value for p, value in before.items())
    summary = {'resumes': len(rows), 'formats': dict(Counter(r['source_format'] for r in rows)),
        'source_bound_replays_passed': len(rows),
        'prior_identity_or_responsibility_difference_documents': sum(bool(r['prior_identity_or_responsibility_differences']) for r in rows),
        'awards_promoted_to_candidate_data': sum(r['after']['awards_in_candidate_data'] for r in rows),
        'additional_content_records_preserved': sum(r['after']['additional_content_records'] for r in rows),
        'baseline_replay_identity_or_responsibility_difference_documents': sum(bool(r['baseline_replay_identity_or_responsibility_differences']) for r in rows) if baseline else None,
        'independent_originals_compared': sum(r['independent_original_comparison']['original_available_with_matching_hash'] for r in rows),
        'independent_literal_checks': sum(r['independent_original_comparison'].get('literal_checks', 0) for r in rows),
        'independent_unconfirmed_values': sum(len(r['independent_original_comparison'].get('unconfirmed_paths', [])) for r in rows),
        'requires_review': sum(r['after']['validation_status']['requires_human_review'] for r in rows),
        'network_calls': 0, 'saved_inputs_unchanged': True,
        'limitations': 'Replays saved extraction and section boundaries. Does not re-extract PDFs/DOCX or establish visual/semantic completeness against original documents.'}
    (args.output / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
