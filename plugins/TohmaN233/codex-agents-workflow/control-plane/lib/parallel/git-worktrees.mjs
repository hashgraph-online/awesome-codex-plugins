import { spawn } from 'node:child_process';
import { writeFile, readFile, lstat, rm, open, readdir } from 'node:fs/promises';
import { join, resolve, sep, isAbsolute } from 'node:path';
import { randomUUID } from 'node:crypto';
import { ensureDirectory, insideRoot, noSymlinks, requireValue, workflowId, resourcePath, canonicalNoLinks } from '../workflow-paths.mjs';
import { pathBoundaries } from '../workflow-bindings.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { syncDirectory } from '../workflow-store.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';

const oid = value => typeof value === 'string' && /^[a-f0-9]{40,64}$/.test(value);
const key = value => process.platform === 'win32' ? resolve(value).toLowerCase() : resolve(value);
const equalPath = (left, right) => key(left) === key(right);
const samePhysicalPath = async (left, right) => equalPath(await canonicalNoLinks(left), await canonicalNoLinks(right));
const contains = (root, path) => key(path) === key(root) || key(path).startsWith(key(root) + sep);
const MAX_OUTPUT = 32 * 1024 * 1024;
async function missing(path) { try { await lstat(path); return false; } catch (error) { if (error.code === 'ENOENT') return true; throw error; } }

export function statusPaths(bytes) {
  const records = bytes.toString('utf8').split('\0'); const paths = [];
  for (let index = 0; index < records.length; index++) {
    const record = records[index]; if (!record) continue;
    requireValue(record.length > 3 && record[2] === ' ', 'GIT_STATUS_FORMAT', 'Unexpected Git status record');
    paths.push(record.slice(3));
    if (/[RC]/.test(record.slice(0, 2))) { requireValue(records[index + 1], 'GIT_STATUS_FORMAT', 'Missing rename source'); paths.push(records[++index]); }
  }
  return [...new Set(paths)].sort();
}

