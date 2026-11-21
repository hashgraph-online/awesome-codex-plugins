import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assessMerge, readChecks, readThreads, readPr, parsePrFields, mapRollupNode, mapFastCheck } from '../lib/snapshot.mjs';
import { QueryError } from '../lib/errors.mjs';
import { cfg, fakeReader, prFields, passCheck, pendCheck, thread } from './fakes.mjs';

const SHA = 'a'.repeat(40);

test('truth table for the merge assessment', () => {
  const head = (state) => [{ oid: SHA, state }];
  assert.equal(assessMerge('BLOCKED', head('FAILURE'), SHA).refuses, true);
  assert.equal(assessMerge('BLOCKED', head('ERROR'), SHA).refuses, true);
  assert.equal(assessMerge('BLOCKED', head('PENDING'), SHA).refuses, false);
  assert.equal(assessMerge('BLOCKED', head('SUCCESS'), SHA).refuses, false);
  for (const ms of ['UNSTABLE', 'UNKNOWN', 'CLEAN', 'BEHIND', 'HAS_HOOKS']) {
    for (const rollup of ['FAILURE', 'ERROR', 'PENDING', 'SUCCESS', null]) {
      assert.equal(assessMerge(ms, head(rollup), SHA).refuses, false, `${ms}/${rollup}`);
    }
  }
});

test('the merge assessment remembers an earlier green commit', () => {
  const m = assessMerge('BLOCKED', [{ oid: 'b'.repeat(40), state: 'SUCCESS' }, { oid: SHA, state: 'FAILURE' }], SHA);
  assert.equal(m.wasGreenBefore, true);
  assert.equal(m.headRollup, 'FAILURE');
  assert.equal(assessMerge('CLEAN', [{ oid: SHA, state: 'SUCCESS' }], SHA).wasGreenBefore, false);
});

test('enums accept a CONFLICTING merge state and map an empty review decision to null', () => {
  const p = parsePrFields(prFields({ mergeStateStatus: 'CONFLICTING', reviewDecision: '' }));
  assert.equal(p.mergeState, 'CONFLICTING');
  assert.equal(p.reviewDecision, null);
});

test('enums treat an unknown value as retryable and keep the raw value', () => {
  for (const [key, raw] of [['reviewDecision', 'MAYBE'], ['mergeable', 'SORT_OF'], ['mergeStateStatus', 'WOBBLY']]) {
    assert.throws(
      () => parsePrFields(prFields({ [key]: raw })),
      (e) => e instanceof QueryError && e.retryable === true && e.raw === raw,
    );
  }
});

test('merged and closed PRs return before threads and checks are read', async () => {
  const calls = [];
  const reader = fakeReader({ calls, script: { 5: { fields: prFields({ state: 'MERGED', mergedAt: '2026-10-01T00:00:00Z' }) }, 6: { fields: prFields({ state: 'CLOSED' }) } } });
  assert.equal((await readPr(reader, 'acme', 'widgets', 5, cfg())).status, 'merged');
  assert.equal((await readPr(reader, 'acme', 'widgets', 6, cfg())).status, 'closed');
  assert.deepEqual(calls.map((c) => c[0]), ['prFields', 'prFields']);
});

test('mergedAt on its own marks a PR as merged', () => {
  assert.equal(parsePrFields(prFields({ state: 'OPEN', mergedAt: '2026-10-01T00:00:00Z' })).status, 'merged');
});

// ---------- threads ----------

function pages(...lists) {
  return lists.map((nodes, i) => ({ nodes, pageInfo: { hasNextPage: i < lists.length - 1, endCursor: i < lists.length - 1 ? `c${i + 1}` : null } }));
}

