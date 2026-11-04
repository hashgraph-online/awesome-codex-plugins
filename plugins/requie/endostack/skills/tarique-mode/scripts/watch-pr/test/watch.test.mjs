import { test } from 'node:test';
import assert from 'node:assert/strict';
import { watch, retryBackoff } from '../lib/watch.mjs';
import { main } from '../lib/main.mjs';
import { render } from '../lib/render.mjs';
import { QueryError } from '../lib/errors.mjs';
import { cfg, fakeClock, fakeReader, prFields, passCheck, pendCheck, failCheck, thread, baseOpts, collector } from './fakes.mjs';

const ok = (over = {}) => ({ fields: prFields(), checks: [passCheck()], ...over });
const pending = (over = {}) => ({ fields: prFields(), checks: [pendCheck()], ...over });
const merged = () => ({ fields: prFields({ state: 'MERGED', mergedAt: '2026-10-01T00:00:00Z' }) });

async function run(opts, script, extra = {}) {
  const clock = extra.clock ?? fakeClock();
  const calls = [];
  const reader = extra.reader ?? fakeReader({ script, calls, openPrs: extra.openPrs ?? [] });
  const { out, write } = collector();
  const code = await watch(baseOpts(opts), extra.cfg ?? cfg(), { reader, clock, write });
  return { code, out, clock, calls };
}

// ---------- single ----------

test('single: a clean PR is READY, exits 0, and carries its proof', async () => {
  const { code, out } = await run({}, { 1: ok() });
  assert.equal(code, 0);
  assert.equal(out.length, 1);
  const v = out[0];
  assert.equal(v.kind, 'READY');
  assert.equal(v.terminal, true);
  assert.equal(v.exitCode, 0);
  assert.equal(v.schema, 1);
  assert.equal(v.seq, 1);
  assert.equal(v.mode, 'single');
  const expected = { pr: 1, state: 'OPEN', mergeable: 'MERGEABLE', mergeState: 'CLEAN', ci: 'clean', githubAllows: true, threads: 0, reviewDecision: 'APPROVED', draft: 'ready-for-review' };
  assert.deepEqual(v.prs[0], expected);
});

test('single: tiers rank conflicts, then threads, then checks, then gate', async () => {
  const all = { fields: prFields({ mergeable: 'CONFLICTING', isDraft: true }), threads: [thread()], checks: [failCheck()] };
  assert.equal((await run({}, { 1: all })).code, 2);
  assert.equal((await run({}, { 1: { ...all, fields: prFields({ isDraft: true }) } })).code, 3);
  assert.equal((await run({}, { 1: { ...all, fields: prFields({ isDraft: true }), threads: [] } })).code, 4);
  assert.equal((await run({}, { 1: { fields: prFields({ isDraft: true }), checks: [passCheck()] } })).code, 6);
});

test('single: a DIRTY merge state counts as a conflict', async () => {
  const { code, out } = await run({}, { 1: ok({ fields: prFields({ mergeStateStatus: 'DIRTY' }) }) });
  assert.equal(code, 2);
  assert.equal(out[0].blocker, 'conflict');
});

test('single: clean visible checks with a GitHub refusal exit 4', async () => {
  const st = ok({ fields: prFields({ mergeStateStatus: 'BLOCKED' }), commits: [{ oid: 'b'.repeat(40), state: 'SUCCESS' }, { oid: 'a'.repeat(40), state: 'FAILURE' }] });
  const { code, out } = await run({}, { 1: st });
  assert.equal(code, 4);
  assert.equal(out[0].ciState, 'rejected');
  assert.deepEqual(out[0].github, { refuses: true, mergeState: 'BLOCKED', headRollup: 'FAILURE', wasGreenBefore: true });
});

test('single: BLOCKED while the rollup is pending is not a refusal', async () => {
  const st = ok({ fields: prFields({ mergeStateStatus: 'BLOCKED' }), commits: [{ oid: 'a'.repeat(40), state: 'PENDING' }] });
  assert.equal((await run({}, { 1: st })).code, 0);
});

