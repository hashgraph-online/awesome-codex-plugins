import assert from 'node:assert/strict';
import { execFile, spawn } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { mkdir, mkdtemp, readFile, writeFile, utimes } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import test from 'node:test';
import { Script } from 'node:vm';

import { loadConfig, saveConfig } from '../lib/config.mjs';
import { ConnectorRegistry } from '../connectors/registry.mjs';
import { GrokAcpConnector, stopOwnedProcess } from '../connectors/grok-acp.mjs';
import { ConnectorTaskStore } from '../connectors/task-store.mjs';
import { AttemptAdmissionRegistry } from '../lib/execution/attempt-admission.mjs';
import { captureWorkspaceSnapshot } from '../connectors/scope-guard.mjs';
import {
  cursorCreateAgentExpression,
  cursorProbeExpression,
} from '../connectors/cursor-profile.mjs';
import { startConnectorSelection } from '../lib/control.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

const execFileAsync = promisify(execFile);
const here = dirname(fileURLToPath(import.meta.url));
const fakeSource = join(here, 'fixtures', 'fake-grok.mjs');

test('Grok startup kill is not a confirmed stop until the owned process exits', async () => {
  const stuck = new EventEmitter(); stuck.exitCode = null; stuck.signalCode = null;
  let kills = 0; stuck.kill = () => { kills++; return true; };
  await assert.rejects(stopOwnedProcess(stuck, 'stuck Grok', 20), { code: 'CONNECTOR_PROCESS_STOP_PENDING' });
  assert.equal(kills, 1);
  const exiting = new EventEmitter(); exiting.exitCode = null; exiting.signalCode = null;
  exiting.kill = () => { queueMicrotask(() => { exiting.exitCode = 0; exiting.emit('exit', 0); }); return true; };
  await stopOwnedProcess(exiting, 'exiting Grok', 20);
});

test('connector startup paused in durable reservation cannot spawn after its Run is revoked', async t => {
  const root = await mkdtemp(join(tmpdir(), 'connector-admission-'));
  t.after(async () => { await import('node:fs/promises').then(({ rm }) => rm(root, { recursive: true, force: true })); });
  const workspace = join(root, 'workspace'); await mkdir(workspace);
  await execFileAsync('git', ['-C', workspace, 'init', '-q']);
  let release; const held = new Promise(resolve => { release = resolve; });
  let entered; const reserved = new Promise(resolve => { entered = resolve; });
  let spawns = 0; const updates = [];
  const connector = new GrokAcpConnector({ configPath: join(root, 'config.json'), env: { GROK_BIN: process.execPath },
    store: { async create() { entered(); await held; return { task_id: 'exact-attempt' }; }, async update(_id, value) { updates.push(value); } },
    spawnImpl: () => { spawns++; throw new Error('revoked connector must not spawn'); } });
  const registry = new AttemptAdmissionRegistry(); const admission = registry.begin('run-a', 'node-a', 'exact-attempt', 'connector');
  const pending = assert.rejects(connector.start({ provider: { id: 'grok', capabilities: { read: true, write: false }, config: { binary_env: 'GROK_BIN' } },
    stage: { read_only: true }, prompt: 'fixture', workspace, taskTypeId: 'fixture', stageId: 'node-a', taskId: 'exact-attempt',
    assertActive: admission.assertActive, signal: admission.controller.signal }), { code: 'ATTEMPT_STOPPED' });
  await reserved; registry.fenceRun('run-a'); release(); await pending;
  assert.equal(spawns, 0);
  assert.equal(updates.at(-1).state, 'failed');
});

