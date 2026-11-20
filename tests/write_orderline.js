// Writes the order-line project with the app's own code:  node tests/write_orderline.js <outdir>
// <outdir>/cards.py and <outdir>/main.py come from buildDeterministicFiles(). Prints {ok, gaps, tokens}.
const fs = require('fs');
const path = require('path');
const { load, ROOT } = require('./orderline_helper');

const t = load();
const g = JSON.parse(fs.readFileSync(path.join(ROOT, 'final_check', 'orderline', 'graph.json'), 'utf8'));
t.setGraph(g);
const built = t.run('buildDeterministicFiles()');
const out = process.argv[2];
if (built.ok) {
  fs.mkdirSync(out, { recursive: true });
  for (const f of built.files) fs.writeFileSync(path.join(out, f.path), f.content);
}
console.log(JSON.stringify({ ok: built.ok, gaps: built.gaps, files: built.files.map((f) => f.path) }));