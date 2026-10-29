// Default previz for the 36 shots of storyboard_v4.json.
// Timing, lyric and picture text come from the storyboard; this file adds, per shot:
//   set     – which master set it is framed in (one set per location)
//   mood    – lighting of the cockpit set
//   cam     – camera keys a (start) and b (end): p = position, t = look-at target, fov (vertical, deg), roll (deg); ease
//   shake   – local times (s) of impacts that kick the camera
//   overlay – what will be drawn in code (HyperFrames) on top of the AI clip
//   anim    – poses the set for local progress c.k (0..1) / local seconds c.lt
// Camera keys are the editable part; edits made in the UI are saved to data/edits.json and override these.
import * as THREE from 'three';
import { C, pose, trailAt, burstAt, ringAt } from './props.js';
import { setMood, SERVICES } from './sets.js';

export const BEAT = 60 / 133.8;
const cl = x => Math.max(0, Math.min(1, x));
const ramp = (x, a, b) => cl((x - a) / (b - a));
const sm = x => x * x * (3 - 2 * x);
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const cam = (ap, at, af, bp, bt, bf, ease = 'inOut', ar = 0, br = 0) =>
  ({ a: { p: ap, t: at, fov: af, roll: ar }, b: { p: bp, t: bt || at, fov: bf ?? af, roll: br }, ease });

// --------------------------------------------------------------- shared helpers
function sing(pilot, lt, amt = 1) {
  const m = pilot.getObjectByName('mouth');
  m.scale.y = 1 + amt * 4 * Math.abs(Math.sin(lt * 11) * Math.sin(lt * 3.3 + 1));
  const j = pilot.userData.j;
  j.neck.rotation.x += Math.sin(lt * 2 * Math.PI / BEAT) * 0.04 * amt;
  j.neck.rotation.z += Math.sin(lt * 1.7) * 0.05 * amt;
}
function redAlarm(S, lt, base = 7) {
  setMood(S, 'red');
  S.o.key.intensity = base * (0.65 + 0.35 * Math.abs(Math.sin(lt * Math.PI / BEAT)));
}
function handWorld(pilot, side) {
  pilot.updateMatrixWorld(true);
  return pilot.userData.j['hand' + side].getWorldPosition(new THREE.Vector3());
}
// Drones stream toward +Z past the hero (the ship flies -Z through them).
function swarm(S, T, speed = 22) {
  for (const d of S.o.drones.children) {
    const b = d.userData.base;
    d.position.set(b.x + Math.sin(T * 0.9 + d.userData.phase) * 2, b.y + Math.cos(T * 0.7 + d.userData.phase) * 1.5, ((b.z + T * speed + 160) % 175) - 160);
    d.lookAt(0, 0, 0);
    d.rotateY(Math.PI);
  }
}
function walk(m, T, amt = 1) {
  const ph = (T / (2 * BEAT)) * Math.PI * 2, j = m.userData.j;
  j.hipL.rotation.x = Math.sin(ph) * 0.42 * amt; j.hipR.rotation.x = -Math.sin(ph) * 0.42 * amt;
  j.kneeL.rotation.x = -Math.max(0, -Math.sin(ph + 0.6)) * 0.7 * amt; j.kneeR.rotation.x = -Math.max(0, Math.sin(ph + 0.6)) * 0.7 * amt;
  j.shoulderR.rotation.x = Math.sin(ph) * 0.35 * amt; j.shoulderR.rotation.z = 0.08;
  j.shoulderL.rotation.set(0.5, 0, -0.1); j.elbowL.rotation.x = 1.2; // helmet under the arm
  m.position.y = 0.95 + Math.abs(Math.cos(ph)) * 0.03 * amt;
}
function badges(S, T) {
  const beat = Math.floor(T / BEAT);
  S.o.models.forEach((m, i) => m.userData.badges.forEach(b => (b.visible = b.userData.k === (i * 2 + beat) % SERVICES.length)));
}
function tunnel(S, T, speed) { S.o.scroll.position.z = (T * speed) % S.o.SP; }
// Sound rings from the sax kill drones they reach (x29/x30).
function trench(S, c, speed, ringsFrom = 0) {
  const o = S.o, v = 45, emit = [];
  for (let j = 0; j < 8; j++) emit.push(ringsFrom + j * BEAT);
  const saxZ = 0.2;
  o.drones.children.forEach((d, i) => {
    const b = d.userData.base, z0 = b.z - 30;
    let killed = -1;
    for (const tj of emit) { const m = (v * tj - z0 + saxZ * 0) / (speed + v); if (m >= tj && m <= c.lt) { killed = m; break; } }
    d.position.set(b.x, b.y, z0 + speed * c.lt);
    d.visible = killed < 0 && d.position.z < 8;
    if (killed >= 0) { const bu = o.bursts[i % o.bursts.length]; bu.position.set(b.x, b.y, z0 + speed * killed); burstAt(bu, (c.lt - killed) / 0.5); }
  });
  emit.forEach((tj, j) => {
    const r = o.rings[j % o.rings.length];
    if (c.lt < tj) return;
    r.position.set(0, 2.2, saxZ - v * (c.lt - tj));
    ringAt(r, (c.lt - tj) / 2.2, 9);
  });
}

