import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { watch } from 'node:fs';
import { lstat, readFile, readlink, realpath, stat } from 'node:fs/promises';
import {
  dirname,
  isAbsolute,
  relative,
  resolve,
  sep,
} from 'node:path';
import { promisify } from 'node:util';
import { connectorError } from './errors.mjs';

const execFileAsync = promisify(execFile);
const GLOB_RE = /[*?\[\]{}!]/;

async function git(workspace, args, { encoding = 'utf8' } = {}) {
  try {
    // Scope inspection is read-only. Git status otherwise refreshes the index
    // concurrently with metadata readers, causing Windows sharing violations.
    const result = await execFileAsync('git', ['--no-optional-locks', '-C', workspace, ...args], {
      encoding,
      windowsHide: true,
      timeout: 20_000,
      maxBuffer: 32 * 1024 * 1024,
    });
    return result.stdout || (encoding === 'buffer' ? Buffer.alloc(0) : '');
  } catch (error) {
    throw connectorError('WORKSPACE_NOT_GIT',
      `Connector work requires a Git repository: ${error.message}`,
      { actionRequired: 'Initialize Git or select a Git repository root.' });
  }
}

function samePath(left, right) {
  const normalizedLeft = resolve(left);
  const normalizedRight = resolve(right);
  return process.platform === 'win32'
    ? normalizedLeft.toLowerCase() === normalizedRight.toLowerCase()
    : normalizedLeft === normalizedRight;
}

function normalizeSlashes(value) {
  return String(value || '').replace(/\\/g, '/');
}

