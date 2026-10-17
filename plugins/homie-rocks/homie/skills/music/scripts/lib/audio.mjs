/**
 * Audio facts measured off the file, with ffmpeg doing the decoding and plain
 * JavaScript doing the arithmetic (no Python, no native add-ons): loudness, an
 * onset envelope, a beat grid, the lag between two recordings.
 */
import { spawnSync } from 'node:child_process';

export function run(cmd, args, { input, maxBuffer = 1024 * 1024 * 1024, timeout = 10 * 60_000 } = {}) {
  const r = spawnSync(cmd, args, { input: typeof input === 'string' ? Buffer.from(input) : input, maxBuffer, timeout });
  if (r.error) throw new Error(`${cmd} could not run: ${r.error.message}`);
  return { code: r.status ?? 1, stdout: r.stdout ?? Buffer.alloc(0), stderr: (r.stderr ?? Buffer.alloc(0)).toString('utf8') };
}

export function need(cmd) {
  const r = spawnSync(cmd, ['-version'], { encoding: 'utf8' });
  return !r.error && r.status === 0;
}

/** Container and stream facts: duration (s), audio rate/channels, video size/fps/frames. */
export function probe(file) {
  const r = run('ffprobe', ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,sample_rate,channels,width,height,r_frame_rate,nb_frames', '-of', 'json', file]);
  if (r.code !== 0) throw new Error(`ffprobe could not read ${file}: ${r.stderr.trim().split('\n').pop()}`);
  const j = JSON.parse(r.stdout.toString('utf8'));
  const a = (j.streams ?? []).find((s) => s.codec_type === 'audio');
  const v = (j.streams ?? []).find((s) => s.codec_type === 'video');
  const [fn, fd] = String(v?.r_frame_rate ?? '0/1').split('/').map(Number);
  return {
    duration: Number(j.format?.duration ?? NaN),
    audio: a ? { codec: a.codec_name, rate: Number(a.sample_rate), channels: Number(a.channels) } : null,
    video: v ? { codec: v.codec_name, width: v.width, height: v.height, fps: fd ? fn / fd : null, frames: v.nb_frames ? Number(v.nb_frames) : null } : null,
  };
}

/** Mono float samples at `rate` (optionally a window and a filter chain). */
export function decodeMono(file, { rate = 22050, start = null, duration = null, filter = null } = {}) {
  const args = ['-hide_banner', '-loglevel', 'error'];
  if (start !== null) args.push('-ss', String(start));
  if (duration !== null) args.push('-t', String(duration));
  args.push('-i', file, '-vn', '-ac', '1', '-ar', String(rate));
  if (filter) args.push('-af', filter);
  args.push('-f', 'f32le', '-');
  const r = run('ffmpeg', args);
  if (r.code !== 0) throw new Error(`ffmpeg could not decode ${file}: ${r.stderr.trim().split('\n').pop()}`);
  const b = r.stdout;
  return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength - (b.byteLength % 4)));
}

/** EBU R128: integrated loudness (LUFS), loudness range (LU) and true peak (dBTP). */
export function loudness(file) {
  const r = run('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', 'ebur128=peak=true', '-f', 'null', '-']);
  const text = r.stderr;
  const sum = text.slice(text.lastIndexOf('Summary:'));
  const num = (re) => { const m = re.exec(sum); return m ? Number(m[1]) : null; };
  return { lufs: num(/I:\s+(-?[\d.]+|-inf) LUFS/), lra: num(/LRA:\s+(-?[\d.]+) LU/), truePeak: num(/Peak:\s+(-?[\d.]+|-inf) dBFS/) };
}

/* ---------------------------------------------------------------- FFT */

/** In-place radix-2 FFT (re, im of a power-of-two length). */
export function fft(re, im, inverse = false) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (2 * Math.PI / len) * (inverse ? 1 : -1);
    const wr = Math.cos(ang); const wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1; let ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const ar = re[i + k]; const ai = im[i + k];
        const br = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
        const bi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
        re[i + k] = ar + br; im[i + k] = ai + bi;
        re[i + k + len / 2] = ar - br; im[i + k + len / 2] = ai - bi;
        const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t;
      }
    }
  }
  if (inverse) for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
}

const pow2 = (n) => 1 << Math.ceil(Math.log2(Math.max(2, n)));

/**
 * Spectral-flux onset envelope: log-magnitude rises summed over a band, the
 * slow trend removed. Returns { env, rate } (envelope values per second).
 */
