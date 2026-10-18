import test from 'node:test';
import {prepareNativeSpan,reuseNativeSpanPublication} from '../lib/execution/native-dispatch-span.mjs';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm,unlink} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {DEFAULT_CONFIG_PATH} from '../server.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {WorkflowService} from '../lib/workflow-service.mjs';
import {HostToolRunner} from '../lib/execution/host-tool-runner.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {retainOwnedAuthority} from '../lib/execution/owned-workflow-authority.mjs';
import {captureNativeWorkspace,nativeWorkspaceChanges,nativeSpanIdentity,materializeWithNativeSpan,settleNativeSpan,requireNativeSpanCompletion,requireNativeRootClaim,releaseNativeSpanOwner,assertNativeSpanAdmission,abandonNativeSpan} from '../lib/execution/native-dispatch-span.mjs';
import {appendEvent} from '../lib/workflow-events.mjs';
import nativeFs from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {materializeNativeTaskBundle} from '../lib/execution/node-input-materials.mjs';
const THREAD='00000000-0000-7000-8000-000000000001',MODEL={model:true,modelThreadId:THREAD};
const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
async function setup(t,write,{observe}={}){
 const root=await mkdtemp(join(tmpdir(),'native-span-')),workspace=join(root,'workspace');await mkdir(workspace);await mkdir(join(workspace,'pages'));await mkdir(join(workspace,'.git'));
 await writeFile(join(workspace,'.git/existing'),'unchanged');
 const semantic=object({conclusion:{type:'string',minLength:1,maxLength:600}});
 const contract={id:'verify-existing',identity:{name:'span-fixture',version:'1',sha256:digest('span-fixture')},argv:[],input_schema:object({inputs:object({task:{type:'string'}}),output:semantic}),output_schema:object({complete:{type:'boolean'},diagnostic:{type:'string'}}),permissions:{network:false,read_paths:['.'],write_paths:['pages']},env_allow:[],input_cap_bytes:1048576,output_cap_bytes:1048576,deadline_ms:2000,idempotency:{mode:'safe'}};
 const broker={identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:'span-fixture',evidence_sha256:digest('qualified')},execute:async()=>({exit_code:0,output:{complete:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}}),cancel:async()=>({termination_confirmed:true,evidence:[],effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})};
 const registry={'span-fixture':broker};
 const service=new WorkflowService({configPath:join(root,'config.json'),defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:{hostToolRegistry:registry,hostToolRunner:new HostToolRunner({registry,env:{}}),nativeParentVerifier:async()=>{},nativeAgentObserver:async ids=>{await write(workspace);return observe?observe(ids):{status:'completed',agent_id:ids[0],turn_id:'exact-terminal-turn',result:{conclusion:'A neutral semantic result.'}};}}});
 await service.call('migrate_v6',{}, {human:true});
 t.after(async()=>{await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);assert(resolve(root).startsWith(resolve(tmpdir())));await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
 const workflow={...createDraft('span-'+Math.random().toString(36).slice(2),'Native span qualification'),status:'ready',skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},inputs_schema:object({task:{type:'string'}}),host_tools:[contract],finalization:{required:true,node_id:'final'},nodes:[{id:'start',type:'start'},{id:'worker',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},access:'bounded_write',path_scope:['pages'],approval:{required:false},retry:{max_attempts:2},input_bindings:{task:'/inputs/task'},prompt_template:'Complete the neutral task.',outputs_schema:semantic,completion_contract:{on_missing:'block',outcome:'validated_artifact',host_check:{tool:'verify-existing',success_field:'complete',correction_field:'diagnostic'}}},{id:'final',type:'agent',role:'finalizer',executor:{kind:'main',mode:'orchestration'},access:'read_only',approval:{required:false},retry:{max_attempts:1},input_bindings:{conclusion:'/nodes/worker/output/conclusion'},prompt_template:'Accept the actual semantic result.',outputs_schema:object({accepted:{type:'boolean'}})},{id:'end',type:'end'}],edges:[{id:'sw',source:'start',target:'worker'},{id:'wf',source:'worker',target:'final'},{id:'fe',source:'final',target:'end'}]};
 const created=await service.call('create',{workflow},{human:true});
 const run=await service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace,access:'bounded_write',allowed_paths:['pages'],main_actor:'root',native_parent_thread_id:THREAD,inputs:{task:'Explain a neutral valve.'}});
 const {runtime}=await service.open();await retainOwnedAuthority(runtime,run);
 return {service,workspace,runtime,run};
}
test('native span public MODEL_REQUEST rejects actual outside child effects with zero checker delta',async t=>{
 for(const path of ['outside.txt','.git/existing','.hidden/outside.txt'])await t.test(path,async t=>{
  const f=await setup(t,async workspace=>{if(path.includes('/'))await mkdir(join(workspace,path.split('/')[0]),{recursive:true});await writeFile(join(workspace,path),'actual child interval write');});
  const handoff=await f.service.call('native_next',{},MODEL);
  await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL),{code:'NATIVE_SPAN_SCOPE'});
 });
});
test('native span public MODEL_REQUEST retains actual granted child effects with zero checker delta',async t=>{
 const f=await setup(t,workspace=>writeFile(join(workspace,'pages/product.txt'),'actual child interval product'));
 const handoff=await f.service.call('native_next',{},MODEL);const result=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL);
 assert.equal(result.status,'orchestration_handoff');const record=await f.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.worker.attempts[0];
 assert(attempt.completion.changed_paths.includes('pages/product.txt'),'Actual child effects must not be replaced by empty checker effects');
 assert(attempt.native_dispatch_span?.before_ref);assert(attempt.native_dispatch_span?.settled_ref);assert.equal(attempt.completion.evidence.find(e=>e.kind==='native_dispatch_span').reference.sha256,attempt.native_dispatch_span.settled_ref.sha256);
});

