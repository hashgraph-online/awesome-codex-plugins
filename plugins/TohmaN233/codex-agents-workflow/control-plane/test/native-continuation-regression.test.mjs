import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { randomUUID } from 'node:crypto';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { WorkflowRunStore, withRunStoreObservation } from '../lib/workflow-run-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { withForegroundOperationObservation } from '../lib/foreground-operation-observation.mjs';
import fsPromises from 'node:fs/promises';
import { watch } from 'node:fs';
import { syncBuiltinESMExports } from 'node:module';
import { retainOwnedAuthority } from '../lib/execution/owned-workflow-authority.mjs';
import { leaseToken } from '../lib/workflow-execution-envelope.mjs';
import { inspectNativeAgents,waitForNativeSessionEvent } from '../lib/execution/native-agent-observer.mjs';
import { deferred } from './fixtures/deferred.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { HostToolRunner } from '../lib/execution/host-tool-runner.mjs';
import { workerHostCheckContext,executeWorkerHostCheck,readNativeTextRepair } from '../lib/execution/worker-host-check.mjs';
import { WorkflowExecutor,compilePrompt } from '../lib/workflow-executor.mjs';
import { WorkflowDrive } from '../lib/workflow-drive.mjs';
import { workflowResourceProgramIdentity,workflowResourceProgramRegistry } from '../lib/execution/workflow-resource-program.mjs';
import {captureNativeWorkspace} from '../lib/execution/native-dispatch-span.mjs';
import {readNativeTaskProjection} from '../lib/execution/node-input-materials.mjs';

const PARENT_THREAD_ID = '00000000-0000-7000-8000-000000000001';
const MODEL_REQUEST = Object.freeze({ model: true, modelThreadId: PARENT_THREAD_ID });

test('native parallel collection overlaps independent checker work before public acknowledgement closes',async t=>{
  const started=deferred(),both=deferred(),release=deferred();let active=0,peak=0,settled=0;
  const f=await nativeCheckFixture(t,{itemCount:2,maxConcurrency:2,orchestration:true,checkerDeadline:10000,execute:async request=>{
    peak=Math.max(peak,++active);started.resolve();if(active===2)both.resolve();
    await release.promise;
    await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.summary);
    active--;settled++;
    return {exit_code:0,output:{complete:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};
  }});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const pending=f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  pending.catch(()=>{}); // The release finally below always joins the original operation.
  let timer;
  try{
    await Promise.race([started.promise,pending]);
    await Promise.race([both.promise,new Promise((_resolve,reject)=>{timer=setTimeout(()=>reject(new Error('Independent checker overlap barrier was not reached')),3000);})]);
  }finally{clearTimeout(timer);release.resolve();await pending;
    console.log('NATIVE_PARALLEL_COLLECTION_BARRIER '+JSON.stringify({peak,settled,active,observer_calls:f.seen.length,checker_calls:f.calls.length}));}
  assert.equal(peak,2);assert.equal(active,0);assert.equal(settled,2);
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,[{summary:'accepted 1'},{summary:'accepted 1'}]);
});

test('native parallel checker admission overlaps independent items and excludes an exact duplicate slot',async t=>{
  const started=deferred(),both=deferred(),release=deferred();let arrivals=0;
  const f=await nativeCheckFixture(t,{itemCount:2,maxConcurrency:2,checkerDeadline:10000,execute:async request=>{
    started.resolve();if(++arrivals===2)both.resolve();await release.promise;
    await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.summary);
    return {exit_code:0,output:{complete:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};
  }});
  const c=await nativeCheckContext(f),{executor}=await f.service.open();
  const sibling={index:1,agent_id:'/root/'+publicPackets(c.handoff)[1].spawn_config.task_name,turn_id:'independent-sibling-terminal'};
  await recordNativeSpawn(f,{...f.binding,attempt_id:c.attempt.id,index:sibling.index,agent_id:sibling.agent_id});
  const first=executor.executeNativeHostCheck(f.run.run_id,c.binding,c.output,{item_index:0,native_observation:c.native_observation});
  first.catch(()=>{}); // Joined after releasing the owned checker below.
  let second;
  try{
    await started.promise;
    await assert.rejects(executor.executeNativeHostCheck(f.run.run_id,c.binding,c.output,{item_index:0,native_observation:c.native_observation}),{code:'ATTEMPT_DUPLICATE'});
    second=executor.executeNativeHostCheck(f.run.run_id,c.binding,c.output,{item_index:1,native_observation:sibling});
    second.catch(()=>{});await both.promise;
    const owners=f.service.attemptAdmission.pendingAttempt(f.run.run_id,'worker',c.attempt.id);
    assert.equal(owners.length,2);assert(owners.every(owner=>!owner.settled&&!owner.controller.signal.aborted));
    assert.throws(()=>f.service.attemptAdmission.begin(f.run.run_id,'worker',c.attempt.id,'host_tool'),{code:'ATTEMPT_DUPLICATE'});
    assert.equal(f.calls.length,2,'The rejected duplicate must not execute another checker');
  }finally{release.resolve();await Promise.all([first,second].filter(Boolean));}
  assert.equal(f.service.attemptAdmission.pendingAttempt(f.run.run_id,'worker',c.attempt.id).length,0);
});

test('native parallel collection cancels and drains every started exact checker slot',async t=>{
  const both=deferred();let started=0;
  const f=await nativeCheckFixture(t,{itemCount:2,maxConcurrency:2,checkerDeadline:10000,execute:request=>{
    if(++started===2)both.resolve();
    return new Promise((_resolve,reject)=>request.signal.addEventListener('abort',()=>reject(new Error('exact parallel checker cancelled')),{once:true}));
  }});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),pending=f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  const rejected=assert.rejects(pending);
  await both.promise;
  const {runtime}=await f.service.open();await runtime.cancel(f.run.run_id,f.binding,()=>f.service.attemptAdmission.fenceRun(f.run.run_id));await rejected;
  const record=await runtime.runs.read(f.run.run_id),attempt=record.state.nodes.worker.attempts[0],slots=Object.values(attempt.worker_host_checks);
  assert.equal(slots.length,2);assert(slots.every(slot=>slot.receipt.reconciliation.termination_confirmed));
  assert.equal(Object.keys(attempt.native_item_results??{}).length,0);assert.equal(f.service.attemptAdmission.pending(f.run.run_id).length,0);
});

test('native parallel collection stops inspection after original checker failure and joins held sibling cleanup',async t=>{
  const both=deferred(),waiting=deferred(),releaseFailure=deferred(),releaseSibling=deferred(),aborted=deferred();let starts=0,closed=false;
  const f=await nativeCheckFixture(t,{itemCount:3,maxConcurrency:3,checkerDeadline:10000,execute:async request=>{
    if(++starts===2)both.resolve();
    if(request.input.inputs.jobs[0].name==='a'){await releaseFailure.promise;throw new Error('original parallel checker failure');}
    await releaseSibling.promise;
    return {exit_code:0,output:{complete:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};
  }});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),ids=publicPackets(handoff).map(packet=>'/root/'+packet.spawn_config.task_name);
  f.service.nativeAgentObserver=async(pending,options)=>{
    const id=pending[0];if(id===ids[2]){waiting.resolve();return new Promise((_resolve,reject)=>options.signal.addEventListener('abort',()=>{aborted.resolve();reject(options.signal.reason);},{once:true}));}
    return {status:'completed',agent_id:id,turn_id:'original-failure-turn-'+ids.indexOf(id),result:{items:[{outcome:'completed',result:{summary:'original proposal'}}]}};
  };
  const pending=f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  const rejected=assert.rejects(pending,error=>error.message.includes('original parallel checker failure'));pending.finally(()=>{closed=true;}).catch(()=>{});
  try{await both.promise;await waiting.promise;releaseFailure.resolve();await aborted.promise;assert.equal(closed,false);}
  finally{releaseFailure.resolve();releaseSibling.resolve();await rejected;}
  assert.equal(f.calls.length,2);assert.equal(f.service.attemptAdmission.pending(f.run.run_id).length,0);
});

test('native parallel collection overlaps the actual neutral Node resource checker in independent item workspaces',async t=>{
  const nativeCheckerProgram='import {readFileSync,writeFileSync,watch,existsSync} from "node:fs";const value=JSON.parse(readFileSync(process.argv[2],"utf8"));if(value.inputs.jobs.length!==1)throw new Error("routing");const released=new Promise(resolve=>{const watcher=watch(".",(_event,file)=>{if(String(file)===".release"){watcher.close();resolve();}});if(existsSync(".release")){watcher.close();resolve();}});writeFileSync(".started",value.inputs.jobs[0].name);await released;writeFileSync("rendered.txt",value.output.summary);console.log(JSON.stringify({complete:true,diagnostic:""}));';
  const f=await nativeCheckFixture(t,{itemCount:2,maxConcurrency:2,orchestration:true,qualifiedResource:true,nativeCheckerProgram});
  const watchers=[],arrived=Promise.all(f.jobs.map(job=>new Promise(resolveStarted=>{
    const watcher=watch(join(f.workspace,job.workspace),(_event,file)=>{if(String(file)==='.started')resolveStarted();});watchers.push(watcher);
  })));
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),pending=f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  pending.catch(()=>{});let timer;
  try{await Promise.race([arrived,new Promise((_resolve,reject)=>{timer=setTimeout(()=>reject(new Error('Real Node checker overlap barrier was not reached')),5000);})]);}
  finally{clearTimeout(timer);await Promise.all(f.jobs.map(job=>writeFile(join(f.workspace,job.workspace,'.release'),'release')));try{await pending;}finally{watchers.forEach(watcher=>watcher.close());}}
  const state=await f.service.call('get',f.binding),slots=Object.values(state.nodes.worker.attempts[0].worker_host_checks);
  assert.equal(state.nodes.worker.status,'succeeded');assert.equal(slots.length,2);
  assert(slots.every(slot=>slot.receipt.status==='succeeded'));
  for(const job of f.jobs)assert.equal(await readFile(join(f.workspace,job.workspace,'.started'),'utf8'),job.name);
});

test('native terminal public success returns the exact committed semantic output',async t=>{
 const finalSchema=checkObject({accepted:{type:'boolean'},semantic_result:{type:'string'}});
 const f=await nativeCheckFixture(t,{single:true,orchestration:true,finalSchema});
 const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
 assert.equal((await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST)).status,'orchestration_handoff');
 const output={accepted:true,semantic_result:'Ready: [one](./one.html), [two](./two.html), [三](./three.html).'};
 const result=await f.service.call('orchestration_complete',{output},MODEL_REQUEST);
 const state=await f.service.call('get',f.binding);
 assert.equal(result.status,'succeeded');assert.equal(result.completion_satisfied,true);assert.deepEqual(result.output,state.output);
 assert.equal(result.output.semantic_result,output.semantic_result);
 await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'MODEL_RUN_AUTHORITY'});
 const terminal=await f.service.call('native_next',f.binding);assert.deepEqual(terminal.output,state.output);
 const waited=await f.service.call('wait',{...f.binding,timeout_ms:1000});assert.deepEqual(waited.output,state.output);
});

for(const shape of ['completion envelope','blocked envelope','bare semantic result'])test(`native parser result shape public collection accepts ${shape}`,async t=>{
  const f=await nativeCheckFixture(t,{single:true,orchestration:true});
  const home=await mkdtemp(join(tmpdir(),'native-result-shape-')),sessions=join(home,'sessions');await mkdir(sessions);
  t.after(()=>rm(home,{recursive:true,maxRetries:3,retryDelay:100}));
  const threadId=randomUUID(),path=join(sessions,`rollout-${threadId}.jsonl`),parsed=[],rpc=[];let ordinal=0;
  f.service.nativeAgentObserver=async(ids,options)=>{
    assert.equal(ids.length,1);assert.equal(options.parentThreadId,PARENT_THREAD_ID);
    const agentPath=ids[0],turnId='neutral-parser-turn-'+(++ordinal),blocked=shape==='blocked envelope'&&ordinal===1;
    const semantic={summary:'Exact neutral parser proposal'};
    const payload=blocked?{outcome:'blocked',block_reason:'Neutral semantic correction required.'}
      :shape==='bare semantic result'?semantic:{outcome:'completed',result:semantic};
    const spawn={parent_thread_id:PARENT_THREAD_ID,agent_path:agentPath};
    const thread={id:threadId,parentThreadId:PARENT_THREAD_ID,path,source:{subAgent:{thread_spawn:spawn}}};
    const row=(type,payload)=>JSON.stringify({timestamp:'2026-10-09T07:00:00.000Z',type,payload})+'\n';
    // Actual durable lifecycle reader, exact parent-scoped identity and final parser.
    await writeFile(path,row('session_meta',{id:threadId,parent_thread_id:PARENT_THREAD_ID,agent_path:agentPath,
      source:{subagent:{thread_spawn:spawn}}})+row('event_msg',{type:'task_started',turn_id:turnId})
      +row('event_msg',{type:'task_complete',turn_id:turnId}));
    const client={async call(method,args){rpc.push({method,args});
      if(method==='thread/list')return {data:[thread]};
      if(method==='thread/read')return {thread};
      assert.equal(method,'thread/turns/list');
      return {data:[{id:turnId,status:'completed',itemsView:args.itemsView,
        items:args.itemsView==='full'?[{type:'agentMessage',phase:'final_answer',text:JSON.stringify(payload)}]:[]}]};
    }};
    const observed=await inspectNativeAgents(client,ids,{...options,lifecycleHome:home});parsed.push(observed);return observed;
  };
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  let result=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  if(shape==='blocked envelope'){
    assert.equal(parsed[0].status,'blocked');assert.equal(result.next_action,'repair_recorded_agent');assert.equal(f.calls.length,0);
    assert.equal(result.followup_config.target,parsed[0].agent_id);
    result=await f.service.call('native_followed_up',{},MODEL_REQUEST);
    assert.equal(parsed[1].agent_id,parsed[0].agent_id);assert.notEqual(parsed[1].turn_id,parsed[0].turn_id);
  }
  assert.equal(result.status,'orchestration_handoff');assert.equal(f.calls.length,1);
  assert.equal(f.calls[0].input.output.summary,'Exact neutral parser proposal');
  const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
  assert.equal(state.nodes.worker.status,'succeeded');
  const diagnostics=attempt.executor_events.filter(event=>event.kind==='session_state'&&event.metadata.status==='native_result_shape');
  assert.equal(diagnostics.length,parsed.length);
  diagnostics.forEach((event,index)=>{
    assert.deepEqual(Object.keys(event.metadata).sort(),['code','diagnostic','status']);
    assert.equal(event.metadata.code,'NATIVE_AGENT_RESULT_SHAPE');assert(event.metadata.diagnostic.includes(parsed[index].result_shape));
  });
  assert.equal(parsed[0].result_shape,shape==='bare semantic result'?'bare_semantic_result':'completion_envelope');
  assert(rpc.some(item=>item.method==='thread/list'));assert(rpc.some(item=>item.method==='thread/turns/list'&&item.args.itemsView==='full'));
});

test('native parser result shape diagnostic retains exact bounded type and native authority guards',async t=>{
  const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
  const path=join(c.runtime.runs.directory(f.run.run_id),'events.jsonl'),before=await readFile(path);
  const event={kind:'session_state',metadata:{status:'native_result_shape',code:'NATIVE_AGENT_RESULT_SHAPE',
    diagnostic:'Exact Host parser completion_envelope diagnostic'}};
  const invoke=(value,override={})=>c.runtime.recordNativeExecutorEvent(f.run.run_id,{...c.binding,...override,event:value});
  for(const metadata of [{status:'native_result_shape',diagnostic:'missing code'},
    {...event.metadata,code:'OTHER_CODE'},{...event.metadata,diagnostic:''},
    {...event.metadata,status:'native_result_shape_unknown'}])await assert.rejects(invoke({kind:'session_state',metadata}),{code:'NATIVE_JOURNAL_KIND'});
  await assert.rejects(invoke({...event,metadata:{...event.metadata,proposal:'semantic'}}),{code:'EXECUTOR_EVENT_SCHEMA'});
  await assert.rejects(invoke({...event,metadata:{...event.metadata,diagnostic:'x'.repeat(4097)}}),{code:'EXECUTOR_EVENT_SCHEMA'});
  await assert.rejects(invoke(event,{control_token:'wrong'}),{code:'RUN_AUTHORITY'});
  await assert.rejects(invoke(event,{lease_token:'wrong'}),{code:'LEASE_INVALID'});
  await assert.rejects(invoke(event,{attempt_id:'foreign'}),{code:'LEASE_INVALID'});
  await assert.rejects(invoke(event,{node_id:'final'}),{code:'NATIVE_JOURNAL_BINDING'});
  assert.deepEqual(await readFile(path),before);
  await invoke(event);const record=await c.runtime.runs.read(f.run.run_id);
  assert.deepEqual(record.state.nodes.worker.attempts[0].executor_events.at(-1),
    {sequence:record.state.nodes.worker.attempts[0].executor_event_count,...event});
});

test('native lock boundary measures the complete public acknowledgement with 73 pinned resources',async t=>{
  const resources=Object.fromEntries(Array.from({length:73},(_,index)=>['neutral/resource-'+index+'.txt','Neutral pinned resource '+index]));
  const f=await nativeCheckFixture(t,{itemCount:3,orchestration:true,resources});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const methods={},journal_events={},read_callers={},restores=[],originalRead=fsPromises.readFile;let objects=0,foreground;
  for(const name of Object.getOwnPropertyNames(WorkflowRunStore.prototype)){
    if(name==='constructor'||typeof WorkflowRunStore.prototype[name]!=='function')continue;
    const original=WorkflowRunStore.prototype[name];
    WorkflowRunStore.prototype[name]=function(...args){methods[name]=(methods[name]??0)+1;
      if(name==='mutate'||name==='mutateNativeJournal'){const key=name+':'+args[1];journal_events[key]=(journal_events[key]??0)+1;}
      if(name==='read'){const caller=new Error().stack.split('\n').slice(2,6).join(' | ');read_callers[caller]=(read_callers[caller]??0)+1;}
      return Reflect.apply(original,this,args);};
    restores.push(()=>{WorkflowRunStore.prototype[name]=original;});
  }
  fsPromises.readFile=async function(path,...args){if(/[\\/]objects[\\/][0-9a-f]{64}$/.test(String(path)))objects++;return originalRead(path,...args);};
  syncBuiltinESMExports();let result;
  try{result=await withForegroundOperationObservation(()=>f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),report=>{foreground=report;});}
  finally{for(const restore of restores)restore();fsPromises.readFile=originalRead;syncBuiltinESMExports();}
  assert.equal(result.status,'orchestration_handoff');assert.equal(f.calls.length,3);
  assert.equal(objects,0,'Neutral continuation consumes no resources and ordinary reads do not audit objects');
  const report={phase:process.env.NATIVE_BOUNDARY_PHASE??'current',resource_inventory:73,full_resource_audit_count:objects/73,
    resource_objects:objects,methods,journal_events,read_callers,journal_methods:Object.fromEntries(Object.entries(methods).filter(([name])=>/mutate|append|Executor|Observation/.test(name))),
    foreground,distinct_admissions:foreground.n[0]-foreground.n[3]};
  console.log('NATIVE_ACK_BOUNDARY_MEASUREMENT '+JSON.stringify(report));
  if(process.env.NATIVE_BOUNDARY_MEASUREMENT_PATH)await writeFile(process.env.NATIVE_BOUNDARY_MEASUREMENT_PATH,JSON.stringify(report,null,2)+'\n');
  if(report.phase==='current')assert(report.full_resource_audit_count<100,'Public acknowledgement still repeatedly audits the complete inventory');
});
test('native lock boundary cooperative ACK avoids adjacent controller audits and generic joined-receipt mutations',async t=>{
  const f=await nativeCheckFixture(t,{itemCount:3,orchestration:true});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),counts={controller:0,managed:0};
  const controller=WorkflowRuntime.prototype.authorizeController,managed=WorkflowRuntime.prototype.recordManagedNativeResults;
  WorkflowRuntime.prototype.authorizeController=function(...args){counts.controller++;return Reflect.apply(controller,this,args);};
  WorkflowRuntime.prototype.recordManagedNativeResults=function(...args){counts.managed++;return Reflect.apply(managed,this,args);};
  let result;
  try{result=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);}
  finally{WorkflowRuntime.prototype.authorizeController=controller;WorkflowRuntime.prototype.recordManagedNativeResults=managed;}
  assert.equal(result.status,'orchestration_handoff');assert.equal(f.calls.length,3);
  assert.deepEqual(counts,{controller:0,managed:0},'A cooperative ACK repeated adjacent controller authority and used the generic full-audited joined receipt API');
});
test('native lock boundary explicit native observation API refuses semantic unknown foreign and stale events',async t=>{
  const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
  const path=join(c.runtime.runs.directory(f.run.run_id),'events.jsonl'),before=await readFile(path);
  const invoke=(event,override={})=>c.runtime.recordNativeExecutorEvent(f.run.run_id,{...c.binding,...override,event});
  await assert.rejects(invoke({kind:'result_proposed',metadata:{sha256:digest('proposal'),artifact:'proposal'}}),{code:'NATIVE_JOURNAL_KIND'});
  await assert.rejects(invoke({kind:'session_state',metadata:{status:'closed'}}),{code:'NATIVE_JOURNAL_KIND'});
  await assert.rejects(invoke({kind:'unknown',metadata:{}}),{code:'EXECUTOR_EVENT_SCHEMA'});
  const event={kind:'session_state',metadata:{status:'native_render_preflight'}};
  await assert.rejects(invoke(event,{node_id:'final'}),{code:'NATIVE_JOURNAL_BINDING'});
  await assert.rejects(invoke(event,{lease_token:'wrong'}),{code:'LEASE_INVALID'});
  await assert.rejects(invoke(event,{control_token:'wrong'}),{code:'RUN_AUTHORITY'});
  assert.deepEqual(await readFile(path),before);
});
test('native lock boundary cooperative joined receipts preserve the generic managed audit and refuse another backend',async t=>{
  const f=await nativeCheckFixture(t,{qualifiedResource:true,observer:async()=>{throw Object.assign(new Error('Neutral collection remains pending'),{code:'EPERM'});}});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),{code:'EPERM'});
  const state=await f.service.call('get',f.binding);
  const c=await nativeAttemptContext(f,{...f.binding,attempt_id:state.nodes.worker.active_attempt_id});
  const results=c.attempt.dispatch.receipt.agent_ids.map((agent_id,result_index)=>({agent_id,dispatch_id:agent_id,result_index,result_sha256:digest('neutral '+result_index)}));
  const original=c.runtime.runs.read.bind(c.runtime.runs);let reads=0;
  c.runtime.runs.read=(...args)=>{reads++;return original(...args);};
  await c.runtime.recordManagedNativeResults(f.run.run_id,{...c.binding,results});assert.equal(reads,1);
  reads=0;await c.runtime.recordCooperativeNativeResults(f.run.run_id,{...c.binding,results});assert.equal(reads,1);
  const writer=c.runtime.runs.withRunWriter.bind(c.runtime.runs),entered=deferred(),release=deferred(),mutable=structuredClone(results);
  c.runtime.runs.withRunWriter=async(...args)=>{entered.resolve();await release.promise;return writer(...args);};
  const pending=c.runtime.recordCooperativeNativeResults(f.run.run_id,{...c.binding,results:mutable});
  await entered.promise;mutable[0].result_sha256=digest('changed during admission');release.resolve();await pending;
  c.runtime.runs.withRunWriter=writer;
  await c.runtime.runs.mutate(f.run.run_id,'recover',state=>{state.nodes.worker.attempts[0].dispatch.receipt.executor='codex-managed-native';});
  await assert.rejects(c.runtime.recordCooperativeNativeResults(f.run.run_id,{...c.binding,results}),{code:'NATIVE_JOURNAL_BINDING'});
  reads=0;await c.runtime.recordManagedNativeResults(f.run.run_id,{...c.binding,results});assert.equal(reads,1);
  const record=await original(f.run.run_id),resource=record.pins.resources[0];
  await writeFile(join(c.runtime.runs.directory(f.run.run_id),'pins.json'),'{}');
  await assert.rejects(c.runtime.recordManagedNativeResults(f.run.run_id,{...c.binding,results}),{code:'RUN_PINS_CORRUPT'});
});

test('native lock boundary snapshots pure native input before admission can await',async t=>{
  const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
  const original=c.runtime.runs.withRunWriter.bind(c.runtime.runs),entered=deferred(),release=deferred();
  c.runtime.runs.withRunWriter=async(...args)=>{entered.resolve();await release.promise;return original(...args);};
  const event={kind:'session_state',metadata:{status:'native_render_preflight'}};
  const operation=c.runtime.recordNativeExecutorEvent(f.run.run_id,{...c.binding,event});
  await entered.promise;event.kind='result_proposed';event.metadata={artifact:'unexpected',sha256:digest('unexpected')};
  release.resolve();await operation;c.runtime.runs.withRunWriter=original;
  const record=await c.runtime.runs.read(f.run.run_id);
  assert.deepEqual(record.state.nodes.worker.attempts[0].executor_events.at(-1),
    {sequence:record.state.nodes.worker.attempts[0].executor_event_count,kind:'session_state',metadata:{status:'native_render_preflight'}});
});

test('native lock boundary resolves one authority locator for a three-terminal public acknowledgement drive',async t=>{
  const f=await nativeCheckFixture(t,{itemCount:3,orchestration:true});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const original=WorkflowRunStore.prototype.listForThread;let lookups=0;
  WorkflowRunStore.prototype.listForThread=function(...args){lookups++;return Reflect.apply(original,this,args);};
  let result;
  try{result=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);}
  finally{WorkflowRunStore.prototype.listForThread=original;}
  assert.equal(result.status,'orchestration_handoff');assert.equal(f.calls.length,3);
  assert.equal(lookups,1,'same public acknowledgement recursively scanned unrelated history again');
});

test('native lock boundary reuses the exact execution audit before environment verification and the fresh verified record afterward',async t=>{
  const f=await nativeCheckFixture(t,{qualifiedResource:true}),c=await nativeCheckContext(f);
  const original=c.runtime.runs.read.bind(c.runtime.runs);let reads=0;
  c.runtime.runs.read=(...args)=>{reads++;return original(...args);};
  const result=await c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding);
  assert.equal(result.binding.attempt_id,c.binding.attempt_id);
  assert.equal(reads,2,'execution/environment helpers repeated the same pre/post-verification complete resource audit');
});

test('native lock boundary checker consumes its fresh authorize result instead of an immediate duplicate full read',async t=>{
  const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
  const original=c.runtime.runs.read.bind(c.runtime.runs);let directReads=0;
  c.runtime.runs.read=(...args)=>{
    if(new Error().stack.split('\n')[2]?.includes('executeWorkerHostCheck'))directReads++;
    return original(...args);
  };
  const result=await executeWorkerHostCheck({hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})},
    {runtime:c.runtime,runId:f.run.run_id},c.binding,c.output,{item_index:0,native_observation:c.native_observation,
      authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}});
  assert.equal(result.accepted,true);assert.equal(f.calls.length,1);
  assert.equal(directReads,0,'checker discarded the immediately preceding full authorized snapshot');
});

