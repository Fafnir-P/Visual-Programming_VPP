const fs=require('fs'),path=require('path'),vm=require('vm');
const R=path.join('prototype');
const ctx=vm.createContext({console,TextEncoder});
for(const f of ['catalog.js','templates.js','ports.js','prompt.js','models.js','bedrock.js']) vm.runInContext(fs.readFileSync(path.join(R,f),'utf8'),ctx,{filename:f});
const C=vm.runInContext('CATALOG',ctx);
for(const c of C){ if(process.argv[2] && !new RegExp(process.argv[2],'i').test(c.title)) continue;
 console.log(c.title+' | '+c.category+' | in: '+c.ports.inputs.map(p=>p.id+':'+p.cls+(p.optional?'?':'')).join(',')+' | out: '+c.ports.outputs.map(p=>p.id+':'+p.cls).join(','));}