test('native span public retry terminal-abandons failed actual turns and admits a fresh attempt',async t=>{
 let turns=0;const f=await setup(t,workspace=>writeFile(join(workspace,'pages/failed-draft.txt'),'actual failed draft'),
  {observe:ids=>({status:'completed',agent_id:ids[0],turn_id:`rejected-${++turns}`,result:{wrong:true}})});
 const binding={run_id:f.run.run_id,control_token:f.run.control_token};
 const initial=await f.service.call('native_next',{},MODEL);
 const repair=await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL);
 assert.equal(repair.status,'native_agent_invalid_result');
 const internal=await f.service.call('native_next',binding);await f.service.call('native_followed_up',internal.next_action_args);
 const exhausted=await f.service.call('native_next',binding);assert.equal(exhausted.status,'native_agent_repair_exhausted');
 const before=await f.runtime.runs.read(f.run.run_id),failed=before.state.nodes.worker.attempts.at(-1);assert.equal(failed.status,'failed');
 await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:failed.id,dispatch_request_id:failed.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'actual_terminal_turns'}]}});
 const after=await f.runtime.runs.read(f.run.run_id),closed=after.state.nodes.worker.attempts[0];assert.equal(closed.status,'failed');assert.equal(closed.completion,undefined);assert(closed.native_dispatch_span.abandoned_ref);assert.deepEqual(closed.native_dispatch_span.before_ref,failed.native_dispatch_span.before_ref);
 const next=await f.service.call('native_next',binding);assert.notEqual(next.attempt_id,failed.id);assert(next.packets.length>0);
});