test('independent connector stores merge durable task records under the cross-process lock', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'sol-task-store-lock-'));
  t.after(async () => { await import('node:fs/promises').then(({ rm }) => rm(root, { recursive: true, force: true })); });
  const path = join(root, 'connector-tasks.json');
  const first = new ConnectorTaskStore({ statePath: path });
  const second = new ConnectorTaskStore({ statePath: path });
  await Promise.all([first.initialize(), second.initialize()]);
  await first.create({ task_id: 'task-a', state: 'completed', workspace: 'workspace-a' });
  await second.create({ task_id: 'task-b', state: 'completed', workspace: 'workspace-b' });
  const stored = JSON.parse(await readFile(path, 'utf8'));
  assert.deepEqual(stored.tasks.map((task) => task.task_id).sort(), ['task-a', 'task-b']);
  assert.equal((await first.get('task-b')).task_id, 'task-b');
});

test('connector task creation reserves one active workspace atomically', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'sol-task-store-reservation-'));
  t.after(async () => { await import('node:fs/promises').then(({ rm }) => rm(root, { recursive: true, force: true })); });
  const path = join(root, 'connector-tasks.json');
  const first = new ConnectorTaskStore({ statePath: path });
  const second = new ConnectorTaskStore({ statePath: path });
  await first.create({ task_id: 'task-a', workspace: 'same-workspace' });
  await assert.rejects(
    second.create({ task_id: 'task-b', workspace: 'same-workspace' }),
    { code: 'CONNECTOR_BUSY' },
  );
});

test('Cursor profile emits valid browser JavaScript for a Windows workspace', () => {
  const workspace = String.raw`C:\Users\fixture\Documents\repo`;
  for (const expression of [cursorProbeExpression(workspace), cursorCreateAgentExpression(workspace)]) {
    assert.doesNotThrow(() => new Script(`(${expression})`));
  }
});

async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'sol-grok-connector-'));
  const workspace = join(root, 'repo');
  await mkdir(workspace, { recursive: true });
  await execFileAsync('git', ['-C', workspace, 'init', '-q']);
  await execFileAsync('git', ['-C', workspace, 'config', 'user.email', 'fixture@example.test']);
  await execFileAsync('git', ['-C', workspace, 'config', 'user.name', 'Fixture']);
  await writeFile(join(workspace, 'tracked.txt'), 'baseline\n');
  await execFileAsync('git', ['-C', workspace, 'add', 'tracked.txt']);
  await execFileAsync('git', ['-C', workspace, 'commit', '-qm', 'fixture']);
  const configPath = join(root, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const provider = config.providers.find((item) => item.id === 'grok-local');
  provider.enabled = true;
  provider.config.task_timeout_ms = 1000;
  config.task_types.push({
    id: 'connector-readonly-fixture',
    name: 'Connector read-only fixture',
    enabled: true,
    description: 'Connector test task type.',
    route: 'delegate',
    tags: ['fixture'],
    stages: [{
      id: 'implementation', role: 'implementer', provider_id: provider.id,
      access: 'read_only', requires_user_approval: true,
      template: 'Perform {{task}} under {{constraints}}. Verify with {{verification}}.',
    }],
  });
  await saveConfig(config, { configPath });
  const env = { ...process.env, GROK_BIN: fakeSource };
  const spawnImpl = (command, args, options) => {
    assert.equal(command, fakeSource);
    return spawn(process.execPath, [fakeSource, ...args], options);
  };
  const registry = new ConnectorRegistry({ configPath, env, spawnImpl });
  await registry.initialize();
  return { root, workspace, configPath, env, registry };
}

test('read-only scope snapshots never refresh the Git index while inspecting metadata', async () => {
  const fx = await fixture();
  // Invalidate Git's cached stat data without changing the tracked content.
  await utimes(join(fx.workspace, 'tracked.txt'), new Date('2020-01-01'), new Date('2020-01-01'));
  const indexPath = join(fx.workspace, '.git', 'index');
  const before = await readFile(indexPath);
  const snapshot = await captureWorkspaceSnapshot(fx.workspace);
  assert.deepEqual(snapshot.entries, {});
  assert.deepEqual(await readFile(indexPath), before, 'scope observation must not write the index');
});

