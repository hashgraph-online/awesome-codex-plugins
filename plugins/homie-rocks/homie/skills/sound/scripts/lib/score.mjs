/**
 * A score, written as JSON, rendered to audio on this computer: tempo, key, chords per section,
 * a pattern per instrument, an arrangement of sections. Every section is a whole number of bars,
 * so section starts are bar lines a game can switch music on and a trailer can cut on.
 *
 * What comes out (render()):
 *   mix     the stereo master (limited, before loudness targeting)
 *   stems   one stereo buffer per instrument, plus 'reverb' (the shared room); they sum to the mix
 *   grid    { bpm, beatsPerBar, barSeconds, sections: [{ name, bar, at, bars }] }
 * loop(): one section rendered three times over and the middle copy kept, so the tails of the
 * copy before it (reverb, echoes, a held note) are already in its head: it loops without a seam.
 *
 * The pattern language (references/SCORE.md has all of it):
 *   notes      "A4 . C5 - | E5*2 D5 C5 ."   one token per step; '-' holds, '.' rests, '*n' lasts n steps,
 *              "[A3 C4 E4]" a chord, '!' after a note accents it, '|' marks a bar (checked)
 *   from the chords   root · root8 · pulse · octaves · chords · stabs · arp · arp-down · arp-updown  (':8' sets the rate)
 *   drums      four · backbeat · half · break · shuffle · hats · none, '+fill' on the last bar,
 *              or { "kick": "x...x...", "snare": "....x...", "hat": "x.x.x.x." } (a bar, repeated)
 */
import {
  RATE, addInto, dbToGain, dcBlock, drum, echo, hzOfMidi, limit, midiOf, mixMono, peakOf, pluck, reverb, stereo, voice,
} from './synth.mjs';

/* ---------------------------------------------------------------- harmony */

const QUALITIES = {
  '': [0, 4, 7], maj: [0, 4, 7], m: [0, 3, 7], min: [0, 3, 7], '5': [0, 7], '6': [0, 4, 7, 9], m6: [0, 3, 7, 9],
  '7': [0, 4, 7, 10], maj7: [0, 4, 7, 11], m7: [0, 3, 7, 10], m9: [0, 3, 7, 10, 14], '9': [0, 4, 7, 10, 14], add9: [0, 4, 7, 14],
  dim: [0, 3, 6], dim7: [0, 3, 6, 9], m7b5: [0, 3, 6, 10], aug: [0, 4, 8], sus2: [0, 2, 7], sus4: [0, 5, 7], '7sus4': [0, 5, 7, 10],
};
const PC = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