async function unit(t){
 const base=await mkdtemp(join(tmpdir(),'native-span-unit-')),workspace=join(base,'workspace'),store=join(base,'store');await mkdir(workspace);await mkdir(store);await mkdir(join(workspace,'pages'));await mkdir(join(workspace,'pages/a'));await mkdir(join(workspace,'pages/b'));
 t.after(()=>rm(base,{recursive:true,maxRetries:3,retryDelay:100}));
 const definition={id:'worker',access:'bounded_write',path_scope:['pages'],fanout:{scheduling:'parallel',distribution:'one_per_item',write_paths_field:'destinations',max_concurrency:2}};
 const plan={items:[{destinations:['pages/a']},{destinations:['pages/b']}],assignments:[[{destinations:['pages/a']}],[{destinations:['pages/b']}]]};
 const attempt={id:'attempt',lease_hash:digest('lease'),dispatch:{request_id:'dispatch',envelope_hash:digest('envelope'),receipt:{executor:'codex-native-subagent'}},native_agents:{}};
 const record={pins:{native_dispatch_span_version:1,root:{workflow:{nodes:[definition]}}},state:{run_id:'run1',pins_hash:digest('pins'),control_hash:digest('control'),permissions:{workspace,access:'bounded_write',allowed_paths:['pages']},nodes:{worker:{attempts:[attempt]}}}};
 const artifacts=new Map();
 const runtime={runs:{root:store,directory:id=>join(store,'run-'+id+'.run'),saveArtifact:async(id,label,content)=>{const bytes=Buffer.from(content),sha256=digest(bytes),reference={artifact:label+'-'+sha256,sha256,bytes:bytes.length};artifacts.set(sha256,bytes);return reference;},readArtifact:async(id,ref)=>{const bytes=artifacts.get(ref.sha256);assert(bytes&&digest(bytes)===ref.sha256);return bytes;}},recordNativeSpan:async(id,{phase,value})=>{if(phase==='before')attempt.native_dispatch_span=structuredClone(value);else if(phase==='publication_intent')attempt.native_dispatch_span.publication_intent=value;else if(phase==='publication'){assert.deepEqual(attempt.native_dispatch_span.publication_intent,value.intent_ref);attempt.native_dispatch_span.publications.push(value.reference);delete attempt.native_dispatch_span.publication_intent;}else attempt.native_dispatch_span.settled_ref=value;}};
 runtime.runs.readNativeWaitState=async id=>{assert.equal(id,record.state.run_id);return {state:record.state};};
 const binding={node_id:'worker',attempt_id:'attempt'},dispatched={envelope:{workspace}};
 const publish=index=>materializeWithNativeSpan(runtime,record,definition,binding,dispatched,plan,async()=>{
  const directory=join(workspace,'work/.workflow-runtime/native-agent/run1/attempt/partition-'+index);
  const material=await materializeNativeTaskBundle({directory,envelope:{workspace,access:'bounded_write',inputs:{task:'A neutral exact semantic task.'},prompt_template:'Complete {{task}}',context_projection:{references:[]}},allowedPaths:plan.items[index].destinations,resultSchema:object({conclusion:{type:'string'}})});
  return {packets:[{index,...material}]};
 });
 return {workspace,store,definition,plan,attempt,record,runtime,binding,publish,close:()=>settleNativeSpan(runtime,record,definition,attempt,binding,plan)};
}

test('native span empty dispatch establishes a reusable baseline without material publication',async t=>{
 const f=await unit(t);f.plan.assignments=[];
 const first=await prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan);
 assert.deepEqual(first.identity.grants,[]);assert(first.span.before_ref);assert.deepEqual(first.span.publications,[]);
 const replay=await prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan);
 assert.deepEqual(replay.span.before_ref,first.span.before_ref);assert.deepEqual(replay.span.publications,[]);
 const settled=await f.close();assert.deepEqual(settled.changed_paths,[]);
});

test('native preparation failure before journal publication releases its exact root reservation',async t=>{
 const f=await unit(t);f.attempt.dispatch.receipt=null;
 const original=f.runtime.runs.saveArtifact,error=Object.assign(new Error('Injected baseline storage failure'),{code:'TEST_BASELINE_WRITE'});
 f.runtime.runs.saveArtifact=async()=>{throw error;};
 await assert.rejects(prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan),caught=>caught===error);
 f.runtime.runs.saveArtifact=original;
 assert.equal(f.attempt.native_dispatch_span,undefined);
 await requireNativeRootClaim(f.runtime,{...f.record.state,run_id:'next-run'},f.definition);
 await prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan);
});

