#!/usr/bin/env node
// worktree-audit: read-only report on every non-main git worktree, with a suggested
// bucket for each, so a human can decide what to delete. It never deletes anything.
//
// Usage: node worktree-audit.mjs [options] [repo-path]
//
//   -b, --base <ref>          Ref used for the IN_BASE test. Without it the audit tries the
//                             remote default branch, falling back to main and then master on
//                             origin, and warns which one it picked.
//       --prs-file <file>     Read PR state from a JSON array of {number, state, headRefName}
//                             instead of calling `gh pr list`.
//       --transcripts <dir>   Agent chat transcript directory to scan for CHAT_SEEN.
//                             Repeatable. Also read from ENDOSTACK_TRANSCRIPTS (path-list).
//       --json                Print rows as JSON instead of the table.
//   -h, --help                Print this help and exit 0.
//
// Columns: DISK IDLE IN_BASE EDITS UPSTREAM PULL CHAT_SEEN ADVICE PATH, tab-separated,
// largest first. ADVICE holds the bucket. Buckets, first match wins:
//   hold-wip            tracked files have uncommitted changes
//   hold-open-pr        the branch has an open or draft PR
//   verify-recent-chat  an agent transcript touched the worktree in the last 4 days
//   safe                HEAD is merged into base, or the branch has a merged or closed PR
//   review              everything else
//
// Exit 0 after printing, 1 on a repo or base error, 2 on a usage error.
// The only write is a best-effort `git fetch` of the base branch.

import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync, lstatSync, statSync, existsSync, realpathSync } from 'node:fs';
import { join, resolve, delimiter } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

export const RECENT_DAYS = 4;
const DAY_MS = 86_400_000;
const TRANSCRIPT_EXT = /\.(jsonl|json|md|txt|log)$/i;

class UsageError extends Error {}
class AuditError extends Error {}

// ---------- arguments ----------

export function parseArgs(argv, env = process.env) {
  const opts = { base: null, repo: null, prsFile: null, transcripts: [], json: false, help: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const value = () => {
      const v = argv[++i];
      if (v === undefined || v === '') throw new UsageError(`${a} needs a value`);
      return v;
    };
    if (a === '-h' || a === '--help') opts.help = true;
    else if (a === '-b' || a === '--base') opts.base = value();
    else if (a.startsWith('--base=')) opts.base = a.slice(7) || (() => { throw new UsageError('--base needs a value'); })();
    else if (a === '--prs-file') opts.prsFile = value();
    else if (a === '--transcripts') opts.transcripts.push(value());
    else if (a === '--json') opts.json = true;
    else if (a.startsWith('-')) throw new UsageError(`unknown option ${a}`);
    else if (opts.repo) throw new UsageError(`unexpected argument ${a}`);
    else opts.repo = a;
  }
  if (env.ENDOSTACK_TRANSCRIPTS) opts.transcripts.push(...env.ENDOSTACK_TRANSCRIPTS.split(delimiter).filter(Boolean));
  return opts;
}

// ---------- git helpers ----------

function git(cwd, args, { allowFail = false } = {}) {
  try {
    return execFileSync('git', ['-C', cwd, ...args], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      maxBuffer: 64 * 1024 * 1024,
    }).trimEnd();
  } catch (e) {
    if (allowFail) return null;
    throw e;
  }
}

const ok = (cwd, args) => git(cwd, args, { allowFail: true }) !== null;

