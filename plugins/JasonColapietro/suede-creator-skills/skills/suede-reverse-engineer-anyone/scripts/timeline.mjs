#!/usr/bin/env node
// timeline.mjs: the arithmetic engine for growth teardowns.
// Code does the arithmetic (growth rates, inflections, move clusters, lift,
// rank correlations, content thirds, move diffs) so nobody computes rates by hand.
// Dependency free. Node >= 22, ESM.

import { readFileSync, writeFileSync, realpathSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

export const CAVEAT =
  'Timing is a lead, not a verdict: funding, press, seasonality, and category trends can produce the same lift.';

export class InputError extends Error {}
const fail = (msg) => {
  throw new InputError(msg);
};

// ---------- CSV ----------

/** Quote-aware CSV parser. Returns { headers, rows } where rows are objects keyed by header. */
export function parseCsv(text) {
  const src = String(text).replace(/^﻿/, '');
  const records = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < src.length; i++) {
    const c = src[i];
    if (inQuotes) {
      if (c === '"') {
        if (src[i + 1] === '"') {
          field += '"';
          i++;
        } else inQuotes = false;
      } else field += c;
    } else if (c === '"' && field === '') {
      inQuotes = true;
    } else if (c === ',') {
      row.push(field);
      field = '';
    } else if (c === '\n' || c === '\r') {
      row.push(field);
      records.push(row);
      row = [];
      field = '';
      if (c === '\r' && src[i + 1] === '\n') i++;
    } else field += c;
  }
  if (inQuotes) fail('CSV has an unclosed quoted field');
  if (field !== '' || row.length) {
    row.push(field);
    records.push(row);
  }
  const nonEmpty = records.filter((r) => !(r.length === 1 && r[0].trim() === ''));
  if (!nonEmpty.length) return { headers: [], rows: [] };
  const headers = nonEmpty[0].map((h) => h.trim());
  const rows = nonEmpty.slice(1).map((r) => {
    const obj = {};
    headers.forEach((h, k) => {
      if (h) obj[h] = r[k] ?? '';
    });
    return obj;
  });
  return { headers, rows };
}

