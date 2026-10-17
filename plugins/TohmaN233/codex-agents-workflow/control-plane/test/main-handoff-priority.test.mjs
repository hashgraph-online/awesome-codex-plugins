import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm,writeFile,readFile} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {WorkflowRuntime} from '../lib/workflow-runtime.mjs';
import {RunHistoryMaintenance,HISTORY_MAINTENANCE_INTERVAL_MS,runHistoryMaintenanceFor,closeRunHistoryMaintenances} from '../lib/run-history-maintenance.mjs';
import {withForegroundActivity,foregroundActivityCount,inForegroundActivity,retainedForegroundPriority,foregroundPriorityPreparation,retainForegroundPriority} from '../lib/foreground-activity.mjs';
import {prepareMainOrchestration,completeMainOrchestration} from '../lib/execution/main-orchestration.mjs';
import {readyWorkflow,agent,edge} from './fixtures/workflow-fixtures.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {adoptRunTree,reattachAttempt,conversationControlRecoveryRequest} from '../lib/workflow-recovery.mjs';
import {withForegroundOperationObservation} from '../lib/foreground-operation-observation.mjs';
import {AttemptAdmissionRegistry} from '../lib/execution/attempt-admission.mjs';
import {RunExecutionCoordinator} from '../lib/execution/run-execution-coordinator.mjs';

const thread='12345678-1234-4234-8234-123456789abc';
const coordinatorFor=f=>{
 const manager=()=>({entries:new Map(),fenceRun(){},fenceAttempt(){},async stopRun(){},async stopAttempt(){}});
 const coordinator=new RunExecutionCoordinator({admission:f.options.executionAdmission,strictManager:manager(),managedNativeManager:manager(),hostMainManager:manager(),registry:{}});
 coordinator.bind(f.runtime);return coordinator;
};
const gateReceipt=f=>{
 let release,entered;const ready=new Promise(r=>entered=r),gate=new Promise(r=>release=r);
 const receipt=f.runtime.recordHostMainDispatchReceipt.bind(f.runtime);
 f.runtime.recordHostMainDispatchReceipt=async(...args)=>{const result=await receipt(...args);entered();await gate;return result;};
 return {ready,release};
};
async function fixture(t,{mutate=()=>{},prepare=true,executionAdmission=new AttemptAdmissionRegistry()}={}){
 const root=await mkdtemp(join(tmpdir(),'main-handoff-priority-')),workspace=join(root,'workspace');await mkdir(workspace);
 let launches=0;
 const manager=new RunHistoryMaintenance({runRoot:join(root,'runs'),launchWorker:async options=>{
  launches++;await options.onReady(process.pid);return {examined:0,deleted_count:0,preserved_count:0};
 }});
 let run;
 const workflow=readyWorkflow('main-priority');workflow.skill_policy.mode='cooperative';
 const node=workflow.nodes.find(n=>n.id==='final');node.executor.mode='orchestration';node.retry.max_attempts=3;
 node.outputs_schema={type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false};
 mutate(workflow);
 const store=await new WorkflowStore(join(root,'packs')).initialize();await store.create(workflow);
 const options={workflowStore:store,runRoot:manager.root,historyMaintenance:manager.hook,executionAdmission};
 const runtime=await new WorkflowRuntime(options).initialize();
 t.after(async()=>{
  if(run&&(await runtime.get(run.run_id)).status!=='succeeded')await runtime.cancel(run.run_id,{control_token:run.control_token});
  await manager.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});
 });
 const dispatch=async(nodeId,requestId)=>{
  const lease=await runtime.claimHostMain(run.run_id,{node_id:nodeId,owner:'root',request_id:requestId,control_token:run.control_token});
  const binding={node_id:nodeId,attempt_id:lease.attempt_id,lease_token:lease.lease_token,control_token:run.control_token};
  const envelope=await runtime.execution(run.run_id,binding);
  await runtime.recordHostMainDispatchIntent(run.run_id,{...binding,request_id:`dispatch-${lease.attempt_id}`,envelope_hash:digest(canonicalJSON(envelope))});
  return binding;
 };
 let binding;
 await withForegroundActivity(manager.root,async()=>{
  run=await runtime.start({workflow_id:workflow.id,workspace,access:'read_only',main_actor:'root',constraints:{native_parent_thread_id:thread}});
  binding=await dispatch(workflow.nodes.find(n=>n.type==='agent').id,'claim');
  if(prepare)await prepareMainOrchestration(runtime,{run_id:run.run_id,control_token:run.control_token,thread_id:thread});
  if(manager.task)await manager.task;
 });
 return {root,workspace,runtime,options,run,manager,binding,dispatch,launches:()=>launches,
  args:{run_id:run.run_id,control_token:run.control_token,thread_id:thread}};
}

