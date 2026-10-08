import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { mkdtemp, mkdir, readFile, rm, symlink, writeFile, lstat, unlink } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { WorkflowRunStore } from '../lib/workflow-run-store.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { interruptActiveNodes } from '../lib/workflow-state.mjs';

async function fixture(t) {
  const parent = await mkdtemp(join(tmpdir(), 'workflow-run-history-'));
  const relativeTemp = relative(resolve(tmpdir()), resolve(parent));
  assert(relativeTemp && relativeTemp !== '..' && !relativeTemp.startsWith(`..${sep}`) && !isAbsolute(relativeTemp));
  t.after(() => rm(parent, { recursive: true, maxRetries: 3, retryDelay: 100 }));
  const root = join(parent, 'runs'); await mkdir(root);
  const workspace = join(parent, 'workspace'); await mkdir(workspace);
  await writeFile(join(workspace, 'product.txt'), 'preserve this workspace file');
  const store = await new WorkflowRunStore(root).initialize();
  return { parent, root, store, workspace };
}

async function addRun(store, id, {
  status = 'succeeded',
  created_at = '2026-01-01T00:00:00.000Z',
  updated_at = created_at,
  finished_at,
  nodes = {},
  parallel = {},
  pins: pinChanges = {},
  state: stateChanges = {},
} = {}) {
  const pins = { resources: [], root: { workflow: { id: 'flow', nodes: [], edges: [] } }, ...pinChanges };
  const state = {
    schema_version: 1, run_id: id, workflow_id: 'flow', status,
    pins_hash: digest(canonicalJSON(pins)), created_at, updated_at,
    ...(finished_at === undefined ? {} : { finished_at }), nodes, parallel, ...stateChanges,
  };
  await store.create(id, pins, new Map(), state);
  return state;
}

function childRunId(parentId, nodeId, attemptId) {
  return `child-${digest([parentId, nodeId, attemptId].join('\0')).slice(0, 58)}`;
}

function latch() {
  let release;
  const promise = new Promise(resolve => { release = resolve; });
  return { promise, release };
}

test('history preserves exact pending child intent before its directory exists', async t => {
  const { store } = await fixture(t);
  for (const status of ['running', 'failed']) {
    const id = `pending-${status}`, attemptId = `${status}-attempt`;
    await addRun(store, id, { status, nodes: { child: { status, attempts: [{ id: attemptId, status,
      child_run_id: childRunId(id, 'child', attemptId),
      dispatch: { request_id: `subworkflow-${attemptId}`, phase: 'intent', receipt: null },
    }] } } });
  }
  assert.deepEqual((await store.cleanupHistory({ olderThanMs: 0 })).preserved_run_ids, ['pending-failed', 'pending-running']);
  await addRun(store, 'unrelated-start', { status: 'running' });
  assert.equal((await store.list()).length, 3);
});

test('history and list queued during child creation do not invert root and Run locks', { timeout: 10000 }, async t => {
  const { store } = await fixture(t);
  await addRun(store, 'creating-parent', { status: 'running' });
  const entered = latch(), proceed = latch();
  const creating = store.mutate('creating-parent', 'fixture-child', async () => {
    entered.release(); await proceed.promise;
    await addRun(store, 'creating-child', { status: 'running' });
    await store.read('creating-child');
  });
  await entered.promise;
  const cleanup = store.cleanupHistory({ olderThanMs: 0 });
  const listing = store.list();
  proceed.release();
  const [, result, rows] = await Promise.all([creating, cleanup, listing]);
  assert.equal(result.preserved_count, 2); assert.equal(rows.length, 2);
});

test('opposing parent and child journal reads remain live across store instances', { timeout: 10000 }, async t => {
  const { store, root } = await fixture(t);
  await addRun(store, 'opposing-parent', { status: 'running' });
  await addRun(store, 'opposing-child', { status: 'running' });
  const secondStore = new WorkflowRunStore(process.platform === 'win32' ? root.toUpperCase() : root), entered = latch(), proceed = latch();
  const parent = store.mutate('opposing-parent', 'fixture-parent', async () => {
    entered.release(); await proceed.promise;
    await secondStore.read('opposing-parent');
    await store.read('opposing-child');
  });
  await entered.promise;
  const child = secondStore.mutate('opposing-child', 'fixture-child', async () => secondStore.read('opposing-parent'));
  proceed.release();
  await Promise.all([parent, child]);
});

