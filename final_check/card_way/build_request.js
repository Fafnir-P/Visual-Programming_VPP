const fs=require('fs'),path=require('path'),vm=require('vm');
const R='C:/Users/Leyang/Desktop/VISUAL_PROGRAMMING_PROJECT';
const ctx=vm.createContext({console,TextEncoder});
for(const f of ['catalog.js','templates.js','ports.js','prompt.js','meter.js','models.js','bedrock.js'])vm.runInContext(fs.readFileSync(path.join(R,'prototype',f),'utf8'),ctx,{filename:f});
const CAT=vm.runInContext('CATALOG',ctx);
const nodeFor=(t,id)=>{const c=CAT.find(x=>x.title===t);return{id,catalogID:c.id,title:t,type:c.category,role:c.role,ports:c.ports};};
const E=(id,a,ap,b,bp)=>({id,fromNodeID:a,fromPort:ap,toNodeID:b,toPort:bp});
const nodes=[['App Start','n1'],['Enter Text','n2'],['Trim Whitespace','n3'],['Change Text Case','n4'],['Check Field Is Required','n5'],['Enter Number','n6'],['Enter Number','n7'],['Calculate From Two Values','n8'],['Format Currency Value','n9'],['App End','n10']].map(a=>nodeFor(...a));
const edges=[E('e1','n2','value','n3','text'),E('e2','n3','text','n4','text'),E('e3','n4','text','n5','value'),E('e4','n6','value','n8','first'),E('e5','n7','value','n8','second'),E('e6','n8','result','n9','value'),E('e7','n9','_done','n10','finish'),E('e8','n1','event','n2','_start')];
ctx.__n=nodes;ctx.__e=edges;
const sw=process.hrtime.bigint();
vm.runInContext(`state={order:[],nodes:new Map(),edges:new Map()};getBedrockEndpoint=()=>'https://example.invalid/converse';for(const n of __n){state.nodes.set(n.id,n);state.order.push(n.id);}for(const e of __e)state.edges.set(e.id,e);`,ctx);
const bad=[];for(const e of edges){const r=vm.runInContext('checkConnection',ctx)(new Map(nodes.map(n=>[n.id,n])),new Map(edges.filter(x=>x.id!==e.id).map(x=>[x.id,x])),{nodeID:e.fromNodeID,portID:e.fromPort,side:'output'},{nodeID:e.toNodeID,portID:e.toPort,side:'input'});if(!r.ok)bad.push([e.id,r]);}
console.error('linkcheck bad:',JSON.stringify(bad));
const req=vm.runInContext('assembleBedrockRequest()',ctx);
const t1=Number(process.hrtime.bigint()-sw)/1e6;
const out=process.argv[2];
fs.writeFileSync(out+'/request.json',JSON.stringify(req,null,0));
const sys=req.body.system?JSON.stringify(req.body.system):'';
const graphText=req.body.messages[0].content[0].text;
const sp=vm.runInContext('SYSTEM_PROMPT',ctx);
const est=vm.runInContext('estimateTokens',ctx);
console.log(JSON.stringify({requestMs:t1,requestBytes:Buffer.byteLength(JSON.stringify(req)),bodyBytes:Buffer.byteLength(JSON.stringify(req.body)),sysChars:sp.length,graphChars:graphText.length,inputTokens:est(sp+graphText),appEstimate:vm.runInContext('estimateRequestTokens',ctx)(req),keys:Object.keys(req.body)}));
fs.writeFileSync(out+'/graph.txt',graphText);