test('validated semantic handoff keeps automatic maintenance idle while the Main thinks',async t=>{
 const f=await fixture(t);
 if(f.manager.task)await f.manager.task;
 assert.equal(inForegroundActivity(f.manager.root),false,'The originating async-local request is closed');
 assert.equal(f.launches(),0,'The request idle tail must preserve handoff priority');
 assert.equal(foregroundActivityCount(f.manager.root),1);
 const fresh=await new WorkflowRuntime(f.options).initialize();
 const again=await prepareMainOrchestration(fresh,f.args);assert.equal(again.status,'orchestration_handoff');
 assert.equal(foregroundActivityCount(f.manager.root),1,'Preparation by a fresh per-RPC runtime is idempotent');
 f.manager.hook(f.runtime.runs);if(f.manager.task)await f.manager.task;
 assert.equal(f.launches(),0,'A later automatic opportunity outside ALS sees retained priority');
 await completeMainOrchestration(fresh,{...f.args,output:{conclusion:'Accepted'}});
 await f.manager.settle();assert.equal(f.launches(),1);assert.equal(foregroundActivityCount(f.manager.root),0);
});

test('owned transport failure fences synchronously and settles priority before origin quiescence fails',async t=>{
 const f=await fixture(t),coordinator=coordinatorFor(f),exact=Object.assign(new Error('Origin close failed'),{code:'EXACT_STOP_FAILURE'});
 let audits=0;const read=f.runtime.runs.read.bind(f.runtime.runs);f.runtime.runs.read=async(...args)=>{audits++;return read(...args);};
 const entry={session:{async interrupt(){},async close(){throw exact;}},status:'running'};
 const failing=coordinator.failAttemptAfterQuiescence(f.run.run_id,f.binding,{message:'Transport lost'},{originEntry:entry});
 assert.throws(()=>f.options.executionAdmission.assertAttemptActive(f.run.run_id,f.binding.node_id,f.binding.attempt_id),{code:'ATTEMPT_STOPPED'});
 assert.equal(foregroundActivityCount(f.manager.root),0);assert.equal(audits,0,'The original synchronous revocation must precede I/O');
 await assert.rejects(failing,error=>error.code==='FAIL_NODE_STOP_INCOMPLETE'&&error.errors.includes(exact));
 assert.equal(entry.cleanupPending,true);assert.equal((await f.runtime.get(f.run.run_id)).status,'running');
});

