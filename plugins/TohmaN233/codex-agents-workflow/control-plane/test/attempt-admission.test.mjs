import assert from 'node:assert/strict';
import test from 'node:test';
import { AttemptAdmissionRegistry, attemptAdmissionFor, fenceAllAttemptAdmissions } from '../lib/execution/attempt-admission.mjs';
import { connectorExecutionQuiescent } from '../connectors/registry.mjs';

const nativeSlot=index=>'native-'+String(index).padStart(40,'0');
test('native checker slots exclude ordinary owners, duplicate slots and concurrent turns of one item',()=>{
  const registry=new AttemptAdmissionRegistry();
  const first=registry.beginNativeCheck('run','node','attempt',nativeSlot(1),0);
  const second=registry.beginNativeCheck('run','node','attempt',nativeSlot(2),1);
  assert.equal(registry.pendingAttempt('run','node','attempt').length,2);
  assert.throws(()=>registry.begin('run','node','attempt','host_tool'),{code:'ATTEMPT_DUPLICATE'});
  assert.throws(()=>registry.beginNativeCheck('run','node','attempt',nativeSlot(1),0),{code:'ATTEMPT_DUPLICATE'});
  assert.throws(()=>registry.beginNativeCheck('run','node','attempt',nativeSlot(3),0),{code:'ATTEMPT_DUPLICATE'});
  first.settle();second.settle();
  const ordinary=registry.begin('run','node','attempt','host_tool');
  assert.throws(()=>registry.beginNativeCheck('run','node','attempt',nativeSlot(1),0),{code:'ATTEMPT_DUPLICATE'});
  ordinary.settle();
  for(const [slot,item]of [['arbitrary-slot',0],[nativeSlot(1),null],[nativeSlot(1),-1]])
    assert.throws(()=>registry.beginNativeCheck('run','node','attempt',slot,item),{code:'NATIVE_CHECK_ADMISSION'});
});

for(const fence of ['attempt','run','all'])test('native checker '+fence+' fence aborts and drains every exact slot',async()=>{
  const registry=new AttemptAdmissionRegistry(),owners=[0,1].map(index=>registry.beginNativeCheck('run','node','attempt',nativeSlot(index),index));
  const other=registry.begin('other','node','attempt','connector');
  if(fence==='attempt')registry.fenceAttempt('run','node','attempt');
  else if(fence==='run')registry.fenceRun('run');else registry.fenceAll();
  for(const owner of owners){assert.equal(owner.controller.signal.aborted,true);assert.throws(()=>owner.assertActive(),{code:'ATTEMPT_STOPPED'});}
  assert.equal(other.controller.signal.aborted,fence==='all');
  assert.throws(()=>registry.beginNativeCheck('run','node','attempt',nativeSlot(2),2),{code:'ATTEMPT_STOPPED'});
  let drained=false;const wait=registry.waitAttempt('run','node','attempt').then(()=>{drained=true;});
  owners[0].settle();await Promise.resolve();assert.equal(drained,false);assert.equal(registry.pendingAttempt('run','node','attempt').length,1);
  owners[1].settle();await wait;other.settle();assert.equal(drained,true);
});

test('native checker uncertain cleanup remains owned while other slots drain and retries only its owner',async()=>{
  const registry=new AttemptAdmissionRegistry(),first=registry.beginNativeCheck('run','node','attempt',nativeSlot(1),0),second=registry.beginNativeCheck('run','node','attempt',nativeSlot(2),1);
  let confirmed=false,cleanups=0;const failure=new Error('exact native cleanup unconfirmed');
  first.registerCleanup(async()=>{cleanups++;if(!confirmed)throw failure;});
  second.registerCleanup(async()=>assert.fail('Confirmed sibling must not be cleaned again'));
  registry.fenceAttempt('run','node','attempt');first.settle({error:failure});second.settle();
  assert.deepEqual(registry.pendingAttempt('run','node','attempt'),[first]);
  await assert.rejects(registry.waitAttempt('run','node','attempt'),error=>error.code==='ATTEMPT_STOP_INCOMPLETE'&&error.errors[0]===failure);
  await assert.rejects(registry.retryCleanup('run','host_tool','node','attempt'),{code:'ATTEMPT_STOP_INCOMPLETE'});
  assert.deepEqual(registry.pendingAttempt('run','node','attempt'),[first]);
  confirmed=true;await registry.retryCleanup('run','host_tool','node','attempt');
  assert.equal(cleanups,2);assert.deepEqual(registry.pendingAttempt('run','node','attempt'),[]);
});

