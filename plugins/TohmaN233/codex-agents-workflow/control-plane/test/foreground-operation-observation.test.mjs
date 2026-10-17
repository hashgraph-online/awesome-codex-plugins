import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile, readFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowRunStore } from '../lib/workflow-run-store.mjs';
import { WorkflowStore, withRunAdmissionObserver } from '../lib/workflow-store.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { observeStoreOperation, observeGuardedStoreAction, withForegroundOperationObservation } from '../lib/foreground-operation-observation.mjs';
import { handleRpc } from '../server.mjs';
import { runInNewContext } from 'node:vm';

const gate = () => { let release; const promise = new Promise(resolve => { release = resolve; }); return { promise, release }; };
const dispatchBarrier = () => new Promise(resolve => setImmediate(resolve));
async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'foreground-observation-'));
  t.after(() => rm(root, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 }));
  const store = await new WorkflowRunStore(join(root, 'runs')).initialize();
  const pins = { resources: [], root: { workflow: { nodes: [] } } };
  for (const id of ['parent', 'child']) await store.create(id, pins, new Map(),
    { run_id: id, pins_hash: digest(canonicalJSON(pins)), status: 'running', nodes: {} });
  return { root, store, admission: join(store.root, '.run-locks', '.store-operation') };
}
function collector() { const reports = []; return { reports, run: action => withForegroundOperationObservation(action, report => reports.push(report)) }; }
function assertComplete(report) {
  assert.equal(report.incomplete, false); assert.equal(report.n[4], 0); assert.equal(report.n[6], 0);
  assert.equal(report.overlapping_not_additive, true); assert(JSON.stringify(report).length <= 1000);
  assert.equal(report.p.fifo[0], 1); assert.equal(report.p.setup[0], 1); assert.equal(report.p.admission[0], 1);
}

test('a public read measures held local FIFO separately from admitted work', { timeout: 10000 }, async t => {
  const f = await fixture(t), entered = gate(), release = gate(), c = collector();
  const prior = f.store.withRunWriter('parent', async () => { entered.release(); await release.promise; });
  await entered.promise;
  const original = f.store.withRunGuard.bind(f.store); let childGuards = 0;
  f.store.withRunGuard = (id, action) => { if (id === 'child') childGuards++; return original(id, action); };
  const observed = c.run(() => f.store.read('child')), heldAt = performance.now();
  await dispatchBarrier(); assert.equal(childGuards, 0);
  const releasedAt = performance.now(); release.release();
  await prior; assert.equal((await observed).state.run_id, 'child');
  const [report] = c.reports; assertComplete(report); assert.equal(childGuards, 1);
  assert(report.p.fifo[2] >= releasedAt - heldAt - 0.005);
  assert.equal(report.p.fifo[1], report.p.fifo[3]);
});

test('a public read measures original global admission and preserves its observer', { timeout: 10000 }, async t => {
  const f = await fixture(t), entered = gate(), release = gate(), waiting = gate(), c = collector();
  const prior = new WorkflowStore(f.admission).withRunAdmission(async () => { entered.release(); await release.promise; });
  await entered.promise;
  const phases = [];
  const observed = c.run(() => withRunAdmissionObserver({ admissionRoot: f.admission, onWait: detail => {
    phases.push(detail.phase); if (detail.phase === 'waiting') waiting.release();
  } }, () => f.store.read('child')));
  await waiting.promise; const heldAt = performance.now(); await dispatchBarrier();
  const releasedAt = performance.now(); release.release();
  await prior; await observed;
  const [report] = c.reports; assertComplete(report);
  assert.deepEqual(phases, ['waiting', 'acquired']);
  assert(report.p.admission[2] >= releasedAt - heldAt - 0.005);
  assert.match(report.basis, /setup\/queue\/observers/);
});