test('opaque fence provenance rejects guessed, cross-runtime and wrong exact identities',async t=>{
 const f=await fixture(t),ticket=f.runtime.foregroundExecutionFence(f.run.run_id,f.binding);
 assert(ticket);assert.equal(f.runtime.foregroundExecutionFence(f.run.run_id,{...f.binding,lease_token:'wrong'}),undefined);
 const other=await new WorkflowRuntime(f.options).initialize();
 other.settleForegroundExecutionFence(ticket,f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 f.runtime.settleForegroundExecutionFence({},f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 f.runtime.settleForegroundExecutionFence(ticket,'another-run',f.binding.node_id,f.binding.attempt_id);
 f.runtime.settleForegroundExecutionFence(ticket,f.run.run_id,'another-node',f.binding.attempt_id);
 f.runtime.settleForegroundExecutionFence(ticket,f.run.run_id,f.binding.node_id,'another-attempt');
 assert.equal(foregroundActivityCount(f.manager.root),1);
 f.runtime.settleForegroundExecutionFence(ticket,f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 assert.equal(foregroundActivityCount(f.manager.root),0);
});

test('an old exact attempt fence cannot cancel a successor handoff awaiting bundle I/O without a hold',async t=>{
 const f=await fixture(t,{mutate:w=>{
  const first={...agent('first'),executor:{kind:'main',mode:'orchestration'},retry:{max_attempts:3},outputs_schema:w.nodes[1].outputs_schema};
  w.nodes.splice(1,0,first);w.edges=[edge('start','first'),edge('first','final'),edge('final','end')];
 }}),coordinator=coordinatorFor(f),old=f.binding,ticket=f.runtime.foregroundExecutionFence(f.run.run_id,old);
 await withForegroundActivity(f.manager.root,async()=>{
  await completeMainOrchestration(f.runtime,{...f.args,output:{conclusion:'First accepted'}});
  const successor=await f.dispatch('final','successor-claim');
  const gate=gateReceipt(f),preparing=prepareMainOrchestration(f.runtime,f.args);await gate.ready;
  assert.equal(retainedForegroundPriority(f.manager.root,f.run.run_id),undefined,'Receipt and bundle preparation have no retained handoff yet');
  coordinator.fenceAttempt(f.run.run_id,old.node_id,old.attempt_id,ticket);
  f.options.executionAdmission.assertAttemptActive(f.run.run_id,successor.node_id,successor.attempt_id);
  gate.release();assert.equal((await preparing).status,'orchestration_handoff');
 });
 assert.equal(foregroundActivityCount(f.manager.root),1);assert.equal(f.launches(),0);
});

test('an old coordinator attempt fence cannot cancel a same-node retry preparation awaiting receipt I/O',async t=>{
 const f=await fixture(t),coordinator=coordinatorFor(f),old=f.binding,ticket=f.runtime.foregroundExecutionFence(f.run.run_id,old);
 await withForegroundActivity(f.manager.root,async()=>{
  await f.runtime.failNode(f.run.run_id,{...old,error:{message:'Scoped retry preparation fixture'}});
  await f.runtime.retryNode(f.run.run_id,{node_id:old.node_id,control_token:f.run.control_token,reconciliation:{attempt_id:old.attempt_id,
   dispatch_request_id:`dispatch-${old.attempt_id}`,outcome:'terminated',evidence:[{kind:'logical_main_closed'}]}});
  await coordinator.assertRunQuiescent(await f.runtime.runs.read(f.run.run_id));f.options.executionAdmission.releaseRun(f.run.run_id);
  const current=await f.dispatch(old.node_id,'scoped-retry-claim');assert.notEqual(current.attempt_id,old.attempt_id);
  const gate=gateReceipt(f),preparing=prepareMainOrchestration(f.runtime,f.args);await gate.ready;
  assert.equal(retainedForegroundPriority(f.manager.root,f.run.run_id),undefined);
  for(let repeat=0;repeat<2;repeat++)coordinator.fenceAttempt(f.run.run_id,old.node_id,old.attempt_id,ticket);
  f.options.executionAdmission.assertAttemptActive(f.run.run_id,current.node_id,current.attempt_id);
  gate.release();assert.equal((await preparing).status,'orchestration_handoff');
 });
 assert.equal(foregroundActivityCount(f.manager.root),1);assert.equal(f.launches(),0);
});

for(const scope of ['generation','controller'])test(`old ${scope} priority settlement cannot cancel reattached preparation awaiting receipt I/O`,async t=>{
 const f=await fixture(t,{prepare:false}),ticket=f.runtime.foregroundExecutionFence(f.run.run_id,f.binding);
 await withForegroundActivity(f.manager.root,async()=>{
  const before=await f.runtime.authorizedRun(f.run.run_id,f.args);
  if(scope==='controller'){
   const recovered=await adoptRunTree(f.runtime,f.run.run_id,{expected_sequence:before.sequence,reason:'Scoped preparation recovery',main_actor:'root'},
    id=>f.options.executionAdmission.fenceRun(id));
   f.run.control_token=recovered.run.control_token;f.args.control_token=f.run.control_token;
  }else await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token,after_restart:true});
  await reattachAttempt(f.runtime,f.run.run_id,{node_id:f.binding.node_id,attempt_id:f.binding.attempt_id,control_token:f.run.control_token},
   {kind:'logical_main_closed',dispatch_request_id:`dispatch-${f.binding.attempt_id}`,attempt_id:f.binding.attempt_id});
  await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token});
  if(scope==='controller')f.options.executionAdmission.releaseRun(f.run.run_id);
  const gate=gateReceipt(f),preparing=prepareMainOrchestration(f.runtime,f.args);await gate.ready;
  assert.equal(retainedForegroundPriority(f.manager.root,f.run.run_id),undefined);
  // The admission registry intentionally fences by attempt ID. Exercise only
  // genuine scheduling settlement so old-generation execution revocation is
  // neither bypassed nor misrepresented as generation-aware admission.
  for(let repeat=0;repeat<2;repeat++)f.runtime.settleForegroundExecutionFence(ticket,f.run.run_id,f.binding.node_id,f.binding.attempt_id);
  if(scope==='controller')f.runtime.fenceMainForeground(before.state);
  f.options.executionAdmission.assertAttemptActive(f.run.run_id,f.binding.node_id,f.binding.attempt_id);
  gate.release();assert.equal((await preparing).status,'orchestration_handoff');
 });
 assert.equal(foregroundActivityCount(f.manager.root),1);
});

for(const fence of ['attempt','cancel','recovery'])test(`real ${fence} fence rejects the same pending first preparation after receipt I/O`,async t=>{
 const f=await fixture(t,{prepare:false}),gate=gateReceipt(f),coordinator=coordinatorFor(f);
 const ticket=f.runtime.foregroundExecutionFence(f.run.run_id,f.binding);
 await withForegroundActivity(f.manager.root,async()=>{
  const preparing=prepareMainOrchestration(f.runtime,f.args);await gate.ready;
  assert.equal(retainedForegroundPriority(f.manager.root,f.run.run_id),undefined);
  if(fence==='attempt')coordinator.fenceAttempt(f.run.run_id,f.binding.node_id,f.binding.attempt_id,ticket);
  else if(fence==='cancel')await f.runtime.cancel(f.run.run_id,{control_token:f.run.control_token});
  else{
   const before=await f.runtime.get(f.run.run_id),recovered=await adoptRunTree(f.runtime,f.run.run_id,
    {expected_sequence:before.sequence,reason:'Pending preparation recovery',main_actor:'root'},id=>f.options.executionAdmission.fenceRun(id));
   f.run.control_token=recovered.run.control_token;f.args.control_token=f.run.control_token;
  }
  assert.throws(()=>f.options.executionAdmission.assertAttemptActive(f.run.run_id,f.binding.node_id,f.binding.attempt_id),{code:'ATTEMPT_STOPPED'});
  gate.release();await assert.rejects(preparing,{code:'ATTEMPT_STOPPED'});
 });
 assert.equal(foregroundActivityCount(f.manager.root),0);
});

