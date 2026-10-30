import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { diagnose, format, main, TOOLS } from '../doctor.mjs';

const script = new URL('../doctor.mjs', import.meta.url).pathname;

// Fake runner: `have` maps a command name to its version output; anything else is missing.
const fakeRun = (have, authOk = true) => (argv) => {
  if (argv[0] === 'gh' && argv[1] === 'auth') return { status: authOk ? 0 : 1, out: '' };
  return argv[0] in have ? { status: 0, out: have[argv[0]] } : { status: null, out: '' };
};
const ALL = { git: 'git version 2.43.0', gh: 'gh version 2.60.1 (2024-10-01)', java: 'openjdk version "21.0.2" 2024-01-16' };

test('every tool found yields a pass with parsed versions', () => {
  const r = diagnose(fakeRun(ALL));
  assert.deepEqual(r.map((x) => [x.name, x.version, x.problem]), [
    ['node', process.versions.node, null],
    ['git', '2.43.0', null],
    ['gh', '2.60.1', null],
    ['java', '21.0.2', null],
  ]);
  const io = { text: '', out: (s) => (io.text += s), err: () => {} };
  assert.equal(main([], io, fakeRun(ALL)), 0);
  assert.match(io.text, /all required tools present/);
});

test('absent git fails and prints how to fix it', () => {
  const io = { text: '', out: (s) => (io.text += s), err: () => {} };
  const { git, ...noGit } = ALL;
  assert.equal(main([], io, fakeRun(noGit)), 1);
  assert.match(io.text, /FAIL  git \(required\): not found on PATH/);
  assert.match(io.text, /git: Install git/);
});

test('absent optional java and an unauthenticated gh produce warnings only', () => {
  const { java, ...noJava } = ALL;
  const io = { text: '', out: (s) => (io.text += s), err: () => {} };
  assert.equal(main([], io, fakeRun(noJava, false)), 0);
  assert.match(io.text, /warn  java \(optional\): not found/);
  assert.match(io.text, /warn  gh 2\.60\.1 \(recommended\): not authenticated/);
});

test('an outdated node counts as a required failure', () => {
  const node = { ...TOOLS[0], probe: () => ({ ok: true, version: '20.11.0' }) };
  const r = diagnose(fakeRun(ALL), [node]);
  assert.match(r[0].problem, /older than 22/);
  assert.match(format(r), /FAIL  node 20\.11\.0/);
});

test('--json emits machine-readable output and an unknown flag exits 2', () => {
  const io = { text: '', out: (s) => (io.text += s), err: () => {} };
  main(['--json'], io, fakeRun(ALL));
  assert.equal(JSON.parse(io.text).length, 4);
  assert.equal(main(['--frob'], { out() {}, err() {} }, fakeRun(ALL)), 2);
});

test('the CLI runs against the real PATH', () => {
  const r = spawnSync(process.execPath, [script], { encoding: 'utf8' });
  assert.ok(r.status === 0 || r.status === 1, r.stderr);
  assert.match(r.stdout, /node \d+\.\d+\.\d+ \(required\)/);
});
