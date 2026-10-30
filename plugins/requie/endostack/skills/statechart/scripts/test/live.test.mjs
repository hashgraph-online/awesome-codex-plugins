// Tests against a real TLC. They run only when TLA2TOOLS points at a jar and
// Java starts; otherwise each test is skipped with a reason.

import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { listCases, caseFiles, expectedFiles, normalizeError } from './support/corpus.mjs';
import { liveRunner, javaMajor } from '../lib/toolchain.mjs';
import { runPipeline } from '../lib/pipeline.mjs';
import { loadView } from '../lib/view.mjs';
import { parseConfig } from '../lib/config.mjs';

const LAUNCHER = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'statechart');
const jar = process.env.TLA2TOOLS;
const java = process.env.JAVA || 'java';
const skip = !jar ? 'TLA2TOOLS is not set'
  : !fs.existsSync(jar) ? `TLA2TOOLS points at a missing file ${jar}`
    : javaMajor(java) === null ? `cannot run ${java}` : false;

function workDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'statechart-live-'));
}

async function live(specPath, configPath, view = null) {
  const dir = workDir();
  try {
    return await runPipeline({ specPath, configPath, view, run: liveRunner({ java, jar, workDir: dir }) });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

const NORMALIZE = [
  [/seed -?\d+/g, 'seed N'], [/pid: \d+/g, 'pid: N'], [/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/g, 'TS'],
  [/\([\d,]+ d?s\/min\)/g, '(R)'], [/Finished in [^\n]* at/g, 'Finished in D at'], [/\d+MB heap/g, 'NMB heap'],
  [/val = [\d.E-]+/g, 'val = V'], [/Parsing file [^\n]*\/(\w+\.tla)/g, 'Parsing file $1'], [/on \d+ cores/g, 'on N cores'],
  [/Finished checking temporal properties in [^\n]*/g, 'Finished checking temporal properties'],
  [/\d+MB offheap memory \[pid: N\] \([^)\n]*\)/g, 'NMB offheap memory [pid: N] (HOST)'],
];
const norm = (s) => NORMALIZE.reduce((t, [re, to]) => t.replace(re, to), s);

for (const name of listCases()) {
  test(`live ${name}: reproduces committed outputs`, { skip }, async () => {
    const c = caseFiles(undefined, name);
    const exp = expectedFiles(c);
    const view = c.view ? await loadView(c.view) : null;
    if (exp.exit === 2) {
      await assert.rejects(live(c.spec, c.config, view), (e) => normalizeError(e.message, c) === exp.error);
      return;
    }
    const result = await live(c.spec, c.config, view);
    assert.equal(result.exit, exp.exit);
    assert.deepEqual([...result.files.keys()].sort(), [...exp.files.keys()].sort());
    for (const f of ['report.md', 'chart.mmd']) if (exp.files.has(f)) assert.equal(result.files.get(f), exp.files.get(f), `${name}/${f}`);
    for (const [f, text] of exp.files) if (f.endsWith('.out')) assert.equal(norm(result.files.get(f)), norm(text), `${name}/${f}`);
  });
}

test('tlc.out equals plain TLC output on the config as written', { skip }, async () => {
  for (const name of ['light', 'past', 'partial', 'player', 'depths']) {
    const c = caseFiles(undefined, name);
    const result = await live(c.spec, c.config, c.view ? await loadView(c.view) : null);
    const cfgFile = path.join(path.dirname(c.spec), `__plain_${process.pid}.cfg`);
    const cfg = parseConfig(fs.readFileSync(c.config, 'utf8'));
    const lines = [cfg.written];
    if (cfg.invariants.length) lines.push(`INVARIANT ${cfg.invariants.join(' ')}`);
    if (cfg.properties.length) lines.push(`PROPERTY ${cfg.properties.join(' ')}`);
    lines.push(`CHECK_DEADLOCK ${cfg.checkDeadlock ? 'TRUE' : 'FALSE'}`);
    fs.writeFileSync(cfgFile, `${lines.join('\n')}\n`);
    const meta = workDir();
    try {
      const r = spawnSync(java, ['-XX:+UseParallelGC', `-DTLA-Library=${path.dirname(c.spec)}`, '-cp', jar, 'tlc2.TLC', '-workers', '1', '-fp', '0', '-lncheck', 'final', '-metadir', meta, '-config', path.basename(cfgFile), path.basename(c.spec)], { cwd: path.dirname(c.spec), encoding: 'utf8', env: { ...process.env, JAVA_TOOL_OPTIONS: '' } });
      const plain = r.stdout.split('\n').filter((l) => !l.startsWith('Picked up JAVA_TOOL_OPTIONS')).join('\n');
      assert.equal(norm(result.files.get('tlc.out')), norm(plain), name);
    } finally {
      fs.rmSync(cfgFile, { force: true });
      fs.rmSync(meta, { recursive: true, force: true });
    }
  }
});

function specIn(dir, name, body, cfg) {
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, `${name}.tla`), `---- MODULE ${name} ----\n${body}\n====\n`);
  fs.writeFileSync(path.join(dir, `${name}.cfg`), cfg);
  return [path.join(dir, `${name}.tla`), path.join(dir, `${name}.cfg`)];
}

