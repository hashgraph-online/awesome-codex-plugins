import { lstat, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { noSymlinks, requireValue, workflowId } from './workflow-paths.mjs';
import { canonicalJSON } from './workflow-revisions.mjs';
import { writeDurableJSON } from './workflow-events.mjs';

// Access only under store admission. An absent witness is the pre-upgrade
// store's revision zero; sanctioned writers never remove or reset the witness.
export async function readHistoryRevision(root) {
  const path = join(root, '.run-locks', 'history-revision.json');
  try { await noSymlinks(path); }
  catch (error) { if (error.code === 'ENOENT' && error.path === path) return { revision: 0, runs: {} }; throw error; }
  const info = await lstat(path);
  requireValue(info.isFile() && info.nlink === 1 && info.size <= 16 * 1024 * 1024,
    'RUN_HISTORY_REVISION', 'History revision must be a bounded regular file');
  const bytes = await readFile(path);
  requireValue(bytes.length <= 16 * 1024 * 1024, 'RUN_HISTORY_REVISION', 'History revision grew beyond its bound');
  const value = JSON.parse(bytes.toString('utf8'));
  requireValue(value.schema_version === 1 && Number.isSafeInteger(value.revision) && value.revision > 0,
    'RUN_HISTORY_REVISION', 'History revision must have its exact monotonic identity');
  requireValue(value.runs && typeof value.runs === 'object' && !Array.isArray(value.runs)
    && Object.values(value.runs).every(epoch => Number.isSafeInteger(epoch) && epoch > 0 && epoch <= value.revision),
    'RUN_HISTORY_REVISION', 'History Run epochs must belong to the store revision');
  return value;
}

export async function advanceHistoryRevision(root, id, { removing = false } = {}) {
  workflowId(id);
  const current = await readHistoryRevision(root), revision = current.revision + 1;
  requireValue(current.revision < Number.MAX_SAFE_INTEGER, 'RUN_HISTORY_REVISION_EXHAUSTED', 'History revision cannot wrap');
  if (removing) delete current.runs[id];
  else Object.defineProperty(current.runs, id, { value: revision, enumerable: true, configurable: true, writable: true });
  // Durable before the first effect, including a failed or interrupted writer.
  const next = { schema_version: 1, revision, runs: current.runs };
  requireValue(Buffer.byteLength(canonicalJSON(next)) + 1 <= 16 * 1024 * 1024,
    'RUN_HISTORY_REVISION', 'History revision exceeds its bound');
  await writeDurableJSON(join(root, '.run-locks', 'history-revision.json'), next);
}

export function historyEpoch(witness, id) { return Object.hasOwn(witness.runs, id) ? witness.runs[id] : 0; }
