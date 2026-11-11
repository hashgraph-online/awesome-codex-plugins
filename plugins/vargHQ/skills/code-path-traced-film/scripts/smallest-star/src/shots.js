// The film as a function of time. state(t) returns the camera, both characters and the lights;
// toUniforms() turns that into shader inputs. Motion blur comes from calling this at many times per frame.
import { W, terrain, pathZ, logTopY } from './world.js';
import { add, sub, mul, dot, cross, len, norm, lerp, lerp3, clamp, sstep, ease, easeOut, easeIn, remap, spline, frame, mat3mul, wob } from './vec.js';

export let TL = null;
export function setTimeline(tl) { TL = tl; }

const FF_COL = [1.0, 0.95, 0.30];
const MOON_DIR = norm([-0.42, 0.52, -0.74]);

function base() {
  return {
    cam: { pos: [0, 3, 10], tgt: [0, 2, 0], fov: 35, ap: 0.0, focus: 10, roll: 0 },
    ff: { pos: [0, 3, 0], fwd: [1, 0, 0], up: [0, 1, 0], scale: 1.4, glow: 1.0, emi: 5.0, wing: 0, elytra: 0, droop: 0, pitch: 0, vis: 1, col: FF_COL },
    ms: { pos: [9, 0, 1.5], fwd: [1, 0, 0], up: [0, 1, 0], scale: 1.0, headPitch: 0, headYaw: 0, ear: 0, squash: 1, tailPhase: 0, tailLift: 0, vis: 1 },
    moonDir: MOON_DIR, moonCol: [0.44, 0.62, 1.0], moonI: 0.42, moonVis: 1,
    sky: 0.46, skyVis: 0.16, fogGain: 0.10, star: 1.0, win: 0, wind: 1, fog: 0.007, glowFog: 0.0035, catchl: 0.35, fade0: 62, smoke: 1, clay: 0,
    clrA: [0, 0, 0, 0], clrP: [0, 1, 0, 0], clrB: [0, 0, 0, 0], clrQ: [0, 1, 0, 0],
    fillDir: null, fillCol: [0, 0, 0], spike: 0, sppMul: 1,
    post: { exposure: 3.4, bloom: 0.22, bloomThresh: 0.9, bloomSpread: 0.85, vig: 0.42, grain: 0.03, sat: 1.10, contrast: 0.25, lift: [0.006, 0.009, 0.022], fade: 1.0 },
  };
}

// hero blade: where the firefly perches
export function heroPerch(t, u = 0.9, wind = 1) {
  const hb = W.HERO; const by = terrain(hb.base[0], hb.base[1]) - 0.1;
  const L = hb.L + 0.10 * wind * Math.sin(t * 1.7 + 0.5);
  const p = [hb.base[0] + hb.ld[0] * L * u * u, by + hb.h * u, hb.base[1] + hb.ld[1] * L * u * u];
  const tan = norm([hb.ld[0] * 2 * L * u, hb.h, hb.ld[1] * 2 * L * u]);
  const nup = norm([-hb.ld[0] * hb.h, 2 * L * u, -hb.ld[1] * hb.h]);
  return { p, tan, nup };
}

const ground = (x, z) => [x, terrain(x, z), z];

