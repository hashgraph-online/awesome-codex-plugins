/**
 * The sound of a film that was rendered frame by frame, rebuilt offline.
 *
 * A page stepped on a virtual clock (record-fixed.mjs) has no speaker worth recording: its audio clock
 * runs at the wall's speed while the picture runs at the film's. What it has is the capture log the sound
 * player keeps when a recorder asks (sound.js: window.__homieSoundCapture): every sound it scheduled, with
 * the file, the gain, the rate, the pan, the loop and the time. This mixes those events again, from the
 * game's own files, onto the film's clock:
 *
 *   start   the file decoded (ffmpeg), resampled by its playback rate, panned, faded in, looped
 *   stop    a hard cut, a straight fade, or the exponential fall of setTargetAtTime (time constant fade / 3)
 *   duck    the music bus down to `to` (time constant 15 ms) and back after `seconds` (120 ms)
 *   levels  the master, effect and music faders (and mute), smoothed as the player smooths them
 *
 * Out: three stereo buffers at 48 kHz: `sfx`, `music` (after the duck and its fader) and `mix`, so an
 * edit can keep the music running under shots whose own effects are cut with the picture.
 *
 * What it is NOT: a recording. The player's safety compressor (threshold -6 dB, ratio 8) is stood in for
 * by a peak limiter at -1 dBFS that only acts when the sum goes over; anything the game plays outside
 * the log (its own oscillators, an <audio> element, speech synthesis) is not in the mix at all.
 */
import { run } from '../../../music/scripts/lib/audio.mjs';
import { dbToGain, limit } from '../../../sound/scripts/lib/synth.mjs';

export const MIX_RATE = 48000;

/** A sound file as float stereo at 48 kHz, with how many channels the file really has (a mono file pans differently). */
export function decodeFile(file) {
  const p = run('ffprobe', ['-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels', '-of', 'csv=p=0', file]);
  const channels = Number(String(p.stdout).trim()) || 2;
  const out = run('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-i', file, '-vn', '-ac', '2', '-ar', String(MIX_RATE), '-f', 'f32le', '-']);
  if (out.code !== 0) throw new Error(`ffmpeg could not decode ${file}: ${out.stderr.trim().split('\n').pop()}`);
  const b = out.stdout;
  const all = new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength - (b.byteLength % 8)));
  const n = all.length / 2;
  const L = new Float32Array(n); const R = new Float32Array(n);
  for (let i = 0; i < n; i++) { L[i] = all[2 * i]; R[i] = all[2 * i + 1]; }
  return { L, R, channels };
}

/** A fader the player moves with setTargetAtTime: a list of { at (s), to, tc (s) } read as one smoothed curve. */
function fader(moves, n, first = 1) {
  const out = new Float32Array(n);
  const list = [...moves].sort((a, b) => a.at - b.at);
  let v = first; let target = first; let k = 0; let coef = 0;
  for (let i = 0; i < n; i++) {
    const t = i / MIX_RATE;
    while (k < list.length && list[k].at <= t) { target = list[k].to; coef = 1 - Math.exp(-1 / (Math.max(1e-4, list[k].tc) * MIX_RATE)); k++; }
    v += (target - v) * coef;
    out[i] = v;
  }
  return out;
}

/**
 * Mix a capture log. `events` have `t` in SECONDS on the film's clock (the recorder converts them);
 * `fileFor(url)` gives the local copy of a file, or null. Returns { sfx, music, mix, report }.
 */
