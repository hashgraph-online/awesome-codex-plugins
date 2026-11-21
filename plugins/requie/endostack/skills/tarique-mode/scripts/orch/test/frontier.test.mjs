// Frontier resolution against real git fixture repos and a fake gh on PATH.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as path from 'node:path';
import * as fs from 'node:fs';
import { cli, tmpdir, fixtureRepo, fakeGh, ghPr } from './helpers.mjs';

async function setup(branches, prs, { checkout, raw } = {}) {
  const repo = fixtureRepo(branches, { checkout });
  const gh = fakeGh(prs, { raw });
  const store = path.join(tmpdir(), 'store');
  const env = { ORCH_STORE: store, PATH: gh.PATH };
  assert.equal((await cli(['init'], { env })).code, 0);
  return { repo, env, store };
}

test('the base chain yields the ordered frontier over merged, closed, open, and draft PRs, and the pin is checked', async () => {
  // s1 merged, s2 closed (its replacement is not open either), s3 open, s4 draft.
  const { repo, env, store } = await setup(['s1', 's2', 's3', 's4'], [
    ghPr(11, 's1', 'main', 'MERGED'),
    ghPr(12, 's2', 's1', 'CLOSED'),
    ghPr(13, 's3', 's2', 'OPEN'),
    ghPr(14, 's4', 's3', 'OPEN', true),
  ], { checkout: 's3' });
  const r = await cli(['frontier', 'set', '--repo', repo.work, '--prs', '11,12,13,14'], { env });
  assert.equal(r.code, 0, r.stderr);
  assert.equal(
    r.stdout.trim(),
    `generation=1 prs=s1#11@${repo.shas.s1}:MERGED,s2#12@${repo.shas.s2}:CLOSED,s3#13@${repo.shas.s3}:OPEN,s4#14@${repo.shas.s4}:OPEN lowest-unmerged=13`,
  );
  const saved = JSON.parse(fs.readFileSync(path.join(store, 'frontier.json'), 'utf8'));
  assert.equal(saved.generation, 1);
  assert.equal(saved.lowestUnmerged, 13);
  assert.equal((await cli(['frontier', 'show'], { env })).stdout, r.stdout);
  // A second set bumps the generation.
  const again = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.match(again.stdout, /^generation=2 /);
});

test('--prs drift is described as missing, extra, or out-of-order PRs', async () => {
  const { repo, env } = await setup(['a', 'b'], [ghPr(1, 'a', 'main'), ghPr(2, 'b', 'a')]);
  const miss = await cli(['frontier', 'set', '--repo', repo.work, '--prs', '1,2,3'], { env });
  assert.equal(miss.code, 1);
  assert.match(miss.stderr, /resolved stack differs from --prs: missing from chain: #3/);
  const extra = await cli(['frontier', 'set', '--repo', repo.work, '--prs', '1'], { env });
  assert.match(extra.stderr, /not in pin: #2/);
  const order = await cli(['frontier', 'set', '--repo', repo.work, '--prs', '2,1'], { env });
  assert.match(order.stderr, /expected order 2,1, resolved 1,2/);
  const dup = await cli(['frontier', 'set', '--repo', repo.work, '--prs', '1,1'], { env });
  assert.match(dup.stderr, /lists #1 twice/);
  const empty = await cli(['frontier', 'set', '--repo', repo.work, '--prs', '1,,2'], { env });
  assert.match(empty.stderr, /no empty entries/);
});

test('a branch with older closed PRs resolves to its replacement PR', async () => {
  const { repo, env } = await setup(['a', 'b'], [ghPr(1, 'a', 'main'), ghPr(5, 'b', 'a', 'CLOSED'), ghPr(6, 'b', 'a', 'OPEN')]);
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.equal(r.code, 0, r.stderr);
  assert.match(r.stdout, /a#1@[0-9a-f]+:OPEN,b#6@[0-9a-f]+:OPEN lowest-unmerged=1/);
});

test('two active PRs for a single branch are refused', async () => {
  const { repo, env } = await setup(['a'], [ghPr(1, 'a', 'main'), ghPr(2, 'a', 'main')]);
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.equal(r.code, 1);
  assert.match(r.stderr, /found 2 PRs for branch 'a' \(#1 OPEN, #2 OPEN\); close all but one/);
});

test('a stack that forks above the tip is refused', async () => {
  const { repo, env } = await setup(['a'], [ghPr(1, 'a', 'main'), ghPr(2, 'x', 'a'), ghPr(3, 'y', 'a')]);
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.match(r.stderr, /stack forks at 'a': x#2, y#3/);
});

test('gh output that cannot be parsed fails and names the command', async () => {
  const { repo, env } = await setup(['a'], null, { raw: 'Welcome to gh! <html>' });
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.equal(r.code, 1);
  assert.match(r.stderr, /gh pr list .* printed output that is not JSON/);
  const { repo: r2, env: e2 } = await setup(['a'], null, { raw: '[{"number":"1","state":"OPEN","headRefName":"a","baseRefName":"main"}]' });
  const bad = await cli(['frontier', 'set', '--repo', r2.work], { env: e2 });
  assert.match(bad.stderr, /returned a row without a valid number/);
});

test('a branch in the chain lacking a PR is reported by name', async () => {
  const { repo, env } = await setup(['a', 'b'], [ghPr(2, 'b', 'a')]);
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.equal(r.code, 1);
  assert.match(r.stderr, /no PR found for branch 'a'; create one with 'gh pr create'/);
});

test('the frontier is empty when sitting on trunk', async () => {
  const { repo, env } = await setup(['a'], [ghPr(1, 'a', 'main')], { checkout: 'main' });
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.equal(r.code, 0, r.stderr);
  assert.equal(r.stdout.trim(), 'generation=1 prs=(none) lowest-unmerged=none');
});

test('a gh failure is reported along with its command line', async () => {
  const repo = fixtureRepo(['a']);
  const store = path.join(tmpdir(), 'store');
  const dir = tmpdir('orch-gh-');
  fs.writeFileSync(path.join(dir, 'gh'), '#!/bin/sh\necho "HTTP 401: Bad credentials" >&2\nexit 1\n', { mode: 0o755 });
  const env = { ORCH_STORE: store, PATH: `${dir}${path.delimiter}${process.env.PATH}` };
  await cli(['init'], { env });
  const r = await cli(['frontier', 'set', '--repo', repo.work], { env });
  assert.match(r.stderr, /command failed: gh pr list .*--head a.*: HTTP 401: Bad credentials/);
});

test('the repository comes from ORCH_REPO', async () => {
  const { repo, env } = await setup(['a'], [ghPr(1, 'a', 'main')]);
  const r = await cli(['frontier', 'set'], { env: { ...env, ORCH_REPO: repo.work } });
  assert.equal(r.code, 0, r.stderr);
  assert.match(r.stdout, /a#1@/);
});
