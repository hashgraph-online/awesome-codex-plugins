import * as cp from 'node:child_process';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { main } from '../lib/cli.mjs';

export function tmpdir(prefix = 'orch-test-') {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

export async function cli(argv, { env = {}, cwd, run } = {}) {
  let stdout = '';
  let stderr = '';
  const code = await main(argv, {
    env: { PATH: process.env.PATH, ...env },
    cwd,
    run,
    stdout: (s) => (stdout += s),
    stderr: (s) => (stderr += s),
  });
  return { code, stdout, stderr };
}

function git(cwd, ...args) {
  const r = cp.spawnSync('git', args, { cwd, encoding: 'utf8', env: { ...process.env, GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@example.com', GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@example.com' } });
  if (r.status === 0) return r.stdout.trim();
  throw new Error(`fixture git command exited ${r.status} (git ${args.join(' ')}): ${r.stderr}`);
}

// A repo with trunk `main` and a chain of branches, each one commit on top
// of the previous. origin/HEAD points at main through a bare remote.
export function fixtureRepo(branches, { checkout } = {}) {
  const root = tmpdir('orch-repo-');
  const bare = path.join(root, 'origin.git');
  const work = path.join(root, 'work');
  git(root, 'init', '--bare', '-b', 'main', bare);
  git(root, 'init', '-b', 'main', work);
  fs.writeFileSync(path.join(work, 'f.txt'), 'base\n');
  git(work, 'add', '.');
  git(work, 'commit', '-m', 'base');
  git(work, 'remote', 'add', 'origin', bare);
  git(work, 'push', '-q', 'origin', 'main');
  git(work, 'remote', 'set-head', 'origin', 'main');
  let prev = 'main';
  const shas = {};
  for (const b of branches) {
    git(work, 'checkout', '-q', '-b', b, prev);
    fs.writeFileSync(path.join(work, `${b.replace(/\W/g, '_')}.txt`), `${b}\n`);
    git(work, 'add', '.');
    git(work, 'commit', '-q', '-m', b);
    shas[b] = git(work, 'rev-parse', 'HEAD');
    prev = b;
  }
  git(work, 'checkout', '-q', checkout ?? branches.at(-1) ?? 'main');
  return { root, work, shas, git: (...a) => git(work, ...a) };
}

// A fake gh on PATH: answers `gh pr list --head/--base --state` from a
// JSON file, so tests run with no network.
export function fakeGh(prs, { raw } = {}) {
  const dir = tmpdir('orch-gh-');
  const data = path.join(dir, 'prs.json');
  fs.writeFileSync(data, raw ?? JSON.stringify(prs));
  const script = `#!/usr/bin/env node
const { appendFileSync, readFileSync } = require('node:fs');
const [, , ...args] = process.argv;
const log = process.env.FAKE_GH_LOG;
if (log) appendFileSync(log, JSON.stringify(args) + '\\n');
if (args[0] !== 'pr' || args[1] !== 'list') { process.stderr.write('fake gh: unsupported ' + args.join(' ') + '\\n'); process.exit(1); }
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };
const text = readFileSync(${JSON.stringify(data)}, 'utf8');
let rows;
try { rows = JSON.parse(text); } catch { process.stdout.write(text); process.exit(0); }
if (!Array.isArray(rows)) { process.stdout.write(text); process.exit(0); }
const head = opt('--head'), base = opt('--base'), state = (opt('--state') || 'open').toLowerCase();
rows = rows.filter((r) => (!head || r.headRefName === head) && (!base || r.baseRefName === base) && (state === 'all' || r.state.toLowerCase() === state));
process.stdout.write(JSON.stringify(rows));
`;
  const gh = path.join(dir, 'gh');
  fs.writeFileSync(gh, script, { mode: 0o755 });
  return { dir, PATH: `${dir}${path.delimiter}${process.env.PATH}` };
}

export const ghPr = (number, head, base, state = 'OPEN', isDraft = false) => ({ number, headRefName: head, baseRefName: base, state, isDraft });
