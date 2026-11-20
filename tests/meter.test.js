// Tests for prototype/meter.js.   node tests/meter.test.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ctx = vm.createContext({ console });
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'prototype', 'meter.js'), 'utf8'), ctx, { filename: 'meter.js' });
const run = (code) => vm.runInContext(code, ctx);
const J = (x) => JSON.stringify(x);

let pass = 0;
let fail = 0;
function ok(cond, name, extra) {
  if (cond) pass++; else { fail++; console.log('FAIL', name, extra === undefined ? '' : extra); }
}

ok(run("estimateTokens('')") === 0 && run("estimateTokens('abcd')") === 1 && run("estimateTokens('abcde')") === 2, 'estimateTokens = ceil(chars/4)');
ok(run('estimateTokens(undefined)') === 0 && run('estimateTokens(null)') === 0, 'estimateTokens of nothing is 0');

// No usage: uncertain, never zero.
run('resetMeter()');
let s = run('summary()');
ok(s.accounting === 'uncertain' && s.inputTokens === null && s.outputTokens === null && s.totalTokens === null && s.waitMs === null, 'empty summary is uncertain', J(s));

// Estimate.
run('recordUsage({ input: 100, output: 40, estimated: true })');
s = run('summary()');
ok(s.accounting === 'estimate' && s.inputTokens === 100 && s.outputTokens === 40 && s.totalTokens === 140, 'estimate usage', J(s));

// Reported only.
run('resetMeter(); recordUsage({ input: 10, output: 5 }); recordUsage({ input: 1, output: 2 })');
s = run('summary()');
ok(s.accounting === 'reported' && s.inputTokens === 11 && s.outputTokens === 7 && s.totalTokens === 18, 'reported usage adds up', J(s));

// Mixed: weakest label.
run('recordUsage({ input: 1, output: 1, estimated: true })');
ok(run('summary()').accounting === 'estimate', 'mixed reported + estimate is labeled estimate');

// Missing usage is uncertain and never counted as zero.
for (const bad of ['{}', 'undefined', '{ input: 5 }', '{ input: 5, output: "x" }', '{ input: -1, output: 2 }', '{ input: NaN, output: 2 }']) {
  run('resetMeter(); recordUsage({ input: 3, output: 3 }); recordUsage(' + bad + ')');
  s = run('summary()');
  ok(s.accounting === 'uncertain' && s.totalTokens === null && s.inputTokens === null, 'missing usage ' + bad + ' -> uncertain', J(s));
}

// Wait time, separate from tokens and from task time.
run('resetMeter()');
ok(run('endGeneration(5)') === null, 'endGeneration without start is null');
run('startGeneration(1000)');
ok(run('endGeneration(1750)') === 750, 'wait = end - start');
run('startGeneration(2000); endGeneration(2250)');
s = run('summary()');
ok(s.waitMs === 1000 && s.accounting === 'uncertain', 'waits add up; no usage stays uncertain', J(s));
ok(run('startGeneration(); endGeneration()') >= 0, 'default clock works');
ok(J(run('TASK_TIME_FIELDS')) === J(['firstCardPlacedAt', 'previewAcceptedAt']) && !('taskMs' in s), 'task time: field names only, not measured');

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
