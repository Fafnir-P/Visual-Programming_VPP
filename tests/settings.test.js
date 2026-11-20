// Tests for the settings logic (prototype/compile.js), the deterministic main.py compiler and the
// trimmed request.   node tests/settings.test.js     No network, no model.
const fs = require('fs');
const path = require('path');
const { load, ROOT } = require('./orderline_helper');

let pass = 0;
let fail = 0;
function ok(cond, name, extra) {
  if (cond) pass++; else { fail++; console.log('FAIL', name, extra === undefined ? '' : extra); }
}

const t = load();
const { run, ctx } = t;
const clone = (o) => JSON.parse(JSON.stringify(o));
const order = clone(JSON.parse(fs.readFileSync(path.join(ROOT, 'final_check', 'orderline', 'graph.json'), 'utf8')));
const def = (title, name) => run('CARD_TEMPLATES')[title].settings.find((s) => s.name === name);
const call = (fn, ...args) => { ctx.__a = args; return run(fn + '(...__a)'); };

// --- settingKind
ok(call('settingKind', { name: 'x', default: true }) === 'bool', 'kind: boolean default is yes/no');
ok(call('settingKind', def('Format Currency Value', 'decimals')) === 'number', 'kind: number');
ok(call('settingKind', def('Enter Text', 'name')) === 'text', 'kind: text');
ok(call('settingKind', def('Enter Text', 'required')) === 'bool', 'kind: Enter Text required is yes/no');
ok(call('settingKind', { name: 'c', default: 'a', choices: ['a', 'b'] }) === 'choice', 'kind: choices listed -> choice');
ok(call('settingKind', { name: 'r', required: true }) === 'text', 'kind: required, no default -> text');

// --- parseSettingValue
let r = call('parseSettingValue', def('Format Currency Value', 'decimals'), '3');
ok(r.ok && r.value === 3, 'number: 3');
r = call('parseSettingValue', def('Format Currency Value', 'decimals'), '2.5');
ok(r.ok && r.value === 2.5, 'number: decimals allowed');
for (const bad of ['abc', '', '  ', 'Infinity', '1e999', 'NaN']) {
  r = call('parseSettingValue', def('Format Currency Value', 'decimals'), bad);
  ok(!r.ok && typeof r.error === 'string' && r.error.length > 0, 'number: bad value refused: ' + JSON.stringify(bad), JSON.stringify(r));
}
r = call('parseSettingValue', def('Enter Text', 'name'), ' customer ');
ok(r.ok && r.value === ' customer ', 'text kept as typed');
r = call('parseSettingValue', def('Enter Text', 'name'), '');
ok(r.ok && r.value === '', 'text: empty is empty text');
ok(call('parseSettingValue', def('Enter Text', 'required'), true).value === true && call('parseSettingValue', def('Enter Text', 'required'), false).value === false, 'bool: checkbox state');
r = call('parseSettingValue', def('Build Summary Record', 'labels'), 'customer, total');
ok(r.ok && JSON.stringify(r.value) === '["customer","total"]', 'list setting: comma text', JSON.stringify(r));
r = call('parseSettingValue', def('Build Summary Record', 'labels'), '["a","b"]');
ok(r.ok && r.value.length === 2, 'list setting: JSON text');
r = call('parseSettingValue', def('Build Summary Record', 'labels'), '["a"');
ok(!r.ok && /JSON/.test(r.error), 'list setting: broken JSON refused');
r = call('parseSettingValue', def('Build Summary Record', 'labels'), '');
ok(r.ok && r.value === null, 'optional setting: empty means not set');
r = call('parseSettingValue', { name: 'c', default: 'a', choices: ['a', 'b'] }, 'z');
ok(!r.ok, 'choice: unknown value refused');
ok(call('settingDisplay', {}, ['a', 'b']) === '["a","b"]' && call('settingDisplay', {}, null) === '' && call('settingDisplay', {}, 3) === '3', 'settingDisplay');

// --- nodeSettings
{
  const tpl = run('CARD_TEMPLATES')['Enter Text'];
  let s = call('nodeSettings', { title: 'Enter Text' }, tpl);
  ok(s.name === 'text' && s.required === false, 'nodeSettings: defaults');
  s = call('nodeSettings', { title: 'Enter Text', config: { name: 'customer' } }, tpl);
  ok(s.name === 'customer' && s.label === 'Text', 'nodeSettings: config overrides one setting');
  const req = Object.values(run('CARD_TEMPLATES')).find((x) => x.settings.some((q) => q.required));
  if (req) {
    const rn = req.settings.find((q) => q.required).name;
    ok(!(rn in call('nodeSettings', { title: 'x' }, req)) && call('nodeSettings', { title: 'x', config: { [rn]: 'v' } }, req)[rn] === 'v', 'nodeSettings: required setting only when set');
  }
}

// --- python text
ok(call('pyStr', "it's \\ \n") === "'it\\'s \\\\ \\n'" && call('pyStr', 'é') === "'\\u00e9'" && call('pyStr', '\u{1F600}') === "'\\U0001f600'", 'pyStr escapes');
ok(call('pyLiteral', { a: [1, null, true, 'x'] }) === "{'a': [1, None, True, 'x']}", 'pyLiteral');

