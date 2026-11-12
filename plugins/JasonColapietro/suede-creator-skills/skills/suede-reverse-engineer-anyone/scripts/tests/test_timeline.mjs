import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  parseCsv, toCsv, parseCurve, growthSeries, findInflections, clusterMoves, computeLift,
  spearman, leadingChannels, splitThirds, diffMoves, InputError, CAVEAT, main,
} from '../timeline.mjs';

const near = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);

function months(start, n) {
  const [y, m] = start.split('-').map(Number);
  return Array.from({ length: n }, (_, k) => {
    const i = y * 12 + m - 1 + k;
    return `${Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, '0')}`;
  });
}
// Build a curve from MoM growth percentages, starting at 100.
function curveFromGrowth(start, growths) {
  const vals = [100];
  for (const g of growths) vals.push(vals[vals.length - 1] * (1 + g / 100));
  return months(start, vals.length).map((month, k) => ({ month, primary: vals[k], secondary: null }));
}
function withTmp(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'timeline-test-'));
  try {
    return fn(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}
// Runs the CLI entry point in-process and captures what it prints.
const run = (...args) => {
  const out = [];
  const err = [];
  const status = main(args, { log: (...a) => out.push(a.join(' ')), error: (...a) => err.push(a.join(' ')) });
  return { status, stdout: out.length ? `${out.join('\n')}\n` : '', stderr: err.length ? `${err.join('\n')}\n` : '' };
};

test('parseCsv handles quotes, embedded commas, escaped quotes, newlines and CRLF', () => {
  const text = '﻿date,channel,move\r\n2026-01-02,x,"Launch, then ""thread"""\r\n2026-01-03,"li","two\nlines"\r\n\r\n';
  const { headers, rows } = parseCsv(text);
  assert.deepEqual(headers, ['date', 'channel', 'move']);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].move, 'Launch, then "thread"');
  assert.equal(rows[1].move, 'two\nlines');
  assert.deepEqual(parseCsv(toCsv(rows, headers)).rows, rows);
  assert.throws(() => parseCsv('a,b\n"open,1'), InputError);
});

test('parseCurve rejects gaps and duplicates and short curves', () => {
  const base = months('2025-01', 7).map((month) => ({ month, primary: '100' }));
  assert.equal(parseCurve(base).length, 7);
  const gap = base.filter((r) => r.month !== '2025-04');
  assert.throws(() => parseCurve(gap), /gap: 2025-03 is followed by 2025-05/);
  assert.throws(() => parseCurve([...base, { month: '2025-02', primary: '1' }]), /duplicate month 2025-02/);
  assert.throws(() => parseCurve(base.slice(0, 5)), /need at least 6/);
  assert.throws(() => parseCurve([{ month: '2025/01', primary: '1' }, ...base]), /not YYYY-MM/);
});

test('findInflections finds a held step-up and ignores a one-month spike', () => {
  // growth: flat 2% then 20% for 3 months then back to 2%
  const series = growthSeries(curveFromGrowth('2025-01', [2, 2, 2, 2, 20, 20, 20, 2, 2]));
  const inf = findInflections(series);
  assert.equal(inf.length, 1);
  assert.equal(inf[0].month, '2025-06');
  near(inf[0].step, 18);
  // a single-month spike between non-positive months is not held
  const spike = growthSeries(curveFromGrowth('2025-01', [2, 2, 2, -1, 30, -5, 2, 2]));
  assert.deepEqual(findInflections(spike), []);
  // a step below --min-step is not an inflection
  const small = growthSeries(curveFromGrowth('2025-01', [2, 2, 2, 2, 5, 5, 5, 5]));
  assert.deepEqual(findInflections(small, { minStep: 5 }), []);
  assert.equal(findInflections(small, { minStep: 3 }).length, 1);
});

test('clusterMoves chains moves within the gap even when the span exceeds it', () => {
  const moves = [
    { date: '2026-05', channel: 'x', kind: 'post', move: 'late' },
    { date: '2026-01-01', channel: 'x', kind: 'post', move: 'a' },
    { date: '2026-03-10', channel: 'li', kind: 'post', move: 'c' },
    { date: '2026-02-05', channel: 'x', kind: 'post', move: 'b' },
  ];
  const c = clusterMoves(moves, 42);
  assert.equal(c.length, 2);
  assert.deepEqual(c[0].moves.map((m) => m.move), ['a', 'b', 'c']);
  assert.equal(c[0].start, '2026-01-01');
  assert.equal(c[0].end, '2026-03-10');
  assert.deepEqual(c[0].channels, ['li', 'x']);
  assert.equal(c[1].start, '2026-05-01');
  assert.equal(clusterMoves(moves, 30).length, 4);
});

