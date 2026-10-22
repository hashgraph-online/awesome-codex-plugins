import {lstat,readdir,open,readFile,mkdir,unlink} from 'node:fs/promises';
import {constants} from 'node:fs';
import {join,resolve,relative,dirname} from 'node:path';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {requireValue,noSymlinks} from '../workflow-paths.mjs';
import {pathBoundaryContains} from '../workflow-bindings.mjs';
import {nodePermissions} from '../workflow-execution-envelope.mjs';
import {assignedFanoutWritePaths,assertFanoutWriteScopesDisjoint} from './fanout-input-projection.mjs';
import {readNativeTaskProjection} from './node-input-materials.mjs';
import {readStartedEvent} from '../workflow-events.mjs';
import {retireOwnedFile} from '../owned-file-retirement.mjs';

const MAX_ENTRIES=20000,MAX_BYTES=2*1024*1024*1024;
const identical=(a,b)=>['dev','ino','mode','nlink','size','mtimeNs','ctimeNs','birthtimeNs'].every(key=>a[key]===b[key]);
const slash=path=>path.replaceAll('\\','/');
const same=(a,b)=>canonicalJSON(a??null)===canonicalJSON(b??null);
const rootKey=path=>process.platform==='win32'?resolve(path).toLowerCase():resolve(path);
const fail=(condition,code,message,details)=>requireValue(condition,`NATIVE_SPAN_${code}`,message,details);

// Dispatch intent alone does not release work. A published packet, batch or
// receipt remains uncertain even when no child acknowledgement was recorded.
export function nativePreparationUnreleased(attempt){
  return Boolean(attempt?.dispatch)&&!attempt.dispatch.receipt
    &&!Object.keys(attempt.native_agents??{}).length&&!Object.keys(attempt.native_pending_spawns??{}).length
    &&!Object.keys(attempt.native_spawn_batches??{}).length&&!attempt.native_pending_followup
    &&!(attempt.native_dispatch_span?.publications??[]).length&&!attempt.native_dispatch_span?.publication_intent
    &&!attempt.host_tool&&!Object.keys(attempt.worker_host_checks??{}).length;
}
export function nativePreparationNotStarted(pins,definition,attempt){
  return pins.native_dispatch_span_version===1&&definition?.executor?.kind==='provider'
    &&pins.providers?.some(provider=>provider.id===definition.executor.provider_id&&provider.kind==='native_agent')
    &&nativePreparationUnreleased(attempt);
}