for(const fence of ['attempt','cancel','recovery'])test(`a genuine ${fence} fence rejects pending first preparation even without an execution registry`,async t=>{
 const f=await fixture(t,{prepare:false,executionAdmission:null}),gate=gateReceipt(f);
 const ticket=f.runtime.foregroundExecutionFence(f.run.run_id,f.binding);
 await withForegroundActivity(f.manager.root,async()=>{
  const preparing=prepareMainOrchestration(f.runtime,f.args);await gate.ready;
  if(fence==='attempt')f.runtime.settleForegroundExecutionFence(ticket,f.run.run_id,f.binding.node_id,f.binding.attempt_id);
  else if(fence==='cancel')await f.runtime.cancel(f.run.run_id,{control_token:f.run.control_token});
  else{
   const before=await f.runtime.get(f.run.run_id),recovered=await adoptRunTree(f.runtime,f.run.run_id,
    {expected_sequence:before.sequence,reason:'Pending standalone preparation recovery',main_actor:'root'});
   f.run.control_token=recovered.run.control_token;f.args.control_token=f.run.control_token;
  }
  gate.release();await assert.rejects(preparing,{code:'ATTEMPT_STOPPED',message:'Main handoff was fenced during preparation'});
 });
 assert.equal(foregroundActivityCount(f.manager.root),0);
});