/** Serialize row objects to CSV text, quoting fields that need it. */
export function toCsv(rows, headers) {
  const cols = headers ?? (rows.length ? Object.keys(rows[0]) : []);
  const esc = (v) => {
    const s = v == null ? '' : String(v);
    return /[",\r\n]|^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.map(esc).join(','), ...rows.map((r) => cols.map((c) => esc(r[c])).join(','))].join('\n') + '\n';
}

// ---------- small helpers ----------

export function parseNumber(v) {
  if (v == null) return null;
  const s = String(v).trim().replace(/[,_\s]/g, '');
  if (s === '') return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
const round = (v, d = 2) => (v == null ? null : Math.round(v * 10 ** d) / 10 ** d);

const MONTH_RE = /^(\d{4})-(\d{2})$/;
const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

function monthIndex(m) {
  const x = MONTH_RE.exec(m);
  return Number(x[1]) * 12 + Number(x[2]) - 1;
}
function monthFromIndex(i) {
  return `${Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, '0')}`;
}

/** Normalize YYYY-MM-DD or YYYY-MM (treated as the 1st) to YYYY-MM-DD. Returns null when invalid. */
export function normalizeDate(s) {
  const t = String(s ?? '').trim();
  const m = MONTH_RE.exec(t);
  const full = m ? `${t}-01` : t.length > 10 && /^\d{4}-\d{2}-\d{2}T/.test(t) ? t.slice(0, 10) : t;
  const d = DATE_RE.exec(full);
  if (!d) return null;
  const [y, mo, da] = [Number(d[1]), Number(d[2]), Number(d[3])];
  const dt = new Date(Date.UTC(y, mo - 1, da));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== mo - 1 || dt.getUTCDate() !== da) return null;
  return full;
}

const dayNumber = (date) => Date.UTC(+date.slice(0, 4), +date.slice(5, 7) - 1, +date.slice(8, 10)) / 86400000;

// ---------- curve and growth ----------

/** Validate curve rows: YYYY-MM months, numeric primary, optional secondary, contiguous, no duplicates. */
export function parseCurve(rows, { minMonths = 6 } = {}) {
  const out = rows.map((r, k) => {
    const month = String(r.month ?? '').trim();
    const x = MONTH_RE.exec(month);
    if (!x || +x[2] < 1 || +x[2] > 12) fail(`curve data row ${k + 1}: month "${month}" is not YYYY-MM`);
    const primary = parseNumber(r.primary);
    if (primary == null) fail(`curve data row ${k + 1} (${month}): primary "${r.primary ?? ''}" is not a number`);
    const rawSecondary = String(r.secondary ?? '').trim();
    const secondary = parseNumber(rawSecondary);
    if (rawSecondary !== '' && secondary == null) fail(`curve data row ${k + 1} (${month}): secondary "${rawSecondary}" is not a number`);
    return { month, primary, secondary };
  });
  out.sort((a, b) => monthIndex(a.month) - monthIndex(b.month));
  for (let k = 1; k < out.length; k++) {
    const step = monthIndex(out[k].month) - monthIndex(out[k - 1].month);
    if (step === 0) fail(`curve has duplicate month ${out[k].month}`);
    if (step > 1) fail(`curve has a gap: ${out[k - 1].month} is followed by ${out[k].month} (missing ${monthFromIndex(monthIndex(out[k - 1].month) + 1)})`);
  }
  if (out.length < minMonths) fail(`curve has ${out.length} months; need at least ${minMonths}`);
  return out;
}

/** Month-over-month growth in percent. Growth is null for the first month or when either value is missing or the prior value is <= 0. */
export function growthSeries(curve, metric = 'primary') {
  return curve.map((row, k) => {
    const value = row[metric] ?? null;
    const prev = k > 0 ? curve[k - 1][metric] ?? null : null;
    const growth = value != null && prev != null && prev > 0 ? ((value - prev) / prev) * 100 : null;
    return { month: row.month, value, growth };
  });
}

/**
 * Inflection: month i where mean(growth[i], growth[i+1]) beats mean(growth[i-3..i-1]) by at least minStep
 * percentage points and both growth[i] and growth[i+1] are positive. Each run of consecutive qualifying
 * months collapses to the month with the largest step.
 */
export function findInflections(series, { minStep = 5 } = {}) {
  const g = series.map((s) => s.growth);
  const hits = [];
  for (let i = 3; i + 1 < g.length; i++) {
    const prior = [g[i - 3], g[i - 2], g[i - 1]];
    const hold = [g[i], g[i + 1]];
    if ([...prior, ...hold].some((v) => v == null)) continue;
    if (!(hold[0] > 0 && hold[1] > 0)) continue;
    const step = mean(hold) - mean(prior);
    if (step >= minStep - 1e-9) hits.push({ month: series[i].month, priorMean: mean(prior), holdMean: mean(hold), step });
  }
  // A sharp jump also qualifies the month just before it (its 2-month mean straddles the jump),
  // so each run of consecutive qualifying months collapses to its largest step.
  const runs = [];
  for (const h of hits) {
    const run = runs[runs.length - 1];
    if (run && monthIndex(h.month) - monthIndex(run[run.length - 1].month) === 1) run.push(h);
    else runs.push([h]);
  }
  return runs.map((run) => run.reduce((a, b) => (b.step > a.step + 1e-9 ? b : a)));
}

// ---------- moves ----------

/** Sort moves by date and chain them into clusters: each next move within gapDays of the previous one joins. */
export function clusterMoves(moves, gapDays = 42) {
  const sorted = moves
    .map((m, k) => ({ m, k, date: normalizeDate(m.date) }))
    .map((x) => (x.date ? x : fail(`move "${x.m.move ?? ''}" has bad date "${x.m.date ?? ''}"`)))
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : a.k - b.k));
  const clusters = [];
  for (const { m, date } of sorted) {
    const last = clusters[clusters.length - 1];
    const move = { ...m, date };
    if (last && dayNumber(date) - dayNumber(last.end) <= gapDays) {
      last.moves.push(move);
      last.end = date;
    } else clusters.push({ start: date, end: date, moves: [move] });
  }
  for (const c of clusters) c.channels = [...new Set(c.moves.map((m) => String(m.channel ?? '').trim()))].sort();
  return clusters;
}

