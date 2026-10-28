'use strict';
// Browser renderers do not consistently expose floating Word text boxes.
// Render a private copy in reading order; the original download stays unchanged.
async function prepareDocxPreview(data) {
  const archive = await JSZip.loadAsync(data);
  const part = archive.file('word/document.xml');
  if (!part) throw new Error('Missing document part');
  const xml = new DOMParser().parseFromString(await part.async('string'), 'application/xml');
  if (xml.getElementsByTagName('parsererror').length) throw new Error('Invalid document XML');
  const w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';
  const mc = 'http://schemas.openxmlformats.org/markup-compatibility/2006';
  for (const alternate of [...xml.getElementsByTagNameNS(mc, 'AlternateContent')]) {
    const branches = [...alternate.children];
    const eligible = branches.filter(b => b.getElementsByTagNameNS(w, 'txbxContent').length);
    if (eligible.length) {
      const selected = eligible.find(b => b.localName === 'Choice') || eligible[0];
      alternate.replaceWith(...[...selected.childNodes]);
    }
  }
  const tails = new Map();
  while (xml.getElementsByTagNameNS(w, 'txbxContent').length) {
    const box = xml.getElementsByTagNameNS(w, 'txbxContent')[0];
    let anchor = box.parentElement;
    while (anchor && !(anchor.namespaceURI === w && anchor.localName === 'p')) anchor = anchor.parentElement;
    if (!anchor) throw new Error('Unsupported text box anchor');
    let tail = tails.get(anchor) || anchor;
    for (const child of [...box.children]) {
      if (child.namespaceURI === w && ['p', 'tbl'].includes(child.localName)) {
        const copy = child.cloneNode(true);
        tail.parentNode.insertBefore(copy, tail.nextSibling); tail = copy;
      }
    }
    tails.set(anchor, tail); box.remove();
  }
  archive.file('word/document.xml', new XMLSerializer().serializeToString(xml));
  return archive.generateAsync({type: 'arraybuffer'});
}
let previewScale = 'fit';
function fitDocxPreview() {
  const container = document.getElementById('document');
  const available = Math.max(1, container.clientWidth - 32);
  for (const page of container.querySelectorAll('section.docx')) {
    page.style.zoom = '1';
    const width = Math.max(page.getBoundingClientRect().width, page.scrollWidth);
    page.style.zoom = String(previewScale === 'fit' ? Math.min(1, available / width) : 1);
  }
}
document.getElementById('preview-fit')?.addEventListener('click', () => {previewScale='fit'; fitDocxPreview();});
document.getElementById('preview-full')?.addEventListener('click', () => {previewScale='full'; fitDocxPreview();});
new ResizeObserver(fitDocxPreview).observe(document.documentElement);
window.addEventListener('message', async event => {
  if (event.source !== parent || event.data?.type !== 'render-docx') return;
  try {
    await docx.renderAsync(await prepareDocxPreview(event.data.data), document.getElementById('document'), null,
      {ignoreWidth: false, ignoreHeight: true, renderAltChunks: false, useBase64URL: true});
    fitDocxPreview();
    document.getElementById('message').hidden = true;
  } catch {
    document.getElementById('message').textContent = 'This file could not be previewed. Open it in Word to inspect the original.';
    parent.postMessage({type: 'docx-error'}, '*');
  }
});
