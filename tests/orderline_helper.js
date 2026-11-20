// Shared test helper: loads the prototype scripts into a vm context and builds `state` from a graph file.
//   const { load } = require('./orderline_helper');  const t = load(); t.setGraph(graph); t.run('...')
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const FILES = ['catalog.js', 'templates.js', 'ports.js', 'prompt.js', 'meter.js', 'models.js', 'compile.js', 'bedrock.js'];

function load() {
  const ctx = vm.createContext({ console, TextEncoder });
  for (const f of FILES) vm.runInContext(fs.readFileSync(path.join(ROOT, 'prototype', f), 'utf8'), ctx, { filename: f });
  const run = (code) => vm.runInContext(code, ctx);
  const CAT = run('CATALOG');
  function setGraph(g) {
    const nodes = g.nodes.map((n) => {
      const c = CAT.find((x) => x.title === n.title);
      const node = { id: n.id, catalogID: c.id, title: n.title, type: c.category, role: c.role, ports: c.ports };
      if (n.config) node.config = JSON.parse(JSON.stringify(n.config));
      return node;
    });
    const edges = g.edges.map((e, i) => ({ id: 'e' + i, fromNodeID: e[0], fromPort: e[1], toNodeID: e[2], toPort: e[3] }));
    ctx.__nodes = nodes;
    ctx.__edges = edges;
    ctx.__order = g.order || nodes.map((n) => n.id);
    run(`state = { order: __order.slice(), nodes: new Map(), edges: new Map() };
         getBedrockEndpoint = () => 'https://example.invalid/converse';
         for (const n of __nodes) state.nodes.set(n.id, n);
         for (const e of __edges) state.edges.set(e.id, e);`);
  }
  return { ctx, run, setGraph, CAT };
}

module.exports = { load, ROOT };