// Cooperative evidence, not an OS sandbox or a claim about the actor that
// wrote a path. Include hidden entries, .git, types and directory topology.
// Descriptor/path identity and directory listing checks make partial or
// unstable coverage an error instead of a successful empty effect report.
export async function captureNativeWorkspace(workspace,{subtree=null,hashPaths=null}={}){
  const root=resolve(workspace),entries=[];let bytes=0,hashed=0;
  const hashFile=path=>hashPaths===null||hashPaths.some(scope=>pathBoundaryContains(scope,path));
  await noSymlinks(root);
  const visit=async(absolute,path)=>{
    const before=await lstat(absolute,{bigint:true});
    if(before.isSymbolicLink()&&hashPaths!==null&&!hashPaths.some(scope=>pathBoundaryContains(scope,path)||pathBoundaryContains(path,scope))){
      entries.push({path,kind:'symlink',mode:Number(before.mode),bytes:Number(before.size),mtime_ns:String(before.mtimeNs),ctime_ns:String(before.ctimeNs)});return;
    }
    fail(!before.isSymbolicLink(),'COVERAGE',`Symbolic workspace entry: ${path}`);
    if(hashPaths===null)fail(entries.length<MAX_ENTRIES,'LIMIT','Native span exceeds its entry bound');
    if(before.isDirectory()){
      const names=(await readdir(absolute)).sort();entries.push({path,kind:'directory',mode:Number(before.mode)});
      for(const name of names)await visit(join(absolute,name),path?`${path}/${name}`:name);
      const after=await lstat(absolute,{bigint:true});
      fail(identical(before,after)&&same(names,(await readdir(absolute)).sort()),'UNSTABLE',`Directory changed during native snapshot: ${path}`);return;
    }
    fail(before.isFile(),'COVERAGE',`Unsupported workspace entry: ${path}`);
    if(!hashFile(path)){
      // Scope observation needs identity/timestamp metadata, not repository
      // contents. Existing product checks own artifact integrity; exact Host
      // material publication still carries its content hashes.
      const after=await lstat(absolute,{bigint:true});
      fail(identical(before,after),'UNSTABLE',`File changed during native observation: ${path}`);
      entries.push({path,kind:'file',mode:Number(after.mode),bytes:Number(after.size),mtime_ns:String(after.mtimeNs),ctime_ns:String(after.ctimeNs)});return;
    }
    fail(++hashed<=MAX_ENTRIES,'LIMIT','Native span exceeds its declared content entry bound');
    bytes+=Number(before.size);fail(bytes<=MAX_BYTES,'LIMIT','Native span exceeds its content bound');
    const file=await open(absolute,constants.O_RDONLY|(process.platform==='win32'?0:constants.O_NOFOLLOW|constants.O_NONBLOCK));
    try{
      const opened=await file.stat({bigint:true});fail(identical(before,opened),'UNSTABLE',`File changed while opening: ${path}`);
      const content=await file.readFile(),after=await file.stat({bigint:true});await noSymlinks(absolute);
      fail(identical(opened,after)&&identical(after,await lstat(absolute,{bigint:true}))&&BigInt(content.length)===opened.size,'UNSTABLE',`File changed during native snapshot: ${path}`);
      entries.push({path,kind:'file',mode:Number(after.mode),bytes:content.length,sha256:digest(content),mtime_ns:String(after.mtimeNs),ctime_ns:String(after.ctimeNs)});
    }finally{await file.close();}
  };
  if(subtree!==null){
    const path=slash(relative(root,resolve(subtree)));fail(path&&!path.startsWith('../')&&path!=='..','PUBLICATION','Material subtree leaves workspace');
    try{await visit(resolve(subtree),path);}catch(error){if(error.code!=='ENOENT')throw error;fail(entries.length===0,'UNSTABLE','Material subtree disappeared during capture');}
  }else await visit(root,'');
  return {schema_version:1,coverage:subtree===null?'whole_workspace':'exact_material_subtree',workspace:root,entries,
    ...(hashPaths===null?{}:{hash_paths:[...hashPaths]})};
}

export function nativeWorkspaceChanges(before,after){
  fail(before.workspace===after.workspace,'BINDING','Snapshot workspace changed');
  const left=new Map(before.entries.map(e=>[e.path,e])),right=new Map(after.entries.map(e=>[e.path,e]));
  return [...new Set([...left.keys(),...right.keys()])].sort().filter(path=>!same(left.get(path),right.get(path)))
    .map(path=>({path,before:left.get(path)??null,after:right.get(path)??null}));
}

export function nativeSpanIdentity(record,definition,attempt,plan){
  const workspace=resolve(record.state.permissions.workspace),permissions=nodePermissions(definition,record.state);
  const assignments=plan?.assignments??[null];
  assertFanoutWriteScopesDisjoint({workspace,nodeAllowedPaths:permissions.allowed_paths,assignments,fanout:definition.fanout});
  const grants=assignments.map((items,index)=>({index,paths:permissions.access==='read_only'?[]:items===null?permissions.allowed_paths:
    assignedFanoutWritePaths({workspace,nodeAllowedPaths:permissions.allowed_paths,assignedItems:items,fanout:definition.fanout})}));
  return {run_id:record.state.run_id,pins_hash:record.state.pins_hash,node_id:definition.id,attempt_id:attempt.id,
    dispatch_request_id:attempt.dispatch.request_id,envelope_hash:attempt.dispatch.envelope_hash,workspace,access:permissions.access,
    grants,input_sha256:digest(canonicalJSON(plan?.items??null)),controller_binding:digest(record.state.control_hash),
    lease_generation:attempt.lease_generation??0,lease_binding:digest(attempt.lease_hash)};
}

