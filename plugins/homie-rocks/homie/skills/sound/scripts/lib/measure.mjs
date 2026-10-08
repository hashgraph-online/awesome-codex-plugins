/**
 * What a sound file actually is, measured, so "it sounds fine" is never the report:
 * loudness (EBU R128, and again through a phone-speaker curve), true peak, clipping, DC, how late
 * the sound starts, silences and gaps, where the energy sits (five bands and the share below
 * 300 Hz that phone speakers throw away), stereo correlation and what folding to mono costs,
 * onset density, narrow tones with their level and how much of the time they are there (a steady one
 * is a hum), and a loudness arc over time.
 *
 * ffmpeg decodes and does R128; everything else is plain JavaScript over the decoded samples.
 */
import { existsSync } from 'node:fs';
import { fft, run } from '../../../music/scripts/lib/audio.mjs';
import { svf } from './synth.mjs';

export const BANDS = [
  { id: 'sub', from: 20, to: 120 },
  { id: 'low', from: 120, to: 500 },
  { id: 'mid', from: 500, to: 2000 },
  { id: 'high', from: 2000, to: 8000 },
  { id: 'air', from: 8000, to: 20000 },
];
/** A small phone speaker: nothing much under ~350 Hz, little over 12 kHz (4th-order high-pass, 2nd-order low-pass). */
export const PHONE_CURVE = 'highpass=f=350:poles=2,highpass=f=350:poles=2,lowpass=f=12000:poles=2';
/** A television's speakers: a little more bass. */
export const TV_CURVE = 'highpass=f=110:poles=2,lowpass=f=15000:poles=2';

const db = (x) => (x > 0 ? 20 * Math.log10(x) : -Infinity);
const r = (x, p = 2) => (Number.isFinite(x) ? +x.toFixed(p) : null);

/** Decode to interleaved float stereo at `rate` (mono files come back with L = R). */
export function decodeStereo(file, { rate = 48000, filter = null, start = null, duration = null } = {}) {
  if (!existsSync(file)) throw new Error(`no such file: ${file}`);
  const args = ['-hide_banner', '-loglevel', 'error'];
  if (start !== null) args.push('-ss', String(start));
  if (duration !== null) args.push('-t', String(duration));
  args.push('-i', file, '-vn', '-ac', '2', '-ar', String(rate));
  if (filter) args.push('-af', filter);
  args.push('-f', 'f32le', '-');
  const out = run('ffmpeg', args);
  if (out.code !== 0) throw new Error(`ffmpeg could not decode ${file}: ${out.stderr.trim().split('\n').pop()}`);
  const b = out.stdout;
  const all = new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength - (b.byteLength % 8)));
  const n = all.length / 2;
  const L = new Float32Array(n); const R = new Float32Array(n);
  for (let i = 0; i < n; i++) { L[i] = all[2 * i]; R[i] = all[2 * i + 1]; }
  return { L, R, rate };
}

/** EBU R128 through an optional filter chain: integrated LUFS, range, true peak. Needs 0.4 s or more of audio. */
export function r128(file, filter = null) {
  const chain = `${filter ? `${filter},` : ''}ebur128=peak=true`;
  const out = run('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', chain, '-f', 'null', '-']);
  const text = out.stderr;
  const sum = text.slice(text.lastIndexOf('Summary:'));
  const num = (re) => { const m = re.exec(sum); return m ? (m[1] === '-inf' ? -Infinity : Number(m[1])) : null; };
  return { lufs: num(/I:\s+(-?[\d.]+|-inf) LUFS/), lra: num(/LRA:\s+(-?[\d.]+) LU/), truePeak: num(/Peak:\s+(-?[\d.]+|-inf) dBFS/) };
}

/**
 * Everything about one file. `sections` [{ id, from, to }] (seconds) adds per-section numbers.
 * `silenceDb` is the floor for silence and gaps (default -50 dBFS over 100 ms windows).
 */
