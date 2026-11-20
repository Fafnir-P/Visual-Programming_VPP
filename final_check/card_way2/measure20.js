// 23-card graph: link validity, compileMainPy, write, run. Edits no project file.
const fs = require('fs');
const path = require('path');
const cp = require('child_process');
const { load, ROOT } = require(path.join('..', '..', 'tests', 'orderline_helper'));
const HERE = __dirname;
const g = JSON.parse(fs.readFileSync(path.join(HERE, 'graph20.json'), 'utf8'));
const t = load();
t.setGraph(g);
const out = { cards: g.nodes.length };

// every link through checkConnection (links added one by one)
t.ctx.__g = g;
out.linkChecks = t.run(`(() => {
  const res = []; const edges = new Map();
  __g.edges.forEach((e, i) => {
    const r = checkConnection(state.nodes, edges, { nodeID: e[0], portID: e[1] }, { nodeID: e[2], portID: e[3] });
    res.push({ link: e.join(' '), ok: r.ok, message: r.ok ? '' : r.message });
    if (r.ok) edges.set('x' + i, { id: 'x' + i, fromNodeID: e[0], fromPort: e[1], toNodeID: e[2], toPort: e[3] });
  });
  return res;
})()`);
out.allLinksOk = out.linkChecks.every((x) => x.ok);

const issues = t.run('typeof findGenerationIssues === "function" ? findGenerationIssues(state.nodes, state.edges, state.order) : "n/a (app.js not loaded)"');
out.generationIssues = issues;

const built = t.run('buildDeterministicFiles()');
out.compileOk = built.ok;
out.gaps = built.gaps;
const dir = path.join(HERE, 'run20');
fs.rmSync(dir, { recursive: true, force: true });
fs.mkdirSync(dir, { recursive: true });
if (built.ok) {
  for (const f of built.files) fs.writeFileSync(path.join(dir, f.path), f.content);
  fs.cpSync(path.join(ROOT, 'card_templates'), path.join(dir, 'card_templates'), { recursive: true, filter: (s) => !s.includes('__pycache__') });
  const sz = {};
  for (const f of built.files) { sz[f.path] = { bytes: Buffer.byteLength(f.content), lines: f.content.split('\n').length - 1, estTokens: Math.ceil(f.content.length / 4) }; }
  out.fileSizes = sz;
  out.equivalentHandWrittenEstTokens = Math.ceil(built.files.reduce((a, f) => a + f.content.length, 0) / 4);
  const run = (args) => { const r = cp.spawnSync('python', [path.join(dir, 'main.py'), ...args], { encoding: 'utf8' }); return { code: r.status, stdout: r.stdout.trim(), stderr: r.stderr.trim() }; };
  const good = ['--customer', '  ada-lovelace  ', '--qty', '3', '--price', '2.5', '--shipping', '4', '--handling', '1', '--old', '50', '--new', '60'];
  out.run_ok = run(good);
  out.run_repeat = run(good);
  out.run_blank_ok = run(good.map((x) => (x === '  ada-lovelace  ' ? 'bob' : x)));
  out.run_badnum = run(good.map((x) => (x === '3' ? 'abc' : x)));
  out.run_missing_flag = run(['--customer', 'bob']);
  const t0 = process.hrtime.bigint();
  const reps = [];
  for (let i = 0; i < 3; i++) { const s = process.hrtime.bigint(); run(good); reps.push(Number(process.hrtime.bigint() - s) / 1e6); }
  out.pythonRunMs = reps;
  // compile timing, 5 runs
  const ct = [];
  for (let i = 0; i < 5; i++) { const tt = load(); tt.setGraph(g); const s = process.hrtime.bigint(); tt.run('buildDeterministicFiles()'); ct.push(Number(process.hrtime.bigint() - s) / 1e6); }
  out.buildDeterministicFilesMs = ct;
  // slim request size of the same graph (what the model path would send)
  t.run('1');
  try {
    const req = t.run('assembleBedrockRequest([])');
    t.ctx.__req = req;
    out.modelPathIfUsed = { requestBodyBytes: Buffer.byteLength(JSON.stringify(req.body)), estInputTokens: t.run('estimateRequestTokens(__req)') };
  } catch (e) { out.modelPathIfUsed = { error: e.message }; }
}
fs.writeFileSync(path.join(HERE, 'result20.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