test('single: gates fire for changes requested, a closed PR, and the approval check', async () => {
  const cr = await run({}, { 1: ok({ fields: prFields({ reviewDecision: 'CHANGES_REQUESTED' }) }) });
  assert.equal(cr.code, 6);
  assert.equal(cr.out[0].reason, 'changes-requested');
  const closed = await run({}, { 1: { fields: prFields({ state: 'CLOSED' }) } });
  assert.equal(closed.code, 6);
  assert.equal(closed.out[0].reason, 'closed');
  const appr = await run({}, { 1: ok({ checks: [passCheck(), pendCheck('Owner approval')] }) }, { cfg: cfg({ approvalChecks: ['Owner approval'] }) });
  assert.equal(appr.code, 6);
  assert.equal(appr.out[0].reason, 'approval-check');
});

test('single: --allow-draft allows a draft to be READY', async () => {
  const { code, out } = await run({ allowDraft: true }, { 1: ok({ fields: prFields({ isDraft: true }) }) });
  assert.equal(code, 0);
  assert.equal(out[0].prs[0].draft, 'draft-permitted');
});

test('single: a draft waits for pending checks before the draft gate applies', async () => {
  const draft = prFields({ isDraft: true });
  const { code, out } = await run({}, { 1: [pending({ fields: draft }), ok({ fields: draft })] });
  assert.deepEqual(out.map((v) => v.kind), ['WAITING', 'BLOCKER']);
  assert.equal(code, 6);
  assert.equal(out[1].reason, 'draft');
});

test('single: pending followed by ready prints WAITING then READY after one interval of sleep', async () => {
  const { code, out, clock } = await run({ interval: 30 }, { 1: [pending(), ok()] });
  assert.equal(code, 0);
  assert.deepEqual(out.map((v) => [v.kind, v.seq, v.terminal]), [['WAITING', 1, false], ['READY', 2, true]]);
  assert.deepEqual(out[0].pending, ['build']);
  assert.deepEqual(clock.sleeps, [30]);
});

test('single: a deadline yields TIMEOUT, exit 5, and pending checks, with sleeps cut off at the deadline', async () => {
  const { code, out, clock } = await run({ interval: 60, timeout: 100 }, { 1: pending() });
  assert.equal(code, 5);
  const last = out.at(-1);
  assert.equal(last.kind, 'TIMEOUT');
  assert.deepEqual(last.pending, ['build']);
  assert.deepEqual(clock.sleeps, [60, 40]);
});

test('without a deadline, each sleep lasts the whole interval', async () => {
  const { clock } = await run({ interval: 7.5 }, { 1: [pending(), pending(), pending(), ok()] });
  assert.deepEqual(clock.sleeps, [7.5, 7.5, 7.5]);
});

test('the thread blocker lists every thread and annotates bot threads', async () => {
  const { code, out } = await run({}, { 1: ok({ threads: [thread({ author: 'review-bot', body: 'x\nrun-id: z9' })] }) }, { cfg: cfg({ reviewBots: ['review-bot'] }) });
  assert.equal(code, 3);
  assert.equal(out[0].threads[0].bot, true);
  assert.equal(out[0].threads[0].botPasses, 1);
  assert.equal(out[0].botPasses, 1);
});

// ---------- retries ----------

test('retry backoff stays between a 60s floor and a 300s cap', () => {
  assert.equal(retryBackoff(5, 1), 60);
  assert.equal(retryBackoff(5, 2), 120);
  assert.equal(retryBackoff(5, 3), 240);
  assert.equal(retryBackoff(5, 4), 300);
  assert.equal(retryBackoff(90, 1), 90);
  assert.equal(retryBackoff(400, 1), 300);
});

test('failed queries RETRY with backoff and a success clears the counter', async () => {
  const err = () => new QueryError('command-failed', 'HTTP 502');
  const { code, out, clock } = await run({ interval: 10, maxQueryErrors: 3 }, { 1: [err(), err(), pending(), err(), err(), ok()] });
  assert.equal(code, 0);
  assert.deepEqual(out.map((v) => v.kind), ['RETRY', 'RETRY', 'WAITING', 'RETRY', 'RETRY', 'READY']);
  assert.deepEqual(out.filter((v) => v.kind === 'RETRY').map((v) => v.failures), [1, 2, 1, 2]);
  assert.deepEqual(clock.sleeps, [60, 120, 10, 60, 120]);
});

