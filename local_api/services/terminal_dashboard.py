"""Terminal projection of pipeline events. No processing decisions originate here."""
from collections import OrderedDict, defaultdict
from datetime import datetime
import logging
import time

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from local_api.services.terminal_trace_format import STAGES

STARTS = {
    'extraction': 1, 'section_classification': 2, 'record_grouping': 3,
    'section_recovery': 4, 'schema_mapping': 5, 'schema_audit_adapter': 6,
    'standardization': 7,
}
STATUSES = {'waiting': 'dim', 'running': 'cyan', 'completed': 'green', 'failed': 'red'}
MISSING = {'not_stated': 'Not present in source', 'unmapped': 'Field not mapped',
           'ambiguous': 'Conflicting evidence', 'unresolved': 'Human review required'}


def cell(value, style=None):
    return Text(str(value if value is not None else 'Not available'), style=style)


class DashboardRun:
    def __init__(self, identifier):
        self.identifier = identifier
        self.started = time.monotonic()
        self.clock = datetime.now().strftime('%H:%M:%S')
        self.document = {}
        self.stages = {}
        self.operation_seconds = defaultdict(float)
        self.blocks = {}
        self.groups = {}
        self.fields = {}
        self.export_fields = {}
        self.ownership = {}
        self.routing_reasons = set()
        self.judge_skip_reasons = set()
        self.current = None
        self.status = 'Waiting'
        self.totals = {}

    def start_stage(self, number):
        self.current = number
        self.stages[number] = ('running', time.monotonic())
        self.status = 'Running'

    def finish_stage(self, number, status='completed'):
        previous = self.stages.get(number)
        now = time.monotonic()
        elapsed = self.operation_seconds.get(number)
        if elapsed is None and previous and previous[0] == 'running':
            elapsed = now - previous[1]
        self.stages[number] = (status, elapsed)
        if self.current == number:
            self.current = None
        if self.current is None:
            self.status = 'Exported' if number == 7 else 'Waiting for next stage'

    def tracker(self):
        table = Table.grid(padding=(0, 2))
        table.add_column(style='cyan')
        table.add_column()
        table.add_column(style='dim', justify='right')
        for number, title in enumerate(STAGES, 1):
            status, duration = self.stages.get(number, ('waiting', None))
            if status == 'running':
                duration = time.monotonic() - duration
            table.add_row(f'{number}. {title}', cell(status.upper(), STATUSES[status]),
                          f'{duration:.2f}s' if duration is not None else '—')
        header = Table.grid(padding=(0, 1))
        header.add_row(cell('Execution', 'dim'), cell(self.identifier[:8]))
        header.add_row(cell('Resume', 'dim'), cell(self.document.get('filename', 'Hidden or unavailable')))
        header.add_row(cell('File', 'dim'), cell(
            f"{self.document.get('file_type', 'unknown')} · {self.document.get('size', 'unknown')} bytes"))
        header.add_row(cell('Started', 'dim'), cell(self.clock))
        header.add_row(cell('Elapsed', 'dim'), cell(f'{time.monotonic() - self.started:.2f}s'))
        header.add_row(cell('Status', 'dim'), cell(self.status))
        header.add_row(cell('Current stage', 'dim'), cell(STAGES[self.current - 1] if self.current else '—'))
        from rich.console import Group
        return Panel(Group(header, Text(''), table), title='RESUME INTELLIGENCE ENGINE', border_style='cyan')