export function onsetEnvelope(x, sr, { hop = 256, nfft = 1024, lo = 30, hi = 8000 } = {}) {
  const frames = Math.max(0, 1 + Math.floor((x.length - nfft) / hop));
  const win = new Float32Array(nfft).map((_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / nfft));
  const kLo = Math.max(1, Math.floor((lo * nfft) / sr)); const kHi = Math.min(nfft / 2, Math.ceil((hi * nfft) / sr));
  const env = new Float32Array(frames);
  let prev = new Float32Array(kHi - kLo + 1);
  const re = new Float64Array(nfft); const im = new Float64Array(nfft);
  for (let f = 0; f < frames; f++) {
    for (let i = 0; i < nfft; i++) { re[i] = x[f * hop + i] * win[i]; im[i] = 0; }
    fft(re, im);
    const cur = new Float32Array(kHi - kLo + 1);
    let flux = 0;
    for (let k = kLo; k <= kHi; k++) {
      const m = Math.log1p(20 * Math.hypot(re[k], im[k]));
      cur[k - kLo] = m;
      if (f > 0) flux += Math.max(0, m - prev[k - kLo]);
    }
    env[f] = flux; prev = cur;
  }
  // Frame f describes the window centred at (f * hop + nfft / 2) samples.
  // Remove a half-second moving average so sustained loud passages don't read as onsets.
  const rate = sr / hop; const w = Math.max(1, Math.round(rate / 2));
  const out = new Float32Array(frames);
  let acc = 0;
  for (let i = 0; i < frames; i++) {
    acc += env[i]; if (i >= w) acc -= env[i - w];
    const mean = acc / Math.min(i + 1, w);
    out[i] = Math.max(0, env[i] - mean);
  }
  return { env: out, rate, offset: nfft / 2 / sr };
}

/**
 * A sharper onset envelope for WHERE the hits are (spectral flux is steadier for
 * HOW FAST they come): the rise of log energy in short windows, centred.
 */
export function energyOnsets(x, sr, { win = 0.012, hop = 0.004 } = {}) {
  const w = Math.max(8, Math.round(win * sr)); const h = Math.max(1, Math.round(hop * sr));
  const frames = Math.max(0, 1 + Math.floor((x.length - w) / h));
  const e = new Float32Array(frames);
  for (let f = 0; f < frames; f++) {
    let s = 0; for (let i = f * h; i < f * h + w; i++) s += x[i] * x[i];
    e[f] = Math.log10(s / w + 1e-10);
  }
  const env = new Float32Array(frames);
  for (let f = 1; f < frames; f++) env[f] = Math.max(0, e[f] - e[f - 1]);
  // Credit the rise to the window it completes in: the hit sits near the newer window's centre.
  return { env, rate: sr / h, offset: w / 2 / sr };
}

/**
 * A beat grid off an onset envelope: tempo by autocorrelation (or a given
 * `bpm`), phase by summing the envelope on a comb. Confidence is how far the
 * best comb stands above the average one (1 = no preference, 2+ = clear).
 */
export function beatGrid(env, rate, { bpm = null, lo = 70, hi = 180, from = 0, to = null, offset = 0 } = {}) {
  const n = env.length;
  const end = to === null ? n / rate + offset : to;
  const at = (t) => Math.round((t - offset) * rate);
  const comb = (period, ph) => {
    let sum = 0; let count = 0;
    for (let t = from + ph; t < end; t += period) {
      const i = at(t);
      if (i >= 0 && i < n) { sum += env[i] + 0.5 * ((env[i - 1] ?? 0) + (env[i + 1] ?? 0)); count++; }
    }
    return count ? sum / count : 0;
  };
  let period;
  if (!bpm) {
    const minLag = Math.floor((60 / hi) * rate); const maxLag = Math.ceil((60 / lo) * rate);
    let best = -Infinity; let bestLag = minLag;
    const mean = env.reduce((a, b) => a + b, 0) / Math.max(1, n);
    for (let lag = minLag; lag <= Math.min(maxLag, n - 1); lag++) {
      let s = 0;
      for (let i = 0; i + lag < n; i++) s += (env[i] - mean) * (env[i + lag] - mean);
      const bpmHere = 60 / (lag / rate);
      const prior = Math.exp(-0.5 * (Math.log2(bpmHere / 120) / 1.0) ** 2); // octave errors lean toward ~120
      const score = s * (0.6 + 0.4 * prior);
      if (score > best) { best = score; bestLag = lag; }
    }
    // The integer lag is coarse (one envelope frame); settle the period on the comb itself, within that frame.
    let bestP = bestLag / rate; let bestScore = -Infinity;
    for (let k = -20; k <= 20; k++) {
      const p = (bestLag + k / 20) / rate;
      let top = 0;
      for (let s = 0; s < 48; s++) top = Math.max(top, comb(p, (s / 48) * p));
      if (top > bestScore) { bestScore = top; bestP = p; }
    }
    period = bestP;
    bpm = 60 / period;
  } else period = 60 / bpm;
  const steps = 96; let bestPhase = 0; let bestSum = -Infinity; let total = 0;
  for (let s = 0; s < steps; s++) {
    const ph = (s / steps) * period;
    const v = comb(period, ph);
    total += v;
    if (v > bestSum) { bestSum = v; bestPhase = ph; }
  }
  const avg = total / steps;
  const beats = [];
  for (let t = from + bestPhase; t < end; t += period) beats.push(+t.toFixed(4));
  return { bpm: +bpm.toFixed(3), period, phase: from + bestPhase, beats, confidence: +(bestSum / (avg || 1)).toFixed(2) };
}