test('exhausting the error budget gives a status-query BLOCKER and exit 7', async () => {
  const { code, out } = await run({ maxQueryErrors: 2 }, { 1: new QueryError('json-parse', 'bad json') });
  assert.equal(code, 7);
  const last = out.at(-1);
  assert.equal(last.kind, 'BLOCKER');
  assert.equal(last.blocker, 'status-query');
  assert.equal(last.failures, 2);
  assert.equal(last.error.kind, 'json-parse');
});

test('an unknown enum value is retried and reported raw', async () => {
  const { code, out } = await run({ maxQueryErrors: 1 }, { 1: ok({ fields: prFields({ reviewDecision: 'MAYBE' }) }) });
  assert.equal(code, 7);
  assert.equal(out[0].error.raw, 'MAYBE');
});

test('a context failure that cannot be retried stops immediately with exit 7', async () => {
  const reader = fakeReader({ lookup: { number: 1, url: 'https://enterprise.example/o/r/pull/1' } });
  const { code, out } = await run({ owner: null, repo: null, pr: null }, {}, { reader });
  assert.equal(code, 7);
  assert.equal(out.length, 1);
  assert.equal(out[0].error.kind, 'invalid-pr-url');
});

test('a deadline that passes mid-retry gives TIMEOUT status-unavailable', async () => {
  const { code, out } = await run({ timeout: 30, maxQueryErrors: 10 }, { 1: new QueryError('command-failed', 'down') });
  assert.equal(code, 5);
  assert.equal(out.at(-1).reason, 'status-unavailable');
});

// ---------- stack ----------

const stackPrs = [
  { number: 1, headRefName: 'a', baseRefName: 'main', isCrossRepository: false },
  { number: 2, headRefName: 'b', baseRefName: 'a', isCrossRepository: false },
  { number: 3, headRefName: 'c', baseRefName: 'b', isCrossRepository: false },
];

test('stack: a conflict higher up outranks a CI failure at the bottom', async () => {
  const { code, out } = await run({ mode: 'stack', pr: 1 }, { 1: ok({ checks: [failCheck()] }), 2: ok(), 3: ok({ fields: prFields({ mergeable: 'CONFLICTING' }) }) }, { openPrs: stackPrs });
  assert.equal(code, 2);
  assert.equal(out[0].kind, 'STATUS');
  assert.equal(out[0].terminal, false);
  assert.equal(out[1].pr, 3);
});

test('stack: WAITING names the member whose checks are still running', async () => {
  const { out } = await run({ mode: 'stack', pr: 1, timeout: 1 }, { 1: ok(), 2: pending({ checks: [pendCheck('e2e')] }), 3: ok() }, { openPrs: stackPrs });
  const wait = out.find((v) => v.kind === 'WAITING');
  assert.equal(wait.pr, 2);
  assert.deepEqual(wait.pending, ['e2e']);
});

test('stack: when all is clear, READY lists every PR including merged rows', async () => {
  const { code, out } = await run({ mode: 'stack', pr: 2 }, { 1: merged(), 2: ok(), 3: ok() }, { openPrs: stackPrs });
  assert.equal(code, 0);
  assert.deepEqual(out.at(-1).prs.map((p) => p.pr), [1, 2, 3]);
  assert.equal(out.at(-1).prs[0].merged, true);
});

// ---------- status only ----------

test('status-only prints a single terminal STATUS and exits 0 despite blockers', async () => {
  const { code, out } = await run({ statusOnly: true }, { 1: ok({ checks: [failCheck()] }) });
  assert.equal(code, 0);
  assert.equal(out.length, 1);
  assert.equal(out[0].kind, 'STATUS');
  assert.equal(out[0].terminal, true);
  assert.equal(out[0].rows[0].ci.state, 'failing');
});

test('queued mode with --status-only skips the queue machine', async () => {
  const { code, out } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2], statusOnly: true }, { 1: merged(), 2: pending() });
  assert.equal(code, 0);
  assert.deepEqual(out.map((v) => v.kind), ['STATUS']);
  assert.deepEqual(out[0].rows.map((r) => r.status), ['merged', 'open']);
});

// ---------- queued ----------

