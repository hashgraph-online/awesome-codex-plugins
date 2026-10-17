/**
 * Sound effects for games, synthesized: each preset is a small recipe of voices and effects with
 * a few knobs (pitch, length, seed, style), so a set of effects shares one character and every
 * effect can be re-rendered from its JSON line.
 *
 * Levels: every effect is set to a loudness class by its loudest 50 ms (see `levels` in synth.mjs),
 * then held under a -1 dBFS peak, so a set sits together in a mix without hand-balancing:
 *   ui -20 dB · small -16 dB · normal -12 dB · big -9 dB (RMS of the loudest 50 ms).
 */
import {
  RATE, addInto, crush, dbToGain, dcBlock, drive, drum, echo, levels, limit, mixMono, mulberry32, peakOf, reverb, scale, semis, stereo, trimTail, voice,
} from './synth.mjs';

export const LEVELS = { ui: -20, small: -16, normal: -12, big: -9 };

const P = (p, hz) => hz * semis(p.pitch ?? 0);
const L = (p, s) => s * (p.length ?? 1);

/** Each preset: what it is for, its default loudness class, and the recipe. */
export const PRESETS = {
  jump: {
    about: 'a rising blip: a jump, a hop, a small launch', level: 'normal',
    make: (p) => voice({ wave: 'square', duty: 0.3, freq: P(p, 270), slide: { to: P(p, 640), time: L(p, 0.16) }, env: { a: 0.002, d: L(p, 0.2), curve: 1.6 }, filter: { type: 'lowpass', freq: 5200 } }),
  },
  doublejump: {
    about: 'a second, higher jump in the air', level: 'normal',
    make: (p) => mixMono([
      voice({ wave: 'square', duty: 0.25, freq: P(p, 420), slide: { to: P(p, 880), time: L(p, 0.1) }, env: { a: 0.002, d: L(p, 0.13), curve: 1.6 } }),
      { at: L(p, 0.06), buf: voice({ wave: 'triangle', freq: P(p, 880), slide: { to: P(p, 1320), time: L(p, 0.1) }, env: { a: 0.002, d: L(p, 0.16) } }), gain: 0.7 },
    ]),
  },
  land: {
    about: 'a soft thud with a knock on top: landing, a heavy footfall (the knock is what a phone speaker plays)', level: 'small',
    make: (p) => mixMono([
      voice({ wave: 'sine', freq: P(p, 160), slide: { to: P(p, 60), time: L(p, 0.08) }, env: { a: 0.001, d: L(p, 0.14) }, gain: 0.45 }),
      { at: 0, buf: voice({ wave: 'triangle', freq: P(p, 520), slide: { to: P(p, 300), time: L(p, 0.05) }, env: { a: 0.001, d: L(p, 0.08) } }), gain: 1.0 },
      { at: 0, buf: voice({ wave: 'noise', seed: p.seed, filter: { type: 'bandpass', freq: 1500, q: 1.1 }, env: { a: 0.001, d: L(p, 0.05) } }), gain: 1.6 },
    ]),
  },
  step: {
    about: 'a footstep tick', level: 'ui',
    make: (p) => voice({ wave: 'noise', seed: p.seed, filter: { type: 'bandpass', freq: P(p, 1800), q: 1.5 }, env: { a: 0.001, d: L(p, 0.035), curve: 2.5 } }),
  },
  coin: {
    about: 'a two-note pickup chime: a coin, a gem, a point', level: 'normal',
    make: (p) => voice({ wave: 'square', duty: 0.5, freq: P(p, 988), arp: { steps: [0, 5], every: L(p, 0.065) }, env: { a: 0.001, d: L(p, 0.32), curve: 2 }, filter: { type: 'lowpass', freq: 7000 } }),
  },
  pickup: {
    about: 'a bright rising sparkle: an item, a key, a heart', level: 'normal',
    make: (p) => voice({ wave: 'triangle', freq: P(p, 784), arp: { steps: [0, 4, 7, 12], every: L(p, 0.045) }, vibrato: { rate: 14, depth: 0.15 }, env: { a: 0.002, d: L(p, 0.3) } }),
  },
  powerup: {
    about: 'a four-step rising arpeggio with shimmer: a power-up, a level up', level: 'normal',
    make: (p) => {
      const a = voice({ wave: 'square', duty: 0.25, freq: P(p, 392), arp: { steps: [0, 4, 7, 12, 16, 19, 24], every: L(p, 0.06) }, vibrato: { rate: 9, depth: 0.2, delay: 0.3 }, env: { a: 0.002, d: L(p, 0.62), curve: 1.4 }, filter: { type: 'lowpass', freq: 6000 } });
      return echo(a, { time: 0.09, feedback: 0.3, mix: 0.25 });
    },
  },
  hit: {
    about: 'a punchy impact: a punch, a bonk, a knock-back', level: 'big',
    make: (p) => drive(mixMono([
      voice({ wave: 'noise', seed: p.seed, filter: { type: 'lowpass', freq: 4200, to: 600, time: L(p, 0.12) }, env: { a: 0.0005, d: L(p, 0.14), curve: 2.2 } }),
      voice({ wave: 'square', duty: 0.5, freq: P(p, 220), slide: { to: P(p, 70), time: L(p, 0.1) }, env: { a: 0.001, d: L(p, 0.16) }, gain: 0.6 }),
      voice({ wave: 'sine', freq: P(p, 110), slide: { to: P(p, 45), time: L(p, 0.08) }, env: { a: 0.001, d: L(p, 0.18) }, gain: 0.8 }),
    ]), 2.2),
  },
  hurt: {
    about: 'the player took damage: a falling buzz', level: 'normal',
    make: (p) => drive(voice({ wave: 'saw', freq: P(p, 520), slide: { to: P(p, 140), time: L(p, 0.25) }, vibrato: { rate: 30, depth: 0.6 }, env: { a: 0.001, d: L(p, 0.3) }, filter: { type: 'lowpass', freq: 3000 } }), 1.8),
  },
  explosion: {
    about: 'a big noisy boom with a low thump and a room: an explosion, a crash', level: 'big',
    make: (p) => {
      const body = mixMono([
        voice({ wave: 'crunch', seed: p.seed, freq: P(p, 900), slide: { to: P(p, 60), time: L(p, 0.9) }, env: { a: 0.001, d: L(p, 1.1), curve: 2.4 } }),
        voice({ wave: 'noise', seed: p.seed + 1, filter: { type: 'lowpass', freq: 2400, to: 140, time: L(p, 0.8) }, env: { a: 0.001, d: L(p, 1.2), curve: 2 }, gain: 0.8 }),
        voice({ wave: 'sine', freq: P(p, 90), slide: { to: P(p, 32), time: L(p, 0.4) }, env: { a: 0.001, d: L(p, 0.6) }, gain: 1.1 }),
      ]);
      return reverb(drive(body, 2.5), { room: 0.5, damp: 0.6, mix: 0.18, tail: 0.8 });
    },
  },
  shoot: {
    about: 'a falling zap: a laser, a blaster, a shot', level: 'normal',
    make: (p) => mixMono([
      voice({ wave: 'saw', freq: P(p, 1500), slide: { to: P(p, 260), time: L(p, 0.16) }, env: { a: 0.001, d: L(p, 0.18), curve: 1.5 }, filter: { type: 'lowpass', freq: 6500 } }),
      { at: 0, buf: voice({ wave: 'noise', seed: p.seed, filter: { type: 'highpass', freq: 3000 }, env: { a: 0.0005, d: 0.03 } }), gain: 0.35 },
    ]),
  },
  dash: {
    about: 'a quick filtered swoosh: a dash, a dodge, a swing', level: 'small',
    make: (p) => voice({ wave: 'noise', seed: p.seed, filter: { type: 'bandpass', freq: P(p, 500), to: P(p, 4200), time: L(p, 0.22), q: 2.2 }, env: { a: L(p, 0.06), d: L(p, 0.2), curve: 1.5 }, gain: 1.4 }),
  },
  whoosh: {
    about: 'a slow air swell and fall: a pass-by, a transition', level: 'small',
    make: (p) => {
      const n = L(p, 0.7);
      const up = voice({ wave: 'noise', seed: p.seed, length: n, filter: { type: 'bandpass', freq: P(p, 300), to: P(p, 2600), time: n * 0.55, q: 1.6 }, env: { a: n * 0.5, d: n * 0.5, curve: 1.2 }, gain: 1.4 });
      return up;
    },
  },
  bounce: {
    about: 'a springy boing: a bounce pad, a trampoline', level: 'normal',
    make: (p) => voice({ wave: 'sine', freq: P(p, 180), slide: { to: P(p, 520), time: L(p, 0.08) }, vibrato: { rate: 18, depth: 1.2, delay: 0.06 }, env: { a: 0.002, d: L(p, 0.45), curve: 1.6 } }),
  },
  click: {
    about: 'a UI tick: a button, a hover, a menu move', level: 'ui',
    make: (p) => voice({ wave: 'sine', freq: P(p, 1900), env: { a: 0.0005, d: L(p, 0.025), curve: 2 } }),
  },
  confirm: {
    about: 'a UI yes: two notes up', level: 'ui',
    make: (p) => voice({ wave: 'triangle', freq: P(p, 880), arp: { steps: [0, 7], every: L(p, 0.07) }, env: { a: 0.001, d: L(p, 0.2) } }),
  },
  back: {
    about: 'a UI no or back: two notes down', level: 'ui',
    make: (p) => voice({ wave: 'triangle', freq: P(p, 880), arp: { steps: [0, -5], every: L(p, 0.07) }, env: { a: 0.001, d: L(p, 0.2) } }),
  },
  deny: {
    about: 'a low double buzz: not allowed, locked, not enough', level: 'small',
    make: (p) => voice({ wave: 'square', duty: 0.5, freq: P(p, 150), arp: { steps: [0, 0, -1], every: L(p, 0.08) }, env: { a: 0.001, d: L(p, 0.26), curve: 1 }, filter: { type: 'lowpass', freq: 1800 } }),
  },
  countdown: {
    about: 'a round-start beep (3, 2, 1)', level: 'normal',
    make: (p) => voice({ wave: 'square', duty: 0.5, freq: P(p, 880), env: { a: 0.002, d: L(p, 0.16), s: 0, curve: 1 }, filter: { type: 'lowpass', freq: 5000 } }),
  },
  go: {
    about: 'the start signal after the countdown: higher and longer', level: 'normal',
    make: (p) => voice({ wave: 'square', duty: 0.5, freq: P(p, 1760), env: { a: 0.002, d: L(p, 0.5), curve: 1.2 }, vibrato: { rate: 7, depth: 0.1, delay: 0.1 }, filter: { type: 'lowpass', freq: 6000 } }),
  },
  tick: {
    about: 'a clock tick for the last seconds of a round', level: 'small',
    make: (p) => drum('rim', { tone: p.pitch ?? 0 }),
  },
  alarm: {
    about: 'a two-tone warning: time nearly up, danger near', level: 'normal',
    make: (p) => voice({ wave: 'square', duty: 0.5, freq: P(p, 660), arp: { steps: [0, 5, 0, 5], every: L(p, 0.12) }, env: { a: 0.002, d: L(p, 0.5), curve: 0.6 }, filter: { type: 'lowpass', freq: 3500 } }),
  },
  teleport: {
    about: 'a rising shimmer with echo: a portal, a respawn, a warp', level: 'normal',
    make: (p) => echo(voice({ wave: 'sine', freq: P(p, 300), slide: { to: P(p, 2400), time: L(p, 0.35) }, vibrato: { rate: 22, depth: 0.8 }, env: { a: 0.01, d: L(p, 0.4) } }), { time: 0.07, feedback: 0.45, mix: 0.4 }),
  },
  shatter: {
    about: 'a glassy crackle: breaking a crate, ice, a shield', level: 'normal',
    make: (p) => {
      const r = mulberry32(p.seed ?? 5);
      const parts = [];
      for (let i = 0; i < 9; i++) parts.push({ at: r() * L(p, 0.12), buf: voice({ wave: 'sine', freq: P(p, 2200 + r() * 3800), env: { a: 0.0005, d: 0.05 + r() * 0.12 } }), gain: 0.5 });
      parts.push({ at: 0, buf: voice({ wave: 'noise', seed: p.seed, filter: { type: 'highpass', freq: 2500 }, env: { a: 0.0005, d: L(p, 0.18) } }), gain: 0.8 });
      return mixMono(parts);
    },
  },
  score: {
    about: 'a clean ding for a point or a combo (raise --pitch per combo step)', level: 'normal',
    make: (p) => voice({ fm: { ratio: 3.5, index: 2.2, decay: 0.12 }, freq: P(p, 1047), env: { a: 0.001, d: L(p, 0.5), curve: 2.2 } }),
  },
  win: {
    about: 'a short major fanfare: a round won', level: 'normal',
    make: (p) => {
      const notes = [[0, 0], [0.11, 4], [0.22, 7], [0.36, 12]];
      const lead = mixMono(notes.map(([at, s], i) => ({ at: L(p, at), buf: voice({ wave: 'square', duty: 0.25, freq: P(p, 523.25) * semis(s), gate: i === 3 ? L(p, 0.5) : L(p, 0.09), env: { a: 0.002, d: 0.08, s: 0.7, r: 0.12 }, vibrato: i === 3 ? { rate: 6, depth: 0.15, delay: 0.1 } : undefined, filter: { type: 'lowpass', freq: 5000 } }) })));
      const harm = mixMono(notes.map(([at, s], i) => ({ at: L(p, at), buf: voice({ wave: 'triangle', freq: P(p, 261.63) * semis(s), gate: i === 3 ? L(p, 0.5) : L(p, 0.09), env: { a: 0.002, d: 0.08, s: 0.8, r: 0.15 } }), gain: 0.7 })));
      return reverb(mixMono([lead, { at: 0, buf: harm, gain: 0.8 }]), { room: 0.4, mix: 0.15, tail: 0.6 });
    },
  },
  lose: {
    about: 'a short falling minor phrase: a round lost, knocked out', level: 'normal',
    make: (p) => {
      const notes = [[0, 7], [0.18, 6], [0.36, 5], [0.54, 0]];
      return reverb(mixMono(notes.map(([at, s], i) => ({ at: L(p, at), buf: voice({ wave: 'pulse', duty: 0.4, freq: P(p, 392) * semis(s - 5), gate: i === 3 ? L(p, 0.55) : L(p, 0.15), env: { a: 0.004, d: 0.1, s: 0.7, r: 0.2 }, vibrato: i === 3 ? { rate: 5, depth: 0.3, delay: 0.15 } : undefined, filter: { type: 'lowpass', freq: 2600 } }) }))), { room: 0.5, mix: 0.18, tail: 0.8 });
    },
  },
  thud: {
    about: 'a heavy wooden knock: a door, a crate landing', level: 'normal',
    // The tom now really falls to a low note (its slide target is hertz, and used to be misread as a MIDI note four
    // octaves up, which is what a phone was playing). A body under 150 Hz is silent on a phone, so the knock is its
    // own voice here, as in `land`: a short triangle and a band of noise between 300 Hz and 1 kHz.
    make: (p) => mixMono([
      drum('tom', { tone: (p.pitch ?? 0) - 7, decay: 0.6, gain: 0.6 }),
      { at: 0, buf: voice({ wave: 'triangle', freq: P(p, 430), slide: { to: P(p, 250), time: 0.05 }, env: { a: 0.001, d: 0.1 } }), gain: 1.0 },
      { at: 0, buf: voice({ wave: 'noise', seed: p.seed, filter: { type: 'bandpass', freq: 700, q: 1.2 }, env: { a: 0.001, d: 0.06 } }), gain: 1.4 },
    ]),
  },
};

