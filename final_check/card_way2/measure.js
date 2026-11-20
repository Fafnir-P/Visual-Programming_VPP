// MEASURER C harness. node measure.js  -> writes result.json next to this file. Edits no project file.
const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const { load, ROOT } = require(path.join('..', '..', 'tests', 'orderline_helper'));

const HERE = __dirname;
const ms = (t0) => Number(process.hrtime.bigint() - t0) / 1e6;
const stats = (a) => { const s = a.slice().sort((x, y) => x - y); return { min: s[0], median: s[Math.floor(s.length / 2)], max: s[s.length - 1], all: a }; };
const PY = process.env.PYBIN || 'python';

function loadGraph(file) {
  const t = load();
  t.setGraph(JSON.parse(fs.readFileSync(file, 'utf8')));
  return t;
}

function copyTemplates(dst) {
  fs.cpSync(path.join(ROOT, 'card_templates'), path.join(dst, 'card_templates'), {
    recursive: true, filter: (s) => !s.includes('__pycache__'),
  });
}

function py(dir, args) {
  const t0 = process.hrtime.bigint();
  const r = cp.spawnSync(PY, [path.join(dir, 'main.py'), ...args], { encoding: 'utf8' });
  return { code: r.status, stdout: r.stdout, stderr: r.stderr, ms: ms(t0) };
}

const out = {};

// ---- 1. five timed runs on the order-line graph
const OL = path.join(ROOT, 'final_check', 'orderline', 'graph.json');
const runs = [];
for (let i = 1; i <= 5; i++) {
  const t = loadGraph(OL);
  const tSer = process.hrtime.bigint();
  const full = t.run('serializeGraph()');
  const serMs = ms(tSer);
  t.ctx.__full = full;
  const tC = process.hrtime.bigint();
  const compiled = t.run('compileMainPy(__full)');
  const compMs = ms(tC);
  const tB = process.hrtime.bigint();
  const built = t.run('buildDeterministicFiles()');
  const buildMs = ms(tB);
  const dir = fs.mkdtempSync(path.join(HERE, 'run' + i + '_'));
  const tW = process.hrtime.bigint();
  for (const f of built.files) fs.writeFileSync(path.join(dir, f.path), f.content);
  const writeMs = ms(tW);
  const tCp = process.hrtime.bigint();
  copyTemplates(dir);
  const copyMs = ms(tCp);
  const c1 = py(dir, ['--customer', '  ada lovelace ', '--qty', '3', '--price', '2.5']);
  runs.push({ run: i, dir: path.basename(dir), serializeGraph: serMs, compileMainPy: compMs, buildDeterministicFiles: buildMs,
    writeProject: writeMs, copyCardTemplates_not_part_of_app: copyMs, pythonC1: c1.ms, c1code: c1.code, c1stdout: c1.stdout.trim(), compiledOk: compiled.ok });
}
out.timing = {};
for (const k of ['serializeGraph', 'compileMainPy', 'buildDeterministicFiles', 'writeProject', 'copyCardTemplates_not_part_of_app', 'pythonC1']) out.timing[k] = stats(runs.map((r) => r[k]));
out.runs = runs;

// ---- 2. checks C1-C4 on the last written project
const dir = path.join(HERE, runs[4].dir);
const checks = {};
const c1 = py(dir, ['--customer', '  ada lovelace ', '--qty', '3', '--price', '2.5']);
checks.C1 = { pass: c1.code === 0 && c1.stdout.trim() === '{"customer": "Ada Lovelace", "total": "$7.50"}' && c1.stderr === '', code: c1.code, stdout: c1.stdout.trim(), stderr: c1.stderr.trim() };
const c2 = py(dir, ['--customer', '   ', '--qty', '1', '--price', '1']);
checks.C2 = { pass: c2.code === 1 && c2.stdout === '' && c2.stderr.trim().split(/\r?\n/).length === 1 && !c2.stderr.includes('Traceback'), code: c2.code, stdout: c2.stdout, stderr: c2.stderr.trim() };
const a = py(dir, ['--customer', 'bob', '--qty', '2', '--price', '1.25']);
const b = py(dir, ['--customer', 'bob', '--qty', '2', '--price', '1.25']);
checks.C3 = { pass: a.code === 0 && a.stdout === b.stdout && a.stdout.length > 0, stdout_a: a.stdout.trim(), stdout_b: b.stdout.trim() };
const c4 = py(dir, ['--customer', 'x', '--qty', 'abc', '--price', '1']);
checks.C4 = { pass: c4.code === 1 && c4.stdout === '' && c4.stderr.trim().split(/\r?\n/).length === 1 && !c4.stderr.includes('Traceback'), code: c4.code, stdout: c4.stdout, stderr: c4.stderr.trim() };
out.checks = checks;
out.fileSizes = {
  'cards.py': { bytes: fs.statSync(path.join(dir, 'cards.py')).size, lines: fs.readFileSync(path.join(dir, 'cards.py'), 'utf8').split('\n').length },
  'main.py': { bytes: fs.statSync(path.join(dir, 'main.py')).size, lines: fs.readFileSync(path.join(dir, 'main.py'), 'utf8').split('\n').length },
};

// ---- 3. meter summary the way runGeneration does it
{
  const t = loadGraph(OL);
  const built = t.run('buildDeterministicFiles()');
  t.run('resetMeter()');
  t.run("recordUsage({ input: 0, output: 0, estimated: true, note: 'assembled by the app' })");
  out.meterSummary = t.run('summary()');
  out.meterBuiltOk = built.ok;
}

// ---- 4. model path size: blank the name of Enter Text n2 -> duplicate flag gap (qty/price keep their names)
{
  const g = JSON.parse(fs.readFileSync(OL, 'utf8'));
  g.nodes.find((n) => n.id === 'n7').config = { label: 'Price' };   // name back to default 'number' -> duplicates n6? n6 is 'qty'
  g.nodes.find((n) => n.id === 'n6').config = { label: 'Qty' };     // both default 'number' -> duplicate flag gap
  fs.writeFileSync(path.join(HERE, 'graph_gap.json'), JSON.stringify(g, null, 2));
  const t = loadGraph(path.join(HERE, 'graph_gap.json'));
  const built = t.run('buildDeterministicFiles()');
  const full = t.run('serializeGraph()');
  const info = { buildOk: built.ok, gaps: built.gaps };
  if (!built.ok) {
    t.ctx.__gaps = built.gaps;
    const req = t.run('assembleBedrockRequest(__gaps)');
    t.ctx.__req = req;
    info.requestBodyBytes = Buffer.byteLength(JSON.stringify(req.body));
    info.estInputTokens = t.run('estimateRequestTokens(__req)');
    info.systemPromptChars = req.body.system[0].text.length;
    info.graphChars = req.body.messages[0].content[0].text.length;
    info.maxTokensReserved = req.body.inferenceConfig.maxTokens;
    // can buildProjectFiles handle a reply? use a minimal fake reply (no model call)
    t.ctx.__reply = '=== FILE: main.py ===\nprint(1)\n=== END FILE ===';
    const files = t.run('buildProjectFiles(__req, __reply)');
    info.buildProjectFiles = { gaps: files.gaps, files: files.map((f) => f.path) };
    fs.writeFileSync(path.join(HERE, 'gap_request.json'), JSON.stringify(req.body, null, 2));
  }
  out.modelPath = info;
}

fs.writeFileSync(path.join(HERE, 'result.json'), JSON.stringify(out, null, 2));
console.log('done');
