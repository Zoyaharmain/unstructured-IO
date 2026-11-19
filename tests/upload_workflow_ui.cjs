const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const events = [];
class Element {
  constructor() {
    this.dataset = {};
    this.children = [];
    this.value = '';
  }
  addEventListener() {}
  setAttribute() {}
  querySelector() { return this.children[0] ||= new Element(); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  add(option) { this.append(option); }
}

const nodes = new Map();
function getElementById(id) {
  if (!nodes.has(id)) nodes.set(id, new Element());
  return nodes.get(id);
}

const context = vm.createContext({
  document: {
    getElementById,
    querySelectorAll: () => [],
    createElement: () => new Element(),
    createDocumentFragment: () => new Element(),
    dispatchEvent: event => events.push(event.type),
  },
  window: {addEventListener() {}},
  Event, URL,
  Option: class {},
  File, FormData,
  performance,
});
const appPath = 'local_api/static/app.js';
vm.runInContext(fs.readFileSync(appPath, 'utf8'), context, {filename: appPath});
context.selectedFile = new File(['sample'], payload.filename);

async function main() {
  let finish;
  context.fetch = (url, request) => {
    assert.equal(url, '/api/v1/extract/text');
    assert.equal(request.method, 'POST');
    assert.equal(request.body.get('include_elements'), 'true');
    return new Promise(resolve => { finish = resolve; });
  };
  const extraction = context.chooseFile(context.selectedFile);
  assert.equal(getElementById('extract').disabled, true);
  assert.equal(getElementById('stage-extract').dataset.state, 'working');
  finish({ok: true, json: async () => payload});
  await extraction;
  assert.equal(getElementById('plain-text').textContent, payload.text);
  assert.equal(getElementById('stage-extract').dataset.state, 'complete');
  assert.equal(getElementById('extract').disabled, false);
  assert.equal(getElementById('block-badge').textContent, payload.metadata.total_elements);
  assert.equal(events.filter(event => event === 'extraction-ready').length, 1);

  for (const [response, message] of [
    [{ok: false, status: 413, json: async () => ({detail: 'Uploaded file exceeds configured size limit'})},
      /exceeds configured size limit/],
    [{ok: false, status: 502, json: async () => { throw new SyntaxError(); }},
      /HTTP 502/],
  ]) {
    context.fetch = async () => response;
    await context.runExtraction();
    assert.equal(getElementById('stage-extract').dataset.state, 'failed');
    assert.match(getElementById('status').textContent, message);
    assert.equal(getElementById('extract').disabled, false);
    assert.equal(getElementById('download').disabled, true);
    assert.equal(events.filter(event => event === 'extraction-ready').length, 1);
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
