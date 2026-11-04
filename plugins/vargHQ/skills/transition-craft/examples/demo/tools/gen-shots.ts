// Generates the five shots of the demo as small vector SVGs (no footage, no rights issues):
//   room.svg   – edit-suite plate with a centred monitor (screen 480x270 = 1/4 frame -> Droste k = 4)
//   ridge.svg  – dusk mountain ridges            (Droste landing, shake-cut A)
//   dunes.svg  – noon dunes                       (shake-cut B, tile-flip A)
//   harbor.svg – harbour city at night            (tile-flip B, bokeh A)
//   sea.svg    – morning sea with sun glitter     (bokeh B)
// plus highlights.json: the brightest points of harbor/sea that seed the bokeh discs.
// Run: bun tools/gen-shots.ts   (from examples/demo)
import { mkdirSync, writeFileSync } from "node:fs";

const W = 1920;
const H = 1080;
const OUT = new URL("../assets/shots/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });

function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 1D value noise with octaves
function noise1D(seed: number) {
  const r = rng(seed);
  const pts = Array.from({ length: 512 }, () => r());
  const smooth = (x: number) => {
    const i = Math.floor(x);
    const f = x - i;
    const u = f * f * (3 - 2 * f);
    return pts[i & 511] * (1 - u) + pts[(i + 1) & 511] * u;
  };
  return (x: number, oct = 5) => {
    let v = 0;
    let amp = 0.5;
    let fr = 1;
    for (let o = 0; o < oct; o++) {
      v += amp * smooth(x * fr);
      amp *= 0.5;
      fr *= 2.03;
    }
    return v; // ~0..1
  };
}

const f1 = (n: number) => n.toFixed(1);
const svg = (body: string, defs = "") =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${defs}</defs>${body}</svg>\n`;

// ---------------------------------------------------------------- ridge (dusk)
function ridge() {
  const r = rng(11);
  let defs = `
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0d1230"/><stop offset="0.38" stop-color="#2e2a5a"/>
    <stop offset="0.6" stop-color="#8a4f78"/><stop offset="0.74" stop-color="#e0866f"/>
    <stop offset="0.86" stop-color="#f6b27e"/><stop offset="1" stop-color="#f9cf98"/>
  </linearGradient>
  <radialGradient id="sunglow" cx="1250" cy="600" r="620" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ffe4b8" stop-opacity="0.95"/><stop offset="0.12" stop-color="#ffc98f" stop-opacity="0.55"/>
    <stop offset="0.45" stop-color="#f39a74" stop-opacity="0.18"/><stop offset="1" stop-color="#f39a74" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="haze" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f4b48a" stop-opacity="0"/><stop offset="1" stop-color="#f4b48a" stop-opacity="0.35"/>
  </linearGradient>`;
  let body = `<rect width="${W}" height="${H}" fill="url(#sky)"/>`;
  for (let i = 0; i < 160; i++) {
    const x = r() * W;
    const y = Math.pow(r(), 1.6) * 430;
    body += `<circle cx="${f1(x)}" cy="${f1(y)}" r="${(0.6 + r() * 1.1).toFixed(2)}" fill="#fff" opacity="${(0.15 + r() * 0.6 * (1 - y / 520)).toFixed(2)}"/>`;
  }
  body += `<rect width="${W}" height="${H}" fill="url(#sunglow)"/><circle cx="1250" cy="600" r="58" fill="#fff1d6"/>`;
  const layers = [
    { base: 700, amp: 120, sc: 0.0011, col: "#c98395", seed: 3 },
    { base: 760, amp: 150, sc: 0.0013, col: "#a0628a", seed: 5 },
    { base: 830, amp: 170, sc: 0.0015, col: "#6f4372", seed: 7 },
    { base: 910, amp: 180, sc: 0.0018, col: "#462d57", seed: 9 },
    { base: 1000, amp: 190, sc: 0.0021, col: "#26193c", seed: 13 },
    { base: 1090, amp: 200, sc: 0.0024, col: "#120c20", seed: 17 },
  ];
  layers.forEach((L, li) => {
    const n = noise1D(L.seed);
    let d = `M0 ${H} `;
    for (let x = 0; x <= W; x += 6) {
      const v = n(x * L.sc * 4 + li * 10, 4);
      const y = L.base - L.amp * Math.pow(v, 1.25) * 1.7;
      d += `L${x} ${f1(y)} `;
    }
    d += `L${W} ${H} Z`;
    body += `<path d="${d}" fill="${L.col}"/>`;
    if (li < 4) body += `<rect y="${L.base - 150}" width="${W}" height="210" fill="url(#haze)"/>`;
  });
  return svg(body, defs);
}

// ---------------------------------------------------------------- dunes (noon)
function dunes() {
  const r = rng(21);
  let defs = `
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1f5fa8"/><stop offset="0.35" stop-color="#4f8cc9"/>
    <stop offset="0.48" stop-color="#9cc3e3"/><stop offset="0.53" stop-color="#f1dcc0"/>
  </linearGradient>
  <radialGradient id="sun" cx="430" cy="150" r="520" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="0.1" stop-color="#fff6de" stop-opacity="0.5"/>
    <stop offset="1" stop-color="#fff6de" stop-opacity="0"/>
  </radialGradient>
  <filter id="cloud" x="-20%" y="-200%" width="140%" height="500%"><feGaussianBlur stdDeviation="5"/></filter>
  <linearGradient id="lit1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f2c08a"/><stop offset="1" stop-color="#e2a46a"/></linearGradient>
  <linearGradient id="lit2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eba46a"/><stop offset="1" stop-color="#d9874d"/></linearGradient>
  <linearGradient id="lit3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0a463"/><stop offset="1" stop-color="#d47a3f"/></linearGradient>
  <linearGradient id="sh" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9c4f2a"/><stop offset="1" stop-color="#6e3118"/></linearGradient>
  <linearGradient id="sh2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b8673a"/><stop offset="1" stop-color="#8a4322"/></linearGradient>`;
  let body = `<rect width="${W}" height="${H}" fill="url(#sky)"/><rect width="${W}" height="${H}" fill="url(#sun)"/><circle cx="430" cy="150" r="38" fill="#fffdf6"/>`;
  // thin high clouds
  for (let i = 0; i < 7; i++) {
    const x = 700 + r() * 1200;
    const y = 120 + r() * 260;
    body += `<ellipse cx="${f1(x)}" cy="${f1(y)}" rx="${f1(120 + r() * 220)}" ry="${f1(6 + r() * 8)}" fill="#ffffff" opacity="${(0.2 + r() * 0.25).toFixed(2)}" filter="url(#cloud)"/>`;
  }
  // dunes: sharp-crested humps (gentle windward slope left, steep lee right); the lee side is in shadow
  type Peak = { px: number; py: number; wl: number; wr: number };
  const layers: { base: number; peaks: Peak[]; lit: [string, string]; shade: [string, string] }[] = [
    { base: 640, peaks: [{ px: 260, py: 585, wl: 420, wr: 260 }, { px: 900, py: 560, wl: 520, wr: 330 }, { px: 1560, py: 575, wl: 480, wr: 300 }], lit: ["#f3d2ad", "#efc49a"], shade: ["#dcae86", "#d39f74"] },
    { base: 760, peaks: [{ px: 560, py: 630, wl: 700, wr: 380 }, { px: 1500, py: 650, wl: 560, wr: 420 }], lit: ["#efbb86", "#e7a96f"], shade: ["#c27c4b", "#b46d3e"] },
    { base: 1080, peaks: [{ px: 1060, py: 760, wl: 1300, wr: 620 }], lit: ["#f2ad6c", "#de8d4c"], shade: ["#9a4b25", "#7a3618"] },
  ];
  layers.forEach((L, li) => {
    defs += `<linearGradient id="dl${li}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${L.lit[0]}"/><stop offset="1" stop-color="${L.lit[1]}"/></linearGradient>`;
    defs += `<linearGradient id="ds${li}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${L.shade[0]}"/><stop offset="1" stop-color="${L.shade[1]}"/></linearGradient>`;
    if (L.base < H) body += `<rect y="${L.base - 1}" width="${W}" height="${H - L.base + 1}" fill="${L.lit[1]}"/>`;
    // each peak is its own dune, drawn left to right so a dune in front covers the lee shadow behind it
    L.peaks.forEach((p, pi) => {
      const prof = (x: number) => {
        const u = x < p.px ? (p.px - x) / p.wl : (x - p.px) / p.wr;
        return u < 1 ? L.base - (L.base - p.py) * Math.pow(1 - u, 1.7) : L.base;
      };
      const x0 = Math.max(-40, p.px - p.wl);
      const x1 = Math.min(W + 40, p.px + p.wr);
      let d = `M${f1(x0)} ${L.base} `;
      for (let x = x0; x <= x1; x += 6) d += `L${f1(x)} ${f1(prof(x))} `;
      d += `L${f1(x1)} ${L.base} Z`;
      body += `<path d="${d}" fill="url(#dl${li})"/>`;
      // lee shadow: crest -> concave boundary to the bottom -> back up along the lee slope
      const span = L.base - p.py;
      let sh = `M${p.px} ${p.py} C ${f1(p.px + 0.03 * p.wr)} ${f1(p.py + span * 0.35)} ${f1(p.px + 0.08 * p.wr)} ${f1(p.py + span * 0.75)} ${f1(p.px + 0.22 * p.wr)} ${L.base} L ${f1(x1)} ${L.base} `;
      for (let x = x1; x >= p.px; x -= 6) sh += `L${f1(x)} ${f1(prof(x))} `;
      sh += "Z";
      body += `<path d="${sh}" fill="url(#ds${li})"/>`;
      if (li > 0) {
        for (let i = 0; i < 10 * li; i++) {
          const xa = p.px - p.wl * (0.1 + r() * 0.75);
          const ya = prof(xa) + 16 + r() * (li === 2 ? 240 : 50);
          const len = Math.min(p.px - xa - 10, 100 + r() * 240);
          if (len < 40) continue;
          body += `<path d="M${f1(xa)} ${f1(ya)} q ${f1(len / 2)} ${f1(-8 - r() * 8)} ${f1(len)} ${f1(-4 + r() * 8)}" stroke="#ffe2bd" stroke-width="${li === 2 ? 2 : 1.3}" fill="none" opacity="${(0.16 + r() * 0.18).toFixed(2)}"/>`;
        }
      }
      body += `<path d="M${f1(p.px - p.wl * 0.45)} ${f1(prof(p.px - p.wl * 0.45))} Q ${f1(p.px - p.wl * 0.18)} ${f1(p.py + 3)} ${p.px} ${p.py}" stroke="#fff0da" stroke-width="2" fill="none" opacity="0.3"/>`;
    });
  });
  return svg(body, defs);
}

// ---------------------------------------------------------------- harbour (night)
function harbor() {
  const r = rng(31);
  const horizon = 640;
  const defs = `
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#04060e"/><stop offset="0.5" stop-color="#0b1430"/>
    <stop offset="0.6" stop-color="#1c2650"/><stop offset="0.62" stop-color="#3a2a48"/>
  </linearGradient>
  <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0d1430"/><stop offset="1" stop-color="#02040a"/>
  </linearGradient>
  <radialGradient id="cityglow" cx="960" cy="${horizon}" r="900" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ff9a5a" stop-opacity="0.28"/><stop offset="1" stop-color="#ff9a5a" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="lamp"><stop offset="0" stop-color="#fffaf0"/><stop offset="0.18" stop-color="#ffe2b0"/>
    <stop offset="0.45" stop-color="#ffb86b" stop-opacity="0.45"/><stop offset="1" stop-color="#ff9a4a" stop-opacity="0"/></radialGradient>
  <linearGradient id="refl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffcf8a" stop-opacity="0.8"/><stop offset="1" stop-color="#ffcf8a" stop-opacity="0"/></linearGradient>`;
  let body = `<rect width="${W}" height="${H}" fill="url(#sky)"/>`;
  for (let i = 0; i < 70; i++)
    body += `<circle cx="${f1(r() * W)}" cy="${f1(r() * 330)}" r="${(0.5 + r() * 0.9).toFixed(2)}" fill="#cfd8ff" opacity="${(0.15 + r() * 0.4).toFixed(2)}"/>`;
  body += `<circle cx="1580" cy="170" r="26" fill="#f3f0e6" opacity="0.92"/><circle cx="1580" cy="170" r="70" fill="#f3f0e6" opacity="0.06"/>`;
  body += `<rect width="${W}" height="${horizon + 20}" fill="url(#cityglow)"/>`;
  const highlights: { x: number; y: number; c: string; w: number }[] = [];
  // two rows of buildings (back row lighter)
  for (const row of [
    { col: "#141a33", hmin: 160, hmax: 420, wl: 0.18, seed: 1 },
    { col: "#0a0e1d", hmin: 90, hmax: 330, wl: 0.32, seed: 2 },
  ]) {
    let x = -20;
    while (x < W + 20) {
      const bw = 70 + r() * 120;
      const centreBoost = 1 - Math.abs(x + bw / 2 - 960) / 1300;
      const bh = row.hmin + (row.hmax - row.hmin) * Math.pow(r(), 0.8) * (0.6 + 0.6 * centreBoost);
      const top = horizon - bh;
      body += `<rect x="${f1(x)}" y="${f1(top)}" width="${f1(bw)}" height="${f1(bh + 2)}" fill="${row.col}"/>`;
      if (bh > 300 && r() < 0.6) body += `<circle cx="${f1(x + bw / 2)}" cy="${f1(top - 6)}" r="2.6" fill="#ff4a3a"/>`;
      for (let wy = top + 14; wy < horizon - 14; wy += 20) {
        for (let wx = x + 9; wx < x + bw - 12; wx += 15) {
          if (r() < row.wl) {
            const c = ["#ffd28a", "#ffb86b", "#fff0c8", "#ffe1a3"][Math.floor(r() * 4)];
            const op = 0.45 + r() * 0.55;
            body += `<rect x="${f1(wx)}" y="${f1(wy)}" width="6" height="9" fill="${c}" opacity="${op.toFixed(2)}"/>`;
          }
        }
      }
      x += bw + 2 + r() * 10;
    }
  }
  // promenade + water
  body += `<rect y="${horizon}" width="${W}" height="18" fill="#05070f"/>`;
  body += `<rect y="${horizon + 18}" width="${W}" height="${H - horizon - 18}" fill="url(#water)"/>`;
  // window light reflections: soft broken streaks
  for (let i = 0; i < 140; i++) {
    const x = r() * W;
    const y = horizon + 30 + Math.pow(r(), 1.5) * 300;
    body += `<rect x="${f1(x)}" y="${f1(y)}" width="${f1(10 + r() * 30)}" height="2" fill="#ffc98a" opacity="${(0.08 + r() * 0.2).toFixed(2)}"/>`;
  }
  // street lamps along the waterfront
  for (let i = 0; i < 17; i++) {
    const x = 70 + i * 112 + (r() - 0.5) * 20;
    const y = horizon - 46;
    body += `<rect x="${f1(x - 1.5)}" y="${y}" width="3" height="46" fill="#05070f"/>`;
    body += `<circle cx="${f1(x)}" cy="${y}" r="34" fill="url(#lamp)"/><circle cx="${f1(x)}" cy="${y}" r="4.5" fill="#fffaf0"/>`;
    // reflection column
    for (let k = 0; k < 14; k++) {
      const ry = horizon + 26 + k * 22 + r() * 6;
      const rw = 6 + r() * 16 + k * 1.2;
      body += `<rect x="${f1(x - rw / 2 + (r() - 0.5) * 8)}" y="${f1(ry)}" width="${f1(rw)}" height="3" fill="#ffd9a0" opacity="${(0.75 * (1 - k / 15)).toFixed(2)}"/>`;
    }
    highlights.push({ x: Math.round(x), y, c: "#ffd9a0", w: 1 });
    highlights.push({ x: Math.round(x + (r() - 0.5) * 10), y: Math.round(horizon + 60 + r() * 120), c: "#ffc27a", w: 0.6 });
  }
  return { svg: svg(body, defs), highlights };
}

// ---------------------------------------------------------------- sea (morning)
function sea() {
  const r = rng(41);
  const horizon = 560;
  const defs = `
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#5e7fb8"/><stop offset="0.3" stop-color="#9eaed0"/>
    <stop offset="0.43" stop-color="#f0c6aa"/><stop offset="0.52" stop-color="#fde2bf"/>
  </linearGradient>
  <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#7d8fad"/><stop offset="0.25" stop-color="#3e5a82"/><stop offset="1" stop-color="#16294a"/>
  </linearGradient>
  <radialGradient id="glow" cx="960" cy="${horizon - 70}" r="700" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#fff7e6" stop-opacity="0.95"/><stop offset="0.08" stop-color="#ffe7c2" stop-opacity="0.6"/>
    <stop offset="0.4" stop-color="#ffd2a0" stop-opacity="0.15"/><stop offset="1" stop-color="#ffd2a0" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>`;
  let body = `<rect width="${W}" height="${H}" fill="url(#sky)"/>`;
  for (let i = 0; i < 9; i++) {
    const x = r() * W;
    const y = 90 + r() * 330;
    body += `<ellipse cx="${f1(x)}" cy="${f1(y)}" rx="${f1(160 + r() * 260)}" ry="${f1(18 + r() * 26)}" fill="#fff3e4" opacity="${(0.25 + r() * 0.3).toFixed(2)}" filter="url(#soft)"/>`;
  }
  body += `<rect width="${W}" height="${horizon}" fill="url(#glow)"/><circle cx="960" cy="${horizon - 70}" r="44" fill="#fffaf0"/>`;
  body += `<rect y="${horizon}" width="${W}" height="${H - horizon}" fill="url(#sea)"/>`;
  body += `<rect y="${horizon}" width="${W}" height="${H - horizon}" fill="url(#glow)" opacity="0.5"/>`;
  // swell lines
  for (let i = 0; i < 120; i++) {
    const y = horizon + 6 + Math.pow(r(), 1.7) * (H - horizon);
    const x = r() * W;
    const w = 30 + (y - horizon) * 0.5 * r();
    body += `<rect x="${f1(x)}" y="${f1(y)}" width="${f1(w)}" height="${f1(1 + (y - horizon) / 220)}" fill="#c9d6ea" opacity="${(0.08 + r() * 0.14).toFixed(2)}"/>`;
  }
  // sun glitter path
  const highlights: { x: number; y: number; c: string; w: number }[] = [];
  for (let i = 0; i < 420; i++) {
    const t = Math.pow(r(), 1.3);
    const y = horizon + 4 + t * (H - horizon);
    const spread = 30 + t * 340;
    const x = 960 + (r() + r() + r() - 1.5) * spread * 0.9;
    const bright = (1 - t) * (0.5 + r() * 0.5);
    const w = 4 + t * 22 * r();
    body += `<ellipse cx="${f1(x)}" cy="${f1(y)}" rx="${f1(w)}" ry="${f1(1 + t * 2.2)}" fill="#fff6e2" opacity="${Math.min(1, 0.2 + bright).toFixed(2)}"/>`;
    if (bright > 0.62 && highlights.length < 22 && r() < 0.5) highlights.push({ x: Math.round(x), y: Math.round(y), c: "#fff1d6", w: bright });
  }
  // a small distant sail
  body += `<path d="M1418 548 L1430 508 L1436 548 Z" fill="#3a4a66"/><rect x="1408" y="548" width="34" height="4" fill="#3a4a66"/>`;
  highlights.unshift({ x: 960, y: horizon - 70, c: "#fffaf0", w: 1 });
  return { svg: svg(body, defs), highlights };
}

// ---------------------------------------------------------------- room (Droste plate)
function room() {
  const r = rng(51);
  const defs = `
  <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#14171d"/><stop offset="1" stop-color="#232832"/>
  </linearGradient>
  <radialGradient id="lampglow" cx="300" cy="560" r="700" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ffb46a" stop-opacity="0.42"/><stop offset="0.35" stop-color="#e98a4c" stop-opacity="0.14"/>
    <stop offset="1" stop-color="#e98a4c" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="screenspill" cx="960" cy="560" r="620" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#9cc0ff" stop-opacity="0.16"/><stop offset="1" stop-color="#9cc0ff" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="desk" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#4a3427"/><stop offset="0.08" stop-color="#3a281e"/><stop offset="1" stop-color="#140d09"/>
  </linearGradient>
  <radialGradient id="pool" cx="960" cy="800" r="520" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#b9d0ff" stop-opacity="0.2"/><stop offset="1" stop-color="#b9d0ff" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="warmpool" cx="320" cy="800" r="420" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#ffb46a" stop-opacity="0.35"/><stop offset="1" stop-color="#ffb46a" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="chassis" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a2d33"/><stop offset="0.03" stop-color="#121418"/><stop offset="1" stop-color="#0b0c0f"/>
  </linearGradient>
  <linearGradient id="spk" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#1b1d22"/><stop offset="0.5" stop-color="#23262c"/><stop offset="1" stop-color="#15171b"/>
  </linearGradient>
  <radialGradient id="cone"><stop offset="0" stop-color="#2f333a"/><stop offset="0.7" stop-color="#0d0e11"/><stop offset="1" stop-color="#2a2d33"/></radialGradient>
  <linearGradient id="print1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e2866a"/><stop offset="1" stop-color="#5a3a6e"/></linearGradient>
  <linearGradient id="print2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f6fb3"/><stop offset="1" stop-color="#f1dcc0"/></linearGradient>
  <radialGradient id="vig" cx="960" cy="540" r="1150" gradientUnits="userSpaceOnUse">
    <stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.55"/>
  </radialGradient>`;
  let body = `<rect width="${W}" height="${H}" fill="url(#wall)"/>`;
  // acoustic slats on the wall
  for (let x = 1260; x < 1880; x += 22) body += `<rect x="${x}" y="120" width="14" height="560" fill="#1a1e25" opacity="0.9"/><rect x="${x}" y="120" width="2" height="560" fill="#2b313b" opacity="0.6"/>`;
  // framed prints, left wall
  body += `<rect x="390" y="150" width="230" height="300" fill="#0d0f13"/><rect x="404" y="164" width="202" height="272" fill="#e9e4da"/><rect x="424" y="184" width="162" height="232" fill="url(#print1)"/>`;
  body += `<circle cx="505" cy="270" r="40" fill="#f6d2a2" opacity="0.85"/>`;
  body += `<rect x="650" y="210" width="160" height="200" fill="#0d0f13"/><rect x="662" y="222" width="136" height="176" fill="#e9e4da"/><rect x="678" y="238" width="104" height="144" fill="url(#print2)"/>`;
  body += `<rect width="${W}" height="${H}" fill="url(#lampglow)"/><rect width="${W}" height="${H}" fill="url(#screenspill)"/>`;
  // desk
  body += `<rect y="790" width="${W}" height="${H - 790}" fill="url(#desk)"/><rect y="788" width="${W}" height="3" fill="#6a4b38" opacity="0.8"/>`;
  body += `<rect y="790" width="${W}" height="${H - 790}" fill="url(#pool)"/><rect y="790" width="${W}" height="${H - 790}" fill="url(#warmpool)"/>`;
  // desk lamp (left)
  body += `<ellipse cx="300" cy="792" rx="70" ry="10" fill="#0b0c0f"/><rect x="292" y="600" width="9" height="190" fill="#0f1114" transform="rotate(-12 296 790)"/>`;
  body += `<rect x="250" y="560" width="9" height="120" fill="#0f1114" transform="rotate(38 254 620)"/>`;
  body += `<path d="M300 520 L400 520 L380 580 L320 580 Z" fill="#14161a" transform="rotate(-24 350 550)"/>`;
  body += `<ellipse cx="368" cy="592" rx="34" ry="8" fill="#ffe0b0" opacity="0.9" transform="rotate(-24 368 592)"/>`;
  // speakers
  for (const sx of [500, 1300]) {
    body += `<rect x="${sx}" y="560" width="120" height="228" rx="6" fill="url(#spk)"/>`;
    body += `<circle cx="${sx + 60}" cy="610" r="18" fill="url(#cone)"/><circle cx="${sx + 60}" cy="700" r="44" fill="url(#cone)"/><circle cx="${sx + 60}" cy="700" r="10" fill="#2f333a"/>`;
  }
  // monitor: chassis, screen hole (filled dark; recursion is drawn on top), stand
  body += `<path d="M928 690 L992 690 L1006 772 L914 772 Z" fill="#101215"/><rect x="840" y="770" width="240" height="18" rx="4" fill="#15171b"/><rect x="840" y="770" width="240" height="2" fill="#3a3e46"/>`;
  body += `<rect x="704" y="389" width="512" height="302" rx="8" fill="url(#chassis)"/><rect x="706" y="390" width="508" height="2" fill="#4a4f59" opacity="0.8"/>`;
  body += `<rect x="720" y="405" width="480" height="270" fill="#05070b"/>`;
  // keyboard + mug
  body += `<path d="M800 838 L1120 838 L1140 872 L780 872 Z" fill="#17191d"/><path d="M800 838 L1120 838 L1122 842 L798 842 Z" fill="#33363d"/>`;
  for (let i = 0; i < 3; i++) for (let j = 0; j < 18; j++) body += `<rect x="${806 + j * 17.5 + i * 3}" y="${846 + i * 8}" width="14" height="5" fill="#24272d"/>`;
  body += `<rect x="1196" y="806" width="52" height="62" rx="6" fill="#d8d2c6"/><path d="M1248 820 q 22 4 0 30" stroke="#d8d2c6" stroke-width="7" fill="none"/>`;
  // plant (right)
  body += `<path d="M1620 790 L1700 790 L1688 700 L1632 700 Z" fill="#2d2925"/>`;
  for (let i = 0; i < 9; i++) {
    const a = -1.2 + i * 0.3 + (r() - 0.5) * 0.1;
    const len = 120 + r() * 80;
    const x2 = 1660 + Math.sin(a) * len;
    const y2 = 700 - Math.cos(a) * len;
    body += `<path d="M1660 702 Q ${f1(1660 + Math.sin(a) * len * 0.4 - 20)} ${f1(700 - Math.cos(a) * len * 0.6)} ${f1(x2)} ${f1(y2)} Q ${f1(1660 + Math.sin(a) * len * 0.5 + 24)} ${f1(700 - Math.cos(a) * len * 0.5)} 1660 702 Z" fill="#1d3326" opacity="0.95"/>`;
  }
  body += `<rect width="${W}" height="${H}" fill="url(#vig)"/>`;
  return svg(body, defs);
}

writeFileSync(OUT + "room.svg", room());
writeFileSync(OUT + "ridge.svg", ridge());
writeFileSync(OUT + "dunes.svg", dunes());
const h = harbor();
writeFileSync(OUT + "harbor.svg", h.svg);
const s = sea();
writeFileSync(OUT + "sea.svg", s.svg);
writeFileSync(OUT + "highlights.json", JSON.stringify({ harbor: h.highlights, sea: s.highlights }, null, 1));
console.log("ok", h.highlights.length, s.highlights.length);
