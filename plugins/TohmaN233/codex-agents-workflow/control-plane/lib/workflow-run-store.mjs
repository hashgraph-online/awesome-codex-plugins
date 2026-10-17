import { automaticAuthoringCompletion } from './skill-import/completion-policy.mjs';
import { boundedRead } from './bounded-read.mjs';
import { observeStoreOperation, observeGuardedStoreAction } from './foreground-operation-observation.mjs';
import { readHistoryRevision, advanceHistoryRevision, historyEpoch } from './run-history-revision.mjs';
import { AsyncLocalStorage } from 'node:async_hooks';
import { mkdir, lstat, readFile, open, rename, rm, readdir } from 'node:fs/promises';
import { join, isAbsolute, resolve } from 'node:path';
import { randomUUID } from 'node:crypto';
import { WorkflowStore, syncDirectory } from './workflow-store.mjs';
import { ensureDirectory, insideRoot, noSymlinks, statNoSymlinks, requireValue, workflowId } from './workflow-paths.mjs';
import { canonicalJSON, digest, LIMITS } from './workflow-revisions.mjs';
import { appendEvent, appendEvents, readEvents, readStartedEvent, replayEvents, statePatch, recoverEventTail, writeDurableJSON } from './workflow-events.mjs';
import {authorizeRunController,executionAttempt,validateExecutorObservation} from './executor-observation-contract.mjs';
import {fileURLToPath} from 'node:url';
import {dirname} from 'node:path';
import {readPinnedObject} from './pinned-object-reader.mjs';

