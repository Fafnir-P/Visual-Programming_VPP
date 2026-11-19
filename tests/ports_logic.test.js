// Tests for prototype/ports.js and the port data in prototype/catalog.js.
// Plain Node, no packages:   node tests/ports_logic.test.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..', 'prototype');
const ctx = vm.createContext({ console });
for (const f of ['catalog.js', 'ports.js']) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), 'utf8'), ctx, { filename: f });
}
const get = (expr) => vm.runInContext(expr, ctx);
const PORT_CLASSES = get('PORT_CLASSES');
const PORT_COMPAT = get('PORT_COMPAT');
const CATALOG = get('CATALOG');
const ORDER = get('PORT_CLASS_ORDER');

let pass = 0;
let fail = 0;
function ok(cond, name, extra) {
  if (cond) { pass++; } else { fail++; console.log('FAIL', name, extra === undefined ? '' : extra); }
}

// ---- classes ---------------------------------------------------------------
ok(ORDER.length === 10 && ORDER.every((c) => PORT_CLASSES[c]), 'ten classes in order');
ok(new Set(ORDER.map((c) => PORT_CLASSES[c].color)).size === ORDER.length, 'every class has its own colour');
ok(ORDER.every((c) => /^#[0-9a-f]{6}$/i.test(PORT_CLASSES[c].color)), 'colours are hex');
for (const o of ORDER) {
  for (const i of ORDER) {
    const expected = o === i || o === 'any' || i === 'any';
    ok(get(`classesCompatible(${JSON.stringify(o)}, ${JSON.stringify(i)})`) === expected, `compat ${o} -> ${i}`);
  }
}
ok(get('classesCompatible("text", "nope")') === false && get('classesCompatible("nope", "text")') === false, 'unknown class never links');

// ---- the catalog's ports -----------------------------------------------------
ok(CATALOG.length === 209, '209 cards in the catalog', CATALOG.length);
ok(new Set(CATALOG.map((c) => c.id)).size === CATALOG.length, 'catalog ids unique');
ok(new Set(CATALOG.map((c) => c.title)).size === CATALOG.length, 'card titles unique');
const catIds = new Set(get('CATEGORIES').map((c) => c.id));
ok(CATALOG.every((c) => catIds.has(c.category)), 'every card has a known category');
ok(get('CATEGORIES').every((c) => c.count === CATALOG.filter((x) => x.category === c.id).length), 'category counts match');
for (const card of CATALOG) {
  for (const side of ['inputs', 'outputs']) {
    const ports = card.ports[side];
    ok(new Set(ports.map((p) => p.id)).size === ports.length, `${card.title}: port ids unique (${side})`);
    ok(ports.every((p) => PORT_CLASSES[p.cls]), `${card.title}: ${side} have known classes`);
  }
  const implicitIn = card.ports.inputs.filter((p) => p.implicit);
  const implicitOut = card.ports.outputs.filter((p) => p.implicit);
  if (['trigger', 'start', 'end'].includes(card.role)) {
    ok(implicitIn.length === 0 && implicitOut.length === 0, `${card.title}: a ${card.role} card has no Start/Done ports`);
    const controlPorts = card.role === 'end' ? card.ports.inputs : card.ports.outputs;
    ok(controlPorts.some((p) => p.cls === 'control'), `${card.title}: a ${card.role} card has a control port`);
  } else {
    ok(implicitIn.length === 1 && implicitOut.length === 1 && implicitIn[0].id === '_start' && implicitOut[0].id === '_done',
      `${card.title}: Start and Done ports`);
  }
}

// ---- checkConnection -----------------------------------------------------------
let nextNode = 1;
function nodeFor(title) {
  const card = CATALOG.find((c) => c.title === title);
  if (!card) throw new Error('no card ' + title);
  return {
    id: 'n' + nextNode++, catalogID: card.id, title: card.title, type: card.category, role: card.role,
    ports: { inputs: card.ports.inputs.map((p) => ({ ...p })), outputs: card.ports.outputs.map((p) => ({ ...p })) }
  };
}
function graph(...titles) {
  const nodes = new Map();
  const list = titles.map((t) => { const n = nodeFor(t); nodes.set(n.id, n); return n; });
  return { nodes, edges: new Map(), list };
}
const check = (g, a, aPort, b, bPort) => vm.runInContext('checkConnection', ctx)(g.nodes, g.edges,
  { nodeID: a.id, portID: aPort }, { nodeID: b.id, portID: bPort });
let edgeNo = 1;
function link(g, a, aPort, b, bPort) {
  const r = check(g, a, aPort, b, bPort);
  if (r.ok) g.edges.set('e' + edgeNo, { id: 'e' + edgeNo++, fromNodeID: a.id, fromPort: aPort, toNodeID: b.id, toPort: bPort });
  return r;
}

{
  const g = graph('Enter Number', 'Round Numeric Value', 'Show Records Table');
  const [num, round, table] = g.list;
  let r = check(g, num, 'value', round, 'value');
  ok(r.ok === true && r.loose === false, 'number -> number is allowed');
  r = check(g, table, 'view', round, 'value');
  ok(!r.ok && r.code === 'type_mismatch', 'view -> number is refused', JSON.stringify(r));
  ok(r.message.includes('Show Records Table') && r.message.includes('Round Numeric Value') && r.message.includes('View') && r.message.includes('Number'),
    'the refusal names both cards and both classes', r.message);
  ok(r.details.from.cls === 'view' && r.details.to.cls === 'number' && r.details.from.nodeID === table.id, 'refusal details carry the ends');
  r = check(g, num, 'view', round, 'value');
  ok(!r.ok && r.code === 'type_mismatch', 'view output of Enter Number -> number input refused');
  r = check(g, num, 'value', num, 'value');
  ok(!r.ok && r.code === 'same_card', 'a card cannot link to itself');
  r = check(g, num, 'nope', round, 'value');
  ok(!r.ok && r.code === 'no_such_port', 'unknown port');
  r = check(g, { id: 'ghost' }, 'value', round, 'value');
  ok(!r.ok && r.code === 'no_such_port', 'unknown card');
  r = check(g, num, 'value', round, 'places');
  ok(!r.ok && r.code === 'no_such_port', 'a setting is not a port');
  // direction: an input used as the output end, and an output used as the input end
  // Round Numeric Value has an input and an output both called "value": the side decides which one is meant
  r = check(g, round, 'value', num, 'value');
  ok(r.ok === true && r.details.from.portName === 'value' && r.details.to.portName === 'value', 'the same name on both sides is resolved by side');
  r = check(g, table, 'records', round, 'value');
  ok(!r.ok && r.code === 'direction' && /input/.test(r.message), 'an input on the output end: direction', JSON.stringify(r));
  r = check(g, num, 'value', table, 'view');
  ok(!r.ok && r.code === 'direction' && /output/.test(r.message), 'an output on the input end: direction', JSON.stringify(r));
  // Both Enter Number and Round Numeric Value have an input and an output named "value": `side` tells them apart
  const sided = (a, aSide, b, bSide) => vm.runInContext('checkConnection', ctx)(g.nodes, g.edges,
    { nodeID: a.id, portID: 'value', side: aSide }, { nodeID: b.id, portID: 'value', side: bSide });
  r = sided(num, 'output', round, 'output');
  ok(!r.ok && r.code === 'direction' && /output/.test(r.message), 'output to output with the same port name is a direction error', JSON.stringify(r));
  r = sided(num, 'input', round, 'input');
  ok(!r.ok && r.code === 'direction' && /input/.test(r.message), 'input to input with the same port name is a direction error', JSON.stringify(r));
  r = sided(num, 'input', round, 'output');
  ok(!r.ok && r.code === 'direction' && r.message.includes('is an input') && r.message.includes('is an output'), 'both ends the wrong way round', JSON.stringify(r));
  r = sided(num, 'output', round, 'input');
  ok(r.ok === true, 'explicit sides, the right way round');
  r = vm.runInContext('checkConnection', ctx)(g.nodes, g.edges, { nodeID: num.id, portID: 'view', side: 'input' }, { nodeID: round.id, portID: 'value', side: 'input' });
  ok(!r.ok && r.code === 'no_such_port', 'a port that is not on that side does not exist');
}

{
  const g = graph('Enter Number', 'Round Numeric Value', 'Enter Currency Amount');
  const [num, round, cur] = g.list;
  ok(link(g, num, 'value', round, 'value').ok, 'first link works');
  let r = check(g, num, 'value', round, 'value');
  ok(!r.ok && r.code === 'duplicate', 'the same link twice is refused');
  r = check(g, cur, 'value', round, 'value');
  ok(!r.ok && r.code === 'input_taken' && r.message.includes('Enter Number') && r.details.existingEdgeID === 'e' + (edgeNo - 1), 'a second source for one input is refused', JSON.stringify(r));
  // outputs fan out
  const g2 = graph('Enter Number', 'Round Numeric Value', 'Calculate Percentage Of Total');
  ok(link(g2, g2.list[0], 'value', g2.list[1], 'value').ok && link(g2, g2.list[0], 'value', g2.list[2], 'value').ok, 'one output may feed several inputs');
}

{
  // the first example in Cards.md ("Connection rules")
  const g = graph('Enter Text', 'Trim Whitespace');
  ok(check(g, g.list[0], 'value', g.list[1], 'text').ok === true, 'Cards.md example: Enter Text.value -> Trim Whitespace.text is allowed');
}

{
  const g = graph('Enter Text', 'Show Status Badge', 'Show Message Banner', 'Arrange In Grid');
  const [t1, badge, banner, grid] = g.list;
  ok(link(g, badge, 'view', grid, 'children').ok, 'a view into a children input');
  ok(link(g, banner, 'view', grid, 'children').ok, 'a second view into the same children input (several links allowed)');
  ok(link(g, t1, 'view', grid, 'children').ok, 'a third');
  ok(g.edges.size === 3, 'three links on one multi input');
}

{
  const g = graph('Filter Records By Condition', 'Sort Records By Field');
  const [filter, sort] = g.list;
  ok(link(g, filter, 'records', sort, 'records').ok, 'records -> records');
  let r = check(g, sort, 'records', filter, 'records');
  ok(!r.ok && r.code === 'cycle' && /loop/.test(r.message), 'a data loop is refused', JSON.stringify(r));
  const g2 = graph('Create New Record', 'Show Detail View', 'Read Record By ID');
  ok(link(g2, g2.list[0], '_done', g2.list[1], '_start').ok, 'Done -> Start');
  ok(link(g2, g2.list[1], '_done', g2.list[2], '_start').ok, 'Done -> Start, next card');
  r = check(g2, g2.list[2], '_done', g2.list[0], '_start');
  ok(!r.ok && r.code === 'cycle', 'a control loop through three cards is refused');
  r = check(g2, g2.list[0], 'record', g2.list[1], '_start');
  ok(!r.ok && r.code === 'type_mismatch', 'a record cannot feed a Start port');
}

{
  const g = graph('Handle Error Without Stopping', 'Round Numeric Value', 'Enter Text');
  const [handle, round, text] = g.list;
  let r = check(g, handle, 'value', round, 'value');
  ok(r.ok && r.loose === true, 'Any -> Number is allowed and marked loose');
  r = check(g, text, 'value', handle, 'value');
  ok(r.ok && r.loose === true, 'Text -> Any is allowed and marked loose');
  r = check(g, handle, 'error', round, 'value');
  ok(!r.ok && r.code === 'type_mismatch', 'a Record error output does not feed a Number input');
}

{
  // triggers
  const g = graph('Run When Button Pressed', 'Run Steps In Sequence', 'Create New Record', 'Click Button');
  const [trig, seq, create, click] = g.list;
  ok(link(g, trig, 'event', seq, 'steps').ok, 'trigger event -> steps of a flow card');
  ok(link(g, trig, 'event', create, '_start').ok, 'trigger event -> a card\'s Start');
  ok(link(g, create, '_done', seq, 'steps').ok, 'Done -> steps (several allowed)');
  ok(check(g, trig, 'fire', create, '_start').code === 'type_mismatch', 'the fire flag is not a control signal');
  ok(check(g, click, 'view', trig, 'pressed').code === 'type_mismatch', 'a view does not feed a trigger flag');
}

// Every output port against every input port of other cards, in an empty graph:
// allowed exactly when the classes are compatible
{
  const outs = [];
  const ins = [];
  CATALOG.forEach((card, idx) => {
    card.ports.outputs.forEach((p) => outs.push({ idx, card, p }));
    card.ports.inputs.forEach((p) => ins.push({ idx, card, p }));
  });
  const checkFn = vm.runInContext('checkConnection', ctx);
  let wrong = 0;
  let total = 0;
  for (const o of outs) {
    const a = { id: 'a', title: o.card.title, ports: o.card.ports };
    for (const i of ins) {
      if (i.idx === o.idx) continue;
      const b = { id: 'b', title: i.card.title, ports: i.card.ports };
      const nodes = new Map([['a', a], ['b', b]]);
      const r = checkFn(nodes, new Map(), { nodeID: 'a', portID: o.p.id }, { nodeID: 'b', portID: i.p.id });
      const expected = o.p.cls === i.p.cls || o.p.cls === 'any' || i.p.cls === 'any';
      total++;
      if (r.ok !== expected || (!r.ok && r.code !== 'type_mismatch')) wrong++;
    }
  }
  ok(wrong === 0, `all ${total} output/input pairs follow the colour rule`, wrong);
}

// ---- open inputs ------------------------------------------------------------------
{
  const g = graph('Round Numeric Value', 'Enter Number', 'Show Records Table');
  const open = vm.runInContext('findOpenInputs', ctx)(g.nodes, g.edges);
  ok(open.length === 1 && open[0].card === 'Round Numeric Value' && open[0].portName === 'value', 'Round Numeric Value has one open input', JSON.stringify(open));
  link(g, g.list[1], 'value', g.list[0], 'value');
  ok(vm.runInContext('findOpenInputs', ctx)(g.nodes, g.edges).length === 0, 'the open input closes when linked');
}

// ---- re-check of saved links ---------------------------------------------------------
{
  const g = graph('Enter Number', 'Round Numeric Value', 'Show Records Table');
  g.edges.set('x1', { id: 'x1', fromNodeID: g.list[0].id, fromPort: 'value', toNodeID: g.list[1].id, toPort: 'value' });
  g.edges.set('x2', { id: 'x2', fromNodeID: g.list[2].id, fromPort: 'view', toNodeID: g.list[1].id, toPort: 'value' });
  const problems = vm.runInContext('recheckAllLinks', ctx)(g.nodes, g.edges);
  ok(problems.length === 1 && problems[0].edgeID === 'x2', 'recheck finds the one bad saved link', JSON.stringify(problems.map((p) => p.code)));
}

// ---- the cards added with the bridge ports --------------------------------------------------------
{
  const pairs = [
    ['Compare Two Numbers', 'result', 'Branch On Yes/No', 'condition', true, false],
    ['Calculate Stock Level', 'stock', 'Compare Two Numbers', 'first', true, false],
    ['Branch On Yes/No', 'yes', 'Show Message Banner', 'message', true, true],
    ['Flag Reorder Level Reached', 'flag', 'Branch On Yes/No', 'condition', true, false],
    ['Choose File', 'filename', 'Read Chosen File', 'filename', true, false],
    ['Read Chosen File', 'content', 'Import Records', 'content', true, false],
    ['Calculate Stock Level', 'stock', 'Set Field Of Record', 'value', true, true],
    ['Set Field Of Record', 'record', 'Update Existing Record', 'changes', true, false],
    ['Pick Field From Records', 'values', 'Update Field Across Records', 'ids', true, false],
    ['Pick Field From Records', 'values', 'Show Records Table', 'records', false, false],
    ['Get Current Date And Time', 'date', 'Filter Records By Date', 'compare_date', true, false],
    ['Query Saved Records By Criteria', 'records', 'Filter Records By Date', 'records', true, false],
    ['Filter Records By Date', 'records', 'Exception List', 'records', true, false],
    ['Calculate Sum Of Field', 'sum', 'Build Summary Record', 'value_1', true, true],
    ['Build Summary Record', 'rows', 'Summary Table', 'data', true, false],
    ['Build Summary Record', 'record', 'Summary Table', 'data', false, false],
    ['App Start', 'event', 'App End', 'finish', true, false],
    ['App Start', 'event', 'Create New Record', '_start', true, false],
    ['App Start', 'started_at', 'Shift Date By Time', 'date', true, false],
    ['Create New Record', '_done', 'App End', 'finish', true, false],
    ['Run When Button Pressed', 'fire', 'App End', 'finish', false, false],
    ['App Start', 'event', 'Run Steps In Sequence', 'steps', true, false]
  ];
  for (const [a, ap, b, bp, allowed, loose] of pairs) {
    const g = graph(a, b);
    const r = check(g, g.list[0], ap, g.list[1], bp);
    ok(r.ok === allowed && (!allowed || r.loose === loose), `${a}.${ap} -> ${b}.${bp}: ${allowed ? 'allowed' : 'refused'}`, JSON.stringify(r));
  }
  // a branch feeds two different cards; End takes several links
  const g = graph('App End', 'Create New Record', 'Delete Record', 'Branch On Yes/No');
  ok(link(g, g.list[1], '_done', g.list[0], 'finish').ok && link(g, g.list[2], '_done', g.list[0], 'finish').ok, 'App End takes several links');
  // nothing can end at App Start and App End has nothing to start from
  const s = graph('App Start', 'Create New Record');
  ok(!check(s, s.list[1], '_done', s.list[0], '_start').ok, 'nothing can be linked to App Start');
  ok(!check(s, s.list[0], '_done', s.list[1], '_start').ok, 'App Start has no Done port');
}

// ---- what is missing before generating ---------------------------------------------------------------
{
  const issues = (g, order) => vm.runInContext('findGenerationIssues', ctx)(g.nodes, g.edges, order);
  const kinds = (list) => list.map((i) => i.kind).sort().join();
  let g = graph();
  ok(kinds(issues(g)) === 'no_end,no_start', 'an empty canvas: no Start, no End');
  g = graph('App Start', 'Round Numeric Value', 'App End');
  const [start, round, end] = g.list;
  let list = issues(g, [start.id, round.id, end.id]);
  ok(kinds(list) === 'open_input,open_input,start_unlinked', 'Start unlinked, two open inputs', kinds(list));
  const roundIssue = list.find((i) => i.kind === 'open_input' && i.nodeID === round.id);
  ok(roundIssue.where === 'Round Numeric Value (card 2 in the run order)', 'where: the card and its place in the run order', roundIssue.where);
  ok(roundIssue.portID === 'value' && roundIssue.message.includes('\u201cvalue\u201d') && roundIssue.message.includes('Number'), 'what: the port and its class', roundIssue.message);
  ok(issues(g).find((i) => i.nodeID === round.id).where === 'Round Numeric Value', 'without a run order only the name is given');
  ok(list.find((i) => i.kind === 'start_unlinked').where === 'App Start (card 1 in the run order)', 'the Start card is named with its place');
  link(g, start, 'event', end, 'finish');
  list = issues(g, [start.id, round.id, end.id]);
  ok(kinds(list) === 'open_input', 'linked: only the open input of Round Numeric Value is left', kinds(list));
  const num = nodeFor('Enter Number');
  g.nodes.set(num.id, num);
  link(g, num, 'value', round, 'value');
  ok(issues(g).length === 0, 'nothing is missing in a complete graph');
  const two = graph('App Start', 'App End', 'App End');
  ok(kinds(issues(two)) === 'open_input,open_input,start_unlinked', 'two End cards, both unlinked');
}

// portCanLink (highlighting while dragging)
{
  const f = vm.runInContext('portCanLink', ctx);
  ok(f('output', 'text', 'input', 'text') && !f('output', 'text', 'input', 'number') && f('output', 'any', 'input', 'number'), 'portCanLink from an output');
  ok(f('input', 'number', 'output', 'number') && !f('input', 'number', 'output', 'text') && f('input', 'number', 'output', 'any'), 'portCanLink from an input');
  ok(!f('output', 'text', 'output', 'text') && !f('input', 'text', 'input', 'text'), 'same side never links');
}

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