test('computeLift matches a hand-computed example and refuses partial windows', () => {
  // values 100,100,100,100,110,121,133.1: growth -,0,0,0,10,10,10
  const curve = months('2025-01', 7).map((month, k) => ({ month, primary: [100, 100, 100, 100, 110, 121, 133.1][k] }));
  const s = growthSeries(curve);
  const l = computeLift(s, '2025-05');
  near(l.lift, 10);
  near(l.before, 0);
  near(l.after, 10);
  // explicit growths: after mean (10+11+12)/3=11, before mean (1+2+3)/3=2, lift 9
  const g = [null, 1, 2, 3, 10, 11, 12].map((growth, k) => ({ month: months('2025-01', 7)[k], growth }));
  near(computeLift(g, '2025-05').lift, 9);
  assert.equal(computeLift(s, '2025-04').lift, null);
  assert.match(computeLift(s, '2025-06').reason, /edge/);
  assert.match(computeLift(s, '2024-01').reason, /outside/);
});

test('spearman uses average ranks for ties', () => {
  // ranks x = 1, 2.5, 2.5, 4 ; y = 1,2,3,4 ; rho = 4.5 / sqrt(4.5 * 5)
  near(spearman([1, 2, 2, 3], [10, 20, 30, 40]), 4.5 / Math.sqrt(22.5));
  near(spearman([1, 2, 2, 3], [10, 20, 30, 40]), 0.9486833);
  near(spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]), -1);
  assert.equal(spearman([1, 1, 1], [1, 2, 3]), null);
});

test('leadingChannels declines under 18 months and under 6 moves', () => {
  const short = growthSeries(curveFromGrowth('2025-01', Array(11).fill(3)));
  const moves = Array.from({ length: 8 }, (_, k) => ({ date: `2025-0${k + 1}-01`, channel: 'x' }));
  const [r] = leadingChannels(moves, short);
  assert.equal(r.rho, undefined);
  assert.match(r.reason, /curve has 12 months; need 18/);

  // exact growth values (no compounding float noise) so ties stay ties
  const ms = months('2024-01', 24);
  const long = ms.map((month, i) => ({ month, growth: i === 0 ? null : ((i - 1) % 4) * 3 + 1 }));
  // channel x posts more two months before high growth; channel y has only 3 moves
  const xm = [];
  ms.forEach((m, i) => { for (let n = 0; n < ((i + 1) % 4); n++) xm.push({ date: m, channel: 'x' }); });
  const out = leadingChannels([...xm, ...ms.slice(0, 3).map((m) => ({ date: m, channel: 'y' }))], long);
  const x = out.find((o) => o.channel === 'x');
  const y = out.find((o) => o.channel === 'y');
  assert.match(y.reason, /3 moves; need 6/);
  // counts at month i equal the growth pattern at month i+2, so lag 2 wins with rho 1
  assert.equal(x.bestLag, 2);
  near(x.rho[2], 1);
  assert.ok(x.rho[0] < 1);
});

test('splitThirds refuses under 24, keeps channels separate, filters by age', () => {
  const posts = [];
  for (let k = 0; k < 30; k++) posts.push({ channel: 'a', date: '2026-09-01', url: `a${k}`, views: String(10000 + k * 100) });
  for (let k = 0; k < 30; k++) posts.push({ channel: 'b', date: '2026-09-01', url: `b${k}`, views: String(k) });
  for (let k = 0; k < 25; k++) posts.push({ channel: 'c', date: k < 2 ? '2026-11-05' : '2026-08-01', url: `c${k}`, views: '5' });
  const res = splitThirds(posts, 'views', { asOf: '2026-11-11', minAgeDays: 10 });
  const by = Object.fromEntries(res.channels.map((c) => [c.channel, c]));
  assert.deepEqual(by.a.sizes, { top: 10, middle: 10, bottom: 10 });
  assert.deepEqual(by.b.sizes, { top: 10, middle: 10, bottom: 10 });
  // b is ranked on its own: its best posts are top even though all are below channel a
  const tierOf = (url) => res.posts.find((p) => p.url === url).tier;
  assert.equal(tierOf('b29'), 'top');
  assert.equal(tierOf('b0'), 'bottom');
  assert.equal(tierOf('a0'), 'bottom');
  assert.equal(by.c.settled, 23);
  assert.equal(by.c.tooYoung, 2);
  assert.equal(by.c.called, false);
  assert.equal(by.c.reason, 'fewer than 24 settled posts: no pattern called');
  assert.equal(tierOf('c0'), 'too-young');
  assert.equal(tierOf('c5'), 'no-pattern');
  // uneven split: extra goes to top, then middle
  const p26 = Array.from({ length: 26 }, (_, k) => ({ channel: 'z', date: '2026-01-01', url: `${k}`, views: `${k}` }));
  assert.deepEqual(splitThirds(p26, 'views', { asOf: '2026-11-11' }).channels[0].sizes, { top: 9, middle: 9, bottom: 8 });
  // min-age 0 keeps the young posts
  assert.equal(splitThirds(posts, 'views', { asOf: '2026-11-11', minAgeDays: 0 }).channels.find((c) => c.channel === 'c').called, true);
});