// ---------------------------------------------------------------- dev shots (look development)
const DEV = {
  dev_mouse(k) {
    const S = base(); const c = ground(9, 1.5);
    const a = k * Math.PI * 2 + 0.6;
    S.ms.pos = c; S.ff.vis = 0; S.ff.glow = 0;
    S.cam = { pos: add(c, [Math.cos(a) * 3.6, 1.35, Math.sin(a) * 3.6]), tgt: add(c, [0.05, 0.5, 0]), fov: 30, ap: 0, focus: 3.6, roll: 0 };
    S.moonDir = norm([0.5, 0.7, 0.6]); S.moonCol = [1, 1, 1]; S.moonI = 2.4; S.sky = 9; S.skyVis = 1; S.star = 0; S.moonVis = 0;
    S.clrA = [9, 1.5, 9, 1.6]; S.clrP = [9, 0, 0, 0]; S.post.exposure = 1.0; S.post.bloom = 0.1; S.fog = 0.0;
    return S;
  },
  dev_ff(k) {
    const S = base(); const c = [9, 3.0, 1.5];
    const a = k * Math.PI * 2 + 0.6;
    S.ms.vis = 0; S.ff.pos = c; S.ff.glow = 0.25; S.ff.emi = 2.0; S.ff.wing = k > 0.5 ? 1 : 0; S.ff.elytra = k > 0.5 ? 1 : 0;
    S.cam = { pos: add(c, [Math.cos(a) * 1.9, 0.45, Math.sin(a) * 1.9]), tgt: add(c, [-0.05, 0, 0]), fov: 30, ap: 0, focus: 1.9, roll: 0 };
    S.moonDir = norm([0.5, 0.7, 0.6]); S.moonCol = [1, 1, 1]; S.moonI = 2.4; S.sky = 9; S.skyVis = 1; S.star = 0; S.moonVis = 0;
    S.clrA = [9, 1.5, 9, 1.6]; S.clrP = [9, 0, 0, 0]; S.post.exposure = 1.0; S.post.bloom = 0.25; S.fog = 0.0;
    return S;
  },
  dev_house(k) {
    const S = base(); const c = ground(W.HOUSE[0], W.HOUSE[1]);
    const a = Math.PI * 0.72 + (k - 0.5) * 1.6;
    S.ms.pos = ground(36.7, 0.02); S.ms.fwd = [1, 0, -0.1]; S.ff.pos = [35.6, 2.6, 1.0]; S.ff.wing = 1; S.ff.elytra = 1; S.ff.glow = 2.5; S.win = 2.5;
    S.cam = { pos: add(c, [Math.cos(a) * 13, 2.2, Math.sin(a) * 13]), tgt: add(c, [-0.6, 2.6, 0]), fov: 32, ap: 0.03, focus: 12.5, roll: 0 };
    return S;
  },
  dev_meadow(k) {
    const S = base();
    S.ff.pos = add(heroPerch(0).p, [0, 0.12, 0]); S.ff.glow = 1.2;
    S.ms.vis = 0;
    S.cam = { pos: [lerp(-9, 4, k), lerp(4.0, 2.0, k), 12], tgt: [1.2, 4.6, 0], fov: 34, ap: 0.04, focus: 13, roll: 0 };
    return S;
  },
  dev_pond(k) {
    const S = base();
    S.ms.pos = [24.5 + k * 2, logTopY(), 0.05]; S.ff.pos = [26.0 + k * 2, logTopY() + 1.7, 0.2]; S.ff.wing = 1; S.ff.elytra = 1; S.ff.glow = 2.2;
    S.cam = { pos: [22.0, 0.55, 8.6], tgt: [25.5, 0.8, 0], fov: 32, ap: 0.04, focus: 9.2, roll: 0 };
    return S;
  },
  dev_grass(k) {
    const S = base();
    S.ms.pos = ground(9, 1.5); S.ff.pos = [10.3, 1.5, 1.9]; S.ff.wing = 1; S.ff.elytra = 1; S.ff.glow = lerp(0.3, 3.0, k); S.ff.fwd = [-1, 0, -0.2];
    S.cam = { pos: [10.4, 0.75, 6.2], tgt: [9.5, 0.95, 1.6], fov: 30, ap: 0.05, focus: 4.7, roll: 0 };
    S.clrA = [10.2, 6.5, 9.6, 2.6]; S.clrP = [1.5, 0.12, 0, 0];
    return S;
  },
};

// ---------------------------------------------------------------- film shots
const SHOT = {};
const BEAT = 60 / 72;
const perchPos = (t) => { const h = heroPerch(t, 0.9); return { pos: add(h.p, mul(h.nup, 0.16)), tan: h.tan, nup: h.nup }; };
const pathPos = (x) => [x, terrain(x, pathZ(x)), pathZ(x)];
const pulse = (t, rate = 1.0) => 0.5 + 0.5 * Math.sin(t * 2 * Math.PI * rate);
const glowEmi = (g) => 0.7 + 1.0 * g;

