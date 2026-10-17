import {mkdir,readFile,writeFile,lstat,realpath} from 'node:fs/promises';
import {join,resolve,relative,isAbsolute,basename,sep} from 'node:path';
import {requireValue,noSymlinks} from '../workflow-paths.mjs';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {bindingContext} from '../workflow-execution-envelope.mjs';
import {projectNodeContext} from '../workflow-context-projection.mjs';

const owners=new Map();
const ownerKey=(runtime,runId,attemptId)=>`${resolve(runtime.runs.root)}\0${runId}\0${attemptId}`;

export function sharedHostRegion(workflow,nodeId){
  if(!Object.hasOwn(workflow,'nodes'))return null;
  requireValue(Array.isArray(workflow.nodes),'SHARED_HOST_POLICY','Declared workflow nodes must be an array');
  return workflow.nodes.find(node=>node.type==='parallel'&&node.workspace_policy?.kind==='host_tool_overlap'
    &&[node.workspace_policy.tool_node_id,node.workspace_policy.main_node_id].includes(nodeId));
}

export function validateSharedHostPolicy(workflow,parallel){
  const policy=parallel.workspace_policy;
  if(policy===undefined)return;
  requireValue(policy&&typeof policy==='object'&&!Array.isArray(policy)
    &&Object.keys(policy).every(key=>['kind','tool_node_id','main_node_id','read_inputs','semantic_rejection'].includes(key))
    &&policy.kind==='host_tool_overlap','SHARED_HOST_POLICY','Unknown parallel workspace policy');
  const tool=workflow.nodes.find(node=>node.id===policy.tool_node_id),main=workflow.nodes.find(node=>node.id===policy.main_node_id);
  requireValue(tool?.type==='tool'&&tool.executor?.kind==='tool'&&main?.type==='agent'
    &&main.executor?.kind==='main'&&main.executor.mode==='orchestration'&&main.access==='read_only'
    &&!main.completion_contract?.host_check&&!main.required_artifacts?.length&&!main.fanout
    &&parallel.failure_policy==='fail_fast','SHARED_HOST_POLICY','Overlap requires one Host tool and one read-only current Main with fail-fast join');
  const branches=workflow.edges.filter(edge=>edge.source===parallel.id);
  requireValue(branches.length===2&&branches.every(edge=>[tool.id,main.id].includes(edge.target))
    &&new Set(branches.map(edge=>edge.target)).size===2
    &&[tool.id,main.id].every(id=>{const out=workflow.edges.filter(edge=>edge.source===id);return out.length===1&&out[0].target===parallel.join_id&&(out[0].on??'success')==='success';}),
  'SHARED_HOST_POLICY','Overlap requires two direct branches and an all-required deterministic join');
  requireValue(Array.isArray(policy.read_inputs)&&policy.read_inputs.length>0&&policy.read_inputs.length<=16
    &&new Set(policy.read_inputs).size===policy.read_inputs.length
    &&policy.read_inputs.every(name=>typeof name==='string'&&/^[A-Za-z][A-Za-z0-9_-]{0,127}$/.test(name)&&Object.hasOwn(main.input_bindings??{},name)),
  'SHARED_HOST_POLICY','Overlap requires explicit bound source inputs');
  requireValue(main.outputs_schema?.properties?.accepted?.type==='boolean'&&(main.outputs_schema.required??[]).includes('accepted'),
    'SHARED_HOST_POLICY','Semantic overlap review requires an explicit accepted boolean');
  requireValue(policy.semantic_rejection===undefined||policy.semantic_rejection==='defer_to_join',
    'SHARED_HOST_POLICY','Unknown overlap semantic rejection policy');
  if(policy.semantic_rejection==='defer_to_join')requireValue((workflow.loops??[]).some(loop=>loop.review_context==='current_main'
    &&[parallel.id,tool.id,main.id,parallel.join_id].every(id=>loop.node_ids?.includes(id))),
  'SHARED_HOST_POLICY','Deferred rejection requires a current Main repair loop whose acceptance includes this exact source review');
  for(const other of workflow.nodes.filter(node=>node.type==='parallel'&&node!==parallel)){
    const visited=new Set(),todo=workflow.edges.filter(edge=>edge.source===other.id).map(edge=>edge.target);
    while(todo.length){const id=todo.pop();if(id===other.join_id||visited.has(id))continue;visited.add(id);todo.push(...workflow.edges.filter(edge=>edge.source===id).map(edge=>edge.target));}
    requireValue(!visited.has(parallel.id),'SHARED_HOST_POLICY','A Host overlap region cannot nest inside another parallel workspace');
  }
  requireValue(!workflow.nodes.some(node=>node!==parallel&&node.type==='parallel'&&node.workspace_policy?.kind==='host_tool_overlap'
    &&[node.workspace_policy.tool_node_id,node.workspace_policy.main_node_id].some(id=>[tool.id,main.id].includes(id))),
  'SHARED_HOST_POLICY','An overlap node cannot belong to multiple owners');
}

