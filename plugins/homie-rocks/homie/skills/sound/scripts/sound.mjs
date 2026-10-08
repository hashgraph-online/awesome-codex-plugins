#!/usr/bin/env node
/**
 * sound.mjs: sound effects and synthesized music for a Homie studio, made on this computer.
 * No provider, no account, no money: every file is rendered from a JSON spec by plain JavaScript,
 * then measured (and encoded) with ffmpeg.
 *
 *   check                                   node, ffmpeg and its encoders, the studio
 *   presets                                 the effect presets, the instruments and the grooves
 *   sfx <set> [--kit arcade|platformer|shooter|party|ui] [--only a,b] [--spec file]
 *             [--style clean|retro|soft] [--variants n] [--for-game <id>]
 *                                           a set of effects: music/<set>/sfx/<name>-<v>.wav, sfx.json, a reel to listen to
 *   score <slug> --spec <score.json> [--lufs -14] [--loops a,b|all] [--loop-stems]
 *                                           a synthesized score: master, page mp3, stems, seamless section loops
 *   mix <slug> --spec <mix.json>            parts (files, ffmpeg aevalsrc expressions, effects) placed, panned, faded, summed
 *   analyze <file> [--kind sfx|music|capture] [--sheet out.png]
 *                                           loudness (also through a phone speaker), peaks, clipping, DC, late start,
 *                                           gaps, bands, stereo, onsets, hum: numbers and plain-words warnings
 *   wire <slug...> --game <id>              copy sets and loops into the game with sound.js (a player) and sound.json
 *   add <slug> --title "<Title>" [--blurb] [--for-game <id>] [--publish]
 *                                           the manifest entry, so the studio's site gets a page for it
 *   publish <slug>                          rebuild and redeploy the site (the music skill's publish)
 *
 * Every command takes --json. Run it from inside the studio (the folder with studio.json).
 */
import { spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, statfsSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { need, probe, run } from '../../music/scripts/lib/audio.mjs';
import { SLUG, findStudio, readJson, rel, upsertEntry, writeJson } from '../../music/scripts/lib/studio.mjs';
import { measure, r128, sheetPng, warnings } from './lib/measure.mjs';
import { INSTRUMENTS, loop as loopSection, master as masterMix, normalise, render as renderScore, seamWarning } from './lib/score.mjs';
import { KITS, LEVELS, PRESETS, renderEffect } from './lib/sfx.mjs';
import { RATE, addInto, dbToGain, dcBlock, levels as levelsOf, limit, peakOf, scale, stereo, wavBytes } from './lib/synth.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const flags = new Map();
const pos = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) { const k = a.slice(2); const v = argv[i + 1]; if (v === undefined || v.startsWith('--')) flags.set(k, true); else { flags.set(k, v); i++; } } else pos.push(a);
}
const JSON_OUT = flags.has('json');
const print = (o) => {
  if (JSON_OUT) { process.stdout.write(`${JSON.stringify(o, null, 2)}\n`); return; }
  if (o.ok === false) { process.stdout.write(`sound: ${o.why}\n`); return; }
  const lines = [];
  for (const [k, v] of Object.entries(o)) if (k !== 'ok' && k !== 'command') lines.push(`${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
  process.stdout.write(`${lines.join('\n')}\n`);
};

function studioRoot() {
  const root = findStudio();
  if (!root) throw new Error('not inside a Homie studio (no studio.json here or above). The studio-setup skill makes one.');
  return root;
}
function jobDir(root, slug) {
  if (!SLUG.test(String(slug ?? ''))) throw new Error('give a slug: lowercase letters, digits and hyphens (up to 40), e.g. "theme" or "gem-rush-sfx"');
  const d = join(root, 'music', slug);
  mkdirSync(d, { recursive: true });
  return d;
}
function freeGb(dir) { try { const f = statfsSync(dir); return (f.bavail * f.bsize) / 1e9; } catch { return 99; } }
function guardDisk(dir, needGb = 2) { if (freeGb(dir) < needGb + 8) throw new Error(`only ${freeGb(dir).toFixed(1)} GB free on this disk; free some space first (renders stop below 10 GB)`); }
const writeWav = (file, buf, opts) => { mkdirSync(dirname(file), { recursive: true }); writeFileSync(file, wavBytes(buf, opts)); return file; };

function encode(src, out, kind) {
  const args = ['-hide_banner', '-loglevel', 'error', '-y', '-i', src];
  if (kind === 'mp3') args.push('-c:a', 'libmp3lame', '-b:a', '192k', '-ar', '48000', out);
  else if (kind === 'ogg') {
    let r = run('ffmpeg', [...args, '-c:a', 'libvorbis', '-q:a', '6', out]);
    if (r.code === 0) return { file: out, codec: 'vorbis' };
    r = run('ffmpeg', [...args, '-c:a', 'libopus', '-b:a', '160k', out]);
    if (r.code !== 0) throw new Error(`ffmpeg could not encode ${out}: ${r.stderr.trim().split('\n').pop()}`);
    return { file: out, codec: 'opus' };
  }
  const r = run('ffmpeg', args);
  if (r.code !== 0) throw new Error(`ffmpeg could not encode ${out}: ${r.stderr.trim().split('\n').pop()}`);
  return { file: out, codec: kind };
}

/** Bring a stereo buffer to an integrated loudness (measured by ffmpeg's R128), peaks held under the ceiling. */
function toLoudness(buf, target, ceilingDb, work) {
  const tmp = join(work, `loud-${process.pid}.wav`);
  let lufs = null;
  for (let pass = 0; pass < 3; pass++) {
    writeWav(tmp, buf, { bits: 24 });
    lufs = r128(tmp).lufs;
    if (lufs === null || !Number.isFinite(lufs)) break;
    const d = target - lufs;
    if (Math.abs(d) < 0.4) break;
    scale(buf, dbToGain(d));
    limit(buf, { ceiling: dbToGain(ceilingDb), releaseMs: 150, lookaheadMs: 5 });
  }
  rmSync(tmp, { force: true });
  return buf;
}

/* ---------------------------------------------------------------- check / presets */

function check() {
  const ffmpeg = need('ffmpeg') && need('ffprobe');
  const enc = ffmpeg ? run('ffmpeg', ['-hide_banner', '-encoders']).stdout.toString() : '';
  const root = findStudio();
  const node = Number(process.versions.node.split('.')[0]);
  return {
    ok: ffmpeg && node >= 22, command: 'check', node: process.versions.node, ffmpeg,
    encoders: { mp3: /libmp3lame/.test(enc), vorbis: /libvorbis/.test(enc), opus: /libopus/.test(enc) },
    studio: root ? { root, games: existsSync(join(root, 'games')) ? readdirSync(join(root, 'games')).filter((d) => existsSync(join(root, 'games', d, 'game.json'))) : [] } : null,
    provider: 'none: everything is synthesized here, nothing is sent anywhere, nothing costs money',
    ...(ffmpeg ? {} : { why: 'ffmpeg is missing: brew install ffmpeg (macOS) or the system package; the person approves the install' }),
  };
}

function presets() {
  return {
    ok: true, command: 'presets',
    effects: Object.fromEntries(Object.entries(PRESETS).map(([k, v]) => [k, `${v.about} (${v.level})`])),
    kits: KITS, levels: LEVELS,
    instruments: Object.fromEntries(Object.entries(INSTRUMENTS).map(([k, v]) => [k, `${v.about} (${v.role})`])),
    grooves: ['four', 'backbeat', 'half', 'break', 'shuffle', 'hats', 'pulse', 'none'],
    patterns: ['root', 'root8', 'pulse', 'octaves', 'chords', 'stabs', 'arp', 'arp-down', 'arp-updown', 'or notes: "A4 . C5 - | E5*2 D5 C5 ."'],
  };
}

/* ---------------------------------------------------------------- sfx */

function sfxSpec() {
  if (flags.has('spec')) {
    const s = readJson(resolve(String(flags.get('spec'))), null);
    if (!s) throw new Error(`could not read ${flags.get('spec')} as JSON`);
    return s;
  }
  const kit = String(flags.get('kit') ?? 'arcade');
  const names = flags.has('only') ? String(flags.get('only')).split(',').map((x) => x.trim()).filter(Boolean) : KITS[kit];
  if (!names) throw new Error(`no kit "${kit}" (${Object.keys(KITS).join(', ')})`);
  return { style: flags.get('style') ?? 'clean', variants: Number(flags.get('variants') ?? 3), effects: names.map((n) => ({ name: n })) };
}

const ONE_TAKE = new Set(['win', 'lose', 'go', 'countdown', 'alarm', 'teleport', 'powerup', 'confirm', 'back', 'deny']);

function sfx(root) {
  const set = pos[1];
  const dir = jobDir(root, set);
  guardDisk(dir);
  const spec = sfxSpec();
  const style = flags.get('style') ?? spec.style ?? 'clean';
  const variants = Math.max(1, Math.min(8, Number(flags.get('variants') ?? spec.variants ?? 3)));
  const out = join(dir, 'sfx');
  rmSync(out, { recursive: true, force: true });
  mkdirSync(out, { recursive: true });
  const made = [];
  const reel = [];
  for (const [i, e] of (spec.effects ?? []).entries()) {
    if (!e?.name || !/^[a-z0-9][a-z0-9-]{0,39}$/.test(e.name)) throw new Error(`effect ${i + 1}: a name of lowercase letters, digits and hyphens`);
    const files = [];
    // Variants keep a sound heard over and over (a jump, a hit) from machine-gunning; a fanfare or a signal
    // heard once a round wants to be the same every time: one take.
    const takes = Math.max(1, Math.min(8, Number(e.variants ?? (ONE_TAKE.has(e.preset ?? e.name) ? 1 : variants))));
    for (let v = 1; v <= takes; v++) {
      // A variant: the same recipe a touch higher or lower and a little longer or shorter, with its own noise.
      const jitter = takes === 1 ? 0 : ((v - 1) / (takes - 1) - 0.5) * 1.2;
      const spec1 = { ...e, style: e.style ?? style, seed: (e.seed ?? 1) + v * 101, pitch: (e.pitch ?? 0) + jitter, length: (e.length ?? 1) * (1 + jitter * 0.05) };
      const { buf, facts } = renderEffect(spec1);
      const file = join(out, `${e.name}-${v}.wav`);
      writeWav(file, buf, { bits: 16, channels: e.stereo ? 2 : 1 });
      // An Ogg (Opus) copy a tenth the size; the WAV stays for browsers that cannot decode Ogg.
      const ogg = encode(file, file.replace(/\.wav$/, '.ogg'), 'ogg');
      files.push({ file: rel(root, file), ogg: rel(root, ogg.file), ...facts });
      if (v === 1) reel.push(buf);
    }
    made.push({ name: e.name, preset: e.preset ?? e.name, about: PRESETS[e.preset ?? e.name].about, files });
  }
  // A reel to listen to: every effect once, half a second apart.
  const gap = 0.5;
  const reelBuf = stereo(reel.reduce((a, b) => a + b.L.length / RATE + gap, 0.2));
  let at = 0.1;
  for (const b of reel) { addInto(reelBuf, b, { at }); at += b.L.length / RATE + gap; }
  const reelWav = writeWav(join(dir, 'work', `${set}-reel.wav`), reelBuf, { bits: 16 });
  encode(reelWav, join(dir, `${set}.mp3`), 'mp3');
  let sheet = null;
  try { sheet = rel(root, sheetPng(reelWav, join(dir, `${set}-reel.png`))); } catch { /* no picture, still fine */ }
  const checks = made.flatMap((m) => m.files.map((f) => ({ name: m.name, ...f }))).map((f) => {
    const m = measure(join(root, f.file), { silenceDb: -60 });
    return { file: f.file, warnings: warnings(m, 'sfx'), startMs: m.startMs, peakDb: m.samplePeakDb, under300: m.under300Share };
  });
  const info = { v: 1, kind: 'sfx', set, style, variants, at: new Date().toISOString(), made: 'synthesized on this computer by the Homie plugin\'s sound skill (no samples, no provider)', ...(flags.has('for-game') ? { for: { game: String(flags.get('for-game')) } } : {}), effects: made, spec: { ...spec, style, variants } };
  writeJson(join(dir, 'sfx.json'), info);
  const warn = checks.filter((c) => c.warnings.length);
  return {
    ok: true, command: 'sfx', set, style, variants, effects: made.map((m) => `${m.name}: ${m.files.length} file(s), ${m.files[0].seconds}s, loudest ${m.files[0].loudestDb} dB (${m.files[0].level})`),
    reel: rel(root, join(dir, `${set}.mp3`)), sheet, spec: rel(root, join(dir, 'sfx.json')),
    warnings: warn.length ? warn.map((c) => `${c.file}: ${c.warnings.join('; ')}`) : 'none: every file starts at once, no clipping, no DC',
    next: `look at ${sheet ?? 'the reel'}; then: node sound.mjs wire ${set} --game <id>`,
  };
}

/* ---------------------------------------------------------------- score */

function score(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  guardDisk(dir);
  const specPath = resolve(String(flags.get('spec') ?? join(dir, 'score.json')));
  const raw = readJson(specPath, null);
  if (!raw) throw new Error(`no score at ${specPath} (write one: references/SCORE.md)`);
  const s = normalise(raw);
  if (specPath !== join(dir, 'score.json')) writeJson(join(dir, 'score.json'), raw);
  const work = join(dir, 'work'); mkdirSync(work, { recursive: true });
  const lufs = Number(flags.get('lufs') ?? s.master?.lufs ?? -14);
  const t0 = Date.now();
  const r = renderScore(s);
  // Master: peaks under the ceiling, then to the loudness target, measured. Stems get the same gain.
  const before = peakOf(r.mix);
  const mix = masterMix(r.mix, { ceilingDb: -1.5 });
  toLoudness(mix, lufs, -1.2, work);
  const gain = peakOf(mix) / Math.max(1e-9, before);
  const masterWav = writeWav(join(dir, `${slug}-master.wav`), mix, { bits: 24 });
  encode(masterWav, join(dir, `${slug}.mp3`), 'mp3');
  const stemsDir = join(dir, 'stems'); rmSync(stemsDir, { recursive: true, force: true }); mkdirSync(stemsDir, { recursive: true });
  const stems = [];
  for (const [name, st] of Object.entries(r.stems)) {
    if (!(peakOf(st) > 1e-5)) continue;
    scale(st, gain);
    writeWav(join(stemsDir, `${name}.wav`), st, { bits: 16 });
    stems.push(name);
  }
  // Seamless loops of the sections asked for (default: the ones the score marks, else the longest).
  const want = flags.has('loops') ? String(flags.get('loops')) : (s.loops ?? []).join(',');
  const names = want === 'all' ? s.sections.map((x) => x.name) : want ? want.split(',').map((x) => x.trim()).filter(Boolean) : [s.sections.reduce((a, b) => (b.bars > a.bars ? b : a)).name];
  const loops = [];
  for (const name of names) {
    // The master's gain and limiter go on inside loopSection, across the three copies it cuts the loop from:
    // limiting the cut loop by itself puts a step of gain at the wrap.
    const lp = loopSection(s, name, { gain, ceilingDb: -1.2 });
    const base = `${slug}-${name}-loop-${lp.bars}bars`;
    const wav = writeWav(join(dir, `${base}.wav`), lp.mix, { bits: 16 });
    const ogg = encode(wav, join(dir, `${base}.ogg`), 'ogg');
    const seam = lp.seam;
    writeJson(join(dir, `${base}.json`), { section: name, bars: lp.bars, seconds: +lp.seconds.toFixed(6), bpm: s.bpm, beatsPerBar: s.beatsPerBar, seam, codec: ogg.codec });
    if (flags.has('loop-stems')) {
      for (const [st, b] of Object.entries(lp.stems)) { if (!(peakOf(b) > 1e-5)) continue; scale(b, gain); writeWav(join(dir, 'loops', name, `${st}.wav`), b, { bits: 16 }); }
    }
    loops.push({ section: name, bars: lp.bars, seconds: +lp.seconds.toFixed(3), seam, wav: rel(root, wav), ogg: rel(root, ogg.file) });
  }
  const m = measure(join(dir, `${slug}.mp3`));
  // A loop over the seam limit is a warning like any other: an empty list must mean the loops were checked and pass.
  const seamWarnings = loops.map((l) => seamWarning(l.section, l.seam)).filter(Boolean);
  const allWarnings = [...warnings(m, 'music'), ...seamWarnings];
  // plan.json: the bar grid, in the shape the video skill reads to cut a trailer on this music's bar lines.
  const plan = {
    title: s.title ?? slug, bpm: s.bpm, key: s.key ?? null, beatsPerBar: s.beatsPerBar, vocals: false, synthesized: true,
    sections: r.grid.sections.map((x) => ({ name: x.name, bars: x.bars, startMs: Math.round(x.at * 1000), durationMs: Math.round(x.bars * r.grid.barSeconds * 1000) })),
    totalMs: Math.round(r.grid.seconds * 1000),
  };
  writeJson(join(dir, 'plan.json'), plan);
  writeJson(join(dir, 'master.json'), { seconds: m.seconds, mp3: { lufs: m.loudness.lufs, truePeak: m.loudness.truePeakDb }, phoneLufs: m.loudness.phoneLufs });
  writeJson(join(dir, 'render.json'), { at: new Date().toISOString(), made: 'synthesized', seconds: m.seconds, grid: r.grid, loudness: m.loudness, stems, loops, warnings: allWarnings, renderMs: Date.now() - t0 });
  let sheet = null;
  try { sheet = rel(root, sheetPng(join(dir, `${slug}.mp3`), join(dir, `${slug}.png`))); } catch { /* */ }
  return {
    ok: true, command: 'score', slug, title: plan.title, seconds: m.seconds, bars: r.grid.bars, bpm: s.bpm,
    loudness: `${m.loudness.lufs} LUFS, true peak ${m.loudness.truePeakDb} dBTP, through a phone speaker ${m.loudness.phoneLufs} LUFS`,
    page: rel(root, join(dir, `${slug}.mp3`)), master: rel(root, masterWav), stems: stems.map((x) => `stems/${x}.wav`),
    loops: loops.map((l) => `${l.section}: ${l.bars} bars, ${l.seconds}s, seam ${l.seam} ${l.seam > 1 ? 'OVER 1: NOT SEAMLESS, see warnings' : '(1 or less is seamless)'} ${l.wav}`),
    loopsSeamless: seamWarnings.length === 0,
    sheet, warnings: allWarnings, renderMs: Date.now() - t0,
  };
}

/* ---------------------------------------------------------------- mix */

/** One part of a mix as a stereo buffer: a file, an ffmpeg aevalsrc expression, or an effect preset. */
function partBuffer(root, p, i) {
  const where = `part ${i + 1}`;
  if (p.effect) return renderEffect(typeof p.effect === 'string' ? { name: p.effect } : p.effect).buf;
  let input;
  if (p.file) {
    const f = resolve(root, String(p.file));
    if (!existsSync(f)) throw new Error(`${where}: no file ${p.file}`);
    input = ['-i', f];
  } else if (p.expr) {
    const exprs = Array.isArray(p.expr) ? p.expr : [p.expr];
    if (!(exprs.length === 1 || exprs.length === 2)) throw new Error(`${where}: expr is one expression (mono) or two (left, right)`);
    for (const e of exprs) {
      if (typeof e !== 'string' || !e.trim()) throw new Error(`${where}: an empty expression`);
      if (/['\\;[\]]/.test(e)) throw new Error(`${where}: an expression may not hold quotes, backslashes, semicolons or brackets (ffmpeg's filter parser takes them)`);
      if (e.length > 8000) throw new Error(`${where}: an expression over 8000 characters; split it into two parts (they sum the same)`);
      if (/[<>]=?/.test(e)) throw new Error(`${where}: aevalsrc has no comparison operators: use gte(a,b), lte(a,b), gt(a,b), lt(a,b)`);
    }
    if (!(Number(p.seconds) > 0 && Number(p.seconds) <= 600)) throw new Error(`${where}: an expression needs "seconds" (0..600)`);
    input = ['-f', 'lavfi', '-i', `aevalsrc=exprs=${exprs.map((e) => `'${e}'`).join('|')}:s=${RATE}:d=${Number(p.seconds)}${exprs.length === 2 ? ':c=stereo' : ''}`];
  } else throw new Error(`${where}: a part is { "file" } or { "expr", "seconds" } or { "effect" }`);
  const chain = [];
  if (p.from || p.seconds) chain.push(`atrim=${p.from ? `start=${Number(p.from)}` : 'start=0'}${p.file && p.seconds ? `:duration=${Number(p.seconds)}` : ''}`, 'asetpts=PTS-STARTPTS');
  if (p.filter) {
    if (/['\\;]/.test(String(p.filter))) throw new Error(`${where}: a filter may not hold quotes, backslashes or semicolons`);
    chain.push(String(p.filter));
  }
  const args = ['-hide_banner', '-loglevel', 'error', ...input, '-vn', '-ac', '2', '-ar', String(RATE)];
  if (chain.length) args.push('-af', chain.join(','));
  args.push('-f', 'f32le', '-');
  const r = run('ffmpeg', args);
  if (r.code !== 0) throw new Error(`${where}: ffmpeg said: ${r.stderr.trim().split('\n').pop()}`);
  const b = r.stdout;
  const all = new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength - (b.byteLength % 8)));
  const n = all.length / 2;
  const out = stereo(n / RATE);
  for (let k = 0; k < n; k++) { out.L[k] = all[2 * k]; out.R[k] = all[2 * k + 1]; }
  // An expression that exits 0 can still be NaN or silence (0*inf, a random() slot): say so, never mix it quietly.
  let bad = 0; for (let k = 0; k < n; k += 11) if (!Number.isFinite(out.L[k]) || !Number.isFinite(out.R[k])) bad++;
  if (bad) throw new Error(`${where}: the expression produced NaN samples (0*inf is NaN; write exp(-max(0,t-a)*k))`);
  if (!(peakOf(out) > 1e-6)) throw new Error(`${where}: rendered silence (exit code 0 is not audio: check the expression's envelope and slots)`);
  return out;
}

