// Offline audio analysis for the silk-ribbons scene, following the audio-visualizer reference "Timing and numbers":
//   44.1 kHz mono, FFT 4096 with a Hann window centred on each frame (30 fps -> 1470-sample hop),
//   32 log-spaced bands 30 Hz–16 kHz, dB = 20·log10(mag) clamped −100…−30 dB -> 0…1,
//   per-band normalisation to the track's 98th percentile, attack 1 frame / release tau 0.45 s (ribbons).
// Writes the frames used by the ribbons scene straight into compositions/ribbons.html (between the AUDIO markers),
// so the render never fetches anything at runtime.
//   bun tools/analyze-audio.ts            (from examples/demo, after tools/make-beat.sh)
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";

const SR = 44100;
const FPS = 30;
const N = 4096;
const BANDS = 32;
const TAU = 0.45;
const SCENE_START = 12.5; // ribbons scene in the film
const SCENE_END = 16.0;

const raw = execFileSync("ffmpeg", ["-v", "error", "-i", "assets/beat.m4a", "-ac", "1", "-ar", String(SR), "-f", "f32le", "-"], {
  maxBuffer: 1 << 28,
});
const x = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
const frames = Math.floor((x.length / SR) * FPS);

// radix-2 FFT (in place)
function fft(re: Float64Array, im: Float64Array) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    const wr = Math.cos(ang),
      wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1,
        ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const ar = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
        const ai = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
        re[i + k + len / 2] = re[i + k] - ar;
        im[i + k + len / 2] = im[i + k] - ai;
        re[i + k] += ar;
        im[i + k] += ai;
        const t = cr * wr - ci * wi;
        ci = cr * wi + ci * wr;
        cr = t;
      }
    }
  }
}

const hann = Float64Array.from({ length: N }, (_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (N - 1)));
const edges = Array.from({ length: BANDS + 1 }, (_, i) => 30 * Math.pow(16000 / 30, i / BANDS));
const binHz = SR / N;
const levels: number[][] = [];
for (let f = 0; f < frames; f++) {
  const centre = Math.round((f / FPS) * SR);
  const re = new Float64Array(N);
  const im = new Float64Array(N);
  for (let i = 0; i < N; i++) {
    const s = centre - N / 2 + i;
    re[i] = (s >= 0 && s < x.length ? x[s] : 0) * hann[i];
  }
  fft(re, im);
  const row: number[] = [];
  for (let b = 0; b < BANDS; b++) {
    const lo = Math.max(1, Math.floor(edges[b] / binHz));
    const hi = Math.max(lo + 1, Math.ceil(edges[b + 1] / binHz));
    let sum = 0;
    for (let k = lo; k < hi; k++) sum += Math.hypot(re[k], im[k]) / (N / 4); // full-scale sine ≈ 1
    const mag = sum / (hi - lo);
    const db = 20 * Math.log10(Math.max(mag, 1e-9));
    row.push(Math.max(0, Math.min(1, (db + 100) / 70)));
  }
  levels.push(row);
}
// per-band normalisation to the 98th percentile
for (let b = 0; b < BANDS; b++) {
  const col = levels.map((r) => r[b]).sort((a, c) => a - c);
  const p98 = col[Math.floor(0.98 * (col.length - 1))] || 1;
  for (const r of levels) r[b] = Math.min(1.2, r[b] / p98);
}
// envelope: attack 1 frame, release tau
const rel = 1 - Math.exp(-1 / (FPS * TAU));
const env = levels.map((r) => r.slice());
for (let f = 1; f < frames; f++)
  for (let b = 0; b < BANDS; b++) {
    const prev = env[f - 1][b];
    const now = levels[f][b];
    env[f][b] = now > prev ? now : prev + (now - prev) * rel;
  }

const f0 = Math.round(SCENE_START * FPS);
const f1 = Math.min(frames, Math.round(SCENE_END * FPS) + 1);
const rows = env.slice(f0, f1).map((r) => r.map((v) => Math.round(v * 100)));
const block = `/*AUDIO*/ const AUDIO = { fps: ${FPS}, start: ${SCENE_START}, bands: ${BANDS}, frames: ${JSON.stringify(rows)} }; /*END AUDIO*/`;
const file = "compositions/ribbons.html";
const html = readFileSync(file, "utf8");
const out = html.replace(/\/\*AUDIO\*\/[\s\S]*?\/\*END AUDIO\*\//, block);
if (out === html && !html.includes(block)) throw new Error("AUDIO markers not found in " + file);
writeFileSync(file, out);
console.log(`frames ${frames}, scene rows ${rows.length}, wrote ${file}`);
