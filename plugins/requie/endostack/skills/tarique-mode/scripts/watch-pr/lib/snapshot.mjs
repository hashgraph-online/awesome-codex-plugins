// Read one PR into a snapshot: PR fields, unresolved review threads,
// check results with a fallback chain, and GitHub's own merge assessment.

import { QueryError, firstLine } from './errors.mjs';
import { ciResult, mergeAssessment } from './proof.mjs';

const ENUMS = {
  mergeable: ['MERGEABLE', 'CONFLICTING', 'UNKNOWN'],
  // Every value GitHub documents for MergeStateStatus.
  mergeStateStatus: ['CLEAN', 'UNSTABLE', 'HAS_HOOKS', 'BLOCKED', 'BEHIND', 'DIRTY', 'CONFLICTING', 'DRAFT', 'UNKNOWN'],
  reviewDecision: ['APPROVED', 'CHANGES_REQUESTED', 'REVIEW_REQUIRED'],
  state: ['OPEN', 'CLOSED', 'MERGED'],
};

function enumField(fields, name, { nullable = false } = {}) {
  if (!(name in fields)) throw new QueryError('missing-field', `gh pr view did not return ${name}`);
  let value = fields[name];
  // gh prints "no review decision" as an empty string.
  if (name === 'reviewDecision' && (value === '' || value === null)) return null;
  if (nullable && value === null) return null;
  if (typeof value !== 'string' || !ENUMS[name].includes(value)) {
    throw new QueryError('unexpected-value', `${name} has an unrecognized value`, { raw: value });
  }
  return value;
}

export function parsePrFields(fields) {
  if (!fields || typeof fields !== 'object') throw new QueryError('missing-field', 'gh pr view returned no object');
  const state = enumField(fields, 'state');
  const mergedAt = fields.mergedAt ?? null;
  if (state === 'MERGED' || (typeof mergedAt === 'string' && mergedAt !== '')) {
    return { status: 'merged', state: 'MERGED' };
  }
  if (state === 'CLOSED') return { status: 'closed', state };
  for (const name of ['headRefOid', 'headRefName', 'baseRefName']) {
    if (typeof fields[name] !== 'string' || fields[name] === '') throw new QueryError('missing-field', `gh pr view did not return ${name}`);
  }
  if (typeof fields.isDraft !== 'boolean') throw new QueryError('missing-field', 'gh pr view did not return isDraft');
  return {
    status: 'open',
    state,
    mergeable: enumField(fields, 'mergeable'),
    mergeState: enumField(fields, 'mergeStateStatus'),
    reviewDecision: enumField(fields, 'reviewDecision'),
    headSha: fields.headRefOid,
    head: fields.headRefName,
    base: fields.baseRefName,
    isDraft: fields.isDraft,
  };
}

// ---------- review threads ----------

export function botMatcher(cfg) {
  const names = cfg.reviewBots.map((n) => n.toLowerCase());
  const hosts = cfg.reviewBotHosts.map((n) => n.toLowerCase());
  const markers = cfg.reviewBotMarkers.map((n) => n.toLowerCase());
  return (author, body) => {
    const who = String(author ?? '').toLowerCase();
    if (who && names.some((n) => who.includes(n))) return true;
    if (who && hosts.includes(who)) {
      const text = String(body ?? '').toLowerCase();
      return markers.some((m) => text.includes(m));
    }
    return false;
  };
}

export async function readThreads(reader, owner, repo, number, cfg) {
  const isBot = botMatcher(cfg);
  const passRe = new RegExp(cfg.passIdPattern, 'gi');
  const passIds = new Set();
  let sawBot = false;
  const unresolved = [];
  let cursor = null;
  for (let page = 0; ; page++) {
    const conn = await reader.threadPage(owner, repo, number, cursor);
    const info = conn?.pageInfo;
    if (!info || typeof info.hasNextPage !== 'boolean') {
      throw new QueryError('missing-field', `review threads page ${page + 1} has no pageInfo`);
    }
    if (!Array.isArray(conn.nodes)) throw new QueryError('missing-field', `review threads page ${page + 1} has no nodes`);
    for (const node of conn.nodes) {
      const first = node?.comments?.nodes?.[0] ?? {};
      const author = first.author?.login ?? null;
      const bot = isBot(author, first.body);
      if (bot) {
        sawBot = true;
        for (const m of String(first.body ?? '').matchAll(passRe)) passIds.add(m[1] ?? m[0]);
      }
      if (node?.isResolved === true) continue;
      unresolved.push({
        id: node?.id ?? null,
        author,
        body: first.body ?? '',
        path: first.path ?? null,
        line: first.line ?? first.originalLine ?? null,
        createdAt: first.createdAt ?? null,
        bot,
      });
    }
    if (!info.hasNextPage) break;
    if (typeof info.endCursor !== 'string' || info.endCursor === '') {
      throw new QueryError('missing-field', `review threads page ${page + 1} says more pages follow but has no cursor`);
    }
    cursor = info.endCursor;
  }
  const passes = passIds.size > 0 ? passIds.size : sawBot ? 1 : 0;
  for (const t of unresolved) t.botPasses = passes;
  return { threads: unresolved, botPasses: passes };
}

// ---------- checks ----------

function isApproval(name, cfg) {
  return cfg.approvalChecks.includes(name);
}