/** The beat grid of a file, with an optional low band (the kick) to settle half-beat ambiguity. */
export function beatsOf(file, { bpm = null, kick = true, start = null, duration = null } = {}) {
  const sr = 22050;
  const x = decodeMono(file, { rate: sr, start, duration });
  // Tempo off spectral flux (steady); phase off short-window energy rises (sharp), full band and the kick band.
  const full = onsetEnvelope(x, sr);
  const tempo = beatGrid(full.env, full.rate, { bpm, offset: full.offset });
  // Music made to a stated tempo is almost always a whole number of BPM: a measurement within 0.15 of one is that number.
  if (!bpm && Math.abs(tempo.bpm - Math.round(tempo.bpm)) < 0.15) tempo.bpm = Math.round(tempo.bpm);
  const sharp = energyOnsets(x, sr);
  const grid = beatGrid(sharp.env, sharp.rate, { bpm: tempo.bpm, offset: sharp.offset });
  if (!kick) return { ...grid, tempoConfidence: tempo.confidence, duration: x.length / sr };
  const lowX = decodeMono(file, { rate: sr, start, duration, filter: 'lowpass=f=160,lowpass=f=160' });
  const low = energyOnsets(lowX, sr, { win: 0.02, hop: 0.004 });
  const kg = beatGrid(low.env, low.rate, { bpm: tempo.bpm, offset: low.offset });
  // Prefer the kick's phase when it is clearer than the full-band one (it settles half-beat doubt).
  const useKick = kg.confidence >= grid.confidence;
  return { ...(useKick ? kg : grid), tempoConfidence: tempo.confidence, fullConfidence: grid.confidence, kickConfidence: kg.confidence, phaseFrom: useKick ? 'kick' : 'full', duration: x.length / sr };
}

/**
 * The lag of `b` against `a` in seconds (positive: b is late), by GCC-PHAT on
 * band-limited signals, with the peak's height over the median (above ~8 is a
 * clear answer; a pass-through copy reads 40+).
 */
export function lagBetween(a, b, sr, { maxLagS = 0.6 } = {}) {
  const n = Math.min(a.length, b.length);
  const N = pow2(2 * n);
  const ar = new Float64Array(N); const ai = new Float64Array(N); const br = new Float64Array(N); const bi = new Float64Array(N);
  for (let i = 0; i < n; i++) { ar[i] = a[i]; br[i] = b[i]; }
  fft(ar, ai); fft(br, bi);
  const rr = new Float64Array(N); const ri = new Float64Array(N);
  const kLo = Math.floor((200 * N) / sr); const kHi = Math.ceil((4000 * N) / sr);
  for (let k = 0; k < N; k++) {
    const f = k <= N / 2 ? k : N - k;
    if (f < kLo || f > kHi) continue;
    // B * conj(A): its peak sits at the lag of b behind a.
    const xr = br[k] * ar[k] + bi[k] * ai[k]; const xi = bi[k] * ar[k] - br[k] * ai[k];
    const m = Math.hypot(xr, xi) + 1e-12;
    rr[k] = xr / m; ri[k] = xi / m;
  }
  fft(rr, ri, true);
  const maxLag = Math.floor(maxLagS * sr);
  let best = -Infinity; let bestLag = 0; const mags = [];
  for (let l = -maxLag; l <= maxLag; l++) {
    const v = rr[(l + N) % N];
    mags.push(Math.abs(v));
    if (v > best) { best = v; bestLag = l; }
  }
  mags.sort((x, y) => x - y);
  const median = mags[Math.floor(mags.length / 2)] || 1e-12;
  return { lagS: bestLag / sr, peak: +(best / median).toFixed(1) };
}

/** RMS in dBFS over windows of `win` seconds. */
export function rmsDb(x, sr, win = 0.05) {
  const w = Math.max(1, Math.round(win * sr)); const out = [];
  for (let i = 0; i + w <= x.length; i += w) {
    let s = 0; for (let j = i; j < i + w; j++) s += x[j] * x[j];
    out.push(10 * Math.log10(s / w + 1e-12));
  }
  return out;
}