// one mouse hop cycle: returns height, squash and how far along the hop we are
function hop(tt, period, height) {
  const n = Math.floor(tt / period); const ph = tt / period - n; const air = 0.64;
  if (ph < air) { const a = ph / air; return { n, y: height * 4 * a * (1 - a), sq: 1 + 0.10 * Math.sin(a * Math.PI), adv: n + ease(a) * 1.0, pitch: 0.22 * Math.cos(a * Math.PI) }; }
  const b = (ph - air) / (1 - air);
  return { n, y: 0, sq: 1 - 0.15 * Math.sin(b * Math.PI), adv: n + 1.0, pitch: 0 };
}
function flyTo(S, p, fwd, t, glow, bob = 0.07) {
  S.ff.pos = add(p, [wob(t * 2.3, 1) * bob, wob(t * 2.9, 2) * bob * 1.3, wob(t * 2.1, 3) * bob]);
  S.ff.fwd = fwd; S.ff.up = [0, 1, 0]; S.ff.wing = 1; S.ff.elytra = 1; S.ff.glow = glow; S.ff.emi = glowEmi(glow);
}

// s01: crane down from the stars to the meadow and one faint glow
SHOT.s01 = (tl, u, t) => {
  const S = base(); const e = ease(remap(u, 0.0, 0.92));
  const pp = perchPos(t);
  S.ff.pos = pp.pos; S.ff.fwd = pp.tan; S.ff.up = pp.nup; S.ff.pitch = 0.5;
  const g = 0.35 + 0.35 * pulse(t, 0.9) * sstep(2.2, 3.4, tl) + 0.15;
  S.ff.glow = g; S.ff.emi = glowEmi(g);
  S.ms.vis = 0;
  S.cam.pos = lerp3([-1.0, 10.5, 19.5], [1.0, 6.5, 11.5], e);
  const d0 = norm(add(MOON_DIR, [0.16, -0.10, 0.0])); const d1 = norm(sub(add(pp.pos, [0.1, 0.3, 0]), [1.0, 6.5, 11.5]));
  S.cam.tgt = add(S.cam.pos, mul(norm(lerp3(d0, d1, e)), 20));
  S.cam.fov = 36; S.cam.ap = 0.04; S.cam.focus = lerp(16, 11.8, e);
  S.clrA = [1.0, 12.0, 2.4, 1.5]; S.clrP = [3.4, 0.0, 0, 0];
  S.fillCol = [0.012, 0.018, 0.035];
  S.post.fade = sstep(0.0, 0.9, tl);
  return S;
};

// s02: close on the firefly, looking up
SHOT.s02 = (tl, u, t) => {
  const S = base(); const e = ease(u);
  const pp = perchPos(t);
  S.ff.pos = pp.pos; S.ff.fwd = pp.tan; S.ff.up = pp.nup;
  S.ff.pitch = lerp(0.75, 0.35, sstep(3.0, 4.6, tl)); S.ff.droop = sstep(2.6, 4.4, tl) * 0.9;
  const g = 0.30 + 0.30 * pulse(t, 0.9); S.ff.glow = g; S.ff.emi = glowEmi(g);
  S.ms.vis = 0;
  S.cam.pos = add(pp.pos, lerp3([-0.70, -0.02, 2.65], [-0.52, 0.03, 2.15], e));
  S.cam.tgt = add(pp.pos, [0.20, 0.12, 0]);
  S.cam.fov = 30; S.cam.ap = 0.03; S.cam.focus = len(sub(S.cam.pos, pp.pos));
  S.ff.emi = 0.55 + 0.7 * g; S.fillCol = [0.030, 0.040, 0.070]; S.catchl = 0.5; S.glowFog = 0.0015; S.sppMul = 2.5;
  S.clrA = [S.cam.pos[0], S.cam.pos[2], 1.0, 0.0]; S.clrP = [2.4, 0.0, 0, 0];
  return S;
};