export function measure(file, { rate = 48000, silenceDb = -50, gapSeconds = 0.4, arcSeconds = 10 } = {}) {
  const { L, R } = decodeStereo(file, { rate });
  const n = L.length;
  const seconds = n / rate;
  let peak = 0; let sum = 0; let clipped = 0; let dc = 0; let lr = 0; let ll = 0; let rr = 0; let monoSum = 0;
  for (let i = 0; i < n; i++) {
    const a = L[i]; const b = R[i];
    const pa = Math.abs(a); const pb = Math.abs(b);
    if (pa > peak) peak = pa; if (pb > peak) peak = pb;
    if (pa >= 0.9999) clipped++; if (pb >= 0.9999) clipped++;
    const m = (a + b) * 0.5;
    sum += (a * a + b * b) * 0.5; dc += m; lr += a * b; ll += a * a; rr += b * b; monoSum += m * m;
  }
  const rms = Math.sqrt(sum / Math.max(1, n));
  const floor = 10 ** (silenceDb / 20);
  // 100 ms windows: silence share, gaps, when the sound starts, the loudness arc.
  const w = Math.max(1, Math.round(rate * 0.1));
  const wins = [];
  for (let i = 0; i < n; i += w) {
    let s = 0; const e = Math.min(n, i + w);
    for (let j = i; j < e; j++) { const m = (L[j] + R[j]) * 0.5; s += m * m; }
    wins.push(Math.sqrt(s / Math.max(1, e - i)));
  }
  const silent = wins.filter((v) => v < floor).length;
  const gaps = [];
  let run0 = -1;
  for (let k = 0; k <= wins.length; k++) {
    const quiet = k < wins.length && wins[k] < floor;
    if (quiet && run0 < 0) run0 = k;
    if (!quiet && run0 >= 0) {
      const len = (k - run0) * 0.1;
      // Only gaps inside the sound count: leading and trailing silence is reported as start/tail.
      if (len >= gapSeconds && run0 > 0 && k < wins.length) gaps.push({ at: r(run0 * 0.1, 1), seconds: r(len, 1) });
      run0 = -1;
    }
  }
  let start = null;
  const startFloor = Math.max(floor, peak * 10 ** (-40 / 20));
  for (let i = 0; i < n; i++) if (Math.abs(L[i]) > startFloor || Math.abs(R[i]) > startFloor) { start = i / rate; break; }
  const arc = [];
  const per = Math.max(1, Math.round(arcSeconds / 0.1));
  for (let k = 0; k < wins.length; k += per) {
    const slice = wins.slice(k, k + per);
    const e = Math.sqrt(slice.reduce((a, v) => a + v * v, 0) / slice.length);
    arc.push({ at: r(k * 0.1, 1), rmsDb: r(db(e), 1) });
  }
  // Spectrum: Hann frames of 4096, at most ~800 of them spread over the file.
  const N = 4096;
  const hop = Math.max(1024, Math.floor((n - N) / 800));
  const hann = new Float32Array(N); for (let i = 0; i < N; i++) hann[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (N - 1));
  const bandE = new Float64Array(BANDS.length); const monoBandE = new Float64Array(BANDS.length); const lrBandE = new Float64Array(BANDS.length);
  let under300 = 0; let total = 0; let cTop = 0; let cBot = 0;
  const mean = new Float64Array(N / 2);
  const flux = [];
  let prev = null; let frames = 0;
  const spectra = []; // every frame's power spectrum, kept so a narrow tone can be asked how OFTEN it is there
  const reL = new Float64Array(N); const imL = new Float64Array(N); const reR = new Float64Array(N); const imR = new Float64Array(N);
  for (let s = 0; s + N <= n; s += hop) {
    for (let i = 0; i < N; i++) { reL[i] = L[s + i] * hann[i]; imL[i] = 0; reR[i] = R[s + i] * hann[i]; imR[i] = 0; }
    fft(reL, imL); fft(reR, imR);
    const mag = new Float64Array(N / 2);
    for (let k = 1; k < N / 2; k++) {
      const hz = (k * rate) / N;
      const pl = reL[k] * reL[k] + imL[k] * imL[k]; const pr = reR[k] * reR[k] + imR[k] * imR[k];
      const mr = (reL[k] + reR[k]) * 0.5; const mi = (imL[k] + imR[k]) * 0.5; const pm = mr * mr + mi * mi;
      const p = (pl + pr) * 0.5;
      mag[k] = Math.sqrt(p); mean[k] += p;
      if (hz < 20 || hz > 20000) continue;
      total += p; if (hz < 300) under300 += p;
      cTop += hz * p; cBot += p;
      const bi = BANDS.findIndex((b) => hz >= b.from && hz < b.to);
      if (bi >= 0) { bandE[bi] += p; monoBandE[bi] += pm; lrBandE[bi] += p; }
    }
    if (prev) { let f = 0; for (let k = 1; k < N / 2; k++) { const d = mag[k] - prev[k]; if (d > 0) f += d; } flux.push(f); }
    prev = mag; frames++;
    const pw = new Float32Array(N / 2); for (let k = 1; k < N / 2; k++) pw[k] = mag[k] * mag[k]; spectra.push(pw);
  }
  const bands = Object.fromEntries(BANDS.map((b, i) => [b.id, r(bandE[i] / (total || 1), 3)]));
  const monoLossDb = Object.fromEntries(BANDS.map((b, i) => [b.id, lrBandE[i] > 0 ? r(10 * Math.log10(Math.max(1e-20, monoBandE[i]) / lrBandE[i]), 1) : null]));
  const med = (xs) => { if (!xs.length) return 0; const s = [...xs].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]; };
  const fm = med(flux); const mad = med(flux.map((v) => Math.abs(v - fm)));
  const onsets = flux.filter((v, i) => v > fm + 3 * mad && v > (flux[i - 1] ?? 0) && v >= (flux[i + 1] ?? 0)).length;
  const hopSeconds = hop / rate;
  // Narrow tones: a bin 10 dB over its neighbourhood in the AVERAGE spectrum. That alone is only "narrow": a melody's
  // high partial that sounds for two seconds of sixteen is narrow too, and so is any single note. Three more numbers
  // say whether it is a hum (a whine, a stuck voice), which is steady and audible:
  //   levelDb        how loud the tone is, in dBFS (its RMS as a sine, averaged over the file): prominence is
  //                  relative, and a filter that lowers a tone lowers its neighbours with it and leaves it unchanged
  //   energyShare    the tone's share of all the energy between 20 Hz and 20 kHz
  //   presentShare   the share of the file's frames in which the tone stands 10 dB over its neighbours and is
  //                  above -70 dBFS: a hum is there nearly all the time, a note is not
  // A Hann-windowed sine of amplitude A puts A² · N²/16 · 1.5 of power across its main lobe (1.5 = the window's
  // noise bandwidth in bins), so three bins summed and divided by that give A² back.
  const lobe = (N * N / 16) * 1.5;
  const toneFloor = 10 ** (-70 / 10) * 2; // A² of a sine at -70 dBFS RMS
  const lines = [];
  for (let k = 4; k < N / 2 - 4; k++) {
    const hz = (k * rate) / N;
    if (hz < 40 || hz > 16000) continue;
    const local = (mean[k - 4] + mean[k - 3] + mean[k + 3] + mean[k + 4]) / 4;
    if (!(local > 0 && mean[k] > local * 10 && mean[k] >= mean[k - 1] && mean[k] >= mean[k + 1])) continue;
    let present = 0;
    for (const pw of spectra) {
      const near = (pw[k - 4] + pw[k - 3] + pw[k + 3] + pw[k + 4]) / 4;
      const a2 = (pw[k - 1] + pw[k] + pw[k + 1]) / lobe;
      if (a2 > toneFloor && pw[k] > near * 10) present++;
    }
    const three = mean[k - 1] + mean[k] + mean[k + 1];
    const a2mean = three / Math.max(1, frames) / lobe;
    lines.push({
      hz: r(hz, 1), prominenceDb: r(10 * Math.log10(mean[k] / local), 1),
      levelDb: r(10 * Math.log10(Math.max(1e-20, a2mean / 2)), 1),
      energyShare: r(three / (total || 1), 4),
      presentShare: r(present / Math.max(1, frames), 3),
    });
  }
  lines.sort((a, b) => b.prominenceDb - a.prominenceDb);
  const corr = ll > 0 && rr > 0 ? lr / Math.sqrt(ll * rr) : null;
  const stereoDiff = (() => { let d = 0; for (let i = 0; i < n; i += 3) d = Math.max(d, Math.abs(L[i] - R[i])); return d; })();
  const long = seconds >= 0.45;
  const full = long ? r128(file) : { lufs: null, lra: null, truePeak: null };
  const phone = long ? r128(file, PHONE_CURVE) : { lufs: null };
  // A short effect is too short for R128: the same phone curve in JavaScript, RMS of the loudest 50 ms before and after.
  const phoneRmsLoss = (() => {
    if (rate !== 48000) return null;
    const a = svf(); const b = svf(); const c = svf();
    const w50 = Math.round(rate * 0.05);
    let best = 0; let bestF = 0; let win = 0; let winF = 0;
    const hist = new Float32Array(n); const histF = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const m = (L[i] + R[i]) * 0.5;
      const f = c(b(a(m, 350, 0.707, 'highpass'), 350, 0.707, 'highpass'), 12000, 0.707, 'lowpass');
      hist[i] = m * m; histF[i] = f * f; win += hist[i]; winF += histF[i];
      if (i >= w50) { win -= hist[i - w50]; winF -= histF[i - w50]; }
      if (win > best) best = win; if (winF > bestF) bestF = winF;
    }
    return best > 0 ? r(10 * Math.log10(best / Math.max(1e-20, bestF)), 1) : null;
  })();
  return {
    file, seconds: r(seconds, 3), rate,
    loudness: { lufs: r(full.lufs, 1), lra: r(full.lra, 1), truePeakDb: r(full.truePeak, 1), phoneLufs: r(phone.lufs, 1), phoneLossDb: full.lufs !== null && phone.lufs !== null ? r(full.lufs - phone.lufs, 1) : phoneRmsLoss },
    samplePeakDb: r(db(peak), 2), rmsDb: r(db(rms), 2), crestDb: rms > 0 ? r(db(peak / rms), 1) : null,
    clippedSamples: clipped, dcOffset: r(dc / Math.max(1, n), 5),
    startMs: start === null ? null : Math.round(start * 1000), silentShare: r(silent / Math.max(1, wins.length), 3), gaps: gaps.slice(0, 20),
    bands, under300Share: r(under300 / (total || 1), 3), centroidHz: cBot > 0 ? Math.round(cTop / cBot) : null,
    stereo: { correlation: r(corr, 3), wide: stereoDiff > 1e-4, monoLossDb },
    onsetsPerSecond: frames > 1 ? r(onsets / (frames * hopSeconds), 2) : 0,
    narrowTones: lines.slice(0, 5),
    arc,
  };
}

