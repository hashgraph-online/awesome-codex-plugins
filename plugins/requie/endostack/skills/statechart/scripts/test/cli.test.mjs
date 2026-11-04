// End-to-end tests of the launcher and supervisor. TLC output comes from the
// corpus recordings through the STATECHART_REPLAY hook, so no Java is needed.

import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { caseFiles } from './support/corpus.mjs';

const SCRIPTS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const LAUNCHER = path.join(SCRIPTS, 'statechart');

function tmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'statechart-cli-'));
}

function run(args, { env = {}, replay = 'counter', cwd } = {}) {
  const c = replay ? caseFiles(undefined, replay) : null;
  const r = spawnSync(LAUNCHER, args, {
    encoding: 'utf8',
    cwd,
    env: { ...process.env, ...(c ? { STATECHART_REPLAY: c.recordings } : {}), ...env },
  });
  return { code: r.status, out: r.stdout, err: r.stderr };
}

function copyCase(name) {
  const c = caseFiles(undefined, name);
  const dir = tmp();
  for (const f of fs.readdirSync(c.dir)) {
    if (f.endsWith('.tla') || f.endsWith('.cfg') || f === 'view.mjs') fs.copyFileSync(path.join(c.dir, f), path.join(dir, f));
  }
  return { dir, spec: path.join(dir, path.basename(c.spec)), cfg: path.join(dir, path.basename(c.config)), c };
}

function leftovers(parent) {
  return fs.readdirSync(parent).filter((n) => n.includes('.statechart-'));
}

test('writes outputs to the default folder and prints the report', () => {
  const { dir, spec, c } = copyCase('counter');
  const r = run([spec]);
  assert.equal(r.code, 1, r.err);
  const out = path.join(dir, 'Counter-chart');
  assert.deepEqual(fs.readdirSync(out).sort(), ['chart.mmd', 'report.md', 'tlc.out']);
  assert.equal(fs.readFileSync(path.join(out, 'chart.mmd'), 'utf8'), fs.readFileSync(path.join(c.expected, 'chart.mmd'), 'utf8'));
  assert.ok(r.out.startsWith('# Counter\n'));
  assert.match(r.out, /Wrote .*Counter-chart\n$/);
  assert.deepEqual(leftovers(dir), []);
});

test('an existing empty folder receives the outputs; exit 0 when every rule holds', () => {
  const { dir, spec } = copyCase('hidden-clock');
  const out = path.join(dir, 'out');
  fs.mkdirSync(out);
  const r = run([spec, '--out', out], { replay: 'hidden-clock' });
  assert.equal(r.code, 0, r.err);
  assert.ok(fs.existsSync(path.join(out, 'report.md')));
});

test('the launcher works through absolute and relative symlink chains', () => {
  const { dir, spec } = copyCase('counter');
  const links = tmp();
  fs.symlinkSync(LAUNCHER, path.join(links, 'a'));
  fs.symlinkSync('a', path.join(links, 'b'));
  fs.mkdirSync(path.join(links, 'sub'));
  fs.symlinkSync('../b', path.join(links, 'sub', 'c'));
  const r = spawnSync(path.join(links, 'sub', 'c'), [spec, '--out', path.join(dir, 'o')], { encoding: 'utf8', env: { ...process.env, STATECHART_REPLAY: caseFiles(undefined, 'counter').recordings } });
  assert.equal(r.status, 1, r.stderr);
});

test('the launcher exits 127 without a usable Node', () => {
  const bin = tmp();
  const fake = path.join(bin, 'node');
  fs.writeFileSync(fake, '#!/bin/sh\necho v20.11.0\n');
  fs.chmodSync(fake, 0o755);
  const old = spawnSync(LAUNCHER, ['x.tla'], { encoding: 'utf8', env: { ...process.env, STATECHART_NODE: fake } });
  assert.equal(old.status, 127);
  assert.match(old.stderr, /Node\.js 22 or later/);
  fs.writeFileSync(fake, '#!/bin/sh\nexit 3\n');
  const broken = spawnSync(LAUNCHER, ['x.tla'], { encoding: 'utf8', env: { ...process.env, STATECHART_NODE: fake } });
  assert.equal(broken.status, 127);
  const none = spawnSync('/bin/sh', [LAUNCHER, 'x.tla'], { encoding: 'utf8', env: { PATH: bin.replace(/$/, '-empty') } });
  assert.equal(none.status, 127);
});

test('usage errors print the usage text and exit 2', () => {
  for (const args of [[], ['a.tla', 'b.tla'], ['a.tla', '--colour', 'x'], ['a.tla', '--out']]) {
    const r = run(args, { replay: null });
    assert.equal(r.code, 2, args.join(' '));
    assert.match(r.err, /usage: statechart SPEC\.tla/);
    assert.match(r.err, /500 distinct states/);
    assert.match(r.err, /blue, orange, purple, yellow, teal, tan, pink/);
    assert.match(r.err, /Exit codes/);
  }
});

