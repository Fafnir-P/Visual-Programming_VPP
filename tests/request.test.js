// Tests for the Generate request (prototype/bedrock.js with prototype/templates.js).
// Plain Node, no packages:   node tests/request.test.js
// No network is used: assembleBedrockRequest only builds the request.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..', 'prototype');
const ctx = vm.createContext({ console, TextEncoder });
for (const f of ['catalog.js', 'templates.js', 'ports.js', 'prompt.js', 'meter.js', 'models.js', 'compile.js', 'bedrock.js']) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), 'utf8'), ctx, { filename: f });
}
const run = (code) => vm.runInContext(code, ctx);

let pass = 0;
let fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; } else { fail++; console.log('FAIL', name, extra === undefined ? '' : extra); }
}

const CATALOG = run('CATALOG');
const TEMPLATES = run('CARD_TEMPLATES');
ok(CATALOG.every((c) => TEMPLATES[c.title]), 'every catalog card has a template');
ok(Object.keys(TEMPLATES).length === CATALOG.length, 'no extra templates');
ok(!!TEMPLATES['App Start'] && !!TEMPLATES['App End'], 'App Start and App End have templates');
ok(CATALOG.every((c) => !/@card\(|examples=/.test(TEMPLATES[c.title].source)), 'no decorator or examples in sources');

// A canvas with App Start, Enter Text and App End.
function nodeFor(title, id) {
  const c = CATALOG.find((x) => x.title === title);
  return { id, catalogID: c.id, title, type: c.category, role: c.role, ports: c.ports };
}
run(`state = { order: [], nodes: new Map(), edges: new Map() };
     getBedrockEndpoint = () => 'https://example.invalid/converse';`);
ctx.__nodes = [nodeFor('App Start', 'n1'), nodeFor('Enter Text', 'n2'), nodeFor('App End', 'n3')];
run(`for (const n of __nodes) { state.nodes.set(n.id, n); state.order.push(n.id); }`);

const req = run('assembleBedrockRequest()');
const graph = JSON.parse(req.body.messages[0].content[0].text);
ok(graph.nodes.length === 3, 'only the cards on the canvas are sent', graph.nodes.length);
ok(Object.keys(graph).sort().join() === 'cards,edges,nodes,order', 'request keys', Object.keys(graph).join());
ok(!/templateCode|"source"|runtimeNames|requiredConfig/.test(req.body.messages[0].content[0].text), 'no template source or old fields in the request');
ok(!req.body.messages[0].content[0].text.includes('\n'), 'graph text is compact JSON (no indentation)');
const text = graph.nodes.find((n) => n.title === 'Enter Text');
ok(text.fn === TEMPLATES['Enter Text'].function && !!graph.cards[text.fn], 'Enter Text function and its entry in cards');
ok(JSON.stringify(Object.keys(text).sort()) === JSON.stringify(['fn', 'id', 'title']), 'node fields', Object.keys(text).join());
ok(text.set === undefined && text.settings === undefined, 'request: settings equal to the default are not sent');
{
  const full = run('serializeGraph()');
  const ft = full.nodes.find((n) => n.title === 'Enter Text');
  ok(JSON.stringify(ft.settings) === JSON.stringify(Object.fromEntries(
    TEMPLATES['Enter Text'].settings.filter((s) => !s.required).map((s) => [s.name, s.default]))), 'full graph holds the defaults');
}
const card = graph.cards[text.fn];
ok(JSON.stringify(card.out) === JSON.stringify(TEMPLATES['Enter Text'].outputs) && card.set.includes('name') && Array.isArray(card.in) && card.req === undefined, 'cards entry: in, set, out (req only when needed)');
ok(Object.keys(graph.cards).join() === 'enter_text', 'Start and End cards have no function entry', Object.keys(graph.cards).join());
ok(graph.nodes.find((n) => n.title === 'App Start').fn === undefined && graph.nodes.find((n) => n.title === 'App End').role === 'end', 'Start/End nodes: no function, role kept');
ok(!req.body.messages[0].content[0].text.includes(TEMPLATES['Trim Whitespace'].function), 'unused card not sent');
ok(Object.keys(graph.nodes.find((n) => n.title === 'App Start')).sort().join() === 'id,role,title', 'App Start node is id, role, title only');
ok(!/blank in this prototype|empty object in this prototype/.test(run('SYSTEM_PROMPT')), 'prompt no longer says placeholder');
ok(!/placeholder|blank in this prototype/i.test(run('SYSTEM_PROMPT')), 'prompt has no placeholder wording');
ok(/Python 3\.10\+/.test(run('SYSTEM_PROMPT')) && !/3\.8/.test(run('SYSTEM_PROMPT')), 'prompt targets Python 3.10+');
ok(/Context\(store=Store\(\)\)/.test(run('SYSTEM_PROMPT')) && /=== FILE:/.test(run('SYSTEM_PROMPT')) && /=== GAP:/.test(run('SYSTEM_PROMPT')), 'prompt explains calls and reply format');
ok(/'--' \+ the card's setting 'name'/.test(run('SYSTEM_PROMPT')) && /role start\/end/.test(run('SYSTEM_PROMPT')), 'prompt explains value source and App Start/End');

// Nodes carry their role, so the issue checker sees Start and End.
ok(graph.nodes.length === 3 && ctx.__nodes.every((n) => n.role !== undefined), 'test nodes have role');
{
  const issues = run('findGenerationIssues(state.nodes, state.edges, state.order)').map((i) => i.kind).sort().join();
  ok(/start_unlinked/.test(issues) && !/no_start|no_end/.test(issues), 'issue checker with roles: Start and End found', issues);
}

// Reply parser.
{
  const parse = (t) => { ctx.__t = t; return run('parseGenerationReply(__t)'); };
  let r = parse('note\n=== FILE: main.py ===\nprint(1)\n\nx = 2\n=== END FILE ===\n=== FILE: sub/a.py ===\na\n=== END FILE ===\n');
  ok(r.files.length === 2 && r.gaps.length === 0, 'parse: two files');
  ok(r.files[0].path === 'main.py' && r.files[0].content === 'print(1)\n\nx = 2', 'parse: content kept', JSON.stringify(r.files[0]));
  r = parse('=== GAP: Enter Number | no value for first ===\r\n');
  ok(r.files.length === 0 && r.gaps.length === 1 && r.gaps[0].card === 'Enter Number' && r.gaps[0].missing === 'no value for first', 'parse: gap only');
  for (const p of ['../x.py', 'a/../../x.py', '/etc/x', 'C:\\x.py', '\\x.py']) {
    r = parse('=== FILE: ' + p + ' ===\nbad\n=== END FILE ===');
    ok(r.files.length === 0 && r.gaps.length === 1, 'parse: refuses path ' + p, JSON.stringify(r));
  }
  r = parse('=== FILE: a.py ===\nunclosed');
  ok(r.files.length === 0 && r.gaps.length === 1, 'parse: unclosed block is a gap');
}
// Fixes round 2: parser rules.
{
  const parse = (t) => { ctx.__t = t; return run('parseGenerationReply(__t)'); };
  const file = (p, body) => '=== FILE: ' + p + ' ===\n' + (body === undefined ? 'x' : body) + '\n=== END FILE ===\n';
  let r = parse('=== GAP: Enter Number no bar ===');
  ok(r.files.length === 0 && r.gaps.length === 1 && r.gaps[0].card === '(reply)' && /Malformed GAP/.test(r.gaps[0].missing), 'parse: malformed GAP line is a gap', JSON.stringify(r));
  for (const empty of ['', 'just notes', '   \n']) {
    r = parse(empty);
    ok(r.files.length === 0 && r.gaps.length === 1 && r.gaps[0].card === '(reply)' && r.gaps[0].missing === 'no files in reply', 'parse: empty reply is a gap', JSON.stringify(r));
  }
  for (const p of ['a:b.py', 'main.py::$DATA', 'C:x.py', 'CON', 'nul.txt', 'sub/PRN.py', 'aux', 'COM1.txt', 'lpt9', 'a/./b.py', './a.py', '~/x.py', '~x.py', 'a//b.py', 'a.py.', 'a /b.py', 'a\u0001b.py']) {
    r = parse(file(p));
    ok(r.files.length === 0 && r.gaps.length === 1 && /Refused file/.test(r.gaps[0].missing), 'parse: refuses ' + JSON.stringify(p), JSON.stringify(r));
  }
  for (const p of ['console.py', 'com10.py', 'a/b/c.py', 'cards.py']) {
    r = parse(file(p));
    ok(r.files.length === 1 && r.gaps.length === 0, 'parse: allows ' + p, JSON.stringify(r));
  }
  r = parse(file('a.py') + file('A.PY') + file('b/c.py') + file('b\\c.py'));
  ok(r.files.length === 1 + 1 && r.gaps.length === 2, 'parse: duplicate paths refused', JSON.stringify(r.gaps));
  let many = '';
  for (let i = 0; i < 21; i++) many += file('f' + i + '.py');
  r = parse(many);
  ok(r.files.length === 20 && r.gaps.length === 1 && /more than 20/.test(r.gaps[0].missing), 'parse: file count capped at 20', r.files.length + ' ' + r.gaps.length);
  r = parse(file('big.py', 'x'.repeat(200001)) + file('ok.py', 'x'.repeat(200000)));
  ok(r.files.length === 1 && r.files[0].path === 'ok.py' && r.gaps.length === 1 && /over 200000/.test(r.gaps[0].missing), 'parse: file size capped at 200000 bytes', JSON.stringify(r.gaps));
}
// Fix round 2: prompt text and imports.
{
  const sp = run('SYSTEM_PROMPT');
  ok(/sys\.path\.insert/.test(sp) && /no PYTHONPATH/.test(sp), 'prompt: main.py puts project root on sys.path');
  ok(/=== FILE: main\.py ===/.test(sp) && /Do not write cards\.py/.test(sp), 'prompt: model writes only main.py');
  ok(sp.length < 2400 && !/templateCode|runtimeNames/.test(sp), 'prompt is short and has no old fields', sp.length);
  ok(/setting 'name'/.test(sp) && /default None/.test(sp) && /same name: report a gap/.test(sp) && /gaps: what the app could not wire/.test(sp), 'prompt: flag name, duplicate names and gaps');
  ok(/no outgoing link/.test(sp) && /JSON/.test(sp) && /exits 1/.test(sp) && /stderr/.test(sp), 'prompt: result and CardError rule');
  const exp = TEMPLATES['Export Table'];
  ok(exp.imports.includes('import csv') && exp.imports.includes('import io'), 'Export Table lists csv and io imports');
  ok(TEMPLATES['Shift Date By Time'].runtime.includes('iso') && TEMPLATES['Define App Settings'].runtime.includes('check_identifier'), 'helper runtime names listed');
}
// The app assembles cards.py; the model writes only main.py.
{
  const req2 = run('assembleBedrockRequest()');
  const main = '=== FILE: main.py ===\nprint(1)\n=== END FILE ===\n';
  const withCards = (p) => main + '=== FILE: ' + p + ' ===\nx = 1\n=== END FILE ===\n';
  ctx.__req = req2;
  const build = (reply) => { ctx.__reply = reply; return run('buildProjectFiles(__req, __reply)'); };
  let files = build(main);
  ok(files.length === 2 && files[0].path === 'cards.py' && files[1].path === 'main.py' && files.gaps.length === 0, 'buildProjectFiles: cards.py + main.py', JSON.stringify(files.gaps));
  ok(/def enter_text\(/.test(files[0].content) && !/def app_start|def app_end/.test(files[0].content), 'cards.py holds Enter Text, not Start/End');
  ok(files[0].content.split('def enter_text(').length === 2, 'each card source once');
  for (const p of ['cards.py', 'CARDS.PY', 'sub\\cards.py'.replace('sub\\', '')]) {
    files = build(withCards(p));
    ok(files.length === 0 && files.gaps.some((g) => /cards\.py/.test(g.missing)), 'cards.py in reply is refused: ' + p, JSON.stringify(files.gaps));
  }
  files = build('=== GAP: Enter Text | no value ===');
  ok(files.length === 0 && files.gaps.length === 1, 'model gap passes through');
  files = build('=== FILE: other.py ===\nx\n=== END FILE ===');
  ok(files.length === 0 && files.gaps.some((g) => /no main\.py/.test(g.missing)), 'reply without main.py is a gap');

  // Distinct titles once; helpers and imports gathered.
  const titles = ['Export Table', 'Import Records', 'Shift Date By Time', 'Define App Settings', 'Trim Whitespace', 'Trim Whitespace'];
  ctx.__nodes2 = titles.map((t) => ({ title: t }));
  const mod = run('assembleCardsModule(__nodes2)');
  ok(mod.split('def ' + TEMPLATES['Trim Whitespace'].function + '(').length === 2, 'repeated card: source once');
  ok(/^import csv$/m.test(mod) && /^import io$/m.test(mod) && /^from card_templates\.runtime import .*\biso\b/m.test(mod) && /^from card_templates\.runtime import .*\bcheck_identifier\b/m.test(mod), 'imports and runtime names at the top', mod.slice(0, 300));
  ok(mod.indexOf('def _same_shape') < mod.indexOf('def ' + TEMPLATES['Shift Date By Time'].function + '('), 'helpers come before the card');
  // Every card assembles together without a name clash.
  ctx.__every = CATALOG.map((c) => ({ title: c.title, role: c.role }));
  let err = '';
  try { run('assembleCardsModule(__every)'); } catch (e) { err = e.message; }
  ok(err === '', 'all cards assemble together', err);
  ok(run('assembleCardsModule([])').startsWith('# cards.py'), 'empty graph gives a header only');
  // Size: no source in the request, so it is much smaller than the sum of the card sources.
  ok(Buffer.byteLength(JSON.stringify(req2)) < 8000, 'slim request for 3 cards', Buffer.byteLength(JSON.stringify(req2)));
  ok(run('RESERVED_MAX_OUTPUT_TOKENS') === req2.body.inferenceConfig.maxTokens && run('estimateRequestTokens(__req)') > 0, 'reserve constant and token estimate');
}// The size cap.
run('MAX_REQUEST_BYTES = 100;');
// The system prompt alone (about 4 KB) is over a 100 byte cap, so a one-card graph is refused too.
let message = '';
try { run('assembleBedrockRequest()'); } catch (e) { message = e.message; }
ok(/too large/.test(message) && /100/.test(message), 'oversize request is refused with a clear error', message);

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
