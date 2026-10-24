"""Offline six-row review form with explicit JSON/CSV download, no autosubmission."""
import json
from pathlib import Path
OUT=Path(__file__).parent
rows=json.loads((OUT/'group-01.json').read_text())['rows']
for row in rows:
    row['document_key']='aditya-vashisth' if row['row_id'].startswith('A') else 'manjunath-murugan'
payload=json.dumps(rows,ensure_ascii=False).replace('<','\\u003c')
page=r'''<!doctype html><meta charset="utf-8"><title>Group 01: contact field review</title>
<style>body{font:16px system-ui;margin:24px;max-width:1100px}article{border:1px solid #bbb;border-radius:6px;padding:16px;margin:20px 0}pre{white-space:pre-wrap;background:#f5f5f5;padding:10px}textarea{display:block;width:98%;min-height:55px}label{display:block;margin:12px 0}button{padding:10px;margin:8px}input{padding:6px}small{display:block;color:#444}#message{white-space:pre-wrap}</style>
<h1>Group 01 — six contact fields</h1>
<p>Every row starts unreviewed. Compare the original PDF with the saved source text and current output. Confirming means you approve the displayed value, parent, record and exact evidence together. Correct any part or leave it uncertain.</p>
<p><strong>Selections are temporary until you download JSON or CSV.</strong> Downloads create a separate decision file, not a ground-truth update. Keep the file and share its saved path. No API calls, automatic approvals or scoring occur here.</p>
<label>Your reviewer name <input id="reviewer" autocomplete="name"></label><div id="rows"></div>
<button id="json">Download reviewed decisions (JSON)</button><button id="csv">Download reviewed decisions (CSV)</button><p id="message" role="status"></p>
<script>
const rows=PAYLOAD;
function el(tag,text,parent){const n=document.createElement(tag);n.textContent=text;parent.append(n);return n;}
const controls=[];
for(const row of rows){
 const article=el('article','',document.getElementById('rows'));
 el('h2',`${row.row_id} · ${row.document_key} · ${row.attribute}`,article);
 el('p',`Current parent: ${row.parent_section}; current record: ${row.predicted_record_id}`,article);
 el('pre','Mapped value: '+JSON.stringify(row.predicted_values),article);
 const source=el('details','',article);el('summary','Original saved record text',source);
 for(const block of row.source_text)el('pre',`${block.source_id}: ${block.text??block.quote??''}`,source);
 el('pre','Proposed evidence (not approved): '+JSON.stringify(row.predicted_evidence),article);
 const decision=el('select','',el('label','Decision ',article));
 for(const [value,label] of [['pending','Unreviewed'],['correct','Confirm displayed value + parent + record + evidence'],['corrected','Correct the fields below'],['ambiguous','Uncertain — do not treat as verified']]){const option=el('option',label,decision);option.value=value;}
 decision.value='pending';
 const values=el('textarea','',el('label','Your expected values (JSON array)',article));
 const parent=el('input','',el('label','Your expected parent section',article));
 const association=el('textarea','',el('label','Your expected record association (JSON object)',article));
 const evidence=el('textarea','',el('label','Your exact source evidence (JSON array)',article));
 const notes=el('textarea','',el('label','Reviewer notes / uncertainty',article));
 decision.onchange=()=>{if(decision.value==='correct'){
   values.value=JSON.stringify(row.predicted_values);parent.value=row.parent_section;
   association.value=JSON.stringify({kind:'record_id',value:row.predicted_record_id});evidence.value=JSON.stringify(row.predicted_evidence);
 }};
 controls.push({row,decision,values,parent,association,evidence,notes});
}
function reviewed(){
 const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer)throw Error('Enter your reviewer name.');
 const selected=controls.filter(c=>c.decision.value!=='pending');if(!selected.length)throw Error('No decisions selected. Pending rows are not approvals.');
 return selected.map(c=>{
  const result={document_key:c.row.document_key,row_id:c.row.row_id,attribute:c.row.attribute,
   review_status:c.decision.value,reviewer,reviewed_at:new Date().toISOString(),reviewer_notes:c.notes.value,
   expected_values:null,expected_parent_section:null,expected_record_association:null,reviewer_source_evidence:[]};
  if(c.decision.value==='ambiguous'){if(!c.notes.value.trim())throw Error(c.row.row_id+': describe the uncertainty.');return result;}
  result.expected_values=JSON.parse(c.values.value);result.expected_parent_section=c.parent.value.trim();
  result.expected_record_association=JSON.parse(c.association.value);result.reviewer_source_evidence=JSON.parse(c.evidence.value);
  if(!Array.isArray(result.expected_values)||!result.expected_values.length||!result.expected_parent_section||!result.expected_record_association.kind||!Array.isArray(result.reviewer_source_evidence)||!result.reviewer_source_evidence.length)throw Error(c.row.row_id+': explicit values, parent, record and evidence are required. Use uncertainty for unresolved/absent facts in this first group.');
  for(const q of result.reviewer_source_evidence){const block=c.row.source_text.find(b=>b.source_id===q.source_id);if(!q.quote?.trim()||!block||(block.text??block.quote??'').includes(q.quote)===false)throw Error(c.row.row_id+': quote does not occur in the selected original source block.');}
  for(const value of result.expected_values){if(!result.reviewer_source_evidence.some(q=>q.quote.includes(String(value))))throw Error(c.row.row_id+': expected value must be supported by an exact source quote.');}
  return result;
 });
}
function download(kind){try{
 const decisions=reviewed();const filename='group-01-reviewed-'+new Date().toISOString().replaceAll(':','-');
 let content;
 if(kind==='json')content=JSON.stringify({review_group:'group-01',pending_rows_omitted:rows.length-decisions.length,decisions},null,2);
 else {const fields=['document_key','row_id','attribute','review_status','expected_values','expected_parent_section','expected_record_association','reviewer_source_evidence','reviewer','reviewed_at','reviewer_notes'];
 const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
 content=[fields,...decisions.map(d=>fields.map(k=>typeof d[k]==='object'?JSON.stringify(d[k]):d[k]))].map(record=>record.map(quote).join(',')).join('\r\n');}
 const url=URL.createObjectURL(new Blob([content],{type:kind==='json'?'application/json':'text/csv'}));
 const link=document.createElement('a');link.href=url;link.download=filename+'.'+kind;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 document.getElementById('message').textContent='Downloaded '+decisions.length+' explicit decisions. Save the file and provide its path. No ground truth or score has been updated.';
 }catch(error){document.getElementById('message').textContent=error.message;}}
document.getElementById('json').onclick=()=>download('json');document.getElementById('csv').onclick=()=>download('csv');
</script>'''.replace('PAYLOAD',payload)
(OUT/'group-01.html').write_text(page)
