import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {createInterface} from 'node:readline';
import {createOwnedToolMcp,ownedMcpResult,OWNED_MCP_NAMESPACE,assertOwnedMcpNamespaceAvailable} from '../lib/execution/owned-tool-mcp.mjs';
const definition={name:'neutral',description:'Neutral test tool',inputSchema:{type:'object',properties:{value:{oneOf:[{const:0},{type:'string'}]}}}};
const endpoint=transport=>JSON.parse(transport.overrides.find(value=>value.includes('.env.CODEX_WORKFLOW_TOOL_ENDPOINT=')).split('=').slice(1).join('='));
const response=value=>({success:true,contentItems:[{type:'inputText',text:JSON.stringify(value)}]});
function effectiveConfiguration(transport,base={}){
 const config=structuredClone(base);
 for(const override of transport.overrides){const assignment=override.indexOf('='),keys=override.slice(0,assignment).split('.');let target=config;
  for(const key of keys.slice(0,-1))target=target[key]??={};
  const raw=override.slice(assignment+1);target[keys.at(-1)]=JSON.parse(raw.startsWith('{')?raw.replace(/(\w+)=/g,'"$1":'):raw);
 }
 config.mcp_servers[OWNED_MCP_NAMESPACE].enabled=true;return config;
}

test('owned public namespace is stable across simultaneous transports with private endpoints and isolated callbacks',async()=>{
 const calls=[[],[]],transports=await Promise.all(calls.map((own,index)=>createOwnedToolMcp({tools:[definition],call:async params=>{own.push(params.arguments.value);return response(index);}})));
 try{
  assert(transports.every(transport=>transport.namespace===OWNED_MCP_NAMESPACE));
  const urls=transports.map(endpoint);assert.notEqual(urls[0],urls[1]);
  for(const url of urls)assert.match(new URL(url).pathname,/^\/[a-f0-9]{64}$/);
  const results=await Promise.all(urls.map((url,index)=>fetch(url,{method:'POST',body:JSON.stringify({method:'tools/call',params:{name:'neutral',arguments:{value:index}}})}).then(result=>result.json())));
  assert.deepEqual(calls,[[0],[1]]);assert.deepEqual(results.map(result=>JSON.parse(result.contentItems[0].text)),[0,1]);
 }finally{await Promise.all(transports.map(transport=>transport.close()));}
});

test('owned namespace collision and invalid effective configuration fail visibly without mutations',()=>{
 for(const enabled of [false,true]){
  const config={mcp_servers:{[OWNED_MCP_NAMESPACE]:{enabled},ordinary:{command:'unchanged'}}},before=structuredClone(config);
  assert.throws(()=>assertOwnedMcpNamespaceAvailable(config),{code:'CODEX_MCP_NAMESPACE_COLLISION'});assert.deepEqual(config,before);
 }
 for(const config of [undefined,null,[],{mcp_servers:null},{mcp_servers:[]}])assert.throws(()=>assertOwnedMcpNamespaceAvailable(config),{code:'CODEX_MCP_CONFIG'});
 for(const config of [{},{mcp_servers:{ordinary:{enabled:false}}}])assert.doesNotThrow(()=>assertOwnedMcpNamespaceAvailable(config));
});

test('owned binding verifies exact command args private endpoint and required native policy without leaking authority',async()=>{
 const transport=await createOwnedToolMcp({tools:[definition],call:async()=>response('unused')});
 const config=effectiveConfiguration(transport,{mcp_servers:{ordinary:{command:'unchanged',enabled:false}}}),before=structuredClone(config);
 try{
  assert.deepEqual(transport.qualifyConfiguration(config),{owned_mcp_namespace:OWNED_MCP_NAMESPACE,owned_mcp_binding_qualified:true,
   owned_mcp_direct_tools:true,owned_mcp_direct_namespaces:[`mcp__${OWNED_MCP_NAMESPACE}`,OWNED_MCP_NAMESPACE]});assert.deepEqual(config,before);
  const mutations=[value=>delete value.mcp_servers[OWNED_MCP_NAMESPACE],value=>{value.mcp_servers[OWNED_MCP_NAMESPACE].command='substituted';},
   value=>{value.mcp_servers[OWNED_MCP_NAMESPACE].args.push('extra');},value=>{value.mcp_servers[OWNED_MCP_NAMESPACE].env.CODEX_WORKFLOW_TOOL_ENDPOINT='private-substitution';},
   value=>{value.mcp_servers[OWNED_MCP_NAMESPACE].supports_parallel_tool_calls=false;},value=>{value.mcp_servers[OWNED_MCP_NAMESPACE].default_tools_approval_mode='prompt';},
   value=>{value.mcp_servers[OWNED_MCP_NAMESPACE].enabled=false;}];
  for(const mutate of mutations){const changed=structuredClone(config);mutate(changed);assert.throws(()=>transport.qualifyConfiguration(changed),error=>error.code==='CODEX_MCP_BINDING'&&!error.message.includes(endpoint(transport)));}
 }finally{await transport.close();}
});

