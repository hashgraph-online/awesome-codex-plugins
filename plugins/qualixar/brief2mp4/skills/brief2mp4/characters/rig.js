/*
 * rig.js: the character rig runtime. No dependencies; runs in a HyperFrames page, on a canvas, and in Node.
 *
 *   B2M.pose(character, track, t [, opts]) -> the transform of every part at time t
 *
 * The result is a pure function of (character, track, t, opts). It reads no clock and no unseeded randomness:
 * blinks and talk gestures come from a seeded hash of (character id, time bucket), so two renders of the same
 * frame match exactly.
 *
 * A track is a list of keys { t, pose, ease } or an object:
 *   { keys: [{ t, pose, ease }],            the ease shapes the move INTO that key (linear, in, out, inOut, sine, backOut, hold)
 *     move: [{ t, x, y, facing, walk, ease }], where it stands: absolute scene positions (x across, y of the feet); facing "left" or "right"; walk: true = walk to here
 *                                             (flip -1 or 1 is the older spelling); a key without x or y keeps opts.home
 *     layers: [{ cycle, from, to, steps }],  walk, run, wave, laugh, breath, talk; steps = new drawings per second
 *     visemes: [{ t, v }],                   the lip-sync track from scripts/lipsync.py
 *     blink: true, props: ["prop_kite"], fx: { speedLines: [[t0, t1]] },
 *     view: 'front' }                         a close-up head drawing that faces the camera (parts with a 'front' variant)
 * opts.scale is the character's size in the scene (for walk keys). opts.home = { x, y, flip } is where the character stands when a move key does not say (the scene's cast x and y).
 * opts.steps quantises time (a handmade skin holds each drawing for 1/steps of a second); leave it out for smooth motion.
 * Cycles hold their drawings at the layer's steps per second; opts.smooth: true (for a smooth skin) blends between them instead.
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.POSES)) require('./poses.js');
  const B = (g.B2M = g.B2M || {});
  const EPS = 1e-6;
  const CHANNELS = ['r', 'x', 'y', 'sx', 'sy'];
  const SPECIAL = new Set(['lift', 'smile', 'gaze', 'mouth', 'variants']);
  const clamp01 = (x) => Math.min(1, Math.max(0, x));
  const lerp = (a, b, k) => a + (b - a) * k;

  const EASE = {
    linear: (x) => x,
    in: (x) => x * x * x,
    out: (x) => 1 - Math.pow(1 - x, 3),
    inOut: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    sine: (x) => 0.5 - 0.5 * Math.cos(Math.PI * x),
    backOut: (x) => 1 + 2.70158 * Math.pow(x - 1, 3) + 1.70158 * Math.pow(x - 1, 2),
    hold: (x) => (x >= 1 ? 1 : 0),
  };

  function ease(name, x) {
    const f = EASE[name || 'inOut'];
    if (!f) throw new Error('unknown ease "' + name + '". Use one of: ' + Object.keys(EASE).join(', '));
    return f(clamp01(x));
  }

  // Seeded hash of (string, integer) to [0, 1). Same inputs, same number, on every machine.
  function hash(id, n) {
    let h = 2166136261;
    const s = String(id);
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    h ^= (Math.floor(n) + 0x9e3779b9) | 0;
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }

  const quantise = (t, steps) => (steps ? Math.floor(t * steps + EPS) / steps : t);
  const channels = (v) => (typeof v === 'number' ? { r: v } : v || {});
  const restOf = (k) => (k === 'sx' || k === 'sy' ? 1 : 0);

  function resolvePose(character, name) {
    const base = B.POSES[name];
    if (!base) throw new Error('unknown pose "' + name + '". Poses: ' + Object.keys(B.POSES).join(', '));
    const over = character.poseOverrides && character.poseOverrides[name];
    return over ? Object.assign({}, base, over) : base;
  }

  function mixPoses(a, b, k, nearest) {
    const out = {};
    const joints = new Set(Object.keys(a).concat(Object.keys(b)));
    joints.forEach((j) => {
      if (SPECIAL.has(j)) return;
      const ca = channels(a[j]), cb = channels(b[j]), o = {};
      CHANNELS.forEach((c) => {
        const va = ca[c] === undefined ? restOf(c) : ca[c], vb = cb[c] === undefined ? restOf(c) : cb[c];
        if (va !== restOf(c) || vb !== restOf(c)) o[c] = lerp(va, vb, k);
      });
      out[j] = o;
    });
    out.lift = lerp(a.lift || 0, b.lift || 0, k);
    out.smile = lerp(a.smile || 0, b.smile || 0, k);
    const ga = a.gaze || [0, 0], gb = b.gaze || [0, 0];
    out.gaze = [lerp(ga[0], gb[0], k), lerp(ga[1], gb[1], k)];
    out.mouth = nearest.mouth;
    out.variants = nearest.variants || {};
    return out;
  }

  function sampleKeys(character, keysIn, ts) {
    const keys = (keysIn && keysIn.length ? keysIn : [{ t: 0, pose: 'idle' }]).slice().sort((p, q) => p.t - q.t);
    let i = -1;
    for (let n = 0; n < keys.length; n++) if (keys[n].t <= ts + EPS) i = n;
    const first = resolvePose(character, keys[0].pose);
    if (i < 0) return mixPoses(first, first, 0, first);
    const a = resolvePose(character, keys[i].pose);
    if (i === keys.length - 1) return mixPoses(a, a, 0, a);
    const b = resolvePose(character, keys[i + 1].pose);
    const k = ease(keys[i + 1].ease, (ts - keys[i].t) / (keys[i + 1].t - keys[i].t));
    return mixPoses(a, b, k, k < 0.5 ? a : b);
  }

  function visemeAt(track, t) {
    if (!track || !track.length) return 'rest';
    let lo = 0, hi = track.length - 1, found = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (track[mid].t <= t + EPS) { found = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return found < 0 ? 'rest' : track[found].v;
  }

  // A pose gives scale as the size itself (sy: 1.15); the accumulator adds deltas, so take away the 1 first.
  const asDelta = (value) => { const c = channels(value), o = Object.assign({}, c); ['sx', 'sy'].forEach((k) => { if (c[k] !== undefined) o[k] = c[k] - 1; }); return o; };

  function addDelta(acc, joint, value, w) {
    const target = acc[joint] || (acc[joint] = { r: 0, x: 0, y: 0, sx: 1, sy: 1 });
    const ch = channels(value);
    CHANNELS.forEach((c) => { if (ch[c] !== undefined) target[c] += ch[c] * w; });
  }

  function layerWeight(ts, layer) {
    const from = layer.from || 0, to = layer.to === undefined ? Infinity : layer.to, fade = layer.fade === undefined ? 0.1 : layer.fade;
    if (ts < from - EPS || ts > to + EPS) return 0;
    const inK = fade > 0 ? clamp01((ts - from) / fade) : 1;
    const outK = fade > 0 && Number.isFinite(to) ? clamp01((to - ts) / fade) : 1;
    return Math.min(inK, outK) * (layer.amp === undefined ? 1 : layer.amp);
  }

  function cycleDeltas(layer, ts, smooth) {
    const def = B.CYCLES[layer.cycle];
    const steps = layer.steps || def.steps, n = def.frames;
    const c = (ts - (layer.from || 0)) * steps + EPS;
    const useSmooth = layer.smooth !== undefined ? layer.smooth : def.smooth || smooth;
    const idx = useSmooth ? c : Math.floor(c);
    return def.fn((((idx % n) + n) % n) / n, useSmooth);
  }

  function talkDeltas(character, layer, ts, smooth) {
    const rate = layer.rate || 7;
    const k = (ts - (layer.from || 0)) * rate + EPS, i = Math.floor(k), f = k - i;
    const mix = smooth ? f * f * (3 - 2 * f) : 0;
    const v = (salt) => lerp(hash(character.id + salt, i), hash(character.id + salt, i + 1), mix) - 0.5;
    const big = lerp(hash(character.id + 'g', i), hash(character.id + 'g', i + 1), mix);
    const gesture = big > 0.62 ? big : 0;
    return { head: 5 * v('a'), torso: 1.2 * v('b'), armN_up: 18 * gesture, armN_lo: 14 * gesture, handN: 10 * gesture, armF_up: 6 * gesture * (v('c') + 0.5), head_y: 2.5 * v('d') };
  }

  function applyLayers(character, track, ts, opts, acc, speaking) {
    const smooth = !!opts.smooth, active = [];
    (track.layers || []).forEach((layer) => {
      const w = layerWeight(ts, layer);
      if (w <= 0) return;
      active.push(layer.cycle);
      let deltas;
      if (layer.cycle === 'talk') {
        deltas = talkDeltas(character, layer, ts, smooth);
        const wt = w * (speaking ? 1 : 0.25);
        const { head_y: dy, ...rest } = deltas;
        Object.keys(rest).forEach((j) => addDelta(acc, j, rest[j], wt));
        addDelta(acc, 'head', { y: dy }, wt);
        return;
      }
      if (!B.CYCLES[layer.cycle]) throw new Error('unknown cycle "' + layer.cycle + '". Cycles: talk, ' + Object.keys(B.CYCLES).join(', '));
      deltas = cycleDeltas(layer, ts, smooth);
      Object.keys(deltas).forEach((j) => addDelta(acc, j, deltas[j], w));
    });
    return active;
  }

  function blinkAmount(character, track, ts) {
    if (track.blink === false || character.blink === false) return 0;
    // one blink in every 4 s window, at a seeded moment 0.5 to 2 s in: blinks come 2.5 to 5.5 s apart
    const period = 4.0, k = Math.floor(ts / period + EPS);
    const start = k * period + 0.5 + hash(character.id, k) * 1.5, u = (ts - start) / 0.18;
    if (u < 0 || u > 1) return 0;
    return u < 0.4 ? u / 0.4 : 1 - (u - 0.4) / 0.6;
  }

  // Outside the words a mouth stays closed, so a listener never looks as if they are talking. The pose can still
  // smile or frown (`smile`). A mouth shape is shown only when the track asks for it: a key with { mouth: "O" }
  // holds that shape until the next key, or the track sets poseMouths: true to use each pose's own mouth.
  function heldMouth(track, base, ts) {
    const keys = (track.keys || []).slice().sort((p, q) => p.t - q.t);
    let hit = null;
    keys.forEach((k) => { if (k.t <= ts + EPS) hit = k; });
    if (hit && hit.mouth) return hit.mouth;
    return track.poseMouths ? base.mouth || 'rest' : 'rest';
  }

  // Where the character stands. Move keys hold absolute positions in scene units (the y of the feet on screen);
  // a key that leaves x or y out keeps the character's home position, and with no move keys it stays at home.
  // facing "left" or "right" (flip -1 or 1 is the older spelling) turns it; the facing of the latest key holds.
  const facingOf = (m, fallback) => (m.facing === 'left' ? -1 : m.facing === 'right' ? 1 : m.flip === undefined ? fallback : m.flip);

  // A move key with walk: true means "walk to here from the key before": the walk cycle plays between the two keys at
  // the speed that plants the feet (see walkSteps), the move is a steady glide, and unless a key says facing the
  // character turns to face the way it walks. A facing, whether a key set it or a walk turned the character, holds
  // until a key sets another: it carries on after the last key.
  function sampleMove(moves, ts, home) {
    const h = Object.assign({ x: null, y: null, flip: 1 }, home);
    if (!moves || !moves.length) return { x: h.x, y: h.y, flip: h.flip };
    const keys = moves.slice().sort((p, q) => p.t - q.t);
    let i = -1;
    for (let n = 0; n < keys.length; n++) if (keys[n].t <= ts + EPS) i = n;
    const xOf = (m) => (m.x === undefined ? h.x : m.x), told = (m) => m.facing !== undefined || m.flip !== undefined;
    const heading = (m, next) => (next && next.walk && !told(m) && xOf(next) !== null && xOf(m) !== null && xOf(next) !== xOf(m) ? Math.sign(xOf(next) - xOf(m)) : null);
    const facingAfter = (upto) => {   // the way the character faces on the segment that starts at key `upto`
      let f = h.flip;
      for (let n = 0; n <= upto; n++) f = told(keys[n]) ? facingOf(keys[n], f) : heading(keys[n], keys[n + 1]) || f;
      return f;
    };
    const val = (n) => ({ x: xOf(keys[n]), y: keys[n].y === undefined ? h.y : keys[n].y, flip: facingAfter(Math.max(0, n)) });
    const mix = (u, v, k) => (u === null ? v : v === null ? u : lerp(u, v, k));
    if (i < 0) return val(0);
    const a = val(i);
    if (i === keys.length - 1) return a;
    const k = ease(keys[i + 1].walk ? 'linear' : keys[i + 1].ease, (ts - keys[i].t) / (keys[i + 1].t - keys[i].t)), b = val(i + 1);
    return { x: mix(a.x, b.x, k), y: mix(a.y, b.y, k), flip: a.flip };
  }

  // Drawings a second the walk cycle needs so that a character `scale` times its drawn size, covering `distance` pixels
  // in `seconds`, does not slide its feet: four leg lengths times the sine of the swing is the ground one stride covers.
  function walkSteps(character, distance, seconds, scale) {
    const def = B.CYCLES.walk;
    return ((distance / seconds) * def.frames) / (4 * character.proportions.legLength * Math.sin(B.rad(def.amp)) * (scale || 1));
  }

  function walkLayers(character, moves, scale, home) {
    const keys = (moves || []).slice().sort((p, q) => p.t - q.t), out = [];
    for (let n = 1; n < keys.length; n++) {
      const a = keys[n - 1], b = keys[n], x0 = a.x === undefined ? (home && home.x) : a.x, x1 = b.x === undefined ? (home && home.x) : b.x;
      if (!b.walk || b.t <= a.t || x0 === null || x0 === undefined || x1 === null || x1 === undefined || x0 === x1) continue;
      out.push({ cycle: 'walk', from: a.t, to: b.t, steps: walkSteps(character, Math.abs(x1 - x0), b.t - a.t, scale), fade: Math.min(0.1, (b.t - a.t) / 4) });
    }
    return out;
  }

  function visibleProps(list, ts) {
    return (list || []).filter((p) => typeof p === 'string' || ((p.from === undefined || ts >= p.from) && (p.to === undefined || ts <= p.to))).map((p) => (typeof p === 'string' ? p : p.id));
  }

  function inRanges(ranges, ts) {
    return (ranges || []).some((r) => ts >= r[0] && ts <= r[1]);
  }

  const clampScale = (v) => Math.min(1.3, Math.max(0.05, v));   // a part never grows past 130% or vanishes, whatever the mix
  const signOf = (part) => (part.sign !== undefined ? part.sign : B.SIGN[part.id] === undefined ? 1 : B.SIGN[part.id]);

  function pose(character, trackIn, t, opts) {
    const o = opts || {};
    const track = Array.isArray(trackIn) ? { keys: trackIn } : trackIn || {};
    const steps = o.steps !== undefined ? o.steps : track.steps || null;
    const ts = quantise(t, steps);
    const base = sampleKeys(character, track.keys, ts);
    const vis = track.visemes && track.visemes.length ? track.visemes.slice().sort((p, q) => p.t - q.t) : null;
    const inSpeech = vis && ts >= vis[0].t - EPS && ts <= vis[vis.length - 1].t + EPS;
    const viseme = inSpeech ? visemeAt(vis, ts) : heldMouth(track, base, ts);
    const acc = {};
    Object.keys(base).forEach((j) => { if (!SPECIAL.has(j)) addDelta(acc, j, asDelta(base[j]), 1); });
    const own = (track.layers || []).concat(walkLayers(character, track.move, o.scale, o.home));
    const layers = track.breath === false ? own : [{ cycle: 'breath' }].concat(own);
    const cycles = applyLayers(character, Object.assign({}, track, { layers }), ts, o, acc, viseme !== 'rest');
    const blink = blinkAmount(character, track, ts);
    const legLength = (character.proportions && character.proportions.legLength) || 0;
    addDelta(acc, 'hip', { y: base.lift * legLength }, 1);
    ['eyeN', 'eyeF'].forEach((j) => { if (blink) addDelta(acc, j, { sy: -0.92 * blink * (channels(acc[j]).sy || 1) }, 1); });
    ['pupilN', 'pupilF'].forEach((j) => addDelta(acc, j, { x: base.gaze[0] * 3, y: base.gaze[1] * 3 }, 1));
    const parts = {};
    character.parts.forEach((p) => {
      const a = acc[p.id] || { r: 0, x: 0, y: 0, sx: 1, sy: 1 };
      parts[p.id] = { r: a.r * signOf(p), x: a.x, y: a.y, sx: clampScale(a.sx), sy: clampScale(a.sy) };
    });
    return {
      t, ts, frame: steps ? Math.round(ts * steps) : Math.round(t * 60), parts, viseme, blink, smile: base.smile, lift: base.lift, cycles,
      variants: base.variants, view: track.view || 'side',
      move: sampleMove(track.move, ts, o.home), props: visibleProps(track.props, ts), speedLines: inRanges(track.fx && track.fx.speedLines, ts),
    };
  }

  // Units per second a walking character must travel for its feet to stay planted: four leg lengths times the
  // sine of the swing, per cycle. Use it for the move track of a walk layer.
  function strideSpeed(character, cycle, steps) {
    const def = B.CYCLES[cycle || 'walk'];
    return (4 * character.proportions.legLength * Math.sin(B.rad(def.amp)) * (steps || def.steps)) / def.frames;
  }

  Object.assign(B, { pose, visemeAt, hash, ease, quantise, strideSpeed, walkSteps, walkLayers, EASES: Object.keys(EASE) });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