async function start(fx, task) {
  return startConnectorSelection({
    task_type_id: 'connector-readonly-fixture',
    stage_id: 'implementation',
    task,
    context: 'Fixture evidence only.',
    constraints: 'Read-only. Do not change files.',
    verification: 'Return a bounded result.',
    workspace: fx.workspace,
    user_approved: true,
  }, {
    configPath: fx.configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: fx.env,
    registry: fx.registry,
  });
}

test('built-in Grok connector completes with exact task/session/run identity', async () => {
  const fx = await fixture();
  const started = await start(fx, 'NORMAL');
  assert.ok(['running', 'completed'].includes(started.state));
  assert.match(started.task_id, /^[0-9a-f-]{36}$/);
  assert.equal(started.remote_identity.session_id, '11111111-1111-7111-8111-111111111111');
  assert.match(started.remote_identity.run_id, /^[0-9a-f-]{36}$/);
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'completed', JSON.stringify({ state: done.state, error: done.error, scope: done.scope }));
  assert.equal(done.terminal_evidence.kind, 'acp_prompt_result');
  assert.equal(done.scope.unchanged, true);
  assert.match(done.result.text, /fixture result/);
});

test('observed Grok result does not time out while terminal evidence is being persisted', async () => {
  const fx = await fixture();
  const update = fx.registry.store.update.bind(fx.registry.store);
  let release;
  let entered;
  const persistenceGate = new Promise(resolve => { release = resolve; });
  const reachedTerminal = new Promise(resolve => { entered = resolve; });
  const states = [];
  fx.registry.store.update = async (taskId, fields) => {
    if (fields.state === 'completed') {
      entered();
      await persistenceGate;
    }
    if (fields.state) states.push(fields.state);
    return update(taskId, fields);
  };
  const started = await start(fx, 'NORMAL');
  const reached = await Promise.race([
    reachedTerminal.then(() => true),
    new Promise(resolve => setTimeout(() => resolve(false), 5000)),
  ]);
  try {
    assert.equal(reached, true, 'Fixture never reached terminal persistence');
    await new Promise(resolve => setTimeout(resolve, 1200));
    const pending = await fx.registry.status(started.task_id);
    assert.equal(pending.state, 'running', JSON.stringify({ state: pending.state, error: pending.error }));
    assert.equal(pending.result, null, 'Unpersisted evidence cannot be accepted');
    assert.ok(!states.includes('needs_attention'), JSON.stringify(states));
  } finally {
    release();
    await fx.registry.status(started.task_id, 5000);
  }
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'completed');
  assert.equal(done.scope.unchanged, true);
  assert.equal(done.terminal_evidence.kind, 'acp_prompt_result');
});

test('permission is surfaced and only an exact returned option resumes the run', async () => {
  const fx = await fixture();
  const started = await start(fx, 'ASK_PERMISSION');
  const waiting = await fx.registry.status(started.task_id, 5000);
  assert.equal(waiting.state, 'needs_permission');
  const request = waiting.pending_request;
  await assert.rejects(
    fx.registry.control(started.task_id, {
      action: 'respond_permission', request_id: request.request_id,
      decision: 'select', option_id: 'not-returned',
    }),
    /option_id was not returned/,
  );
  await fx.registry.control(started.task_id, {
    action: 'respond_permission', request_id: request.request_id,
    decision: 'select', option_id: 'allow-once',
  });
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'completed', JSON.stringify(done.error));
  assert.match(done.result.text, /approved fixture result/);
});

test('cancellation is processed while a permission request is still waiting', async () => {
  const fx = await fixture();
  const started = await start(fx, 'ASK_PERMISSION');
  const waiting = await fx.registry.status(started.task_id, 5000);
  assert.equal(waiting.state, 'needs_permission');
  const cancelled = await fx.registry.control(started.task_id, {
    action: 'cancel', confirm: true,
    expected_session_id: started.remote_identity.session_id,
    expected_run_id: started.remote_identity.run_id,
  });
  assert.equal(cancelled.state, 'cancelling');
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'cancelled');
});

