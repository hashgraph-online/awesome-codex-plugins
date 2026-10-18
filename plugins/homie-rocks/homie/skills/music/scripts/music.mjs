#!/usr/bin/env node
/** music.mjs: local asset preparation only. Generation, schemas and pricing belong to the official provider MCP.
 * Read ../SKILL.md for the current workflow. */
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { beatsOf, decodeMono, loudness, need, probe, run } from './lib/audio.mjs';

import { SLUG, checkBudget, getEntry, readBudget, readJson, receipt, rel, requireStudio, setBudget, studioHasMediaPages, upsertEntry, writeJson } from './lib/studio.mjs';

const argv = process.argv.slice(2);
const flags = new Map();
const pos = [];
const BOOL = new Set(['json', 'yes', 'dry-run', 'vocals', 'publish', 'instrumental', 'again', 'no-deploy']);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const [k, v] = a.slice(2).split(/=(.*)/s, 2);
    if (v !== undefined) flags.set(k, v);
    else if (!BOOL.has(k) && argv[i + 1] !== undefined && !argv[i + 1].startsWith('--')) flags.set(k, argv[++i]);
    else flags.set(k, true);
  } else pos.push(a);
}
const asJson = flags.has('json');
const say = (line) => { if (!asJson) process.stderr.write(`${line}\n`); };
const OUTPUT_FORMAT = 'mp3_48000_192';

function jobDir(root, slug) {
  if (!SLUG.test(String(slug ?? ''))) throw new Error('name the song with a slug: lowercase letters, digits and hyphens (it becomes /music/<slug>/)');
  const dir = join(root, 'music', slug);
  mkdirSync(join(dir, 'work'), { recursive: true });
  return dir;
}

/* ---------------------------------------------------------------- check / quote / budget */

async function check() {
  const out = { ok: true, command: 'check', ffmpeg: need('ffmpeg') && need('ffprobe'), generation: 'Use the official ElevenLabs MCP in your AI client' };
  let root = null;
  try { root = requireStudio(); } catch (error) { out.studio = { ok: false, why: error.message }; }
  if (root) out.studio = { ok: true, root, pages: studioHasMediaPages(root) };
  if (!out.ffmpeg) { out.ok = false; out.why = [out.why, 'ffmpeg is not installed (macOS: `brew install ffmpeg`; the person approves the install)'].filter(Boolean).join('; '); }
  return out;
}

function budget(root) {
  const slug = pos[1];
  const cap = Number(flags.get('cap'));
  if (!(cap > 0)) throw new Error('--cap <credits>: the most the person agreed to spend on this song');
  const b = setBudget(jobDir(root, slug), { provider: 'elevenlabs', unit: 'credits', cap, approvedBy: flags.get('by') ?? 'the person, in chat', note: flags.get('note') ?? null });
  return { ok: true, command: 'budget', slug, budget: b };
}

/* ---------------------------------------------------------------- plan */

/**
 * spec.json: { title, bpm, key?, styles[], avoid[], sections: [ { name, bars, lines[] | instrumental: true, styles[], avoid[] } ] }
 * Every section is a whole number of bars at the song's tempo, so the plan's
 * section boundaries are bar lines: loops and video cuts can land on them.
 */
