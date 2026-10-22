'use strict';
let mappedResume = null, schemaGeneration = 0, schemaAbort = null;
function resetSchemaMapping() {
  schemaGeneration++; mappedResume = null;
  if (schemaAbort) schemaAbort.abort(); schemaAbort = null;
  $('map-schema').disabled = true; $('download-schema').disabled = true;
  $('schema-preview').hidden = true; $('schema-json').textContent = '';
  $('schema-status').textContent = 'Group sections before mapping.';
}
document.addEventListener('extraction-reset', resetSchemaMapping);
document.addEventListener('sections-reset', resetSchemaMapping);
document.addEventListener('sections-ready', () => { $('map-schema').disabled = !sectionResult; });
$('map-schema').addEventListener('click', async () => {
  if (!result?.elements || !sectionResult || schemaAbort) return;
  const generation = ++schemaGeneration;
  const controller = new AbortController(); schemaAbort = controller;
  $('map-schema').disabled = true; $('download-schema').disabled = true;
  $('schema-status').textContent = 'Mapping existing blocks…';
  try {
    const data = await readResponse(await fetch('/api/v1/resume/schema', {
      method: 'POST', signal: controller.signal, headers: {'Content-Type':'application/json'},
      body: JSON.stringify({elements:result.elements, sections:sectionResult, source:file?.name || 'uploaded-resume'})
    }));
    if (generation !== schemaGeneration) return;
    mappedResume = data; $('schema-json').textContent = JSON.stringify(data,null,2);
    $('schema-preview').hidden = false; $('download-schema').disabled = false;
    const missing = data.meta?.missing_required_fields?.length || 0;
    $('schema-status').textContent = `Schema mapped. ${missing} required field(s) missing. Review field evidence and record warnings before use.`;
  } catch (error) {
    if (generation === schemaGeneration) $('schema-status').textContent = error.message;
  } finally {
    if (schemaAbort === controller) { schemaAbort = null; $('map-schema').disabled = !sectionResult; }
  }
});
$('download-schema').addEventListener('click', () => {
  if (!mappedResume) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(mappedResume,null,2)],{type:'application/json'}));
  const anchor = node('a'); anchor.href = url;
  anchor.download = (file?.name || 'resume').replace(/\.[^.]+$/,'')+'.schema.json'; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url),1000);
});