test('public cancel retires a historical unstarted reservation and the next same-root Run can dispatch',async t=>{
 const f=await setup(t,async()=>{});
 const claim=await f.runtime.claimNode(f.run.run_id,{node_id:'worker',owner:'root',request_id:'unstarted-claim',control_token:f.run.control_token});
 await f.runtime.recordDispatchIntent(f.run.run_id,{node_id:'worker',attempt_id:claim.attempt_id,lease_token:claim.lease_token,
  request_id:'unstarted-dispatch',envelope_hash:digest('unstarted-envelope'),control_token:f.run.control_token});
 const record=await f.runtime.runs.read(f.run.run_id),definition=record.pins.root.workflow.nodes.find(n=>n.id==='worker'),attempt=record.state.nodes.worker.attempts.at(-1);
 const identity=nativeSpanIdentity(record,definition,attempt,null),directory=join(f.runtime.runs.root,'.run-locks','.native-task-roots');
 await mkdir(directory,{recursive:true});
 const owner=Object.fromEntries(['run_id','pins_hash','node_id','attempt_id','dispatch_request_id','workspace'].map(key=>[key,identity[key]]));
 const key=process.platform==='win32'?resolve(f.workspace).toLowerCase():resolve(f.workspace);
 const path=join(directory,digest(key)+'.json');await writeFile(path,canonicalJSON(owner));
 await f.service.call('cancel',{run_id:f.run.run_id,control_token:f.run.control_token});
 const cancelled=await f.runtime.runs.read(f.run.run_id);
 assert.equal(cancelled.state.status,'cancelled');
 assert.equal(cancelled.state.nodes.worker.attempts.at(-1).dispatch.cancellation_pending,false);
 await assert.rejects(readFile(path),{code:'ENOENT'});
 const next=await f.service.call('start',{workflow_id:record.state.workflow_id,revision_hash:record.pins.root.revision_hash,
  workspace:f.workspace,access:'bounded_write',allowed_paths:['pages'],main_actor:'root',native_parent_thread_id:THREAD,inputs:{task:'Explain the next neutral task.'}});
 await retainOwnedAuthority(f.runtime,next);
 const handoff=await f.service.call('native_next',{},MODEL);
 assert(handoff.spawn_calls?.length>0||handoff.packets?.length>0);
});

test('same-root admission repairs an already-cancelled historical preparation without resubmitting it',async t=>{
 const f=await setup(t,async()=>{});
 const claim=await f.runtime.claimNode(f.run.run_id,{node_id:'worker',owner:'root',request_id:'historical-claim',control_token:f.run.control_token});
 await f.runtime.recordDispatchIntent(f.run.run_id,{node_id:'worker',attempt_id:claim.attempt_id,lease_token:claim.lease_token,
  request_id:'historical-dispatch',envelope_hash:digest('historical-envelope'),control_token:f.run.control_token});
 const record=await f.runtime.runs.read(f.run.run_id),definition=record.pins.root.workflow.nodes.find(n=>n.id==='worker'),attempt=record.state.nodes.worker.attempts.at(-1);
 const identity=nativeSpanIdentity(record,definition,attempt,null),directory=join(f.runtime.runs.root,'.run-locks','.native-task-roots');
 await mkdir(directory,{recursive:true});
 const owner=Object.fromEntries(['run_id','pins_hash','node_id','attempt_id','dispatch_request_id','workspace'].map(key=>[key,identity[key]]));
 const key=process.platform==='win32'?resolve(f.workspace).toLowerCase():resolve(f.workspace);
 await writeFile(join(directory,digest(key)+'.json'),canonicalJSON(owner));
 await f.runtime.runs.mutate(f.run.run_id,'cancel',state=>{
  state.status='cancelled';state.nodes.worker.status='cancelled';
  const current=state.nodes.worker.attempts.at(-1);current.status='cancelled';current.dispatch.cancellation_pending=true;
 });
 await requireNativeRootClaim(f.runtime,{...record.state,run_id:'next-run'},definition);
 const closed=(await f.runtime.runs.read(f.run.run_id)).state.nodes.worker.attempts.at(-1);
 assert.equal(closed.dispatch.cancellation_pending,false);assert.equal(closed.native_preparation_closure.outcome,'not_started');
 assert.equal(closed.dispatch.receipt,null);assert.equal(closed.native_agents,undefined);
});