/** Lift in percentage points: mean growth of the 3 months starting at `month` minus mean growth of the 3 months before. */
export function computeLift(series, month) {
  const idx = series.findIndex((s) => s.month === month);
  if (idx < 0) return { lift: null, reason: `${month} is outside the curve` };
  if (idx - 3 < 0 || idx + 2 >= series.length) return { lift: null, reason: 'needs 3 months of growth on each side; too close to the edge of the curve' };
  const before = series.slice(idx - 3, idx).map((s) => s.growth);
  const after = series.slice(idx, idx + 3).map((s) => s.growth);
  if ([...before, ...after].some((v) => v == null)) return { lift: null, reason: 'missing or zero values in the 6-month window' };
  return { lift: mean(after) - mean(before), before: mean(before), after: mean(after) };
}

function averageRanks(xs) {
  const idx = xs.map((v, k) => [v, k]).sort((a, b) => a[0] - b[0]);
  const ranks = new Array(xs.length);
  for (let i = 0; i < idx.length; ) {
    let j = i;
    while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    const r = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) ranks[idx[k][1]] = r;
    i = j + 1;
  }
  return ranks;
}

/** Spearman rank correlation with average ranks for ties (Pearson on ranks). Null when n < 3 or a side has no variation. */
export function spearman(x, y) {
  if (x.length !== y.length) fail('spearman needs equal-length inputs');
  if (x.length < 3) return null;
  const rx = averageRanks(x);
  const ry = averageRanks(y);
  const mx = mean(rx);
  const my = mean(ry);
  let cov = 0;
  let vx = 0;
  let vy = 0;
  for (let k = 0; k < rx.length; k++) {
    cov += (rx[k] - mx) * (ry[k] - my);
    vx += (rx[k] - mx) ** 2;
    vy += (ry[k] - my) ** 2;
  }
  return vx === 0 || vy === 0 ? null : cov / Math.sqrt(vx * vy);
}

/** Per channel: Spearman between monthly move counts and growth at lags 0..2 months. Declines when data is thin. */
export function leadingChannels(moves, series, { minMonths = 18, minMoves = 6, lags = [0, 1, 2] } = {}) {
  const byChannel = new Map();
  for (const m of moves) {
    const ch = String(m.channel ?? '').trim();
    if (!byChannel.has(ch)) byChannel.set(ch, []);
    byChannel.get(ch).push(m);
  }
  const first = series.length ? monthIndex(series[0].month) : 0;
  return [...byChannel.keys()].sort().map((channel) => {
    const list = byChannel.get(channel);
    if (series.length < minMonths) return { channel, moves: list.length, reason: `curve has ${series.length} months; need ${minMonths}` };
    if (list.length < minMoves) return { channel, moves: list.length, reason: `${list.length} moves; need ${minMoves}` };
    const counts = new Array(series.length).fill(0);
    for (const m of list) {
      const d = normalizeDate(m.date);
      const i = d ? monthIndex(d.slice(0, 7)) - first : -1;
      if (i >= 0 && i < counts.length) counts[i]++;
    }
    const rho = {};
    for (const lag of lags) {
      const x = [];
      const y = [];
      for (let i = 0; i + lag < series.length; i++) {
        if (series[i + lag].growth == null) continue;
        x.push(counts[i]);
        y.push(series[i + lag].growth);
      }
      rho[lag] = spearman(x, y);
    }
    const valid = lags.filter((l) => rho[l] != null);
    const best = valid.length ? valid.reduce((a, b) => (rho[b] > rho[a] ? b : a)) : null;
    return { channel, moves: list.length, rho, bestLag: best, reason: best == null ? 'no variation in counts or growth' : null };
  });
}