test('purge queued during nested creation completes and rejected admission releases the queue', { timeout: 10000 }, async t => {
  const { store } = await fixture(t);
  await addRun(store, 'purge-parent', { status: 'running' });
  const root = { workflow: { id: 'flow', nodes: [], edges: [] }, revision_hash: 'revision',
    provenance: { kind: 'authoring_workflow_run', source_workflow_id: 'source', source_revision: 'source-revision' } };
  await addRun(store, 'purge-old', { pins: { root } });
  const entered = latch(), proceed = latch();
  const creating = store.mutate('purge-parent', 'fixture-create', async () => {
    entered.release(); await proceed.promise; await addRun(store, 'purge-child', { status: 'running' });
  });
  await entered.promise;
  const purge = store.purge('purge-old', { expected_workflow_id: 'flow', expected_revision: 'revision',
    expected_source_workflow_id: 'source', expected_source_revision: 'source-revision' });
  proceed.release();
  const [, result] = await Promise.all([creating, purge]); assert.equal(result.purged, true);
  await assert.rejects(store.mutate('purge-parent', 'fixture-failure', () => { throw new Error('visible failure'); }), /visible failure/);
  assert.equal((await store.list()).length, 2);
});

test('detached continuations cannot reuse expired store admission or bypass queued work', { timeout: 10000 }, async t => {
  const { store } = await fixture(t);
  await addRun(store, 'admission', { status: 'running' });
  const launch = latch(), queuedEntered = latch(), queuedProceed = latch();
  let detached;
  await store.mutate('admission', 'fixture-admission', async () => {
    detached = launch.promise.then(() => store.read('admission'));
  });
  const queued = store.mutate('admission', 'fixture-queued', async () => {
    queuedEntered.release(); await queuedProceed.promise;
  });
  await queuedEntered.promise;
  launch.release(); queuedProceed.release();
  await Promise.all([queued, detached]);
});

test('a detached read cannot reuse an expired Run writer to bypass an external guard', async t => {
  const { store } = await fixture(t);
  await addRun(store, 'expired-writer', { status: 'running' });
  const launch = latch(); let detached;
  await store.mutate('expired-writer', 'fixture-writer', async () => {
    detached = launch.promise.then(() => store.read('expired-writer'));
  });
  const externalGuard = join(store.runLockDirectory('expired-writer'), '.writer.lock');
  await writeFile(externalGuard, JSON.stringify({ pid: process.pid, token: randomUUID() }));
  try {
    launch.release();
    await assert.rejects(detached, { code: 'WORKFLOW_STORE_BUSY' });
  } finally { await unlink(externalGuard); }
  await store.read('expired-writer');
});

async function addLinkedChildRun(store, parentId, {
  parentStatus = 'failed', parentUpdatedAt = '2020-01-01T00:00:00.000Z', childStatus = 'failed',
} = {}) {
  const childId = childRunId(parentId, 'child', 'child-attempt');
  const parent = await addRun(store, parentId, { status: parentStatus, updated_at: parentUpdatedAt, nodes: {
    child: { status: 'failed', active_attempt_id: null, attempts: [{ id: 'child-attempt', status: 'failed', child_run_id: childId }] },
  } });
  await addRun(store, childId, { status: childStatus, pins: {
    parent: { run_id: parentId, node_id: 'child', attempt_id: 'child-attempt', pins_hash: parent.pins_hash }, child_run_id: childId,
  } });
  return childId;
}

test('retention removes old succeeded and failed Runs, keeps the exact age boundary and lists timestamps', async t => {
  const { store } = await fixture(t);
  const now = Date.parse('2026-10-01T12:00:00.000Z'); const age = 24 * 60 * 60 * 1000;
  const old = new Date(now - age - 1).toISOString(); const boundary = new Date(now - age).toISOString();
  await addRun(store, 'old-success', { created_at: old, updated_at: new Date(now).toISOString(), finished_at: old });
  await addRun(store, 'old-failure', { status: 'failed', created_at: old, updated_at: old });
  await addRun(store, 'age-boundary', { created_at: boundary, updated_at: boundary });
  await addRun(store, 'fresh-success', { created_at: new Date(now - 1).toISOString(), updated_at: new Date(now - 1).toISOString() });

  const freshSummary = (await store.list()).find(item => item.run_id === 'fresh-success');
  assert.deepEqual({ created_at: freshSummary.created_at, updated_at: freshSummary.updated_at },
    { created_at: new Date(now - 1).toISOString(), updated_at: new Date(now - 1).toISOString() });

  const result = await store.cleanupHistory({ olderThanMs: age, now });
  assert.equal(result.examined, 4);
  assert.deepEqual(result.deleted_run_ids, ['old-failure', 'old-success']);
  assert.equal(result.deleted_count, 2);
  assert.deepEqual(result.preserved_run_ids, ['age-boundary', 'fresh-success']);
  assert.equal(result.preserved_count, 2);
});

