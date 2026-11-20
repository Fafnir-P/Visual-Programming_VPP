// usage: node sample_build2/parse_reply.js <reply file> <out dir>
const fs = require('fs'), path = require('path'), vm = require('vm');
const ctx = vm.createContext({ console, TextEncoder });
for (const f of ['catalog.js', 'templates.js', 'ports.js', 'prompt.js', 'models.js', 'bedrock.js'])
  vm.runInContext(fs.readFileSync(path.join('prototype', f), 'utf8'), ctx, { filename: f });
ctx.__t = fs.readFileSync(process.argv[2], 'utf8');
const r = vm.runInContext('parseGenerationReply(__t)', ctx);
const out = path.resolve(process.argv[3]);
for (const f of r.files) {
  const dest = path.resolve(out, f.path);
  if (!dest.startsWith(out + path.sep)) throw new Error('escape ' + f.path);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, f.content + '\n');
}
console.log('files:', r.files.map(f => f.path).join(', ') || '(none)');
console.log('gaps:', JSON.stringify(r.gaps));