function mix(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  guardDisk(dir);
  const spec = readJson(resolve(String(flags.get('spec') ?? join(dir, 'mix.json'))), null);
  if (!spec?.parts?.length) throw new Error('a mix spec is { "parts": [ { "file" | "expr"+"seconds" | "effect", "at", "db", "pan", "fadeIn", "fadeOut", "repeat", "every", "filter" } ], "master": { "lufs" } }');
  const placed = [];
  for (const [i, p] of spec.parts.entries()) {
    const buf = partBuffer(root, p, i);
    const repeat = Math.max(1, Math.min(512, Number(p.repeat ?? 1)));
    const every = Number(p.every ?? buf.L.length / RATE);
    const fi = Math.round(Number(p.fadeIn ?? 0) * RATE); const fo = Math.round(Number(p.fadeOut ?? 0) * RATE);
    for (let k = 0; k < fi && k < buf.L.length; k++) { const g = k / fi; buf.L[k] *= g; buf.R[k] *= g; }
    for (let k = 0; k < fo && k < buf.L.length; k++) { const g = k / fo; buf.L[buf.L.length - 1 - k] *= g; buf.R[buf.R.length - 1 - k] *= g; }
    for (let k = 0; k < repeat; k++) placed.push({ buf, at: Number(p.at ?? 0) + k * every, gain: dbToGain(Number(p.db ?? 0)), pan: Number(p.pan ?? 0), i });
  }
  const length = Math.max(...placed.map((p) => p.at + p.buf.L.length / RATE)) + Number(spec.tail ?? 0);
  const out = stereo(length);
  // Summed at the levels written: no automatic normalisation (ffmpeg's amix divides by the number of inputs by default).
  for (const p of placed) {
    if (p.pan) {
      const g = p.pan; const l = Math.cos((g + 1) * Math.PI / 4) * Math.SQRT2; const r = Math.sin((g + 1) * Math.PI / 4) * Math.SQRT2;
      const off = Math.round(p.at * RATE);
      for (let k = 0; k < p.buf.L.length && off + k < out.L.length; k++) { out.L[off + k] += p.buf.L[k] * p.gain * l; out.R[off + k] += p.buf.R[k] * p.gain * r; }
    } else addInto(out, p.buf, { at: p.at, gain: p.gain });
  }
  dcBlock(out);
  const work = join(dir, 'work'); mkdirSync(work, { recursive: true });
  const peakBefore = levelsOf(out).peakDb;
  limit(out, { ceiling: dbToGain(spec.master?.ceilingDb ?? -1.5), releaseMs: 120 });
  if (spec.master?.lufs !== undefined) toLoudness(out, Number(spec.master.lufs), spec.master?.ceilingDb ?? -1.2, work);
  const wav = writeWav(join(dir, `${slug}-master.wav`), out, { bits: 24 });
  encode(wav, join(dir, `${slug}.mp3`), 'mp3');
  const m = measure(wav);
  writeJson(join(dir, 'master.json'), { seconds: m.seconds, mp3: { lufs: m.loudness.lufs, truePeak: m.loudness.truePeakDb } });
  return { ok: true, command: 'mix', slug, parts: spec.parts.length, placed: placed.length, seconds: m.seconds, peakBeforeLimiterDb: peakBefore, loudness: m.loudness, master: rel(root, wav), page: rel(root, join(dir, `${slug}.mp3`)), warnings: warnings(m, 'music') };
}

