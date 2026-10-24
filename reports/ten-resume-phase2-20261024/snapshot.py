import hashlib,json
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'reports/ten-resume-phase2-20261024'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p):sha(p) for name in ['reports','ground_truth','tests/fixtures'] for p in (ROOT/name).rglob('*') if p.is_file() and OUT not in p.parents and '__pycache__' not in p.parts}
selection=json.loads((ROOT/'reports/end-to-end10-preflight-20261024/selection-manifest.json').read_text())
for r in selection['selected']:protected[r['source_path']]=sha(Path(r['source_path']))
(OUT/'protected-before.json').write_text(json.dumps(protected,indent=2)+'\n')
code={str(p.relative_to(ROOT)):sha(p) for name in ['local_api','scripts','tests'] for p in (ROOT/name).rglob('*.py')}
(OUT/'code-before.json').write_text(json.dumps(code,indent=2)+'\n')
print(len(protected))
