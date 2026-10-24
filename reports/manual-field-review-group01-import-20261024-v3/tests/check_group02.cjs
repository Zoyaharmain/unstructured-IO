const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('reports/manual-field-review-group01-import-20261024-v3/group-02.html','utf8');
const source=html.split('<script>')[1].split('</script>')[0];
class Element{constructor(){this.value='';this.children=[];this.textContent='';}append(e){this.children.push(e);}click(){}}
const elements={rows:new Element(),reviewer:new Element(),message:new Element(),json:new Element(),csv:new Element()};
let blob;
const context=vm.createContext({document:{createElement:()=>new Element(),getElementById:id=>elements[id]},
 Blob:class{constructor(parts){this.parts=parts;blob=this;}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},setTimeout:()=>{}});
vm.runInContext(source,context);elements.reviewer.value='Test reviewer';
assert.equal(vm.runInContext('rows.length',context),5);
assert.throws(()=>vm.runInContext('reviewed()',context),/No decisions/);
vm.runInContext("controls[0].decision.value='correct';controls[0].decision.onchange()",context);
assert.throws(()=>vm.runInContext('reviewed()',context),/explicit values/);
vm.runInContext("controls[0].decision.value='absent';controls[0].decision.onchange()",context);
assert.throws(()=>vm.runInContext('reviewed()',context),/verified absence/);
vm.runInContext("controls[0].absence.checked=true;controls[0].notes.value='Checked original PDF for candidate location.'",context);
const decisions=vm.runInContext('reviewed()',context);
assert.equal(decisions.length,1);assert.equal(decisions[0].review_status,'absent');
assert.equal(decisions[0].expected_values.length,0);
assert.equal(decisions[0].absence_scope.kind,'reviewer_declared_original_pdf_review');
assert.ok(decisions[0].absence_scope.source_sha256);
vm.runInContext("download('json')",context);
const exported=JSON.parse(blob.parts.join(''));
assert.equal(exported.review_group,'group-02');assert.equal(exported.pending_rows_omitted,4);
assert.equal(vm.runInContext('rows[0].review_status',context),'pending');
console.log('Group 02 behavior passed: five pending fields, explicit decisions, no inferred absence, scope/checkbox required, unreviewed rows omitted, original state unchanged.');
