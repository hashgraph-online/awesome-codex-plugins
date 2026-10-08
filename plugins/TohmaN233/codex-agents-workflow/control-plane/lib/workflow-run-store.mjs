import { AsyncLocalStorage } from 'node:async_hooks';
import { mkdir, lstat, readFile, open, rename, rm, readdir } from 'node:fs/promises';
import { join, isAbsolute, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { WorkflowStore, syncDirectory } from './workflow-store.mjs';
import { ensureDirectory, insideRoot, noSymlinks, requireValue, workflowId } from './workflow-paths.mjs';
import { canonicalJSON, digest, LIMITS } from './workflow-revisions.mjs';
import { appendEvent, readEvents, replayEvents, statePatch, recoverEventTail, writeDurableJSON } from './workflow-events.mjs';

const runWriters = new Map();
const activeRunWriters = new AsyncLocalStorage();
const activeStoreOperations = new AsyncLocalStorage();
const TERMINAL_HISTORY_STATUSES = new Set(['succeeded', 'failed']);
const TERMINAL_RUN_STATUSES = new Set(['succeeded', 'failed', 'cancelled']);
const SETTLED_ATTEMPT_STATUSES = new Set(['succeeded', 'failed', 'cancelled', 'interrupted']);
const RECONCILED_OUTCOMES = new Set(['not_started', 'terminated', 'explicit_retry', 'safe_replay']);
const HISTORY_RETENTION_MS = 24 * 60 * 60 * 1000;
export const EXECUTOR_RESULT_MAX_BYTES = 256 * 1024;
const operationKey = root => process.platform === 'win32' ? root.toLowerCase() : root;
function serializeRun(root, action) {
  const key = operationKey(root);
  const operation = (runWriters.get(key) ?? Promise.resolve()).then(action);
  // Each caller receives its own failure. A later independent transition may
  // proceed after it settles; the OS writer lock still protects other processes.
  const settled = operation.then(() => undefined, () => undefined);
  runWriters.set(key, settled);
  void settled.then(() => { if (runWriters.get(key) === settled) runWriters.delete(key); });
  return operation;
}

// Admit a journal transaction before taking any root or Run lock. Transactions
// may read ancestors or create children, so per-Run lock order alone cannot
// prevent inversion. This serializes short store operations, not Agent work.
function storeOperation(root, action) {
  const key = `store-operation:${operationKey(root)}`;
  if (activeStoreOperations.getStore()?.get(key)?.active) return action();
  return serializeRun(key, async () => {
    const owners = new Map(activeStoreOperations.getStore() ?? []);
    const owner = { active: true }; owners.set(key, owner);
    try { return await activeStoreOperations.run(owners, action); }
    finally { owner.active = false; }
  });
}

function reconciliationSettlesEffects(value) {
  return RECONCILED_OUTCOMES.has(value?.outcome) && Array.isArray(value.evidence) && value.evidence.length > 0;
}

async function retainedForLiveEffects(record, readChild, childDirectory, ancestors = new Set()) {
  const { state, pins } = record;
  if (!TERMINAL_RUN_STATUSES.has(state.status)) return 'run_not_terminal';
  requireValue(!ancestors.has(state.run_id), 'RUN_HISTORY_CHILD_CYCLE', 'SubWorkflow Run ancestry contains a cycle');
  ancestors.add(state.run_id);
  try {
    for (const [nodeId, node] of Object.entries(state.nodes ?? {})) {
      if (['claimed', 'running'].includes(node.status)) return 'node_execution_unsettled';
      for (const attempt of node.attempts ?? []) {
        if (!SETTLED_ATTEMPT_STATUSES.has(attempt.status)) return 'attempt_unsettled';
        if (attempt.dispatch?.cancellation_pending) return 'cancellation_pending';
        if (attempt.dispatch) {
          const dispatchSettled = attempt.dispatch.phase === 'acknowledged' && attempt.dispatch.receipt
            || attempt.dispatch.phase === 'intent' && reconciliationSettlesEffects(attempt.reconciliation);
          if (!dispatchSettled) return 'dispatch_unsettled';
        }
        const definition = pins.root.workflow.nodes.find(item => item.id === nodeId);
        const provider = pins.providers?.find(item => item.id === definition?.executor?.provider_id);
        const dispatchHasSettlementEvidence = reconciliationSettlesEffects(attempt.reconciliation);
        const connectorWasObserved = attempt.connector_control?.phase === 'observed';
        const childOwnershipIsRecorded = definition?.type === 'subworkflow' && Boolean(attempt.child_run_id);
        const sessionWasClosed = [...(attempt.executor_events ?? [])].reverse().find(event => event.kind === 'session_state')?.metadata?.status === 'closed';
        if (attempt.status === 'interrupted' && attempt.dispatch?.phase === 'acknowledged' && attempt.dispatch.receipt
          && !dispatchHasSettlementEvidence && !connectorWasObserved && !childOwnershipIsRecorded && !sessionWasClosed) return 'interrupted_dispatch_unsettled';
        if (attempt.host_tool) {
          if (!attempt.host_tool.receipt && !reconciliationSettlesEffects(attempt.host_tool.reconciliation)) return 'host_tool_unsettled';
          const receipt = attempt.host_tool.receipt;
          if (receipt && !['succeeded', 'failed', 'timed_out', 'cancelled'].includes(receipt.status)) return 'host_tool_receipt_unsettled';
          if (['timed_out', 'cancelled'].includes(receipt?.status)
            && receipt.reconciliation?.termination_confirmed !== true
            && !reconciliationSettlesEffects(attempt.host_tool.reconciliation)) return 'host_tool_timed_out';
        }
        if (attempt.connector_control && attempt.connector_control.phase !== 'observed') return 'connector_control_unsettled';
        if (attempt.status === 'interrupted' && provider?.kind === 'builtin_connector' && attempt.dispatch?.receipt
          && attempt.connector_control?.phase !== 'observed' && !reconciliationSettlesEffects(attempt.reconciliation)) return 'connector_unsettled';
        if (attempt.child_run_id) {
          const childId = workflowId(attempt.child_run_id);
          let child;
          try { child = await readChild(childId); }
          catch (error) {
            if ((error.code === 'RUN_HISTORY_CHILD_MISSING' || error.code === 'ENOENT' && error.path === childDirectory(childId))
              && pendingChildIntent(state.run_id, nodeId, attempt, childId)) return 'child_creation_pending';
            if (error.code === 'ENOENT' && error.path === childDirectory(childId)) {
              throw Object.assign(new Error(`Referenced child Run ${childId} is missing; cleanup cannot prove it is settled`),
                { code: 'RUN_HISTORY_CHILD_MISSING', child_run_id: childId, cause: error });
            }
            throw error;
          }
          requireValue(child.pins.parent?.run_id === state.run_id
            && child.pins.parent.node_id === nodeId
            && child.pins.parent.attempt_id === attempt.id
            && child.pins.parent.pins_hash === state.pins_hash,
          'RUN_HISTORY_CHILD_IDENTITY', 'Child Run ancestry differs from its exact parent attempt');
          const childReason = await retainedForLiveEffects(child, readChild, childDirectory, ancestors);
          if (childReason) return `child_${childReason}`;
        }
      }
    }

    const parallelRecords = Object.entries(state.parallel ?? {});
    for (const [regionId, regionState] of parallelRecords) {
      const region = pins.parallel?.regions?.find(item => item.id === regionId && item.isolated);
      if (!region || regionState.phase !== 'merged') return 'parallel_worktree_unsettled';
      const branchIds = region.branches.map(branch => branch.id);
      if (!Array.isArray(regionState.cleaned_branches)
        || branchIds.some(branchId => !regionState.cleaned_branches.includes(branchId))) return 'parallel_worktree_unsettled';
    }
    return null;
  } finally {
    ancestors.delete(state.run_id);
  }
}

async function assertNoSymlinksRecursively(path) {
  await noSymlinks(path);
  const info = await lstat(path);
  requireValue(info.isDirectory(), 'RUN_HISTORY_TARGET', 'History cleanup target must be a directory');
  for (const entry of await readdir(path, { withFileTypes: true })) {
    const child = join(path, entry.name);
    await noSymlinks(child);
    const childInfo = await lstat(child);
    if (childInfo.isDirectory()) await assertNoSymlinksRecursively(child);
    else requireValue(childInfo.isFile(), 'RUN_HISTORY_TARGET', 'History cleanup found a non-file entry');
  }
}

function terminalTimestamp(state) {
  const value = state.finished_at ?? state.updated_at;
  const timestamp = typeof value === 'string' ? Date.parse(value) : NaN;
  requireValue(Number.isFinite(timestamp), 'RUN_HISTORY_TIMESTAMP', 'Terminal Run needs a valid finished_at or updated_at timestamp');
  return timestamp;
}

function expectedChildRunId(parentId, nodeId, attemptId) {
  return `child-${digest([parentId, nodeId, attemptId].join('\0')).slice(0, 58)}`;
}

function pendingChildIntent(parentId, nodeId, attempt, childId) {
  return attempt.dispatch?.phase === 'intent'
    && attempt.dispatch.request_id === `subworkflow-${attempt.id}`
    && attempt.dispatch.receipt == null
    && childId === expectedChildRunId(parentId, nodeId, attempt.id);
}

function buildRunFamilies(records) {
  const parentByChild = new Map();
  const childrenByParent = new Map([...records.keys()].map(id => [id, new Set()]));
  const link = (parentId, childId, identity) => {
    const parent = records.get(parentId); const child = records.get(childId);
    if (!parent) throw Object.assign(new Error(`Referenced parent Run ${parentId} is missing`), { code: 'RUN_HISTORY_PARENT_MISSING', parent_run_id: parentId });
    if (!child) throw Object.assign(new Error(`Referenced child Run ${childId} is missing`), { code: 'RUN_HISTORY_CHILD_MISSING', child_run_id: childId });
    const childParent = child.pins.parent;
    requireValue(childParent?.run_id === parentId && childParent.node_id === identity.node_id
      && childParent.attempt_id === identity.attempt_id && childParent.pins_hash === parent.state.pins_hash
      && childId === expectedChildRunId(parentId, identity.node_id, identity.attempt_id)
      && (!child.pins.child_run_id || child.pins.child_run_id === childId),
    'RUN_HISTORY_CHILD_IDENTITY', 'Child Run ancestry differs from its exact parent attempt');
    const prior = parentByChild.get(childId);
    requireValue(!prior || prior === parentId, 'RUN_HISTORY_CHILD_IDENTITY', 'Child Run is referenced by more than one parent');
    parentByChild.set(childId, parentId);
    childrenByParent.get(parentId).add(childId);
  };

  for (const [parentId, record] of records) {
    for (const [nodeId, node] of Object.entries(record.state.nodes ?? {})) for (const attempt of node.attempts ?? []) {
      if (attempt.child_run_id) {
        const childId = workflowId(attempt.child_run_id);
        // The exact intent is durable before the child directory is published.
        // Missing acknowledged children remain corruption; pending creation is
        // legitimate recovery state and must preserve its parent.
        if (!records.has(childId) && pendingChildIntent(parentId, nodeId, attempt, childId)) continue;
        if (attempt.dispatch?.phase === 'acknowledged') requireValue(attempt.dispatch.receipt?.child_run_id === childId,
          'RUN_HISTORY_CHILD_IDENTITY', 'Acknowledged child dispatch differs from its exact child Run');
        link(parentId, childId, { node_id: nodeId, attempt_id: attempt.id });
      }
    }
  }
  for (const [childId, record] of records) if (record.pins.parent) {
    const parentId = workflowId(record.pins.parent.run_id);
    const parent = records.get(parentId);
    if (!parent) throw Object.assign(new Error(`Referenced parent Run ${parentId} is missing`), { code: 'RUN_HISTORY_PARENT_MISSING', parent_run_id: parentId });
    const attempt = parent.state.nodes?.[record.pins.parent.node_id]?.attempts?.find(item => item.id === record.pins.parent.attempt_id);
    const pendingChildCreation = attempt && pendingChildIntent(parentId, record.pins.parent.node_id, attempt, childId);
    requireValue(attempt?.child_run_id === childId || pendingChildCreation,
      'RUN_HISTORY_CHILD_IDENTITY', 'Parent Run no longer pins this exact child or pending SubWorkflow dispatch');
    if (attempt.dispatch?.phase === 'acknowledged') requireValue(attempt.dispatch.receipt?.child_run_id === childId,
      'RUN_HISTORY_CHILD_IDENTITY', 'Acknowledged child dispatch differs from its exact child Run');
    link(parentId, childId, record.pins.parent);
  }

  const families = []; const visited = new Set();
  const visit = (id, family, ancestry) => {
    requireValue(!ancestry.has(id), 'RUN_HISTORY_CHILD_CYCLE', 'SubWorkflow Run ancestry contains a cycle');
    requireValue(!visited.has(id), 'RUN_HISTORY_CHILD_IDENTITY', 'SubWorkflow Run belongs to multiple parent trees');
    visited.add(id); family.push(id);
    const next = new Set(ancestry); next.add(id);
    for (const childId of [...childrenByParent.get(id)].sort()) visit(childId, family, next);
  };
  for (const id of [...records.keys()].sort()) if (!parentByChild.has(id)) {
    const family = []; visit(id, family, new Set()); families.push(family);
  }
  requireValue(visited.size === records.size, 'RUN_HISTORY_CHILD_CYCLE', 'SubWorkflow Run ancestry contains a cycle');
  return families;
}

export class WorkflowRunStore {
  constructor(root) {
    requireValue(isAbsolute(root), 'ABSOLUTE_PATH_REQUIRED', 'Run store root must be absolute');
    this.root = resolve(root); this.writer = new WorkflowStore(this.root);
  }
  async initialize() { await this.writer.initialize(); await ensureDirectory(join(this.root, '.run-locks')); return this; }
  directory(id) { return join(this.root, `run-${workflowId(id)}.run`); }
  runLockDirectory(id) { return insideRoot(this.root, join(this.root, '.run-locks', `run-${workflowId(id)}`)); }
  async withRunGuard(id, action) {
    return storeOperation(this.root, () => this.#withRunGuard(id, action));
  }
  async #withRunGuard(id, action) {
    await noSymlinks(this.root);
    await ensureDirectory(join(this.root, '.run-locks'));
    const lockDirectory = this.runLockDirectory(id);
    await ensureDirectory(lockDirectory);
    return serializeRun(lockDirectory, () => {
      const active = new Map(activeRunWriters.getStore() ?? []);
      const owner = { active: true }; active.set(operationKey(this.directory(id)), owner);
      return new WorkflowStore(lockDirectory).withWriter(async () => {
        try { return await activeRunWriters.run(active, action); }
        finally { owner.active = false; }
      });
    });
  }
  async #withRunGuards(ids, index, action) {
    if (index >= ids.length) return action();
    return this.withRunGuard(ids[index], () => this.#withRunGuards(ids, index + 1, action));
  }
  withRunWriter(id, action) {
    return storeOperation(this.root, () => this.#withRunWriter(id, action));
  }
  #withRunWriter(id, action) {
    const root = this.directory(id);
    return serializeRun(root, async () => {
      await noSymlinks(root);
      return this.withRunGuard(id, async () => {
        await noSymlinks(root);
        return new WorkflowStore(root).withWriter(action);
      });
    });
  }

  async saveArtifact(id, label, value) {
    return storeOperation(this.root, () => this.#saveArtifact(id, label, value));
  }
  async #saveArtifact(id, label, value) {
    workflowId(label); const bytes = Buffer.from(value); const sha256 = digest(bytes);
    requireValue(bytes.length <= 32 * 1024 * 1024, 'RUN_ARTIFACT_LIMIT', 'Run artifact exceeds its bounded size');
    const artifact = `artifact-${label}-${sha256}.bin`; const path = insideRoot(this.directory(id), join(this.directory(id), artifact));
    // Caller may already own the Run journal writer. Content addressing and wx
    // handle concurrent artifact publication without nesting the writer lock.
    try {
      await noSymlinks(this.directory(id)); const handle = await open(path, 'wx', 0o600);
      try { await handle.writeFile(bytes); await handle.sync(); } finally { await handle.close(); }
      await syncDirectory(this.directory(id));
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      await this.readArtifact(id, { artifact, sha256, bytes: bytes.length });
    }
    return { artifact, sha256, bytes: bytes.length };
  }

  async readArtifact(id, reference) {
    return storeOperation(this.root, () => this.#readArtifact(id, reference));
  }
  async #readArtifact(id, reference) {
    requireValue(reference && /^artifact-[a-z0-9._-]+-[a-f0-9]{64}\.bin$/.test(reference.artifact) && /^[a-f0-9]{64}$/.test(reference.sha256) && Number.isSafeInteger(reference.bytes) && reference.bytes >= 0 && reference.bytes <= 32 * 1024 * 1024, 'RUN_ARTIFACT_REFERENCE', 'Artifact reference needs its exact bounded identity');
    const path = insideRoot(this.directory(id), join(this.directory(id), reference.artifact)); await noSymlinks(path);
    const info = await lstat(path); requireValue(info.isFile() && info.nlink === 1 && info.size === reference.bytes, 'RUN_ARTIFACT_CORRUPT', 'Artifact size/type differs from its reference');
    const bytes = await readFile(path); requireValue(bytes.length === reference.bytes && digest(bytes) === reference.sha256, 'RUN_ARTIFACT_CORRUPT', 'Artifact bytes differ from their committed hash'); return bytes;
  }

  async saveExecutorResult(id, attemptId, result) {
    workflowId(attemptId); const bytes = canonicalJSON(result);
    requireValue(Buffer.byteLength(bytes) <= EXECUTOR_RESULT_MAX_BYTES, 'EXECUTOR_RESULT_LIMIT', 'Executor result exceeds the durable artifact limit');
    const sha256 = digest(bytes); const artifact = `executor-${attemptId}-${sha256}.json`;
    const root = this.directory(id); const path = insideRoot(root, join(root, artifact));
    await this.withRunWriter(id, async () => {
      await noSymlinks(root);
      try {
        await noSymlinks(path); requireValue(digest(await readFile(path)) === sha256, 'EXECUTOR_RESULT_CORRUPT', 'Existing result artifact differs'); return;
      } catch (error) { if (error.code !== 'ENOENT') throw error; }
      const handle = await open(path, 'wx', 0o600);
      try { await handle.writeFile(bytes); await handle.sync(); } finally { await handle.close(); }
      await syncDirectory(root);
    });
    return { artifact, sha256 };
  }

  async readExecutorResult(id, attemptId, sha256) {
    return storeOperation(this.root, () => this.#readExecutorResult(id, attemptId, sha256));
  }
  async #readExecutorResult(id, attemptId, sha256) {
    workflowId(attemptId); requireValue(/^[a-f0-9]{64}$/.test(sha256), 'EXECUTOR_RESULT_ID', 'Result needs an exact content pin');
    const path = join(this.directory(id), `executor-${attemptId}-${sha256}.json`); await noSymlinks(path);
    const stat = await lstat(path); requireValue(stat.isFile() && stat.nlink === 1 && stat.size <= EXECUTOR_RESULT_MAX_BYTES, 'EXECUTOR_RESULT_LIMIT', 'Result artifact must be a bounded regular file');
    const bytes = await readFile(path); requireValue(digest(bytes) === sha256, 'EXECUTOR_RESULT_CORRUPT', 'Result artifact differs from its journal pin');
    return JSON.parse(bytes.toString('utf8'));
  }

  async create(id, pins, blobs, state) {
    return storeOperation(this.root, () => this.#create(id, pins, blobs, state));
  }
  async #create(id, pins, blobs, state) {
    const pinsHash = digest(canonicalJSON(pins));
    requireValue(state.run_id === id && state.pins_hash === pinsHash, 'RUN_IDENTITY', 'Initial state does not match its pinned inputs');
    requireValue(Buffer.byteLength(canonicalJSON(pins)) <= 16 * 1024 * 1024, 'RUN_PINS_LIMIT', 'Pinned metadata is too large');
    requireValue(Array.isArray(pins.resources) && pins.resources.length <= LIMITS.files, 'RUN_RESOURCE', 'Run needs a bounded resource manifest');
    for (const resource of pins.resources) {
      const bytes = blobs.get(resource.sha256);
      requireValue(bytes && bytes.length === resource.bytes && digest(bytes) === resource.sha256, 'RUN_RESOURCE', 'Every pinned resource must have verified bytes before publication');
    }
    return serializeRun(this.root, () => this.writer.withWriter(async () => {
      const destination = this.directory(id);
      try { await lstat(destination); throw Object.assign(new Error('Run already exists'), { code: 'RUN_EXISTS' }); } catch (error) { if (error.code !== 'ENOENT') throw error; }
      const temporary = insideRoot(this.root, join(this.root, '.pending', randomUUID()));
      await noSymlinks(join(this.root, '.pending')); await mkdir(temporary);
      try {
        await mkdir(join(temporary, 'objects'));
        let total = 0;
        for (const [hash, value] of blobs) {
          const bytes = Buffer.from(value); total += bytes.length;
          requireValue(/^[a-f0-9]{64}$/.test(hash) && digest(bytes) === hash && bytes.length <= LIMITS.resource && total <= 256 * 1024 * 1024, 'RUN_RESOURCE', 'Invalid or oversized pinned resource');
          const file = await open(join(temporary, 'objects', hash), 'wx', 0o600);
          try { await file.writeFile(bytes); await file.sync(); } finally { await file.close(); }
        }
        await writeDurableJSON(join(temporary, 'pins.json'), pins);
        const event = await appendEvent(join(temporary, 'events.jsonl'), [], 'started', { state });
        await syncDirectory(join(temporary, 'objects')); await syncDirectory(temporary);
        await rename(temporary, destination); await syncDirectory(this.root);
        return { state: structuredClone(state), pins: structuredClone(pins), sequence: 1, events: [event] };
      } catch (error) {
        try { await noSymlinks(temporary); await rm(insideRoot(this.root, temporary), { recursive: true, maxRetries: 3, retryDelay: 100 }); }
        catch (cleanupError) { if (cleanupError.code !== 'ENOENT') throw new AggregateError([error, cleanupError], 'Run creation and staging cleanup failed'); }
        throw error;
      }
    }));
  }

  async read(id) {
    return storeOperation(this.root, () => this.#read(id));
  }
  async #read(id) {
    const root = this.directory(id);
    if (activeRunWriters.getStore()?.get(operationKey(root))?.active) return this.#readUnlocked(id);
    return serializeRun(root, async () => {
      await noSymlinks(root);
      return this.withRunGuard(id, async () => {
        await noSymlinks(root);
        return new WorkflowStore(root).withWriter(() => this.#readUnlocked(id));
      });
    });
  }

  async #readUnlocked(id) {
    const root = this.directory(id); await noSymlinks(root);
    const { events } = await readEvents(join(root, 'events.jsonl'));
    const state = replayEvents(events);
    requireValue(state.run_id === id, 'RUN_IDENTITY', 'Run journal identity mismatch');
    const pinPath = join(root, 'pins.json'); await noSymlinks(pinPath);
    const pinInfo = await lstat(pinPath);
    requireValue(pinInfo.isFile() && pinInfo.size <= 16 * 1024 * 1024, 'RUN_PINS_LIMIT', 'Pinned metadata must be a bounded regular file');
    const pinBytes = await readFile(pinPath);
    requireValue(pinBytes.length <= 16 * 1024 * 1024, 'RUN_PINS_LIMIT', 'Pinned metadata grew beyond limit');
    const pins = JSON.parse(pinBytes.toString('utf8'));
    requireValue(digest(canonicalJSON(pins)) === state.pins_hash, 'RUN_PINS_CORRUPT', 'Run pins differ from the committed start');
    for (const resource of pins.resources ?? []) {
      requireValue(/^[a-f0-9]{64}$/.test(resource.sha256), 'RUN_RESOURCE', 'Invalid resource digest');
      const path = join(root, 'objects', resource.sha256); await noSymlinks(path);
      const info = await lstat(path);
      requireValue(info.isFile() && info.size <= LIMITS.resource, 'RUN_RESOURCE', 'Pinned resource must be a bounded regular file');
      const bytes = await readFile(path);
      requireValue(bytes.length === resource.bytes && digest(bytes) === resource.sha256, 'RUN_RESOURCE_CORRUPT', 'Pinned resource is missing or modified');
    }
    return { state, pins, events, sequence: events.length };
  }

  async mutate(id, kind, mutate, { expected_sequence } = {}) {
    const root = this.directory(id);
    return this.withRunWriter(id, async () => {
      const current = await this.read(id);
      if (expected_sequence !== undefined) requireValue(current.sequence === expected_sequence, 'RUN_SEQUENCE_CONFLICT', 'Run changed since it was read');
      const next = structuredClone(current.state);
      const result = await mutate(next, current.pins, current);
      requireValue(next.run_id === id && next.pins_hash === current.state.pins_hash, 'RUN_IDENTITY', 'A transition cannot change Run identity/pins');
      const patch = statePatch(current.state, next);
      if (Object.values(patch).every(values => !Object.keys(values).length)) return { ...current, result, idempotent: true };
      const event = await appendEvent(join(root, 'events.jsonl'), current.events, kind, { patch });
      return { state: next, pins: current.pins, sequence: event.sequence, result, events: [...current.events, event] };
    });
  }

  async recover(id, repairState = () => {}, authorizeRecovery = () => {}) {
    return storeOperation(this.root, () => this.#recover(id, repairState, authorizeRecovery));
  }
  async #recover(id, repairState, authorizeRecovery) {
    const root = this.directory(id); const writer = new WorkflowStore(root);
    return serializeRun(root, async () => {
      await noSymlinks(root);
      const lockDirectory = this.runLockDirectory(id);
      await ensureDirectory(join(this.root, '.run-locks')); await ensureDirectory(lockDirectory);
      const guard = new WorkflowStore(lockDirectory);
      const guardOwner = await guard.inspectWriter();
      if (guardOwner) await guard.recoverWriter(guardOwner.token);
      return this.withRunGuard(id, async () => {
        const owner = await writer.inspectWriter();
        if (owner) await writer.recoverWriter(owner.token); // Only a confirmed absent owner can be recovered.
        return writer.withWriter(async () => {
          const committed = await readEvents(join(root, 'events.jsonl'), { allowTornTail: true });
          await authorizeRecovery(replayEvents(committed.events));
          const repaired = await recoverEventTail(join(root, 'events.jsonl'));
          const current = await this.read(id); const next = structuredClone(current.state);
          await repairState(next, current.pins, current);
          const patch = statePatch(current.state, next);
          let event = current.events.at(-1);
          if (repaired.recovered || Object.values(patch).some(value => Object.keys(value).length)) {
            event = await appendEvent(join(root, 'events.jsonl'), current.events, 'recover', { patch, journal_recovery: repaired.recovered });
          }
          return { state: next, pins: current.pins, sequence: event.sequence };
        });
      });
    });
  }

  // Successful authoring Runs pin the private source bundle.  Once a reviewed
  // source-free conversion is committed, retain neither the journal nor its
  // resource objects.  Exact pinned identities prevent this internal cleanup
  // primitive from becoming a general Run-deletion API.
  async purge(id, { expected_workflow_id, expected_revision, expected_source_workflow_id, expected_source_revision, allow_missing = false } = {}) {
    return storeOperation(this.root, () => this.#purge(id, { expected_workflow_id, expected_revision, expected_source_workflow_id, expected_source_revision, allow_missing }));
  }
  async #purge(id, { expected_workflow_id, expected_revision, expected_source_workflow_id, expected_source_revision, allow_missing }) {
    requireValue(typeof allow_missing === 'boolean', 'RUN_PURGE_POLICY', 'Run purge missing policy must be explicit');
    const root = this.directory(id);
    return serializeRun(this.root, () => this.writer.withWriter(async () => {
      try { await noSymlinks(root); }
      catch (error) {
        if (allow_missing && error.code === 'ENOENT' && error.path === root) return { run_id: id, purged: false, missing: true };
        throw error;
      }
      const result = await serializeRun(root, () => this.withRunGuard(id, async () => {
        await noSymlinks(root);
        let current;
        await new WorkflowStore(root).withWriter(async () => { current = await this.read(id); });
        const provenance = current.pins.root.provenance;
        requireValue(current.state.status === 'succeeded' && provenance?.kind === 'authoring_workflow_run',
          'RUN_PURGE_STATE', 'Only a succeeded current authoring Run can be permanently purged');
        requireValue(current.pins.root.workflow.id === expected_workflow_id && current.pins.root.revision_hash === expected_revision,
          'RUN_PURGE_IDENTITY', 'Run-pinned authoring Workflow identity changed before purge');
        requireValue(provenance.source_workflow_id === expected_source_workflow_id && provenance.source_revision === expected_source_revision,
          'RUN_PURGE_SOURCE', 'Run-pinned source identity changed before purge');
        await assertNoSymlinksRecursively(root);
        await rm(insideRoot(this.root, root), { recursive: true, maxRetries: 3, retryDelay: 100 });
        await syncDirectory(this.root);
        return { run_id: id, purged: true, sequence: current.sequence };
      }));
      return result;
    }));
  }

  async cleanupHistory({ olderThanMs = HISTORY_RETENTION_MS, now = Date.now() } = {}) {
    return storeOperation(this.root, () => this.#cleanupHistory({ olderThanMs, now }));
  }
  async #cleanupHistory({ olderThanMs, now }) {
    requireValue(Number.isFinite(olderThanMs) && olderThanMs >= 0, 'RUN_HISTORY_AGE', 'History retention age must be a nonnegative finite number');
    requireValue(Number.isFinite(now) && now >= 0, 'RUN_HISTORY_NOW', 'History cleanup time must be a nonnegative finite number');
    return serializeRun(this.root, () => this.writer.withWriter(async () => {
      await noSymlinks(this.root);
      const runIds = [];
      for (const entry of await readdir(this.root, { withFileTypes: true })) {
        if (['.pending', '.trash', '.run-locks', '.writer.lock', '.recovery.lock'].includes(entry.name)) {
          await noSymlinks(join(this.root, entry.name));
          continue;
        }
        requireValue(entry.isDirectory() && !entry.isSymbolicLink() && /^run-.+\.run$/.test(entry.name),
          'RUN_STORE_ENTRY', 'Unexpected Run store entry');
        runIds.push(workflowId(entry.name.slice(4, -4)));
      }
      runIds.sort();

      const deletedRunIds = []; const preservedRunIds = [];
      // Hold every per-Run guard in a stable order while taking the fresh
      // journal snapshot. The root writer above prevents create/purge from
      // changing the directory set; these guards keep mutations and executor
      // result writes from changing family links or eligibility during cleanup.
      await this.#withRunGuards(runIds, 0, async () => {
        const records = new Map();
        for (const id of runIds) {
          const root = this.directory(id);
          await noSymlinks(root);
          const record = await new WorkflowStore(root).withWriter(() => this.#readUnlocked(id));
          records.set(id, record);
        }

        const families = buildRunFamilies(records);
        const readChild = async childId => {
          const child = records.get(childId);
          if (child) return child;
          const childRoot = this.directory(childId);
          let error;
          try { await noSymlinks(childRoot); }
          catch (cause) { error = cause; }
          if (error?.code === 'ENOENT' && error.path === childRoot) {
            throw Object.assign(new Error(`Referenced child Run ${childId} is missing; cleanup cannot prove it is settled`),
              { code: 'RUN_HISTORY_CHILD_MISSING', child_run_id: childId, cause: error });
          }
          if (error) throw error;
          throw Object.assign(new Error(`Referenced child Run ${childId} was not present in the locked history snapshot`),
            { code: 'RUN_HISTORY_CHILD_MISSING', child_run_id: childId });
        };

        for (const family of families) {
          let eligible = true;
          for (const id of family) {
            const current = records.get(id);
            const state = current.state;
            const terminalStatuses = id === family[0] ? TERMINAL_HISTORY_STATUSES : TERMINAL_RUN_STATUSES;
            if (!terminalStatuses.has(state.status)) { eligible = false; break; }
            const completedAt = terminalTimestamp(state);
            if (olderThanMs !== 0 && completedAt >= now - olderThanMs) { eligible = false; break; }
            const retained = await retainedForLiveEffects(current, readChild, childId => this.directory(childId));
            if (retained) { eligible = false; break; }
          }

          // Validate every member before deleting any. A recent, interrupted,
          // live, or otherwise ineligible parent therefore keeps its old child.
          for (const id of family) {
            const root = this.directory(id);
            await assertNoSymlinksRecursively(root);
            const info = await lstat(root);
            requireValue(info.isDirectory() && !info.isSymbolicLink(), 'RUN_HISTORY_TARGET', 'History cleanup target must be one exact Run directory');
          }

          if (!eligible) {
            preservedRunIds.push(...family);
            continue;
          }

          // Parent-first removal prevents any extant parent from pointing at a
          // child already removed if the filesystem reports an actual error.
          // Directory removals are separate filesystem operations, so report
          // the precise partial family progress if one of them fails.
          const deletedFamilyIds = [];
          for (const id of family) {
            const root = this.directory(id);
            try {
              await rm(insideRoot(this.root, root), { recursive: true, maxRetries: 3, retryDelay: 100 });
              deletedFamilyIds.push(id);
              await syncDirectory(this.root);
            } catch (cause) {
              throw Object.assign(new Error(`History family deletion failed after removing ${deletedFamilyIds.length} of ${family.length} Runs: ${cause.message}`, { cause }),
                { code: 'RUN_HISTORY_DELETE_FAILED', family_run_ids: [...family], deleted_run_ids: [...deletedRunIds, ...deletedFamilyIds] });
            }
          }
          deletedRunIds.push(...deletedFamilyIds);
        }
      });
      deletedRunIds.sort(); preservedRunIds.sort();
      return { examined: runIds.length, deleted_count: deletedRunIds.length, deleted_run_ids: deletedRunIds,
        preserved_count: preservedRunIds.length, preserved_run_ids: preservedRunIds };
    }));
  }

  async list() {
    return storeOperation(this.root, () => this.#list());
  }
  async #list() {
    return serializeRun(this.root, () => this.writer.withWriter(async () => {
      await noSymlinks(this.root); const runs = [];
      for (const entry of await readdir(this.root, { withFileTypes: true })) {
        if (['.pending', '.trash', '.run-locks', '.writer.lock', '.recovery.lock'].includes(entry.name)) { await noSymlinks(join(this.root, entry.name)); continue; }
        requireValue(entry.isDirectory() && !entry.isSymbolicLink() && /^run-.+\.run$/.test(entry.name), 'RUN_STORE_ENTRY', 'Unexpected Run store entry');
        const { state, sequence } = await this.read(entry.name.slice(4, -4));
        runs.push({ run_id: state.run_id, workflow_id: state.workflow_id, status: state.status,
          created_at: state.created_at, updated_at: state.updated_at, sequence });
      }
      return runs.sort((a, b) => a.run_id < b.run_id ? -1 : 1);
    }));
  }
}