const runWriters = new Map();
const activeRunWriters = new AsyncLocalStorage();
const activeStoreOperations = new AsyncLocalStorage();
const storeObservations = new AsyncLocalStorage();
const hostTransactions=new AsyncLocalStorage(),observationPhases=new AsyncLocalStorage(),readPurposes=new AsyncLocalStorage();
let bootClosure;
const HOST_TRANSACTION_PHASES=new Set(['claim','main_dispatch','main_prepare','main_commit','native_prepare']);
export function assertOutsideHostRunTransaction(){
  requireValue(!hostTransactions.getStore()?.active,'HOST_RUN_TRANSACTION_EXTERNAL','External execution/wait/environment callbacks cannot run inside a Host Run transaction');
}
export async function withRunStorePhase(name,action){
  requireValue(['plan','claim','prepare','effect_pre','effect_post','accept','native_wait'].includes(name),'RUN_STORE_PHASE','Unknown Host observation phase');
  return observationPhases.run(name,action);
}
export function withRunStorePurpose(name,action){
  requireValue(['authorization','dependency_pre','dependency_post','dispatch_plan','native_projection','checker_pre','checker_post','terminal_prepare','ordinary'].includes(name),
    'RUN_STORE_PURPOSE','Unknown fixed Host read purpose');
  if(name==='authorization'&&readPurposes.getStore())return action();
  return readPurposes.run(name,action);
}
async function sourceBootClosure(){
  bootClosure??=(async()=>{
    const root=dirname(fileURLToPath(import.meta.url)),paths=['workflow-run-store.mjs','workflow-runtime.mjs','workflow-service.mjs','workflow-drive.mjs',
      'workflow-executor.mjs','runtime-environment-state.mjs','execution/native-agent-observer.mjs','execution/main-orchestration.mjs',
      'execution/owned-workflow-authority.mjs','parallel/worktree-manager.mjs','workflow-wait.mjs',
      'execution/terminal-output.mjs','execution/host-main-manager.mjs','workflow-store.mjs','execution/worker-host-check.mjs'];
    return digest(canonicalJSON(await Promise.all(paths.map(async path=>({path,sha256:digest(await readFile(join(root,path)))})))));
  })();
  return bootClosure;
}
function observeMethod(name){
  const current=storeObservations.getStore();if(current?.active)current.methods[name]=(current.methods[name]??0)+1;
}
export async function withRunStoreObservation(action,onReport){
  requireValue(typeof action==='function'&&typeof onReport==='function','RUN_STORE_OBSERVATION','Run observation requires callable boundaries');
  if(storeObservations.getStore()?.active)return action();
  // Snapshot this process's source closure before its first observed action.
  // This identifies disk bytes at initialization, not an in-memory attestation.
  const bootSha256=await sourceBootClosure();
  const current={active:true,methods:{},phases:{},purposes:{},audits:0,objects:0,failures:[]},started=performance.now();
  let value,failure,rejected=false;
  try{value=await storeObservations.run(current,action);}catch(error){rejected=true;failure=error;}
  current.active=false;
  if(Object.keys(current.methods).length){
    const report={v:1,pid:process.pid,ms:Math.round(performance.now()-started),methods:current.methods,
      resource_audits:current.audits,resource_objects:current.objects,failures:current.failures,
      phases:current.phases,read_purposes:current.purposes,boot_sha256:bootSha256};
    try{await onReport(report);}catch(error){if(rejected)throw new AggregateError([failure,error],'Run operation and its diagnostic both failed');throw error;}
  }
  if(rejected)throw failure;return value;
}
const TERMINAL_HISTORY_STATUSES = new Set(['succeeded', 'failed']);
const TERMINAL_RUN_STATUSES = new Set(['succeeded', 'failed', 'cancelled']);
const SETTLED_ATTEMPT_STATUSES = new Set(['succeeded', 'failed', 'cancelled', 'interrupted']);
const RECONCILED_OUTCOMES = new Set(['not_started', 'terminated', 'explicit_retry', 'safe_replay']);
const HISTORY_RETENTION_MS = 24 * 60 * 60 * 1000;
export const EXECUTOR_RESULT_MAX_BYTES = 256 * 1024;
function startupPublicationFor(state) {
  if (!state.constraints?.host_startup_key) return null;
  const value = {schema_version:1,run_id:state.run_id,
    thread_id:state.constraints.native_parent_thread_id,
    launch_key:state.constraints.host_startup_key,sha256:state.constraints.host_startup_sha256};
  requireValue([value.run_id,value.thread_id,value.launch_key].every(id => typeof id==='string' && /^[0-9a-f-]{36}$/.test(id))
    && typeof value.sha256==='string' && /^[0-9a-f]{64}$/.test(value.sha256),
    'WORKFLOW_STARTUP_PUBLICATION','Startup publication needs exact Host-owned identity');
  return value;
}
async function readStartupPublication(root,id) {
  const directory=join(root,'.run-locks','.startup-publications');
  await noSymlinks(join(root,'.run-locks'));
  try{await noSymlinks(directory);}catch(error){if(error.code==='ENOENT'&&typeof error.path==='string'
    &&operationKey(resolve(error.path))===operationKey(resolve(directory)))return null;throw error;}
  const path=join(directory,`${workflowId(id)}.json`);
  try {
    await noSymlinks(path);const info=await lstat(path);
    requireValue(info.isFile()&&info.nlink===1&&info.size<=4096,
      'WORKFLOW_STARTUP_PUBLICATION','Startup publication must be one bounded regular file');
    const bytes=await readFile(path);
    requireValue(bytes.length<=4096,'WORKFLOW_STARTUP_PUBLICATION','Startup publication grew beyond its limit');
    const value=JSON.parse(bytes.toString('utf8'));
    requireValue(value.schema_version===1&&value.run_id===id
      && canonicalJSON(value)===canonicalJSON(startupPublicationFor({run_id:id,constraints:{
        native_parent_thread_id:value.thread_id,host_startup_key:value.launch_key,host_startup_sha256:value.sha256}})),
      'WORKFLOW_STARTUP_PUBLICATION','Startup publication identity is invalid');
    return value;
  } catch(error) {if(error.code==='ENOENT'&&typeof error.path==='string'
    &&operationKey(resolve(error.path))===operationKey(resolve(path)))return null;throw error;}
}
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
async function storeOperation(root, action,name='internal') {
  observeMethod(name);
  try{return await observeStoreOperation(mark => {
    const key = `store-operation:${operationKey(root)}`;
    if (activeStoreOperations.getStore()?.get(key)?.active) {
      mark('reentrant');
      return observeGuardedStoreAction(action, mark);
    }
    return serializeRun(key, async () => {
      mark('local_fifo_entry');
      await noSymlinks(root);
      const admission=join(root,'.run-locks','.store-operation');
      await ensureDirectory(join(root,'.run-locks'));await ensureDirectory(admission);
      mark('root_setup_finished');
      mark('admission_call');
      return new WorkflowStore(admission).withRunAdmission(async()=>{
        const owners = new Map(activeStoreOperations.getStore() ?? []);
        const owner = { active: true }; owners.set(key, owner);
        try { return await observeGuardedStoreAction(() => activeStoreOperations.run(owners, action), mark); }
        finally { owner.active = false; }
      },{operation:name});
    });
  });}catch(error){
    const current=storeObservations.getStore();
    if(current?.active&&current.failures.length<1){
      const detail={method:name,code:typeof error.code==='string'&&/^[A-Z0-9_]{1,128}$/.test(error.code)?error.code:'UNKNOWN'};
      if(Number.isSafeInteger(error.owner_pid))detail.owner_pid=error.owner_pid;
      if(typeof error.owner_operation==='string'&&/^[a-z_]{1,32}$/.test(error.owner_operation))detail.owner_operation=error.owner_operation;
      if(Number.isSafeInteger(error.waited_ms))detail.waited_ms=error.waited_ms;
      if(typeof error.created_at==='string')detail.created_at=error.created_at;
      if(typeof error.lock_path==='string')detail.lock_scope=operationKey(error.lock_path)===operationKey(join(root,'.run-locks','.store-operation','.writer.lock'))?'global_admission':'other';
      current.failures.push(detail);
    }
    throw error;
  }
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
  // Host source calls only. No record/skip flag enters this interface. One
  // short exact Run writer owns fresh journal/pins and subsequent projections;
  // execution/environment/SDK callbacks must run outside this boundary.
  async withHostTransaction(id,phase,action){
    requireValue(HOST_TRANSACTION_PHASES.has(phase)&&typeof action==='function','HOST_RUN_TRANSACTION_PHASE','Unknown Host Run transaction phase');
    const prior=hostTransactions.getStore();
    if(prior?.active){requireValue(prior.store===this&&prior.id===id,'HOST_RUN_TRANSACTION_SCOPE','A Host transaction cannot reuse another Run');return action();}
    return withRunStorePurpose(phase==='native_prepare'?'native_projection':phase==='main_commit'?'terminal_prepare':'dispatch_plan',()=>withRunStorePhase(phase==='main_commit'?'accept':phase==='claim'?'claim':'prepare',()=>this.withRunWriter(id,async()=>{
      const record=await this.#readUnlocked(id),owner={store:this,id,record,active:true};
      try{return await hostTransactions.run(owner,action);}finally{owner.active=false;}
    })));
  }
  #transaction(id){const owner=hostTransactions.getStore();return owner?.active&&owner.store===this&&owner.id===id?owner:null;}
  #advanceTransaction(id,record){const owner=this.#transaction(id);if(owner)owner.record=structuredClone(record);}
  async withRunGuard(id, action) {
    return storeOperation(this.root, () => this.#withRunGuard(id, action),'guard');
  }
  async #withRunGuard(id, action, observation = false) {
    await noSymlinks(this.root);
    await ensureDirectory(join(this.root, '.run-locks'));
    const lockDirectory = this.runLockDirectory(id);
    await ensureDirectory(lockDirectory);
    return serializeRun(lockDirectory, () => {
      const active = new Map(activeRunWriters.getStore() ?? []);
      const owner = { active: true }; active.set(operationKey(this.directory(id)), owner);
      const writer=new WorkflowStore(lockDirectory);
      const guard=async () => {
        try { return await activeRunWriters.run(active, action); }
        finally { owner.active = false; }
      };
      return observation?writer.withRunObservationGuard(guard):writer.withWriter(guard);
    });
  }
  async #withRunGuards(ids, index, action) {
    if (index >= ids.length) return action();
    return this.withRunGuard(ids[index], () => this.#withRunGuards(ids, index + 1, action));
  }
  withRunWriter(id, action) {
    if(this.#transaction(id))return action();
    return storeOperation(this.root, () => this.#withRunWriter(id, async () => {
      // Public callbacks may publish authority/results as well as journal data.
      // Invalidate before handing arbitrary writer code its first write scope.
      await advanceHistoryRevision(this.root, id);
      return action();
    }),'writer');
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
    return storeOperation(this.root, () => this.#saveArtifact(id, label, value),'artifact_write');
  }
  async #saveArtifact(id, label, value) {
    workflowId(label); const bytes = Buffer.from(value); const sha256 = digest(bytes);
    requireValue(bytes.length <= 32 * 1024 * 1024, 'RUN_ARTIFACT_LIMIT', 'Run artifact exceeds its bounded size');
    const artifact = `artifact-${label}-${sha256}.bin`; const path = insideRoot(this.directory(id), join(this.directory(id), artifact));
    // Caller may already own the Run journal writer. Content addressing and wx
    // handle concurrent artifact publication without nesting the writer lock.
    try {
      await noSymlinks(this.directory(id));
      await advanceHistoryRevision(this.root, id);
      const handle = await open(path, 'wx', 0o600);
      try { await handle.writeFile(bytes); await handle.sync(); } finally { await handle.close(); }
      await syncDirectory(this.directory(id));
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      await this.readArtifact(id, { artifact, sha256, bytes: bytes.length });
    }
    return { artifact, sha256, bytes: bytes.length };
  }

  async readArtifact(id, reference) {
    return storeOperation(this.root, () => this.#readArtifact(id, reference),'artifact_read');
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
    return storeOperation(this.root, () => this.#readExecutorResult(id, attemptId, sha256),'result_read');
  }
  async #readExecutorResult(id, attemptId, sha256) {
    workflowId(attemptId); requireValue(/^[a-f0-9]{64}$/.test(sha256), 'EXECUTOR_RESULT_ID', 'Result needs an exact content pin');
    const path = join(this.directory(id), `executor-${attemptId}-${sha256}.json`); await noSymlinks(path);
    const stat = await lstat(path); requireValue(stat.isFile() && stat.nlink === 1 && stat.size <= EXECUTOR_RESULT_MAX_BYTES, 'EXECUTOR_RESULT_LIMIT', 'Result artifact must be a bounded regular file');
    const bytes = await readFile(path); requireValue(digest(bytes) === sha256, 'EXECUTOR_RESULT_CORRUPT', 'Result artifact differs from its journal pin');
    return JSON.parse(bytes.toString('utf8'));
  }

  async create(id, pins, blobs, state, {hostAuthority} = {}) {
    if (hostAuthority) requireValue(hostAuthority.run_id === id && typeof hostAuthority.control_token === 'string'
      && digest(hostAuthority.control_token) === state.control_hash, 'RUN_AUTHORITY', 'Initial Host authority differs from its Run');
    return storeOperation(this.root, () => this.#create(id, pins, blobs, state, hostAuthority),'create');
  }
  async startupPublication(id) {
    return storeOperation(this.root,()=>readStartupPublication(this.root,id),'startup_publication');
  }
  async #create(id, pins, blobs, state, hostAuthority) {
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
      requireValue(!await readStartupPublication(this.root,id),'WORKFLOW_STARTUP_PUBLICATION_REUSED',
        'This Run publication was already committed or its outcome is indeterminate; inspect it before starting a new invocation');
      await advanceHistoryRevision(this.root, id);
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
        if (hostAuthority) await writeDurableJSON(join(temporary, 'host-authority.json'), hostAuthority);
        const event = await appendEvent(join(temporary, 'events.jsonl'), [], 'started', { state });
        await syncDirectory(join(temporary, 'objects')); await syncDirectory(temporary);
        const publication=startupPublicationFor(state);
        if(publication){
          // Commit intent precedes rename under admission. It survives history
          // removal and crashes; an uncertain rename must never be replayed.
          const directory=join(this.root,'.run-locks','.startup-publications');
          await ensureDirectory(directory);
          await writeDurableJSON(join(directory,`${id}.json`),publication);
        }
        await rename(temporary, destination); await syncDirectory(this.root);
        return { state: structuredClone(state), pins: structuredClone(pins), sequence: 1, events: [event] };
      } catch (error) {
        try { await noSymlinks(temporary); await rm(insideRoot(this.root, temporary), { recursive: true, maxRetries: 3, retryDelay: 100 }); }
        catch (cleanupError) { if (cleanupError.code !== 'ENOENT') throw new AggregateError([error, cleanupError], 'Run creation and staging cleanup failed'); }
        throw error;
      }
    }));
  }

  async read(id, { auditHistoryTree = false } = {}) {
    const transaction=this.#transaction(id);
    if(transaction&&!auditHistoryTree){observeMethod('transaction_read');return structuredClone(transaction.record);}
    return storeOperation(this.root, async () => {
      const record = await this.#read(id, { auditHistoryTree });
      if (auditHistoryTree) record.history_epoch = historyEpoch(await readHistoryRevision(this.root), id);
      return record;
    },'read');
  }

  // Status and lookup inspect immutable pins and the append-only journal. They
  // do not publish effects, repair ownership or wait for a stale writer.
  async observe(id) {
    observeMethod('observe');
    return this.#readJournalPins(id);
  }

  // Explicit whole-package integrity audit. This is a Host storage operation,
  // not a caller-controlled execution shortcut or a resource cache.
  async audit(id) {
    return storeOperation(this.root,()=>this.#read(id,{auditResources:true}),'audit');
  }

  // Retention classification needs committed lifecycle/lineage and exact pins,
  // never executable resource authority. Audit resource bytes and the complete
  // tree only for an eligible deletion family, outside foreground admission.
  async readHistoryMetadata(id) {
    return storeOperation(this.root,async()=>{
      const record=await this.#read(id);
      record.history_epoch=historyEpoch(await readHistoryRevision(this.root),id);
      return record;
    },'history_metadata');
  }
  async readHistoryMetadataBatch(ids) {
    requireValue(Array.isArray(ids)&&ids.length>0&&ids.length<=4,'RUN_HISTORY_METADATA_BATCH',
      'Retention metadata admission is bounded to 1..4 exact Run records');
    const selected=[...ids];selected.forEach(workflowId);
    return storeOperation(this.root,()=>boundedRead(selected,4,async id=>[id,await this.readHistoryMetadata(id)]),'history_batch');
  }

  // Lifecycle observation needs no writer admission. Otherwise this exact Run
  // guard can collide with a maintenance writer in another process, even though
  // both readers are healthy. Keep strict journal/pin verification and return no
  // executable pins/resources; actual transitions retain writer ownership.
  async readNativeWaitState(id) {
    observeMethod('native_wait');
    const {state,events,sequence}=await this.#readJournalPins(id);
    return {state,events,sequence};
  }
  async #read(id, { auditHistoryTree=false, auditResources=false } = {}) {
    const root = this.directory(id);
    const read=()=>this.#readUnlocked(id,{auditHistoryTree,auditResources});
    if (activeRunWriters.getStore()?.get(operationKey(root))?.active) return read();
    return serializeRun(root, async () => {
      await noSymlinks(root);
      return this.withRunGuard(id, async () => {
        await noSymlinks(root);
        return new WorkflowStore(root).withWriter(read);
      });
    });
  }

  async #readJournalPins(id) {
    const transaction=this.#transaction(id);if(transaction)return structuredClone(transaction.record);
    const root = this.directory(id); await noSymlinks(root);
    const { events } = await readEvents(join(root, 'events.jsonl'));
    const state = replayEvents(events);
    requireValue(state.run_id === id, 'RUN_IDENTITY', 'Run journal identity mismatch');
    const pinPath = join(root, 'pins.json'); const {stat:pinInfo} = await statNoSymlinks(pinPath);
    requireValue(pinInfo.isFile() && pinInfo.size <= 16 * 1024 * 1024, 'RUN_PINS_LIMIT', 'Pinned metadata must be a bounded regular file');
    const pinBytes = await readFile(pinPath);
    requireValue(pinBytes.length <= 16 * 1024 * 1024, 'RUN_PINS_LIMIT', 'Pinned metadata grew beyond limit');
    const pins = JSON.parse(pinBytes.toString('utf8'));
    requireValue(digest(canonicalJSON(pins)) === state.pins_hash, 'RUN_PINS_CORRUPT', 'Run pins differ from the committed start');
    return {state,pins,events,sequence:events.length};
  }

  async #readUnlocked(id, { auditHistoryTree = false, auditResources = false } = {}) {
    const record=await this.#readJournalPins(id);
    if(auditResources||auditHistoryTree)await this.#auditRecordFiles(id,record,{auditHistoryTree});
    return record;
  }

  async #auditRecordFiles(id,{pins},{auditHistoryTree=false}={}) {
    const root=this.directory(id);
    const observation=storeObservations.getStore();if(observation?.active){observation.audits++;observation.objects+=(pins.resources??[]).length;}
    if(observation?.active){const key=readPurposes.getStore()??'ordinary',counts=observation.purposes[key]??={audits:0,objects:0};counts.audits++;counts.objects+=(pins.resources??[]).length;}
    const phase=observationPhases.getStore();if(observation?.active&&phase){const counts=observation.phases[phase]??={audits:0,objects:0};counts.audits++;counts.objects+=(pins.resources??[]).length;}
    await boundedRead(pins.resources ?? [],4,resource=>readPinnedObject(join(root,'objects'),resource));
    if (auditHistoryTree) {
      await assertNoSymlinksRecursively(root);
      const info = await lstat(root);
      requireValue(info.isDirectory() && !info.isSymbolicLink(), 'RUN_HISTORY_TARGET', 'History cleanup target must be one exact Run directory');
    }
  }

  // No partial record or callback escapes this internal, fixed observation write.
  // Object integrity is checked by the consumer or an explicit whole-package audit.
  async appendExecutorObservation(id,{node_id,attempt_id,lease_token,control_token,event}) {
    return this.appendExecutorObservations(id,{node_id,attempt_id,lease_token,control_token,events:[event]});
  }
  async appendExecutorObservations(id,{node_id,attempt_id,lease_token,control_token,events}) {
    requireValue(Array.isArray(events)&&events.length>0&&events.length<=64,'EXECUTOR_OBSERVATION_BATCH_LIMIT','Observation batch must contain 1..64 events');
    const observations=structuredClone(events);observations.forEach(validateExecutorObservation);
    requireValue(Buffer.byteLength(canonicalJSON(observations))<=2*1024*1024,'EXECUTOR_OBSERVATION_BATCH_LIMIT','Observation batch exceeds its byte bound');
    return this.withRunWriter(id,async()=>{
      const current=await this.#readJournalPins(id);let next=structuredClone(current.state);const records=[];
      authorizeRunController(next,control_token);
      // Preserve late metadata for a fenced attempt without reviving its lease.
      executionAttempt(next,node_id,attempt_id,lease_token,{active:false});
      for(const observation of observations){
        const before=next;next=structuredClone(before);
        const {attempt}=executionAttempt(next,node_id,attempt_id,lease_token,{active:false});
        attempt.executor_event_count=(attempt.executor_event_count??0)+1;
        attempt.executor_events=[...(attempt.executor_events??[]).slice(-63),{sequence:attempt.executor_event_count,...observation}];
        next.updated_at=new Date().toISOString();
        requireValue(next.run_id===id&&next.pins_hash===current.state.pins_hash,'RUN_IDENTITY','A transition cannot change Run identity/pins');
        records.push({kind:'executor_event',at:new Date().toISOString(),payload:{patch:statePatch(before,next)}});
      }
      const committed=await appendEvents(join(this.directory(id),'events.jsonl'),current.events,records);
      this.#advanceTransaction(id,{state:next,pins:current.pins,events:[...current.events,...committed],sequence:committed.at(-1).sequence});
      return {sequence:committed.at(-1).sequence};
    });
  }

  async mutate(id, kind, mutate, { expected_sequence } = {}) {
    return this.#mutate(id,kind,mutate,{expected_sequence});
  }
  // Fixed Host executor-state journaling, never a dispatch/claim/completion
  // grant. The runtime validates its typed event and exact controller/lease;
  // this seam still rereads the complete journal and validates the pin hash.
  async mutateExecutorJournal(id,mutate){
    return this.#mutate(id,'executor_event',mutate);
  }
  // Host-internal native persistence only. No caller-controlled skip-audit
  // option exists; every mutation reads fresh journal/pins identically.
  async mutateNativeJournal(id,kind,mutate){
    requireValue(['native_spawn_batch','native_serial_result','native_agent_rejection','native_text_amendment',
      'native_parallel_result','native_item_results','native_dispatch_span','native_host_check_proposal',
      'usage','dispatch_receipt','host_tool_intent','host_tool_receipt','managed_native_results'].includes(kind),
      'NATIVE_JOURNAL_KIND','Only fixed native journal events may use metadata persistence');
    return this.#mutate(id,kind,mutate);
  }
  async #mutate(id,kind,mutate,{expected_sequence}={}){
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
      const committed={ state: next, pins: current.pins, sequence: event.sequence, result, events: [...current.events, event] };
      this.#advanceTransaction(id,committed);return committed;
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
      await advanceHistoryRevision(this.root, id);
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
  async purge(id, { expected_workflow_id, expected_revision, expected_source_workflow_id, expected_source_revision, allow_missing = false, terminal_authoring = false } = {}) {
    return storeOperation(this.root, () => this.#purge(id, { expected_workflow_id, expected_revision, expected_source_workflow_id, expected_source_revision, allow_missing, terminal_authoring }));
  }
  async #purge(id, { expected_workflow_id, expected_revision, expected_source_workflow_id, expected_source_revision, allow_missing, terminal_authoring }) {
    requireValue(typeof allow_missing === 'boolean'&&typeof terminal_authoring==='boolean', 'RUN_PURGE_POLICY', 'Run purge missing policy must be explicit');
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
        requireValue((current.state.status === 'succeeded'||terminal_authoring&&TERMINAL_RUN_STATUSES.has(current.state.status)) && provenance?.kind === 'authoring_workflow_run',
          'RUN_PURGE_STATE', 'Only a succeeded current authoring Run can be permanently purged');
        requireValue(current.pins.root.workflow.id === expected_workflow_id && current.pins.root.revision_hash === expected_revision,
          'RUN_PURGE_IDENTITY', 'Run-pinned authoring Workflow identity changed before purge');
        requireValue(provenance.source_workflow_id === expected_source_workflow_id && provenance.source_revision === expected_source_revision,
          'RUN_PURGE_SOURCE', 'Run-pinned source identity changed before purge');
        const retained=await retainedForLiveEffects(current,childId=>this.read(childId),childId=>this.directory(childId));
        requireValue(!retained,'RUN_PURGE_LIVE_EFFECTS','Authoring cleanup cannot remove unresolved execution ownership',{reason:retained});
        await assertNoSymlinksRecursively(root);
        await advanceHistoryRevision(this.root, id);
        await rm(insideRoot(this.root, root), { recursive: true, maxRetries: 3, retryDelay: 100 });
        await advanceHistoryRevision(this.root, id, { removing: true });
        await syncDirectory(this.root);
        return { run_id: id, purged: true, sequence: current.sequence };
      }));
      return result;
    }));
  }

  async cleanupHistory({ olderThanMs = HISTORY_RETENTION_MS, now = Date.now(), signal } = {}) {
    requireValue(Number.isFinite(olderThanMs) && olderThanMs >= 0, 'RUN_HISTORY_AGE', 'History retention age must be a nonnegative finite number');
    requireValue(Number.isFinite(now) && now >= 0, 'RUN_HISTORY_NOW', 'History cleanup time must be a nonnegative finite number');
    const records = new Map();
    const checkpoint = () => requireValue(!signal?.aborted, 'RUN_HISTORY_CANCELLED', 'History audit was cancelled before new work admission');
    for (;;) {
      checkpoint();
      const { runIds, witness } = await this.#captureHistory();
      const present = new Set(runIds);
      for (const id of records.keys()) if (!present.has(id)) records.delete(id);
      const changedIds = runIds.filter(id => !records.has(id) || records.get(id).history_epoch !== historyEpoch(witness, id));
      let entries;
      try {
        entries=[];
        // Bound each admission to four metadata records. Do not keep a global
        // writer while hashing historical objects or walking historical trees.
        for(let index=0;index<changedIds.length;index+=4){
          checkpoint();
          entries.push(...await this.readHistoryMetadataBatch(changedIds.slice(index,index+4)));
        }
      }
      catch (error) {
        // A captured directory may be deleted before its short read is admitted.
        // Other read/lock/integrity failures are real failures, never retries.
        const failures = error instanceof AggregateError ? error.errors : [error];
        if (failures.every(item => item.code === 'ENOENT' && runIds.some(id => item.path === this.directory(id)))
          && !await this.#historyUnchanged(witness.revision)) continue;
        throw error;
      }
      for (const [id, record] of entries) records.set(id, record);
      // Do not interpret parent/child relationships from different revisions.
      // Each changed journal/pin is revalidated; unchanged records retain their
      // exact durable epochs only during this audit, never across invocations.
      checkpoint();
      const fresh = await this.#captureHistory();
      if (fresh.runIds.length !== records.size || fresh.runIds.some(id => !records.has(id)
        || records.get(id).history_epoch !== historyEpoch(fresh.witness, id))) continue;
      const revision = fresh.witness.revision;
      const audit = await this.#auditHistory(records, { olderThanMs, now });
      checkpoint();
      // Classification confers no deletion grant. Every actual candidate still
      // needs the complete resource and physical tree checks. Concurrent Host
      // mutations change the durable witness and force fresh classification;
      // all corrupt/unreadable candidate faults propagate without a fallback.
      await boundedRead(audit.eligibleFamilies.flat(),4,async id=>{
        checkpoint();await this.#auditRecordFiles(id,records.get(id),{auditHistoryTree:true});
      });
      checkpoint();
      const committed = await storeOperation(this.root, () => serializeRun(this.root, () => this.writer.withWriter(async () => {
        checkpoint();
        if ((await readHistoryRevision(this.root)).revision !== revision) return null;
        const candidates = audit.eligibleFamilies.flat().sort();
        return this.#withRunGuards(candidates, 0, async () => {
          checkpoint();
          // Equal durable revision makes every audited journal, relationship,
          // live effect and tree check fresh. No writer can enter until commit
          // releases admission, and all candidate guards use stable ordering.
          const deletedRunIds = [];
          for (const family of audit.eligibleFamilies) {
            const deletedFamilyIds = [];
            for (const id of family) {
              const root = this.directory(id);
              try {
                await advanceHistoryRevision(this.root, id);
                await rm(insideRoot(this.root, root), { recursive: true, maxRetries: 3, retryDelay: 100 });
                deletedFamilyIds.push(id);
                await advanceHistoryRevision(this.root, id, { removing: true });
                await syncDirectory(this.root);
              } catch (cause) {
                throw Object.assign(new Error(`History family deletion failed after removing ${deletedFamilyIds.length} of ${family.length} Runs: ${cause.message}`, { cause }),
                  { code: 'RUN_HISTORY_DELETE_FAILED', family_run_ids: [...family], deleted_run_ids: [...deletedRunIds, ...deletedFamilyIds] });
              }
            }
            deletedRunIds.push(...deletedFamilyIds);
          }
          deletedRunIds.sort(); audit.preservedRunIds.sort();
          return { examined: runIds.length, deleted_count: deletedRunIds.length, deleted_run_ids: deletedRunIds,
            preserved_count: audit.preservedRunIds.length, preserved_run_ids: audit.preservedRunIds };
        });
      })));
      if (committed) return committed;
    }
  }

  async #historyUnchanged(revision) {
    return storeOperation(this.root, async () => (await readHistoryRevision(this.root)).revision === revision,'history_fence');
  }

  async #historyRunIds({validateReserved=false}={}) {
      await noSymlinks(this.root);
      const runIds = [];
      for (const entry of await readdir(this.root, { withFileTypes: true })) {
        if (['.pending', '.trash', '.run-locks', '.writer.lock', '.recovery.lock'].includes(entry.name)) {
          if(validateReserved)await noSymlinks(join(this.root, entry.name));
          continue;
        }
        requireValue(entry.isDirectory() && !entry.isSymbolicLink() && /^run-.+\.run$/.test(entry.name),
          'RUN_STORE_ENTRY', 'Unexpected Run store entry');
        runIds.push(workflowId(entry.name.slice(4, -4)));
      }
      runIds.sort();
      return runIds;
  }

  async #captureHistory() {
    return storeOperation(this.root, () => serializeRun(this.root, () => this.writer.withWriter(async () => {
      return { runIds:await this.#historyRunIds({validateReserved:true}), witness: await readHistoryRevision(this.root) };
    })),'history_locator');
  }

  async #auditHistory(records, { olderThanMs, now }) {
    const eligibleFamilies = []; const preservedRunIds = [];
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
      throw Object.assign(new Error(`Referenced child Run ${childId} was not present in the verified history snapshot`),
        { code: 'RUN_HISTORY_CHILD_MISSING', child_run_id: childId });
    };

    for (const family of families) {
      let eligible = true;
      for (const id of family) {
        const current = records.get(id);
        const state = current.state;
        const terminalStatuses = id === family[0] ? TERMINAL_HISTORY_STATUSES : TERMINAL_RUN_STATUSES;
        if (!terminalStatuses.has(state.status)) { eligible = false; break; }
        // A succeeded automatic authoring Run still present owns an
        // unfinished completion candidate. Only its exact deployment
        // cleanup may remove that evidence, irrespective of retention age.
        if(state.status==='succeeded'&&current.pins.root.provenance?.kind==='authoring_workflow_run'
          &&automaticAuthoringCompletion(current.pins.root.provenance)){eligible=false;break;}
        const completedAt = terminalTimestamp(state);
        if (olderThanMs !== 0 && completedAt >= now - olderThanMs) { eligible = false; break; }
        const retained = await retainedForLiveEffects(current, readChild, childId => this.directory(childId));
        if (retained) { eligible = false; break; }
      }

      if (!eligible) {
        preservedRunIds.push(...family);
        continue;
      }

      // Preserve the original parent-first family deletion order; complete
      // resource/tree validation follows classification before the CAS commit.
      eligibleFamilies.push(family);
    }
    return { eligibleFamilies, preservedRunIds };
  }

  async list() {
    const runIds = await this.#historyRunIds();
    const runs = await boundedRead(runIds, 4, async id => {
      // Concurrent deletion is an explicit ENOENT, not a silently omitted row.
      const { state, sequence } = await this.observe(id);
      return { run_id: state.run_id, workflow_id: state.workflow_id, status: state.status,
        created_at: state.created_at, updated_at: state.updated_at, sequence };
    });
    return runs;
  }

  async listForThread(threadId, { onLookup } = {}) {
    requireValue(typeof threadId === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(threadId),
      'MODEL_THREAD_ID', 'Run lookup requires an authenticated conversation identity');
    requireValue(onLookup === undefined || typeof onLookup === 'function', 'RUN_LOOKUP_DIAGNOSTIC', 'Run lookup diagnostics require a callback');
    const startedAt = performance.now(); let inspected = 0;
    const result = await (async () => {
      await noSymlinks(this.root); const matches = [];
      const entries = await readdir(this.root, { withFileTypes: true }), pending = new Map();
      const reserved = entry => ['.pending', '.trash', '.run-locks', '.writer.lock', '.recovery.lock'].includes(entry.name);
      let next = 0, failedLocator;
      const fill = () => {
        while (next < entries.length && pending.size < 4) {
          const index = next++, entry = entries[index], job = {started:false};
          // Defer every fault to its original ordered position. Only locator
          // reads are prefetched; these objects never confer Run authority.
          job.result = (async () => {
            if (reserved(entry) || !entry.isDirectory() || entry.isSymbolicLink() || !/^run-.+\.run$/.test(entry.name)) return {};
            const id = workflowId(entry.name.slice(4, -4)); job.started = true;
            return {value:await readStartedEvent(join(this.directory(id), 'events.jsonl'))};
          })().catch(error => ({error}));
          pending.set(index, job);
        }
      };
      fill();
      try { for (const [index, entry] of entries.entries()) {
        const job = pending.get(index);
        if (reserved(entry)) { pending.delete(index); fill(); continue; }
        requireValue(entry.isDirectory() && !entry.isSymbolicLink() && /^run-.+\.run$/.test(entry.name), 'RUN_STORE_ENTRY', 'Unexpected Run store entry');
        const id = workflowId(entry.name.slice(4, -4));
        const located = await job.result;
        if (Object.hasOwn(located, 'error')) { failedLocator = job; throw located.error; }
        const started = located.value;
        inspected++;
        requireValue(started.payload?.state?.run_id === id, 'RUN_IDENTITY', 'Run start identity differs from its directory');
        // The locator supplies no authority, terminal state or resource grants.
        // Validate every exact candidate through the usual current read path.
        if (started.payload.state.constraints?.native_parent_thread_id === threadId) matches.push(await this.observe(id));
        pending.delete(index); fill();
      } } catch (error) {
        // Settle the bounded in-flight reads and preserve every ordered fault.
        const jobs = [...pending.values()], settled = await Promise.all(jobs.map(job => job.result));
        const additional = settled.flatMap((result,index) => jobs[index].started && jobs[index] !== failedLocator && Object.hasOwn(result, 'error') ? [result.error] : []);
        if (!additional.length) throw error;
        const failure = new AggregateError([error,...additional], 'Run lookup and prefetched metadata reads failed', {cause:error});
        if (typeof error?.code === 'string') failure.code = error.code;
        throw failure;
      }
      return matches;
    })();
    if (onLookup) await onLookup({ inspected_start_records: inspected, fully_validated_candidates: result.length, duration_ms: Math.round(performance.now() - startedAt) });
    return result;
  }
}
