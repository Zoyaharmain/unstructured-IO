const fs=require('fs'),vm=require('vm'),assert=require('assert');
const page=fs.readFileSync('reports/manual-field-review-resume-20261024-v2/group-01.html','utf8');
const source=page.split('<script>')[1].split('</script>')[0];
class Element{constructor(){this.value='';this.children=[];this.textContent='';}append(e){this.children.push(e);}click(){}}
const elements={rows:new Element(),reviewer:new Element(),message:new Element(),json:new Element(),csv:new Element()};
let lastBlob;
const context=vm.createContext({document:{createElement:()=>new Element(),getElementById:id=>elements[id]},
 Blob:class{constructor(parts){this.parts=parts;lastBlob=this;}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},setTimeout:()=>{},console});
vm.runInContext(source,context);
assert.throws(()=>vm.runInContext('reviewed()',context),/reviewer name/);
elements.reviewer.value='Test Reviewer';
assert.throws(()=>vm.runInContext('reviewed()',context),/No decisions/);
vm.runInContext("controls[0].decision.value='correct';controls[0].decision.onchange()",context);
const reviewed=vm.runInContext('reviewed()',context);
assert.equal(reviewed.length,1);assert.equal(reviewed[0].row_id,'A001');
assert.equal(reviewed[0].expected_values[0],'Aditya Vashisth');
assert.equal(vm.runInContext('rows[0].expected_values',context),null);
vm.runInContext("download('json')",context);
const exported=JSON.parse(lastBlob.parts.join(''));
assert.equal(exported.pending_rows_omitted,5);assert.equal(exported.decisions.length,1);
vm.runInContext("controls[0].evidence.value='[{\"source_id\":\"e99:0:2\",\"quote\":\"Fake\"}]'",context);
assert.throws(()=>vm.runInContext('reviewed()',context),/quote does not occur/);
vm.runInContext("controls[0].decision.value='ambiguous';controls[0].notes.value='Needs PDF check'",context);
assert.equal(vm.runInContext('reviewed()[0].expected_values',context),null);
console.log('Review-page behavior checks passed: explicit decision required, pending omitted, source quotes checked, uncertainty retained, original rows unchanged.');