// s03: takeoff and climb
const climb = (tl) => {
  const pp = perchPos(10.4); const k = ease(remap(tl, 0.4, 5.6));
  return spline([pp.pos, add(pp.pos, [0.5, 2.0, 0.3]), [2.6, 10.5, -0.6], [1.9, 15.0, -1.0], [2.4, 19.5, -1.2]], k);
};
SHOT.s03 = (tl, u, t) => {
  const S = base();
  if (tl < 0.4) {
    const pp = perchPos(t); S.ff.pos = pp.pos; S.ff.fwd = pp.tan; S.ff.up = pp.nup; S.ff.pitch = 0.8;
    S.ff.elytra = sstep(0.05, 0.35, tl); S.ff.wing = sstep(0.2, 0.4, tl); S.ff.glow = 0.5; S.ff.emi = glowEmi(0.5);
  } else {
    const p = climb(tl); const p2 = climb(tl + 0.05);
    const g = lerp(0.6, 1.8, sstep(0.4, 4.0, tl));
    flyTo(S, p, norm(add(norm(sub(p2, p)), [0.35, 0.0, 0.0])), t, g, 0.05); S.ff.pitch = 0.5;
  }
  S.ms.vis = 0;
  const e = ease(remap(tl, 0.3, 5.0));
  S.cam.pos = lerp3([5.4, 5.0, 7.6], [6.4, 13.2, 9.0], e);
  const look = climb(Math.max(tl - 0.25, 0.4));
  S.cam.tgt = lerp3(add(perchPos(t).pos, [0, 0.2, 0]), add(look, [0, lerp(0.4, 1.6, e), 0]), sstep(0.2, 1.2, tl));
  S.cam.fov = 34; S.cam.ap = 0.03; S.cam.focus = len(sub(S.cam.pos, S.ff.pos));
  S.clrA = [2.6, 1.0, 5.6, 8.0]; S.clrP = [3.0, 0.0, 0, 0];
  S.fillCol = [0.02, 0.028, 0.05];
  return S;
};

// s04: a tiny light against a huge moon; it falters
const stall = (tl) => {
  const y = 24.0 + 2.2 * easeOut(remap(tl, 0, 3.2)) - 1.5 * easeIn(remap(tl, 3.2, 5.0));
  return [2.4 + 0.25 * Math.sin(tl * 0.9), y, -1.2];
};
SHOT.s04 = (tl, u, t) => {
  const S = base();
  const p = stall(tl);
  const falter = sstep(2.3, 3.6, tl);
  const flick = 1.0 - falter * (0.55 + 0.35 * Math.sin(t * 23.0) * Math.sin(t * 7.3));
  const g = lerp(1.8, 0.7, falter) * flick;
  flyTo(S, p, norm([0.5, lerp(0.75, -0.15, falter), -0.35]), t, g, 0.06 + 0.10 * falter);
  S.ff.wing = lerp(1.0, 0.55, falter) * (1.0 - 0.3 * falter * pulse(t, 5.0)); S.ff.droop = falter; S.ff.pitch = lerp(0.6, -0.2, falter);
  S.ms.vis = 0;
  const D = lerp(21.0, 19.0, ease(u));
  const c0 = add([2.4, 25.2, -1.2], mul(S.moonDir, -D));
  S.cam.pos = add(c0, [0.9, -0.2, 0]); S.cam.tgt = [2.4, lerp(25.0, 25.5, ease(u)), -1.2];
  S.cam.fov = 13.5; S.cam.ap = 0.012; S.cam.focus = D;
  S.star = 1.25; S.glowFog = 0.002; S.sppMul = 1.5;
  return S;
};

// s05: sinking back into the dark grass
const sink = (tl) => spline([[6.6, 11.4, 1.2], [7.6, 8.6, 1.6], [8.6, 5.6, 2.0], [9.4, 3.0, 2.3]], easeIn(remap(tl, 0, 2.6)) * 0.55 + remap(tl, 0, 2.6) * 0.45);
SHOT.s05 = (tl, u, t) => {
  const S = base();
  const p = sink(tl);
  const g = 0.38 * (0.7 + 0.3 * Math.sin(t * 19.0) * Math.sin(t * 6.1));
  flyTo(S, p, norm([0.5, -0.6, 0.2]), t, g, 0.12);
  S.ff.wing = 0.35 + 0.2 * pulse(t, 4.0); S.ff.droop = 1; S.ff.pitch = -0.3; S.ff.up = norm([0.25 * Math.sin(t * 3.0), 1, 0.2 * Math.cos(t * 2.3)]);
  S.ms.vis = 0;
  S.cam.pos = [12.6, 6.9, 9.8]; S.cam.tgt = add(sink(Math.max(tl - 0.12, 0)), [0.2, 0.5, 0]);
  S.cam.fov = 30; S.cam.ap = 0.04; S.cam.focus = len(sub(S.cam.pos, p));
  S.clrA = [12.6, 9.8, 10.0, 3.6]; S.clrP = [2.2, 0.0, 0, 0];
  S.fillCol = [0.02, 0.028, 0.05];
  return S;
};

