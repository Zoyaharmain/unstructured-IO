"""Run the local frontend/API with private DeepSeek settings loaded from .env."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8012)
    parser.add_argument('--development', action='store_true', help='Expose sanitized mapping diagnostics in API responses')
    args = parser.parse_args()
    if args.development:
        os.environ['RESUME_APP_ENV'] = 'development'
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    from local_api.core.provider_env import load_provider_env
    load_provider_env(ROOT / '.env')
    for key, value in {
        'HF_HOME': str(ROOT / '.venv/model-cache'), 'HF_HUB_OFFLINE': '1',
        'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'DO_NOT_TRACK': 'true',
        'NUMBA_CACHE_DIR': '/tmp/resume-inspector-numba', 'MPLCONFIGDIR': '/tmp/resume-inspector-mpl',
    }.items():
        os.environ.setdefault(key, value)
    from local_api.services.llm_section_review import review_status
    status = review_status()
    print(f"Resume Inspector: http://localhost:{args.port}", flush=True)
    print(f"DeepSeek enabled: {status['enabled']}; configured: {status['configured']}", flush=True)
    import uvicorn
    run_options = {'host': '127.0.0.1', 'port': args.port}
    if args.development:
        # Schema/mapper edits must invalidate the running development process.
        # Watch application code only, excluding reports and model caches.
        run_options.update(reload=True, reload_dirs=[str(ROOT / 'local_api')])
    uvicorn.run('local_api.app:app', **run_options)


if __name__ == '__main__':
    main()
