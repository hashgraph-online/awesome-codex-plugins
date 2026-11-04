// Resolve the PR chain for a repository's checked-out branch: walk down
// through each PR's base to trunk, then up through open PRs stacked on the
// tip. Uses git for branch names and SHAs and the GitHub CLI for PRs.

import { spawnSync } from 'node:child_process';
import { UserError } from './errors.mjs';

const STATES = new Set(['OPEN', 'MERGED', 'CLOSED']);

export function commandRunner(cwd, env = process.env) {
  return (cmd, args) => {
    const r = spawnSync(cmd, args, { cwd, env, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
    if (r.error) return { code: 127, stdout: '', stderr: r.error.message };
    return { code: r.status ?? 1, stdout: r.stdout ?? '', stderr: r.stderr ?? '' };
  };
}

function show(cmd, args) {
  return [cmd, ...args].join(' ');
}

function must(run, cmd, args) {
  const r = run(cmd, args);
  if (r.code !== 0) {
    const why = (r.stderr || '').trim().split('\n')[0] || `exit ${r.code}`;
    throw new UserError(`command failed: ${show(cmd, args)}: ${why}`);
  }
  return r.stdout;
}

export function trunkBranch(run) {
  const r = run('git', ['symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD']);
  if (r.code !== 0) return 'main';
  const ref = r.stdout.trim();
  return ref.startsWith('origin/') ? ref.slice('origin/'.length) : ref || 'main';
}

export function currentBranch(run) {
  const r = run('git', ['symbolic-ref', '--quiet', '--short', 'HEAD']);
  if (r.code !== 0 || r.stdout.trim() === '') throw new UserError('the repository has no checked-out branch (detached HEAD); check out the stack branch first');
  return r.stdout.trim();
}

// List PRs through gh and validate each row.
export function listPrs(run, { head, base, state }) {
  const args = ['pr', 'list', '--state', state, '--limit', '200', '--json', 'number,state,headRefName,baseRefName,isDraft,headRefOid'];
  if (head) args.push('--head', head);
  if (base) args.push('--base', base);
  const out = must(run, 'gh', args);
  let rows;
  try {
    rows = JSON.parse(out);
  } catch {
    throw new UserError(`${show('gh', args)} printed output that is not JSON`);
  }
  if (!Array.isArray(rows)) throw new UserError(`${show('gh', args)} did not print a JSON array`);
  return rows.map((r) => {
    const ok =
      r && Number.isSafeInteger(r.number) && r.number > 0 && STATES.has(r.state) &&
      typeof r.headRefName === 'string' && r.headRefName !== '' && typeof r.baseRefName === 'string' && r.baseRefName !== '';
    if (!ok) throw new UserError(`${show('gh', args)} returned a row without a valid number, state, headRefName, and baseRefName`);
    return { pr: r.number, state: r.state, head: r.headRefName, base: r.baseRefName, draft: Boolean(r.isDraft), forgeSha: r.headRefOid ?? null };
  });
}

function resolveSha(run, branch, forgeSha) {
  for (const ref of [`refs/heads/${branch}`, `refs/remotes/origin/${branch}`]) {
    const r = run('git', ['rev-parse', '--verify', '--quiet', `${ref}^{commit}`]);
    if (r.code === 0) return r.stdout.trim();
  }
  if (forgeSha) return forgeSha;
  throw new UserError(`cannot find a commit for branch '${branch}' locally, on origin, or from gh`);
}

export function resolveChain(run) {
  const trunk = trunkBranch(run);
  const current = currentBranch(run);
  if (current === trunk) return { trunk, chain: [] };

  const chain = [];
  const seen = new Set();
  let branch = current;
  while (branch !== trunk) {
    if (seen.has(branch)) throw new UserError(`PR chain loops back to branch '${branch}'`);
    seen.add(branch);
    const all = listPrs(run, { head: branch, state: 'all' });
    const open = all.filter((p) => p.state === 'OPEN');
    const candidates = open.length ? open : all;
    if (!candidates.length) throw new UserError(`no PR found for branch '${branch}'; create one with 'gh pr create', then rerun`);
    if (candidates.length !== 1) {
      const listed = candidates.map((p) => `#${p.pr} ${p.state}`).join(', ');
      throw new UserError(`found ${candidates.length} PRs for branch '${branch}' (${listed}); close all but one`);
    }
    chain.unshift(candidates[0]);
    branch = candidates[0].base;
  }

  let tip = current;
  for (;;) {
    const kids = listPrs(run, { base: tip, state: 'open' }).filter((p) => p.state === 'OPEN');
    if (kids.length === 0) break;
    if (kids.length !== 1) throw new UserError(`stack forks at '${tip}': ${kids.map((p) => `${p.head}#${p.pr}`).join(', ')} all target it`);
    const kid = kids[0];
    if (seen.has(kid.head)) throw new UserError(`PR chain loops back to branch '${kid.head}'`);
    seen.add(kid.head);
    chain.push(kid);
    tip = kid.head;
  }

  const numbers = new Set();
  for (const p of chain) {
    if (numbers.has(p.pr)) throw new UserError(`PR #${p.pr} appears twice in the chain`);
    numbers.add(p.pr);
  }

  return {
    trunk,
    chain: chain.map((p) => {
      const sha = resolveSha(run, p.head, p.forgeSha);
      if (!/^[0-9a-f]{40,64}$/.test(sha)) throw new UserError(`branch '${p.head}' resolved to an invalid SHA '${sha}'`);
      return { pr: p.pr, branch: p.head, sha, state: p.state };
    }),
  };
}

export function checkPin(chain, pin) {
  const got = chain.map((p) => p.pr);
  if (got.length === pin.length && got.every((n, i) => n === pin[i])) return;
  const missing = pin.filter((n) => !got.includes(n));
  const extra = got.filter((n) => !pin.includes(n));
  const parts = [];
  if (missing.length) parts.push(`missing from chain: ${missing.map((n) => `#${n}`).join(', ')}`);
  if (extra.length) parts.push(`not in pin: ${extra.map((n) => `#${n}`).join(', ')}`);
  if (!parts.length) parts.push(`expected order ${pin.join(',')}, resolved ${got.join(',')}`);
  throw new UserError(`resolved stack differs from --prs: ${parts.join('; ')}`);
}

export function frontierLine(f) {
  const prs = f.prs.map((p) => `${p.branch}#${p.pr}@${p.sha}:${p.state}`).join(',');
  return `generation=${f.generation} prs=${prs || '(none)'} lowest-unmerged=${f.lowestUnmerged ?? 'none'}`;
}