test('retention preserves every noneligible Run status and unsettled execution state', async t => {
  const { store } = await fixture(t);
  for (const status of ['running', 'paused', 'blocked', 'interrupted', 'cancelled'])
    await addRun(store, `status-${status}`, { status });
  await addRun(store, 'active-attempt', { status: 'failed', nodes: {
    work: { status: 'failed', active_attempt_id: 'attempt-a', attempts: [{ id: 'attempt-a', status: 'running' }] },
  } });
  await addRun(store, 'pending-cancel', { status: 'succeeded', nodes: {
    work: { status: 'cancelled', active_attempt_id: null, attempts: [{ id: 'attempt-b', status: 'cancelled', dispatch: { phase: 'acknowledged', receipt: { task_id: 'task-b' }, cancellation_pending: true } }] },
  } });
  await addRun(store, 'dispatch-intent', { status: 'failed', nodes: {
    work: { status: 'failed', active_attempt_id: null, attempts: [{ id: 'attempt-c', status: 'failed', dispatch: { phase: 'intent', receipt: null, cancellation_pending: false } }] },
  } });
  await addRun(store, 'interrupted-dispatch', { status: 'failed', nodes: {
    work: { status: 'interrupted', active_attempt_id: 'attempt-d', attempts: [{ id: 'attempt-d', status: 'interrupted',
      dispatch: { phase: 'acknowledged', receipt: { task_id: 'task-d' }, cancellation_pending: false } }] },
  } });

  const result = await store.cleanupHistory({ olderThanMs: 0 });
  assert.deepEqual(result.deleted_run_ids, []);
  assert.equal(result.preserved_count, 9);
  assert.equal((await store.list()).length, 9);
});

test('retention preserves a terminal parent while a child Run is live', async t => {
  const { store } = await fixture(t);
  const childId = childRunId('parent-run', 'child', 'child-attempt');
  const parent = await addRun(store, 'parent-run', { status: 'failed', nodes: {
    child: { status: 'failed', active_attempt_id: null, attempts: [{ id: 'child-attempt', status: 'failed', child_run_id: childId }] },
  } });
  await addRun(store, childId, { status: 'running', pins: {
    parent: { run_id: 'parent-run', node_id: 'child', attempt_id: 'child-attempt', pins_hash: parent.pins_hash }, child_run_id: childId,
  } });

  const result = await store.cleanupHistory({ olderThanMs: 0 });
  assert.deepEqual(result.deleted_run_ids, []);
  assert.deepEqual(result.preserved_run_ids, [childId, 'parent-run'].sort());
});

test('retention preserves exact pending SubWorkflow lineage while child creation is in flight', async t => {
  const { store } = await fixture(t);
  const parentId = 'pending-parent'; const nodeId = 'child'; const attemptId = 'pending-attempt';
  const childId = `child-${digest([parentId, nodeId, attemptId].join('\0')).slice(0, 58)}`;
  const parent = await addRun(store, parentId, { status: 'running', nodes: {
    [nodeId]: { status: 'running', active_attempt_id: attemptId, attempts: [{ id: attemptId, status: 'running',
      dispatch: { request_id: `subworkflow-${attemptId}`, phase: 'intent', receipt: null, cancellation_pending: false } }] },
  } });
  await addRun(store, childId, { status: 'running', pins: {
    parent: { run_id: parentId, node_id: nodeId, attempt_id: attemptId, pins_hash: parent.pins_hash }, child_run_id: childId,
  } });

  const result = await store.cleanupHistory({ olderThanMs: 0 });
  assert.deepEqual(result.deleted_run_ids, []);
  assert.deepEqual(result.preserved_run_ids, [childId, parentId].sort());
});