test('native span published pending packet replay is read-only and rejects changed evidence or authority',async t=>{
 for(const scenario of ['exact','pending tuple','packet hash','published bytes','unsettled publication','authority during verification'])await t.test(scenario,async t=>{
  const f=await unit(t),published=await f.publish(0),packet=published.packets[0];
  const pending={index:0,agent_id:'recorded-child',item_index:0,task_bundle_sha256:packet.task_bundle_sha256,followup_kind:'repair',rejection_count:1};
  f.attempt.native_pending_followup=structuredClone(pending);
  let authorizations=0,writes=0;const recordSpan=f.runtime.recordNativeSpan;
  f.runtime.recordNativeSpan=async(...args)=>{writes++;return recordSpan(...args);};
  const authorityError=Object.assign(new Error('Exact controller revoked'),{code:'RUN_AUTHORITY'});
  f.runtime.authorizedExecution=async(runId,binding,select)=>{
   authorizations++;assert.equal(runId,f.record.state.run_id);assert.deepEqual(select(f.record),binding);
   if(scenario==='authority during verification'&&authorizations===2)throw authorityError;
   return {record:f.record};
  };
  const before=canonicalJSON(f.attempt.native_dispatch_span);
  const options={pending:structuredClone(pending),task_bundle_path:packet.task_bundle_path};
  if(scenario==='pending tuple')options.pending.agent_id='different-child';
  if(scenario==='packet hash'){f.attempt.native_pending_followup.task_bundle_sha256='f'.repeat(64);options.pending.task_bundle_sha256='f'.repeat(64);}
  if(scenario==='published bytes')await writeFile(packet.task_bundle_path,'changed material');
  if(scenario==='unsettled publication')f.attempt.native_dispatch_span.publication_intent={sha256:'e'.repeat(64)};
  const replay=()=>reuseNativeSpanPublication(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan,options);
  if(scenario==='exact'){
   const result=await replay();assert.equal(result.task_bundle_sha256,packet.task_bundle_sha256);assert.equal(result.index,0);
   assert.equal(authorizations,2);assert.equal(canonicalJSON(f.attempt.native_dispatch_span),before);
  }else await assert.rejects(replay,{code:({'pending tuple':'NATIVE_SPAN_BINDING','packet hash':'NATIVE_SPAN_PUBLICATION','published bytes':'NATIVE_SPAN_PUBLICATION_CHANGED','unsettled publication':'NATIVE_SPAN_PUBLICATION_UNSETTLED','authority during verification':'RUN_AUTHORITY'})[scenario]});
  assert.equal(writes,0,'Replay must never publish or recreate missing/changed evidence');
 });
});

test('native span cannot create an empty baseline after a possibly started child',async t=>{
 const f=await unit(t);f.attempt.native_agents={0:'started'};
 await assert.rejects(prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan),{code:'NATIVE_SPAN_BEFORE_REQUIRED'});
 assert.equal(f.attempt.native_dispatch_span,undefined);
});

test('native span whole-root coverage includes hidden files, git and directory/type changes',async t=>{
 const f=await unit(t);await mkdir(join(f.workspace,'.git'));await writeFile(join(f.workspace,'.git/index'),'before');
 const before=await captureNativeWorkspace(f.workspace);await writeFile(join(f.workspace,'.git/index'),'after');await mkdir(join(f.workspace,'.hidden'));await mkdir(join(f.workspace,'pages/empty'));
 const paths=nativeWorkspaceChanges(before,await captureNativeWorkspace(f.workspace)).map(c=>c.path);
 assert(paths.includes('.git/index'));assert(paths.includes('.hidden'));assert(paths.includes('pages/empty'));
});

test('native scoped observation avoids unrelated file contents and still records outside changes',async t=>{
 const f=await unit(t),outside=join(f.workspace,'unrelated-binary');await writeFile(outside,'original bytes');
 const original=nativeFs.open;let before;
 nativeFs.open=async(path,...args)=>{assert.notEqual(path,outside,'Unrelated content must not be read');return original(path,...args);};syncBuiltinESMExports();
 try{before=await captureNativeWorkspace(f.workspace,{hashPaths:['pages']});}
 finally{nativeFs.open=original;syncBuiltinESMExports();}
 assert.equal(before.entries.find(entry=>entry.path==='unrelated-binary').sha256,undefined);
 await writeFile(outside,'changed bytes');
 const changes=nativeWorkspaceChanges(before,await captureNativeWorkspace(f.workspace,{hashPaths:['pages']}));
 assert(changes.some(change=>change.path==='unrelated-binary'));
});
test('native dispatch preparation does not read or count unrelated content toward its 2 GiB material bound',async t=>{
 const f=await unit(t),outside=join(f.workspace,'large-unrelated-binary');await writeFile(outside,'small physical fixture');
 const originalStat=nativeFs.lstat,originalOpen=nativeFs.open,virtualBytes=2*1024*1024*1024+1;
 nativeFs.lstat=async(path,...args)=>{const info=await originalStat(path,...args);if(path===outside)info.size=typeof info.size==='bigint'?BigInt(virtualBytes):virtualBytes;return info;};
 nativeFs.open=async(path,...args)=>{assert.notEqual(path,outside,'Dispatch must not open unrelated repository content');return originalOpen(path,...args);};syncBuiltinESMExports();
 let prepared;
 try{prepared=await prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan);}
 finally{nativeFs.lstat=originalStat;nativeFs.open=originalOpen;syncBuiltinESMExports();}
 const before=JSON.parse((await f.runtime.runs.readArtifact('run1',prepared.span.before_ref)).toString('utf8'));
 const observed=before.snapshot.entries.find(entry=>entry.path==='large-unrelated-binary');
 assert.equal(observed.bytes,virtualBytes);assert.equal(observed.sha256,undefined);
 assert.deepEqual(before.snapshot.hash_paths,['work/.workflow-runtime/native-agent/run1/attempt']);
});