test('chart budget edges: 500 states draw everything, 501 write no chart', { skip }, async () => {
  const dir = workDir();
  const body = (n) => `EXTENDS Naturals\nVARIABLES x\nInit == x = 0\nNext == x < ${n - 1} /\\ x' = x + 1\nOk == TRUE`;
  const [s500, c500] = specIn(path.join(dir, 'a'), 'Line', body(500), 'INIT Init\nNEXT Next\nINVARIANT Ok\nCHECK_DEADLOCK FALSE\n');
  const r500 = await live(s500, c500);
  assert.match(r500.report, /TLC reached 500 states and 499 steps\. The chart draws 500 states/);
  const [s501, c501] = specIn(path.join(dir, 'b'), 'Line', body(501), 'INIT Init\nNEXT Next\nINVARIANT Ok\nCHECK_DEADLOCK FALSE\n');
  const r501 = await live(s501, c501);
  assert.match(r501.report, /TLC reached 501 distinct states, over the chart budget of 500\. Nothing broke, so no chart was written\./);
  assert.equal(r501.files.has('chart.mmd'), false);
  fs.rmSync(dir, { recursive: true });
});

test('a spec in a non-ASCII folder works', { skip }, async () => {
  const dir = path.join(workDir(), 'mödel-ç');
  const [s, c] = specIn(dir, 'Uni', 'VARIABLES x\nInit == x = "é"\nNext == x\' = x\nOk == x = "é"', 'INIT Init\nNEXT Next\nINVARIANT Ok\n');
  const r = await live(s, c);
  assert.equal(r.exit, 0);
  assert.match(r.files.get('chart.mmd'), /#34;#233;#34;/);
});

test('an invariant named NoDeadlock and a real deadlock break as two rules', { skip }, async () => {
  const c = caseFiles(undefined, 'nodeadlock-name');
  const r = await live(c.spec, c.config);
  assert.match(r.report, /## NoDeadlock breaks[\s\S]*## CHECK_DEADLOCK breaks/);
});

test('initial-only notes: substituted and extended-module properties, LOCAL shadowing', { skip }, async () => {
  const dir = workDir();
  fs.writeFileSync(path.join(dir, 'Base.tla'), '---- MODULE Base ----\nVARIABLES x\nInBase == x = 0\nLOCAL Shadow == [](x = 0)\n====\n');
  const [s, c] = specIn(dir, 'Top', 'EXTENDS Base\nInit == x = 0\nNext == UNCHANGED x\nSpec == Init /\\ [][Next]_x\nReal == [](x = 0)\nStatePred == x = 0\nShadow == x = 0', 'SPECIFICATION Spec\nCONSTANT Real <- StatePred\nPROPERTIES InBase Real Shadow\n');
  const r = await live(s, c);
  assert.equal(r.exit, 0);
  for (const n of ['InBase', 'Real', 'Shadow']) assert.match(r.report, new RegExp(`TLC checked ${n} only in initial states`));
  fs.rmSync(dir, { recursive: true });
});

test('the CLI runs end to end against real TLC', { skip }, () => {
  const c = caseFiles(undefined, 'jugs');
  const dir = workDir();
  fs.copyFileSync(c.spec, path.join(dir, 'Jugs.tla'));
  fs.copyFileSync(c.config, path.join(dir, 'Jugs.cfg'));
  const r = spawnSync(LAUNCHER, [path.join(dir, 'Jugs.tla')], { encoding: 'utf8', env: { ...process.env, STATECHART_REPLAY: '' } });
  assert.equal(r.status, 1, r.stderr);
  assert.equal(fs.readFileSync(path.join(dir, 'Jugs-chart', 'report.md'), 'utf8'), fs.readFileSync(path.join(c.expected, 'report.md'), 'utf8'));
  fs.rmSync(dir, { recursive: true });
});
