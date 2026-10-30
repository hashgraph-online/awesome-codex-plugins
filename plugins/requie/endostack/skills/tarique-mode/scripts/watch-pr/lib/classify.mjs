// Decide what a snapshot (or a list of them) means. Blockers are checked
// in a fixed tier order: conflicts, unresolved threads, failing checks,
// merge gates. Across a stack the scan is tier-major: every row is checked
// for conflicts before any row is checked for threads, and so on.

import { readyProof, mergedProof } from './proof.mjs';

export const TIERS = ['conflict', 'threads', 'checks', 'gate'];

export function hasConflict(s) {
  return s.status === 'open' && (s.mergeable === 'CONFLICTING' || s.mergeState === 'DIRTY' || s.mergeState === 'CONFLICTING');
}

// Returns a gate reason, or null. A draft whose checks are still running
// waits for the checks first, so the agent sees CI results before being
// told to mark it ready.
export function gateReason(s, { allowDraft }) {
  if (s.status === 'closed') return 'closed';
  if (s.status !== 'open') return null;
  if (s.reviewDecision === 'CHANGES_REQUESTED') return 'changes-requested';
  if (s.ci.gates.length > 0) return 'approval-check';
  if (s.isDraft && !allowDraft && s.ci.pending.length === 0) return 'draft';
  return null;
}

export function tierHit(s, tier, opts) {
  switch (tier) {
    case 'conflict':
      return hasConflict(s);
    case 'threads':
      return s.status === 'open' && s.threads.length > 0;
    case 'checks':
      return s.status === 'open' && (s.ci.state === 'failing' || s.ci.state === 'rejected');
    case 'gate':
      return gateReason(s, opts) !== null;
    default:
      return false;
  }
}

export function isPending(s) {
  return s.status === 'open' && s.ci.state === 'pending';
}

// rows: snapshots in bottom-to-top order.
// Returns one of:
//   { outcome: 'blocker', tier, snap, reason? }
//   { outcome: 'waiting', snap }          (first row with pending checks)
//   { outcome: 'ready', proofs }
export function decide(rows, opts) {
  for (const tier of TIERS) {
    const snap = rows.find((s) => tierHit(s, tier, opts));
    if (snap) return { outcome: 'blocker', tier, snap, reason: tier === 'gate' ? gateReason(snap, opts) : undefined };
  }
  const waiting = rows.find(isPending);
  if (waiting) return { outcome: 'waiting', snap: waiting };
  const proofs = rows.map((s) => (s.status === 'merged' ? mergedProof(s) : readyProof(s, opts)));
  return { outcome: 'ready', proofs };
}

// Queued mode: blockers anywhere still stop the run, but upstack pending
// checks do not hold up the frontier. Returns blocker or null.
export function firstBlocker(rows, opts) {
  for (const tier of TIERS) {
    const snap = rows.find((s) => tierHit(s, tier, opts));
    if (snap) return { tier, snap, reason: tier === 'gate' ? gateReason(snap, opts) : undefined };
  }
  return null;
}
