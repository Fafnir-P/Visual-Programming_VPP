// Helper for tests/test_assembled_cards.py:  node tests/assemble_cards.js <outdir>
// Writes <outdir>/cards_7.py (the 7-card sample graph) and <outdir>/cards_all.py (every card), then
// prints {requestBytes, inputTokens} of the 7-card request as JSON. No network.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..', 'prototype');
const ctx = vm.createContext({ console, TextEncoder });
for (const f of ['catalog.js', 'templates.js', 'ports.js', 'prompt.js', 'meter.js', 'models.js', 'compile.js', 'bedrock.js']) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), 'utf8'), ctx, { filename: f });
}
const CAT = vm.runInContext('CATALOG', ctx);
const nodeFor = (title, id) => {
  const c = CAT.find((x) => x.title === title);
  return { id, catalogID: c.id, title, type: c.category, role: c.role, ports: c.ports };
};
const E = (id, a, ap, b, bp) => ({ id, fromNodeID: a, fromPort: ap, toNodeID: b, toPort: bp });
const nodes = [['App Start', 'n1'], ['Enter Text', 'n2'], ['Trim Whitespace', 'n3'], ['Change Text Case', 'n4'],
  ['Check Field Is Required', 'n5'], ['Show Message Banner', 'n6'], ['App End', 'n7']].map((a) => nodeFor(...a));
const edges = [E('e1', 'n2', 'value', 'n3', 'text'), E('e2', 'n3', 'text', 'n4', 'text'), E('e3', 'n4', 'text', 'n5', 'value'),
  E('e4', 'n5', 'value', 'n6', 'message'), E('e5', 'n1', 'event', 'n7', 'finish')];
ctx.__n = nodes;
ctx.__e = edges;
ctx.__all = CAT.map((c, i) => nodeFor(c.title, 'a' + i));
vm.runInContext(`state = { order: [], nodes: new Map(), edges: new Map() };
  getBedrockEndpoint = () => 'https://example.invalid/converse';
  for (const n of __n) { state.nodes.set(n.id, n); state.order.push(n.id); }
  for (const e of __e) state.edges.set(e.id, e);`, ctx);
const req = vm.runInContext('assembleBedrockRequest()', ctx);
const graph = JSON.parse(req.body.messages[0].content[0].text);
const out = process.argv[2];
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'cards_7.py'), vm.runInContext('assembleCardsModule', ctx)(graph.nodes));
fs.writeFileSync(path.join(out, 'cards_all.py'), vm.runInContext('assembleCardsModule', ctx)(ctx.__all));
console.log(JSON.stringify({
  requestBytes: Buffer.byteLength(JSON.stringify(req)),
  bodyBytes: Buffer.byteLength(JSON.stringify(req.body)),
  inputTokens: vm.runInContext('estimateRequestTokens', ctx)(req),
  functions7: Object.keys(graph.cards),
}));