function stableIdentity(value){
  const copy={...value};delete copy.controller_binding;delete copy.lease_generation;delete copy.lease_binding;return copy;
}
function requireIdentity(before,current,attempt){
  fail(same(stableIdentity(before),stableIdentity(current)),'BINDING','Native span differs from its original dispatch and scopes');
  fail(same(before,current)||current.lease_generation>before.lease_generation&&attempt.reconciliation?.resubmitted===false,
    'BINDING','Native span controller or lease changed without exact non-resubmitted recovery');
}

export async function assertNativeSpanAdmission(runtime,record,nodeId,attemptId){
  const root=resolve(record.state.permissions.workspace);
  // Locate by the immutable bounded start record first. Never load unrelated
  // histories' executable resources merely to compare their task-root address.
  for(const entry of await readdir(runtime.runs.root,{withFileTypes:true})){
    const match=/^run-([A-Za-z0-9-]+)\.run$/.exec(entry.name);if(!match)continue;
    fail(entry.isDirectory()&&!entry.isSymbolicLink(),'COVERAGE','Run locator is not a physical directory');
    const runId=match[1],started=await readStartedEvent(join(runtime.runs.directory(runId),'events.jsonl'));
    if(rootKey(started.payload.state.permissions.workspace)!==rootKey(root))continue;
    let other=record;
    if(runId!==record.state.run_id){
      const {state}=await runtime.runs.readNativeWaitState(runId);
      const pins=JSON.parse(await readFile(join(runtime.runs.directory(runId),'pins.json'),'utf8'));
      fail(digest(canonicalJSON(pins))===state.pins_hash,'BINDING','Same-root admission pins changed');other={state,pins};
    }
    for(const definition of other.pins.root.workflow.nodes){
      const node=other.state.nodes[definition.id];
      for(const attempt of node.attempts){
        if(other.state.run_id===record.state.run_id&&definition.id===nodeId&&attempt.id===attemptId)continue;
        const unfinished=attempt.native_dispatch_span&&!attempt.native_dispatch_span.settled_ref&&!attempt.native_dispatch_span.abandoned_ref&&!attempt.native_preparation_closure;
        const active=['claimed','running'].includes(attempt.status)&&nodePermissions(definition,other.state).access==='bounded_write';
        fail(!unfinished&&!active,'CONCURRENT_WRITER','Another same-root writer or unfinished native span prevents honest group effect evidence',
          {run_id:other.state.run_id,node_id:definition.id,attempt_id:attempt.id});
      }
    }
  }
}

