'use strict';
let sectionResult = null, sectionGeneration = 0, sectionsBusy = false, sectionAbort = null;
const sectionStatus = (message, error = false) => { $('section-status').textContent = message; $('section-status').className = error ? 'status error' : 'status'; };
function updateSectionButton() { $('detect-sections').disabled = !result?.text.trim() || !$('verify-extraction').checked || sectionsBusy; }
document.addEventListener('extraction-reset', () => {
  sectionGeneration++; sectionResult = null; sectionsBusy = false;
  if (sectionAbort) sectionAbort.abort(); sectionAbort = null;
  $('verify-extraction').checked = false; $('verify-extraction').disabled = true;
  $('download-sections').disabled = true; $('section-results').replaceChildren();
  updateSectionButton(); sectionStatus('Extract and verify the text before grouping it.');
});
document.addEventListener('extraction-ready', () => { $('verify-extraction').disabled = !result?.text.trim(); updateSectionButton(); });
$('verify-extraction').addEventListener('change', () => {
  if (!$('verify-extraction').checked) { if (sectionAbort) sectionAbort.abort(); sectionAbort = null; sectionsBusy = false; sectionGeneration++; sectionResult = null; $('section-results').replaceChildren(); $('download-sections').disabled = true; sectionStatus('Verify the extracted words to enable section detection.'); }
  updateSectionButton();
});
function renderSectionBlock(block) {
  const card = node('article', 'section-source');
  card.append(node('p', 'block-text', block.text || '(Empty element)'));
  const details = document.createElement('details'); details.append(node('summary', '', `Source block ${block.source_element_index + 1} · ${block.page_number == null ? 'Page unknown' : 'Page ' + block.page_number} · ${block.assignment}`));
  details.append(node('p', '', block.reason), node('pre', '', JSON.stringify({source_start:block.start, source_end:block.end, lane:block.lane, cluster_id:block.cluster_id, cluster_space:block.cluster_space, context_source_element_index:block.context_source_element_index, similarity:block.similarity, margin:block.margin, candidate_section:block.candidate_section, alternatives:block.alternatives}, null, 2)));
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
$('detect-sections').addEventListener('click', async () => {
  if (!result || !$('verify-extraction').checked || sectionsBusy) return;
  const generation = ++sectionGeneration; const controller = new AbortController(); sectionAbort = controller; sectionsBusy = true; updateSectionButton();
  sectionStatus('Running local BERT embeddings and K-means… First use can take longer.');
  $('section-results').replaceChildren(); $('download-sections').disabled = true;
  try {
    const data = await readResponse(await fetch('/api/v1/resume/sections', {method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({elements:result.elements, extraction_verified:true})}));
    if (generation !== sectionGeneration) return;
    sectionResult = data;
    const fragment = document.createDocumentFragment();
    const summary = node('div', 'compare-summary');
    for (const [value, label] of [[data.sections.length, 'Proposed sections'], [data.metadata.assigned_units, 'Assigned text units'], [data.metadata.review_units, 'Units needing review']]) { const card = node('div', 'compare-stat'); card.append(node('strong','',value), node('span','',label)); summary.append(card); }
    fragment.append(summary, node('p','comparison-note', `${data.metadata.assigned_text_percent}% of text assigned; this is coverage, not accuracy. All extracted input text preserved: ${data.metadata.all_source_text_preserved ? 'yes' : 'no'}.`));
    const warnings = document.createElement('details'); warnings.className = 'section-warnings'; warnings.append(node('summary','','Model limitations and evidence'));
    for (const warning of data.warnings) warnings.append(node('p','comparison-note',warning));
    warnings.append(node('p','comparison-note',`${data.metadata.encoder} · ${data.metadata.algorithm}`)); fragment.append(warnings);
    for (const section of data.sections) {
      const card = node('section','resume-section'); const header = node('div','section-title');
      header.append(node('h3','',section.label), node('span','',`${section.blocks.length} source units`)); card.append(header);
      header.querySelector('h3').textContent = section.source_heading || section.label;
      for (const group of section.readable_blocks || []) card.append(renderReadableGroup(group, section));
      const evidence = document.createElement('details'); evidence.className = 'section-evidence';
      evidence.append(node('summary', '', 'Inspect original text and grouping evidence'));
      for (const block of section.blocks) evidence.append(renderSectionBlock(block));
      card.append(evidence);
      fragment.append(card);
    }
    if (data.needs_review.length) { const card = node('section','resume-section review-section'); card.append(node('h3','','Needs review — not forced into a section')); for (const block of data.needs_review) card.append(renderSectionBlock(block)); fragment.append(card); }
    $('section-results').replaceChildren(fragment); $('download-sections').disabled = false;
    sectionStatus('Proposed sections are ready. Verify their boundaries and inspect Needs review before use.');
  } catch (error) { if (generation === sectionGeneration) sectionStatus(error.message, true); }
  finally { if (sectionAbort === controller) { sectionAbort = null; sectionsBusy = false; updateSectionButton(); } }
});
$('download-sections').addEventListener('click', () => {
  if (!sectionResult) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(sectionResult,null,2)],{type:'application/json'}));
  const anchor = node('a'); anchor.href = url; anchor.download = file.name.replace(/\.[^.]+$/,'')+'.sections.json'; anchor.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
