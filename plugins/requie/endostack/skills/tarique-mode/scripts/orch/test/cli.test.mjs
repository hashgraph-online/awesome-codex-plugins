import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as path from 'node:path';
import * as cp from 'node:child_process';
import { cli, tmpdir } from './helpers.mjs';

const launcher = new URL('../orch', import.meta.url).pathname;

async function initStore() {
  const store = path.join(tmpdir(), 'store');
  const env = { ORCH_STORE: store };
  const r = await cli(['init'], { env });
  assert.equal(r.code, 0, r.stderr);
  assert.equal(r.stdout.trim(), `initialized ${store}`);
  return { store, env };
}

test('--help prints the command list and exits 0', async () => {
  const r = await cli(['--help']);
  assert.equal(r.code, 0);
  for (const c of ['init', 'unit add', 'ledger record', 'inbox drain', 'gate park', 'frontier set', 'status', 'standing add']) assert.ok(r.stdout.includes(c), c);
});

test('frontier set --help documents --repo and --prs', async () => {
  const r = await cli(['frontier', 'set', '--help']);
  assert.equal(r.code, 0);
  assert.match(r.stdout, /--repo <dir>/);
  assert.match(r.stdout, /--prs <n,\.\.\.>/);
});

test('an absent store exits 1 with a hint, and a blank value counts as absent', async () => {
  for (const env of [{}, { ORCH_STORE: '   ' }]) {
    const r = await cli(['unit', 'list'], { env });
    assert.equal(r.code, 1);
    assert.match(r.stderr, /error: set --store or ORCH_STORE/);
  }
});

test('a command group without a subcommand is a usage error once the store is checked', async () => {
  assert.match((await cli(['unit'])).stderr, /set --store or ORCH_STORE/);
  const r = await cli(['unit'], { env: { ORCH_STORE: '/tmp/x' } });
  assert.equal(r.code, 1);
  assert.match(r.stderr, /'unit' needs a subcommand/);
});

test('an absent required option exits 1 and names the option', async () => {
  const { env } = await initStore();
  const r = await cli(['unit', 'add', 'u1'], { env });
  assert.equal(r.code, 1);
  assert.match(r.stderr, /'unit add' requires --track/);
  assert.match(r.stderr, /usage: orch/);
});

test('an unsupported option, a stray positional, or an unknown command is a usage error', async () => {
  const { env } = await initStore();
  assert.match((await cli(['unit', 'get', 'x', '--track', 't'], { env })).stderr, /does not take --track/);
  assert.match((await cli(['unit', 'get', 'x', 'y'], { env })).stderr, /unexpected argument 'y'/);
  assert.match((await cli(['unit', 'nuke'], { env })).stderr, /unknown command 'unit nuke'/);
  assert.match((await cli(['--bogus', 'init'], { env })).stderr, /error: Unknown option '--bogus'/);
});

test('--store behaves like ORCH_STORE and --json prints the whole row', async () => {
  const store = path.join(tmpdir(), 'store');
  assert.equal((await cli(['--store', store, 'init'])).code, 0);
  const add = await cli(['--store', store, '--json', 'unit', 'add', 'u1', '--track', 'api', '--brief', 'b.md']);
  assert.equal(add.code, 0);
  assert.equal(add.stdout, JSON.stringify({ name: 'u1', track: 'api', stage: 'pending', pr: '', branch: '', head: '', brief: 'b.md' }, null, 2) + '\n');
  const get = await cli(['--json', 'unit', 'get', 'u1'], { env: { ORCH_STORE: store } });
  assert.equal(JSON.parse(get.stdout).track, 'api');
});

test('a blank unit name exits 1', async () => {
  const { env } = await initStore();
  const r = await cli(['unit', 'add', '', '--track', 't'], { env });
  assert.equal(r.code, 1);
  assert.match(r.stderr, /unit name cannot be blank/);
});

test('an unknown unit exits 2 and reports on stderr', async () => {
  const { env } = await initStore();
  const r = await cli(['unit', 'get', 'ghost'], { env });
  assert.equal(r.code, 2);
  assert.equal(r.stdout, '');
  assert.match(r.stderr, /unit 'ghost' not found/);
  assert.equal((await cli(['gate', 'resolve', 'ghost', '--answer', 'x'], { env })).code, 2);
});

test('an absent ledger row exits 2, prints NO-VERDICT on stdout, and leaves stderr empty', async () => {
  const { env } = await initStore();
  const plain = await cli(['ledger', 'check', '7', 'abc'], { env });
  assert.equal(plain.code, 2);
  assert.equal(plain.stdout, 'NO-VERDICT\n');
  assert.equal(plain.stderr, '');
  const json = await cli(['--json', 'ledger', 'check', '7', 'abc'], { env });
  assert.equal(json.code, 2);
  assert.deepEqual(JSON.parse(json.stdout), { pr: 7, head: 'abc', verdict: 'NO-VERDICT' });
  assert.equal(json.stderr, '');
});

