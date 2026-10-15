#!/usr/bin/env python3
"""Compare complete ordered serialized outputs in isolated upstream and port processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

WORKER = r'''
import json, sys, importlib.util
from pathlib import Path
mode, source, pdf, destination, settings_file = sys.argv[1:]
settings = json.loads(Path(settings_file).read_text())
if mode == 'upstream':
    sys.path.insert(0, source)
    from unstructured.partition.pdf import partition_pdf
    elements = [e.to_dict() for e in partition_pdf(filename=pdf, strategy='hi_res', **settings)]
else:
    from pdf_hires import extract_pdf
    assert importlib.util.find_spec('unstructured') is None, 'Full Unstructured must be absent'
    elements = extract_pdf(pdf, **settings)
    assert [e.pop('reading_order') for e in elements] == list(range(1, len(elements)+1))
Path(destination).write_text(json.dumps(elements, indent=2, ensure_ascii=False)+'\n')
'''


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--upstream-source', type=Path, required=True, help='Archive extraction containing unstructured/')
    p.add_argument('--upstream-python', required=True)
    p.add_argument('--port-python', default=sys.executable)
    p.add_argument('--settings', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('reports/comparison'))
    p.add_argument('pdfs', type=Path, nargs='+')
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, DO_NOT_TRACK='true', HF_HUB_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='2')
    environment.pop('PYTHONPATH', None)
    reports = []
    for pdf in args.pdfs:
        pdf = pdf.resolve()
        result = {'pdf': pdf.name, 'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()}
        outputs = {}
        for mode, python in [('upstream', args.upstream_python), ('port', args.port_python)]:
            dest = (args.output / (pdf.stem + '.' + mode + '.json')).resolve()
            proc = subprocess.run([python, '-c', WORKER, mode, str(args.upstream_source.resolve()),
                str(pdf), str(dest), str(args.settings.resolve())], env=environment,
                capture_output=True, text=True)
            (args.output / (pdf.stem + '.' + mode + '.log')).write_text(proc.stdout + proc.stderr)
            result[mode + '_returncode'] = proc.returncode
            if proc.returncode == 0:
                outputs[mode] = json.loads(dest.read_text())
            else:
                print(mode, pdf.name, proc.stderr[-1800:], flush=True)
        if len(outputs) == 2:
            a, b = outputs['upstream'], outputs['port']
            result.update(upstream_elements=len(a), port_elements=len(b), exact_ordered_match=a == b)
            result['differences'] = []
            for i in range(max(len(a), len(b))):
                if i >= len(a) or i >= len(b):
                    result['differences'].append({'index': i, 'field': 'missing_element'})
                    continue
                for field in sorted(set(a[i]) | set(b[i])):
                    if a[i].get(field) != b[i].get(field):
                        result['differences'].append({'index': i, 'field': field,
                            'upstream': a[i].get(field), 'port': b[i].get(field)})
        reports.append(result)
        print(json.dumps({k:v for k,v in result.items() if k!='differences'}), flush=True)
    report = {'settings': json.loads(args.settings.read_text()), 'comparisons': reports}
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    return 0 if all(x.get('exact_ordered_match') for x in reports) else 1

if __name__ == '__main__':
    sys.exit(main())