test('native lock boundary pure executor journal state never rehashes resources or grants execution',async t=>{
  const f=await nativeCheckFixture(t,{qualifiedResource:true}),c=await nativeCheckContext(f);
  const original=c.runtime.runs.read.bind(c.runtime.runs);let reads=0;
  c.runtime.runs.read=(...args)=>{reads++;return original(...args);};
  await c.runtime.recordNativeExecutorEvent(f.run.run_id,{...c.binding,event:{kind:'session_state',metadata:{status:'native_render_preflight'}}});
  assert.equal(reads,1,'journal event uses the unified fresh metadata read');
  const record=await original(f.run.run_id),resource=record.pins.resources[0];
  await writeFile(join(c.runtime.runs.directory(f.run.run_id),'pins.json'),'{}');
  await assert.rejects(c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),{code:'RUN_PINS_CORRUPT'});
  await assert.rejects(c.runtime.completeNode(f.run.run_id,{...c.binding,completion:{status:'succeeded',summary:'neutral completion',
    structured_output:{summaries:[]},artifacts:[],evidence:[{kind:'neutral'}],changed_paths:[],outside_paths:[]}}),{code:'RUN_PINS_CORRUPT'});
});
test('native lock boundary native proposal and usage journal commits require fresh metadata without repeated execution audits',async t=>{
  const f=await nativeCheckFixture(t,{qualifiedResource:true}),c=await nativeCheckContext(f);
  const original=c.runtime.runs.read.bind(c.runtime.runs);let reads=0;
  c.runtime.runs.read=(...args)=>{reads++;return original(...args);};
  await c.runtime.recordNativeHostCheckProposal(f.run.run_id,{...c.binding,item_index:0,native_observation:c.native_observation,output:c.output});
  await c.runtime.recordNativeUsage(f.run.run_id,{...c.binding,request_id:c.attempt.dispatch.request_id,usage:{unknown:true}});
  assert.equal(reads,2,'proposal and usage each use a fresh metadata read');
  const record=await original(f.run.run_id),resource=record.pins.resources[0];
  await writeFile(join(c.runtime.runs.directory(f.run.run_id),'pins.json'),'{}');
  await assert.rejects(c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),{code:'RUN_PINS_CORRUPT'});
});
test('native lock boundary immediate checker preparation retains only actual execution boundary audits',async t=>{
  const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
  const original=c.runtime.runs.read.bind(c.runtime.runs);let reads=0;
  c.runtime.runs.read=(...args)=>{reads++;return original(...args);};
  const checked=await executeWorkerHostCheck({hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})},
    {runtime:c.runtime,runId:f.run.run_id},c.binding,c.output,{item_index:0,native_observation:c.native_observation,
      authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}});
  assert.equal(checked.accepted,true);assert.equal(reads,4,'Initial/post-effect authorization and both journal commits read fresh metadata without consuming unused objects');
});
test('native lock boundary committed pins tampering across actual checker effects fails before semantic acceptance',async t=>{
  let resourcePath;
  const f=await nativeCheckFixture(t,{resources:{'neutral.txt':'sealed neutral'},execute:async request=>{
    await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.summary);await writeFile(resourcePath,'{}');
    return {exit_code:0,output:{complete:true,diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};
  }}),c=await nativeCheckContext(f);
  resourcePath=join(c.runtime.runs.directory(f.run.run_id),'pins.json');
  await assert.rejects(executeWorkerHostCheck({hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})},
    {runtime:c.runtime,runId:f.run.run_id},c.binding,c.output,{item_index:0,native_observation:c.native_observation,
      authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}}),{code:'RUN_PINS_CORRUPT'});
  assert.equal(f.calls.length,1);
});
const control = run => ({ run_id: run.run_id, control_token: run.control_token });
const publicPackets=value=>{
  assert.equal(value.packets,undefined,'Public child calls must not expose a second raw packet path');
  assert(Array.isArray(value.spawn_calls));
  return value.spawn_calls.map(call=>{
    assert.equal(call.tool,'collaboration.spawn_agent');
    const {message,...spawn_config}=call.arguments;
    return {index:Number(spawn_config.task_name.split('_').at(-1)),spawn_config,prompt:message};
  });
};
const inlineNativeTask=message=>{
  const scope=message.indexOf('Workspace: '),taskStart=message.indexOf('\n\n',scope)+2;
  const schemaStart=message.lastIndexOf('\nResult schema:\n');
  assert(scope>=0&&taskStart>scope&&schemaStart>=taskStart,'The same-child follow-up must contain its direct semantic packet');
  return {task:message.slice(taskStart,schemaStart),result_schema:JSON.parse(message.slice(schemaStart+'\nResult schema:\n'.length).split('\n')[0])};
};
async function publicNativeTask(message){
  const address=message.match(/\nTask bundle: ([^\n]+)\nRead this Host-generated JSON file once,/);
  if(!address)return inlineNativeTask(message);
  const path=JSON.parse(address[1]);assert.equal(typeof path,'string');
  const task=JSON.parse(await readFile(path,'utf8'));
  assert.equal(typeof task.task,'string');assert(task.result_schema);
  return task;
}

test('native model-facing handoff exposes exact spawn tool arguments while retaining internal materials',async t=>{
  for(const upstream of [false,true])await t.test(upstream?'upstream':'fresh',async t=>{
    const f=await nativeCheckFixture(t,{contextInheritance:upstream?'upstream':'fresh',transport:'direct_mcp'});
    const visible=await f.service.call('native_next',{},MODEL_REQUEST);
    const internal=await f.service.call('native_next',f.binding);
    assert.equal(visible.packets,undefined);
    assert.deepEqual(visible.spawn_calls,internal.packets.map(packet=>({tool:'collaboration.spawn_agent',arguments:{...packet.spawn_config,message:packet.prompt}})));
    for(const [index,call] of visible.spawn_calls.entries()){
      assert.equal(call.arguments.fork_turns,upstream?'all':'none');
      assert.equal(call.arguments.model,upstream?undefined:'gpt-6-luna');
      assert.equal(call.arguments.reasoning_effort,upstream?undefined:'max');
      assert.doesNotMatch(call.arguments.message,/Host-only exact baseline/);
      const projection=await readNativeTaskProjection(internal.packets[index],{materialize:true});
      const delivered=projection.inline?projection.task_bundle:JSON.parse(await readFile(projection.task_bundle_path));
      assert.equal((delivered.task.match(/Node worker only\./g)??[]).length,1);
      assert.doesNotMatch(delivered.task,/Host-only exact baseline/);
      if(!projection.inline)assert(call.arguments.message.includes(canonicalJSON(projection.task_bundle_path)));
    }
    for(const key of ['run_id','attempt_id','packets','workspace','access','allowed_paths','result_schema','released_packet_indices','recorded_agent_ids','recovery'])assert.equal(visible[key],undefined,key);
    assert.equal(visible.invocation_adapter.tool_name,'workflow_native_spawned_batch');
    assert.equal(visible.invocation_adapter.kind,'direct_mcp');
    assert.equal(visible.invocation_adapter.tool,'mcp__caw_execution__workflow_native_spawned_batch');
    assert.deepEqual(visible.invocation_adapter.arguments,{batch_id:visible.batch_id});
    for(const key of ['code','budget','pragma','wait'])assert.equal(Object.hasOwn(visible.invocation_adapter,key),false,key);
    assert(internal.packets.every(packet=>packet.task_bundle_path&&/^[a-f0-9]{64}$/.test(packet.task_bundle_sha256)));
    assert.equal(f.service.modelResult(visible).spawn_calls.length,visible.spawn_calls.length,'Model projection must remain idempotent');
  });
});

test('native spawn acknowledgement retries the same durable batch after collector EPERM', async t => {
  const observed=[];
  const failure=Object.assign(new Error('Injected collector journal permission failure'),{code:'EPERM'});
  const f=await fixture(t,async ids=>{
    observed.push([...ids]);
    if(observed.length===1)throw failure;
    return {status:'completed',agent_id:ids[0],turn_id:'turn-recovered-batch',result:{summary:'accepted'}};
  });
  const {binding}=await startRun(f,definition('native-batch-collector-recovery','ordinary'),{task:'one task'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const acknowledgement=handoff.batch_id?{batch_id:handoff.batch_id}:{};
  await assert.rejects(f.service.call('native_spawned_batch',acknowledgement,MODEL_REQUEST),error=>error===failure);
  const before=await f.service.call('get',binding);
  const {runtime:privateRuntime}=await f.service.open(),privateRecord=await privateRuntime.runs.read(binding.run_id);
  assert.equal(JSON.stringify(before).includes(privateRecord.state.control_hash),false);
  assert.equal(JSON.stringify(before).includes(privateRecord.state.nodes.worker.attempts[0].lease_hash),false);
  assert.equal(before.nodes.worker.attempts[0].native_pending_spawns,undefined);
  const agentId=`/root/${publicPackets(handoff)[0].spawn_config.task_name}`;
  assert.deepEqual(before.nodes.worker.attempts[0].native_agents,{'0':agentId});
  f.service=new WorkflowService({configPath:f.service.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,
    env:{},capabilities:f.service.capabilities});
  const recovered=await f.service.call('native_spawned_batch',acknowledgement,MODEL_REQUEST);
  assert.equal(recovered.journaled_spawn_count,1);
  const legacyRetry=await f.service.call('native_spawned_batch',{},MODEL_REQUEST);
  assert.equal(legacyRetry.acknowledged_batch_id,handoff.batch_id);
  assert.deepEqual(observed,[[agentId],[agentId]]);
  const after=await f.service.call('get',binding);
  assert.equal(after.nodes.worker.status,'succeeded');
  assert.equal(after.nodes.worker.attempts[0].executor_events.filter(event=>event.kind==='native_agent_spawn').length,1);
});

test('native spawn batch resumes only uncommitted slots after a partial multi-slot journal failure',async t=>{
  const jobs=Array.from({length:20},(_,index)=>index),observed=[];
  const f=await fixture(t,async ids=>{
    observed.push([...ids]);
    const {runtime}=await f.service.open(),records=await runtime.runs.listForThread(PARENT_THREAD_ID);
    const attempt=records[0].state.nodes.worker.attempts[0];
    const index=Number(Object.entries(attempt.native_agents).find(([,id])=>id===ids[0])[0]);
    return {status:'completed',agent_id:ids[0],turn_id:`partial-turn-${index}`,result:jobs.slice(index*10,(index+1)*10)};
  });
  const {binding}=await startRun(f,definition('native-batch-partial-journal','capped-two'),{jobs});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),args={batch_id:handoff.batch_id};
  const open=f.service.open.bind(f.service);let failSecond=true;
  f.service.open=async(...options)=>{
    const result=await open(...options),record=result.runtime.recordNativeExecutorEvent.bind(result.runtime);
    result.runtime.recordNativeExecutorEvent=async(...call)=>{
      if(failSecond&&call[1].event.kind==='native_agent_spawn'&&call[1].event.metadata.index===1){
        failSecond=false;throw Object.assign(new Error('Injected second-slot journal failure'),{code:'EPERM'});
      }
      return record(...call);
    };return result;
  };
  await assert.rejects(f.service.call('native_spawned_batch',args,MODEL_REQUEST),{code:'EPERM'});
  const partial=(await f.service.call('get',binding)).nodes.worker.attempts[0];
  assert.deepEqual(partial.native_spawn_batches[handoff.batch_id].acknowledged_indices,[0]);
  assert.deepEqual(Object.keys(partial.native_pending_spawns),['1']);assert.deepEqual(observed,[]);
  const completed=await f.service.call('native_spawned_batch',args,MODEL_REQUEST);
  assert.equal(completed.journaled_spawn_count,2);
  const finished=(await f.service.call('get',binding)).nodes.worker.attempts[0];
  assert.deepEqual(finished.native_spawn_batches[handoff.batch_id].acknowledged_indices,[0,1]);
  assert.equal(finished.executor_events.filter(event=>event.kind==='native_agent_spawn').length,2);
});

test('an old native batch adapter cannot acknowledge an unseen window after continuation fails',async t=>{
  const jobs=Array.from({length:21},(_,index)=>index);
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:'old-window-turn',result:jobs.slice(0,10)}));
  const {binding}=await startRun(f,definition('native-batch-unseen-window','capped-two'),{jobs});
  const first=await f.service.call('native_next',{},MODEL_REQUEST),args={batch_id:first.batch_id};
  const publish=f.service.persistModelSpawnWindow.bind(f.service);let failReturnedWindow=true;
  f.service.persistModelSpawnWindow=async(...args)=>{
    const result=await publish(...args);
    if(failReturnedWindow&&result.batch_id&&result.batch_id!==first.batch_id){
      failReturnedWindow=false;throw Object.assign(new Error('Injected error after next-window publication'),{code:'EPERM'});
    }return result;
  };
  await assert.rejects(f.service.call('native_spawned_batch',args,MODEL_REQUEST),{code:'EPERM'});
  const before=(await f.service.call('get',binding)).nodes.worker.attempts[0];
  assert.deepEqual(Object.keys(before.native_agents),['0','1']);
  assert.deepEqual(Object.keys(before.native_pending_spawns),['2']);
  await assert.rejects(f.service.call('native_spawned_batch',{},MODEL_REQUEST),{code:'NATIVE_AGENT_BATCH_AMBIGUOUS'});
  const recovered=await f.service.call('native_spawned_batch',args,MODEL_REQUEST);
  assert.deepEqual(publicPackets(recovered).map(packet=>packet.index),[2]);
  assert.notEqual(recovered.batch_id,first.batch_id);assert.equal(recovered.acknowledged_batch_id,first.batch_id);
  const after=(await f.service.call('get',binding)).nodes.worker.attempts[0];
  assert.deepEqual(after.native_agents,before.native_agents);
  assert.deepEqual(after.native_pending_spawns,before.native_pending_spawns);
});

test('native batch retry after node advancement reuses its receipt and never respawns or recollects',async t=>{
  let observations=0;
  const f=await fixture(t,async ids=>{
    observations++;return {status:'completed',agent_id:ids[0],turn_id:'advanced-turn',result:{summary:'accepted'}};
  });
  const {binding}=await startRun(f,definition('native-batch-after-advancement','ordinary'),{task:'one task'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),args={batch_id:handoff.batch_id};
  const call=f.service.call.bind(f.service);let failAfterAdvance=true;
  f.service.call=async(operation,...rest)=>{
    const result=await call(operation,...rest);
    if(operation==='native_spawned_batch'&&failAfterAdvance){failAfterAdvance=false;
      throw Object.assign(new Error('Injected delivery error after native node completion'),{code:'EPERM'});
    }return result;
  };
  await assert.rejects(f.service.call('native_spawned_batch',args,MODEL_REQUEST),{code:'EPERM'});
  assert.equal((await f.service.call('get',binding)).nodes.worker.status,'succeeded');
  const retry=await f.service.call('native_spawned_batch',args,MODEL_REQUEST);
  assert.equal(retry.acknowledged_batch_id,handoff.batch_id);assert.equal(retry.journaled_spawn_count,1);
  assert.equal(observations,1);
});

test('native batch acknowledgement rejects foreign receipt, parent, lease generation and controller authority',async t=>{
  for(const scenario of ['foreign batch','foreign parent','rotated lease','rotated controller','inactive attempt'])await t.test(scenario,async t=>{
    let observations=0;
    const f=await fixture(t,async()=>{observations++;throw new Error('Stale acknowledgement reached collection');});
    const {binding}=await startRun(f,definition('native-batch-fence-'+scenario.replaceAll(' ','-'),'ordinary'),{task:'one task'});
    const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
    const {runtime}=await f.service.open();
    if(scenario==='rotated lease')await runtime.runs.mutate(binding.run_id,'recover',state=>{
      const attempt=state.nodes.worker.attempts[0];attempt.lease_generation=(attempt.lease_generation??0)+1;
      attempt.lease_hash=digest(leaseToken(binding.control_token,binding.run_id,'worker',attempt.id,attempt.lease_generation));
    });
    if(scenario==='rotated controller')await runtime.runs.mutate(binding.run_id,'control_recovery',state=>{
      state.control_hash=digest('different-current-controller');
    });
    if(scenario==='inactive attempt')await runtime.runs.mutate(binding.run_id,'recover',state=>{
      state.status='paused';state.nodes.worker.status='interrupted';state.nodes.worker.attempts[0].status='interrupted';
    });
    const args={batch_id:scenario==='foreign batch'?'0'.repeat(64):handoff.batch_id};
    const request=scenario==='foreign parent'?{...MODEL_REQUEST,modelThreadId:'00000000-0000-7000-8000-000000000002'}:MODEL_REQUEST;
    const code={'foreign batch':'NATIVE_AGENT_BATCH_MISSING','foreign parent':'MODEL_RUN_AUTHORITY',
      'rotated lease':'NATIVE_AGENT_BATCH_STALE','rotated controller':'RUN_AUTHORITY','inactive attempt':'NATIVE_AGENT_BATCH_STALE'}[scenario];
    await assert.rejects(f.service.call('native_spawned_batch',args,request),{code});assert.equal(observations,0);
    const record=await runtime.runs.read(binding.run_id);
    assert.deepEqual(record.state.nodes.worker.attempts[0].native_agents??{},{});
  });
});

test('terminal native batch retry explicitly rejects without safe current invocation authority',async t=>{
  const f=await fixture(t,async()=>{throw Object.assign(new Error('Injected collector failure'),{code:'EPERM'});});
  const {binding}=await startRun(f,definition('native-batch-terminal-authority','ordinary'),{task:'one task'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),args={batch_id:handoff.batch_id};
  await assert.rejects(f.service.call('native_spawned_batch',args,MODEL_REQUEST),{code:'EPERM'});
  const attempt_id=(await f.service.call('get',binding)).nodes.worker.active_attempt_id;
  const {runtime,binding:lease}=await nativeAttemptContext(f,{...binding,attempt_id});
  await runtime.failNode(binding.run_id,{...lease,error:{code:'TEST_TERMINAL',message:'Exact terminal boundary'}});
  await assert.rejects(f.service.call('native_spawned_batch',args,MODEL_REQUEST),{code:'MODEL_RUN_AUTHORITY'});
  const record=await runtime.runs.read(binding.run_id);
  assert.deepEqual(record.state.nodes.worker.attempts[0].native_spawn_batches[handoff.batch_id].acknowledged_indices,[0]);
});

test('a new authenticated startup never inherits a previous Run native batch adapter',async t=>{
  const f=await fixture(t,async()=>{throw Object.assign(new Error('Injected collector failure'),{code:'EPERM'});});
  const firstRun=await startRun(f,definition('native-batch-old-startup','ordinary'),{task:'old task'});
  const first=await f.service.call('native_next',{},MODEL_REQUEST),oldArgs={batch_id:first.batch_id};
  await assert.rejects(f.service.call('native_spawned_batch',oldArgs,MODEL_REQUEST),{code:'EPERM'});
  const attempt_id=(await f.service.call('get',firstRun.binding)).nodes.worker.active_attempt_id;
  const context=await nativeAttemptContext(f,{...firstRun.binding,attempt_id});
  await context.runtime.failNode(firstRun.binding.run_id,{...context.binding,error:{code:'TEST_NEW_STARTUP',message:'Old invocation ended'}});
  // An uncertain old child still owns its original workspace. A distinct
  // authenticated startup may use a different root; it cannot erase that owner.
  f.workspace=join(f.workspace,'..','new-startup-workspace');await mkdir(f.workspace);
  const secondRun=await startRun(f,definition('native-batch-new-startup','ordinary'),{task:'new task'});
  const second=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.notEqual(second.batch_id,first.batch_id);
  await assert.rejects(f.service.call('native_spawned_batch',oldArgs,MODEL_REQUEST),{code:'NATIVE_AGENT_BATCH_MISSING'});
  const state=await f.service.call('get',secondRun.binding);
  assert.deepEqual(state.nodes.worker.attempts[0].native_agents??{},{});
});

test('native batch continuation fences a lease rotated after the final slot acknowledgement',async t=>{
  let observations=0;
  const f=await fixture(t,async()=>{observations++;throw new Error('Rotated lease reached collection');});
  const {binding}=await startRun(f,definition('native-batch-lease-rotation-race','ordinary'),{task:'one task'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const {runtime}=await f.service.open(),original=WorkflowRunStore.prototype.mutateExecutorJournal;let rotate=true;
  WorkflowRunStore.prototype.mutateExecutorJournal=async function(...args){
    const result=await Reflect.apply(original,this,args);
    if(rotate&&result.state.run_id===binding.run_id&&result.state.nodes.worker.attempts[0].native_spawn_batches?.[handoff.batch_id]?.acknowledged_indices.length===1){rotate=false;await runtime.runs.mutate(binding.run_id,'recover',state=>{
      const attempt=state.nodes.worker.attempts[0];attempt.lease_generation=(attempt.lease_generation??0)+1;
      attempt.lease_hash=digest(leaseToken(binding.control_token,binding.run_id,'worker',attempt.id,attempt.lease_generation));
    });}
    return result;
  };
  try{await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),{code:'NATIVE_AGENT_BATCH_STALE'});}
  finally{WorkflowRunStore.prototype.mutateExecutorJournal=original;}
  assert.equal(observations,0);
  const record=await runtime.runs.read(binding.run_id);
  assert.deepEqual(record.state.nodes.worker.attempts[0].native_spawn_batches[handoff.batch_id].acknowledged_indices,[0]);
});

async function nativeAttemptContext(f,args){
  const {runtime}=await f.service.open();await runtime.authorizeController(args.run_id,{control_token:args.control_token});
  const record=await runtime.runs.read(args.run_id);
  const match=record.pins.root.workflow.nodes.flatMap(definition=>{
    const attempt=record.state.nodes[definition.id]?.attempts.find(item=>item.id===args.attempt_id);
    return attempt?[{definition,attempt}]:[];
  });
  assert.equal(match.length,1,'Test must identify one native attempt');
  const {definition,attempt}=match[0],binding={run_id:args.run_id,node_id:definition.id,attempt_id:attempt.id,
    lease_token:leaseToken(args.control_token,args.run_id,definition.id,attempt.id,attempt.lease_generation??0),
    control_token:args.control_token};
  return {runtime,record,definition,attempt,binding};
}

async function recordNativeSpawn(f,args){
  const {runtime,binding}=await nativeAttemptContext(f,args);
  await runtime.recordNativeExecutorEvent(args.run_id,{...binding,event:{kind:'native_agent_spawn',metadata:{index:args.index,agent_id:args.agent_id}}});
  return {recorded:true,index:args.index,agent_id:args.agent_id};
}

async function fixture(t, nativeAgentObserver, extraCapabilities={},taskEnv={}) {
  const root = await mkdtemp(join(tmpdir(), 'native-continuation-regression-'));
  const workspace = join(root, 'workspace');
  await mkdir(workspace);
  const configPath = join(root, 'control-plane.json');
  const service = new WorkflowService({
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: taskEnv,
    capabilities: { ...extraCapabilities, nativeAgentObserver, nativeParentVerifier: async () => {} },
  });
  await service.call('migrate_v6', {}, { human: true });
  t.after(async () => {
    await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);
    // History is an independent real owner, even with a mocked native agent.
    // Stop it before deleting its root; preserve both settlement/close faults.
    let historyError;
    try{await service.historyMaintenance.settle();}catch(error){historyError=error;}
    try{await service.historyMaintenance.close();}catch(error){historyError=historyError
      ?new AggregateError([historyError,error],'Native fixture history cleanup failed'):error;}
    if(historyError)throw historyError;
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 });
  });
  return { workspace, service };
}

function delayedReceiptHostMainManager(){
  let current=null,release,launchedResolve;
  const gate=new Promise(resolve=>{release=resolve;});
  const launched=new Promise(resolve=>{launchedResolve=resolve;});
  const manager={launches:0,waits:0,launched,
    async launch({runtime,handoff}){
      if(handoff?.stop_reason!=='main_node')return handoff;
      manager.launches++;
      const binding=handoff.host_binding;
      await runtime.recordHostMainDispatchReceipt(binding.run_id,{...binding,
        request_id:`dispatch-${binding.attempt_id}`,receipt:{invocation_id:`host-main-${binding.attempt_id}`,
          executor:'codex-app-server-host-main',executable_sha256:'0'.repeat(64),model:'gpt-6-sol',effort:'medium',
          main_actor:'root',session_id:`logical-main-${binding.run_id}`,call_chain_id:`workflow-run-${binding.run_id}`}});
      current={runtime,binding};launchedResolve();
      return {run_id:binding.run_id,status:'running',node_id:binding.node_id};
    },
    async wait(runId){manager.waits++;assert.equal(current?.binding.run_id,runId);await gate;return {run_id:runId,status:'failed'};},
    async fail(){
      assert(current);
      await current.runtime.failNode(current.binding.run_id,{...current.binding,
        error:{code:'TEST_HOST_MAIN_STOP',message:'Test completes the joined Host Main owner'}});
      release();
    },
    async pending(){return current?{kind:'host_main',run_id:current.binding.run_id,status:'running'}:null;},
    failureWorker(){return null;},
    fenceAttempt(){},fenceRun(){},async stopAttempt(){},async stopRun(){},
  };
  return manager;
}

function definition(id, mode) {
  const hasFanout = mode !== 'ordinary';
  const outputSchema = hasFanout
    ? { type: 'object', properties: { results: { type: 'array', items: { type: 'array', items: { type: 'integer' } } } }, required: ['results'], additionalProperties: false }
    : { type: 'object', properties: { summary: { type: 'string' } }, required: ['summary'], additionalProperties: false };
  const inputSchema = hasFanout
    ? { type: 'object', properties: { jobs: { type: 'array', items: { type: 'integer' } } }, required: ['jobs'], additionalProperties: false }
    : { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false };
  const fanout = ['capped-one','capped-two'].includes(mode)
    ? { input: 'jobs', item_name: 'job', distribution: 'partition', batch_size: 10, result_output: 'results', scheduling: 'parallel', max_concurrency: mode==='capped-two'?2:4, join: 'all_required' }
    : mode === 'uncapped-three'
      ? { input: 'jobs', item_name: 'job', distribution: 'partition', batch_size: 1, result_output: 'results', scheduling: 'parallel', join: 'all_required' }
      : null;
  const worker = {
    id: 'worker', type: 'agent', role: 'implementer',
    executor: { kind: 'provider', provider_id: 'native-luna' },
    access: 'read_only', approval: { required: false }, retry: { max_attempts: 2 },
    input_bindings: hasFanout ? { jobs: '/inputs/jobs' } : { task: '/inputs/task' },
    prompt_template: hasFanout ? 'Process assigned jobs.' : 'Complete the assigned task.',
    outputs_schema: outputSchema,
    ...(fanout ? { subagent_count: 'auto', fanout } : {}),
  };
  return {
    ...createDraft(id, 'Native continuation regression'),
    status: 'ready',
    skill_policy: { mode: 'cooperative', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: inputSchema,
    finalization: { required: true, node_id: 'final' },
    nodes: [
      { id: 'start', type: 'start' },
      worker,
      {
        id: 'final', type: 'agent', role: 'finalizer', executor: { kind: 'main' },
        access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 },
        input_bindings: hasFanout ? { results: '/nodes/worker/output/results' } : { summary: '/nodes/worker/output/summary' },
        prompt_template: 'Accept the completed work.',
        outputs_schema: { type: 'object', properties: { accepted: { type: 'boolean' } }, required: ['accepted'], additionalProperties: false },
      },
      { id: 'end', type: 'end' },
    ],
    edges: [
      { id: 'start-worker', source: 'start', target: 'worker' },
      { id: 'worker-final', source: 'worker', target: 'final' },
      { id: 'final-end', source: 'final', target: 'end' },
    ],
  };
}

function sequentialNativeDefinition(id) {
  const workflow=definition(id,'ordinary');
  const first=workflow.nodes.find(node=>node.id==='worker');
  first.outputs_schema={type:'object',properties:{summary:{type:'string'}},required:['summary'],additionalProperties:false};
  const second={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
    access:'read_only',approval:{required:false},retry:{max_attempts:3},
    input_bindings:{task:'/nodes/worker/output/summary'},prompt_template:'Integrate the completed work.',
    outputs_schema:{type:'object',properties:{summary:{type:'string'}},required:['summary'],additionalProperties:false}};
  workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,second);
  workflow.nodes.find(node=>node.id==='final').input_bindings={summary:'/nodes/integrator/output/summary'};
  workflow.edges=[{id:'start-worker',source:'start',target:'worker'},
    {id:'worker-integrator',source:'worker',target:'integrator'},
    {id:'integrator-final',source:'integrator',target:'final'},
    {id:'final-end',source:'final',target:'end'}];
  return workflow;
}

async function startRun(f, workflow, inputs,resources={}, {historical=false}={}) {
  const created = await f.service.call('create', { workflow,resources }, { human: true });
  let run = await f.service.call('start', {
    workflow_id: workflow.id,
    revision_hash: created.revision_hash,
    workspace: f.workspace,
    access: workflow.nodes.some(node=>node.access==='bounded_write')?'bounded_write':'read_only',
    ...(workflow.nodes.some(node=>node.access==='bounded_write')?{allowed_paths:['pages']}:{}),
    main_actor: 'root',
    native_parent_thread_id: PARENT_THREAD_ID,
    inputs,
  });
  const {runtime}=await f.service.open();
  if(historical){
    // Publish an independent historical journal from its initial state, before
    // any dispatch/material publication. Never strip a live span or rewrite a
    // new Run's sealed pins/state to simulate the legacy protocol.
    const original=await runtime.runs.read(run.run_id),pins=structuredClone(original.pins),state=structuredClone(original.state);
    assert.equal(pins.native_dispatch_span_version,1);delete pins.native_dispatch_span_version;
    assert.equal(pins.executable_projection_version,1);delete pins.executable_projection_version;
    assert(Object.values(state.nodes).every(node=>node.attempts.length===0));
    const blobs=new Map(await Promise.all(pins.resources.map(async resource=>[resource.sha256,await readFile(join(runtime.runs.directory(run.run_id),'objects',resource.sha256))])));
    await f.service.call('cancel',control(run));
    const id=randomUUID();state.run_id=id;state.pins_hash=digest(canonicalJSON(pins));state.main_session_identity=null;
    delete state.constraints.host_startup_key;delete state.constraints.host_startup_sha256;
    await runtime.runs.create(id,pins,blobs,state,{hostAuthority:{run_id:id,control_token:run.control_token}});
    run={...run,run_id:id};
  }
  await retainOwnedAuthority(runtime,run);
  return { run, binding: control(run) };
}

test('native_next retains a historical prepared executable dispatch hash on continuation',async t=>{
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:'legacy-executable-turn',result:{summary:'Legacy assigned result'}}),{},process.env);
  const workflow=definition('native-prepared-executable-legacy','ordinary');workflow.requirements.executables=[{name:'node',version:'>=20.0.0'}];
  const {binding}=await startRun(f,workflow,{task:'An independent neutral task'},{},{historical:true});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const {runtime,executor,config}=await f.service.open(),before=await runtime.runs.read(binding.run_id),attempt=before.state.nodes.worker.attempts[0];
  assert.equal(before.pins.executable_projection_version,undefined);
  const lease={node_id:'worker',attempt_id:attempt.id,lease_token:leaseToken(binding.control_token,binding.run_id,'worker',attempt.id),control_token:binding.control_token};
  const prepared=await executor.prepareNativeObservation(binding.run_id,lease,before,config);
  assert.match(prepared.envelope.prompt_template,/Dependencies:.*node.*Report unresolved dependencies/);
  assert.equal(digest(canonicalJSON(prepared)),attempt.dispatch.envelope_hash);
  const replay=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(replay.batch_id,handoff.batch_id);
  assert.deepEqual((await runtime.runs.read(binding.run_id)).state.nodes.worker.attempts[0].dispatch,attempt.dispatch);
});

