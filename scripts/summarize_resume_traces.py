"""Summarize completed private trace runs without reading résumé text."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace-dir', type=Path,
                        default=Path(os.getenv('RESUME_TRACE_DIR', '/tmp/resume-pipeline-traces')))
    args = parser.parse_args()
    counts = Counter()
    runs = 0
    cost = 0.0
    for path in args.trace_dir.glob('*/state.json'):
        try:
            totals = json.loads(path.read_text()).get('totals', {})
        except (OSError, ValueError):
            continue
        if '7' not in totals.get('stages', {}):
            continue
        runs += 1
        for key in ('elements', 'completion_calls', 'verification_calls', 'judge_calls',
                    'field_review_calls', 'structural_review_calls',
                    'errors', 'retries', 'escalations', 'human_review_blocks',
                    'input_tokens_reported', 'output_tokens_reported', 'processing_ms', 'priced_calls'):
            counts[key] += totals.get(key, 0)
        cost += totals.get('estimated_cost', 0)
    print(json.dumps({'completed_runs': runs, **counts,
                      'estimated_cost_usd_for_priced_calls': round(cost, 8) if counts['priced_calls'] else None}, indent=2))


if __name__ == '__main__':
    main()
