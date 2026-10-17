import {createHash} from 'node:crypto';
import {appendFile, lstat, open, readFile, realpath} from 'node:fs/promises';
import {basename, delimiter, dirname, isAbsolute, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {isDeepStrictEqual} from 'node:util';

const modulePath=fileURLToPath(import.meta.url);
const selected=['search_query','open','find'];
const other=['image_query','click','screenshot','finance','weather','sports','time'];
const fields=new Set([...selected,...other,'response_length']);
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const requireValue=(condition,message)=>{
  if(!condition)throw Object.assign(new Error(message),{code:'CODEX_WEB_RESPONSE_DEFAULT'});
};

function safeReference(value){
  if(typeof value!=='string')return null;
  if(!/^https?:\/\//i.test(value))return value;
  const url=new URL(value);url.username='';url.password='';
  for(const key of [...url.searchParams.keys()])if(/token|secret|password|auth|api[_-]?key|signature/i.test(key))url.searchParams.set(key,'[redacted]');
  return url.toString();
}

// The output preserves the complete tool input; the audit retains only selected web arguments.
export function decideWebResponseDefault(request){
  requireValue(request&&request.hook_event_name==='PreToolUse','Unexpected web hook event');
  const input=request.tool_input;
  requireValue(input&&typeof input==='object'&&!Array.isArray(input),'Web hook tool_input must be an object');
  const explicit=Object.hasOwn(input,'response_length');
  const active=selected.some(key=>Array.isArray(input[key])&&input[key].length);
  const mixed=other.some(key=>Object.hasOwn(input,key));
  const unknown=Object.keys(input).some(key=>!fields.has(key));
  // The public web interface requires medium/long for four-query batches.
  const broadSearch=Array.isArray(input.search_query)&&input.search_query.length>3;
  const rewrite=request.tool_name==='webrun'&&!explicit&&active&&!mixed&&!unknown&&!broadSearch;
  const reason=request.tool_name!=='webrun'?'other_tool':explicit?'explicit_response_length':!active?'no_selected_operation':mixed?'mixed_operations':unknown?'unknown_field':broadSearch?'multi_query_batch':'default_short';
  const length=explicit&&['short','medium','long',null].includes(input.response_length)?input.response_length:undefined;
  const audit={session_id:request.session_id,turn_id:request.turn_id,tool_use_id:request.tool_use_id,
    tool_name:request.tool_name,response_length_present:explicit,
    ...(length!==undefined?{response_length:length}:explicit?{response_length_type:typeof input.response_length}:{}),
    decision:reason,rewritten:rewrite,...(rewrite?{effective_response_length:'short'}:{})};
  if(request.tool_name==='webrun')for(const key of selected)if(Array.isArray(input[key]))audit[key]=input[key].map(item=>{
    requireValue(item&&typeof item==='object'&&!Array.isArray(item),'Invalid selected web operation');
    return key==='search_query'?{q:typeof item.q==='string'?item.q:null}:
      key==='open'?{ref_id:safeReference(item.ref_id)}:
        {ref_id:safeReference(item.ref_id),pattern:typeof item.pattern==='string'?item.pattern:null};
  });
  return {audit,output:rewrite?{hookSpecificOutput:{hookEventName:'PreToolUse',permissionDecision:'allow',
    updatedInput:{...input,response_length:'short'}}}:{}};
}

export function webResponseHookCommand({nodePath,scriptPath,auditPath}){
  const name=basename(nodePath);
  requireValue(/^[A-Za-z0-9_][A-Za-z0-9_.-]*$/.test(name),'Invalid web hook executable basename');
  requireValue([scriptPath,auditPath].every(value=>isAbsolute(value)),'Invalid web hook runtime path');
  const encoded=value=>Buffer.from(value).toString('base64');
  // Only fixed JavaScript and base64 enter the shell string: no path, query, $, or backtick interpolation.
  const bootstrap=`import(Buffer.from('${encoded(pathToFileURL(scriptPath).href)}','base64').toString()).then(m=>m.runWebHook(Buffer.from('${encoded(auditPath)}','base64').toString())).catch(e=>{process.stderr.write('CODEX_WEB_RESPONSE_DEFAULT: '+e.message+'\\n');process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'PreToolUse',permissionDecision:'deny',permissionDecisionReason:'Web response default hook failed: '+e.message}})+'\\n');})`;
  return `${name} -e "${bootstrap}"`;
}

function listedHooks(value,cwd){
  requireValue(Array.isArray(value?.data)&&value.data.length===1,'Invalid web hook inventory');
  const entry=value.data[0];
  requireValue(resolve(entry.cwd)===resolve(cwd)&&Array.isArray(entry.hooks)&&Array.isArray(entry.errors)&&!entry.errors.length
    &&Array.isArray(entry.warnings)&&!entry.warnings.length,'Web hook inventory has errors or warnings');
  return entry.hooks;
}

// Only metadata RPCs run here. The caller uses the returned overrides when opening its execution client.
export async function prepareCodexWebResponseDefault({binary,home,cwd,auditPath,clientFactory,clientOptions={},overrides=[]}){
  requireValue([binary,home,cwd,auditPath].every(value=>typeof value==='string'&&isAbsolute(value)), 'Web default preparation requires absolute runtime paths');
  requireValue(typeof clientFactory==='function'&&Array.isArray(overrides)&&overrides.every(value=>typeof value==='string'),'Web default preparation requires its ordinary metadata client');
  requireValue(!overrides.some(value=>/^hooks(?:\.|=)/.test(value)),'Existing SessionFlags hook overrides require explicit composition before web preparation');
  const scriptPath=await realpath(modulePath),nodePath=await realpath(process.execPath);
  const scriptSha256=digest(await readFile(scriptPath)),nodeSha256=digest(await readFile(nodePath));
  const environment=clientOptions.env??process.env;
  const pathKey=process.platform==='win32'?(Object.keys(environment).find(key=>key.toLowerCase()==='path')??'PATH'):'PATH';
  const environmentOverlay={[pathKey]:dirname(nodePath)+delimiter+(environment[pathKey]??'')};
  const command=webResponseHookCommand({nodePath,scriptPath,auditPath});
  const declaration=`hooks.PreToolUse=[{matcher="^webrun$",hooks=[{type="command",command=${JSON.stringify(command)},async=false,timeout=10}]}]`;
  const discoveryOverrides=[...overrides,'features.hooks=true',declaration];
  async function inventory(values){
    const client=await clientFactory(binary,{...clientOptions,env:{...environment,...environmentOverlay},home,cwd,overrides:values});
    let primary;
    try{
      await client.call('initialize',{clientInfo:{name:'codex_workflow_web_default',version:'1.2'},capabilities:{experimentalApi:true}});
      client.initialized();
      return listedHooks(await client.call('hooks/list',{cwds:[cwd]}),cwd);
    }catch(error){primary=error;throw error;}
    finally{
      try{await client.close();}catch(error){throw primary?new AggregateError([primary,error],'Web hook metadata and client cleanup failed'):error;}
    }
  }
  const baseline=await inventory(overrides),discovered=await inventory(discoveryOverrides);
  const own=discovered.filter(h=>h.source==='sessionFlags'&&h.eventName==='preToolUse'&&h.handlerType==='command'&&h.command===command&&h.matcher==='^webrun$');
  requireValue(own.length===1,'Scoped web hook was not uniquely discovered');
  for(const original of baseline){
    const matches=discovered.filter(h=>h.key===original.key);
    requireValue(matches.length===1&&isDeepStrictEqual(original,matches[0]),'Scoped web hook altered an existing hook');
  }
  requireValue(discovered.length===baseline.length+1,'Scoped web hook changed the normal inventory');
  const hook=own[0];
  requireValue(hook.enabled===true&&typeof hook.key==='string'&&/^sha256:[a-f0-9]{64}$/.test(hook.currentHash),'Invalid scoped web hook identity');
  const trustedOverrides=[...discoveryOverrides,`hooks.state={${JSON.stringify(hook.key)}={enabled=true,trusted_hash=${JSON.stringify(hook.currentHash)}}}`];
  const audit=await open(auditPath,'wx');await audit.close();
  return {overrides:trustedOverrides,audit_path:auditPath,audit_initial_sha256:digest(Buffer.alloc(0)),script_path:scriptPath,
    script_sha256:scriptSha256,node_path:nodePath,node_sha256:nodeSha256,environment_overlay:environmentOverlay,
    configuration_overlay:{features:{hooks:true},hooks:{PreToolUse:[{matcher:'^webrun$',hooks:[{type:'command',command,timeout:10,async:false}]}],
      state:{[hook.key]:{enabled:true,trusted_hash:hook.currentHash}}}},
    own_hook:{key:hook.key,current_hash:hook.currentHash,matcher:'^webrun$',source:'sessionFlags'},
    normal_hooks_preserved:baseline.map(h=>({key:h.key,current_hash:h.currentHash,trust_status:h.trustStatus,enabled:h.enabled})),
    qualification:'metadata_discovered_preservation_checked_execution_trust_pending'};
}

export async function runWebHook(auditPath){
  requireValue(typeof auditPath==='string'&&isAbsolute(auditPath),'Invalid web hook audit path');
  const info=await lstat(auditPath);requireValue(info.isFile()&&!info.isSymbolicLink(),'Web hook audit must be a regular owned file');
  let stdin='';for await(const chunk of process.stdin){stdin+=chunk;requireValue(Buffer.byteLength(stdin)<=1024*1024,'Web hook stdin exceeded 1 MiB');}
  let request;try{request=JSON.parse(stdin);}catch{requireValue(false,'Web hook stdin is invalid JSON');}
  const {audit,output}=decideWebResponseDefault(request);
  await appendFile(auditPath,JSON.stringify(audit)+'\n');
  process.stdout.write(JSON.stringify(output)+'\n');
}

if(process.argv[1]&&resolve(process.argv[1])===resolve(modulePath)){
  try{requireValue(process.argv.length===4&&process.argv[2]==='--hook','Invalid web hook invocation');await runWebHook(process.argv[3]);}
  catch(error){
    process.stderr.write(`${error.code??'CODEX_WEB_RESPONSE_DEFAULT'}: ${error.message}\n`);
    process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'PreToolUse',permissionDecision:'deny',permissionDecisionReason:'Web response default hook failed: '+error.message}})+'\n');
  }
}