test('thread paging visits every page and finds an unresolved thread beyond the first', async () => {
  const calls = [];
  const reader = fakeReader({ calls, script: { 1: { threadPages: pages([thread({ id: 'A', resolved: true })], [thread({ id: 'B', resolved: true })], [thread({ id: 'C' })]) } } });
  await reader.prFields('acme', 'widgets', 1);
  const { threads } = await readThreads(reader, 'acme', 'widgets', 1, cfg());
  assert.deepEqual(threads.map((t) => t.id), ['C']);
  assert.equal(calls.filter((c) => c[0] === 'threadPage').length, 3);
});

test('thread paging ends after a single page when there is no next page', async () => {
  const calls = [];
  const reader = fakeReader({ calls, script: { 1: { threads: [thread()] } } });
  await reader.prFields('acme', 'widgets', 1);
  await readThreads(reader, 'acme', 'widgets', 1, cfg());
  assert.equal(calls.filter((c) => c[0] === 'threadPage').length, 1);
});

test('resolved threads on later pages are discarded', async () => {
  const reader = fakeReader({ script: { 1: { threadPages: pages([thread({ id: 'A' })], [thread({ id: 'B', resolved: true }), thread({ id: 'C' })]) } } });
  await reader.prFields('acme', 'widgets', 1);
  const { threads } = await readThreads(reader, 'acme', 'widgets', 1, cfg());
  assert.deepEqual(threads.map((t) => t.id), ['A', 'C']);
});

test('a thread page lacking pageInfo is refused and never taken as the final page', async () => {
  const reader = fakeReader({ script: { 1: { threadPages: [{ nodes: [thread()] }] } } });
  await reader.prFields('acme', 'widgets', 1);
  await assert.rejects(readThreads(reader, 'acme', 'widgets', 1, cfg()), (e) => e instanceof QueryError && /pageInfo/.test(e.detail));
});

test('review-bot threads yield a distinct pass count across pages', async () => {
  const c = cfg({ reviewBots: ['review-bot'] });
  const reader = fakeReader({
    script: {
      1: {
        threadPages: pages(
          [thread({ id: 'A', author: 'review-bot[bot]', body: 'issue\nrun-id: r1' }), thread({ id: 'B', author: 'review-bot[bot]', body: 'run-id: r1', resolved: true })],
          [thread({ id: 'C', author: 'review-bot[bot]', body: 'more\nrun-id: r2' }), thread({ id: 'D', author: 'alice' })],
        ),
      },
    },
  });
  await reader.prFields('acme', 'widgets', 1);
  const { threads, botPasses } = await readThreads(reader, 'acme', 'widgets', 1, c);
  assert.equal(botPasses, 2);
  assert.deepEqual(threads.map((t) => [t.id, t.bot, t.botPasses]), [['A', true, 2], ['C', true, 2], ['D', false, 2]]);
});

test('a bot thread without a pass id is one pass, and with no bot configured the count is zero', async () => {
  const reader = fakeReader({ script: { 1: { threads: [thread({ author: 'review-bot', body: 'nit' })] } } });
  await reader.prFields('acme', 'widgets', 1);
  assert.equal((await readThreads(reader, 'acme', 'widgets', 1, cfg({ reviewBots: ['review-bot'] }))).botPasses, 1);
  assert.equal((await readThreads(reader, 'acme', 'widgets', 1, cfg())).botPasses, 0);
});

test('a host account is treated as the bot only if the body carries a marker', async () => {
  const c = cfg({ reviewBotHosts: ['github-actions[bot]'], reviewBotMarkers: ['<!-- review-pass -->'] });
  const reader = fakeReader({
    script: { 1: { threads: [thread({ id: 'A', author: 'github-actions[bot]', body: '<!-- review-pass --> x' }), thread({ id: 'B', author: 'github-actions[bot]', body: 'lint' })] } },
  });
  await reader.prFields('acme', 'widgets', 1);
  const { threads } = await readThreads(reader, 'acme', 'widgets', 1, c);
  assert.deepEqual(threads.map((t) => t.bot), [true, false]);
});

// ---------- checks ----------

