/* Stickman rig for HyperFrames (and any seek-driven SVG renderer). MIT, vargHQ.
 *
 * One jointed SVG figure: round head, torso, two-bone arms and legs with FIXED bone lengths.
 * Poses are numbers (joint angles in degrees, offsets in px), never image swaps.
 * Everything is a pure function of time t: no Math.random, no clocks, no state between frames.
 *
 *   const hero = Stickman.create(svgGroup, { scale: 1.45, ground: 1420 });
 *   const P = Stickman.track(Stickman.DEFAULT_POSE, Stickman.LEAD);   // keyed channels
 *   P.move(2.0, 0.4, { aSh: 90, aEl: 10 }, "back");                  // at 2.0 s start, 0.4 s later arrive
 *   Stickman.draw(hero, P, t);                                         // call from the timeline clock
 *
 * Angle conventions (side view, figure faces +x before the `turn` flip):
 *   lean      torso tilt, + = forward            headTilt  head tilt vs torso, + = chin down
 *   aSh/bSh   shoulder: 0 = arm hangs, 90 = arm points forward, 180 = straight up, - = behind
 *   aEl/bEl   elbow bend, + = forearm folds forward/up
 *   a* = near arm (drawn in front), b* = far arm (drawn behind, darker)
 *   legs are solved by two-bone IK from foot targets, so feet stay on the ground and knees bend forward
 */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const D2R = Math.PI / 180;

  // Bone lengths in local units (multiplied by opts.scale). They never change at runtime.
  const BONES = { headR: 36, neck: 12, torso: 124, upperArm: 70, foreArm: 66, thigh: 86, shin: 84, foot: 24, hand: 8 };
  const HIP_H = 0.955 * (BONES.thigh + BONES.shin); // standing hip height: knees a hair soft, never locked

  const DEFAULT_POSE = {
    x: 0, y: 0, turn: 1, gait: 1, // world x of the hips, jump height (px, - = up), facing (+1 right, -1 left), walk cycle on/off
    hipDrop: 0, lean: 0, headTilt: 0,
    lookX: 1, lookY: 0, eyeOpen: 1, brow: 0, mouthOpen: 0, mouthCurve: 0,
    aSh: 8, aEl: 14, bSh: -6, bEl: 16,
    standA: 16, standB: -14, liftA: 0, liftB: 0,
    breath: 1, tremble: 0, wave: 0,
  };

  // Overlapping action: the head leads, the near arm follows, the far arm follows a little later.
  const LEAD = { headTilt: 0.05, lookX: 0.06, lookY: 0.06, brow: 0.04, aSh: -0.05, aEl: -0.07, bSh: -0.09, bEl: -0.11 };

  // ---------- easing ----------
  const walkEase = (u, a = 0.15) =>
    u < a ? (u * u) / (2 * a * (1 - a)) : u < 1 - a ? (u - a / 2) / (1 - a) : 1 - ((1 - u) * (1 - u)) / (2 * a * (1 - a));
  const EASES = {
    linear: (u) => u,
    inOut: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
    out: (u) => 1 - Math.pow(1 - u, 3),
    in: (u) => u * u * u,
    snap: (u) => 1 - Math.pow(1 - u, 5),
    back: (u) => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(u - 1, 3) + c1 * Math.pow(u - 1, 2); },
    walk: (u) => walkEase(u),
  };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, u) => a + (b - a) * u;
  const smooth = (e0, e1, v) => { const u = clamp((v - e0) / (e1 - e0), 0, 1); return u * u * (3 - 2 * u); };
  // deterministic hash noise in [-1, 1]
  const hash = (a, b) => { let h = (a * 374761393 + b * 668265263) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); h ^= h >>> 16; return ((h & 0xffff) / 0x7fff) - 1; };
  // smooth bump of width w centred at c (for blinks, flinches)
  const bump = (t, c, w) => { const u = Math.abs(t - c) / (w / 2); return u >= 1 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * u); };

  // ---------- keyed channels ----------
  function track(base, lead = {}) {
    const ch = {};
    for (const k in base) ch[k] = [{ t: -1e9, v: base[k], e: "linear" }];
    function valueAt(keys, t) {
      let i = keys.length - 1;
      while (i > 0 && keys[i].t > t) i--;
      const k0 = keys[i], k1 = keys[i + 1];
      if (!k1) return k0.v;
      const u = (t - k0.t) / (k1.t - k0.t);
      return lerp(k0.v, k1.v, (EASES[k1.e] || EASES.inOut)(clamp(u, 0, 1)));
    }
    const api = {
      channels: ch,
      value: (name, t) => valueAt(ch[name], t),
      // At t0 each named channel holds what it had; it arrives at the new value at t0 + dur.
      move(t0, dur, values, ease = "inOut") {
        for (const k in values) {
          if (!ch[k]) ch[k] = [{ t: -1e9, v: values[k], e: "linear" }];
          const keys = ch[k];
          const hold = valueAt(keys, t0);
          keys.push({ t: t0, v: hold, e: "linear" }, { t: t0 + Math.max(dur, 1e-3), v: values[k], e: ease });
          keys.sort((a, b) => a.t - b.t);
        }
        return api;
      },
      // Instant change (a cut), e.g. a teleport between scenes.
      set(t, values) { return api.move(t - 1e-3, 1e-3, values, "linear"); },
      at(t) {
        const p = {};
        for (const k in ch) p[k] = valueAt(ch[k], t + (lead[k] || 0));
        return p;
      },
      // Distance travelled along x up to t (sum of |dx| over keyed segments): drives the walk phase,
      // so feet stay planted at any speed and never slide while the cycle is on.
      dist(t, name = "x") {
        const keys = ch[name];
        let d = 0;
        for (let i = 1; i < keys.length; i++) {
          const a = keys[i - 1], b = keys[i];
          if (t >= b.t) d += Math.abs(b.v - a.v);
          else { if (t > a.t) d += Math.abs(valueAt(keys, t) - a.v); break; }
        }
        return d;
      },
      speed(t, name = "x") { const h = 1 / 60; return Math.abs(valueAt(ch[name], t + h) - valueAt(ch[name], t - h)) / (2 * h); },
    };
    return api;
  }

  // ---------- SVG figure ----------
  function create(parent, opts = {}) {
    const o = Object.assign({ scale: 1.4, ground: 1400, ink: "#f4f0e6", shade: "#8e97aa", face: "#0b0f18", outline: "#0b0f18", stroke: 15, stride: 72, lift: 24, bob: 6, swing: 24, blinks: [] }, opts);
    const mk = (tag, attrs, p) => { const e = document.createElementNS(NS, tag); for (const a in attrs) e.setAttribute(a, attrs[a]); p.appendChild(e); return e; };
    const root = mk("g", { class: "stickman" }, parent);
    const shadow = mk("ellipse", { fill: "#000", opacity: 0.4 }, root);
    const body = mk("g", {}, root);
    const line = (color, w) => ({ fill: "none", stroke: color, "stroke-width": w, "stroke-linecap": "round", "stroke-linejoin": "round" });
    const farArm = mk("path", line(o.shade, o.stroke - 2), body);
    const farHand = mk("circle", { fill: o.shade, r: BONES.hand }, body);
    const farLeg = mk("path", line(o.shade, o.stroke - 1), body);
    const torso = mk("path", line(o.ink, o.stroke + 1), body);
    // near limbs get a dark outline pass so a white arm crossing the white head or torso still reads as an arm
    const nearLegLine = mk("path", line(o.outline, o.stroke + 7), body);
    const nearLeg = mk("path", line(o.ink, o.stroke), body);
    const head = mk("circle", { fill: o.ink, r: BONES.headR }, body);
    const face = mk("g", {}, body);
    const eye1 = mk("ellipse", { fill: o.face }, face);
    const eye2 = mk("ellipse", { fill: o.face }, face);
    const brow1 = mk("path", line(o.face, 4), face);
    const brow2 = mk("path", line(o.face, 4), face);
    const mouthLine = mk("path", line(o.face, 4), face);
    const mouthO = mk("ellipse", { fill: o.face }, face);
    const nearArmLine = mk("path", line(o.outline, o.stroke + 7), body);
    const nearHandLine = mk("circle", { fill: o.outline, r: BONES.hand + 3.5 }, body);
    const nearArm = mk("path", line(o.ink, o.stroke), body);
    const nearHand = mk("circle", { fill: o.ink, r: BONES.hand }, body);
    return { o, root, shadow, body, farArm, farHand, farLeg, torso, nearLegLine, nearLeg, head, face, eye1, eye2, brow1, brow2, mouthLine, mouthO, nearArmLine, nearHandLine, nearArm, nearHand };
  }

  // Two-bone IK: hip H, foot target T, bone lengths a, b. Knee bends toward +x (forward).
  function ik(H, T, a, b) {
    let dx = T[0] - H[0], dy = T[1] - H[1];
    let D = Math.hypot(dx, dy);
    const Dc = clamp(D, Math.abs(a - b) + 0.5, a + b - 0.5);
    if (Dc !== D) { dx *= Dc / D; dy *= Dc / D; D = Dc; } // out of reach: foot stops where the leg ends (bones never stretch)
    const base = Math.atan2(dy, dx);
    const off = Math.acos(clamp((a * a + D * D - b * b) / (2 * a * D), -1, 1));
    const K = [H[0] + a * Math.cos(base - off), H[1] + a * Math.sin(base - off)];
    return { K, F: [H[0] + dx, H[1] + dy] };
  }

  // Walk cycle from distance travelled (local units). Returns foot offsets vs the hips and lifts.
  function gaitAt(dLocal, L, lift) {
    const foot = (off) => {
      const q = (dLocal + off) / (2 * L), f = q - Math.floor(q);
      if (f < 0.5) return { x: 2 * L * (0.25 - f), y: 0 }; // stance: planted, slides back under the moving hips
      const g = (f - 0.5) / 0.5; // swing: lifts and travels forward
      return { x: lerp(-L / 2, L / 2, EASES.inOut(g)), y: Math.sin(Math.PI * g) * lift, g };
    };
    const q = dLocal / (2 * L);
    return { A: foot(0), B: foot(L), bob: Math.cos(4 * Math.PI * (q - 0.25)) };
  }

  const P2 = (p) => p[0].toFixed(2) + " " + p[1].toFixed(2);

  function draw(fig, trackOrPose, t) {
    const o = fig.o, s = o.scale, R = BONES.headR;
    const isTrack = typeof trackOrPose.at === "function";
    const p = isTrack ? trackOrPose.at(t) : trackOrPose;

    // --- locomotion layer (only when the hips travel and gait is on) ---
    let walk = 0, gait = null;
    if (isTrack) {
      walk = smooth(4, 40, trackOrPose.speed(t)) * clamp(p.gait, 0, 1);
      gait = gaitAt(trackOrPose.dist(t) / s, o.stride, o.lift);
    }
    // --- idle layer: breathing, weight shift, tremble, all from t ---
    const br = Math.sin((2 * Math.PI * t) / 3.1), br2 = Math.sin((2 * Math.PI * t) / 3.1 - 0.7);
    const idle = p.breath * (1 - walk);
    const tr = p.tremble * (Math.sin(2 * Math.PI * 9.1 * t) * 0.6 + Math.sin(2 * Math.PI * 13.3 * t + 1.3) * 0.4);
    const shift = Math.sin((2 * Math.PI * t) / 5.7) * 3 * idle;

    const lean = p.lean + br * 0.9 * idle + walk * 6 + tr * 1.2;
    const headTilt = p.headTilt + br2 * 1.6 * idle + tr * 1.5;
    const bob = gait ? gait.bob * o.bob * walk : 0;
    const hipY = -(HIP_H - p.hipDrop + bob + br * 1.4 * idle);
    const H = [shift + tr * 2.4, hipY];

    // feet: mix the standing stance with the walk cycle
    const fa = gait ? gait.A : { x: 0, y: 0 }, fb = gait ? gait.B : { x: 0, y: 0 };
    const footA = [lerp(p.standA, fa.x, walk), -lerp(p.liftA, fa.y, walk)];
    const footB = [lerp(p.standB, fb.x, walk), -lerp(p.liftB, fb.y, walk)];
    const swingA = gait ? (fb.x / (o.stride / 2)) * walk : 0; // near arm swings with the far leg
    const swingB = gait ? (fa.x / (o.stride / 2)) * walk : 0;

    // torso and head
    const th = -Math.PI / 2 + lean * D2R;
    const C = [H[0] + BONES.torso * Math.cos(th), H[1] + BONES.torso * Math.sin(th)];
    const hh = th + headTilt * D2R;
    const Hc = [C[0] + (BONES.neck + R) * Math.cos(hh), C[1] + (BONES.neck + R) * Math.sin(hh)];
    const S = [H[0] + (BONES.torso - 10) * Math.cos(th), H[1] + (BONES.torso - 10) * Math.sin(th)];

    // line boil: tiny seeded jitter redrawn 12 times a second, keeps holds alive
    const fr = Math.floor(t * 12);
    const j = (id) => [hash(fr, id) * 0.8, hash(fr, id + 99) * 0.8];
    const add = (a, b) => [a[0] + b[0], a[1] + b[1]];

    // arms: forward kinematics from joint angles
    const waveOsc = p.wave * Math.sin(2 * Math.PI * 3.2 * t) * 28;
    const arm = (sh, el, sw, id) => {
      const a1 = Math.PI / 2 + lean * D2R - (sh + sw * o.swing) * D2R;
      const E = [S[0] + BONES.upperArm * Math.cos(a1), S[1] + BONES.upperArm * Math.sin(a1)];
      const a2 = a1 - (el + Math.abs(sw) * 10 + 6 * walk) * D2R;
      const W = [E[0] + BONES.foreArm * Math.cos(a2), E[1] + BONES.foreArm * Math.sin(a2)];
      return { E: add(E, j(id)), W: add(W, j(id + 1)) };
    };
    const A = arm(p.aSh + tr * 3 + br * 2 * idle, p.aEl + waveOsc, swingA, 1);
    const B = arm(p.bSh - tr * 3 - br2 * 2 * idle, p.bEl, swingB, 3);

    // legs: IK to the foot targets
    const LA = ik(H, footA, BONES.thigh, BONES.shin), LB = ik(H, footB, BONES.thigh, BONES.shin);
    const toe = (F, lift) => { const pitch = -clamp(-F[1] / o.lift, 0, 1) * 22 * D2R; return [F[0] + BONES.foot * Math.cos(pitch), F[1] - BONES.foot * Math.sin(pitch)]; };
    const KA = add(LA.K, j(5)), KB = add(LB.K, j(7));

    fig.nearLeg.setAttribute("d", `M${P2(H)} L${P2(KA)} L${P2(LA.F)} L${P2(toe(LA.F))}`);
    // outline starts partway down the bone, so the hip and shoulder joins stay clean
    const part = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
    fig.nearLegLine.setAttribute("d", `M${P2(part(H, KA, 0.4))} L${P2(KA)} L${P2(LA.F)} L${P2(toe(LA.F))}`);
    fig.farLeg.setAttribute("d", `M${P2(H)} L${P2(KB)} L${P2(LB.F)} L${P2(toe(LB.F))}`);
    fig.torso.setAttribute("d", `M${P2(H)} L${P2(C)} L${P2(Hc)}`);
    fig.nearArm.setAttribute("d", `M${P2(S)} L${P2(A.E)} L${P2(A.W)}`);
    fig.nearArmLine.setAttribute("d", `M${P2(part(S, A.E, 0.35))} L${P2(A.E)} L${P2(A.W)}`);
    fig.nearHandLine.setAttribute("cx", A.W[0].toFixed(2)); fig.nearHandLine.setAttribute("cy", A.W[1].toFixed(2));
    fig.farArm.setAttribute("d", `M${P2(S)} L${P2(B.E)} L${P2(B.W)}`);
    fig.nearHand.setAttribute("cx", A.W[0].toFixed(2)); fig.nearHand.setAttribute("cy", A.W[1].toFixed(2));
    fig.farHand.setAttribute("cx", B.W[0].toFixed(2)); fig.farHand.setAttribute("cy", B.W[1].toFixed(2));
    fig.head.setAttribute("cx", Hc[0].toFixed(2)); fig.head.setAttribute("cy", Hc[1].toFixed(2));

    // face: eyes slide across the head to turn it; spacing compresses toward profile
    let blink = 1;
    for (const b of o.blinks) blink = Math.min(blink, 1 - 0.9 * bump(t, b, 0.16));
    const lx = clamp(p.lookX, -1, 1), ly = clamp(p.lookY, -1, 1);
    const cx = R * 0.4 * lx, spacing = R * (0.56 - 0.24 * Math.abs(lx));
    const ey = -R * 0.08 + ly * R * 0.24;
    const sz = clamp(p.eyeOpen, 0.2, 1.8);
    const e1x = cx - spacing / 2, e2x = cx + spacing / 2;
    for (const [el, ex] of [[fig.eye1, e1x], [fig.eye2, e2x]]) {
      el.setAttribute("cx", ex.toFixed(2)); el.setAttribute("cy", ey.toFixed(2));
      el.setAttribute("rx", (R * 0.1 * (0.75 + 0.25 * sz) * (1 - 0.25 * Math.abs(lx) * (ex * lx < 0 ? 1 : 0))).toFixed(2));
      el.setAttribute("ry", (R * 0.15 * sz * blink).toFixed(2));
    }
    const by = ey - R * (0.26 + 0.06 * sz) - R * 0.06 * Math.max(0, p.brow), bt = p.brow * R * 0.09;
    fig.brow1.setAttribute("d", `M${(e1x - R * 0.13).toFixed(2)} ${(by + bt).toFixed(2)} L${(e1x + R * 0.12).toFixed(2)} ${(by - bt).toFixed(2)}`);
    fig.brow2.setAttribute("d", `M${(e2x - R * 0.12).toFixed(2)} ${(by - bt).toFixed(2)} L${(e2x + R * 0.13).toFixed(2)} ${(by + bt).toFixed(2)}`);
    const browOp = clamp(Math.abs(p.brow) * 2.5, 0, 1).toFixed(3);
    fig.brow1.setAttribute("opacity", browOp); fig.brow2.setAttribute("opacity", browOp);
    const my = R * 0.38 + ly * R * 0.14, mw = R * 0.15 * (1 - 0.35 * Math.abs(lx)), mo = clamp(p.mouthOpen, 0, 1);
    fig.mouthLine.setAttribute("d", `M${(cx - mw).toFixed(2)} ${my.toFixed(2)} Q${cx.toFixed(2)} ${(my + p.mouthCurve * R * 0.14).toFixed(2)} ${(cx + mw).toFixed(2)} ${my.toFixed(2)}`);
    fig.mouthLine.setAttribute("opacity", (1 - clamp(mo * 4, 0, 1)).toFixed(3));
    fig.mouthO.setAttribute("cx", cx.toFixed(2)); fig.mouthO.setAttribute("cy", (my + R * 0.04).toFixed(2));
    fig.mouthO.setAttribute("rx", (R * (0.08 + 0.05 * mo)).toFixed(2)); fig.mouthO.setAttribute("ry", (R * 0.17 * mo + 0.01).toFixed(2));
    fig.mouthO.setAttribute("opacity", mo > 0.04 ? "1" : "0");
    const headRot = (hh + Math.PI / 2) / D2R;
    fig.face.setAttribute("transform", `translate(${P2(Hc)}) rotate(${headRot.toFixed(2)})`);

    // place the whole figure: hips at world x, feet on the ground line; turn flips it (a quick squash through edge-on)
    const turn = clamp(p.turn, -1, 1), sx = Math.sign(turn || 1) * Math.max(0.12, Math.abs(turn));
    fig.body.setAttribute("transform", `translate(${p.x.toFixed(2)} ${(o.ground + p.y).toFixed(2)}) scale(${(sx * s).toFixed(4)} ${s.toFixed(4)})`);
    const air = clamp(-p.y / 220, 0, 0.7);
    fig.shadow.setAttribute("cx", p.x.toFixed(2)); fig.shadow.setAttribute("cy", (o.ground + 4).toFixed(2));
    fig.shadow.setAttribute("rx", (70 * s * (1 - air)).toFixed(2)); fig.shadow.setAttribute("ry", (11 * s * (1 - air)).toFixed(2));
    return { H, C, Hc, S, hands: [A.W, B.W] };
  }

  window.Stickman = { BONES, HIP_H, DEFAULT_POSE, LEAD, EASES, track, create, draw, ik, gaitAt, hash, bump, smooth, clamp, lerp };
})();
