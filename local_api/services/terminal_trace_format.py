"""Readable console view of the existing privacy-safe trace records."""
import json
import logging


COLORS = {
    logging.DEBUG: '36', logging.INFO: '32', logging.WARNING: '33',
    logging.ERROR: '31', logging.CRITICAL: '1;31',
}
STAGES = (
    'Document extraction', 'Section detection and classification', 'Record grouping',
    'Recovery and source ownership', 'Schema mapping and field extraction',
    'Evidence validation and review', 'Standardization and JSON export',
)


def pick(row, *keys):
    return {key: row[key] for key in keys if key in row}


def console_confidence(value):
    value = value or {}
    probability = value.get('probability')
    return {
        'state': value.get('state', 'not_calibrated'),
        'candidate_correctness_estimate': f'{probability:.1%}' if probability is not None else None,
    }


def format_event(row):
    kind = row['event']
    stage = row.get('stage', '')
    review = ('Read-only schema audit' if stage.startswith('schema_audit')
              else 'LLM-as-judge' if stage == 'section_judge' else 'LLM call')
    if kind == 'llm_call_start':
        return (f'{review} · DeepSeek request',
                {**pick(row, 'call_id', 'provider', 'trigger', 'attempt', 'source_span_count', 'input_bytes', 'timeout_seconds'),
                 'source_ids_preview': row.get('source_ids', [])[:8]},
                {'model': row['model'],
                 'routing': 'conflict adjudication' if row.get('model_tier') == 'judge' else (
                     'confidence-based' if row.get('confidence_based_routing') else 'configured model'),
                 'tier': row.get('model_tier') or 'configured',
                 'routing_probability': row.get('routing_probability'),
                 'requirement': row.get('requirement')})
    if kind == 'section_model_routing':
        probability = row.get('probability')
        return ('Section review · model selection',
                {'lowest_calibrated_candidate_confidence': f'{probability:.1%}' if probability is not None else None},
                pick(row, 'tier', 'model', 'reason'))
    if kind in {'llm_call_end', 'llm_call_error'}:
        return (f'{review} · DeepSeek response', pick(row, 'call_id'),
                pick(row, 'model', 'status', 'latency_ms', 'token_usage', 'estimated_cost', 'error_code', 'error_type'))
    if kind == 'section_judge_decision':
        return ('LLM-as-judge · section verdict',
                pick(row, 'target', 'original', 'initial', 'independent'),
                pick(row, 'final', 'evidence'))
    if kind == 'section_judge_plan':
        return ('LLM-as-judge · planned adjudication', pick(row, 'disputed_targets'), pick(row, 'model'))
    if kind == 'verification_plan':
        return ('Section verification · planned request', pick(row, 'targets'),
                pick(row, 'model', 'status', 'reason'))
    if kind == 'verification_outcome':
        result = (pick(row, 'checked', 'agreed', 'conflicting') if row.get('independent_response')
                  else {'status': 'No accepted independent response', 'agreement': 'Not available'})
        return ('Section verification · result', {'targets': row.get('checked')}, result)
    if kind == 'provider_retry':
        return ('DeepSeek retry', pick(row, 'call_id'), pick(row, 'attempt', 'reason'))
    if kind == 'run_summary':
        return ('Résumé processing summary', {}, row.get('totals', {}))
    if kind == 'request_start' and row.get('endpoint') == '/api/v1/extract/text':
        return ('Résumé processing started', {'document': 'upload received'}, {})
    if kind == 'audit_outcome':
        return ('Read-only schema audit',
                pick(row, 'expected_units', 'checked_units'),
                pick(row, 'status', 'outcome', 'findings', 'partial_findings', 'provider_calls',
                     'semantic_correctness'))
    if kind == 'review_outcome':
        return ('Review result', pick(row, 'review_stage', 'provider_calls'),
                pick(row, 'status', 'accepted', 'rejected', 'semantic_correctness'))
    if kind == 'extraction_result':
        return ('Stage 1 · extraction', pick(row, 'requested_strategy'),
                pick(row, 'element_count', 'source_accuracy'))
    if kind == 'extracted_element':
        return ('Stage 1 · extracted element', pick(row, 'source_id', 'page'),
                pick(row, 'element_type', 'characters'))
    if kind == 'decision':
        decision = row.get('decision_type')
        if decision == 'ml_section_prediction':
            return ('Stage 2 · local model suggestion', pick(row, 'source_ids', 'model'),
                    {'heading': {**pick(row, 'heading_candidate', 'heading_similarity', 'heading_margin'),
                                 'confidence': console_confidence(row.get('heading_confidence'))},
                     'content': {**pick(row, 'content_candidate', 'content_similarity', 'content_margin'),
                                 'confidence': console_confidence(row.get('confidence'))}})
        if decision == 'section_rule_evidence':
            return ('Stage 2 · rules considered', pick(row, 'source_ids', 'active_section', 'explicit_context'),
                    pick(row, 'structural_label', 'is_heading', 'record_field', 'employer_boundary', 'compound'))
        if decision == 'ownership':
            return ('Source placement', {**pick(row, 'source_ids'), 'previous': row.get('before')},
                    row.get('after') or {})
        if decision == 'record_group':
            return ('Stage 3 · record grouping', pick(row, 'source_ids'),
                    pick(row, 'section', 'record_ids', 'rule'))
        if decision == 'field_mapping':
            return ('Stage 5 · mapped field', pick(row, 'section', 'record_ids', 'field', 'source_ids'),
                    pick(row, 'evidence_state', 'item_count', 'value_ref', 'confidence'))
        if decision == 'standardization':
            return ('Stage 7 · standardization', pick(row, 'field'),
                    pick(row, 'rule', 'evidence_state', 'applied'))
    if kind == 'stage_start':
        return ('Start', pick(row, 'function', 'trigger', 'input_structure'), {})
    if kind in {'stage_end', 'stage_failure'}:
        return ('Finish', {}, pick(row, 'status', 'duration_ms', 'error_type', 'output_structure'))
    metadata = {'event', 'event_id', 'run_id', 'stage', 'sequence', 'timestamp_ns', 'parent_decision_id'}
    return (kind.replace('_', ' ').capitalize(), {}, {k: v for k, v in row.items() if k not in metadata})


