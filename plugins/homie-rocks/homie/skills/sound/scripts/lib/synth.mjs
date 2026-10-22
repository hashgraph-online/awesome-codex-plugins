/**
 * A small offline synthesizer in plain JavaScript, for sound effects and short scores that are
 * made on the creator's own computer: no provider, no account, no money.
 *
 * - Pitch is integrated into phase every sample, so a slide, a vibrato or an arpeggio is a change
 *   of frequency and never a jump of phase (a bend written as sin(2*pi*f(t)*t) runs backwards).
 * - Saw and square are band-limited (PolyBLEP): a naive square at a high note aliases into
 *   whistles that a phone speaker makes worse.
 * - Everything is a function of the sample index and a seed: the same spec renders the same
 *   samples on every machine, so a sound can be re-rendered from its JSON.
 *
 * Buffers are Float32Array at RATE. A stereo buffer is { L, R }.
 */

export const RATE = 48000;
const TAU = Math.PI * 2;

/* ---------------------------------------------------------------- numbers */

export function mulberry32(seed) {
  let a = (Number(seed) >>> 0) || 0x9e3779b9;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const dbToGain = (db) => 10 ** (db / 20);
export const gainToDb = (g) => 20 * Math.log10(Math.max(1e-12, Math.abs(g)));
export const semis = (n) => 2 ** (n / 12);

const NOTE_INDEX = { c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 };
/** A note as a MIDI number: "A4" → 69, "C#3" → 49, "Bb2" → 46; a number is taken as a MIDI number already (60 → 60). */
export function midiOf(note) {
  if (typeof note === 'number') return note;
  const m = /^([A-Ga-g])([#b]?)(-?\d)$/.exec(String(note).trim());
  if (!m) throw new Error(`not a note: "${note}" (write it like C4, F#3 or Bb2)`);
  const acc = m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0;
  return 12 * (Number(m[3]) + 1) + NOTE_INDEX[m[1].toLowerCase()] + acc;
}
export const hzOfMidi = (m) => 440 * 2 ** ((m - 69) / 12);
/**
 * A pitch as hertz. A NUMBER IS ALWAYS HERTZ; a string is a note name ("A2" → 110). There is no guessing by size.
 *
 * This used to read a number of 127 or less as a MIDI note, so that 60 could mean middle C. But every bass note
 * is a frequency under 127 Hz: a caller that had already converted its note (A2 → 110 Hz) had it converted again
 * (MIDI 110 = 4698.6 Hz; B2 → 123.47 Hz → 10.2 kHz), and a bass line came out as a whistle five octaves up with no
 * error. A MIDI number is now said out loud: hzOfMidi(57), or `midi` / `slide.toMidi` on a voice.
 */
export function hzOf(pitch) {
  if (typeof pitch === 'number') {
    if (!(pitch > 0) || !Number.isFinite(pitch)) throw new Error(`not a frequency: ${pitch} (a number is hertz and must be above 0; for a MIDI note use "midi", for a name write "A2")`);
    return pitch;
  }
  return hzOfMidi(midiOf(pitch));
}
/**
 * The pitch of a spec that may give it either way: { freq } (hertz, or a note name) or { midi } (a MIDI note
 * number, fractions allowed for a detune). Giving both is refused: one of them would be silently ignored.
 */
export function pitchHz(freq, midi, what = 'freq') {
  if (midi !== undefined && midi !== null) {
    if (freq !== undefined && freq !== null) throw new Error(`give ${what} (hertz or a note name) or its MIDI form, not both`);
    if (typeof midi !== 'number' || !Number.isFinite(midi)) throw new Error(`not a MIDI note: ${midi} (a number, 69 = A4 = 440 Hz)`);
    return hzOfMidi(midi);
  }
  return hzOf(freq);
}

/* ---------------------------------------------------------------- buffers */

export function mono(seconds) { return new Float32Array(Math.max(1, Math.ceil(seconds * RATE))); }
export function stereo(seconds) { return { L: mono(seconds), R: mono(seconds) }; }
export const secondsOf = (buf) => (buf.L ? buf.L.length : buf.length) / RATE;

/** Add a mono buffer into a stereo one at `at` seconds, with gain and a constant-power pan (-1..1). */
export function addInto(dst, src, { at = 0, gain = 1, pan = 0 } = {}) {
  const off = Math.round(at * RATE);
  const p = Math.max(-1, Math.min(1, pan));
  const gl = gain * Math.cos((p + 1) * Math.PI / 4);
  const gr = gain * Math.sin((p + 1) * Math.PI / 4);
  if (src.L) {
    const n = Math.min(src.L.length, dst.L.length - off);
    for (let i = Math.max(0, -off); i < n; i++) { dst.L[off + i] += src.L[i] * gain; dst.R[off + i] += src.R[i] * gain; }
    return dst;
  }
  const n = Math.min(src.length, dst.L.length - off);
  for (let i = Math.max(0, -off); i < n; i++) { dst.L[off + i] += src[i] * gl; dst.R[off + i] += src[i] * gr; }
  return dst;
}

export function peakOf(buf) {
  let p = 0;
  for (const ch of buf.L ? [buf.L, buf.R] : [buf]) for (let i = 0; i < ch.length; i++) { const v = Math.abs(ch[i]); if (v > p) p = v; }
  return p;
}

export function scale(buf, g) {
  for (const ch of buf.L ? [buf.L, buf.R] : [buf]) for (let i = 0; i < ch.length; i++) ch[i] *= g;
  return buf;
}

/** Trim trailing near-silence (below `floorDb` for good), keeping `keep` seconds of tail, and fade the last 5 ms. */
export function trimTail(buf, { floorDb = -70, keep = 0.01 } = {}) {
  const chans = buf.L ? [buf.L, buf.R] : [buf];
  const floor = dbToGain(floorDb);
  let last = 0;
  for (const ch of chans) for (let i = ch.length - 1; i > last; i--) if (Math.abs(ch[i]) > floor) { last = i; break; }
  const n = Math.min(chans[0].length, last + Math.round(keep * RATE) + 1);
  const cut = chans.map((ch) => ch.slice(0, n));
  const fade = Math.min(n, Math.round(0.005 * RATE));
  for (const ch of cut) for (let i = 0; i < fade; i++) ch[n - 1 - i] *= i / fade;
  return buf.L ? { L: cut[0], R: cut[1] } : cut[0];
}

/* ---------------------------------------------------------------- oscillators */

function blep(t, dt) {
  if (t < dt) { t /= dt; return t + t - t * t - 1; }
  if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; }
  return 0;
}

/**
 * One oscillator sample at phase `ph` (0..1) with phase step `dt` (freq / RATE).
 * Waves: sine, triangle, saw, square (duty), pulse (= square), noise (white), crunch (noise held for one
 * period: pitched grit, the 8-bit explosion), metal (six detuned squares, a cymbal's clang).
 */
function osc(wave, ph, dt, duty, rnd, state) {
  switch (wave) {
    case 'sine': return Math.sin(TAU * ph);
    case 'triangle': return 1 - 4 * Math.abs(ph - 0.5);
    case 'saw': return 2 * ph - 1 - blep(ph, dt);
    case 'square': case 'pulse': {
      const d = duty ?? 0.5;
      // Minus the pulse's mean (2d - 1): an uneven pulse is otherwise a DC offset, a click at every start and stop.
      return (ph < d ? 1 : -1) + blep(ph, dt) - blep((ph + 1 - d) % 1, dt) - (2 * d - 1);
    }
    case 'noise': return rnd() * 2 - 1;
    case 'crunch': {
      if (ph < state.lastPh) state.held = rnd() * 2 - 1;
      state.lastPh = ph;
      return state.held ?? 0;
    }
    default: throw new Error(`unknown wave "${wave}" (sine, triangle, saw, square, pulse, noise, crunch)`);
  }
}

/* ---------------------------------------------------------------- envelopes */

/**
 * Amplitude at time t (s) of a note held for `gate` seconds.
 * env: { a attack, d decay, s sustain level 0..1, r release, curve (2 = a natural exponential-ish fall) }.
 * A one-shot effect is { a, d, s: 0 } and ignores the gate.
 */
export function envAt(t, gate, env = {}) {
  const a = Math.max(0.0005, env.a ?? 0.002);
  const d = Math.max(0.001, env.d ?? 0.1);
  const s = env.s ?? 0;
  const r = Math.max(0.002, env.r ?? 0.05);
  const c = env.curve ?? 2;
  const level = (x) => {
    if (x < 0) return 0;
    if (x < a) return x / a;
    if (x < a + d) return s + (1 - s) * (1 - (x - a) / d) ** c;
    return s;
  };
  if (s === 0 && (env.s === undefined || env.s === 0) && gate === Infinity) return level(t);
  if (t < gate) return level(t);
  const from = level(gate);
  const x = (t - gate) / r;
  return x >= 1 ? 0 : from * (1 - x) ** c;
}

/** How long a note of `gate` seconds sounds with this envelope, tail included. */
export function envLength(gate, env = {}) {
  const a = env.a ?? 0.002; const d = env.d ?? 0.1; const s = env.s ?? 0; const r = env.r ?? 0.05;
  if (!s) return Math.min(gate === Infinity ? a + d : Math.max(gate, 0) + r, a + d);
  return gate + r;
}

/* ---------------------------------------------------------------- filters */

/** Zavalishin's TPT state-variable filter: stable under fast sweeps. type lowpass | highpass | bandpass. */
export function svf() {
  let ic1 = 0; let ic2 = 0; let g = 0; let k = 1; let a1 = 0; let a2 = 0; let a3 = 0; let lastF = -1; let lastQ = -1;
  return (x, freq, q, type) => {
    if (freq !== lastF || q !== lastQ) {
      const f = Math.min(Math.max(freq, 10), RATE * 0.45);
      g = Math.tan(Math.PI * f / RATE); k = 1 / Math.max(0.3, q); a1 = 1 / (1 + g * (g + k)); a2 = g * a1; a3 = g * a2;
      lastF = freq; lastQ = q;
    }
    const v3 = x - ic2;
    const v1 = a1 * ic1 + a2 * v3;
    const v2 = ic2 + a2 * ic1 + a3 * v3;
    ic1 = 2 * v1 - ic1; ic2 = 2 * v2 - ic2;
    if (type === 'highpass') return x - k * v1 - v2;
    if (type === 'bandpass') return v1 * k;
    return v2;
  };
}

/* ---------------------------------------------------------------- one voice */

/**
 * Render one voice (mono). spec:
 *   wave, duty,
 *   freq (a number is hertz, a string is a note like "A4")  OR  midi (a MIDI note number, 57 = A2 = 110 Hz)
 *   slide: { to (hertz or a note name) OR toMidi, time (s), curve: 'exp' | 'lin' }   pitch glide from freq to `to`
 *         (a number is never guessed to be one or the other: 110 is 110 Hz, and MIDI 110 is written midi: 110)
 *   vibrato: { rate (Hz), depth (semitones), delay (s) }
 *   arp: { steps: [semitones...], every (s) }                          stepped pitch: a coin, a power-up
 *   env: { a, d, s, r, curve }, gate (s held; one-shots leave it out)
 *   filter: { type, freq, to, time, q }                                 a swept TPT filter
 *   fm: { ratio, index, decay }                                        2-operator FM (a bell, an electric piano)
 *   gain (linear) or db
 *   seed
 */
export function voice(spec) {
  const rnd = mulberry32(spec.seed ?? 1);
  const gate = spec.gate ?? Infinity;
  const env = spec.env ?? {};
  const len = Math.min(30, (spec.length ?? envLength(gate, env)) + 0.002);
  const out = mono(len);
  const f0 = spec.freq === undefined && spec.midi === undefined ? 440 : pitchHz(spec.freq, spec.midi, 'freq');
  const to = spec.slide ? pitchHz(spec.slide.to, spec.slide.toMidi, 'slide.to') : f0;
  const slideT = Math.max(1e-4, spec.slide?.time ?? len);
  const vib = spec.vibrato;
  const arp = spec.arp;
  const flt = spec.filter ? { f: svf(), type: spec.filter.type ?? 'lowpass', from: spec.filter.freq ?? 2000, to: spec.filter.to ?? spec.filter.freq ?? 2000, time: Math.max(1e-4, spec.filter.time ?? len), q: spec.filter.q ?? 0.707 } : null;
  const fm = spec.fm;
  const g = spec.db !== undefined ? dbToGain(spec.db) : (spec.gain ?? 1);
  const state = {};
  let ph = spec.phase ?? 0; let mph = 0;
  for (let i = 0; i < out.length; i++) {
    const t = i / RATE;
    let f = f0;
    if (spec.slide) {
      const x = Math.min(1, t / slideT);
      f = spec.slide.curve === 'lin' ? f0 + (to - f0) * x : f0 * (to / f0) ** x;
    }
    if (arp?.steps?.length) f *= semis(arp.steps[Math.min(arp.steps.length - 1, Math.floor(t / Math.max(0.005, arp.every ?? 0.06)))]);
    if (vib && t >= (vib.delay ?? 0)) f *= semis((vib.depth ?? 0.3) * Math.sin(TAU * (vib.rate ?? 6) * (t - (vib.delay ?? 0))));
    const dt = f / RATE;
    let x;
    if (fm) {
      const idx = (fm.index ?? 2) * (fm.decay ? Math.exp(-t / fm.decay) : 1);
      x = Math.sin(TAU * ph + idx * Math.sin(TAU * mph));
      mph = (mph + dt * (fm.ratio ?? 1.4)) % 1;
    } else x = osc(spec.wave ?? 'sine', ph, dt, spec.duty, rnd, state);
    ph += dt; if (ph >= 1) ph -= Math.floor(ph);
    if (flt) {
      const y = Math.min(1, t / flt.time);
      const cf = flt.from * (flt.to / flt.from) ** y;
      x = flt.f(x, cf, flt.q, flt.type);
    }
    out[i] = x * envAt(t, gate, env) * g;
  }
  return out;
}

/** Karplus-Strong plucked string: a noise burst in a tuned delay line that loses its highs each pass. */
export function pluck({ freq, midi, gate = 0.5, bright = 0.5, decay = 0.996, gain = 1, seed = 1, length = null }) {
  const rnd = mulberry32(seed);
  // The same two explicit forms as voice(): freq (hertz or a note name) or midi; A3 when neither is given.
  const f = freq === undefined && midi === undefined ? hzOf('A3') : pitchHz(freq, midi, 'freq');
  const len = length ?? Math.max(gate + 0.4, 1.2);
  const out = mono(len);
  const n = Math.max(2, Math.round(RATE / f));
  const line = new Float32Array(n);
  let prev = 0;
  for (let i = 0; i < n; i++) { const w = rnd() * 2 - 1; prev = prev + (w - prev) * (0.2 + 0.8 * bright); line[i] = prev; }
  let idx = 0;
  const rel = Math.round((gate) * RATE);
  for (let i = 0; i < out.length; i++) {
    const a = line[idx]; const b = line[(idx + 1) % n];
    const damp = i > rel ? decay * 0.985 : decay;
    line[idx] = (a + b) * 0.5 * damp;
    out[i] = a * gain;
    idx = (idx + 1) % n;
  }
  const fade = Math.round(0.004 * RATE);
  for (let i = 0; i < fade; i++) out[out.length - 1 - i] *= i / fade;
  return out;
}

/* ---------------------------------------------------------------- drums */

/** Synthesized drums: kick, snare, clap, hat, openhat, tom, rim, shaker. `tone` shifts the pitch (semitones). */
export function drum(kind, { gain = 1, tone = 0, decay = 1, seed = 7 } = {}) {
  const k = semis(tone);
  switch (kind) {
    case 'kick': {
      const body = voice({ wave: 'sine', freq: 150 * k, slide: { to: 44 * k, time: 0.09 }, env: { a: 0.001, d: 0.42 * decay, curve: 2.2 }, gain: 1.0 * gain });
      const click = voice({ wave: 'noise', seed, filter: { type: 'highpass', freq: 3000 }, env: { a: 0.0005, d: 0.006 }, gain: 0.35 * gain });
      return mixMono([body, click]);
    }
    case 'snare': {
      const tone1 = voice({ wave: 'triangle', freq: 190 * k, slide: { to: 160 * k, time: 0.05 }, env: { a: 0.001, d: 0.11 * decay }, gain: 0.55 * gain });
      const noise = voice({ wave: 'noise', seed, filter: { type: 'highpass', freq: 1400 * k, q: 0.8 }, env: { a: 0.001, d: 0.2 * decay, curve: 2.4 }, gain: 0.65 * gain });
      return mixMono([tone1, noise]);
    }
    case 'clap': {
      const parts = [0, 0.011, 0.022].map((at, i) => ({ at, buf: voice({ wave: 'noise', seed: seed + i, filter: { type: 'bandpass', freq: 1250 * k, q: 1.2 }, env: { a: 0.0005, d: 0.012 }, gain: 0.9 * gain }) }));
      parts.push({ at: 0.03, buf: voice({ wave: 'noise', seed: seed + 9, filter: { type: 'bandpass', freq: 1150 * k, q: 1 }, env: { a: 0.001, d: 0.16 * decay }, gain: 0.7 * gain }) });
      return mixMono(parts);
    }
    case 'hat': case 'openhat': {
      // Six detuned square oscillators (the classic analog cymbal), band-passed high.
      const fs = [205.3, 304.4, 369.6, 522.7, 540, 800].map((f) => f * k);
      const d = (kind === 'hat' ? 0.045 : 0.32) * decay;
      const len = d + 0.01;
      const out = mono(len);
      const hp = svf(); const bp = svf();
      const phs = fs.map(() => 0);
      for (let i = 0; i < out.length; i++) {
        const t = i / RATE;
        let x = 0;
        for (let j = 0; j < fs.length; j++) { phs[j] = (phs[j] + fs[j] / RATE) % 1; x += phs[j] < 0.5 ? 1 : -1; }
        x = hp(bp(x / 6, 10000, 0.9, 'bandpass'), 7000, 0.7, 'highpass');
        out[i] = x * envAt(t, Infinity, { a: 0.0005, d, curve: 3 }) * 1.6 * gain;
      }
      return out;
    }
    case 'tom': return voice({ wave: 'sine', freq: 180 * k, slide: { to: 110 * k, time: 0.18 }, env: { a: 0.001, d: 0.35 * decay }, gain: 0.9 * gain });
    case 'rim': return voice({ wave: 'square', freq: 1700 * k, filter: { type: 'bandpass', freq: 1800 * k, q: 3 }, env: { a: 0.0005, d: 0.025 }, gain: 0.8 * gain });
    case 'shaker': return voice({ wave: 'noise', seed, filter: { type: 'highpass', freq: 6000, q: 0.7 }, env: { a: 0.008, d: 0.06 * decay }, gain: 0.45 * gain });
    default: throw new Error(`unknown drum "${kind}" (kick, snare, clap, hat, openhat, tom, rim, shaker)`);
  }
}

/** Sum mono buffers (or { at, buf, gain }) into one mono buffer. */
export function mixMono(parts) {
  const items = parts.map((p) => (p instanceof Float32Array ? { at: 0, buf: p, gain: 1 } : { at: p.at ?? 0, buf: p.buf, gain: p.gain ?? 1 }));
  const len = Math.max(...items.map((p) => Math.round(p.at * RATE) + p.buf.length));
  const out = new Float32Array(Math.max(1, len));
  for (const p of items) { const off = Math.round(p.at * RATE); for (let i = 0; i < p.buf.length; i++) out[off + i] += p.buf[i] * p.gain; }
  return out;
}

/* ---------------------------------------------------------------- effects */

/** A DC blocker (one-pole high-pass at about 10 Hz): no offset left to click when a sound starts or stops. */
export function dcBlock(buf) {
  const R0 = 1 - (2 * Math.PI * 10) / RATE;
  for (const ch of buf.L ? [buf.L, buf.R] : [buf]) {
    let x1 = 0; let y1 = 0;
    for (let i = 0; i < ch.length; i++) { const y = ch[i] - x1 + R0 * y1; x1 = ch[i]; y1 = y; ch[i] = y; }
  }
  return buf;
}

/** Soft saturation: tanh drive, level-matched at small signals. */
export function drive(buf, amount = 2) {
  if (!(amount > 1)) return buf;
  const n = Math.tanh(amount);
  for (const ch of buf.L ? [buf.L, buf.R] : [buf]) for (let i = 0; i < ch.length; i++) ch[i] = Math.tanh(ch[i] * amount) / n;
  return buf;
}

/** Retro grit: fewer bits and a lower sample-and-hold rate. */
export function crush(buf, { bits = 8, rate = 11025 } = {}) {
  const step = 2 / 2 ** bits;
  const hold = Math.max(1, Math.round(RATE / rate));
  for (const ch of buf.L ? [buf.L, buf.R] : [buf]) {
    let held = 0;
    for (let i = 0; i < ch.length; i++) { if (i % hold === 0) held = Math.round(ch[i] / step) * step; ch[i] = held; }
  }
  return buf;
}

/** A feedback echo; `pingpong` alternates sides. Returns a stereo buffer long enough for the tail. */
export function echo(buf, { time = 0.18, feedback = 0.35, mix = 0.3, pingpong = true, tail = null } = {}) {
  const src = buf.L ? buf : { L: buf, R: buf };
  const taps = Math.ceil(Math.log(0.001) / Math.log(Math.max(0.01, feedback)));
  const extra = tail ?? Math.min(4, time * taps);
  const out = stereo(secondsOf(src) + extra);
  out.L.set(src.L); out.R.set(src.R);
  const d = Math.round(time * RATE);
  for (let k = 1, g = mix; k <= taps; k++, g *= feedback) {
    const off = d * k;
    const toL = !pingpong || k % 2 === 0; const toR = !pingpong || k % 2 === 1;
    for (let i = 0; i < src.L.length && off + i < out.L.length; i++) {
      const m = (src.L[i] + src.R[i]) * 0.5 * g;
      if (toL) out.L[off + i] += m;
      if (toR) out.R[off + i] += m;
    }
  }
  return out;
}

/**
 * A small plate-like reverb (eight damped combs and four allpasses a side, after Freeverb).
 * room 0..1 (size), damp 0..1 (how fast the highs die), mix 0..1. Returns stereo with the tail.
 */
export function reverb(buf, { room = 0.6, damp = 0.4, mix = 0.22, tail = null } = {}) {
  const src = buf.L ? buf : { L: buf, R: buf };
  const extra = tail ?? 0.6 + room * 2.2;
  const out = stereo(secondsOf(src) + extra);
  const sr = RATE / 44100;
  const combs = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617];
  const alls = [556, 441, 341, 225];
  const fb = 0.7 + room * 0.28;
  for (const [side, spread] of [['L', 0], ['R', 23]]) {
    const cs = combs.map((c) => ({ buf: new Float32Array(Math.round((c + spread) * sr)), i: 0, store: 0 }));
    const as = alls.map((a) => ({ buf: new Float32Array(Math.round((a + spread) * sr)), i: 0 }));
    const input = src[side];
    const dst = out[side];
    for (let n = 0; n < dst.length; n++) {
      const x = (n < input.length ? (src.L[n] + src.R[n]) * 0.5 : 0) * 0.015;
      let acc = 0;
      for (const c of cs) {
        const y = c.buf[c.i];
        c.store = y * (1 - damp) + c.store * damp;
        c.buf[c.i] = x + c.store * fb;
        c.i = (c.i + 1) % c.buf.length;
        acc += y;
      }
      for (const a of as) {
        const y = a.buf[a.i];
        a.buf[a.i] = acc + y * 0.5;
        acc = y - acc;
        a.i = (a.i + 1) % a.buf.length;
      }
      dst[n] = (n < input.length ? input[n] : 0) + acc * mix * 3;
    }
  }
  return out;
}

/** A gentle program limiter: an instant-attack, smooth-release peak follower holding peaks under `ceiling` (linear). */
export function limit(buf, { ceiling = dbToGain(-1), releaseMs = 80, lookaheadMs = 3 } = {}) {
  const src = buf.L ? buf : { L: buf, R: buf };
  const n = src.L.length;
  const look = Math.round(lookaheadMs / 1000 * RATE);
  const rel = Math.exp(-1 / (releaseMs / 1000 * RATE));
  // Required gain per sample, then a running minimum over the lookahead, then smooth release.
  const need = new Float32Array(n);
  for (let i = 0; i < n; i++) { const p = Math.max(Math.abs(src.L[i]), Math.abs(src.R[i])); need[i] = p > ceiling ? ceiling / p : 1; }
  const gain = new Float32Array(n);
  let g = 1;
  for (let i = n - 1; i >= 0; i--) { let m = need[i]; for (let j = 1; j <= look && i + j < n; j++) if (need[i + j] < m) m = need[i + j]; gain[i] = m; }
  for (let i = 0; i < n; i++) { g = gain[i] < g ? gain[i] : gain[i] + (g - gain[i]) * rel; src.L[i] *= g; if (src.R !== src.L) src.R[i] *= g; }
  return buf;
}

/* ---------------------------------------------------------------- measuring */

/**
 * Levels a person hears, without ffmpeg: sample peak, whole-file RMS, and the loudest 50 ms window's RMS
 * (the fair number for a short effect: integrated LUFS needs 400 ms blocks and gates a 0.2 s blip out).
 */
export function levels(buf) {
  const L = buf.L ?? buf; const R = buf.R ?? buf;
  const n = L.length;
  let peak = 0; let sum = 0;
  for (let i = 0; i < n; i++) { const m = (L[i] + R[i]) * 0.5; sum += m * m; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
  const w = Math.max(1, Math.round(0.05 * RATE));
  let win = 0; let best = 0;
  for (let i = 0; i < n; i++) {
    const m = (L[i] + R[i]) * 0.5; win += m * m;
    if (i >= w) { const o = (L[i - w] + R[i - w]) * 0.5; win -= o * o; }
    if (i >= w - 1 || i === n - 1) best = Math.max(best, win / Math.min(w, i + 1));
  }
  return { seconds: +(n / RATE).toFixed(3), peakDb: +gainToDb(peak).toFixed(2), rmsDb: +gainToDb(Math.sqrt(sum / Math.max(1, n))).toFixed(2), loudestDb: +gainToDb(Math.sqrt(best)).toFixed(2) };
}

/* ---------------------------------------------------------------- files */

/** 16- or 24-bit PCM WAV (mono or stereo). Samples are clipped at full scale and dithered at 16 bits. */
export function wavBytes(buf, { bits = 16, rate = RATE, channels = null, seed = 3 } = {}) {
  const chans = buf.L ? (channels === 1 ? [mixDown(buf)] : [buf.L, buf.R]) : [buf];
  const n = chans[0].length; const ch = chans.length; const bps = bits / 8;
  const out = Buffer.alloc(44 + n * ch * bps);
  out.write('RIFF', 0); out.writeUInt32LE(36 + n * ch * bps, 4); out.write('WAVE', 8);
  out.write('fmt ', 12); out.writeUInt32LE(16, 16); out.writeUInt16LE(1, 20); out.writeUInt16LE(ch, 22);
  out.writeUInt32LE(rate, 24); out.writeUInt32LE(rate * ch * bps, 28); out.writeUInt16LE(ch * bps, 32); out.writeUInt16LE(bits, 34);
  out.write('data', 36); out.writeUInt32LE(n * ch * bps, 40);
  const rnd = mulberry32(seed);
  const max = 2 ** (bits - 1) - 1;
  let o = 44;
  for (let i = 0; i < n; i++) {
    for (let c = 0; c < ch; c++) {
      const d = bits === 16 ? (rnd() - rnd()) / max : 0;
      const v = Math.max(-1, Math.min(1, chans[c][i] + d));
      const q = Math.round(v * max);
      if (bits === 16) out.writeInt16LE(q, o); else out.writeIntLE(q, o, 3);
      o += bps;
    }
  }
  return out;
}

export function mixDown(buf) {
  if (!buf.L) return buf;
  const out = new Float32Array(buf.L.length);
  for (let i = 0; i < out.length; i++) out[i] = (buf.L[i] + buf.R[i]) * 0.5;
  return out;
}

/** Is a stereo buffer really two channels, or the same signal twice? */
export function isWide(buf) {
  if (!buf.L) return false;
  for (let i = 0; i < buf.L.length; i += 7) if (Math.abs(buf.L[i] - buf.R[i]) > 1e-4) return true;
  return false;
}