const ownerPath=(runtime,workspace)=>join(runtime.runs.root,'.run-locks','.native-task-roots',digest(rootKey(workspace))+'.json');
const ownerIdentity=identity=>Object.fromEntries(['run_id','pins_hash','node_id','attempt_id','dispatch_request_id','workspace'].map(key=>[key,identity[key]]));
async function readOwner(runtime,workspace){
  const path=ownerPath(runtime,workspace);try{await noSymlinks(path);return JSON.parse(await readFile(path,'utf8'));}
  catch(error){if(error.code==='ENOENT')return null;throw error;}
}
async function reserveOwner(runtime,identity){
  const path=ownerPath(runtime,identity.workspace),value=ownerIdentity(identity);await mkdir(dirname(path),{recursive:true});await noSymlinks(dirname(path));
  try{const file=await open(path,'wx',0o600);try{await file.writeFile(canonicalJSON(value));await file.sync();}finally{await file.close();}return true;}
  catch(error){if(error.code!=='EEXIST')throw error;fail(same(await readOwner(runtime,identity.workspace),value),'CONCURRENT_WRITER','A different native dispatch owns this task-root effect span');return false;}
}
async function retireOwner(runtime,owner){
  const path=ownerPath(runtime,owner.workspace);
  await retireOwnedFile(path,{stagingRoot:join(dirname(path),'.pending'),validate:bytes=>{
    fail(same(JSON.parse(bytes.toString('utf8')),owner),'BINDING','Native root owner changed before release');
  }});
}
async function closeUnstartedOwner(runtime,owner){
  const record=await runtime.runs.mutate(owner.run_id,'execution_drain',(state,pins)=>{
    const definition=pins.root.workflow.nodes.find(node=>node.id===owner.node_id);
    const attempt=state.nodes[owner.node_id]?.attempts.find(item=>item.id===owner.attempt_id);
    fail(['cancelled','failed','interrupted','blocked'].includes(attempt?.status)&&nativePreparationNotStarted(pins,definition,attempt),
      'UNSETTLED','Native root release requires a stopped attempt with no released work');
    fail(state.pins_hash===owner.pins_hash&&attempt.dispatch.request_id===owner.dispatch_request_id
      &&rootKey(state.permissions.workspace)===rootKey(owner.workspace),'BINDING','Unstarted native owner differs from its original attempt');
    attempt.native_preparation_closure={outcome:'not_started',owner_sha256:digest(canonicalJSON(owner))};
    attempt.dispatch.cancellation_pending=false;
  });
  const current=await readOwner(runtime,owner.workspace);
  // Another cleanup may already have retired this owner. Preserve any successor.
  if(current&&same(current,owner))await retireOwner(runtime,owner);
  return record;
}
export async function releaseCancelledNativePreparation(runtime,record){
  if(record.pins.native_dispatch_span_version!==1)return record;
  const owner=await readOwner(runtime,record.state.permissions.workspace);
  if(!owner||owner.run_id!==record.state.run_id)return record;
  const definition=record.pins.root.workflow.nodes.find(node=>node.id===owner.node_id);
  const attempt=record.state.nodes[owner.node_id]?.attempts.find(item=>item.id===owner.attempt_id);
  if(!['cancelled','failed','interrupted','blocked'].includes(attempt?.status)||!nativePreparationNotStarted(record.pins,definition,attempt))return record;
  return closeUnstartedOwner(runtime,owner);
}
export async function requireNativeRootClaim(runtime,state,definition,existing){
  if(nodePermissions(definition,state).access!=='bounded_write')return;
  const owner=await readOwner(runtime,state.permissions.workspace);if(!owner)return;
  if(owner.run_id===state.run_id&&owner.node_id===definition.id&&owner.attempt_id===existing?.id)return;
  // A crash after committed acceptance but before file release is resumable.
  // The narrow lifecycle read supplies no execution permission; this claim's
  // original fully audited transaction still controls its own authority.
  const {state:previous}=await runtime.runs.readNativeWaitState(owner.run_id),attempt=previous.nodes[owner.node_id]?.attempts.find(a=>a.id===owner.attempt_id);
  if(['cancelled','failed','interrupted','blocked'].includes(attempt?.status)&&nativePreparationUnreleased(attempt)){
    await closeUnstartedOwner(runtime,owner);return;
  }
  await requireClosedOwner(runtime,owner.run_id,attempt,'CONCURRENT_WRITER',owner);
  fail(same(await readOwner(runtime,state.permissions.workspace),owner),'BINDING','Native root owner changed during settled release');
  await retireOwner(runtime,owner);
}
export async function releaseNativeSpanOwner(runtime,record,definition,attempt){
  if(record.pins.native_dispatch_span_version!==1||!attempt.native_dispatch_span?.settled_ref&&!attempt.native_dispatch_span?.abandoned_ref)return;
  const {state}=await runtime.runs.readNativeWaitState(record.state.run_id),accepted=state.nodes[definition.id]?.attempts.find(a=>a.id===attempt.id);
  await requireClosedOwner(runtime,record.state.run_id,accepted,'UNSETTLED');
  fail(same(accepted.native_dispatch_span,attempt.native_dispatch_span),'BINDING','Native closed span changed before owner release');
  const owner=await readOwner(runtime,record.state.permissions.workspace);if(!owner)return;
  fail(same(owner,ownerIdentity(attempt.native_dispatch_span.identity)),'BINDING','Native task-root admission owner changed before release');
  await unlink(ownerPath(runtime,record.state.permissions.workspace));
}
async function requireClosedOwner(runtime,runId,attempt,code,owner){
  const span=attempt?.native_dispatch_span;
  const accepted=attempt?.status==='succeeded'&&span?.settled_ref&&same(attempt.completion?.evidence.find(e=>e.kind==='native_dispatch_span')?.reference,span.settled_ref);
  const abandoned=span?.abandoned_ref&&span.closure?.outcome==='abandoned'&&['failed','interrupted','blocked','cancelled'].includes(attempt.status);
  const unstarted=owner&&attempt?.native_preparation_closure?.outcome==='not_started'
    &&attempt.native_preparation_closure.owner_sha256===digest(canonicalJSON(owner))&&nativePreparationUnreleased(attempt);
  fail(accepted||abandoned||unstarted,code,'An unfinished native dispatch owns the task-root write admission');
  if(abandoned){const closed=await artifact(runtime,runId,span.abandoned_ref);
    fail(closed.kind==='native_dispatch_abandoned'&&same(closed.identity,span.identity)&&same(closed.before_ref,span.before_ref)
      &&same(closed.terminal_turns,span.closure.terminal_turns),'BINDING','Abandoned native owner lacks its exact durable failed closure');}
}