test('queued: QUEUE, a sweep STATUS, then COMPLETE once everything merged', async () => {
  const { code, out } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2] }, { 1: merged(), 2: merged() });
  assert.equal(code, 0);
  assert.deepEqual(out.map((v) => v.kind), ['QUEUE', 'STATUS', 'COMPLETE']);
  assert.deepEqual(out[0].prs, [1, 2]);
  assert.deepEqual(out[2].merged, [1, 2]);
  assert.ok(!out.some((v) => v.kind === 'READY'));
});

test('queued: a failed sweep read restarts at the same PR and STATUS waits for the final read', async () => {
  const calls = [];
  const fail = new QueryError('command-failed', 'flaky');
  const reader = fakeReader({ calls, script: { 1: merged(), 2: [fail, merged()], 3: merged() } });
  const { out } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2, 3] }, null, { reader });
  assert.deepEqual(calls.filter((c) => c[0] === 'prFields').map((c) => c[1]), [1, 2, 2, 3]);
  assert.deepEqual(out.map((v) => v.kind), ['QUEUE', 'RETRY', 'STATUS', 'COMPLETE']);
  assert.equal(out[2].rows.length, 3);
});

test('queued: ADVANCE moves on with no sleep', async () => {
  const { out, clock } = await run(
    { mode: 'queued', pr: null, stackPrs: [1, 2], interval: 10 },
    { 1: [pending(), merged()], 2: [ok(), merged()] },
  );
  const kinds = out.map((v) => v.kind);
  assert.deepEqual(kinds, ['QUEUE', 'STATUS', 'WAITING', 'ADVANCE', 'COMPLETE']);
  const adv = out[3];
  assert.deepEqual(adv.merged, [1]);
  assert.equal(adv.frontier, 2);
  assert.equal(adv.remaining, 1);
  // One sleep after WAITING; none after ADVANCE.
  assert.deepEqual(clock.sleeps, [10]);
});

test('queued: repeated identical waits print once and the next sweep is scheduled', async () => {
  const calls = [];
  const reader = fakeReader({ calls, script: { 1: [pending(), pending(), pending(), pending(), pending(), merged()], 2: [ok(), ok(), merged()] } });
  const { out } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2], interval: 10, sweepInterval: 25 }, null, { reader });
  const kinds = out.map((v) => v.kind);
  assert.equal(kinds.filter((k) => k === 'WAITING').length, 1);
  // Initial sweep reads 1,2; frontier polls 1,1; at t>=25 a new sweep reads 1,2.
  const reads = calls.filter((c) => c[0] === 'prFields').map((c) => c[1]);
  assert.deepEqual(reads.slice(0, 6), [1, 2, 1, 1, 1, 2]);
  assert.equal(kinds.filter((k) => k === 'STATUS').length >= 2, true);
});

test('queued: pending checks higher in the stack do not hold back a frontier with no blockers', async () => {
  const { out, code } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2], timeout: 5 }, { 1: ok(), 2: pending() });
  const wait = out.find((v) => v.kind === 'WAITING');
  assert.equal(wait.reason, 'merge-queue');
  assert.equal(wait.pr, 1);
  assert.equal(wait.unmerged, 2);
  assert.equal(code, 5);
  const t = out.at(-1);
  assert.equal(t.kind, 'TIMEOUT');
  assert.equal(t.pr, 1);
  assert.equal(t.unmerged, 2);
});

test('queued: any blocker among the active rows is terminal, ranked by tier first', async () => {
  const { code, out } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2] }, { 1: ok({ checks: [failCheck()] }), 2: ok({ threads: [thread()] }) });
  assert.equal(code, 3);
  assert.equal(out.at(-1).pr, 2);
});

test('queued: a pending frontier waits for its own checks', async () => {
  const { out } = await run({ mode: 'queued', pr: null, stackPrs: [1, 2], timeout: 1 }, { 1: pending({ checks: [pendCheck('unit')] }), 2: ok() });
  const wait = out.find((v) => v.kind === 'WAITING');
  assert.equal(wait.reason, 'checks');
  assert.deepEqual(wait.pending, ['unit']);
});

test('queued without --stack-prs discovers the stack a single time', async () => {
  const { out } = await run({ mode: 'queued', pr: 2 }, { 1: merged(), 2: merged(), 3: merged() }, { openPrs: stackPrs });
  assert.deepEqual(out[0].prs, [1, 2, 3]);
});

// ---------- output ----------

