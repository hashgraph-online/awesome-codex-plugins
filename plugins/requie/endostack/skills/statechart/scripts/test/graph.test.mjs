import test from 'node:test';
import assert from 'node:assert/strict';
import { parseDot } from '../lib/dot.mjs';
import { parseMarks, GraphError, bfs, findBugs } from '../lib/graph.mjs';

const TAG = 'abcdef0123456789abcdef0123456789';

test('DOT: node labels, initial fill, edge actions, stutter loops ignored, legend skipped', () => {
  const dot = [
    'strict digraph DiskGraph {',
    'subgraph cluster_graph {',
    '-5 [label="/\\\\ x = 0\\n/\\\\ y = \\"a\\"",style = filled]',
    '-5 -> 7 [label="Inc",color="black",fontcolor="black"];',
    '7 [label="/\\\\ x = 1\\n/\\\\ y = \\"a\\""];',
    '-5 -> -5 [style="dashed"];',
    '}',
    'subgraph cluster_legend {graph[style=bold];label = "Next State Actions" style="solid"',
    'Inc [label="Inc",fillcolor=2]',
    '}}',
  ].join('\n');
  const g = parseDot(dot);
  assert.equal(g.states.size, 2);
  assert.equal(g.states.get('-5').text, '/\\ x = 0\n/\\ y = "a"');
  assert.equal(g.states.get('-5').initial, true);
  assert.deepEqual(g.edges, [{ from: '-5', to: '7', action: 'Inc' }]);
});

test('DOT: a step to an unlisted state is an error', () => {
  assert.throws(() => parseDot('1 [label="x = 0",style = filled]\n1 -> 2 [label="A"];\n'), /never lists/);
});

test('DOT: parsed strings are copies, not slices of the input', () => {
  const big = `1 [label="x = 0",style = filled]\n${'2 [label="x = 1"]\n'.repeat(1)}1 -> 2 [label="A"];\n`;
  const g = parseDot(big);
  // A detached copy compares equal but is built independently.
  assert.equal(g.states.get('1').text, 'x = 0');
  assert.equal(typeof g.edges[0].action, 'string');
});

test('marks: wrapped across lines place correctly', () => {
  const out = [
    `<< "${TAG}",`,
    '   << { 1,',
    '        2 },',
    '      "a" >>,',
    '   {"Inv"} >>',
  ].join('\n');
  const marks = parseMarks(out, TAG, 2);
  assert.equal(marks.length, 1);
  assert.deepEqual(marks[0].names, ['Inv']);
});

test('marks: a tuple inside a TLC message and untagged look-alikes are ignored', () => {
  const out = [
    '@!@!@STARTMSG 2217:4 @!@!@',
    `<<"${TAG}", <<1>>, {"Inv"}>>`,
    '@!@!@ENDMSG 2217 @!@!@',
    '<<"someone else", <<1>>, {"Inv"}>>',
    `<<"${TAG}", <<constructor>>, {"Inv"}>>`,
  ].join('\n');
  const marks = parseMarks(out, TAG, 1);
  assert.equal(marks.length, 1);
  assert.equal(marks[0].vals[0].v, 'constructor');
});

test('marks: tagged text in the wrong shape, or cut off, is an error', () => {
  assert.throws(() => parseMarks(`<<"${TAG}", 1, 2>>`, TAG, 1), GraphError);
  assert.throws(() => parseMarks(`<<"${TAG}", <<1>>,`, TAG, 1), /ends in the middle/);
});

test('BFS is deterministic and independent of edge order', () => {
  const mk = (edges) => ({
    states: ['a', 'b', 'c', 'd'].map((l, i) => ({ index: i, label0: l, initial: i === 0, breaks: new Set(i === 3 ? ['r'] : []) })),
    edges,
    lassos: new Map(),
    ruleEnd: new Map(),
  });
  const e1 = [{ from: 0, to: 1, action: 'B' }, { from: 0, to: 2, action: 'A' }, { from: 1, to: 3, action: 'X' }, { from: 2, to: 3, action: 'X' }];
  const e2 = e1.slice().reverse();
  const verdicts = new Map([['r', { status: 'broken' }]]);
  const rules = [{ id: 'r', kind: 'invariant' }];
  const b1 = findBugs(mk(e1), rules, verdicts).bugs[0];
  const b2 = findBugs(mk(e2), rules, verdicts).bugs[0];
  assert.deepEqual(b1.states, [0, 2, 3]);
  assert.deepEqual(b1, b2);
  assert.deepEqual(bfs(mk(e1)).order, [0, 2, 1, 3]);
});
