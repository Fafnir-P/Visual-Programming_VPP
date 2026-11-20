const fs=require('fs'),path=require('path'),vm=require('vm');
const R='C:/Users/Leyang/Desktop/VISUAL_PROGRAMMING_PROJECT';
const ctx=vm.createContext({console,TextEncoder});
for(const f of ['catalog.js','templates.js','ports.js','prompt.js','meter.js','models.js','bedrock.js'])vm.runInContext(fs.readFileSync(path.join(R,'prototype',f),'utf8'),ctx,{filename:f});
const [,, reqf, replyf, outdir]=process.argv;
const req=JSON.parse(fs.readFileSync(reqf,'utf8'));
const reply=fs.readFileSync(replyf,'utf8');
const est=vm.runInContext('estimateTokens',ctx);
const t=process.hrtime.bigint();
const res=vm.runInContext('buildProjectFiles',ctx)(req,reply);
const ms=Number(process.hrtime.bigint()-t)/1e6;
fs.mkdirSync(outdir,{recursive:true});
const files=Array.isArray(res)?res:(res.files||res);
const info={assemblyMs:ms,outTokens:est(reply),shape:Array.isArray(res)?'array':Object.keys(res)};
if(Array.isArray(files)){for(const f of files){fs.writeFileSync(path.join(outdir,f.path||f.name),f.content);info[f.path||f.name]=Buffer.byteLength(f.content);}}
else console.log(JSON.stringify(res).slice(0,500));
console.log(JSON.stringify(info));
