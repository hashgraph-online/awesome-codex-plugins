import {createInterface} from 'node:readline';
import {request} from 'node:http';
import {ownedMcpResult} from './owned-tool-mcp.mjs';

// Per-owned-session native MCP stdio transport. All work and authorization stay
// in the existing parent brokers. Neither endpoint nor tool inputs are logged.
const endpoint=process.env.CODEX_WORKFLOW_TOOL_ENDPOINT;
if(!/^http:\/\/127\.0\.0\.1:\d+\/[a-f0-9]{64}$/.test(endpoint??''))throw new Error('Owned MCP endpoint is missing or invalid');
const pending=new Map();let closing=false;
const reply=(id,result)=>{if(!closing)process.stdout.write(JSON.stringify({jsonrpc:'2.0',id,result})+'\n');};
async function parent(message,signal){
 const response=await fetch(endpoint,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(message),signal});
 if(!response.ok)throw new Error('Owned MCP broker rejected request: '+response.status);
 return response.json();
}
const input=createInterface({input:process.stdin});
const stop=code=>{closing=true;for(const controller of pending.values())controller.abort();process.exit(code);};
// A held owner channel has no polling and no model context. Native subprocesses
// may retain stdio after the App Server exits; exact Host revocation or channel
// loss ends this owned shim even when its stdin never receives EOF.
// fetch has implicit five-minute header/body deadlines. The lifecycle channel
// must remain silent for the full Host wait; only explicit EOF/revocation ends it.
const owner=request(endpoint,{method:'POST',headers:{'content-type':'application/json'},timeout:0},response=>{
 if(response.statusCode!==200)return stop(1);
 let body='';response.setTimeout(0);
 response.on('data',chunk=>{body+=chunk;if(Buffer.byteLength(body)>64)stop(1);});
 response.on('error',()=>stop(1));response.on('aborted',()=>stop(1));
 response.on('end',()=>{try{stop(JSON.parse(body).revoked===true?0:1);}catch{stop(1);}});
});
owner.on('socket',socket=>socket.setTimeout(0));owner.on('error',()=>stop(1));
owner.end(JSON.stringify({method:'owner/wait'}));
input.on('line',line=>{
 let message;
 try{message=JSON.parse(line);}catch{process.stderr.write('Invalid owned MCP JSON\n');process.exit(1);}
 if(message.method==='notifications/cancelled'){pending.get(message.params?.requestId)?.abort();return;}
 if(message.id==null)return;
 if(pending.has(message.id)){process.stderr.write('Duplicate owned MCP request identity\n');process.exit(1);}
 const controller=new AbortController();pending.set(message.id,controller);
 (async()=>{
  if(message.method==='initialize')return reply(message.id,{protocolVersion:message.params.protocolVersion,capabilities:{tools:{}},serverInfo:{name:'workflow-owned-tools',version:'1.2'}});
  if(message.method==='ping')return reply(message.id,{});
  if(message.method==='tools/list'){
   const {tools}=await parent({method:'tools/list'},controller.signal);
   return reply(message.id,{tools:tools.map(tool=>({...tool,annotations:{readOnlyHint:false,openWorldHint:true}}))});
  }
  if(message.method==='tools/call')return reply(message.id,ownedMcpResult(await parent({method:'tools/call',params:message.params},controller.signal)));
  throw new Error('Unknown owned MCP method');
 })().catch(error=>{
   if(!closing)process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message.id,error:{code:-32603,message:error.message}})+'\n');
 }).finally(()=>pending.delete(message.id));
});
input.on('close',()=>stop(0));