test('unknown or differently bound preparation snapshots cannot retain an authenticated identity',async t=>{
 const f=await fixture(t,{prepare:false}),record=await f.runtime.authorizedRun(f.run.run_id,f.args);
 const identity={run_id:f.run.run_id,node_id:f.binding.node_id,attempt_id:f.binding.attempt_id,lease_generation:0,
  controller_binding_hash:f.runtime.mainForegroundControllerBinding(record.state)};
 for(const snapshot of [{},foregroundPriorityPreparation(f.manager.root,'another-run'),foregroundPriorityPreparation(f.workspace,f.run.run_id)])
  assert.throws(()=>retainForegroundPriority(f.manager.root,identity,snapshot),{code:'ATTEMPT_STOPPED'});
 assert.equal(retainedForegroundPriority(f.manager.root,f.run.run_id),undefined);
 f.options.executionAdmission.assertAttemptActive(f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 assert.equal((await prepareMainOrchestration(f.runtime,f.args)).status,'orchestration_handoff');
});

test('owned Run drain preserves synchronous revocation then settles from its original audit before stop failure',async t=>{
 const f=await fixture(t),coordinator=coordinatorFor(f),exact=Object.assign(new Error('Run stop failed'),{code:'EXACT_STOP_FAILURE'});
 coordinator.hostMainManager.stopRun=async()=>{throw exact;};
 const draining=coordinator.drainRun(f.run.run_id);
 assert.throws(()=>f.options.executionAdmission.assertRunActive(f.run.run_id),{code:'ATTEMPT_STOPPED'});
 await assert.rejects(draining,error=>error.code==='RUN_EXECUTION_STOP_INCOMPLETE'&&error.errors.includes(exact));
 assert.equal(foregroundActivityCount(f.manager.root),0);assert.equal((await f.runtime.get(f.run.run_id)).status,'running');
});

test('unreadable owned drain preserves its original revocation and error without guessing a priority identity',async t=>{
 const f=await fixture(t),coordinator=coordinatorFor(f),exact=Object.assign(new Error('Original audit failed'),{code:'EXACT_AUDIT_FAILURE'});
 const read=f.runtime.runs.read.bind(f.runtime.runs);f.runtime.runs.read=async()=>{throw exact;};
 const draining=coordinator.drainRun(f.run.run_id);
 assert.throws(()=>f.options.executionAdmission.assertRunActive(f.run.run_id),{code:'ATTEMPT_STOPPED'});
 await assert.rejects(draining,error=>error===exact);assert.equal(foregroundActivityCount(f.manager.root),1);
 f.runtime.runs.read=read;
});

test('wrong controller, conversation and stale execution lease cannot clear a validated handoff',async t=>{
 const f=await fixture(t),before=await f.runtime.get(f.run.run_id);
 await assert.rejects(prepareMainOrchestration(f.runtime,{...f.args,control_token:'wrong'}),{code:'RUN_AUTHORITY'});
 await assert.rejects(completeMainOrchestration(f.runtime,{...f.args,control_token:'wrong',output:{conclusion:'wrong'}}),{code:'RUN_AUTHORITY'});
 await assert.rejects(prepareMainOrchestration(f.runtime,{...f.args,thread_id:'another-thread'}),{code:'MAIN_ORCHESTRATION_CONTEXT'});
 await assert.rejects(f.runtime.cancel(f.run.run_id,{control_token:'wrong'}),{code:'RUN_AUTHORITY'});
 await assert.rejects(f.runtime.failNode(f.run.run_id,{...f.binding,lease_token:'wrong',error:{message:'wrong'}}),{code:'LEASE_INVALID'});
 assert.equal(foregroundActivityCount(f.manager.root),1);assert.equal(f.launches(),0);
 assert.deepEqual(await f.runtime.get(f.run.run_id),before);
});

test('invalid semantic schema keeps an active repair attempt, exhaustion releases it',async t=>{
 const f=await fixture(t);
 for(let index=1;index<=3;index++){
  await assert.rejects(completeMainOrchestration(f.runtime,{...f.args,output:{invalid:'schema'}}));
  const state=await f.runtime.get(f.run.run_id);
  assert.equal(state.nodes.final.attempts[0].completion_turns,index);
  assert.equal(state.status,index<3?'running':'failed');
  assert.equal(foregroundActivityCount(f.manager.root),index<3?1:0);
  if(index<3)assert.equal(f.launches(),0);
 }
 await f.manager.settle();assert.equal(f.launches(),1);
});

test('semantic schema repair completes the original dispatched attempt and releases exactly once',async t=>{
 const f=await fixture(t);
 await assert.rejects(completeMainOrchestration(f.runtime,{...f.args,output:{invalid:true}}));
 await completeMainOrchestration(f.runtime,{...f.args,output:{conclusion:'Repaired'}});
 const state=await f.runtime.get(f.run.run_id);assert.equal(state.status,'succeeded');
 assert.equal(state.nodes.final.attempts.length,1);assert.equal(state.nodes.final.attempts[0].completion_turns,2);
 await f.manager.settle();assert.equal(f.launches(),1);assert.equal(foregroundActivityCount(f.manager.root),0);
});

test('explicit Main rejection reaches its terminal failure and releases priority',async t=>{
 const f=await fixture(t,{mutate:w=>{
  const node=w.nodes.find(n=>n.id==='final');node.outputs_schema.properties.accepted={type:'boolean'};node.outputs_schema.required.push('accepted');
 }});
 await assert.rejects(completeMainOrchestration(f.runtime,{...f.args,output:{conclusion:'Rejected',accepted:false}}),{code:'FINAL_ACCEPTANCE_REQUIRED'});
 assert.equal((await f.runtime.get(f.run.run_id)).status,'failed');assert.equal(foregroundActivityCount(f.manager.root),0);
 await f.manager.settle();assert.equal(f.launches(),1);
});

test('tampered dispatch bundle failures preserve existing priority; first invalid handoff retains none',async t=>{
 for(const prepare of [true,false]){
  const f=await fixture(t,{prepare});
  if(!prepare){
   const record=f.runtime.recordHostMainDispatchReceipt.bind(f.runtime);
   f.runtime.recordHostMainDispatchReceipt=async(id,args)=>{const result=await record(id,args);await writeFile(args.receipt.task_bundle_path,'tampered');return result;};
  }else{
   const before=await f.runtime.runs.read(f.run.run_id);await writeFile(before.state.nodes.final.attempts[0].dispatch.receipt.task_bundle_path,'tampered');
  }
  await assert.rejects(prepareMainOrchestration(f.runtime,f.args),{code:'MAIN_ORCHESTRATION_BUNDLE'});
  assert.equal(foregroundActivityCount(f.manager.root),prepare?1:0);
 }
});

test('retry and successive Main handoff inside one foreground request expose no idle scheduling gap',async t=>{
 const f=await fixture(t,{mutate:w=>{
  const first={...agent('first'),executor:{kind:'main',mode:'orchestration'},retry:{max_attempts:3},outputs_schema:w.nodes[1].outputs_schema};
  w.nodes.splice(1,0,first);w.edges=[edge('start','first'),edge('first','final'),edge('final','end')];
 }});
 await withForegroundActivity(f.manager.root,async()=>{
  await f.runtime.failNode(f.run.run_id,{...f.binding,error:{message:'Exact failed attempt'}});
  assert.equal(foregroundActivityCount(f.manager.root),1);assert.equal(f.launches(),0);
  await f.runtime.retryNode(f.run.run_id,{node_id:'first',control_token:f.run.control_token,reconciliation:{attempt_id:f.binding.attempt_id,
   dispatch_request_id:`dispatch-${f.binding.attempt_id}`,outcome:'terminated',evidence:[{kind:'logical_main_closed'}]}});
  await coordinatorFor(f).assertRunQuiescent(await f.runtime.runs.read(f.run.run_id));f.options.executionAdmission.releaseRun(f.run.run_id);
  await f.dispatch('first','retry-claim');await prepareMainOrchestration(f.runtime,f.args);
  await assert.rejects(f.runtime.failNode(f.run.run_id,{...f.binding,error:{message:'Stale failure'}}),{code:'STALE_LEASE'});
  assert.equal(foregroundActivityCount(f.manager.root),2);assert.equal(f.launches(),0);
  await completeMainOrchestration(f.runtime,{...f.args,output:{conclusion:'First accepted'}});
  assert.equal(f.launches(),0);
  await f.dispatch('final','final-claim');await prepareMainOrchestration(f.runtime,f.args);
 });
 assert.equal(foregroundActivityCount(f.manager.root),1);assert.equal(f.launches(),0);
 await completeMainOrchestration(f.runtime,{...f.args,output:{conclusion:'Final accepted'}});
 await f.manager.settle();assert.equal(f.launches(),1);
});

test('retained handoff preserves the original automatic age escape at the next normal opportunity',async t=>{
 const f=await fixture(t),requested=f.manager.deferred.requestedAt;
 t.mock.method(Date,'now',()=>requested+HISTORY_MAINTENANCE_INTERVAL_MS-1);
 f.manager.hook(f.runtime.runs);if(f.manager.task)await f.manager.task;assert.equal(f.launches(),0);
 assert.equal(f.manager.deferred.requestedAt,requested,'Idempotent preparation and opportunities never reset deferred age');
 await prepareMainOrchestration(f.runtime,f.args);
 t.mock.method(Date,'now',()=>requested+HISTORY_MAINTENANCE_INTERVAL_MS);
 f.manager.hook(f.runtime.runs);if(f.manager.task)await f.manager.task;
 assert.equal(f.launches(),1);assert.equal(foregroundActivityCount(f.manager.root),1);
});

test('manual maintenance and explicit settlement keep their original immediate behavior during a handoff',async t=>{
 for(const explicit of ['schedule','settle']){
  const f=await fixture(t);if(explicit==='schedule')f.manager.schedule(f.runtime.runs);
  await f.manager.settle();assert.equal(f.launches(),1);assert.equal(foregroundActivityCount(f.manager.root),1);
 }
});

test('cancellation revokes priority and an already authorized preparation cannot restore it after awaiting I/O',{timeout:10000},async t=>{
 const f=await fixture(t);let entered,release;
 const gate=new Promise(r=>release=r),ready=new Promise(r=>entered=r),authorized=f.runtime.authorizedHostMainPlanning.bind(f.runtime);
 f.runtime.authorizedHostMainPlanning=async(...args)=>{const result=await authorized(...args);entered();await gate;return result;};
 const preparing=withForegroundActivity(f.manager.root,()=>prepareMainOrchestration(f.runtime,f.args));
 await ready;await f.runtime.cancel(f.run.run_id,{control_token:f.run.control_token});
 assert.equal(foregroundActivityCount(f.manager.root),1,'Only the still-open request remains');
 release();await assert.rejects(preparing,{code:'ATTEMPT_STOPPED'});
 await f.manager.settle();assert.equal(f.launches(),1);assert.equal(foregroundActivityCount(f.manager.root),0);
});

test('restart recovery fence releases only after original controller authorization',async t=>{
 const f=await fixture(t);
 await assert.rejects(f.runtime.resume(f.run.run_id,{control_token:'wrong',after_restart:true}),{code:'RUN_AUTHORITY'});
 assert.equal(foregroundActivityCount(f.manager.root),1);
 const result=await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token,after_restart:true});
 assert.equal(result.status,'interrupted');assert.equal(foregroundActivityCount(f.manager.root),0);
});

