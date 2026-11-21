import test from 'node:test';
import assert from 'node:assert/strict';
import { buildChart, condition } from '../lib/chart.mjs';
import { applyView, checkView } from '../lib/view.mjs';
import { renderMermaid, encodeLabel, encodeTitle } from '../lib/mermaid.mjs';
import { parseValue, toView, stateKey } from '../lib/values.mjs';
import { findBugs } from '../lib/graph.mjs';

// Build a graph from states given as {a: 'x', b: 'y'} string records.
function graphOf(vars, stateList, edges, { initial = [0], breaks = {} } = {}) {
  const states = stateList.map((rec, i) => {
    const vals = vars.map((v) => parseValue(JSON.stringify(rec[v])));
    return { index: i, vals, key: stateKey(vals), initial: initial.includes(i), kind: 'normal', breaks: new Set(breaks[i] ?? []), label0: JSON.stringify(rec) };
  });
  return { variables: vars, states, edges: edges.map(([from, to, action]) => ({ from, to, action })), lassos: new Map(), ruleEnd: new Map(), stateCount: states.length, stepCount: edges.length };
}

function chartFor(graph, view, rules = [], verdicts = new Map()) {
  const v = checkView(view);
  const applied = applyView(v, graph.variables, graph.states, graph.edges, toView, (s) => s.label0);
  const { bugs } = findBugs(graph, rules, verdicts);
  const chart = buildChart({ graph, applied, bugs, rules, verdicts });
  return { chart, bugs, mmd: renderMermaid(chart, { title: v.title, colors: v.colors, ruleName: (id) => rules.find((r) => r.id === id).display }) };
}

const regionsView = { state: ({ a, b }) => ({ A: a, B: b }), step: (act) => act };

test('regions: different start combinations refuse regions', () => {
  const g = graphOf(['a', 'b'], [{ a: 'x', b: 'p' }, { a: 'y', b: 'q' }], [], { initial: [0, 1] });
  const { chart } = chartFor(g, regionsView);
  assert.equal(chart.mode, 'nested');
  assert.match(chart.notes.regionsReason, /start in A x, B q|start in A y, B p/);
});

test('regions: a move that depends on two other regions together refuses regions', () => {
  // b and c toggle freely; a moves only when b equals c (exclusive-or of b and c blocks it).
  const s = [];
  const idx = new Map();
  for (const a of ['0', '1']) for (const b of ['0', '1']) for (const c of ['0', '1']) { idx.set(a + b + c, s.length); s.push({ a, b, c }); }
  const e = [];
  for (const [k, i] of idx) {
    const [a, b, c] = k;
    e.push([i, idx.get(a + (b === '0' ? '1' : '0') + c), 'B']);
    e.push([i, idx.get(a + b + (c === '0' ? '1' : '0')), 'C']);
    if (a === '0' && b === c) e.push([i, idx.get(`1${b}${c}`), 'A']);
  }
  const g = graphOf(['a', 'b', 'c'], s, e);
  const { chart } = chartFor(g, { state: ({ a, b, c }) => ({ A: a, B: b, C: c }), step: (x) => x });
  assert.equal(chart.mode, 'nested');
  assert.match(chart.notes.regionsReason, /no single condition/);
});

test('regions: a forked shared step names the invented move', () => {
  const g = graphOf(['a', 'b'], [{ a: '0', b: '0' }, { a: '1', b: '1' }, { a: '1', b: '0' }],
    [[0, 1, 'Go'], [0, 2, 'Go']]);
  const { chart } = chartFor(g, regionsView);
  assert.equal(chart.mode, 'nested');
  assert.match(chart.notes.regionsReason, /"Go"/);
});

test('regions: a partial set of start combinations refuses regions', () => {
  const g = graphOf(['a', 'b'], [{ a: '0', b: '0' }, { a: '0', b: '1' }, { a: '1', b: '0' }], [], { initial: [0, 1, 2] });
  const { chart } = chartFor(g, regionsView);
  assert.equal(chart.mode, 'nested');
  assert.match(chart.notes.regionsReason, /A 1, B 1/);
});

