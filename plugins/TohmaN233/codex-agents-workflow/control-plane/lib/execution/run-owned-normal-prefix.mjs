import {mkdtemp,mkdir,open,readFile,rm,realpath} from 'node:fs/promises';
import {join,resolve,relative,isAbsolute,dirname} from 'node:path';
import {randomUUID} from 'node:crypto';
import {ensureDirectory,statNoSymlinks,requireValue} from '../workflow-paths.mjs';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';

const homes=new WeakMap(),prefixes=new WeakMap(),MAX_CONFIG=2*1024*1024,MAX_ROLLOUT=8*1024*1024;
const within=(root,path)=>{const r=relative(root,path);return r===''||(!r.startsWith('..')&&!isAbsolute(r));};
const identity=stat=>({dev:stat.dev,ino:stat.ino});
const same=(a,b)=>a.dev===b.dev&&a.ino===b.ino;
function normalConfig(value,depth=0,key=''){
  requireValue(depth<=16,'CODEX_PREFIX_CONFIG','Normal configuration nesting is unbounded');
  if(value===null||value===undefined)return undefined;
  requireValue(typeof value!=='string'||(!/^(?:api_key|access_token|refresh_token|authorization|password|cookie|secret|auth_token)$/i.test(key)
    && !(depth>1&&/(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)/i.test(key))),
    'CODEX_PREFIX_CONFIG_SECRET','Private normal configuration cannot persist credentials',{configuration_key:key.slice(0,128)});
  if(Array.isArray(value))return value.map(v=>{const item=normalConfig(v,depth+1);requireValue(item!==undefined,'CODEX_PREFIX_CONFIG','Null array configuration is not portable');return item;});
  if(typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,normalConfig(v,depth+1,k)]).filter(([,v])=>v!==undefined));
  requireValue(typeof value==='string'||typeof value==='boolean'||typeof value==='number'&&Number.isFinite(value),
    'CODEX_PREFIX_CONFIG','Normal configuration has unsupported values');return value;
}
function nullablePaths(value,path=[],result=new Set()){
  if(value===null)result.add(canonicalJSON(path));
  else if(value&&typeof value==='object')for(const [key,item]of Object.entries(value))nullablePaths(item,[...path,key],result);
  return result;
}
const toml=value=>Array.isArray(value)?`[${value.map(toml).join(', ')}]`:typeof value==='object'
  ?`{ ${Object.entries(value).map(([k,v])=>`${JSON.stringify(k)} = ${toml(v)}`).join(', ')} }`:JSON.stringify(value);
async function exclusive(path,bytes){const file=await open(path,'wx',0o600);try{await file.writeFile(bytes);await file.sync();}finally{await file.close();}}
async function bounded(path,limit){const {stat}=await statNoSymlinks(path);requireValue(stat.isFile()&&stat.nlink===1&&stat.size<=limit,'CODEX_PREFIX_FILE','Prefix file must be a bounded owned regular file');const bytes=await readFile(path);requireValue(bytes.length<=limit,'CODEX_PREFIX_FILE','Prefix file grew beyond its bound');return bytes;}
async function owned(state){
  const {stat}=await statNoSymlinks(state.home);requireValue(stat.isDirectory()&&same(identity(stat),state.identity),'CODEX_PREFIX_OWNER','Private prefix directory ownership changed');
  requireValue(digest(await bounded(join(state.home,'owner.json'),4096))===state.owner_hash,'CODEX_PREFIX_OWNER','Private prefix owner changed');
  requireValue(digest(await bounded(join(state.home,'config.toml'),MAX_CONFIG))===state.config_hash,'CODEX_PREFIX_CONFIG_CHANGED','Private prefix configuration changed');
}

