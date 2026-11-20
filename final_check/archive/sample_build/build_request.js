const fs=require('fs'),path=require('path'),vm=require('vm');
const R='prototype';
const ctx=vm.createContext({console,TextEncoder});
for(const f of ['catalog.js','templates.js','ports.js','prompt.js','models.js','bedrock.js']) vm.runInContext(fs.readFileSync(path.join(R,f),'utf8'),ctx,{filename:f});
const CAT=vm.runInContext('CATALOG',ctx);
const nodeFor=(title,id)=>{const c=CAT.find(x=>x.title===title);if(!c)throw new Error('no '+title);return {id,catalogID:c.id,title,type:c.category,role:c.role,ports:c.ports};};
const nodes=[['App Start','n1'],['Enter Number','n2'],['Enter Number','n3'],['Calculate From Two Values','n4'],['Validate Number Range','n5'],['Format Currency Value','n6'],['Show Message Banner','n7'],['App End','n8']].map(a=>nodeFor(...a));
const E=(id,a,ap,b,bp)=>({id,fromNodeID:a,fromPort:ap,toNodeID:b,toPort:bp});
const edges=[E('e1','n2','value','n4','first'),E('e2','n3','value','n4','second'),E('e3','n4','result','n5','value'),E('e4','n5','value','n6','value'),E('e5','n6','text','n7','message'),E('e6','n1','event','n8','finish')];
ctx.__n=nodes;ctx.__e=edges;
vm.runInContext(`state={order:[],nodes:new Map(),edges:new Map()};getBedrockEndpoint=()=>'https://example.invalid/converse';
for(const n of __n){state.nodes.set(n.id,n);state.order.push(n.id);} `,ctx);
// validate each link with the app's own rules
const out=[];
vm.runInContext(`globalThis.__chk=[]`,ctx);
for(const e of edges){
  const f=nodes.find(n=>n.id===e.fromNodeID),t=nodes.find(n=>n.id===e.toNodeID);
  const fp=f.ports.outputs.find(p=>p.id===e.fromPort),tp=t.ports.inputs.find(p=>p.id===e.toPort);
  const ok=vm.runInContext(`classesCompatible(${JSON.stringify(fp.cls)},${JSON.stringify(tp.cls)})`,ctx);
  console.log(e.id,f.title+'.'+fp.id+'('+fp.cls+') -> '+t.title+'.'+tp.id+'('+tp.cls+')',ok?'OK':'BAD');
}
ctx.__edges=edges;
vm.runInContext(`for(const e of __edges) state.edges.set(e.id,e);`,ctx);
const req=vm.runInContext('assembleBedrockRequest()',ctx);
fs.mkdirSync('sample_build',{recursive:true});
const s=JSON.stringify(req,null,2);fs.writeFileSync('sample_build/request.json',s);
const g=JSON.parse(req.body.messages[0].content[0].text);
fs.writeFileSync('sample_build/graph.json',JSON.stringify(g,null,2));
console.log('request.json bytes',Buffer.byteLength(s),'graph text bytes',Buffer.byteLength(req.body.messages[0].content[0].text),'system bytes',Buffer.byteLength(req.body.system[0].text));
for(const n of g.nodes) console.log(n.id,n.title,'cfg',JSON.stringify(n.config),'req',JSON.stringify(n.requiredConfig),'inputs',n.ports.inputs.map(p=>p.id+(p.optional?'?':'')).join(','),'outputs',n.ports.outputs.map(p=>p.id).join(','),'codeBytes',n.templateCode.length);

