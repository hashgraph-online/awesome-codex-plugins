import { lstat, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';

// A worker receipt owns only its declared products. Reading task inputs or
// renderer bookkeeping does not grant authority to freeze the whole directory.
async function capture(workspace, paths) {
  const entries = [];
  for (const path of paths) {
    const absolute = resolve(workspace,path); await noSymlinks(absolute);
    const before = await lstat(absolute);
    requireValue(before.isFile(), 'REQUIRED_ARTIFACT_MISSING', `Declared worker product is not a file: ${path}`);
    const content = await readFile(absolute), after = await lstat(absolute);
    requireValue(after.isFile() && before.dev === after.dev && before.ino === after.ino
      && before.size === after.size && content.length === before.size && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs,
      'MAIN_ORCHESTRATION_HOST_CHECK_STALE', `Declared worker product changed while being read: ${path}`);
    entries.push({path,bytes:content.length,sha256:digest(content)});
  }
  return {schema_version:1,coverage:'declared_products',workspace:resolve(workspace),entries};
}

export async function saveWorkerArtifactSnapshot(runtime,runId,slotId,workspace,paths) {
  return runtime.runs.saveArtifact(runId,`completion-snapshot-${slotId}`,canonicalJSON(await capture(workspace,paths)));
}

export async function readWorkerArtifactSnapshot(runtime,runId,workspace,paths,reference) {
  requireValue(reference && typeof reference === 'object','MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED','Declared worker products have no durable check snapshot');
  const saved=JSON.parse((await runtime.runs.readArtifact(runId,reference)).toString('utf8'));
  if(saved.schema_version===1 && saved.coverage==='whole_workspace' && saved.workspace===resolve(workspace) && Array.isArray(saved.entries)){
    // Immutable receipts from older runtimes retain their original bytes. Read
    // their explicit product proofs without reintroducing directory immutability.
    const entries=paths.map(path=>saved.entries.find(item=>item.path===path&&item.kind==='file'));
    requireValue(entries.every(Boolean),'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED','Legacy worker snapshot lacks a declared product');
    return {schema_version:1,coverage:'declared_products',workspace:resolve(workspace),entries:entries.map(({path,bytes,sha256})=>({path,bytes,sha256}))};
  }
  requireValue(saved.schema_version===1 && saved.coverage==='declared_products' && saved.workspace===resolve(workspace)
    && Array.isArray(saved.entries) && canonicalJSON(saved.entries.map(item=>item.path))===canonicalJSON(paths),
    'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED','Worker snapshot differs from its exact declared product paths');
  return saved;
}

export async function requireWorkerArtifactFreshness(runtime,runId,workspace,paths,reference) {
  const saved=await readWorkerArtifactSnapshot(runtime,runId,workspace,paths,reference),current=await capture(workspace,paths);
  requireValue(canonicalJSON(saved)===canonicalJSON(current),'MAIN_ORCHESTRATION_HOST_CHECK_STALE','Declared worker products changed after their completion check');
}
