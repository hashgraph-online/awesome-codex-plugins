// Replays every corpus case from its recorded TLC output and checks that the
// pipeline reproduces the committed report, chart, and TLC output files.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { listCases, caseFiles, expectedFiles, normalizeError } from './support/corpus.mjs';
import { replayRunner, TAG_PLACEHOLDER } from '../lib/replay.mjs';
import { runPipeline } from '../lib/pipeline.mjs';
import { loadView } from '../lib/view.mjs';
import { parseMessages, trace } from '../lib/tlc-output.mjs';
import { parseState } from '../lib/values.mjs';
import { parseSanyXml } from '../lib/sany.mjs';

async function replay(c, { tag = TAG_PLACEHOLDER, runner } = {}) {
  const view = c.view ? await loadView(c.view) : null;
  const log = [];
  const run = runner ?? replayRunner(c.recordings, tag, log);
  const result = await runPipeline({ specPath: c.spec, configPath: c.config, view, run, tag });
  return { result, log };
}

for (const name of listCases()) {
  const c = caseFiles(undefined, name);
  test(`corpus ${name}: reproduces committed outputs`, async () => {
    const exp = expectedFiles(c);
    if (exp.exit === 2) {
      await assert.rejects(replay(c), (e) => normalizeError(e.message, c) === exp.error);
      return;
    }
    const { result } = await replay(c);
    assert.equal(result.exit, exp.exit);
    assert.deepEqual([...result.files.keys()].sort(), [...exp.files.keys()].sort());
    for (const [f, text] of exp.files) assert.equal(result.files.get(f), text, `${name}/${f}`);
    for (const [f, text] of result.files) assert.doesNotMatch(text, /@!@!@(START|END)MSG/, `${name}/${f} has TLC markers`);
    const named = [...result.report.matchAll(/`(tlc-[^`]+\.out)`/g)].map((m) => m[1]);
    for (const f of named) assert.ok(result.files.has(f), `${name}: report names ${f}`);
  });
}

test('a random mark tag gives the same output as the placeholder', async () => {
  const c = caseFiles(undefined, 'depths');
  const a = await replay(c);
  const b = await replay(c, { tag: 'f'.repeat(32) });
  assert.deepEqual([...a.result.files], [...b.result.files]);
});

test('shuffling DOT lines and renumbering state IDs changes nothing', async () => {
  for (const name of ['jugs', 'merge', 'player']) {
    const c = caseFiles(undefined, name);
    const base = replayRunner(c.recordings);
    let seed = 7;
    const rnd = () => { seed = (seed * 48271) % 2147483647; return seed; };
    const runner = async (req) => {
      const res = await base(req);
      if (!res.dot) return res;
      const lines = res.dot.split('\n');
      const first = lines.findIndex((l) => /^-?\d/.test(l));
      const head = lines.slice(0, first);
      const body = lines.slice(first).filter((l) => /^-?\d/.test(l));
      const tail = lines.slice(first).filter((l) => !/^-?\d/.test(l));
      const ids = new Map();
      const swap = (l) => l.replace(/^(-?\d+)( -> (-?\d+))?/, (m, a, arrow, b) => {
        for (const id of [a, b]) if (id && !ids.has(id)) ids.set(id, String(1000 + rnd() % 900000));
        return arrow ? `${ids.get(a)} -> ${ids.get(b)}` : ids.get(a);
      });
      const shuffled = body.map((l) => [rnd(), swap(l)]).sort((x, y) => x[0] - y[0]).map((x) => x[1]);
      return { ...res, dot: [...head, ...shuffled, ...tail].join('\n') };
    };
    const a = await replay(c);
    const b = await replay(c, { runner });
    assert.equal(b.result.files.get('report.md'), a.result.files.get('report.md'), name);
    assert.equal(b.result.files.get('chart.mmd'), a.result.files.get('chart.mmd'), name);
  }
});

test('the drawing run config lists the mark invariant and the budget constraint', async () => {
  const c = caseFiles(undefined, 'counter');
  const { log } = await replay(c);
  const draw = log.find((l) => l.name === 'draw');
  assert.match(draw.req.cfgText, /INVARIANT SCDraw_Counter_Mark/);
  assert.match(draw.req.cfgText, /CONSTRAINT SCDraw_Counter_Budget/);
  assert.match(draw.req.cfgText, /CHECK_DEADLOCK FALSE/);
  assert.match(draw.req.wrapper.text, /TLCGet\("distinct"\) <= 500/);
  const later = log.find((l) => l.name === 'verdict-2');
  assert.match(later.req.wrapper.text, /TLCGet\("distinct"\) < 100000/);
});

test('every invariant and deadlock bug path is a shortest path to its rule', async () => {
  for (const name of listCases()) {
    const c = caseFiles(undefined, name);
    if (expectedFiles(c).exit === 2) continue;
    const { result } = await replay(c);
    const report = result.files.get('report.md');
    for (const m of report.matchAll(/The shortest path to a state that breaks (\S+) takes (\d+) steps?\./g)) {
      // TLC's own breadth-first counterexample has the same length.
      const evidence = fs.readdirSync(c.recordings).map((f) => JSON.parse(fs.readFileSync(path.join(c.recordings, f), 'utf8')))
        .filter((r) => r.request.kind === 'tlc' && !r.request.wrapper?.name.startsWith('SCDraw'));
      const lengths = evidence.map((r) => {
        const tree = parseMessages(r.stdout);
        const first = tree.body.find((n) => typeof n === 'object' && 'code' in n && [2107, 2110, 2114].includes(n.code));
        if (!first) return null;
        const text = first.body.join('\n');
        const hit = first.code === 2114 ? ['NoDeadlock', 'CHECK_DEADLOCK'].includes(m[1]) : text.includes(`Invariant ${m[1]} is violated`);
        return hit ? trace(tree).states.length - 1 : null;
      }).filter((x) => x !== null);
      if (lengths.length && !c.spec.includes('excluded') && !c.spec.includes('Tank')) {
        assert.ok(lengths.includes(Number(m[2])), `${name}: ${m[1]} path ${m[2]} vs TLC ${lengths}`);
      }
    }
  }
});

test('in paths-only mode the view is asked once per state and step on the paths', async () => {
  const c = caseFiles(undefined, 'big');
  const calls = { state: 0, step: 0 };
  const view = {
    state: ({ x, y }) => { calls.state++; return `${x},${y}`; },
    step: (a) => { calls.step++; return a; },
    group: null, colors: new Map(), title: null,
  };
  const result = await runPipeline({ specPath: c.spec, configPath: c.config, view, run: replayRunner(c.recordings), tag: TAG_PLACEHOLDER });
  assert.match(result.files.get('report.md'), /draws only the paths to broken rules: 62 states and 61 arrows/);
  assert.deepEqual(calls, { state: 62, step: 61 });
});

test('pipeline: a hand-built run set compiles with no TLC', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'statechart-hand-'));
  fs.writeFileSync(path.join(dir, 'M.tla'), '---- MODULE M ----\n====\n');
  fs.writeFileSync(path.join(dir, 'M.cfg'), 'INIT Init\nNEXT Next\nINVARIANT NoDeadlock\nPROPERTY NoDeadlock\n');
  const rec = path.join(dir, 'rec');
  fs.mkdirSync(rec);
  const sany = '<?xml version="1.0"?><modules><RootModule>M</RootModule><context>'
    + '<entry><UID>1</UID><ModuleNode><location><column><begin>1</begin><end>1</end></column><line><begin>1</begin><end>1</end></line><filename>M</filename></location><uniquename>M</uniquename><OpDeclNodeRef><UID>2</UID></OpDeclNodeRef></ModuleNode></entry>'
    + '<entry><UID>2</UID><OpDeclNode><location><column><begin>11</begin><end>11</end></column><line><begin>2</begin><end>2</end></line><filename>M</filename></location><level>1</level><uniquename>x</uniquename><arity>0</arity><kind>3</kind></OpDeclNode></entry>'
    + '<entry><UID>3</UID><UserDefinedOpKind><location><column><begin>1</begin><end>1</end></column><line><begin>3</begin><end>3</end></line><filename>M</filename></location><level>3</level><uniquename>NoDeadlock</uniquename><arity>0</arity></UserDefinedOpKind></entry>'
    + '</context></modules>';
  const M = (code, level, ...lines) => [`@!@!@STARTMSG ${code}:${level} @!@!@`, ...lines, `@!@!@ENDMSG ${code} @!@!@`].join('\n');
  const init = M(2190, 0, 'Finished computing initial states: 1 distinct state generated at t.');
  const stats = (n) => M(2199, 0, `${n} states generated, ${n} distinct states found, 0 states left on queue.`);
  const st = (i, act, x) => M(2217, 4, `${i}: ${act}`, `x = ${x}`, '');
  const save = (name, obj) => fs.writeFileSync(path.join(rec, `${name}.json`), JSON.stringify({ request: {}, stderr: '', dot: null, ...obj }));
  save('sany', { exit: 0, stdout: sany });
  save('verdict-1', { exit: 12, stdout: [init, M(2110, 1, 'Invariant NoDeadlock is violated.'), M(2121, 1, 'The behavior up to this point is:'), st(1, '<Initial predicate>', 0), st(2, '<Inc line 1, col 1 to line 1, col 2 of module M>', 1), stats(2), ''].join('\n') });
  save('verdict-2', { exit: 11, stdout: [init, M(2114, 1, 'Deadlock reached.'), M(2121, 1, 'The behavior up to this point is:'), st(1, '<Initial predicate>', 0), st(2, '<Inc line 1, col 1 to line 1, col 2 of module M>', 1), stats(2), ''].join('\n') });
  save('verdict-3', { exit: 13, stdout: [init, M(2116, 1, 'Temporal properties were violated.'), M(2264, 1, 'The following behavior constitutes a counter-example:'), st(1, '<Initial predicate>', 0), M(2218, 4, '2: Stuttering'), stats(2), ''].join('\n') });
  save('draw', {
    exit: 0,
    stdout: [init, `<<"${TAG_PLACEHOLDER}", <<1>>, {"NoDeadlock"}>>`, stats(2), ''].join('\n'),
    dot: 'strict digraph DiskGraph {\nsubgraph cluster_graph {\n1 [label="x = 0",style = filled]\n1 -> 2 [label="Inc"];\n2 [label="x = 1"];\n}\n}\n',
  });
  const result = await runPipeline({ specPath: path.join(dir, 'M.tla'), configPath: path.join(dir, 'M.cfg'), view: null, run: replayRunner(rec), tag: TAG_PLACEHOLDER });
  const report = result.files.get('report.md');
  assert.equal(result.exit, 1);
  // An invariant and a property with one name are two rules; the deadlock rule moves to CHECK_DEADLOCK.
  assert.match(report, /## NoDeadlock breaks\n\nThe shortest path/);
  assert.match(report, /## CHECK_DEADLOCK breaks/);
  assert.match(report, /TLC's counterexample for NoDeadlock is in `tlc-NoDeadlock.out`/);
  assert.match(report, /stops in 0 forever/);
  assert.ok(result.files.has('tlc-NoDeadlock.out'));
  fs.rmSync(dir, { recursive: true });
});

test('a run without deadlock checking never shows CHECK_DEADLOCK', async () => {
  for (const name of ['depths', 'halt']) {
    const { result } = await replay(caseFiles(undefined, name));
    assert.doesNotMatch(result.files.get('report.md'), /CHECK_DEADLOCK|NoDeadlock/);
  }
});

test('SANY XML: variables in declaration order, LOCAL definitions yield to the root', () => {
  const xml = fs.readFileSync(path.join(caseFiles(undefined, 'depths').recordings, 'sany.json'), 'utf8');
  const s = parseSanyXml(JSON.parse(xml).stdout);
  assert.deepEqual(s.variables, ['a', 'b']);
  assert.equal(s.module, 'Depths');
  const c = caseFiles(undefined, 'instance');
  const inst = parseSanyXml(JSON.parse(fs.readFileSync(path.join(c.recordings, 'sany.json'), 'utf8')).stdout);
  assert.deepEqual(inst.variables, ['light']);
  const st = parseState('/\\ a = 1\n/\\ b = 2', s.variables);
  assert.equal(st.length, 2);
});