test('pending permission persistence failures reject the ACP request and fail the task visibly', async () => {
  const fx = await fixture();
  const originalUpdate = fx.registry.store.update.bind(fx.registry.store);
  fx.registry.store.update = async (taskId, fields) => {
    if (fields.state === 'needs_permission') {
      throw Object.assign(new Error('synthetic pending persistence failure'), { code: 'SYNTHETIC_PENDING_PERSISTENCE' });
    }
    return originalUpdate(taskId, fields);
  };
  const started = await start(fx, 'ASK_PERMISSION');
  const failed = await fx.registry.status(started.task_id, 5000);
  assert.equal(failed.state, 'failed');
  assert.equal(failed.error.code, 'ACP_PROMPT_FAILED');
});

test('pending input persistence failures reject the ACP request and fail the task visibly', async () => {
  const fx = await fixture();
  const originalUpdate = fx.registry.store.update.bind(fx.registry.store);
  fx.registry.store.update = async (taskId, fields) => {
    if (fields.state === 'needs_input') {
      throw Object.assign(new Error('synthetic pending persistence failure'), { code: 'SYNTHETIC_PENDING_PERSISTENCE' });
    }
    return originalUpdate(taskId, fields);
  };
  const started = await start(fx, 'ASK_INPUT');
  const failed = await fx.registry.status(started.task_id, 5000);
  assert.equal(failed.state, 'failed');
  assert.equal(failed.error.code, 'ACP_PROMPT_FAILED');
});


test('input elicitation validates the returned schema before resuming', async () => {
  const fx = await fixture();
  const started = await start(fx, 'ASK_INPUT');
  const waiting = await fx.registry.status(started.task_id, 5000);
  assert.equal(waiting.state, 'needs_input');
  const request = waiting.pending_request;
  await assert.rejects(
    fx.registry.control(started.task_id, {
      action: 'respond_input', request_id: request.request_id,
      decision: 'accept', content: { value: 'fixture', wrong: true },
    }),
    /unknown field: wrong/,
  );
  await fx.registry.control(started.task_id, {
    action: 'respond_input', request_id: request.request_id,
    decision: 'accept', content: { value: 'fixture' },
  });
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'completed');
  assert.match(done.result.text, /approved fixture result/);
});

test('cancel requires exact identity and reaches a confirmed cancelled terminal state', async () => {
  const fx = await fixture();
  const started = await start(fx, 'WAIT_FOR_CANCEL');
  await assert.rejects(
    fx.registry.control(started.task_id, {
      action: 'cancel', confirm: true,
    }),
    /requires the exact expected_session_id and expected_run_id/,
  );
  await assert.rejects(
    fx.registry.control(started.task_id, {
      action: 'cancel', confirm: true, expected_session_id: 'wrong',
      expected_run_id: started.remote_identity.run_id,
    }),
    /expected_session_id does not match/,
  );
  await fx.registry.control(started.task_id, {
    action: 'cancel', confirm: true,
    expected_session_id: started.remote_identity.session_id,
    expected_run_id: started.remote_identity.run_id,
  });
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'cancelled');
  assert.equal(done.terminal_evidence.kind, 'acp_prompt_result');
});

test('timeout is ambiguous and never auto-resubmits', async () => {
  const fx = await fixture();
  const started = await start(fx, 'HANG');
  await new Promise((resolve) => setTimeout(resolve, 1200));
  const timed = await fx.registry.status(started.task_id);
  assert.equal(timed.state, 'needs_attention');
  assert.equal(timed.error.code, 'TIMEOUT_UNCONFIRMED');
  const stored = JSON.parse(await readFile(join(fx.root, 'connector-tasks.json'), 'utf8'));
  assert.equal(stored.tasks.length, 1);
  await fx.registry.control(started.task_id, {
    action: 'abandon', confirm: true, acknowledge_may_still_run: true,
    reason: 'fixture cleanup',
  });
});

