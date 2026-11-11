// beats.ts: find the tempo and the beat grid of a music track, so shots can be cut on beats.
//
//   bun scripts/beats.ts music.mp3                 prints BPM + first-beat offset, writes music.beats.json
//   bun scripts/beats.ts music.mp3 --min 80 --max 160
//
// Put the result in the director: "bpm": <bpm>, "music": { "file": "music.mp3", "offset": <offset> },
// then give every shot "beats" instead of "duration". cut.ts starts the track at the offset, so beat 1
// lands on the first frame and every cut lands on a beat.
// Method: spectral-flux onset envelope (1024-point FFT, hop 256 at 22.05 kHz), autocorrelation over the
// allowed tempo range with a mild preference for ~120 BPM, then the beat phase with the most onset energy.
// Good for music with a pulse; for ambient beds without one, cut on bars of the BPM the prompt asked for.
const argv = process.argv.slice(2);
const opt = (n: string, d: string) => { const i = argv.indexOf(`--${n}`); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const file = argv.find((a) => !a.startsWith('--') && !/^\d+$/.test(a));
if (!file) { console.error('usage: bun scripts/beats.ts music.(mp3|wav|m4a) [--min 70] [--max 180]'); process.exit(1); }
const SR = 22050, N = 1024, HOP = 256;
const p = Bun.spawn(['ffmpeg', '-v', 'error', '-i', file, '-ac', '1', '-ar', String(SR), '-f', 'f32le', '-'], { stdout: 'pipe' });
const pcm = new Float32Array(await new Response(p.stdout).arrayBuffer());
if (await p.exited || !pcm.length) throw new Error(`could not decode ${file}`);

function fft(re: Float64Array, im: Float64Array) { // in place, radix 2
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) { let bit = n >> 1; for (; j & bit; bit >>= 1) j ^= bit; j ^= bit; if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
  for (let len = 2; len <= n; len <<= 1) {
    const a = (-2 * Math.PI) / len, wr = Math.cos(a), wi = Math.sin(a);
    for (let i = 0; i < n; i += len) { let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) { const ur = re[i + k], ui = im[i + k], vr = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci, vi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
        re[i + k] = ur + vr; im[i + k] = ui + vi; re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi; const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t; } }
  }
}
const win = Float64Array.from({ length: N }, (_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / N));
const frames = Math.floor((pcm.length - N) / HOP), env = new Float64Array(frames);
let prev = new Float64Array(N / 2);
for (let f = 0; f < frames; f++) {
  const re = new Float64Array(N), im = new Float64Array(N);
  for (let i = 0; i < N; i++) re[i] = pcm[f * HOP + i] * win[i];
  fft(re, im);
  const mag = new Float64Array(N / 2); let flux = 0;
  for (let k = 1; k < N / 2; k++) { mag[k] = Math.log1p(10 * Math.hypot(re[k], im[k])); flux += Math.max(0, mag[k] - prev[k]); }
  env[f] = flux; prev = mag;
}
// remove the local mean (0.5 s), keep the positive part
const W = Math.round((0.5 * SR) / HOP), o = new Float64Array(frames);
for (let f = 0; f < frames; f++) { let s = 0, n = 0; for (let k = Math.max(0, f - W); k < Math.min(frames, f + W); k++) { s += env[k]; n++; } o[f] = Math.max(0, env[f] - s / n); }

const fr = SR / HOP, minB = Number(opt('min', '70')), maxB = Number(opt('max', '180'));
let best = 0, bestLag = 0;
const score = (lag: number) => { let s = 0; for (let f = 0; f + lag < frames; f++) s += o[f] * o[f + lag]; return s / (frames - lag); };
for (let lag = Math.floor((60 * fr) / maxB); lag <= Math.ceil((60 * fr) / minB); lag++) {
  const bpm = (60 * fr) / lag, prior = Math.exp(-0.5 * (Math.log2(bpm / 120) / 1.0) ** 2);
  const s = score(lag) * prior;
  if (s > best) { best = s; bestLag = lag; }
}
const a = score(bestLag - 1), b = score(bestLag), c = score(bestLag + 1); // parabolic refinement
const lag = bestLag + (a - c) / (2 * (a - 2 * b + c) || 1);
const bpm = +((60 * fr) / lag).toFixed(2), period = lag;
let bestPh = 0, bestPhS = -1;
for (let ph = 0; ph < period; ph += 0.25) { let s = 0; for (let t = ph; t < frames; t += period) s += o[Math.round(t)] || 0; if (s > bestPhS) { bestPhS = s; bestPh = ph; } }
const offset = +((bestPh * HOP + N / 2) / SR).toFixed(3), dur = pcm.length / SR, beatS = 60 / bpm;
const beats: number[] = []; for (let t = offset; t < dur; t += beatS) beats.push(+t.toFixed(3));
const mean = o.reduce((x, y) => x + y, 0) / frames, sd = Math.sqrt(o.reduce((x, y) => x + (y - mean) ** 2, 0) / frames);
const onsets: number[] = []; for (let f = 1; f < frames - 1; f++) if (o[f] > mean + 2 * sd && o[f] >= o[f - 1] && o[f] > o[f + 1]) onsets.push(+((f * HOP + N / 2) / SR).toFixed(3));
const out = file.replace(/\.[^.]+$/, '') + '.beats.json';
await Bun.write(out, JSON.stringify({ file, bpm, offset, beat: +beatS.toFixed(4), bar: +(beatS * 4).toFixed(4), duration: +dur.toFixed(3), beats, onsets }, null, 1));
console.log(`${file}: ${bpm} BPM, first beat at ${offset} s, beat ${beatS.toFixed(3)} s, ${beats.length} beats, ${onsets.length} strong onsets -> ${out}`);