export function remix(events, { seconds, fileFor, decode = decodeFile }) {
  const n = Math.max(1, Math.round(seconds * MIX_RATE));
  const sfx = { L: new Float32Array(n), R: new Float32Array(n) };
  const music = { L: new Float32Array(n), R: new Float32Array(n) };
  const cache = new Map();
  const missing = new Set();
  const stops = new Map();
  for (const e of events) if (e.type === 'stop' && e.id != null && !stops.has(e.id)) stops.set(e.id, e);
  let placed = 0; let dropped = 0;
  for (const e of events) {
    if (e.type === 'drop') { dropped++; continue; }
    if (e.type !== 'start') continue;
    const file = fileFor(e.url);
    if (!file) { missing.add(e.url); continue; }
    if (!cache.has(file)) { try { cache.set(file, decode(file)); } catch { cache.set(file, null); } }
    const src = cache.get(file);
    if (!src || !src.L.length) { missing.add(e.url); continue; }
    const bus = e.bus === 'music' ? music : sfx;
    const from = e.t + (e.delay ?? 0);
    const rate = Number(e.rate) > 0 ? Number(e.rate) : 1;
    const gain = Number(e.gain ?? 1);
    // The player's panner: a mono file is placed between the speakers at equal power; a stereo one has the far
    // channel folded into the near one. With no pan there is no panner, and a mono file plays in both at full level.
    const pan = Math.max(-1, Math.min(1, Number(e.pan) || 0));
    let ll = 1; let lr = 0; let rl = 0; let rr = 1;
    if (pan !== 0 && src.channels === 1) { const x = ((pan + 1) / 2) * (Math.PI / 2); ll = Math.cos(x); rr = Math.sin(x); lr = 0; rl = 0; }
    else if (pan < 0) { const x = (pan + 1) * (Math.PI / 2); ll = 1; lr = Math.cos(x); rl = 0; rr = Math.sin(x); }
    else if (pan > 0) { const x = pan * (Math.PI / 2); ll = Math.cos(x); lr = 0; rl = Math.sin(x); rr = 1; }
    const stop = stops.get(e.id) ?? null;
    const stopAt = stop ? stop.t + (stop.delay ?? 0) : Infinity;
    const fade = stop ? Math.max(0, Number(stop.fade) || 0) : 0;
    const endAt = !stop ? Infinity : stop.curve === 'target' ? stopAt + fade + 0.1 : stop.curve === 'linear' ? stopAt + fade : stopAt;
    const fadeIn = Math.max(0, Number(e.fadeIn) || 0);
    const len = src.L.length;
    const i0 = Math.max(0, Math.round(from * MIX_RATE));
    for (let i = i0; i < n; i++) {
      const t = i / MIX_RATE;
      if (t >= endAt) break;
      let pos = (i - from * MIX_RATE) * rate;
      if (pos < 0) continue;
      if (e.loop) pos %= len; else if (pos >= len - 1) break;
      const a = Math.floor(pos); const f = pos - a; const b = e.loop ? (a + 1) % len : a + 1;
      let g = gain;
      if (fadeIn > 0 && t - from < fadeIn) g *= (t - from) / fadeIn;
      if (t >= stopAt) {
        if (stop.curve === 'linear') g *= Math.max(0, 1 - (t - stopAt) / Math.max(1e-4, fade));
        else if (stop.curve === 'target') g *= Math.exp(-(t - stopAt) / Math.max(1e-4, fade / 3));
      }
      const l = (src.L[a] + (src.L[b] - src.L[a]) * f) * g;
      const r = (src.R[a] + (src.R[b] - src.R[a]) * f) * g;
      if (src.channels === 1 && pan !== 0) { bus.L[i] += l * ll; bus.R[i] += l * rr; } else { bus.L[i] += l * ll + r * lr; bus.R[i] += l * rl + r * rr; }
    }
    placed++;
  }
  // The faders, as the player moves them. Before the first `levels` event the player's own defaults hold.
  const lv = events.filter((e) => e.type === 'levels');
  const first = lv[0] ?? { master: 1, sfx: 1, music: 0.7, muted: false };
  const master = fader(lv.map((e) => ({ at: e.t, to: e.muted ? 0 : e.master, tc: 0.02 })), n, first.muted ? 0 : first.master);
  const sfxG = fader(lv.map((e) => ({ at: e.t, to: e.sfx, tc: 0.02 })), n, first.sfx);
  const musG = fader(lv.map((e) => ({ at: e.t, to: e.music, tc: 0.05 })), n, first.music);
  const duck = fader(events.filter((e) => e.type === 'duck').flatMap((e) => [{ at: e.t, to: e.to, tc: 0.015 }, { at: e.t + e.seconds, to: 1, tc: 0.12 }]), n, 1);
  const mix = { L: new Float32Array(n), R: new Float32Array(n) };
  for (let i = 0; i < n; i++) {
    const s = sfxG[i] * master[i]; const m = musG[i] * duck[i] * master[i];
    sfx.L[i] *= s; sfx.R[i] *= s; music.L[i] *= m; music.R[i] *= m;
    mix.L[i] = sfx.L[i] + music.L[i]; mix.R[i] = sfx.R[i] + music.R[i];
  }
  let peak = 0; for (let i = 0; i < n; i++) { const p = Math.max(Math.abs(mix.L[i]), Math.abs(mix.R[i])); if (p > peak) peak = p; }
  const ceiling = dbToGain(-1);
  const limited = peak > ceiling;
  if (limited) limit(mix, { ceiling, releaseMs: 150 });
  return {
    sfx, music, mix,
    report: {
      seconds: n / MIX_RATE, placed, dropped, files: cache.size, missing: [...missing],
      peakDb: peak > 0 ? +(20 * Math.log10(peak)).toFixed(1) : null, limited,
      note: 'Rebuilt from the game\'s own sound files and its log of what it scheduled; the player\'s compressor is stood in for by a peak limiter at -1 dBFS. Sound the game makes outside the log is not here.',
    },
  };
}

/**
 * Where the highlights are, by what the game played: each effect's start counts, a rare sound more than a
 * common one (one win outweighs fifty footsteps), a louder one more than a quiet one. Returns a score for
 * every tenth of a second (the same grid as the picture's motion), and the events by tenth.
 */
export function eventScores(events, seconds) {
  const n = Math.max(1, Math.ceil(seconds * 10));
  const scores = new Float32Array(n);
  const names = Array.from({ length: n }, () => []);
  const starts = events.filter((e) => e.type === 'start' && e.bus !== 'music');
  const count = new Map();
  for (const e of starts) count.set(e.name, (count.get(e.name) ?? 0) + 1);
  for (const e of starts) {
    const k = Math.floor((e.t + (e.delay ?? 0)) * 10);
    if (k < 0 || k >= n) continue;
    scores[k] += Math.min(1.5, Math.max(0.2, Number(e.gain ?? 1))) / Math.sqrt(count.get(e.name));
    names[k].push(e.name);
  }
  return { scores, names };
}