async function artifact(runtime,runId,reference){
  fail(reference&&typeof reference==='object','EVIDENCE','Native span has no durable reference');
  return JSON.parse((await runtime.runs.readArtifact(runId,reference)).toString('utf8'));
}
async function publications(runtime,runId,span){
  fail(!span.publication_intent,'PUBLICATION_UNSETTLED','A native material publication did not settle; explicit reconciliation is required');
  return Promise.all((span.publications??[]).map(ref=>artifact(runtime,runId,ref)));
}
function verifyPublications(current,values){
  const entries=new Map(current.entries.map(e=>[e.path,e]));
  for(const publication of values)for(const entry of publication.entries)
    fail(same(entries.get(entry.path),entry),'PUBLICATION_CHANGED',`Published native material changed: ${entry.path}`);
}

// Explicit publication paths are derived from the verified canonical material
// declaration, never from a prefix exception or model-provided changed paths.
async function packetFiles(packet){
  await readNativeTaskProjection(packet);
  const bundle=JSON.parse(await readFile(packet.task_bundle_path,'utf8'));
  const files=[packet.task_bundle_path];let metadata=bundle;
  if(bundle.context_preparation){files.push(bundle.context_preparation.path);metadata=JSON.parse(await readFile(bundle.context_preparation.path,'utf8'));}
  for(const item of [...(metadata.resources??[]),...(metadata.verified_files??[])])files.push(item.local_path);
  for(const item of metadata.inputs??[])if(item.delivery==='file'||bundle.schema_version===1)files.push(item.local_path??item.path);
  const projection=await readNativeTaskProjection(packet);if(!projection.inline)files.push(projection.task_bundle_path);
  return [...new Set(files)];
}

export async function prepareNativeSpan(runtime,record,definition,binding,dispatched,plan){
  if(record.pins.native_dispatch_span_version!==1)return null;
  const runId=record.state.run_id,attempt=record.state.nodes[definition.id].attempts.find(a=>a.id===binding.attempt_id);
  const identity=nativeSpanIdentity(record,definition,attempt,plan),root=identity.workspace;
  fail(resolve(dispatched.envelope.workspace)===root,'WORKSPACE','Native span requires the exact task workspace; isolated external roots need separate evidence');
  let span=attempt.native_dispatch_span;
  if(!span){
    fail(!Object.keys(attempt.native_agents??{}).length&&!Object.keys(attempt.native_pending_spawns??{}).length,'BEFORE_REQUIRED','Cannot invent a native baseline after a possibly-started spawn');
    await assertNativeSpanAdmission(runtime,record,definition.id,attempt.id);
    const reserved=await reserveOwner(runtime,identity);
    try{
      await assertNativeSpanAdmission(runtime,record,definition.id,attempt.id);
      const materialRoot=slash(relative(root,join(root,'work','.workflow-runtime','native-agent',runId,attempt.id)));
      const hashPaths=[materialRoot];
      const before={kind:'native_dispatch_before',identity,snapshot:await captureNativeWorkspace(root,{hashPaths})};
      const before_ref=await runtime.runs.saveArtifact(runId,`native-before-${attempt.id}`,canonicalJSON(before));
      await runtime.recordNativeSpan(runId,{...binding,phase:'before',value:{before_ref,identity,publications:[]}});
      span={before_ref,identity,publications:[]};
    }catch(error){
      if(reserved)try{
        const {state}=await runtime.runs.readNativeWaitState(runId),current=state.nodes[definition.id]?.attempts.find(item=>item.id===attempt.id);
        const owner=await readOwner(runtime,root);
        if(!current?.native_dispatch_span&&nativePreparationUnreleased(current)&&same(owner,ownerIdentity(identity)))await retireOwner(runtime,owner);
      }catch(cleanup){throw new AggregateError([error,cleanup],'Native preparation failed and its reservation cleanup failed',{cause:error});}
      throw error;
    }
  }else fail(same(await readOwner(runtime,root),ownerIdentity(span.identity)),'BINDING','Native publication lost its exact task-root owner');
  requireIdentity(span.identity,identity,attempt);
  return {runId,attempt,identity,root,span};
}

