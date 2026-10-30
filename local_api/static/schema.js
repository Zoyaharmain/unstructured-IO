'use strict';
let mappedResume = null, schemaGeneration = 0, schemaAbort = null;
function resetSchemaMapping() {
  schemaGeneration++; mappedResume = null;
  if (schemaAbort) schemaAbort.abort(); schemaAbort = null;
  $('map-schema').disabled = true; $('download-schema').disabled = true;
  $('schema-preview').hidden = true; $('schema-json').textContent = '';
  $('schema-fields').replaceChildren();
  $('schema-status').textContent = 'Group sections before mapping.';
}
document.addEventListener('extraction-reset', resetSchemaMapping);
document.addEventListener('sections-reset', resetSchemaMapping);
document.addEventListener('sections-ready', () => { $('map-schema').disabled = !sectionResult; mapExistingSections(); });
async function mapExistingSections() {
  if (!result?.elements || !sectionResult || schemaAbort) return;
  const generation = ++schemaGeneration;
  const controller = new AbortController(); schemaAbort = controller;
  $('map-schema').disabled = true; $('download-schema').disabled = true;
  const reviewFields = $('section-mode').value === 'reviewed';
  $('schema-status').textContent = reviewFields ? 'DeepSeek is mapping fields and subschemas from source evidence…' : 'Mapping existing blocks…';
  workflowStage('schema', 'working', 'Assigning fields and checking source evidence…');
  try {
    const data = await readResponse(await fetch('/api/v1/resume/schema', {
      method: 'POST', signal: controller.signal, headers: {'Content-Type':'application/json'},
      body: JSON.stringify({elements:result.elements, sections:sectionResult, source:file?.name || 'uploaded-resume', review_fields:reviewFields})
    }));
    if (generation !== schemaGeneration) return;
    if (data.meta?.reviewed_sections) {
      sectionResult = data.meta.reviewed_sections;
      renderSectionResults(sectionResult, $('section-mode').value === 'local');
    }
    mappedResume = data; $('schema-json').textContent = JSON.stringify(standardizedResumeExport(data),null,2);
    renderSubschemas(data.section_schemas || []);
    renderStandardizationWarnings(data);
    $('schema-preview').hidden = false; $('download-schema').disabled = false;
    const missing = data.meta?.missing_required_fields?.length || 0;
    const coverage = data.meta?.source_coverage_ledger?.status_counts || {};
    const unmapped = coverage.present_but_unmapped || 0;
    const ambiguous = coverage.present_but_ambiguous || 0;
    $('schema-status').textContent = `Schema mapped. ${missing} required field(s) missing; ${unmapped} field(s) present but unmapped; ${ambiguous} ambiguous. Review source evidence before use.`;
    const outcome = schemaOutcome(data, reviewFields);
    const reason = outcome.diagnostic ? ` ${outcome.diagnostic.recovered ? 'Corrected validation issue:' : 'Reason:'} ${outcome.diagnostic.category}${outcome.diagnostic.field ? ' (' + outcome.diagnostic.field + ')' : ''}. Details below.` : '';
    const findings = outcome.status === 'needs_review' && outcome.reviewReasons.length ? ' ' + outcome.reviewReasons.join('; ') + '.' : '';
    workflowStage('schema', outcome.status, outcome.message + findings + reason);
    $('workflow-verdict').textContent = outcome.message + findings;
    $('workflow-verdict').className = outcome.className;
    if (outcome.diagnostic) renderSchemaDiagnostic(outcome.diagnostic);
    if (outcome.recoveredDiagnostics.length) renderSchemaHistory(outcome.recoveredDiagnostics);

  } catch (error) {
    if (generation === schemaGeneration) { $('schema-status').textContent = error.message; workflowStage('schema', 'failed', error.message); $('workflow-verdict').textContent = 'Schema mapping failed. Section results remain available for inspection.'; $('workflow-verdict').className = 'status error'; if (error.diagnostic) renderSchemaDiagnostic(error.diagnostic); }
  } finally {
    if (schemaAbort === controller) { schemaAbort = null; $('map-schema').disabled = !sectionResult; }
  }
}
function renderSchemaDiagnostic(diagnostic, target = $('schema-status')) {
  const details = document.createElement('details'); details.className = 'schema-diagnostic'; details.open = diagnostic.recovered !== true;
  const summary = document.createElement('summary'); summary.textContent = diagnostic.recovered ? 'Resolved validation check (history)' : 'Field review failure details'; details.append(summary);
  const message = document.createElement('pre');
  const labels = {category:'Category', exception_type:'Exception', code:'Code', field:'Field', path:'Path', validation_message:'Reason', id:'Diagnostic reference'};
  message.textContent = Object.entries(labels).filter(([key]) => diagnostic[key] != null)
    .map(([key, label]) => `${label}: ${diagnostic[key]}`).join('\n');
  if (diagnostic.evidence_analysis) {
    const analysis = diagnostic.evidence_analysis;
    message.textContent += `\nField item: ${analysis.item_index + 1}\nEvidence check: ${JSON.stringify(analysis)}`;
  }
  details.append(message); target.append(details);
}
function renderSchemaHistory(diagnostics) {
  const history = document.createElement('details'); history.className = 'schema-history'; history.open = false;
  const summary = document.createElement('summary');
  summary.textContent = `Processing history: ${diagnostics.length} automatic correction(s) completed`;
  history.append(summary);
  const note = document.createElement('p');
  note.textContent = 'These checks were corrected and the final mapping was revalidated. Any remaining review items are listed in the current status above.';
  history.append(note);
  for (const diagnostic of diagnostics) renderSchemaDiagnostic(diagnostic, history);
  $('schema-status').append(history);
}
$('map-schema').addEventListener('click', mapExistingSections);
function schemaSourceCoverage(section, block, sources = []) {
  const text = block.quote;
  const covered = Array(text.length).fill(false);
  const mappedFields = new Set();
  const context = [];
  const source = sources.find(b => `e${b.source_element_index}:${b.start}:${b.end}` === block.source_id);
  if (source && ['section_heading', 'structural_heading'].includes(source.assignment)) {
    return {mappedFields: [], remaining: [], context: [text]};
  }
  // Labels group competencies; their values, not their labels, are skill items.
  if (section.category === 'skills' && text.includes(':')) {
    const end = text.indexOf(':') + 1;
    if (text.slice(0, end).split(/\s+/).length <= 8) {
      context.push(text.slice(0, end));
      covered.fill(true, 0, end);
    }
  }
  for (const record of section.records) for (const field of record.attributes) {
    for (const item of field.items) for (const ref of item.evidence) {
      if (ref.source_id !== block.source_id || !ref.quote) continue;
      const start = text.indexOf(ref.quote);
      // Repeated quotes lack offsets: leave ambiguous occurrences visible.
      if (start < 0 || text.indexOf(ref.quote, start + 1) !== -1) continue;
      covered.fill(true, start, start + ref.quote.length);
      mappedFields.add(`${section.category}.${field.name}`);
    }
  }
  const remaining = [];
  let start = null;
  for (let i = 0; i <= text.length; i++) {
    if (i < text.length && !covered[i]) { if (start === null) start = i; }
    else if (start !== null) {
      const value = text.slice(start, i).trim();
      if (/[\p{L}\p{N}]/u.test(value)) remaining.push(value);
      start = null;
    }
  }
  return {mappedFields: [...mappedFields], remaining, context};
}
function renderSubschemas(sections) {
  const root = $('schema-fields'); root.replaceChildren();
  const add = (parent, tag, text) => {
    const element = document.createElement(tag); element.textContent = text;
    parent.append(element); return element;
  };
  for (const section of sections) {
    const card = add(root, 'section', '');
    add(card, 'h3', section.label);
    for (const [index, record] of section.records.entries()) {
      const group = add(card, 'details', ''); group.open = true;
      group.dataset.recordId = record.record_id;
      add(group, 'summary', `${section.label} ${index + 1}`);
      const fields = add(group, 'dl', '');
      for (const field of record.attributes) {
        add(fields, 'dt', field.name.replaceAll('_', ' '));
        const value = add(fields, 'dd', '');
        const standardized = section.category === 'experience' && field.name === 'duration'
          ? mappedResume?.standardized_data?.experience?.[index] : null;
        if (standardized) {
          add(value, 'p', (standardized.duration ? `${standardized.duration_months} months · ${standardized.duration}` : null) || 'Cannot calculate duration safely from these dates.');
          if (standardized.duration) add(value, 'small', `${standardized.duration_is_approximate ? 'Approximate calendar-month coverage' : 'Calculated from exact dates'}${standardized.duration_as_of ? ' · as of '+standardized.duration_as_of : ''}`);
        }

        if (!standardized && !field.items.length) add(value, 'span', ({not_stated:'Not stated in this source record.',ambiguous:'Ambiguous — source association needs review.',unmapped:'Present in source — mapping still needs review.'})[field.status] || 'Unresolved — not established by the local mapper.');
        for (const item of field.items) {
          if (!standardized) add(value, 'p', String(item.value) + (item.status === 'needs_review' ? ' · association needs review' : ''));
          const evidence = add(value, 'details', ''); add(evidence, 'summary', 'Source evidence');
          if (standardized) add(evidence, 'p', 'Original source duration/range: '+String(item.value));
          for (const ref of item.evidence) add(evidence, 'p', `${ref.source_id}: “${ref.quote}”`);
        }
      }
      for (const reason of record.review_reasons) add(group, 'p', reason);
    }
    if (section.residual_blocks.length) {
      const residual = add(card, 'details', '');
      const sources = sectionResult?.sections?.find(s => s.category === section.category)?.blocks || [];
      const coverage = section.residual_blocks.map(block => ({block, ...schemaSourceCoverage(section, block, sources)}));
      const incomplete = coverage.filter(item => item.remaining.length);
      add(residual, 'summary', incomplete.length
        ? `${incomplete.length} source excerpt(s) contain text still needing field mapping`
        : 'Source coverage: cited content mapped; headings and labels retained as context');
      for (const item of coverage) {
        const row = add(residual, 'details', '');
        add(row, 'summary', `${item.block.source_id} · ${item.remaining.length ? 'Some text needs mapping' : item.mappedFields.length ? 'Mapped' : 'Section context'}`);
        if (item.mappedFields.length) add(row, 'p', `Assigned to: ${item.mappedFields.join(', ')}`);
        if (item.context.length) add(row, 'p', `Heading or label: ${item.context.join(' ')}`);
        for (const value of item.remaining) add(row, 'p', `Still needs mapping: ${value}`);
        const original = add(row, 'details', '');
        add(original, 'summary', 'Original source excerpt');
        add(original, 'p', item.block.quote);
      }
    }
  }
}
function standardizedResumeExport(response) {
  if (!response.standardized_data) return response;
  const clean = value => Array.isArray(value) ? value.map(clean)
    : value && typeof value === 'object' ? Object.fromEntries(Object.entries(value)
      .filter(([key]) => !key.startsWith('raw_')).map(([key, item]) => [key, clean(item)])) : value;
  const data = clean(response.standardized_data);
  const metadata = {...response.standardization_metadata};
  const diagnosticKeys = ['duration_is_approximate', 'duration_as_of', 'duration_status',
    'start_date_iso', 'end_date_iso', 'start_date_precision', 'end_date_precision'];
  const order = ['company', 'role', 'location', 'start_date', 'end_date', 'is_current',
    'duration', 'duration_months', 'responsibilities', 'technologies'];
  metadata.experience_calculations = (data.experience || []).map((job, index) => {
    const calculation = {record_path: `data.experience[${index}]`};
    for (const key of diagnosticKeys) if (key in job) {calculation[key] = job[key]; delete job[key];}
    data.experience[index] = Object.fromEntries([
      ...order.filter(key => key in job).map(key => [key, job[key]]),
      ...Object.entries(job).filter(([key]) => !order.includes(key))
    ]);
    return calculation;
  });
  return {
    export_type: 'standardized_resume',
    schema_version: response.standardization_metadata?.schema_version || '1.1.0',
    source: response.source,
    data,
    standardization_metadata: metadata,
    validation_status: response.validation_status,
    warnings: response.warnings || [],
    source_evidence: Object.fromEntries(['data', 'section_schemas', 'meta', 'raw_sections', 'field_index']
      .filter(key => key in response).map(key => [key, response[key]]))
  };
}
function renderStandardizationWarnings(data) {
  if (!data.standardized_data) return;
  const card = document.createElement('details');
  const heading = document.createElement('summary');
  heading.textContent = `Standardization checks · ${data.warnings?.length || 0} notices`;
  card.append(heading);
  const policy = document.createElement('p');
  policy.textContent = `As of ${data.standardization_metadata?.as_of_date || 'unspecified'} · ${data.standardization_metadata?.duration_policy || ''}`;
  card.append(policy);
  for (const warning of data.warnings || []) {
    const text = document.createElement('p');
    text.textContent = `${warning.field}: ${warning.message}${warning.suggested_value ? ' Suggested: '+warning.suggested_value : ''}${warning.basis ? ' Basis: '+warning.basis : ''}`;
    card.append(text);
  }
  $('schema-fields').append(card);
}
$('download-schema').addEventListener('click', () => {
  if (!mappedResume) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(standardizedResumeExport(mappedResume),null,2)],{type:'application/json'}));
  const anchor = node('a'); anchor.href = url;
  anchor.download = (file?.name || 'resume').replace(/\.[^.]+$/,'')+(mappedResume.standardized_data ? '.standardized.json' : '.schema.json'); anchor.click();
  setTimeout(() => URL.revokeObjectURL(url),1000);
});
