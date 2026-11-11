// score.ts: a trailer score written in code (no samples, no credits): a music bed on the director's
// BPM shaped by the shot roles, plus game sounds placed on the frames where capture.ts saw them.
//
//   bun scripts/score.ts director.json                 -> music.wav + sfx.wav beside the director
//   bun scripts/score.ts director.json --key A --out-dir sound/
//   then: bun scripts/cut.ts director.json --music music.wav --sfx sfx.wav
//
// Needs "bpm" in the director and capture/manifest.json (for shot lengths and the events list).
// Roles drive the arrangement: establishing = drone + pad; mechanic = + pulse; escalation = + hats
// and bass; a riser into "hero"; an impact on "hero", on every "gate" event and on "title"; "end" = pad out.
// Events: "spark" -> a chime that climbs with the chain, "gate" -> whoosh + chord, "hit" -> thud,
// anything else -> a soft tick. Use a varg music track instead when you want a real composition
// (SKILL.md, step 4); keep sfx.wav either way.
import { readFile } from 'node:fs/promises';
import { dirname, resolve, join } from 'node:path';

const argv = process.argv.slice(2);
const opt = (n: string, d: string) => { const i = argv.indexOf(`--${n}`); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const directorPath = argv.find((a) => a.endsWith('.json'));
if (!directorPath) { console.error('usage: bun scripts/score.ts director.json [--out-dir dir] [--key A]'); process.exit(1); }
const D = JSON.parse(await readFile(directorPath, 'utf8'));
const base = dirname(resolve(directorPath));
const capDir = resolve(opt('capture', join(base, 'capture')));
const M = JSON.parse(await readFile(join(capDir, 'manifest.json'), 'utf8'));
const outDir = resolve(opt('out-dir', base));
const bpm = D.music?.bpm ?? D.bpm;
if (!bpm) throw new Error('set "bpm" in the director');
const SR = 48000, beat = 60 / bpm, fps = M.fps;
const KEYS: Record<string, number> = { A: 0, B: 2, C: 3, D: 5, E: 7, F: 8, G: 10 };
const root = 55 * Math.pow(2, (KEYS[opt('key', 'A')] ?? 0) / 12); // A1 = 55 Hz

// timeline from the capture (frame-exact, the same numbers cut.ts uses)
let t = 0;
const tl = D.shots.map((s: any) => { const m = M.shots.find((x: any) => x.id === s.id); const r = { ...s, ...m, start: t, end: t + m.frames / fps }; t = r.end; return r; });
const T = t + 0.5, N = Math.ceil(T * SR);
const music = [new Float32Array(N), new Float32Array(N)], sfx = [new Float32Array(N), new Float32Array(N)], wet = [new Float32Array(N), new Float32Array(N)];
let seed = 12345; const noise = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 2147483648 - 1; };
const roleAt = (x: number) => (tl.find((s: any) => x >= s.start && x < s.end) || tl[tl.length - 1]).role ?? 'mechanic';
const add = (buf: Float32Array[], i: number, v: number, pan = 0, w = 0) => {
  if (i < 0 || i >= N) return;
  buf[0][i] += v * (1 - pan) * 0.5 * 2; buf[1][i] += v * (1 + pan) * 0.5 * 2;
  if (w) { wet[0][i] += v * w; wet[1][i] += v * w; }
};
const midi = (semi: number) => root * Math.pow(2, semi / 12);

