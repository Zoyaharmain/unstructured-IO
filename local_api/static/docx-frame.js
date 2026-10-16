'use strict';
window.addEventListener('message', async event => {
  if (event.source !== parent || event.data?.type !== 'render-docx') return;
  try {
    await docx.renderAsync(event.data.data, document.getElementById('document'), null,
      {ignoreWidth: true, ignoreHeight: true, renderAltChunks: false, useBase64URL: true});
    document.getElementById('message').hidden = true;
  } catch {
    document.getElementById('message').textContent = 'This file could not be previewed. Open it in Word to inspect the original.';
    parent.postMessage({type: 'docx-error'}, '*');
  }
});
