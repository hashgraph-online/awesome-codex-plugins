import { resolve } from 'node:path';
import { requireValue } from '../workflow-paths.mjs';

const registries = new Map();
let globallyAccepting = true;
const STOP_WAIT_MS = 5_000;
const keyOf = (runId, nodeId, attemptId) => `${runId}\0${nodeId}\0${attemptId}`;
const stopped = () => Object.assign(new Error('Execution attempt was revoked'), { code: 'ATTEMPT_STOPPED' });

// One in-process owner set is shared by every request for a config. It owns
// admission, cancellation and finite settlement for Host tools, connectors and
// direct API calls; no caller may create a private cancellation snapshot.
export class AttemptAdmissionRegistry {
  constructor() { this.entries = new Map(); this.children = new Map(); this.fencedRuns = new Set(); this.fencedAttempts = new Set(); this.drainJobs = new Map(); this.drainErrors = new Map(); this.accepting = true; }

  registerChild(parentRunId, childRunId, nodeId, attemptId) {
    const children = this.children.get(parentRunId) ?? new Map();
    const parentKey = nodeId && attemptId ? keyOf(parentRunId, nodeId, attemptId) : null;
    children.set(childRunId, parentKey);
    this.children.set(parentRunId, children);
    if (this.fencedRuns.has(parentRunId) || parentKey && this.fencedAttempts.has(parentKey)) this.fenceRun(childRunId);
  }

  assertRunActive(runId) {
    requireValue(this.accepting && !this.fencedRuns.has(runId), 'ATTEMPT_STOPPED', 'Run execution admission is closed');
  }

  assertAttemptActive(runId, nodeId, attemptId) {
    this.assertRunActive(runId);
    requireValue(!this.fencedAttempts.has(keyOf(runId, nodeId, attemptId)), 'ATTEMPT_STOPPED', 'Execution attempt was revoked');
  }

  begin(runId, nodeId, attemptId, kind) {
    const key = keyOf(runId, nodeId, attemptId);
    this.assertAttemptActive(runId, nodeId, attemptId);
    requireValue(!this.entries.has(key), 'ATTEMPT_DUPLICATE', 'This attempt already has an execution owner');
    const controller = new AbortController(); let finish;
    const entry = { run_id: runId, node_id: nodeId, attempt_id: attemptId, kind, controller,
      done: new Promise(resolveDone => { finish = resolveDone; }), settled: false, cleanup: null, cleanupConfirmed: false, result: null };
    entry.registerCleanup = cleanup => {
      requireValue(!entry.settled && typeof cleanup === 'function', 'ATTEMPT_CLEANUP_OWNER', 'Cleanup ownership must be registered before attempt settlement');
      entry.cleanup = async () => { await cleanup(); entry.cleanupConfirmed = true; };
      return entry.cleanup;
    };
    entry.assertActive = () => requireValue(this.accepting && !this.fencedRuns.has(runId) && !this.fencedAttempts.has(key) && !controller.signal.aborted,
      'ATTEMPT_STOPPED', 'Execution attempt was revoked');
    entry.settle = (result = {}) => {
      if (entry.settled) return;
      entry.settled = true;
      entry.result = result;
      // A failed owner after revocation remains visible for a later cleanup
      // attempt; removing it would let another request report false success.
      if (!result.error || !entry.cleanup || entry.cleanupConfirmed) this.entries.delete(key);
      finish(result);
    };
    this.entries.set(key, entry);
    return entry;
  }

  pending(runId, kind = null) {
    return [...this.entries.values()].filter(entry => entry.run_id === runId && (!kind || entry.kind === kind));
  }

  pendingAttempt(runId, nodeId, attemptId) {
    const entry = this.entries.get(keyOf(runId, nodeId, attemptId));
    return entry ? [entry] : [];
  }

  fenceRun(runId) {
    if (this.fencedRuns.has(runId)) return;
    this.fencedRuns.add(runId);
    for (const entry of this.pending(runId)) entry.controller.abort(stopped());
    for (const childRunId of this.children.get(runId)?.keys() ?? []) this.fenceRun(childRunId);
  }

  fenceAttempt(runId, nodeId, attemptId) {
    const key = keyOf(runId, nodeId, attemptId);
    this.fencedAttempts.add(key);
    this.entries.get(key)?.controller.abort(stopped());
    for (const [childRunId, parentKey] of this.children.get(runId) ?? []) if (parentKey === key) this.fenceRun(childRunId);
  }

