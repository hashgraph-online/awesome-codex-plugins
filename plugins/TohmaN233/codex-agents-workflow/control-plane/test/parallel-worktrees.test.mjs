import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { tmpdir as osTmpdir } from 'node:os';
import { join, resolve, relative } from 'node:path';
import { GitWorktrees, statusPaths } from '../lib/parallel/git-worktrees.mjs';
import { spawn } from 'node:child_process';

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'parallel-git-')); const workspace = join(root, 'repository'); await mkdir(workspace);
  const git = await new GitWorktrees(join(root, 'owned')).initialize();
  await git.git(workspace, ['init', '-b', 'main']); await mkdir(join(workspace, 'src'));
  await writeFile(join(workspace, 'src', 'a.txt'), 'Base A\n'); await writeFile(join(workspace, 'src', 'b.txt'), 'Base B\n');
  await writeFile(join(workspace, '.gitignore'), 'ignored/\n'); await git.git(workspace, ['add', '--all']); await git.git(workspace, ['commit', '-m', 'Synthetic fixture']);
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  return { root, workspace, git, base: await git.inspect(workspace) };
}

test('Windows environment short paths resolve to the same Git root without accepting subdirectories', { skip: process.platform !== 'win32' }, async t => {
  const f = await fixture(t); const alias = join(osTmpdir(), relative(tmpdir(), f.workspace));
  const observed = await f.git.inspect(alias); assert.equal(observed.base_commit, f.base.base_commit); assert.equal(observed.common_directory, f.base.common_directory);
  await assert.rejects(f.git.inspect(join(alias, 'src')), { code: 'PARALLEL_REPOSITORY_ROOT' });
});
test('actual detached worktrees isolate disjoint edits and merge a proposal without changing the source workspace', async t => {
  const f = await fixture(t); const a = await f.git.create(f.base, 'branch-a'); const b = await f.git.create(f.base, 'branch-b');
  assert.notEqual(a.workspace, b.workspace);
  await Promise.all([writeFile(join(a.workspace, 'src', 'a.txt'), 'Changed A\n'), writeFile(join(b.workspace, 'src', 'b.txt'), 'Changed B\n')]);
  assert.equal(await readFile(join(a.workspace, 'src', 'b.txt'), 'utf8'), 'Base B\n');
  const [left, right] = await Promise.all([f.git.snapshot(a.workspace, f.base.base_commit, ['src/a.txt']), f.git.snapshot(b.workspace, f.base.base_commit, ['src/b.txt'])]);
  const proposal = await f.git.merge(f.workspace, f.base.base_commit, [left, right]);
  assert(proposal.patch.toString().includes('Changed A')); assert(proposal.patch.toString().includes('Changed B'));
  let checks = 0;
  await assert.rejects(f.git.apply(f.workspace, proposal.patch, proposal.patch_sha256, async () => { if (++checks === 2) throw Object.assign(new Error('Parent cancelled before apply'), { code: 'PARENT_CANCELLED' }); }), { code: 'PARENT_CANCELLED' });
  assert.equal(checks, 2);
  assert.deepEqual(await f.git.status(f.workspace), []); assert.equal(await readFile(join(f.workspace, 'src', 'a.txt'), 'utf8'), 'Base A\n');
  assert.equal((await f.git.create(f.base, 'branch-a')).workspace, a.workspace);
  await f.git.remove(a); await f.git.remove(b);
  await assert.rejects(readFile(join(a.workspace, '.git')), { code: 'ENOENT' });
});

test('an interrupted Git subprocess durably blocks later integration and cleanup across manager restart', async t => {
  const f = await fixture(t); let child;
  const interrupted = new GitWorktrees(f.git.root, { timeoutMs: 80, spawnImpl: (_binary, _args, options) => { child = spawn(process.execPath, ['-e', 'setInterval(() => {}, 1000)'], options); return child; } });
  await assert.rejects(interrupted.git(f.workspace, ['status']), { code: 'PARALLEL_GIT_TIMEOUT' });
  const report = JSON.parse(await readFile(join(f.git.root, 'git-operation-uncertain.json'), 'utf8')); assert.equal(report.child_pid, child.pid); assert.equal(report.helper_termination_confirmed, false);
  const restarted = await new GitWorktrees(f.git.root).initialize();
  await assert.rejects(restarted.status(f.workspace), { code: 'PARALLEL_GIT_UNCERTAIN' });
  assert.equal(await readFile(join(f.workspace, 'src', 'a.txt'), 'utf8'), 'Base A\n');
});

test('merge conflicts retain both branch edits and outside or ignored writes remain visible', async t => {
  const f = await fixture(t); const a = await f.git.create(f.base, 'left'); const b = await f.git.create(f.base, 'right');
  await writeFile(join(a.workspace, 'src', 'a.txt'), 'Left alternative\n'); await writeFile(join(b.workspace, 'src', 'a.txt'), 'Right alternative\n');
  const left = await f.git.snapshot(a.workspace, f.base.base_commit, ['src/a.txt']); const right = await f.git.snapshot(b.workspace, f.base.base_commit, ['src/a.txt']);
  await assert.rejects(f.git.merge(f.workspace, f.base.base_commit, [left, right]), { code: 'PARALLEL_MERGE_CONFLICT' });
  assert.equal(await readFile(join(a.workspace, 'src', 'a.txt'), 'utf8'), 'Left alternative\n'); assert.equal(await readFile(join(f.workspace, 'src', 'a.txt'), 'utf8'), 'Base A\n');
  await mkdir(join(a.workspace, 'ignored')); await writeFile(join(a.workspace, 'ignored', 'outside.txt'), 'Observable outside write');
  await assert.rejects(f.git.snapshot(a.workspace, f.base.base_commit, ['src']), error => error.code === 'PARALLEL_SCOPE_VIOLATION' && error.outside_paths.includes('ignored/outside.txt'));
});

test('dirty source, custom drivers, changed HEAD and unowned paths fail closed', async t => {
  const f = await fixture(t);
  await writeFile(join(f.workspace, 'untracked.txt'), 'User edit'); await assert.rejects(f.git.inspect(f.workspace), { code: 'PARALLEL_WORKSPACE_DIRTY' });
  await rm(join(f.workspace, 'untracked.txt'));
  await f.git.git(f.workspace, ['config', '--local', 'filter.synthetic.smudge', 'never execute this']);
  await assert.rejects(f.git.inspect(f.workspace), { code: 'PARALLEL_GIT_DRIVER_UNSUPPORTED' }); await f.git.git(f.workspace, ['config', '--local', '--unset', 'filter.synthetic.smudge']);
  await mkdir(f.git.directory('occupied')); await assert.rejects(f.git.create(f.base, 'occupied'), { code: 'PARALLEL_UNOWNED_PATH' });
  const own = await f.git.create(f.base, 'changed'); await writeFile(join(own.workspace, 'src', 'a.txt'), 'Unauthorized commit');
  await f.git.git(own.workspace, ['add', '--all']); await f.git.git(own.workspace, ['commit', '-m', 'Unexpected branch commit']);
  await assert.rejects(f.git.verify(own), { code: 'PARALLEL_WORKTREE_CHANGED' }); await assert.rejects(f.git.remove(own), { code: 'PARALLEL_WORKTREE_CHANGED' });
});

test('NUL status parsing preserves spaces and both sides of renamed paths', () => {
  assert.deepEqual(statusPaths(Buffer.from(' M src/a file.txt\0R  src/new.txt\0src/old.txt\0?? fresh.txt\0')), ['fresh.txt', 'src/a file.txt', 'src/new.txt', 'src/old.txt']);
});