export function listWorktrees(repo) {
  const out = git(repo, ['worktree', 'list', '--porcelain']);
  const list = [];
  let cur = null;
  for (const line of out.split('\n')) {
    if (line.startsWith('worktree ')) list.push((cur = { path: line.slice(9), head: null, branch: null, detached: false, bare: false }));
    else if (!cur) continue;
    else if (line.startsWith('HEAD ')) cur.head = line.slice(5);
    else if (line.startsWith('branch ')) cur.branch = line.slice(7).replace(/^refs\/heads\//, '');
    else if (line === 'detached') cur.detached = true;
    else if (line === 'bare') cur.bare = true;
  }
  return list;
}

export function resolveBase(repo, requested, warn) {
  let base = requested;
  if (!base) {
    const sym = git(repo, ['symbolic-ref', '--quiet', 'refs/remotes/origin/HEAD'], { allowFail: true });
    if (sym) base = sym.replace(/^refs\/remotes\//, '');
    else if (ok(repo, ['rev-parse', '--verify', '--quiet', 'refs/remotes/origin/main'])) base = 'origin/main';
    else if (ok(repo, ['rev-parse', '--verify', '--quiet', 'refs/remotes/origin/master'])) base = 'origin/master';
    else throw new AuditError('cannot pick a base: the remote has no default branch and neither main nor master exists on origin; pass --base');
    warn(`using base ${base}; the remote default branch may differ from the branch PRs merge into, pass --base to override`);
  }
  if (base.startsWith('origin/')) {
    const branch = base.slice(7);
    const spec = `+refs/heads/${branch}:refs/remotes/origin/${branch}`;
    if (!ok(repo, ['fetch', '--quiet', 'origin', spec])) warn(`fetch of ${base} failed; using the local copy`);
  }
  if (!ok(repo, ['rev-parse', '--verify', '--quiet', `${base}^{commit}`])) {
    throw new AuditError(`base ${base} does not resolve to a commit`);
  }
  return base;
}

// ---------- PR state ----------

export function loadPrs(repo, prsFile, warn) {
  let raw;
  if (prsFile) {
    try {
      raw = readFileSync(prsFile, 'utf8');
    } catch (e) {
      warn(`cannot read ${prsFile} (${e.code || e.message}); PR column will be empty`);
      return [];
    }
  } else {
    try {
      raw = execFileSync(
        'gh',
        ['pr', 'list', '--json', 'headRefName,number,state', '--state', 'all', '--author', '@me', '--limit', '1000'],
        { cwd: repo, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 64 * 1024 * 1024 },
      );
    } catch {
      warn('gh pr list failed or gh is missing; PR column will be empty');
      return [];
    }
  }
  try {
    const list = JSON.parse(raw);
    if (!Array.isArray(list)) throw new Error('not an array');
    return list.map((p) => ({
      number: p.number,
      state: String(p.isDraft && /open/i.test(p.state) ? 'draft' : p.state).toLowerCase(),
      head: p.headRefName,
    }));
  } catch (e) {
    warn(`PR data is not a JSON array (${e.message}); PR column will be empty`);
    return [];
  }
}

// ---------- filesystem ----------

export function diskBytes(path) {
  let total = 0;
  const stack = [path];
  while (stack.length) {
    const p = stack.pop();
    let st;
    try {
      st = lstatSync(p);
    } catch {
      continue;
    }
    total += typeof st.blocks === 'number' && st.blocks > 0 ? st.blocks * 512 : st.size;
    if (st.isDirectory()) {
      let names = [];
      try {
        names = readdirSync(p);
      } catch {
        continue;
      }
      for (const n of names) stack.push(join(p, n));
    }
  }
  return total;
}

export function humanSize(bytes) {
  const units = ['B', 'K', 'M', 'G', 'T'];
  let v = bytes;
  let u = 0;
  while (v >= 1024 && u < units.length - 1) {
    v /= 1024;
    u++;
  }
  if (u === 0) return `${v}B`;
  return `${v < 10 ? Math.ceil(v * 10) / 10 : Math.ceil(v)}${units[u]}`;
}

// Claude Code keeps per-project transcripts under ~/.claude/projects/<path with
// non-alphanumerics replaced by "-">. Other agents are reached with --transcripts.
export function defaultTranscriptDirs(mainPath, home = homedir()) {
  const slug = mainPath.replace(/[^A-Za-z0-9]/g, '-');
  return [join(home, '.claude', 'projects', slug)];
}

function transcriptFiles(dirs) {
  const files = [];
  for (const dir of dirs) {
    const stack = [dir];
    while (stack.length) {
      const p = stack.pop();
      let st;
      try {
        st = statSync(p);
      } catch {
        continue;
      }
      if (st.isDirectory()) {
        let names = [];
        try {
          names = readdirSync(p);
        } catch {
          continue;
        }
        for (const n of names) stack.push(join(p, n));
      } else if (TRANSCRIPT_EXT.test(p)) files.push({ path: p, mtime: st.mtimeMs });
    }
  }
  return files.sort((a, b) => b.mtime - a.mtime);
}

// Needles: the path followed by a separator or a quote, plain and JSON-escaped,
// so /repo/wt-a does not match a transcript that only mentions /repo/wt-ab.
export function pathNeedles(path) {
  const forms = new Set([path, path.replace(/\\/g, '/'), path.replace(/\//g, '\\')]);
  const needles = [];
  for (const f of forms) {
    const esc = JSON.stringify(f).slice(1, -1);
    for (const base of new Set([f, esc])) {
      const sep = base.includes('\\\\') ? '\\\\' : base.includes('\\') ? '\\' : '/';
      needles.push(base + sep, base + '"', base + "'", base + '\\"');
    }
  }
  return [...new Set(needles)];
}

export function lastChats(paths, dirs) {
  const result = new Map();
  const pending = new Map(paths.map((p) => [p, pathNeedles(p)]));
  for (const f of transcriptFiles(dirs)) {
    if (!pending.size) break;
    let text;
    try {
      text = readFileSync(f.path, 'utf8');
    } catch {
      continue;
    }
    for (const [p, needles] of pending) {
      if (needles.some((n) => text.includes(n))) {
        result.set(p, f.mtime);
        pending.delete(p);
      }
    }
  }
  return result;
}

// ---------- per-worktree facts ----------

function dirtyState(path) {
  const out = git(path, ['status', '--porcelain=v1', '--untracked-files=all'], { allowFail: true });
  if (out === null) return { label: '?', tracked: 0 };
  const lines = out.split('\n').filter(Boolean);
  const untracked = lines.filter((l) => l.startsWith('??')).length;
  const tracked = lines.length - untracked;
  if (tracked) return { label: `wip:${tracked}`, tracked };
  if (untracked) return { label: `scratch:${untracked}`, tracked: 0 };
  return { label: 'clean', tracked: 0 };
}

function remoteState(repo, wt) {
  if (!wt.branch) return 'detached';
  const ref = `refs/remotes/origin/${wt.branch}`;
  const remote = git(repo, ['rev-parse', '--verify', '--quiet', ref], { allowFail: true });
  if (!remote) return 'no-remote';
  if (remote === wt.head) return 'pushed';
  const ahead = Number(git(repo, ['rev-list', '--count', `${ref}..${wt.head}`], { allowFail: true }) || 0);
  if (ahead > 0) return `ahead:${ahead}`;
  const behind = Number(git(repo, ['rev-list', '--count', `${wt.head}..${ref}`], { allowFail: true }) || 0);
  return `behind:${behind}`;
}

export function bucketFor({ tracked, prState, chatRecent, merged }) {
  if (tracked > 0) return 'hold-wip';
  if (prState === 'open' || prState === 'draft') return 'hold-open-pr';
  if (chatRecent) return 'verify-recent-chat';
  if (merged || prState) return 'safe';
  return 'review';
}

const isoDate = (ms) => new Date(ms).toISOString().slice(0, 10);

export function audit(opts, warn = (m) => process.stderr.write(`warning: ${m}\n`), now = Date.now()) {
  const start = resolve(opts.repo || process.cwd());
  const top = git(start, ['rev-parse', '--show-toplevel'], { allowFail: true });
  if (!top) {
    throw new AuditError(opts.repo ? `${opts.repo} is not a git repository` : 'not inside a git repository; pass a repo path');
  }
  const all = listWorktrees(top);
  const main = all[0];
  const base = resolveBase(main.path, opts.base, warn);
  const prs = loadPrs(main.path, opts.prsFile, warn);
  const others = all.slice(1).filter((w) => !w.bare);
  const dirs = opts.transcripts.length ? opts.transcripts : defaultTranscriptDirs(main.path);
  const chats = lastChats(others.map((w) => w.path), dirs);

  const rows = others.map((wt) => {
    const present = existsSync(wt.path);
    const bytes = present ? diskBytes(wt.path) : 0;
    const ct = present ? git(wt.path, ['log', '-1', '--format=%ct', 'HEAD'], { allowFail: true }) : null;
    const age = ct ? `${Math.floor((now - Number(ct) * 1000) / DAY_MS)}d` : '?';
    const merged = !!wt.head && ok(main.path, ['merge-base', '--is-ancestor', wt.head, base]);
    const dirty = present ? dirtyState(wt.path) : { label: 'missing', tracked: 0 };
    const remote = remoteState(main.path, wt);
    const pr = wt.branch ? prs.find((p) => p.head === wt.branch) : undefined;
    const chat = chats.get(wt.path);
    const chatRecent = chat !== undefined && now - chat <= RECENT_DAYS * DAY_MS;
    return {
      bytes,
      size: present ? humanSize(bytes) : '?',
      age,
      merged: merged ? 'YES' : 'no',
      dirty: dirty.label,
      remote,
      pr: pr ? `#${pr.number}/${pr.state}` : '-',
      lastChat: chat === undefined ? '-' : isoDate(chat),
      bucket: bucketFor({ tracked: dirty.tracked, prState: pr?.state, chatRecent, merged }),
      worktree: wt.path,
      branch: wt.branch,
    };
  });
  rows.sort((a, b) => b.bytes - a.bytes);
  return { base, rows };
}

export const COLUMNS = ['DISK', 'IDLE', 'IN_BASE', 'EDITS', 'UPSTREAM', 'PULL', 'CHAT_SEEN', 'ADVICE', 'PATH'];

export function formatTable({ base, rows }) {
  const lines = [`# base: ${base}`, COLUMNS.join('\t')];
  for (const r of rows) {
    lines.push([r.size, r.age, r.merged, r.dirty, r.remote, r.pr, r.lastChat, r.bucket, r.worktree].join('\t'));
  }
  return lines.join('\n') + '\n';
}

function helpText() {
  const src = readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n');
  const out = [];
  for (const line of src.slice(1)) {
    if (!line.startsWith('//')) break;
    out.push(line.replace(/^\/\/ ?/, ''));
  }
  return out.join('\n') + '\n';
}

export function main(argv, io = { out: (s) => process.stdout.write(s), err: (s) => process.stderr.write(s) }) {
  let opts;
  try {
    opts = parseArgs(argv);
  } catch (e) {
    io.err(`worktree-audit: ${e.message}\nusage: node worktree-audit.mjs [-b <ref>] [--prs-file <f>] [--transcripts <dir>] [--json] [repo-path]\n`);
    return 2;
  }
  if (opts.help) {
    io.out(helpText());
    return 0;
  }
  try {
    const result = audit(opts, (m) => io.err(`warning: ${m}\n`));
    io.out(opts.json ? JSON.stringify(result, null, 2) + '\n' : formatTable(result));
    return 0;
  } catch (e) {
    if (e instanceof AuditError) {
      io.err(`worktree-audit: ${e.message}\n`);
      return 1;
    }
    io.err(`worktree-audit: ${e.stderr ? String(e.stderr).trim() : e.message}\n`);
    return 1;
  }
}

function isEntry() {
  if (!process.argv[1]) return false;
  try {
    return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

if (isEntry()) process.exitCode = main(process.argv.slice(2));