async function checksFor(state, c = cfg()) {
  const calls = [];
  const reader = fakeReader({ calls, script: { 1: state } });
  await reader.prFields('acme', 'widgets', 1);
  calls.length = 0;
  const result = await readChecks(reader, 'acme', 'widgets', 1, c);
  return { result, calls };
}

test('a non-empty fast path avoids GraphQL', async () => {
  const { result, calls } = await checksFor({ checks: [passCheck(), pendCheck('lint')] });
  assert.equal(result.source, 'checks');
  assert.deepEqual(result.checks.map((c) => c.result), ['passed', 'pending']);
  assert.ok(!calls.some((c) => c[0] === 'rollupPage'));
});

test('fast path exit codes 1 and 8 remain usable', async () => {
  for (const code of [1, 8]) {
    const { result } = await checksFor({ fast: { code, stdout: JSON.stringify([passCheck()]), stderr: '' } });
    assert.equal(result.source, 'checks');
  }
});

test('an unusable fast path pages through the GraphQL rollup', async () => {
  const run = (name) => ({ __typename: 'CheckRun', name, status: 'COMPLETED', conclusion: 'SUCCESS' });
  const { result, calls } = await checksFor({
    fast: { code: 4, stdout: '', stderr: 'boom' },
    rollupPages: [
      { nodes: [run('a')], pageInfo: { hasNextPage: true, endCursor: 'r1' } },
      { nodes: [run('b')], pageInfo: { hasNextPage: false, endCursor: null } },
    ],
  });
  assert.equal(result.source, 'rollup');
  assert.deepEqual(result.checks.map((c) => c.name), ['a', 'b']);
  assert.equal(calls.filter((c) => c[0] === 'rollupPage').length, 2);
});

test('fast-path JSON that is valid but empty falls back to the rollup', async () => {
  const { result } = await checksFor({
    fast: { code: 0, stdout: '[]', stderr: '' },
    rollupPages: [{ nodes: [{ __typename: 'StatusContext', context: 'ci/legacy', state: 'SUCCESS' }], pageInfo: { hasNextPage: false } }],
  });
  assert.equal(result.source, 'rollup');
});

test('fast-path JSON that is not an array falls back', async () => {
  const { result } = await checksFor({
    fast: { code: 0, stdout: '{"x":1}', stderr: '' },
    rollupPages: [{ nodes: [{ __typename: 'StatusContext', context: 'ci', state: 'SUCCESS' }], pageInfo: { hasNextPage: false } }],
  });
  assert.equal(result.source, 'rollup');
});

test('when both sources are empty it fails closed with the fast-path exit and stderr', async () => {
  await assert.rejects(
    checksFor({ fast: { code: 4, stdout: '', stderr: 'no checks reported\nmore' } }),
    (e) => e instanceof QueryError && e.kind === 'checks-unavailable' && /exit 4/.test(e.detail) && /no checks reported/.test(e.detail) && !/more/.test(e.detail),
  );
});

test('CheckRun rollup mapping fails closed on unknown terminal states', () => {
  const m = (status, conclusion) => mapRollupNode({ __typename: 'CheckRun', name: 'x', status, conclusion }, cfg()).result;
  assert.equal(m('IN_PROGRESS', null), 'pending');
  assert.equal(m('QUEUED', null), 'pending');
  assert.equal(m('COMPLETED', 'SUCCESS'), 'passed');
  assert.equal(m('COMPLETED', 'NEUTRAL'), 'skipped');
  assert.equal(m('COMPLETED', 'SKIPPED'), 'skipped');
  assert.equal(m('COMPLETED', 'ACTION_REQUIRED'), 'failed');
  assert.equal(m('COMPLETED', 'FAILURE'), 'failed');
  assert.equal(m('COMPLETED', 'STALE'), 'failed');
  assert.equal(m('COMPLETED', 'SOMETHING_NEW'), 'failed');
});