test('native span capped publications retain first baseline and aggregate both disjoint grants',async t=>{
 const f=await unit(t);await f.publish(0);const initial=f.attempt.native_dispatch_span.before_ref;
 await writeFile(join(f.workspace,'pages/a/first'),'first');await f.publish(1);await writeFile(join(f.workspace,'pages/b/second'),'second');
 assert.deepEqual(f.attempt.native_dispatch_span.before_ref,initial);const result=await f.close();assert.deepEqual(result.changed_paths,['pages/a/first','pages/b/second']);
 const evidence=JSON.parse((await f.runtime.runs.readArtifact('run1',result.reference)).toString());assert.equal(evidence.attribution,'dispatch_group_only');assert.equal(evidence.publication_refs.length,2);
});
test('native span later capped publication cannot erase an earlier outside effect',async t=>{
 const f=await unit(t);await f.publish(0);await writeFile(join(f.workspace,'outside'),'outside');await f.publish(1);await assert.rejects(f.close(),{code:'NATIVE_SPAN_SCOPE'});
});
test('native span exact publication tamper and undeclared material never gain prefix exemptions',async t=>{
 const f=await unit(t),packet=await f.publish(0);await writeFile(packet.packets[0].task_bundle_path,'tampered');await assert.rejects(f.close(),{code:'NATIVE_SPAN_PUBLICATION_CHANGED'});
 const g=await unit(t);await g.publish(0);await writeFile(join(g.workspace,'work/.workflow-runtime/native-agent/run1/attempt/unknown'),'unrelated');await assert.rejects(g.close(),{code:'NATIVE_SPAN_SCOPE'});
});
test('native span exact restart replay retains refs; post-settlement change fails freshness',async t=>{
 const f=await unit(t);await f.publish(0);const before=f.attempt.native_dispatch_span.before_ref;
 // Durable state rehydration, with the original artifact store; no replacement baseline.
 f.attempt.native_dispatch_span=JSON.parse(JSON.stringify(f.attempt.native_dispatch_span));await f.publish(0);assert.deepEqual(f.attempt.native_dispatch_span.before_ref,before);
 const settled=await f.close(),payload={evidence:[{kind:'native_dispatch_span',reference:settled.reference}]};
 assert.deepEqual(await requireNativeSpanCompletion(f.runtime,'run1',f.record,f.definition,f.attempt,payload),[]);
 await writeFile(join(f.workspace,'pages/a/late'),'late');await assert.rejects(requireNativeSpanCompletion(f.runtime,'run1',f.record,f.definition,f.attempt,payload),{code:'NATIVE_SPAN_STALE'});
});
test('native span root owner fences unrelated claims and survives cancellation uncertainty',async t=>{
 const f=await unit(t);await f.publish(0);await assert.rejects(requireNativeRootClaim(f.runtime,{...f.record.state,run_id:'other'},f.definition),{code:'NATIVE_SPAN_CONCURRENT_WRITER'});
 f.attempt.status='cancelled';await assert.rejects(requireNativeRootClaim(f.runtime,f.record.state,f.definition,{id:'next-attempt'}),{code:'NATIVE_SPAN_CONCURRENT_WRITER'});
 f.attempt.status='running';const settled=await f.close();await assert.rejects(releaseNativeSpanOwner(f.runtime,f.record,f.definition,f.attempt),{code:'NATIVE_SPAN_UNSETTLED'});
 f.attempt.status='succeeded';f.attempt.completion={evidence:[{kind:'native_dispatch_span',reference:settled.reference}]};await releaseNativeSpanOwner(f.runtime,f.record,f.definition,f.attempt);await requireNativeRootClaim(f.runtime,{...f.record.state,run_id:'other'},f.definition);
});
test('unpublished native preparation closes as not started after control recovery without attributing Main edits',async t=>{
 const f=await unit(t);f.attempt.dispatch.receipt=null;
 await prepareNativeSpan(f.runtime,f.record,f.definition,f.binding,{envelope:{workspace:f.workspace}},f.plan);
 f.record.state.control_hash=digest('recovered-control');f.attempt.status='interrupted';
 await writeFile(join(f.workspace,'main-repair.txt'),'Authorized Main repair before any packet was released');
 const closed=await abandonNativeSpan(f.runtime,f.record,f.definition,f.attempt,f.binding,f.plan);
 const evidence=JSON.parse((await f.runtime.runs.readArtifact('run1',closed.reference)).toString());
 assert.equal(evidence.outcome,'not_started');assert.equal(evidence.attribution,'no_worker_dispatched');
 assert.deepEqual(evidence.changed_paths,[]);assert.equal(evidence.snapshot,undefined);
 f.attempt.dispatch.envelope_hash=digest('changed-dispatch');
 await assert.rejects(abandonNativeSpan(f.runtime,f.record,f.definition,f.attempt,f.binding,f.plan),{code:'NATIVE_SPAN_BINDING'});
});