export class GitWorktrees {
  constructor(root, { binary = 'git', env = process.env, spawnImpl = spawn, timeoutMs = 30000 } = {}) {
    requireValue(isAbsolute(root), 'PARALLEL_ROOT', 'Worktree ownership root must be absolute');
    this.root = resolve(root); this.binary = binary; this.env = env;
    this.spawnImpl = spawnImpl; this.timeoutMs = timeoutMs; this.uncertain = null;
  }
  async initialize() {
    await ensureDirectory(this.root); await ensureDirectory(join(this.root, 'hooks'));
    const config = join(this.root, 'empty.gitconfig');
    try { await writeFile(config, '', { flag: 'wx', mode: 0o600 }); }
    catch (error) { if (error.code !== 'EEXIST') throw error; await noSymlinks(config); requireValue((await readFile(config)).length === 0, 'PARALLEL_CONFIG_CHANGED', 'Owned Git configuration was modified'); }
    return this;
  }
  async git(workspace, args, { input, allowed = [0], index } = {}) {
    const uncertainty = join(this.root, 'git-operation-uncertain.json');
    requireValue(!this.uncertain && await missing(uncertainty), 'PARALLEL_GIT_UNCERTAIN', 'A prior Git command has unconfirmed helper termination; retain all worktrees and inspect git-operation-uncertain.json before any further Git action');
    await noSymlinks(workspace);
    await noSymlinks(join(this.root, 'hooks'));
    requireValue((await readdir(join(this.root, 'hooks'))).length === 0, 'PARALLEL_HOOKS_CHANGED', 'Owned Git hook suppression directory must remain empty');
    await noSymlinks(join(this.root, 'empty.gitconfig'));
    requireValue((await readFile(join(this.root, 'empty.gitconfig'))).length === 0, 'PARALLEL_CONFIG_CHANGED', 'Owned Git configuration must remain empty');
    const env = Object.fromEntries(Object.entries(this.env).filter(([name]) => !name.toUpperCase().startsWith('GIT_')));
    Object.assign(env, { GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: join(this.root, 'empty.gitconfig'), GIT_TERMINAL_PROMPT: '0', GIT_LITERAL_PATHSPECS: '1',
      GIT_AUTHOR_NAME: 'Codex Agents Workflow', GIT_AUTHOR_EMAIL: 'workflow@localhost', GIT_COMMITTER_NAME: 'Codex Agents Workflow', GIT_COMMITTER_EMAIL: 'workflow@localhost' });
    if (index) { insideRoot(this.root, index); env.GIT_INDEX_FILE = index; }
    const fixed = ['--no-pager', '-c', 'core.hooksPath=' + join(this.root, 'hooks'), '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
      '-c', 'core.quotePath=false', '-c', 'diff.external=', '-c', 'submodule.recurse=false', '-c', 'protocol.file.allow=never', '-c', 'commit.gpgSign=false'];
    return new Promise((resolveResult, reject) => {
      const child = this.spawnImpl(this.binary, [...fixed, ...args], { cwd: workspace, env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
      const output = []; const diagnostic = []; let size = 0; let error;
      let audit = Promise.resolve(null); let stopTimer; let stopped = false;
      const uncertain = cause => {
        if (stopped) return; stopped = true;
        error = cause; this.uncertain = { code: cause.code, operation: args[0], workspace, parent_pid: process.pid, child_pid: child.pid ?? null, at: new Date().toISOString(), helper_termination_confirmed: false };
        // Parent termination does not establish descendant termination. Persist
        // that uncertainty and refuse subsequent apply/cleanup across restarts.
        audit = writeDurableJSON(uncertainty, this.uncertain).then(() => null, failure => failure);
        child.kill();
        stopTimer = setTimeout(async () => {
          const failure = await audit;
          child.stdin.destroy(); child.stdout.destroy(); child.stderr.destroy(); child.unref();
          reject(failure ? new AggregateError([error, failure], 'Git interruption and uncertainty audit persistence failed') : Object.assign(new Error('Git helper shutdown is unconfirmed; all worktrees remain retained'), { code: 'PARALLEL_GIT_STOP_UNCONFIRMED', cause: error }));
        }, 5000);
      };
      const timer = setTimeout(() => uncertain(Object.assign(new Error('Git operation exceeded its bounded deadline; worktrees retained'), { code: 'PARALLEL_GIT_TIMEOUT', operation: args[0] })), this.timeoutMs);
      child.on('error', cause => { error = Object.assign(new Error('Git process could not start'), { code: 'PARALLEL_GIT_START', cause }); });
      child.stdout.on('data', bytes => { size += bytes.length; if (size <= MAX_OUTPUT) output.push(bytes); else uncertain(Object.assign(new Error('Git output exceeded its limit'), { code: 'PARALLEL_GIT_LIMIT' })); });
      child.stderr.on('data', bytes => { size += bytes.length; if (size <= MAX_OUTPUT) diagnostic.push(bytes); else uncertain(Object.assign(new Error('Git diagnostic exceeded its limit'), { code: 'PARALLEL_GIT_LIMIT' })); });
      child.stdin.on('error', cause => { if (cause.code !== 'EPIPE') error = cause; });
      child.on('close', async (code, signal) => {
        clearTimeout(timer); clearTimeout(stopTimer);
        const auditFailure = await audit;
        if (auditFailure) return reject(new AggregateError([error, auditFailure], 'Git interruption and uncertainty audit persistence failed'));
        if (error) return reject(error);
        if (!allowed.includes(code)) return reject(Object.assign(new Error('Git operation failed'), { code: 'PARALLEL_GIT_FAILED', operation: args[0], exit_code: code, signal, diagnostic: Buffer.concat(diagnostic).toString('utf8').slice(-4000) }));
        resolveResult({ code, stdout: Buffer.concat(output), stderr: Buffer.concat(diagnostic).toString('utf8') });
      });
      child.stdin.end(input);
    });
  }
  async text(workspace, args, options) { return (await this.git(workspace, args, options)).stdout.toString('utf8').trim(); }
  async status(workspace, { includeIgnored = true } = {}) {
    const paths = statusPaths((await this.git(workspace, ['status', '--porcelain=v1', '-z', '--untracked-files=all'])).stdout);
    if (includeIgnored) paths.push(...(await this.git(workspace, ['ls-files', '--others', '-z'])).stdout.toString('utf8').split('\0').filter(Boolean));
    return [...new Set(paths)].sort();
  }
  async inspect(workspace, { clean = true } = {}) {
    await noSymlinks(workspace);
    const top = await this.text(workspace, ['rev-parse', '--show-toplevel']);
    requireValue(await samePhysicalPath(top, workspace), 'PARALLEL_REPOSITORY_ROOT', 'Parallel writes require the selected Git working-tree root', { git_root: top, requested_workspace: workspace });
    const common = await canonicalNoLinks(resolve(workspace, await this.text(workspace, ['rev-parse', '--git-common-dir']))); await noSymlinks(common);
    const drivers = await this.git(workspace, ['config', '--includes', '--name-only', '--get-regexp', '^(include\.path|includeif\..*\.path|filter\..*\.(smudge|clean|process)|merge\..*\.driver)$'], { allowed: [0, 1] });
    requireValue(drivers.code === 1, 'PARALLEL_GIT_DRIVER_UNSUPPORTED', 'Custom checkout filters, merge drivers or configuration includes are not qualified for owned worktrees');
    const base = await this.text(workspace, ['rev-parse', '--verify', 'HEAD^{commit}']); requireValue(oid(base), 'PARALLEL_BASE', 'Git HEAD must identify an existing commit');
    await this.validateTree(workspace, base);
    if (clean) requireValue(!(await this.status(workspace, { includeIgnored: false })).length, 'PARALLEL_WORKSPACE_DIRTY', 'Parallel launch requires a clean working tree, including untracked files');
    return { workspace: resolve(workspace), common_directory: common, base_commit: base };
  }
  async validateTree(workspace, tree) {
    requireValue(oid(tree), 'PARALLEL_TREE', 'Tree inspection requires a pinned Git object');
    const listing = (await this.git(workspace, ['ls-tree', '-r', '-z', tree])).stdout.toString('utf8').split('\0').filter(Boolean);
    requireValue(listing.length <= 100000, 'PARALLEL_TREE_LIMIT', 'Repository exceeds the bounded tree inventory');
    for (const entry of listing) {
      const match = /^(\d+) blob [a-f0-9]+\t(.+)$/s.exec(entry);
      requireValue(match && ['100644', '100755'].includes(match[1]), 'PARALLEL_TREE_UNSUPPORTED', 'Submodules, symbolic links and special entries are not qualified');
      resourcePath(match[2]);
    }
  }
  directory(owner) { workflowId(owner); return insideRoot(this.root, join(this.root, 'tree-' + owner)); }
  manifest(owner) { workflowId(owner); return insideRoot(this.root, join(this.root, 'owner-' + owner + '.json')); }
  async create(base, owner) {
    const workspace = this.directory(owner); const manifest = this.manifest(owner);
    requireValue(oid(base.base_commit), 'PARALLEL_BASE', 'Worktree creation needs an exact base commit');
    const source = await this.inspect(base.workspace, { clean: false });
    requireValue(equalPath(source.common_directory, base.common_directory), 'PARALLEL_REPOSITORY_CHANGED', 'Repository identity changed before worktree creation');
    await this.validateTree(base.workspace, base.base_commit);
    const ownership = { schema_version: 1, owner, workspace, repository: base.workspace, common_directory: base.common_directory, base_commit: base.base_commit };
    let exists = false;
    try { await noSymlinks(manifest); exists = true; requireValue(canonicalJSON(JSON.parse(await readFile(manifest, 'utf8'))) === canonicalJSON(ownership), 'PARALLEL_OWNER_CONFLICT', 'Owned worktree identity differs from its journal request'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (!exists) {
      try { await lstat(workspace); throw Object.assign(new Error('Unowned worktree directory already exists'), { code: 'PARALLEL_UNOWNED_PATH' }); } catch (error) { if (error.code !== 'ENOENT') throw error; }
      // Caller must journal creation intent before this side effect. Retain partial
      // creations on failure so exact ownership can be inspected, never guessed.
      const handle = await open(manifest, 'wx', 0o600);
      try { await handle.writeFile(canonicalJSON(ownership)); await handle.sync(); } finally { await handle.close(); }
      await syncDirectory(this.root);
      await this.git(base.workspace, ['worktree', 'add', '--detach', workspace, base.base_commit]);
    } else if (await missing(workspace)) {
      requireValue(!(await this.registered(base.workspace, workspace)), 'PARALLEL_PARTIAL_WORKTREE', 'Git retains a partially created worktree; inspect exact ownership before recovery');
      await this.git(base.workspace, ['worktree', 'add', '--detach', workspace, base.base_commit]);
    }
    await this.verify(ownership);
    return ownership;
  }
  async verify(ownership) {
    requireValue(equalPath(this.directory(ownership.owner), ownership.workspace), 'PARALLEL_OWNER_CONFLICT', 'Worktree does not belong to this ownership root');
    await noSymlinks(this.manifest(ownership.owner));
    requireValue(canonicalJSON(JSON.parse(await readFile(this.manifest(ownership.owner), 'utf8'))) === canonicalJSON(ownership), 'PARALLEL_OWNER_CONFLICT', 'Worktree ownership changed');
    const actual = await this.inspect(ownership.workspace, { clean: false });
    requireValue((await this.git(ownership.workspace, ['symbolic-ref', '-q', 'HEAD'], { allowed: [0, 1] })).code === 1, 'PARALLEL_WORKTREE_CHANGED', 'Owned worktrees must remain detached from user branches');
    requireValue(await samePhysicalPath(actual.common_directory, ownership.common_directory) && actual.base_commit === ownership.base_commit, 'PARALLEL_WORKTREE_CHANGED', 'Worktree Git identity or HEAD changed outside its owned execution');
    const marker = await readFile(join(ownership.workspace, '.git'), 'utf8');
    requireValue(marker.startsWith('gitdir: '), 'PARALLEL_WORKTREE_CHANGED', 'Owned worktree Git marker is invalid');
    const gitDir = resolve(ownership.workspace, marker.slice(8).trim());
    requireValue(contains(join(ownership.common_directory, 'worktrees'), gitDir), 'PARALLEL_WORKTREE_CHANGED', 'Owned worktree points outside the expected repository metadata');
    requireValue(await samePhysicalPath((await readFile(join(gitDir, 'gitdir'), 'utf8')).trim(), join(ownership.workspace, '.git')), 'PARALLEL_WORKTREE_CHANGED', 'Git worktree registration does not point back to its exact owned path');
    return actual;
  }
  async snapshot(workspace, baseCommit, allowedPaths, { includeIgnored = true, extraPaths = [] } = {}) {
    requireValue(oid(baseCommit), 'PARALLEL_BASE', 'Snapshot requires an exact base commit');
    await this.inspect(workspace, { clean: false });
    const scope = pathBoundaries(allowedPaths); const extra = [];
    for (const path of pathBoundaries(extraPaths)) {
      try { await lstat(insideRoot(workspace, join(workspace, path))); extra.push(path); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
    const changed = [...new Set([...(await this.status(workspace, { includeIgnored })), ...extra])].sort();
    const outside = changed.filter(path => !scope.some(root => contains(join(workspace, root), join(workspace, path))));
    requireValue(!outside.length, 'PARALLEL_SCOPE_VIOLATION', 'Worktree changed outside its effective branch scope', { changed_paths: changed, outside_paths: outside });
    for (const path of changed) {
      resourcePath(path); const absolute = insideRoot(workspace, join(workspace, path));
      try { await noSymlinks(absolute); const info = await lstat(absolute); requireValue(info.isFile() && info.nlink === 1 && info.size <= 8 * 1024 * 1024, 'PARALLEL_FILE_UNSUPPORTED', 'Changed files must be bounded regular files without links'); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
    const index = insideRoot(this.root, join(this.root, 'index-' + randomUUID())); let operationError;
    try {
      await this.git(workspace, ['read-tree', baseCommit], { index });
      if (changed.length) await this.git(workspace, ['add', '--all', '--force', '--', ...changed], { index });
      const tree = await this.text(workspace, ['write-tree'], { index }); requireValue(oid(tree), 'PARALLEL_TREE', 'Snapshot did not produce a tree'); await this.validateTree(workspace, tree);
      const patch = (await this.git(workspace, ['diff', '--binary', '--full-index', '--no-ext-diff', '--no-textconv', baseCommit, tree, '--'])).stdout;
      const commit = await this.text(workspace, ['commit-tree', tree, '-p', baseCommit], { input: 'Owned Workflow snapshot\n' });
      return { tree, commit, base_commit: baseCommit, changed_paths: changed, outside_paths: [], patch_sha256: digest(patch), patch };
    } catch (error) { operationError = error; throw error; }
    finally {
      try { await noSymlinks(index); await rm(insideRoot(this.root, index)); }
      catch (error) { if (error.code !== 'ENOENT') { if (operationError) throw new AggregateError([operationError, error], 'Snapshot and owned index cleanup failed'); throw error; } }
    }
  }
  async merge(repository, baseCommit, snapshots) {
    requireValue(snapshots.length >= 1 && snapshots.length <= 64 && snapshots.every(item => item.base_commit === baseCommit && oid(item.commit)), 'PARALLEL_MERGE_INPUT', 'Merge requires bounded branches from the exact same base');
    await this.inspect(repository, { clean: false });
    let commit = baseCommit;
    for (const snapshot of snapshots) {
      const merged = await this.git(repository, ['merge-tree', '--write-tree', commit, snapshot.commit], { allowed: [0, 1] });
      requireValue(merged.code === 0, 'PARALLEL_MERGE_CONFLICT', 'Branch changes conflict; main integration must resolve them explicitly', { branch_commit: snapshot.commit });
      const tree = merged.stdout.toString('utf8').split('\n')[0]; requireValue(oid(tree), 'PARALLEL_MERGE_RESULT', 'Merge did not return a pinned tree');
      await this.validateTree(repository, tree);
      commit = await this.text(repository, ['commit-tree', tree, '-p', commit, '-p', snapshot.commit], { input: 'Owned Workflow integration proposal\n' });
    }
    const tree = await this.text(repository, ['rev-parse', commit + '^{tree}']);
    const patch = (await this.git(repository, ['diff', '--binary', '--full-index', '--no-ext-diff', '--no-textconv', baseCommit, tree, '--'])).stdout;
    return { base_commit: baseCommit, commit, tree, patch_sha256: digest(patch), patch };
  }
  async apply(workspace, patch, expectedHash, authorize) {
    requireValue(typeof authorize === 'function', 'PARALLEL_APPLY_AUTHORITY', 'Integration requires a live authority check before Git can apply files');
    requireValue(Buffer.isBuffer(patch) && digest(patch) === expectedHash, 'PARALLEL_PATCH_CHANGED', 'Integration patch differs from the reviewed artifact');
    await this.inspect(workspace, { clean: false });
    if (!patch.length) return;
    await authorize();
    await this.git(workspace, ['apply', '--check', '--binary', '--whitespace=nowarn', '-'], { input: patch });
    await authorize();
    await this.git(workspace, ['apply', '--binary', '--whitespace=nowarn', '-'], { input: patch });
  }
  async registered(repository, workspace) {
    const records = (await this.git(repository, ['worktree', 'list', '--porcelain', '-z'])).stdout.toString('utf8').split('\0');
    for (const record of records) if (record.startsWith('worktree ') && await samePhysicalPath(record.slice(9), workspace)) return true;
    return false;
  }
  async remove(ownership, { reconcile = false, beforeRemove } = {}) {
    try { await this.verify(ownership); }
    catch (error) {
      if (!reconcile || error.code !== 'ENOENT' || !(await missing(ownership.workspace))) throw error;
      requireValue(equalPath(this.directory(ownership.owner), ownership.workspace), 'PARALLEL_OWNER_CONFLICT', 'Cleanup recovery path differs from its journal owner');
      const manifest = this.manifest(ownership.owner);
      if (!(await missing(manifest))) { await noSymlinks(manifest); requireValue(canonicalJSON(JSON.parse(await readFile(manifest, 'utf8'))) === canonicalJSON(ownership), 'PARALLEL_OWNER_CONFLICT', 'Cleanup recovery owner differs'); }
      if (await this.registered(ownership.repository, ownership.workspace)) {
        requireValue(!(await missing(manifest)), 'PARALLEL_OWNER_CONFLICT', 'Git registration has no retained owner proof');
        await this.git(ownership.repository, ['worktree', 'remove', '--force', ownership.workspace]);
      }
      if (!(await missing(manifest))) await rm(manifest);
      await syncDirectory(this.root); return { reconciled: true };
    }
    if (beforeRemove) await beforeRemove();
    // Both the absolute path and Git back-reference were checked above. Only an
    // explicitly owned temporary worktree is eligible for force removal.
    await this.git(ownership.repository, ['worktree', 'remove', '--force', ownership.workspace]);
    await noSymlinks(this.manifest(ownership.owner)); await rm(this.manifest(ownership.owner));
    await syncDirectory(this.root); return { reconciled: false };
  }
}