// ---------- pad + bass: i - VI - III - VII (Am F C G in A), one chord per bar ----------
const CHORDS = [[12, 15, 19], [8, 12, 15], [15, 19, 22], [10, 14, 17]];
let lp = [0, 0];
for (let i = 0; i < N; i++) {
  const x = i / SR, bar = Math.floor(x / (beat * 4)), ch = CHORDS[bar % 4], role = roleAt(x);
  const inBar = (x % (beat * 4)) / (beat * 4), env = Math.min(1, inBar * 8) * (1 - Math.max(0, inBar - 0.9) * 6);
  const level = role === 'establishing' ? 0.5 : role === 'end' ? 0.55 : role === 'title' ? 0.7 : 0.45;
  for (let c = 0; c < 2; c++) {
    let v = 0;
    for (const n of ch) for (const det of [-0.07, 0.07]) { const f = midi(n + 12 + det + (c ? 0.03 : 0)); v += ((x * f) % 1) * 2 - 1; }
    const cutoff = role === 'escalation' || role === 'hero' ? 0.12 : 0.05;
    lp[c] += cutoff * (v - lp[c]);
    music[c][i] += lp[c] * 0.05 * level * env;
    wet[c][i] += lp[c] * 0.03 * level * env;
  }
  const bass = Math.sin(2 * Math.PI * midi(ch[0] - 12) * x) * (role === 'establishing' ? 0.18 : 0.3) * Math.min(1, x / 2);
  add(music, i, bass * 0.5);
}

// ---------- drums by role ----------
const kick = (at: number, g = 1) => { let ph = 0; for (let k = 0; k < 0.45 * SR; k++) { const x = k / SR; ph += (45 + 95 * Math.exp(-x * 28)) / SR; add(music, Math.round(at * SR) + k, Math.sin(2 * Math.PI * ph) * Math.exp(-x * 8) * 0.55 * g); } };
const hat = (at: number, g = 1) => { let p = 0; for (let k = 0; k < 0.06 * SR; k++) { const n = noise(), h = n - p; p = n; add(music, Math.round(at * SR) + k, h * Math.exp(-k / SR * 70) * 0.08 * g, 0.3); } };
for (let b = 0; b * beat < t; b++) {
  const x = b * beat, role = roleAt(x + 1e-3);
  if (role === 'mechanic') kick(x, b % 2 ? 0.6 : 0.9);
  if (role === 'escalation') { kick(x, 1); hat(x + beat / 2); hat(x + beat / 4, 0.5); hat(x + 3 * beat / 4, 0.5); }
}

// ---------- riser into the hero shot, impacts ----------
const boom = (at: number, g = 1) => {
  let ph = 0, lpn = 0;
  for (let k = 0; k < 3.2 * SR; k++) {
    const x = k / SR; ph += (32 + 40 * Math.exp(-x * 6)) / SR; lpn += 0.08 * (noise() - lpn);
    const v = Math.sin(2 * Math.PI * ph) * Math.exp(-x * 1.6) * 0.9 + lpn * Math.exp(-x * 10) * 1.2
      + (Math.sin(2 * Math.PI * midi(48) * x) + Math.sin(2 * Math.PI * midi(55) * x)) * 0.05 * Math.exp(-x * 1.2);
    add(music, Math.round(at * SR) + k, v * g, 0, 0.35);
  }
};
for (const s of tl) {
  if (s.role === 'hero') { // the riser lands on the game's own big moment (first gate event), else on the cut
    const ev = (s.events || []).find((e: any) => e.type === 'gate'), hit = ev ? s.start + ev.frame / fps : s.start;
    const len = Math.min(4 * beat, hit), a = hit - len; let lpn = 0;
    for (let k = 0; k < len * SR; k++) { const u = k / (len * SR); lpn += (0.01 + 0.4 * u * u) * (noise() - lpn); add(music, Math.round(a * SR) + k, (lpn * 0.5 + Math.sin(2 * Math.PI * (200 + 600 * u * u) * k / SR) * 0.03) * u * u, 0, 0.2); }
    if (!ev) boom(hit, 0.8); // a gate event booms below, with the game sounds
  }
  if (s.role === 'title') boom(s.start, 1);
}