test('native_next resumes an unacknowledged historical schema1 spawn from exact legacy materials without migration',async t=>{
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:'legacy-own-turn',result:[0,1]}));
  const {binding}=await startRun(f,definition('native-pending-legacy','capped-one'),{jobs:[0,1]},{},{historical:true});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST),internal=await f.service.call('native_next',binding),packet=internal.packets[0];
  const current=JSON.parse(await readFile(packet.task_bundle_path));
  const directory=join(packet.task_bundle_path,'..'),inputDirectory=join(directory,'inputs');await mkdir(inputDirectory,{recursive:true});
  const inputPath=join(inputDirectory,`input-${digest(Buffer.from('jobs'))}.json`),inputBytes=Buffer.from(canonicalJSON([0,1]));await writeFile(inputPath,inputBytes);
  const reference=`Read this bound input from the local file at ${canonicalJSON(inputPath)} (format: json).`;
  const historical={schema_version:1,task:current.task.replace(/\nInputs:\n[^\n]+/,()=> '\nInputs:\n'+canonicalJSON({jobs:reference})),
    workspace:current.workspace,access:current.access,writable_paths:current.writable_paths,result_schema:current.result_schema,resources:[],verified_files:[]};
  const bytes=Buffer.from(canonicalJSON(historical));await writeFile(packet.task_bundle_path,bytes);
  const preparationPath=current.context_preparation.path;await rm(preparationPath);
  const before=await f.service.call('get',binding);assert.equal(Object.keys(before.nodes.worker.attempts[0].native_pending_spawns).length,1);
  const replay=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(publicPackets(replay)[0].spawn_config.task_name,packet.spawn_config.task_name);
  const replayInternal=await f.service.call('native_next',binding);assert.equal(replayInternal.attempt_id,internal.attempt_id);
  assert.equal(replayInternal.packets[0].task_bundle_sha256,digest(bytes));assert.deepEqual(await readFile(packet.task_bundle_path),bytes);
  await assert.rejects(readFile(preparationPath),{code:'ENOENT'});
  await writeFile(inputPath,'changed');await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'NATIVE_TASK_FILE_CHANGED'});
  await writeFile(inputPath,inputBytes);
  await recordNativeSpawn(f,{...binding,attempt_id:internal.attempt_id,index:0,agent_id:before.nodes.worker.attempts[0].native_pending_spawns[0].agent_id});
  const accepted=await f.service.call('native_next',{},MODEL_REQUEST);assert.equal(accepted.next_action,'workflow_native_next');
  assert.deepEqual((await f.service.call('get',binding)).nodes.worker.output,{results:[[0,1]]});
});

test('native_next historical schema1 replay delivers nonempty resource and verified-file addresses without rewriting canonical bytes',async t=>{
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:'legacy-material-turn',result:[0,1]}));
  const sourceBytes=Buffer.from('Verified historical source bytes.'),resourceText='Exact historical reference.';
  await writeFile(join(f.workspace,'source.bin'),sourceBytes);
  const workflow=definition('native-pending-legacy-materials','capped-one'),worker=workflow.nodes.find(node=>node.id==='worker');
  workflow.inputs_schema.properties.source={type:'object',properties:{document_path:{type:'string'},document_sha256:{type:'string'}},required:['document_path','document_sha256'],additionalProperties:false};
  worker.input_bindings.source='/inputs/source';worker.resources=['reference.md'];
  const {binding}=await startRun(f,workflow,{jobs:[0,1],source:{document_path:'source.bin',document_sha256:digest(sourceBytes)}},{'reference.md':resourceText},{historical:true});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST),internal=await f.service.call('native_next',binding),packet=internal.packets[0];
  const current=JSON.parse(await readFile(packet.task_bundle_path)),metadata=JSON.parse(await readFile(current.context_preparation.path));
  assert.equal(metadata.resources.length,1);assert.equal(metadata.verified_files.length,1);
  const directory=join(packet.task_bundle_path,'..'),inputDirectory=join(directory,'inputs');await mkdir(inputDirectory,{recursive:true});
  const {executor}=await f.service.open(),context=await nativeAttemptContext(f,{...binding,attempt_id:internal.attempt_id});
  const prepared=await executor.prepare(binding.run_id,context.binding),inputs=structuredClone(prepared.envelope.inputs);
  inputs.source.document_path=metadata.verified_files[0].local_path;
  for(const name of ['jobs','source']){
    const inputPath=join(inputDirectory,`input-${digest(Buffer.from(name))}.json`);
    await writeFile(inputPath,Buffer.from(canonicalJSON(inputs[name])));
    inputs[name]=`Read this bound input from the local file at ${canonicalJSON(inputPath)} (format: json).`;
  }
  const materialItems=items=>items.map(({delivery,...item})=>item);
  const legacyTemplate=prepared.envelope.prompt_template.replace('Resources listed below are logical identifiers, not filesystem paths. Use read_workflow_resource; cite resource IDs.',
    'Pinned resources are Host-materialized local files listed in this task bundle; read those exact local paths.');
  const historical={schema_version:1,task:compilePrompt({...prepared.envelope,prompt_template:legacyTemplate,inputs},64000),
    workspace:current.workspace,access:current.access,writable_paths:current.writable_paths,result_schema:current.result_schema,
    resources:materialItems(metadata.resources),verified_files:materialItems(metadata.verified_files)};
  const bytes=Buffer.from(canonicalJSON(historical));await writeFile(packet.task_bundle_path,bytes);await rm(current.context_preparation.path);
  // This old-epoch fixture predates schema2's sealed semantic carrier. Remove
  // only the synthetic schema2 carrier produced while arranging its materials;
  // the legacy projection must be generated from these exact historical bytes.
  await rm(join(directory,'semantic-task.json'),{force:true});
  const replay=await f.service.call('native_next',{},MODEL_REQUEST),message=publicPackets(replay)[0].prompt;
  const semanticPath=join(directory,'semantic-task.json');
  assert(message.includes(canonicalJSON(semanticPath)),'The historical child must receive the exact public semantic carrier address');
  const semanticBytes=await readFile(semanticPath,'utf8'),semantic=JSON.parse(semanticBytes);
  for(const field of ['resources','verified_files']){
    const addresses=historical[field].map(({path,local_path})=>({path,local_path}));
    assert.deepEqual(semantic[field],addresses,field+' semantic addresses must reach the historical child through its public carrier');
  }
  assert.equal(semantic.task,historical.task);
  assert.equal(semantic.workspace,historical.workspace);assert.equal(semantic.access,historical.access);
  assert.deepEqual(semantic.writable_paths,historical.writable_paths);assert.deepEqual(semantic.result_schema,historical.result_schema);
  assert.doesNotMatch(semanticBytes,/context-preparation|"sha256"|"bytes"|"references"/);
  assert.doesNotMatch(message,/context-preparation|"sha256"|"bytes"|"references"/);
  assert.equal(publicPackets(replay)[0].spawn_config.task_name,publicPackets(initial)[0].spawn_config.task_name);
  const retained=await f.service.call('native_next',binding);
  assert.equal(retained.packets[0].task_bundle_sha256,digest(bytes));assert.deepEqual(await readFile(packet.task_bundle_path),bytes);
  for(const field of ['resources','verified_files']){
    const item=historical[field][0],original=await readFile(item.local_path);
    await writeFile(item.local_path,'tampered');await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'NATIVE_TASK_FILE_CHANGED'});
    await writeFile(item.local_path,original);
  }
  await assert.rejects(readFile(current.context_preparation.path),{code:'ENOENT'});
  await recordNativeSpawn(f,{...binding,attempt_id:internal.attempt_id,index:0,agent_id:context.attempt.native_pending_spawns[0].agent_id});
  assert.equal((await f.service.call('native_next',{},MODEL_REQUEST)).next_action,'workflow_native_next');
  assert.deepEqual((await f.service.call('get',binding)).nodes.worker.output,{results:[[0,1]]});
});

test('native_next completes an ordinary Agent and a capped fan-out with exactly one partition', async t => {
  for (const scenario of [
    { name: 'ordinary Agent', mode: 'ordinary', inputs: { task: 'one task' }, agentId: 'ordinary-child', expected: { summary: 'accepted' } },
    { name: 'one capped partition', mode: 'capped-one', inputs: { jobs: Array.from({ length: 10 }, (_, index) => index) }, agentId: 'capped-child' },
  ]) {
    await t.test(scenario.name, async t => {
      const expected = scenario.expected ?? { results: [scenario.inputs.jobs] };
      const observed = [];
      const f = await fixture(t, async ids => {
        observed.push([...ids]);
        return {
          status: 'completed',
          agent_id: ids[0],
          turn_id: 'turn-' + scenario.agentId,
          result: scenario.mode === 'ordinary' ? expected : scenario.inputs.jobs,
        };
      });
      const workflow = definition('native-' + scenario.mode, scenario.mode);
      const { run, binding } = await startRun(f, workflow, scenario.inputs);
      const handoff = await f.service.call('native_next', binding);
      assert.equal(handoff.status, 'native_handoff');
      assert.deepEqual(handoff.packets.map(packet => packet.index), [0]);
      assert.equal(Object.hasOwn(handoff,'next_action'),false,'The internal test seam must not publish a retired receipt interface');

      const spawned = await recordNativeSpawn(f, {
        ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: scenario.agentId,
      });
      assert.equal(spawned.recorded,true);

      if (scenario.mode === 'capped-one') {
        const beforeObservation = await f.service.call('get', binding);
        const attempt = beforeObservation.nodes.worker.attempts[0];
        assert.equal(beforeObservation.nodes.worker.status, 'claimed');
        assert.equal(attempt.dispatch.receipt ?? null, null);
        assert.equal(beforeObservation.nodes.worker.output, null);
      }

      const advanced = await f.service.call('native_next', binding);
      assert.equal(advanced.next_action, 'workflow_native_next');
      assert.deepEqual(observed, [[scenario.agentId]]);
      const state = await f.service.call('get', binding);
      assert.equal(state.nodes.worker.status, 'succeeded');
      assert.deepEqual(state.nodes.worker.output, expected);
      const receipt = state.nodes.worker.attempts[0].dispatch.receipt;
      assert.deepEqual(receipt.agent_ids ?? [receipt.agent_id], [scenario.agentId]);
      assert.equal(state.nodes.final.attempts.length, 0);
      assert.equal(run.status, 'running');
    });
  }
});

test('the model-facing last native spawn stays inside Host collection until the Agent event', async t => {
  let release;
  const observed = new Promise(resolve => { release = resolve; });
  const f = await fixture(t, async ids => {
    const result = await observed;
    return { ...result, agent_id: ids[0] };
  },{}, {WORKFLOW_MCP_TRANSPORT:'direct_mcp'});
  const { binding } = await startRun(f, definition('native-wait-before-collection', 'ordinary'), { task: 'one task' });
  const handoff = await f.service.call('native_next', {}, MODEL_REQUEST);
  assert.equal(handoff.registration_tool, 'workflow_native_spawned_batch');
  assert.equal(handoff.invocation_adapter?.tool_name, 'workflow_native_spawned_batch');
  assert.equal(handoff.invocation_adapter.slot,'none');
  assert.equal(handoff.invocation_adapter.kind,'direct_mcp');
  assert.equal(handoff.invocation_adapter.tool,'mcp__caw_execution__workflow_native_spawned_batch');
  assert.deepEqual(handoff.invocation_adapter.arguments,{batch_id:handoff.batch_id});
  for(const key of ['code','budget','pragma','wait'])assert.equal(Object.hasOwn(handoff.invocation_adapter,key),false,key);
  const expectedAgent=`/root/${publicPackets(handoff)[0].spawn_config.task_name}`;
  let settled = false;
  const pending = f.service.call('native_spawned_batch', {}, MODEL_REQUEST).finally(() => { settled = true; });

  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(settled, false, 'The last registration must hold the model-facing call instead of returning a prompt instruction');
  release({ status: 'completed', agent_id:expectedAgent,turn_id: 'turn-waiting-child', result: { summary: 'accepted' } });
  const spawned = await pending;

  assert.equal(spawned.next_action, 'workflow_native_next');
  assert.deepEqual(spawned.next_action_args, {});
  assert.equal(spawned.invocation_adapter?.tool_name, 'workflow_native_next');
  assert.equal(spawned.journaled_spawn_count,1);
  assert.equal((await f.service.call('get', binding)).nodes.worker.status, 'succeeded');
});

test('model-facing native continuation joins one receipted Host Main job without returning a polling turn',async t=>{
  const hostMainManager=delayedReceiptHostMainManager();
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:'turn-native-complete',
    result:{summary:'accepted'}}),{hostMainManager});
  const {binding}=await startRun(f,definition('native-host-main-join','ordinary'),{task:'one task'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const registered=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(registered.next_action,'workflow_native_next');

  let firstSettled=false;
  const first=f.service.call('native_next',{},MODEL_REQUEST).finally(()=>{firstSettled=true;});
  await hostMainManager.launched;
  await new Promise(resolve=>setTimeout(resolve,20));
  assert.equal(firstSettled,false,'The model-facing call must remain inside the Host Main owner');
  assert.equal(hostMainManager.launches,1);
  assert.equal(hostMainManager.waits,1);

  await hostMainManager.fail();
  const firstResult=await first;
  assert.equal(firstResult.status,'failed');
  assert.equal((await f.service.call('get',binding)).status,'failed');
});

test('model-facing spawn registration follows the newly active Agent node after a prior Agent succeeds',async t=>{
  let observation=0;
  const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:`turn-${++observation}`,
    result:{summary:observation===1?'written':'integrated'}}));
  const workflow=sequentialNativeDefinition('native-model-sequential-agent-nodes');
  const {binding}=await startRun(f,workflow,{task:'one task'});

  const first=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(first.node_id,'worker');
  await f.service.call('native_spawned_batch',{batch_id:first.batch_id},MODEL_REQUEST);
  const second=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(second.node_id,'integrator');

  const oldRetry=await f.service.call('native_spawned_batch',{batch_id:first.batch_id},MODEL_REQUEST);
  assert.equal(oldRetry.batch_id,second.batch_id);
  assert.equal(oldRetry.acknowledged_batch_id,first.batch_id);
  assert.equal(observation,1);
  assert.deepEqual((await f.service.call('get',binding)).nodes.integrator.attempts[0].native_agents??{},{});

  await assert.rejects(f.service.call('native_spawned_batch',{},MODEL_REQUEST),{code:'NATIVE_AGENT_BATCH_AMBIGUOUS'});
  const registered=await f.service.call('native_spawned_batch',{batch_id:second.batch_id},MODEL_REQUEST);
  assert.equal(registered.journaled_spawn_count,1);
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.equal(state.nodes.integrator.status,'succeeded');
  assert.deepEqual(state.nodes.integrator.output,{summary:'integrated'});
});

test('model-facing capped fan-out releases and journals one complete concurrency window', async t => {
  const jobs = Array.from({ length: 20 }, (_, index) => index);
  let release;
  const observed = new Promise(resolve => { release = resolve; });
  const indexByAgent=new Map();
  const f = await fixture(t, async ids => {
    await observed;
    const agentId = ids[0];
    const index = indexByAgent.get(agentId);
    return { status: 'completed', agent_id: agentId, turn_id: 'turn-' + agentId,
      result: jobs.slice(index * 10, (index + 1) * 10) };
  });
  const { binding } = await startRun(f, definition('native-model-capped-two', 'capped-one'), { jobs });
  const first = await f.service.call('native_next', {}, MODEL_REQUEST);
  for(const packet of publicPackets(first))indexByAgent.set(`/root/${packet.spawn_config.task_name}`,packet.index);
  assert.deepEqual(publicPackets(first).map(packet => packet.index), [0, 1]);
  assert.equal(first.released_packet_indices,undefined);
  assert.equal(first.registration_tool, 'workflow_native_spawned_batch');

  let settled = false;
  const pending = f.service.call('native_spawned_batch', {}, MODEL_REQUEST).finally(() => { settled = true; });
  await new Promise(resolve => setTimeout(resolve, 50));
  assert.equal(settled, false, 'The final registration must enter Host collection after both exact IDs are journaled');
  release();
  const completed = await pending;
  assert.equal(completed.next_action, 'workflow_native_next');
  assert.equal(completed.journaled_spawn_count,2);
  assert.equal((await f.service.call('get', binding)).nodes.worker.status, 'succeeded');
});

test('31-item model-facing fan-out refills only the completed slot and never reissues accepted partitions', {timeout:30_000}, async t => {
  const jobs=Array.from({length:31},(_,index)=>index),waiters=[];
  const observerEntries=Array.from({length:4},()=>deferred());
  const f=await fixture(t,ids=>new Promise(resolve=>{
    const waiter={ids:[...ids],resolve};waiters.push(waiter);
    assert(waiters.length<=observerEntries.length,'Host must not observe an accepted partition again');
    observerEntries[waiters.length-1].resolve(waiter);
  }));
  const {binding}=await startRun(f,definition('native-model-rolling-window','capped-two'),{jobs});
  const agentByIndex=new Map();
  const waitForObserver=(count,operation)=>Promise.race([
    observerEntries[count-1].promise,
    operation.then(()=>{throw new Error('Host operation completed before entering its expected observer wait');}),
  ]);
  const result=index=>({status:'completed',agent_id:agentByIndex.get(index),turn_id:`turn-child-${index}`,
    result:jobs.slice(index*10,Math.min(jobs.length,(index+1)*10))});

  const first=await f.service.call('native_next',{}, MODEL_REQUEST);
  assert.deepEqual(publicPackets(first).map(packet=>packet.index),[0,1]);
  for(const packet of publicPackets(first))agentByIndex.set(packet.index,`/root/${packet.spawn_config.task_name}`);
  await assert.rejects(f.service.call('native_spawned_batch',{attempt_id:'foreign-attempt'},MODEL_REQUEST),{code:'MODEL_CONTINUATION_FIELDS'});
  assert.deepEqual((await f.service.call('get',binding)).nodes.worker.attempts[0].native_agents??{},{});

  const firstWindow=f.service.call('native_spawned_batch',{batch_id:first.batch_id}, MODEL_REQUEST);
  await waitForObserver(1,firstWindow);assert.deepEqual(waiters[0].ids,[agentByIndex.get(0),agentByIndex.get(1)]);waiters[0].resolve(result(0));
  const refillTwo=await firstWindow;assert.deepEqual(publicPackets(refillTwo).map(packet=>packet.index),[2]);
  agentByIndex.set(2,`/root/${publicPackets(refillTwo)[0].spawn_config.task_name}`);

  const secondWindow=f.service.call('native_spawned_batch',{batch_id:refillTwo.batch_id}, MODEL_REQUEST);
  await waitForObserver(2,secondWindow);assert.deepEqual(waiters[1].ids,[agentByIndex.get(1),agentByIndex.get(2)]);waiters[1].resolve(result(1));
  const refillThree=await secondWindow;assert.deepEqual(publicPackets(refillThree).map(packet=>packet.index),[3]);
  agentByIndex.set(3,`/root/${publicPackets(refillThree)[0].spawn_config.task_name}`);

  const finalWindow=f.service.call('native_spawned_batch',{batch_id:refillThree.batch_id}, MODEL_REQUEST);
  await waitForObserver(3,finalWindow);assert.deepEqual(waiters[2].ids,[agentByIndex.get(2),agentByIndex.get(3)]);waiters[2].resolve(result(2));
  await waitForObserver(4,finalWindow);assert.deepEqual(waiters[3].ids,[agentByIndex.get(3)]);waiters[3].resolve(result(3));
  const completed=await finalWindow;
  assert.equal(completed.next_action,'workflow_native_next');
  const state=await f.service.call('get',binding);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,[jobs.slice(0,10),jobs.slice(10,20),jobs.slice(20,30),jobs.slice(30)]);
  assert.deepEqual(state.nodes.worker.attempts[0].native_agents,
    Object.fromEntries([...agentByIndex].map(([index,id])=>[String(index),id])));
});

test('native observer cannot return a polling continuation to WorkflowService', async t => {
  let inspections = 0;
  const f = await fixture(t, async ids => {
    inspections++;
    return { status: 'pending', pending_phase: 'running', agent_ids: [...ids] };
  });
  const { binding } = await startRun(f, definition('native-nonblocking-collection', 'ordinary'), { task: 'one task' });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'running-child',
  });

  await assert.rejects(f.service.call('native_next', binding),{code:'NATIVE_AGENT_OBSERVER_PROTOCOL'});
  assert.equal(inspections, 1);
});

test('partial out-of-order spawn journaling reports exact remaining indexes and does not reissue a sealed packet', async t => {
  const jobs = [10, 20, 30];
  const observed = [];
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    const agentId = ids[0];
    const jobIndex = Number(agentId.slice('agent-'.length));
    return { status: 'completed', agent_id: agentId, turn_id: 'turn-' + agentId, result: [jobs[jobIndex]] };
  });
  const workflow = definition('native-uncapped-three', 'uncapped-three');
  const { binding } = await startRun(f, workflow, { jobs });
  const firstHandoff = await f.service.call('native_next', binding);
  assert.deepEqual(firstHandoff.packets.map(packet => packet.index), [0, 1, 2]);
  const sealedPrompt = firstHandoff.packets.find(packet => packet.index === 1).prompt;
  const attemptId = firstHandoff.attempt_id;

  const firstJournal = await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 1, agent_id: 'agent-1' });
  assert.equal(firstJournal.recorded,true);
  assert.equal(Object.hasOwn(firstJournal, 'packets'), false);

  const recoveredHandoff = await f.service.call('native_next', binding);
  assert.deepEqual(recoveredHandoff.packets.map(packet => packet.index), [0, 2]);
  assert.equal(recoveredHandoff.packets.some(packet => packet.index === 1 || packet.prompt === sealedPrompt), false);

  const secondJournal = await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 0, agent_id: 'agent-0' });
  assert.equal(secondJournal.recorded,true);
  const finalJournal = await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 2, agent_id: 'agent-2' });
  assert.equal(finalJournal.recorded,true);
  assert.deepEqual(observed, []);

  const advanced = await f.service.call('native_next', binding);
  assert.equal(advanced.next_action, 'workflow_native_next');
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results, [[10], [20], [30]]);
  assert.deepEqual(observed[0], ['agent-0', 'agent-1', 'agent-2']);
  assert.equal(observed.length, 3);
});

for (const mode of ['ordinary', 'capped-one', 'uncapped-three']) {
  test(`model-facing ${mode} repair adapter continues collection without inventing a follow-up intent`, async t => {
    let observations = 0;
    const f = await fixture(t, async ids => {
      observations++;
      return {status:'completed',agent_id:ids[0],turn_id:`adapter-turn-${observations}`,
        result:observations===1 ? {invalid:true} : mode==='ordinary' ? {summary:'accepted'} : [1]};
    });
    const {binding}=await startRun(f,definition(`adapter-repair-${mode}`,mode),mode==='ordinary'?{task:'one task'}:{jobs:[1]});
    await f.service.call('native_next',{},MODEL_REQUEST);
    const rejected=await f.service.call('native_spawned_batch',{},MODEL_REQUEST);
    assert.equal(rejected.next_action,'repair_recorded_agent');
    assert.equal(rejected.followup_config,undefined);
    assert.equal(rejected.invocation_adapter.tool_name,'workflow_native_next');
    assert.deepEqual(rejected.next_action_args,{});
    const state=await f.service.call('get',binding);
    assert.equal(state.nodes.worker.attempts[0].native_pending_followup,undefined);
    const repaired=await f.service.call('native_next',{},MODEL_REQUEST);
    assert.equal(repaired.invocation_adapter.tool_name,'workflow_native_next');
    assert.equal((await f.service.call('get',binding)).nodes.worker.status,'succeeded');
  });
}

test('invalid capped result cannot seal before validation', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let observations = 0;
  const f = await fixture(t, async ids => {
    observations++;
    return observations === 1
      ? { status: 'completed', agent_id: ids[0], turn_id: 'invalid-turn', result: { invalid: true } }
      : { status: 'completed', agent_id: ids[0], turn_id: 'repaired-turn', result: jobs };
  });
  const workflow = definition('native-capped-invalid', 'capped-one');
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  const attemptId = handoff.attempt_id;
  await recordNativeSpawn(f, { ...binding, attempt_id: attemptId, index: 0, agent_id: 'repairable-child' });

  const invalid = await f.service.call('native_next', binding);
  assert.equal(invalid.status, 'native_agent_invalid_result');
  assert.equal(invalid.next_action, 'repair_recorded_agent');
  assert.equal(invalid.turn_id, 'invalid-turn');
  const rejectedState = await f.service.call('get', binding);
  const rejectedAttempt = rejectedState.nodes.worker.attempts[0];
  assert.equal(rejectedState.nodes.worker.status, 'claimed');
  assert.equal(rejectedState.nodes.worker.output, null);
  assert.equal(rejectedAttempt.dispatch.receipt ?? null, null);
  assert.equal(Object.keys(rejectedAttempt.native_parallel_results ?? {}).length, 0);
  assert.equal(rejectedAttempt.native_rejected_turns[0].turn_id, 'invalid-turn');

  const repaired = await f.service.call('native_next', binding);
  assert.equal(repaired.next_action, 'workflow_native_next');
  const finalState = await f.service.call('get', binding);
  assert.equal(finalState.nodes.worker.status, 'succeeded');
  assert.deepEqual(finalState.nodes.worker.output.results, [jobs]);
  assert.equal(observations, 2);
});

test('uncapped native fan-out retains a valid sibling across same-child repair and exhausts pinned correction budget', async t => {
  const jobs = [10, 20, 30];
  const observed = [];
  let badTurns = 0;
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    const id = ids[0];
    if (id === 'agent-1') return ++badTurns === 1
      ? { status: 'completed', agent_id: id, turn_id: 'bad-1', result: { wrong: true } }
      : { status: 'completed', agent_id: id, turn_id: 'fixed-1', result: [20] };
    const index = Number(id.slice(-1));
    return { status: 'completed', agent_id: id, turn_id: `good-${index}`, result: [jobs[index]] };
  });
  const { binding } = await startRun(f, definition('native-uncapped-repair', 'uncapped-three'), { jobs });
  const handoff = await f.service.call('native_next', binding);
  for (let index = 0; index < 3; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  const rejected = await f.service.call('native_next', binding);
  assert.equal(rejected.next_action, 'repair_recorded_agent');
  assert.equal(rejected.agent_id, 'agent-1');
  assert.equal(rejected.repair_remaining, 1);
  assert.doesNotMatch(rejected.repair_prompt, /bad-1/);
  assert.match(rejected.repair_prompt, /Result schema/);
  assert.doesNotMatch(rejected.repair_prompt, /same recorded Agent|"outcome":"blocked"/);
  assert.doesNotMatch(rejected.repair_prompt, /Process assigned jobs|\[10,20,30\]/);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.attempts[0].native_parallel_results[0],
    { agent_id: 'agent-0', result: [10] });
  await f.service.call('native_next', binding);
  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, [[10], [20], [30]]);
  assert.deepEqual(observed[0], ['agent-0', 'agent-1', 'agent-2']);
  assert.ok(observed.slice(1).every(ids => !ids.includes('agent-0')), 'Validated sibling must never be observed again');
  assert.deepEqual(Object.values(state.nodes.worker.attempts[0].native_agents), ['agent-0', 'agent-1', 'agent-2']);
});

test('repeated malformed native result stops same-child repair but leaves an explicit node-attempt retry', async t => {
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `bad-${++turn}`, result: { wrong: true } }));
  const { binding } = await startRun(f, definition('native-repair-limit', 'ordinary'), { task: 'test' });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'same-child' });
  const first = await f.service.call('native_next', binding);
  assert.equal(first.next_action, 'repair_recorded_agent');
  assert.equal(first.repair_remaining, 1);
  const exhausted = await f.service.call('native_next', binding);
  assert.equal(exhausted.status, 'native_agent_repair_exhausted');
  assert.equal(exhausted.next_action, null);
  assert.equal(exhausted.completion_satisfied,false);
  assert.equal(exhausted.recovery_required,true);
  assert.equal(exhausted.agent_id, 'same-child');
  assert.match(exhausted.reason, /wrong|summary/i);
  assert.equal(turn, 2);
  const failedState=await f.service.call('get', binding);
  assert.equal(failedState.nodes.worker.status, 'failed');
  assert.equal(failedState.completion_satisfied,false);
  assert.equal(failedState.recovery_required,true);
  const { runtime } = await f.service.open();
  const previous=failedState.nodes.worker.attempts.at(-1);
  const retried=await runtime.retryNode(binding.run_id,{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'host_protocol_repaired'}]}});
  assert.equal(retried.status,'running');
  assert.equal(retried.nodes.worker.status,'ready');
  assert.equal(retried.nodes.worker.attempts.length,1,'Retry releases a new attempt without rewriting the failed journal');
});