test('authorized controller recovery fences the old binding and reattachment retains the explicit new lease generation',async t=>{
 const f=await fixture(t),before=await f.runtime.get(f.run.run_id);
 const oldFence=f.runtime.foregroundExecutionFence(f.run.run_id,f.binding);
 const args=conversationControlRecoveryRequest({run_id:f.run.run_id,expected_sequence:before.sequence,main_actor:'root',reason:'Authorized fixture recovery',
  authorization:{confirmed:true,source:'user_message',statement:'Recover this exact fixture Run'}});
 await assert.rejects(adoptRunTree(f.runtime,f.run.run_id,{...args,expected_sequence:before.sequence-1}),{code:'RUN_SEQUENCE_CONFLICT'});
 assert.equal(foregroundActivityCount(f.manager.root),1);
 const recovered=await adoptRunTree(f.runtime,f.run.run_id,args,id=>f.options.executionAdmission.fenceRun(id));
 const oldArgs={...f.args};f.run.control_token=recovered.run.control_token;f.args.control_token=f.run.control_token;
 assert.equal(foregroundActivityCount(f.manager.root),0);assert.equal(recovered.run.status,'paused');
 const old=f.binding,reattached=await reattachAttempt(f.runtime,f.run.run_id,{node_id:old.node_id,attempt_id:old.attempt_id,control_token:f.run.control_token},
  {kind:'logical_main_closed',dispatch_request_id:`dispatch-${old.attempt_id}`,attempt_id:old.attempt_id});
 assert.equal(reattached.envelope.attempt_id,old.attempt_id);
 await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token});
 f.options.executionAdmission.releaseRun(f.run.run_id);
 await prepareMainOrchestration(f.runtime,f.args);assert.equal(foregroundActivityCount(f.manager.root),1);
 f.runtime.settleForegroundExecutionFence(oldFence,f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 assert.equal(foregroundActivityCount(f.manager.root),1,'Old controller/generation provenance cannot clear the reattached handoff');
 await assert.rejects(coordinatorFor(f).fenceAndSnapshotAttempt(f.run.run_id,f.binding.node_id,f.binding.attempt_id,old),{code:'RUN_AUTHORITY'});
 f.options.executionAdmission.assertAttemptActive(f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 await assert.rejects(prepareMainOrchestration(f.runtime,oldArgs),{code:'RUN_AUTHORITY'});
 await assert.rejects(f.runtime.failNode(f.run.run_id,{...old,error:{message:'Revoked generation'}}),{code:'LEASE_INVALID'});
 const state=await f.runtime.runs.read(f.run.run_id);assert.equal(state.state.nodes.final.attempts[0].lease_generation,2);
 assert.equal(foregroundActivityCount(f.manager.root),1);
});