test('Grok ACP activity renews the inactivity deadline beyond the original timeout', async () => {
  const fx = await fixture();
  const started = await start(fx, 'ACTIVITY_THEN_COMPLETE');
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'completed', JSON.stringify(done.error));
  assert.match(done.result.text, /active fixture result/);
});

test('Grok inactivity timeout pauses while an exact permission decision is pending', async () => {
  const fx = await fixture();
  const started = await start(fx, 'ASK_PERMISSION');
  const waiting = await fx.registry.status(started.task_id, 5000);
  assert.equal(waiting.state, 'needs_permission');
  assert.equal(waiting.deadline_at, null);
  await new Promise(resolve => setTimeout(resolve, 1200));
  const stillWaiting = await fx.registry.status(started.task_id);
  assert.equal(stillWaiting.state, 'needs_permission');
  await fx.registry.control(started.task_id, {
    action: 'respond_permission', request_id: waiting.pending_request.request_id,
    decision: 'select', option_id: 'allow-once',
  });
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'completed', JSON.stringify(done.error));
});

test('read-only workspace mutation produces scope_violation', async () => {
  const fx = await fixture();
  const started = await start(fx, 'WRITE_FILE');
  const done = await fx.registry.status(started.task_id, 5000);
  assert.equal(done.state, 'scope_violation');
  assert.equal(done.error.code, 'SCOPE_VIOLATION');
  assert.equal(done.result, null);
});

test('credential-shaped stderr is redacted from connector errors', async () => {
  const fx = await fixture();
  const started = await start(fx, 'STDERR_SECRET');
  await new Promise((resolve) => setTimeout(resolve, 250));
  const observed = await fx.registry.status(started.task_id);
  assert.ok(['failed', 'needs_attention'].includes(observed.state));
  const serialized = JSON.stringify(observed);
  assert.doesNotMatch(serialized, /fixture-secret|fixture-token/);
  assert.match(serialized, /\[redacted\]/);
  if (!['completed', 'failed', 'cancelled', 'scope_violation', 'abandoned'].includes(observed.state)) {
    await fx.registry.control(started.task_id, {
      action: 'abandon', confirm: true, acknowledge_may_still_run: true,
      reason: 'fixture cleanup',
    });
  }
});

test('restart changes a nonterminal task to unknown_after_restart without creating a duplicate', async () => {
  const fx = await fixture();
  const started = await start(fx, 'HANG');
  const restarted = new ConnectorRegistry({ configPath: fx.configPath, env: fx.env });
  await restarted.initialize();
  const recovered = await restarted.status(started.task_id);
  assert.equal(recovered.state, 'unknown_after_restart');
  assert.equal(recovered.error.code, 'UNKNOWN_AFTER_RESTART');
  const stored = JSON.parse(await readFile(join(fx.root, 'connector-tasks.json'), 'utf8'));
  assert.equal(stored.tasks.length, 1);
  await fx.registry.control(started.task_id, {
    action: 'abandon', confirm: true, acknowledge_may_still_run: true,
    reason: 'fixture cleanup',
  });
});


test('task persistence stores a prompt digest but not the prompt body', async () => {
  const fx = await fixture();
  const marker = 'PRIVATE_PROMPT_MARKER_7ca6b3';
  const started = await start(fx, `${marker} HANG`);
  const raw = await readFile(join(fx.root, 'connector-tasks.json'), 'utf8');
  assert.doesNotMatch(raw, new RegExp(marker));
  const stored = JSON.parse(raw).tasks[0];
  assert.match(stored.prompt_sha256, /^[0-9a-f]{64}$/);
  await fx.registry.control(started.task_id, {
    action: 'abandon', confirm: true, acknowledge_may_still_run: true,
    reason: 'fixture cleanup',
  });
});


