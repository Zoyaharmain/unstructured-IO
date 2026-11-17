"""Validate saved corrected sections through the real API and JS renderers."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts', type=Path)
    args = parser.parse_args()
    from fastapi.testclient import TestClient
    from local_api.app import app
    elements = json.loads((args.artifacts/'elements.json').read_text())
    sections = json.loads((args.artifacts/'after.sections.json').read_text())
    # No field review; this endpoint must consume the accepted source structure.
    response = TestClient(app).post('/api/v1/resume/schema', json={
        'elements':elements, 'sections':sections, 'review_fields':False})
    response.raise_for_status()
    payload = response.json()
    (args.artifacts/'api.schema.json').write_text(json.dumps(payload, indent=2))
    expected = json.loads((args.artifacts/'after.schema.json').read_text())
    assert payload['section_schemas'] == expected['section_schemas']
    actual_owners = payload['meta']['source_ownership']
    expected_owners = expected['meta']['source_ownership']
    assert {r['source_id']:r['owner'] for r in actual_owners['spans']} == {r['source_id']:r['owner'] for r in expected_owners['spans']}
    for key in ('source_digest', 'record_parents', 'group_records', 'employer_parents'):
        assert actual_owners.get(key) == expected_owners.get(key)
    process = subprocess.run(['node', 'tests/semantic_ownership_ui.cjs', str(args.artifacts/'after.sections.json'),
                              str(args.artifacts/'api.schema.json')], check=True, capture_output=True, text=True, cwd=ROOT)
    summary = {'http_status':response.status_code, 'schema_ownership_preserved':True,
               'ui_dom_validation':json.loads(process.stdout), 'real_browser_validation':'not_performed'}
    (args.artifacts/'api-ui-validation.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