test('explicit per-item retry inherits accepted siblings and resets the fresh Agent correction allowance', async t => {
  const jobs=Array.from({length:10},(_,index)=>index);let firstTurns=0,retryTurns=0;
  const f=await fixture(t,async ids=>{
    if(ids[0]==='first-child'){
      firstTurns++;
      return {status:'completed',agent_id:ids[0],turn_id:`first-${firstTurns}`,result:{items:firstTurns===1
        ?jobs.map((job,index)=>index===7?{outcome:'blocked',block_reason:'item 7 still needs work'}:{outcome:'completed',result:[job]})
        :[{outcome:'blocked',block_reason:'item 7 still needs work'}]}};
    }
    return {status:'completed',agent_id:ids[0],turn_id:`second-invalid-${++retryTurns}`,result:{wrong:true}};
  });
  const workflow=definition('native-per-item-explicit-retry','capped-one');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.retry.max_attempts=3;worker.fanout.result_mode='per_item';
  const {binding}=await startRun(f,workflow,{jobs});
  const first=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'first-child'});
  const firstRepair=await f.service.call('native_next',binding);
  assert.equal(firstRepair.repair_remaining,2);
  assert.equal(f.service.modelResult(firstRepair).invocation_adapter.tool_name,'workflow_native_followed_up');
  await f.service.call('native_followed_up',firstRepair.next_action_args);
  const secondRepair=await f.service.call('native_next',binding);
  assert.equal(secondRepair.repair_remaining,1);
  await f.service.call('native_followed_up',secondRepair.next_action_args);
  const exhausted=await f.service.call('native_next',binding);
  assert.equal(exhausted.status,'native_agent_repair_exhausted');
  const failed=await f.service.call('get',binding),previous=failed.nodes.worker.attempts.at(-1);
  assert.deepEqual(Object.keys(previous.native_item_results).map(Number),[0,1,2,3,4,5,6,8,9]);
  await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
  const retry=await f.service.call('native_next',binding);
  assert.equal(retry.packets.length,1);
  const retryBundle=JSON.parse(await readFile(retry.packets[0].task_bundle_path,'utf8'));
  assert.equal(retryBundle.result_schema.properties.items.minItems,1);
  assert.equal(retryBundle.result_schema.properties.items.maxItems,1);
  assert.equal(JSON.parse(await readFile(retryBundle.context_preparation.path)).verified_files.length,0);
  await recordNativeSpawn(f,{...binding,attempt_id:retry.attempt_id,index:0,agent_id:'second-child'});
  const rejected=await f.service.call('native_next',binding);
  assert.equal(rejected.next_action,'repair_recorded_agent');
  assert.equal(rejected.repair_remaining,2,'A prior failed attempt must not consume this Agent correction budget');
  const retried=await f.service.call('get',binding),attempt=retried.nodes.worker.attempts.at(-1);
  assert.deepEqual(attempt.inherited_native_item_indices,[0,1,2,3,4,5,6,8,9]);
  await f.service.call('native_followed_up',rejected.next_action_args);
  const observedRepairTurn=await f.service.call('native_next',binding);
  assert.equal(observedRepairTurn.next_action,'repair_recorded_agent',
    'An acknowledged repair must be observed before another incremental packet is generated for its unresolved item');
  assert.equal(observedRepairTurn.turn_id,'second-invalid-2');
  assert.equal(observedRepairTurn.repair_remaining,1);
  assert.equal(retryTurns,2);
  assert.equal((await f.service.call('get',binding)).nodes.worker.attempts.at(-1).native_rejected_turns[0].count,2);
});