test('a missing config exits 2 and suggests --config', () => {
  const { dir, spec, cfg } = copyCase('counter');
  fs.rmSync(cfg);
  const r = run([spec]);
  assert.equal(r.code, 2);
  assert.match(r.err, /Counter\.cfg does not exist\. Pass the right file with --config/);
  assert.deepEqual(fs.readdirSync(dir).sort(), ['Counter.tla']);
});

test('output folder conflicts stop before TLC and leave contents untouched', () => {
  const { dir, spec } = copyCase('counter');
  const cases = {
    userFiles: (p) => { fs.mkdirSync(p); fs.writeFileSync(path.join(p, 'notes.txt'), 'mine'); fs.writeFileSync(path.join(p, 'a.txt'), 'x'); },
    dotfile: (p) => { fs.mkdirSync(p); fs.writeFileSync(path.join(p, '.keep'), ''); },
    regularFile: (p) => fs.writeFileSync(p, 'file'),
    brokenLink: (p) => fs.symlinkSync(path.join(dir, 'nowhere'), p),
  };
  for (const [name, make] of Object.entries(cases)) {
    const p = path.join(dir, name);
    make(p);
    const before = fs.lstatSync(p).isDirectory() ? fs.readdirSync(p).sort() : null;
    const r = run([spec, '--out', p]);
    assert.equal(r.code, 2, name);
    if (name === 'userFiles') assert.match(r.err, /already contains a\.txt/);
    if (name === 'dotfile') assert.match(r.err, /already contains \.keep/);
    if (name === 'regularFile') assert.match(r.err, /Cannot list the output folder.*ENOTDIR/);
    if (name === 'brokenLink') assert.match(r.err, /broken symbolic link/);
    if (before) assert.deepEqual(fs.readdirSync(p).sort(), before);
  }
  const first = path.join(dir, 'first');
  assert.equal(run([spec, '--out', first]).code, 1);
  const again = run([spec, '--out', first]);
  assert.equal(again.code, 2);
  assert.match(again.err, /already contains chart\.mmd/);
  assert.deepEqual(leftovers(dir), []);
});

test('config refusals stop with exit 2 and the line number', () => {
  const { spec, cfg } = copyCase('counter');
  fs.writeFileSync(cfg, 'INIT Init\nNEXT Next\nINVARIANT BelowThree, Other\n');
  const r = run([spec]);
  assert.equal(r.code, 2);
  assert.match(r.err, /TLC refuses the config .*Counter\.cfg at line 3: , is not defined/);
});

test('view errors stop before TLC with the specific message', () => {
  const { dir, spec } = copyCase('counter');
  const views = {
    'colors: { a: "breaks" }': /colors entry "a" is 'breaks'/,
    'colors: new Map()': /plain object/,
    'colors: "blue"': /plain object/,
    'title: 7': /title export must be a string/,
  };
  let i = 0;
  for (const [body, re] of Object.entries(views)) {
    const f = path.join(dir, `v${i++}.mjs`);
    const [k, ...v] = body.split(': ');
    fs.writeFileSync(f, `export const ${k} = ${v.join(': ')};\n`);
    const r = run([spec, '--view', f, '--out', path.join(dir, `o${i}`)], { replay: null, env: { STATECHART_REPLAY: '/nonexistent' } });
    assert.equal(r.code, 2, body);
    assert.match(r.err, re);
  }
  const g = path.join(dir, 'g.mjs');
  fs.writeFileSync(g, 'export const group = () => "a";\n');
  assert.match(run([spec, '--view', g, '--out', path.join(dir, 'og')], { env: { STATECHART_REPLAY: '/nonexistent' } }).err, /needs a colors export/);
  const d = path.join(dir, 'd.mjs');
  fs.writeFileSync(d, 'export default {};\n');
  assert.match(run([spec, '--view', d, '--out', path.join(dir, 'od')], { env: { STATECHART_REPLAY: '/nonexistent' } }).err, /default are not recognized/);
  const t = path.join(dir, 't.mjs');
  fs.writeFileSync(t, 'throw { message: "view refused to load" };\n');
  const tr = run([spec, '--view', t, '--out', path.join(dir, 'ot')]);
  assert.equal(tr.code, 2);
  assert.equal(tr.err, 'statechart: view refused to load\n');
});

test('view errors during drawing exit 2 and write nothing', () => {
  const { dir, spec } = copyCase('counter');
  const cases = {
    'export const state = () => 3;': /returned 3/,
    'export const state = (v) => v.nope.x;': /state function threw/,
    'export const step = () => "";': /step function returned ''/,
    'export const step = (a) => (a === "Up" ? null : a);': /on the path to the BelowThree bug/,
    'export const group = () => "x"; export const colors = { y: "blue" };': /'x'.*not a key of colors/,
  };
  let i = 0;
  for (const [src, re] of Object.entries(cases)) {
    const f = path.join(dir, `v${i}.mjs`);
    fs.writeFileSync(f, src);
    const out = path.join(dir, `o${i++}`);
    const r = run([spec, '--view', f, '--out', out]);
    assert.equal(r.code, 2, src);
    assert.match(r.err, re);
    assert.equal(fs.existsSync(out), false);
  }
  assert.deepEqual(leftovers(dir), []);
});