// ---------- content thirds ----------

/** Rank settled posts by metric within each channel and tier them top/middle/bottom. Never ranks across channels. */
export function splitThirds(posts, metric, { minAgeDays = 10, asOf, minPosts = 24 } = {}) {
  const asOfDate = normalizeDate(asOf ?? new Date().toISOString().slice(0, 10));
  if (!asOfDate) fail(`--as-of "${asOf}" is not YYYY-MM-DD`);
  const today = dayNumber(asOfDate);
  const out = posts.map((p, k) => {
    const date = normalizeDate(p.date);
    if (!date) fail(`posts data row ${k + 1}: date "${p.date ?? ''}" is not YYYY-MM-DD`);
    return { post: { ...p, tier: '' }, k, date, value: parseNumber(p[metric]), channel: String(p.channel ?? '').trim() };
  });
  const groups = new Map();
  for (const x of out) {
    if (!groups.has(x.channel)) groups.set(x.channel, { total: 0, young: 0, noMetric: 0, settled: [] });
    const g = groups.get(x.channel);
    g.total++;
    if (today - dayNumber(x.date) < minAgeDays) {
      g.young++;
      x.post.tier = 'too-young';
    } else if (x.value == null) {
      g.noMetric++;
      x.post.tier = 'no-metric';
    } else g.settled.push(x);
  }
  const channels = [...groups.keys()].sort().map((channel) => {
    const g = groups.get(channel);
    const n = g.settled.length;
    const base = { channel, total: g.total, settled: n, tooYoung: g.young, noMetric: g.noMetric };
    if (n < minPosts) {
      for (const x of g.settled) x.post.tier = 'no-pattern';
      return { ...base, called: false, reason: `fewer than ${minPosts} settled posts: no pattern called` };
    }
    const ranked = [...g.settled].sort((a, b) => b.value - a.value || a.k - b.k);
    const third = Math.floor(n / 3);
    const top = third + (n % 3 > 0 ? 1 : 0);
    const middle = third + (n % 3 > 1 ? 1 : 0);
    ranked.forEach((x, r) => (x.post.tier = r < top ? 'top' : r < top + middle ? 'middle' : 'bottom'));
    return {
      ...base,
      called: true,
      sizes: { top, middle, bottom: n - top - middle },
      topFloor: ranked[top - 1].value,
      bottomCeiling: ranked[top + middle].value,
    };
  });
  return { asOf: asOfDate, channels, posts: out.map((x) => x.post) };
}

// ---------- diff ----------

export function moveKey(m) {
  const t = (v) => String(v ?? '').trim().toLowerCase().replace(/\s+/g, ' ');
  return [normalizeDate(m.date) ?? t(m.date), t(m.channel), t(m.kind), t(m.move)].join('\u0001');
}

/** Moves present in newMoves but not oldMoves, keyed by normalized (date, channel, kind, move). */
export function diffMoves(oldMoves, newMoves) {
  const seen = new Set(oldMoves.map(moveKey));
  return newMoves.filter((m) => !seen.has(moveKey(m)));
}

// ---------- CLI ----------

const USAGE = `timeline.mjs: arithmetic for growth teardowns

Usage:
  node timeline.mjs inflections --curve curve.csv [--metric primary|secondary] [--min-step 5] [--out growth.csv] [--json]
  node timeline.mjs moves --moves moves.csv --curve curve.csv [--cluster-days 42] [--min-step 5] [--out moves-vs-growth.csv] [--json]
  node timeline.mjs thirds --posts posts.csv --metric views [--min-age-days 10] [--as-of YYYY-MM-DD] [--out posts-tiered.csv] [--json]
  node timeline.mjs diff --old old.csv --new new.csv [--out new-moves.csv] [--json]

Inputs:
  curve.csv   month,primary,secondary   (month YYYY-MM, contiguous; secondary optional)
  moves.csv   date,channel,kind,move,reach,link,evidence   (date YYYY-MM-DD or YYYY-MM)
  posts.csv   channel,date,url,<metric>,...`;