test('a public read measures held guarded action and its overlapping reentrant guard', { timeout: 10000 }, async t => {
  const f = await fixture(t), entered = gate(), release = gate(), c = collector();
  const original = f.store.withRunGuard.bind(f.store); let calls = 0;
  f.store.withRunGuard = (id, action) => original(id, async () => { calls++; entered.release(); await release.promise; return action(); });
  const observed = c.run(() => f.store.read('child'));
  await entered.promise; const heldAt = performance.now(); await dispatchBarrier();
  const releasedAt = performance.now(); release.release(); await observed;
  const [report] = c.reports; assertComplete(report); assert.equal(calls, 1);
  assert.equal(report.n[3], 1); assert.equal(report.p.guarded[0], 2);
  assert(report.p.guarded[2] >= releasedAt - heldAt - 0.005);
  assert(report.p.guarded[1] > report.p.guarded[3]);
  assert(report.p.retirement[0] === 1);
});

test('profiled original admission-observer rejection keeps its exact error and failed prefix', { timeout: 10000 }, async t => {
  const f = await fixture(t), entered = gate(), release = gate(), c = collector(), fault = new Error('private observer fault');
  const holder = new WorkflowStore(f.admission).withRunAdmission(async () => { entered.release(); await release.promise; });
  await entered.promise; let callbacks = 0;
  try {
    await assert.rejects(c.run(() => withRunAdmissionObserver({ admissionRoot: f.admission,
      onWait: () => { callbacks++; throw fault; } }, () => f.store.read('child'))), error => error === fault);
  } finally { release.release(); await holder; }
  assert.equal(callbacks, 1); const [report] = c.reports;
  assert.equal(report.p.admission[0], 1); assert.equal(report.p.guarded[0], 0); assert.equal(report.n[2], 1);
  assert.equal(report.p.admission[1], report.p.admission[3]); assert.match(report.basis, /failed-prefix/);
  assert.equal(await new WorkflowStore(f.admission).inspectWriter(), null);
});

test('original failures and reentrant ownership survive one outer report', async t => {
  const f = await fixture(t), c = collector(), fault = new Error('private original body'); let calls = 0;
  await assert.rejects(c.run(() => f.store.withRunWriter('parent', async () => {
    calls++; await f.store.read('parent');
    await withForegroundOperationObservation(() => f.store.read('child'), () => assert.fail('nested report'));
    throw fault;
  })), error => error === fault);
  assert.equal(calls, 1); assert.equal(c.reports.length, 1); assertComplete(c.reports[0]);
  assert(c.reports[0].n[2] > 0); assert(c.reports[0].n[3] > 0);
  assert.equal(JSON.stringify(c.reports).includes('private original body'), false);
  assert.equal(await new WorkflowStore(f.admission).inspectWriter(), null);
  assert.equal((await f.store.read('child')).state.run_id, 'child');
});

test('public corruption and cancellation remain failures, with no diagnostic authority', async t => {
  const f = await fixture(t), c = collector();
  await writeFile(join(f.store.directory('parent'), 'pins.json'), '{}');
  await assert.rejects(c.run(() => f.store.read('parent')), { code: 'RUN_PINS_CORRUPT' });
  const controller = new AbortController(); controller.abort();
  await assert.rejects(c.run(() => f.store.cleanupHistory({ signal: controller.signal })), { code: 'RUN_HISTORY_CANCELLED' });
  assert.equal(c.reports.length, 2); assert(c.reports[0].n[2] > 0); assert.equal(c.reports[1].n[0], 0);
  assert.equal(await new WorkflowStore(f.admission).inspectWriter(), null);
});

