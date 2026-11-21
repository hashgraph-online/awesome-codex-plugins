// Builders for the objects the watcher prints. Every object shares the
// envelope { schema, seq, at, mode, kind, terminal } and terminal objects
// add exitCode. The emitter assigns seq and at.

import { EXIT, blockerExit, readyBody } from './proof.mjs';
import { gateReason, hasConflict } from './classify.mjs';

export const SCHEMA_VERSION = 1;

export function makeEmitter({ mode, now, write }) {
  let seq = 0;
  return (kind, body, { terminal = false, exitCode } = {}) => {
    seq += 1;
    const obj = {
      schema: SCHEMA_VERSION,
      seq,
      at: new Date(now() * 1000).toISOString(),
      mode,
      kind,
      terminal,
      ...(terminal ? { exitCode } : {}),
      ...body,
    };
    write(obj);
    return obj;
  };
}

function checkBrief(c) {
  return { name: c.name, state: c.state, description: c.description, link: c.link };
}

export function rowSummary(s, opts) {
  if (s.status !== 'open') {
    return { pr: s.pr, url: s.url, status: s.status, merge: s.status };
  }
  let merge = 'ok';
  if (hasConflict(s)) merge = 'conflict';
  else if (s.reviewDecision === 'CHANGES_REQUESTED') merge = 'changes-requested';
  else if (s.isDraft && !opts.allowDraft) merge = 'draft';
  else if (s.ci.gates.length > 0) merge = 'approval-check';
  return {
    pr: s.pr,
    url: s.url,
    status: 'open',
    head: s.head,
    base: s.base,
    headSha: s.headSha,
    ci: {
      state: s.ci.state,
      source: s.ci.source,
      passed: s.ci.passed,
      skipped: s.ci.skipped,
      pending: s.ci.pending.map((c) => c.name),
      failed: s.ci.failed.map((c) => c.name),
      approvalChecks: s.ci.gates.map((c) => c.name),
      githubRefuses: s.ci.merge?.refuses ?? null,
      headRollup: s.ci.merge?.headRollup ?? null,
      wasGreenBefore: s.ci.merge?.wasGreenBefore ?? false,
    },
    threads: s.threads.length,
    botPasses: s.botPasses,
    reviewAutomationRunning: s.reviewAutomationRunning,
    reviewDecision: s.reviewDecision,
    draft: s.isDraft,
    mergeable: s.mergeable,
    mergeState: s.mergeState,
    merge,
  };
}

const ACTIONS = {
  conflict: 'rebase or merge the base branch, resolve the conflicts, push, then rearm the watcher',
  threads: 'address each unresolved thread (fix and reply, or reply with the reason to decline), resolve it, then rearm',
  checks: 'open the failing check logs, fix the cause, push, then rearm',
  'status-query': 'verify the repository context, gh authentication, and GitHub API availability, then rearm',
};

const GATE_ACTIONS = {
  draft: 'mark the PR ready for review when the work is done, or rerun with --allow-draft',
  'changes-requested': 'address the requested changes and ask the reviewer to re-review',
  closed: 'reopen or replace the closed PR, or drop it from the queued list',
  'approval-check': 'ask the owner to approve the pending approval check',
};

export function blockerBody(tier, snap, reason) {
  const body = { blocker: tier, pr: snap.pr, url: snap.url };
  if (tier === 'conflict') {
    Object.assign(body, { mergeable: snap.mergeable, mergeState: snap.mergeState });
  } else if (tier === 'threads') {
    Object.assign(body, {
      threadCount: snap.threads.length,
      botPasses: snap.botPasses,
      threads: snap.threads.map((t) => ({
        id: t.id,
        path: t.path,
        line: t.line,
        author: t.author,
        bot: t.bot,
        botPasses: t.botPasses,
        createdAt: t.createdAt,
        body: t.body.length > 4000 ? `${t.body.slice(0, 4000)}...` : t.body,
      })),
    });
  } else if (tier === 'checks') {
    Object.assign(body, {
      ciState: snap.ci.state,
      failed: snap.ci.failed.map(checkBrief),
      pending: snap.ci.pending.map((c) => c.name),
      github: snap.ci.merge
        ? { refuses: snap.ci.merge.refuses, mergeState: snap.mergeState, headRollup: snap.ci.merge.headRollup, wasGreenBefore: snap.ci.merge.wasGreenBefore }
        : null,
    });
  } else if (tier === 'gate') {
    Object.assign(body, {
      reason,
      draft: snap.isDraft ?? null,
      reviewDecision: snap.reviewDecision ?? null,
      approvalChecks: snap.ci?.gates.map(checkBrief) ?? [],
    });
  }
  body.action = tier === 'gate' ? GATE_ACTIONS[reason] : ACTIONS[tier];
  return { body, exitCode: blockerExit(tier) };
}

export function queryBlockerBody(error, failures) {
  return {
    body: { blocker: 'status-query', failures, error: error.toJSON(), action: ACTIONS['status-query'] },
    exitCode: blockerExit('status-query'),
  };
}

export function readyVerdictBody(proofs, opts) {
  const { exitCode } = readyBody(proofs);
  return { body: { prs: proofs.map((p) => ({ ...p })), allowDraft: Boolean(opts.allowDraft) }, exitCode };
}

export { EXIT, gateReason };
