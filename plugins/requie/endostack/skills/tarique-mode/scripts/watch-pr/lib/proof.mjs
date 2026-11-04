// Checked constructors for the values whose combinations matter. The spec
// for this tool asks for type-level guarantees; in plain JavaScript the
// same guarantees come from constructors that refuse inconsistent input and
// return frozen objects. Code elsewhere builds these values only through
// the functions below, so an invalid combination fails loudly at the point
// it is made instead of producing a wrong exit code.

export class InvariantError extends Error {
  constructor(message) {
    super(message);
    this.name = 'InvariantError';
  }
}

const REFUSING_ROLLUPS = new Set(['FAILURE', 'ERROR']);

// GitHub's view of whether it would merge the head commit.
export function mergeAssessment({ refuses, headRollup = null, wasGreenBefore = false }) {
  if (typeof refuses !== 'boolean') throw new InvariantError('merge assessment needs a boolean refuses');
  if (refuses && !REFUSING_ROLLUPS.has(headRollup)) {
    throw new InvariantError(`a refusal needs a FAILURE or ERROR head rollup, got ${headRollup}`);
  }
  return Object.freeze({ kind: refuses ? 'refuses' : 'allows', refuses, headRollup, wasGreenBefore: Boolean(wasGreenBefore) });
}

const CI_STATES = new Set(['clean', 'pending', 'failing', 'rejected']);

export function ciResult({ state, source, failed, pending, gates, passed, skipped, merge }) {
  if (!CI_STATES.has(state)) throw new InvariantError(`unknown CI state ${state}`);
  if (merge !== null && merge?.kind !== 'refuses' && merge?.kind !== 'allows') {
    throw new InvariantError('CI result needs a merge assessment built by mergeAssessment() or null');
  }
  if (state === 'failing' && failed.length === 0) throw new InvariantError('failing CI needs at least one failed check');
  if (state === 'rejected' && (failed.length > 0 || !merge?.refuses)) {
    throw new InvariantError('GitHub-rejected CI needs a refusal and no visible failed check');
  }
  if (state === 'clean') {
    if (failed.length > 0 || pending.length > 0) throw new InvariantError('clean CI cannot have failed or pending checks');
    if (!merge || merge.refuses) throw new InvariantError('clean CI must carry a merge assessment that allows the merge');
  }
  if (state === 'pending' && pending.length === 0) throw new InvariantError('pending CI needs a pending check');
  return Object.freeze({
    state,
    source,
    failed: Object.freeze([...failed]),
    pending: Object.freeze([...pending]),
    gates: Object.freeze([...gates]),
    passed,
    skipped,
    merge,
  });
}

// Evidence that one open PR is safe to merge. Every field is checked
// against the snapshot it came from.
export function readyProof(snap, { allowDraft }) {
  if (snap.status !== 'open') throw new InvariantError(`PR #${snap.pr} is ${snap.status}, not open`);
  const fail = (why) => {
    throw new InvariantError(`PR #${snap.pr} is not ready: ${why}`);
  };
  if (snap.mergeable === 'CONFLICTING' || snap.mergeState === 'DIRTY' || snap.mergeState === 'CONFLICTING') fail('merge conflict');
  if (snap.threads.length !== 0) fail('unresolved review threads');
  if (snap.ci.state !== 'clean' || !snap.ci.merge || snap.ci.merge.refuses) fail('CI is not clean with GitHub allowing the merge');
  if (snap.ci.gates.length !== 0) fail('an approval check is still open');
  if (snap.state !== 'OPEN') fail(`state is ${snap.state}`);
  if (snap.reviewDecision === 'CHANGES_REQUESTED') fail('changes requested');
  if (snap.isDraft && !allowDraft) fail('draft');
  return Object.freeze({
    pr: snap.pr,
    mergeable: snap.mergeable,
    mergeState: snap.mergeState,
    threads: 0,
    ci: 'clean',
    githubAllows: true,
    state: 'OPEN',
    reviewDecision: snap.reviewDecision,
    draft: draftLabel(snap.isDraft),
  });
}

// How a ready proof describes draft status: a draft only reaches READY when --allow-draft was set.
export function draftLabel(isDraft) {
  return isDraft ? 'draft-permitted' : 'ready-for-review';
}

export function mergedProof(snap) {
  if (snap.status !== 'merged') throw new InvariantError(`PR #${snap.pr} is not merged`);
  return Object.freeze({ pr: snap.pr, merged: true });
}

export const EXIT = Object.freeze({
  READY: 0,
  CONFLICT: 2,
  THREADS: 3,
  CHECKS: 4,
  TIMEOUT: 5,
  GATE: 6,
  QUERY: 7,
  USAGE: 64,
});

const BLOCKER_EXITS = new Map([
  ['conflict', EXIT.CONFLICT],
  ['threads', EXIT.THREADS],
  ['checks', EXIT.CHECKS],
  ['gate', EXIT.GATE],
  ['status-query', EXIT.QUERY],
]);

export function blockerExit(kind) {
  const code = BLOCKER_EXITS.get(kind);
  if (code === undefined) throw new InvariantError(`unknown blocker kind ${kind}`);
  return code;
}

// A READY verdict body. Every entry must be a readyProof or mergedProof,
// and the exit code is fixed at 0.
export function readyBody(proofs, exitCode = EXIT.READY) {
  if (exitCode !== EXIT.READY) throw new InvariantError(`READY cannot carry exit code ${exitCode}`);
  if (!Array.isArray(proofs) || proofs.length === 0) throw new InvariantError('READY needs at least one proof');
  for (const p of proofs) {
    if (!Object.isFrozen(p) || !(p.merged === true || p.githubAllows === true)) {
      throw new InvariantError('READY entries must come from readyProof() or mergedProof()');
    }
  }
  return { exitCode, proofs };
}