class DashboardHandler(logging.Handler):
    """Buffer repeated events and print tables only at relevant checkpoints."""
    def __init__(self, *, mode='normal', console=None, live=True):
        super().__init__()
        self.mode = mode
        self.console = console or Console(stderr=True)
        self.use_live = live and self.console.is_terminal
        self.runs = OrderedDict()
        self.live = None
        self.active = None
        self.last_refresh = 0.0

    def emit(self, record):
        try:
            self.handle_event(record)
        except Exception:
            # The renderer is optional. Its output must never affect processing.
            pass

    def refresh(self, run, *, force=False):
        if not self.use_live:
            return
        now = time.monotonic()
        if self.active == run.identifier and not force and now - self.last_refresh < .25:
            return
        self.active = run.identifier
        self.last_refresh = now
        if self.live is None:
            self.live = Live(run.tracker(), console=self.console, refresh_per_second=2,
                             get_renderable=lambda: self.runs.get(self.active, run).tracker(),
                             transient=True, redirect_stdout=True, redirect_stderr=True)
            self.live.start(refresh=True)
        else:
            self.live.update(run.tracker(), refresh=True)

    def close(self):
        if self.live:
            self.live.stop()
            self.live = None
        super().close()

    def panel(self, title, rows, *, style='cyan'):
        grid = Table.grid(padding=(0, 1))
        grid.add_column(style='dim')
        grid.add_column()
        for name, value in rows:
            grid.add_row(name, cell(value))
        self.console.print(Panel(grid, title=title, border_style=style))

    def handle_event(self, record):
        row = getattr(record, 'trace_row', None)
        if row is None:
            if record.levelno >= logging.WARNING:
                self.console.print(cell(record.getMessage(), 'yellow'))
            return
        identifier = row['run_id']
        run = self.runs.get(identifier)
        if run is None:
            if len(self.runs) >= 32:
                self.runs.popitem(last=False)
            run = self.runs[identifier] = DashboardRun(identifier)
        self.runs.move_to_end(identifier)

        event = row['event']
        preview = getattr(record, 'trace_preview', None)
        if event == 'document_received':
            run.document.update(size=row.get('input_bytes'), filename=preview or 'Hidden',
                                file_type=row.get('declared_file_type') or 'Not available')
            run.start_stage(1)
            if not self.use_live:
                self.console.print(run.tracker())
            self.refresh(run, force=True)
        elif event == 'extraction_result':
            pages = row.get('pages')
            run.document.update(file_type=row.get('file_type'), pages=pages if pages is not None else 'Not measured',
                                elements=row['element_count'], extraction_status='Completed')
            if self.mode != 'quiet':
                self.panel('INGESTION', [(key.replace('_', ' ').capitalize(), value)
                                         for key, value in run.document.items()])
        elif event == 'stage_start' and row['stage'] in STARTS:
            if row['stage'] == 'section_classification':
                run.blocks.clear()
                run.groups.clear()
                run.ownership.clear()
            run.start_stage(STARTS[row['stage']])
            self.refresh(run)
        elif event == 'stage_failure':
            number = STARTS.get(row['stage'], run.current)
            if number:
                run.finish_stage(number, 'failed')
            run.status = 'Failed'
            rows = [('Operation', row['stage']), ('Error', row.get('error_type'))]
            if self.mode == 'debug' and row.get('frames'):
                rows.append(('Traceback frames', '\n'.join(row['frames'])))
            self.panel('PROCESSING ERROR', rows, style='red')
            self.refresh(run, force=True)
        elif event == 'stage_end' and row['stage'] in STARTS:
            number = STARTS[row['stage']]
            if row.get('duration_ms') is not None:
                run.operation_seconds[number] += row['duration_ms'] / 1000
        elif event == 'decision':
            self.record_decision(run, row, preview)
        elif event == 'stage_summary':
            number = row['number']
            run.finish_stage(number)
            self.panel(f'STAGE {number} · {STAGES[number - 1]}', [
                ('Input', row['inputs']), ('Output', row['outputs']), ('Method', row['method']),
                ('Duration', f'{run.stages[number][1]:.2f}s' if run.stages[number][1] is not None else 'Not measured'),
            ])
            if self.mode != 'quiet':
                if number == 2:
                    self.confidence_summary(run)
                    self.classification(run)
                elif number == 3:
                    self.records(run)
                elif number == 5:
                    self.field_table(run)
                elif number == 4:
                    self.recovery_table(run)
            self.refresh(run, force=True)
        elif event in {'llm_call_start', 'llm_call_end', 'llm_call_error', 'provider_retry',
                       'audit_outcome', 'section_judge_plan', 'section_judge_decision',
                       'verification_plan', 'verification_outcome', 'section_model_routing'}:
            if event == 'section_model_routing' and row.get('reason'):
                run.routing_reasons.add(row['reason'])
            if event == 'llm_call_start':
                run.status = f"Waiting for {row.get('model', 'provider')}"
                self.refresh(run, force=True)
            elif event in {'llm_call_end', 'llm_call_error'}:
                run.status = 'Running' if run.current else 'Waiting for next stage'
                self.refresh(run, force=True)
            if self.mode != 'quiet' or record.levelno >= logging.WARNING:
                self.activity(row, record)
        elif event == 'section_judge_skipped':
            run.judge_skip_reasons.add(row['reason'])
        elif event == 'final_export':
            if self.mode != 'quiet':
                self.panel('FINAL JSON', [('Status', 'Exported'), ('Schema', row.get('schema_version')),
                                         ('Populated scalar values', row.get('populated_values')),
                                         ('Review required', row.get('requires_human_review'))], style='green')
                if preview:
                    self.console.print(Panel(Syntax(preview, 'json', word_wrap=True), title='Export preview'))
                self.export_table(run)
        elif event == 'export_field':
            run.export_fields[row['path']] = (row, preview)
        elif event == 'run_summary':
            totals = dict(row.get('totals', {}))
            usage_status = 'Not available' if totals.get('completion_calls') else 'Not applicable'
            totals.setdefault('input_tokens_reported', usage_status)
            totals.setdefault('output_tokens_reported', usage_status)
            judge_calls = totals.get('judge_calls', 0)
            audit_calls = totals.get('schema_audit_calls', 0)
            judge_rows = [('Section judge calls', judge_calls), ('Read-only schema audit calls', audit_calls)]
            if not judge_calls:
                reasons = sorted(run.judge_skip_reasons | run.routing_reasons)
                judge_rows.append(('Why the section judge did not run',
                                   '\n'.join(reasons) or 'No section judge call was recorded for this run'))
            self.panel('LLM-AS-A-JUDGE · SECTION REVIEW', judge_rows, style='magenta')
            self.panel('RÉSUMÉ PROCESSING SUMMARY', [(k.replace('_', ' ').capitalize(), v)
                       for k, v in totals.items()], style='green')
            if self.live and self.active == identifier:
                self.live.stop()
                self.live = None
        elif event == 'request_end' and row.get('http_status', 200) >= 400:
            if run.current:
                run.finish_stage(run.current, 'failed')
            run.status = 'Failed'
            self.panel('REQUEST FAILED', [('HTTP status', row['http_status'])], style='red')
            self.refresh(run, force=True)
        elif event == 'validation_failure':
            self.panel('EVIDENCE OR SCHEMA VALIDATION REJECTED', [
                ('Path', row.get('path')), ('Reason', row.get('reason')), ('Attempt', row.get('attempt')),
            ], style='red')
        elif record.levelno >= logging.WARNING:
            self.panel(event.replace('_', ' ').upper(), [('Stage', row['stage']),
                       ('Reason', row.get('reason') or row.get('error_type') or row.get('status'))],
                       style='red' if record.levelno >= logging.ERROR else 'yellow')

    def record_decision(self, run, row, preview):
        kind = row.get('decision_type')
        if kind == 'section_assignment':
            for source in row['source_ids']:
                run.blocks[source] = (row, preview)
        elif kind == 'record_group':
            run.groups[(row['section'], tuple(row['record_ids']))] = row
        elif kind == 'field_mapping':
            run.fields[row['value_ref']] = (row, preview)
        elif kind == 'ownership' and run.stages.get(4, (None,))[0] == 'running':
            for source in row['source_ids']:
                run.ownership[source] = row

    def recovery_table(self, run):
        if not run.ownership:
            return
        table = Table(title='RECOVERY AND SOURCE OWNERSHIP', expand=True)
        for label in ('Source', 'Before', 'After', 'Rule'):
            table.add_column(label, overflow='fold')
        for source, row in run.ownership.items():
            before = row.get('before') or {}
            after = row.get('after') or {}
            table.add_row(cell(source, 'dim'), cell(before.get('section') or 'Unresolved'),
                          cell(after.get('section') or 'Unresolved'),
                          cell(after.get('rule') or after.get('evidence_state')))
        self.console.print(table)

    def confidence_summary(self, run):
        candidates = [row for row, _ in run.blocks.values()
                      if row.get('rule') in {'semantic', 'section_heading', 'needs_review'}]
        probabilities = [row['confidence']['probability'] for row in candidates
                         if row.get('confidence', {}).get('probability') is not None]
        margins = [row['margin'] for row, _ in run.blocks.values() if row.get('margin') is not None]
        self.panel('STAGE 2 · CONFIDENCE SCORES', [
            ('Calibrated predictions', len(probabilities)),
            ('Calibrated probability range', f'{min(probabilities):.1%} to {max(probabilities):.1%}'
             if probabilities else 'Requires matching human-verified calibration'),
            ('Raw model margin range', f'{min(margins):.3f} to {max(margins):.3f}' if margins else 'Not measured'),
            ('Model-based assignments without a probability', len(candidates) - len(probabilities)),
            ('Other assignments without a probability', len(run.blocks) - len(candidates)),
            ('Score guide', 'Similarity measures closeness. Margin measures the gap between candidates.'),
        ])

    def classification(self, run):
        sections = defaultdict(list)
        for index, (source, (row, preview)) in enumerate(run.blocks.items(), 1):
            sections[row['section']].append((index, source, row, preview))
        for name, blocks in sections.items():
            table = Table(title=f'BLOCK CLASSIFICATION · {name.replace("_", " ").upper()}', expand=True)
            compact = self.mode != 'debug'
            table.add_column('# / source', style='dim', no_wrap=True)
            table.add_column('Source text', style='blue', no_wrap=compact, overflow='ellipsis', ratio=4)
            table.add_column('Method / why', no_wrap=compact, overflow='ellipsis', ratio=4)
            table.add_column('Model confidence signal', overflow='fold', ratio=3)
            table.add_column('Review', no_wrap=True)
            for index, source, row, preview in blocks:
                rule = row.get('rule', '')
                probability = row.get('confidence', {}).get('probability')
                model_used = rule in {'semantic', 'section_heading', 'needs_review'}
                margin = row.get('margin')
                similarity = row.get('similarity')
                if model_used and probability is not None:
                    score = f'{probability:.1%} calibrated candidate probability'
                elif margin is not None:
                    score = f'{margin:.3f} raw model margin'
                elif similarity is not None:
                    score = f'{similarity:.3f} raw model similarity'
                else:
                    score = 'Model signal unavailable' if model_used else 'Rule-based — no probability'
                candidate = row.get('candidate') or 'None'
                if row.get('alternatives'):
                    candidate += '; alternatives: ' + ', '.join(row['alternatives'])
                if margin is not None and model_used and probability is not None:
                    candidate += f'; margin {margin:.3f}'
                if similarity is not None and margin is not None:
                    candidate += f'; similarity {similarity:.3f}'
                if not model_used and (margin is not None or similarity is not None):
                    score += ' (rule made the assignment)'
                table.add_row(cell(f'{index} / {source}'), cell(preview or 'Hidden'),
                              cell(row.get('reason', rule)), cell(f'{candidate}\n{score}'),
                              cell('Required' if name == 'unresolved' else 'Assigned',
                                   'yellow' if name == 'unresolved' else 'green'))
            self.console.print(table)

    def records(self, run):
        table = Table(title='RECORD GROUPING', expand=True)
        for label in ('Section / record', 'Source blocks', 'Grouping method'):
            table.add_column(label, overflow='fold')
        show_previews = any(preview for _, preview in run.blocks.values())
        if show_previews:
            table.add_column('Grouped source preview', overflow='fold')
        for row in run.groups.values():
            cells = [cell(f"{row['section']} / {', '.join(row['record_ids'])}"),
                     cell(', '.join(row['source_ids']), 'blue'), cell(row.get('rule'))]
            if show_previews:
                previews = [run.blocks[source][1] for source in row['source_ids'] if source in run.blocks]
                grouped = ' · '.join(value for value in previews if value)
                cells.append(cell(grouped[:220] + ('…' if len(grouped) > 220 else '') or 'Not available'))
            table.add_row(*cells)
        self.console.print(table)

    def field_table(self, run):
        table = Table(title='FIELD MAPPING AND EVIDENCE', expand=True)
        for label in ('Field', 'Value / evidence preview', 'Source blocks', 'Schema location', 'Mapping status'):
            table.add_column(label, overflow='fold')
        for row, preview in run.fields.values():
            status = row['evidence_state']
            table.add_row(cell(f"{row['section']}.{row['field']}"), cell(preview or 'Hidden'),
                          cell(', '.join(row['source_ids']) or 'No recorded span', 'blue'),
                          cell(row['value_ref'], 'dim'), cell(MISSING.get(status, status),
                                                            'green' if status == 'mapped' else 'yellow'))
        self.console.print(table)

    def export_table(self, run):
        table = Table(title='FINAL JSON DESTINATIONS', expand=True)
        for label in ('Destination', 'Final value preview', 'Source blocks', 'Source status'):
            table.add_column(label, overflow='fold')
        for row, preview in run.export_fields.values():
            table.add_row(cell(row['path']), cell(preview or 'Hidden'),
                          cell(', '.join(row['source_ids']) or 'No recorded span', 'blue'),
                          cell(row.get('status')))
        if run.export_fields:
            self.console.print(table)

    def activity(self, row, record):
        from local_api.services.terminal_trace_format import format_event
        title, inputs, outputs = format_event(row)
        fields = [(f'In · {key}', value) for key, value in inputs.items()]
        fields.extend((f'Out · {key}', value) for key, value in outputs.items())
        self.panel(title.upper(), fields, style='red' if record.levelno >= logging.ERROR else 'magenta')
        payload = getattr(record, 'trace_payload_preview', None)
        if payload:
            self.console.print(Panel(Syntax(payload, 'json', word_wrap=True),
                                     title='Private DEBUG payload preview',
                                     subtitle='Full redacted payload in private-payloads/',
                                     border_style='magenta'))
