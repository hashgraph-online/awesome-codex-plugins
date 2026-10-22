import { lstat, open, readFile, rename, unlink } from 'node:fs/promises';
import { dirname } from 'node:path';
import { randomUUID } from 'node:crypto';
import { canonicalJSON, digest } from './workflow-revisions.mjs';
import { noSymlinks, statNoSymlinks, requireValue } from './workflow-paths.mjs';
import { syncDirectory } from './workflow-store.mjs';

const MAX_JOURNAL = 128 * 1024 * 1024;
const MAX_EVENT = 4 * 1024 * 1024;
// Runtime registration is Host state. Rebinding never rewrites the initial pin.
const ENVIRONMENT_EVENTS = ['runtime_environment_attention', 'runtime_environment_rebound'];
export const EVENT_KINDS = new Set(['generation_repair', 'generation_projection', 'generation_review_recheck', 'started', 'claim', 'complete', 'fail', 'retry', 'cancel', 'pause', 'resume', 'approve', 'dispatch_intent', 'dispatch_receipt', 'host_tool_intent', 'host_tool_receipt', 'usage', 'executor_event', 'completion_turn', 'main_item_result', 'native_agent_rejection', 'native_serial_result', 'native_parallel_result', 'native_item_results', 'native_host_check_proposal', 'managed_native_results', 'recover', 'control_recovery', 'child_intent', 'child_started']);
for (const kind of ENVIRONMENT_EVENTS) EVENT_KINDS.add(kind);
EVENT_KINDS.add('native_spawn_batch');
EVENT_KINDS.add('native_text_amendment');
EVENT_KINDS.add('native_dispatch_span');
EVENT_KINDS.add('shared_host_projection');
for (const kind of ['reattach', 'connector_control', 'execution_drain', 'parent_execution_lost', 'host_main_advance_failed', 'host_main_worker_start_failed', 'workspace_input_bound', 'parallel_intent', 'parallel_base', 'parallel_branch', 'parallel_ready', 'parallel_proposal', 'parallel_apply_intent', 'parallel_integrated', 'parallel_error', 'parallel_cleanup']) EVENT_KINDS.add(kind);

export function decodeEvents(bytes, { allowTornTail = false } = {}) {
  const buffer = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes);
  requireValue(buffer.length <= MAX_JOURNAL, 'RUN_JOURNAL_LIMIT', 'Run journal exceeds its size limit');
  const completeLength = buffer.length && buffer.at(-1) !== 10 ? buffer.lastIndexOf(10) + 1 : buffer.length;
  const tail = buffer.subarray(completeLength);
  requireValue(allowTornTail || !tail.length, 'RUN_JOURNAL_TORN', 'Run has an uncommitted journal tail; recover before mutation');
  const lines = buffer.subarray(0, completeLength).toString('utf8');
  const events = lines ? lines.slice(0, -1).split('\n').map(line => {
    requireValue(Buffer.byteLength(line) <= MAX_EVENT, 'RUN_EVENT_LIMIT', 'Run event is oversized');
    return JSON.parse(line);
  }) : [];
  let previous = null;
  for (const [index, event] of events.entries()) {
    const { hash, ...content } = event;
    requireValue(content.sequence === index + 1 && content.previous === previous && digest(canonicalJSON(content)) === hash, 'RUN_JOURNAL_CORRUPT', 'Run journal hash chain is invalid');
    requireValue(EVENT_KINDS.has(content.kind) && (index === 0 ? content.kind === 'started' : content.kind !== 'started'), 'RUN_EVENT_KIND', 'Unexpected Run event kind/order');
    previous = hash;
  }
  return { events, tail, completeLength };
}

export async function readEvents(path, options) {
  const {stat:info} = await statNoSymlinks(path);
  requireValue(info.isFile() && info.size <= MAX_JOURNAL, 'RUN_JOURNAL_LIMIT', 'Run journal must be a bounded regular file');
  return decodeEvents(await readFile(path), options);
}