/**
 * What makes a narrow tone a steady one, a hum rather than a note: it stands well over its neighbours, it is
 * loud enough to hear, and it is there most of the time. A melody's brief high partial passes the first test
 * and often the second, never the third; a tone under the level floor is prominent only because nothing else
 * is near it.
 */
export const STEADY = { prominenceDb: 25, levelDb: -60, presentShare: 0.6 };
/** The most prominent narrow tone that is steady by STEADY's three tests, or null. Older measurements without the two new numbers are never called steady. */
export function steadyTone(m) {
  return (m.narrowTones ?? []).find((t) => t.prominenceDb > STEADY.prominenceDb && (t.levelDb ?? -Infinity) > STEADY.levelDb && (t.presentShare ?? 0) >= STEADY.presentShare) ?? null;
}

/** Plain-words warnings from a measurement: what a person will hear wrong. `kind` sfx | music | capture. */
export function warnings(m, kind = 'music') {
  const w = [];
  if (m.clippedSamples > 0) w.push(`${m.clippedSamples} clipped samples: it distorts; lower the gain before the limiter`);
  if (m.samplePeakDb !== null && m.samplePeakDb < -40) w.push(`the loudest sample is ${m.samplePeakDb} dBFS: this is close to silence`);
  if (Math.abs(m.dcOffset ?? 0) > 0.01) w.push(`DC offset ${m.dcOffset}: a click at every start and stop; high-pass it at 20 Hz`);
  if (m.loudness.truePeakDb !== null && m.loudness.truePeakDb > -1) w.push(`true peak ${m.loudness.truePeakDb} dBTP: over -1 dBTP it can clip after mp3/aac encoding`);
  if ((m.loudness.phoneLossDb ?? 0) > 10) w.push(`through a phone speaker it is ${m.loudness.phoneLossDb} dB quieter (${Math.round(m.under300Share * 100)}% of its energy is under 300 Hz, which phones barely play): give it something between 500 Hz and 4 kHz, a click, a knock, an upper harmonic`);
  if (m.stereo.wide && m.stereo.correlation !== null && m.stereo.correlation < 0) w.push(`stereo correlation ${m.stereo.correlation}: the channels fight; folded to mono (one phone speaker) parts cancel`);
  const monoWorst = Object.entries(m.stereo.monoLossDb).filter(([, v]) => v !== null && v < -3);
  if (m.stereo.wide && monoWorst.length) w.push(`folding to mono loses ${monoWorst.map(([b, v]) => `${-v} dB of ${b}`).join(', ')}`);
  if (kind === 'sfx' && m.startMs !== null && m.startMs > 15) w.push(`the sound starts ${m.startMs} ms late: a hit feels laggy; trim the head`);
  if (kind !== 'sfx' && m.gaps.length) w.push(`${m.gaps.length} gap(s) of silence inside it (first at ${m.gaps[0].at} s, ${m.gaps[0].seconds} s long)`);
  if (kind === 'music' && m.loudness.lufs !== null && (m.loudness.lufs > -9 || m.loudness.lufs < -24)) w.push(`integrated loudness ${m.loudness.lufs} LUFS is outside -24..-9: a web page or a game bed usually sits at -14 to -20`);
  const hum = steadyTone(m);
  if (hum && kind === 'capture') w.push(`a steady tone at ${hum.hz} Hz: there ${Math.round(hum.presentShare * 100)}% of the time at ${hum.levelDb} dBFS (${(hum.energyShare * 100).toFixed(1)}% of the energy), ${hum.prominenceDb} dB over its neighbours: a hum or a stuck voice?`);
  return w;
}

/** A spectrogram over a waveform, one PNG, for looking at a sound (width x 2 x height). */
export function sheetPng(file, out, { width = 1200, height = 240 } = {}) {
  const graph = `[0:a]aformat=channel_layouts=mono,showspectrumpic=s=${width}x${height}:legend=0:scale=log:fscale=log:color=intensity[s];[0:a]aformat=channel_layouts=mono,showwavespic=s=${width}x${Math.round(height / 2)}:colors=0xffcf5a[w];[s][w]vstack=inputs=2`;
  const res = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', file, '-filter_complex', graph, '-frames:v', '1', out]);
  if (res.code !== 0) throw new Error(`ffmpeg could not draw ${out}: ${res.stderr.trim().split('\n').pop()}`);
  return out;
}