// This store holds exactly one setup-only source, never a user/global thread.
// Ordinary resource paths remain reads; only known state/storage roots change.
export async function createRunOwnedNormalHome({parent,owner,cwd,normalHome,configuration,onOwned}){
  requireValue(typeof owner?.run_id==='string'&&owner.run_id.length>0&&owner.run_id.length<=128
    &&typeof owner?.attempt_id==='string'&&owner.attempt_id.length>0&&owner.attempt_id.length<=128,
    'CODEX_PREFIX_OWNER','Prefix needs exact Run/attempt ownership');
  requireValue(configuration?.config&&typeof configuration.config==='object'&&!Array.isArray(configuration.config),'CODEX_PREFIX_CONFIG','Effective normal configuration is required');
  const config=normalConfig(configuration.config);
  requireValue(Buffer.byteLength(canonicalJSON(config))<=MAX_CONFIG,'CODEX_PREFIX_CONFIG','Effective normal configuration is too large');
  await ensureDirectory(parent);const actualParent=await realpath(parent),actualCwd=await realpath(cwd),actualNormal=await realpath(normalHome);
  requireValue(!within(actualCwd,actualParent),'CODEX_PREFIX_OWNER','Prefix storage must be outside setup workspace');
  const home=await mkdtemp(join(actualParent,'normal-prefix-')),token=randomUUID();
  const projected={...config,sqlite_home:join(home,'sqlite'),log_dir:join(home,'logs'),
    model_catalog_json:config.model_catalog_json?resolve(cwd,config.model_catalog_json):join(actualNormal,'models_cache.json')};
  const ownerBytes=canonicalJSON({schema_version:1,token,pid:process.pid,owner,created_at:new Date().toISOString()});
  const configBytes=Object.entries(projected).map(([k,v])=>`${JSON.stringify(k)} = ${toml(v)}`).join('\n')+'\n';
  const handle=Object.freeze({}),state={home,parent:actualParent,token,owner_hash:digest(ownerBytes),config_hash:digest(configBytes),projected,nullable_paths:nullablePaths(configuration.config),children:new Set(),closed:false,closing:false};
  state.identity=identity((await statNoSymlinks(home)).stat);homes.set(handle,state);await onOwned?.(handle);
  // Retain partial owned evidence on write failure; no guessed cleanup target.
  await exclusive(join(home,'owner.json'),ownerBytes);await mkdir(projected.sqlite_home);await mkdir(projected.log_dir);await exclusive(join(home,'config.toml'),configBytes);
  return handle;
}
export function normalPrefixHome(handle){const state=homes.get(handle);requireValue(state&&!state.closed,'CODEX_PREFIX_HANDLE','Private normal home is not a live Host handle');return {home:state.home,sqlite_home:state.projected.sqlite_home,config_hash:state.config_hash};}
function executionOverlay(value){
  const object=item=>item&&typeof item==='object'&&!Array.isArray(item),keys=(item,allowed)=>object(item)&&Object.keys(item).every(key=>allowed.includes(key));
  const binding=value?.mcp_servers?.codex_agents_workflow_owned,mode=value?.features?.code_mode;
  requireValue(keys(value,['model_catalog_json','features','mcp_servers','hooks'])&&typeof value.model_catalog_json==='string'&&isAbsolute(value.model_catalog_json)
    &&keys(value.features,['code_mode_host','code_mode','standalone_web_search','hooks'])&&value.features.code_mode_host===true
    &&(value.features.standalone_web_search===undefined||value.features.standalone_web_search===true)
    &&keys(mode,['enabled','default_exec_yield_time_ms','experimental_show_cell_overhead','tool_input_schema_max_bytes','direct_only_tool_namespaces','excluded_tool_namespaces'])
    &&Object.values(mode).every(item=>typeof item==='boolean'||typeof item==='number'&&Number.isFinite(item)||Array.isArray(item)&&item.every(entry=>typeof entry==='string'))
    &&keys(value.mcp_servers,['codex_agents_workflow_owned'])
    &&keys(binding,['command','args','env','environment_id','enabled','supports_parallel_tool_calls','default_tools_approval_mode'])
    &&typeof binding.command==='string'&&isAbsolute(binding.command)&&Array.isArray(binding.args)&&binding.args.every(item=>typeof item==='string')
    &&keys(binding.env,['CODEX_WORKFLOW_TOOL_ENDPOINT'])&&typeof binding.env.CODEX_WORKFLOW_TOOL_ENDPOINT==='string'
    &&binding.environment_id==='local'&&binding.enabled===true&&binding.supports_parallel_tool_calls===true&&binding.default_tools_approval_mode==='approve',
    'CODEX_PREFIX_CONFIG_OVERLAY','Private execution overlay is outside its exact catalog and owned MCP declarations');
  if(value.hooks){
    const declaration=value.hooks.PreToolUse?.[0],handler=declaration?.hooks?.[0],states=Object.values(value.hooks.state??{});
    requireValue(value.features.hooks===true&&keys(value.hooks,['PreToolUse','state'])&&Array.isArray(value.hooks.PreToolUse)&&value.hooks.PreToolUse.length===1
      &&keys(declaration,['matcher','hooks'])&&declaration.matcher==='^webrun$'&&Array.isArray(declaration.hooks)&&declaration.hooks.length===1
      &&keys(handler,['type','command','timeout','async'])&&handler.type==='command'&&typeof handler.command==='string'&&handler.command.length>0
      &&handler.timeout===10&&handler.async===false&&object(value.hooks.state)&&states.length===1
      &&keys(states[0],['enabled','trusted_hash'])&&states[0].enabled===true&&/^sha256:[a-f0-9]{64}$/.test(states[0].trusted_hash),
      'CODEX_PREFIX_CONFIG_OVERLAY','Private web default is outside its exact scoped hook declaration');
  }else requireValue(value.features.hooks===undefined,'CODEX_PREFIX_CONFIG_OVERLAY','Hook feature requires its scoped declaration');
  return normalConfig(value);
}
export async function qualifyNormalPrefixHome(handle,configuration,{overlay}={}){
  const state=homes.get(handle);requireValue(state&&!state.closed,'CODEX_PREFIX_HANDLE','Unknown private normal home');await owned(state);
  const actual=normalConfig(configuration?.config);
  let expected=state.projected;
  if(overlay){
    const declared=executionOverlay(overlay);
    requireValue(!Object.hasOwn(expected.mcp_servers??{},'codex_agents_workflow_owned'),'CODEX_PREFIX_CONFIG_OVERLAY','Private source already contains the owned MCP namespace');
    // config/read adds these exact local stdio defaults in the qualified binary.
    // Inspect raw keys before null normalization so unknown fields cannot disappear.
    const binding=configuration?.config?.mcp_servers?.codex_agents_workflow_owned,mode=configuration?.config?.features?.code_mode;
    requireValue(binding&&Object.keys(binding).every(key=>Object.hasOwn(declared.mcp_servers.codex_agents_workflow_owned,key)||key==='tool_timeout_sec')
      &&mode&&Object.keys(mode).every(key=>Object.hasOwn(declared.features.code_mode,key)),
      'CODEX_PREFIX_CONFIG_UNCONTROLLED','Private execution added unknown owned MCP or code-mode configuration fields');
    const executionNullDefaults=new Set([canonicalJSON(['mcp_servers','codex_agents_workflow_owned','tool_timeout_sec']),canonicalJSON(['features','network_proxy']),
      ...(declared.hooks?['commandWindows','statusMessage'].map(key=>canonicalJSON(['hooks','PreToolUse','0','hooks','0',key])):[])]);
    requireValue([...nullablePaths(configuration.config)].every(path=>state.nullable_paths.has(path)||executionNullDefaults.has(path)),
      'CODEX_PREFIX_CONFIG_UNCONTROLLED','Private execution added unknown nullable configuration fields');
    expected={...expected,model_catalog_json:declared.model_catalog_json,features:{...expected.features,...declared.features},mcp_servers:{...expected.mcp_servers,...declared.mcp_servers},
      ...(declared.hooks?{hooks:{...expected.hooks,...declared.hooks,state:{...expected.hooks?.state,...declared.hooks.state}}}:{})};
  }
  requireValue(canonicalJSON(actual)===canonicalJSON(expected),'CODEX_PREFIX_CONFIG_UNCONTROLLED','Private source changed effective normal configuration or storage roots');
}
export async function sealNormalPrefix(handle,{path,thread_id,turn_id,model,effort,usage,selection,command_declarations_sha256}){
  const state=homes.get(handle);requireValue(state&&!state.closed,'CODEX_PREFIX_HANDLE','Unknown private normal home');await owned(state);
  requireValue(typeof path==='string'&&isAbsolute(path)&&within(state.home,resolve(path))&&typeof thread_id==='string'&&thread_id.length>0
    &&typeof turn_id==='string'&&turn_id.length>0&&typeof model==='string'&&typeof effort==='string'
    &&selection?.model===model&&selection?.effort===effort&&/^[a-f0-9]{64}$/.test(command_declarations_sha256),
    'CODEX_PREFIX_SOURCE','Completed setup needs its exact private rollout and thread/turn/model identity');
  const bytes=await bounded(path,MAX_ROLLOUT),prefix=Object.freeze({});
  prefixes.set(prefix,{state,path:resolve(path),sha256:digest(bytes),bytes:bytes.length,thread_id,turn_id,model,effort,
    selection:structuredClone(selection),command_declarations_sha256,usage:structuredClone(usage)});return prefix;
}
export async function acquireNormalPrefix(prefix){
  const data=prefixes.get(prefix);requireValue(data&&!data.state.closed&&!data.state.closing,'CODEX_PREFIX_HANDLE','Prefix must be a live trusted in-process handle');
  const lease=Object.freeze({});data.state.children.add(lease);
  try{await owned(data.state);const bytes=await bounded(data.path,MAX_ROLLOUT);
    requireValue(bytes.length===data.bytes&&digest(bytes)===data.sha256,'CODEX_PREFIX_CHANGED','Completed private prefix changed');}
  catch(error){data.state.children.delete(lease);throw error;}
  return {home:data.state.home,sqlite_home:data.state.projected.sqlite_home,selection:structuredClone(data.selection),
    source_path:data.path,source_thread_id:data.thread_id,last_turn_id:data.turn_id,rollout_sha256:data.sha256,rollout_bytes:data.bytes,command_declarations_sha256:data.command_declarations_sha256,
    async verify(model,effort){
      requireValue(data.state.children.has(lease)&&!data.state.closed,'CODEX_PREFIX_HANDLE','Prefix child no longer owns its backing library');
      requireValue(data.model===model&&data.effort===effort,'CODEX_PREFIX_MODEL','Prefix and worker must select the same exact model/effort');
      await owned(data.state);const bytes=await bounded(data.path,MAX_ROLLOUT);
      requireValue(bytes.length===data.bytes&&digest(bytes)===data.sha256,'CODEX_PREFIX_CHANGED','Completed private prefix changed');
    },release(){data.state.children.delete(lease);}};
}
export function normalPrefixReceipt(prefix){
  const data=prefixes.get(prefix);requireValue(data&&!data.state.closed,'CODEX_PREFIX_HANDLE','Prefix must be a live trusted in-process handle');
  return {source_path:data.path,source_thread_id:data.thread_id,last_turn_id:data.turn_id,model:data.model,effort:data.effort,
    rollout_sha256:data.sha256,rollout_bytes:data.bytes,command_declarations_sha256:data.command_declarations_sha256,
    backing_store:'run_owned_temporary_normal_library'};
}
export async function closeNormalPrefixHome(handle){
  const state=homes.get(handle);requireValue(state,'CODEX_PREFIX_HANDLE','Unknown private normal home');if(state.closed)return;
  state.closing=true;requireValue(state.children.size===0,'CODEX_PREFIX_CHILD_ACTIVE','Close all prefix workers before releasing their private source');await owned(state);
  requireValue(dirname(state.home)===state.parent,'CODEX_PREFIX_OWNER','Private source is not the exact owned direct child');
  await rm(state.home,{recursive:true,maxRetries:3,retryDelay:100});state.closed=true;
}