// The first committed record is immutable and contains the conversation binding.
// Candidate discovery must not replay unrelated histories or read their resources.
// This is a verified locator; execution still reads the selected complete journal.
export async function readStartedEvent(path) {
  await noSymlinks(path);
  const file = await open(path, 'r');
  try {
    const info = await file.stat();
    requireValue(info.isFile() && info.size <= MAX_JOURNAL, 'RUN_JOURNAL_LIMIT', 'Run journal must be a bounded regular file');
    const chunks = []; let length = 0;
    for (;;) {
      const buffer = Buffer.alloc(Math.min(4096, MAX_EVENT + 1 - length));
      const { bytesRead } = await file.read(buffer, 0, buffer.length, length);
      requireValue(bytesRead > 0, 'RUN_START_MISSING', 'Run has no complete committed start event');
      const bytes = buffer.subarray(0, bytesRead), newline = bytes.indexOf(10);
      chunks.push(newline < 0 ? bytes : bytes.subarray(0, newline + 1));
      length += newline < 0 ? bytesRead : newline + 1;
      requireValue(length <= MAX_EVENT + 1, 'RUN_EVENT_LIMIT', 'Run start event is oversized');
      if (newline >= 0) return decodeEvents(Buffer.concat(chunks)).events[0];
      requireValue(length <= MAX_EVENT, 'RUN_EVENT_LIMIT', 'Run start event is oversized');
    }
  } finally { await file.close(); }
}

export async function appendEvent(path, events, kind, payload) {
  return (await appendEvents(path,events,[{kind,payload,at:new Date().toISOString()}]))[0];
}

// Caller holds the original writer. Every record retains its own timestamp,
// sequence, patch and hash; only the physical append/sync is amortized.
export async function appendEvents(path, events, records) {
  requireValue(Array.isArray(records)&&records.length>0&&records.length<=64,'RUN_EVENT_BATCH_LIMIT','Journal batch must contain 1..64 records');
  let previous=events.at(-1)?.hash??null;
  const committed=records.map(({kind,payload,at},index)=>{
    requireValue(EVENT_KINDS.has(kind),'RUN_EVENT_KIND','Unknown Run event');
    requireValue(typeof at==='string'&&new Date(at).toISOString()===at,'RUN_EVENT_TIMESTAMP','Invalid journal timestamp');
    const content={sequence:events.length+index+1,previous,kind,at,payload};
    const event={...content,hash:digest(canonicalJSON(content))};previous=event.hash;return event;
  });
  const lines=committed.map(event=>{const line=canonicalJSON(event)+'\n';
    requireValue(Buffer.byteLength(line)<=MAX_EVENT,'RUN_EVENT_LIMIT','Run event exceeds its size limit');return line;});
  const bytes=lines.join('');
  await noSymlinks(dirname(path));
  let currentSize = 0;
  try { await noSymlinks(path); currentSize = (await lstat(path)).size; }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  requireValue(currentSize + Buffer.byteLength(bytes) <= MAX_JOURNAL, 'RUN_JOURNAL_LIMIT', 'Run journal is full; dependent execution is blocked');
  const file = await open(path, events.length ? 'a' : 'wx', 0o600);
  try { await file.writeFile(bytes); await file.sync(); } finally { await file.close(); }
  return committed;
}