test('regions: lockstep moves are accepted with a step note', () => {
  const g = graphOf(['a', 'b'], [{ a: '0', b: '0' }, { a: '1', b: '1' }], [[0, 1, 'Both'], [1, 0, 'Back']]);
  const { chart, mmd } = chartFor(g, regionsView);
  assert.equal(chart.mode, 'regions');
  assert.equal(chart.notes.stepNotes.length, 2);
  assert.match(mmd, /--\n/);
});

test('regions: fully interleaved moves are accepted', () => {
  const s = [{ a: '0', b: '0' }, { a: '1', b: '0' }, { a: '0', b: '1' }, { a: '1', b: '1' }];
  const g = graphOf(['a', 'b'], s, [[0, 1, 'A'], [2, 3, 'A'], [0, 2, 'B'], [1, 3, 'B']]);
  const { chart } = chartFor(g, regionsView);
  assert.equal(chart.mode, 'regions');
  assert.equal(chart.arrowCount, 2);
});

test('regions: conditions on the other region are phrased with its labels', () => {
  const s = [{ a: 'out', b: 'on' }, { a: 'in', b: 'on' }, { a: 'out', b: 'off' }, { a: 'in', b: 'off' }];
  const g = graphOf(['a', 'b'], s, [[0, 1, 'SignIn'], [1, 0, 'SignOut'], [3, 2, 'SignOut'], [0, 2, 'Drop'], [1, 3, 'Drop'], [2, 0, 'Up'], [3, 1, 'Up']]);
  const { mmd } = chartFor(g, regionsView);
  assert.match(mmd, /SignIn #91;when on#93;/);
});

test('condition(): and, or, and tuple cases', () => {
  const others = [
    { region: 'X', leaves: ['x1', 'x2'], names: new Map([['x1', 'p'], ['x2', 'q']]) },
    { region: 'Y', leaves: ['y1', 'y2'], names: new Map([['y1', 'r'], ['y2', 's']]) },
  ];
  const ctx = (...l) => new Set(l.map((c) => JSON.stringify(c)));
  assert.equal(condition(ctx(['x1', 'y1'], ['x1', 'y2']), others).phrase, 'X is p');
  assert.equal(condition(ctx(['x1', 'y1'], ['x1', 'y2'], ['x2', 'y1']), others).kind, 'or');
  assert.equal(condition(ctx(['x1', 'y1'], ['x2', 'y2']), others).kind, 'tuple');
  assert.equal(condition(ctx(['x1', 'y1'], ['x1', 'y2'], ['x2', 'y1'], ['x2', 'y2']), others).kind, 'none');
});

test('region marking: a combination that breaks marks states that each work elsewhere', () => {
  const s = [{ a: '0', b: '0' }, { a: '1', b: '0' }, { a: '0', b: '1' }, { a: '1', b: '1' }];
  const g = graphOf(['a', 'b'], s, [[0, 1, 'A'], [2, 3, 'A'], [0, 2, 'B'], [1, 3, 'B']], { breaks: { 3: ['r'] } });
  const rules = [{ id: 'r', kind: 'invariant', display: 'R' }];
  const { chart } = chartFor(g, regionsView, rules, new Map([['r', { status: 'broken' }]]));
  const marked = [...chart.trees.values()].flatMap((t) => [...t.nodes.values()]).filter((n) => n.mark).map((n) => `${n.region}:${n.name}`).sort();
  assert.deepEqual(marked, ['A:1', 'B:1']);
});

test('lifting: a step leaving every child the same way becomes one arrow from the parent', () => {
  const s = [{ a: 'p1' }, { a: 'p2' }, { a: 'out' }];
  const g = graphOf(['a'], s, [[0, 1, 'next'], [0, 2, 'leave'], [1, 2, 'leave'], [2, 0, 'enter']]);
  const { chart, mmd } = chartFor(g, { state: ({ a }) => (a === 'out' ? 'Out' : ['Phase', a]) });
  assert.equal(chart.arrowCount, 3);
  assert.match(mmd, /state "Phase" as (s\d+) \{[\s\S]*\1 --> s\d+: leave/);
});

test('a bug-path self-step is a loop only in a flat chart', () => {
  const s = [{ a: 'x', n: 0 }, { a: 'x', n: 1 }];
  const mk = () => graphOf(['a', 'n'], s, [[0, 1, 'Tick']], { breaks: { 1: ['r'] } });
  const rules = [{ id: 'r', kind: 'invariant', display: 'R' }];
  const verdicts = new Map([['r', { status: 'broken' }]]);
  const flat = chartFor(mk(), { state: ({ a }) => a }, rules, verdicts);
  assert.equal(flat.chart.arrowCount, 1);
  const nested = chartFor(mk(), { state: ({ a }) => ['P', a] }, rules, verdicts);
  assert.equal(nested.chart.arrowCount, 0);
  assert.equal(nested.chart.notes.inside, 1);
});

test('a leaf that is also a parent is refused', () => {
  const g = graphOf(['a'], [{ a: '1' }, { a: '2' }], [[0, 1, 'x']]);
  assert.throws(() => chartFor(g, { state: ({ a }) => (a === '1' ? ['P'] : ['P', 'child']) }), /both as a state and as the parent/);
});

test('hiding a bug-path step is refused; hiding others is counted', () => {
  const g = graphOf(['a'], [{ a: '0' }, { a: '1' }, { a: '2' }], [[0, 1, 'A'], [0, 2, 'B']], { breaks: { 1: ['r'] } });
  const rules = [{ id: 'r', kind: 'invariant', display: 'R' }];
  const verdicts = new Map([['r', { status: 'broken' }]]);
  assert.throws(() => chartFor(g, { step: (a) => (a === 'A' ? null : a) }, rules, verdicts), /on the path to the R bug/);
  const ok = chartFor(g, { step: (a) => (a === 'B' ? null : a) }, rules, verdicts);
  assert.equal(ok.chart.notes.hidden, 1);
});

test('mixed groups get no color; a themed group appears in the legend', () => {
  const g = graphOf(['a'], [{ a: '0' }, { a: '1' }, { a: '2' }], [[0, 1, 'A'], [1, 2, 'A']]);
  const { mmd } = chartFor(g, { state: ({ a }) => (a === '0' ? 'zero' : 'more'), group: ({ a }) => (a === '2' ? 'two' : 'low'), colors: { low: 'blue', two: 'pink', undefined: 'tan' } });
  assert.match(mmd, /legend0: low/);
  assert.match(mmd, /class s0 blue/);
  assert.doesNotMatch(mmd, /pink|tan/);
});

test('mermaid: only syntax characters are coded, and hazards are neutralised', () => {
  assert.equal(encodeLabel('Sign in, then wait (2 s)'), 'Sign in, then wait (2 s)');
  assert.equal(encodeLabel('a:b'), 'a#58;b');
  assert.doesNotMatch(encodeLabel('%%{init}%%'), /%%/);
  assert.equal(encodeLabel('line\nbreak x'), 'line break x');
  assert.equal(encodeLabel('   '), '#32;');
  assert.equal(encodeLabel('a\u0000b\u0085c'), 'abc');
  assert.equal(encodeLabel('x\ud800y'), 'x#65533;y');
  assert.match(encodeLabel('[[fork]]'), /^#91;#91;fork#93;#93;$/);
  assert.match(encodeLabel('direction LR'), /direction#32;LR/);
  assert.match(encodeLabel('C4Context'), /^#67;4Context$/);
  assert.match(encodeLabel('marker-end="x"'), /marker-end⁠#61;|marker-end⁠/);
  assert.match(encodeLabel('#35;'), /#35;⁠/);
  assert.match(encodeLabel('<script>'), /^#60;script#62;$/);
  assert.equal(encodeLabel('_x_'), '#95;x#95;');
  assert.equal(encodeLabel('a_b'), 'a_b');
  assert.equal(encodeTitle('A <b> "c"'), 'A &lt;b> \\"c\\"');
});

test('performance: a 10,000-state graph with no view draws in seconds', () => {
  const n = 10000;
  const states = [];
  for (let i = 0; i < n; i++) states.push({ x: i });
  const edges = [];
  for (let i = 0; i + 1 < n; i++) edges.push([i, i + 1, 'Inc']);
  edges.push([n - 1, 0, 'Wrap']);
  const g = graphOf(['x'], states.map((s) => ({ x: s.x })), edges);
  const t0 = Date.now();
  const { chart } = chartFor(g, {});
  assert.equal(chart.stateCount, n);
  assert.ok(Date.now() - t0 < 10000, `took ${Date.now() - t0}ms`);
});
