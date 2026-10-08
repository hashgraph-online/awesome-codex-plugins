import assert from 'node:assert/strict';
import test from 'node:test';
import { AttemptAdmissionRegistry, attemptAdmissionFor, fenceAllAttemptAdmissions } from '../lib/execution/attempt-admission.mjs';
import { connectorExecutionQuiescent } from '../connectors/registry.mjs';

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