test('diffMoves normalizes date, case and whitespace', () => {
  const old = [{ date: ' 2026-03 ', channel: 'X ', kind: 'Post', move: 'Launch  Thread ' }];
  const fresh = [
    { date: '2026-03-01', channel: 'x', kind: 'post', move: 'launch thread' },
    { date: '2026-04-02', channel: 'x', kind: 'post', move: 'launch thread' },
  ];
  const d = diffMoves(old, fresh);
  assert.equal(d.length, 1);
  assert.equal(d[0].date, '2026-04-02');
  assert.deepEqual(diffMoves(fresh, fresh), []);
});

test('CLI: help, bad input, moves, thirds --out, diff', () => {
  const help = run('--help');
  assert.equal(help.status, 0);
  assert.match(help.stdout, /inflections --curve/);
  assert.equal(run('nope').status, 1);

  withTmp((dir) => {
    const curvePath = join(dir, 'curve.csv');
    const curve = curveFromGrowth('2025-01', [2, 2, 2, 2, 20, 20, 20, 2, 2]);
    writeFileSync(curvePath, toCsv(curve.map((r) => ({ ...r, secondary: '' })), ['month', 'primary', 'secondary']));
    const inf = run('inflections', '--curve', curvePath, '--json');
    assert.equal(inf.status, 0, inf.stderr);
    assert.equal(JSON.parse(inf.stdout).inflections[0].month, '2025-06');

    const gapPath = join(dir, 'gap.csv');
    writeFileSync(gapPath, 'month,primary\n2025-01,1\n2025-03,2\n');
    const bad = run('inflections', '--curve', gapPath);
    assert.equal(bad.status, 1);
    assert.match(bad.stderr, /gap/);

    const movesPath = join(dir, 'moves.csv');
    writeFileSync(movesPath, 'date,channel,kind,move,reach,link,evidence\n2025-06-03,x,post,"Big launch, with ""quotes""",1000,https://e.x,ok\n2025-02,blog,post,early post,,,\n');
    const outPath = join(dir, 'mvg.csv');
    const mv = run('moves', '--moves', movesPath, '--curve', curvePath, '--out', outPath);
    assert.equal(mv.status, 0, mv.stderr);
    assert.ok(mv.stdout.includes(CAVEAT));
    assert.match(mv.stdout, /declined: curve has 10 months; need 18/);
    const rows = parseCsv(readFileSync(outPath, 'utf8')).rows;
    assert.equal(rows.length, 2);
    assert.equal(rows[1].start, '2025-06-03');
    assert.equal(rows[1].lift_primary_pp, '18');
    assert.equal(rows[0].before_inflection, 'yes');
    assert.equal(rows[1].before_inflection, 'no');
    assert.match(rows[1].items, /Big launch, with "quotes"/);

    const postsPath = join(dir, 'posts.csv');
    const posts = Array.from({ length: 24 }, (_, k) => ({ channel: 'x', date: '2026-01-01', url: `u${k}`, views: k, title: `t, ${k}` }));
    writeFileSync(postsPath, toCsv(posts, ['channel', 'date', 'url', 'views', 'title']));
    const tiered = join(dir, 'tiered.csv');
    const th = run('thirds', '--posts', postsPath, '--metric', 'views', '--as-of', '2026-11-11', '--out', tiered);
    assert.equal(th.status, 0, th.stderr);
    const t = parseCsv(readFileSync(tiered, 'utf8'));
    assert.deepEqual(t.headers, ['channel', 'date', 'url', 'views', 'title', 'tier']);
    assert.equal(t.rows.find((r) => r.url === 'u23').tier, 'top');
    assert.equal(run('thirds', '--posts', postsPath, '--metric', 'likes').status, 1);

    const df = run('diff', '--old', movesPath, '--new', movesPath);
    assert.equal(df.status, 0, df.stderr);
    assert.match(df.stdout, /no new moves/);
  });
});