// ---------- game sounds from the capture's events ----------
const PENTA = [0, 3, 5, 7, 10];
let chain = 0;
for (const s of tl) for (const e of s.events || []) {
  const at = s.start + e.frame / fps, i0 = Math.round(at * SR), pan = Math.sin(at * 7) * 0.4;
  if (e.type === 'spark') {
    chain++; const n = 36 + 12 * Math.floor(chain / 5 % 2) + PENTA[chain % 5], f = midi(n);
    for (let k = 0; k < 0.5 * SR; k++) { const x = k / SR; add(sfx, i0 + k, (Math.sin(2 * Math.PI * f * x) + 0.3 * Math.sin(4 * Math.PI * f * x)) * Math.exp(-x * 9) * 0.12, pan, 0.4); }
  } else if (e.type === 'gate') {
    let lpn = 0;
    for (let k = 0; k < 1.6 * SR; k++) { const x = k / SR; lpn += 0.15 * (noise() - lpn);
      const chord = [24, 31, 36, 40].reduce((v, n) => v + Math.sin(2 * Math.PI * midi(n + 12) * x), 0);
      add(sfx, i0 + k, lpn * Math.exp(-x * 3) * 0.6 + chord * 0.05 * Math.exp(-x * 1.5), 0, 0.5); }
    boom(at, 0.6);
  } else if (e.type === 'hit') {
    for (let k = 0; k < 0.4 * SR; k++) { const x = k / SR; add(sfx, i0 + k, Math.sin(2 * Math.PI * 70 * x) * Math.exp(-x * 14) * 0.5 + noise() * Math.exp(-x * 40) * 0.2, pan); }
  } else {
    for (let k = 0; k < 0.05 * SR; k++) add(sfx, i0 + k, noise() * Math.exp(-k / SR * 80) * 0.08, pan);
  }
  if (e.type !== 'spark') chain = 0;
}

// ---------- reverb (Schroeder: 4 combs + 2 allpasses per side) on the wet send ----------
function reverb(x: Float32Array, spread: number) {
  const y = new Float32Array(N);
  for (const d of [1557, 1617, 1491, 1422].map((v) => Math.round((v + spread) * SR / 44100))) {
    const buf = new Float32Array(d); let p = 0, f = 0;
    for (let i = 0; i < N; i++) { const o = buf[p]; f = o * 0.7 + f * 0.3; buf[p] = x[i] + f * 0.8; p = (p + 1) % d; y[i] += o * 0.25; }
  }
  for (const d of [225, 556].map((v) => Math.round((v + spread) * SR / 44100))) {
    const buf = new Float32Array(d); let p = 0;
    for (let i = 0; i < N; i++) { const o = buf[p]; const v = y[i] + o * 0.5; buf[p] = v; y[i] = o - v * 0.5; p = (p + 1) % d; }
  }
  return y;
}
const rv = [reverb(wet[0], 0), reverb(wet[1], 23)];
for (let c = 0; c < 2; c++) for (let i = 0; i < N; i++) {
  const fadeIn = Math.min(1, i / (SR * 0.8)), fadeOut = Math.min(1, (N - i) / (SR * 1.2));
  music[c][i] = Math.tanh((music[c][i] + rv[c][i] * 0.6) * 0.9) * fadeIn * fadeOut;
  sfx[c][i] = Math.tanh(sfx[c][i]) * fadeOut;
}

function wav(ch: Float32Array[]) {
  const n = ch[0].length, buf = new ArrayBuffer(44 + n * 4), v = new DataView(buf);
  const s = (o: number, str: string) => { for (let i = 0; i < str.length; i++) v.setUint8(o + i, str.charCodeAt(i)); };
  s(0, 'RIFF'); v.setUint32(4, 36 + n * 4, true); s(8, 'WAVE'); s(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
  v.setUint16(22, 2, true); v.setUint32(24, SR, true); v.setUint32(28, SR * 4, true); v.setUint16(32, 4, true); v.setUint16(34, 16, true);
  s(36, 'data'); v.setUint32(40, n * 4, true);
  for (let i = 0; i < n; i++) for (let c = 0; c < 2; c++) v.setInt16(44 + i * 4 + c * 2, Math.max(-1, Math.min(1, ch[c][i])) * 32767, true);
  return new Uint8Array(buf);
}
await Bun.write(join(outDir, 'music.wav'), wav(music));
await Bun.write(join(outDir, 'sfx.wav'), wav(sfx));
const evs = tl.reduce((n: number, s: any) => n + (s.events?.length || 0), 0);
console.log(`music.wav + sfx.wav -> ${outDir}  (${t.toFixed(2)} s, ${bpm} BPM, ${evs} game events)`);