test('bounded samples preserve complete counters and flag partial interval unions', async () => {
  const c = collector(), value = { original: true };
  const result = await c.run(async () => {
    for (let index = 0; index < 150; index++) {
      const original = Promise.resolve(value);
      assert.equal(observeStoreOperation(mark => { mark('reentrant'); return observeGuardedStoreAction(() => original, mark); }), original);
      await original;
    }
    return value;
  });
  assert.equal(result, value); const [report] = c.reports;
  assert.deepEqual(report.n, [150, 150, 0, 150, 0, 128, 22, 0]); assert.equal(report.incomplete, true);
  assert.equal(report.p.guarded[0], 150); assert(report.p.guarded[1] >= report.p.guarded[3]);
  assert(JSON.stringify(report).length <= 1000); assert.equal(report.operations, undefined);
  // Even extreme positive metrics fit the unchanged audit-detail budget.
  const wide = structuredClone(report); wide.pid = 2147483647; wide.r = Number.MAX_SAFE_INTEGER;
  wide.caller = '12345678-1234-4234-8234-123456789012';
  wide.ms = 1.2345678901234568e+308; wide.n = wide.n.map(() => Number.MAX_SAFE_INTEGER);
  for (const key of Object.keys(wide.p)) wide.p[key] = [Number.MAX_SAFE_INTEGER, wide.ms, wide.ms, wide.ms];
  assert(JSON.stringify(wide).length <= 1000);
});

test('pending original work is snapshotted without waiting, cancellation or scope leakage', async t => {
  const f = await fixture(t), entered = gate(), release = gate(), c = collector(); let pending;
  await c.run(async () => { pending = f.store.withRunWriter('parent', async () => { entered.release(); await release.promise; }); await entered.promise; });
  const before = JSON.stringify(c.reports[0]); assert(c.reports[0].n[4] > 0); assert.equal(c.reports[0].incomplete, true);
  release.release(); await pending;
  assert.equal(JSON.stringify(c.reports[0]), before);
  await f.store.read('child'); assert.equal(c.reports.length, 1);
});

test('concurrent original requests keep separate private timing ownership', async t => {
  const f = await fixture(t), first = collector(), second = collector();
  const values = await Promise.all([first.run(() => f.store.read('parent')), second.run(() => f.store.read('child'))]);
  assert.deepEqual(values.map(value => value.state.run_id), ['parent', 'child']);
  assert.notEqual(first.reports[0].r, second.reports[0].r);
  for (const c of [first, second]) { assert.equal(c.reports.length, 1); assertComplete(c.reports[0]); assert.equal(c.reports[0].n[0], 2); }
});

test('report failures remain visible and retain the original request error', async () => {
  const original = new Error('original'), diagnostic = new Error('diagnostic');
  await assert.rejects(withForegroundOperationObservation(() => { throw original; }, () => { throw diagnostic; }),
    error => error instanceof AggregateError && error.errors[0] === original && error.errors[1] === diagnostic);
  await assert.rejects(withForegroundOperationObservation(() => true, () => { throw diagnostic; }), error => error === diagnostic);
});

test('arbitrary thenables are not replayed or falsely settled by observation', async () => {
  for (const rejects of [false, true]) {
    const c = collector(), fault = new Error('original thenable rejection'); let gets = 0, calls = 0;
    const thenable = Object.defineProperty({}, 'then', { get() { gets++; return (resolve, reject) => { calls++; rejects ? reject(fault) : resolve('original'); }; } });
    const action = async () => {
      const returned = observeStoreOperation(mark => { mark('reentrant'); return observeGuardedStoreAction(() => thenable, mark); });
      assert.equal(returned, thenable); assert.equal(gets, 0); assert.equal(calls, 0);
      return await returned;
    };
    if (rejects) await assert.rejects(c.run(action), error => error === fault); else assert.equal(await c.run(action), 'original');
    assert.equal(gets, 1); assert.equal(calls, 1);
    const [report] = c.reports; assert.equal(report.n[1], 0); assert.equal(report.n[4], 1); assert.equal(report.n[7], 1);
    assert.equal(report.incomplete, true); assert.equal(report.p.guarded[0], 0);
  }
});

test('cross-realm Promise identity survives with settlement explicitly unobserved', async () => {
  const c = collector(), sandbox = {}, foreign = runInNewContext('new Promise(resolve => { globalThis.resolve = resolve; })', sandbox);
  assert.equal(foreign instanceof Promise, false);
  const observed = c.run(async () => {
    const returned = observeStoreOperation(mark => { mark('reentrant'); return observeGuardedStoreAction(() => foreign, mark); });
    assert.equal(returned, foreign); return await returned;
  });
  await dispatchBarrier(); sandbox.resolve('original');
  assert.equal(await observed, 'original'); const [report] = c.reports;
  assert.equal(report.n[1], 0); assert.equal(report.n[7], 1); assert.equal(report.incomplete, true);
  assert.equal(report.p.guarded[0], 0);
});

