"""Start the local API with private DeepSeek settings loaded without dotenv."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--llm-review', action='store_true')
    mode.add_argument('--local-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    from scripts.check_pilot_fallback import load_provider_env
    load_provider_env(ROOT / '.env')
    if args.llm_review:
        os.environ['DEEPSEEK_REVIEW_ENABLED'] = 'true'
        if not os.getenv('DEEPSEEK_API_KEY', '').strip():
            parser.error('DEEPSEEK_API_KEY must be configured for --llm-review')
    elif args.local_only:
        os.environ['DEEPSEEK_REVIEW_ENABLED'] = 'false'
    os.environ.setdefault('HF_HOME', str(ROOT / '.venv/model-cache'))
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    import uvicorn
    uvicorn.run('local_api.app:app', host=args.host, port=args.port)


if __name__ == '__main__':
    main()