test('StatusContext states map as expected and unknown typenames are skipped', () => {
  const m = (state) => mapRollupNode({ __typename: 'StatusContext', context: 'x', state }, cfg()).result;
  assert.equal(m('PENDING'), 'pending');
  assert.equal(m('EXPECTED'), 'pending');
  assert.equal(m('SUCCESS'), 'passed');
  assert.equal(m('FAILURE'), 'failed');
  assert.equal(m('ERROR'), 'failed');
  assert.equal(mapRollupNode({ __typename: 'Mystery', name: 'x' }, cfg()), null);
});

test('fast path mapping handles every bucket and fails closed', () => {
  const m = (state, bucket) => mapFastCheck({ name: 'x', state, bucket }, cfg()).result;
  assert.equal(m('ACTION_REQUIRED', 'fail'), 'failed');
  assert.equal(m('ERROR', 'pass'), 'failed');
  assert.equal(m('FAILURE', ''), 'failed');
  assert.equal(m('IN_PROGRESS', 'pending'), 'pending');
  assert.equal(m('SUCCESS', 'pass'), 'passed');
  assert.equal(m('SKIPPED', 'skipping'), 'skipped');
  assert.equal(m('CANCELLED', 'cancel'), 'failed');
});

test('the approval check gates from the rollup when in progress, from the rollup when action is required, and from the fast path', () => {
  const c = cfg({ approvalChecks: ['Owner approval'] });
  assert.equal(mapRollupNode({ __typename: 'CheckRun', name: 'Owner approval', status: 'IN_PROGRESS' }, c).result, 'gate');
  assert.equal(mapRollupNode({ __typename: 'CheckRun', name: 'Owner approval', status: 'COMPLETED', conclusion: 'ACTION_REQUIRED' }, c).result, 'gate');
  assert.equal(mapRollupNode({ __typename: 'StatusContext', context: 'Owner approval', state: 'PENDING' }, c).result, 'gate');
  assert.equal(mapFastCheck({ name: 'Owner approval', state: 'ACTION_REQUIRED', bucket: 'fail' }, c).result, 'gate');
  assert.equal(mapFastCheck({ name: 'Owner approval', state: 'PENDING', bucket: 'pending' }, c).result, 'gate');
  // With no approval check configured, the same names are ordinary checks.
  assert.equal(mapFastCheck({ name: 'Owner approval', state: 'PENDING', bucket: 'pending' }, cfg()).result, 'pending');
});

test('queued reads with pending checks and no failures skip the commit rollup', async () => {
  const calls = [];
  const reader = fakeReader({ calls, script: { 1: { checks: [pendCheck()] } } });
  const snap = await readPr(reader, 'acme', 'widgets', 1, cfg(), { queued: true });
  assert.equal(snap.ci.state, 'pending');
  assert.ok(!calls.some((c) => c[0] === 'commitRollups'));
});

test('queued reads whose checks settled or failed fetch commit rollups', async () => {
  for (const checks of [[passCheck()], [pendCheck(), { ...passCheck('x'), state: 'FAILURE', bucket: 'fail' }]]) {
    const calls = [];
    const reader = fakeReader({ calls, script: { 1: { checks } } });
    await readPr(reader, 'acme', 'widgets', 1, cfg(), { queued: true });
    assert.ok(calls.some((c) => c[0] === 'commitRollups'));
  }
});

test('pending check names reveal that review automation is running', async () => {
  const reader = fakeReader({ script: { 1: { checks: [pendCheck('security-review / scan')] } } });
  assert.equal((await readPr(reader, 'acme', 'widgets', 1, cfg())).reviewAutomationRunning, true);
  const reader2 = fakeReader({ script: { 1: { checks: [pendCheck('review-bot pass')] } } });
  assert.equal((await readPr(reader2, 'acme', 'widgets', 1, cfg({ reviewBots: ['review-bot'] }))).reviewAutomationRunning, true);
});
