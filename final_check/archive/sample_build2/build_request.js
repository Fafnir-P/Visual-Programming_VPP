const fs=require('fs'),path=require('path'),vm=require('vm');
const R='prototype';
const gap=process.argv[2]==='gap';
const ctx=vm.createContext({console,TextEncoder});
for(const f of ['catalog.js','templates.js','ports.js','prompt.js','models.js','bedrock.js']) vm.runInContext(fs.readFileSync(path.join(R,f),'utf8'),ctx,{filename:f});
const CAT=vm.runInContext('CATALOG',ctx);
const nodeFor=(title,id)=>{const c=CAT.find(x=>x.title===title);if(!c)throw new Error('no '+title);return {id,catalogID:c.id,title,type:c.category,role:c.role,ports:c.ports};};
const nodes=[['App Start','n1'],['Enter Text','n2'],['Trim Whitespace','n3'],['Change Text Case','n4'],['Check Field Is Required','n5'],['Show Message Banner','n6'],['App End','n7']].map(a=>nodeFor(...a));
const E=(id,a,ap,b,bp)=>({id,fromNodeID:a,fromPort:ap,toNodeID:b,toPort:bp});
let edges=[E('e1','n2','value','n3','text'),E('e2','n3','text','n4','text'),E('e3','n4','text','n5','value'),E('e4','n5','value','n6','message'),E('e5','n1','event','n7','finish')];
if(gap) edges=edges.filter(e=>e.id!=='e2');
ctx.__n=nodes;ctx.__e=edges;
vm.runInContext(`state={order:[],nodes:new Map(),edges:new Map()};getBedrockEndpoint=()=>'https://example.invalid/converse';
for(const n of __n){state.nodes.set(n.id,n);state.order.push(n.id);} for(const e of __e) state.edges.set(e.id,e);`,ctx);
for(const e of edges){
  const f=nodes.find(n=>n.id===e.fromNodeID),t=nodes.find(n=>n.id===e.toNodeID);
  const fp=f.ports.outputs.find(p=>p.id===e.fromPort),tp=t.ports.inputs.find(p=>p.id===e.toPort);
  console.log(e.id,f.title+'.'+fp.id+'('+fp.cls+') -> '+t.title+'.'+tp.id+'('+tp.cls+')',vm.runInContext(`classesCompatible(${JSON.stringify(fp.cls)},${JSON.stringify(tp.cls)})`,ctx)?'OK':'BAD');
}
console.log('issues',JSON.stringify(vm.runInContext('findGenerationIssues(state.nodes,state.edges,state.order)',ctx)));
const req=vm.runInContext('assembleBedrockRequest()',ctx);
const sfx=gap?'_gap':'';
const s=JSON.stringify(req,null,2);fs.writeFileSync('sample_build2/request'+sfx+'.json',s);
const g=JSON.parse(req.body.messages[0].content[0].text);
fs.writeFileSync('sample_build2/graph'+sfx+'.json',JSON.stringify(g,null,2));
fs.writeFileSync('sample_build2/system_prompt.txt',req.body.system[0].text);
console.log('request bytes',Buffer.byteLength(s),'graph',Buffer.byteLength(req.body.messages[0].content[0].text),'system',Buffer.byteLength(req.body.system[0].text));
for(const n of g.nodes) console.log(n.id,n.title,'cfg',JSON.stringify(n.config),'req',JSON.stringify(n.requiredConfig),'rt',JSON.stringify(n.runtimeNames),'in',n.ports.inputs.map(p=>p.id+':'+p.class+(p.optional?'?':'')).join(','),'out',n.ports.outputs.map(p=>p.id+':'+p.class).join(','));