// the mouse's spot in the deep grass
const LOST = () => ground(9.0, 1.5);
function lostMouse(S, t, fear) {
  S.ms.pos = add(LOST(), [Math.sin(t * 31.0) * 0.012 * fear, 0, Math.cos(t * 27.0) * 0.012 * fear]);
  S.ms.fwd = norm([0.86, 0, 0.5]);
  S.ms.ear = 0.75 * fear; S.ms.squash = 1 - 0.07 * fear + 0.012 * Math.sin(t * 2.4); S.ms.tailPhase = t * 1.5; S.ms.tailLift = 0;
}

// s06: the mouse, lost
SHOT.s06 = (tl, u, t) => {
  const S = base();
  lostMouse(S, t, 1.0);
  const look = sstep(3.2, 4.2, tl);
  S.ms.headYaw = lerp(0.55 * Math.sin(tl * 1.5), -0.1, look); S.ms.headPitch = lerp(-0.05 + 0.05 * Math.sin(tl * 2.2), 0.6, look);
  S.ms.ear = lerp(0.75, 0.3, look);
  // the firefly drifts down into the shot
  const k = remap(tl, 2.6, 5.0);
  const p = lerp3([10.6, 7.5, 1.2], [10.75, 2.5, 1.6], easeOut(k));
  const g = 0.28 * (0.75 + 0.25 * Math.sin(t * 17.0) * Math.sin(t * 5.3)) * sstep(2.4, 3.2, tl);
  flyTo(S, p, norm([-0.7, -0.3, 0.1]), t, g, 0.1);
  S.ff.wing = 0.45; S.ff.droop = 1; S.ff.vis = tl > 2.4 ? 1 : 0;
  S.cam.pos = lerp3([11.6, 0.72, 7.4], [11.1, 0.74, 6.3], ease(u)); S.cam.tgt = [9.2, lerp(0.85, 1.25, look * 0.6), 1.5];
  S.cam.fov = 31; S.cam.ap = 0.05; S.cam.focus = len(sub(S.cam.pos, add(LOST(), [0.2, 0.6, 0])));
  S.clrA = [S.cam.pos[0], S.cam.pos[2], 9.5, 2.3]; S.clrP = [1.25, 0.0, 0, 0];
  S.clrB = [12.5, 7.0, 8.0, 3.0]; S.clrQ = [3.6, 0.10, 0, 0];
  S.fillCol = [0.030, 0.042, 0.075]; S.moonI = 0.55;
  return S;
};