for (const scheduling of ['serial', 'parallel', 'capped_parallel']) {
  test(`explicit per-item retry closes the ${scheduling} join with inherited siblings and exact evidence`, async t => {
    const jobs=Array.from({length:10},(_,index)=>index);let turns=0;
    const f=await fixture(t,async ids=>({status:'completed',agent_id:ids[0],turn_id:`turn-${++turns}`,
      result:{items:ids[0]==='retry-child'?[{outcome:'completed',result:[7]}]
        :(turns===1?jobs:[7]).map(job=>job===7?{outcome:'blocked',block_reason:'only item 7 needs work'}
          :{outcome:'completed',result:[job]})}}));
    const workflow=definition(`retry-join-${scheduling}`,'capped-one'),worker=workflow.nodes.find(node=>node.id==='worker');
    worker.fanout.result_mode='per_item';worker.retry.max_attempts=2;
    if(scheduling==='serial'){worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;}
    if(scheduling==='parallel')delete worker.fanout.max_concurrency;
    const {binding}=await startRun(f,workflow,{jobs});
    const first=await f.service.call('native_next',binding);
    await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'failed-child'});
    const repair=await f.service.call('native_next',binding);
    await f.service.call('native_followed_up',repair.next_action_args);
    assert.equal((await f.service.call('native_next',binding)).status,'native_agent_repair_exhausted');
    const failed=await f.service.call('get',binding),previous=failed.nodes.worker.attempts.at(-1);
    const accepted=structuredClone(previous.native_item_results);
    await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
      dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
    const retry=await f.service.call('native_next',binding);
    const bundle=JSON.parse(await readFile(retry.packets[0].task_bundle_path,'utf8'));
    assert.equal(bundle.result_schema.properties.items.minItems,1);
    await recordNativeSpawn(f,{...binding,attempt_id:retry.attempt_id,index:0,agent_id:'retry-child'});
    await f.service.call('native_next',binding);
    const state=await f.service.call('get',binding),attempt=state.nodes.worker.attempts.at(-1);
    assert.equal(state.nodes.worker.status,'succeeded');
    assert.deepEqual(state.nodes.worker.output.results,jobs.map(job=>[job]));
    for(const [index,result]of Object.entries(accepted))assert.deepEqual(attempt.native_item_results[index],result);
    assert.equal(attempt.managed_native_results.length,1);
    assert.equal(attempt.managed_native_results[0].result_sha256,digest(canonicalJSON(jobs.map(job=>[job]))));
    assert.equal(state.nodes.final.status,'ready','Only the verified complete join releases its successor');
    assert.equal(turns,3,'Accepted siblings require no new observation or model turn');
    const {runtime}=await f.service.open();
    const final=await runtime.claimHostMain(binding.run_id,{...binding,node_id:'final',owner:'root',request_id:'claim-final'});
    const finalArgs={...binding,node_id:'final',attempt_id:final.attempt_id,lease_token:final.lease_token};
    const request_id=`dispatch-${final.attempt_id}`;
    await runtime.recordHostMainDispatchIntent(binding.run_id,{...finalArgs,request_id,envelope_hash:digest(canonicalJSON(final))});
    await runtime.recordHostMainDispatchReceipt(binding.run_id,{...finalArgs,request_id,receipt:{
      invocation_id:`fixture-${final.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'a'.repeat(64),
      model:'fixture-main',effort:'medium',main_actor:'root',session_id:`logical-main-${binding.run_id}`,call_chain_id:`workflow-run-${binding.run_id}`}});
    const proposal={status:'succeeded',summary:'Fixture accepts verified results',structured_output:{accepted:true},
      artifacts:[],evidence:[{kind:'fixture_acceptance'}],changed_paths:[],outside_paths:[]};
    const saved=await runtime.runs.saveExecutorResult(binding.run_id,final.attempt_id,proposal);
    await runtime.recordExecutorEvent(binding.run_id,{...finalArgs,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:true}}});
    assert.equal((await runtime.completeHostMainResult(binding.run_id,finalArgs,{accepted:true})).status,'succeeded');
  });
}

for(const scheduling of ['serial','parallel','capped_parallel']){
test(`explicit per-item ${scheduling} retry completes after omitting a fully inherited partition`,async t=>{
  const jobs=Array.from({length:20},(_,index)=>index);let badTurns=0;
  const f=await fixture(t,async ids=>{
    const id=ids[0];
    if(id==='first-good')return {status:'completed',agent_id:id,turn_id:'good',result:{items:jobs.slice(0,10)
      .map(job=>({outcome:'completed',result:[job]}))}};
    if(id==='retry-child')return {status:'completed',agent_id:id,turn_id:'retry-good',result:{items:jobs.slice(10)
      .map(job=>({outcome:'completed',result:[job]}))}};
    badTurns++;
    return {status:'completed',agent_id:id,turn_id:`bad-${badTurns}`,result:{items:jobs.slice(10)
      .map(()=>({outcome:'blocked',block_reason:'second partition still needs work'}))}};
  });
  const workflow=definition(`native-full-partition-${scheduling}-retry`,'capped-two');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.retry.max_attempts=3;worker.fanout.result_mode='per_item';
  if(scheduling==='serial'){worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;}
  if(scheduling==='parallel')delete worker.fanout.max_concurrency;
  const {binding}=await startRun(f,workflow,{jobs});
  const first=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'first-good'});
  if(scheduling==='serial')assert.deepEqual((await f.service.call('native_next',binding)).packets.map(packet=>packet.index),[1]);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:1,agent_id:'first-bad'});
  const repair1=await f.service.call('native_next',binding);
  assert.equal(repair1.agent_id,'first-bad');
  await f.service.call('native_followed_up',repair1.next_action_args);
  const repair2=await f.service.call('native_next',binding);
  await f.service.call('native_followed_up',repair2.next_action_args);
  assert.equal((await f.service.call('native_next',binding)).status,'native_agent_repair_exhausted');
  const failed=await f.service.call('get',binding),previous=failed.nodes.worker.attempts.at(-1);
  assert.deepEqual(Object.keys(previous.native_item_results).map(Number),jobs.slice(0,10));
  await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
  const retry=await f.service.call('native_next',binding);
  assert.deepEqual(retry.packets.map(packet=>packet.index),[1]);
  const bundle=JSON.parse(await readFile(retry.packets[0].task_bundle_path,'utf8'));
  assert.equal(bundle.result_schema.properties.items.minItems,10);
  assert.equal(JSON.parse(await readFile(bundle.context_preparation.path)).verified_files.length,0);
  await recordNativeSpawn(f,{...binding,attempt_id:retry.attempt_id,index:1,agent_id:'retry-child'});
  await f.service.call('native_next',binding);
  const state=await f.service.call('get',binding),attempt=state.nodes.worker.attempts.at(-1);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.deepEqual(Object.keys(attempt.native_agents),['1']);
  assert.equal(attempt.managed_native_results.length,1);
  assert.equal(attempt.managed_native_results[0].result_sha256,digest(canonicalJSON(jobs.slice(10).map(job=>[job]))));
});
}

test('all-inherited serial per-item retry records an empty trusted dispatch and completes idempotently',async t=>{
  const jobs=[10,20,30];let observerCalls=0;
  const f=await fixture(t,async ids=>{
    observerCalls++;
    assert.fail(`All items are inherited; native child ${ids[0]} must not be observed`);
  });
  const workflow=definition('native-serial-all-inherited-retry','capped-one');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.fanout.result_mode='per_item';worker.fanout.scheduling='serial';delete worker.fanout.max_concurrency;
  const {run,binding}=await startRun(f,workflow,{jobs});
  const first=await f.service.call('native_next',binding);
  assert.deepEqual(first.packets.map(packet=>packet.index),[0]);
  await recordNativeSpawn(f,{...binding,attempt_id:first.attempt_id,index:0,agent_id:'seed-serial-child'});

  const seed=await nativeAttemptContext(f,{...binding,attempt_id:first.attempt_id});
  await seed.runtime.recordNativeItemResults(run.run_id,{...seed.binding,index:0,agent_id:'seed-serial-child',turn_id:'seed-complete-turn',
    target_indices:jobs.map((_job,index)=>index),result:{items:jobs.map(job=>({outcome:'completed',result:[job]}))}});
  await f.service.call('fail_node',{...seed.binding,error:{code:'TEST_RETRY_SEED',message:'Retry after all per-item results were journaled'}});
  const failed=await f.service.call('get',binding);
  const previous=failed.nodes.worker.attempts.at(-1);
  assert.equal(failed.nodes.worker.status,'failed');
  assert.deepEqual(Object.keys(previous.native_item_results).map(Number),[0,1,2]);

  await f.service.call('retry_node',{...binding,node_id:'worker',reconciliation:{attempt_id:previous.id,
    dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'all_items_already_accepted'}]}});
  const recovered=await f.service.call('native_next',binding);
  assert.equal(recovered.node_id,'worker');
  assert.equal(recovered.next_action,'workflow_native_next');
  const completed=await f.service.call('get',binding);
  const attempt=completed.nodes.worker.attempts.at(-1);
  assert.equal(completed.nodes.worker.status,'succeeded');
  assert.deepEqual(completed.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.deepEqual(Object.keys(attempt.native_agents??{}),[],'The all-inherited retry must not spawn a child');
  assert.deepEqual(attempt.native_serial_results??[],[]);
  assert.deepEqual(attempt.dispatch.receipt.agent_ids,[]);
  assert.deepEqual(attempt.dispatch.receipt.subagent_dispatch_ids,[]);
  assert.deepEqual(attempt.dispatch.receipt.subagent_plan,{resolved_count:0,input_sha256:digest(canonicalJSON(jobs)),assignments:[]});
  assert.deepEqual(attempt.managed_native_results,[]);
  assert(attempt.native_dispatch_span?.before_ref,'The empty retry still needs a fresh exact completion baseline');
  assert(attempt.native_dispatch_span?.settled_ref);
  assert.deepEqual(attempt.native_dispatch_span.publications,[],'No runnable packet needs publication');
  assert.deepEqual(attempt.completion.changed_paths,[]);
  assert.deepEqual(attempt.completion.evidence.find(item=>item.kind==='subagent_pool'),
    {kind:'subagent_pool',resolved_count:0,dispatch_ids:[]});
  assert.deepEqual(attempt.completion.evidence.filter(item=>item.kind==='native_agent_result'),[]);
  assert.equal(completed.nodes.final.status,'ready','The accepted full join must release the successor');
  assert.equal(observerCalls,0);

  const replay=await nativeAttemptContext(f,{...binding,attempt_id:attempt.id});
  await replay.runtime.recordDispatchReceipt(run.run_id,{...replay.binding,request_id:attempt.dispatch.request_id,
    receipt:attempt.dispatch.receipt});
  await replay.runtime.completeNode(run.run_id,{...replay.binding,completion:attempt.completion});
  let afterReplay=await f.service.call('get',binding);
  assert.deepEqual(afterReplay.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.deepEqual(afterReplay.nodes.worker.attempts.at(-1).managed_native_results,[]);

  const final=await replay.runtime.claimHostMain(run.run_id,{...binding,node_id:'final',owner:'root',request_id:'all-inherited-final'});
  const finalArgs={...binding,node_id:'final',attempt_id:final.attempt_id,lease_token:final.lease_token};
  const request_id=`dispatch-${final.attempt_id}`;
  await replay.runtime.recordHostMainDispatchIntent(run.run_id,{...finalArgs,request_id,envelope_hash:digest(canonicalJSON(final))});
  await replay.runtime.recordHostMainDispatchReceipt(run.run_id,{...finalArgs,request_id,receipt:{
    invocation_id:`fixture-${final.attempt_id}`,executor:'codex-app-server-host-main',executable_sha256:'b'.repeat(64),
    model:'fixture-main',effort:'medium',main_actor:'root',session_id:`logical-main-${run.run_id}`,call_chain_id:`workflow-run-${run.run_id}`}});
  const proposal={status:'succeeded',summary:'Fixture accepts inherited serial results',structured_output:{accepted:true},
    artifacts:[],evidence:[{kind:'fixture_acceptance'}],changed_paths:[],outside_paths:[]};
  const saved=await replay.runtime.runs.saveExecutorResult(run.run_id,final.attempt_id,proposal);
  await replay.runtime.recordExecutorEvent(run.run_id,{...finalArgs,event:{kind:'result_proposed',metadata:{...saved,final_acceptance_required:true}}});
  assert.equal((await replay.runtime.completeHostMainResult(run.run_id,finalArgs,{accepted:true})).status,'succeeded');
  afterReplay=await f.service.call('get',binding);
  assert.equal(afterReplay.nodes.final.status,'succeeded');
  assert.equal(afterReplay.status,'succeeded');
  assert.equal(observerCalls,0);
});

test('parallel siblings each retain their own pinned correction allowance', async t => {
  const jobs = [10, 20, 30], turns = new Map(), repairs = [];
  const f = await fixture(t, async ids => {
    const id = ids[0], count = (turns.get(id) ?? 0) + 1;
    turns.set(id, count);
    if (id !== 'agent-2' && count === 1) return {
      status: 'invalid', agent_id: id, turn_id: `${id}-bad`, reason: `Invalid ${id} fields`,
    };
    return { status: 'completed', agent_id: id, turn_id: `${id}-good`, result: [jobs[Number(id.slice(-1))]] };
  });
  const { binding } = await startRun(f, definition('native-two-repairs', 'uncapped-three'), { jobs });
  const handoff = await f.service.call('native_next', binding);
  for (let index = 0; index < 3; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  for (let call = 0; call < 4; call++) {
    const next = await f.service.call('native_next', binding);
    if (next.next_action === 'repair_recorded_agent') {
      repairs.push(next.agent_id);
      assert.equal(next.repair_remaining, 1);
      continue;
    }
    assert.equal(next.next_action, 'workflow_native_next');
    break;
  }
  assert.deepEqual(repairs, ['agent-0', 'agent-1']);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results, [[10], [20], [30]]);
});

test('repair exhaustion identifies only still outstanding recorded parallel siblings for controller interruption', async t => {
  const jobs = [10, 20, 30];
  let badTurns = 0;
  const f = await fixture(t, async ids => {
    const id = ids[0];
    if (id === 'agent-0') return { status: 'completed', agent_id: id, turn_id: 'good-0', result: [10] };
    if (id === 'agent-1') return { status: 'invalid', agent_id: id, turn_id: `bad-${++badTurns}`, reason: 'Missing result field' };
    assert.fail('Outstanding sibling should not be observed before correction is exhausted');
  });
  const { binding } = await startRun(f, definition('native-exhausted-siblings', 'uncapped-three'), { jobs });
  const handoff = await f.service.call('native_next', binding);
  for (let index = 0; index < 3; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  assert.equal((await f.service.call('native_next', binding)).next_action, 'repair_recorded_agent');
  const exhausted = await f.service.call('native_next', binding);
  assert.equal(exhausted.status, 'native_agent_repair_exhausted');
  assert.equal(exhausted.next_action, null);
  assert.deepEqual(exhausted.outstanding_agent_ids, ['agent-2']);
  assert.deepEqual(exhausted.controller_cleanup, { tool: 'collaboration.interrupt_agent', agent_ids: ['agent-2'] });
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.attempts[0].native_parallel_results[0],
    { agent_id: 'agent-0', result: [10] });
});

test('one ten-item native batch journals nine accepted items and repairs only the failed index in the same child', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  const observed = [];
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    return { status: 'completed', agent_id: ids[0], turn_id: `turn-${observed.length}`, result: {
      items: observed.length === 1
        ? jobs.map((job, item_index) => item_index === 7
          ? { outcome: 'blocked', block_reason: 'Scenario 7 needs correction' }
          : { outcome: 'completed', result: [job] })
        : [{ outcome: 'completed', result: [7] }],
    } };
  });
  const workflow = definition('native-per-item-ten', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  const bundle=JSON.parse(await readFile(handoff.packets[0].task_bundle_path,'utf8'));
  assert.equal(Object.hasOwn(bundle,'item_positions'),false);
  assert.doesNotMatch(JSON.stringify(bundle.result_schema),/"item_index"/);
  assert.equal(bundle.result_schema.properties.items.minItems,10);
  assert.equal(bundle.result_schema.properties.items.maxItems,10);
  assert.equal(handoff.packets[0].spawn_config.fork_turns, 'none');
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const partial = await f.service.call('native_next', binding);
  assert.equal(partial.next_action, 'repair_recorded_agent');
  assert.equal(partial.agent_id, 'batch-child');
  assert.deepEqual(partial.unresolved_item_indices, [7]);
  assert.deepEqual(partial.accepted_item_indices, [0,1,2,3,4,5,6,8,9]);
  assert.doesNotMatch(partial.repair_prompt, /Task bundle:/);
  assert.doesNotMatch(partial.repair_prompt,/Host-selected unresolved positions/);
  assert.equal(partial.followup_config.target,'batch-child');
  assert.equal(partial.item_index,7);
  assert.deepEqual(partial.next_action_args,binding);
  assert.match(partial.followup_config.message,/Return exactly 1 ordered items for initial assignment positions \[8\] \(one-based\)/);
  assert.doesNotMatch(partial.followup_config.message,/Process assigned jobs|"jobs":|"result_schema":/);
  await f.service.call('native_followed_up',partial.next_action_args);
  const prior = await f.service.call('get', binding);
  assert.equal(Object.keys(prior.nodes.worker.attempts[0].native_item_results).length, 9);
  assert.equal(prior.nodes.worker.attempts[0].native_item_results[7], undefined);
  assert.deepEqual(prior.nodes.worker.attempts[0].native_repair_followups['0:1'].item_indices,[7]);
  const completed = await f.service.call('native_next', binding);
  assert.equal(completed.next_action, 'workflow_native_next');
  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, jobs.map(job => [job]));
  assert.deepEqual(observed, [['batch-child'], ['batch-child']]);
  assert.deepEqual(Object.values(state.nodes.worker.attempts[0].native_agents), ['batch-child']);
});

test('a schema-valid shared change is admitted as delegated work instead of retrying the local item', async t => {
  const f = await fixture(t, async ids => ({status:'completed',agent_id:ids[0],turn_id:'delegated-turn',result:{items:[{
    outcome:'delegated',block_reason:'Shared runtime work belongs to the integration owner.',
    result:{changes:'Local card and scenarios written.',shared_change:'Add the shared transform hook.'},
  }]}}));
  const workflow=definition('native-delegated-shared-change','capped-one');
  workflow.inputs_schema={type:'object',additionalProperties:false,required:['jobs'],properties:{jobs:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['write_paths'],properties:{write_paths:{type:'array',minItems:1,items:{type:'string'}}}}}}};
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.access='bounded_write';worker.path_scope={binding:'run.allowed_paths'};worker.fanout.result_mode='per_item';
  worker.fanout.write_paths_field='write_paths';worker.fanout.shared_change_field='shared_change';
  worker.outputs_schema={type:'object',additionalProperties:false,required:['results'],properties:{results:{type:'array',minItems:1,items:{type:'object',additionalProperties:false,required:['changes','shared_change'],properties:{changes:{type:'string'},shared_change:{type:'string'}}}}}};
  const integrator={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
    access:'bounded_write',path_scope:{binding:'run.allowed_paths'},approval:{required:false},retry:{max_attempts:3},
    input_bindings:{requests:{path:'/nodes/worker/output/results',pluck:'shared_change'}},prompt_template:'Apply shared changes once.',
    outputs_schema:{type:'object',additionalProperties:false,required:['all_passed','evidence'],properties:{all_passed:{type:'boolean'},evidence:{type:'string'}}},
    completion_contract:{on_missing:'block',outcome:'validated_artifact',fail_on_false:['all_passed']}};
  workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,integrator);
  workflow.edges=[{id:'start-worker',source:'start',target:'worker'},{id:'worker-integrator',source:'worker',target:'integrator'},
    {id:'integrator-final',source:'integrator',target:'final'},{id:'final-end',source:'final',target:'end'}];
  workflow.nodes.find(node=>node.id==='final').input_bindings={evidence:'/nodes/integrator/output/evidence'};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'bounded_write',allowed_paths:['.'],main_actor:'root',native_parent_thread_id:PARENT_THREAD_ID,
    inputs:{jobs:[{write_paths:['cards/one.ts']}]}});
  const binding=control(run),handoff=await f.service.call('native_next',binding);
  assert.deepEqual(handoff.result_schema.properties.items.items.properties.outcome.enum,['completed','delegated','blocked']);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'delegating-child'});
  const continued=await f.service.call('native_next',binding);
  assert.equal(continued.next_action,'workflow_native_next');
  const state=await f.service.call('get',binding),attempt=state.nodes.worker.attempts[0];
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,[{changes:'Local card and scenarios written.',shared_change:'Add the shared transform hook.'}]);
  assert.equal(attempt.native_item_results[0].delegated,true);
  assert.match(attempt.native_item_results[0].delegation_reason,/integration owner/);
});

test('incremental ten-item delivery checkpoints one item per turn in the same child and repairs only the failed item', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  const observed = [];
  let blockedSeven = false;
  const f = await fixture(t, async ids => {
    const state = await f.service.call('get', binding);
    const attempt = state.nodes.worker.attempts[0];
    const unresolved = jobs.find(index => !attempt.native_item_results?.[index]);
    observed.push({ ids: [...ids], unresolved });
    if (unresolved === 7 && !blockedSeven) {
      blockedSeven = true;
      return { status: 'completed', agent_id: ids[0], turn_id: 'turn-7-blocked', result: {
        items: [{ outcome: 'blocked', block_reason: 'Scenario 7 needs correction' }],
      } };
    }
    return { status: 'completed', agent_id: ids[0], turn_id: `turn-${unresolved}`, result: {
      items: [{ outcome: 'completed', result: [unresolved] }],
    } };
  });
  const workflow = definition('native-per-item-incremental-ten', 'capped-one');
  const worker = workflow.nodes.find(node => node.id === 'worker');
  worker.fanout.result_mode = 'per_item';
  worker.fanout.item_delivery = 'incremental';
  worker.retry.max_attempts = 3;
  let binding;
  ({ binding } = await startRun(f, workflow, { jobs }));

  const handoff = await f.service.call('native_next', binding);
  assert.deepEqual(handoff.packets.map(packet => packet.index), [0]);
  assert.equal(handoff.packets[0].spawn_config.fork_turns, 'none');
  const firstBundle = JSON.parse(await readFile(handoff.packets[0].task_bundle_path, 'utf8'));
  assert.equal(Object.hasOwn(firstBundle,'item_positions'),false);
  assert.equal(firstBundle.result_schema.properties.items.minItems,1);
  assert.equal(firstBundle.result_schema.properties.items.maxItems,1);
  const firstInputs = JSON.parse(firstBundle.task.match(/\nInputs:\n([^\n]+)/)?.[1] ?? 'null');
  assert.deepEqual(firstInputs.jobs, [0]);
  await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'incremental-child',
  });

  for (let expected = 0; expected < jobs.length; expected++) {
    let next = await f.service.call('native_next', binding);
    if (expected === 7) {
      assert.equal(next.next_action, 'repair_recorded_agent');
      assert.equal(next.agent_id, 'incremental-child');
      assert.deepEqual(next.accepted_item_indices, [0,1,2,3,4,5,6]);
      assert.deepEqual(next.unresolved_item_indices, [7,8,9]);
      const beforeRepair = await f.service.call('get', binding);
      assert.equal(Object.keys(beforeRepair.nodes.worker.attempts[0].native_item_results).length, 7);
      await f.service.call('native_followed_up',next.next_action_args);
      next = await f.service.call('native_next', binding);
    }
    if (expected < jobs.length - 1) {
      assert.equal(next.next_action, 'continue_recorded_agent');
      assert.equal(next.followup_config.target, 'incremental-child');
      assert.equal(next.item_index, expected + 1);
      assert.deepEqual(next.next_action_args,binding);
      const task = inlineNativeTask(next.followup_config.message);
      assert.equal(Object.hasOwn(task,'item_positions'),false);
      const taskInputs = JSON.parse(task.task.match(/\nInputs:\n([^\n]+)/)?.[1] ?? 'null');
      assert.deepEqual(taskInputs.jobs, [expected + 1]);
      if (expected === 0) {
        const recovered = await f.service.call('native_next', binding);
        assert.equal(recovered.status, 'native_item_continuation_pending');
        assert.deepEqual(recovered.followup_config, next.followup_config);
        assert.deepEqual(recovered.next_action_args, next.next_action_args);
      }
      const followed = await f.service.call('native_followed_up', next.next_action_args);
      assert.equal(followed.next_action, 'workflow_native_next');
      assert.deepEqual(followed.next_action_args,binding);
    } else {
      assert.equal(next.next_action, 'workflow_native_next');
    }
  }

  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, jobs.map(job => [job]));
  assert.deepEqual(Object.values(state.nodes.worker.attempts[0].native_agents), ['incremental-child']);
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_followups).length, 9);
  assert.deepEqual(observed.map(item => item.ids), Array(11).fill(['incremental-child']));
  assert.deepEqual(observed.map(item => item.unresolved), [0,1,2,3,4,5,6,7,7,8,9]);
});

for (const scenario of [
  { name: 'post-seal uncapped', mode: 'uncapped-three', scheduling: 'parallel', interruptNextPreparation: true },
  { name: 'pre-seal capped', mode: 'capped-one', scheduling: 'parallel', maxConcurrency: 1 },
  { name: 'pre-seal serial', mode: 'capped-one', scheduling: 'serial' },
]) {
  test(`incremental ${scenario.name} recovery replays an undelivered repair before observing again`, async t => {
    const jobs = [10, 20, 30];
    let binding;
    let rejectedItemOne = false;
    const observed = [];
    const f = await fixture(t, async ids => {
      assert.deepEqual(ids, ['repair-replay-child']);
      const state = await f.service.call('get', binding);
      const attempt = state.nodes.worker.attempts[0];
      const itemIndex = jobs.findIndex((_, index) => !attempt.native_item_results?.[index]);
      assert.ok(itemIndex >= 0, 'The observer must only see an unresolved item');
      assert.equal(attempt.native_pending_followup ?? null, null,
        'The Host must resolve every pending follow-up before invoking the observer');
      observed.push(itemIndex);
      if (itemIndex === 1 && !rejectedItemOne) {
        rejectedItemOne = true;
        return { status: 'completed', agent_id: ids[0], turn_id: 'item-one-blocked', result: {
          items: [{ outcome: 'blocked', block_reason: 'Item 20 needs repair' }],
        } };
      }
      return { status: 'completed', agent_id: ids[0], turn_id: `item-${itemIndex}-accepted`, result: {
        items: [{ outcome: 'completed', result: [jobs[itemIndex]] }],
      } };
    });
    let failAfterRepairResult = false;
    let prepareInterrupted = false;
    if (scenario.interruptNextPreparation) {
      const originalOpen = f.service.open.bind(f.service);
      f.service.open = async (...args) => {
        const opened = await originalOpen(...args);
        const originalPrepare = opened.executor.prepare.bind(opened.executor);
        opened.executor.prepare = async (...prepareArgs) => {
          if (failAfterRepairResult && !prepareInterrupted) {
            const record = await opened.runtime.runs.read(binding.run_id);
            const attempt = record.state.nodes.worker.attempts[0];
            if (attempt.native_item_results?.[1] && !attempt.native_pending_followup) {
              prepareInterrupted = true;
              throw Object.assign(new Error('Simulated interruption after repaired result persistence'), {
                code: 'TEST_PREPARE_INTERRUPTED',
              });
            }
          }
          return originalPrepare(...prepareArgs);
        };
        return opened;
      };
    }
    const workflow = definition(`native-incremental-${scenario.name.replaceAll(' ', '-')}`, scenario.mode);
    const worker = workflow.nodes.find(node => node.id === 'worker');
    worker.fanout.batch_size = jobs.length;
    worker.fanout.result_mode = 'per_item';
    worker.fanout.item_delivery = 'incremental';
    worker.fanout.scheduling = scenario.scheduling;
    if (scenario.maxConcurrency) worker.fanout.max_concurrency = scenario.maxConcurrency;
    else if (scenario.scheduling === 'serial') delete worker.fanout.max_concurrency;
    worker.retry.max_attempts = 3;
    ({ binding } = await startRun(f, workflow, { jobs }));

    const handoff = await f.service.call('native_next', binding);
    assert.deepEqual(handoff.packets.map(packet => packet.index), [0]);
    await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'repair-replay-child' });

    const firstContinuation = await f.service.call('native_next', binding);
    assert.equal(firstContinuation.next_action, 'continue_recorded_agent');
    assert.equal(firstContinuation.item_index, 1);
    await f.service.call('native_followed_up', firstContinuation.next_action_args);

    const repair = await f.service.call('native_next', binding);
    assert.equal(repair.status, 'native_agent_blocked');
    assert.equal(repair.next_action, 'repair_recorded_agent');
    assert.equal(repair.item_index, 1);
    assert.deepEqual(observed, [0, 1]);
    const beforeRecovery = await f.service.call('get', binding);
    const beforeAttempt = beforeRecovery.nodes.worker.attempts[0];
    assert.deepEqual(beforeAttempt.native_item_results[0], {
      agent_id: 'repair-replay-child', result: [10], turn_id: 'item-0-accepted',
    });
    assert.equal(Object.hasOwn(beforeAttempt.native_item_results, '1'), false,
      'A rejected item stays unresolved until its repair is observed');
    assert.equal(beforeAttempt.native_rejected_turns[0].count, 1);
    assert.equal(beforeAttempt.native_pending_followup.index, 0);
    assert.equal(beforeAttempt.native_pending_followup.agent_id, 'repair-replay-child');
    assert.equal(beforeAttempt.native_pending_followup.item_index, 1);
    assert.match(beforeAttempt.native_pending_followup.task_bundle_sha256, /^[a-f0-9]{64}$/);
    assert.equal(beforeAttempt.native_pending_followup.followup_kind, 'repair');
    assert.equal(beforeAttempt.native_pending_followup.rejection_count, 1);

    const recoveredRepair = await f.service.call('native_next', binding);
    assert.deepEqual(recoveredRepair, repair,
      'Recovery must regenerate the exact persisted repair packet and message');
    const afterRecovery = await f.service.call('get', binding);
    const afterAttempt = afterRecovery.nodes.worker.attempts[0];
    assert.equal(afterRecovery.sequence, beforeRecovery.sequence,
      'Replaying pending delivery must not append another rejection or follow-up intent');
    assert.equal(afterAttempt.native_rejected_turns[0].count, 1);
    assert.deepEqual(afterAttempt.native_pending_followup, beforeAttempt.native_pending_followup);
    assert.deepEqual(afterAttempt.native_item_results, beforeAttempt.native_item_results,
      'Recovery must retain accepted siblings and must not accept the rejected turn');
    assert.deepEqual(observed, [0, 1], 'Recovery must not observe the undelivered repair turn');

    await f.service.call('native_followed_up', recoveredRepair.next_action_args);
    let secondContinuation;
    if (scenario.interruptNextPreparation) {
      failAfterRepairResult = true;
      await assert.rejects(f.service.call('native_next', binding), error => error.code === 'TEST_PREPARE_INTERRUPTED');
      assert.equal(prepareInterrupted, true, 'The service reached continuation preparation only after persisting the repaired item');
      failAfterRepairResult = false;
    } else {
      const repairContext = await nativeAttemptContext(f, { ...binding, attempt_id: repair.attempt_id });
      const repairResult = await repairContext.runtime.recordNativeItemResults(binding.run_id, {
        ...repairContext.binding, index: 0, agent_id: 'repair-replay-child', turn_id: 'item-1-accepted',
        target_indices: [1], result: { items: [{ outcome: 'completed', result: [20] }] },
      });
      assert.deepEqual(repairResult.accepted_item_indices, [0, 1]);
      assert.deepEqual(repairResult.unresolved_item_indices, [2]);
    }
    const interrupted = await f.service.call('get', binding);
    const interruptedAttempt = interrupted.nodes.worker.attempts[0];
    assert.equal(interruptedAttempt.native_pending_followup ?? null, null,
      'Simulate recovery after the repaired result is journaled but before the next packet intent exists');
    assert.deepEqual(interruptedAttempt.native_item_results[1], {
      agent_id: 'repair-replay-child', result: [20], turn_id: 'item-1-accepted',
    });
    assert.equal(interruptedAttempt.native_last_followup.followup_kind, 'repair');
    assert.equal(interruptedAttempt.native_last_followup.item_index, 1);
    const observedBeforeRecovery = [...observed];

    secondContinuation = await f.service.call('native_next', binding);
    assert.equal(secondContinuation.next_action, 'continue_recorded_agent');
    assert.equal(secondContinuation.item_index, 2,
      'Recovery must deliver the next incremental item after the repaired result is already accepted');
    assert.deepEqual(observed, observedBeforeRecovery, 'Recovery returns item 2 before asking the child for another turn');
    const continuationState = await f.service.call('get', binding);
    assert.equal(continuationState.nodes.worker.attempts[0].native_pending_followup.followup_kind, 'incremental');
    assert.equal(continuationState.nodes.worker.attempts[0].native_pending_followup.item_index, 2);
    await f.service.call('native_followed_up', secondContinuation.next_action_args);
    const completed = await f.service.call('native_next', binding);
    assert.equal(completed.next_action, 'workflow_native_next');
    assert.deepEqual(observed, scenario.interruptNextPreparation ? [0, 1, 1, 2] : [0, 1, 2]);

    const finalState = await f.service.call('get', binding);
    assert.equal(finalState.nodes.worker.status, 'succeeded');
    assert.deepEqual(finalState.nodes.worker.output.results, jobs.map(job => [job]));
    assert.deepEqual(finalState.nodes.worker.attempts[0].native_item_results[0], {
      agent_id: 'repair-replay-child', result: [10], turn_id: 'item-0-accepted',
    }, 'The earlier accepted sibling remains journaled after repair');
    assert.deepEqual(finalState.nodes.worker.attempts[0].native_item_results[1], {
      agent_id: 'repair-replay-child', result: [20], turn_id: 'item-1-accepted',
    });
    assert.deepEqual(finalState.nodes.worker.attempts[0].native_item_results[2], {
      agent_id: 'repair-replay-child', result: [30], turn_id: 'item-2-accepted',
    });
    assert.equal(finalState.nodes.final.status, 'ready', 'The full Host-owned item join releases the successor');
  });
}

test('uncapped parallel incremental partitions continue their recorded children, join every item and complete downstream', async t => {
  const jobs=[0,1,2,3],observed=[];
  let binding;
  const f=await fixture(t,async ids=>{
    const state=await f.service.call('get',binding);
    if(state.nodes.worker.status==='running'){
      const attempt=state.nodes.worker.attempts[0],agentId=ids[0];
      assert.notEqual(attempt.native_pending_followup?.followup_kind,'incremental',
        'The Host must resolve a pending incremental continuation before observing the old Agent turn again');
      const slot=Object.entries(attempt.native_agents??{}).find(([,id])=>id===agentId)?.[0];
      assert.notEqual(slot,undefined,'Observer must receive a journaled worker Agent');
      const assigned=jobs.slice(Number(slot)*2,Number(slot)*2+2);
      const itemIndex=assigned.find(index=>!attempt.native_item_results?.[index]);
      assert.notEqual(itemIndex,undefined,'Observer must receive a partition with an unresolved item');
      observed.push({node:'worker',agent_id:agentId,item_index:itemIndex});
      return {status:'completed',agent_id:agentId,turn_id:`${agentId}-turn-${itemIndex}`,
        result:{items:[{outcome:'completed',result:[itemIndex]}]}};
    }
    assert.equal(state.nodes.integrator.status,'running','Only the released downstream node may be observed after the join');
    observed.push({node:'integrator',agent_id:ids[0]});
    return {status:'completed',agent_id:ids[0],turn_id:'downstream-integrator-turn',result:{summary:'all joined items integrated'}};
  });
  const workflow=definition('native-per-item-incremental-uncapped','uncapped-three');
  const worker=workflow.nodes.find(node=>node.id==='worker');
  worker.fanout.batch_size=2;
  worker.fanout.result_mode='per_item';
  worker.fanout.item_delivery='incremental';
  assert.equal(Object.hasOwn(worker.fanout,'max_concurrency'),false);
  const integrator={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
    access:'read_only',approval:{required:false},retry:{max_attempts:2},
    input_bindings:{results:'/nodes/worker/output/results'},prompt_template:'Integrate the complete joined results.',
    outputs_schema:{type:'object',properties:{summary:{type:'string'}},required:['summary'],additionalProperties:false}};
  workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,integrator);
  workflow.edges=[{id:'start-worker',source:'start',target:'worker'},{id:'worker-integrator',source:'worker',target:'integrator'},
    {id:'integrator-final',source:'integrator',target:'final'},{id:'final-end',source:'final',target:'end'}];
  workflow.nodes.find(node=>node.id==='final').input_bindings={summary:'/nodes/integrator/output/summary'};
  const created=await f.service.call('create',{workflow},{human:true});
  const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,
    access:'read_only',main_actor:'root',native_parent_thread_id:PARENT_THREAD_ID,inputs:{jobs}});
  binding=control(run);

  const handoff=await f.service.call('native_next',binding);
  assert.equal(handoff.status,'native_handoff');
  assert.deepEqual(handoff.packets.map(packet=>packet.index),[0,1]);
  for(const packet of handoff.packets){
    const bundle=JSON.parse(await readFile(packet.task_bundle_path,'utf8'));
    const taskInputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    assert.deepEqual(taskInputs.jobs,[jobs[packet.index*2]],
      'Initial incremental delivery starts with the first item in each partition');
    await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:packet.index,
      agent_id:`uncapped-incremental-child-${packet.index}`});
  }

  const continuations=[];
  let next=await f.service.call('native_next',binding);
  assert.equal(next.next_action,'continue_recorded_agent');
  const firstContinuation={index:next.index,item_index:next.item_index,agent_id:next.agent_id,
    accepted_item_indices:next.accepted_item_indices};
  const recorded=await f.service.call('get',binding);
  assert.deepEqual(recorded.nodes.worker.attempts[0].native_item_results[0],
    {agent_id:'uncapped-incremental-child-0',result:[0],turn_id:'uncapped-incremental-child-0-turn-0'});
  assert.deepEqual(recorded.nodes.worker.attempts[0].native_rejected_turns??{},{});
  assert.equal(observed.length,1);
  const repeated=await f.service.call('native_next',binding);
  assert.equal(repeated.next_action,'continue_recorded_agent');
  assert.equal(repeated.agent_id,next.agent_id);
  assert.equal(repeated.item_index,next.item_index);
  assert.deepEqual(repeated.followup_config,next.followup_config);
  assert.deepEqual(repeated.accepted_item_indices,next.accepted_item_indices);
  const stillPending=await f.service.call('get',binding);
  assert.equal(Object.keys(stillPending.nodes.worker.attempts[0].native_item_results).length,1);
  assert.deepEqual(stillPending.nodes.worker.attempts[0].native_rejected_turns??{},{});
  assert.equal(observed.length,1,'Repeating native_next must not re-observe or accept the old turn');
  continuations.push(firstContinuation);
  await f.service.call('native_followed_up',next.next_action_args);
  next=await f.service.call('native_next',binding);
  while(next.next_action==='continue_recorded_agent'){
    continuations.push({index:next.index,item_index:next.item_index,agent_id:next.agent_id,
      accepted_item_indices:next.accepted_item_indices});
    const bundle=inlineNativeTask(next.followup_config.message);
    const taskInputs=JSON.parse(bundle.task.match(/\nInputs:\n([^\n]+)/)?.[1]??'null');
    assert.deepEqual(taskInputs.jobs,[next.item_index],
      'A continuation carries only the next unresolved item, never an accepted item');
    await f.service.call('native_followed_up',next.next_action_args);
    next=await f.service.call('native_next',binding);
  }
  assert.equal(next.next_action,'workflow_native_next');
  let state=await f.service.call('get',binding);
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(state.nodes.worker.output.results,jobs.map(job=>[job]));
  assert.equal(state.nodes.integrator.status,'ready','The downstream integrator is released only after the full item join');
  assert.equal(state.nodes.final.status,'pending');
  assert.deepEqual(continuations,[
    {index:0,item_index:1,agent_id:'uncapped-incremental-child-0',accepted_item_indices:[0]},
    {index:1,item_index:3,agent_id:'uncapped-incremental-child-1',accepted_item_indices:[2]},
  ]);

  const downstream=await f.service.call('native_next',binding);
  assert.equal(downstream.status,'native_handoff');
  assert.equal(downstream.node_id,'integrator');
  assert.equal(downstream.packets.length,1);
  await recordNativeSpawn(f,{...binding,attempt_id:downstream.attempt_id,index:downstream.packets[0].index,
    agent_id:'uncapped-incremental-downstream-integrator'});
  const completed=await f.service.call('native_next',binding);
  assert.equal(completed.next_action,'workflow_native_next');
  state=await f.service.call('get',binding);
  assert.equal(state.nodes.integrator.status,'succeeded');
  assert.deepEqual(state.nodes.integrator.output,{summary:'all joined items integrated'});
  assert.equal(state.nodes.final.status,'ready');
  assert.deepEqual(observed,[
    {node:'worker',agent_id:'uncapped-incremental-child-0',item_index:0},
    {node:'worker',agent_id:'uncapped-incremental-child-0',item_index:1},
    {node:'worker',agent_id:'uncapped-incremental-child-1',item_index:2},
    {node:'worker',agent_id:'uncapped-incremental-child-1',item_index:3},
    {node:'integrator',agent_id:'uncapped-incremental-downstream-integrator'},
  ]);
});

test('per-item native results reject copied Host indices and wrong cardinality atomically', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `invalid-${++turn}`, result: {
    items: turn === 1
      ? [{ outcome: 'completed', result: [0] }, { item_index: 1, outcome: 'completed', result: [1] }]
      : Array.from({length:10},(_,index)=>({outcome:'completed',result:[index]})),
  } }));
  const workflow = definition('native-per-item-invalid', 'capped-one');
  const worker = workflow.nodes.find(node => node.id === 'worker');
  worker.fanout.result_mode = 'per_item';worker.retry.max_attempts = 3;
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'exact-child' });
  const copied = await f.service.call('native_next', binding);
  assert.equal(copied.status, 'native_agent_invalid_result');
  assert.match(copied.reason, /returned 2 entries for 10 Host-selected items; no positional result was accepted/);
  assert.deepEqual(copied.unresolved_item_indices,jobs);
  await f.service.call('native_followed_up',copied.next_action_args);
  const completed = await f.service.call('native_next', binding);
  assert.equal(completed.next_action,'workflow_native_next');
  const state=await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.attempts[0].native_item_results[1],{agent_id:'exact-child',result:[1]});
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_item_results).length,10);
});

test('concurrent per-item batches join out-of-order child results in original input order', async t => {
  const jobs = Array.from({ length: 20 }, (_, index) => index);
  const observed = [];
  const f = await fixture(t, async ids => {
    observed.push([...ids]);
    const id = ids.includes('agent-1') ? 'agent-1' : ids[0];
    const start = id === 'agent-1' ? 10 : 0;
    return { status: 'completed', agent_id: id, turn_id: `turn-${id}`, result: {
      items: jobs.slice(start, start + 10).map(job => ({outcome: 'completed', result: [job]})),
    } };
  });
  const workflow = definition('native-per-item-parallel', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  assert.deepEqual(handoff.packets.map(packet => packet.index), [0, 1]);
  for (let index = 0; index < 2; index++) await recordNativeSpawn(f, {
    ...binding, attempt_id: handoff.attempt_id, index, agent_id: `agent-${index}`,
  });
  await f.service.call('native_next', binding);
  const state = await f.service.call('get', binding);
  assert.deepEqual(state.nodes.worker.output.results, jobs.map(job => [job]));
  assert.deepEqual(observed, [['agent-0','agent-1'],['agent-0']]);
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_item_results).length, 20);
});

test('per-item repair exhaustion retains nine accepted items without accepting a blocked tenth', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `turn-${++turn}`, result: {
    items: turn === 1
      ? jobs.map((job, item_index) => item_index === 7
        ? { outcome: 'blocked', block_reason: 'Still failing' }
        : { outcome: 'completed', result: [job] })
      : [{ outcome: 'blocked', block_reason: 'Still failing' }],
  } }));
  const workflow = definition('native-per-item-exhaustion', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const repair=await f.service.call('native_next', binding);
  assert.equal(repair.next_action, 'repair_recorded_agent');
  await f.service.call('native_followed_up',repair.next_action_args);
  const exhausted = await f.service.call('native_next', binding);
  assert.equal(exhausted.status, 'native_agent_repair_exhausted');
  assert.deepEqual(exhausted.unresolved_item_indices, [7]);
  const state = await f.service.call('get', binding);
  assert.equal(state.nodes.worker.status, 'failed');
  assert.equal(Object.keys(state.nodes.worker.attempts[0].native_item_results).length, 9);
  assert.equal(state.nodes.worker.attempts[0].native_item_results[7], undefined);
});

test('invalid per-item semantic value keeps valid siblings and rejects extra ordered entries without overwriting accepted values', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => {
    turn++;
    const items = turn === 1
      ? jobs.map((job, item_index) => ({ outcome: 'completed', result: item_index === 7 ? 'invalid' : [job] }))
      : turn === 2
        ? [{ outcome: 'completed', result: [7] }, { outcome: 'completed', result: [999] }]
        : [{ outcome: 'completed', result: [7] }];
    return { status: 'completed', agent_id: ids[0], turn_id: `turn-${turn}`, result: { items } };
  });
  const workflow = definition('native-per-item-conflict', 'capped-one');
  const worker=workflow.nodes.find(node=>node.id==='worker');worker.fanout.result_mode='per_item';worker.retry.max_attempts=3;
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const invalid = await f.service.call('native_next', binding);
  assert.deepEqual(invalid.unresolved_item_indices, [7]);
  assert.match(invalid.reason, /item 7/);
  await f.service.call('native_followed_up',invalid.next_action_args);
  const extra = await f.service.call('native_next', binding);
  assert.equal(extra.status, 'native_agent_invalid_result');
  assert.match(extra.reason, /returned 2 entries for 1 Host-selected items/);
  await f.service.call('native_followed_up',extra.next_action_args);
  assert.deepEqual(extra.unresolved_item_indices, [7]);
  assert.match(extra.repair_prompt,/initial assignment positions \[8\]/);
  const before = await f.service.call('get', binding);
  assert.deepEqual(before.nodes.worker.attempts[0].native_item_results[0], { agent_id:'batch-child',result:[0] });
  assert.equal(before.nodes.worker.attempts[0].native_item_results[7],undefined);
  await f.service.call('native_next', binding);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results, jobs.map(job=>[job]));
});

test('per-item top-level rejection recomputes unresolved indices from accepted journal', async t => {
  for(const invalidResult of [
    {status:'completed',result:{wrong:[]}},
    {status:'blocked',reason:'Remaining item needs correction'},
    {status:'invalid',reason:'Malformed completion envelope'},
  ])await t.test(invalidResult.status+(invalidResult.result?' container':''),async t=>{
    const jobs=Array.from({length:10},(_,index)=>index);
    let turn=0;
    const f=await fixture(t,async ids=>{
      turn++;
      if(turn===1)return {status:'completed',agent_id:ids[0],turn_id:'partial',result:{items:jobs
        .map((job,index)=>index===9?{outcome:'completed',result:'invalid'}:{outcome:'completed',result:[job]})}};
      if(turn===2)return {agent_id:ids[0],turn_id:'bad-top',...invalidResult};
      return {status:'completed',agent_id:ids[0],turn_id:'repaired',result:{items:[
        {outcome:'completed',result:[9]}]}};
    });
    const workflow=definition('native-per-item-top-'+invalidResult.status+(invalidResult.result?'-container':''),'capped-one');
    const worker=workflow.nodes.find(node=>node.id==='worker');worker.fanout.result_mode='per_item';worker.retry.max_attempts=3;
    const {binding}=await startRun(f,workflow,{jobs});
    const handoff=await f.service.call('native_next',binding);
    await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'batch-child'});
    const partial=await f.service.call('native_next',binding);
    assert.deepEqual(partial.unresolved_item_indices,[9]);
    await f.service.call('native_followed_up',partial.next_action_args);
    const top=await f.service.call('native_next',binding);
    assert.deepEqual(top.unresolved_item_indices,[9]);
    assert.deepEqual(top.accepted_item_indices,jobs.slice(0,9));
    assert.match(top.repair_prompt,/initial assignment positions \[10\]/);
    assert.doesNotMatch(top.repair_prompt,/Host-selected unresolved positions/);
    assert.equal(top.next_action,'repair_recorded_agent');
    assert.equal(Object.keys((await f.service.call('get',binding)).nodes.worker.attempts[0].native_item_results).length,9);
    await f.service.call('native_followed_up',top.next_action_args);
    await f.service.call('native_next',binding);
    assert.deepEqual((await f.service.call('get',binding)).nodes.worker.output.results,jobs.map(job=>[job]));
  });
});

test('nine valid items survive one malformed semantic item and same child repairs only that item', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let turn = 0;
  const f = await fixture(t, async ids => ({ status: 'completed', agent_id: ids[0], turn_id: `turn-${++turn}`, result: {
    items: turn === 1
      ? jobs.map((job, item_index) => ({outcome:'completed',result:item_index===7?'invalid':[job]}))
      : [{outcome:'completed',result:[7]}],
  } }));
  const workflow = definition('native-per-item-malformed', 'capped-one');
  workflow.nodes.find(node => node.id === 'worker').fanout.result_mode = 'per_item';
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'batch-child' });
  const partial = await f.service.call('native_next', binding);
  assert.deepEqual(partial.accepted_item_indices, [0,1,2,3,4,5,6,8,9]);
  assert.deepEqual(partial.unresolved_item_indices, [7]);
  assert.match(partial.reason, /item 7/);
  assert.match(partial.repair_prompt,/initial assignment positions \[8\]/);
  assert.doesNotMatch(partial.repair_prompt,/Host-selected unresolved positions/);
  assert.equal(Object.keys((await f.service.call('get', binding)).nodes.worker.attempts[0].native_item_results).length,9);
  await f.service.call('native_followed_up',partial.next_action_args);
  await f.service.call('native_next', binding);
  assert.equal(turn,2);
  assert.deepEqual((await f.service.call('get', binding)).nodes.worker.output.results,jobs.map(job=>[job]));
});

test('a replayed rejected per-item turn does not spend another correction or replace accepted items', async t => {
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  let observations = 0;
  const f = await fixture(t, async ids => {
    observations++;
    if (observations <= 2) return { status:'completed',agent_id:ids[0],turn_id:'bad-turn',result:{items:
      jobs.map((job,item_index)=>item_index===7
        ? {outcome:'blocked',block_reason:'Repair item seven'}
        : {outcome:'completed',result:[job]})} };
    return {status:'completed',agent_id:ids[0],turn_id:'fixed-turn',result:{items:[{outcome:'completed',result:[7]}]}};
  });
  const workflow=definition('native-per-item-replay','capped-one');
  workflow.nodes.find(node=>node.id==='worker').fanout.result_mode='per_item';
  const {binding}=await startRun(f,workflow,{jobs});
  const handoff=await f.service.call('native_next',binding);
  await recordNativeSpawn(f,{...binding,attempt_id:handoff.attempt_id,index:0,agent_id:'batch-child'});
  const repair=await f.service.call('native_next',binding);
  assert.equal(repair.next_action,'repair_recorded_agent');
  await f.service.call('native_followed_up',repair.next_action_args);
  await f.service.call('native_next',binding);
  const attempt=(await f.service.call('get',binding)).nodes.worker.attempts[0];
  assert.equal(attempt.native_rejected_turns[0].count,1);
  assert.equal(Object.keys(attempt.native_item_results).length,10);
  assert.equal(observations,3);
});

test('cancellation during Host observation leaves a capped native node cancelled and unsealed', async t => {
  const entered = deferred();
  const release = deferred();
  const jobs = Array.from({ length: 10 }, (_, index) => index);
  const f = await fixture(t, async ids => {
    entered.resolve();
    await release.promise;
    return { status: 'completed', agent_id: ids[0], turn_id: 'late-turn', result: jobs };
  });
  const workflow = definition('native-capped-cancel', 'capped-one');
  const { binding } = await startRun(f, workflow, { jobs });
  const handoff = await f.service.call('native_next', binding);
  await recordNativeSpawn(f, { ...binding, attempt_id: handoff.attempt_id, index: 0, agent_id: 'late-child' });

  const pending = f.service.call('native_next', binding);
  const cancelledWait = assert.rejects(pending, { code: 'ATTEMPT_STOPPED' });
  await entered.promise;
  try {
    await f.service.call('cancel', binding);
  } finally {
    release.resolve();
    await cancelledWait;
  }

  const state = await f.service.call('get', binding);
  assert.equal(state.status, 'cancelled');
  assert.equal(state.nodes.worker.status, 'cancelled');
  assert.equal(state.nodes.worker.output, null);
  assert.equal(state.nodes.worker.attempts[0].dispatch.receipt ?? null, null);
});

const checkObject=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
const nativePageSchema=checkObject({name:{type:'string'},workspace:{type:'string'},destinations:{type:'array',items:{type:'string'}}});
const nativeSemanticSchema=checkObject({summary:{type:'string',minLength:1,maxLength:128*1024}});

test('native text amendment public repair seals the first draft and merges same-child edits',async t=>{
  const initial='old\r\n😀 unchanged';
  const f=await nativeCheckFixture(t,{single:true,textAmendment:true,accept:(_r,count)=>count>2,
    observer:async(ids,turn)=>turn===1?{status:'completed',agent_id:ids[0],turn_id:'amend-'+turn,result:{summary:initial}}
      :{status:'amendment',agent_id:ids[0],turn_id:'amend-'+turn,amendment:{amendments:[{field:'summary',start_line:1,end_line:1,replacement:turn===2?'better\r\n':'best\r\n'}]}}});
  const first=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.deepEqual(inlineNativeTask(publicPackets(first)[0].prompt).result_schema,nativeSemanticSchema);
  const repair=await f.service.call('native_spawned_batch',{batch_id:first.batch_id},MODEL_REQUEST);
  assert.match(repair.followup_config.message,/amendments/);assert(!repair.followup_config.message.includes(initial));
  const sameChild=repair.followup_config.target;
  const second=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal(second.followup_config.target,sameChild);
  const done=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal((await f.service.call('get',f.binding)).nodes.worker.status,'succeeded');
  assert.deepEqual(f.calls.map(c=>c.input.output.summary),[initial,'better\r\n😀 unchanged','best\r\n😀 unchanged']);
  assert.equal(done.status,'running');
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.binding.run_id),attempt=record.state.nodes.worker.attempts[0];
  assert.equal(Object.keys(attempt.native_text_amendments).length,2);
  for(const trace of Object.values(attempt.native_text_amendments)){
    const raw=await runtime.runs.readExecutorResult(f.binding.run_id,attempt.id,trace.raw_ref.sha256);
    assert.equal(raw.payload.amendments.length,1);assert.equal(raw.payload.summary,undefined);
    const merged=await runtime.runs.readExecutorResult(f.binding.run_id,attempt.id,trace.merged_ref.sha256);
    assert.match(merged.output.summary,/😀 unchanged$/);
  }
});

test('native text amendment restores exact pending repair and rejects baseline or binding tampering',async t=>{
  const f=await nativeCheckFixture(t,{single:true,textAmendment:true,accept:(_r,count)=>count>1,
    observer:async(ids,turn)=>turn===1?{status:'completed',agent_id:ids[0],turn_id:'sealed-first',result:{summary:'old'}}
      :{status:'amendment',agent_id:ids[0],turn_id:'sealed-edit',amendment:{amendments:[{field:'summary',start_line:1,end_line:1,replacement:'new'}]}}});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST),repair=await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.binding.run_id),attempt=record.state.nodes.worker.attempts[0];
  const binding={...f.binding,node_id:'worker',attempt_id:attempt.id,lease_token:leaseToken(f.binding.control_token,f.binding.run_id,'worker',attempt.id,attempt.lease_generation??0)};
  const ref=attempt.native_pending_followup.text_repair_ref;
  await assert.rejects(readNativeTextRepair(runtime,f.binding.run_id,binding,{...ref,artifact:'wrong.json'}),{code:'NATIVE_TEXT_AMENDMENT_BINDING'});
  f.service=new WorkflowService({configPath:f.service.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:f.service.capabilities});
  assert.deepEqual((await f.service.call('native_next',{},MODEL_REQUEST)).followup_config,repair.followup_config);
  assert.equal((await runtime.runs.read(f.binding.run_id)).sequence,record.sequence,
    'Exact published pending-repair replay must leave the journal unchanged');
  await assert.rejects(f.service.call('native_next',{...f.binding,control_token:'wrong'}),{code:'RUN_AUTHORITY'});
  assert.equal((await runtime.runs.read(f.binding.run_id)).sequence,record.sequence);
  const snapshot=await runtime.runs.readExecutorResult(f.binding.run_id,attempt.id,ref.sha256);
  const badSnapshot={...snapshot,native_observation:{...snapshot.native_observation,agent_id:'another-child'}};
  const badRef=await runtime.runs.saveExecutorResult(f.binding.run_id,attempt.id,badSnapshot);
  await assert.rejects(readNativeTextRepair(runtime,f.binding.run_id,binding,badRef),{code:'NATIVE_TEXT_AMENDMENT_BINDING'});
  for(const mutate of [s=>s.item_index=1,s=>s.native_observation.turn_id='other-turn',s=>s.lease_generation++,s=>s.scope.summary[0].end_line=2]){
    const changed=structuredClone(snapshot);mutate(changed);const changedRef=await runtime.runs.saveExecutorResult(f.binding.run_id,attempt.id,changed);
    await assert.rejects(readNativeTextRepair(runtime,f.binding.run_id,binding,changedRef),{code:'NATIVE_TEXT_AMENDMENT_BINDING'});
  }
  const path=join(runtime.runs.directory(f.binding.run_id),snapshot.input_ref.artifact),bytes=await readFile(path);
  await writeFile(path,'tampered');
  await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'EXECUTOR_RESULT_CORRUPT'});
  assert.equal(f.calls.length,1);await writeFile(path,bytes);
  assert.deepEqual((await f.service.call('native_next',{},MODEL_REQUEST)).followup_config,repair.followup_config);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.deepEqual(f.calls.map(c=>c.input.output.summary),['old','new']);
});

test('native pending incremental continuation replay preserves publication across repeated calls and service restart',async t=>{
  const f=await nativeCheckFixture(t,{incremental:true,itemCount:3});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  const continuation=await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  assert.equal(continuation.next_action,'continue_recorded_agent');
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.binding.run_id),attempt=record.state.nodes.worker.attempts[0];
  assert.equal(attempt.native_pending_followup.followup_kind,'incremental');assert.equal(attempt.native_pending_followup.item_index,1);
  const material=join(f.workspace,'work','.workflow-runtime','native-agent',f.binding.run_id,attempt.id,'partition-0','item-1');
  const before=await captureNativeWorkspace(f.workspace,{subtree:material});
  for(const restarted of [false,true]){
    if(restarted)f.service=new WorkflowService({configPath:f.service.configPath,defaultConfigPath:DEFAULT_CONFIG_PATH,env:{},capabilities:f.service.capabilities});
    const repeated=await f.service.call('native_next',{},MODEL_REQUEST);
    assert.deepEqual(repeated.followup_config,continuation.followup_config);
    const after=await runtime.runs.read(f.binding.run_id);
    assert.equal(after.sequence,record.sequence,'Published ordinary incremental continuation replay must not append publication events');
    assert.deepEqual(after.events,record.events);assert.deepEqual(after.state.nodes.worker.attempts[0],attempt);
    assert.deepEqual(await captureNativeWorkspace(f.workspace,{subtree:material}),before);
    assert.equal(f.calls.length,1);assert.equal(f.seen.length,1);
  }
  await assert.rejects(f.service.call('native_next',{...f.binding,control_token:'wrong'}),{code:'RUN_AUTHORITY'});
  assert.equal((await runtime.runs.read(f.binding.run_id)).sequence,record.sequence);
});

test('native pending incremental replay rejects changed published material without regenerating it',async t=>{
  const f=await nativeCheckFixture(t,{incremental:true,itemCount:2});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.binding.run_id),attempt=record.state.nodes.worker.attempts[0];
  const taskPath=join(f.workspace,'work','.workflow-runtime','native-agent',f.binding.run_id,attempt.id,'partition-0','item-1','task.json');
  const changed=Buffer.concat([await readFile(taskPath),Buffer.from(' ')]);await writeFile(taskPath,changed);
  await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'NATIVE_SPAN_PUBLICATION_CHANGED'});
  const after=await runtime.runs.read(f.binding.run_id);
  assert.equal(after.sequence,record.sequence);assert.deepEqual(after.events,record.events);
  assert.deepEqual(after.state.nodes.worker.attempts[0].native_pending_followup,attempt.native_pending_followup);
  assert.deepEqual(await readFile(taskPath),changed);assert.equal(f.calls.length,1);assert.equal(f.seen.length,1);
});

test('native pending repair replay rejects changed published material without republishing or checker effects',async t=>{
  const f=await nativeCheckFixture(t,{single:true,accept:()=>false});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.binding.run_id),attempt=record.state.nodes.worker.attempts[0];
  const taskPath=join(f.workspace,'work','.workflow-runtime','native-agent',f.binding.run_id,attempt.id,'partition-0','repair-1','task.json');
  const changed=Buffer.concat([await readFile(taskPath),Buffer.from(' ')]);await writeFile(taskPath,changed);
  await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'NATIVE_SPAN_PUBLICATION_CHANGED'});
  const after=await runtime.runs.read(f.binding.run_id);
  assert.equal(after.sequence,record.sequence);assert.deepEqual(after.events,record.events);
  assert.deepEqual(after.state.nodes.worker.attempts[0].native_pending_followup,attempt.native_pending_followup);
  assert.deepEqual(await readFile(taskPath),changed,'Replay must not regenerate changed published bytes');
  assert.equal(f.calls.length,1);assert.equal(f.seen.length,1);
});

test('native text amendment incremental same-slot repair retains accepted siblings and releases the next full item',async t=>{
  const f=await nativeCheckFixture(t,{textAmendment:true,incremental:true,itemCount:3,accept:r=>r.input.output.summary!=='draft b',
    observer:async(ids,turn)=>({agent_id:ids[0],turn_id:'incremental-text-'+turn,...(turn===3
      ?{status:'amendment',amendment:{amendments:[{field:'summary',start_line:1,end_line:1,replacement:'accepted b'}]}}
      :{status:'completed',result:{items:[{outcome:'completed',result:{summary:turn===1?'accepted a':turn===2?'draft b':'accepted c'}}]}})})});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  const itemB=await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  assert.equal(itemB.next_action,'continue_recorded_agent');
  const repair=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.match(repair.followup_config.message,/amendments/);assert.equal(repair.followup_config.target,itemB.followup_config.target);
  const itemC=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal(itemC.next_action,'continue_recorded_agent');assert.doesNotMatch(itemC.followup_config.message,/Amendment schema:/);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
  assert.deepEqual(state.nodes.worker.output.results.map(r=>r.summary),['accepted a','accepted b','accepted c']);
  assert.deepEqual(f.calls.map(c=>c.input.output.summary),['accepted a','draft b','accepted b','accepted c']);
  assert.equal(attempt.native_item_results[0].turn_id,'incremental-text-1');assert.equal(Object.keys(attempt.native_text_amendments).length,1);
});

test('native text amendment one-per-item batch repairs only its rejected child',async t=>{
  const f=await nativeCheckFixture(t,{textAmendment:true,itemCount:2,accept:r=>r.input.output.summary!=='draft',
    observer:async(ids,turn)=>{const slot=ids[0].split('_').at(-1);return {agent_id:ids[0],turn_id:`batch-text-${slot}-${turn}`,...(turn===2
      ?{status:'amendment',amendment:{amendments:[{field:'summary',start_line:1,end_line:1,replacement:'fixed'}]}}
      :{status:'completed',result:{items:[{outcome:'completed',result:{summary:slot==='1'?'draft':'accepted'}}]}})};}});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST),repair=await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding);
  assert.deepEqual(state.nodes.worker.output.results.map(r=>r.summary),['accepted','fixed']);assert.equal(f.calls.length,3);
  assert.equal(repair.followup_config.target,f.seen.at(-1)[0]);
});

// The whole fixture includes durable checker, amendment and replay I/O. Windows
// CI completed the ACK at 28.9s and hit the old 30s budget during final reads;
// actual event/ACK waits keep their independent 10s deadlines below.
test('native text amendment repair ACK accepts a ready sibling before the repairing child terminates',{timeout:60_000},async t=>{
  const began=performance.now();
  const phase=value=>console.log('NATIVE_REPAIR_SIBLING_PHASE '+value+' '+JSON.stringify({elapsed_ms:Math.round(performance.now()-began)}));
  phase('fixture');
  const draft='draft a\r\npreserved second line',fixed='accepted a\r\npreserved second line';
  const siblingChecked=deferred(),repairWaitArmed=deferred(),repairReleased=deferred();
  const f=await nativeCheckFixture(t,{itemCount:2,maxConcurrency:2,textAmendment:true,orchestration:true,max_attempts:3,transport:'direct_mcp',
    execute:async request=>{
      const complete=request.input.output.summary!==draft;
      await writeFile(join(request.context.workspace,'rendered.txt'),request.input.output.summary);
      if(request.input.inputs.jobs[0].name==='b')siblingChecked.resolve();
      return {exit_code:0,output:{complete,diagnostic:complete?'':'Correct only the first line.',
        repair_scope:complete?{}:{summary:[{start_line:1,end_line:1}]}},diagnostic:'',
        effects:{observed:true,changed_paths:['rendered.txt'],outside_paths:[],artifacts:[]}};
    }});
  const home=await mkdtemp(join(tmpdir(),'native-repair-sibling-'));await mkdir(join(home,'sessions'));
  t.after(()=>rm(home,{recursive:true,maxRetries:3,retryDelay:100}));
  const start=await f.service.call('native_next',{},MODEL_REQUEST),packets=publicPackets(start);
  phase('prepared');
  assert.deepEqual(packets.map(packet=>packet.index),[0,1]);
  for(const packet of packets)assert.deepEqual((await publicNativeTask(packet.prompt)).result_schema.properties.items.items.properties.result,nativeSemanticSchema);
  const agents=packets.map(packet=>'/root/'+packet.spawn_config.task_name),threads=new Map(),rpc={},observations=[];
  const row=(type,payload)=>JSON.stringify({timestamp:'2026-10-09T09:00:00.000Z',type,payload})+'\n';
  let repairing=false,repairTerminal=false,waits=0;
  for(const [index,agentId]of agents.entries()){
    const id=randomUUID(),path=join(home,'sessions','rollout-'+id+'.jsonl'),spawn={parent_thread_id:PARENT_THREAD_ID,agent_path:agentId};
    const thread={id,path,parentThreadId:PARENT_THREAD_ID,source:{subAgent:{thread_spawn:spawn}}};
    threads.set(agentId,{index,thread,firstTurn:'first-'+id,repairTurn:'repair-'+id});
    await writeFile(path,row('session_meta',{id,parent_thread_id:PARENT_THREAD_ID,agent_path:agentId,source:{subagent:{thread_spawn:spawn}}})
      +row('event_msg',{type:'task_started',turn_id:'first-'+id})+row('event_msg',{type:'task_complete',turn_id:'first-'+id}));
  }
  const client={async call(method,args){
    rpc[method]=(rpc[method]??0)+1;
    if(method==='thread/list')return {data:[...threads.values()].map(item=>item.thread)};
    const item=[...threads.values()].find(item=>item.thread.id===args.threadId);assert(item);
    if(method==='thread/read')return {thread:item.thread};
    assert.equal(method,'thread/turns/list');
    // The sibling becomes ready at ACK, so this test exercises collection during
    // repair rather than relying on how much work initial collection completes.
    const isRepair=item.index===0&&repairing,terminal=item.index===1?repairing:!isRepair||repairTerminal;
    const payload=isRepair?{amendments:[{field:'summary',start_line:1,end_line:1,replacement:'accepted a\r\n'}]}
      :{outcome:'completed',result:{items:[{outcome:'completed',result:{summary:item.index===0?draft:'accepted b'}}]}};
    return {data:[{id:isRepair?item.repairTurn:item.firstTurn,status:terminal?'completed':'inProgress',itemsView:args.itemsView,
      items:terminal&&args.itemsView==='full'?[{type:'agentMessage',phase:'final_answer',text:JSON.stringify(payload)}]:[]}]};
  }};
  f.service.nativeAgentObserver=async(ids,options)=>{
    const entry={agent_ids:[...ids],repairing,waits_before:waits,text_amendments:structuredClone(options.textAmendments)};observations.push(entry);
    const observed=await inspectNativeAgents(client,ids,{...options,
      signal:options.signal?AbortSignal.any([options.signal,t.signal]):t.signal,
      lifecycleHome:home,waitForTerminal:true,waitTimeoutMs:10_000,
      waitForChange:async({signal,timeoutMs})=>{
        waits++;repairWaitArmed.resolve();
        let abort,timer;const cancelled=new Promise((_resolve,reject)=>{
          abort=()=>reject(signal.reason);if(signal.aborted)abort();else signal.addEventListener('abort',abort,{once:true});
        });
        const expired=new Promise((_resolve,reject)=>{timer=setTimeout(()=>reject(Object.assign(
          new Error('Fixture child event wait reached its supplied deadline'),{code:'NATIVE_AGENT_WAIT_TIMEOUT'})),timeoutMs);});
        try{await Promise.race([repairReleased.promise,cancelled,expired]);return {event_scope:'child',event_type:'change',filename:'exact-first-child-repair'};}
        finally{clearTimeout(timer);signal.removeEventListener('abort',abort);}
      }});
    Object.assign(entry,{status:observed.status,agent_id:observed.agent_id,turn_id:observed.turn_id,waits_after:waits});return observed;
  };
  assert.equal(start.invocation_adapter.kind,'direct_mcp');
  phase('initial-collection');
  const repair=await f.service.call('native_spawned_batch',start.invocation_adapter.arguments,MODEL_REQUEST);
  phase('repair-issued');
  assert.equal(repair.next_action,'repair_recorded_agent');assert.equal(repair.followup_config.target,agents[0]);
  assert.match(repair.followup_config.message,/Amendment schema:/);assert(!repair.followup_config.message.includes(draft));
  assert.equal(repair.invocation_adapter.kind,'direct_mcp');assert.deepEqual(repair.invocation_adapter.arguments,{});
  const {runtime}=await f.service.open(),before=await runtime.runs.read(f.binding.run_id),beforeAttempt=before.state.nodes.worker.attempts[0];
  const originalRepair=structuredClone(beforeAttempt.native_pending_followup),repairRef=originalRepair.text_repair_ref;
  assert.equal(originalRepair.agent_id,agents[0]);assert.equal(originalRepair.rejection_count,1);
  // Do not advance native_next merely to inspect the budget: it can accept the
  // ready sibling before this ACK, invalidating the concurrency precondition.
  const sealedBaseline=await runtime.runs.readExecutorResult(f.binding.run_id,beforeAttempt.id,repairRef.sha256);
  assert.deepEqual(sealedBaseline.native_observation,{index:0,agent_id:agents[0],turn_id:threads.get(agents[0]).firstTurn});
  assert.equal(sealedBaseline.item_index,0);
  repairing=true;await fsPromises.appendFile(threads.get(agents[0]).thread.path,row('event_msg',{type:'task_started',turn_id:threads.get(agents[0]).repairTurn}));
  let ackSettled=false;
  const ack=f.service.call('native_followed_up',repair.invocation_adapter.arguments,MODEL_REQUEST).finally(()=>{ackSettled=true;});
  phase('repair-ack');
  const deadline=async(promise,label)=>{
    let timer;try{return await Promise.race([promise,
      new Promise((_resolve,reject)=>{timer=setTimeout(()=>reject(new Error('Timed out waiting for '+label)),10_000);})]);}
    finally{clearTimeout(timer);}
  };
  const boundary=(promise,label)=>deadline(Promise.race([promise,ack.then(()=>{throw new Error('Repair ACK settled before '+label);})]),label);
  const releaseRepair=async()=>{
    if(repairTerminal)return;repairTerminal=true;
    await fsPromises.appendFile(threads.get(agents[0]).thread.path,row('event_msg',{type:'task_complete',turn_id:threads.get(agents[0]).repairTurn}));
    repairReleased.resolve();
  };
  let failure,midpoint,next;
  try{
    await boundary(siblingChecked.promise,'ready sibling checker');
    phase('sibling-checked');
    await boundary(repairWaitArmed.promise,'remaining child event wait');
    phase('child-wait-armed');
    const middle=await runtime.runs.read(f.binding.run_id),attempt=middle.state.nodes.worker.attempts[0];
    assert.equal(ackSettled,false);assert.equal(repairTerminal,false);
    assert.equal(attempt.native_item_results?.[0],undefined);
    assert.deepEqual(attempt.native_item_results[1].result,{summary:'accepted b'});
    assert.equal(attempt.native_item_results[1].agent_id,agents[1]);
    assert.equal(attempt.native_item_results[1].turn_id,threads.get(agents[1]).firstTurn);
    assert.equal(middle.state.nodes.final.status,'pending');
    const readySibling=observations.find(entry=>entry.repairing&&entry.agent_id===agents[1]);
    assert.deepEqual(readySibling.agent_ids,agents);assert.equal(readySibling.waits_before,0);assert.equal(readySibling.waits_after,0);
    assert.deepEqual(readySibling.text_amendments,{[agents[0]]:true});
    midpoint={first_child_has_result:false,repair_terminal:false,sibling_result:attempt.native_item_results[1],ready_sibling_observation:readySibling};
    await releaseRepair();next=await deadline(ack,'repair ACK after terminal release');
    phase('repair-complete');
    assert.equal(next.status,'orchestration_handoff');
  }catch(error){failure=error;}
  finally{await releaseRepair();const [settled]=await Promise.allSettled([deadline(ack,'repair ACK cleanup')]);if(!failure&&settled.status==='rejected')failure=settled.reason;}
  if(failure)throw failure;
  const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
  phase('final-state-read');
  assert.deepEqual(state.nodes.worker.output.results,[{summary:fixed},{summary:'accepted b'}]);
  assert.deepEqual(f.calls.map(call=>[call.input.inputs.jobs[0].name,call.input.output.summary]),[['a',draft],['b','accepted b'],['a',fixed]]);
  assert.equal(attempt.native_rejected_turns[0].count,1);assert.equal(attempt.native_rejected_turns[1],undefined);
  assert.deepEqual(attempt.native_repair_followups['0:1'].text_repair_ref,repairRef);
  assert.equal(before.pins.root.workflow.nodes.find(node=>node.id==='worker').retry.max_attempts,3);
  const traces=Object.values(attempt.native_text_amendments);assert.equal(traces.length,1);
  const trace=traces[0];assert.equal(trace.agent_id,agents[0]);assert.equal(trace.turn_id,threads.get(agents[0]).repairTurn);
  assert.equal(trace.item_index,0);assert.deepEqual(trace.text_repair_ref,repairRef);
  const raw=await runtime.runs.readExecutorResult(f.binding.run_id,attempt.id,trace.raw_ref.sha256);
  const merged=await runtime.runs.readExecutorResult(f.binding.run_id,attempt.id,trace.merged_ref.sha256);
  assert.deepEqual(raw.payload,{amendments:[{field:'summary',start_line:1,end_line:1,replacement:'accepted a\r\n'}]});
  assert.deepEqual(merged.output,{summary:fixed});
  const slots=Object.values(attempt.worker_host_checks);
  assert.equal(slots.filter(slot=>slot.identity.native_observation.agent_id===agents[0]).length,2);
  assert.equal(slots.filter(slot=>slot.identity.native_observation.agent_id===agents[1]).length,1);
  assert.equal((await f.service.call('native_next',{},MODEL_REQUEST)).status,'orchestration_handoff');
  assert.equal(f.calls.length,3,'Replay must not rerender either accepted child');
  phase('replay-verified');
  const report={midpoint,observations,rpc,waits,amendment_trace:trace,checker_calls:f.calls.map(call=>({item:call.input.inputs.jobs[0].name,output:call.input.output})),
    repair_budget:{max_attempts:3,rejections:attempt.native_rejected_turns[0].count},final_status:next.status,replay_checker_calls:f.calls.length};
  console.log('NATIVE_REPAIR_SIBLING_BOUNDARY '+JSON.stringify(report));
  if(process.env.NATIVE_REPAIR_SIBLING_REPORT)await writeFile(process.env.NATIVE_REPAIR_SIBLING_REPORT,JSON.stringify(report,null,2)+'\n');
});

test('native text amendment refuses a full-result fallback and durably retains the failed raw amendment',async t=>{
  const f=await nativeCheckFixture(t,{single:true,textAmendment:true,accept:()=>false,
    observer:async(ids,turn)=>turn===1?{status:'completed',agent_id:ids[0],turn_id:'no-fallback-first',result:{summary:'draft'}}
      :{status:'amendment',agent_id:ids[0],turn_id:'no-fallback-edit',amendment:{summary:'unrequested whole replacement'}}});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  await assert.rejects(f.service.call('native_followed_up',{},MODEL_REQUEST),{code:'NATIVE_TEXT_AMENDMENT'});
  assert.equal(f.calls.length,1);
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.binding.run_id),attempt=record.state.nodes.worker.attempts[0];
  const trace=Object.values(attempt.native_text_amendments)[0];assert.equal(trace.error.code,'NATIVE_TEXT_AMENDMENT');assert.equal(trace.merged_ref,null);
  const raw=await runtime.runs.readExecutorResult(f.binding.run_id,attempt.id,trace.raw_ref.sha256);assert.equal(raw.payload.summary,'unrequested whole replacement');
  assert.equal(attempt.native_rejected_turns[0].count,1);
});

test('native text amendment rejects unsupported partition before starting a Run',async t=>{
  await assert.rejects(nativeCheckFixture(t,{textAmendment:true,partition:true}),error=>error.code==='WORKFLOW_NOT_READY'
    &&error.validation.errors.some(issue=>issue.code==='NATIVE_TEXT_AMENDMENT_MODE'));
});

test('native text amendment rejects an empty false-check scope before repair or acceptance',async t=>{
  const f=await nativeCheckFixture(t,{single:true,textAmendment:true,execute:async()=>({exit_code:0,output:{complete:false,diagnostic:'real rejection',repair_scope:{}},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  await assert.rejects(f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST),{code:'NATIVE_TEXT_AMENDMENT'});
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'failed');assert.equal(f.calls.length,1);
  assert.equal(state.nodes.worker.attempts[0].native_pending_followup,undefined);
});

function nativeCheckGraph(id,{single=false,max_attempts=3}={}){
  const workflow=definition(id,'ordinary'),worker=workflow.nodes.find(node=>node.id==='worker');
  workflow.inputs_schema=checkObject({jobs:{type:'array',minItems:1,maxItems:5,items:nativePageSchema},baseline:{type:'string'}});
  worker.executor.context_inheritance='upstream';worker.access='bounded_write';worker.path_scope=['pages'];worker.retry={max_attempts};
  worker.input_bindings={jobs:'/inputs/jobs'};worker.outputs_schema=single?nativeSemanticSchema:checkObject({results:{type:'array',items:nativeSemanticSchema}});
  worker.completion_contract={on_missing:'block',outcome:'validated_artifact',host_check:{tool:'native-check',success_field:'complete',correction_field:'diagnostic',input_bindings:{jobs:'/inputs/jobs',baseline:'/inputs/baseline'}}};
  if(!single){worker.subagent_count='auto';worker.fanout={input:'jobs',item_name:'page',distribution:'one_per_item',result_output:'results',scheduling:'parallel',join:'all_required',result_mode:'per_item',write_paths_field:'destinations',workspace_field:'workspace'};}
  workflow.nodes.find(node=>node.id==='final').input_bindings={};
  return workflow;
}
async function nativeCheckFixture(t,{single=false,accept=()=>true,execute,diagnostic='Correct this page.',max_attempts=3,observer,qualifiedResource=false,dependencyPath=false,requiredArtifacts=[],partition=false,sharedChange=false,inputCap=1024*1024,itemCount=2,maxConcurrency,contextInheritance='upstream',orchestration=false,textAmendment=false,incremental=false,resources={},finalSchema,finalBindings,transport,checkerDeadline=2000,nativeCheckerProgram}={}){
  const jobs=(single?['a']:Array.from({length:itemCount},(_,index)=>String.fromCharCode(97+index))).map(name=>({name,workspace:'pages/'+name,destinations:['pages/'+name]}));
  const contract={id:'native-check',identity:{name:'native-check-fixture',version:'1',sha256:digest('native-check-fixture')},argv:['render'],
    input_schema:checkObject({inputs:checkObject({jobs:{type:'array',minItems:1,maxItems:single?5:1,items:nativePageSchema},baseline:{type:'string'}}),output:nativeSemanticSchema}),
    output_schema:checkObject({complete:{type:'boolean'},diagnostic:{type:'string'}}),env_allow:[],permissions:{network:false,read_paths:['.'],write_paths:single?['pages']:['.']},input_cap_bytes:inputCap,output_cap_bytes:256*1024,deadline_ms:checkerDeadline,idempotency:{mode:'safe'}};
  const calls=[],turns=new Map(),seen=[];
  if(textAmendment)contract.output_schema.properties.repair_scope={type:'object',additionalProperties:false,properties:{summary:{type:'array',items:checkObject({start_line:{type:'integer',minimum:1},end_line:{type:'integer',minimum:1}})}}};
  if(textAmendment)contract.output_schema.required.push('repair_scope');
  if(qualifiedResource){contract.identity=workflowResourceProgramIdentity();contract.argv=['node','host/native-render.mjs','.host-render','@INPUT@'];contract.deadline_ms=10000;}
  const broker={identity:contract.identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:contract.identity,broker_id:'native-check',evidence_sha256:digest('native-check-qualified')},
    execute:async request=>{calls.push(request);if(execute)return execute(request,calls.length);
      const complete=accept(request,calls.length);await writeFile(join(request.context.workspace,single?'pages/rendered.txt':'rendered.txt'),request.input.output.summary);
      return {exit_code:0,output:{complete,diagnostic:complete?'':diagnostic,...(textAmendment?{repair_scope:complete?{}:{summary:[{start_line:1,end_line:1}]}}:{})},diagnostic:'',effects:{observed:true,changed_paths:[single?'pages/rendered.txt':'rendered.txt'],outside_paths:[],artifacts:[]}};},
    cancel:async()=>({termination_confirmed:true,evidence:[{kind:'terminated',sha256:digest('terminated')}],effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}})};
  const f=await fixture(t,async ids=>{seen.push([...ids]);const agent_id=ids[0],turn=(turns.get(agent_id)??0)+1;turns.set(agent_id,turn);
    if(observer)return observer(ids,turn,f);
    return {status:'completed',agent_id,turn_id:'native-turn-'+turn+'-'+agent_id.split('_').at(-1),result:single?{summary:'accepted '+turn}:{items:[{outcome:'completed',result:{summary:'accepted '+turn}}]}};
  },{hostToolRegistry:qualifiedResource?workflowResourceProgramRegistry():{'native-check':broker},hostToolRunner:new HostToolRunner({registry:qualifiedResource?workflowResourceProgramRegistry():{'native-check':broker},env:qualifiedResource?process.env:{}}),
    nativeMainSelection:async record=>{assert.equal(record.state.constraints.native_parent_thread_id,PARENT_THREAD_ID);return {model:'gpt-6-luna',effort:'max'};}},{...(qualifiedResource?process.env:{}),...(transport?{WORKFLOW_MCP_TRANSPORT:transport}:{})});
  await mkdir(join(f.workspace,'pages'));for(const job of jobs)await mkdir(join(f.workspace,job.workspace));
  const workflow=nativeCheckGraph('native-check-'+(single?'single':'fanout')+'-'+Math.random().toString(36).slice(2),{single,max_attempts});workflow.host_tools=[contract];
  if(textAmendment)workflow.nodes.find(node=>node.id==='worker').completion_contract.host_check.text_amendment={fields:['summary'],repair_scope_field:'repair_scope',max_edits:8,max_replacement_bytes:8192};
  if(orchestration)workflow.nodes.find(node=>node.id==='final').executor.mode='orchestration';
  if(finalSchema)workflow.nodes.find(node=>node.id==='final').outputs_schema=finalSchema;
  if(finalBindings)workflow.nodes.find(node=>node.id==='final').input_bindings=finalBindings;
  workflow.nodes.find(node=>node.id==='worker').executor.context_inheritance=contextInheritance;
  if(maxConcurrency!==undefined)workflow.nodes.find(node=>node.id==='worker').fanout.max_concurrency=maxConcurrency;
  if(sharedChange){
    workflow.nodes.find(node=>node.id==='worker').fanout.shared_change_field='summary';
    const integrator={id:'integrator',type:'agent',role:'implementer',executor:{kind:'provider',provider_id:'native-luna'},
      access:'bounded_write',path_scope:['pages'],approval:{required:false},retry:{max_attempts:3},
      input_bindings:{requests:{path:'/nodes/worker/output/results',pluck:'summary'}},prompt_template:'Apply delegated shared changes once.',
      outputs_schema:checkObject({complete:{type:'boolean'}}),completion_contract:{on_missing:'block',outcome:'validated_artifact',fail_on_false:['complete']}};
    workflow.nodes.splice(workflow.nodes.indexOf(workflow.nodes.find(node=>node.id==='final')),0,integrator);
    workflow.edges=[{id:'start-worker',source:'start',target:'worker'},{id:'worker-integrator',source:'worker',target:'integrator'},
      {id:'integrator-final',source:'integrator',target:'final'},{id:'final-end',source:'final',target:'end'}];
  }
  if(partition){const worker=workflow.nodes.find(node=>node.id==='worker');worker.subagent_count=1;worker.fanout.distribution='partition';}
  if(incremental){const worker=workflow.nodes.find(node=>node.id==='worker');worker.subagent_count='auto';worker.fanout.distribution='partition';worker.fanout.batch_size=itemCount;worker.fanout.item_delivery='incremental';}
  workflow.nodes.find(node=>node.id==='worker').required_artifacts=requiredArtifacts;
  let started;
  if(qualifiedResource){
    if(dependencyPath){
      workflow.requirements.executables=[{name:'node',version:'>=20.0.0'}];
      const final=workflow.nodes.find(node=>node.id==='final');final.access='bounded_write';final.path_scope=['pages'];
      final.input_bindings={results:'/nodes/worker/output/results'};
      final.completion_contract={on_missing:'block',outcome:'validated_artifact',host_check:{tool:'final-check',success_field:'complete',correction_field:'diagnostic'}};
      workflow.host_tools.push({...contract,id:'final-check',argv:['node','host/final-check.mjs','pages/.host-final','@INPUT@'],
        input_schema:checkObject({inputs:checkObject({results:{type:'array',items:nativeSemanticSchema}}),output:final.outputs_schema}),
        permissions:{network:false,read_paths:['.'],write_paths:['pages']}});
    }else workflow.nodes.find(node=>node.id==='worker').runtime_requirements={executables:['node']};
    const created=await f.service.call('create',{workflow,resources:{...resources,'host/native-render.mjs':nativeCheckerProgram??'import {readFileSync,writeFileSync} from "node:fs";const value=JSON.parse(readFileSync(process.argv[2],"utf8"));if(value.inputs.jobs.length!==1||value.inputs.baseline!=="Host-only exact baseline")throw new Error("routing");writeFileSync("rendered.txt",value.output.summary);console.log(JSON.stringify({complete:true,diagnostic:""}));',
      ...(dependencyPath?{'host/final-check.mjs':'import {readFileSync} from "node:fs";const value=JSON.parse(readFileSync(process.argv[2],"utf8"));if(value.inputs.results.length!==3||value.output.accepted!==true)throw new Error("final routing");console.log(JSON.stringify({complete:true,diagnostic:""}));'}:{})}},{human:true});
    const run=await f.service.call('start',{workflow_id:workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,access:'bounded_write',allowed_paths:['pages'],main_actor:'root',native_parent_thread_id:PARENT_THREAD_ID,inputs:{jobs,baseline:'Host-only exact baseline'}});
    const {runtime}=await f.service.open();await retainOwnedAuthority(runtime,run);started={run,binding:control(run)};
  }else started=await startRun(f,workflow,{jobs,baseline:'Host-only exact baseline'},resources);
  return {...f,...started,jobs,calls,seen,broker,workflow};
}

test('native dependency path uses real Node broker and non-speculative Main transactions',async t=>{
  const resources=Object.fromEntries(Array.from({length:71},(_,index)=>['neutral/r'+index+'.txt','Neutral dependency resource '+index]));
  const f=await nativeCheckFixture(t,{qualifiedResource:true,dependencyPath:true,itemCount:3,maxConcurrency:3,orchestration:true,resources});
  const home=await mkdtemp(join(tmpdir(),'dependency-pending-'));await mkdir(join(home,'sessions'));
  t.after(()=>rm(home,{recursive:true,maxRetries:3,retryDelay:100}));
  const threads=new Map(),rpc={};let terminal=false,wakes=0;
  const row=(type,payload)=>JSON.stringify({timestamp:'2026-10-09T08:00:00.000Z',type,payload})+'\n';
  f.service.nativeAgentObserver=async(ids,options)=>{
    for(const agentId of ids)if(!threads.has(agentId)){
      const id=randomUUID(),path=join(home,'sessions','rollout-'+id+'.jsonl'),spawn={parent_thread_id:PARENT_THREAD_ID,agent_path:agentId};
      const thread={id,path,parentThreadId:PARENT_THREAD_ID,source:{subAgent:{thread_spawn:spawn}}};threads.set(agentId,thread);
      await writeFile(path,row('session_meta',{id,parent_thread_id:PARENT_THREAD_ID,agent_path:agentId,source:{subagent:{thread_spawn:spawn}}})
        +row('event_msg',{type:'task_started',turn_id:'turn-'+id})+(terminal?row('event_msg',{type:'task_complete',turn_id:'turn-'+id}):''));
    }
    const client={async call(method,args){rpc[method]=(rpc[method]??0)+1;
      if(method==='thread/list')return {data:[...threads.values()]};
      const thread=[...threads.values()].find(item=>item.id===args.threadId);assert(thread);
      if(method==='thread/read')return {thread};
      assert.equal(method,'thread/turns/list');return {data:[{id:'turn-'+thread.id,status:terminal?'completed':'interrupted',itemsView:args.itemsView,
        items:terminal&&args.itemsView==='full'?[{type:'agentMessage',phase:'final_answer',text:JSON.stringify({outcome:'completed',result:{items:[{outcome:'completed',result:{summary:'accepted neutral pending'}}]}})}]:[]}]};
    }};
    return inspectNativeAgents(client,ids,{...options,lifecycleHome:home,waitForTerminal:true,waitForChange:async()=>{
      wakes++;if(wakes>3)terminal=true;
      for(const thread of threads.values())await fsPromises.appendFile(thread.path,row('event_msg',terminal
        ?{type:'task_complete',turn_id:'turn-'+thread.id}:{type:'token_count',info:{}}));
      return {event_type:'change',filename:'exact-neutral-child'};
    }});
  };
  const {runtime}=await f.service.open(),initial=await runtime.runs.read(f.run.run_id);
  assert.equal(initial.pins.resources.length,73);assert.deepEqual(initial.state.constraints.runtime_requirements,{executables:[{name:'node',version:'>=20.0.0'}]});
  assert.equal(initial.pins.executable_projection_version,1);
  const reports=[],phases={},original=WorkflowRunStore.prototype.withHostTransaction;let speculative=0;
  WorkflowRunStore.prototype.withHostTransaction=async function(id,phase,action){
    const result=await Reflect.apply(original,this,[id,phase,action]);if(phase==='main_dispatch'&&(result===null||result===true))speculative++;return result;
  };
  try{
    const observe=async(name,action)=>{const value=await withRunStoreObservation(action,report=>{reports.push({name,...report});phases[name]=report;});return value;};
    const handoff=await observe('startup',()=>f.service.call('native_next',{},MODEL_REQUEST));assert.equal(handoff.status,'native_handoff');
    const next=await observe('ack',()=>f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST));assert.equal(next.status,'orchestration_handoff');
    const final=await observe('final',()=>f.service.call('orchestration_complete',{output:{accepted:true}},MODEL_REQUEST));assert.equal(final.status,'succeeded');
    const outputs=[];for(const job of f.jobs){const path=job.workspace+'/rendered.txt',content=await readFile(join(f.workspace,path),'utf8');assert.match(content,/^accepted/);outputs.push({path,content,sha256:digest(Buffer.from(content))});}
    const current=await runtime.runs.read(f.run.run_id);
    const measured={speculative,rpc,wakes,reports,qualification:{requirements:initial.state.constraints.runtime_requirements,
      resource_pins:initial.pins.resources,runtime_environment:initial.state.constraints.runtime_environment??initial.state.runtime_environment,
      outputs,final_status:current.state.status,semantic_output:current.state.output}};
    console.log('NATIVE_DEPENDENCY_BOUNDARY '+JSON.stringify(measured));
    if(process.env.NATIVE_DEPENDENCY_REPORT)await writeFile(process.env.NATIVE_DEPENDENCY_REPORT,JSON.stringify(measured,null,2)+'\n');
    assert.equal(wakes,4);assert(rpc['thread/read']<=6,'Token count progress must not trigger SDK whole-group sweeps');
    assert.equal(speculative,0,'Executable requirements must not open full-audit Main transactions merely to abandon them');
  }finally{WorkflowRunStore.prototype.withHostTransaction=original;}
});

test('terminal Main semantic inputs carry complete declared 13KB input without private metadata',async t=>{
  const content='Neutral semantic line 🌱\r\n'.repeat(500);
  const f=await nativeCheckFixture(t,{single:true,orchestration:true,finalBindings:{proposal:'/nodes/worker/output'},
    observer:async ids=>({status:'completed',agent_id:ids[0],turn_id:'neutral-large-terminal',result:{summary:content}})});
  const start=await f.service.call('native_next',{},MODEL_REQUEST);
  const handoff=await f.service.call('native_spawned_batch',{batch_id:start.batch_id},MODEL_REQUEST);
  assert.equal(handoff.status,'orchestration_handoff');
  assert.deepEqual(handoff.semantic_inputs.proposal.content,{summary:content});
  assert.equal(handoff.semantic_inputs.proposal.format,'json');
  const task=handoff.task_bundle.task,inputs=JSON.parse(task.split('\nInputs:\n')[1].split('\n')[0]);
  assert.deepEqual(inputs.proposal,{delivery:'inline',value_path:['semantic_inputs','proposal','content'],format:'json'});
  assert(!task.includes('Read this bound input'));assert(!task.includes(content));
  assert.equal(JSON.stringify(handoff).split(JSON.stringify(handoff.semantic_inputs.proposal.content).slice(1,-1)).length-1,1);
  assert.doesNotMatch(JSON.stringify(handoff.semantic_inputs),/context_preparation|lease_token|control_token|receipt|host_check|sha256/);
  const repeated=await f.service.call('native_next',{},MODEL_REQUEST);assert.deepEqual(repeated.semantic_inputs,handoff.semantic_inputs);
});

test('native semantic child packets omit Host mechanical checker metadata and retain the exact result schema',async t=>{
  const f=await nativeCheckFixture(t);
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  for(const packet of publicPackets(handoff)){
    assert.doesNotMatch(packet.prompt,/host_check|native-check|success_field|correction_field|input_bindings|Host-only exact baseline/);
    const delivered=await publicNativeTask(packet.prompt);
    assert.doesNotMatch(JSON.stringify(delivered),/host_check|native-check|success_field|correction_field|input_bindings|Host-only exact baseline/);
    assert.deepEqual(delivered.result_schema.properties.items.items.properties.result,nativeSemanticSchema);
  }
  await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(f.calls.length,2,'Omitting prompt metadata must retain every Host checker dispatch');
  assert(f.calls.every(call=>call.input.inputs.baseline==='Host-only exact baseline'));
});

test('native accepted model batch returns the next current-Main handoff in the same call',async t=>{
  for(const options of [{single:true},{itemCount:3,maxConcurrency:3}])await t.test(options.single?'single':'capped fanout',async t=>{
    const f=await nativeCheckFixture(t,{...options,orchestration:true});
    const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
    const next=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
    assert.equal(next.status,'orchestration_handoff');
    assert.equal(next.completion_tool,'workflow_orchestration_complete');
    assert.equal(next.context,'current_conversation');
    assert.equal(next.next_action,undefined);
    const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
    assert.equal(state.nodes.worker.status,'succeeded');
    assert.equal(state.nodes.final.attempts[0].dispatch.receipt.executor,'codex-current-main-orchestration');
    assert.equal(state.nodes.final.attempts[0].dispatch.receipt.thread_id,PARENT_THREAD_ID);
    assert.equal(f.calls.length,options.single?1:3);
    assert.equal(attempt.dispatch.receipt.agent_ids.length,options.single?1:3);
    assert.equal((await f.service.call('native_next',{},MODEL_REQUEST)).status,'orchestration_handoff');
    assert.equal(f.calls.length,options.single?1:3,'Recovery must not rerender accepted children');
  });
});

test('native checker correction ACK returns current-Main only after exact same-child acceptance',async t=>{
  const f=await nativeCheckFixture(t,{single:true,orchestration:true,accept:(_request,count)=>count>1});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(repair.next_action,'repair_recorded_agent');
  assert.equal((await f.service.call('get',f.binding)).nodes.final.status,'pending');
  const next=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal(next.status,'orchestration_handoff');
  assert.equal(f.calls.length,2);
  assert.deepEqual(f.seen[0],f.seen[1]);
  const state=await f.service.call('get',f.binding),slots=Object.values(state.nodes.worker.attempts[0].worker_host_checks);
  assert.equal(slots.length,2);
  assert.notEqual(slots[0].identity.native_observation.turn_id,slots[1].identity.native_observation.turn_id);
});

test('native model repair sends one diagnostic delta while retaining canonical task and exact recovery intent',async t=>{
  const diagnostic='EXACT_RENDER_DIAGNOSTIC: revise the decisive statement.';
  const f=await nativeCheckFixture(t,{single:true,orchestration:true,diagnostic,accept:(_request,count)=>count>1});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),originalTask=inlineNativeTask(publicPackets(handoff)[0].prompt).task;
  const repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(repair.followup_config.message.split(diagnostic).length-1,1);
  assert.doesNotMatch(repair.followup_config.message,/Complete the assigned task|Workspace:|"task":|"jobs":|"result_schema":/);
  assert.match(repair.followup_config.message,/Result schema from the initial packet/);
  for(const field of ['repair_prompt','reason','repair_remaining','run_id','attempt_id','index','agent_id','turn_id','accepted_item_indices','unresolved_item_indices'])
    assert.equal(Object.hasOwn(repair,field),false,field);
  assert.equal(repair.invocation_adapter.tool_name,'workflow_native_followed_up');
  const {runtime}=await f.service.open(),record=await runtime.runs.read(f.run.run_id),attempt=record.state.nodes.worker.attempts[0];
  const pending=attempt.native_pending_followup;
  assert.equal(pending.agent_id,repair.followup_config.target);
  assert.equal(pending.followup_kind,'repair');
  assert.equal(pending.rejection_count,1);
  const privateRepair=await f.service.call('native_next',f.binding);
  assert.equal(privateRepair.repair_prompt,repair.followup_config.message);
  assert.equal(privateRepair.repair_remaining,2);
  assert.equal((await f.service.call('native_next',{},MODEL_REQUEST)).followup_config.message,repair.followup_config.message);
  const bundleRoot=join(f.workspace,'work','.workflow-runtime','native-agent',f.run.run_id,attempt.id,'partition-0');
  const original=JSON.parse(await readFile(join(bundleRoot,'task.json'),'utf8'));
  assert.equal(original.task,originalTask);
  const next=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal(next.status,'orchestration_handoff');
  assert.equal(f.calls.length,2);
});

test('native capped checker batch ACK accepts all three recorded children before final receipt sealing',async t=>{
  const f=await nativeCheckFixture(t,{itemCount:3,maxConcurrency:3});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  assert.equal(publicPackets(handoff).length,3);
  const before=await f.service.call('get',f.binding);
  assert.equal(before.nodes.worker.attempts[0].dispatch.receipt,null);
  await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
  assert.equal(state.nodes.worker.status,'succeeded');
  assert.deepEqual(f.calls.map(call=>call.input.inputs.jobs[0].name),['a','b','c']);
  assert.deepEqual(f.calls.map(call=>call.context.workspace),f.jobs.map(job=>join(f.workspace,job.workspace)));
  assert.deepEqual(attempt.dispatch.receipt.agent_ids,Object.values(attempt.native_agents));
  assert.equal(Object.keys(attempt.native_parallel_results).length,3);
  assert.equal(Object.keys(attempt.native_item_results).length,3);
  const traces=attempt.executor_events.filter(event=>event.kind==='session_state'&&event.metadata.status==='native_render_preflight');
  assert.equal(traces.length,3);
  for(const [index,item]of Object.entries(attempt.native_item_results)){
    const slot=attempt.worker_host_checks[item.host_check.slot_id];
    assert.equal(slot.identity.native_observation.index,Number(index));
    assert.equal(slot.identity.native_observation.agent_id,attempt.native_agents[index]);
    assert.equal(slot.identity.native_observation.turn_id,item.turn_id);
    assert(traces.some(event=>event.metadata.diagnostic.includes(`slot ${index}, Agent ${item.agent_id}, observed turn ${item.turn_id}`)
      &&event.metadata.diagnostic.endsWith('not yet sealed')));
  }
  assert(state.cost_ledger.calls.every(call=>call.usage.unknown===true));
});

test('native capped checker refills two-child window and retains accepted siblings without invented future identities',async t=>{
  const f=await nativeCheckFixture(t,{itemCount:3,maxConcurrency:2});
  const first=await f.service.call('native_next',{},MODEL_REQUEST);assert.equal(publicPackets(first).length,2);
  const next=await f.service.call('native_spawned_batch',{batch_id:first.batch_id},MODEL_REQUEST);
  assert.equal(next.status,'native_handoff');assert.deepEqual(publicPackets(next).map(packet=>packet.index),[2]);
  const middle=await f.service.call('get',f.binding),pending=middle.nodes.worker.attempts[0];
  assert.equal(pending.dispatch.receipt,null);
  assert.deepEqual(Object.keys(pending.native_agents),['0','1']);
  assert.deepEqual(Object.keys(pending.native_item_results),['0','1']);
  const accepted=structuredClone(pending.native_item_results);
  assert.equal(Object.values(pending.worker_host_checks).filter(slot=>slot.receipt?.status==='succeeded').length,2);
  await f.service.call('native_spawned_batch',{batch_id:next.batch_id},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
  assert.equal(state.nodes.worker.status,'succeeded');
  for(const index of [0,1])assert.deepEqual(attempt.native_item_results[index],accepted[index]);
  assert.deepEqual(f.calls.map(call=>call.input.inputs.jobs[0].name),['a','b','c']);
  assert.deepEqual(attempt.dispatch.receipt.agent_ids,Object.values(attempt.native_agents));
  assert.equal(new Set(f.seen.flat()).size,3);
});

test('native capped checker rejects wrong observed slot or child before effects',async t=>{
  const f=await nativeCheckFixture(t,{itemCount:3,maxConcurrency:3});
  const c=await nativeCheckContext(f);
  const invoke=async(index,agent_id)=>f.service.recordObservedNativeItems(c.runtime,f.binding,{definition:c.definition,
    attempt:c.attempt,binding:c.binding,index,observed:{status:'completed',agent_id,turn_id:'exact-negative-turn',
      result:{items:[{outcome:'completed',result:{summary:'neutral proposal'}}]}},executor:c.executor});
  await assert.rejects(invoke(1,c.native_observation.agent_id),{code:'NATIVE_HOST_CHECK_IDENTITY'});
  await assert.rejects(invoke(0,'foreign-child'),{code:'NATIVE_HOST_CHECK_IDENTITY'});
  assert.equal(f.calls.length,0);
  const state=await f.service.call('get',f.binding),attempt=state.nodes.worker.attempts[0];
  assert.equal(attempt.dispatch.receipt,null);assert.equal(attempt.native_item_results,undefined);
});

test('native Host checker gates acceptance and repairs the same inherited child with full diagnostics',async t=>{
  for(const single of [false,true])await t.test(single?'single':'per item',async t=>{
    const decisive='x'.repeat(5000)+' decisive issue at the end';
    const f=await nativeCheckFixture(t,{single,diagnostic:decisive,accept:(_request,count)=>count>1});
    const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
    assert.equal(publicPackets(handoff)[0].spawn_config.fork_turns,'all');assert.equal(publicPackets(handoff)[0].spawn_config.model,undefined);
    assert.doesNotMatch(publicPackets(handoff)[0].prompt,/Host-only exact baseline/);
    const repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
    assert.equal(repair.followup_config.target,f.seen[0][0]);assert(repair.followup_config.message.includes(decisive));
    let state=await f.service.call('get',f.binding),before=state.nodes.worker.attempts[0];
    assert.deepEqual(Object.keys(before.native_item_results??{}),single?[]:['1']);
    const acceptedSibling=structuredClone(before.native_item_results?.[1]);
    if(!single){
      assert.equal(acceptedSibling.agent_id,before.native_agents[1]);
      assert.equal(before.worker_host_checks[acceptedSibling.host_check.slot_id].receipt.status,'succeeded');
    }
    const resumed=await f.service.call('native_followed_up',{},MODEL_REQUEST);
    state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');
    const slots=Object.values(state.nodes.worker.attempts[0].worker_host_checks).filter(slot=>slot.identity.native_observation.agent_id===f.seen[0][0]);assert.equal(slots.length,2);
    assert.notEqual(slots[0].identity.native_observation.turn_id,slots[1].identity.native_observation.turn_id);
    assert.equal(f.calls[0].input.inputs.baseline,'Host-only exact baseline');
    if(!single){
      assert.equal(f.calls[0].context.workspace,join(f.workspace,'pages/a'));assert.deepEqual(f.calls[0].permissions.write_paths,['.']);
      assert.deepEqual(state.nodes.worker.attempts[0].native_item_results[1],acceptedSibling);
      assert.equal(f.calls.filter(call=>call.input.inputs.jobs[0].name==='b').length,1);
    }
    assert(resumed);
  });
});

async function nativeCheckContext(f){
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),agent_id='/root/'+publicPackets(handoff)[0].spawn_config.task_name;
  const attempt_id=(await f.service.call('get',f.binding)).nodes.worker.active_attempt_id;
  await recordNativeSpawn(f,{...f.binding,attempt_id,index:0,agent_id});
  const context=await nativeAttemptContext(f,{...f.binding,attempt_id});
  const native_observation={index:0,agent_id,turn_id:'exact-neutral-terminal-turn'},output={summary:'neutral semantic proposal'};
  await context.runtime.recordNativeHostCheckProposal(f.run.run_id,{...context.binding,native_observation,item_index:0,output});
  return {...context,native_observation,output,handoff};
}

test('native item preflight and successful assignment each share one exact Run writer',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f),{runtime,executor}=await f.service.open();
 const spans=[],stack=[],transaction=WorkflowRunStore.prototype.withHostTransaction,mutate=WorkflowRunStore.prototype.mutateNativeJournal,events=WorkflowRunStore.prototype.mutateExecutorJournal,open=fsPromises.open;
 WorkflowRunStore.prototype.withHostTransaction=async function(id,phase,action){
   if(id!==f.run.run_id)return Reflect.apply(transaction,this,[id,phase,action]);
   const row={phase,kinds:[],opened:[]};stack.push(row);try{return await Reflect.apply(transaction,this,[id,phase,action]);}finally{stack.pop();spans.push(row);}
 };
 WorkflowRunStore.prototype.mutateNativeJournal=async function(id,kind,...args){if(id===f.run.run_id&&stack.length)stack.at(-1).kinds.push(kind);return Reflect.apply(mutate,this,[id,kind,...args]);};
 WorkflowRunStore.prototype.mutateExecutorJournal=async function(id,...args){if(id===f.run.run_id&&stack.length)stack.at(-1).kinds.push('executor_event');return Reflect.apply(events,this,[id,...args]);};
 fsPromises.open=async(path,flags,...args)=>{if(stack.length&&flags==='wx'&&String(path).endsWith('.writer.lock'))stack.at(-1).opened.push(String(path));return open(path,flags,...args);};syncBuiltinESMExports();
 try{
   const result=await f.service.recordObservedNativeItems(runtime,f.binding,{definition:c.definition,attempt:c.attempt,binding:c.binding,index:0,executor,
     observed:{status:'completed',agent_id:c.native_observation.agent_id,turn_id:c.native_observation.turn_id,result:{items:[{outcome:'completed',result:c.output}]}}});
   assert.deepEqual(result.result,[c.output]);
 }finally{WorkflowRunStore.prototype.withHostTransaction=transaction;WorkflowRunStore.prototype.mutateNativeJournal=mutate;WorkflowRunStore.prototype.mutateExecutorJournal=events;fsPromises.open=open;syncBuiltinESMExports();}
 for(const kind of ['executor_event','native_item_results']){
   const matches=spans.filter(s=>s.kinds.includes(kind));assert.equal(matches.length,1,kind+' transaction count');
   for(const path of [join(runtime.runs.runLockDirectory(f.run.run_id),'.writer.lock'),join(runtime.runs.directory(f.run.run_id),'.writer.lock')])assert.equal(matches[0].opened.filter(p=>p===path).length,1);
   if(kind==='native_item_results')assert.deepEqual(matches[0].kinds,['native_item_results','native_parallel_result']);
 }
 const attempt=(await runtime.runs.read(f.run.run_id)).state.nodes.worker.attempts[0];
 assert.deepEqual(attempt.native_item_results[0].result,c.output);assert.deepEqual(attempt.native_parallel_results[0].result,[c.output]);assert.equal(f.calls.length,1);
});

test('native assignment append failure preserves accepted item evidence and stays visible',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f),{runtime,executor}=await f.service.open();
 const mutation=runtime.runs.mutateNativeJournal.bind(runtime.runs),failure=Object.assign(new Error('injected assignment append failure'),{code:'TEST_ASSIGNMENT_APPEND'});
 runtime.runs.mutateNativeJournal=async(id,kind,...args)=>{if(kind==='native_parallel_result')throw failure;return mutation(id,kind,...args);};
 await assert.rejects(f.service.recordObservedNativeItems(runtime,f.binding,{definition:c.definition,attempt:c.attempt,binding:c.binding,index:0,executor,
   observed:{status:'completed',agent_id:c.native_observation.agent_id,turn_id:c.native_observation.turn_id,result:{items:[{outcome:'completed',result:c.output}]}}}),error=>error===failure);
 const attempt=(await runtime.runs.read(f.run.run_id)).state.nodes.worker.attempts[0];
 assert.deepEqual(attempt.native_item_results[0].result,c.output);assert.equal(attempt.native_parallel_results?.[0],undefined);
 assert.equal(Object.values(attempt.worker_host_checks)[0].receipt.status,'succeeded');assert.equal(f.calls.length,1);
 assert.equal(attempt.native_rejected_turns?.[0],undefined,'Persistence failure became a model correction');
});

test('native raw and merged amendment artifacts share one publication writer',async t=>{
 const f=await nativeCheckFixture(t,{single:true,textAmendment:true,accept:(_r,count)=>count>1,
   observer:async(ids,turn)=>turn===1?{status:'completed',agent_id:ids[0],turn_id:'artifact-first',result:{summary:'old\nunchanged'}}
    :{status:'amendment',agent_id:ids[0],turn_id:'artifact-repair',amendment:{amendments:[{field:'summary',start_line:1,end_line:1,replacement:'new\n'}]}}});
 const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
 await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
 const {runtime}=await f.service.open(),spans=[],stack=[],transaction=WorkflowRunStore.prototype.withHostTransaction,save=WorkflowRunStore.prototype.saveExecutorResult,open=fsPromises.open;
 WorkflowRunStore.prototype.withHostTransaction=async function(id,phase,action){
   if(id!==f.run.run_id)return Reflect.apply(transaction,this,[id,phase,action]);
   const row={kinds:[],opened:[]};stack.push(row);try{return await Reflect.apply(transaction,this,[id,phase,action]);}finally{stack.pop();spans.push(row);}
 };
 WorkflowRunStore.prototype.saveExecutorResult=async function(id,attempt,value){if(id===f.run.run_id&&stack.length)stack.at(-1).kinds.push(value.kind);return Reflect.apply(save,this,[id,attempt,value]);};
 fsPromises.open=async(path,flags,...args)=>{if(stack.length&&flags==='wx'&&String(path).endsWith('.writer.lock'))stack.at(-1).opened.push(String(path));return open(path,flags,...args);};syncBuiltinESMExports();
 try{await f.service.call('native_followed_up',{},MODEL_REQUEST);}
 finally{WorkflowRunStore.prototype.withHostTransaction=transaction;WorkflowRunStore.prototype.saveExecutorResult=save;fsPromises.open=open;syncBuiltinESMExports();}
 const rows=spans.filter(s=>s.kinds.includes('native_text_amendment'));assert.equal(rows.length,1);
 assert.deepEqual(rows[0].kinds,['native_text_amendment','native_text_merged_proposal']);
 for(const path of [join(runtime.runs.runLockDirectory(f.run.run_id),'.writer.lock'),join(runtime.runs.directory(f.run.run_id),'.writer.lock')])assert.equal(rows[0].opened.filter(p=>p===path).length,1);
 assert.equal(f.calls.length,2);assert.equal(f.calls[1].input.output.summary,'new\nunchanged');
 const attempt=(await runtime.runs.read(f.run.run_id)).state.nodes.worker.attempts[0];assert.equal(Object.keys(attempt.native_text_amendments).length,1);
});

test('native checker input and intent share one fresh exact Run writer',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
 const record=(await c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding)).record;
 const context=workerHostCheckContext(record,c.binding,{output:c.output,item_index:0,native_observation:c.native_observation});
 const opened=[],original=fsPromises.open;
 fsPromises.open=async(path,flags,...args)=>{if(flags==='wx'&&String(path).endsWith('.writer.lock'))opened.push(String(path));return original(path,flags,...args);};syncBuiltinESMExports();
 try{
  const result=await c.runtime.recordNativeWorkerHostCheckIntent(f.run.run_id,{...c.binding,identity:context.identity,input:context.input},record);
  assert.equal(result.created,true);
 }finally{fsPromises.open=original;syncBuiltinESMExports();}
 for(const path of [join(c.runtime.runs.runLockDirectory(f.run.run_id),'.writer.lock'),join(c.runtime.runs.directory(f.run.run_id),'.writer.lock')])assert.equal(opened.filter(p=>p===path).length,1,'Input and intent reopened the exact Run writer: '+path);
 assert.equal(f.calls.length,0,'Persistence preparation invoked the checker');
});

test('native intent rejects a newer controller before publishing its input artifact',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
 const record=(await c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding)).record;
 const context=workerHostCheckContext(record,c.binding,{output:c.output,item_index:0,native_observation:c.native_observation});
 await c.runtime.runs.mutate(f.run.run_id,'control_recovery',state=>{state.control_hash=digest('replacement-controller');});
 const save=c.runtime.runs.saveExecutorResult.bind(c.runtime.runs);let publications=0;
 c.runtime.runs.saveExecutorResult=async(...args)=>{publications++;return save(...args);};
 await assert.rejects(c.runtime.recordNativeWorkerHostCheckIntent(f.run.run_id,{...c.binding,identity:context.identity,input:context.input},record),{code:'RUN_AUTHORITY'});
 assert.equal(publications,0);assert.equal(f.calls.length,0);
});

test('native intent rejects a fenced lease before publishing its input artifact',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
 const record=(await c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding)).record;
 const context=workerHostCheckContext(record,c.binding,{output:c.output,item_index:0,native_observation:c.native_observation});
 await c.runtime.runs.mutate(f.run.run_id,'control_recovery',state=>{state.nodes.worker.attempts[0].lease_hash=digest('replacement-lease');});
 const save=c.runtime.runs.saveExecutorResult.bind(c.runtime.runs);let publications=0;
 c.runtime.runs.saveExecutorResult=async(...args)=>{publications++;return save(...args);};
 await assert.rejects(c.runtime.recordNativeWorkerHostCheckIntent(f.run.run_id,{...c.binding,identity:context.identity,input:context.input},record),{code:'LEASE_INVALID'});
 assert.equal(publications,0);assert.equal(f.calls.length,0);
});

test('native intent append failure retains its input and retries without checker effects',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f);
 const record=(await c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding)).record;
 const context=workerHostCheckContext(record,c.binding,{output:c.output,item_index:0,native_observation:c.native_observation});
 const args={...c.binding,identity:context.identity,input:context.input};
 const failure=new Error('injected intent append failure'),open=fsPromises.open;
 const save=c.runtime.runs.saveExecutorResult.bind(c.runtime.runs),refs=[];
 c.runtime.runs.saveExecutorResult=async(...args)=>{const ref=await save(...args);refs.push(ref);return ref;};
 fsPromises.open=async(path,flags,...rest)=>{if(flags==='a'&&String(path).endsWith('events.jsonl'))throw failure;return open(path,flags,...rest);};syncBuiltinESMExports();
 try{
  await assert.rejects(c.runtime.recordNativeWorkerHostCheckIntent(f.run.run_id,args,record),error=>error===failure);
  assert.equal(refs.length,1);assert.equal((await c.runtime.runs.readExecutorResult(f.run.run_id,c.binding.attempt_id,refs[0].sha256)).kind,'worker_host_check_input');
 }finally{fsPromises.open=open;syncBuiltinESMExports();}
 const accepted=await c.runtime.recordNativeWorkerHostCheckIntent(f.run.run_id,args,record);
 assert.equal(refs.length,2);assert.deepEqual(refs[1],refs[0]);
 assert.equal(accepted.created,true);assert.deepEqual(accepted.slot.input_ref,refs[0]);
 assert.equal((await c.runtime.recordNativeWorkerHostCheckIntent(f.run.run_id,args,record)).created,false);
 assert.equal(f.calls.length,0);
});

test('native checker output and receipt share one writer after snapshot preparation',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f),manager={hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})};
 const spans=[],transaction=c.runtime.runs.withHostTransaction.bind(c.runtime.runs),save=c.runtime.runs.saveExecutorResult.bind(c.runtime.runs),open=fsPromises.open;let active=null;
 c.runtime.runs.withHostTransaction=async(id,phase,action)=>{const row={phase,opened:[],kind:null};active=row;try{return await transaction(id,phase,action);}finally{active=null;spans.push(row);}};
 c.runtime.runs.saveExecutorResult=async(id,attempt,value)=>{if(active)active.kind=value.kind;return save(id,attempt,value);};
 fsPromises.open=async(path,flags,...args)=>{if(active&&flags==='wx'&&String(path).endsWith('.writer.lock'))active.opened.push(String(path));return open(path,flags,...args);};syncBuiltinESMExports();
 try{
  const result=await executeWorkerHostCheck(manager,{runtime:c.runtime,runId:f.run.run_id},c.binding,c.output,{item_index:0,native_observation:c.native_observation,authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}});
  assert.equal(result.accepted,true);
 }finally{fsPromises.open=open;syncBuiltinESMExports();}
 const outputSpans=spans.filter(s=>s.kind==='worker_host_check_output');assert.equal(outputSpans.length,1,'Output and receipt did not share their publication transaction');
 for(const path of [join(c.runtime.runs.runLockDirectory(f.run.run_id),'.writer.lock'),join(c.runtime.runs.directory(f.run.run_id),'.writer.lock')])assert.equal(outputSpans[0].opened.filter(p=>p===path).length,1);
 assert.equal(f.calls.length,1);
});

test('native checker receipt append failure keeps its uncertain intent without replaying effects',async t=>{
 const f=await nativeCheckFixture(t),c=await nativeCheckContext(f),manager={hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})};
 const options={item_index:0,native_observation:c.native_observation,authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}},entry={runtime:c.runtime,runId:f.run.run_id};
 const receipt=c.runtime.recordNativeWorkerHostCheckReceipt.bind(c.runtime),failure=new Error('injected receipt append failure');
 c.runtime.recordNativeWorkerHostCheckReceipt=async()=>{throw failure;};
 await assert.rejects(executeWorkerHostCheck(manager,entry,c.binding,c.output,options),error=>error===failure);
 c.runtime.recordNativeWorkerHostCheckReceipt=receipt;
 const state=(await c.runtime.runs.read(f.run.run_id)).state,slot=Object.values(state.nodes.worker.attempts[0].worker_host_checks)[0];assert.equal(slot.phase,'intent');assert.equal(slot.receipt,null);
 await assert.rejects(executeWorkerHostCheck(manager,entry,c.binding,c.output,options),{code:'HOST_TOOL_RECONCILIATION_REQUIRED'});
 assert.equal(f.calls.length,1);
});

test('native Host checker atomically admits concurrent exact child-turn collectors once',async t=>{
  const f=await nativeCheckFixture(t),c=await nativeCheckContext(f),ready=deferred();let arrivals=0;
  const original=c.runtime.recordNativeWorkerHostCheckIntent.bind(c.runtime);
  c.runtime.recordNativeWorkerHostCheckIntent=async(...args)=>{if(++arrivals===2)ready.resolve();await ready.promise;return original(...args);};
  const manager={hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})},options={item_index:0,native_observation:c.native_observation,
    authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}};
  const results=await Promise.allSettled([0,1].map(()=>executeWorkerHostCheck(manager,{runtime:c.runtime,runId:f.run.run_id},c.binding,c.output,options)));
  assert.equal(f.calls.length,1);assert.equal(results.filter(result=>result.status==='fulfilled').length,1);
  assert.equal(results.find(result=>result.status==='rejected').reason.code,'HOST_TOOL_RECONCILIATION_REQUIRED');
});

test('native Host checker receipt replay rejects semantic, receipt and declared product tampering',async t=>{
  const f=await nativeCheckFixture(t,{requiredArtifacts:[{path:'pages/a/rendered.txt',requirement_id:'a-render'}]}),c=await nativeCheckContext(f),manager={hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})};
  const entry={runtime:c.runtime,runId:f.run.run_id},options={item_index:0,native_observation:c.native_observation,authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}};
  const first=await executeWorkerHostCheck(manager,entry,c.binding,c.output,options);assert(first.accepted);
  const replay=await executeWorkerHostCheck(manager,entry,c.binding,c.output,options);assert.deepEqual(replay.reference,first.reference);assert.equal(f.calls.length,1);
  await assert.rejects(executeWorkerHostCheck(manager,entry,c.binding,{summary:'tampered semantic'},options),{code:'NATIVE_HOST_CHECK_PROPOSAL'});
  await writeFile(join(f.workspace,'pages/a/rendered.txt'),'changed after check');
  await assert.rejects(executeWorkerHostCheck(manager,entry,c.binding,c.output,options),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
  await writeFile(join(f.workspace,'pages/a/rendered.txt'),c.output.summary);
  const record=await c.runtime.runs.read(f.run.run_id),slot=record.state.nodes.worker.attempts[0].worker_host_checks[first.reference.slot_id];
  await writeFile(join(c.runtime.runs.directory(f.run.run_id),slot.receipt.output_ref.artifact),'tampered artifact');
  await assert.rejects(executeWorkerHostCheck(manager,entry,c.binding,c.output,options));assert.equal(f.calls.length,1);
});

test('native Host checker replay ignores bookkeeping and snapshots only declared products',async t=>{
  for(const declared of [false,true]){
    const f=await nativeCheckFixture(t,{requiredArtifacts:declared?[{path:'pages/a/rendered.txt',requirement_id:'a-render'}]:[]}),c=await nativeCheckContext(f);
    const manager={hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}})},entry={runtime:c.runtime,runId:f.run.run_id};
    const options={item_index:0,native_observation:c.native_observation,authorize:()=>c.runtime.authorizedExecution(f.run.run_id,c.binding,()=>c.binding),assertActive:()=>{}};
    const first=await executeWorkerHostCheck(manager,entry,c.binding,c.output,options);
    await writeFile(join(f.workspace,'pages/a/runtime-state.json'),JSON.stringify({closed:true}));
    const replay=await executeWorkerHostCheck(manager,entry,c.binding,c.output,options);
    assert.deepEqual(replay.reference,first.reference);assert.equal(f.calls.length,1);
    const record=await c.runtime.runs.read(f.run.run_id),slot=record.state.nodes.worker.attempts[0].worker_host_checks[first.reference.slot_id];
    const stored=await c.runtime.runs.readExecutorResult(f.run.run_id,c.binding.attempt_id,slot.receipt.output_ref.sha256);
    if(declared){
      const snapshot=JSON.parse((await c.runtime.runs.readArtifact(f.run.run_id,stored.completion_snapshot)).toString('utf8'));
      assert.equal(snapshot.coverage,'declared_products');assert.deepEqual(snapshot.entries.map(item=>item.path),['rendered.txt']);
    }else assert.equal(stored.completion_snapshot,undefined);
  }
});

test('native rejected render can repair before a declared product exists',async t=>{
  const f=await nativeCheckFixture(t,{single:true,requiredArtifacts:[{path:'pages/rendered.txt',requirement_id:'render'}],execute:async(request,count)=>{
    if(count===2)await writeFile(join(request.context.workspace,'pages/rendered.txt'),request.input.output.summary);
    return {exit_code:0,output:{complete:count===2,diagnostic:count===1?'Correct this component.':''},diagnostic:'',
      effects:{observed:true,changed_paths:count===2?['pages/rendered.txt']:[],outside_paths:[],artifacts:[]}};
  }});
  const initial=await f.service.call('native_next',{},MODEL_REQUEST);
  const rejected=await f.service.call('native_spawned_batch',{batch_id:initial.batch_id},MODEL_REQUEST);
  assert.equal(rejected.status,'native_agent_invalid_result');
  const state=await f.service.call('get',f.binding),first=Object.values(state.nodes.worker.attempts[0].worker_host_checks)[0];
  const {runtime}=await f.service.open(),stored=await runtime.runs.readExecutorResult(f.run.run_id,first.receipt.attempt_id,first.receipt.output_ref.sha256);
  assert.equal(stored.completion_snapshot,undefined);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal((await f.service.call('get',f.binding)).nodes.worker.status,'succeeded');assert.equal(f.calls.length,2);
});

test('native Host checker exhausts false results visibly and preserves accepted siblings across correction',async t=>{
  const f=await nativeCheckFixture(t,{accept:request=>request.input.inputs.jobs[0].name==='a',max_attempts:2});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(repair.accepted_item_indices,undefined,'Accepted positions stay in the Host journal');
  let state=await f.service.call('get',f.binding);assert.deepEqual(Object.keys(state.nodes.worker.attempts[0].native_item_results),['0']);
  const exhausted=await f.service.call('native_followed_up',{},MODEL_REQUEST);
  assert.equal(exhausted.status,'native_agent_repair_exhausted');assert.equal(exhausted.completion_satisfied,false);
  state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'failed');assert.deepEqual(Object.keys(state.nodes.worker.attempts[0].native_item_results),['0']);
  assert.equal(f.calls.filter(call=>call.input.inputs.jobs[0].name==='a').length,1);assert.equal(f.calls.filter(call=>call.input.inputs.jobs[0].name==='b').length,2);
});

test('native Host checker cancellation retains an exact terminated receipt without accepting an item',async t=>{
  const started=deferred();let cancelled;
  const f=await nativeCheckFixture(t,{execute:request=>{started.resolve();return new Promise((_resolve,reject)=>request.signal.addEventListener('abort',()=>reject(new Error('cancel exact native check')),{once:true}));}});
  const original=f.broker.cancel;f.broker.cancel=async request=>{cancelled=request.context;return original(request);};
  const c=await nativeCheckContext(f),executor=new WorkflowExecutor({runtime:c.runtime,getConfig:()=>f.service.config(),hostToolRunner:new HostToolRunner({registry:{'native-check':f.broker},env:{}}),attemptAdmission:f.service.attemptAdmission});
  const job=executor.executeNativeHostCheck(f.run.run_id,c.binding,c.output,{item_index:0,native_observation:c.native_observation});
  const rejected=assert.rejects(job);await started.promise;await c.runtime.cancel(f.run.run_id,f.binding,()=>f.service.attemptAdmission.fenceRun(f.run.run_id));await rejected;
  const record=await c.runtime.runs.read(f.run.run_id),attempt=record.state.nodes.worker.attempts[0],slots=Object.values(attempt.worker_host_checks);
  assert.equal(slots.length,1);assert.equal(cancelled.execution_slot,slots[0].identity.slot_id);assert.equal(slots[0].receipt.reconciliation.termination_confirmed,true);
  assert.equal(record.state.cost_ledger.calls[0].usage.unknown,true);
  assert.equal(Object.keys(attempt.native_item_results??{}).length,0);assert.equal(f.service.attemptAdmission.pending(f.run.run_id).length,0);
});

test('native Host checker narrowed item workspace grant fails before effects or child spawn',async t=>{
  const f=await nativeCheckFixture(t);
  const {runtime}=await f.service.open();
  await runtime.runs.mutate(f.run.run_id,'workspace_input_bound',state=>{state.inputs.jobs[0].destinations=['pages/a/subdirectory'];});
  await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'HOST_MAIN_WORKSPACE_ISOLATION'});
  assert.equal(f.calls.length,0);assert.equal(f.seen.length,0);
});

test('native Host checker retained sibling freshness blocks the final join',async t=>{
  const f=await nativeCheckFixture(t,{requiredArtifacts:[{path:'pages/a/rendered.txt',requirement_id:'a-render'}],accept:request=>request.input.inputs.jobs[0].name==='a'||request.input.output.summary==='accepted 2'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST),repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(repair.status,'native_agent_invalid_result');
  await writeFile(join(f.workspace,'pages/a/rendered.txt'),'tampered accepted sibling');
  await assert.rejects(f.service.call('native_followed_up',{},MODEL_REQUEST),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
  const state=await f.service.call('get',f.binding);assert.notEqual(state.nodes.worker.status,'succeeded');
  assert.equal(f.calls.filter(call=>call.input.inputs.jobs[0].name==='a').length,1);
});

test('native Host checker executes the actual pinned resource program in each Host-owned item cwd',async t=>{
  const f=await nativeCheckFixture(t,{qualifiedResource:true,requiredArtifacts:[{path:'pages/a/rendered.txt',requirement_id:'a-render'},{path:'pages/b/rendered.txt',requirement_id:'b-render'}]});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  for(const packet of publicPackets(handoff))assert.doesNotMatch(packet.prompt,/native-render.mjs|Host-only exact baseline/);
  await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');
  for(const item of ['a','b'])assert.equal(await readFile(join(f.workspace,'pages',item,'rendered.txt'),'utf8'),'accepted 1');
  assert(Object.values(state.nodes.worker.attempts[0].worker_host_checks).every(slot=>slot.receipt.status==='succeeded'));
});

test('native Host checker rejects inherited model mismatch before issuing a spawn',async t=>{
  const f=await nativeCheckFixture(t);f.service.nativeMainSelection=async()=>({model:'wrong-model',effort:'high'});
  await assert.rejects(f.service.call('native_next',{},MODEL_REQUEST),{code:'NATIVE_CONTEXT_MODEL_MISMATCH'});
  assert.equal(f.calls.length,0);assert.equal(f.seen.length,0);
});

test('upstream native context fails visibly before ordinary drive can choose a managed fresh session',async t=>{
  const f=await nativeCheckFixture(t),{runtime}=await f.service.open();let prepares=0;
  const executor=new WorkflowExecutor({runtime,getConfig:()=>f.service.config(),managedNativeManager:{prepare:async()=>{prepares++;throw new Error('Fresh managed session must never start');}},attemptAdmission:f.service.attemptAdmission});
  const drive=new WorkflowDrive({runtime,executor});
  await assert.rejects(drive.advanceToMain(f.run.run_id,{...f.binding,owner:'root',managedProviders:true}),{code:'NATIVE_CONTEXT_EXECUTION_UNSUPPORTED'});
  assert.equal(prepares,0);assert.equal(f.seen.length,0);assert.equal(f.calls.length,0);
});

test('native Host checker serialized UTF8 proposal limit fails before render effects',async t=>{
  const f=await nativeCheckFixture(t,{single:true,observer:async ids=>({status:'completed',agent_id:ids[0],turn_id:'oversize-native-turn',result:{summary:'界'.repeat(128*1024)}})});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),{code:'COMPLETION_LIMIT'});
  assert.equal(f.calls.length,0);
  assert.equal((await f.service.call('get',f.binding)).cost_ledger.calls[0].usage.unknown,true);
});

test('native Host checker preflights the serialized join including known accepted siblings',async t=>{
  const f=await nativeCheckFixture(t,{observer:async ids=>({status:'completed',agent_id:ids[0],turn_id:'large-own-turn-'+ids[0],result:{items:[{outcome:'completed',result:{summary:'a'.repeat(128*1024)}}]}})});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),{code:'COMPLETION_LIMIT'});
  assert.equal(f.calls.length,1,'The oversized second proposal must not start its renderer');
  const state=await f.service.call('get',f.binding);assert.deepEqual(Object.keys(state.nodes.worker.attempts[0].native_item_results),['0']);assert.equal(state.cost_ledger.calls[0].usage.unknown,true);
});

test('native Host checker thrown or invalid output retains termination and unknown usage with visible failure',async t=>{
  for(const invalid of [false,true])await t.test(invalid?'invalid output':'throw',async t=>{
    const f=await nativeCheckFixture(t,{single:true,execute:async()=>{if(!invalid)throw new Error('Exact native checker failure');return {exit_code:0,output:{complete:'invalid',diagnostic:''},diagnostic:'',effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};}});
    const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
    await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST));
    const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'failed');assert.equal(state.cost_ledger.calls[0].usage.unknown,true);
    const slot=Object.values(state.nodes.worker.attempts[0].worker_host_checks)[0];assert.equal(slot.receipt.reconciliation.termination_confirmed,true);
  });
});

test('native Host checker retries only the unresolved child and revalidates retained sibling receipts',async t=>{
  let permit=false;
  const f=await nativeCheckFixture(t,{max_attempts:2,accept:request=>permit||request.input.inputs.jobs[0].name==='a'});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  const failed=await f.service.call('get',f.binding),previous=failed.nodes.worker.attempts[0];permit=true;
  await f.service.call('retry_node',{...f.binding,node_id:'worker',reconciliation:{attempt_id:previous.id,dispatch_request_id:previous.dispatch.request_id,outcome:'explicit_retry',evidence:[{kind:'fresh_attempt'}]}});
  const retry=await f.service.call('native_next',{},MODEL_REQUEST);assert.equal(publicPackets(retry).length,1);assert.equal(publicPackets(retry)[0].index,1);
  await f.service.call('native_spawned_batch',{batch_id:retry.batch_id},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');assert.deepEqual(state.nodes.worker.attempts[1].inherited_native_item_indices,[0]);
  assert.equal(f.calls.filter(call=>call.input.inputs.jobs[0].name==='a').length,1);
});

test('native Host checker retains successful siblings inside the same partition before exact-child correction',async t=>{
  const diagnostic='neutral issue '.repeat(500)+' decisive partition issue';
  const f=await nativeCheckFixture(t,{partition:true,diagnostic,accept:request=>request.input.inputs.jobs[0].name==='a'||request.input.output.summary==='corrected b',
    observer:async(ids,turn)=>({status:'completed',agent_id:ids[0],turn_id:'partition-turn-'+turn,result:{items:(turn===1?['original a','original b']:['corrected b']).map(summary=>({outcome:'completed',result:{summary}}))}})});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);assert.equal(publicPackets(handoff).length,1);
  const repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(repair.accepted_item_indices,undefined);assert.equal(repair.unresolved_item_indices,undefined);
  assert(repair.followup_config.message.includes(diagnostic));
  assert.match(repair.followup_config.message,/Return exactly 1 ordered items for initial assignment positions \[2\]/);
  assert.doesNotMatch(repair.followup_config.message,/Complete the assigned task|"jobs":|"result_schema":/);
  const privateRepair=await f.service.call('native_next',f.binding);
  assert.deepEqual(privateRepair.accepted_item_indices,[0]);assert.deepEqual(privateRepair.unresolved_item_indices,[1]);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');assert.deepEqual(f.calls.map(call=>call.input.inputs.jobs[0].name),['a','b','b']);
  assert.equal(new Set(f.seen.flat()).size,1);
});

test('native Host checker validates legacy blocked shared-change results before delegated acceptance',async t=>{
  const f=await nativeCheckFixture(t,{sharedChange:true,accept:(_request,count)=>count>1,
    observer:async(ids,turn)=>({status:'completed',agent_id:ids[0],turn_id:'legacy-shared-turn-'+turn+'-'+ids[0],result:{items:[{outcome:'blocked',result:{summary:'local work complete; downstream shared change'},block_reason:'shared owner must finish integration'}]}})});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  const repair=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  assert.equal(f.calls.length,1);assert.equal(Object.keys((await f.service.call('get',f.binding)).nodes.worker.attempts[0].native_item_results??{}).length,0);
  assert.equal(repair.followup_config.target,f.seen[0][0]);
  await f.service.call('native_followed_up',{},MODEL_REQUEST);
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');assert.equal(f.calls.length,3);
  assert(Object.values(state.nodes.worker.attempts[0].native_item_results).every(item=>item.delegated&&item.host_check&&item.turn_id));
});

test('native Host checker input capacity is validated before intent or rendering and retains unknown usage',async t=>{
  const f=await nativeCheckFixture(t,{single:true,inputCap:1024,observer:async ids=>({status:'completed',agent_id:ids[0],turn_id:'input-capacity-turn',result:{summary:'x'.repeat(2048)}})});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
  await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),{code:'HOST_TOOL_INPUT_LIMIT'});
  const state=await f.service.call('get',f.binding);assert.equal(state.cost_ledger.calls[0].usage.unknown,true);assert.equal(state.nodes.worker.attempts[0].worker_host_checks,undefined);assert.equal(f.calls.length,0);
});

test('native Host checker component corrections can exceed two turns within the pinned budget',async t=>{
  const f=await nativeCheckFixture(t,{single:true,max_attempts:10,accept:(_request,count)=>count>=6});
  const handoff=await f.service.call('native_next',{},MODEL_REQUEST);let next=await f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST);
  for(let turn=1;turn<=5;turn++){assert.equal(next.followup_config.target,f.seen[0][0]);next=await f.service.call('native_followed_up',{},MODEL_REQUEST);}
  const state=await f.service.call('get',f.binding);assert.equal(state.nodes.worker.status,'succeeded');assert.equal(f.calls.length,6);assert.equal(f.seen.length,6);
});

for(const fence of ['cancellation','controller','lease'])test('native public quiet wait rejects durable '+fence+' changes',async t=>{
 const f=await nativeCheckFixture(t,{itemCount:1,orchestration:true});
 const home=await mkdtemp(join(tmpdir(),'native-quiet-authority-'));await mkdir(join(home,'sessions'));
 t.after(()=>rm(home,{recursive:true,maxRetries:3,retryDelay:100}));
 const threadId=randomUUID(),turnId='quiet-owned-turn',path=join(home,'sessions','rollout-'+threadId+'.jsonl');
 f.service.nativeAgentObserver=async(ids,options)=>{
  const agentPath=ids[0],spawn={parent_thread_id:PARENT_THREAD_ID,agent_path:agentPath};
  const thread={id:threadId,path,parentThreadId:PARENT_THREAD_ID,source:{subAgent:{thread_spawn:spawn}}};
  const row=(type,payload)=>JSON.stringify({timestamp:'2026-10-09T08:00:00.000Z',type,payload})+'\n';
  await writeFile(path,row('session_meta',{id:threadId,parent_thread_id:PARENT_THREAD_ID,agent_path:agentPath,source:{subagent:{thread_spawn:spawn}}})+row('event_msg',{type:'task_started',turn_id:turnId}));
  const client={call:async method=>method==='thread/list'?{data:[thread]}:method==='thread/read'?{thread}:{data:[{id:turnId,status:'interrupted',itemsView:'summary',items:[]}]}};
  return inspectNativeAgents(client,ids,{...options,lifecycleHome:home,waitForTerminal:true,waitTimeoutMs:30000,
   waitForChange:async args=>{
    const waiting=waitForNativeSessionEvent(args);
    // Register the wait rejection immediately, before the faster observer can
    // see the deliberate authority change. Settle both owned operations.
    const changing=(async()=>{
     const {runtime}=await f.service.open();
     await runtime.runs.mutate(f.binding.run_id,'control_recovery',state=>{
      if(fence==='cancellation')state.status='cancelled';
      else if(fence==='controller')state.control_hash=digest('revoked-neutral-controller');
      else state.nodes.worker.attempts[0].lease_generation=(state.nodes.worker.attempts[0].lease_generation??0)+1;
     });
    })();
    const results=await Promise.allSettled([waiting,changing]),errors=results.filter(item=>item.status==='rejected').map(item=>item.reason);
    if(errors.length===1)throw errors[0];
    if(errors.length)throw new AggregateError(errors,'Native authority fixture operations failed');
    return results[0].value;
   }});
 };
 const handoff=await f.service.call('native_next',{},MODEL_REQUEST);
 await assert.rejects(f.service.call('native_spawned_batch',{batch_id:handoff.batch_id},MODEL_REQUEST),{code:'NATIVE_AGENT_ATTEMPT_CHANGED'});
 assert.equal(f.calls.length,0);
});