test('owned MCP exposes a detached exact configuration overlay without changing callable schemas or overrides',async()=>{
 const transport=await createOwnedToolMcp({tools:[definition],call:async()=>response('unused'),configuration:{features:{code_mode:{enabled:false,direct_only_tool_namespaces:['existing']}}}});
 try{
  const expected=effectiveConfiguration(transport);expected.mcp_servers[OWNED_MCP_NAMESPACE].environment_id='local';assert.deepEqual(transport.configuration_overlay,expected);
  const changed=transport.configuration_overlay;changed.mcp_servers[OWNED_MCP_NAMESPACE].env.CODEX_WORKFLOW_TOOL_ENDPOINT='foreign';changed.features.code_mode.direct_only_tool_namespaces=[];
  assert.deepEqual(transport.configuration_overlay,expected);
 }finally{await transport.close();}
});

test('owned direct namespace projection preserves existing mode settings and rejects changed or forced deferred configuration',async()=>{
 const configuration={features:{code_mode:{enabled:false,direct_only_tool_namespaces:['existing'],excluded_tool_namespaces:['unchanged'],tool_input_schema_max_bytes:32768},unrelated:true}};
 const before=structuredClone(configuration),transport=await createOwnedToolMcp({tools:[definition],call:async()=>response('unused'),configuration});
 try{
  assert.deepEqual(configuration,before);const effective=effectiveConfiguration(transport,configuration);
  assert.deepEqual(effective.features.code_mode,{...configuration.features.code_mode,direct_only_tool_namespaces:['existing',`mcp__${OWNED_MCP_NAMESPACE}`,OWNED_MCP_NAMESPACE]});
  assert.equal(effective.features.unrelated,true);assert.equal(transport.qualifyConfiguration(effective).owned_mcp_direct_tools,true);
  for(const change of [config=>delete config.features.code_mode,config=>config.features.code_mode.direct_only_tool_namespaces.pop(),
    config=>{config.features.code_mode.enabled=true;},config=>{config.features.code_mode.excluded_tool_namespaces=[];}]){
   const changed=structuredClone(effective);change(changed);assert.throws(()=>transport.qualifyConfiguration(changed),{code:'CODEX_MCP_DIRECT_BINDING'});
  }
  const forced=structuredClone(effective);forced.features.code_mode_only_strict_3p_tools=true;
  assert.throws(()=>transport.qualifyConfiguration(forced),{code:'CODEX_MCP_DIRECT_UNSUPPORTED'});
 }finally{await transport.close();}
 for(const configuration of [{features:{code_mode_only_strict_3p_tools:true}},{features:{code_mode:{direct_only_tool_namespaces:'bad'}}},
   {features:{code_mode:{unknown_option:true}}},{features:{code_mode_only_strict_3p_tools:'unknown'}},{features:[]}])await assert.rejects(createOwnedToolMcp({tools:[definition],call:async()=>response('unused'),configuration}),
   error=>['CODEX_MCP_DIRECT_CONFIG','CODEX_MCP_DIRECT_UNSUPPORTED'].includes(error.code));
});

test('owned direct namespace projection preserves boolean feature value and nullable default absence',async()=>{
 for(const value of [false,true,{enabled:null,direct_only_tool_namespaces:null}]){
  const transport=await createOwnedToolMcp({tools:[definition],call:async()=>response('unused'),configuration:{features:{code_mode:value}}});
  try{const effective=effectiveConfiguration(transport);assert.equal(transport.qualifyConfiguration(effective).owned_mcp_direct_tools,true);
   assert.equal(effective.features.code_mode.enabled,typeof value==='boolean'?value:undefined);
  }finally{await transport.close();}
 }
});