test('writer fence revalidates lease generation even when the controller is unchanged',async t=>{
 const f=await fixture(t),coordinator=coordinatorFor(f),before=await f.runtime.get(f.run.run_id);
 const oldFence=f.runtime.foregroundExecutionFence(f.run.run_id,f.binding);
 await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token,after_restart:true});
 await reattachAttempt(f.runtime,f.run.run_id,{node_id:f.binding.node_id,attempt_id:f.binding.attempt_id,control_token:f.run.control_token},
  {kind:'logical_main_closed',dispatch_request_id:`dispatch-${f.binding.attempt_id}`,attempt_id:f.binding.attempt_id});
 await f.runtime.resume(f.run.run_id,{control_token:f.run.control_token});await prepareMainOrchestration(f.runtime,f.args);
 assert.equal((await f.runtime.get(f.run.run_id)).control_hash,before.control_hash);
 f.runtime.settleForegroundExecutionFence(oldFence,f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 assert.equal(foregroundActivityCount(f.manager.root),1);
 await assert.rejects(coordinator.fenceAndSnapshotAttempt(f.run.run_id,f.binding.node_id,f.binding.attempt_id,f.binding),{code:'LEASE_INVALID'});
 await assert.rejects(coordinator.fenceAndSnapshotAttempt(f.run.run_id,f.binding.node_id,f.binding.attempt_id,{control_token:f.run.control_token},true),{code:'NODE_RETRY_STATE'});
 f.options.executionAdmission.assertAttemptActive(f.run.run_id,f.binding.node_id,f.binding.attempt_id);
 assert.equal(foregroundActivityCount(f.manager.root),1);
});

test('observer failure after preparation preserves the committed dispatch and handoff for exact reconciliation',async t=>{
 const f=await fixture(t),error=new Error('Exact audit failure');
 await assert.rejects(withForegroundActivity(f.manager.root,()=>withForegroundOperationObservation(
  ()=>prepareMainOrchestration(f.runtime,f.args),()=>{throw error;})),e=>e===error);
 assert.equal(foregroundActivityCount(f.manager.root),1);assert.equal(f.launches(),0);
 const record=await f.runtime.runs.read(f.run.run_id);assert.equal(record.state.nodes.final.attempts.length,1);
 assert.equal(record.state.nodes.final.attempts[0].dispatch.receipt.executor,'codex-current-main-orchestration');
 await prepareMainOrchestration(f.runtime,f.args);assert.equal(foregroundActivityCount(f.manager.root),1);
});

test('a recovery error after the original execution fence releases priority and preserves its uncommitted journal evidence',async t=>{
 const f=await fixture(t);
 await f.runtime.runs.mutate(f.run.run_id,'reattach',state=>{state.nodes.final.attempts[0].lease_generation=Number.MAX_SAFE_INTEGER;});
 const before=await f.runtime.runs.read(f.run.run_id);
 await assert.rejects(adoptRunTree(f.runtime,f.run.run_id,{expected_sequence:before.sequence,reason:'Exact recovery fixture',main_actor:'root'},
  id=>f.options.executionAdmission.fenceRun(id)),{code:'LEASE_GENERATION_LIMIT'});
 assert.throws(()=>f.options.executionAdmission.assertRunActive(f.run.run_id),{code:'ATTEMPT_STOPPED'});
 assert.equal(foregroundActivityCount(f.manager.root),0);
 assert.deepEqual(await f.runtime.runs.read(f.run.run_id),before,'No successful recovery is fabricated after the fenced callback fails');
});

