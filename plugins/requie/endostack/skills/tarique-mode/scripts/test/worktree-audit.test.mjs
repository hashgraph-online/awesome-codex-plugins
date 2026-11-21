import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import * as os from 'node:os';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync, realpathSync, utimesSync } from 'node:fs';
import { execFileSync, spawnSync } from 'node:child_process';
import { bucketFor, humanSize, parseArgs, pathNeedles, defaultTranscriptDirs, COLUMNS } from '../worktree-audit.mjs';

const script = new URL('../worktree-audit.mjs', import.meta.url).pathname;
const env = {
  ...process.env,
  GIT_AUTHOR_NAME: 'Test',
  GIT_AUTHOR_EMAIL: 'test@example.com',
  GIT_COMMITTER_NAME: 'Test',
  GIT_COMMITTER_EMAIL: 'test@example.com',
  GIT_CONFIG_NOSYSTEM: '1',
  GIT_TERMINAL_PROMPT: '0',
  ENDOSTACK_TRANSCRIPTS: '',
};

let root, repo, chatDir, prsFile;
const wt = (name) => join(root, name);
const g = (cwd, ...args) => execFileSync('git', ['-C', cwd, ...args], { env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
const commit = (cwd, file, text) => {
  writeFileSync(join(cwd, file), text);
  g(cwd, 'add', file);
  g(cwd, 'commit', '-q', '-m', `add ${file}`);
};
const run = (args, opts = {}) => spawnSync(process.execPath, [script, ...args], { env, encoding: 'utf8', ...opts });

function rows(stdout) {
  const lines = stdout.trim().split('\n');
  const header = lines[1].split('\t');
  return Object.fromEntries(
    lines.slice(2).map((l) => {
      const cells = l.split('\t');
      const row = Object.fromEntries(header.map((h, i) => [h, cells[i]]));
      return [row.PATH.split(/[\\/]/).pop(), row];
    }),
  );
}

before(() => {
  root = realpathSync(mkdtempSync(join(os.tmpdir(), 'wt-audit-')));
  const origin = join(root, 'origin.git');
  repo = join(root, 'repo');
  execFileSync('git', ['init', '-q', '--bare', '-b', 'main', origin], { env });
  execFileSync('git', ['init', '-q', '-b', 'main', repo], { env });
  g(repo, 'remote', 'add', 'origin', origin);
  commit(repo, 'README.md', 'hello\n');
  g(repo, 'push', '-q', 'origin', 'main');
  g(repo, 'remote', 'set-head', 'origin', 'main');

  // merged: same commit as main, pushed under its own name.
  g(repo, 'worktree', 'add', '-q', '-b', 'merged', wt('wt-merged'));
  g(wt('wt-merged'), 'push', '-q', 'origin', 'merged');
  writeFileSync(join(wt('wt-merged'), 'big.bin'), Buffer.alloc(300 * 1024, 1));
  writeFileSync(join(wt('wt-merged'), '.gitignore'), 'big.bin\n.gitignore\n');

  // wip: tracked file modified.
  g(repo, 'worktree', 'add', '-q', '-b', 'wip', wt('wt-wip'));
  writeFileSync(join(wt('wt-wip'), 'README.md'), 'changed\n');

  // scratch: unmerged commit, only untracked files, never pushed.
  g(repo, 'worktree', 'add', '-q', '-b', 'scratch', wt('wt-scratch'));
  commit(wt('wt-scratch'), 'a.txt', 'a\n');
  writeFileSync(join(wt('wt-scratch'), 'notes.txt'), 'n\n');
  writeFileSync(join(wt('wt-scratch'), 'notes2.txt'), 'n\n');

  // open PR, pushed and then one more local commit (ahead).
  g(repo, 'worktree', 'add', '-q', '-b', 'feature-open', wt('wt-open'));
  commit(wt('wt-open'), 'b.txt', 'b\n');
  g(wt('wt-open'), 'push', '-q', 'origin', 'feature-open');
  commit(wt('wt-open'), 'c.txt', 'c\n');

  // closed PR, unmerged.
  g(repo, 'worktree', 'add', '-q', '-b', 'feature-closed', wt('wt-closed'));
  commit(wt('wt-closed'), 'd.txt', 'd\n');

  // draft PR.
  g(repo, 'worktree', 'add', '-q', '-b', 'feature-draft', wt('wt-draft'));
  commit(wt('wt-draft'), 'e.txt', 'e\n');

  // recent chat, plus a worktree whose path is a prefix of it.
  g(repo, 'worktree', 'add', '-q', '-b', 'chatty', wt('wt-chat'));
  commit(wt('wt-chat'), 'f.txt', 'f\n');
  g(repo, 'worktree', 'add', '-q', '-b', 'prefix', wt('wt-cha'));
  commit(wt('wt-cha'), 'g.txt', 'g\n');

  // old chat only: should stay in review.
  g(repo, 'worktree', 'add', '-q', '-b', 'oldchat', wt('wt-oldchat'));
  commit(wt('wt-oldchat'), 'h.txt', 'h\n');

  // detached HEAD.
  g(repo, 'worktree', 'add', '-q', '--detach', wt('wt-detached'), 'HEAD');

  chatDir = join(root, 'chats');
  mkdirSync(join(chatDir, 'session'), { recursive: true });
  const recent = join(chatDir, 'session', 'a.jsonl');
  writeFileSync(recent, JSON.stringify({ cmd: `cd ${wt('wt-chat')}/src && ls` }) + '\n');
  const old = join(chatDir, 'old.jsonl');
  writeFileSync(old, JSON.stringify({ cwd: wt('wt-oldchat') }) + '\n');
  const tenDaysAgo = (Date.now() - 10 * 86_400_000) / 1000;
  utimesSync(old, tenDaysAgo, tenDaysAgo);

  prsFile = join(root, 'prs.json');
  writeFileSync(
    prsFile,
    JSON.stringify([
      { number: 11, state: 'OPEN', headRefName: 'feature-open' },
      { number: 12, state: 'CLOSED', headRefName: 'feature-closed' },
      { number: 13, state: 'OPEN', isDraft: true, headRefName: 'feature-draft' },
      { number: 14, state: 'MERGED', headRefName: 'wip' },
    ]),
  );
});

after(() => rmSync(root, { recursive: true, force: true }));

const audit = (extra = []) => run(['--prs-file', prsFile, '--transcripts', chatDir, ...extra, repo]);

test('output starts with the base and header lines and omits the main worktree', () => {
  const r = audit(['-b', 'origin/main']);
  const lines = r.stdout.split('\n');
  assert.strictEqual(r.status, 0, r.stderr);
  assert.equal(lines[0], '# base: origin/main');
  assert.equal(lines[1], ['DISK', 'IDLE', 'IN_BASE', 'EDITS', 'UPSTREAM', 'PULL', 'CHAT_SEEN', 'ADVICE', 'PATH'].join('\t'));
  assert.equal(lines[1], COLUMNS.join('\t'));
  assert.ok(!Object.keys(rows(r.stdout)).includes('repo'));
  assert.equal(Object.keys(rows(r.stdout)).length, 10);
});

test('buckets are chosen by priority', () => {
  const t = rows(audit(['-b', 'origin/main']).stdout);
  assert.equal(t['wt-wip'].ADVICE, 'hold-wip');
  assert.equal(t['wt-open'].ADVICE, 'hold-open-pr');
  assert.equal(t['wt-draft'].ADVICE, 'hold-open-pr');
  assert.equal(t['wt-chat'].ADVICE, 'verify-recent-chat');
  assert.equal(t['wt-merged'].ADVICE, 'safe');
  assert.equal(t['wt-closed'].ADVICE, 'safe');
  assert.equal(t['wt-detached'].ADVICE, 'safe');
  assert.equal(t['wt-scratch'].ADVICE, 'review');
  assert.equal(t['wt-oldchat'].ADVICE, 'review');
  assert.equal(t['wt-cha'].ADVICE, 'review');
});

test('merged, dirty, remote, PR, and age columns are filled in', () => {
  const t = rows(audit(['-b', 'origin/main']).stdout);
  assert.equal(t['wt-merged'].IN_BASE, 'YES');
  assert.equal(t['wt-scratch'].IN_BASE, 'no');
  assert.equal(t['wt-wip'].EDITS, 'wip:1');
  assert.equal(t['wt-wip'].PULL, '#14/merged');
  assert.equal(t['wt-scratch'].EDITS, 'scratch:2');
  assert.equal(t['wt-merged'].EDITS, 'clean');
  assert.equal(t['wt-merged'].UPSTREAM, 'pushed');
  assert.equal(t['wt-open'].UPSTREAM, 'ahead:1');
  assert.equal(t['wt-scratch'].UPSTREAM, 'no-remote');
  assert.equal(t['wt-detached'].UPSTREAM, 'detached');
  assert.equal(t['wt-open'].PULL, '#11/open');
  assert.equal(t['wt-draft'].PULL, '#13/draft');
  assert.equal(t['wt-closed'].PULL, '#12/closed');
  assert.equal(t['wt-scratch'].PULL, '-');
  assert.equal(t['wt-merged'].IDLE, '0d');
});

test('CHAT_SEEN requires a separator after the path and ignores mere prefixes', () => {
  const t = rows(audit(['-b', 'origin/main']).stdout);
  assert.match(t['wt-chat'].CHAT_SEEN, /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(t['wt-cha'].CHAT_SEEN, '-');
  assert.match(t['wt-oldchat'].CHAT_SEEN, /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(t['wt-scratch'].CHAT_SEEN, '-');
});

test('rows come out biggest first', () => {
  const r = audit(['-b', 'origin/main', '--json']);
  const sizes = JSON.parse(r.stdout).rows.map((x) => x.bytes);
  assert.deepEqual(sizes, [...sizes].sort((a, b) => b - a));
  assert.ok(JSON.parse(r.stdout).rows[0].worktree.endsWith('wt-merged'));
});

test('with no --base, origin/HEAD is used and a warning printed', () => {
  const r = audit();
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^# base: origin\/main\n/);
  assert.match(r.stderr, /warning: using base origin\/main/);
});

test('origin/main is the fallback when origin/HEAD is missing', () => {
  g(repo, 'remote', 'set-head', 'origin', '--delete');
  try {
    const r = audit();
    assert.equal(r.status, 0, r.stderr);
    assert.match(r.stdout, /^# base: origin\/main\n/);
  } finally {
    g(repo, 'remote', 'set-head', 'origin', 'main');
  }
});

test('running inside a linked worktree with no repo argument succeeds', () => {
  const r = run(['--prs-file', prsFile, '--transcripts', chatDir, '-b', 'main'], { cwd: wt('wt-scratch') });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^# base: main\n/);
  assert.equal(rows(r.stdout)['wt-merged'].IN_BASE, 'YES');
});

test('a local base ref is used as is with no fetch', () => {
  const r = audit(['--base=main']);
  assert.equal(r.status, 0, r.stderr);
  assert.equal(r.stderr, '');
});

test('a base that cannot be resolved exits 1', () => {
  const r = audit(['-b', 'origin/nope']);
  assert.ok(/does not resolve/.test(r.stderr), r.stderr);
  assert.strictEqual(r.status, 1);
});

test('a directory outside any git repo exits 1', () => {
  const plain = join(root, 'plain');
  mkdirSync(plain, { recursive: true });
  const r = run(['--prs-file', prsFile, plain]);
  assert.ok(/not a git repository/.test(r.stderr), r.stderr);
  assert.strictEqual(r.status, 1);
});

test('a missing option value or unknown option exits 2 and help exits 0', () => {
  assert.equal(run(['-b']).status, 2);
  assert.equal(run(['--frob']).status, 2);
  const h = run(['--help']);
  assert.equal(h.status, 0);
  assert.match(h.stdout, /Usage: node worktree-audit\.mjs/);
  assert.match(h.stdout, /hold-open-pr/);
});

test('a PR file that cannot be read warns and blanks the PR column', () => {
  const r = run(['--prs-file', join(root, 'missing.json'), '--transcripts', chatDir, '-b', 'main', repo]);
  assert.ok(/PR column will be empty/.test(r.stderr), r.stderr);
  assert.strictEqual(r.status, 0);
  assert.equal(rows(r.stdout)['wt-open'].PULL, '-');
});

test('auditing leaves every worktree untouched', () => {
  const before = Object.fromEntries(['wt-wip', 'wt-scratch', 'wt-open'].map((n) => [n, g(wt(n), 'status', '--porcelain')]));
  const list = g(repo, 'worktree', 'list', '--porcelain');
  audit(['-b', 'origin/main']);
  for (const [n, s] of Object.entries(before)) assert.equal(g(wt(n), 'status', '--porcelain'), s);
  assert.equal(g(repo, 'worktree', 'list', '--porcelain'), list);
});

// ---------- unit ----------

test('bucketFor ordering', () => {
  assert.equal(bucketFor({ tracked: 1, prState: 'open', chatRecent: true, merged: true }), 'hold-wip');
  assert.equal(bucketFor({ tracked: 0, prState: 'draft', chatRecent: true, merged: true }), 'hold-open-pr');
  assert.equal(bucketFor({ tracked: 0, prState: 'merged', chatRecent: true, merged: false }), 'verify-recent-chat');
  assert.equal(bucketFor({ tracked: 0, prState: 'closed', chatRecent: false, merged: false }), 'safe');
  assert.equal(bucketFor({ tracked: 0, prState: undefined, chatRecent: false, merged: false }), 'review');
});

test('humanSize, parseArgs, pathNeedles, and the default transcript directory', () => {
  assert.equal(humanSize(512), '512B');
  assert.equal(humanSize(1536), '1.5K');
  assert.equal(humanSize(300 * 1024 * 1024), '300M');
  assert.deepEqual(parseArgs(['--base', 'x', 'r'], {}).base, 'x');
  assert.deepEqual(parseArgs([], { ENDOSTACK_TRANSCRIPTS: ['a', 'b'].join(process.platform === 'win32' ? ';' : ':') }).transcripts, ['a', 'b']);
  assert.throws(() => parseArgs(['a', 'b'], {}), /unexpected argument/);
  const needles = pathNeedles('C:\\work\\wt');
  assert.ok(needles.includes('C:\\\\work\\\\wt\\\\'));
  assert.ok(needles.includes('C:/work/wt/'));
  assert.ok(defaultTranscriptDirs('/home/u/repo', '/h')[0].endsWith(join('.claude', 'projects', '-home-u-repo')));
});