export function buildPlan(spec) {
  const bpm = Number(spec.bpm);
  if (!(bpm >= 50 && bpm <= 220)) throw new Error('spec.bpm must be 50..220');
  const beats = Number(spec.beatsPerBar ?? 4);
  const barMs = (60_000 / bpm) * beats;
  const sections = Array.isArray(spec.sections) ? spec.sections : [];
  if (!sections.length) throw new Error('spec.sections is empty');
  const chunks = [];
  const warnings = [];
  let bar = 0;
  const lyrics = [];
  sections.forEach((s, i) => {
    const bars = Number(s.bars);
    if (!(Number.isInteger(bars) && bars >= 1)) throw new Error(`section ${i + 1} (${s.name}): bars must be a whole number`);
    const start = Math.round(bar * barMs); const end = Math.round((bar + bars) * barMs);
    const ms = end - start;
    if (ms < 3000) throw new Error(`section ${i + 1} (${s.name}) is ${ms} ms; ElevenLabs needs 3000 ms or more per section (at ${bpm} BPM that is ${Math.ceil(3000 / barMs)} bars): merge it or lengthen it`);
    if (ms > 120_000) throw new Error(`section ${i + 1} (${s.name}) is over 120 s; split it`);
    const lines = Array.isArray(s.lines) ? s.lines.map((l) => String(l).trim()).filter(Boolean) : [];
    for (const l of lines) if (l.length > 200) throw new Error(`a line in ${s.name} is over 200 characters`);
    if (lines.length > bars * 2) warnings.push(`${s.name}: ${lines.length} lines in ${bars} bars will be rushed (about one or two lines a bar is singable)`);
    const instrumental = Boolean(s.instrumental) || !lines.length;
    const first = i === 0;
    const pos = [
      ...(first ? [...(spec.styles ?? []), `${Math.round(bpm * 100) / 100} BPM`, ...(spec.key ? [spec.key] : [])] : [`${Math.round(bpm * 100) / 100} BPM`]),
      ...(s.styles ?? []),
      ...(instrumental ? ['instrumental'] : []),
    ].map(String);
    const neg = [...(spec.avoid ?? []), ...(s.avoid ?? []), ...(instrumental ? ['vocals', 'singing'] : [])].map(String);
    const name = String(s.name ?? `Section ${i + 1}`).slice(0, 60);
    chunks.push({ text: instrumental ? `[${name}]\n{instrumental, no vocals}` : `[${name}]\n${lines.join('\n')}`, duration_ms: ms, positive_styles: [...new Set(pos)], negative_styles: [...new Set(neg)] });
    if (!instrumental) lyrics.push({ section: name, startBar: bar, lines });
    bar += bars;
  });
  const totalMs = chunks.reduce((a, c) => a + c.duration_ms, 0);
  if (totalMs > 600_000) throw new Error('the song is over 10 minutes');
  return { plan: { chunks }, bpm, beatsPerBar: beats, barMs, bars: bar, totalMs, lyrics, vocals: lyrics.length > 0, warnings };
}

function plan(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  const specFile = flags.get('spec') ? resolve(String(flags.get('spec'))) : join(dir, 'spec.json');
  const spec = readJson(specFile, null);
  if (!spec) throw new Error(`no spec at ${specFile} (see references/COMPOSITION.md for its shape)`);
  if (specFile !== join(dir, 'spec.json')) writeJson(join(dir, 'spec.json'), spec);
  const p = buildPlan(spec);
  writeJson(join(dir, 'plan.json'), { title: spec.title ?? slug, bpm: p.bpm, key: spec.key ?? null, beatsPerBar: p.beatsPerBar, bars: p.bars, totalMs: p.totalMs, vocals: p.vocals, lyrics: p.lyrics, composition_plan: p.plan });
  const q = { status: 'unknown', next: 'Quote through the official ElevenLabs MCP before generation' };
  return { ok: true, command: 'plan', slug, seconds: p.totalMs / 1000, bars: p.bars, bpm: p.bpm, vocals: p.vocals, sections: p.plan.chunks.map((c) => ({ text: c.text.split('\n')[0], ms: c.duration_ms })), warnings: p.warnings, quote: q, file: rel(root, join(dir, 'plan.json')) };
}

/* ---------------------------------------------------------------- render */

/**
 * ElevenLabs' balance can lag a render by several seconds (measured: unchanged right after a render,
 * +445 a minute later). Wait up to ~40 s for it to move; null when it has not (the receipt then holds
 * the quote and is marked pending, and `reconcile` settles it later).
 */




/* ---------------------------------------------------------------- lyrics check */