test('the default output is compact NDJSON and --pretty renders the same verdicts', async () => {
  const reader = fakeReader({ script: { 1: [pending(), ok({ fields: prFields({ isDraft: true }) })] } });
  let json = '';
  const code = await main(['--owner', 'acme', '--repo', 'widgets', '--pr', '1', '--allow-draft', '--interval', '1'], {
    stdout: (s) => (json += s), stderr: () => {}, reader, clock: fakeClock(), readText: async () => { throw new Error('none'); },
  });
  assert.equal(code, 0);
  const lines = json.trimEnd().split('\n');
  assert.equal(lines.length, 2);
  for (const l of lines) {
    assert.ok(!l.includes('\n') && !/^\s|:\s/.test(l.slice(0, 12)));
    JSON.parse(l);
  }
  const ready = JSON.parse(lines[1]);
  const text = render(ready);
  assert.match(text, /^READY: #1: no conflicts, no unresolved threads, no failing or pending checks\./);
  assert.match(text, /leave it as a draft/);
});

test('pretty STATUS draws a table with PR links, dashes on merged rows, and a was-green suffix', () => {
  const v = {
    kind: 'STATUS',
    rows: [
      { pr: 1, url: 'https://github.com/o/r/pull/1', status: 'merged', merge: 'merged' },
      {
        pr: 2, url: 'https://github.com/o/r/pull/2', status: 'open', merge: 'ok', threads: 2, reviewAutomationRunning: true,
        ci: { state: 'failing', failed: ['a'], pending: ['b'], wasGreenBefore: true },
      },
      { pr: 3, url: 'https://github.com/o/r/pull/3', status: 'open', merge: 'draft', threads: 0, reviewAutomationRunning: false, ci: { state: 'rejected', failed: [], pending: [], headRollup: 'ERROR', wasGreenBefore: false } },
    ],
  };
  const text = render(v);
  assert.match(text, /\| PR \| Checks \| Threads \| Mergeability \|/);
  assert.match(text, /\| \[#1\]\(https:\/\/github\.com\/o\/r\/pull\/1\) \| - \| - \| merged \|/);
  assert.match(text, /1 failed, 1 pending \(was green before\) \| 2 open threads, review automation running \| ok/);
  assert.match(text, /GitHub-reported failure \(head rollup ERROR\) \| 0 open threads \| draft/);
});

test('pretty BLOCKER prints key=value lines, truncated bodies, and an action line', async () => {
  const long = 'x'.repeat(400);
  const { out } = await run({}, { 1: ok({ threads: [thread({ body: `${long}\nsecond` })] }) });
  const text = render(out[0]);
  const lines = text.split('\n');
  assert.match(lines[0], /^BLOCKER: unresolved review threads on #1 \(exit 3\)/);
  assert.ok(lines.includes('pr=1'));
  const t = lines.find((l) => l.startsWith('thread '));
  assert.ok(t.includes(`"${'x'.repeat(180)}..."`));
  assert.ok(!t.includes('second'));
  assert.match(lines.at(-1), /^action=/);
});

test('pretty single-line output for QUEUE, WAITING, ADVANCE, RETRY, COMPLETE, and TIMEOUT', () => {
  assert.match(render({ kind: 'QUEUE', prs: [1, 2] }), /QUEUE: watching 2 PRs bottom to top: #1 #2/);
  assert.match(render({ kind: 'WAITING', reason: 'merge-queue', pr: 1, unmerged: 2 }), /merge queue \(2 unmerged\)/);
  assert.match(render({ kind: 'WAITING', reason: 'checks', pr: 1, pending: ['a', 'b'] }), /#1 has 2 pending checks: a, b/);
  assert.match(render({ kind: 'ADVANCE', merged: [1], frontier: 2, remaining: 1 }), /frontier is now #2; 1 remaining/);
  assert.match(render({ kind: 'RETRY', error: { kind: 'json-parse', detail: 'x' }, failures: 1, backoffSeconds: 60 }), /retrying in 60s/);
  assert.match(render({ kind: 'COMPLETE', merged: [1, 2] }), /all 2 queued PRs merged/);
  assert.match(render({ kind: 'TIMEOUT', mode: 'queued', pr: 3, unmerged: 2 }), /frontier #3 and 2 unmerged/);
});