// Assault on THE 503 (c24–c26). Attackers: Kling, Replicate (took fal's slot in c23), Veo, Runway, Seedance.
function assaultBase(S) {
  const o = S.o;
  o.drones.visible = false;
  o.the503.position.copy(o.P503);
  o.squad[1].visible = false;
  return [o.squad[0], o.replacement, o.squad[2], o.squad[3], o.squad[4]];
}
// Point a ship's nose (-Z) at a target, with a bank.
function aim(f, target, bank = 0) { f.lookAt(target); f.rotateY(Math.PI); f.rotateZ(bank); }
function strafe(f, a, T, i) {
  f.visible = true;
  f.position.copy(a.station).add(V(Math.sin(T * 1.3 + i) * 6, Math.cos(T * 1.1 + i) * 4, Math.sin(T * 0.9 + i * 2) * 5));
  aim(f, a.hit, 0.3 * Math.sin(T * 2 + i));
}
// events: [side, local time] sorted by time; shows each side's latest hit and makes the eye flinch.
function strikes(S, lt, events) {
  const o = S.o;
  let flinch = 0;
  for (const [i, t0] of events) {
    if (lt < t0) continue;
    const a = o.assault[i], k = (lt - t0) / 0.9;
    if (k < 1) { a.burst.position.copy(a.hit); burstAt(a.burst, k); }
    flinch = Math.max(flinch, 1 - (lt - t0) / 0.25);
  }
  o.the503.getObjectByName('lid').visible = flinch > 0;
  o.redLight.intensity = 3 + 5 * Math.max(0, flinch);
}
function boost(ship, k) { ['flameL', 'flameR'].forEach(n => ship.getObjectByName(n).scale.set(1, 1 + k, 1)); }