function readCsv(path, flag) {
  if (!path) fail(`--${flag} is required`);
  let text;
  try {
    text = readFileSync(path, 'utf8');
  } catch (e) {
    fail(`cannot read ${path}: ${e.code ?? e.message}`);
  }
  return parseCsv(text);
}

function requireColumns({ headers }, cols, label) {
  const missing = cols.filter((c) => !headers.includes(c));
  if (missing.length) fail(`${label} is missing column(s): ${missing.join(', ')} (found: ${headers.join(', ') || 'none'})`);
}

function loadMoves(path, flag) {
  const csv = readCsv(path, flag);
  requireColumns(csv, ['date', 'channel', 'kind', 'move'], path);
  csv.rows.forEach((r, k) => {
    if (!normalizeDate(r.date)) fail(`${path} data row ${k + 1}: date "${r.date}" is not YYYY-MM-DD or YYYY-MM`);
  });
  return csv;
}

function loadCurve(path) {
  const csv = readCsv(path, 'curve');
  requireColumns(csv, ['month', 'primary'], path);
  return parseCurve(csv.rows);
}

function num(v, flag, { min = -Infinity, integer = false } = {}) {
  const n = Number(v);
  if (v === undefined || v === '' || !Number.isFinite(n) || n < min || (integer && !Number.isInteger(n))) fail(`--${flag} must be a ${integer ? 'whole ' : ''}number${min > -Infinity ? ` >= ${min}` : ''}`);
  return n;
}