test('native span non-resubmitted same-attempt recovery keeps baseline and rejects dispatch change',async t=>{
 const f=await unit(t);await f.publish(0);const before=f.attempt.native_dispatch_span.before_ref;f.attempt.lease_generation=1;f.attempt.lease_hash=digest('newlease');f.attempt.reconciliation={resubmitted:false};await f.publish(1);assert.deepEqual(f.attempt.native_dispatch_span.before_ref,before);await f.close();
 const g=await unit(t);await g.publish(0);g.attempt.dispatch.envelope_hash=digest('changed');await assert.rejects(g.publish(1),{code:'NATIVE_SPAN_BINDING'});
});
test('native span pending Host publication, followup and unacknowledged spawn cannot settle',async t=>{
 for(const kind of ['publication','followup','spawn','checker'])await t.test(kind,async t=>{const f=await unit(t);await f.publish(0);
  if(kind==='publication')f.attempt.native_dispatch_span.publication_intent={sha256:digest('uncertain')};
  if(kind==='followup')f.attempt.native_pending_followup={};
  if(kind==='spawn')f.attempt.native_spawn_batches={b:{identity:{spawns:[{index:0}]},acknowledged_indices:[]}};
  if(kind==='checker')f.attempt.worker_host_checks={slot:{}};
  await assert.rejects(f.close(),{code:kind==='publication'?'NATIVE_SPAN_PUBLICATION_UNSETTLED':'NATIVE_SPAN_UNSETTLED'});
 });
});
test('native span owner release resumes exact committed acceptance after process restart',async t=>{
 const f=await unit(t);await f.publish(0);const settled=await f.close();f.attempt.status='succeeded';f.attempt.completion={evidence:[{kind:'native_dispatch_span',reference:settled.reference}]};
 await requireNativeRootClaim(f.runtime,{...f.record.state,run_id:'other'},f.definition);await requireNativeRootClaim(f.runtime,{...f.record.state,run_id:'another'},f.definition);
});
test('native span admission skips unrelated resource histories and rejects active exact same-root writer',async t=>{
 const f=await unit(t),foreign=f.runtime.runs.directory('unrelated');await mkdir(foreign);
 await appendEvent(join(foreign,'events.jsonl'),[],'started',{state:{permissions:{workspace:join(f.workspace,'unrelated-root')}}});await writeFile(join(foreign,'pins.json'),'malformed unrelated resource history');
 await assertNativeSpanAdmission(f.runtime,f.record,'worker','attempt');
 const other=f.runtime.runs.directory('same-root');await mkdir(other);const pins={root:{workflow:{nodes:[f.definition]}}},state={run_id:'same-root',permissions:f.record.state.permissions,pins_hash:digest(canonicalJSON(pins)),nodes:{worker:{attempts:[{id:'unrelated-writer',status:'running'}]}}};
 await appendEvent(join(other,'events.jsonl'),[],'started',{state});await writeFile(join(other,'pins.json'),canonicalJSON(pins));f.runtime.runs.readNativeWaitState=async id=>{assert.equal(id,'same-root');return {state};};
 await assert.rejects(assertNativeSpanAdmission(f.runtime,f.record,'worker','attempt'),{code:'NATIVE_SPAN_CONCURRENT_WRITER'});
});