// s07: the turn. A little light.
SHOT.s07 = (tl, u, t) => {
  const S = base();
  const bloom = ease(remap(tl, 1.7, 3.3));
  lostMouse(S, t, 1.0 - bloom);
  S.ms.fwd = norm([1, 0, 0.12]);
  const startle = sstep(0.0, 0.5, tl) * (1 - sstep(0.9, 1.9, tl));
  S.ms.headPitch = lerp(0.42, 0.30, bloom) - 0.15 * startle; S.ms.headYaw = 0.1;
  S.ms.squash = 1 - 0.08 * startle + 0.05 * bloom * Math.sin(Math.min(1, remap(tl, 1.7, 3.0)) * Math.PI);
  S.ms.ear = lerp(0.7, 0.0, bloom); S.ms.tailLift = bloom * 0.6; S.ms.tailPhase = t * (1.5 + 3 * bloom);
  const hover = add(LOST(), [lerp(2.05, 1.75, ease(remap(tl, 0.0, 2.0))), 1.02 + 0.06 * Math.sin(t * 2.0), 0.12]);
  const g = lerp(0.22, 3.6, bloom) * (0.9 + 0.1 * Math.sin(t * 3.1));
  flyTo(S, hover, norm([-1, -0.12, 0.0]), t, g, 0.035);
  S.ff.droop = 1 - bloom; S.ff.pitch = lerp(-0.2, 0.25, bloom);
  S.cam.pos = lerp3([10.35, 0.98, 5.3], [10.2, 1.0, 4.7], ease(u)); S.cam.tgt = add(LOST(), [0.95, 0.86, 0.0]);
  S.cam.fov = 30; S.cam.ap = 0.045; S.cam.focus = len(sub(S.cam.pos, add(LOST(), [0.6, 0.8, 0.0])));
  S.sppMul = 1.5;
  S.clrA = [S.cam.pos[0], S.cam.pos[2], 10.0, 2.3]; S.clrP = [1.5, 0.0, 0, 0];
  S.clrB = [12.6, 5.6, 7.6, 3.2]; S.clrQ = [3.2, 0.08, 0, 0];
  return S;
};

// s08: the journey
SHOT.s08 = (tl, u, t) => {
  const S = base();
  const period = BEAT / 2; const hp = hop(tl + 0.64 * period, period, 0.34);
  const x = 9.7 + (hp.adv - 1) * 0.49;
  const mp = pathPos(x); const mp2 = pathPos(x + 0.3);
  S.ms.pos = add(mp, [0, hp.y, 0]);
  const dir = norm(sub(mp2, mp));
  S.ms.fwd = norm([dir[0], dir[1] + hp.pitch, dir[2]]);
  S.ms.squash = hp.sq; S.ms.headPitch = 0.28; S.ms.ear = 0.15 + 0.25 * (hp.y > 0.05 ? 1 : 0) * 0.5; S.ms.tailLift = 0.5; S.ms.tailPhase = t * 7.0;
  const fx = 9.7 + (tl / period) * 0.49 + 1.9;
  const fp = add(pathPos(fx), [0, 1.55 + 0.12 * Math.sin(t * 2.6), 0.15]);
  flyTo(S, fp, norm([1, 0.05 * Math.sin(t * 2.6), -0.05]), t, 3.4, 0.05);
  S.ff.pitch = 0.1;
  const cx = 9.7 + (tl / period) * 0.49 + 0.9 + 0.5 * ease(u);
  const cz = pathZ(cx) + 7.4;
  S.cam.pos = [cx, 1.02, cz]; S.cam.tgt = [cx + 0.25, 1.12, pathZ(cx)];
  S.cam.fov = 33; S.cam.ap = 0.05; S.cam.focus = 7.4;
  S.clrA = [cx - 14, cz - 3.2, cx + 14, cz - 3.2]; S.clrP = [3.3, 0.0, 0, 0];
  S.clrB = [cx - 1.5, cz, cx + 1.5, cz]; S.clrQ = [2.2, 0.0, 0, 0];
  return S;
};

// s09: across the pond on a fallen twig
SHOT.s09 = (tl, u, t) => {
  const S = base();
  const period = BEAT; const t9 = tl - (0.8 - 0.64 * period); const hp = hop(Math.max(t9, 0), period, 0.10);
  const x = 22.9 + (t9 > 0 ? hp.adv * 0.72 : 0);
  const lz = lerp(W.LOG.a[1], W.LOG.b[1], (x - W.LOG.a[0]) / (W.LOG.b[0] - W.LOG.a[0]));
  S.ms.pos = [x, logTopY() - 0.03 + (t9 > 0 ? hp.y : 0), lz]; S.ms.fwd = norm([1, t9 > 0 ? hp.pitch * 0.5 : 0, 0]);
  S.ms.squash = lerp(1, hp.sq, 0.6); S.ms.headPitch = 0.22; S.ms.ear = 0.2; S.ms.tailLift = 0.9; S.ms.tailPhase = t * 3.0;
  const fx = 22.9 + Math.max(t9, 0) / period * 0.72 + 1.9;
  flyTo(S, [fx - 0.45, logTopY() + 1.02 + 0.08 * Math.sin(t * 2.2), lz + 0.2], norm([1, 0, -0.05]), t, 3.0, 0.035);
  const cx = lerp(23.7, 25.3, ease(u));
  S.cam.pos = [cx, W.WL + 0.36, 5.9]; S.cam.tgt = [cx + 0.45, -0.40, 0];
  S.cam.fov = 38; S.cam.ap = 0.03; S.cam.focus = 5.9; S.sppMul = 2.0;
  S.star = 1.2;
  return S;
};