test('a retained exact cleanup owner can retire only after later confirmed cleanup', async () => {
  const registry = new AttemptAdmissionRegistry();
  const attempt = registry.begin('run', 'node', 'attempt', 'connector');
  let confirms = 0; attempt.registerCleanup(async () => { confirms++; });
  registry.fenceRun('run'); attempt.settle({ error: new Error('initial cleanup unconfirmed') });
  await assert.rejects(registry.wait('run', 'connector'), { code: 'ATTEMPT_STOP_INCOMPLETE' });
  await registry.retryCleanup('run', 'connector');
  assert.equal(confirms, 1); assert.deepEqual(await registry.wait('run', 'connector'), []);
});

test('startup failure retains unconfirmed cleanup even without cancellation', async () => {
  const registry = new AttemptAdmissionRegistry();
  const attempt = registry.begin('run', 'node', 'attempt', 'connector');
  let confirms = 0;
  attempt.registerCleanup(async () => { confirms++; });
  attempt.settle({ error: new Error('startup failed before cleanup confirmed') });
  await assert.rejects(registry.wait('run', 'connector'), { code: 'ATTEMPT_STOP_INCOMPLETE' });
  await registry.retryCleanup('run', 'connector');
  assert.equal(confirms, 1);
  assert.deepEqual(await registry.wait('run', 'connector'), []);
});

test('exact attempt fence bars late owners and fences only its child', () => {
  const registry = new AttemptAdmissionRegistry();
  registry.registerChild('parent', 'child-a', 'node', 'attempt-a');
  registry.registerChild('parent', 'child-b', 'node', 'attempt-b');
  registry.fenceAttempt('parent', 'node', 'attempt-a');
  assert.throws(() => registry.begin('parent', 'node', 'attempt-a', 'host_tool'), { code: 'ATTEMPT_STOPPED' });
  assert.throws(() => registry.begin('child-a', 'work', 'child-attempt', 'host_tool'), { code: 'ATTEMPT_STOPPED' });
  registry.begin('parent', 'node', 'attempt-b', 'host_tool').settle();
  registry.begin('child-b', 'work', 'child-attempt', 'host_tool').settle();
});

test('successful Run drain retires on release and the next epoch owns a fresh drain', () => {
  const registry = new AttemptAdmissionRegistry();
  registry.fenceRun('run');
  registry.drainJobs.set('run', Promise.resolve());
  registry.releaseRun('run');
  assert.equal(registry.drainJobs.has('run'), false);
  registry.begin('run', 'node', 'new-attempt', 'host_tool').settle();
  registry.fenceRun('run');
  registry.drainJobs.set('run', Promise.resolve());
  assert.equal(registry.drainJobs.has('run'), true);
});

test('connector result terminal is not execution quiescence', () => {
  const terminal = { connector: 'grok_acp', state: 'cancelled', terminal_evidence: { kind: 'acp_prompt_result' } };
  assert.equal(connectorExecutionQuiescent(terminal), false);
  assert.equal(connectorExecutionQuiescent({ ...terminal, execution_cleanup: { local_quiescent: true } }), true);
  assert.equal(connectorExecutionQuiescent({ ...terminal, state: 'abandoned', execution_cleanup: { local_quiescent: true } }), false);
  assert.equal(connectorExecutionQuiescent({ ...terminal, terminal_evidence: { kind: 'acp_permission_denied' }, execution_cleanup: { local_quiescent: true } }), false);
});

test('global shutdown closes registries created after the first fence', () => {
  const existing = attemptAdmissionFor('C:/workflow-admission-existing.json');
  fenceAllAttemptAdmissions();
  assert.equal(existing.accepting, false);
  const late = attemptAdmissionFor('C:/workflow-admission-created-after-shutdown.json');
  assert.equal(late.accepting, false);
  assert.throws(() => late.begin('run', 'node', 'attempt', 'host_tool'), { code: 'ATTEMPT_STOPPED' });
});