/* ---------------------------------------------------------------- analyze */

function analyze() {
  const file = resolve(String(pos[1] ?? ''));
  if (!existsSync(file)) throw new Error('usage: analyze <audio file> [--kind sfx|music|capture] [--sheet out.png]');
  const kind = String(flags.get('kind') ?? (probe(file).duration < 3 ? 'sfx' : 'music'));
  const m = measure(file);
  let sheet = null;
  if (flags.has('sheet')) sheet = sheetPng(file, resolve(String(flags.get('sheet') === true ? file.replace(/\.[a-z0-9]+$/i, '.png') : flags.get('sheet'))));
  return { ok: true, command: 'analyze', kind, ...m, warnings: warnings(m, kind), sheet };
}

/* ---------------------------------------------------------------- wire */

function gameMode(gameDir) {
  const g = readJson(join(gameDir, 'game.json'), {});
  return g.build?.mode === 'static' ? 'static' : 'bundle';
}

function wire(root) {
  const game = String(flags.get('game') ?? '');
  const gameDir = join(root, 'games', game);
  if (!game || !existsSync(join(gameDir, 'game.json'))) throw new Error('--game <id>: a game in this studio (games/<id>/game.json)');
  const slugs = pos.slice(1);
  if (!slugs.length) throw new Error('usage: wire <sfx set or score slug...> --game <id>');
  const mode = gameMode(gameDir);
  const assets = mode === 'static' ? join(gameDir, 'sound') : join(gameDir, 'public', 'sound');
  mkdirSync(assets, { recursive: true });
  const manifest = readJson(join(assets, 'sound.json'), { v: 1, sfx: {}, music: {} });
  let bytes = 0;
  const copied = [];
  const seams = [];
  for (const slug of slugs) {
    const dir = join(root, 'music', slug);
    const sfxInfo = readJson(join(dir, 'sfx.json'), null);
    if (sfxInfo) {
      for (const e of sfxInfo.effects) {
        // Each variant as [ogg, wav]: sound.js plays the first this browser decodes.
        manifest.sfx[e.name] = e.files.map((f) => [f.ogg, f.file].filter((x) => x && existsSync(join(root, x))).map((x) => { const b = basename(x); copyFileSync(join(root, x), join(assets, b)); bytes += statSync(join(assets, b)).size; copied.push(b); return b; }));
      }
      continue;
    }
    const plan = readJson(join(dir, 'plan.json'), null);
    const loopsFound = existsSync(dir) ? readdirSync(dir).filter((f) => /-loop-\d+bars\.wav$/.test(f)) : [];
    if (plan && loopsFound.length) {
      const loops = {};
      for (const f of loopsFound) {
        const info = readJson(join(dir, f.replace(/\.wav$/, '.json')), {});
        const name = info.section ?? 'main';
        const sw = seamWarning(name, info.seam);
        if (sw) seams.push(`music/${slug}: ${sw}`);
        // Ogg first (a tenth of the bytes), the WAV for a browser that cannot decode Ogg: sound.js takes the first that decodes.
        const list = [];
        for (const g of [f.replace(/\.wav$/, '.ogg'), f]) {
          if (!existsSync(join(dir, g))) continue;
          copyFileSync(join(dir, g), join(assets, g)); bytes += statSync(join(assets, g)).size; copied.push(g); list.push(g);
        }
        loops[name] = list;
      }
      // Order: the plan's section order, so music('<slug>') starts with the first section.
      const ordered = Object.fromEntries(plan.sections.map((x) => x.name).filter((n, i, a) => loops[n] && a.indexOf(n) === i).map((n) => [n, loops[n]]));
      for (const [k, v] of Object.entries(loops)) if (!ordered[k]) ordered[k] = v;
      manifest.music[slug] = { bpm: plan.bpm, beatsPerBar: plan.beatsPerBar ?? 4, barSeconds: (60 / plan.bpm) * (plan.beatsPerBar ?? 4), loops: ordered };
      continue;
    }
    throw new Error(`music/${slug}: neither an effect set (sfx.json) nor a score with loops (make loops with: score ${slug} --loops <sections>, or music.mjs loop)`);
  }
  writeJson(join(assets, 'sound.json'), manifest);
  const sizeOf = (f) => (existsSync(join(assets, f)) ? statSync(join(assets, f)).size : 0);
  const downloadBytes = Object.values(manifest.sfx).flat().reduce((a, f) => a + sizeOf(Array.isArray(f) ? f[0] : f), 0)
    + Object.values(manifest.music).flatMap((t) => Object.values(t.loops)).reduce((a, l) => a + sizeOf(Array.isArray(l) ? l[0] : l), 0);
  const playerSrc = join(HERE, 'player', 'sound.js');
  const playerDest = mode === 'static' ? join(assets, 'sound.js') : join(gameDir, 'src', 'sound.js');
  mkdirSync(dirname(playerDest), { recursive: true });
  copyFileSync(playerSrc, playerDest);
  copyFileSync(join(HERE, 'player', 'sound.d.ts'), playerDest.replace(/\.js$/, '.d.ts'));
  const importLine = mode === 'static'
    ? `<script type="module">import { createSound } from './sound/sound.js'; window.sound = createSound({ base: 'sound/' });</script>`
    : `import { createSound } from './sound.js';\nconst sound = createSound({ base: 'sound/' });`;
  return {
    ok: true, command: 'wire', game, mode, files: copied.length, kb: Math.round(bytes / 1024), manifest: rel(root, join(assets, 'sound.json')), player: rel(root, playerDest),
    sfx: Object.keys(manifest.sfx), music: Object.fromEntries(Object.entries(manifest.music).map(([k, v]) => [k, Object.keys(v.loops)])),
    add: importLine,
    then: 'call sound.play(\'<name>\') where the action happens (the host AND every replica: each browser plays its own sound for what it sees), sound.music(\'<slug>\') once at start, sound.section(\'<name>\') when the game\'s intensity changes. Build, then prove it with the playtest skill (its sound row captures what the game really plays).',
    warnings: seams,
    download: `about ${Math.round(downloadBytes / 1024)} KB for a browser that decodes Ogg (the WAV copies are only fetched when it cannot)`,
    ...(downloadBytes > 3 * 1024 * 1024 ? { note: `${Math.round(downloadBytes / 1024 / 1024)} MB of sound: phones download it before the first round; fewer variants or shorter loops` } : {}),
  };
}