const pct = (v, unit = '%') => (v == null ? '-' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}${unit}`);

function table(headers, rows) {
  const cells = rows.map((r) => r.map((c) => (c == null ? '' : String(c))));
  const w = headers.map((h, k) => Math.max(h.length, ...cells.map((r) => r[k].length)));
  const line = (r) => r.map((c, k) => c.padEnd(w[k])).join('  ').trimEnd();
  return [line(headers), line(w.map((n) => '-'.repeat(n))), ...cells.map(line)].join('\n');
}

function writeOut(path, rows, headers) {
  try {
    writeFileSync(path, toCsv(rows, headers));
  } catch (e) {
    fail(`cannot write ${path}: ${e.code ?? e.message}`);
  }
}

function cmdInflections(o, log) {
  const metric = o.metric ?? 'primary';
  if (!['primary', 'secondary'].includes(metric)) fail('--metric must be primary or secondary');
  const curve = loadCurve(o.curve);
  if (curve.every((r) => r[metric] == null)) fail(`curve has no ${metric} values`);
  const series = growthSeries(curve, metric);
  const inflections = findInflections(series, { minStep: num(o['min-step'] ?? '5', 'min-step', { min: 0 }) });
  const flagged = new Set(inflections.map((i) => i.month));
  const rows = series.map((s) => ({ month: s.month, value: s.value, mom_growth_pct: round(s.growth), inflection: flagged.has(s.month) ? 'yes' : '' }));
  if (o.out) writeOut(o.out, rows, ['month', 'value', 'mom_growth_pct', 'inflection']);
  if (o.json) return log(JSON.stringify({ metric, months: series.length, series: rows, inflections: inflections.map((i) => ({ month: i.month, prior_mean_pct: round(i.priorMean), hold_mean_pct: round(i.holdMean), step_pp: round(i.step) })) }, null, 2));
  log(table(['month', metric, 'MoM', 'inflection'], series.map((s) => [s.month, s.value ?? '-', pct(s.growth), flagged.has(s.month) ? '<< inflection' : ''])));
  log('');
  if (!inflections.length) log('No inflection found (needs a step-up held 2+ months).');
  for (const i of inflections) log(`Inflection ${i.month}: ${pct(i.holdMean)} avg MoM over 2 months vs ${pct(i.priorMean)} over the prior 3 (step ${pct(i.step, 'pp')}).`);
  if (o.out) log(`Wrote ${o.out}`);
}

function cmdMoves(o, log) {
  const curve = loadCurve(o.curve);
  const moves = loadMoves(o.moves, 'moves').rows;
  const gap = num(o['cluster-days'] ?? '42', 'cluster-days', { min: 0, integer: true });
  const primary = growthSeries(curve, 'primary');
  const hasSecondary = curve.some((r) => r.secondary != null);
  const secondary = hasSecondary ? growthSeries(curve, 'secondary') : null;
  const firstInflection = findInflections(primary, { minStep: num(o['min-step'] ?? '5', 'min-step', { min: 0 }) })[0]?.month ?? null;
  const clusters = clusterMoves(moves, gap).map((c, k) => {
    const month = c.start.slice(0, 7);
    const lp = computeLift(primary, month);
    const ls = secondary ? computeLift(secondary, month) : null;
    return {
      cluster: k + 1, start: c.start, end: c.end, moves: c.moves.length, channels: c.channels,
      lift_primary_pp: round(lp.lift), lift_primary_note: lp.reason ?? null,
      lift_secondary_pp: ls ? round(ls.lift) : null, lift_secondary_note: ls ? ls.reason ?? null : 'no secondary series',
      before_inflection: firstInflection ? month < firstInflection : null,
      items: c.moves.map((m) => ({ date: m.date, channel: m.channel, kind: m.kind, move: m.move, reach: m.reach ?? '', link: m.link ?? '' })),
    };
  });
  const leading = leadingChannels(moves, primary).map((l) => ({
    channel: l.channel, moves: l.moves, rho_lag0: round(l.rho?.[0] ?? null, 3), rho_lag1: round(l.rho?.[1] ?? null, 3), rho_lag2: round(l.rho?.[2] ?? null, 3), best_lag: l.bestLag ?? null, note: l.reason ?? null,
  }));
  if (o.out) {
    const rows = clusters.map((c) => ({ ...c, channels: c.channels.join('; '), before_inflection: c.before_inflection == null ? '' : c.before_inflection ? 'yes' : 'no', items: c.items.map((m) => `${m.date} ${m.channel}/${m.kind}: ${m.move}`).join(' | ') }));
    writeOut(o.out, rows, ['cluster', 'start', 'end', 'moves', 'channels', 'lift_primary_pp', 'lift_primary_note', 'lift_secondary_pp', 'lift_secondary_note', 'before_inflection', 'items']);
  }
  if (o.json) return log(JSON.stringify({ first_inflection: firstInflection, cluster_days: gap, clusters, leading, caveat: CAVEAT }, null, 2));
  log(`First inflection (primary): ${firstInflection ?? 'none found'}. Cluster gap: ${gap} days.\n`);
  const yn = (v) => (v == null ? '-' : v ? 'yes' : 'no');
  log(table(['#', 'start', 'end', 'moves', 'channels', 'lift primary', 'lift secondary', 'before infl.'],
    clusters.map((c) => [c.cluster, c.start, c.end, c.moves, c.channels.join(', '), pct(c.lift_primary_pp, 'pp'), hasSecondary ? pct(c.lift_secondary_pp, 'pp') : 'n/a', yn(c.before_inflection)])));
  for (const c of clusters) {
    if (c.lift_primary_note) log(`  #${c.cluster}: no primary lift (${c.lift_primary_note})`);
    if (hasSecondary && c.lift_secondary_note) log(`  #${c.cluster}: no secondary lift (${c.lift_secondary_note})`);
  }
  log('\nLeading channel (Spearman: monthly move count vs primary MoM growth):');
  log(table(['channel', 'moves', 'lag 0', 'lag 1', 'lag 2', 'best'],
    leading.map((l) => (l.note && l.best_lag == null ? [l.channel, l.moves, '-', '-', '-', `declined: ${l.note}`] : [l.channel, l.moves, l.rho_lag0 ?? '-', l.rho_lag1 ?? '-', l.rho_lag2 ?? '-', `lag ${l.best_lag}`]))));
  log(`\n${CAVEAT}`);
  if (o.out) log(`Wrote ${o.out}`);
}

