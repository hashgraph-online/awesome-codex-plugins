import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseRemote, parsePrUrl, resolveTarget, buildStack } from '../lib/context.mjs';
import { githubReader, LIST_FIELDS } from '../lib/github.mjs';
import { QueryError } from '../lib/errors.mjs';
import { fakeReader, baseOpts } from './fakes.mjs';

test('remote parsing accepts exactly the three github.com forms', () => {
  assert.deepEqual(parseRemote('https://github.com/acme/widgets.git'), { owner: 'acme', repo: 'widgets' });
  assert.deepEqual(parseRemote('https://github.com/acme/widgets'), { owner: 'acme', repo: 'widgets' });
  assert.deepEqual(parseRemote('git@github.com:acme/widgets.git'), { owner: 'acme', repo: 'widgets' });
  assert.deepEqual(parseRemote('ssh://git@github.com/acme/widgets'), { owner: 'acme', repo: 'widgets' });
  for (const bad of [
    'https://github.com:443/acme/widgets',
    'https://user:tok@github.com/acme/widgets',
    'https://github.com/acme/widgets?x=1',
    'https://github.com/acme/widgets#frag',
    'https://github.com/acme/widgets/extra',
    'https://gitlab.com/acme/widgets',
    'ssh://git@github.com:22/acme/widgets',
    'http://github.com/acme/widgets',
    null,
  ]) {
    assert.equal(parseRemote(bad), null, String(bad));
  }
});

test('PR URL parsing insists on the canonical form', () => {
  assert.deepEqual(parsePrUrl('https://github.com/acme/widgets/pull/12'), { owner: 'acme', repo: 'widgets', number: 12 });
  assert.equal(parsePrUrl('https://github.com/acme/widgets/pull/12/files'), null);
  assert.equal(parsePrUrl('https://example.com/acme/widgets/pull/12'), null);
});

test('a fully specified context skips the reader', async () => {
  const calls = [];
  const t = await resolveTarget(baseOpts({ owner: 'o', repo: 'r', pr: 9 }), fakeReader({ calls }));
  assert.deepEqual(t, { owner: 'o', repo: 'r', numbers: [9] });
  assert.equal(calls.length, 0);
});

test('with an explicit number the origin remote is tried before gh', async () => {
  const calls = [];
  const t = await resolveTarget(baseOpts({ owner: null, repo: null, pr: 9 }), fakeReader({ calls }));
  assert.deepEqual(t, { owner: 'acme', repo: 'widgets', numbers: [9] });
  assert.deepEqual(calls.map((c) => c[0]), ['originUrl']);
});

test('an origin outside github falls back to gh pr view', async () => {
  const calls = [];
  const t = await resolveTarget(baseOpts({ owner: null, repo: null, pr: 9 }), fakeReader({ calls, origin: 'https://gitlab.com/x/y' }));
  assert.equal(t.owner, 'acme');
  assert.deepEqual(calls.map((c) => c[0]), ['originUrl', 'lookupPr']);
});

test('without a number, gh pr view on the current branch fills in everything', async () => {
  const calls = [];
  const t = await resolveTarget(baseOpts({ owner: null, repo: null, pr: null }), fakeReader({ calls, lookup: { number: 33, url: 'https://github.com/o/r/pull/33' } }));
  assert.deepEqual(t, { owner: 'o', repo: 'r', numbers: [33] });
  assert.deepEqual(calls.map((c) => c[0]), ['lookupPr']);
});

test('a PR URL in a non-canonical form fails without retry', async () => {
  await assert.rejects(
    resolveTarget(baseOpts({ owner: null, repo: null, pr: null }), fakeReader({ lookup: { number: 1, url: 'https://ghe.corp/o/r/pull/1' } })),
    (e) => e instanceof QueryError && e.kind === 'invalid-pr-url' && e.retryable === false,
  );
});