for (const request of ['ASK_PERMISSION', 'ASK_INPUT']) {
  test(`poisoned pending ${request} store still closes owned Grok resources`, { timeout: 6000 }, async t => {
    const fx = await fixture();
    t.after(() => { for (const active of fx.registry.grok.active.values()) { active.intentionalCleanup=true; clearTimeout(active.timeout); active.scopeMonitor?.close(); active.peer?.close(); active.acp?.kill(); active.leader?.kill(); } });
    const update = fx.registry.store.update.bind(fx.registry.store);
    const failure = new Error('synthetic persistent disk failure');
    fx.registry.store.update = async (id, fields) => {
      if (['needs_permission','needs_input'].includes(fields.state)) {
        fx.registry.store.persistenceError = failure;
        throw failure;
      }
      return update(id, fields);
    };
    await start(fx, request).catch(error => assert.match(error.message, /persistent disk failure/));
    const deadline = Date.now()+2000;
    while (fx.registry.grok.active.size && Date.now()<deadline) await new Promise(resolve => setTimeout(resolve, 20));
    assert.equal(fx.registry.grok.active.size, 0, 'owned processes and monitors must close even when store reads/writes fail');
    await assert.rejects(fx.registry.store.initialize(), /persistent disk failure/);
  });
}


test('conditional task update observes the committed state inside the mutation lock', async t => {
  const root = await mkdtemp(join(tmpdir(), 'workflow-conditional-update-'));
  const store = new ConnectorTaskStore({ statePath: join(root, 'tasks.json') });
  await store.create({ task_id: 'conditional', state: 'running' });
  const completion = store.update('conditional', { state: 'completed' });
  const staleTimeout = store.update('conditional', { state: 'needs_attention' }, {
    guard: current => current.state === 'running',
  });
  await Promise.all([completion, staleTimeout]);
  assert.equal((await store.get('conditional')).state, 'completed');
});


test('Grok deliberate disconnect keeps the workspace reserved after prompt rejection settles', async () => {
  const fx = await fixture();
  const started = await start(fx, 'ASK_PERMISSION');
  await fx.registry.status(started.task_id, 5000);
  await fx.registry.control(started.task_id, { action: 'disconnect', confirm: true });
  await new Promise(resolve => setTimeout(resolve, 100));
  const task = await fx.registry.status(started.task_id);
  assert.equal(task.state, 'needs_attention');
  assert.equal(task.error.code, 'DISCONNECTED_UNCONFIRMED');
  assert.equal((await fx.registry.store.activeForWorkspace(task.workspace)).length, 1);
  await assert.rejects(fx.registry.store.create({ workspace: task.workspace }), { code: 'CONNECTOR_BUSY' });
});


test('Grok unexpected ACP stream loss does not certify remote failure or release workspace', { timeout: 10000 }, async () => {
  const fx = await fixture();
  const started = await start(fx, 'ASK_PERMISSION');
  await fx.registry.status(started.task_id, 5000);
  const update = fx.registry.store.update.bind(fx.registry.store);
  let settled;
  const persisted = new Promise(resolve => { settled = resolve; });
  fx.registry.store.update = async (id, fields, options) => {
    const task = await update(id, fields, options);
    if (fields.error?.code === 'ACP_TERMINAL_UNCONFIRMED') settled();
    return task;
  };
  fx.registry.grok.active.get(started.task_id).peer.close(new Error('simulated stream loss'));
  await persisted;
  const task = await fx.registry.status(started.task_id);
  assert.equal(task.state, 'needs_attention');
  assert.equal(task.error.code, 'ACP_TERMINAL_UNCONFIRMED');
  assert.equal((await fx.registry.store.activeForWorkspace(task.workspace)).length, 1);
  await assert.rejects(fx.registry.store.create({ workspace: task.workspace }), { code: 'CONNECTOR_BUSY' });
});