  releaseRun(runId) {
    requireValue(!this.pending(runId).length, 'RUN_EXECUTION_STOP_INCOMPLETE', 'Run still has execution ownership');
    requireValue(this.accepting, 'ATTEMPT_STOPPED', 'Global execution admission cannot be reopened');
    requireValue(!this.drainJobs.has(runId) || !this.drainErrors.has(runId), 'RUN_EXECUTION_STOP_INCOMPLETE', 'Run cleanup has not succeeded');
    this.drainJobs.delete(runId); this.drainErrors.delete(runId);
    this.fencedRuns.delete(runId);
  }

  fenceAll() {
    this.accepting = false;
    for (const entry of this.entries.values()) entry.controller.abort(stopped());
  }

  async retryCleanup(runId, kind, nodeId = null, attemptId = null) {
    const retained = this.pending(runId, kind).filter(entry => (!nodeId || entry.node_id === nodeId)
      && (!attemptId || entry.attempt_id === attemptId) && entry.settled && entry.result?.error && entry.cleanup);
    const results = await Promise.allSettled(retained.map(entry => {
      entry.cleanupJob ??= Promise.resolve().then(() => entry.cleanup()).finally(() => { entry.cleanupJob = null; });
      return entry.cleanupJob;
    }));
    const errors = [];
    for (let index = 0; index < retained.length; index++) {
      const result = results[index];
      if (result.status === 'rejected') errors.push(result.reason);
      else { retained[index].result = {}; this.entries.delete(keyOf(runId, retained[index].node_id, retained[index].attempt_id)); }
    }
    if (errors.length) throw Object.assign(new AggregateError(errors, 'Exact attempt cleanup remains unconfirmed'), { code: 'ATTEMPT_STOP_INCOMPLETE' });
  }

  async wait(runId = null, kind = null, nodeId = null, attemptId = null) {
    const entries = [...this.entries.values()].filter(entry => (!runId || entry.run_id === runId) && (!kind || entry.kind === kind)
      && (!nodeId || entry.node_id === nodeId) && (!attemptId || entry.attempt_id === attemptId));
    if (!entries.length) return [];
    let timer;
    try {
      await Promise.race([
        Promise.all(entries.map(entry => entry.done.then(() => entry.result))),
        new Promise((_resolve, reject) => { timer = setTimeout(() => reject(Object.assign(new Error('Execution cancellation did not settle'), { code: 'ATTEMPT_STOP_PENDING' })), STOP_WAIT_MS); }),
      ]);
      const errors = entries.flatMap(entry => this.entries.get(keyOf(entry.run_id, entry.node_id, entry.attempt_id)) === entry && entry.result?.error
        ? [entry.result.error] : []);
      if (errors.length) throw Object.assign(new AggregateError(errors, 'Execution owner did not confirm cleanup'), { code: 'ATTEMPT_STOP_INCOMPLETE' });
      return entries;
    } finally { clearTimeout(timer); }
  }

  async waitAttempt(runId, nodeId, attemptId) {
    await this.wait(runId, null, nodeId, attemptId);
  }
}

export function attemptAdmissionFor(configPath) {
  const key = resolve(configPath);
  if (!registries.has(key)) {
    const registry = new AttemptAdmissionRegistry();
    if (!globallyAccepting) registry.fenceAll();
    registries.set(key, registry);
  }
  return registries.get(key);
}

export function fenceAllAttemptAdmissions() {
  globallyAccepting = false;
  for (const registry of registries.values()) registry.fenceAll();
}

export function assertExecutionAdmission(configPath, runId) {
  attemptAdmissionFor(configPath).assertRunActive(runId);
}

export function assertExecutionAttemptAdmission(configPath, runId, nodeId, attemptId) {
  attemptAdmissionFor(configPath).assertAttemptActive(runId, nodeId, attemptId);
}

export function executionAdmissionOpen(configPath) {
  return attemptAdmissionFor(configPath).accepting;
}

export async function closeAttemptAdmissions() {
  fenceAllAttemptAdmissions();
  const settled = await Promise.allSettled([...registries.values()].flatMap(registry => [
    ...registry.drainJobs.values(), registry.wait(),
  ]));
  const errors = settled.filter(item => item.status === 'rejected').map(item => item.reason);
  if (errors.length) throw new AggregateError(errors, 'Execution admission still owns unconfirmed work');
}
