import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { tmpdir } from './physical-tempdir.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { WorkflowRuntime } from '../lib/workflow-runtime.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { initialRunState, advanceRun } from '../lib/workflow-state.mjs';

const context = { providers: [{ id: 'p', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, config: { role: 'implementer' } }] };
const agent = (id, source) => ({ id, type: 'agent', executor: id === 'final' ? { kind: 'main' } : { kind: 'thread', provider_id: 'p', lifecycle: source ? 'continue' : 'start', ...(source ? { source_node: source } : {}) }, role: id === 'final' ? 'finalizer' : 'implementer', access: 'read_only', prompt_template: 'Synthetic task', approval: { required: false }, retry: { max_attempts: 3 }, input_bindings: {}, outputs_schema: {} });
const edge = (source, target, label) => ({ id: source + '-' + target, source, target, ...(label ? { label } : {}) });
function definition(kind = 'sequential') {
  const w = { ...createDraft('thread-protocol', 'Thread protocol fixture'), status: 'ready', skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, finalization: { required: true, node_id: 'final' } };
  const parallel = kind === 'parallel';
  w.nodes = [{ id: 'start', type: 'start' }, agent('seed'), ...(kind === 'sequential' ? [agent('a', 'seed')] : [parallel ? { id: 'fork', type: 'parallel', join_id: 'join' } : { id: 'fork', type: 'condition', cases: [{ label: 'yes', when: { op: 'exists', args: [{ path: '/inputs/choice' }] } }], default_label: 'no' }, agent('a', 'seed'), agent('b', 'seed'), ...(parallel ? [{ id: 'join', type: 'join', parallel_id: 'fork' }] : [])]), agent('final'), { id: 'end', type: 'end' }];
  w.edges = [edge('start', 'seed'), ...(kind === 'sequential' ? [edge('seed', 'a'), edge('a', 'final')] : [edge('seed', 'fork'), edge('fork', 'a', 'yes'), edge('fork', 'b', 'no'), edge('a', parallel ? 'join' : 'final'), edge('b', parallel ? 'join' : 'final'), ...(parallel ? [edge('join', 'final')] : [])]), edge('final', 'end')];
  return w;
}

test('shared-task branches are rejected, including indirect aliases, but exclusive and sequential continuations remain valid', () => {
  for (const kind of ['sequential', 'condition']) assert.equal(validateWorkflowGraph(definition(kind), context).valid, true);
  const w = definition('parallel');
  assert(validateWorkflowGraph(w, context).errors.some(e => e.code === 'THREAD_CONCURRENT_CONTINUATION'));
  w.nodes.push(agent('alias', 'seed')); w.edges = w.edges.filter(e => e.source !== 'seed'); w.edges.push(edge('seed', 'alias'), edge('alias', 'fork'));
  w.nodes.find(n => n.id === 'a').executor.source_node = 'alias';
  assert(validateWorkflowGraph(w, context).errors.some(e => e.code === 'THREAD_CONCURRENT_CONTINUATION'));
  for (const id of ['a', 'b']) w.nodes.find(n => n.id === id).executor = agent(id).executor;
  assert.equal(validateWorkflowGraph(w, context).valid, true);
  const self = definition(); self.nodes.find(n => n.id === 'a').executor.source_node = 'a';
  assert(validateWorkflowGraph(self, context).errors.some(e => e.code === 'THREAD_SOURCE_ORDER'));
});

