// Work out which repository and PR numbers to watch, and discover the
// connected stack around a seed PR.

import { QueryError } from './errors.mjs';

const ascendingPr = (x, y) => x.number - y.number;

const NAME = '[A-Za-z0-9_.-]+';

// Accept only plain github.com remotes: no port, credentials, query,
// fragment, or extra path parts.
export function parseRemote(url) {
  if (typeof url !== 'string') return null;
  const text = url.trim();
  const patterns = [
    new RegExp(`^https://github\\.com/(${NAME})/(${NAME})$`),
    new RegExp(`^git@github\\.com:(${NAME})/(${NAME})$`),
    new RegExp(`^ssh://git@github\\.com/(${NAME})/(${NAME})$`),
  ];
  for (const re of patterns) {
    const m = re.exec(text);
    if (m) {
      const repo = m[2].replace(/\.git$/, '');
      if (repo === '' || repo === '.' || repo === '..' || m[1] === '.' || m[1] === '..') return null;
      return { owner: m[1], repo };
    }
  }
  return null;
}

export function parsePrUrl(url) {
  const m = /^https:\/\/github\.com\/([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)\/pull\/([1-9][0-9]*)$/.exec(String(url ?? ''));
  if (!m) return null;
  return { owner: m[1], repo: m[2], number: Number(m[3]) };
}

// Returns { owner, repo, numbers: [seed] } for single/stack mode or the
// full frozen list for queued mode with --stack-prs.
export async function resolveTarget(opts, reader) {
  const seed = opts.pr ?? opts.stackPrs?.[0] ?? null;
  let { owner, repo } = opts;
  let number = seed;

  if (!(owner && repo && number !== null)) {
    let fromRemote = null;
    if (number !== null) {
      fromRemote = parseRemote(await reader.originUrl());
    }
    if (fromRemote) {
      owner ??= fromRemote.owner;
      repo ??= fromRemote.repo;
    } else {
      const info = await reader.lookupPr(number);
      const parsed = parsePrUrl(info?.url);
      if (!parsed) {
        throw new QueryError('invalid-pr-url', `gh returned a PR URL that is not a github.com pull request: '${info?.url ?? ''}'`, {
          retryable: false,
        });
      }
      owner ??= parsed.owner;
      repo ??= parsed.repo;
      number ??= parsed.number;
    }
  }
  const numbers = opts.stackPrs ? [...opts.stackPrs] : [number];
  return { owner, repo, numbers };
}

// Walk the open PRs into a bottom-to-top chain through `seed`. A PR's
// parent is the same-repo PR whose head branch is its base. Fork PRs can
// sit in a stack as leaves but never act as parents, so a fork branch that
// happens to be named like a base branch cannot splice itself in.
export function buildStack(seed, openPrs) {
  const rows = openPrs.map((p) => ({
    number: p.number,
    head: p.headRefName,
    base: p.baseRefName,
    fork: Boolean(p.isCrossRepository),
  }));
  const byNumber = new Map(rows.map((r) => [r.number, r]));
  const start = byNumber.get(seed);
  if (!start) return [seed];

  const seen = new Set([seed]);
  const below = [];
  let cur = start;
  for (;;) {
    const parent = rows.find((r) => !r.fork && r.head === cur.base && !seen.has(r.number));
    if (!parent) break;
    seen.add(parent.number);
    below.unshift(parent.number);
    cur = parent;
  }

  const above = [];
  const visit = (node) => {
    if (node.fork) return;
    const kids = rows.filter((r) => r.base === node.head && !seen.has(r.number)).sort(ascendingPr);
    for (const kid of kids) {
      if (seen.has(kid.number)) continue;
      seen.add(kid.number);
      above.push(kid.number);
      visit(kid);
    }
  };
  visit(start);
  return [...below, seed, ...above];
}

export async function discoverStack(reader, owner, repo, seed) {
  const list = await reader.listOpenPrs(owner, repo);
  if (!Array.isArray(list)) throw new QueryError('missing-field', 'gh pr list did not return a list');
  for (const p of list) {
    if (!Number.isSafeInteger(p?.number) || typeof p.headRefName !== 'string' || typeof p.baseRefName !== 'string') {
      throw new QueryError('missing-field', 'gh pr list row is missing number, headRefName, or baseRefName');
    }
  }
  return buildStack(seed, list);
}