class TerminalTraceFormatter(logging.Formatter):
    def __init__(self, *, use_color=False):
        super().__init__('%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
        self.use_color = use_color

    def accent(self, text, color):
        return f'\x1b[{color}m{text}\x1b[0m' if self.use_color else text

    def format(self, record):
        row = getattr(record, 'trace_row', None)
        if row is None:
            return super().format(record)
        if row['event'] == 'stage_summary':
            number = row['number']
            level = self.accent(record.levelname, COLORS.get(record.levelno, '37'))
            return '\n'.join([
                f"{self.formatTime(record, self.datefmt)} {level}: [{row['run_id'][:8]}] "
                + self.accent(f'Stage {number} · {STAGES[number - 1]}', '36'),
                f"    {self.accent('Input', '36')}: {row['inputs']}",
                f"    {self.accent('Output', '32')}: {row['outputs']}",
                f"    {self.accent('Method', '33')}: {row['method']}",
            ])
        if row.get('decision_type') == 'section_assignment':
            confidence = console_confidence(row.get('confidence'))
            estimate = confidence['candidate_correctness_estimate']
            rule = row.get('rule')
            if rule and rule not in {'semantic', 'section_heading', 'needs_review'}:
                detail = 'Rule-based placement; no model probability used.'
            else:
                detail = f'{estimate} for local candidate {row.get("candidate")}' if estimate else (
                    f'not calibrated for local candidate {row.get("candidate")}')
            level = self.accent(record.levelname, COLORS.get(record.levelno, '37'))
            span = ', '.join(row['source_ids'])
            preview = getattr(record, 'trace_preview', '[text hidden; source ID shown above]')
            return '\n'.join([
                f"{self.formatTime(record, self.datefmt)} {level}: Stage 2 · {span} [{row['run_id'][:8]}]",
                f"    {self.accent('Input', '36')}: {preview}",
                f"    {self.accent('Assigned to', '32')}: {row['section'].replace('_', ' ').capitalize()}",
                f"    {self.accent('Why', '33')}: {row['reason']}",
                f"    {self.accent('Confidence', '35')}: {detail}",
            ])
        title, inputs, outputs = format_event(row)
        color = COLORS.get(record.levelno, '37')
        if record.levelno < logging.WARNING:
            if 'judge' in title.lower():
                color = '35'
            elif title.startswith('LLM call'):
                color = '34'
        level = self.accent(record.levelname, color)
        run = row['run_id'][:8]
        header = f"{self.formatTime(record, self.datefmt)} {level} [{run} #{row.get('sequence', '?')}] {row['stage']} / {title}"
        lines = [header]
        for label, payload, color in [('Input', inputs, '36'), ('Output', outputs, '32')]:
            if payload:
                details = json.dumps(payload, ensure_ascii=True, default=str)
                lines.append(f"    {self.accent(label, color)}  {details}")
        if row['event'] in {'section_judge_decision', 'extracted_element'} and hasattr(record, 'trace_preview'):
            label = 'Source evidence' if row['event'] == 'section_judge_decision' else 'Text preview'
            lines.append(f"    {self.accent(label, '35')}  {record.trace_preview}")
        return '\n'.join(lines)


class ConsolidatedSectionFilter(logging.Filter):
    def __init__(self, *, summary=False, quiet=False):
        super().__init__()
        self.summary = summary
        self.quiet = quiet

    def filter(self, record):
        row = getattr(record, 'trace_row', {})
        if self.quiet and record.levelno < logging.WARNING:
            return row.get('event') in {'stage_summary', 'run_summary'}
        if self.summary and record.levelno < logging.WARNING:
            return row.get('event') in {
                'stage_summary', 'llm_call_start', 'llm_call_end', 'section_model_routing',
                'audit_outcome', 'run_summary', 'section_judge_decision', 'section_judge_plan',
                'verification_plan', 'verification_outcome',
            }
        if row.get('decision_type') == 'section_assignment' and row.get('meaningful') is False:
            return False
        return row.get('decision_type') not in {'ml_section_prediction', 'section_rule_evidence'}