/** "Am7" → { root: 9, tones: [0,3,7,10], bass: 9 }; "C/E" puts E in the bass. */
export function parseChord(sym) {
  const m = /^([A-G])([#b]?)([a-z0-9#]*)(?:\/([A-G])([#b]?))?$/.exec(String(sym).trim());
  if (!m) throw new Error(`not a chord: "${sym}" (write it like Am, F, G7, Cmaj7, Dsus4, C/E)`);
  const acc = (a) => (a === '#' ? 1 : a === 'b' ? -1 : 0);
  const root = (PC[m[1]] + acc(m[2]) + 12) % 12;
  const tones = QUALITIES[m[3]];
  if (!tones) throw new Error(`unknown chord quality "${m[3]}" in "${sym}" (${Object.keys(QUALITIES).filter(Boolean).join(', ')})`);
  const bass = m[4] ? (PC[m[4]] + acc(m[5]) + 12) % 12 : root;
  return { sym, root, tones, bass };
}

/** The chords of a section, one entry per bar: [[{ chord, from, to } in beats within the bar]]. */
export function chordBars(text, bars, beatsPerBar) {
  if (!text) return Array.from({ length: bars }, () => []);
  const src = String(text).trim();
  const groups = src.includes('|') ? src.split('|').map((g) => g.trim()).filter(Boolean) : src.split(/\s+/).filter(Boolean);
  const out = [];
  for (let b = 0; b < bars; b++) {
    const g = groups[b % groups.length];
    const syms = src.includes('|') ? g.split(/\s+/).filter(Boolean) : [g];
    const each = beatsPerBar / syms.length;
    out.push(syms.map((s, i) => ({ chord: parseChord(s), from: i * each, to: (i + 1) * each })));
  }
  return out;
}

/** Chord tones as MIDI notes, voiced close around `center` (a pad in the middle of the keyboard). */
function voiceChord(ch, center = 60) {
  const notes = ch.tones.map((t) => {
    let m = 48 + ((ch.root + t) % 12);
    while (m < center - 7) m += 12;
    while (m > center + 7) m -= 12;
    return m;
  });
  return [...new Set(notes)].sort((a, b) => a - b);
}
const bassNote = (ch, octave = 2) => 12 * (octave + 1) + ch.bass;

/* ---------------------------------------------------------------- instruments */

/**
 * A note on an instrument: a mono (or stereo) buffer. `gate` is how long the key is held, in seconds.
 * `m` is a MIDI note number and is handed to the synthesizer AS one (`midi:`), never as a bare number in `freq`:
 * a bare number there is hertz. Only the organ converts, because a harmonic is a multiple of hertz, not of a note.
 */
export const INSTRUMENTS = {
  'pulse-lead': { about: 'a narrow pulse lead with a late vibrato: the classic game melody', role: 'lead', play: (m, gate, v) => voice({ wave: 'pulse', duty: 0.25, midi: m, gate, env: { a: 0.004, d: 0.15, s: 0.62, r: 0.07 }, vibrato: { rate: 5.5, depth: 0.12, delay: 0.18 }, filter: { type: 'lowpass', freq: 5200 }, gain: v }) },
  'square-lead': { about: 'a hollow square lead: brighter, more 8-bit', role: 'lead', play: (m, gate, v) => voice({ wave: 'square', midi: m, gate, env: { a: 0.003, d: 0.12, s: 0.6, r: 0.06 }, filter: { type: 'lowpass', freq: 4200 }, gain: v * 0.8 }) },
  'saw-lead': { about: 'two detuned saws, filtered: a fat synth lead', role: 'lead', play: (m, gate, v) => mixMono([voice({ wave: 'saw', midi: m + 0.07, gate, env: { a: 0.008, d: 0.2, s: 0.7, r: 0.1 }, filter: { type: 'lowpass', freq: 3400, q: 0.9 }, gain: v * 0.55 }), voice({ wave: 'saw', midi: m - 0.07, phase: 0.37, gate, env: { a: 0.008, d: 0.2, s: 0.7, r: 0.1 }, filter: { type: 'lowpass', freq: 3400, q: 0.9 }, gain: v * 0.55 })]) },
  'soft-lead': { about: 'a triangle with vibrato: a gentle flute-like line', role: 'lead', play: (m, gate, v) => voice({ wave: 'triangle', midi: m, gate, env: { a: 0.03, d: 0.2, s: 0.8, r: 0.15 }, vibrato: { rate: 5, depth: 0.15, delay: 0.2 }, gain: v }) },
  bell: { about: 'an FM bell: sparkle, a music box, a menu theme', role: 'lead', play: (m, gate, v) => voice({ fm: { ratio: 3.5, index: 2.4, decay: 0.3 }, midi: m, gate, env: { a: 0.001, d: 1.4, s: 0, r: 0.6, curve: 2.4 }, gain: v * 0.8, length: Math.max(gate, 1.4) }) },
  epiano: { about: 'an FM electric piano: warm chords and lines', role: 'keys', play: (m, gate, v) => voice({ fm: { ratio: 1, index: 1.6, decay: 0.45 }, midi: m, gate, env: { a: 0.002, d: 1.2, s: 0.25, r: 0.25 }, gain: v * 0.8 }) },
  pluck: { about: 'a plucked string (Karplus-Strong): arpeggios, a harp, a koto', role: 'keys', play: (m, gate, v) => pluck({ midi: m, gate, bright: 0.55, gain: v * 0.9 }) },
  organ: { about: 'three sine harmonics: an organ, a calm pad', role: 'keys', play: (m, gate, v) => mixMono([1, 2, 3].map((h, i) => voice({ wave: 'sine', freq: hzOfMidi(m) * h, gate, env: { a: 0.01, d: 0.1, s: 0.9, r: 0.08 }, gain: v * [0.6, 0.3, 0.15][i] }))) },
  pad: { about: 'three detuned saws, slow and filtered: a wide, soft bed', role: 'pad', stereo: true, play: (m, gate, v) => {
    const len = gate + 0.9;
    const out = stereo(len);
    [[-0.1, -0.6], [0, 0], [0.1, 0.6]].forEach(([det, pan], i) => addInto(out, voice({ wave: 'saw', midi: m + det, phase: i * 0.31, gate, env: { a: 0.35, d: 0.5, s: 0.8, r: 0.8 }, filter: { type: 'lowpass', freq: 1500, q: 0.7 }, gain: v * 0.4 }), { pan }));
    return out;
  } },
  'warm-pad': { about: 'soft triangles and a sine: a darker, calmer bed', role: 'pad', play: (m, gate, v) => mixMono([voice({ wave: 'triangle', midi: m, gate, env: { a: 0.5, d: 0.5, s: 0.85, r: 1.0 }, gain: v * 0.6 }), voice({ wave: 'sine', midi: m + 12, gate, env: { a: 0.6, d: 0.5, s: 0.7, r: 1.0 }, gain: v * 0.2 })]) },
  'saw-bass': { about: 'a filtered saw bass with a pluck on the filter', role: 'bass', play: (m, gate, v) => voice({ wave: 'saw', midi: m, gate, env: { a: 0.003, d: 0.25, s: 0.7, r: 0.05 }, filter: { type: 'lowpass', freq: 1800, to: 420, time: 0.18, q: 1.1 }, gain: v }) },
  'square-bass': { about: 'a square bass: chiptune', role: 'bass', play: (m, gate, v) => voice({ wave: 'square', midi: m, gate, env: { a: 0.002, d: 0.1, s: 0.8, r: 0.04 }, filter: { type: 'lowpass', freq: 1400 }, gain: v * 0.8 }) },
  'triangle-bass': { about: 'a triangle bass: the 8-bit console bass', role: 'bass', play: (m, gate, v) => voice({ wave: 'triangle', midi: m, gate, env: { a: 0.002, d: 0.05, s: 0.95, r: 0.03 }, gain: v }) },
  'sub-bass': { about: 'a sine sub with a little edge (phones need the edge to hear it)', role: 'bass', play: (m, gate, v) => mixMono([voice({ wave: 'sine', midi: m, gate, env: { a: 0.004, d: 0.1, s: 0.9, r: 0.06 }, gain: v }), voice({ wave: 'saw', midi: m + 12, gate, env: { a: 0.004, d: 0.1, s: 0.9, r: 0.06 }, filter: { type: 'lowpass', freq: 900 }, gain: v * 0.18 })]) },
  kit: { about: 'synthesized drums (kick, snare, clap, hats, toms)', role: 'drums' },
  'chip-kit': { about: 'crunchy 8-bit drums', role: 'drums' },
};

/* ---------------------------------------------------------------- patterns */

const GROOVES = {
  // One bar at 4 steps a beat (16 steps in 4/4); stretched or cut to other bar lengths.
  four: { kick: 'x...x...x...x...', clap: '....x.......x...', hat: '..x...x...x...x.', openhat: '' },
  backbeat: { kick: 'x.......x.x.....', snare: '....x.......x...', hat: 'x.x.x.x.x.x.x.x.' },
  half: { kick: 'x...........x...', snare: '........x.......', hat: 'x.x.x.x.x.x.x.x.' },
  break: { kick: 'x.........x..x..', snare: '....x..x.x..x...', hat: 'x.xxx.x.x.xxx.x.' },
  shuffle: { kick: 'x.....x...x.....', snare: '....x.......x..x', hat: 'x..x..x..x..x..x' },
  hats: { hat: 'x.x.x.x.x.x.x.x.' },
  pulse: { kick: 'x...x...x...x...' },
  none: {},
};
const FILL = { snare: '........x.x.xxxx', tom: '....x.x.........' };

function tokens(text) {
  const t = [];
  const re = /\[[^\]]*\]!?(\*\d+)?|\S+/g;
  let m;
  while ((m = re.exec(text))) t.push(m[0]);
  return t;
}

/** Parse a notes pattern for one section into events { step, steps, notes: [midi], accent }. */
export function parseNotes(text, { stepsPerBar, bars, octave = 0, where = 'a pattern' }) {
  const events = [];
  let step = 0;
  const barMarks = [];
  let last = null;
  for (const tok of tokens(String(text))) {
    if (tok === '|') { barMarks.push(step); continue; }
    const mult = /\*(\d+)$/.exec(tok);
    const n = mult ? Number(mult[1]) : 1;
    const body = mult ? tok.slice(0, -mult[0].length) : tok;
    if (body === '.') { step += n; last = null; continue; }
    if (body === '-') { if (last) last.steps += n; step += n; continue; }
    const accent = body.endsWith('!');
    const core = accent ? body.slice(0, -1) : body;
    const names = core.startsWith('[') ? core.slice(1, -1).trim().split(/[\s,]+/) : [core];
    let notes;
    try { notes = names.map((x) => midiOf(x) + 12 * octave); } catch (e) { throw new Error(`${where}: ${e.message}`); }
    last = { step, steps: n, notes, accent };
    events.push(last);
    step += n;
  }
  for (const [i, s] of barMarks.entries()) {
    if (s !== (i + 1) * stepsPerBar) throw new Error(`${where}: bar ${i + 1} has ${s - (barMarks[i - 1] ?? 0)} steps, a bar here is ${stepsPerBar} (steps a beat × beats a bar). A token is one step: for eighth notes give the instrument "stepsPerBeat": 2`);
  }
  if (barMarks.length && step % stepsPerBar !== 0) throw new Error(`${where}: the last bar has ${step - barMarks.length * stepsPerBar} steps, a bar here is ${stepsPerBar}`);
  if (step > stepsPerBar * bars) throw new Error(`${where}: ${step} steps is longer than the section (${bars} bars × ${stepsPerBar})`);
  // A pattern shorter than the section repeats to fill it (a one-bar riff over eight bars).
  const len = barMarks.length ? step : Math.ceil(step / stepsPerBar) * stepsPerBar;
  if (len > 0 && len < stepsPerBar * bars) {
    const base = events.slice();
    for (let off = len; off < stepsPerBar * bars; off += len) for (const e of base) if (e.step + off < stepsPerBar * bars) events.push({ ...e, step: e.step + off });
  }
  return events;
}

/** Events generated from the chords: a bass line, a pad, stabs or an arpeggio. */
export function fromChords(kind, cbars, { stepsPerBeat, beatsPerBar, octave = 0 }) {
  const [name, rateArg] = kind.split(':');
  const spb = stepsPerBeat * beatsPerBar;
  const events = [];
  const every = (div) => Math.max(1, Math.round(spb / div));
  cbars.forEach((chords, b) => {
    for (const c of chords) {
      const from = b * spb + Math.round(c.from * stepsPerBeat);
      const to = b * spb + Math.round(c.to * stepsPerBeat);
      const bass = bassNote(c.chord) + 12 * octave;
      const tones = voiceChord(c.chord, 60 + 12 * octave);
      if (name === 'root') events.push({ step: from, steps: to - from, notes: [bass] });
      else if (name === 'root8' || name === 'pulse' || name === 'octaves') {
        const div = name === 'pulse' ? 16 : Number(rateArg) || 8;
        const st = every(div * (beatsPerBar / 4));
        for (let s = from, i = 0; s < to; s += st, i++) events.push({ step: s, steps: Math.max(1, st - (name === 'pulse' ? 0 : 0)), notes: [name === 'octaves' && i % 2 ? bass + 12 : bass], accent: s === from });
      } else if (name === 'chords') events.push({ step: from, steps: to - from, notes: tones });
      else if (name === 'stabs') {
        const st = every(8 * (beatsPerBar / 4));
        for (let s = from + st; s < to; s += st * 2) events.push({ step: s, steps: Math.max(1, Math.round(st / 2)), notes: tones });
      } else if (name.startsWith('arp')) {
        const div = Number(rateArg) || 16;
        const st = every(div * (beatsPerBar / 4));
        const up = [...tones, tones[0] + 12];
        const seq = name === 'arp-down' ? [...up].reverse() : name === 'arp-updown' ? [...up, ...up.slice(1, -1).reverse()] : up;
        for (let s = from, i = 0; s < to; s += st, i++) events.push({ step: s, steps: st, notes: [seq[i % seq.length] + 12] });
      } else throw new Error(`unknown pattern "${kind}" (root, root8, pulse, octaves, chords, stabs, arp, arp-down, arp-updown)`);
    }
  });
  return events;
}

/** Drum hits for a section: [{ step, drum, accent }]. */
export function drumHits(pattern, { stepsPerBeat, beatsPerBar, bars }) {
  let spec = pattern;
  let fill = false;
  if (typeof spec === 'string') {
    fill = spec.includes('+fill');
    const name = spec.replace('+fill', '').replace(/^drums:/, '').trim();
    spec = GROOVES[name];
    if (!spec) throw new Error(`unknown groove "${name}" (${Object.keys(GROOVES).join(', ')}), or write the steps yourself`);
  } else if (spec && typeof spec === 'object') fill = Boolean(spec.fill);
  const spb = stepsPerBeat * beatsPerBar;
  const hits = [];
  for (let b = 0; b < bars; b++) {
    const src = fill && b === bars - 1 ? { ...spec, ...FILL } : spec;
    for (const [kind, line] of Object.entries(src)) {
      if (kind === 'fill' || !line) continue;
      const cells = String(line).replace(/\s+/g, '');
      // A line written at 4 steps a beat is resampled to this score's steps.
      const perBeat = cells.length / beatsPerBar >= 1 ? cells.length / beatsPerBar : 4;
      for (let i = 0; i < cells.length; i++) {
        const c = cells[i];
        if (c !== 'x' && c !== 'X') continue;
        const s = Math.round((i / perBeat) * stepsPerBeat);
        if (s >= spb) continue;
        hits.push({ step: b * spb + s, drum: kind, accent: c === 'X' });
      }
    }
  }
  return hits;
}

/* ---------------------------------------------------------------- render */

const clampPan = (p) => Math.max(-1, Math.min(1, Number(p) || 0));

/** Check a score and fill its defaults. Throws a sentence a person can act on. */
export function normalise(score) {
  const s = { beatsPerBar: 4, stepsPerBeat: 4, swing: 0, seed: 1, ...score };
  if (!(s.bpm >= 40 && s.bpm <= 240)) throw new Error('bpm must be 40..240');
  if (!Array.isArray(s.sections) || !s.sections.length) throw new Error('a score needs sections: [{ "name", "bars", "chords", "play": { … } }]');
  if (!s.instruments || typeof s.instruments !== 'object') throw new Error('a score needs instruments: { "lead": { "preset": "pulse-lead" }, … }');
  for (const [name, ins] of Object.entries(s.instruments)) {
    if (!INSTRUMENTS[ins.preset]) throw new Error(`instrument "${name}": no preset "${ins.preset}" (${Object.keys(INSTRUMENTS).join(', ')})`);
  }
  const names = new Set();
  for (const sec of s.sections) {
    if (!sec.name || names.has(sec.name)) throw new Error(`every section needs its own name (found "${sec.name}")`);
    names.add(sec.name);
    if (!(Number.isInteger(sec.bars) && sec.bars >= 1 && sec.bars <= 64)) throw new Error(`section "${sec.name}": bars must be a whole number 1..64`);
    for (const inst of Object.keys(sec.play ?? {})) if (!s.instruments[inst]) throw new Error(`section "${sec.name}" plays "${inst}", which is not in instruments`);
  }
  s.arrangement = s.arrangement ?? s.sections.map((x) => x.name);
  for (const a of s.arrangement) if (!names.has(a)) throw new Error(`arrangement names "${a}", which is not a section`);
  return s;
}

/**
 * Render a list of section names (an arrangement) to stems and a mix.
 * Returns { stems: { name: stereo }, mix: stereo, grid }.
 * `sameSeeds` gives every section in the list the same drum noise (by default each place in the arrangement
 * has its own, so a repeat is not a photocopy): a loop is cut from three copies that must be the same copy.
 * `period` (seconds) starts each section in the list exactly that far after the one before, instead of on its
 * bar line: a loop is a whole number of samples, and at a tempo whose bar is not (140 bpm: 82285.71 samples) the
 * third copy would otherwise start a fraction of a sample away from where the cut expects it.
 */
export function render(scoreIn, { sections: order = null, tail = 2.5, sameSeeds = false, period = null } = {}) {
  const s = normalise(scoreIn);
  const list = order ?? s.arrangement;
  const beat = 60 / s.bpm;
  const step = beat / s.stepsPerBeat;
  const spb = s.stepsPerBeat * s.beatsPerBar;
  const barSeconds = beat * s.beatsPerBar;
  const byName = Object.fromEntries(s.sections.map((x) => [x.name, x]));
  const totalBars = list.reduce((a, n) => a + byName[n].bars, 0);
  const length = totalBars * barSeconds + tail;
  const stems = Object.fromEntries(Object.keys(s.instruments).map((k) => [k, stereo(length)]));
  const kicks = [];
  const grid = { bpm: s.bpm, beatsPerBar: s.beatsPerBar, barSeconds, bars: totalBars, seconds: totalBars * barSeconds, sections: [] };
  const swingAt = (st) => (st % 2 === 1 ? s.swing * step : 0);
  let bar0 = 0;
  for (const [si, name] of list.entries()) {
    const sec = byName[name];
    const t0 = period !== null ? si * period : bar0 * barSeconds;
    grid.sections.push({ name, bar: bar0, at: +t0.toFixed(6), bars: sec.bars });
    const cbars = chordBars(sec.chords, sec.bars, s.beatsPerBar);
    for (const [inst, pat] of Object.entries(sec.play ?? {})) {
      const ins = s.instruments[inst];
      const def = INSTRUMENTS[ins.preset];
      const vel = (a) => (a ? 1 : 0.82);
      if (def.role === 'drums') {
        const hits = drumHits(pat, { stepsPerBeat: s.stepsPerBeat, beatsPerBar: s.beatsPerBar, bars: sec.bars });
        for (const h of hits) {
          const at = t0 + h.step * step + swingAt(h.step);
          const kind = h.drum === 'tom' ? 'tom' : h.drum;
          let buf = drum(kind, { gain: vel(h.accent), seed: 7 + (sameSeeds ? 0 : si) * 131 + h.step, tone: ins.tone ?? 0 });
          if (ins.preset === 'chip-kit') { for (let i = 0, held = 0; i < buf.length; i++) { if (i % 3 === 0) held = Math.round(buf[i] * 16) / 16; buf[i] = held; } }
          const pan = { hat: 0.25, openhat: 0.25, shaker: -0.3, tom: -0.2, rim: 0.2 }[kind] ?? 0;
          addInto(stems[inst], buf, { at, pan });
          if (kind === 'kick') kicks.push(at);
        }
        continue;
      }
      // A pattern's own grid: "stepsPerBeat" on the pattern or the instrument (2 = eighth notes), else the score's.
      const ps = Number((typeof pat === 'object' && pat !== null && pat.stepsPerBeat) || ins.stepsPerBeat || s.stepsPerBeat);
      const pstep = beat / ps;
      const opts = { stepsPerBeat: ps, beatsPerBar: s.beatsPerBar, octave: ins.octave ?? 0 };
      const text = typeof pat === 'object' && pat !== null ? pat.notes : pat;
      const isGen = /^(root|root8|pulse|octaves|chords|stabs|arp)/.test(String(text));
      const events = isGen ? fromChords(String(text), cbars, opts) : parseNotes(text, { stepsPerBar: ps * s.beatsPerBar, bars: sec.bars, octave: ins.octave ?? 0, where: `section "${name}", ${inst}` });
      for (const ev of events) {
        const at = t0 + ev.step * pstep + (ev.step % 2 === 1 ? s.swing * pstep : 0);
        const gate = Math.max(0.03, ev.steps * pstep * (ins.legato ?? 0.92));
        for (const note of ev.notes) {
          const buf = def.play(note, gate, vel(ev.accent) / Math.sqrt(ev.notes.length));
          addInto(stems[inst], buf, { at, pan: clampPan(ins.pan) });
        }
      }
    }
    bar0 += sec.bars;
  }
  // Per-instrument effects: an echo in beats, a duck under the kick (the pump), a level in dB.
  const room = stereo(length);
  for (const [inst, ins] of Object.entries(s.instruments)) {
    let st = stems[inst];
    if (ins.echo) {
      const e = echo(st, { time: (ins.echo.beats ?? 0.75) * beat, feedback: ins.echo.feedback ?? 0.3, mix: ins.echo.mix ?? 0.22, pingpong: ins.echo.pingpong ?? true, tail: 0 });
      st = { L: e.L.subarray(0, st.L.length), R: e.R.subarray(0, st.R.length) };
    }
    if (ins.duck && kicks.length) {
      const depth = Math.min(0.95, Number(ins.duck));
      const rel = 0.6 * beat;
      const ks = kicks.slice().sort((a, b) => a - b);
      let k = 0;
      for (let i = 0; i < st.L.length; i++) {
        const t = i / RATE;
        while (k + 1 < ks.length && ks[k + 1] <= t) k++;
        const d = t >= ks[k] ? t - ks[k] : Infinity;
        const g = d === Infinity ? 1 : 1 - depth * Math.exp(-d / (rel / 3));
        st.L[i] *= g; st.R[i] *= g;
      }
    }
    const g = dbToGain(ins.db ?? -10);
    for (let i = 0; i < st.L.length; i++) { st.L[i] *= g; st.R[i] *= g; }
    stems[inst] = st;
    const send = ins.reverb ?? 0.12;
    if (send > 0) addInto(room, st, { gain: send });
  }
  const wet = reverb(room, { room: s.room ?? 0.55, damp: 0.45, mix: 1, tail: 0 });
  // reverb() returns dry + wet: keep only the wet part for the room stem.
  const roomStem = stereo(length);
  for (let i = 0; i < roomStem.L.length; i++) { roomStem.L[i] = wet.L[i] - room.L[i]; roomStem.R[i] = wet.R[i] - room.R[i]; }
  stems.reverb = roomStem;
  const mix = stereo(length);
  for (const st of Object.values(stems)) addInto(mix, st);
  dcBlock(mix);
  return { stems, mix, grid, score: s };
}

/**
 * One section as a seamless loop: rendered three times in a row, the middle copy kept, so whatever rings over
 * from the copy before it is already in its head. Returns { mix, stems, seconds, bars, seam }.
 *
 * `gain` and `ceilingDb` are the master's: the level and the limiter are applied HERE, across all three copies,
 * and then the middle is cut. A limiter run over the cut loop alone starts at full gain on its first sample and
 * ends wherever the last bar left it, and that step of gain at the wrap is a click the unlimited loop never had
 * (measured: loops with a seam of 0.1 came out at 2 to 15 once limited that way).
 *
 * `seam` is measured against the truth this render has and a finished file does not: the sample the music
 * really played next (the first sample of the third copy). See seamRatio.
 */
export function loop(scoreIn, name, { gain = 1, ceilingDb = null } = {}) {
  const s = normalise(scoreIn);
  const sec = s.sections.find((x) => x.name === name);
  if (!sec) throw new Error(`no section "${name}" to loop`);
  const barSeconds = (60 / s.bpm) * s.beatsPerBar;
  const n = Math.round(sec.bars * barSeconds * RATE);
  const r = render(s, { sections: [name, name, name], tail: 0, sameSeeds: true, period: n / RATE });
  const from = n;
  if (gain !== 1) for (const ch of [r.mix.L, r.mix.R]) for (let i = 0; i < ch.length; i++) ch[i] *= gain;
  if (ceilingDb !== null) limit(r.mix, { ceiling: dbToGain(ceilingDb), releaseMs: 150 });
  const cut = (b) => ({ L: b.L.slice(from, from + n), R: b.R.slice(from, from + n) });
  const stems = Object.fromEntries(Object.entries(r.stems).map(([k, v]) => [k, cut(v)]));
  const mix = cut(r.mix);
  const next = from + n < r.mix.L.length ? { L: r.mix.L[from + n], R: r.mix.R[from + n] } : null;
  return { mix, stems, seconds: n / RATE, bars: sec.bars, seam: seamRatio(mix, next) };
}

/**
 * How wrong the wrap of a loop is, against the music's own sample-to-sample steps (1 or less is seamless).
 *
 * With `next` (the sample the music played right after the loop's last one, which loop() has), the number is how
 * far the loop's FIRST sample is from that: 0 means the wrap is exactly what the music did. That is the honest
 * measure, because a jump at the wrap is often the music's own (a plucked string or a drum starting on the bar
 * line, the edge of a saw or a square falling on the last sample), and calling that a seam fails good loops.
 * Without `next` (a loop cut from a finished file) the whole jump across the wrap is all there is to measure.
 */
export function seamRatio(buf, next = null) {
  const n = buf.L.length;
  const steps = [];
  for (let i = 1; i < n; i += 97) steps.push(Math.abs(buf.L[i] - buf.L[i - 1]) + Math.abs(buf.R[i] - buf.R[i - 1]));
  steps.sort((a, b) => a - b);
  const typical = steps[Math.floor(steps.length * 0.95)] || 1e-6;
  const to = next ?? { L: buf.L[n - 1], R: buf.R[n - 1] };
  const jump = Math.abs(buf.L[0] - to.L) + Math.abs(buf.R[0] - to.R);
  return +(jump / typical).toFixed(3);
}

/** The seam a loop may have and still be called seamless, and the sentence for one that is over it. */
export const SEAM_LIMIT = 1;
export function seamWarning(section, seam) {
  if (!(seam > SEAM_LIMIT)) return null;
  return `loop "${section}": seam ${seam} is over ${SEAM_LIMIT}: the wrap will click or bump every time it comes round. Do not ship this loop as it is: something in the section does not repeat (a note or an echo longer than the section, a pattern that does not fill its bars); shorten it or make the section longer`;
}

/** Master: limit the peaks of a mix (the loudness target is applied by the caller with ffmpeg's measure). */
export function master(mix, { ceilingDb = -1.5 } = {}) {
  const p = peakOf(mix);
  if (!(p > 0)) throw new Error('the score rendered silence: check the sections play something');
  limit(mix, { ceiling: dbToGain(ceilingDb), releaseMs: 120, lookaheadMs: 4 });
  return mix;
}
