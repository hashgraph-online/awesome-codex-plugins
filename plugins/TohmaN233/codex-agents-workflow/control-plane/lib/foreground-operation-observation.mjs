import { AsyncLocalStorage } from 'node:async_hooks';
import { isPromise } from 'node:util/types';

// This context contains timing ownership only. It is never an execution grant,
// does not cross processes, and becomes inactive when the original call settles.
const contexts = new AsyncLocalStorage();
const SAMPLE_LIMIT = 128;
// op = #call open; pm/hm = provider/Host identity migration; rp = Role
// profiles; q = qualification; ss = existing session factory (setup/start);
// cl = session close. These inclusive spans overlap Store and each other.
// ir = request initialization reuse, including fresh directory checks.
// ib/ia = original fresh opening because comparison budget/accessor state
// makes request reuse ineligible. No execution error or grant is substituted.
export const FOREGROUND_PHASES = Object.freeze(['op', 'pm', 'hm', 'rp', 'q', 'ss', 'cl', 'ir', 'ib', 'ia']);
const phaseNames = new Set(FOREGROUND_PHASES);
const PHASE_COUNT_LIMIT = 1000000;
const PHASE_MS_LIMIT = 1000000000000;
const noop = () => {};
const HostPromise = Promise;
const hostPromisePrototype = HostPromise.prototype;
const hostThen = hostPromisePrototype.then;
const hostSpecies = Object.getOwnPropertyDescriptor(HostPromise, Symbol.species).get;
let requestSequence = 0;
const intervals = {
  fifo: ['entered', 'local_fifo_entry'],
  setup: ['local_fifo_entry', 'root_setup_finished'],
  admission: ['admission_call', 'guarded_entry'],
  guarded: ['guarded_entry', 'guarded_settlement'],
  retirement: ['guarded_settlement', 'settlement'],
};
const milliseconds = value => Number(value.toFixed(3));

function observableHostPromise(value) {
  // Brand-checking rejects proxies without invoking their traps. Avoid any
  // custom then/constructor/species callback, including across realms.
  return isPromise(value) && Object.getPrototypeOf(value) === hostPromisePrototype
    && !Object.getOwnPropertyDescriptor(value, 'then') && !Object.getOwnPropertyDescriptor(value, 'constructor')
    && Object.getOwnPropertyDescriptor(hostPromisePrototype, 'constructor')?.value === HostPromise
    && Object.getOwnPropertyDescriptor(hostPromisePrototype, 'then')?.value === hostThen
    && Object.getOwnPropertyDescriptor(HostPromise, Symbol.species)?.get === hostSpecies;
}

function observeSettlement(value, fulfilled, rejected, unobserved) {
  // Arbitrary object/function returns may be thenables: inspecting/assimilating
  // them again could replay callbacks/getters. Preserve identity, mark unknown.
  if (observableHostPromise(value)) void hostThen.call(value, fulfilled, rejected);
  else if (value !== null && ['object', 'function'].includes(typeof value)) unobserved();
  else fulfilled();
  return value;
}

export function observeForegroundPhase(phase, action) {
  const collector = contexts.getStore()?.collector;
  if (!collector?.active) return action();
  if (!phaseNames.has(phase)) throw new TypeError('Unknown foreground observation phase');
  const value = collector.phases[phase] ??= { completed: 0, inclusive_ms: 0, max_ms: 0 };
  const started = performance.now();
  if (collector.phaseEntered < PHASE_COUNT_LIMIT) collector.phaseEntered++;
  else collector.phaseOverflow = true;
  const finish = () => {
    if (!collector.active) return;
    const elapsed = performance.now() - started;
    if (collector.phaseSettled === PHASE_COUNT_LIMIT || value.completed === PHASE_COUNT_LIMIT
      || !Number.isFinite(elapsed) || elapsed < 0 || value.inclusive_ms + elapsed > PHASE_MS_LIMIT) {
      collector.phaseOverflow = true; return;
    }
    collector.phaseSettled++; value.completed++;
    value.inclusive_ms += elapsed; value.max_ms = Math.max(value.max_ms, elapsed);
  };
  const unobserved = () => {
    if (!collector.active) return;
    if (collector.phaseUnobserved < PHASE_COUNT_LIMIT) collector.phaseUnobserved++;
    else collector.phaseOverflow = true;
  };
  try { return observeSettlement(action(), finish, finish, unobserved); }
  catch (error) { finish(); throw error; }
}

export function assertForegroundObservationAuditFits(report) {
  // The server adds only this already-validated UUID (or null). Reserve its
  // maximum size before calling the unchanged 1000-character audit channel.
  if (JSON.stringify({ ...report, caller: '00000000-0000-0000-0000-000000000000' }).length > 1000) {
    throw Object.assign(new Error('Foreground observation exceeds the 1000-character audit detail limit'),
      { code: 'FOREGROUND_OBSERVATION_LIMIT' });
  }
}

export function observeGuardedStoreAction(action, mark) {
  if (mark === noop) return action();
  mark('guarded_entry');
  try { return observeSettlement(action(), () => mark('guarded_settlement'), () => mark('guarded_settlement'), () => mark('unobserved')); }
  catch (error) { mark('guarded_settlement'); throw error; }
}