test('retention rejects an acknowledged SubWorkflow receipt that names another child', async t => {
  const { store } = await fixture(t);
  const parentId = 'ack-parent'; const attemptId = 'ack-attempt'; const childId = childRunId(parentId, 'child', attemptId);
  const parent = await addRun(store, parentId, { status: 'failed', nodes: {
    child: { status: 'failed', active_attempt_id: null, attempts: [{ id: attemptId, status: 'failed', child_run_id: childId,
      dispatch: { request_id: `subworkflow-${attemptId}`, phase: 'acknowledged', receipt: { child_run_id: 'different-child' }, cancellation_pending: false } }] },
  } });
  await addRun(store, childId, { status: 'failed', pins: {
    parent: { run_id: parentId, node_id: 'child', attempt_id: attemptId, pins_hash: parent.pins_hash }, child_run_id: childId,
  } });

  await assert.rejects(store.cleanupHistory({ olderThanMs: 0 }), { code: 'RUN_HISTORY_CHILD_IDENTITY' });
  await lstat(join(store.root, `run-${parentId}.run`));
  await lstat(join(store.root, `run-${childId}.run`));
});

test('retention removes an eligible linked parent and child as one family when child sorts first', async t => {
  const { store } = await fixture(t);
  const parentId = 'z-parent-old'; const childId = await addLinkedChildRun(store, parentId);

  const result = await store.cleanupHistory({ olderThanMs: 0 });
  assert.deepEqual(result.deleted_run_ids, [childId, parentId].sort());
  assert.equal(result.deleted_count, 2);
  await assert.rejects(lstat(join(store.root, `run-${childId}.run`)), { code: 'ENOENT' });
  await assert.rejects(lstat(join(store.root, `run-${parentId}.run`)), { code: 'ENOENT' });
});

test('retention keeps an old child when its linked parent is interrupted or recent', async t => {
  const { store } = await fixture(t);
  const now = Date.parse('2026-10-01T12:00:00.000Z');
  const interruptedChild = await addLinkedChildRun(store, 'z-parent-interrupted', { parentStatus: 'interrupted' });
  const recentChild = await addLinkedChildRun(store, 'z-parent-recent', {
    parentStatus: 'failed', parentUpdatedAt: new Date(now - 1).toISOString(),
  });

  const result = await store.cleanupHistory({ olderThanMs: 24 * 60 * 60 * 1000, now });
  assert.deepEqual(result.deleted_run_ids, []);
  assert.deepEqual(result.preserved_run_ids, [interruptedChild, recentChild, 'z-parent-interrupted', 'z-parent-recent'].sort());
});

test('retention reports a missing linked child instead of treating it as safe', async t => {
  const { store } = await fixture(t);
  await addRun(store, 'missing-child-parent', { status: 'failed', nodes: {
    child: { status: 'failed', active_attempt_id: null, attempts: [{ id: 'child-attempt', status: 'failed', child_run_id: 'missing-child' }] },
  } });

  await assert.rejects(store.cleanupHistory({ olderThanMs: 0 }), { code: 'RUN_HISTORY_CHILD_MISSING', child_run_id: 'missing-child' });
  await lstat(join(store.root, 'run-missing-child-parent.run'));
});

test('a failed Run can be removed after its interrupted sibling work is reconciled', async t => {
  const { store } = await fixture(t);
  const id = 'quiesced-failure';
  const pins = { resources: [], root: { workflow: { id: 'flow', nodes: [], edges: [] } } };
  const state = {
    schema_version: 1, run_id: id, workflow_id: 'flow', status: 'running',
    pins_hash: digest(canonicalJSON(pins)), created_at: '2020-01-01T00:00:00.000Z', updated_at: '2020-01-01T00:00:00.000Z',
    nodes: {
      failed: { status: 'failed', active_attempt_id: null, attempts: [] },
      sibling: { status: 'running', active_attempt_id: 'sibling-attempt', attempts: [{
        id: 'sibling-attempt', status: 'running', dispatch: { request_id: 'dispatch-sibling', phase: 'acknowledged', receipt: { task_id: 'task-sibling' }, cancellation_pending: false },
        reconciliation: { attempt_id: 'sibling-attempt', dispatch_request_id: 'dispatch-sibling', outcome: 'terminated', evidence: [{ kind: 'host_quiescence', confirmed: true }] },
      }] },
    },
  };
  state.control_recovery = { errors: [{ code: 'ORIGIN_RECOVERY_REQUIRED', message: 'Historical origin cleanup diagnostic' }] };
  interruptActiveNodes(state, 'A sibling failed and the execution coordinator drained this attempt');
  state.status = 'failed';
  await store.create(id, pins, new Map(), state);

  const result = await store.cleanupHistory({ olderThanMs: 0 });
  assert.deepEqual(result.deleted_run_ids, [id]);
  await assert.rejects(lstat(join(store.root, `run-${id}.run`)), { code: 'ENOENT' });
});