export async function materializeWithNativeSpan(runtime,record,definition,binding,dispatched,plan,materialize){
  if(record.pins.native_dispatch_span_version!==1)return materialize();
  const {runId,attempt,identity,root,span}=await prepareNativeSpan(runtime,record,definition,binding,dispatched,plan);
  const priorPublications=await publications(runtime,runId,span);
  const materialRoot=join(root,'work','.workflow-runtime','native-agent',runId,attempt.id);
  const prior=await captureNativeWorkspace(root,{subtree:materialRoot});verifyPublications(prior,priorPublications);
  const intent_ref=await runtime.runs.saveArtifact(runId,`native-publication-intent-${attempt.id}`,canonicalJSON({kind:'native_publication_intent',identity,prior}));
  await runtime.recordNativeSpan(runId,{...binding,phase:'publication_intent',value:intent_ref});
  const packet=await materialize();
  const after=await captureNativeWorkspace(root,{subtree:materialRoot}),afterMap=new Map(after.entries.map(e=>[e.path,e]));
  const allowed=new Set();
  for(const item of packet.packets)for(const file of await packetFiles(item)){
    let path=slash(relative(root,resolve(file)));
    fail(pathBoundaryContains(slash(relative(root,materialRoot)),path),'PUBLICATION','Native material declaration leaves its exact attempt tree');
    allowed.add(path);while(path.includes('/')){path=path.slice(0,path.lastIndexOf('/'));allowed.add(path);}
  }
  const changes=nativeWorkspaceChanges(prior,after);
  for(const change of changes)fail(!change.before&&allowed.has(change.path)&&change.after,'PUBLICATION',`Host publication cannot overwrite or exempt undeclared material: ${change.path}`);
  const entries=[...allowed].filter(path=>afterMap.has(path)).sort().map(path=>afterMap.get(path));
  const publication={kind:'native_material_publication',identity,intent_ref,entries,
    packets:packet.packets.map(({index,task_bundle_path,task_bundle_sha256,allowed_paths})=>({index,task_bundle_path,task_bundle_sha256,allowed_paths}))};
  const reference=await runtime.runs.saveArtifact(runId,`native-publication-${attempt.id}`,canonicalJSON(publication));
  await runtime.recordNativeSpan(runId,{...binding,phase:'publication',value:{intent_ref,reference}});
  return packet;
}

/** Replay an already published pending packet without a new publication effect.
 * Fresh authority, root ownership and exact material evidence remain required;
 * no materializer runs, and missing or changed evidence is never recreated. */