// s10: home
const DOOR = () => { const g = ground(34.75, 0.0); return g; };
SHOT.s10 = (tl, u, t) => {
  const S = base();
  const period = BEAT / 2; const arrive = 5 * period;
  const hp = hop(Math.min(tl, arrive - 1e-4), period, 0.30);
  const x = 33.95 + (tl < arrive ? hp.adv : 5) * 0.55;
  const mp = ground(x, 0.02);
  const moving = tl < arrive;
  S.ms.pos = add(mp, [0, moving ? hp.y : 0, 0]);
  const turn = ease(remap(tl, 2.6, 3.4));
  S.ms.fwd = norm([1, moving ? hp.pitch : 0, lerp(0, 0.25, turn)]);
  S.ms.squash = moving ? hp.sq : 1 + 0.01 * Math.sin(t * 2.4);
  S.ms.headYaw = lerp(0, 2.2, turn); S.ms.headPitch = lerp(0.25, 0.5, turn); S.ms.ear = 0.1; S.ms.tailLift = 0.6; S.ms.tailPhase = t * (moving ? 7 : 2.5);
  const fp = lerp3([35.9, 2.2, 1.0], [35.2, 3.5, 1.9], ease(remap(tl, 1.8, 4.6)));
  flyTo(S, fp, norm([0.9, -0.25, -0.3]), t, 3.0, 0.05);
  S.win = 2.6;
  S.cam.pos = lerp3([30.1, 1.25, 8.2], [30.7, 1.35, 7.6], ease(u)); S.cam.tgt = [37.5, 2.75, 0.2];
  S.cam.fov = 34; S.cam.ap = 0.04; S.cam.focus = 10.6;
  S.clrA = [S.cam.pos[0], S.cam.pos[2], 34.1, 3.4]; S.clrP = [2.2, 0.0, 0, 0];
  S.clrB = [28.5, 6.0, 35.5, 5.0]; S.clrQ = [4.2, 0.10, 0, 0];
  return S;
};

// s11: rise and pull back until the firefly is one more star
SHOT.s11 = (tl, u, t) => {
  const S = base();
  const stopX = 33.95 + 5 * 0.55;
  S.ms.pos = ground(stopX, 0.02); S.ms.fwd = norm([1, 0, 0.25]); S.ms.headYaw = 2.2; S.ms.headPitch = lerp(0.5, 0.75, sstep(0, 3, tl)); S.ms.ear = 0.05; S.ms.tailLift = 0.6; S.ms.tailPhase = t * 2.0;
  const rise = ease(remap(tl, 0.0, 5.5));
  const fp = lerp3([35.2, 3.5, 1.9], [38.9, 12.6, 0.4], rise);
  const g = lerp(3.0, 7.5, rise) * (0.93 + 0.07 * Math.sin(t * 2.4));
  flyTo(S, fp, norm([0.3, 0.2, -0.2]), t, g, 0.04);
  S.win = 2.6;
  const e = ease(remap(tl, 1.2, 7.4)); const ey = ease(remap(tl, 0.0, 3.0));
  S.cam.pos = [lerp(30.7, 15.5, e), lerp(1.35, 8.5, ey), lerp(7.6, 18.5, e)];
  S.cam.tgt = lerp3([37.5, 2.75, 0.2], [38.6, 7.9, 0.0], ease(remap(tl, 0.3, 7.4)));
  S.cam.fov = lerp(34, 30, e); S.cam.ap = lerp(0.04, 0.0, e); S.cam.focus = lerp(10.6, 50, e);
  S.clrA = [30.7, 7.6, 34.1, 3.4]; S.clrP = [2.2, 0.0, 0, 0];
  S.clrB = [28.5, 6.0, 35.5, 5.0]; S.clrQ = [4.2, 0.10, 0, 0];
  S.spike = 0.9 * sstep(3.5, 7.0, tl) * (0.9 + 0.1 * Math.sin(t * 2.4));
  S.star = lerp(1.0, 1.35, e); S.fade0 = lerp(62, 90, e); S.glowFog = lerp(0.0035, 0.0022, e);
  return S;
};

