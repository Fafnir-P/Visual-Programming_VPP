// Tests for pure parts of main.js / app.js.   node tests/main_pure.test.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { createLockout } = require('../lockout.js');

let pass = 0;
let fail = 0;
function ok(cond, name) {
  if (cond) pass++; else { fail++; console.log('FAIL', name); }
}

// --- lockout ---
let t = 0;
const lock = createLockout(() => t);
for (let i = 0; i < 4; i++) lock.fail('ann');
ok(lock.remaining('ann') === 0, '4 failures: not locked');
lock.fail('ann');
ok(lock.remaining('ann') === 30000, '5th failure: locked 30 s');
ok(lock.remaining('bob') === 0, 'other name unaffected');
t += 30001;
ok(lock.remaining('ann') === 0, 'lock ends after 30 s');
for (let i = 0; i < 5; i++) lock.fail('ann');
ok(lock.remaining('ann') === 60000, 'second lockout is 60 s');
lock.success('ann');
for (let i = 0; i < 5; i++) lock.fail('ann');
ok(lock.remaining('ann') === 30000, 'success resets growth');

// --- will-navigate rule and Delete guard ---
const mainSrc = fs.readFileSync(path.join(__dirname, '..', 'main.js'), 'utf8');
ok(/function isAppUrl\(/.test(mainSrc), 'main.js has isAppUrl');
const appSrc = fs.readFileSync(path.join(__dirname, '..', 'prototype', 'app.js'), 'utf8');
const m = appSrc.match(/function isEditingTarget\(el\) \{[\s\S]*?\n\}/);
ok(!!m, 'app.js has isEditingTarget');
const ctx = vm.createContext({});
vm.runInContext(m[0], ctx);
const isEdit = (el) => vm.runInContext('isEditingTarget', ctx)(el);
const el = (tagName, extra = {}) => Object.assign({ tagName, isContentEditable: false, closest: () => null }, extra);
ok(isEdit(el('SELECT')) && isEdit(el('BUTTON')) && isEdit(el('INPUT')) && isEdit(el('TEXTAREA')), 'form controls block delete');
ok(isEdit(el('DIV', { isContentEditable: true })), 'contentEditable blocks delete');
ok(isEdit(el('DIV', { closest: (s) => (s === 'dialog' ? {} : null) })), 'inside dialog blocks delete');
ok(!isEdit(el('DIV')) && !isEdit(el('BODY')) && !isEdit(null), 'canvas/body allows delete');

console.log(pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