test('owned transport preserves full native schemas, parallel callbacks, result types and private scope',async()=>{
 let active=0,max=0,release;const barrier=new Promise(resolve=>{release=resolve;});
 const transport=await createOwnedToolMcp({tools:[definition],call:async p=>{
  active++;max=Math.max(max,active);if(active===2)release();await barrier;active--;return response({call_id:p.callId,value:p.arguments.value});
 }}),url=endpoint(transport);
 try{
  assert.equal((await fetch(url+'wrong',{method:'POST'})).status,403);
  const list=await fetch(url,{method:'POST',body:JSON.stringify({method:'tools/list'})});assert.deepEqual((await list.json()).tools,[definition]);
  const invoke=value=>fetch(url,{method:'POST',body:JSON.stringify({method:'tools/call',params:{name:'neutral',arguments:{value}}})}).then(r=>r.json());
  const results=await Promise.all([invoke(0),invoke('two')]);assert.equal(max,2);
  assert(results.every(item=>JSON.parse(item.contentItems[0].text).call_id.startsWith('owned-mcp-')));
  assert.deepEqual(ownedMcpResult(response({kept:'as text'})),{content:[{type:'text',text:'{"kept":"as text"}'}],isError:false});
  assert.deepEqual(ownedMcpResult({success:true,contentItems:[{type:'inputImage',imageUrl:'data:image/png;base64,aA=='}]}),{content:[{type:'image',mimeType:'image/png',data:'aA=='}],isError:false});
  assert.throws(()=>ownedMcpResult({success:true,contentItems:[{type:'unknown'}]}),{code:'CODEX_TOOL_RESULT'});
  transport.revoke();assert.equal((await fetch(url,{method:'POST',body:'{}'})).status,410);
 }finally{release();await transport.close();}
 await assert.rejects(fetch(url,{method:'POST'}));
});

test('actual stdio MCP cancellation fences delivery and exposes failure before the original job ends',async()=>{
 let entered,release,calls=0;const started=new Promise(resolve=>{entered=resolve;}),held=new Promise(resolve=>{release=resolve;});
 const transport=await createOwnedToolMcp({tools:[definition],call:async()=>{calls++;entered();await held;return response('late');}});
 const child=spawn(process.execPath,[fileURLToPath(new URL('../lib/execution/owned-tool-mcp-stdio.mjs',import.meta.url))],
  {windowsHide:true,stdio:['pipe','pipe','pipe'],env:{...process.env,CODEX_WORKFLOW_TOOL_ENDPOINT:endpoint(transport)}});
 const closed=new Promise(resolve=>child.once('close',resolve)),output=[];
 createInterface({input:child.stdout}).on('line',line=>output.push(JSON.parse(line)));
 const send=message=>child.stdin.write(JSON.stringify(message)+'\n');
 try{
  send({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'neutral',arguments:{value:0}}});await started;
  const failure=assert.rejects(transport.failed,{code:'CODEX_MCP_DELIVERY_LOST'});
  send({jsonrpc:'2.0',method:'notifications/cancelled',params:{requestId:1}});await failure;
  const after=await fetch(endpoint(transport),{method:'POST',body:JSON.stringify({method:'tools/call',params:{name:'neutral',arguments:{value:0}}})});
  assert.equal(after.status,410);assert.equal(calls,1,'Failure must fence admission without waiting for receipt I/O');
  assert.throws(()=>transport.throwIfFailed(),{code:'CODEX_MCP_DELIVERY_LOST'});
  release();await new Promise(resolve=>setImmediate(resolve));
  assert(!output.some(message=>message.result));
  await assert.rejects(transport.close(),{code:'CODEX_MCP_DELIVERY_LOST'});
 }finally{release();child.stdin.end();await closed;await transport.close();}
 assert.throws(()=>process.kill(child.pid,0),{code:'ESRCH'});
});

test('Host revocation stops the exact native MCP shim without stdin EOF',async()=>{
 const transport=await createOwnedToolMcp({tools:[definition],call:async()=>response('unused')});
 const child=spawn(process.execPath,[fileURLToPath(new URL('../lib/execution/owned-tool-mcp-stdio.mjs',import.meta.url))],
  {windowsHide:true,stdio:['pipe','pipe','pipe'],env:{...process.env,CODEX_WORKFLOW_TOOL_ENDPOINT:endpoint(transport)}});
 const closed=new Promise(resolve=>child.once('close',resolve));
 const line=new Promise(resolve=>createInterface({input:child.stdout}).once('line',resolve));
 child.stdin.write(JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list'})+'\n');
 await line;transport.revoke();
 let timer;try{assert.equal(await Promise.race([closed,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Owned shim retained stdin')),2000);})]),0);}
 finally{clearTimeout(timer);if(child.exitCode===null)child.kill();await closed;await transport.close();}
 assert.throws(()=>process.kill(child.pid,0),{code:'ESRCH'});
});