// coda / end card backdrop: just the stars, drifting
SHOT.coda = (tl, u, t) => {
  const S = base(); S.ms.vis = 0; S.ff.vis = 0; S.ff.glow = 0;
  const a = 0.9 + t * 0.012;
  S.cam.pos = [0, 30, 0]; S.cam.tgt = [Math.cos(a) * 10, 30 + 7.5, Math.sin(a) * 10]; S.cam.fov = 40; S.cam.ap = 0;
  S.star = 0.5; S.moonVis = 0; S.skyVis = 0.10;
  return S;
};
SHOT.end = SHOT.coda;

export function shotAt(t) {
  const shots = TL.shots;
  let s = shots[0];
  for (const x of shots) if (t >= x.start - 1e-6) s = x;
  return s;
}

export function state(t, dev) {
  if (dev) return DEV[dev.shot](dev.k ?? 0);
  const s = shotAt(t);
  const fn = SHOT[s.id] || SHOT.s01;
  const tl = t - s.start;
  return fn(tl, clamp(tl / s.dur), t, s);
}

export function toUniforms(S) {
  const c = S.cam;
  const f = norm(sub(c.tgt, c.pos));
  let r = norm(cross(f, [0, 1, 0])); let u = cross(r, f);
  if (c.roll) { const cr = Math.cos(c.roll), sr = Math.sin(c.roll); const r2 = add(mul(r, cr), mul(u, sr)); u = add(mul(u, cr), mul(r, -sr)); r = r2; }
  const ffM = frame(S.ff.fwd, S.ff.up);
  const msM = frame(S.ms.fwd, S.ms.up);
  const ffLight = add(S.ff.pos, mul(mat3mul(ffM, [-0.165, -0.012, 0]), S.ff.scale));
  return {
    pt: {
      uCamPos: c.pos, uCamR: r, uCamU: u, uCamF: f, uTanFov: Math.tan(c.fov * Math.PI / 360), uAperture: c.ap, uFocus: c.focus,
      uMoonDir: S.moonDir, uMoonCol: mul(S.moonCol, S.moonI), uSkyGain: S.sky, uSkyVis: S.skyVis, uFogGain: S.fogGain, uStarGain: S.star, uMoonVis: S.moonVis,
      uFfPos: S.ff.pos, uFfRot: ffM, uFfScale: S.ff.scale, uFfGlow: S.ff.glow, uFfCol: S.ff.col, uFfEmi: S.ff.emi,
      uFfPose: [S.ff.wing, S.ff.elytra, S.ff.droop, S.ff.pitch], uFfLight: ffLight, uFfVis: S.ff.vis,
      uMsPos: S.ms.pos, uMsRot: msM, uMsScale: S.ms.scale, uMsA: [S.ms.headPitch, S.ms.headYaw, S.ms.ear, S.ms.squash], uMsB: [S.ms.tailPhase, S.ms.tailLift, 0, 0], uMsVis: S.ms.vis,
      uWin: S.win, uWind: S.wind, uFog: S.fog, uGlowFog: S.glowFog, uClay: S.clay, uCatch: S.catchl, uFade0: S.fade0, uSmoke: S.smoke,
      uClrA: S.clrA, uClrP: S.clrP, uClrB: S.clrB, uClrQ: S.clrQ,
      uFillDir: S.fillDir || norm(add(mul(f, -1), [0, 0.5, 0])), uFillCol: S.fillCol, uSpike: S.spike,
    },
    post: S.post,
  };
}

export { base, ground, DEV, SHOT, FF_COL, MOON_DIR };
