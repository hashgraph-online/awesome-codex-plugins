import { lstat, readdir, readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { requireValue, statNoSymlinks } from '../workflow-paths.mjs';
import { pathBoundaries } from '../workflow-bindings.mjs';
import { isUnneededGeneratedCache } from './workspace-snapshot.mjs';

// Seal a check's declared inputs and outputs. An explicit workspace-wide
// contract still needs freshness coverage for the workspace it can read.
async function capture(workspace, declaredPaths) {
  const entries = []; let bytes = 0;
  const wholeWorkspace = !declaredPaths || declaredPaths.includes('.');
  const visit = async (absolute, path) => {
    const before = await lstat(absolute);
    requireValue(!before.isSymbolicLink(), 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', `Completion check workspace contains a symbolic link: ${path || '.'}`);
    if (before.isDirectory()) {
      entries.push({ path, kind: 'directory' });
      requireValue(entries.length <= 20000, 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', 'Completion check workspace exceeds its snapshot entry bound');
      const children = (await readdir(absolute,{withFileTypes:true})).sort((left,right)=>left.name<right.name?-1:left.name>right.name?1:0);
      for (const child of children) {
        const childPath = path ? `${path}/${child.name}` : child.name;
        if (declaredPaths && isUnneededGeneratedCache(child,childPath,declaredPaths)) continue;
        await visit(join(absolute,child.name),childPath);
      }
      return;
    }
    requireValue(before.isFile(), 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', `Completion check workspace contains an unsupported entry: ${path}`);
    bytes += before.size;
    requireValue(entries.length < 20000 && bytes <= 2 * 1024 * 1024 * 1024, 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', 'Completion check workspace exceeds its bounded content snapshot');
    const content = await readFile(absolute), after = await lstat(absolute);
    requireValue(after.isFile() && !after.isSymbolicLink() && before.dev === after.dev && before.ino === after.ino
      && before.size === after.size && content.length === before.size && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs,
      'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', `Completion check workspace changed while being read: ${path}`);
    entries.push({ path, kind: 'file', bytes: content.length, sha256: digest(content) });
  };
  if (wholeWorkspace) await visit(workspace,'');
  else for (const path of pathBoundaries(declaredPaths)) {
    const absolute = join(workspace,path);
    try { await statNoSymlinks(absolute); }
    catch(error) { if(error.code==='ENOENT')continue; throw error; }
    await visit(absolute,path);
  }
  return { schema_version: 1, coverage: wholeWorkspace?'whole_workspace':'declared_paths', workspace: resolve(workspace), entries,
    ...(declaredPaths ? {declared_paths:declaredPaths} : {}) };
}

export async function saveMainHostCheckSnapshot(runtime, runId, attemptId, workspace, declaredPaths = []) {
  return runtime.runs.saveArtifact(runId, `completion-snapshot-${attemptId}`, canonicalJSON(await capture(workspace,declaredPaths)));
}

export async function readMainHostCheckSnapshot(runtime, runId, workspace, reference) {
  requireValue(reference && typeof reference === 'object', 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED', 'Successful completion check has no durable workspace snapshot');
  const saved = JSON.parse((await runtime.runs.readArtifact(runId,reference)).toString('utf8'));
  requireValue(saved.schema_version === 1 && ['whole_workspace','declared_paths'].includes(saved.coverage) && saved.workspace === resolve(workspace)
    && Array.isArray(saved.entries) && saved.entries.length <= 20000, 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED', 'Completion check snapshot has no exact workspace content coverage');
  return saved;
}

export async function requireMainHostCheckFreshness(runtime, runId, workspace, reference) {
  const saved = await readMainHostCheckSnapshot(runtime,runId,workspace,reference), current = await capture(workspace,saved.declared_paths);
  requireValue(canonicalJSON(saved) === canonicalJSON(current), 'MAIN_ORCHESTRATION_HOST_CHECK_STALE',
    'Workspace content changed after the successful completion check; its receipt cannot accept the current products');
}
