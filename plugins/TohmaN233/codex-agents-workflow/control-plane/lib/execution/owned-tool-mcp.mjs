import {createServer} from 'node:http';
import {randomBytes,randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {requireValue} from '../workflow-paths.mjs';
import {canonicalJSON} from '../workflow-revisions.mjs';

// The public namespace belongs to this module; endpoint authority remains private
// to one owned transport and its separately owned App Server process.
export const OWNED_MCP_NAMESPACE='codex_agents_workflow_owned';
// These are the compiler's two normal MCP namespace forms. Keeping both
// preserves the user's prefix feature rather than changing its global policy.
const ownedModelNamespaces=[`mcp__${OWNED_MCP_NAMESPACE}`,OWNED_MCP_NAMESPACE];
const codeModeKeys=new Set(['enabled','default_exec_yield_time_ms','experimental_show_cell_overhead',
 'tool_input_schema_max_bytes','direct_only_tool_namespaces','excluded_tool_namespaces']);
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
// Core attaches these identities outside the model-authored arguments. Keep
// only the routing fields; arbitrary MCP metadata never enters node context.
export function ownedMcpContext(meta){
 if(meta===undefined)return null;
 const id=value=>typeof value==='string'&&value.length>0&&value.length<=256;
 const turn=meta?.['x-codex-turn-metadata'];
 requireValue(object(meta)&&object(turn)&&id(meta.threadId)&&id(meta.sessionId)
   &&id(meta.callId)&&id(turn.turn_id),'CODEX_MCP_CONTEXT','Owned MCP context is incomplete');
 return Object.freeze({thread_id:meta.threadId,session_id:meta.sessionId,turn_id:turn.turn_id,call_id:meta.callId});
}
function codeModeConfiguration(configuration){
 requireValue(object(configuration)&&(configuration.features==null||object(configuration.features)),
  'CODEX_MCP_DIRECT_CONFIG','Effective code-mode configuration is invalid');
 const features=configuration.features??{};
 requireValue(features.code_mode_only_strict_3p_tools==null||typeof features.code_mode_only_strict_3p_tools==='boolean',
  'CODEX_MCP_DIRECT_CONFIG','Effective third-party deferral policy is invalid');
 requireValue(features.code_mode_only_strict_3p_tools!==true,'CODEX_MCP_DIRECT_UNSUPPORTED',
  'Strict third-party deferral conflicts with direct owned tools');
 const value=features.code_mode;
 requireValue(value==null||typeof value==='boolean'||object(value),'CODEX_MCP_DIRECT_CONFIG','Effective code-mode options are invalid');
 const options=typeof value==='boolean'?{enabled:value}:Object.fromEntries(Object.entries(value??{}).filter(([,v])=>v!==null));
 requireValue(Object.keys(options).every(key=>codeModeKeys.has(key))&&Object.values(options).every(v=>
  typeof v==='boolean'||typeof v==='number'&&Number.isFinite(v)||Array.isArray(v)&&v.every(item=>typeof item==='string')),
  'CODEX_MCP_DIRECT_CONFIG','Effective code-mode options cannot be preserved exactly');
 requireValue(options.direct_only_tool_namespaces===undefined||Array.isArray(options.direct_only_tool_namespaces),
  'CODEX_MCP_DIRECT_CONFIG','Effective direct namespace list is invalid');
 return options;
}
function serversFrom(configuration){
 requireValue(object(configuration),'CODEX_MCP_CONFIG','Effective MCP configuration is unavailable');
 // ConfigReadResponse.Config permits optional additional properties, including
 // an absent MCP dictionary. A present invalid dictionary is never absence.
 if(!Object.hasOwn(configuration,'mcp_servers'))return {};
 requireValue(object(configuration.mcp_servers),'CODEX_MCP_CONFIG','Effective MCP server dictionary is invalid');
 return configuration.mcp_servers;
}
export function assertOwnedMcpNamespaceAvailable(configuration){
 requireValue(!Object.hasOwn(serversFrom(configuration),OWNED_MCP_NAMESPACE),
  'CODEX_MCP_NAMESPACE_COLLISION','The owned MCP public namespace is already configured');
}

export function ownedMcpResult(result){
 requireValue(typeof result?.success==='boolean'&&Array.isArray(result.contentItems),'CODEX_TOOL_RESULT','Owned tool returned an invalid result');
 const content=result.contentItems.map(item=>{
  if(item.type==='inputText'&&typeof item.text==='string')return {type:'text',text:item.text};
  if(item.type==='inputImage'&&typeof item.imageUrl==='string'){
   const match=/^data:(image\/[a-z0-9.+-]+);base64,([A-Za-z0-9+/=]+)$/.exec(item.imageUrl);
   if(match)return {type:'image',mimeType:match[1],data:match[2]};
  }
  requireValue(false,'CODEX_TOOL_RESULT','Owned tool returned an unsupported content item');
 });
 return {content,isError:!result.success};
}

/** Native MCP transport for the existing per-session brokers, not an executor. */
export async function createOwnedToolMcp({tools,call,nodeBinary=process.execPath,configuration={}}) {
 const originalMode=codeModeConfiguration(configuration);
 const directMode={...originalMode,direct_only_tool_namespaces:[...(originalMode.direct_only_tool_namespaces??[])]};
 for(const namespace of ownedModelNamespaces)if(!directMode.direct_only_tool_namespaces.includes(namespace))directMode.direct_only_tool_namespaces.push(namespace);
 // A whole inline table also preserves an existing boolean feature setting;
 // dotted assignment alone could replace that boolean and lose its value.
 const directOverride='features.code_mode={'+Object.entries(directMode).map(([key,value])=>`${key}=${JSON.stringify(value)}`).join(',')+'}';
  const definitions=new Map(tools.map(tool=>[tool.name,tool]));
  requireValue(definitions.size===tools.length,'CODEX_TOOL_DUPLICATE','Owned MCP tools must have unique names');
  const path='/'+randomBytes(32).toString('hex'),namespace=OWNED_MCP_NAMESPACE;
  const jobs=new Set(),owners=new Set();let closing=false,closed=false,closingOperation,stopped,failure,fail;
  const failed=new Promise((_,reject)=>{fail=reject;});
  // Failure is inspected before launch and raced against the active turn below.
  failed.catch(()=>{});
  const revoke=()=>{closing=true;for(const response of owners)response.end(JSON.stringify({revoked:true}));owners.clear();};
  const fatal=error=>{failure??=error;revoke();fail(failure);};
  const server=createServer(async(req,res)=>{
    if(req.method!=='POST'||req.url!==path){res.writeHead(403).end();return;}
    if(closing){res.writeHead(410).end();return;}
    let owner=false;
    res.once('close',()=>{
      if(owner){owners.delete(res);if(!closing)fatal(Object.assign(new Error('Owned MCP owner channel was lost'),{code:'CODEX_MCP_OWNER_LOST'}));return;}
      if(!res.writableFinished&&!closing)fatal(Object.assign(new Error('An owned MCP response was cancelled or disconnected'),{code:'CODEX_MCP_DELIVERY_LOST'}));
    });
    let operation;
    try{
      const chunks=[];let size=0;
      for await(const chunk of req){size+=chunk.length;requireValue(size<=2*1024*1024,'CODEX_TOOL_INPUT_LIMIT','Owned MCP request exceeds its bound');chunks.push(chunk);}
      const message=JSON.parse(Buffer.concat(chunks));
      requireValue(!closing,'CODEX_SESSION_CLOSED','Owned MCP request was revoked while reading');
      if(message.method==='owner/wait'){
        owner=true;owners.add(res);res.setHeader('content-type','application/json');return;
      }
      if(message.method==='tools/list'){
        res.setHeader('content-type','application/json');res.end(JSON.stringify({tools}));return;
      }
      requireValue(message.method==='tools/call','CODEX_TOOL_DENIED','Unknown owned MCP operation');
      const definition=definitions.get(message.params?.name);
      requireValue(definition,'CODEX_TOOL_DENIED','Tool is outside this session catalog');
      // Native tool schemas may use full JSON Schema (including oneOf). Their
      // existing brokers own argument validation; the finite Workflow schema
      // vocabulary must not reject a legitimate native tool contract.
      requireValue(message.params.arguments&&typeof message.params.arguments==='object'&&!Array.isArray(message.params.arguments),
        'CODEX_TOOL_INPUT','Owned MCP arguments must be an object');
      operation=Promise.resolve().then(()=>{
        requireValue(!closing,'CODEX_SESSION_CLOSED','Owned MCP broker admission was revoked');
        const context=ownedMcpContext(message.params._meta);
        return call({tool:definition.name,arguments:message.params.arguments,
          callId:context?.call_id??'owned-mcp-'+randomUUID(),context});
      });
      jobs.add(operation);
      const result=await operation;
      ownedMcpResult(result);
      requireValue(!closing,'CODEX_SESSION_CLOSED','Owned MCP response was revoked');
      res.setHeader('content-type','application/json');res.end(JSON.stringify(result));
    }catch(error){if(!closing)fatal(error);if(!res.destroyed)res.writeHead(500).end(JSON.stringify({code:error.code??'CODEX_TOOL_FAILED'}));}
    finally{if(operation)jobs.delete(operation);}
  });
  server.on('error',fatal);
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const endpoint=`http://127.0.0.1:${server.address().port}${path}`;
  const args=[fileURLToPath(new URL('./owned-tool-mcp-stdio.mjs',import.meta.url))];
  return {
    namespace,failed,throwIfFailed(){if(failure)throw failure;},revoke,
    get configuration_overlay(){return {features:{code_mode:structuredClone(directMode)},mcp_servers:{[namespace]:{
      command:nodeBinary,args:[...args],env:{CODEX_WORKFLOW_TOOL_ENDPOINT:endpoint},enabled:true,
      environment_id:'local',supports_parallel_tool_calls:true,default_tools_approval_mode:'approve'}}};},
    qualifyConfiguration(configuration){
      const binding=serversFrom(configuration)[namespace];
      requireValue(object(binding)&&binding.command===nodeBinary
        &&Array.isArray(binding.args)&&binding.args.length===args.length&&binding.args.every((value,index)=>value===args[index])
        &&object(binding.env)&&binding.env.CODEX_WORKFLOW_TOOL_ENDPOINT===endpoint
        &&binding.enabled===true&&binding.supports_parallel_tool_calls===true&&binding.default_tools_approval_mode==='approve',
        'CODEX_MCP_BINDING','Effective owned MCP binding differs from this exact transport');
      requireValue(canonicalJSON(codeModeConfiguration(configuration))===canonicalJSON(directMode),
        'CODEX_MCP_DIRECT_BINDING','Effective direct owned tool configuration differs from this exact transport');
      return {owned_mcp_namespace:namespace,owned_mcp_binding_qualified:true,owned_mcp_direct_tools:true,
        owned_mcp_direct_namespaces:[...ownedModelNamespaces]};
    },
    overrides:[directOverride,`mcp_servers.${namespace}.command=${JSON.stringify(nodeBinary)}`,
      `mcp_servers.${namespace}.args=${JSON.stringify(args)}`,
      `mcp_servers.${namespace}.env.CODEX_WORKFLOW_TOOL_ENDPOINT=${JSON.stringify(endpoint)}`,
      `mcp_servers.${namespace}.supports_parallel_tool_calls=true`,
      // These tools already have exact Run grants and broker authorization.
      // Workspace commands still use the user's sandboxed command RPC policy.
      `mcp_servers.${namespace}.default_tools_approval_mode="approve"`],
    async close(){
      if(closed)return;if(closingOperation)return closingOperation;revoke();
      const operation=(async()=>{
        if(!stopped){stopped=new Promise((resolve,reject)=>server.close(error=>error?reject(error):resolve()));server.closeAllConnections();}
        await stopped;
        let timer;
        try{
          const outcomes=await Promise.race([Promise.allSettled([...jobs]),new Promise((_,reject)=>{
            timer=setTimeout(()=>reject(Object.assign(new Error('Owned MCP broker jobs did not stop'),{code:'CODEX_MCP_SHUTDOWN_UNCONFIRMED'})),5000);
          })]);
          const errors=outcomes.filter(item=>item.status==='rejected').map(item=>item.reason);
          if(errors.length)throw new AggregateError(errors,'Owned MCP broker jobs failed during shutdown');
          closed=true;
          if(failure)throw failure;
        }finally{clearTimeout(timer);}
      })();
      closingOperation=operation;try{return await operation;}finally{if(closingOperation===operation)closingOperation=null;}
    },
  };
}
