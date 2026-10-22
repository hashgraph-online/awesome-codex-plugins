import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {waitForWorkflow,WORKFLOW_WAIT_MS} from '../lib/workflow-wait.mjs';
async function fixture(t){
  const directory=await mkdtemp(join(tmpdir(),'workflow-wait-'));
  t.after(()=>rm(directory,{recursive:true,maxRetries:3,retryDelay:50}));
  const f={record:{state:{run_id:'trial',status:'running',nodes:{}},sequence:1,events:[]},worker:{phase:'running'},reads:0};
  f.wait=(extra={})=>waitForWorkflow({runId:'trial',directory,readState:async()=>{f.reads++;return structuredClone(f.record);},readWorker:async()=>structuredClone(f.worker),healthMs:5,...extra});
  f.notify=()=>writeFile(join(directory,'events.jsonl'),String(++f.record.sequence));return f;
}
test('one-hour wait wakes on an already failed Run without missing the startup race',async t=>{
  const f=await fixture(t);assert.equal(WORKFLOW_WAIT_MS,3600000);f.record.state.status='failed';
  const result=await f.wait();assert.equal(result.wake_reason,'failed');
  assert.equal(result.completion_satisfied,false);assert.equal(result.recovery_required,true);
});
test('Host heartbeat checks do not wake the model or reread the growing journal',async t=>{
  const f=await fixture(t);let finished=false;const pending=f.wait().then(r=>{finished=true;return r;});
  await new Promise(r=>setTimeout(r,35));assert.equal(finished,false);assert.equal(f.reads,1);
  f.worker={phase:'failed',error:{code:'HOST_MAIN_WORKER_EXIT'}};
  const result=await pending;assert.equal(result.wake_reason,'host_failed');assert.equal(result.host_worker.error.code,'HOST_MAIN_WORKER_EXIT');
});
test('confirmed Host Main termination reaches the waiting caller after Run cancellation',async t=>{
  const f=await fixture(t);f.record.state.status='cancelled';
  f.worker={phase:'cancelled',termination:{confirmed:true,reason:'cancelled',host_main_error:{code:'HOST_MAIN_STOPPED',diagnostic:'permission revoked',secondary_codes:[]}}};
  const result=await f.wait();
  assert.equal(result.wake_reason,'cancelled');
  assert.deepEqual(result.host_worker.termination,f.worker.termination);
  assert.equal(result.error,undefined);
  assert.equal(result.host_worker.error,undefined);
});
test('Host stop at a native node wakes the controller with the native handoff action',async t=>{
  const f=await fixture(t);
  f.worker={phase:'attention',outcome:{status:'running',stop_reason:'non_main_semantic',node_id:'writer'}};
  const result=await f.wait({controlToken:'example-exact-controller-token'});
  assert.equal(result.wake_reason,'native_handoff_required');
  assert.equal(result.next_action,'workflow_native_next');
  assert.deepEqual(result.next_action_args,{run_id:'trial',control_token:'example-exact-controller-token'});
  assert.deepEqual(result.host_worker.outcome,f.worker.outcome);
});
test('a journal failure wakes the waiting controller before its long deadline',async t=>{
  const f=await fixture(t);const pending=f.wait();
  f.record.state.status='failed';f.record.state.error={code:'NODE_FAILED'};await f.notify();
  const result=await pending;assert.equal(result.wake_reason,'failed');assert.equal(result.error.code,'NODE_FAILED');
});
test('subagent result wakes once per caller cursor, ordinary progress does not',async t=>{
  const f=await fixture(t);f.record.events=[{kind:'executor_event',sequence:1}];
  let finished=false;const pending=f.wait().then(r=>{finished=true;return r;});
  await new Promise(r=>setTimeout(r,15));assert.equal(finished,false);
  f.record.events.push({kind:'native_serial_result',sequence:2});await f.notify();
  assert.equal((await pending).wake_reason,'subagent_event');
  assert.equal((await f.wait({afterSequence:2,timeoutMs:20})).wake_reason,'timeout');
});
test('timeout returns waiting continuation and cancellation does not cancel the Run',async t=>{
  const f=await fixture(t);const result=await f.wait({controlToken:'example-exact-controller-token',timeoutMs:20});
  assert.equal(result.next_action,'workflow_wait');assert.equal(result.status,'running');
  assert.deepEqual(result.next_action_args,{run_id:'trial',control_token:'example-exact-controller-token',after_sequence:1,timeout_ms:20});
  const controller=new AbortController();const pending=f.wait({signal:controller.signal});controller.abort();
  await assert.rejects(pending,{code:'WORKFLOW_WAIT_CANCELLED'});assert.equal(f.record.state.status,'running');
});
test('read failures reject instead of turning into silent waits',async t=>{
  const f=await fixture(t);await assert.rejects(f.wait({readWorker:async()=>{throw Object.assign(new Error('corrupt'),{code:'CORRUPT'});}}),{code:'CORRUPT'});
});

test('pending approval wakes the controller with the exact approval identity',async t=>{
  const f=await fixture(t);f.record.state.approvals={approval1:{status:'pending'}};
  const result=await f.wait();assert.equal(result.wake_reason,'needs_attention');assert.deepEqual(result.pending_approvals,['approval1']);
});

test('an in-flight journal append gets a bounded grace period, persistent corruption fails',async t=>{
  const f=await fixture(t);let reads=0;
  const torn=()=>Object.assign(new Error('uncommitted tail'),{code:'RUN_JOURNAL_TORN'});
  const result=await f.wait({readState:async()=>{if(++reads===1)throw torn();return {...f.record,state:{...f.record.state,status:'succeeded'}};}});
  assert.equal(result.wake_reason,'succeeded');
  await assert.rejects(f.wait({readState:async()=>{throw torn();}}),{code:'RUN_JOURNAL_TORN'});
});


test('Host orchestration handoff wakes the initiating conversation without a polling turn',async t=>{
  const f=await fixture(t);
  f.worker={phase:'attention',outcome:{status:'running',stop_reason:'main_orchestration',node_id:'integration'}};
  const result=await f.wait({controlToken:randomBytes(32).toString('hex')});
  assert.equal(result.wake_reason,'native_handoff_required');
  assert.equal(result.next_action,'workflow_native_next');
  assert.equal(result.host_worker.outcome.stop_reason,'main_orchestration');
});
