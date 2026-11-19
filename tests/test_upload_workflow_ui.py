"""Exercise the upload workflow using an actual backend extraction response."""
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from local_api.app import app


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js runtime unavailable')
def test_upload_workflow_uses_backend_payload_and_clears_loading_on_errors():
    document = Path(__file__).parent / 'fixtures' / 'digital-multipage.pdf'
    with TestClient(app) as client, document.open('rb') as file:
        response = client.post(
            '/api/v1/extract/text',
            data={'strategy': 'fast'},
            files={'file': (document.name, file, 'application/pdf')},
        )
    assert response.status_code == 200
    subprocess.run(
        ['node', 'tests/upload_workflow_ui.cjs'],
        input=response.text,
        text=True,
        timeout=15,
        check=True,
    )