/** The set a game usually needs first, by kind of game. */
export const KITS = {
  arcade: ['jump', 'land', 'coin', 'powerup', 'hit', 'hurt', 'explosion', 'countdown', 'go', 'win', 'lose', 'click'],
  platformer: ['jump', 'doublejump', 'land', 'step', 'coin', 'pickup', 'hurt', 'bounce', 'teleport', 'win', 'lose'],
  shooter: ['shoot', 'hit', 'hurt', 'explosion', 'dash', 'pickup', 'alarm', 'countdown', 'go', 'win', 'lose'],
  party: ['countdown', 'go', 'score', 'coin', 'hit', 'dash', 'bounce', 'tick', 'alarm', 'win', 'lose', 'confirm', 'back'],
  ui: ['click', 'confirm', 'back', 'deny', 'tick'],
};

/**
 * Render one effect. spec: { name, preset, pitch, length, seed, style: clean|retro|soft, level: ui|small|normal|big|<dB> }.
 * Returns { buf (stereo), facts }.
 */
export function renderEffect(spec) {
  const preset = PRESETS[spec.preset ?? spec.name];
  if (!preset) throw new Error(`no preset "${spec.preset ?? spec.name}" (presets: ${Object.keys(PRESETS).join(', ')})`);
  const p = { pitch: Number(spec.pitch ?? 0), length: Number(spec.length ?? 1), seed: Number(spec.seed ?? 1) };
  let buf = preset.make(p);
  if (spec.style === 'retro') buf = crush(buf, { bits: 6, rate: 16000 });
  if (spec.style === 'soft') {
    const s = buf.L ? buf : { L: buf, R: buf };
    const out = stereo(s.L.length / RATE);
    addInto(out, s);
    for (const ch of [out.L, out.R]) { let y = 0; for (let i = 0; i < ch.length; i++) { y += (ch[i] - y) * 0.35; ch[i] = y; } }
    buf = out;
  }
  if (!buf.L) { const s = stereo(buf.length / RATE); addInto(s, buf); buf = s; }
  dcBlock(buf);
  // Loudness class, then the peak ceiling.
  const cls = spec.level ?? preset.level;
  const target = typeof cls === 'number' ? cls : LEVELS[cls] ?? LEVELS.normal;
  const before = levels(buf);
  if (!(peakOf(buf) > 0)) throw new Error(`"${spec.name}" rendered silence`);
  scale(buf, dbToGain(target - before.loudestDb));
  limit(buf, { ceiling: dbToGain(-1), releaseMs: 40 });
  buf = trimTail(buf, { floorDb: -66 });
  const after = levels(buf);
  return { buf, facts: { ...after, level: cls, targetDb: target, preset: spec.preset ?? spec.name } };
}
