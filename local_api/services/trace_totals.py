"""Aggregate safe trace metrics across HTTP stages of a résumé run."""
from collections import Counter
import json
import os


def populated_values(value):
    if isinstance(value, dict):
        return sum(populated_values(item) for item in value.values())
    if isinstance(value, list):
        return sum(populated_values(item) for item in value)
    return int(value is not None and value != '')


def update_totals(state, row):
    totals = state.setdefault('totals', {})
    kind = row['event']

    def add(key, amount=1):
        totals[key] = totals.get(key, 0) + amount

    if kind == 'stage_summary':
        number = str(row['number'])
        totals.setdefault('stages', {})[number] = True
    elif kind == 'extraction_result':
        totals['elements'] = row['element_count']
    elif kind == 'decision' and row.get('decision_type') == 'section_assignment' and row.get('meaningful'):
        for span in row['source_ids']:
            totals.setdefault('placements', {})[span] = row['section']
        probability = row.get('confidence', {}).get('probability')
        if probability is not None and row.get('rule') in {'semantic', 'section_heading', 'needs_review'}:
            totals.setdefault('candidate_probabilities', {})[row['source_ids'][0]] = probability
    elif kind == 'llm_call_start':
        if row.get('request_kind') == 'completion':
            add('completion_calls')
            stage = row['stage']
            if 'judge' in stage:
                add('judge_calls')
            elif 'audit' in stage:
                add('schema_audit_calls')
            elif stage == 'field_review':
                add('field_review_calls')
            elif stage == 'structural_review':
                add('structural_review_calls')
            else:
                add('verification_calls')
    elif kind == 'verification_plan' or kind == 'section_judge_plan':
        add('escalations')
    elif kind == 'section_judge_decision' and row['final'] == 'needs_review':
        add('judge_human_review')
    elif kind in {'llm_call_error', 'request_failure', 'stage_failure'}:
        add('errors')
    elif kind == 'provider_retry':
        add('retries')
    elif kind == 'llm_call_end':
        usage = row.get('token_usage') or {}
        for token, counter in (('prompt_tokens', 'input_tokens_reported'),
                               ('completion_tokens', 'output_tokens_reported')):
            if token in usage:
                add(counter, usage[token])
        if row.get('estimated_cost') is not None:
            add('estimated_cost', row['estimated_cost'])
            add('priced_calls')
    elif kind == 'request_end':
        add('processing_ms', row['duration_ms'])
    elif kind == 'stage_summary_result':
        totals['human_review_blocks'] = row['unresolved']
    elif kind == 'audit_outcome':
        totals['audit_findings'] = row['findings']
    elif kind == 'export_result':
        totals['export_requires_human_review'] = row['requires_human_review']
        totals['validation_notices'] = row['validation_notices']


def summarize(totals):
    low = float(os.getenv('DEEPSEEK_LOW_CONFIDENCE', '.50'))
    high = float(os.getenv('DEEPSEEK_HIGH_CONFIDENCE', '.80'))
    distribution = Counter('high' if value >= high else 'medium' if value >= low else 'low'
                           for value in totals.get('candidate_probabilities', {}).values())
    excluded = {'stages', 'placements', 'candidate_probabilities', 'estimated_cost'}
    counters = ('elements', 'completion_calls', 'verification_calls', 'judge_calls', 'schema_audit_calls',
                'field_review_calls', 'structural_review_calls', 'escalations', 'retries',
                'errors', 'human_review_blocks', 'judge_human_review')
    return {**{key: totals.get(key, 0) for key in counters},
            **{k: v for k, v in totals.items() if k not in excluded},
            'stages_completed': len(totals.get('stages', {})),
            'initial_classification': dict(Counter(totals.get('placements', {}).values())),
            'calibrated_candidate_confidence': dict(distribution),
            'estimated_cost_usd_for_priced_calls': totals.get('estimated_cost')}


def estimated_cost(model, usage):
    """Rates are supplied by the user in USD per million tokens."""
    try:
        prices = json.loads(os.getenv('DEEPSEEK_MODEL_PRICES_JSON', '{}'))[model]
        rates = [float(prices[key]) for key in ('input', 'output')]
        import math
        if not all(math.isfinite(rate) and rate >= 0 for rate in rates):
            return None
        return round(sum(usage[token] * rate for token, rate in zip(('prompt_tokens', 'completion_tokens'), rates)) / 1_000_000, 8)
    except (KeyError, ValueError, TypeError):
        return None