/* ---------------------------------------------------------------- add / publish */

function add(root) {
  const slug = pos[1];
  const dir = jobDir(root, slug);
  const sfxInfo = readJson(join(dir, 'sfx.json'), null);
  const plan = readJson(join(dir, 'plan.json'), null);
  const m = readJson(join(dir, 'master.json'), null);
  const title = flags.get('title') ?? plan?.title;
  if (!title || title === true) throw new Error('--title "<title>"');
  const files = [];
  const mp3 = join(dir, `${slug}.mp3`);
  if (!existsSync(mp3)) throw new Error(`music/${slug}/${slug}.mp3 is missing: render it first (sfx, score or mix)`);
  files.push({ role: 'audio', path: rel(root, mp3), type: 'audio/mpeg', bytes: statSync(mp3).size });
  if (existsSync(join(dir, `${slug}-master.wav`))) files.push({ role: 'master', path: rel(root, join(dir, `${slug}-master.wav`)), type: 'audio/wav', public: false });
  for (const f of readdirSync(dir)) {
    const lj = /^(.*-loop-(\d+)bars)\.json$/.exec(f);
    if (!lj) continue;
    const info = readJson(join(dir, f), {});
    const wav = join(dir, `${lj[1]}.wav`);
    if (existsSync(wav)) files.push({ role: 'loop', name: `Loop: ${info.section ?? 'section'}, ${lj[2]} bars`, path: rel(root, wav), type: 'audio/wav', bars: Number(lj[2]), bytes: statSync(wav).size, loopSeconds: info.seconds ?? null });
  }
  if (sfxInfo) for (const e of sfxInfo.effects) { const f = e.files[0]; files.push({ role: 'stem', name: `${e.name} (${e.files.length} variant${e.files.length > 1 ? 's' : ''})`, path: f.file, type: 'audio/wav', bytes: statSync(join(root, f.file)).size }); }
  else if (existsSync(join(dir, 'stems'))) for (const f of readdirSync(join(dir, 'stems')).sort()) files.push({ role: 'stem', name: f.replace(/\.wav$/, ''), path: rel(root, join(dir, 'stems', f)), type: 'audio/wav', bytes: statSync(join(dir, 'stems', f)).size });
  const cover = ['cover.jpg', 'cover.png', 'cover.webp'].map((c) => join(dir, c)).find(existsSync);
  if (cover) files.push({ role: 'cover', path: rel(root, cover) });
  const kind = sfxInfo ? 'sfx' : flags.has('for-game') ? 'score' : 'song';
  const forGame = flags.get('for-game') ?? sfxInfo?.for?.game ?? null;
  const entry = {
    slug, kind, title: String(title), blurb: flags.get('blurb') === true ? '' : String(flags.get('blurb') ?? ''),
    published: flags.has('publish'), duration: m?.seconds ?? null, bpm: plan?.bpm ?? null, key: plan?.key ?? null,
    loudness: m?.mp3 ? { lufs: m.mp3.lufs, truePeak: m.mp3.truePeak } : null, files, lyrics: null,
    credits: flags.get('credits') ?? (sfxInfo ? 'Sound effects synthesized from code by the studio: no samples, no AI model.' : 'Synthesized from a written score by the studio: no samples, no AI model.'),
    rights: { provider: 'none', commercial: null, attribution: null },
    ...(forGame ? { for: { game: String(forGame) } } : {}),
    made: { provider: 'local', model: 'synthesized (the Homie plugin\'s sound skill)', at: new Date().toISOString(), spec: rel(root, join(dir, sfxInfo ? 'sfx.json' : existsSync(join(dir, 'score.json')) ? 'score.json' : 'mix.json')) },
  };
  const saved = upsertEntry(root, 'music', entry);
  return { ok: true, command: 'add', slug, kind, published: saved.published, files: files.map((f) => `${f.role} ${f.path}${f.public === false ? ' (kept off the site)' : ''}`), manifest: 'music/manifest.json' };
}