export async function writeDurableJSON(path, value) {
  const temporary = path + '.write-' + randomUUID();
  await noSymlinks(dirname(path));
  let file;
  try {
    file = await open(temporary, 'wx', 0o600);
    await file.writeFile(canonicalJSON(value) + '\n'); await file.sync();
    await file.close(); file = undefined;
    try { await noSymlinks(path); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    await rename(temporary, path); await syncDirectory(dirname(path));
  } finally {
    if (file) await file.close();
    try { await unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
}

// Caller must hold the Run writer lock. Complete records are never discarded.
export async function recoverEventTail(path) {
  const decoded = await readEvents(path, { allowTornTail: true });
  if (!decoded.tail.length) return { ...decoded, recovered: null };
  const bytes = await readFile(path);
  const originalHash = digest(bytes);
  const quarantine = path + '.torn-' + randomUUID();
  const backup = await open(quarantine, 'wx', 0o600);
  try { await backup.writeFile(bytes); await backup.sync(); } finally { await backup.close(); }
  const temporary = path + '.repair-' + randomUUID();
  const replacement = await open(temporary, 'wx', 0o600);
  try { await replacement.writeFile(bytes.subarray(0, decoded.completeLength)); await replacement.sync(); } finally { await replacement.close(); }
  try {
    requireValue(digest(await readFile(path)) === originalHash, 'RUN_JOURNAL_CHANGED', 'Journal changed during recovery');
    await rename(temporary, path); await syncDirectory(dirname(path));
  } finally { try { await unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; } }
  return { ...decoded, recovered: { retained_at: quarantine, sha256: originalHash, tail_bytes: decoded.tail.length } };
}

export function statePatch(previous, next) {
  for (const field of ['host_startup_sha256','host_startup_key']) requireValue(
    Object.hasOwn(previous.constraints ?? {}, field) === Object.hasOwn(next.constraints ?? {}, field)
    && previous.constraints?.[field] === next.constraints?.[field],
    'RUN_STARTUP_IDENTITY', 'A transition cannot change its Host startup identity');
  requireValue(Object.hasOwn(previous.constraints ?? {}, 'native_parent_thread_id') === Object.hasOwn(next.constraints ?? {}, 'native_parent_thread_id')
    && previous.constraints?.native_parent_thread_id === next.constraints?.native_parent_thread_id,
    'RUN_THREAD_IDENTITY', 'A transition cannot change the initiating conversation');
  const patch = { fields: {}, nodes: {}, edges: {}, approvals: {} };
  for (const key of Object.keys(previous)) requireValue(Object.hasOwn(next, key), 'RUN_STATE_SHAPE', 'Run state cannot silently drop fields');
  for (const [key, value] of Object.entries(next)) {
    if (['nodes', 'edges', 'approvals'].includes(key)) {
      for (const id of Object.keys(previous[key] ?? {})) requireValue(Object.hasOwn(value, id), 'RUN_STATE_SHAPE', 'Run state cannot silently drop entries');
      for (const [id, item] of Object.entries(value)) if (!Object.hasOwn(previous[key] ?? {}, id) || canonicalJSON(previous[key][id]) !== canonicalJSON(item)) Object.defineProperty(patch[key], id, { value: item, enumerable: true });
    } else if (!Object.hasOwn(previous, key) || canonicalJSON(previous[key]) !== canonicalJSON(value)) Object.defineProperty(patch.fields, key, { value, enumerable: true });
  }
  return patch;
}

export function replayEvents(events) {
  requireValue(events.length && events[0].kind === 'started', 'RUN_START_MISSING', 'Run has no committed start event');
  let state = structuredClone(events[0].payload.state);
  for (const event of events.slice(1)) {
    const patch = event.payload.patch;
    requireValue(patch && patch.fields && patch.nodes && patch.edges && patch.approvals, 'RUN_STATE_SHAPE', 'Run transition has no complete patch envelope');
    if (Object.hasOwn(patch.fields, 'constraints')) for (const field of ['host_startup_sha256','host_startup_key']) requireValue(
      Object.hasOwn(state.constraints ?? {}, field) === Object.hasOwn(patch.fields.constraints ?? {}, field)
      && state.constraints?.[field] === patch.fields.constraints?.[field],
      'RUN_STARTUP_IDENTITY', 'Run history cannot change its Host startup identity');
    requireValue(!Object.hasOwn(patch.fields, 'constraints') || Object.hasOwn(patch.fields.constraints ?? {}, 'native_parent_thread_id') === Object.hasOwn(state.constraints ?? {}, 'native_parent_thread_id')
      && patch.fields.constraints?.native_parent_thread_id === state.constraints?.native_parent_thread_id,
      'RUN_THREAD_IDENTITY', 'Run history cannot change the initiating conversation');
    state = {
      ...state, ...patch.fields,
      nodes: { ...state.nodes, ...patch.nodes }, edges: { ...state.edges, ...patch.edges }, approvals: { ...state.approvals, ...patch.approvals },
    };
  }
  return state;
}