test('native span Windows case aliases cannot hide an active same-root writer', {skip:process.platform!=='win32'},async t=>{
 const f=await unit(t),other=f.runtime.runs.directory('same-root-case');await mkdir(other);
 const pins={root:{workflow:{nodes:[f.definition]}}},state={run_id:'same-root-case',permissions:{...f.record.state.permissions,workspace:f.workspace.toUpperCase()},pins_hash:digest(canonicalJSON(pins)),nodes:{worker:{attempts:[{id:'active-case-alias',status:'running'}]}}};
 await appendEvent(join(other,'events.jsonl'),[],'started',{state});await writeFile(join(other,'pins.json'),canonicalJSON(pins));
 f.runtime.runs.readNativeWaitState=async id=>{assert.equal(id,'same-root-case');return {state};};
 await assert.rejects(assertNativeSpanAdmission(f.runtime,f.record,'worker','attempt'),{code:'NATIVE_SPAN_CONCURRENT_WRITER'});
});
test('native span terminal abandon audits original effects and releases failed owner without success',async t=>{
 const f=await unit(t);await f.publish(0);f.attempt.native_agents={0:'child-a'};f.attempt.native_terminal_turns={0:{agent_id:'child-a',turn_id:'exact-rejected',status:'invalid'}};f.attempt.status='failed';f.attempt.error={code:'NATIVE_AGENT_REPAIR_EXHAUSTED',message:'Exact final rejection'};
 await writeFile(join(f.workspace,'pages/a/failed-draft'),'failed draft');const initial=f.attempt.native_dispatch_span.before_ref;
 const closed=await abandonNativeSpan(f.runtime,f.record,f.definition,f.attempt,f.binding,f.plan);const evidence=JSON.parse((await f.runtime.runs.readArtifact('run1',closed.reference)).toString());
 assert.equal(evidence.outcome,'abandoned');assert.deepEqual(evidence.before_ref,initial);assert.deepEqual(closed.changed_paths,['pages/a/failed-draft']);assert.equal(f.attempt.status,'failed');assert.equal(f.attempt.completion,undefined);
 f.attempt.native_dispatch_span.abandoned_ref=closed.reference;f.attempt.native_dispatch_span.closure={outcome:'abandoned',terminal_turns:closed.terminal_turns,error:f.attempt.error};
 await releaseNativeSpanOwner(f.runtime,f.record,f.definition,f.attempt);await requireNativeRootClaim(f.runtime,{...f.record.state,run_id:'next-run'},f.definition);
});
test('native span abandon rejects missing terminal proof failed producer check and actual outside effect',async t=>{
 for(const kind of ['terminal','producer','scope'])await t.test(kind,async t=>{const f=await unit(t);await f.publish(0);f.attempt.native_agents={0:'child'};f.attempt.native_terminal_turns={0:{agent_id:'child',turn_id:'rejected',status:'blocked'}};
  if(kind==='terminal')delete f.attempt.native_terminal_turns[0];
  if(kind==='producer')f.attempt.worker_host_checks={slot:{receipt:{status:'failed'}}};
  if(kind==='scope')await writeFile(join(f.workspace,'outside'),'outside');
  await assert.rejects(abandonNativeSpan(f.runtime,f.record,f.definition,f.attempt,f.binding,f.plan),{code:kind==='scope'?'NATIVE_SPAN_SCOPE':'NATIVE_SPAN_UNSETTLED'});
 });
});