test('ordinary manager close-all keeps its original reopen API outside server shutdown',async t=>{
 const root=await mkdtemp(join(tmpdir(),'history-reopen-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const first=runHistoryMaintenanceFor({runRoot:join(root,'runs')});await closeRunHistoryMaintenances();
 assert.equal(first.closed,true);const next=runHistoryMaintenanceFor({runRoot:join(root,'runs')});
 assert.notEqual(first,next);assert.equal(next.closed,false);await closeRunHistoryMaintenances();
});

test('a separate Host cancellation is reconciled at the next original fully authorized planning read',async t=>{
 const f=await fixture(t);
 const source=`import {WorkflowRuntime} from ${JSON.stringify(new URL('../lib/workflow-runtime.mjs',import.meta.url).href)};
 let bytes='';for await(const chunk of process.stdin)bytes+=chunk;
 const args=JSON.parse(bytes),runtime=await new WorkflowRuntime({workflowStore:null,runRoot:args.root}).initialize();
 const result=await runtime.cancel(args.run_id,{control_token:args.control_token});process.stdout.write(result.status);`;
 const child=spawn(process.execPath,['--input-type=module','--eval',source],{stdio:['pipe','pipe','pipe']});
 let stdout='',stderr='';child.stdout.on('data',chunk=>stdout+=chunk);child.stderr.on('data',chunk=>stderr+=chunk);
 const closed=new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',resolve);});
 child.stdin.end(JSON.stringify({root:f.manager.root,run_id:f.run.run_id,control_token:f.run.control_token}));
 assert.equal(await closed,0,stderr);assert.equal(stdout,'cancelled');
 assert.equal(foregroundActivityCount(f.manager.root),1,'Private scheduling preference has no cross-process notification');
 await assert.rejects(f.runtime.authorizeController(f.run.run_id,{control_token:'wrong'}),{code:'RUN_AUTHORITY'});
 assert.equal(foregroundActivityCount(f.manager.root),1,'Unauthenticated reads cannot release another hold');
 const planned=await f.runtime.authorizedPlanningRun(f.run.run_id,{control_token:f.run.control_token});
 assert.equal(planned.record.state.status,'cancelled');assert.equal(foregroundActivityCount(f.manager.root),0);
 await f.manager.settle();assert.equal(f.launches(),1);
});

for(const mode of ['deferred','failure','stop_pending','stop_pending_write'])test(`real server shutdown closes maintenance before releasing retained Main priority: ${mode}`,{timeout:10000},async t=>{
 const root=await mkdtemp(join(tmpdir(),'handoff-server-shutdown-'));
 const child=spawn(process.execPath,['--import',new URL('./fixtures/main-handoff-shutdown.mjs',import.meta.url).href,
  fileURLToPath(new URL('../server.mjs',import.meta.url))],{env:{...process.env,HANDOFF_PRIORITY_FIXTURE_ROOT:root,HANDOFF_PRIORITY_FIXTURE_MODE:mode},stdio:['pipe','pipe','pipe','ipc']});
 let stderr='';child.stderr.on('data',bytes=>stderr+=bytes);child.stdout.resume();
 const closed=new Promise((resolve,reject)=>{child.once('error',reject);child.once('close',resolve);});
 t.after(async()=>{if(child.exitCode===null){child.kill();await closed;}await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
 const ready=await new Promise((resolve,reject)=>{child.once('message',resolve);closed.then(()=>reject(new Error(`Fixture exited before ready: ${stderr}`)),reject);});
 assert.equal(ready.count,1);assert.equal(ready.launches,mode==='deferred'?0:1);
 child.stdin.end(JSON.stringify({jsonrpc:'2.0',id:901,method:'ping'})+'\n');const exit=await closed;
 const final=JSON.parse(await readFile(join(root,'shutdown-state.json'),'utf8'));
 assert.equal(exit,mode==='deferred'?0:1,stderr);assert.equal(final.closed,true);assert.equal(final.count,0);
 assert.equal(final.retention_error,'ATTEMPT_STOPPED','Shutdown must fence new priority even without an execution registry');
 assert.equal(final.late_manager_error,'RUN_HISTORY_MAINTENANCE_CLOSED','A fresh per-RPC service cannot reopen maintenance during shutdown');
 assert.equal(final.late_rpc_error,'RUN_HISTORY_MAINTENANCE_CLOSED','An actual late service RPC during server write drain fails explicitly');
 assert.equal(final.launches,mode==='deferred'?0:1,'Releasing priority after close cannot launch deferred maintenance');
 if(mode.startsWith('stop_pending')){
  assert.match(stderr,/retained unconfirmed execution ownership/);
  assert.deepEqual(final.close_error,{code:'RUN_HISTORY_MAINTENANCE_STOP_PENDING',persistence_error:'RUN_HISTORY_MAINTENANCE_RECEIPT_PENDING'});
  const receipt=JSON.parse(await readFile(join(root,'runs','.run-locks','.history-maintenance','receipt.json'),'utf8'));
  if(mode==='stop_pending_write'){
   assert.equal(receipt.phase,'auditing');assert.equal(receipt.outcome,'pending');assert.equal(receipt.error,undefined);
  }else{
   assert.equal(receipt.outcome,'stop_pending');assert.equal(receipt.error.code,'RUN_HISTORY_MAINTENANCE_STOP_PENDING');
  }
  const claim=JSON.parse(await readFile(join(root,'runs','.run-locks','.history-maintenance','.writer.lock'),'utf8'));
  for(const key of ['job_id','owner_token','owner_pid','created_at'])assert.equal(claim[key],receipt[key],'Unconfirmed shutdown must retain the exact original owner');
 }
 if(mode==='failure')assert.match(stderr,/retained unconfirmed execution ownership/);
});