function cmdThirds(o, log) {
  if (!o.metric) fail('--metric is required (the column to rank by, e.g. views)');
  const csv = readCsv(o.posts, 'posts');
  requireColumns(csv, ['channel', 'date', 'url', o.metric], o.posts);
  const minAgeDays = num(o['min-age-days'] ?? '10', 'min-age-days', { min: 0 });
  const res = splitThirds(csv.rows, o.metric, { minAgeDays, asOf: o['as-of'] });
  if (o.out) writeOut(o.out, res.posts, [...csv.headers.filter((h) => h && h !== 'tier'), 'tier']);
  if (o.json) return log(JSON.stringify({ metric: o.metric, as_of: res.asOf, min_age_days: minAgeDays, channels: res.channels }, null, 2));
  log(`Metric: ${o.metric}. As of ${res.asOf}; posts younger than ${minAgeDays} days dropped. Ranked within each channel only.\n`);
  log(table(['channel', 'posts', 'settled', 'too young', 'no metric', 'result'], res.channels.map((c) => [
    c.channel, c.total, c.settled, c.tooYoung, c.noMetric,
    c.called ? `top ${c.sizes.top} (>= ${c.topFloor}), middle ${c.sizes.middle}, bottom ${c.sizes.bottom} (<= ${c.bottomCeiling})` : c.reason,
  ])));
  if (o.out) log(`\nWrote ${o.out}`);
}

function cmdDiff(o, log) {
  const oldCsv = loadMoves(o.old, 'old');
  const newCsv = loadMoves(o.new, 'new');
  const added = diffMoves(oldCsv.rows, newCsv.rows);
  if (o.out) writeOut(o.out, added, newCsv.headers.filter(Boolean));
  if (o.json) return log(JSON.stringify({ new_moves: added }, null, 2));
  if (!added.length) log('no new moves');
  else {
    log(`${added.length} new move(s):\n`);
    log(table(['date', 'channel', 'kind', 'move'], added.map((m) => [m.date, m.channel, m.kind, m.move])));
  }
  if (o.out) log(`\nWrote ${o.out}`);
}

const COMMANDS = { inflections: cmdInflections, moves: cmdMoves, thirds: cmdThirds, diff: cmdDiff };

/** Run the CLI. Returns an exit code. */
export function main(argv, { log = console.log, error = console.error } = {}) {
  const [cmd, ...rest] = argv;
  if (!cmd || cmd === '--help' || cmd === '-h' || cmd === 'help') {
    log(USAGE);
    return cmd ? 0 : 1;
  }
  try {
    if (!COMMANDS[cmd]) fail(`unknown command "${cmd}" (expected: ${Object.keys(COMMANDS).join(', ')})`);
    const str = { type: 'string' };
    const { values } = parseArgs({
      args: rest,
      strict: true,
      options: {
        curve: str, moves: str, posts: str, old: str, new: str, out: str, metric: str,
        'min-step': str, 'cluster-days': str, 'min-age-days': str, 'as-of': str,
        json: { type: 'boolean' }, help: { type: 'boolean', short: 'h' },
      },
    });
    if (values.help) {
      log(USAGE);
      return 0;
    }
    COMMANDS[cmd](values, log);
    return 0;
  } catch (e) {
    error(`timeline: ${e.message}`);
    if (!(e instanceof InputError)) error('Run with --help for usage.');
    return 1;
  }
}

function invokedDirectly() {
  if (!process.argv[1]) return false;
  try {
    return import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href;
  } catch {
    return import.meta.url === pathToFileURL(process.argv[1]).href;
  }
}

if (invokedDirectly()) process.exitCode = main(process.argv.slice(2));
