'use strict';
const $ = id => document.getElementById(id);
let file = null, result = null, originalURL = null, busy = false, comparisonGeneration = 0;
const node = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; };
function status(message, kind = '') { $('status').textContent = message; $('status').className = `status ${kind}`; }
function setBusy(value) { busy = value; $('file').disabled = value; $('strategy').disabled = value || file?.name.toLowerCase().endsWith('.docx'); $('extract').disabled = value || !file; $('extract').textContent = value ? 'Extracting…' : 'Extract & inspect →'; $('dropzone').setAttribute('aria-disabled', String(value)); }
function clearResult() {
  comparisonGeneration++;
  document.dispatchEvent(new Event('extraction-reset'));
  result = null;
  for (const id of ['words', 'blocks-count', 'characters', 'pages']) $(id).textContent = '—';
  $('block-badge').textContent = '0'; $('block-list').replaceChildren(node('div', 'empty', 'Extract this document to inspect its text blocks.'));
  $('plain-text').textContent = 'Extracted plain text will appear here.';
  for (const id of ['download', 'copy', 'search', 'type-filter', 'compare']) $(id).disabled = true;
  $('search').value = ''; $('type-filter').replaceChildren(new Option('All types', '')); $('comparison').replaceChildren();
}
async function chooseFile(selected) {
  if (!selected || busy) return;
  if (!/\.(pdf|docx)$/i.test(selected.name)) { status('Choose a PDF or DOCX resume.', 'error'); return; }
  file = selected; clearResult(); $('reference').value = '';
  if (originalURL) URL.revokeObjectURL(originalURL);
  originalURL = URL.createObjectURL(file);
  $('file-name').textContent = file.name;
  $('file-info').textContent = `${(file.size / 1024).toLocaleString(undefined, {maximumFractionDigits: 1})} KB · Ready to inspect`;
  $('open-original').href = originalURL; $('open-original').hidden = false;
  const isDocx = /\.docx$/i.test(file.name);
  if (isDocx) $('strategy').value = 'auto';
  setBusy(false);
  const frame = document.createElement('iframe'); frame.title = isDocx ? 'Original DOCX browser preview' : 'Original PDF';
  if (isDocx) {
    $('preview-label').textContent = 'DOCX browser preview · layout may differ from Microsoft Word';
    frame.sandbox = 'allow-scripts'; frame.src = '/static/docx-preview.html';
    frame.addEventListener('load', async () => {
      try { const data = await selected.arrayBuffer(); if (frame.isConnected) frame.contentWindow.postMessage({type: 'render-docx', data}, '*', [data]); }
      catch { $('preview-label').textContent = 'Preview unavailable. Use Open ↗ to inspect the original file.'; }
    }, {once: true});
  } else { frame.src = originalURL + '#view=FitH&navpanes=0'; $('preview-label').textContent = 'Original PDF · select a block with page metadata to navigate'; }
  $('preview').replaceChildren(frame);
  status('Ready. Choose a strategy and click Extract & inspect.');
}
$('file').addEventListener('change', event => chooseFile(event.target.files[0]));
for (const eventName of ['dragover', 'dragenter']) $('dropzone').addEventListener(eventName, event => { event.preventDefault(); if (!busy) $('dropzone').classList.add('dragging'); });
for (const eventName of ['dragleave', 'drop']) $('dropzone').addEventListener(eventName, event => { event.preventDefault(); $('dropzone').classList.remove('dragging'); });
$('dropzone').addEventListener('drop', event => chooseFile(event.dataTransfer.files[0]));
window.addEventListener('message', event => { const frame = $('preview').querySelector('iframe'); if (frame && event.source === frame.contentWindow && event.data?.type === 'docx-error') $('preview-label').textContent = 'DOCX preview unavailable. Use Open ↗ to view the original; extraction can still be tried.'; });
$('strategy').addEventListener('change', () => { clearResult(); status('Strategy changed. Extract again to see the new result.'); });
async function readResponse(response) { let body; try { body = await response.json(); } catch { throw new Error(`The server returned HTTP ${response.status}. Please try again.`); } if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'The request could not be processed. Check the file or text size.'); return body; }
$('extract').addEventListener('click', async () => {
  if (!file || busy) return;
  clearResult(); setBusy(true); status('Extracting locally… OCR and layout models can take longer on the first run.', 'busy');
  const started = performance.now();
  const data = new FormData(); data.append('file', file); data.append('strategy', $('strategy').value); data.append('include_elements', 'true');
  try {
    result = await readResponse(await fetch('/api/v1/extract/text', {method: 'POST', body: data}));
    $('words').textContent = (result.text.match(/\S+/gu) || []).length.toLocaleString();
    $('characters').textContent = Array.from(result.text).length.toLocaleString();
    $('blocks-count').textContent = result.metadata.total_elements.toLocaleString();
    $('block-badge').textContent = result.metadata.total_elements;
    $('pages').textContent = new Set(result.elements.filter(element => element.text.trim() && element.page_number != null).map(element => element.page_number)).size || 'Unknown';
    $('plain-text').textContent = result.text || 'No text was extracted.';
    for (const id of ['download', 'copy', 'search', 'type-filter', 'compare']) $(id).disabled = false;
    for (const type of [...new Set(result.elements.map(element => element.type))].sort()) $('type-filter').add(new Option(type, type));
    renderBlocks();
    document.dispatchEvent(new Event('extraction-ready'));
    status(result.text.trim() ? `Extraction complete in ${((performance.now() - started) / 1000).toFixed(1)}s · Requested strategy: ${result.strategy} · Review blocks or compare against reference text.` : 'No text was extracted. If this is a scanned PDF, try OCR only or High resolution.', result.text.trim() ? '' : 'error');
  } catch (error) { status(error.message || 'Unable to reach the extraction server.', 'error'); }
  finally { setBusy(false); }
});
function renderBlocks() {
  const query = $('search').value.toLocaleLowerCase(), type = $('type-filter').value;
  const fragment = document.createDocumentFragment(); let shown = 0;
  (result?.elements || []).forEach((element, index) => {
    if ((type && element.type !== type) || !element.text.toLocaleLowerCase().includes(query)) return;
    shown++;
    const block = node('article', 'block'); block.dataset.sourceIndex = index; block.tabIndex = 0; block.setAttribute('aria-label', `Block ${index + 1}, ${element.type}`);
    const header = node('div', 'block-header'); header.append(node('span', '', String(index + 1).padStart(2, '0')), node('span', 'block-type', element.type), node('span', 'block-page', element.page_number == null ? 'Page unknown' : `Page ${element.page_number}`));
    const details = document.createElement('details'); details.append(node('summary', '', 'View metadata'), node('pre', '', JSON.stringify(element.metadata, null, 2)));
    block.append(header, node('div', 'block-text', element.text || '(Empty element)'), details);
    function select() { $('block-list').querySelectorAll('.selected').forEach(el => el.classList.remove('selected')); block.classList.add('selected'); if (/\.pdf$/i.test(file.name) && Number.isInteger(element.page_number) && element.page_number > 0) $('preview').querySelector('iframe').src = `${originalURL}#page=${element.page_number}&view=FitH&navpanes=0`; }
    block.addEventListener('click', event => { if (!event.target.closest('details')) select(); });
    block.addEventListener('keydown', event => { if (event.target === block && ['Enter', ' '].includes(event.key)) { event.preventDefault(); select(); } });
    fragment.append(block);
  });
  if (!shown) fragment.append(node('div', 'empty', result?.elements.length ? 'No blocks match your search.' : 'No text blocks were returned.'));
  $('block-list').replaceChildren(fragment);
}
$('search').addEventListener('input', renderBlocks); $('type-filter').addEventListener('change', renderBlocks);
const tabs = [...document.querySelectorAll('.tab')];
function selectTab(tab) { for (const item of tabs) { const active = item === tab; item.classList.toggle('active', active); item.setAttribute('aria-selected', String(active)); item.tabIndex = active ? 0 : -1; $('view-' + item.dataset.view).hidden = !active; } }
for (const tab of tabs) { tab.tabIndex = tab.classList.contains('active') ? 0 : -1; tab.addEventListener('click', () => selectTab(tab)); tab.addEventListener('keydown', event => { if (['ArrowLeft', 'ArrowRight'].includes(event.key)) { event.preventDefault(); const next = tabs[(tabs.indexOf(tab) + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length]; selectTab(next); next.focus(); } }); }
$('download').addEventListener('click', () => { if (!result) return; const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], {type: 'application/json'})); const anchor = node('a'); anchor.href = url; anchor.download = file.name.replace(/\.[^.]+$/, '') + '.extraction.json'; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); });
$('copy').addEventListener('click', async () => { try { await navigator.clipboard.writeText(result.text); $('copy').textContent = 'Copied'; setTimeout(() => { $('copy').textContent = 'Copy text'; }, 1800); } catch { status('Clipboard unavailable. Select and copy text from the Plain text tab.'); } });
for (const id of ['reference', 'ignore-case']) $(id).addEventListener('input', () => { comparisonGeneration++; $('comparison').replaceChildren(); });
$('compare').addEventListener('click', async () => {
  if (!result) return;
  if (!$('reference').value.trim()) { $('comparison').replaceChildren(node('p', 'status error', 'Paste reference text from the original resume first.')); $('reference').focus(); return; }
  const generation = ++comparisonGeneration;
  $('compare').disabled = true; $('comparison').replaceChildren(node('p', 'status busy', 'Comparing words…'));
  try {
    const extractedText = result.text;
    const data = await readResponse(await fetch('/api/v1/compare/text', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({reference: $('reference').value, extracted: extractedText, ignore_case: $('ignore-case').checked})}));
    if (!result || generation !== comparisonGeneration) return;
    const summary = node('div', 'compare-summary');
    for (const [value, label] of [[`${data.reference_coverage}%`, 'Reference coverage'], [data.missing_words, 'Missing reference words'], [data.extra_words, 'Added extracted words']]) { const metric = node('div', 'compare-stat'); metric.append(node('strong', '', value), node('span', '', label)); summary.append(metric); }
    const legend = node('div', 'diff-legend'); legend.append(node('span', 'missing-key', '− Missing from extraction'), node('span', 'extra-key', '+ Added in extraction'));
    const diff = node('div', 'diff');
    for (const segment of data.segments) { if (segment.kind === 'equal') diff.append(document.createTextNode(segment.reference + ' ')); else { if (segment.reference) diff.append(node('del', '', segment.reference + ' ')); if (segment.extracted) diff.append(node('ins', '', segment.extracted + ' ')); } }
    const explanation = node('p', 'comparison-note', `${data.matched_words.toLocaleString()} of ${data.reference_words.toLocaleString()} reference words matched in reading order. Moved text can appear as both missing and added. Formatting and block boundaries are not scored.`);
    $('comparison').replaceChildren(summary, explanation, legend, diff);
  } catch (error) { if (generation === comparisonGeneration) $('comparison').replaceChildren(node('p', 'status error', error.message)); }
  finally { $('compare').disabled = !result; }
});
window.addEventListener('beforeunload', () => { if (originalURL) URL.revokeObjectURL(originalURL); });
