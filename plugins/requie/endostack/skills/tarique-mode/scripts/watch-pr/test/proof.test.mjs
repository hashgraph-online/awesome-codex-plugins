// The spec asks for compile-time guarantees. These tests pin the runtime
// equivalents: the constructors in proof.mjs refuse each forbidden shape.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mergeAssessment, ciResult, readyProof, readyBody, mergedProof, InvariantError, EXIT } from '../lib/proof.mjs';

const allows = () => mergeAssessment({ refuses: false, headRollup: 'SUCCESS' });
const refuses = () => mergeAssessment({ refuses: true, headRollup: 'FAILURE' });
const ci = (over) => ciResult({ state: 'clean', source: 'checks', failed: [], pending: [], gates: [], passed: 1, skipped: 0, merge: allows(), ...over });

test('building a refusal requires a failing head rollup', () => {
  assert.throws(() => mergeAssessment({ refuses: true, headRollup: 'PENDING' }), InvariantError);
  assert.throws(() => mergeAssessment({ refuses: true, headRollup: null }), InvariantError);
  assert.equal(refuses().kind, 'refuses');
});

test('allowances and refusals are separate kinds', () => {
  assert.equal(allows().kind, 'allows');
  assert.equal(allows().refuses, false);
  assert.ok(Object.isFrozen(allows()));
});

test('clean CI rejects a refusal or an absent assessment', () => {
  assert.throws(() => ci({ merge: refuses() }), InvariantError);
  assert.throws(() => ci({ merge: null }), InvariantError);
  assert.throws(() => ci({ merge: { refuses: false } }), InvariantError);
});

test('clean CI rejects failed or pending checks', () => {
  assert.throws(() => ci({ failed: [{ name: 'x' }] }), InvariantError);
  assert.throws(() => ci({ pending: [{ name: 'x' }] }), InvariantError);
});

test('rejected CI requires a refusal with no visible failure', () => {
  assert.throws(() => ci({ state: 'rejected', merge: allows() }), InvariantError);
  assert.throws(() => ci({ state: 'rejected', merge: refuses(), failed: [{ name: 'x' }] }), InvariantError);
  assert.equal(ci({ state: 'rejected', merge: refuses() }).state, 'rejected');
});

test('READY rejects a blocker exit code', () => {
  const snap = { pr: 1, status: 'open', state: 'OPEN', mergeable: 'MERGEABLE', mergeState: 'CLEAN', threads: [], ci: ci(), reviewDecision: null, isDraft: false };
  const proof = readyProof(snap, { allowDraft: false });
  for (const code of [EXIT.CONFLICT, EXIT.THREADS, EXIT.CHECKS, EXIT.TIMEOUT, EXIT.GATE, EXIT.QUERY]) {
    assert.throws(() => readyBody([proof], code), InvariantError);
  }
  assert.equal(readyBody([proof]).exitCode, 0);
});

test('READY accepts only proofs made by the proof constructors', () => {
  assert.throws(() => readyBody([]), InvariantError);
  assert.throws(() => readyBody([{ pr: 1, githubAllows: true }]), InvariantError);
  assert.equal(readyBody([mergedProof({ pr: 2, status: 'merged' })]).exitCode, 0);
});

test('a ready proof requires all conditions', () => {
  const good = { pr: 1, status: 'open', state: 'OPEN', mergeable: 'MERGEABLE', mergeState: 'CLEAN', threads: [], ci: ci(), reviewDecision: 'APPROVED', isDraft: false };
  assert.equal(readyProof(good, { allowDraft: false }).draft, 'ready-for-review');
  const bad = [
    { mergeable: 'CONFLICTING' },
    { mergeState: 'DIRTY' },
    { threads: [{ id: 't' }] },
    { ci: ci({ state: 'pending', pending: [{ name: 'p' }] }) },
    { ci: ci({ state: 'rejected', merge: refuses() }) },
    { ci: ci({ gates: [{ name: 'Owner approval' }] }) },
    { reviewDecision: 'CHANGES_REQUESTED' },
    { isDraft: true },
    { status: 'closed' },
  ];
  for (const over of bad) assert.throws(() => readyProof({ ...good, ...over }, { allowDraft: false }), InvariantError, JSON.stringify(Object.keys(over)));
  assert.equal(readyProof({ ...good, isDraft: true }, { allowDraft: true }).draft, 'draft-permitted');
});
