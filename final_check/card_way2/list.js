const { load } = require('../../tests/orderline_helper');
const t = load();
const T = t.run('CARD_TEMPLATES');
const rows = t.CAT.filter(c => c.category && /Text|Number|Value|Calc|Format|Trim|Case|Join|Round|Percent|Summary|Compare|Math|Count|Clamp|Replace|Pad|Length|Limit/i.test(c.title)).map(c => { const x = T[c.title]; return c.title + ' | ' + c.category + ' | in=' + (x?x.inputs:'?') + ' out=' + (x?x.outputs:'?') + ' set=' + (x? (x.settings||[]).map(s=>s.name+(s.required?'*':'')+'='+JSON.stringify(s.default)).join(','):'?'); });
console.log(rows.join('\n'));