function publish(root) {
  const slug = pos[1];
  const r = spawnSync(process.execPath, [join(HERE, '..', '..', 'music', 'scripts', 'music.mjs'), 'publish', slug, '--json', ...(flags.has('no-deploy') ? ['--no-deploy'] : [])], { cwd: root, encoding: 'utf8', timeout: 20 * 60_000, maxBuffer: 64 * 1024 * 1024 });
  try { return JSON.parse(r.stdout); } catch { return { ok: false, command: 'publish', why: (r.stdout + r.stderr).trim().split('\n').slice(-3).join(' ') }; }
}

/* ---------------------------------------------------------------- main */

async function main() {
  const cmd = pos[0];
  if (!cmd || cmd === 'help' || flags.has('help')) {
    const head = readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0];
    return { ok: true, command: 'help', usage: head.replace(/^#!.*\n\/\*\*?/, '').replace(/^ \* ?/gm, '').trim() };
  }
  if (cmd === 'check') return check();
  if (cmd === 'presets') return presets();
  if (cmd === 'analyze') return analyze();
  const root = studioRoot();
  if (cmd === 'sfx') return sfx(root);
  if (cmd === 'score') return score(root);
  if (cmd === 'mix') return mix(root);
  if (cmd === 'wire') return wire(root);
  if (cmd === 'add') return add(root);
  if (cmd === 'publish') return publish(root);
  return { ok: false, command: cmd, why: `unknown command "${cmd}" (sound.mjs help)` };
}

try {
  const r = await main();
  if (r) { print(r); if (r.ok === false) process.exitCode = 1; }
} catch (error) {
  print({ ok: false, why: error instanceof Error ? error.message : String(error) });
  process.exitCode = 1;
}