export async function reuseNativeSpanPublication(runtime,record,definition,binding,dispatched,plan,{pending,task_bundle_path}){
  const runId=record.state.run_id;
  const current=(await runtime.authorizedExecution(runId,binding,()=>binding)).record;
  const currentDefinition=current.pins.root.workflow.nodes.find(node=>node.id===definition.id);
  const attempt=current.state.nodes[definition.id]?.attempts.find(item=>item.id===binding.attempt_id);
  fail(current.pins.native_dispatch_span_version===1&&same(currentDefinition,definition)&&current.state.pins_hash===record.state.pins_hash,
    'BINDING','Published packet replay requires its exact current pinned definition');
  fail(attempt?.native_dispatch_span?.before_ref&&!attempt.native_dispatch_span.settled_ref&&!attempt.native_dispatch_span.abandoned_ref
    &&pending&&same(attempt.native_pending_followup,pending),'BINDING','Published packet replay lost its exact pending follow-up');
  const {identity,root,span}=await prepareNativeSpan(runtime,current,currentDefinition,binding,dispatched,plan);
  await assertNativeSpanAdmission(runtime,current,definition.id,attempt.id);
  const values=await publications(runtime,runId,span);
  const matches=values.flatMap(value=>{
    requireIdentity(value.identity,identity,attempt);
    return value.packets.filter(packet=>packet.index===pending.index&&packet.task_bundle_path===task_bundle_path
      &&packet.task_bundle_sha256===pending.task_bundle_sha256);
  });
  fail(matches.length>0&&matches.every(packet=>same(packet,matches[0])),'PUBLICATION','Pending packet has no exact settled publication');
  const packet=matches[0],materialRoot=join(root,'work','.workflow-runtime','native-agent',runId,attempt.id);
  verifyPublications(await captureNativeWorkspace(root,{subtree:materialRoot}),values);
  // This read checks the canonical scope, every declared sidecar and the public
  // projection bytes. It may not repair/rewrite any file during a replay.
  const task_projection=await readNativeTaskProjection(packet);
  const refreshed=(await runtime.authorizedExecution(runId,binding,()=>binding)).record;
  const latest=refreshed.state.nodes[definition.id]?.attempts.find(item=>item.id===attempt.id);
  fail(same(latest?.native_pending_followup,pending)&&same(latest?.native_dispatch_span,span)
    &&same(await readOwner(runtime,root),ownerIdentity(span.identity)),'BINDING','Published packet identity changed during replay');
  return {...packet,task_projection};
}

export async function settleNativeSpan(runtime,record,definition,attempt,binding,plan,{abandoned=false,terminal_turns=[]}={}){
  if(record.pins.native_dispatch_span_version!==1)return null;
  const span=attempt.native_dispatch_span;fail(span?.before_ref,'BEFORE_REQUIRED','Native completion lacks its original dispatch baseline');
  requireIdentity(span.identity,nativeSpanIdentity(record,definition,attempt,plan),attempt);
  await assertNativeSpanAdmission(runtime,record,definition.id,attempt.id);
  fail(!attempt.native_pending_followup&&Object.values(attempt.worker_host_checks??{}).every(slot=>slot.receipt)
    &&Object.values(attempt.native_spawn_batches??{}).every(batch=>batch.identity.spawns.every(s=>batch.acknowledged_indices.includes(s.index))),
    'UNSETTLED','Every possibly-started spawn, follow-up and Host check must settle before native group evidence');
  const before=await artifact(runtime,record.state.run_id,span.before_ref),values=await publications(runtime,record.state.run_id,span);
  fail(same(before.identity,span.identity)&&before.snapshot.coverage==='whole_workspace','BINDING','Native initial snapshot is not its sealed whole-root evidence');
  const current=await captureNativeWorkspace(span.identity.workspace,{hashPaths:before.snapshot.hash_paths??null});verifyPublications(current,values);
  for(const value of values)for(const packet of value.packets)await readNativeTaskProjection(packet);
  const publicationEntries=new Map(values.flatMap(value=>value.entries).map(entry=>[entry.path,entry]));
  const changes=nativeWorkspaceChanges(before.snapshot,current),changed_paths=[];
  for(const change of changes){
    const published=publicationEntries.get(change.path);
    // All new ancestor directories are exact topology from recorded files.
    const ancestor=change.after?.kind==='directory'&&!change.before&&[...publicationEntries.keys()].some(path=>path.startsWith(change.path+'/'));
    if(!change.before&&(same(change.after,published)||ancestor))continue;
    fail(span.identity.access==='bounded_write'&&span.identity.grants.some(grant=>grant.paths.some(path=>pathBoundaryContains(path,change.path))),
      'SCOPE',`Actual native dispatch-span effect exceeds every assigned scope: ${change.path}`,{path:change.path});
    changed_paths.push(change.path);
  }
  const settled={kind:abandoned?'native_dispatch_abandoned':'native_dispatch_settled',identity:span.identity,before_ref:span.before_ref,
    publication_refs:span.publications??[],coverage:'whole_workspace',attribution:'dispatch_group_only',changes,changed_paths,snapshot:current};
  if(abandoned){settled.outcome='abandoned';settled.terminal_turns=terminal_turns;settled.error=attempt.error??record.state.nodes[definition.id].error??null;}
  const reference=await runtime.runs.saveArtifact(record.state.run_id,`native-settled-${attempt.id}`,canonicalJSON(settled));
  if(!abandoned)await runtime.recordNativeSpan(record.state.run_id,{...binding,phase:'settled',value:reference});
  return {reference,changed_paths};
}