test('a hidden step is not drawn and is counted', () => {
  const { dir, spec } = copyCase('counter');
  const f = path.join(dir, 'v.mjs');
  fs.writeFileSync(f, 'export const step = (a, from) => (a === "Reset" && from.n === 1 ? null : a);\n');
  const r = run([spec, '--view', f, '--out', path.join(dir, 'o')]);
  assert.equal(r.code, 1, r.err);
  assert.match(r.out, /The view hides 1 step\./);
});

function startSlow(spec, out, extraEnv = {}) {
  const child = spawn(LAUNCHER, [spec, '--out', out], {
    env: { ...process.env, STATECHART_REPLAY: caseFiles(undefined, 'counter').recordings, STATECHART_REPLAY_DELAY_MS: '3000', ...extraEnv },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let err = '';
  child.stderr.on('data', (d) => { err += d; });
  return { child, err: () => err };
}

function waitExit(child) {
  return new Promise((resolve) => child.on('exit', (code, signal) => resolve({ code, signal })));
}

async function waitFor(pred, ms = 5000) {
  const t0 = Date.now();
  while (!pred()) {
    if (Date.now() - t0 > ms) throw new Error('timed out');
    await new Promise((r) => setTimeout(r, 50));
  }
}

function workerPids() {
  const r = spawnSync('pgrep', ['-f', 'statechart.mjs --worker'], { encoding: 'utf8' });
  return r.stdout.split('\n').filter(Boolean).map(Number);
}

for (const sig of ['SIGINT', 'SIGTERM']) {
  test(`${sig} stops the check, writes nothing, and exits ${sig === 'SIGINT' ? 130 : 143}`, async () => {
    const { dir, spec } = copyCase('counter');
    const out = path.join(dir, 'o');
    const { child, err } = startSlow(spec, out);
    await waitFor(() => leftovers(dir).length > 0);
    await new Promise((r) => setTimeout(r, 300));
    child.kill(sig);
    const { code } = await waitExit(child);
    assert.equal(code, sig === 'SIGINT' ? 130 : 143);
    assert.match(err(), new RegExp(`stopped by ${sig}; nothing was written`));
    assert.equal(fs.existsSync(out), false);
    await waitFor(() => leftovers(dir).length === 0);
  });
}

test('SIGKILL of the command kills the worker and removes temp folders', async () => {
  const { dir, spec } = copyCase('counter');
  const out = path.join(dir, 'o');
  const before = new Set(workerPids());
  const { child } = startSlow(spec, out);
  await waitFor(() => leftovers(dir).length > 0);
  await waitFor(() => workerPids().some((p) => !before.has(p)));
  child.kill('SIGKILL');
  await waitExit(child);
  await waitFor(() => leftovers(dir).length === 0);
  await waitFor(() => workerPids().every((p) => before.has(p)));
  assert.equal(fs.existsSync(out), false);
});

test('a signal that kills the worker gives exit 2 and one line', async () => {
  const { dir, spec } = copyCase('counter');
  const out = path.join(dir, 'o');
  const before = new Set(workerPids());
  const { child, err } = startSlow(spec, out);
  await waitFor(() => workerPids().some((p) => !before.has(p)));
  for (const p of workerPids()) if (!before.has(p)) process.kill(p, 'SIGKILL');
  const { code } = await waitExit(child);
  assert.equal(code, 2);
  assert.match(err(), /killed by SIGKILL; nothing was written/);
  assert.equal(fs.existsSync(out), false);
  await waitFor(() => leftovers(dir).length === 0);
});

test('a file appearing in the output folder during the run is kept; exit 2', async () => {
  const { dir, spec } = copyCase('counter');
  const out = path.join(dir, 'o');
  fs.mkdirSync(out);
  const { child, err } = startSlow(spec, out, { STATECHART_REPLAY_DELAY_MS: '600' });
  await waitFor(() => leftovers(dir).length > 0);
  fs.writeFileSync(path.join(out, 'late.txt'), 'arrived');
  const { code } = await waitExit(child);
  assert.equal(code, 2);
  assert.match(err(), /gained late\.txt during the run/);
  assert.deepEqual(fs.readdirSync(out), ['late.txt']);
  await waitFor(() => leftovers(dir).length === 0);
});

test('java that cannot start exits 2', () => {
  const { dir, spec } = copyCase('counter');
  const r = spawnSync(LAUNCHER, [spec, '--out', path.join(dir, 'o')], {
    encoding: 'utf8',
    env: { ...process.env, STATECHART_REPLAY: '', JAVA: path.join(dir, 'no-java-here'), TLA2TOOLS: path.join(dir, 'x.jar') },
  });
  assert.equal(r.status, 2);
  assert.match(r.stderr, /Cannot run Java/);
});
