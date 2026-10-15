"""Run Uvicorn and verify real HTTP health and partition requests, then stop it."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
env = dict(os.environ, DO_NOT_TRACK='true', HF_HUB_OFFLINE='1')
with (root / 'reports/http-smoke-server.log').open('w') as log:
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'local_api.app:app', '--host', '127.0.0.1', '--port', str(port)], cwd=root, env=env, stdout=log, stderr=log)
    try:
        url = f'http://127.0.0.1:{port}'
        deadline = time.monotonic() + 20
        while True:
            try:
                with urlopen(url + '/health', timeout=1) as response:
                    health = json.load(response)
                break
            except URLError:
                if time.monotonic() >= deadline: raise
                time.sleep(0.1)
        boundary = 'unstructured-api-smoke-boundary'
        payload = (root/'tests/fixtures/digital-multipage.pdf').read_bytes()
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="strategy"\r\n\r\nfast\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="digital-multipage.pdf"\r\nContent-Type: application/pdf\r\n\r\n').encode()+payload+f'\r\n--{boundary}--\r\n'.encode()
        with urlopen(Request(url+'/v1/partition', data=body, headers={'Content-Type':f'multipart/form-data; boundary={boundary}'}), timeout=60) as response:
            result = json.load(response)
            assert response.status == 200
        assert health == {'status':'ok'}
        assert result['element_count'] > 0
        assert result['requested_strategy'] == 'fast'
        assert set(result) == {'filename','requested_strategy','element_count','page_numbers','text','elements'}
        (root/'reports/http-smoke.json').write_text(json.dumps({'health':health,'response':result},indent=2)+'\n')
        print('HTTP health and multipart partition: PASS; elements:',result['element_count'])
    finally:
        process.terminate()
        process.wait(timeout=10)
