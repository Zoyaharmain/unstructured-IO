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
    mappedResume = data; $('schema-json').textContent = JSON.stringify(data,null,2);
    renderSubschemas(data.section_schemas || []);
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
        if (!field.items.length) add(value, 'span', ({not_stated:'Not stated in this source record.',ambiguous:'Ambiguous — source association needs review.',unmapped:'Present in source — mapping still needs review.'})[field.status] || 'Unresolved — not established by the local mapper.');
        for (const item of field.items) {
          add(value, 'p', String(item.value) + (item.status === 'needs_review' ? ' · association needs review' : ''));
          const evidence = add(value, 'details', ''); add(evidence, 'summary', 'Source evidence');
          for (const ref of item.evidence) add(evidence, 'p', `${ref.source_id}: “${ref.quote}”`);
        }
      }
      for (const reason of record.review_reasons) add(group, 'p', reason);
    }
    if (section.residual_blocks.length) {
      const residual = add(card, 'details', '');
      add(residual, 'summary', `${section.residual_blocks.length} source excerpts with headings or text not fully covered by field citations`);
      for (const block of section.residual_blocks) add(residual, 'p', `${block.source_id}: ${block.quote}`);
    }
  }
}
$('download-schema').addEventListener('click', () => {
  if (!mappedResume) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(mappedResume,null,2)],{type:'application/json'}));
  const anchor = node('a'); anchor.href = url;
  anchor.download = (file?.name || 'resume').replace(/\.[^.]+$/,'')+'.schema.json'; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url),1000);
});