test('PR numbers have to be positive safe integers', async () => {
  const { env } = await initStore();
  for (const bad of ['0', '-1', '01', '1.5', '99999999999999999999']) {
    const r = await cli(['ledger', 'check', bad, 'abc'], { env });
    assert.equal(r.code, 1, bad);
  }
  assert.equal((await cli(['unit', 'add', 'u', '--track', 't'], { env })).code, 0);
  assert.equal((await cli(['unit', 'set', 'u', '--stage', 's', '--pr', 'x'], { env })).code, 1);
});

test('an end-to-end session driven through the CLI', async () => {
  const { env } = await initStore();
  for (let i = 1; i <= 6; i++) await cli(['unit', 'add', `u${i}`, '--track', i % 2 ? 'api' : 'web'], { env });
  await cli(['unit', 'set', 'u1', '--stage', 'merged', '--pr', '10', '--branch', 'b1', '--head', 'abc'], { env });
  const list = await cli(['unit', 'list'], { env });
  const lines = list.stdout.trimEnd().split('\n');
  assert.equal(lines.length, 5);
  assert.equal(lines[4], '2 more; use --json');
  assert.equal(JSON.parse((await cli(['--json', 'unit', 'list'], { env })).stdout).length, 6);
  assert.equal((await cli(['unit', 'list', '--stage', 'nope'], { env })).stdout, 'no units\n');
  assert.equal((await cli(['unit', 'counts'], { env })).stdout, 'merged=1, pending=5\n');

  assert.equal((await cli(['ledger', 'record', '10', 'abc', 'tests-proven', '--evidence', 'e.txt'], { env })).stdout, '10\tabc\ttests-proven\n');
  assert.equal((await cli(['ledger', 'check', '10', 'abc'], { env })).stdout, 'tests-proven\n');
  assert.equal((await cli(['ledger', 'summary'], { env })).stdout, 'tests-proven=1\n');
  assert.match((await cli(['ledger', 'record', '10', 'abc', 'great', '--evidence', 'e'], { env })).stderr, /verdict must be one of/);

  const push = await cli(['inbox', 'push', 'owner-a', 'u1', 'done', '--report', 'r.md'], { env });
  assert.match(push.stdout, /^u1\tdone\t.+\.tsv\n$/);
  assert.equal((await cli(['inbox', 'count'], { env })).stdout, '1\n');
  assert.deepEqual(JSON.parse((await cli(['--json', 'inbox', 'count'], { env })).stdout), { count: 1 });
  assert.match((await cli(['inbox', 'drain', '--peek'], { env })).stdout, /\towner-a\tu1\tdone\tr\.md\n$/);
  assert.match((await cli(['inbox', 'drain'], { env })).stdout, /owner-a/);
  assert.equal((await cli(['inbox', 'drain'], { env })).stdout, '(empty)\n');

  assert.equal((await cli(['gate', 'park', 'g1', '--question', 'Ship?', '--options', 'yes,no', '--default', 'no'], { env })).stdout, 'parked g1\n');
  assert.equal((await cli(['gate', 'list'], { env })).stdout, 'g1\tShip?\tyes,no\tno\n');

  assert.equal((await cli(['standing', 'add', 'Keep PRs under 400 lines'], { env })).stdout, '1. Keep PRs under 400 lines\n');
  assert.equal((await cli(['standing', 'show'], { env })).stdout, '1. Keep PRs under 400 lines\n');

  const status = await cli(['status'], { env });
  assert.equal(status.code, 0);
  assert.deepEqual(status.stdout.trimEnd().split('\n'), [
    'units=6 (merged=1, pending=5) ledger=tests-proven=1',
    'changed: first render',
    'open gates=1: g1',
  ]);
  await cli(['gate', 'resolve', 'g1', '--answer', 'yes'], { env });
  const s2 = await cli(['status'], { env });
  assert.match(s2.stdout, /changed: open gates 1->0/);
  assert.match(s2.stdout, /open gates=0\n$/);
});

test('status shows up to four open gate ids followed by +N more', async () => {
  const { env } = await initStore();
  for (const id of ['e', 'a', 'd', 'b', 'c', 'f']) await cli(['gate', 'park', id, '--question', 'q', '--options', 'o', '--default', 'd'], { env });
  const r = await cli(['status'], { env });
  assert.match(r.stdout, /open gates=6: a, b, c, d \+2 more/);
});

test('the POSIX launcher starts the CLI', () => {
  const store = path.join(tmpdir(), 'store');
  const r = cp.spawnSync(launcher, ['--store', store, 'init'], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^initialized /);
  const nf = cp.spawnSync(launcher, ['--store', store, 'ledger', 'check', '1', 'x'], { encoding: 'utf8' });
  assert.equal(nf.status, 2);
  assert.equal(nf.stdout, 'NO-VERDICT\n');
});