export function sharedHostProjection(state,workflow,nodeId){
  const region=sharedHostRegion(workflow,nodeId);
  if(!region||region.workspace_policy.main_node_id!==nodeId)return null;
  const node=state.nodes[region.workspace_policy.tool_node_id];
  const attempt=node?.attempts.find(item=>item.id===node.active_attempt_id);
  requireValue(attempt?.shared_host_projection,'SHARED_HOST_PROJECTION_MISSING','Main source projection must precede Host work');
  const projection=attempt.shared_host_projection;
  requireValue(projection.region_id===region.id&&projection.tool_attempt_id===attempt.id&&projection.main_node_id===nodeId,
    'SHARED_HOST_PROJECTION_IDENTITY','Source projection belongs to another exact Host attempt');
  return projection;
}

export function projectSharedHostInputs(state,workflow,nodeId,inputs){
  const projection=sharedHostProjection(state,workflow,nodeId);
  if(!projection)return inputs;
  const projected=structuredClone(inputs);
  for(const source of projection.sources){
    requireValue(digest(canonicalJSON(inputs[source.input]))===source.input_sha256,'SHARED_HOST_SOURCE_CHANGED','Main bound source changed after projection');
    projected[source.input]={...projected[source.input],path:source.path};
  }
  return projected;
}

/** Copy before launch; the Main and tool retain distinct whole-workspace audits. */
export async function prepareSharedHostProjection(runtime,runId,binding,region){
  const {record}=await runtime.authorizedExecution(runId,binding,()=>binding);
  const node=record.state.nodes[binding.node_id],attempt=node.attempts.find(item=>item.id===binding.attempt_id);
  if(attempt.shared_host_projection)return attempt.shared_host_projection;
  requireValue(!attempt.host_tool,'SHARED_HOST_PROJECTION_ORDER','Cannot project a source after the Host effect intent');
  const main=record.pins.root.workflow.nodes.find(item=>item.id===region.workspace_policy.main_node_id);
  const inputs=projectNodeContext(main,record.pins.root.workflow,bindingContext(record.state)).inputs;
  const workspace=join(runtime.runs.directory(runId),'shared-host-workspaces',binding.attempt_id);
  await mkdir(join(runtime.runs.directory(runId),'shared-host-workspaces'),{recursive:true});
  await noSymlinks(join(runtime.runs.directory(runId),'shared-host-workspaces'));
  await mkdir(workspace,{recursive:false});
  await noSymlinks(workspace);
  const root=await realpath(record.state.permissions.workspace),sources=[];
  for(const name of region.workspace_policy.read_inputs){
    const input=inputs[name];
    requireValue(input&&typeof input==='object'&&!Array.isArray(input)&&typeof input.path==='string'&&isAbsolute(input.path),
      'SHARED_HOST_SOURCE','Projected input requires an absolute source path');
    const sourcePath=resolve(input.path),subpath=relative(root,sourcePath);
    requireValue(subpath&&subpath!=='..'&&!subpath.startsWith('..'+sep)&&!isAbsolute(subpath),'SHARED_HOST_SOURCE_SCOPE','Projected source is outside the Run workspace');
    let parent=root;
    for(const part of subpath.split(/[\\/]/)){parent=join(parent,part);requireValue(!(await lstat(parent)).isSymbolicLink(),'SHARED_HOST_SOURCE_LINK','Projected source contains a link');}
    const stat=await lstat(sourcePath);
    requireValue(stat.isFile()&&stat.size<=16*1024*1024,'SHARED_HOST_SOURCE_LIMIT','Projected source must be a bounded regular file');
    const bytes=await readFile(sourcePath),sha256=digest(bytes);
    if(Object.hasOwn(input,'text'))requireValue(typeof input.text==='string'&&Buffer.from(input.text).equals(bytes),'SHARED_HOST_SOURCE_TEXT','Source text differs from the exact file bytes');
    const directory=join(workspace,name);await mkdir(directory);
    const path=join(directory,basename(sourcePath));await writeFile(path,bytes,{flag:'wx'});
    requireValue(digest(await readFile(sourcePath))===sha256,'SHARED_HOST_SOURCE_CHANGED','Source changed while preparing its immutable projection');
    sources.push({input:name,input_sha256:digest(canonicalJSON(input)),source_path:sourcePath,path,sha256,bytes:bytes.length});
  }
  const projection={region_id:region.id,tool_attempt_id:binding.attempt_id,main_node_id:main.id,workspace,sources};
  await runtime.authorizedExecution(runId,binding,()=>binding);
  await runtime.transition(runId,'shared_host_projection',(state)=>{
    const current=state.nodes[binding.node_id],owned=current.attempts.find(item=>item.id===binding.attempt_id);
    requireValue(state.status==='running'&&current.active_attempt_id===binding.attempt_id&&['claimed','running'].includes(owned?.status),
      'SHARED_HOST_PROJECTION_IDENTITY','Projection lost exact attempt ownership');
    requireValue(state.control_hash===digest(binding.control_token)&&owned.lease_hash===digest(binding.lease_token),
      'SHARED_HOST_PROJECTION_IDENTITY','Projection lost its exact controller or lease before publication');
    requireValue(!owned.host_tool&&!owned.shared_host_projection,'SHARED_HOST_PROJECTION_ORDER','Projection must have one owner before the effect intent');
    owned.shared_host_projection=projection;
  });
  return projection;
}

