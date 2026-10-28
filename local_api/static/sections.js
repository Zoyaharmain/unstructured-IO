'use strict';
let sectionResult = null, sectionGeneration = 0, sectionsBusy = false, sectionAbort = null;
const sectionStatus = (message, error = false) => { $('section-status').textContent = message; $('section-status').className = error ? 'status error' : 'status'; };
function updateSectionButton() { $('detect-sections').disabled = !result?.text.trim() || sectionsBusy; }
document.addEventListener('extraction-reset', () => {
  sectionGeneration++; sectionResult = null; sectionsBusy = false;
  if (sectionAbort) sectionAbort.abort(); sectionAbort = null;
  $('verify-extraction').checked = false; $('verify-extraction').disabled = true;
  $('download-sections').disabled = true; $('section-results').replaceChildren();
  updateSectionButton(); sectionStatus('Extract a resume to see its section blocks automatically.');
});
document.addEventListener('extraction-ready', () => { $('verify-extraction').disabled = !result?.text.trim(); updateSectionButton(); if (result?.text.trim()) { selectTab($('tab-sections')); detectSections(); } });
$('verify-extraction').addEventListener('change', () => {
  if (sectionResult) sectionResult.extraction_verified = $('verify-extraction').checked;
});
function renderSectionBlock(block) {
  const card = node('article', 'section-source');
  card.append(node('p', 'block-text', block.text || '(Empty element)'));
  const details = document.createElement('details'); details.append(node('summary', '', `Source block ${block.source_element_index + 1} · ${block.page_number == null ? 'Page unknown' : 'Page ' + block.page_number} · ${block.assignment}`));
  details.append(node('p', '', block.reason), node('pre', '', JSON.stringify({source_start:block.start, source_end:block.end, lane:block.lane, cluster_id:block.cluster_id, cluster_space:block.cluster_space, context_source_element_index:block.context_source_element_index, similarity:block.similarity, margin:block.margin, candidate_section:block.candidate_section, alternatives:block.alternatives, reviewed_by_llm:block.reviewed_by_llm, local_section:block.local_section, local_assignment:block.local_assignment, llm_action:block.llm_action}, null, 2)));
  const locate = node('button', 'text-button', 'Locate source block ↗');
  locate.addEventListener('click', () => {
    selectTab($('tab-blocks')); $('search').value = ''; $('type-filter').value = ''; renderBlocks();
    const source = $('block-list').querySelector(`[data-source-index="${block.source_element_index}"]`);
    if (source) { source.click(); source.scrollIntoView({block:'center', behavior:'smooth'}); source.focus({preventScroll:true}); }
  });
  card.append(details, locate); return card;
}
function renderReadableGroup(group, section) {
  const container = node('div', 'readable-group ' + group.kind);
  const first = group.block_indices[0];
  const sourceTitle = group.kind === 'role' && first != null && group.title && section.blocks[first].text.toLocaleLowerCase().includes(group.title.toLocaleLowerCase());
  if (group.title) container.append(node('h4', '', sourceTitle ? section.blocks[first].text.trim() : group.title));
  let paragraph = [], previous = null;
  const flush = () => { if (paragraph.length) container.append(node('p', 'readable-text', paragraph.join(' '))); paragraph = []; previous = null; };
  for (const index of group.block_indices) {
    if (sourceTitle && index === first) continue;
    const block = section.blocks[index];
    const text = block.text.replace(/\s+/g, ' ').trim();
    if (!text) continue;
    if (/^[•▪●*]\s*|^-\s+/.test(text)) {
      flush(); container.append(node('p', 'readable-text readable-bullet', text));
    } else {
      const seamless = previous && previous.source_element_index === block.source_element_index && previous.end === block.start && !/\s$/.test(previous.text) && !/^\s/.test(block.text);
      if (seamless && paragraph.length) paragraph[paragraph.length - 1] += text; else paragraph.push(text);
      previous = block;
    }
  }
  flush();
  for (const child of group.children) container.append(renderReadableGroup(child, section));
  return container;
}
function renderSectionResults(data, localOnly) {
  const fragment = document.createDocumentFragment();
  fragment.append(node('h3', '', localOnly ? 'Local model output · no DeepSeek' : data.metadata.llm_review?.status === 'complete' ? 'Output after DeepSeek review' : 'Local output · DeepSeek review incomplete'));
  const summary = node('div', 'compare-summary');
  for (const [value, label] of [[data.sections.length, 'Proposed sections'], [data.metadata.assigned_units, 'Assigned text units'], [data.metadata.review_units, 'Units needing review']]) { const card = node('div', 'compare-stat'); card.append(node('strong','',value), node('span','',label)); summary.append(card); }
  fragment.append(summary, node('p','comparison-note', `${data.metadata.assigned_text_percent}% of text assigned; this is coverage, not accuracy. All extracted input text preserved: ${data.metadata.all_source_text_preserved ? 'yes' : 'no'}.`));
  const review = data.metadata.llm_review;
  const reviewNote = node('p', 'comparison-note llm-review-status');
  reviewNote.dataset.status = review?.status || 'disabled';
  if (review?.status === 'complete') reviewNote.textContent = `DeepSeek reviewed all ${review.reviewed_units} source spans · ${review.changed_units} placement changes · ${review.resolved_units} previously unassigned spans resolved · ${review.pass_count || 1} review pass(es) · ${review.split_units || 0} mixed spans split.`;
  else if (review?.status === 'failed') { reviewNote.textContent = (review.message || 'DeepSeek review failed.') + ' Showing unchanged local blocks; these have not been LLM-validated.'; reviewNote.classList.add('error'); }
  else if (review?.status === 'not_configured') reviewNote.textContent = 'DeepSeek review is enabled but its API key/model is missing. Showing local grouping only.';
  else reviewNote.textContent = localOnly ? 'Local inspection selected. DeepSeek was not called, even if enabled on the server.' : 'DeepSeek review is disabled. Showing local grouping only.';
  fragment.append(reviewNote);
  const warnings = document.createElement('details'); warnings.className = 'section-warnings'; warnings.append(node('summary','','Model limitations and evidence'));
  for (const warning of data.warnings) warnings.append(node('p','comparison-note',warning));
  warnings.append(node('p','comparison-note',`${data.metadata.encoder} · ${data.metadata.algorithm}`)); fragment.append(warnings);
  const inspection = node('details', 'block-inspection');
  inspection.append(node('summary', '', 'Inspect original source fragments and boundaries'));
  inspection.append(node('h3', '', 'Detected block boundaries and labels'), node('p', 'comparison-note', 'Each outlined card is one detected text interval. Compare its full text, page and section with the PDF. These are text blocks, not predicted rectangles on the page. Similarity is an embedding score, not accuracy.'));
  const allBlocks = data.sections.flatMap(section => section.blocks.map(block => ({block, label:section.label, category:section.category})));
  allBlocks.push(...data.needs_review.map(block => ({block, label:'Needs review', category:'needs_review'})));
  allBlocks.sort((a,b) => a.block.source_element_index-b.block.source_element_index || a.block.start-b.block.start);
  const filter = document.createElement('select'); filter.setAttribute('aria-label', 'Filter detected blocks by section');
  const choices = [...new Set(allBlocks.map(item => item.label))];
  for (const label of ['All detected blocks', ...choices]) { const option = node('option', '', label); option.value = label; filter.append(option); }
  inspection.append(filter);
  const list = node('div', 'detected-block-list');
  allBlocks.forEach(({block, label, category}, index) => {
    const card = node('article', 'detected-block-card'); card.dataset.label = label;
    if (category === 'needs_review') card.classList.add('unresolved');
    card.append(node('h4', '', `Block ${index + 1} · ${label}`), node('p', 'comparison-note', `Page ${block.page_number ?? '?'} · source element ${block.source_element_index + 1} · characters ${block.start}–${block.end} · ${block.assignment}`));
    if (typeof block.similarity === 'number') card.append(node('p', 'comparison-note', `Similarity ${block.similarity.toFixed(3)} · cluster ${block.cluster_id ?? 'none'}`));
    card.append(renderSectionBlock(block)); list.append(card);
  });
  filter.addEventListener('change', () => { for (const card of list.children) card.hidden = filter.value !== 'All detected blocks' && card.dataset.label !== filter.value; });
  inspection.append(list); fragment.append(inspection);
  for (const section of data.sections) {
    const text = typeof section.text === 'string' ? section.text : (section.blocks || []).map(block => block.text || '').join('\n');
    const card = node('section','resume-section'); const header = node('div','section-title');
    header.append(node('h3','',section.label), node('span','',`${text.trim() ? text.trim().split(/\s+/).length : 0} words`)); card.append(header);
    card.dataset.category = section.category;
    if (section.source_heading && section.source_heading.toLocaleLowerCase() !== section.label.toLocaleLowerCase()) card.append(node('p', 'comparison-note source-heading', `Detected heading: ${section.source_heading}`));
    const content=node('div','canonical-section-text'); const chars=Array.from(text); let cursor=0;
    for (const highlight of section.highlights || []) {
      if (!Number.isInteger(highlight.start) || !Number.isInteger(highlight.end) || highlight.start<cursor || highlight.end>chars.length) continue;
      content.append(document.createTextNode(chars.slice(cursor,highlight.start).join('')));
      const emphasis=node('strong','resume-emphasis '+highlight.kind,chars.slice(highlight.start,highlight.end).join('')); emphasis.title=highlight.kind;
      content.append(emphasis); cursor=highlight.end;
    }
    content.append(document.createTextNode(chars.slice(cursor).join('')));
    if (section.logical_blocks?.length) {
      for (const [index, group] of section.logical_blocks.entries()) {
        const logical = node('article', 'logical-record');
        if (group.kind !== 'section') logical.append(node('h4', '', group.kind === 'unresolved' ? 'Unassigned record content' : `${section.label} ${index + 1}`));
        if (group.semantic_frame) {
          const scope = group.semantic_frame.scope === 'one_record' ? 'One complete record' : group.semantic_frame.scope === 'complete_section' ? 'Complete section' : 'Association needed';
          logical.append(node('p', 'comparison-note', `${group.semantic_frame.meaning} · ${scope}`));
        }
        logical.append(node('p', 'readable-text', group.text));
        for (const reason of group.review_reasons || []) logical.append(node('p', 'comparison-note', reason));
        card.append(logical);
      }
    } else card.append(content);
    if (section.category === 'experience' && section.readable_blocks?.length) {
      const hierarchy = document.createElement('details'); hierarchy.className = 'section-evidence';
      hierarchy.append(node('summary', '', 'View employers and roles'));
      for (const group of section.readable_blocks) hierarchy.append(renderReadableGroup(group, section));
      card.append(hierarchy);
    }
    const evidence = document.createElement('details'); evidence.className = 'section-evidence';
    evidence.append(node('summary', '', 'Inspect original text and grouping evidence'));
    if (section.logical_blocks?.length) evidence.append(content);
    for (const block of section.blocks) evidence.append(renderSectionBlock(block));
    card.append(evidence);
    fragment.append(card);
  }
  if (data.needs_review.length) { const card = node('section','resume-section review-section'); card.append(node('h3','','Needs review — not forced into a section')); for (const block of data.needs_review) card.append(renderSectionBlock(block)); fragment.append(card); }
    $('section-results').replaceChildren(fragment);
}
async function detectSections() {
  if (!result || sectionsBusy) return;
  document.dispatchEvent(new Event('sections-reset'));
  const generation = ++sectionGeneration; const controller = new AbortController(); sectionAbort = controller; sectionsBusy = true; updateSectionButton();
  const localOnly = $('section-mode').value === 'local';
  workflowStage('review', 'working', localOnly ? 'Running local section detection…' : 'Detecting sections, then reviewing with DeepSeek…');
  workflowStage('schema', 'pending', 'Waiting for section review');
  $('workflow-verdict').textContent = 'Review in progress. Results will appear automatically.';
  sectionStatus(localOnly ? 'Running local Sentence-BERT, K-means and boundary recovery… No DeepSeek calls.' : 'Grouping sections and applying configured LLM review…');
  $('section-results').replaceChildren(); $('download-sections').disabled = true;
  try {
    const data = await readResponse(await fetch(localOnly ? '/api/v1/resume/sections/local' : '/api/v1/resume/sections', {method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({elements:result.elements, extraction_verified:$('verify-extraction').checked})}));
    if (generation !== sectionGeneration) return;
    sectionResult = data;
    sectionResult.extraction_verified = $('verify-extraction').checked;
    renderSectionResults(data, localOnly);
    const review = data.metadata.llm_review;
    workflowStage('review', review?.status === 'complete' ? 'complete' : localOnly ? 'local' : 'failed',
      review?.status === 'complete' ? `DeepSeek complete · ${review.changed_units || 0} placement changes` : localOnly ? 'Local-only mode selected' : review?.message || 'DeepSeek did not complete; local results retained');
    $('download-sections').disabled = false; document.dispatchEvent(new Event('sections-ready'));
    sectionStatus(localOnly ? 'Local blocks are ready. Inspect the numbered boundaries and section labels below; no DeepSeek was called.' : review?.status === 'complete' ? 'LLM-reviewed sections are ready. Check any remaining Needs review items.' : 'Local sections are ready. DeepSeek review has not completed; inspect Needs review before use.');
  } catch (error) { if (generation === sectionGeneration) { sectionStatus(error.message, true); workflowStage('review', 'failed', error.message); $('workflow-verdict').textContent = 'Section processing failed. Retry after checking the error.'; } }
  finally { if (sectionAbort === controller) { sectionAbort = null; sectionsBusy = false; updateSectionButton(); } }
}
$('detect-sections').addEventListener('click', detectSections);
$('section-mode').addEventListener('change', () => {
  sectionGeneration++; if (sectionAbort) sectionAbort.abort(); sectionAbort = null; sectionsBusy = false;
  sectionResult = null; $('section-results').replaceChildren(); $('download-sections').disabled = true;
  document.dispatchEvent(new Event('sections-reset')); updateSectionButton();
  if (result?.text.trim()) detectSections();
});
$('download-sections').addEventListener('click', () => {
  if (!sectionResult) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(sectionResult,null,2)],{type:'application/json'}));
  const anchor = node('a'); anchor.href = url; anchor.download = file.name.replace(/\.[^.]+$/,'')+'.sections.json'; anchor.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});