test('subclasses, species, constructor getters and proxy callbacks are never added by observation', async () => {
  let species = 0, thenCalls = 0;
  class ExoticPromise extends Promise {
    static get [Symbol.species]() { species++; return Promise; }
    then(...args) { thenCalls++; return super.then(...args); }
  }
  const variants = [
    { make: () => new ExoticPromise(resolve => resolve('original')), before: () => { assert.equal(species, 0); assert.equal(thenCalls, 0); }, after: () => { assert.equal(species, 1); assert.equal(thenCalls, 1); } },
  ];
  let constructorGets = 0;
  variants.push({ make: () => Object.defineProperty(Promise.resolve('original'), 'constructor', { get() { constructorGets++; return Promise; } }),
    before: () => assert.equal(constructorGets, 0), after: () => assert.equal(constructorGets, 1) });
  let proxyGets = 0, proxyCalls = 0;
  variants.push({ make: () => new Proxy(Promise.resolve('original'), { get(target, key) {
    if (key === 'then') { proxyGets++; return resolve => { proxyCalls++; resolve('original'); }; }
    return Reflect.get(target, key);
  } }), before: () => { assert.equal(proxyGets, 0); assert.equal(proxyCalls, 0); }, after: () => { assert.equal(proxyGets, 1); assert.equal(proxyCalls, 1); } });
  for (const variant of variants) {
    const c = collector(), original = variant.make();
    assert.equal(await c.run(async () => {
      const returned = observeStoreOperation(mark => { mark('reentrant'); return observeGuardedStoreAction(() => original, mark); });
      assert.equal(returned, original); variant.before(); return await returned;
    }), 'original');
    variant.after(); assert.equal(c.reports[0].n[7], 1); assert.equal(c.reports[0].incomplete, true);
    assert.equal(c.reports[0].p.guarded[0], 0);
  }
  const c = collector(), native = Promise.resolve('original'), speciesDescriptor = Object.getOwnPropertyDescriptor(Promise, Symbol.species);
  let extraSpeciesCalls = 0;
  assert.equal(await c.run(async () => {
    let returned;
    Object.defineProperty(Promise, Symbol.species, { configurable: true, get() { extraSpeciesCalls++; return Promise; } });
    try { returned = observeStoreOperation(mark => { mark('reentrant'); return observeGuardedStoreAction(() => native, mark); }); }
    finally { Object.defineProperty(Promise, Symbol.species, speciesDescriptor); }
    assert.equal(returned, native); assert.equal(extraSpeciesCalls, 0); return await returned;
  }), 'original');
  assert.equal(c.reports[0].n[7], 1); assert.equal(c.reports[0].incomplete, true);
});

test('public writer awaits an original thenable callback exactly once', async t => {
  const f = await fixture(t), c = collector(); let callbacks = 0, thenCalls = 0;
  const value = { original: true }, thenable = { then(resolve) { thenCalls++; resolve(value); } };
  const result = await c.run(() => f.store.withRunWriter('parent', () => { callbacks++; return thenable; }));
  assert.equal(result, value); assert.equal(callbacks, 1); assert.equal(thenCalls, 1);
  assert.equal(c.reports[0].n[7], 0); assert.equal(c.reports[0].incomplete, false);
});

