#!/usr/bin/env bash
# Run direct local models in an isolated container; no .env/provider key is loaded.
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/resumes [batch_check_resumes.py options]" >&2
  exit 2
fi
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
resume_dir="$(realpath "$1")"
shift
if [[ ! -d "$resume_dir" ]]; then echo 'Resume folder is unavailable.' >&2; exit 2; fi
audit_dir="${RESUME_AUDIT_OUTPUT_DIR:-$project_dir/.upstream/batch-validation}"
mkdir -p "$audit_dir"
docker run --rm --name resume-offline-audit --network none --cpus 4 --memory 5g \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,source=$project_dir/local_api,target=/app/local_api,readonly" \
  --mount "type=bind,source=$project_dir/scripts,target=/app/scripts,readonly" \
  --mount "type=bind,source=$audit_dir,target=/audit" \
  --mount "type=bind,source=$resume_dir,target=/resumes,readonly" \
  -e HF_HUB_DISABLE_TELEMETRY=1 -e XDG_CACHE_HOME=/tmp/resume-audit-cache \
  unstructured-text-api:local \
  python scripts/batch_check_resumes.py /resumes --output /audit --workers 3 "$@"