export function observeStoreOperation(action) {
  const context = contexts.getStore();
  if (!context?.collector.active) return action(noop);
  const { collector } = context;
  const row = { operation_id: ++collector.entered, parent_operation_id: context.operationId ?? null,
    reentrant: false, status: 'pending', entered: performance.now() };
  if (collector.samples.length < SAMPLE_LIMIT) collector.samples.push(row);
  else collector.omitted++;
  const mark = boundary => {
    if (!collector.active) return;
    if (boundary === 'reentrant') { row.reentrant = true; collector.reentrant++; return; }
    if (boundary === 'unobserved') {
      if (!row.unobserved) { row.unobserved = true; collector.unobserved++; }
      return;
    }
    row[boundary] = performance.now();
    for (const [name, [start, end]] of Object.entries(intervals)) {
      if (boundary !== end || row[start] === undefined || (row.reentrant && name !== 'guarded')) continue;
      const elapsed = row[end] - row[start], interval = collector.intervals[name];
      interval.completed++; interval.inclusive_ms += elapsed; interval.max_ms = Math.max(interval.max_ms, elapsed);
    }
  };
  const finish = status => {
    if (!collector.active) return;
    mark('settlement'); row.status = status; collector.settled++;
    if (status === 'rejected') collector.failed++;
    // A setup/admission fault has no successful next boundary. Retain its
    // observed prefix through settlement, without inventing body entry.
    for (const name of ['setup', 'admission']) {
      if (row[intervals[name][1]] !== undefined) continue;
      const range = intervalRange(row, name);
      if (!range) continue;
      const elapsed = range[1] - range[0], interval = collector.intervals[name];
      interval.completed++; interval.inclusive_ms += elapsed; interval.max_ms = Math.max(interval.max_ms, elapsed);
    }
  };
  return contexts.run({ collector, operationId: row.operation_id }, () => {
    try { return observeSettlement(action(mark), () => finish('fulfilled'), () => finish('rejected'), () => mark('unobserved')); }
    catch (error) { finish('rejected'); throw error; }
  });
}

function intervalRange(row, name) {
  const [start, end] = intervals[name];
  if (row.reentrant && name !== 'guarded') return null;
  const until = row[end] ?? (row.status === 'rejected' && ['setup', 'admission'].includes(name) ? row.settlement : undefined);
  return row[start] === undefined || until === undefined ? null : [row[start], until];
}

function intervalUnion(samples, name) {
  const ranges = samples.map(row => intervalRange(row, name)).filter(Boolean).sort((left, right) => left[0] - right[0]);
  let total = 0, until = -Infinity;
  for (const [from, to] of ranges) { total += Math.max(0, to - Math.max(from, until)); until = Math.max(until, to); }
  return milliseconds(total);
}

export async function withForegroundOperationObservation(action, onReport) {
  // Nested request helpers inherit the original request and never flush twice.
  if (contexts.getStore()?.collector.active) return action();
  const started = performance.now();
  const collector = { active: true, entered: 0, settled: 0, failed: 0, reentrant: 0, omitted: 0, unobserved: 0, samples: [],
    phases: {}, phaseEntered: 0, phaseSettled: 0, phaseUnobserved: 0, phaseOverflow: false,
    intervals: Object.fromEntries(Object.keys(intervals).map(name => [name, { completed: 0, inclusive_ms: 0, max_ms: 0 }])) };
  const requestId = ++requestSequence;
  let result, failure, rejected = false;
  try { result = await contexts.run({ collector, operationId: null }, action); }
  catch (error) { rejected = true; failure = error; }
  const settled = performance.now();
  collector.active = false;
  // Compact fixed-field summary is explicitly checked against the audit limit.
  // n = entered, settled, rejected, reentrant, pending/unobserved settlement,
  // sampled, omitted, operations with unobserved object-return timing.
  // p values = closed interval count, inclusive sum, maximum, sampled union.
  // Counts/sum/max include all operations; unions include only retained samples.
  const report = {
    v: 1, pid: process.pid, r: requestId, ms: milliseconds(settled - started),
    n: [collector.entered, collector.settled, collector.failed, collector.reentrant,
      collector.entered - collector.settled, collector.samples.length, collector.omitted, collector.unobserved],
    p: Object.fromEntries(Object.entries(collector.intervals).map(([name, value]) =>
      [name, [value.completed, milliseconds(value.inclusive_ms), milliseconds(value.max_ms), intervalUnion(collector.samples, name)]])),
    ...(collector.phaseEntered ? {
      // f = closed count/inclusive ms/max ms; fn = entered/settled/unobserved.
      // No phase union or CPU/fs attribution is inferred from these envelopes.
      f: Object.fromEntries(Object.entries(collector.phases).map(([name, value]) =>
        [name, [value.completed, milliseconds(value.inclusive_ms), milliseconds(value.max_ms)]])),
      fn: [collector.phaseEntered, collector.phaseSettled, collector.phaseUnobserved],
    } : {}),
    incomplete: collector.omitted > 0 || collector.entered !== collector.settled || collector.unobserved > 0
      || collector.phaseEntered !== collector.phaseSettled || collector.phaseUnobserved > 0,
    overlapping_not_additive: true,
    unknown: 'CPU/fs,otherPID,pre/post-scope,non-store,objects',
    basis: 'PID-mono;admission=setup/queue/observers;guarded=locks/action;failed-prefix=end;union=sampled',
  };
  // Reporting has no active timing ownership and runs after the original call.
  try {
    if (collector.phaseOverflow) throw Object.assign(new Error('Foreground phase observation exceeds its numeric bounds'),
      { code: 'FOREGROUND_OBSERVATION_LIMIT' });
    assertForegroundObservationAuditFits(report);
    await onReport(report);
  }
  catch (error) {
    if (rejected) throw new AggregateError([failure, error], 'Workflow request and its foreground diagnostic both failed');
    throw error;
  }
  if (rejected) throw failure;
  return result;
}