test('original MCP request emits one unchanged-channel summary with no result or argument bodies', async t => {
  const f = await fixture(t), configPath = join(f.root, 'config.json');
  const auditPath = join(f.root, 'control-plane-audit.jsonl');
  const readRequest = { jsonrpc: '2.0', id: 16, method: 'tools/call', params: { name: 'workflow_read', arguments: { workflow_id: 'private-inspection-body' } } };
  const inspected = await handleRpc(readRequest, { configPath }); assert.equal(inspected.result.isError, true);
  await handleRpc({ jsonrpc: '2.0', id: 15, method: 'server/discover' }, { configPath });
  await handleRpc({ jsonrpc: '2.0', id: 14, method: 'tools/list' }, { configPath });
  await assert.rejects(readFile(auditPath), { code: 'ENOENT' });
  const request = { jsonrpc: '2.0', id: 17, method: 'tools/call', params: { name: 'workflow_native_next', arguments: {} } };
  const response = await handleRpc(request, { configPath });
  assert.equal(response.id, 17); assert.equal(response.result.isError, true);
  const lines = (await readFile(join(f.root, 'control-plane-audit.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
  assert.equal(lines.length, 1); assert.equal(lines[0].event, 'workflow-foreground-operation');
  assert.equal(lines[0].action, 'native_next'); assert(lines[0].detail.length <= 1000);
  assert.equal(JSON.parse(response.result.content[0].text).code, 'MODEL_THREAD_ID');
  const report = JSON.parse(lines[0].detail); assert.equal(report.pid, process.pid);
  assert.equal(report.caller, null);
  assert.equal(JSON.stringify(report).includes('private-inspection-body'), false);
  assert.equal(JSON.stringify(report).includes(f.root), false);
  assert.deepEqual(await handleRpc({ jsonrpc: '2.0', id: 18, method: 'ping' }, { configPath }), { jsonrpc: '2.0', id: 18, result: {} });
  assert.equal((await readFile(join(f.root, 'control-plane-audit.jsonl'), 'utf8')).trim().split('\n').length, 1);
  // Schema rejection before service opening is a zero-model execution error,
  // retaining the same syntactically valid original caller as correlation only.
  const caller = '12345678-1234-4234-8234-123456789012';
  const boundRequest = { ...request, id: 19, params: { ...request.params, arguments: { unexpected: 'private-execution-body' }, _meta: { threadId: caller } } };
  const boundResponse = await handleRpc(boundRequest, { configPath }); assert.equal(boundResponse.result.isError, true);
  const boundLines = (await readFile(auditPath, 'utf8')).trim().split('\n').map(JSON.parse);
  assert.equal(boundLines.length, 2); assert.equal(JSON.parse(boundLines[1].detail).caller, caller);
  assert.equal(boundLines[1].detail.includes('private-execution-body'), false);
  // Force the original normal audit channel to fail after the response exists.
  await rm(join(f.root, 'control-plane-audit.jsonl')); await mkdir(join(f.root, 'control-plane-audit.jsonl'));
  await assert.rejects(handleRpc(request, { configPath }), error => error.code === 'AUDIT_WRITE_FAILED' && error.committed === true);
});

test('all six execution entrypoints preserve missing and invalid model-thread validation', async t => {
  const f = await fixture(t), configPath = join(f.root, 'config.json');
  const entries = [
    ['start', { workflow_id: 'fixture', workspace: f.root, access: 'read_only' }], ['native_next', {}],
    ['start_prepared', {startup_reference:'12345678-1234-4234-8234-123456789abc'}],
    ['native_spawned_batch', {}], ['native_followed_up', {}], ['orchestration_complete', { output: {} }],
  ];
  for (const [operation, args] of entries) for (const threadId of [undefined, 'private-invalid-thread']) {
    const request = { jsonrpc: '2.0', id: operation, method: 'tools/call', params: { name: `workflow_${operation}`, arguments: args,
      ...(threadId === undefined ? {} : { _meta: { threadId } }) } };
    const response = await handleRpc(request, { configPath });
    assert.equal(response.result.isError, true); assert.equal(JSON.parse(response.result.content[0].text).code, 'MODEL_THREAD_ID');
  }
  const lines = (await readFile(join(f.root, 'control-plane-audit.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
  assert.equal(lines.length, 12);
  for (const line of lines) { const report = JSON.parse(line.detail); assert.equal(report.caller, null); assert.equal(report.n[0], 0); assert(line.detail.length <= 1000); }
  assert.equal(JSON.stringify(lines).includes('private-invalid-thread'), false);
});