// --------------------------------------------------------------- shots
export const SHOTS = {
  // ---------------- A · cockpit, red
  h01: {
    set: 'cockpit', framing: 'pilot face',
    cam: cam([0.02, 1.29, -0.5], [0, 1.28, 0.1], 28, [0.01, 1.29, -0.42], null, 27, 'out'),
    shake: [0.9],
    overlay: 'HOOK "POV: your AI provider died at 99%" · 99 % bar in his pupils → 503',
    anim(S, c) {
      const o = S.o, hitT = 0.9;
      if (c.lt < hitT) { setMood(S, 'calm'); o.key.color.setHex(0x40ff90); o.key.intensity = 3; } else redAlarm(S, c.lt);
      const cn = o.crackPoint.clone().sub(V(0, 0.95, -0.15)).normalize();
      o.drone.visible = c.lt < hitT + 0.25;
      const fly = ramp(c.lt, 0.45, hitT);
      o.drone.position.copy(o.crackPoint).addScaledVector(cn, 0.55 + (1 - fly) * 9 + Math.max(0, c.lt - hitT) * 3);
      o.drone.lookAt(0, 1.2, 0);
      o.crack.visible = c.lt >= hitT; o.crack.scale.setScalar(sm(ramp(c.lt, hitT, hitT + 0.08)));
      const snap = c.lt > hitT ? Math.exp(-(c.lt - hitT) * 5) * Math.sin((c.lt - hitT) * 18) : 0;
      o.pilot.userData.j.neck.rotation.set(-0.3 * snap, 0.25 * snap, 0.1 * snap);
    },
  },
  v03: {
    set: 'cockpit', framing: 'face + shoulders',
    cam: cam([-0.2, 1.12, -1.05], [0, 1.12, 0.1], 42, [-0.14, 1.14, -0.95], null, 40),
    overlay: 'lyrics white-red, glitch',
    anim(S, c) {
      redAlarm(S, c.lt);
      S.o.stick.rotation.set(Math.cos(c.lt * 7) * 0.15, 0, Math.sin(c.lt * 9) * 0.25);
      const j = S.o.pilot.userData.j;
      j.shoulderR.rotation.z += Math.sin(c.lt * 9) * 0.08; j.spine.rotation.z = Math.sin(c.lt * 4) * 0.05;
      sing(S.o.pilot, c.lt);
    },
  },
  v04: {
    set: 'cockpit', framing: 'fist / button',
    cam: cam([0.42, 1.42, 0.42], [0.24, 0.8, -0.5], 42, [0.37, 1.34, 0.3], [0.26, 0.8, -0.5], 40),
    overlay: 'HUD card flips to a red 503',
    anim(S, c) {
      redAlarm(S, c.lt);
      const hits = [BEAT, 2 * BEAT, 3 * BEAT];
      const u = Math.min(...hits.map(h => Math.abs(c.lt - h)));
      const down = 1 - ramp(u, 0, 0.17);
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 1], ['pressRUp', ramp(c.lt, 0, 0.3)], ['pressR', down]]);
      S.o.buttons[2].position.y = 0.8 - 0.015 * down;
      S.o.card503.visible = c.lt > BEAT;
    },
  },
  v05: {
    set: 'cockpit', framing: 'hand + key card',
    cam: cam([-0.3, 1.12, -1.15], [0.1, 1.0, -0.3], 42, [-0.25, 1.1, -1.05], null, 40),
    overlay: '—',
    anim(S, c) {
      redAlarm(S, c.lt);
      const lift = sm(ramp(c.k, 0.05, 0.5));
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 1], ['pressR', 1 - lift], ['showCard', lift]]);
      const h = handWorld(S.o.pilot, 'R');
      const crumble = ramp(c.k, 0.55, 0.95);
      S.o.keycard.visible = crumble < 0.9;
      S.o.keycard.position.copy(h).add(V(-0.02, 0.02, -0.04));
      S.o.keycard.rotation.set(-0.8 * lift, 0.3, 0);
      S.o.keycard.scale.setScalar(1 - crumble);
      S.o.dust.visible = crumble > 0;
      const arr = S.o.dust.geometry.attributes.position;
      S.o.dust.userData.dirs.forEach((d, i) => arr.setXYZ(i, h.x + d.x * crumble * 0.25, h.y + d.y * crumble * 0.25 - crumble * crumble * 0.2, h.z + d.z * crumble * 0.25));
      arr.needsUpdate = true;
    },
  },
  v06: {
    set: 'cockpit', framing: 'face + hand on the headset',
    cam: cam([0.32, 1.25, -1.05], [0, 1.2, 0.1], 36, [0.26, 1.24, -0.98], null, 36),
    overlay: 'lyrics stutter and drop out · waveform goes flat',
    anim(S, c) {
      redAlarm(S, c.lt);
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 1], ['headsetL', sm(ramp(c.k, 0, 0.25))]]);
      sing(S.o.pilot, c.lt, 1.2);
    },
  },
  v09: {
    set: 'cockpit', framing: 'hands on the toggles',
    cam: cam([0, 0.98, -1.2], [0, 0.84, -0.45], 46, [0, 0.95, -1.08], null, 44),
    overlay: 'weapon wheel: Banana / GPT (code)',
    anim(S, c) {
      redAlarm(S, c.lt);
      pose(S.o.pilot, [['sit', 1], ['toggles', 1]]);
      const j = S.o.pilot.userData.j, e = Math.floor(c.lt / (BEAT / 2));
      j.shoulderL.rotation.z += Math.sin(e * 2.1) * 0.12; j.shoulderR.rotation.z += Math.cos(e * 1.7) * 0.12;
      S.o.toggles.forEach((t, i) => (t.rotation.x = ((e + i) % 3 === 0 ? 0.6 : -0.6)));
    },
  },
  v11: {
    set: 'cockpit', framing: 'pilot from behind + glass',
    cam: cam([0.45, 1.75, 0.72], [0, 1.1, -0.7], 56, [0.4, 1.72, 0.66], null, 54),
    overlay: '50 red pop-ups on the glass (code)',
    anim(S, c) {
      redAlarm(S, c.lt);
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 1], ['handsOnHead', sm(ramp(c.k, 0, 0.3))]]);
      const n = Math.floor(50 * ramp(c.k, 0.05, 0.85));
      S.o.popups.children.forEach((p, i) => (p.visible = i < n));
    },
  },
  v12: {
    set: 'cockpit', framing: 'pilot, waist up',
    cam: cam([0.35, 1.2, -1.4], [0, 1.08, 0.1], 46, [0.3, 1.18, -1.25], null, 46),
    overlay: 'leviathan shadow (code shadow pass)',
    anim(S, c) {
      redAlarm(S, c.lt);
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 1], ['coverFace', sm(ramp(c.k, 0, 0.3))]]);
      S.o.popups.children.forEach(p => (p.visible = true));
      S.o.shadow.visible = true;
      S.o.shadow.position.set(-7 + 14 * c.k, 3.2, -1.2);
      S.o.key.intensity *= 1 - 0.8 * Math.exp(-Math.pow((c.k - 0.5) * 4, 2));
    },
  },
  // ---------------- B · space, swarm
  h02: {
    set: 'space', framing: 'ship in the swarm',
    cam: cam([14, 5, 12], [0, 0, -2], 50, [6, 3, 16], null, 50, 'linear'),
    overlay: 'HOOK text holds until 3.6 s',
    anim(S, c) {
      swarm(S, c.T, 30);
      S.o.ship.rotation.set(0.1 * Math.sin(c.k * 6), 0.15 * Math.sin(c.k * 3), -sm(c.k) * Math.PI * 2);
      S.o.trailsRed.visible = true;
      S.o.trailsRed.children.forEach((l, i) => trailAt(l, ramp(c.k, i * 0.04, 0.55 + i * 0.04), 0.4));
      S.o.redLight.intensity = 2;
    },
  },
  v07: {
    set: 'space', framing: 'ship antenna',
    cam: cam([6, 4.5, 9], [0, 1.2, 2], 35, [5.2, 3.8, 8.2], null, 35),
    overlay: '—',
    anim(S, c) {
      const o = S.o; swarm(S, c.T);
      const bite = 0.45, a = sm(ramp(c.k, 0, bite));
      o.biter.visible = true;
      const ant = V(0, 1.6, 2.3);
      if (c.k < bite) o.biter.position.copy(V(-7, 6, -6).lerp(ant.clone().add(V(0.5, 0.3, 0.5)), a));
      else o.biter.position.copy(ant).add(V(0.5 - (c.k - bite) * 8, 0.3 + (c.k - bite) * 6, 0.5 - (c.k - bite) * 6));
      o.biter.lookAt(ant);
      if (c.k > bite) {
        const d = c.k - bite;
        o.antennaLoose.position.set(d * 5, 0.75 + d * 4, 2.0 + d * 7);
        o.antennaLoose.rotation.set(d * 12, d * 5, d * 9);
        o.sparks.visible = true;
        const arr = o.sparks.geometry.attributes.position;
        o.sparks.userData.dirs.forEach((v, i) => arr.setXYZ(i, v.x * d * 3, 1.2 + v.y * d * 3, 2.2 + v.z * d * 3));
        arr.needsUpdate = true;
      }
    },
  },
  v08: {
    set: 'space', ref: 'monster', framing: 'THE 503 behind the ship',
    cam: cam([0, -1.5, 15], [0, 25, -300], 45, [0, -2.2, 17], [0, 55, -300], 45, 'inOut'),
    overlay: 'static band at the bottom only, no white-out',
    anim(S, c) {
      const o = S.o; swarm(S, c.T, 12);
      const part = sm(ramp(c.k, 0.1, 0.55));
      o.noiseL.visible = o.noiseR.visible = part < 1;
      o.noiseL.position.set(-150 - part * 170, 40, -180); o.noiseR.position.set(150 + part * 170, 40, -180);
      o.noiseL.material.map.offset.set(Math.random(), Math.random());
      o.the503.position.y = -220 + 260 * sm(ramp(c.k, 0.12, 0.8));
      o.the503.getObjectByName('lid').visible = c.k < 0.82;
      o.redLight.intensity = 3 * ramp(c.k, 0.8, 0.9);
    },
  },
  v10: {
    set: 'space', ref: 'monster', framing: 'THE 503 hide',
    cam: cam([22, 25, -170], [0, 70, -300], 45, [18, 22, -185], null, 45),
    overlay: '—',
    anim(S, c) {
      const o = S.o; swarm(S, c.T, 12); o.redLight.intensity = 3;
      const shoot = (bolt, t0, hit, away, bi) => {
        const from = V(2, 0, -6), k1 = ramp(c.k, t0, t0 + 0.35), k2 = ramp(c.k, t0 + 0.35, t0 + 0.7);
        bolt.visible = k1 > 0 && k2 < 1;
        const pos = k1 < 1 ? from.clone().lerp(hit, k1) : hit.clone().lerp(away, k2);
        const dir = k1 < 1 ? hit.clone().sub(from) : away.clone().sub(hit);
        bolt.position.copy(pos);
        bolt.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
        const b = o.bursts[bi]; b.position.copy(hit); b.scale.setScalar(4); burstAt(b, ramp(c.k, t0 + 0.35, t0 + 0.6));
      };
      shoot(o.boltC, 0.02, V(-30, 92, -287), V(-260, 250, -120), 0);
      shoot(o.boltM, 0.18, V(35, 80, -285), V(260, 180, -60), 1);
    },
  },
  // ---------------- C · carrier deck
  p13: {
    set: 'carrier', framing: 'squadron of models',
    cam: cam([0, 0.8, 1.5], [0, 1.4, -8], 44, [0, 0.85, 3], [0, 1.4, -4], 44, 'linear'),
    overlay: 'service badges flip above their heads (code)',
    anim(S, c) {
      S.o.models.forEach(m => { m.position.z = -8 + c.lt * 1.3 - m.userData.back; walk(m, c.T); });
      badges(S, c.T);
    },
  },
  p14: {
    set: 'carrier', framing: 'lead model from behind',
    cam: cam([0.7, 1.65, -6.2], [0, 1.6, -3.2], 36, [0.6, 1.62, -3.6], [0, 1.6, -0.6], 36, 'linear'),
    overlay: 'badge settles on "+100 more"',
    anim(S, c) {
      const o = S.o;
      o.models.forEach(m => { m.position.z = -3.3 + c.lt * 0.9 - m.userData.back; walk(m, c.T, m === o.lead ? 1 - ramp(c.k, 0.15, 0.3) : 1); });
      badges(S, c.T);
      const L = o.lead, j = L.userData.j, turn = sm(ramp(c.k, 0.15, 0.45));
      if (turn > 0) {
        const on = sm(ramp(c.k, 0.55, 0.85));
        pose(L, [['stand', 1], ['helmetOn', on]]);
        j.neck.rotation.y = 1.1 * turn * (1 - on * 0.6); j.spine.rotation.y = 0.45 * turn;
        if (c.k > 0.85) { j.head.add(j.helmet); j.helmet.position.set(0, 0.02, 0); }
      }
      L.userData.badges.forEach(b => (b.visible = c.k < 0.6 && b.visible));
      L.userData.more.visible = c.k >= 0.6;
    },
  },
  c18: {
    set: 'carrier', framing: 'six fighters',
    cam: cam([-6, 1.6, 32], [0, 2.5, -10], 55, [-6, 2.2, 30], [0, 6, -40], 55, 'linear'),
    overlay: '—',
    anim(S, c) {
      S.o.models.forEach(m => (m.visible = false));
      S.o.launch.forEach((f, i) => {
        const dt = Math.max(0, c.lt - i * 0.26), b = f.userData.base;
        const dz = 70 * dt * dt + 4 * dt;
        f.position.set(b.x, b.y + Math.max(0, dz - 45) * 0.18, b.z - dz);
        f.rotation.x = Math.max(0, dz - 45) * 0.004;
        const tr = f.userData.trail; tr.visible = dt > 0;
        tr.position.set(b.x, 0.3, b.z - dz / 2 + 2); tr.scale.set(1, Math.max(0.01, dz), 1);
      });
    },
  },
  // ---------------- D · cockpit, orange
  p15: {
    set: 'cockpit', framing: 'pilot in profile',
    cam: cam([0.75, 1.2, -0.95], [0, 1.0, 0], 50, [0.68, 1.18, -0.88], null, 48),
    overlay: '"Use the Force" inverted: he lets go of the stick',
    anim(S, c) {
      setMood(S, 'red'); S.o.key.intensity = 4;
      const off = sm(ramp(c.k, 0.05, 0.3)), slide = sm(ramp(c.k, 0.45, 0.72));
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 1 - off], ['handsUp', off * (1 - slide)], ['slideCard', slide]]);
      const h = handWorld(S.o.pilot, 'R');
      const go = sm(ramp(c.k, 0.72, 1));
      S.o.brief.visible = c.k > 0.4;
      S.o.brief.position.copy(h).lerp(V(0, 0.9, -0.62), go);
      S.o.brief.rotation.set(0, 0.3 * (1 - go), 0);
    },
  },
  c16: {
    set: 'cockpit', framing: 'agent orb',
    cam: cam([0.18, 0.92, -1.25], [0, 0.97, -0.62], 38, [0.12, 0.94, -1.05], null, 32, 'out'),
    overlay: 'agent HUD unfolds · lyrics turn orange',
    anim(S, c) {
      setMood(S, 'red'); S.o.key.intensity = 4;
      setMood(S, 'orange', sm(ramp(c.k, 0.1, 0.55)));
      pose(S.o.pilot, [['sit', 1], ['handsUp', 0.4]]);
      const ign = ramp(c.k, 0.08, 0.3);
      S.o.orb.scale.setScalar(1 + 0.5 * ign + 0.08 * Math.sin(c.lt * 12) * ign);
      S.o.orb.getObjectByName('light').intensity = 0.6 + 5 * ign;
      ringAt(S.o.agentRing, ramp(c.k, 0.25, 0.95), 5);
    },
  },
  c17: {
    set: 'cockpit', framing: 'pilot, chest up',
    cam: cam([0, 1.15, -1.4], [0, 1.15, 0.1], 46, [0.08, 1.15, -1.3], null, 46),
    overlay: 'lyrics orange',
    anim(S, c) {
      setMood(S, 'orange');
      pose(S.o.pilot, [['sit', 1], ['behindHead', sm(ramp(c.k, 0, 0.35))]]);
      sing(S.o.pilot, c.lt);
      S.o.orb.scale.setScalar(1.2); S.o.orb.getObjectByName('light').intensity = 3;
    },
  },
  c19: {
    set: 'cockpit', framing: 'pilot + plan HUD',
    cam: cam([0.05, 1.15, -1.45], [0, 1.15, 0.1], 54, [0.08, 1.17, -1.55], null, 58, 'out'),
    overlay: 'shot plan HUD ×1.5 (code)',
    anim(S, c) {
      setMood(S, 'orange');
      pose(S.o.pilot, [['sit', 1], ['behindHead', 1 - sm(ramp(c.k, 0, 0.4))]]);
      S.o.plan.visible = true;
      S.o.plan.children.forEach((p, i) => (p.visible = c.k > 0.1 + i * 0.18));
      S.o.orb.scale.setScalar(1.2); S.o.orb.getObjectByName('light').intensity = 3;
    },
  },
  c20: {
    set: 'cockpit', framing: 'fist / APPROVE',
    cam: cam([0.22, 1.02, -1.15], [0, 0.8, -0.62], 40, [0.18, 0.98, -1.05], null, 40, 'out'),
    shake: [0.06],
    overlay: 'APPROVE on the 39.79 downbeat · shockwave',
    anim(S, c) {
      setMood(S, 'orange');
      const down = c.lt < 0.06 ? sm(c.lt / 0.06) : 1 - sm(ramp(c.lt, 0.45, 0.9));
      pose(S.o.pilot, [['sit', 1], ['pressCUp', 1], ['pressC', down]]);
      S.o.approve.position.y = 0.8 - 0.02 * (c.lt > 0.05 && c.lt < 0.5 ? 1 : 0);
      ringAt(S.o.shock, ramp(c.lt, 0.05, 1.0), 14);
      S.o.orb.scale.setScalar(1.2); S.o.orb.getObjectByName('light').intensity = 3 + 4 * Math.exp(-c.lt * 4);
    },
  },
  // ---------------- E · dogfight (space set)
  c21: {
    set: 'space', framing: 'squadron vs swarm',
    cam: cam([-22, 12, 28], [0, 0, -30], 55, [-14, 8, 30], null, 55, 'linear'),
    overlay: 'Itano Circus: hundreds of orange missiles',
    anim(S, c) {
      const o = S.o; swarm(S, c.T, 8);
      o.squad.forEach(f => (f.visible = true));
      o.trailsOrange.visible = true;
      o.trailsOrange.children.forEach((l, i) => trailAt(l, ramp(c.k, (i % 20) * 0.015, 0.4 + (i % 20) * 0.015 + (i >= 20 ? 0.25 : 0)), 0.35));
      o.drones.children.forEach((d, i) => {
        const kt = 0.3 + (i / 80) * 0.6;
        if (c.k > kt) d.visible = false;
        if (i < o.bursts.length) { o.bursts[i].position.copy(d.position); burstAt(o.bursts[i], (c.k - kt) / 0.12); }
      });
    },
  },
  c22: {
    set: 'space', framing: 'wingmate "fal"',
    cam: cam([15, 3.5, 17], [9, 1, 4], 45, [14.2, 3.2, 16], null, 45),
    shake: [0.55],
    overlay: '"fal" badge above the wingmate',
    anim(S, c) {
      const o = S.o; swarm(S, c.T, 10);
      o.squad.forEach(f => (f.visible = true));
      const fal = o.squad[1], hit = 0.3;
      fal.visible = c.k < hit + 0.02;
      fal.rotation.z = Math.sin(c.lt * 3) * 0.1;
      o.burstFal.position.copy(fal.position); o.burstFal.scale.setScalar(1);
      burstAt(o.burstFal, ramp(c.k, hit, 1));
    },
  },
  c23: {
    set: 'space', framing: 'replacement slides into the slot',
    cam: cam([16, 5, 16], [12, 1, 5], 50, [14, 4, 15], [9, 1, 5], 50),
    overlay: 'Tron lines: one derezzes, the next lights up (code)',
    anim(S, c) {
      const o = S.o; swarm(S, c.T, 10);
      o.squad.forEach((f, i) => (f.visible = i !== 1));
      const e = 1 - Math.pow(1 - ramp(c.k, 0, 0.75), 3);
      const from = V(40, 1, 9), to = o.squad[1].userData.slot;
      o.replacement.visible = true;
      o.replacement.position.copy(from).lerp(to, e);
      o.replacement.rotation.set(0, (1 - e) * 1.1, (1 - e) * 0.5);
      o.slideTrail.visible = true;
      const mid = from.clone().add(o.replacement.position).multiplyScalar(0.5);
      o.slideTrail.position.set(mid.x, 0.4, mid.z);
      o.slideTrail.scale.set(Math.max(0.01, from.distanceTo(o.replacement.position)), 1, 1);
      o.slideTrail.rotation.z = -Math.atan2(from.z - o.replacement.position.z, from.x - o.replacement.position.x);
    },
  },
  // ---------------- E2 · assault on THE 503 (director, 2026-10-26: "on 'MCP API' the ships attack the monster together from all sides, the hero ship dives straight into its mouth")
  c24: {
    set: 'space', framing: 'squadron fans out',
    cam: cam([0, 16, 80], [0, 5, -100], 55, [0, 12, 64], null, 55),
    overlay: 'lyrics orange · provider badges on the fighters',
    anim(S, c) {
      const o = S.o, fl = assaultBase(S);
      o.ship.position.z = -6 * c.k; boost(o.ship, 0.5);
      o.the503.getObjectByName('jawUpper').rotation.x = -0.12; o.the503.getObjectByName('jawLower').rotation.x = 0.1;
      o.redLight.intensity = 3;
      const slots = [o.squad[0], o.squad[1], o.squad[2], o.squad[3], o.squad[4]].map(f => f.userData.slot);
      fl.forEach((f, i) => {
        const t0 = i * BEAT * 0.6, go = sm(ramp(c.lt, t0, t0 + 0.9)), a = o.assault[i];
        const from = slots[i], to = from.clone().lerp(a.station, 0.3);
        f.visible = true;
        f.position.copy(from).lerp(to, go);
        aim(f, go > 0.02 ? a.station : V(from.x, from.y, from.z - 50), (i % 2 ? -1 : 1) * 0.8 * Math.sin(go * Math.PI));
        boost(f, go);
      });
    },
  },
  c25: {
    set: 'space', ref: 'monster', helperFar: 40, framing: 'assault from five sides',
    cam: cam([-330, 55, 90], [0, 5, -170], 55, [330, 40, 110], null, 55),
    overlay: 'OpenRouter for video: each fighter is a provider, all hit one brief (badges, code)',
    anim(S, c) {
      const o = S.o, fl = assaultBase(S);
      fl.forEach((f, i) => strafe(f, o.assault[i], c.T, i));
      const ev = [[0, 5.08]]; // "VARG!" stamp lands at 55.63
      o.assault.forEach((a, i) => {
        const k0 = 0.06 + 0.13 * i;
        a.trails.visible = true;
        a.trails.children.forEach((l, j) => { const p = ramp(c.k, k0 + j * 0.012, k0 + 0.3 + j * 0.012); trailAt(l, p, 0.3); if (p >= 1) l.visible = false; });
        ev.push([i, (k0 + 0.3) * c.dur]);
      });
      strikes(S, c.lt, ev.sort((x, y) => x[1] - y[1]));
      o.ship.position.set(Math.sin(c.lt * 1.5) * 1.5, 0, -6 - 64 * c.k); boost(o.ship, 1);
      o.the503.getObjectByName('jawUpper').rotation.x = -0.12 - 0.04 * c.k; o.the503.getObjectByName('jawLower').rotation.x = 0.1 + 0.03 * c.k;
    },
  },
  c26: {
    set: 'space', helperFar: 6, framing: 'hero dives into the mouth',
    cam: cam([0, 5, -40], [0, 0, -200], 50, [0, 2, -140], [0, -1, -260], 55, 'in'),
    shake: [0.257, 0.847, 1.917, 2.3],
    overlay: 'stamps VARG! DOT! A! I! on the hits · varg.ai lockup (58.17) over the closed jaws',
    anim(S, c) {
      const o = S.o, fl = assaultBase(S);
      fl.forEach((f, i) => strafe(f, o.assault[i], c.T, i));
      strikes(S, c.lt, [[0, -0.3], [1, 0.257], [2, 0.847], [3, 1.917]]); // VARG (end of c25) · DOT · A · I
      const dive = Math.min(1, c.lt / 2.3);
      o.ship.position.set(0, -2 * dive, -70 - 160 * Math.pow(dive, 1.4)); boost(o.ship, 2);
      const open = sm(ramp(c.lt, 0, 1.0)), slam = sm(ramp(c.lt, 2.24, 2.36));
      o.the503.getObjectByName('jawUpper').rotation.x = -(0.15 + 0.27 * open) * (1 - slam);
      o.the503.getObjectByName('jawLower').rotation.x = (0.12 + 0.24 * open) * (1 - slam);
      const dark = ramp(c.lt, 2.36, 2.6);
      o.dark.visible = dark > 0; o.dark.material.opacity = dark; o.dark.position.copy(c.camPos);
      o.orbGlow.visible = dark > 0.5; o.orbGlow.scale.setScalar(14); o.orbGlow.position.copy(o.ship.position).add(V(0, 1, 0));
    },
  },
  // ---------------- F · inside the beast
  x27: {
    set: 'beast', framing: 'cavity inside the beast',
    cam: cam([0, 3.2, 13], [0, 1.2, -25], 50, [0, 2.6, 9], null, 50),
    overlay: 'darkness, only the orange orb glows → the cavity neon lights up beat by beat',
    anim(S, c) {
      const o = S.o; tunnel(S, c.T, 6);
      o.pilot.position.y = 0.9; pose(o.pilot, [['crouch', 1]]); o.sax.visible = false;
      o.drones.children.forEach(d => d.position.copy(d.userData.base).add(V(0, 0, -40)));
      const b = c.lt / BEAT, step = b < 2 ? 0 : Math.min(4, Math.floor(b - 1)); // lights click on at beats 2, 3, 4, 5
      const dark = 1 - step / 4;
      o.dark.visible = dark > 0; o.dark.material.opacity = dark; o.dark.position.copy(c.camPos);
      o.orbGlow.visible = true; o.orbGlow.position.copy(o.ship.position).add(V(0, 0.6, -1.4));
      o.redKey.intensity = 30 * (step / 4);
    },
  },
  x28: {
    set: 'beast', framing: 'pilot on the hull',
    cam: cam([2.6, 2.3, -5], [0, 2.4, 0.3], 42, [2.0, 2.5, -4.0], null, 40),
    overlay: 'first note = neon sound ring (code)',
    anim(S, c) {
      const o = S.o; tunnel(S, c.T, 10);
      const up = sm(ramp(c.k, 0, 0.35));
      o.pilot.position.y = 0.9 + 1.05 * up;
      pose(o.pilot, [['crouch', 1 - up], ['stand', up], ['sax', ramp(c.k, 0.35, 0.6)], ['saxHigh', ramp(c.k, 0.65, 0.8)]]);
      o.sax.visible = c.k > 0.3;
      o.drones.children.forEach(d => d.position.copy(d.userData.base).add(V(0, 0, -40)));
      o.rings[0].position.set(0, 2.2, 0.2); o.rings[0].rotation.set(0, 0, 0);
      ringAt(o.rings[0], ramp(c.k, 0.78, 1), 10);
    },
  },
  x29: {
    set: 'beast', framing: 'ship in the tunnel',
    cam: cam([0, 6, 12], [0, 1.5, -30], 55, [0, 5.5, 10], null, 55, 'linear'),
    overlay: 'sound rings on the beat (code)',
    anim(S, c) {
      tunnel(S, c.T, 45);
      pose(S.o.pilot, [['stand', 1], ['saxHigh', 0.5 + 0.5 * Math.sin(c.lt * 4)]]);
      trench(S, c, 35, 0.1);
    },
  },
  x30: {
    set: 'beast', framing: 'fingers on the sax keys',
    cam: cam([0.6, 2.3, -0.9], [0.02, 2.05, 0.36], 34, [0.52, 2.26, -0.78], null, 34),
    overlay: '—',
    anim(S, c) {
      tunnel(S, c.T, 45);
      pose(S.o.pilot, [['stand', 1], ['sax', 1]]);
      const j = S.o.pilot.userData.j;
      j.elbowL.rotation.x += Math.sin(c.lt * 40) * 0.03; j.elbowR.rotation.x += Math.cos(c.lt * 37) * 0.03;
      trench(S, c, 35, 0);
    },
  },
  x31: {
    set: 'beast', framing: 'core eye + engines',
    cam: cam([-3.5, 1.2, 10], [0, 5, -80], 48, [-3, 1.4, 9], null, 48),
    shake: [0.65],
    overlay: 'at 73.91 the orb switches over: the right engine ignites',
    anim(S, c) {
      const o = S.o; tunnel(S, c.T, 15);
      o.drones.visible = false;
      pose(o.pilot, [['stand', 1], ['crouch', 0.6]]);
      o.sax.visible = false;
      const eyeW = o.pupil.getWorldPosition(V(0, 0, 0)), engL = V(-1.45, -0.05, 3.0);
      const fire = c.lt > 0.25 && c.lt < 0.9;
      o.laser.visible = fire;
      if (fire) {
        const L = eyeW.distanceTo(engL);
        o.laser.position.copy(eyeW).lerp(engL, 0.5); o.laser.scale.set(1, L, 1);
        o.laser.quaternion.setFromUnitVectors(V(0, 1, 0), engL.clone().sub(eyeW).normalize());
      }
      const dead = c.lt > 0.65;
      o.ship.getObjectByName('engineL').material.color.setHex(dead ? 0x220000 : C.red);
      o.ship.getObjectByName('flameL').visible = !dead;
      const reroute = 73.91 - 72.114, on = c.lt >= reroute;
      o.ship.getObjectByName('engineR').material.color.setHex(on ? C.orange : 0x331100);
      o.ship.getObjectByName('flameR').visible = on;
      o.ship.getObjectByName('flameR').scale.set(1, on ? 1.4 : 0.3, 1);
      o.shipOrb.scale.setScalar(on ? 1 + 1.5 * Math.exp(-(c.lt - reroute) * 3) : 1);
      o.ship.rotation.z = dead && !on ? -0.12 : 0;
    },
  },
  x33: {
    set: 'beast', framing: 'core cracks → stargate',
    cam: cam([0, 2.5, 11], [0, 4, -100], 50, [0, 2.5, 4], null, 60, 'in'),
    overlay: '2001: slit-scan',
    anim(S, c) {
      const o = S.o; tunnel(S, c.T, 20);
      o.drones.visible = false;
      pose(o.pilot, [['stand', 1], ['saxHigh', 1]]);
      o.cracks.visible = true; o.cracks.scale.setScalar(sm(ramp(c.k, 0, 0.45)) * 1.4 + 0.01);
      o.pupil.material.color.lerp(new THREE.Color(0xffffff), ramp(c.k, 0.1, 0.4));
      o.pupil.material.emissive.lerp(new THREE.Color(0xffffff), ramp(c.k, 0.1, 0.4));
      o.white.intensity = 400 * ramp(c.k, 0.1, 0.5);
      const fl = ramp(c.k, 0.38, 0.5) * (1 - ramp(c.k, 0.52, 0.65));
      o.flash.visible = fl > 0; o.flash.material.opacity = fl;
      if (c.k > 0.5) {
        o.tube.visible = o.scroll.visible = o.core.visible = false;
        S.scene.background.setHex(0x000000); S.scene.fog.color.setHex(0x000000);
        o.stargate.visible = true; o.stargateTex.offset.x = -c.lt * 1.8;
      }
    },
  },
  // ---------------- reuse: odyssey
  x32: {
    set: 'odyssey', framing: 'pilot eyes',
    cam: cam([0.03, 1.31, -0.42], [0.036, 1.305, 0], 20, [0.034, 1.31, -0.36], null, 18),
    helperFar: 0.25,
    overlay: 'reuse eye ECU: core reflection red → white',
    anim(S, c) { S.o.eyeLight.color.setHex(C.red).lerp(new THREE.Color(0xffffff), sm(c.k)); S.o.pilot.getObjectByName('boom').visible = false; },
  },
  x34: {
    set: 'odyssey', framing: 'grid of worlds',
    cam: cam([200, 0, 6], [200, 0, -12], 50, [200, 0, 4], null, 50, 'linear'),
    overlay: 'reuse s13b-e + worlds · grid 1→2→4→9 on the beat',
    anim(S, c) {
      const b = Math.floor(c.lt / BEAT), n = b < 3 ? 1 : b < 6 ? 2 : b < 9 ? 4 : 9;
      const cols = n === 9 ? 3 : n === 4 ? 2 : 1, rows = n / cols, W = 9, H = 16;
      S.o.tiles.forEach((t, i) => {
        t.visible = i < n;
        const cx = i % cols, cy = Math.floor(i / cols);
        t.position.set(-W / 2 + W / cols * (cx + 0.5), H / 2 - H / rows * (cy + 0.5), -12);
        t.scale.set(W / cols * 0.94, H / rows * 0.94, 1);
      });
      S.o.slitTex.offset.x = -c.lt * 2;
    },
  },
  x35: {
    set: 'odyssey', framing: 'squadron regroups',
    cam: cam([612, 4, 18], [600, 0, 0], 48, [604, 3, 20], null, 48),
    overlay: 'reuse o3',
    anim(S, c) { S.o.wing.forEach(f => f.position.copy(f.userData.from).lerp(f.userData.slot, 1 - Math.pow(1 - c.k, 3))); },
  },
  // ---------------- G · outro
  o36: {
    set: 'cockpit', framing: 'pilot, chest up',
    cam: cam([0, 1.18, -1.5], [0, 1.12, 0.1], 46, [0, 1.22, -1.1], [0, 1.2, 0.1], 40, 'linear'),
    overlay: 'last 1.2 s: "SEE YOU, SPACE CREATOR…" → cut to frame 1',
    anim(S, c) {
      setMood(S, 'calm');
      pose(S.o.pilot, [['sit', 1], ['stickAndThrottle', 0.3]]);
      sing(S.o.pilot, c.lt, c.lt < c.dur - 1.6 ? 0.8 : 0);
      const wink = c.dur - 2.4;
      S.o.pilot.getObjectByName('eyeR').scale.y = c.lt > wink && c.lt < wink + 0.35 ? 0.1 : 1;
      S.o.orb.scale.setScalar(1.15 + 0.08 * Math.sin(c.lt * 3));
      S.o.orb.getObjectByName('light').intensity = 2;
    },
  },
};