// --- compile: the order-line graph
t.setGraph(order);
const full = run('serializeGraph()');
let c = call('compileMainPy', full);
ok(c.ok === true && c.gaps.length === 0, 'compile: order line is ok', JSON.stringify(c.gaps));
ok(/--customer/.test(c.mainPy) && /--qty/.test(c.mainPy) && /--price/.test(c.mainPy) && !/--number|--text/.test(c.mainPy), 'compile: flags from the name settings');
ok(/case='title'/.test(c.mainPy) && /operation='multiply'/.test(c.mainPy), 'compile: settings become keyword arguments');
ok(/result = n_n10\['record'\]/.test(c.mainPy), 'compile: Build Summary record is the printed result');
ok(/sys\.path\.insert\(0, d\)/.test(c.mainPy) && /sys\.exit\(1\)/.test(c.mainPy) && /file=sys\.stderr/.test(c.mainPy), 'compile: sys.path block and error exit');
ok(call('compileMainPy', full).mainPy === c.mainPy, 'compile: same graph, same text');
ok(/'--customer'.*required=True/.test(c.mainPy) && /'--qty'.*type=num_flag\('qty'\), required=True/.test(c.mainPy) && /'--price'.*required=True/.test(c.mainPy), 'compile: flags feeding required inputs are required, number flags are checked');
ok(/ap\.error = die/.test(c.mainPy) && /import[^\n]*, to_number/.test(c.mainPy), 'compile: argparse errors exit 1 with one line');
{
  const fs = require('fs');
  const g20 = JSON.parse(fs.readFileSync(require('path').join(__dirname, '..', 'final_check', 'card_way2', 'graph20.json'), 'utf8'));
  t.setGraph(g20);
  const c20 = call('compileMainPy', run('serializeGraph()'));
  ok(c20.ok === true, 'compile: graph20 still compiles', JSON.stringify(c20.gaps));
  t.setGraph(order);
}
{
  const calls = c.mainPy.split('\n').filter((l) => /^\s+n_n\d+ = /.test(l)).map((l) => l.trim().split(' ')[0]);
  ok(calls.join() === 'n_n2,n_n3,n_n4,n_n5,n_n6,n_n7,n_n8,n_n9,n_n10', 'compile: calls in run order', calls.join());
}
{
  const files = run('buildDeterministicFiles()');
  ok(files.ok && files.files.map((f) => f.path).join() === 'cards.py,main.py', 'buildDeterministicFiles: cards.py + main.py');
  ok(/def build_summary_record\(/.test(files.files[0].content), 'cards.py holds the cards used');
}

// --- compile: duplicate flag names
{
  const g = clone(order);
  g.nodes.find((n) => n.id === 'n7').config.name = 'qty';
  t.setGraph(g);
  c = call('compileMainPy', run('serializeGraph()'));
  ok(!c.ok && c.mainPy === '' && c.gaps.length === 1 && /qty/.test(c.gaps[0].missing) && /n6/.test(c.gaps[0].missing) && /n7/.test(c.gaps[0].card), 'compile: duplicate names -> a gap naming both cards', JSON.stringify(c.gaps));
  g.nodes.find((n) => n.id === 'n7').config.name = 'two words';
  t.setGraph(g);
  c = call('compileMainPy', run('serializeGraph()'));
  ok(!c.ok && /command line flag/.test(c.gaps[0].missing), 'compile: a name that is not a flag is a gap');
}

// --- compile: unsupported graphs
function gapsFor(mutate) {
  const g = clone(order);
  mutate(g);
  t.setGraph(g);
  return call('compileMainPy', run('serializeGraph()'));
}
{
  c = gapsFor((g) => g.edges.pop());   // no link into App End: still fine (End only orders)
  ok(c.ok, 'compile: missing link into App End is not a compile gap');
  c = gapsFor((g) => { g.edges = g.edges.filter((e) => !(e[2] === 'n8' && e[3] === 'first')); });
  ok(!c.ok && c.gaps.some((x) => /first/.test(x.missing)), 'compile: required input without a link is a gap', JSON.stringify(c.gaps));
  c = gapsFor((g) => { g.nodes.find((n) => n.id === 'n9').config = {}; g.edges.push(['n6', 'value', 'n9', 'value']); });
  ok(!c.ok && c.gaps.some((x) => /2 links/.test(x.missing)), 'compile: two links into one input is a gap', JSON.stringify(c.gaps));
  c = gapsFor((g) => { g.order = ['n1', 'n3', 'n2', 'n4', 'n5', 'n6', 'n7', 'n8', 'n9', 'n10', 'n11']; });
  ok(!c.ok && c.gaps.some((x) => /before/.test(x.missing)), 'compile: link from a later card is a gap');
  c = gapsFor((g) => { g.nodes.push({ id: 'n12', title: 'Run On A Timer' }); g.order.push('n12'); });
  ok(!c.ok && c.gaps.some((x) => /n12/.test(x.card)), 'compile: trigger/flow card is a gap', JSON.stringify(c.gaps));
  const store = Object.keys(run('CARD_TEMPLATES')).find((k) => /ctx\.(?!now)/.test(run('CARD_TEMPLATES')[k].source) && !/^(App|Run)/.test(k) && !/Enter|Pick|Choose/.test(k));
  c = gapsFor((g) => { g.nodes.push({ id: 'n12', title: store }); g.order.push('n12'); });
  ok(!c.ok && c.gaps.some((x) => /n12/.test(x.card)), 'compile: card that uses the store is a gap (' + store + ')', JSON.stringify(c.gaps));
  c = gapsFor((g) => { g.nodes = g.nodes.filter((n) => ['n1', 'n11'].includes(n.id)); g.edges = []; g.order = ['n1', 'n11']; });
  ok(!c.ok && c.gaps.length === 1, 'compile: no cards to run is a gap');
}
// two terminal cards -> object keyed by title
{
  const g = { order: ['n1', 'n2', 'n3'], nodes: [{ id: 'n1', title: 'App Start' }, { id: 'n2', title: 'Enter Text', config: { name: 'a' } }, { id: 'n3', title: 'Enter Number', config: { name: 'b' } }], edges: [] };
  t.setGraph(g);
  c = call('compileMainPy', run('serializeGraph()'));
  ok(c.ok && /\{'Enter Text': \{'value': n_n2\['value'\]\}, 'Enter Number': \{'value': n_n3\['value'\]\}\}/.test(c.mainPy), 'compile: several result cards -> object keyed by title', c.mainPy.split('\n').filter((l) => /result =/.test(l)).join());
}

// --- trimmed request
{
  t.setGraph(order);
  run('MAX_REQUEST_BYTES = 300000;');
  const req = run('assembleBedrockRequest()');
  const text = req.body.messages[0].content[0].text;
  const g = JSON.parse(text);
  ok(g.gaps === undefined, 'request: no gaps key when there are none');
  ok(!/category|catalogID|"inputs"|"outputs"|"class"/.test(text), 'request: no category, catalogID or per-node ports');
  const n4 = g.nodes.find((n) => n.id === 'n4');
  ok(JSON.stringify(n4.set) === '{"case":"title"}', 'request: only the changed setting is sent', JSON.stringify(n4));
  ok(g.nodes.find((n) => n.id === 'n3').set === undefined, 'request: a card with default settings has no settings');
  ok(g.edges[1] === 'n2.value>n3.text' && Array.isArray(g.edges), 'request: links are short text');
  const withGaps = run('assembleBedrockRequest([{ card: "Enter Number (n6)", missing: "x", nodeIDs: ["n6"] }])');
  const g2 = JSON.parse(withGaps.body.messages[0].content[0].text);
  ok(g2.gaps.length === 1 && g2.gaps[0].card === 'Enter Number (n6)' && g2.gaps[0].nodeIDs === undefined, 'request: gaps are passed on (card, missing)');
  ok(text.length < 2500, 'request: graph text for 11 cards is small', text.length);
  ok(run('estimateRequestTokens')(req) < 1300, 'request: input estimate for the order line', run('estimateRequestTokens')(req));
  // buildProjectFiles still adds cards.py for every card from the slim request.
  ctx.__req = req;
  const files = run('buildProjectFiles(__req, "=== FILE: main.py ===\\nprint(1)\\n=== END FILE ===")');
  ok(files.length === 2 && /def calculate_from_two_values\(/.test(files[0].content), 'buildProjectFiles: cards.py from the slim request');
}

// --- meter note
{
  run('resetMeter()');
  run("recordUsage({ input: 0, output: 0, estimated: true, note: 'assembled by the app' })");
  const s = run('summary()');
  ok(s.outputTokens === 0 && s.inputTokens === 0 && s.accounting === 'estimate' && s.note === 'assembled by the app', 'meter: 0 tokens, estimate, note', JSON.stringify(s));
  run('resetMeter()');
  run('recordUsage({ input: 10, output: 5, estimated: true })');
  ok(run('summary()').note === null, 'meter: no note without a note');
}

// --- the settings panel (DOM part) uses no innerHTML
{
  const app = fs.readFileSync(path.join(ROOT, 'prototype', 'app.js'), 'utf8');
  const m = app.match(/function renderSettingsPanel\(\) \{[\s\S]*?\n\}\n/);
  ok(!!m && !/innerHTML|outerHTML|insertAdjacentHTML/.test(m[0]), 'panel: built with textContent/value only');
  ok(!!m && !/\brender\(\)|state\.edges/.test(m[0].replace('function renderSettingsPanel()', '')), 'panel: typing does not re-render or touch links');
  ok(!!m && /htmlFor/.test(m[0]) && /aria-describedby/.test(m[0]), 'panel: labels and described-by notes');
  const html = fs.readFileSync(path.join(ROOT, 'prototype', 'index.html'), 'utf8');
  ok(/id="settingsPanel"/.test(html) && html.indexOf('compile.js') > html.indexOf('templates.js') && html.indexOf('compile.js') < html.indexOf('bedrock.js'), 'index.html: panel and compile.js load order');
}

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);