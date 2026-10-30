import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseCli } from '../lib/args.mjs';
import { main } from '../lib/main.mjs';
import { loadConfig } from '../lib/config.mjs';
import { UsageError } from '../lib/errors.mjs';

test('default options agree with the documented table', () => {
  const o = parseCli([]);
  assert.equal(o.mode, 'single');
  assert.equal(o.pr, null);
  assert.equal(o.owner, null);
  assert.equal(o.repo, null);
  assert.equal(o.interval, 60);
  assert.equal(o.sweepInterval, 300);
  assert.equal(o.timeout, 0);
  assert.equal(o.maxQueryErrors, 5);
  assert.equal(o.statusOnly, false);
  assert.equal(o.allowDraft, false);
  assert.equal(o.pretty, false);
  assert.deepEqual(o.reviewBots, []);
  assert.deepEqual(o.approvalChecks, []);
});

test('a queued stack list with # and spaces, a fractional interval, and every flag', () => {
  const o = parseCli([
    '--owner', 'acme', '--repo', 'widgets', '--stack-prs', '#10, 11,#12', '--queued-stack',
    '--interval', '0.5', '--sweep-interval', '2.5', '--timeout', '90', '--max-query-errors', '3',
    '--status-only', '--allow-draft', '--pretty', '--review-bot', 'reviewer-bot', '--review-bot', 'sec-bot',
    '--approval-check', 'Owner approval',
  ]);
  assert.equal(o.mode, 'queued');
  assert.deepEqual(o.stackPrs, [10, 11, 12]);
  assert.equal(o.interval, 0.5);
  assert.equal(o.sweepInterval, 2.5);
  assert.equal(o.timeout, 90);
  assert.equal(o.maxQueryErrors, 3);
  assert.ok(o.statusOnly && o.allowDraft && o.pretty);
  assert.deepEqual(o.reviewBots, ['reviewer-bot', 'sec-bot']);
  assert.deepEqual(o.approvalChecks, ['Owner approval']);
});

test('--pr tolerates a leading #', () => {
  assert.equal(parseCli(['--pr', '#42']).pr, 42);
  assert.equal(parseCli(['--stack', '--pr', '7']).mode, 'stack');
});

const BAD = [
  ['--bogus'],
  ['--pr', '0'],
  ['--pr', 'abc'],
  ['--pr', '99999999999999999999'],
  ['--interval', '0'],
  ['--interval', '-1'],
  ['--interval', 'fast'],
  ['--sweep-interval', '0'],
  ['--timeout', '-5'],
  ['--max-query-errors', '0'],
  ['--max-query-errors', '1.5'],
  ['--queued-stack', '--stack'],
  ['--stack-prs', '4,5'],
  ['--queued-stack', '--stack-prs', '1,2,1'],
  ['--queued-stack', '--stack-prs', ''],
  ['--queued-stack', '--stack-prs', '1,,2'],
  ['--owner', 'a/b'],
  ['--review-bot', ' '],
  ['extra-positional'],
];

for (const argv of BAD) {
  test(`rejected as usage: ${argv.join(' ') || '(empty)'}`, async () => {
    let out = '';
    let err = '';
    let readerCalled = false;
    const reader = new Proxy({}, { get: () => () => { readerCalled = true; } });
    const code = await main(argv, { stdout: (s) => (out += s), stderr: (s) => (err += s), reader, readText: async () => { throw Object.assign(new Error('x'), { code: 'ENOENT' }); } });
    assert.equal(code, 64);
    assert.equal(out, '');
    assert.match(err, /^error: /);
    assert.equal(readerCalled, false);
  });
}

test('--help exits 0 without calling the reader', async () => {
  let out = '';
  let touched = false;
  const reader = new Proxy({}, { get: () => () => { touched = true; } });
  const code = await main(['--help'], { stdout: (s) => (out += s), stderr: () => {}, reader });
  assert.equal(code, 0);
  assert.match(out, /usage: watch-pr/);
  assert.match(out, /--approval-check/);
  assert.equal(touched, false);
});

test('the config file provides bot logins and approval checks, and flags add to them', async () => {
  const text = JSON.stringify({ reviewBots: ['review-bot'], approvalChecks: ['Owner gate'], reviewBotHosts: ['github-actions[bot]'], reviewBotMarkers: ['<!-- review-pass -->'] });
  const c = await loadConfig({ configPath: 'w.json', reviewBots: ['extra-bot'], approvalChecks: [] }, { readText: async () => text });
  assert.deepEqual(c.reviewBots, ['review-bot', 'extra-bot']);
  assert.deepEqual(c.approvalChecks, ['Owner gate']);
  assert.deepEqual(c.reviewBotHosts, ['github-actions[bot]']);
});

test('config: an absent default file is accepted, while an absent explicit file or bad keys are usage errors', async () => {
  const enoent = async () => { throw Object.assign(new Error('nope'), { code: 'ENOENT' }); };
  const c = await loadConfig({ configPath: null, reviewBots: [], approvalChecks: [] }, { readText: enoent });
  assert.deepEqual(c.approvalChecks, []);
  await assert.rejects(loadConfig({ configPath: 'x.json', reviewBots: [], approvalChecks: [] }, { readText: enoent }), UsageError);
  await assert.rejects(loadConfig({ configPath: 'x.json', reviewBots: [], approvalChecks: [] }, { readText: async () => '{"reviewbots":[]}' }), /unknown key/);
  await assert.rejects(loadConfig({ configPath: 'x.json', reviewBots: [], approvalChecks: [] }, { readText: async () => '{"passIdPattern":"("}' }), /regular expression/);
});
