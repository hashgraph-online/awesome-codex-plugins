import { lstat, readdir, readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';

// The check can read arbitrary task inputs. Write grants cannot prove which
// bytes affect its verdict, so pin the whole workspace, including .git and
// directory topology. Unlike a scope audit, incomplete read coverage is fatal.
async function capture(workspace) {
  const entries = []; let bytes = 0;
  const visit = async (absolute, path) => {
    const before = await lstat(absolute);
    requireValue(!before.isSymbolicLink(), 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', `Completion check workspace contains a symbolic link: ${path || '.'}`);
    if (before.isDirectory()) {
      entries.push({ path, kind: 'directory' });
      requireValue(entries.length <= 20000, 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT', 'Completion check workspace exceeds its snapshot entry bound');
      for (const name of (await readdir(absolute)).sort()) await visit(join(absolute,name),path ? `${path}/${name}` : name);
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
  await visit(workspace,'');
  return { schema_version: 1, coverage: 'whole_workspace', workspace: resolve(workspace), entries };
}

export async function saveMainHostCheckSnapshot(runtime, runId, attemptId, workspace) {
  return runtime.runs.saveArtifact(runId, `completion-snapshot-${attemptId}`, canonicalJSON(await capture(workspace)));
}

export async function readMainHostCheckSnapshot(runtime, runId, workspace, reference) {
  requireValue(reference && typeof reference === 'object', 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED', 'Successful completion check has no durable workspace snapshot');
  const saved = JSON.parse((await runtime.runs.readArtifact(runId,reference)).toString('utf8'));
  requireValue(saved.schema_version === 1 && saved.coverage === 'whole_workspace' && saved.workspace === resolve(workspace)
    && Array.isArray(saved.entries) && saved.entries.length <= 20000, 'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED', 'Completion check snapshot has no exact workspace content coverage');
  return saved;
}

export async function requireMainHostCheckFreshness(runtime, runId, workspace, reference) {
  const saved = await readMainHostCheckSnapshot(runtime,runId,workspace,reference), current = await capture(workspace);
  requireValue(canonicalJSON(saved) === canonicalJSON(current), 'MAIN_ORCHESTRATION_HOST_CHECK_STALE',
    'Workspace content changed after the successful completion check; its receipt cannot accept the current products');
}
