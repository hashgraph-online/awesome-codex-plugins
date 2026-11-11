// World layout shared by the shader (as GLSL constants) and the animation (JS).
// Units: the mouse is about 1.2 long, grass blades are 2.5-6 tall.

export const W = {
  CS: 2.0,          // grass grid cell size
  NB: 6,            // blades per cell
  WL: -0.5,         // water level
  POND: [25.0, 0.3],
  PONDR: 6.3,
  HOUSE: [39.5, 0.0],
  HERO: { base: [0.0, 0.0], h: 5.6, ld: [1.0, 0.0], L: 3.0, w: 0.46 },
  LOG: { a: [18.7, 0.12], b: [31.3, -0.05], r: 0.46 },
  // x, z, capRadius, stemHeight, lean, variant
  mush: [
    // cluster 0: where the mouse is lost
    [8.2, -1.0, 0.56, 0.85, 0.10, 1],
    [12.9, 3.6, 0.42, 0.55, 0.0, 1],
    // cluster 1: the mushroom patch
    [15.2, -2.4, 1.10, 1.70, 0.25, 0],
    [16.9, -3.3, 0.72, 1.05, -0.12, 0],
    [18.1, -1.6, 0.90, 1.45, 0.15, 0],
    [13.9, -1.5, 0.52, 0.75, -0.08, 1],
    [16.4, 2.9, 0.34, 0.40, 0.05, 1],
    // cluster 3: around the house
    [37.9, 4.3, 0.82, 1.20, 0.18, 0],
    [43.2, 3.2, 0.60, 0.90, -0.10, 1],
    [36.6, -3.8, 0.70, 1.00, 0.10, 0],
  ],
  // x, z, radius, flatness(y scale)
  stones: [
    [13.4, -2.7, 0.75, 0.62],
    [12.5, -0.9, 0.46, 0.7],
    [6.9, 3.4, 0.5, 0.7],
    [17.2, -2.6, 0.95, 0.6],
    [15.6, -1.2, 0.42, 0.66],
    [33.4, 2.6, 0.85, 0.6],
    [33.9, -2.1, 0.52, 0.7],
    [34.6, 0.15, 0.50, 0.30],
    [35.8, -0.10, 0.46, 0.30],
    [36.9, 0.10, 0.44, 0.30],
  ],
  // clusters: [mushStart, mushEnd, stoneStart, stoneEnd]; cluster 2 is the pond (log, pads, reeds)
  clusters: [[0, 2, 0, 3], [2, 7, 3, 5], [0, 0, 0, 0], [7, 10, 5, 10]],
  // lily pads: x, z, radius
  pads: [
    [23.0, 2.6, 0.85], [26.9, 3.3, 0.65], [27.6, -2.4, 0.8], [23.4, -2.9, 0.6], [25.3, 1.7, 0.42], [21.4, 3.9, 0.7], [28.8, 4.4, 0.55],
  ],
  // reeds: x, z, height, lean x, lean z
  reeds: [
    [21.6, -4.9, 6.2, 0.5, 0.2], [22.5, -5.5, 7.0, -0.3, 0.4], [28.3, -5.2, 6.6, 0.4, -0.2],
    [29.6, -4.3, 5.8, -0.4, -0.3], [25.2, -5.9, 6.4, 0.2, -0.5], [30.3, -4.6, 5.2, 0.5, 0.1],
  ],
};

const sstep = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

export function terrain(x, z) {
  let h = 0.22 * Math.sin(0.21 * x + 1.3) * Math.sin(0.17 * z + 0.4) + 0.10 * Math.sin(0.53 * x + 0.7) * Math.cos(0.47 * z + 2.0);
  const dp = Math.hypot(x - W.POND[0], z - W.POND[1]);
  h -= 1.9 * (1.0 - sstep(W.PONDR - 2.6, W.PONDR + 0.4, dp));
  const dh = Math.hypot(x - W.HOUSE[0], z - W.HOUSE[1]);
  h += 0.30 * (1.0 - sstep(2.0, 7.5, dh));
  return h;
}

export function pathZ(x) { return 1.5 * (1.0 - sstep(9.0, 20.0, x)); }

// top of the log at parameter x (where the mouse walks)
export function logTopY() { return W.WL + 0.18 + W.LOG.r; }

const f = (v) => { const s = Number(v).toFixed(4); return s.includes('.') ? s : s + '.0'; };
const v2 = (a) => `vec2(${f(a[0])},${f(a[1])})`;
const v3 = (a) => `vec3(${f(a[0])},${f(a[1])},${f(a[2])})`;
const v4 = (a) => `vec4(${f(a[0])},${f(a[1])},${f(a[2])},${f(a[3])})`;

