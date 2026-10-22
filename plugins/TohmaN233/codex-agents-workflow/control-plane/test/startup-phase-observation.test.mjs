import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { runInNewContext } from 'node:vm';
import { tmpdir } from './physical-tempdir.mjs';
import { readyWorkflow } from './fixtures/workflow-fixtures.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { HostMainManager } from '../lib/execution/host-main-manager.mjs';
import { StrictSessionManager } from '../lib/execution/strict-session-manager.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { loadConfig } from '../lib/config.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { FOREGROUND_PHASES, assertForegroundObservationAuditFits, observeForegroundPhase,
  observeStoreOperation, observeGuardedStoreAction, withForegroundOperationObservation } from '../lib/foreground-operation-observation.mjs';

const gate = () => { let release; const promise = new Promise(done => { release = done; }); return { promise, release }; };
const barrier = () => new Promise(done => setImmediate(done));
const collection = () => { const reports = []; return { reports, run: action => withForegroundOperationObservation(action, report => reports.push(report)) }; };
async function temporary(t) {
  const root = await mkdtemp(join(tmpdir(), 'startup-phase-'));
  t.after(async () => {
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await rm(root, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
  });
  return root;
}

test('actual service #call open retains migration and Role boundaries with fresh checks', async t => {
  const root = await temporary(t), configPath = join(root, 'control-plane.json');
  await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const service = new WorkflowService({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    capabilities: { nativeAgentObserver: null } });
  await service.call('migrate_v6', {}, { human: true });
  const c = collection();
  const roles = await c.run(() => service.call('role_templates'));
  assert(roles.length > 0);
  const report = c.reports[0];
  assert.deepEqual(Object.keys(report.f).sort(), ['hm', 'op', 'pm', 'rp']);
  assert.deepEqual(report.fn, [4, 4, 0]);
  for (const phase of Object.values(report.f)) assert.equal(phase[0], 1);
  assert(report.f.op[1] >= report.f.pm[1] + report.f.hm[1] + report.f.rp[1] - 0.003);
  assertForegroundObservationAuditFits(report);
  await writeFile(configPath, '{');
  const failed = collection();
  await assert.rejects(failed.run(() => service.call('role_templates')), /control-plane config is invalid JSON/);
  assert.deepEqual(Object.keys(failed.reports[0].f), ['op']);
  assert.deepEqual(failed.reports[0].fn, [1, 1, 0]);
});

test('actual Strict qualification rejection is observed before Run creation or launch', async t => {
  const root = await temporary(t), configPath = join(root, 'control-plane.json'), fault = new Error('neutral qualifier failure');
  await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  let qualifications = 0, starts = 0;
  const strictManager=new StrictSessionManager({configPath,getConfig:async()=>({}),env:{},
    qualify:async()=>observeForegroundPhase('q',()=>{qualifications++;throw fault;}),sessionFactory:()=>assert.fail('Qualification must fail before session creation')});
  t.after(()=>strictManager.close());
  const service = new WorkflowService({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {}, capabilities: {nativeAgentObserver:null,strictManager} });
  await service.call('migrate_v6', {}, { human: true });
  const { store } = await service.open(); const pack = await store.create(readyWorkflow('neutral-qualification'));
  const open = service.open.bind(service);
  service.open = async () => { const result = await open(); result.runtime.runs.create = () => { starts++; assert.fail('Run must not be created'); }; return result; };
  const c = collection();
  await assert.rejects(c.run(() => service.call('run_main', { workflow_id: pack.workflow.id, workspace: root,
    access: 'read_only',main_actor:'root', inputs: {}, return_after_start: true })), error => error === fault);
  assert.equal(qualifications, 1); assert.equal(starts, 0);
  assert.deepEqual(Object.keys(c.reports[0].f).sort(), ['hm', 'op', 'pm', 'q', 'rp']);
  assert.deepEqual(c.reports[0].fn, [5, 5, 0]);
});

async function mainFixture(t, faults = {}) {
  const { closeFault, setupFault } = faults;
  const root = await temporary(t), workspace = join(root, 'workspace'); await mkdir(workspace);
  const outputSchema = { type: 'object', properties: { value: { type: 'string' } }, required: ['value'], additionalProperties: false };
  const definition = { id: 'work', type: 'agent', executor: { kind: 'main' }, resources: [], outputs_schema: outputSchema };
  const record = { pins: { root: { workflow: { nodes: [definition] }, resources: [], provenance: { kind: 'fixture' } } },
    state: { main_actor: 'logical-main', nodes: { work: { attempts: [] } } } };
  const envelope = { node_id: 'work', executor: definition.executor, allowed_skills: [], resources: [],
    inputs: {}, access: 'read_only', workspace, effective_allowed_paths: [], constraints: {},
    prompt_template: 'neutral mechanical fixture', outputs_schema: outputSchema };
  const order = [], events = []; let fresh = 0, committed = 0;
  const settings = { enabled: true, codex_binary: process.execPath, binary_sha256: 'b'.repeat(64),
    authentication: { mode: 'managed_chatgpt', api_key_env: '' }, main_model: '', main_reasoning_effort: '', inactivity_timeout_ms: 0 };
  const runtime = { runs: { directory: () => join(root, 'runs'), read: async () => record,
    saveExecutorResult: async () => ({ artifact: 'result.json', sha256: 'a'.repeat(64) }) },
    authorizedExecution: async (_id, auth, select) => ({ record, binding: { ...select(record), ...auth }, envelope }),
    execution: async () => { fresh++; return envelope; }, reserveHostMainTurn: async () => {},
    recordHostMainDispatchReceipt: async () => { order.push('receipt'); },
    recordExecutorEvent: async (_id, args) => { events.push(args.event); }, recordHostMainUsage: async () => {},
    completeHostMainResult: async () => { committed++; } };
  const manager = new HostMainManager({register:async({config})=>config, configPath: join(root, 'config.json'), env: {},
    getConfig: async () => { order.push('config'); return { global: { enabled: true }, strict_executor: settings, providers: [] }; },
    qualify: async function () { assert.equal(this, manager); order.push('qualify'); return settings; },
    mainModelSelection: async () => ({ model: 'fixture-model', effort: 'high' }), sessionFactory: async options => {
      order.push('setup'); assert.equal(fresh, 1); await options.authorize(); await options.resolveModelSelection({});
      if (Object.hasOwn(faults,'setupFault')) throw setupFault;
      return { turn: async text => { order.push('turn'); return { output: '{"value":"done"}', thread_id: 'thread', turn_id: 'turn',
        usage: { available: true }, audit: { input_sha256: digest(canonicalJSON([{ type: 'text', text }])) } }; },
      close: async () => { order.push('close'); options.toolBroker.revoke(); if (Object.hasOwn(faults,'closeFault')) throw closeFault; } };
    } });
  const qualifier = manager.qualify;
  Object.defineProperty(manager, 'qualify', { get() { order.push('qualifier-read'); return qualifier; } });
  const entry = { runtime, runId: 'run', stopping: false, status: 'running' };
  t.after(async () => { entry.broker?.revoke(); await manager.close(); });
  return { order, events, fresh: () => fresh, committed: () => committed,
    execute: () => manager.executeNode(entry, { host_binding: { run_id: 'run', node_id: 'work', attempt_id: 'attempt' },
      agent_packet: { prompt: envelope.prompt_template } }) };
}

test('actual Main qualification, existing session setup/start and close preserve order and fresh checks', async t => {
  const f = await mainFixture(t), c = collection(); await c.run(f.execute);
  assert.deepEqual(Object.keys(c.reports[0].f).sort(), ['cl', 'q', 'ss']);
  assert.deepEqual(c.reports[0].fn, [3, 3, 0]);
  assert.deepEqual(f.order, ['qualifier-read', 'config', 'qualify', 'config', 'setup', 'config', 'receipt', 'config', 'turn', 'close']);
  assert.equal(f.fresh(), 3); assert.equal(f.committed(), 1);
  const running = f.events.find(event => event.kind === 'session_state' && event.metadata.status === 'running');
  assert.deepEqual(Object.keys(JSON.parse(running.metadata.diagnostic).startup_phase_ms).sort(),
    ['authorized_execution', 'materialization', 'receipt_commit', 'snapshot']);
});

test('actual Main setup and closing falsy rejections retain original values without commit', async t => {
  for (const stage of ['setupFault', 'closeFault']) for(const value of [null,undefined,false,0,'']) {
    const f = await mainFixture(t, { [stage]: value }), c = collection(); let caught = false;
    try { await c.run(f.execute); } catch (error) { caught = true; assert.equal(error, value); }
    assert(caught); assert.equal(f.committed(), 0);
    assert.equal(c.reports[0].f[stage === 'setupFault' ? 'ss' : 'cl'][0], 1);
    assert.deepEqual(c.reports[0].fn, stage === 'setupFault' ? [2, 2, 0] : [3, 3, 0]);
  }
});

test('phase wrappers keep exact values, Promise identity, thrown values and falsy rejection identity', async () => {
  for (const value of [null, undefined, false, 0, '', 17]) {
    const c = collection(); assert.equal(await c.run(() => observeForegroundPhase('q', () => value)), value);
    assert.deepEqual(c.reports[0].fn, [1, 1, 0]);
    let thrown = false;
    try { await c.run(() => observeForegroundPhase('q', () => { throw value; })); }
    catch (error) { thrown = true; assert.equal(error, value); }
    assert(thrown);
    const rejected = collection(); let caught = false;
    try { await rejected.run(async () => {
      const original = Promise.reject(value);
      assert.equal(observeForegroundPhase('q', () => original), original); return await original;
    }); } catch (error) { caught = true; assert.equal(error, value); }
    assert(caught); assert.deepEqual(rejected.reports[0].fn, [1, 1, 0]);
  }
});

test('inactive phase helpers do not validate names or inspect returned objects', async () => {
  let gets = 0, calls = 0;
  const object = Object.defineProperty({}, 'then', { get() { gets++; throw new Error('must not inspect'); } });
  assert.equal(observeForegroundPhase('unlisted', () => { calls++; return object; }), object);
  assert.equal(calls, 1); assert.equal(gets, 0);
  const release = gate(), entered = gate(), c = collection(); let work;
  await c.run(async () => { work = (async () => { entered.release(); await release.promise;
    assert.equal(observeForegroundPhase('unlisted', () => object), object); })(); await entered.promise; });
  const snapshot = JSON.stringify(c.reports[0]); release.release(); await work;
  assert.equal(JSON.stringify(c.reports[0]), snapshot); assert.equal(gets, 0); assert.equal(c.reports[0].f, undefined);
});

test('fixed allowlist rejects unknown active phases and retains bounded repeated summaries', async () => {
  assert.deepEqual(FOREGROUND_PHASES, ['op', 'pm', 'hm', 'rp', 'q', 'ss', 'cl', 'ir', 'ib', 'ia']);
  assert(Object.isFrozen(FOREGROUND_PHASES));
  const c = collection(); await c.run(() => { for (let index = 0; index < 150; index++) observeForegroundPhase('pm', () => index); });
  assert.deepEqual(Object.keys(c.reports[0].f), ['pm']); assert.equal(c.reports[0].f.pm[0], 150);
  assert.deepEqual(c.reports[0].fn, [150, 150, 0]);
  await assert.rejects(c.run(() => observeForegroundPhase('unlisted', () => assert.fail('unknown phase body'))), TypeError);
});

test('nested and concurrent ownership observe overlap without causal attribution or another report', async () => {
  const c = collection(), other = collection(), entered = gate(), release = gate();
  const operation = c.run(() => observeForegroundPhase('op', () => withForegroundOperationObservation(async () => {
    const first = observeForegroundPhase('ss', async () => { entered.release(); await release.promise; });
    const second = observeForegroundPhase('ss', () => release.promise);
    const store = observeStoreOperation(mark => { mark('reentrant'); return observeGuardedStoreAction(() => release.promise, mark); });
    await Promise.all([first, second, store]);
  }, () => assert.fail('nested flush'))));
  await entered.promise; await barrier(); await other.run(() => observeForegroundPhase('q', () => 2));
  release.release(); await operation;
  assert.equal(c.reports.length, 1); const report = c.reports[0];
  assert.deepEqual(report.fn, [3, 3, 0]); assert.equal(report.f.ss[0], 2);
  assert(report.f.ss[1] > report.f.ss[2]); assert.equal(report.p.guarded[0], 1);
  assert.equal(report.overlapping_not_additive, true); assert.match(report.unknown, /CPU\/fs/);
  assert.deepEqual(Object.keys(other.reports[0].f), ['q']); assert.notEqual(report.r, other.reports[0].r);
});

test('exotic phase returns remain unobserved without replaying getter, then or species', async () => {
  let gets = 0, calls = 0, species = 0;
  const thenable = Object.defineProperty({}, 'then', { get() { gets++; return done => { calls++; done('value'); }; } });
  class Exotic extends Promise { static get [Symbol.species]() { species++; return Promise; } }
  const foreign = runInNewContext('Promise.resolve("value")');
  for (const original of [thenable, new Exotic(done => done('value')), foreign]) {
    const c = collection(); await c.run(async () => {
      const prior = [gets, calls, species]; assert.equal(observeForegroundPhase('ss', () => original), original);
      assert.deepEqual([gets, calls, species], prior); assert.equal(await original, 'value');
    });
    assert.deepEqual(c.reports[0].fn, [1, 0, 1]); assert.equal(c.reports[0].f.ss[0], 0); assert.equal(c.reports[0].incomplete, true);
  }
  assert.equal(gets, 1); assert.equal(calls, 1); assert.equal(species, 1);
});

test('pending spans snapshot immediately and never mutate the settled audit', async () => {
  const c = collection(), release = gate(); let pending;
  await c.run(() => { pending = observeForegroundPhase('cl', () => release.promise); });
  const snapshot = JSON.stringify(c.reports[0]); assert.deepEqual(c.reports[0].fn, [1, 0, 0]);
  assert.equal(c.reports[0].incomplete, true); release.release(); await pending; await barrier();
  assert.equal(JSON.stringify(c.reports[0]), snapshot);
});

test('direct audit-size guard fails visibly without asserting request settlement or business commit', async () => {
  const c = collection(); await c.run(() => { for (const phase of FOREGROUND_PHASES) observeForegroundPhase(phase, () => 1); });
  const report = c.reports[0]; assertForegroundObservationAuditFits(report);
  assert(JSON.stringify({ ...report, caller: '12345678-1234-4234-8234-123456789012' }).length <= 1000);
  const wide = structuredClone(report); wide.pid = 2147483647; wide.r = Number.MAX_SAFE_INTEGER;
  wide.ms = 1.2345678901234568e+308; wide.n.fill(Number.MAX_SAFE_INTEGER);
  for (const phase of Object.keys(wide.p)) wide.p[phase] = [Number.MAX_SAFE_INTEGER, wide.ms, wide.ms, wide.ms];
  for (const phase of FOREGROUND_PHASES) wide.f[phase] = [1000000, 1000000000000, 1000000000000];
  wide.fn.fill(1000000);
  assert.throws(() => assertForegroundObservationAuditFits(wide), error => {
    assert.equal(error.code, 'FOREGROUND_OBSERVATION_LIMIT');
    assert.deepEqual(Object.keys(error), ['code'], 'A direct size guard has no request or business-effect evidence');
    assert.equal(Object.hasOwn(error, 'committed'), false);
    return true;
  });
  const fault = null; let caught = false;
  try { await withForegroundOperationObservation(() => { throw fault; }, () => assertForegroundObservationAuditFits(wide)); }
  catch (error) { caught = true; assert(error instanceof AggregateError); assert.equal(error.errors[0], fault);
    assert.equal(error.errors[1].code, 'FOREGROUND_OBSERVATION_LIMIT');
    assert.equal(Object.hasOwn(error.errors[1], 'committed'), false); }
  assert(caught);
  let reported = false;
  await assert.rejects(withForegroundOperationObservation(() => {
    for (let index = 0; index <= 1000000; index++) observeForegroundPhase('q', () => 1);
  }, () => { reported = true; }), error => {
    assert.equal(error.code, 'FOREGROUND_OBSERVATION_LIMIT');
    assert.equal(Object.hasOwn(error, 'committed'), false); return true;
  });
  assert.equal(reported, false);
});

test('before-effect request failure retains its exact rejection when phase bounds fail without a commit claim', async () => {
  const original = new Error('validation failed before any business effect');
  let businessEffects = 0, reports = 0, actionFinished = false;
  const action = async () => {
    try {
      for (let index = 0; index <= 1000000; index++) observeForegroundPhase('q', () => 1);
      await Promise.reject(original);
      businessEffects++;
    } finally { actionFinished = true; }
  };
  await assert.rejects(withForegroundOperationObservation(action, () => { reports++; }), error => {
    assert(actionFinished, 'The limit failure is exposed only after original settlement');
    assert(error instanceof AggregateError); assert.equal(error.errors[0], original);
    assert.equal(error.errors[1].code, 'FOREGROUND_OBSERVATION_LIMIT');
    for (const failure of [error, ...error.errors]) assert.equal(Object.hasOwn(failure, 'committed'), false);
    return true;
  });
  assert.equal(businessEffects, 0); assert.equal(reports, 0);
});