const norm = (w) => String(w).toLowerCase().replace(/[’`]/g, "'").replace(/[^a-z0-9']/g, '').replace(/^'+|'+$/g, '');
const tokens = (text) => String(text).split(/\s+/).map(norm).filter(Boolean);

/** Longest common subsequence length of two token lists. */
function lcs(a, b) {
  const dp = new Array(b.length + 1).fill(0);
  for (let i = 1; i <= a.length; i++) {
    let prev = 0;
    for (let j = 1; j <= b.length; j++) { const t = dp[j]; dp[j] = a[i - 1] === b[j - 1] ? prev + 1 : Math.max(dp[j], dp[j - 1]); prev = t; }
  }
  return dp[b.length];
}

/** For each planned line: how much of it the transcript heard, in order. A line passes at 75 %. */
export function matchLyrics(lines, heardWords, { pass = 0.75 } = {}) {
  const heard = heardWords.map((w) => ({ ...w, t: norm(w.text ?? w.word ?? '') })).filter((w) => w.t);
  const seq = heard.map((w) => w.t);
  let at = 0;
  const rows = [];
  for (const line of lines) {
    const want = tokens(line);
    let best = { score: 0, from: at, to: at };
    const span = want.length * 2 + 6;
    for (let s = Math.max(0, at - 4); s <= Math.min(seq.length, at + 60); s++) {
      const got = lcs(want, seq.slice(s, s + span));
      if (got > best.score) best = { score: got, from: s, to: Math.min(seq.length, s + span) };
      if (got === want.length) break;
    }
    const frac = want.length ? best.score / want.length : 1;
    const window = heard.slice(best.from, best.to);
    const firstHit = window.find((w) => want.includes(w.t));
    rows.push({ line, heard: window.map((w) => w.text ?? w.word).join(' '), matched: +frac.toFixed(2), ok: frac >= pass, at: firstHit?.start ?? null });
    if (frac >= pass) at = best.from + Math.max(1, Math.round(best.score));
  }
  return rows;
}

/* ---------------------------------------------------------------- master */

function master(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  const last = readJson(join(dir, 'render.json'), null);
  const src = flags.get('in') ? resolve(String(flags.get('in'))) : last ? join(root, last.file) : null;
  if (!src || !existsSync(src)) throw new Error('nothing to master: render first, or --in <file>');
  const I = Number(flags.get('lufs') ?? -14); const TP = Number(flags.get('tp') ?? -1); const LRA = Number(flags.get('lra') ?? 11);
  const fadeOut = Number(flags.get('fade-out') ?? 0);
  const dur = probe(src).duration;
  const pre = ['highpass=f=24:poles=2', ...(fadeOut > 0 ? [`afade=t=out:st=${Math.max(0, dur - fadeOut).toFixed(3)}:d=${fadeOut}`] : [])].join(',');
  const measure = run('ffmpeg', ['-hide_banner', '-i', src, '-af', `${pre},loudnorm=I=${I}:TP=${TP}:LRA=${LRA}:print_format=json`, '-f', 'null', '-']);
  const text = measure.stderr;
  let m = {};
  try { m = JSON.parse(text.slice(text.lastIndexOf('{'), text.lastIndexOf('}') + 1)); } catch { /* reported below */ }
  if (!m.input_i) throw new Error('the loudness measurement failed');
  const wav = join(dir, `${slug}-master.wav`);
  const mp3 = join(dir, `${slug}.mp3`);
  const second = `${pre},loudnorm=I=${I}:TP=${TP}:LRA=${LRA}:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true,alimiter=limit=${(10 ** ((TP - 0.3) / 20)).toFixed(4)}:attack=3:release=60:level=false`;
  const a = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-af', second, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', wav]);
  if (a.code !== 0) throw new Error(`mastering failed: ${a.stderr.trim().split('\n').pop()}`);
  const b = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '256k', '-ar', '48000', mp3]);
  if (b.code !== 0) throw new Error(`the mp3 encode failed: ${b.stderr.trim().split('\n').pop()}`);
  const lw = loudness(wav); const lm = loudness(mp3);
  const out = { ok: Math.abs(lw.lufs - I) <= 1 && lm.truePeak <= TP + 0.6, command: 'master', slug, target: { lufs: I, truePeak: TP }, before: { lufs: Number(m.input_i), truePeak: Number(m.input_tp) }, master: { file: rel(root, wav), ...lw }, mp3: { file: rel(root, mp3), ...lm }, seconds: probe(mp3).duration };
  writeJson(join(dir, 'master.json'), out);
  return out;
}

/* ---------------------------------------------------------------- loop */

function f32(file, { start, duration, rate = 48000 }) {
  const r = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-ss', String(start), '-t', String(duration), '-i', file, '-ac', '2', '-ar', String(rate), '-f', 'f32le', '-']);
  if (r.code !== 0) throw new Error(`could not read ${file}: ${r.stderr.trim().split('\n').pop()}`);
  const b = r.stdout;
  return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength - (b.byteLength % 8)));
}

function loop(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  const p = readJson(join(dir, 'plan.json'), null);
  const src = flags.get('in') ? resolve(String(flags.get('in'))) : existsSync(join(dir, `${slug}-master.wav`)) ? join(dir, `${slug}-master.wav`) : null;
  if (!src) throw new Error('loop a mastered file (run master first) or --in <file>');
  const bpm = Number(flags.get('bpm') ?? p?.bpm);
  if (!(bpm > 0)) throw new Error('--bpm is needed (the plan has it when there is one)');
  const beatsPerBar = Number(flags.get('beats-per-bar') ?? p?.beatsPerBar ?? 4);
  const bars = Number(flags.get('bars'));
  if (!(Number.isInteger(bars) && bars >= 1)) throw new Error('--bars <n>: how many bars the loop holds');
  const fromBar = Number(flags.get('from-bar') ?? 0);
  const rate = 48000;
  const beat = 60 / bpm; const bar = beat * beatsPerBar;
  // Bar lines: the song's measured beat grid at the planned tempo; with a plan the render starts on a downbeat,
  // so the first bar line is the grid's phase folded into one beat.
  const grid = beatsOf(src, { bpm });
  const offset = flags.has('offset') ? Number(flags.get('offset')) : grid.phase % beat;
  const start = offset + fromBar * bar;
  const len = Math.round(bars * bar * rate);
  const xf = Math.round(Number(flags.get('crossfade-ms') ?? 30) / 1000 * rate);
  const dur = probe(src).duration;
  if (start + (len + xf) / rate > dur + 1e-3) throw new Error(`bars ${fromBar}..${fromBar + bars} (plus the crossfade) run past the end of the file (${dur.toFixed(2)} s)`);
  const seg = f32(src, { start: start.toFixed(6), duration: ((len + xf) / rate + 0.05).toFixed(6), rate });
  const out = new Float32Array(len * 2);
  out.set(seg.subarray(0, len * 2));
  // The tail that would follow the loop's end fades out over its head, so the wrap continues the music.
  for (let i = 0; i < xf; i++) {
    const gIn = Math.sin((Math.PI / 2) * (i / xf)); const gOut = Math.cos((Math.PI / 2) * (i / xf));
    for (let c = 0; c < 2; c++) out[i * 2 + c] = seg[i * 2 + c] * gIn + seg[(len + i) * 2 + c] * gOut;
  }
  // The seam: the jump at the wrap against the file's ordinary sample-to-sample steps.
  const steps = [];
  for (let i = 1; i < len; i += 97) steps.push(Math.abs(out[i * 2] - out[(i - 1) * 2]));
  steps.sort((a, b) => a - b);
  const typical = steps[Math.floor(steps.length * 0.99)] || 1e-6;
  const wrap = Math.max(Math.abs(out[0] - out[(len - 1) * 2]), Math.abs(out[1] - out[(len - 1) * 2 + 1]));
  const name = flags.get('name') ?? `${slug}-loop-${bars}bars`;
  const raw = join(dir, 'work', `${name}.f32`);
  writeFileSync(raw, Buffer.from(out.buffer));
  const wav = join(dir, `${name}.wav`); const ogg = join(dir, `${name}.ogg`);
  const w = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', String(rate), '-ac', '2', '-i', raw, '-c:a', 'pcm_s16le', wav]);
  // A compressed copy: Vorbis where ffmpeg has it, else Opus (both in Ogg, both decode to the exact length).
  let codec = 'vorbis';
  let o = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', String(rate), '-ac', '2', '-i', raw, '-c:a', 'libvorbis', '-q:a', '6', ogg]);
  if (o.code !== 0) { codec = 'opus'; o = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', String(rate), '-ac', '2', '-i', raw, '-c:a', 'libopus', '-b:a', '160k', ogg]); }
  rmSync(raw, { force: true });
  if (w.code !== 0) throw new Error(`the loop encode failed: ${w.stderr.trim()}`);
  // Played three times over, the beat must keep landing on the grid across both seams.
  const three = join(dir, 'work', `${name}-x3.wav`);
  run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-stream_loop', '2', '-i', wav, '-c:a', 'pcm_s16le', three]);
  const g3 = beatsOf(three, { bpm });
  const ph = ((g3.phase % beat) + beat) % beat;
  const drift = Math.min(ph, beat - ph); // the loop starts on a beat, so the grid of three passes sits at 0 (mod a beat)
  rmSync(three, { force: true });
  const seam = { wrapJump: +wrap.toFixed(4), typicalStep99: +typical.toFixed(4), ok: wrap <= typical * 1.5 };
  const res = {
    ok: seam.ok && o.code === 0, command: 'loop', slug, bars, fromBar, bpm, seconds: len / rate, samples: len, startInSource: +start.toFixed(4),
    files: { wav: rel(root, wav), ogg: o.code === 0 ? rel(root, ogg) : null }, oggCodec: o.code === 0 ? codec : null, seam, gridConfidenceLooped: g3.confidence, gridPhaseLoopedMs: Math.round(drift * 1000),
    playback: 'WebAudio: decode the WAV (or the OGG) and play it with source.loop = true; loopStart 0 and loopEnd at the full length. Never use an mp3 for a seamless loop: encoders add silence at the ends.',
  };
  writeJson(join(dir, `${name}.json`), res);
  return res;
}

/* ---------------------------------------------------------------- stems */

/* ---------------------------------------------------------------- reconcile */

/**
 * Settle pending receipts: the account's usage now, minus its usage before this song's first pending call,
 * is what those calls cost (plus anything else the account did meanwhile, which is said, not hidden).
 */


/* ---------------------------------------------------------------- analyze */

function analyze() {
  const file = resolve(String(pos[1] ?? ''));
  if (!existsSync(file)) throw new Error('usage: analyze <audio file>');
  const f = probe(file);
  const l = loudness(file);
  const g = beatsOf(file, { bpm: flags.has('bpm') ? Number(flags.get('bpm')) : null });
  const x = decodeMono(file, { rate: 8000 });
  let peak = 0; for (const v of x) peak = Math.max(peak, Math.abs(v));
  return { ok: true, command: 'analyze', file, seconds: f.duration, audio: f.audio, loudness: l, samplePeakDb: +(20 * Math.log10(peak + 1e-12)).toFixed(2), tempo: { bpm: g.bpm, confidence: g.tempoConfidence, phase: +g.phase.toFixed(4), phaseFrom: g.phaseFrom, firstBeats: g.beats.slice(0, 8) } };
}

/* ---------------------------------------------------------------- add / publish */

function add(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  const p = readJson(join(dir, 'plan.json'), null);
  const r = readJson(join(dir, 'render.json'), null);
  const m = readJson(join(dir, 'master.json'), null);
  const title = flags.get('title') ?? p?.title;
  if (!title) throw new Error('--title "<title>"');
  const files = [];
  const mp3 = join(dir, `${slug}.mp3`);
  if (!existsSync(mp3)) throw new Error(`music/${slug}/${slug}.mp3 is missing: master the render first`);
  files.push({ role: 'audio', path: rel(root, mp3), type: 'audio/mpeg', bytes: statSync(mp3).size });
  if (existsSync(join(dir, `${slug}-master.wav`))) files.push({ role: 'master', path: rel(root, join(dir, `${slug}-master.wav`)), type: 'audio/wav', public: false });
  for (const f of readdirSync(dir)) {
    const lj = /^(.*-loop-(\d+)bars)\.json$/.exec(f);
    if (!lj) continue;
    const info = readJson(join(dir, f), {});
    for (const [ext, type] of [['ogg', 'audio/ogg'], ['wav', 'audio/wav']]) {
      const lf = join(dir, `${lj[1]}.${ext}`);
      if (existsSync(lf)) files.push({ role: 'loop', name: `Loop, ${lj[2]} bars (${ext.toUpperCase()})`, path: rel(root, lf), type, bars: Number(lj[2]), bytes: statSync(lf).size, loopSeconds: info.seconds ?? null });
    }
  }
  if (existsSync(join(dir, 'stems'))) for (const f of readdirSync(join(dir, 'stems'))) files.push({ role: 'stem', name: f.replace(/\.[a-z0-9]+$/i, ''), path: rel(root, join(dir, 'stems', f)) });
  const cover = ['cover.jpg', 'cover.png', 'cover.webp'].map((c) => join(dir, c)).find(existsSync);
  if (cover) files.push({ role: 'cover', path: rel(root, cover) });
  const rights = r?.rights ?? null;
  const lyrics = p?.vocals ? p.lyrics.map((s) => s.lines.join('\n')).join('\n\n') : null;
  const entry = {
    slug, kind: flags.get('kind') ?? (flags.has('for-game') ? 'score' : 'song'), title: String(title), blurb: flags.get('blurb') ?? '',
    published: flags.has('publish'), duration: m?.seconds ?? r?.seconds ?? null, bpm: p?.bpm ?? null, key: p?.key ?? null,
    loudness: m ? { lufs: m.mp3.lufs, truePeak: m.mp3.truePeak } : null, files, lyrics,
    credits: flags.get('credits') ?? 'Music made with Eleven Music (ElevenLabs).',
    rights: rights ? { provider: 'elevenlabs', plan: rights.plan, commercial: rights.commercial, attribution: rights.attribution } : null,
    ...(flags.has('for-game') ? { for: { game: String(flags.get('for-game')) } } : {}),
    made: r ? { provider: 'elevenlabs', model: 'music_v2', at: r.at, receipt: rel(root, join(dir, 'budget.json')), songId: r.songId ?? null } : null,
  };
  const saved = upsertEntry(root, 'music', entry);
  return { ok: true, command: 'add', slug, published: saved.published, files: files.map((f) => `${f.role} ${f.path}${f.public === false ? ' (kept off the site)' : ''}`), manifest: 'music/manifest.json' };
}

function studioCli(root, args) {
  const bin = join(root, 'node_modules', '.bin', 'homie-studio');
  const r = spawnSync(bin, [...args, '--json'], { cwd: root, encoding: 'utf8', timeout: 15 * 60_000, maxBuffer: 64 * 1024 * 1024 });
  let j = null; try { j = JSON.parse(r.stdout); } catch { /* */ }
  return { code: r.status ?? 1, json: j, err: (r.stderr ?? '').trim() };
}

/** The studio's live address: its own domain, else the address its last deploy printed (kept on this computer). */
function liveSite(root, studio) {
  const cf = studio.cloudflare ?? {};
  if (cf.domain) return `https://${String(cf.domain).replace(/^https?:\/\//, '').replace(/\/+$/, '')}`;
  return cf.url ?? readJson(join(root, '.studio', 'local.json'), {})?.url ?? null;
}

/**
 * Publish a song or video: its page goes live. Big media goes to the studio's R2 when it has storage: from
 * @homie-rocks/studio 0.18.0 with `media move` (and every deploy), each file uploaded, read back and checked by SHA-256
 * before the site stops carrying it, at the same address; an older studio uploads with `media put` (/media/<key>).
 */
export async function publishEntry(root, kind, slug, { deploy = true } = {}) {
  const pages = studioHasMediaPages(root);
  if (!pages.ok) return { ok: false, command: 'publish', why: pages.why };
  const entry = getEntry(root, kind, slug);
  if (!entry) return { ok: false, command: 'publish', why: `no ${kind} entry "${slug}" (run add first)` };
  if (!entry.published) upsertEntry(root, kind, { slug, published: true });
  const studio = readJson(join(root, 'studio.json'), {});
  const hasR2 = Boolean(studio.cloudflare?.r2 && (studio.cloudflare?.created ?? []).includes(`r2:${studio.cloudflare.r2}`));
  const uploaded = [];
  let r2 = null;
  if (hasR2 && !pages.move) {
    for (const f of entry.files ?? []) {
      if (f.public === false || f.key || !f.path || !existsSync(join(root, f.path))) continue;
      const put = studioCli(root, ['media', 'put', f.path]);
      if (put.code !== 0 || !put.json?.ok) return { ok: false, command: 'publish', why: `uploading ${f.path} to R2 failed: ${put.json?.why ?? put.err.split('\n').pop()}` };
      uploaded.push(put.json.key);
    }
  }
  const site = liveSite(root, studio);
  if (!deploy || !site) {
    if (hasR2 && pages.move) {
      const mv = studioCli(root, ['media', 'move']);
      r2 = { moved: (mv.json?.moved ?? []).map((m) => m.path), failed: mv.json?.failed ?? [], ...(mv.json ? {} : { why: mv.err.split('\n').pop() }) };
    }
    const b = studioCli(root, ['build']);
    return { ok: b.code === 0, command: 'publish', slug, uploaded, ...(r2 ? { r2 } : {}), built: b.json?.[kind === 'music' ? 'songs' : 'videos'] ?? null, live: null, next: site ? 'deploy with `npm run deploy`' : 'the studio is not online yet: the publish skill puts it on its own Cloudflare (npm run deploy), and the page is then at /' + kind + '/' + slug + '/' };
  }
  // A 0.18.0 deploy moves the big media to R2 itself (checked by SHA-256) before it builds.
  const d = studioCli(root, ['deploy']);
  if (d.code !== 0 || !d.json?.ok) return { ok: false, command: 'publish', why: `deploy failed: ${d.json?.why ?? d.err.split('\n').pop()}`, needs: d.json?.needs ?? null };
  if (d.json.media) r2 = { moved: (d.json.media.moved ?? []).map((m) => m.path), failed: d.json.media.failed ?? [] };
  const page = `${d.json.url}/${kind}/${slug}/`;
  const check = await fetch(page).then((r) => r.status).catch(() => 0);
  const main = (entry.files ?? []).find((f) => f.role === (kind === 'music' ? 'audio' : 'video'));
  const fresh = getEntry(root, kind, slug);
  const mainNow = (fresh.files ?? []).find((f) => f.role === main?.role);
  // A file moved to R2 keeps its own address; only a `media put` key lives at /media/<key>.
  const mediaUrl = mainNow?.key ? `${d.json.url}/media/${mainNow.key}` : mainNow?.path ? `${d.json.url}/${mainNow.path.split('/').map(encodeURIComponent).join('/')}` : null;
  const media = mediaUrl ? await fetch(mediaUrl, { headers: { range: 'bytes=0-1023' } }).then((r) => r.status).catch(() => 0) : null;
  return { ok: check === 200 && (media === 206 || media === 200), command: 'publish', slug, uploaded, ...(r2 ? { r2 } : {}), page, pageStatus: check, media: mediaUrl, mediaStatus: media, from: mainNow?.r2 ? 'r2' : mainNow?.key ? 'r2 (/media/)' : 'site' };
}

/* ---------------------------------------------------------------- main */

function print(r) {
  if (asJson) { process.stdout.write(`${JSON.stringify(r, null, 2)}\n`); return; }
  if (r.ok === false && r.why) { process.stdout.write(`music: ${r.why}\n`); if (r.command !== 'lyrics') return; }
  const L = [];
  switch (r.command) {
    case 'check':
      if (r.plan) L.push(`Plan: ${r.plan.tier} (${r.plan.status}); ${r.plan.remaining} credits left of ${r.plan.limit}; resets ${r.plan.resetAt ?? '?'}; ${r.plan.canGoOver ? 'CAN go over (usage-based billing)' : 'cannot go over'}`);
      if (r.rights) L.push(`Rights: ${r.rights.words}`);
      L.push(`ffmpeg: ${r.ffmpeg ? 'yes' : 'NO'}`, `Studio: ${r.studio?.ok ? r.studio.root : r.studio?.why}${r.studio?.pages && !r.studio.pages.ok ? ` (song pages: ${r.studio.pages.why})` : ''}`);
      break;

    case 'plan':
      L.push(`Plan: ${r.seconds} s, ${r.bars} bars at ${r.bpm} BPM${r.vocals ? ', with vocals' : ', instrumental'}; quote through the official ElevenLabs MCP.`, ...r.sections.map((s) => `  ${s.text} ${s.ms} ms`), ...r.warnings.map((w) => `  warning: ${w}`), `Wrote ${r.file}`);
      break;


    case 'master':
      L.push(`Mastered to ${r.master.lufs} LUFS, ${r.master.truePeak} dBTP (target ${r.target.lufs} / ${r.target.truePeak}); the mp3 reads ${r.mp3.lufs} LUFS, ${r.mp3.truePeak} dBTP. ${r.master.file}, ${r.mp3.file}`);
      break;
    case 'loop':
      L.push(`Loop: ${r.bars} bars from bar ${r.fromBar}, ${r.seconds.toFixed(3)} s (${r.samples} samples at 48 kHz). Seam ${r.seam.ok ? 'clean' : 'AUDIBLE'} (jump ${r.seam.wrapJump} vs ${r.seam.typicalStep99}). ${r.files.wav}${r.files.ogg ? `, ${r.files.ogg}` : ''}`, r.playback);
      break;
    case 'analyze':
      L.push(`${r.seconds.toFixed(2)} s, ${r.loudness.lufs} LUFS, ${r.loudness.truePeak} dBTP; tempo ${r.tempo.bpm} BPM (confidence ${r.tempo.confidence}), first beat ${r.tempo.phase} s`);
      break;
    default:
      L.push(JSON.stringify(r, null, 2));
  }
  process.stdout.write(`${L.join('\n')}\n`);
}

async function main() {
  const cmd = pos[0];
  if (!cmd || cmd === 'help' || flags.has('help')) {
    process.stdout.write(`${readFileSync(new URL(import.meta.url), 'utf8').split('*/')[0].split('\n').slice(2).map((l) => l.replace(/^ \* ?/, '')).join('\n')}\n`);
    return null;
  }
  if (cmd === 'check') return check();
  if (cmd === 'analyze') return analyze();
  const root = requireStudio();
  if (cmd === 'budget') return budget(root);
  if (cmd === 'plan') return plan(root);
  if (cmd === 'master') return master(root);
  if (cmd === 'loop') return loop(root);
  if (cmd === 'add') return add(root);
  if (cmd === 'publish') return publishEntry(root, 'music', pos[1], { deploy: !flags.has('no-deploy') });
  return { ok: false, command: cmd, why: `unknown command "${cmd}" (music.mjs help)` };
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('music.mjs')) {
  try {
    const r = await main();
    if (r) { print(r); if (r.ok === false) process.exitCode = 1; }
  } catch (error) {
    print({ ok: false, why: error instanceof Error ? error.message : String(error) });
    process.exitCode = 1;
  }
}

