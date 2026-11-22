/*
 * poses.js: the pose and cycle library for the character kit. Data only, no logic that reads a clock.
 *
 * Angles are degrees. For arms, hands and legs, a positive angle swings the limb FORWARD (the way the character
 * faces); for the torso, head, brows and feet a positive angle turns clockwise on screen (lean forward, toe down).
 * A joint can also be an object { r, x, y, sx, sy } (rotation, offset in units, scale). Joints a pose leaves out
 * stay at rest (0). `lift` moves the whole body up (negative) or down (positive) as a fraction of the leg length,
 * so one pose fits a child and an adult. `variants` picks a drawing for a part (an open hand for a wave, a pointing
 * finger for a point): { handN: 'open' }.
 */
(function (g) {
  'use strict';
  const B = (g.B2M = g.B2M || {});

  const VISEMES = ['rest', 'AI', 'E', 'O', 'U', 'MBP', 'FV', 'L', 'etc'];

  const POSES = {
    idle: { armN_up: 5, armN_lo: 10, handN: 8, armF_up: -6, armF_lo: 10, handF: 6, legN_up: 2, legN_lo: -2, legF_up: -3, legF_lo: -1 },
    wave: { torso: -2, head: -3, armN_up: { r: 198, y: -12 }, armN_lo: -4, handN: 0, variants: { handN: 'open', armN_up: 'over', armN_lo: 'over' }, armF_up: -6, armF_lo: 10, browN: { r: -6, y: -2 }, browF: { r: -6, y: -2 }, smile: 0.7, mouth: 'E' },
    point: { torso: 5, head: 5, armN_up: 88, armN_lo: 3, handN: 0, variants: { handN: 'point' }, armF_up: -12, armF_lo: 12, legN_up: 6, legF_up: -6, smile: 0.2 },
    sit: { lift: 0.46, torso: 2, head: 2, armN_up: 28, armN_lo: 62, handN: 10, armF_up: 18, armF_lo: 70, legN_up: 88, legN_lo: -88, legF_up: 84, legF_lo: -86, footN: 0, footF: 0 },
    'run-ready': { lift: 0.14, torso: 22, head: -8, armN_up: -48, armN_lo: 82, handN: 10, armF_up: 42, armF_lo: 84, handF: 10, legN_up: 42, legN_lo: -52, legF_up: -34, legF_lo: -34, browN: { r: 4 } },
    jump: { lift: -0.28, torso: -4, head: -6, armN_up: { r: 196, y: -8 }, armN_lo: -4, variants: { handN: 'open', handF: 'open', armN_up: 'over', armN_lo: 'over' }, armF_up: { r: 160, y: -8 }, armF_lo: 10, legN_up: 52, legN_lo: -72, legF_up: 24, legF_lo: -64, footN: 8, footF: 12, smile: 0.8, mouth: 'O' },
    surprised: { lift: -0.04, torso: -9, head: -7, armN_up: 44, armN_lo: 46, handN: -8, armF_up: 30, armF_lo: 56, browN: { r: -10, y: -7 }, browF: { r: -10, y: -7 }, eyeN: { sx: 1.12, sy: 1.15 }, eyeF: { sx: 1.12, sy: 1.15 }, mouth: 'O', gaze: [0.4, 0] },
    sad: { torso: 11, head: 20, armN_up: 5, armN_lo: 10, handN: 14, armF_up: -2, armF_lo: 8, handF: 12, browN: { r: 14, y: 1 }, browF: { r: 14, y: 1 }, eyeN: { sy: 0.8 }, eyeF: { sy: 0.8 }, smile: -1, gaze: [0.1, 0.6] },
    laugh: { lift: -0.02, torso: -13, head: -10, armN_up: 22, armN_lo: 44, handN: 10, armF_up: 12, armF_lo: 50, browN: { r: -6 }, eyeN: { sy: 0.45 }, eyeF: { sy: 0.45 }, mouth: 'AI', smile: 1 },
    think: { torso: 3, head: 8, armN_up: 52, armN_lo: 128, handN: 24, armF_up: 22, armF_lo: 96, handF: 8, browN: { r: -10, y: -3 }, browF: { r: 6 }, gaze: [0.5, -0.6], smile: -0.1 },
    'fight-ready': { lift: 0.18, torso: 12, head: 4, armN_up: 72, armN_lo: 96, handN: 14, armF_up: 54, armF_lo: 102, handF: 14, legN_up: 30, legN_lo: -36, legF_up: -30, legF_lo: -22, browN: { r: 8 }, browF: { r: 8 }, smile: -0.3, mouth: 'etc' },
    bow: { lift: 0.03, torso: 56, head: 24, armN_up: 16, armN_lo: 8, armF_up: 6, armF_lo: 10, eyeN: { sy: 0.18 }, eyeF: { sy: 0.18 }, smile: 0.4 },
    strike: { lift: 0.14, torso: 22, head: 8, armN_up: 102, armN_lo: -8, handN: 0, armF_up: -42, armF_lo: 40, legN_up: 46, legN_lo: -12, legF_up: -46, legF_lo: -16, browN: { r: 10 }, browF: { r: 10 }, mouth: 'AI', smile: -0.2 },
    hurt: { lift: -0.03, torso: -22, head: -16, armN_up: -42, armN_lo: 24, armF_up: -30, armF_lo: 30, legN_up: -12, legF_up: 18, eyeN: { sy: 0.3 }, eyeF: { sy: 0.3 }, browN: { r: 16 }, browF: { r: 16 }, mouth: 'O', smile: -1 },
    cheer: { lift: -0.1, torso: -5, head: -6, armN_up: { r: 198, y: -10 }, armN_lo: -4, variants: { handN: 'open', handF: 'open', armN_up: 'over', armN_lo: 'over' }, armF_up: { r: 165, y: -10 }, armF_lo: 8, legN_up: 14, legF_up: -10, mouth: 'AI', smile: 1, eyeN: { sy: 0.6 }, eyeF: { sy: 0.6 } },
  };

  // Which way a positive angle turns each limb joint. Characters may override with a part's own "sign".
  const SIGN = { armN_up: -1, armN_lo: -1, handN: -1, armF_up: -1, armF_lo: -1, handF: -1, legN_up: -1, legN_lo: -1, legF_up: -1, legF_lo: -1 };

  const rad = (d) => (d * Math.PI) / 180;
  const pos = (x) => Math.max(0, x);


  // One line for each pose, cycle, mouth shape and ease. scripts/build_character_docs.py copies these into
  // README-CHARACTERS.md, and a test fails when the README and this file disagree.
  const POSE_INFO = {
    idle: 'standing, arms loose, a slight breath',
    wave: 'near arm raised high behind the head, open palm (add the wave cycle to move the wrist)',
    point: 'near arm straight out in front, one finger pointing',
    sit: 'seated: thighs forward, knees bent, the body drops by 46% of the leg length',
    'run-ready': 'a crouched start, leaning forward, arms bent',
    jump: 'in the air: arms up, knees tucked, the body lifts by 28% of the leg length',
    surprised: 'leaning back, arms out, eyes and brows wide',
    sad: 'head and shoulders down, brows tilted, a frown',
    laugh: 'leaning back, eyes squeezed shut, a wide smile (add the laugh cycle to shake)',
    think: 'a hand at the chin, eyes looking up',
    'fight-ready': 'a low guard, near arm and far arm up, brows down',
    bow: 'bending forward from the waist, eyes closed, a small smile',
    strike: 'a lunge: front leg out, near arm thrown forward',
    hurt: 'thrown back, arms flung, eyes squeezed, a frown',
    cheer: 'both arms up, a wide smile, a small hop',
  };

  const CYCLE_INFO = {
    walk: 'legs swing, arms swing the other way, the body bobs; keep feet planted by moving at B2M.strideSpeed(character, "walk", steps)',
    run: 'a faster, longer stride with bent arms and a lean; the body leaves the ground between steps',
    wave: 'the wrist tips one way, then the other (two held drawings); use after a pose that raises an arm',
    laugh: 'the shoulders and head shake',
    breath: 'a slow rise and fall of the chest; always on unless the track sets breath: false',
    talk: 'a layer with no drawings of its own: head nods and small arm gestures while the mouth speaks, 7 beats a second (rate)',
    blink: 'not a layer: every character blinks every 2.5 to 5.5 s, from a seeded hash; the track sets blink: false to stop it',
  };

  const VISEME_INFO = {
    rest: 'closed mouth (a smile or frown comes from the pose)',
    AI: 'wide open (ah, i, my)',
    E: 'wide, teeth showing (ee, eh)',
    O: 'round and open (oh, ow)',
    U: 'small and round (oo, w)',
    MBP: 'lips pressed together (m, b, p)',
    FV: 'top teeth on the lower lip (f, v)',
    L: 'tongue up behind the teeth (l, th)',
    etc: 'half open, teeth showing (every other consonant)',
  };

  const EASE_INFO = {
    linear: 'constant speed',
    in: 'starts slow, ends fast',
    out: 'starts fast, settles slowly (for arrivals)',
    inOut: 'slow at both ends (the default)',
    sine: 'a gentle inOut',
    backOut: 'overshoots a little, then settles',
    hold: 'stays on the earlier pose until the key time, then snaps',
  };

  // A cycle is N drawings. fn(phase) gives joint offsets (added to the pose) for phase 0..1.
  const CYCLES = {
    walk: {
      frames: 8, steps: 8, lean: 4, amp: 28,
      fn(p) {
        const a = 2 * Math.PI * p, s = Math.sin(a), c = Math.cos(a);
        return {
          legN_up: 28 * s, legF_up: -28 * s, legN_lo: -46 * pos(c), legF_lo: -46 * pos(-c),
          armN_up: -22 * s, armF_up: 22 * s, armN_lo: 8 + 8 * pos(-s), armF_lo: 8 + 8 * pos(s),
          footN: 8 * pos(-c) * s, footF: -8 * pos(c) * s, torso: 3, head: -1, tail: 4 * Math.sin(a * 2),
          hip: { y: -4 * Math.abs(c) },
        };
      },
    },
    run: {
      frames: 6, steps: 12, lean: 10, amp: 52,
      fn(p) {
        const a = 2 * Math.PI * p, s = Math.sin(a), c = Math.cos(a);
        return {
          legN_up: 52 * s, legF_up: -52 * s, legN_lo: -84 * pos(c), legF_lo: -84 * pos(-c),
          armN_up: -50 * s, armF_up: 50 * s, armN_lo: 70, armF_lo: 70,
          footN: 10 * pos(-c), footF: 10 * pos(c), torso: 10, head: -5, tail: 8 * Math.sin(a * 2),
          hip: { y: -16 * Math.abs(s) },
        };
      },
    },
    // the wrist goes through two held drawings: hand tipped one way, then the other (a smooth skin blends them)
    wave: {
      frames: 2, steps: 5,
      fn(p, smooth) { const k = smooth ? Math.sin(2 * Math.PI * p) : p < 0.5 ? 1 : -1; return { armN_lo: 5 * k, handN: 24 * k }; },
    },
    laugh: {
      frames: 4, steps: 8,
      fn(p) { const s = Math.sin(2 * Math.PI * p); return { torso: 4 * s, head: -3 * s, hip: { y: -5 * Math.abs(s) } }; },
    },
    breath: {
      frames: 8, steps: 4, smooth: true,
      fn(p) { const s = Math.sin(2 * Math.PI * p); return { torso: { sy: 0.012 * s }, head: 0.8 * s, hip: { y: 0.8 * s } }; },
    },
  };

  // Mouth shapes: w is the half width, open is how far the lips part (0 closed to 1 wide), round pulls the corners in.
  const VISEME_SHAPE = {
    rest: { w: 0.8, open: 0, round: 0, teeth: 0 },
    AI: { w: 1.0, open: 1.0, round: 0.1, teeth: 0.55, tongue: 1 },
    E: { w: 1.08, open: 0.42, round: 0, teeth: 1.7 },
    O: { w: 0.55, open: 0.9, round: 1, teeth: 0 },
    U: { w: 0.36, open: 0.5, round: 1, teeth: 0 },
    MBP: { w: 0.8, open: 0, round: 0, teeth: 0, press: 1 },
    FV: { w: 0.95, open: 0.5, round: 0, teeth: 1, lip: 1 },
    L: { w: 0.9, open: 0.62, round: 0, teeth: 1, tongue: 1, tongueUp: 1 },
    etc: { w: 0.88, open: 0.34, round: 0, teeth: 0.8 },
  };

  Object.assign(B, { VISEMES, POSES, SIGN, CYCLES, VISEME_SHAPE, POSE_INFO, CYCLE_INFO, VISEME_INFO, EASE_INFO, rad });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