export function glslConsts() {
  const L = [];
  L.push(`const float CS = ${f(W.CS)};`);
  L.push(`#define NB ${W.NB}`);
  L.push(`const float WL = ${f(W.WL)};`);
  L.push(`const vec2 POND = ${v2(W.POND)};`);
  L.push(`const float PONDR = ${f(W.PONDR)};`);
  L.push(`const vec2 HOUSE2 = ${v2(W.HOUSE)};`);
  L.push(`const vec3 HOUSE = ${v3([W.HOUSE[0], terrain(W.HOUSE[0], W.HOUSE[1]) - 0.05, W.HOUSE[1]])};`);
  const hb = W.HERO;
  L.push(`const vec3 HERO_BASE = ${v3([hb.base[0], terrain(hb.base[0], hb.base[1]) - 0.1, hb.base[1]])};`);
  L.push(`const vec4 HERO_P = ${v4([hb.h, hb.L, hb.w, 0])};`);
  L.push(`const vec2 HERO_LD = ${v2(hb.ld)};`);
  const ly = W.WL + 0.18;
  L.push(`const vec3 LOG_A = ${v3([W.LOG.a[0], ly, W.LOG.a[1]])};`);
  L.push(`const vec3 LOG_B = ${v3([W.LOG.b[0], ly, W.LOG.b[1]])};`);
  L.push(`const float LOG_R = ${f(W.LOG.r)};`);
  // mushrooms: vec4(x, groundY, z, capR), vec4(stemH, lean, variant, 0)
  L.push(`#define NMUSH ${W.mush.length}`);
  L.push(`const vec4 MUSH_A[NMUSH] = vec4[](${W.mush.map(m => v4([m[0], terrain(m[0], m[1]) - 0.06, m[1], m[2]])).join(',')});`);
  L.push(`const vec4 MUSH_B[NMUSH] = vec4[](${W.mush.map(m => v4([m[3], m[4], m[5], 0])).join(',')});`);
  L.push(`#define NSTONE ${W.stones.length}`);
  L.push(`const vec4 STONE_A[NSTONE] = vec4[](${W.stones.map(s => v4([s[0], terrain(s[0], s[1]) + s[2] * s[3] * 0.35, s[1], s[2]])).join(',')});`);
  L.push(`const float STONE_F[NSTONE] = float[](${W.stones.map(s => f(s[3])).join(',')});`);
  L.push(`#define NPAD ${W.pads.length}`);
  L.push(`const vec3 PADS[NPAD] = vec3[](${W.pads.map(v3).join(',')});`);
  L.push(`#define NREED ${W.reeds.length}`);
  L.push(`const vec4 REED_A[NREED] = vec4[](${W.reeds.map(r => v4([r[0], r[1], r[2], 0])).join(',')});`);
  L.push(`const vec2 REED_B[NREED] = vec2[](${W.reeds.map(r => v2([r[3], r[4]])).join(',')});`);
  // cluster bounding boxes (x0, z0, x1, z1) and heights
  const boxes = W.clusters.map((c, ci) => {
    let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9, y1 = 0;
    const grow = (x, z, r, y) => { x0 = Math.min(x0, x - r); z0 = Math.min(z0, z - r); x1 = Math.max(x1, x + r); z1 = Math.max(z1, z + r); y1 = Math.max(y1, y); };
    for (let i = c[0]; i < c[1]; i++) { const m = W.mush[i]; grow(m[0], m[1], m[2] + Math.abs(m[4]) + 0.2, terrain(m[0], m[1]) + m[3] + m[2] + 0.3); }
    for (let i = c[2]; i < c[3]; i++) { const st = W.stones[i]; grow(st[0], st[1], st[2] * 1.25, terrain(st[0], st[1]) + st[2] * 1.3); }
    if (ci === 2) {
      grow(W.LOG.a[0], W.LOG.a[1], W.LOG.r + 1.5, W.WL + 2.2); grow(W.LOG.b[0], W.LOG.b[1], W.LOG.r + 1.5, W.WL + 2.2);
      for (const p of W.pads) grow(p[0], p[1], p[2] + 0.1, W.WL + 0.2);
      for (const r of W.reeds) { grow(r[0], r[1], 0.5, 0); grow(r[0] + r[3], r[1] + r[4], 0.6, W.WL + r[2] + 0.4); }
    }
    return [x0, z0, x1, z1, y1];
  });
  L.push(`#define NCL ${W.clusters.length}`);
  L.push(`const vec4 CL_BOX[NCL] = vec4[](${boxes.map(b => v4(b)).join(',')});`);
  L.push(`const float CL_Y[NCL] = float[](${boxes.map(b => f(b[4])).join(',')});`);
  L.push(`const ivec4 CL_RANGE[NCL] = ivec4[](${W.clusters.map(c => `ivec4(${c.join(',')})`).join(',')});`);
  return L.join('\n');
}

export const TERRAIN_GLSL = `
float terrain(vec2 p){
  float h = 0.22*sin(0.21*p.x+1.3)*sin(0.17*p.y+0.4) + 0.10*sin(0.53*p.x+0.7)*cos(0.47*p.y+2.0);
  float dp = length(p-POND);
  h -= 1.9*(1.0-smoothstep(PONDR-2.6, PONDR+0.4, dp));
  float dh = length(p-HOUSE2);
  h += 0.30*(1.0-smoothstep(2.0,7.5,dh));
  return h;
}
float pathZ(float x){ return 1.5*(1.0-smoothstep(9.0,20.0,x)); }
`;