export async function verifySharedHostProjection(projection){
  await noSymlinks(projection.workspace);
  for(const source of projection.sources){
    await noSymlinks(source.path);const stat=await lstat(source.path);
    requireValue(stat.isFile()&&stat.size===source.bytes&&digest(await readFile(source.path))===source.sha256,
      'SHARED_HOST_SOURCE_CORRUPT','Immutable source projection differs from its Host-owned identity');
  }
}

export function requireSharedHostProjectionSnapshot(projection,snapshot){
  for(const source of projection.sources){
    const path=relative(projection.workspace,source.path).replaceAll('\\','/');
    requireValue(snapshot.get(path)===source.sha256,'SHARED_HOST_SOURCE_CORRUPT','The handoff snapshot must retain the exact Host source identity');
  }
}

// Promise ownership is process-local. Durable tool claims/receipts are the join
// authority; a new process never turns an absent live owner into another launch.
export function startSharedHostWork(runtime,runId,binding,execute){
  const key=ownerKey(runtime,runId,binding.attempt_id);
  requireValue(!owners.has(key),'SHARED_HOST_DUPLICATE','The exact Host attempt already has a live join owner');
  const entry={binding:{...binding},settled:false,failed:false,result:null,error:null,promise:null};owners.set(key,entry);
  entry.promise=Promise.resolve().then(execute).then(result=>{entry.result=result;entry.settled=true;return result;},error=>{entry.error=error;entry.failed=true;entry.settled=true;return null;});
  return entry;
}
export async function joinSharedHostWork(runtime,runId,binding){
  const entry=owners.get(ownerKey(runtime,runId,binding.attempt_id));
  requireValue(entry&&entry.binding.node_id===binding.node_id,'HOST_TOOL_RECONCILIATION_REQUIRED','The exact concurrent Host attempt has no live owner; reconcile its durable effect without replay');
  await entry.promise;
  if(entry.failed)throw entry.error;
  return entry.result;
}
export function hasSharedHostWorkOwner(runtime,runId,attemptId){return owners.has(ownerKey(runtime,runId,attemptId));}
export function releaseSettledSharedHostOwners(runtime,runId,state){
  for(const node of Object.values(state.nodes))for(const attempt of node.attempts){
    const key=ownerKey(runtime,runId,attempt.id),entry=owners.get(key);
    if(entry?.settled&&!entry.failed&&!entry.result?.error&&['succeeded','failed','cancelled'].includes(attempt.status))owners.delete(key);
  }
}