async function checkDeepSeekConnection() {
  const button = $('check-llm-connection'); button.disabled = true;
  $('llm-connection').textContent = 'Checking DeepSeek connection…';
  try {
    const data = await readResponse(await fetch('/api/v1/resume/review-connection', {method:'POST'}));
    $('llm-connection').textContent = data.message;
    $('llm-connection').dataset.status = data.status;
  } catch {
    $('llm-connection').textContent = 'Connection check unavailable. Restart the app with the latest startup script.';
    $('llm-connection').dataset.status = 'failed';
  } finally { button.disabled = false; }
}
$('check-llm-connection').addEventListener('click', checkDeepSeekConnection);
// Read local configuration on load; external connection checks stay explicit.
fetch('/api/v1/resume/review-status').then(readResponse).then(data => {
  if ($('llm-connection').dataset.status) return;
  $('llm-connection').textContent = data.enabled && data.configured
    ? `DeepSeek enabled · ${data.model}. Uploaded resume text will be sent for section review.`
    : 'DeepSeek is not enabled or configured in this server. Restart with scripts/start_resume_inspector_local.py after setting DEEPSEEK_API_KEY in .env.';
}).catch(() => { $('llm-connection').textContent = 'Unable to read DeepSeek configuration. Check that the API server is running.'; });