async function fixture(t, { legacy = false, parallel = false } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'thread-protocol-')); t.after(() => rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const workspace = join(root, 'workspace'); await mkdir(workspace);
  const store = await new WorkflowStore(join(root, 'packs'), { validationContext: context }).initialize();
  await store.create(definition());
  const runtime = await new WorkflowRuntime({ workflowStore: store, runRoot: join(root, 'runs'), context }).initialize();
  let run = await runtime.start({ workflow_id: 'thread-protocol', workspace, access: 'read_only', main_actor: 'root' });
  if (legacy) {
    // Construct an old immutable journal through the store, never rewrite pins.
    const original = await runtime.runs.read(run.run_id); const pins = structuredClone(original.pins); delete pins.thread_protocol_version;
    if (parallel) pins.root.workflow = definition('parallel');
    const runId = randomUUID();
    const state = initialRunState({ runId, pinsHash: digest(canonicalJSON(pins)), pins, inputs: {}, permissions: original.state.permissions, constraints: {}, controlHash: original.state.control_hash, mainActor: 'root', requireApproval: false });
    advanceRun(state, pins); await runtime.runs.create(runId, pins, new Map(), state);
    run = { ...await runtime.get(runId), control_token: run.control_token };
  }
  const claim = node_id => runtime.claimNode(run.run_id, { node_id, owner: 'root', request_id: 'claim-' + node_id, control_token: run.control_token });
  const intent = lease => runtime.recordDispatchIntent(run.run_id, { ...lease, control_token: run.control_token, request_id: 'dispatch-' + lease.attempt_id, envelope_hash: 'a'.repeat(64) });
  const receipt = (lease, thread_id = 'task') => runtime.recordDispatchReceipt(run.run_id, { ...lease, control_token: run.control_token, request_id: 'dispatch-' + lease.attempt_id, receipt: { thread_id } });
  const complete = (lease, evidence) => runtime.completeNode(run.run_id, { ...lease, completion: { status: 'succeeded', summary: 'Synthetic observed turn', structured_output: {}, artifacts: [], evidence, changed_paths: [], outside_paths: [] } });
  return { runtime, run, claim, intent, receipt, complete };
}
const evidence = (lease, turn_id = 'turn-' + lease.attempt_id) => [{ kind: 'codex_thread', thread_id: 'task', observed: 'completed', dispatch_request_id: 'dispatch-' + lease.attempt_id, turn_id }];

test('new Runs reject old, wrong-dispatch and replayed-turn evidence without committing output', async t => {
  const f = await fixture(t); assert.equal((await f.runtime.runs.read(f.run.run_id)).pins.thread_protocol_version, 2);
  const seed = await f.claim('seed'); await f.intent(seed); await f.receipt(seed);
  await assert.rejects(f.complete(seed, [{ kind: 'codex_thread', thread_id: 'task', observed: 'completed' }]), { code: 'THREAD_TURN_EVIDENCE' });
  await assert.rejects(f.complete(seed, [{ ...evidence(seed)[0], dispatch_request_id: 'other' }]), { code: 'THREAD_TURN_EVIDENCE' });
  await f.complete(seed, evidence(seed));
  const a = await f.claim('a'); await f.intent(a); await f.receipt(a);
  await assert.rejects(f.complete(a, evidence(a, evidence(seed)[0].turn_id)), { code: 'THREAD_TURN_REUSED' });
  assert.equal((await f.runtime.get(f.run.run_id)).nodes.a.output, null);
  await f.complete(a, evidence(a));
});

test('legacy immutable Runs keep old evidence while atomic dispatch guards prevent parallel task turns', async t => {
  const f = await fixture(t, { legacy: true, parallel: true });
  const seed = await f.claim('seed'); await f.intent(seed); await f.receipt(seed);
  await f.complete(seed, [{ kind: 'codex_thread', thread_id: 'task', observed: 'completed' }]);
  const a = await f.claim('a'), b = await f.claim('b');
  const results = await Promise.allSettled([f.intent(a), f.intent(b)]);
  assert.equal(results.filter(r => r.status === 'fulfilled').length, 1);
  assert.equal(results.find(r => r.status === 'rejected').reason.code, 'THREAD_DISPATCH_BUSY');
  const winner = results[0].status === 'fulfilled' ? a : b;
  const loser = winner === a ? b : a;
  assert.equal((await f.runtime.get(f.run.run_id)).nodes[loser.node_id].attempts[0].dispatch, null);
  await f.receipt(winner); await f.complete(winner, evidence(winner));
  await f.intent(loser); await f.receipt(loser);
});

test('task retries require terminal reconciliation and a fresh task identity for start attempts', async t => {
  const f = await fixture(t); const seed = await f.claim('seed'); await f.intent(seed); await f.receipt(seed);
  await f.runtime.failNode(f.run.run_id, { ...seed, error: { message: 'Synthetic collection failure' } });
  const retry = outcome => f.runtime.retryNode(f.run.run_id, { node_id: 'seed', control_token: f.run.control_token, reconciliation: { attempt_id: seed.attempt_id, dispatch_request_id: 'dispatch-' + seed.attempt_id, outcome, evidence: [{ observed: 'host terminal' }] } });
  await assert.rejects(retry('explicit_retry'), { code: 'THREAD_RECONCILIATION_REQUIRED' });
  await retry('terminated');
  const next = await f.runtime.claimNode(f.run.run_id, { node_id: 'seed', owner: 'root', request_id: 'retry-seed', control_token: f.run.control_token });
  await f.intent(next);
  await assert.rejects(f.receipt(next), { code: 'THREAD_IDENTITY_REUSED' });
  await f.receipt(next, 'fresh-task');
});