test('manual cleanup clears fresh eligible terminal history and preserves workspace files', async t => {
  const { root, store, workspace } = await fixture(t);
  await addRun(store, 'fresh-success', { created_at: '2026-10-01T12:00:00.000Z', updated_at: '2026-10-01T12:00:00.000Z' });
  await addRun(store, 'fresh-failure', { status: 'failed', created_at: '2026-10-01T12:00:00.000Z', updated_at: '2026-10-01T12:00:00.000Z' });
  await addRun(store, 'keep-cancelled', { status: 'cancelled', created_at: '2020-01-01T00:00:00.000Z', updated_at: '2020-01-01T00:00:00.000Z' });

  const result = await store.cleanupHistory({ olderThanMs: 0 });
  assert.deepEqual(result.deleted_run_ids, ['fresh-failure', 'fresh-success']);
  assert.deepEqual(result.preserved_run_ids, ['keep-cancelled']);
  await assert.rejects(lstat(join(root, 'run-fresh-success.run')), { code: 'ENOENT' });
  assert.equal(await readFile(join(workspace, 'product.txt'), 'utf8'), 'preserve this workspace file');
});

test('concurrent mutations cannot restore a directory deleted by history cleanup', async t => {
  const { root, store } = await fixture(t);
  await addRun(store, 'race-run');
  const peer = await new WorkflowRunStore(root).initialize();

  const [cleanup, mutation, resultWrite] = await Promise.allSettled([
    store.cleanupHistory({ olderThanMs: 0 }),
    peer.mutate('race-run', 'control_recovery', state => { state.control_recovery = { errors: [] }; }),
    peer.saveExecutorResult('race-run', 'attempt-a', { completed: true }),
  ]);
  assert.equal(cleanup.status, 'fulfilled');
  assert.deepEqual(cleanup.value.deleted_run_ids, ['race-run']);
  if (mutation.status === 'rejected') assert.equal(mutation.reason.code, 'ENOENT');
  if (resultWrite.status === 'rejected') assert.equal(resultWrite.reason.code, 'ENOENT');
  await assert.rejects(peer.mutate('race-run', 'control_recovery', state => { state.control_recovery = { errors: [] }; }), { code: 'ENOENT' });
  await assert.rejects(peer.saveExecutorResult('race-run', 'attempt-a', { completed: true }), { code: 'ENOENT' });
  await assert.rejects(peer.read('race-run'), { code: 'ENOENT' });
  assert.deepEqual(await peer.list(), []);
  await assert.rejects(lstat(join(root, 'run-race-run.run')), { code: 'ENOENT' });
  await lstat(join(root, '.run-locks', 'run-race-run'));
});

test('history cleanup fails closed on symlinks inside an exact Run directory', async t => {
  const { root, store, workspace } = await fixture(t);
  await addRun(store, 'linked-run');
  const target = join(root, 'run-linked-run.run', 'linked-workspace');
  await symlink(workspace, target, process.platform === 'win32' ? 'junction' : 'dir');

  await assert.rejects(store.cleanupHistory({ olderThanMs: 0 }), { code: 'WORKFLOW_SYMLINK' });
  await lstat(join(root, 'run-linked-run.run'));
  await lstat(join(workspace, 'product.txt'));
});


test('a failed Run with a durably closed interrupted Main session is eligible', async t => {
  const {store}=await fixture(t);
  await addRun(store,'closed-main-failure',{status:'failed',pins:{root:{workflow:{id:'flow',nodes:[{id:'worker',type:'agent',executor:{kind:'main'}}],edges:[]}}},nodes:{
    worker:{status:'interrupted',active_attempt_id:'worker-attempt',attempts:[{
      id:'worker-attempt',status:'interrupted',dispatch:{phase:'acknowledged',receipt:{executor:'codex-app-server-host-main'},cancellation_pending:false},
      executor_events:[{kind:'session_state',metadata:{status:'closed'}}]
    }]}
  }});
  assert.deepEqual((await store.cleanupHistory({olderThanMs:0})).deleted_run_ids,['closed-main-failure']);
});


test('a failed parent may clear its settled cancelled child while standalone cancelled Runs remain',async t=>{
  const {store}=await fixture(t);
  const child=await addLinkedChildRun(store,'failed-parent-with-cancelled-child',{childStatus:'cancelled'});
  await addRun(store,'standalone-cancelled',{status:'cancelled'});
  const result=await store.cleanupHistory({olderThanMs:0});
  assert.deepEqual(result.deleted_run_ids,[child,'failed-parent-with-cancelled-child'].sort());
  assert.deepEqual(result.preserved_run_ids,['standalone-cancelled']);
});