function comparePath(value) {
  const normalized = normalizeSlashes(value).replace(/^\.\//, '').replace(/\/$/, '');
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

function digestText(value) {
  return createHash('sha256').update(String(value || '')).digest('hex');
}

function isPathInside(root, candidate) {
  const rel = relative(root, candidate);
  return rel === '' || (!rel.startsWith(`..${sep}`) && rel !== '..' && !isAbsolute(rel));
}

async function nearestExistingParent(candidate, workspace) {
  let current = candidate;
  while (isPathInside(workspace, current)) {
    const info = await lstat(current).catch(() => null);
    if (info) return realpath(current);
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

export async function validateWorkspace(value) {
  if (typeof value !== 'string' || !isAbsolute(value)) {
    throw connectorError('WORKSPACE_INVALID', 'workspace must be an absolute existing directory');
  }
  const requested = resolve(value);
  const info = await stat(requested).catch(() => null);
  if (!info?.isDirectory()) {
    throw connectorError('WORKSPACE_INVALID', `workspace is not an existing directory: ${requested}`);
  }
  const canonicalWorkspace = await realpath(requested);
  const topLevelRaw = (await git(canonicalWorkspace, ['rev-parse', '--show-toplevel'])).trim();
  const topLevel = await realpath(topLevelRaw);
  if (!samePath(topLevel, canonicalWorkspace)) {
    throw connectorError('WORKSPACE_NOT_GIT_ROOT',
      `workspace must be the Git repository root: ${topLevel}`,
      { actionRequired: 'Select the repository root rather than a nested directory.' });
  }
  return canonicalWorkspace;
}

export async function validateAllowedPaths(workspace, values, { required = false } = {}) {
  const root = await validateWorkspace(workspace);
  const rawValues = Array.isArray(values) ? values : [];
  if (required && rawValues.length === 0) {
    throw connectorError('ALLOWED_PATHS_REQUIRED',
      'bounded-write connector tasks require at least one workspace-relative allowed_paths entry');
  }
  const seen = new Set();
  const result = [];
  for (const [index, rawValue] of rawValues.entries()) {
    if (typeof rawValue !== 'string') {
      throw connectorError('ALLOWED_PATH_INVALID', `allowed_paths[${index}] must be a string`);
    }
    const raw = normalizeSlashes(rawValue.trim());
    if (!raw) {
      throw connectorError('ALLOWED_PATH_INVALID', `allowed_paths[${index}] must name a bounded path`);
    }
    if (GLOB_RE.test(raw)) {
      throw connectorError('ALLOWED_PATH_INVALID', `allowed_paths[${index}] must not contain a glob: ${raw}`);
    }
    if (isAbsolute(raw) || /^[A-Za-z]:\//.test(raw)) {
      throw connectorError('ALLOWED_PATH_INVALID', `allowed_paths[${index}] must be workspace-relative: ${raw}`);
    }
    if (raw === '.' || raw === './') { if(!seen.has('.')) {seen.add('.');result.push('.');} continue; }
    const absolute = resolve(root, raw);
    if (!isPathInside(root, absolute) || samePath(root, absolute)) {
      throw connectorError('ALLOWED_PATH_ESCAPE', `allowed path escapes or covers the entire workspace: ${raw}`);
    }
    const parent = await nearestExistingParent(absolute, root);
    if (!parent || !isPathInside(root, parent)) {
      throw connectorError('ALLOWED_PATH_ESCAPE', `allowed path resolves outside the workspace: ${raw}`);
    }
    const canonicalRelative = normalizeSlashes(relative(root, absolute));
    const key = comparePath(canonicalRelative);
    if (!seen.has(key)) {
      seen.add(key);
      result.push(canonicalRelative);
    }
  }
  result.sort((left, right) => comparePath(left).localeCompare(comparePath(right)));
  return result;
}

export function pathAllowed(relativePath, allowedPaths) {
  const candidate = comparePath(relativePath);
  return (allowedPaths || []).some((allowed) => {
    const boundary = comparePath(allowed);
    if(boundary==='.')return Boolean(candidate) && !candidate.startsWith('/') && !/^[a-z]:/i.test(candidate) && !candidate.split('/').includes('..');
    return candidate === boundary || candidate.startsWith(`${boundary}/`);
  });
}

function pathIsAllowedBoundaryAncestor(relativePath, allowedPaths) {
  const candidate = comparePath(relativePath);
  if (!candidate) return false;
  return (allowedPaths || []).some((allowed) => {
    const boundary = comparePath(allowed);
    return boundary.startsWith(`${candidate}/`);
  });
}

async function fileFingerprint(workspace, relativePath, diffByPath) {
  const hash = createHash('sha256');
  hash.update(relativePath);
  hash.update('\0');
  hash.update(diffByPath || '');
  const absolute = resolve(workspace, relativePath);
  const info = await lstat(absolute).catch(() => null);
  if (!info) {
    hash.update('\0missing');
    return hash.digest('hex');
  }
  hash.update(`\0${info.mode}\0${info.size}`);
  if (info.isSymbolicLink()) {
    hash.update('\0symlink\0');
    hash.update(await readlink(absolute));
  } else if (info.isFile()) {
    hash.update('\0file\0');
    hash.update(await readFile(absolute));
  } else if (info.isDirectory()) {
    hash.update('\0directory');
  } else {
    hash.update('\0other');
  }
  return hash.digest('hex');
}

async function statusPaths(workspace) {
  const raw = await git(workspace, ['status', '--porcelain=v1', '-z', '--untracked-files=all', '--']);
  const parts = raw.split('\0').filter(Boolean);
  const paths = [];
  for (let index = 0; index < parts.length; index += 1) {
    const row = parts[index];
    if (row.length < 4) continue;
    const statusCode = row.slice(0, 2);
    let relativePath = row.slice(3);
    if ((statusCode.includes('R') || statusCode.includes('C')) && parts[index + 1]) {
      paths.push(parts[index + 1]);
      index += 1;
    }
    paths.push(relativePath);
  }
  return [...new Set(paths.map(normalizeSlashes).filter(Boolean))];
}

async function captureGitMetadata(workspace) {
  const [head, refs, indexStage, indexFlags, localConfig, reflog] = await Promise.all([
    git(workspace, ['rev-parse', 'HEAD']),
    git(workspace, ['for-each-ref', '--format=%(refname)%00%(objectname)']),
    git(workspace, ['ls-files', '--stage', '-z']),
    git(workspace, ['ls-files', '-v', '-z']),
    git(workspace, ['config', '--local', '--null', '--list']),
    git(workspace, ['reflog', '--all', '--format=%H%x00%gD%x00%gs']).catch(() => ''),
  ]);
  return {
    head: String(head).trim(),
    refs_sha256: digestText(refs),
    index_sha256: digestText(`${indexStage}\0${indexFlags}`),
    config_sha256: digestText(localConfig),
    reflog_sha256: digestText(reflog),
  };
}

export async function captureWorkspaceSnapshot(workspace) {
  const root = await validateWorkspace(workspace);
  const [paths, gitMetadata] = await Promise.all([
    statusPaths(root),
    captureGitMetadata(root),
  ]);
  const entries = {};
  for (const relativePath of paths.sort((a, b) => comparePath(a).localeCompare(comparePath(b)))) {
    const diff = await git(root, ['diff', '--binary', 'HEAD', '--', relativePath]);
    entries[relativePath] = await fileFingerprint(root, relativePath, diff);
  }
  const digest = createHash('sha256');
  for (const [relativePath, fingerprint] of Object.entries(entries)) {
    digest.update(relativePath);
    digest.update('\0');
    digest.update(fingerprint);
    digest.update('\0');
  }
  for (const field of ['head', 'refs_sha256', 'index_sha256', 'config_sha256', 'reflog_sha256']) {
    digest.update(field);
    digest.update('\0');
    digest.update(String(gitMetadata[field] || ''));
    digest.update('\0');
  }
  return {
    version: 1,
    workspace: root,
    digest: digest.digest('hex'),
    entries,
    git_metadata: gitMetadata,
    captured_at: new Date().toISOString(),
  };
}

export function compareSnapshots(baseline, observed) {
  const keys = new Set([
    ...Object.keys(baseline?.entries || {}),
    ...Object.keys(observed?.entries || {}),
  ]);
  const changedPaths = [...keys]
    .filter((path) => baseline?.entries?.[path] !== observed?.entries?.[path])
    .sort((left, right) => comparePath(left).localeCompare(comparePath(right)));
  return changedPaths;
}

export async function verifyWorkspaceScope(workspace, baseline, {
  readOnly,
  allowedPaths = [],
  preventedAttempts = [],
  runtimeAttempts = [],
} = {}) {
  const observed = await captureWorkspaceSnapshot(workspace);
  const changedPaths = compareSnapshots(baseline, observed);
  const metadataChanges = [];
  const baselineMetadata = baseline?.git_metadata || {};
  const observedMetadata = observed.git_metadata || {};
  for (const [field, label] of [
    ['head', '<git-head>'],
    ['refs_sha256', '<git-refs>'],
    ['index_sha256', '<git-index>'],
    ['config_sha256', '<git-config>'],
    ['reflog_sha256', '<git-reflog>'],
  ]) {
    if (baselineMetadata[field] !== observedMetadata[field]) metadataChanges.push(label);
  }
  const outsidePaths = readOnly
    ? [...changedPaths, ...metadataChanges]
    : [
      ...changedPaths.filter((path) => !pathAllowed(path, allowedPaths)),
      ...metadataChanges,
    ];
  const prevented = [
    ...(Array.isArray(preventedAttempts) ? preventedAttempts : []),
    ...(Array.isArray(runtimeAttempts) ? runtimeAttempts : []),
  ];
  const uniqueOutside = [...new Set(outsidePaths)];
  const compliant = uniqueOutside.length === 0 && prevented.length === 0;
  return {
    read_only: readOnly === true,
    allowed_paths: [...allowedPaths],
    changed_paths: changedPaths,
    metadata_changes: metadataChanges,
    outside_paths: uniqueOutside,
    prevented_attempts: prevented,
    compliant,
    unchanged: changedPaths.length === 0 && metadataChanges.length === 0,
    baseline_digest: baseline?.digest || null,
    observed_digest: observed.digest,
    baseline_git_metadata: baselineMetadata,
    observed_git_metadata: observedMetadata,
  };
}

export function runtimeWatchReasonIsViolation(reason) {
  return !['allowed_path', 'allowed_path_ancestor', 'unknown_path'].includes(reason);
}

export function startWorkspaceScopeMonitor(workspace, {
  readOnly,
  allowedPaths = [],
  onViolation = null,
} = {}) {
  const violations = [];
  const observed = [];
  const seen = new Set();
  let closed = false;
  const record = (eventType, filename, reason) => {
    const relativePath = filename
      ? normalizeSlashes(String(filename)).replace(/^\.\//, '')
      : '<unknown-workspace-change>';
    if (relativePath === '.git' || relativePath.startsWith('.git/')) return;
    const key = `${eventType}:${comparePath(relativePath)}:${reason}`;
    if (seen.has(key)) return;
    seen.add(key);
    const entry = {
      source: 'runtime_watch',
      event_type: eventType,
      path: relativePath,
      reason,
      observed_at: new Date().toISOString(),
    };
    observed.push(entry);
    // fs.watch may occasionally omit the filename on Windows. Keep that event
    // as telemetry, but defer the decision to the terminal full-workspace
    // snapshot, which still rejects every actual changed path outside scope.
    // Known outside paths and watcher errors continue to fail closed at once.
    if (runtimeWatchReasonIsViolation(reason)) {
      violations.push(entry);
      if (typeof onViolation === 'function') {
        Promise.resolve(onViolation(entry)).catch(() => {});
      }
    }
  };
  let watcher;
  try {
    watcher = watch(workspace, { recursive: true, persistent: false, encoding: 'utf8' },
      (eventType, filename) => {
        if (closed) return;
        const relativePath = filename
          ? normalizeSlashes(String(filename)).replace(/^\.\//, '')
          : '';
        const reason = !relativePath
          ? 'unknown_path'
          : readOnly
            ? 'read_only'
            : pathAllowed(relativePath, allowedPaths)
              ? 'allowed_path'
              : pathIsAllowedBoundaryAncestor(relativePath, allowedPaths)
                ? 'allowed_path_ancestor'
                : 'outside_allowed_paths';
        record(eventType, filename, reason);
      });
  } catch (error) {
    throw connectorError('SCOPE_MONITOR_UNAVAILABLE',
      `Could not establish the recursive workspace scope monitor: ${error.message}`, {
        actionRequired: 'Use a local filesystem supported by Node recursive fs.watch.',
      });
  }
  watcher.on('error', (error) => record('watch_error', null, `watch_error:${error.message}`));
  return {
    observed,
    violations,
    close() {
      if (closed) return;
      closed = true;
      watcher.close();
    },
  };
}
