import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { checkView, loadView, applyView, ViewError } from '../lib/view.mjs';
import { parseValue, toView, show } from '../lib/values.mjs';

test('accepts a full view', () => {
  const v = checkView({ state: () => 'x', step: () => 'y', group: () => 'g', colors: { g: 'blue' }, title: 't' });
  assert.equal(v.colors.get('g'), 'blue');
});

test('rejects unknown exports, naming them and the allowed ones', () => {
  assert.throws(() => checkView({ states: () => 'x' }), /exports states are not recognized.*state, step, group, colors, title/);
  assert.throws(() => checkView({ default: {} }), /default/);
});

test('reports every type problem together', () => {
  try {
    checkView({ state: 1, step: 'x', title: 3, colors: { a: 'red', b: 'breaks' } });
    assert.fail('should throw');
  } catch (e) {
    assert.ok(e instanceof ViewError);
    for (const part of ['state export must be a function', 'step export must be a function', 'title export must be a string', '"a" is \'red\'', '"b" is \'breaks\'']) {
      assert.ok(e.message.includes(part), `${part} in ${e.message}`);
    }
  }
});

test('colors must be a plain object, read from own keys only', () => {
  assert.throws(() => checkView({ colors: new Map([['a', 'blue']]) }), /plain object/);
  assert.throws(() => checkView({ colors: 'blue' }), /plain object/);
  class C { constructor() { this.a = 'blue'; } }
  assert.throws(() => checkView({ colors: new C() }), /plain object/);
  assert.throws(() => checkView({ group: () => 'a' }), /needs a colors export/);
  const v = checkView({ group: () => 'toString', colors: { a: 'blue' } });
  const states = [{ vals: [parseValue('1')] }];
  assert.throws(() => applyView(v, ['x'], states, [], toView, () => 'x=1'), /'toString'.*not a key of colors/);
});

test('loadView: a module that throws prints its message without a stack', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'view-'));
  const write = (name, body) => { const f = path.join(dir, name); fs.writeFileSync(f, body); return f; };
  await assert.rejects(loadView(write('a.mjs', 'throw { message: "custom stop" };')), (e) => e.message === 'custom stop');
  await assert.rejects(loadView(write('b.mjs', 'throw null;')), (e) => e.message === 'null');
  await assert.rejects(loadView(write('c.mjs', 'throw Object.create(null);')), (e) => e.message === '[Object: null prototype] {}');
  await assert.rejects(loadView(write('d.mjs', 'export const colour = {};')), /colour are not recognized/);
  await assert.rejects(loadView(write('e.mjs', 'export const title = 5;')), /title export must be a string/);
  fs.rmSync(dir, { recursive: true });
});

test('labels: invalid results show the value and the TLA+ state', () => {
  const states = [{ vals: [parseValue('1')] }];
  const lbl = (s) => `x=${show(s.vals[0])}`;
  const run = (view) => applyView(checkView(view), ['x'], states, [], toView, lbl);
  assert.throws(() => run({ state: () => 5 }), /returned 5 .*state x=1/);
  assert.throws(() => run({ state: (v) => `n ${v.missing}` }), /'n undefined'/);
  assert.throws(() => run({ state: () => '' }), /non-empty/);
  assert.throws(() => run({ state: () => [] }), /empty array/);
  assert.throws(() => run({ state: () => ({}) }), /at least one region/);
  const edgeStates = [{ vals: [parseValue('1')] }, { vals: [parseValue('2')] }];
  assert.throws(() => applyView(checkView({ step: () => '' }), ['x'], edgeStates, [{ from: 0, to: 1, action: 'A' }], toView, lbl), /step function returned ''/);
});

test('view functions are called once per state, step, and group', () => {
  const calls = { state: 0, step: 0, group: 0 };
  const view = checkView({
    state: () => { calls.state++; return 's'; },
    step: () => { calls.step++; return 'go'; },
    group: () => { calls.group++; return 'g'; },
    colors: { g: 'teal' },
  });
  const states = [0, 1, 2].map((i) => ({ vals: [parseValue(String(i))] }));
  const edges = [{ from: 0, to: 1, action: 'A' }, { from: 1, to: 2, action: 'A' }];
  applyView(view, ['x'], states, edges, toView, () => 'x');
  assert.deepEqual(calls, { state: 3, step: 2, group: 3 });
});

test('regions must have the same names in every state', () => {
  const states = [0, 1].map((i) => ({ vals: [parseValue(String(i))] }));
  const view = checkView({ state: ({ x }) => (x === 0 ? { A: 'a', B: 'b' } : { A: 'a', C: 'c' }) });
  assert.throws(() => applyView(view, ['x'], states, [], toView, () => 'x'), /same region names/);
  const proto = checkView({ state: () => ({ __proto__: 'not a region' }) });
  void proto;
});

test('a region named __proto__ is an ordinary region', () => {
  const states = [{ vals: [parseValue('0')] }];
  const view = checkView({ state: () => JSON.parse('{"__proto__": "a", "B": "b"}') });
  const applied = applyView(view, ['x'], states, [], toView, () => 'x');
  assert.deepEqual(applied.regionNames, ['__proto__', 'B']);
});
