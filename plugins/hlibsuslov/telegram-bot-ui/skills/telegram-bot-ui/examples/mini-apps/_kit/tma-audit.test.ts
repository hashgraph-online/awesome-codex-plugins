// Layout audit rules on synthetic screen snapshots. node --test.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { analyze } from './tma-audit.mjs';

type Rect = { x: number; y: number; w: number; h: number };
const surface = (id: string, rect: Rect, content: Rect[] = [], radius = 26, parent: string | null = null) =>
  ({ id, label: id, rect, radius, parent, content });
const screen = (surfaces: ReturnType<typeof surface>[], radii: number[] = [26, 14, 38]) =>
  ({ viewport: { w: 390, h: 844 }, surfaces, tokens: { radii } });
const rules = (snap: ReturnType<typeof screen>) => analyze(snap).map((f: { rule: string; level: string }) => `${f.rule}:${f.level}`);

test('a kit screen passes: cards 16 px apart, content 16 px inside, one radius', () => {
  const snap = screen([
    surface('settings', { x: 16, y: 100, w: 358, h: 160 }, [{ x: 32, y: 116, w: 200, h: 22 }, { x: 32, y: 222, w: 180, h: 20 }]),
    surface('progress', { x: 16, y: 276, w: 358, h: 96 }, [{ x: 32, y: 292, w: 220, h: 22 }, { x: 32, y: 336, w: 140, h: 18 }]),
  ]);
  assert.deepEqual(analyze(snap), []);
});

test('LA01: touching or nearly touching cards (the "Вивчено 13 з 283" screenshot) are errors, 10 px a warning', () => {
  const touching = screen([
    surface('settings', { x: 16, y: 100, w: 358, h: 160 }, [{ x: 40, y: 120, w: 200, h: 22 }]),
    surface('progress', { x: 16, y: 262, w: 358, h: 110 }, [{ x: 40, y: 284, w: 220, h: 22 }]),
  ]);
  assert.deepEqual(rules(touching), ['LA01:error']);
  const close = screen([
    surface('a', { x: 16, y: 100, w: 358, h: 100 }, [{ x: 32, y: 116, w: 100, h: 20 }]),
    surface('b', { x: 16, y: 210, w: 358, h: 100 }, [{ x: 32, y: 226, w: 100, h: 20 }]),
  ]);
  assert.deepEqual(rules(close), ['LA01:warn']);
});

test('LA01 ignores side-by-side tiles and surfaces in different containers', () => {
  const snap = screen([
    surface('left', { x: 16, y: 100, w: 171, h: 200 }),
    surface('right', { x: 203, y: 100, w: 171, h: 200 }),
    surface('inner', { x: 32, y: 302, w: 300, h: 60 }, [], 14, 'other'),
  ]);
  assert.deepEqual(rules(snap).filter((r) => r.startsWith('LA01')), []);
});

test('LA02: text near the side or the top of a rounded card', () => {
  const side = screen([surface('card', { x: 16, y: 100, w: 358, h: 100 }, [{ x: 24, y: 120, w: 200, h: 20 }])]);
  assert.deepEqual(rules(side), ['LA02:error']);
  const top = screen([surface('card', { x: 16, y: 100, w: 358, h: 100 }, [{ x: 32, y: 104, w: 200, h: 20 }])]);
  assert.deepEqual(rules(top), ['LA02:error']);
  const tight = screen([surface('card', { x: 16, y: 100, w: 358, h: 100 }, [{ x: 30, y: 110, w: 200, h: 20 }])]);
  assert.deepEqual(rules(tight), ['LA02:warn', 'LA02:warn']);
});

test('LA03: more than three radii, or a radius outside the kit tokens', () => {
  const mix = screen([
    surface('a', { x: 16, y: 0, w: 358, h: 80 }, [], 26), surface('b', { x: 16, y: 96, w: 358, h: 80 }, [], 20),
    surface('c', { x: 16, y: 192, w: 358, h: 80 }, [], 12), surface('d', { x: 16, y: 288, w: 358, h: 80 }, [], 8),
  ], []);
  assert.deepEqual(rules(mix), ['LA03:warn']);
  const off = screen([surface('a', { x: 16, y: 0, w: 358, h: 80 }, [], 20)]);
  assert.deepEqual(rules(off), ['LA03:warn']);
});

test('LA04 and LA05: a nested surface rounder than its parent, a card 6 px from the edge', () => {
  const nested = screen([
    surface('outer', { x: 16, y: 0, w: 358, h: 200 }, [], 14),
    surface('inner', { x: 32, y: 16, w: 326, h: 80 }, [], 26, 'outer'),
  ]);
  assert.ok(rules(nested).includes('LA04:warn'));
  const edge = screen([surface('card', { x: 6, y: 0, w: 378, h: 80 })]);
  assert.deepEqual(rules(edge), ['LA05:warn']);
  const bleed = screen([surface('band', { x: 0, y: 0, w: 390, h: 80 })]);
  assert.deepEqual(rules(bleed), []);
});