test('the seed is the first --stack-prs entry', async () => {
  const t = await resolveTarget(baseOpts({ pr: null, stackPrs: [4, 5, 6], mode: 'queued' }), fakeReader());
  assert.deepEqual(t.numbers, [4, 5, 6]);
});

// ---------- stack discovery ----------

const pr = (number, head, base, fork = false) => ({ number, headRefName: head, baseRefName: base, isCrossRepository: fork });

test('stacks come out bottom to top whatever the seed', () => {
  const open = [pr(3, 'c', 'b'), pr(1, 'a', 'main'), pr(2, 'b', 'a'), pr(9, 'other', 'main')];
  assert.deepEqual(buildStack(2, open), [1, 2, 3]);
  assert.deepEqual(buildStack(1, open), [1, 2, 3]);
  assert.deepEqual(buildStack(3, open), [1, 2, 3]);
});

test('children are visited depth first in order of PR number', () => {
  const open = [pr(1, 'a', 'main'), pr(5, 'x', 'a'), pr(4, 'y', 'a'), pr(6, 'y2', 'y')];
  assert.deepEqual(buildStack(1, open), [1, 4, 6, 5]);
});

test('a head on a fork never acts as a parent', () => {
  // Fork PR 7 has head "a" (same name as the base of PR 2) but must not
  // become PR 2's parent.
  const open = [pr(7, 'a', 'main', true), pr(2, 'b', 'a')];
  assert.deepEqual(buildStack(2, open), [2]);
});

test('a fork head gets no children attached', () => {
  const open = [pr(1, 'a', 'main'), pr(2, 'f', 'a', true), pr(3, 'g', 'f')];
  assert.deepEqual(buildStack(1, open), [1, 2]);
});

test('an unrelated fork PR from main to main ends the walk and is excluded', () => {
  const open = [pr(8, 'main', 'main', true), pr(1, 'a', 'main'), pr(2, 'b', 'a')];
  assert.deepEqual(buildStack(1, open), [1, 2]);
  assert.deepEqual(buildStack(8, open), [8]);
});

test('a seed absent from the open list forms the entire stack', () => {
  assert.deepEqual(buildStack(42, [pr(1, 'a', 'main')]), [42]);
});

test('stack discovery requests fork identity from gh', async () => {
  const seen = [];
  const reader = githubReader(async (cmd, args) => {
    seen.push([cmd, ...args]);
    return { code: 0, stdout: '[]', stderr: '' };
  });
  await reader.listOpenPrs('acme', 'widgets');
  const args = seen[0];
  assert.equal(args[0], 'gh');
  assert.ok(args.includes('--state') && args.includes('open') && args.includes('300'));
  assert.ok(LIST_FIELDS.includes('isCrossRepository'));
  assert.equal(args[args.indexOf('--json') + 1], LIST_FIELDS);
});

test('failed gh commands report the first line of stderr', async () => {
  const reader = githubReader(async () => ({ code: 1, stdout: '', stderr: '\nHTTP 401: Bad credentials\nsecond line' }));
  await assert.rejects(reader.prFields('o', 'r', 1), (e) => e.kind === 'command-failed' && e.detail === 'HTTP 401: Bad credentials');
  const silent = githubReader(async () => ({ code: 3, stdout: '', stderr: '' }));
  await assert.rejects(silent.prFields('o', 'r', 1), (e) => /gh pr view 1 .* exited 3/.test(e.detail));
});

test('graphql variables leave strings as strings', async () => {
  let args;
  const reader = githubReader(async (cmd, a) => {
    args = a;
    return { code: 0, stdout: JSON.stringify({ data: { repository: { pullRequest: { reviewThreads: { nodes: [], pageInfo: { hasNextPage: false } } } } } }), stderr: '' };
  });
  await reader.threadPage('123', 'true', 5, null);
  assert.ok(args.includes('owner=123') && args[args.indexOf('owner=123') - 1] === '-f');
  assert.ok(args[args.indexOf('number=5') - 1] === '-F');
});