export function mapFastCheck(c, cfg) {
  const name = String(c?.name ?? '');
  const state = String(c?.state ?? '').toUpperCase();
  const bucket = String(c?.bucket ?? '').toLowerCase();
  let result;
  if (state === 'ACTION_REQUIRED') result = isApproval(name, cfg) ? 'gate' : 'failed';
  else if (bucket === 'fail' || state === 'FAILURE' || state === 'ERROR') result = 'failed';
  else if (bucket === 'pending') result = isApproval(name, cfg) ? 'gate' : 'pending';
  else if (bucket === 'pass') result = 'passed';
  else if (bucket === 'skipping') result = 'skipped';
  else result = 'failed';
  return {
    name,
    result,
    state: c?.state ?? null,
    description: c?.description ?? '',
    link: c?.link ?? '',
    workflow: c?.workflow ?? '',
  };
}

export function mapRollupNode(node, cfg) {
  if (node?.__typename === 'CheckRun') {
    const name = String(node.name ?? '');
    const conclusion = node.conclusion ?? null;
    let result;
    if (node.status !== 'COMPLETED') result = isApproval(name, cfg) ? 'gate' : 'pending';
    else if (conclusion === 'SUCCESS') result = 'passed';
    else if (conclusion === 'NEUTRAL' || conclusion === 'SKIPPED') result = 'skipped';
    else if (conclusion === 'ACTION_REQUIRED') result = isApproval(name, cfg) ? 'gate' : 'failed';
    else result = 'failed';
    return {
      name,
      result,
      state: node.status === 'COMPLETED' ? conclusion : node.status ?? null,
      description: '',
      link: node.detailsUrl ?? '',
      workflow: node.checkSuite?.workflowRun?.workflow?.name ?? '',
    };
  }
  if (node?.__typename === 'StatusContext') {
    const name = String(node.context ?? '');
    const state = node.state ?? null;
    let result;
    if (state === 'PENDING' || state === 'EXPECTED') result = isApproval(name, cfg) ? 'gate' : 'pending';
    else if (state === 'SUCCESS') result = 'passed';
    else result = 'failed';
    return { name, result, state, description: node.description ?? '', link: node.targetUrl ?? '', workflow: '' };
  }
  return null;
}

export async function readChecks(reader, owner, repo, number, cfg) {
  const fast = await reader.checksFast(owner, repo, number);
  let fastList = null;
  if ([0, 1, 8].includes(fast.code) && String(fast.stdout ?? '').trim() !== '') {
    try {
      const parsed = JSON.parse(fast.stdout);
      if (Array.isArray(parsed)) fastList = parsed;
    } catch {
      fastList = null;
    }
  }
  if (fastList && fastList.length > 0) {
    return { source: 'checks', checks: fastList.map((c) => mapFastCheck(c, cfg)) };
  }

  const checks = [];
  let cursor = null;
  for (let page = 0; ; page++) {
    const conn = await reader.rollupPage(owner, repo, number, cursor);
    const nodes = Array.isArray(conn?.nodes) ? conn.nodes : [];
    for (const node of nodes) {
      const mapped = mapRollupNode(node, cfg);
      if (mapped) checks.push(mapped);
    }
    const info = conn?.pageInfo;
    if (!info?.hasNextPage) break;
    if (typeof info.endCursor !== 'string' || info.endCursor === '') {
      throw new QueryError('missing-field', `check rollup page ${page + 1} says more pages follow but has no cursor`);
    }
    cursor = info.endCursor;
  }
  if (checks.length > 0) return { source: 'rollup', checks };

  const reason = firstLine(fast.stderr);
  throw new QueryError('checks-unavailable', `no checks from gh pr checks (exit ${fast.code}${reason ? `: ${reason}` : ''}) or the commit rollup`);
}

// ---------- merge assessment ----------

export function assessMerge(mergeState, commits, headSha) {
  const list = Array.isArray(commits) ? commits : [];
  let headIndex = list.findIndex((c) => c.oid === headSha);
  if (headIndex < 0) headIndex = list.length - 1;
  const headRollup = headIndex >= 0 ? list[headIndex].state ?? null : null;
  const wasGreenBefore = list.some((c, i) => i !== headIndex && c.state === 'SUCCESS');
  const refuses = mergeState === 'BLOCKED' && (headRollup === 'FAILURE' || headRollup === 'ERROR');
  return mergeAssessment({ refuses, headRollup, wasGreenBefore });
}

// ---------- whole PR ----------

export async function readPr(reader, owner, repo, number, cfg, { queued = false } = {}) {
  const fields = parsePrFields(await reader.prFields(owner, repo, number));
  const base = { pr: number, url: new URL(`/${owner}/${repo}/pull/${number}`, 'https://github.com').href };
  if (fields.status !== 'open') return { ...base, ...fields };

  const { threads, botPasses } = await readThreads(reader, owner, repo, number, cfg);
  const { checks, source } = await readChecks(reader, owner, repo, number, cfg);

  const failed = checks.filter((c) => c.result === 'failed');
  const pending = checks.filter((c) => c.result === 'pending');
  const gates = checks.filter((c) => c.result === 'gate');

  let merge = null;
  if (!(queued && pending.length > 0 && failed.length === 0)) {
    merge = assessMerge(fields.mergeState, await reader.commitRollups(owner, repo, number), fields.headSha);
  }

  let state;
  if (failed.length > 0) state = 'failing';
  else if (merge?.refuses) state = 'rejected';
  else if (pending.length > 0) state = 'pending';
  else state = 'clean';

  const markers = [...cfg.reviewCheckMarkers, ...cfg.reviewBots].map((m) => m.toLowerCase());
  const reviewAutomationRunning = pending.some((c) => markers.some((m) => c.name.toLowerCase().includes(m)));

  return {
    ...base,
    ...fields,
    threads,
    botPasses,
    ci: ciResult({
      state,
      source,
      failed,
      pending,
      gates,
      passed: checks.filter((c) => c.result === 'passed').length,
      skipped: checks.filter((c) => c.result === 'skipped').length,
      merge,
    }),
    reviewAutomationRunning,
  };
}
