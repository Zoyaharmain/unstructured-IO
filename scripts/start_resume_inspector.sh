#!/usr/bin/env bash
# Build the current app and load the private API key from .env without displaying it.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
api_port="${RESUME_API_PORT:-8011}"
if ! [[ "$api_port" =~ ^[0-9]+$ ]] || ((api_port < 1 || api_port > 65535)); then
  echo 'RESUME_API_PORT must be between 1 and 65535.' >&2
  exit 1
fi
docker build -t unstructured-text-api:local .
if docker container inspect resume-inspector >/dev/null 2>&1; then
  existing_image="$(docker inspect -f '{{.Config.Image}}' resume-inspector)"
  if [[ "$existing_image" != 'unstructured-text-api:local' ]]; then
    echo 'The name resume-inspector belongs to another image; it was left untouched.' >&2
    exit 1
  fi
  docker rm -f resume-inspector
fi
env_args=()
if [[ -f .env ]]; then env_args=(--env-file .env); fi
docker run -d --name resume-inspector --label app=unstructured-resume-inspector \
  -p "127.0.0.1:${api_port}:8000" --restart unless-stopped \
  -e HF_HUB_OFFLINE=1 "${env_args[@]}" unstructured-text-api:local
printf 'Resume Inspector: http://localhost:%s\n' "$api_port"
# Check credentials without sending resume text. Keep the app running for local
# grouping even when the key is rejected or the provider is unavailable.
docker exec -i resume-inspector python - <<'PY'
import json,time
from urllib.request import urlopen,Request
base='http://127.0.0.1:8000'
for attempt in range(30):
    try:
        with urlopen(base+'/health',timeout=2) as response:
            if response.status==200:break
    except Exception:
        time.sleep(.5)
try:
    with urlopen(Request(base+'/api/v1/resume/review-connection',method='POST'),timeout=20) as response:
        result=json.load(response)
    print('DeepSeek check '+result['status'].upper()+': '+result['message'])
except Exception:
    print('DeepSeek check unavailable. Use Check DeepSeek connection in the UI.')
PY
