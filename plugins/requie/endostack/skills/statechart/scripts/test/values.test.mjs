import test from 'node:test';
import assert from 'node:assert/strict';
import { parseValue, show, key, toView, parseState, quoteString } from '../lib/values.mjs';

test('parses and prints back every value form TLC prints', () => {
  const samples = [
    'TRUE', 'FALSE', '0', '-17', '"a\\"b\\\\c\\n\\t"', 'mv1', '{}', '{1, 2, 3}', '<<>>', '<<1, "x", {a}>>',
    '[a |-> 1, b |-> <<>>]', '(1 :> "p" @@ 3 :> "q")', '1..3', '{<<1, 2>>, [f |-> {}]}',
  ];
  for (const s of samples) assert.equal(show(parseValue(s)), s);
});

test('refuses text outside the print grammar', () => {
  for (const bad of ['', '{1, 2', '<<1,>>', 'SUBSET {1}', '[S -> T]', '1 2', '{1,}', '"open', '(1 :> 2', '[]', '99999999999']) {
    assert.throws(() => parseValue(bad), undefined, bad);
  }
});

test('display keeps values TLC tells apart looking different', () => {
  assert.notEqual(show(parseValue('"A"')), show(parseValue('A')));
  assert.notEqual(show(parseValue('<<>>')), show(parseValue('{}')));
  assert.equal(show(parseValue('1..3')), '1..3');
});

test('equality keys follow TLC equality', () => {
  const eq = (a, b) => key(parseValue(a)) === key(parseValue(b));
  assert.ok(eq('{1, 2, 3}', '{3, 2, 1}'));
  assert.ok(eq('{1, 1, 2}', '{2, 1}'));
  assert.ok(eq('1..3', '{1, 2, 3}'));
  assert.ok(eq('2..1', '{}'));
  assert.ok(eq('(1 :> "a" @@ 2 :> "b")', '<<"a", "b">>'));
  assert.ok(eq('[a |-> 1, b |-> 2]', '[b |-> 2, a |-> 1]'));
  assert.ok(eq('[a |-> 1]', '("a" :> 1)'));
  assert.ok(eq('{<<>>}', '{<<>>, <<>>}'));
  assert.ok(!eq('"A"', 'A'));
  assert.ok(!eq('<<1>>', '{1}'));
  assert.ok(!eq('{1, 2}', '{1, 3}'));
  assert.ok(!eq('(1 :> "a" @@ 3 :> "b")', '<<"a", "b">>'));
});

test('generated pairs: key equality matches a reference comparison', () => {
  let seed = 12345;
  const rnd = (n) => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed % n; };
  const gen = (d) => {
    const k = rnd(d > 2 ? 4 : 7);
    if (k === 0) return { t: 'int', v: rnd(4) };
    if (k === 1) return { t: 'str', v: ['a', 'b'][rnd(2)] };
    if (k === 2) return { t: 'mv', v: ['a', 'b'][rnd(2)] };
    if (k === 3) return { t: 'bool', v: rnd(2) === 1 };
    if (k === 4) { const n = rnd(3); return { t: 'set', items: Array.from({ length: n }, () => gen(d + 1)) }; }
    if (k === 5) { const n = rnd(3); return { t: 'tup', items: Array.from({ length: n }, () => gen(d + 1)) }; }
    const lo = rnd(3); return { t: 'iv', lo, hi: lo + rnd(3) - 1 };
  };
  // Reference: normalise to JS structures and compare by canonical JSON.
  const norm = (v) => {
    switch (v.t) {
      case 'int': return ['i', v.v];
      case 'str': return ['s', v.v];
      case 'mv': return ['m', v.v];
      case 'bool': return ['b', v.v];
      case 'iv': { const a = []; for (let i = v.lo; i <= v.hi; i++) a.push(['i', i]); return ['S', [...new Set(a.map((x) => JSON.stringify(x)))].sort()]; }
      case 'set': return ['S', [...new Set(v.items.map((x) => JSON.stringify(norm(x))))].sort()];
      case 'tup': return ['F', v.items.map((x, i) => [i + 1, JSON.stringify(norm(x))])];
      default: throw new Error(v.t);
    }
  };
  for (let i = 0; i < 2000; i++) {
    const a = gen(0);
    const b = rnd(3) === 0 ? parseValue(show(a)) : gen(0);
    const ref = JSON.stringify(norm(a)) === JSON.stringify(norm(b));
    assert.equal(key(a) === key(b), ref, `${show(a)} vs ${show(b)}`);
  }
});

test('values reach the view as JSON-like data', () => {
  assert.deepEqual(toView(parseValue('<<"x", "y">>')), { 1: 'x', 2: 'y' });
  assert.deepEqual(toView(parseValue('{1, 2}')), [1, 2]);
  assert.deepEqual(toView(parseValue('2..4')), [2, 3, 4]);
  assert.equal(toView(parseValue('mv')), 'mv');
  const rec = toView(parseValue('[__proto__ |-> 1, constructor |-> 2]'));
  assert.equal(Object.getOwnPropertyDescriptor(rec, '__proto__').value, 1);
  assert.equal(Object.getOwnPropertyDescriptor(rec, 'constructor').value, 2);
  assert.deepEqual(toView(parseValue('(1 :> TRUE @@ 2 :> FALSE)')), { 1: true, 2: false });
});

test('reads one- and many-variable state printouts', () => {
  const one = parseState('light = "red"', ['light']);
  assert.equal(show(one[0]), '"red"');
  const many = parseState('/\\ b = <<1,\n  2>>\n/\\ a = {}', ['a', 'b']);
  assert.deepEqual(many.map(show), ['{}', '<<1, 2>>']);
  assert.throws(() => parseState('/\\ a = 1', ['a', 'b']), /no value for variable b/);
});

test('quoteString escapes what TLC escapes', () => {
  assert.equal(quoteString('a"b\\c\nd\te'), '"a\\"b\\\\c\\nd\\te"');
});