export async function abandonNativeSpan(runtime,record,definition,attempt,binding,plan){
  // Host-observed terminal turns establish Cooperative logical responsibility.
  // They do not establish OS-level quiescence for undeclared subprocesses.
  fail(!attempt.native_pending_spawns&&!attempt.native_pending_followup&&(!attempt.host_tool||attempt.host_tool.receipt?.status==='succeeded')
    &&Object.values(attempt.worker_host_checks??{}).every(slot=>slot.receipt?.status==='succeeded'),
    'UNSETTLED','Failed or pending producer/checker execution requires exact mechanical reconciliation before abandoning native work');
  const span=attempt.native_dispatch_span;
  // Preparation can fail before any packet leaves Host. There is then no
  // worker interval to audit, even if Main repaired files or recovered control.
  // A published packet/batch/receipt remains uncertain and uses normal closure.
  if(record.pins.native_dispatch_span_version===1&&span?.before_ref&&!attempt.dispatch?.receipt
    &&(span.publications??[]).length===0&&Object.keys(attempt.native_spawn_batches??{}).length===0
    &&Object.keys(attempt.native_agents??{}).length===0&&!attempt.host_tool
    &&Object.keys(attempt.worker_host_checks??{}).length===0){
    fail(same(stableIdentity(span.identity),stableIdentity(nativeSpanIdentity(record,definition,attempt,plan))),
      'BINDING','Unstarted native span differs from its original dispatch and scopes');
    const before=await artifact(runtime,record.state.run_id,span.before_ref);
    fail(same(before.identity,span.identity)&&before.snapshot.coverage==='whole_workspace','BINDING','Unstarted native span lost its sealed preparation evidence');
    const terminal_turns=[],closed={kind:'native_dispatch_abandoned',identity:span.identity,before_ref:span.before_ref,
      publication_refs:[],coverage:'host_release_state',attribution:'no_worker_dispatched',outcome:'not_started',
      terminal_turns,changed_paths:[],error:attempt.error??record.state.nodes[definition.id].error??null};
    const reference=await runtime.runs.saveArtifact(record.state.run_id,`native-not-started-${attempt.id}`,canonicalJSON(closed));
    return {reference,terminal_turns,changed_paths:[]};
  }
  const terminal_turns=Object.entries(attempt.native_agents??{}).map(([slot,agent_id])=>{
    const turn=attempt.native_terminal_turns?.[slot];
    fail(turn?.agent_id===agent_id&&typeof turn.turn_id==='string'&&turn.turn_id.length>0&&['completed','blocked','invalid'].includes(turn.status),
      'UNSETTLED','Every possibly-started native slot needs a durable exact accepted/rejected terminal turn');
    return {index:Number(slot),...turn};
  });
  const closed=await settleNativeSpan(runtime,record,definition,attempt,binding,plan,{abandoned:true,terminal_turns});
  return {...closed,terminal_turns};
}

export async function requireNativeSpanCompletion(runtime,runId,record,definition,attempt,payload){
  if(record.pins.native_dispatch_span_version!==1||attempt.dispatch?.receipt?.executor!=='codex-native-subagent')return [];
  const span=attempt.native_dispatch_span,proof=payload.evidence.find(e=>e.kind==='native_dispatch_span');
  fail(span?.settled_ref&&same(proof?.reference,span.settled_ref),'EVIDENCE','Native completion lacks the exact settled group evidence');
  const settled=await artifact(runtime,runId,span.settled_ref);
  fail(settled.kind==='native_dispatch_settled'&&same(settled.identity,span.identity)&&same(settled.before_ref,span.before_ref),'BINDING','Settled native evidence belongs to another span');
  fail(same(settled.snapshot,await captureNativeWorkspace(span.identity.workspace,{hashPaths:settled.snapshot.hash_paths??null})),'STALE','Workspace changed after native span settled');
  return settled.changed_paths;
}
