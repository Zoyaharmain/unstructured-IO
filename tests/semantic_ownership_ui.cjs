// Exercise the actual render functions with a small DOM; no duplicate renderer.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.textContent = ''; this.dataset = {}; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  get text() { return this.textContent + this.children.map(c => typeof c === 'string' ? c : c.text).join('\n'); }
}
function functionSource(file, name) {
  const source = fs.readFileSync(file, 'utf8');
  const start = source.indexOf(`function ${name}(`);
  assert(start >= 0);
  const end = source.indexOf('\nfunction ', start + 1);
  return source.slice(start, end < 0 ? source.length : end);
}
const sections = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const mapping = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const root = new Element('main');
const context = {document: {createElement: tag => new Element(tag)},
  node: (tag, cls, text = '') => Object.assign(new Element(tag), {textContent: text}),
  $: () => root, mappedResume: mapping, sectionResult: sections};
vm.createContext(context);
for (const [file, name] of [['local_api/static/sections.js', 'renderLogicalRecord'],
                          ['local_api/static/schema.js', 'schemaSourceCoverage'],
                          ['local_api/static/schema.js', 'renderSubschemas']]) {
  vm.runInContext(functionSource(file, name), context);
}
for (const section of sections.sections) {
  for (const group of section.logical_blocks) {
    const dom = context.renderLogicalRecord(group, section);
    assert(dom.text.includes(group.text));
    for (const child of group.children || []) {
      assert(dom.children.some(node => node.tag === 'article' && node.text.includes(child.text)), 'Child must render inside its parent');
    }
  }
}
context.renderSubschemas(mapping.section_schemas);
const flatten = element => [element, ...element.children.filter(c => typeof c !== 'string').flatMap(flatten)];
const nodes = flatten(root);
for (const section of mapping.section_schemas) for (const record of section.records) {
  const rendered = nodes.find(node => node.dataset.recordId === record.record_id);
  assert(rendered, `Missing schema record ${record.record_id}`);
  if (record.parent_record_id) {
    const parent = nodes.find(node => node.dataset.recordId === record.parent_record_id);
    assert(parent.children.includes(rendered), 'Schema child must render inside its parent');
  }
}
const bridge = 'Integrated reporting.';
if (JSON.stringify(mapping).includes(bridge)) {
  assert(root.text.includes(bridge), 'Corrected description is visible');
}
console.log(JSON.stringify({section_renderer: 'passed', schema_renderer: 'passed', nested_parents: 'checked when present', browser_visual_validation: 'not_performed'}));
