// "The Smallest Star" path tracer. Every surface below is math: analytic curved grass blades
// (one quadratic per blade, walked through a grid), signed distance fields for the characters
// and props, an analytic water plane and a procedural night sky. No meshes, no textures.
import { glslConsts, TERRAIN_GLSL } from './world.js';

export const VS = `#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

export function ptFS(q) {
  return `#version 300 es
precision highp float;
precision highp int;
#define PI 3.14159265359
#define PRIMARY_STEPS ${q.primary}
#define SHADOW_STEPS ${q.shadow}
#define BOUNCE_STEPS ${q.bounce}
#define MAXSTEPS ${Math.max(q.primary, q.bounce)}
#define MAXC ${q.cells}
#define MAXCB ${q.cellsBounce}
#define MAXCS ${q.cellsShadow}
#define BOUNCES ${q.bounces}
const float TMAX = 230.0;

uniform vec2 uRes;
uniform int uPass;
uniform int uSeed;
uniform float uTime;
uniform float uSlice;
uniform vec3 uCamPos, uCamR, uCamU, uCamF;
uniform float uTanFov, uAperture, uFocus;
uniform vec3 uMoonDir, uMoonCol;
uniform float uSkyGain, uSkyVis, uFogGain, uStarGain, uMoonVis;
uniform vec3 uFfPos; uniform mat3 uFfRot; uniform float uFfScale;
uniform float uFfGlow; uniform vec3 uFfCol; uniform vec4 uFfPose; uniform float uFfEmi; uniform vec3 uFfLight;
uniform vec3 uMsPos; uniform mat3 uMsRot; uniform float uMsScale; uniform vec4 uMsA; uniform vec4 uMsB;
uniform float uWin, uWind, uFog, uGlowFog, uClay, uFfVis, uMsVis, uCatch, uFade0, uSmoke;
uniform vec4 uClrA, uClrP, uClrB, uClrQ;
uniform vec3 uFillDir, uFillCol;
uniform float uSpike;

layout(location=0) out vec4 oRad;
layout(location=1) out vec4 oEmi;
layout(location=2) out vec4 oAlb;
layout(location=3) out vec4 oNrm;

${glslConsts()}

const vec3 WIN_DIR = vec3(-0.62, 0.0, 0.7846);
const vec3 WIN_C = HOUSE + vec3(-0.62*1.50, 2.05, 0.7846*1.50);
const vec3 WINL = HOUSE + vec3(-0.62*2.05, 2.05, 0.7846*2.05);
const vec3 WIN_COL = vec3(1.0, 0.56, 0.20);
const vec3 TRANS_TINT = vec3(0.85, 1.0, 0.45);
const vec3 GRASS_T = vec3(0.14, 0.27, 0.06);
const vec3 WATER_COL = vec3(0.010, 0.030, 0.045);
const float MOON_COSMAX = 0.9990;
const float FF_LR = 0.10;
const float GY0 = -0.9;
const float GY1 = 8.3;

// ---------------------------------------------------------------- random
uint rs;
uint pcg(){ uint s = rs; rs = rs*747796405u + 2891336453u; uint w = ((s >> ((s >> 28u) + 4u)) ^ s)*277803737u; return (w >> 22u) ^ w; }
float rnd(){ return float(pcg() >> 8u)*(1.0/16777216.0); }
vec2 rnd2(){ float a = rnd(); float b = rnd(); return vec2(a, b); }
uint hashu(uint x){ x ^= x >> 16u; x *= 0x7feb352du; x ^= x >> 15u; x *= 0x846ca68bu; x ^= x >> 16u; return x; }
uint hash2u(ivec2 c, uint k){ return hashu(uint(c.x)*0x9E3779B1u + hashu(uint(c.y)*0x85EBCA77u + k*0xC2B2AE3Du)); }
uint hash3u(ivec3 c){ return hashu(uint(c.x)*0x9E3779B1u + hashu(uint(c.y)*0x85EBCA77u + hashu(uint(c.z)*0xC2B2AE3Du))); }
float u2f(uint h){ return float(h >> 8u)*(1.0/16777216.0); }
float tent(float u){ return u < 0.5 ? sqrt(2.0*u) - 1.0 : 1.0 - sqrt(2.0 - 2.0*u); }
vec2 disk(vec2 u){ float r = sqrt(u.x); float a = 6.2831853*u.y; return r*vec2(cos(a), sin(a)); }
float lum(vec3 c){ return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p); f = f*f*(3.0 - 2.0*f); ivec2 c = ivec2(i);
  float a = u2f(hash2u(c, 3u)), b = u2f(hash2u(c + ivec2(1,0), 3u));
  float cc = u2f(hash2u(c + ivec2(0,1), 3u)), d = u2f(hash2u(c + ivec2(1,1), 3u));
  return mix(mix(a, b, f.x), mix(cc, d, f.x), f.y);
}
float vnoise3(vec3 p){
  vec3 i = floor(p), f = fract(p); f = f*f*(3.0 - 2.0*f); ivec3 c = ivec3(i);
  float n000 = u2f(hash3u(c)), n100 = u2f(hash3u(c + ivec3(1,0,0)));
  float n010 = u2f(hash3u(c + ivec3(0,1,0))), n110 = u2f(hash3u(c + ivec3(1,1,0)));
  float n001 = u2f(hash3u(c + ivec3(0,0,1))), n101 = u2f(hash3u(c + ivec3(1,0,1)));
  float n011 = u2f(hash3u(c + ivec3(0,1,1))), n111 = u2f(hash3u(c + ivec3(1,1,1)));
  return mix(mix(mix(n000, n100, f.x), mix(n010, n110, f.x), f.y), mix(mix(n001, n101, f.x), mix(n011, n111, f.x), f.y), f.z);
}
mat2 rot2(float a){ float c = cos(a), s = sin(a); return mat2(c, s, -s, c); }

void onb(vec3 n, out vec3 t, out vec3 b){
  float s = n.z >= 0.0 ? 1.0 : -1.0; float a = -1.0/(s + n.z); float c = n.x*n.y*a;
  t = vec3(1.0 + s*n.x*n.x*a, s*c, -s*n.x); b = vec3(c, s + n.y*n.y*a, -n.y);
}
vec3 cosHemi(vec3 n){
  vec2 u = rnd2(); float r = sqrt(u.x); float a = 6.2831853*u.y; vec3 t, b; onb(n, t, b);
  return normalize(t*(r*cos(a)) + b*(r*sin(a)) + n*sqrt(max(1.0 - u.x, 0.0)));
}
vec3 coneSample(vec3 d, float cosMax, vec2 u){
  float c = 1.0 - u.x*(1.0 - cosMax); float s = sqrt(max(1.0 - c*c, 0.0)); float a = 6.2831853*u.y; vec3 t, b; onb(d, t, b);
  return normalize(t*(s*cos(a)) + b*(s*sin(a)) + d*c);
}

// ---------------------------------------------------------------- distance fields
float sdSphere(vec3 p, float r){ return length(p) - r; }
float sdEllipsoid(vec3 p, vec3 r){ float k0 = length(p/r); float k1 = length(p/(r*r)); return k0*(k0 - 1.0)/max(k1, 1e-6); }
float sdCapsule(vec3 p, vec3 a, vec3 b, float r){ vec3 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba)/dot(ba, ba), 0.0, 1.0); return length(pa - ba*h) - r; }
float sdRoundCone(vec3 p, vec3 a, vec3 b, float r1, float r2){
  vec3 ba = b - a; float l2 = dot(ba, ba); float rr = r1 - r2; float a2 = l2 - rr*rr; float il2 = 1.0/l2;
  vec3 pa = p - a; float y = dot(pa, ba); float z = y - l2; vec3 xv = pa*l2 - ba*y; float x2 = dot(xv, xv);
  float y2 = y*y*l2; float z2 = z*z*l2; float k = sign(rr)*rr*rr*x2;
  if (sign(z)*a2*z2 > k) return sqrt(x2 + z2)*il2 - r2;
  if (sign(y)*a2*y2 < k) return sqrt(x2 + y2)*il2 - r1;
  return (sqrt(x2*a2*il2) + y*rr)*il2 - r1;
}
float sdTorus(vec3 p, vec2 t){ vec2 q = vec2(length(p.xz) - t.x, p.y); return length(q) - t.y; }
float sdRoundBox(vec3 p, vec3 b, float r){ vec3 q = abs(p) - b + r; return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r; }
float sdCylX(vec3 p, float h, float r){ vec2 d = abs(vec2(length(p.yz), p.x)) - vec2(r, h); return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)); }
float sdCylY(vec3 p, float h, float r){ vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h); return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)); }
float smin(float a, float b, float k){ float h = max(k - abs(a - b), 0.0)/k; return min(a, b) - h*h*k*0.25; }
float smax(float a, float b, float k){ return -smin(-a, -b, k); }
vec2 U(vec2 a, vec2 b){ return a.x < b.x ? a : b; }

${TERRAIN_GLSL}

float gWingT;

// ---------------------------------------------------------------- the mouse
vec2 mapMouse(vec3 pw){
  vec3 p = (transpose(uMsRot)*(pw - uMsPos))/uMsScale;
  float bd = length(p - vec3(-0.25, 0.5, 0.0)) - 1.75;
  if (bd > 0.35) return vec2(bd*uMsScale, 20.0);
  float sq = uMsA.w; float sxz = inversesqrt(sq);
  vec3 q = vec3(p.x/sxz, p.y/sq, p.z/sxz);
  float ds = min(sq, sxz);
  float d = sdEllipsoid(q - vec3(-0.08, 0.42, 0.0), vec3(0.50, 0.41, 0.42));
  d = smin(d, sdEllipsoid(q - vec3(-0.30, 0.37, 0.0), vec3(0.35, 0.36, 0.45)), 0.14);
  vec3 hl = q - vec3(0.24, 0.60, 0.0);
  hl.xz = rot2(-uMsA.y)*hl.xz; hl.xy = rot2(-uMsA.x)*hl.xy;
  float dh = sdSphere(hl - vec3(0.17, 0.10, 0.0), 0.30);
  dh = smin(dh, sdRoundCone(hl, vec3(0.30, 0.05, 0.0), vec3(0.53, 0.01, 0.0), 0.17, 0.065), 0.10);
  d = smin(d, dh, 0.09);
  vec2 r = vec2(d, 20.0);
  // ears
  vec3 e = hl - vec3(0.10, 0.33, 0.0); e.z = abs(e.z) - 0.21;
  e.yz = rot2(-0.42)*e.yz;
  e.xy = rot2(-(0.22 + 1.0*uMsA.z))*e.xy;
  e.y -= 0.15;
  float de = sdEllipsoid(e, vec3(0.05, 0.215, 0.195));
  de = smax(de, -sdEllipsoid(e - vec3(0.06, 0.0, 0.0), vec3(0.045, 0.16, 0.145)), 0.03);
  r = vec2(smin(r.x, de, 0.05), de < r.x ? 21.0 : r.y);
  // eyes, nose
  vec3 ey = hl; ey.z = abs(ey.z);
  r = U(r, vec2(sdSphere(ey - vec3(0.385, 0.175, 0.170), 0.062), 22.0));
  r = U(r, vec2(sdSphere(hl - vec3(0.59, 0.015, 0.0), 0.052), 23.0));
  // paws
  vec3 pf = q; pf.z = abs(pf.z);
  float dp = min(sdEllipsoid(pf - vec3(0.24, 0.055, 0.19), vec3(0.11, 0.06, 0.075)), sdEllipsoid(pf - vec3(-0.22, 0.05, 0.31), vec3(0.17, 0.06, 0.085)));
  r = U(r, vec2(dp, 24.0));
  // tail
  float ph = uMsB.x;
  vec3 t0 = vec3(-0.50, 0.22, 0.0), t1 = vec3(-0.86, 0.09, 0.10*sin(ph)), t2 = vec3(-1.20, 0.07, 0.22*sin(ph + 0.9));
  vec3 t3 = vec3(-1.50, 0.13 + 0.3*uMsB.y, 0.20*sin(ph + 1.8)), t4 = vec3(-1.72, 0.30 + 0.8*uMsB.y, 0.08*sin(ph + 2.7));
  float dt = sdCapsule(q, t0, t1, 0.050); dt = smin(dt, sdCapsule(q, t1, t2, 0.042), 0.03);
  dt = smin(dt, sdCapsule(q, t2, t3, 0.033), 0.03); dt = smin(dt, sdCapsule(q, t3, t4, 0.024), 0.03);
  r = vec2(smin(r.x, dt, 0.06), dt < r.x ? 25.0 : r.y);
  // scarf
  vec3 sc = q - vec3(0.17, 0.50, 0.0); sc.xy = rot2(0.85)*sc.xy;
  float dsc = sdTorus(sc, vec2(0.315, 0.078));
  dsc = min(dsc, sdSphere(q - vec3(0.33, 0.36, 0.22), 0.095));
  dsc = min(dsc, sdCapsule(q, vec3(0.33, 0.36, 0.22), vec3(0.27, 0.12, 0.33), 0.062));
  r = U(r, vec2(dsc, 26.0));
  r.x *= ds*uMsScale*0.9;
  return r;
}

// ---------------------------------------------------------------- the firefly
vec2 mapFirefly(vec3 pw){
  vec3 p = (transpose(uFfRot)*(pw - uFfPos))/uFfScale;
  float bd = length(p) - 0.60;
  if (bd > 0.2) return vec2(bd*uFfScale, 30.0);
  vec2 r = vec2(sdCapsule(p, vec3(-0.04, 0.0, 0.0), vec3(0.08, 0.0, 0.0), 0.066), 30.0);
  r = U(r, vec2(sdEllipsoid(p - vec3(0.10, 0.038, 0.0), vec3(0.09, 0.04, 0.092)), 31.0));
  vec3 hl = p - vec3(0.13, 0.0, 0.0); hl.xy = rot2(-uFfPose.w)*hl.xy;
  r = U(r, vec2(sdSphere(hl - vec3(0.065, -0.004, 0.0), 0.064), 30.0));
  vec3 e = hl; e.z = abs(e.z);
  r = U(r, vec2(sdSphere(e - vec3(0.10, 0.016, 0.044), 0.038), 32.0));
  float dr = uFfPose.z;
  vec3 a0 = vec3(0.10, 0.05, 0.022), a1 = vec3(0.17, 0.125 - 0.07*dr, 0.06), a2 = vec3(0.25, 0.145 - 0.19*dr, 0.105);
  float da = min(sdCapsule(e, a0, a1, 0.0075), sdCapsule(e, a1, a2, 0.0065)); da = min(da, sdSphere(e - a2, 0.015));
  r = U(r, vec2(da, 35.0));
  vec3 b = p - vec3(-0.165, -0.012, 0.0);
  float dl = sdEllipsoid(b, vec3(0.14, 0.085, 0.09)) + 0.004*sin(b.x*75.0);
  r = U(r, vec2(dl, 33.0));
  vec3 w = p; w.z = abs(w.z);
  float eo = uFfPose.y;
  vec3 el = w - vec3(0.045, 0.062, 0.02);
  el.xz = rot2(0.06 + 0.55*eo)*el.xz; el.xy = rot2(0.06 + 0.85*eo)*el.xy;
  r = U(r, vec2(sdEllipsoid(el - vec3(-0.15, 0.0, 0.035), vec3(0.16, 0.02, 0.062)), 36.0));
  if (uFfPose.x > 0.01) {
    float fl = uFfPose.x*(0.25 + 0.95*sin(gWingT*230.0));
    vec3 wg = w - vec3(0.03, 0.07, 0.03);
    wg.yz = rot2(fl)*wg.yz;
    wg -= vec3(-0.05, 0.0, 0.175);
    float dw = max((length(vec2(wg.x*1.9, wg.z)) - 0.17)*0.5, abs(wg.y) - 0.0035);
    r = U(r, vec2(dw, 34.0));
  }
  float dleg = sdCapsule(w, vec3(0.06, -0.04, 0.04), vec3(0.09, -0.115, 0.085), 0.007);
  dleg = min(dleg, sdCapsule(w, vec3(0.01, -0.04, 0.045), vec3(0.0, -0.118, 0.095), 0.007));
  dleg = min(dleg, sdCapsule(w, vec3(-0.04, -0.04, 0.04), vec3(-0.08, -0.115, 0.085), 0.007));
  r = U(r, vec2(dleg, 35.0));
  r.x *= uFfScale*0.9;
  return r;
}

// ---------------------------------------------------------------- props
vec2 mapMush(vec3 p, float capR, float stemH, float lean){
  vec3 q = p; float u = clamp(q.y/stemH, 0.0, 1.0); q.x -= lean*u*u;
  float dS = sdRoundCone(q, vec3(0.0), vec3(0.0, stemH, 0.0), capR*0.27, capR*0.19);
  vec3 c = p - vec3(lean, stemH - capR*0.05, 0.0);
  float dome = sdEllipsoid(c, vec3(capR, capR*0.74, capR));
  float dC = smax(dome, -c.y, capR*0.10);
  dC = smax(dC, -sdEllipsoid(c - vec3(0.0, -capR*0.06, 0.0), vec3(capR*0.84, capR*0.22, capR*0.84)), capR*0.06);
  return U(vec2(dS*0.9, 3.0), vec2(dC, 4.0));
}

float boxD(vec3 p, vec4 b, float ymax){ vec2 q = max(max(b.xy - p.xz, p.xz - b.zw), 0.0); return length(vec3(q, max(p.y - ymax, 0.0))); }

vec2 mapProps(vec3 p){
  vec2 r = vec2(1e5, 0.0);
  for (int c = 0; c < NCL; c++) {
    float db = boxD(p, CL_BOX[c], CL_Y[c]);
    if (db > 0.5) { r.x = min(r.x, db); continue; }
    ivec4 rg = CL_RANGE[c];
    for (int i = rg.x; i < rg.y; i++) {
      vec4 a = MUSH_A[i]; vec4 b = MUSH_B[i]; vec3 q = p - a.xyz;
      float bs = length(q - vec3(0.0, b.x*0.6, 0.0)) - (a.w + b.x*0.75 + 0.3);
      if (bs > 0.4) r.x = min(r.x, bs); else { vec2 m = mapMush(q, a.w, b.x, b.y); if (m.x < r.x) r = m; }
    }
    for (int i = rg.z; i < rg.w; i++) {
      vec4 a = STONE_A[i]; vec3 q = p - a.xyz;
      float bs = length(q) - a.w*1.2;
      if (bs > 0.4) r.x = min(r.x, bs); else {
        float d = sdEllipsoid(q, vec3(a.w, a.w*STONE_F[i], a.w*0.92));
        d += 0.10*a.w*(vnoise3(q*1.9/a.w + float(i)*7.3) - 0.5);
        d *= 0.8;
        if (d < r.x) r = vec2(d, 2.0);
      }
    }
    if (c == 2) {
      float bl = sdCapsule(p, LOG_A, LOG_B, LOG_R + 1.4);
      if (bl > 0.4) r.x = min(r.x, bl); else {
        vec3 pa = p - LOG_A, ba = LOG_B - LOG_A; float h = clamp(dot(pa, ba)/dot(ba, ba), 0.0, 1.0); vec3 cc = pa - ba*h;
        float ang = atan(cc.y, cc.z);
        float d = length(cc) - LOG_R - 0.018*sin(ang*14.0 + h*9.0) - 0.012*sin(h*60.0 + ang*3.0);
        vec3 s0 = mix(LOG_A, LOG_B, 0.30) + vec3(0.0, 0.1, 0.36), s1 = mix(LOG_A, LOG_B, 0.33) + vec3(0.2, 0.8, 1.25);
        d = smin(d, sdRoundCone(p, s0, s1, 0.13, 0.07), 0.12);
        d *= 0.8;
        if (d < r.x) r = vec2(d, 6.0);
      }
      for (int i = 0; i < NPAD; i++) {
        vec3 a = PADS[i]; vec3 q = p - vec3(a.x, WL + 0.03, a.y);
        float bs = length(q) - a.z - 0.1;
        if (bs > 0.4) r.x = min(r.x, bs); else {
          q.xz = rot2(float(i)*1.7)*q.xz;
          float d = max(length(q.xz) - a.z, abs(q.y) - 0.02) - 0.015;
          float dn = max(-q.x, abs(q.z) - 0.16*q.x);
          d = max(d, -dn);
          if (d < r.x) r = vec2(d, 7.0);
        }
      }
      for (int i = 0; i < NREED; i++) {
        vec4 a = REED_A[i]; vec2 l = REED_B[i];
        float sw = 0.12*uWind*sin(uTime*1.3 + float(i)*2.1);
        vec3 b0 = vec3(a.x, WL - 0.6, a.y); vec3 b1 = b0 + vec3(l.x + sw, a.z, l.y + sw*0.6);
        float bs = sdCapsule(p, b0, b1, 0.4);
        if (bs > 0.4) r.x = min(r.x, bs); else {
          float d = sdCapsule(p, b0, b1, 0.055); if (d < r.x) r = vec2(d, 8.0);
          float dh = sdCapsule(p, mix(b0, b1, 0.80), mix(b0, b1, 0.94), 0.16); if (dh < r.x) r = vec2(dh, 9.0);
        }
      }
    }
  }
  return r;
}

vec2 mapHouse(vec3 pw){
  vec3 p = pw - HOUSE;
  float bd = length(p - vec3(0.0, 3.6, 0.0)) - 5.5;
  if (bd > 0.4) return vec2(bd, 10.0);
  float ds = sdRoundCone(p, vec3(0.0, 0.2, 0.0), vec3(0.0, 3.1, 0.0), 1.75, 1.42);
  ds = smin(ds, sdEllipsoid(p, vec3(2.1, 0.5, 2.1)), 0.5);
  vec2 r = vec2(ds, 10.0);
  vec3 c = p - vec3(0.0, 2.85, 0.0);
  float wob = 0.07*sin(atan(c.z, c.x)*7.0 + 1.0);
  float dome = sdEllipsoid(c, vec3(3.7 + wob, 2.55, 3.7 + wob));
  float dc = smax(dome, -(c.y - 0.05), 0.25);
  dc = smax(dc, -sdEllipsoid(c - vec3(0.0, -0.15, 0.0), vec3(3.2, 0.7, 3.2)), 0.15);
  r = U(r, vec2(dc, 11.0));
  // door, facing -x
  vec3 dp = p - vec3(-1.66, 0.92, 0.0);
  float dfr = min(sdRoundBox(dp - vec3(0.02, -0.06, 0.0), vec3(0.10, 0.68, 0.62), 0.05), sdCylX(dp - vec3(0.02, 0.60, 0.0), 0.10, 0.62));
  r = U(r, vec2(dfr, 13.0));
  float ddo = min(sdRoundBox(dp - vec3(-0.07, -0.04, 0.0), vec3(0.08, 0.62, 0.50), 0.04), sdCylX(dp - vec3(-0.07, 0.58, 0.0), 0.08, 0.50));
  r = U(r, vec2(ddo, 12.0));
  r = U(r, vec2(sdSphere(dp - vec3(-0.20, -0.05, 0.33), 0.065), 17.0));
  r = U(r, vec2(sdEllipsoid(p - vec3(-2.45, 0.10, 0.0), vec3(0.62, 0.16, 0.78)), 18.0));
  // round window
  vec3 wq = p - (WIN_C - HOUSE);
  float wu = dot(wq, WIN_DIR); vec3 wt = wq - WIN_DIR*wu; float wr = length(wt);
  r = U(r, vec2(length(vec2(wr - 0.46, wu - 0.03)) - 0.085, 15.0));
  r = U(r, vec2(max(wr - 0.46, abs(wu + 0.02) - 0.06), 14.0));
  vec3 wside = normalize(cross(WIN_DIR, vec3(0.0, 1.0, 0.0)));
  float bars = min(length(vec2(wt.y, wu - 0.05)), length(vec2(dot(wt, wside), wu - 0.05))) - 0.04;
  r = U(r, vec2(max(bars, wr - 0.46), 15.0));
  // chimney and clay smoke
  vec3 ch = p - vec3(1.25, 4.72, -0.85);
  float dch = sdCylY(ch, 0.50, 0.26) - 0.03;
  dch = min(dch, sdTorus(ch - vec3(0.0, 0.5, 0.0), vec2(0.28, 0.07)));
  r = U(r, vec2(dch, 16.0));
  if (uSmoke > 0.01) {
    for (int i = 0; i < 4; i++) {
      float k = fract(uTime*0.11 + float(i)*0.25);
      vec3 sp = vec3(1.25 + 1.7*k*k + 0.16*sin(uTime*0.7 + float(i)*2.0), 5.5 + 2.6*k, -0.85 - 0.9*k*k);
      float sr = (0.15 + 0.30*k)*smoothstep(0.0, 0.12, k)*(1.0 - smoothstep(0.6, 1.0, k))*uSmoke;
      if (sr > 0.01) r = U(r, vec2(sdSphere(p - sp, sr), 19.0));
    }
  }
  return r;
}

vec2 map(vec3 p, bool skipFf){
  vec2 r = mapProps(p);
  vec2 q = mapHouse(p); if (q.x < r.x) r = q;
  if (uMsVis > 0.5) { q = mapMouse(p); if (q.x < r.x) r = q; }
  if (uFfVis > 0.5 && !skipFf) { q = mapFirefly(p); if (q.x < r.x) r = q; }
  return r;
}

vec3 calcNormal(vec3 p, float t, bool sf){
  vec2 e = vec2(1.0, -1.0)*(0.0008 + 0.0006*t);
  return normalize(e.xyy*map(p + e.xyy, sf).x + e.yyx*map(p + e.yyx, sf).x + e.yxy*map(p + e.yxy, sf).x + e.xxx*map(p + e.xxx, sf).x);
}

void rayBox(vec3 ro, vec3 ird, vec3 bmin, vec3 bmax, float tmax, inout float t0, inout float t1){
  vec3 ta = (bmin - ro)*ird, tb = (bmax - ro)*ird; vec3 tn = min(ta, tb), tf = max(ta, tb);
  float a = max(max(tn.x, tn.y), max(tn.z, 0.0)), b = min(min(tf.x, tf.y), min(tf.z, tmax));
  if (a < b) { t0 = min(t0, a); t1 = max(t1, b); }
}
void raySph(vec3 ro, vec3 rd, vec3 c, float r, float tmax, inout float t0, inout float t1){
  vec3 oc = ro - c; float b = dot(oc, rd); float h = b*b - dot(oc, oc) + r*r;
  if (h < 0.0) return;
  h = sqrt(h); float a = max(-b - h, 0.0), e = min(-b + h, tmax);
  if (a < e) { t0 = min(t0, a); t1 = max(t1, e); }
}

// march the objects only inside the hull of the bounding volumes this ray crosses
float march(vec3 ro, vec3 rd, float tmax, int steps, bool skipFf, out float id){
  id = 0.0;
  float t0 = 1e9, t1 = -1.0;
  vec3 ird = 1.0/mix(rd, vec3(1e-8), lessThan(abs(rd), vec3(1e-8)));
  for (int c = 0; c < NCL; c++) { vec4 bx = CL_BOX[c]; rayBox(ro, ird, vec3(bx.x, -1.7, bx.y), vec3(bx.z, CL_Y[c], bx.w), tmax, t0, t1); }
  raySph(ro, rd, HOUSE + vec3(0.0, 3.6, 0.0), 5.5, tmax, t0, t1);
  if (uMsVis > 0.5) raySph(ro, rd, uMsPos + uMsRot*vec3(-0.25, 0.5, 0.0)*uMsScale, 1.8*uMsScale, tmax, t0, t1);
  if (uFfVis > 0.5 && !skipFf) raySph(ro, rd, uFfPos, 0.64*uFfScale, tmax, t0, t1);
  if (t1 < 0.0) return -1.0;
  float t = t0; float dl = 1e5;
  for (int i = 0; i < MAXSTEPS; i++) {
    if (i >= steps) break;
    vec2 m = map(ro + rd*t, skipFf); dl = m.x;
    if (m.x < 0.0006*(1.0 + t*1.5)) { id = m.y; return t; }
    t += m.x;
    if (t > t1) return -1.0;
  }
  if (dl < 0.004*t + 0.004) { id = map(ro + rd*t, skipFf).y; return t; }
  return -1.0;
}

// the ground is a smooth heightfield: step by height over (local slope bound - ray slope)
float terrainTrace(vec3 ro, vec3 rd, float tmax){
  float hl = length(rd.xz); float t = 0.0;
  if (ro.y > 0.66) { if (rd.y >= 0.0) return -1.0; t = (ro.y - 0.66)/(-rd.y); if (t > tmax) return -1.0; }
  for (int i = 0; i < 44; i++) {
    vec3 p = ro + rd*t;
    float h = p.y - terrain(p.xz);
    if (h < 0.002 + 0.0012*t) return t;
    float dpo = length(p.xz - POND) - (PONDR + 1.2);
    float k = dpo < 0.0 ? 1.12 : 0.23;
    float den = k*hl - rd.y;
    if (den <= 1e-4) return -1.0;
    float st = h/den;
    if (dpo > 0.0) st = min(st, dpo/max(hl, 1e-4) + 0.05);
    t += st;
    if (t > tmax) return -1.0;
  }
  return -1.0;
}
vec3 terrainN(vec2 p){
  vec2 e = vec2(0.02, 0.0);
  return normalize(vec3(terrain(p - e.xy) - terrain(p + e.xy), 2.0*e.x, terrain(p - e.yx) - terrain(p + e.yx)));
}

// ---------------------------------------------------------------- grass: analytic curved blades in a grid
struct Blade { vec3 base; float h; vec2 ld; float L; float w; float hue; };
struct CellInfo { float m; float cy; float top; bool nearPath; bool nearClr; float ws; float wc; uint hc; vec2 c0; };

bool cellSetup(ivec2 cell, out CellInfo ci){
  vec2 p = (vec2(cell) + 0.5)*CS;
  float m = min(0.93 + 0.31*sin(p.x*0.19 + 0.7)*sin(p.y*0.23 + 1.9) + 0.12*sin(p.x*0.53 + p.y*0.41), 1.25);
  float along = smoothstep(7.5, 10.0, p.x)*(1.0 - smoothstep(37.5, 40.0, p.x));
  float dpz = abs(p.y - pathZ(p.x));
  m *= mix(1.0, 0.25 + 0.75*smoothstep(0.4, 3.4, dpz), along);
  m *= smoothstep(PONDR - 0.3, PONDR + 2.4, length(p - POND));
  m *= smoothstep(3.4, 7.0, length(p - HOUSE2));
  m *= 1.0 - smoothstep(62.0, 86.0, length(p - vec2(18.0, 0.0)));
  m *= 1.0 - smoothstep(uFade0, uFade0 + 22.0, length(p - uCamPos.xz));
  m *= mix(0.5, 1.0, smoothstep(0.8, 3.2, length(p - HERO_BASE.xz)));
  ci.m = m;
  if (m <= 0.1) return false;
  ci.cy = terrain(p); ci.top = ci.cy + 6.0*m + 0.05;
  ci.nearPath = along > 0.5 && dpz < 2.6;
  vec2 pa = p - uClrA.xy, ba = uClrA.zw - uClrA.xy;
  float hc = clamp(dot(pa, ba)/max(dot(ba, ba), 1e-4), 0.0, 1.0);
  ci.nearClr = length(pa - ba*hc) < uClrP.x + 1.5;
  vec2 pb = p - uClrB.xy, bb = uClrB.zw - uClrB.xy;
  float hb = clamp(dot(pb, bb)/max(dot(bb, bb), 1e-4), 0.0, 1.0);
  ci.nearClr = ci.nearClr || length(pb - bb*hb) < uClrQ.x + 1.5;
  float ph = uTime*1.7 + p.x*0.31 + p.y*0.23; ci.ws = sin(ph); ci.wc = cos(ph);
  ci.hc = hash2u(cell, 1u); ci.c0 = vec2(cell)*CS;
  return true;
}

bool mkBlade(CellInfo ci, int i, out Blade B){
  uint h1 = hashu(ci.hc + uint(i)*0x9e3779b9u); uint h2 = hashu(h1 ^ 0x68bc21ebu);
  float r0 = float(h1 & 255u)*(1.0/255.0), r1 = float((h1 >> 8u) & 255u)*(1.0/255.0), r2 = float((h1 >> 16u) & 255u)*(1.0/255.0), r3 = float(h1 >> 24u)*(1.0/255.0);
  float r4 = float(h2 & 255u)*(1.0/255.0), r5 = float((h2 >> 8u) & 255u)*(1.0/255.0), r6 = float((h2 >> 16u) & 255u)*(1.0/255.0);
  vec2 b = ci.c0 + (0.16 + 0.68*vec2(r0, r1))*CS;
  if (ci.nearPath && abs(b.y - pathZ(b.x)) < 0.9) return false;
  if (ci.nearClr) {
    vec2 pa = b - uClrA.xy, ba = uClrA.zw - uClrA.xy;
    float hc = clamp(dot(pa, ba)/max(dot(ba, ba), 1e-4), 0.0, 1.0);
    if (length(pa - ba*hc) < uClrP.x && r6 >= uClrP.y) return false;
    vec2 pb = b - uClrB.xy, bb = uClrB.zw - uClrB.xy;
    float hb = clamp(dot(pb, bb)/max(dot(bb, bb), 1e-4), 0.0, 1.0);
    if (length(pb - bb*hb) < uClrQ.x && r6 >= uClrQ.y) return false;
  }
  float hgt = (2.4 + 3.6*r2*r2)*ci.m;
  if (hgt < 0.45) return false;
  vec2 tip = clamp(b + (vec2(r3, r4) - 0.5)*hgt*0.56, ci.c0 + 0.12*CS, ci.c0 + 0.88*CS);
  vec2 dl = tip - b; float L = length(dl); vec2 ld = dl/max(L, 1e-3);
  float dph = (r5 - 0.5)*2.0;
  L += hgt*0.03*uWind*(ci.ws*(1.0 - 0.5*dph*dph) + ci.wc*(dph - dph*dph*dph*0.1667));
  B.base = vec3(b.x, ci.cy - 0.15, b.y); B.h = hgt; B.ld = ld; B.L = L; B.w = (0.20 + 0.20*r1)*(0.55 + 0.45*ci.m); B.hue = r6;
  return true;
}

Blade heroBlade(){
  Blade B; B.base = HERO_BASE; B.h = HERO_P.x; B.ld = HERO_LD;
  B.L = HERO_P.y + 0.10*uWind*sin(uTime*1.7 + 0.5); B.w = HERO_P.z; B.hue = 0.37;
  return B;
}

float bladeIsect(Blade B, vec3 ro, vec3 rd, float tmin, float tmax, out vec3 n, out vec2 uv){
  vec3 o = ro - B.base;
  vec2 sd = vec2(-B.ld.y, B.ld.x);
  float b0 = dot(o.xz, B.ld), db = dot(rd.xz, B.ld);
  float a0 = dot(o.xz, sd), da = dot(rd.xz, sd);
  float y0 = o.y, dy = rd.y;
  float K = B.L/(B.h*B.h);
  float A = K*dy*dy, Bq = 2.0*K*y0*dy - db, C = K*y0*y0 - b0;
  float t1, t2;
  if (abs(A) < 1e-7) { if (abs(Bq) < 1e-9) return -1.0; t1 = -C/Bq; t2 = -1.0; }
  else {
    float disc = Bq*Bq - 4.0*A*C; if (disc < 0.0) return -1.0;
    float sq = sqrt(disc); float q = -0.5*(Bq + (Bq < 0.0 ? -sq : sq));
    t1 = q/A; t2 = abs(q) > 1e-12 ? C/q : -1.0;
    if (t1 > t2) { float tt = t1; t1 = t2; t2 = tt; }
  }
  for (int k = 0; k < 2; k++) {
    float t = k == 0 ? t1 : t2;
    if (t > tmin && t < tmax) {
      float y = y0 + t*dy; float u = y/B.h;
      if (u > 0.0 && u < 1.0) {
        float a = a0 + t*da;
        float hw = 0.5*B.w*(1.0 - u*u*u)*(0.6 + 0.4*smoothstep(0.0, 0.2, u));
        if (abs(a) < hw) {
          vec3 nn = normalize(vec3(B.ld.x, -2.0*K*y, B.ld.y));
          n = normalize(nn + vec3(sd.x, 0.0, sd.y)*(a/hw)*0.5);
          uv = vec2(u, a/hw);
          return t;
        }
      }
    }
  }
  return -1.0;
}

bool grassTrace(vec3 ro, vec3 rd, float tmax, int maxc, out float tH, out vec3 nH, out vec3 info){
  tH = tmax; bool found = false;
  { Blade B = heroBlade(); vec3 n; vec2 uv; float t = bladeIsect(B, ro, rd, 1e-3, tH, n, uv); if (t > 0.0) { tH = t; nH = n; info = vec3(uv, B.hue); found = true; } }
  float t0 = 0.0, t1 = tH;
  if (abs(rd.y) > 1e-6) { float ta = (GY0 - ro.y)/rd.y, tb = (GY1 - ro.y)/rd.y; t0 = max(t0, min(ta, tb)); t1 = min(t1, max(ta, tb)); }
  else if (ro.y < GY0 || ro.y > GY1) return found;
  if (t0 >= t1) return found;
  vec2 o = ro.xz + rd.xz*t0; vec2 d = rd.xz;
  ivec2 cell = ivec2(floor(o/CS));
  vec2 sgn = vec2(d.x < 0.0 ? -1.0 : 1.0, d.y < 0.0 ? -1.0 : 1.0);
  vec2 ad = max(abs(d), vec2(1e-7));
  vec2 nextB = (vec2(cell) + max(sgn, 0.0))*CS;
  vec2 tM = t0 + abs(nextB - o)/ad;
  vec2 tD = CS/ad;
  float tIn = t0;
  for (int i = 0; i < MAXC; i++) {
    if (i >= maxc) break;
    float tE = min(min(tM.x, tM.y), t1);
    CellInfo ci;
    if (cellSetup(cell, ci) && min(ro.y + rd.y*tIn, ro.y + rd.y*tE) < ci.top) {
      for (int k = 0; k < NB; k++) {
        Blade B;
        if (mkBlade(ci, k, B)) {
          vec3 n; vec2 uv; float t = bladeIsect(B, ro, rd, 1e-3, tH, n, uv);
          if (t > 0.0) { tH = t; nH = n; info = vec3(uv, B.hue); found = true; }
        }
      }
    }
    if (found && tH <= tE + 0.02) return true;
    if (tE >= t1) break;
    if (tM.x < tM.y) { cell.x += int(sgn.x); tM.x += tD.x; } else { cell.y += int(sgn.y); tM.y += tD.y; }
    tIn = tE;
  }
  return found;
}

vec3 grassShadow(vec3 ro, vec3 rd, float tmax){
  vec3 T = vec3(1.0);
  { Blade B = heroBlade(); vec3 n; vec2 uv; if (bladeIsect(B, ro, rd, 1e-3, tmax, n, uv) > 0.0) T *= GRASS_T; }
  float t0 = 0.0, t1 = tmax;
  if (abs(rd.y) > 1e-6) { float ta = (GY0 - ro.y)/rd.y, tb = (GY1 - ro.y)/rd.y; t0 = max(t0, min(ta, tb)); t1 = min(t1, max(ta, tb)); }
  else if (ro.y < GY0 || ro.y > GY1) return T;
  if (t0 >= t1) return T;
  vec2 o = ro.xz + rd.xz*t0; vec2 d = rd.xz;
  ivec2 cell = ivec2(floor(o/CS));
  vec2 sgn = vec2(d.x < 0.0 ? -1.0 : 1.0, d.y < 0.0 ? -1.0 : 1.0);
  vec2 ad = max(abs(d), vec2(1e-7));
  vec2 nextB = (vec2(cell) + max(sgn, 0.0))*CS;
  vec2 tM = t0 + abs(nextB - o)/ad;
  vec2 tD = CS/ad;
  float tIn = t0;
  for (int i = 0; i < MAXCS; i++) {
    float tE = min(min(tM.x, tM.y), t1);
    CellInfo ci;
    if (cellSetup(cell, ci) && min(ro.y + rd.y*tIn, ro.y + rd.y*tE) < ci.top) {
      for (int k = 0; k < NB; k++) {
        Blade B;
        if (mkBlade(ci, k, B)) { vec3 n; vec2 uv; if (bladeIsect(B, ro, rd, 1e-3, tmax, n, uv) > 0.0) T *= GRASS_T; }
      }
    }
    if (max(T.r, max(T.g, T.b)) < 0.02) return vec3(0.0);
    if (tE >= t1) break;
    if (tM.x < tM.y) { cell.x += int(sgn.x); tM.x += tD.x; } else { cell.y += int(sgn.y); tM.y += tD.y; }
    tIn = tE;
  }
  return T;
}

// ---------------------------------------------------------------- sky
vec3 skyAmb(vec3 d){
  float h = clamp(d.y, 0.0, 1.0);
  vec3 zen = vec3(0.010, 0.019, 0.060), hor = vec3(0.036, 0.052, 0.110);
  return mix(hor, zen, pow(h, 0.45))*uSkyGain;
}
vec3 starLayer(vec3 d, float N, float prob, float gain, float sizeMul, float pixAng){
  vec3 p = d*N; ivec3 c = ivec3(floor(p)); uint h = hash3u(c);
  float r0 = u2f(h); if (r0 > prob) return vec3(0.0);
  h = hashu(h + 0x9e3779b9u); float r1 = u2f(h); h = hashu(h + 0x9e3779b9u); float r2 = u2f(h);
  h = hashu(h + 0x9e3779b9u); float r3 = u2f(h); h = hashu(h + 0x9e3779b9u); float r4 = u2f(h);
  vec3 sp = vec3(c) + 0.15 + 0.7*vec3(r1, r2, r3);
  float ang = length(cross(normalize(sp), d));
  float mag = r4*r4*r4; mag = mag*mag;
  float sig = pixAng*sizeMul*(0.80 + 0.75*mag);
  float b = exp(-0.5*ang*ang/(sig*sig));
  float tw = 1.0 + 0.35*sin(uTime*(1.5 + 4.0*r1) + 40.0*r2);
  vec3 col = mix(vec3(0.70, 0.82, 1.0), vec3(1.0, 0.88, 0.70), r3*r3);
  return col*b*(0.020 + 1.45*mag)*tw*gain;
}
vec3 skyFull(vec3 d, bool withStars){
  vec3 c = skyAmb(d)*uSkyVis;
  float md = dot(d, uMoonDir);
  float mdp = max(md, 0.0); float m2 = mdp*mdp; float m8 = m2*m2*m2*m2; float m48 = m8*m8*m8*m8*m8*m8;
  c += vec3(0.50, 0.62, 0.95)*(0.050*m48 + 0.005*m8)*uMoonVis;
  if (withStars) {
    float pixAng = 2.0*uTanFov/uRes.y;
    float up = smoothstep(0.02, 0.20, d.y);
    vec3 st = starLayer(d, 40.0, 0.24, 1.0, 1.2, pixAng) + starLayer(d, 92.0, 0.17, 0.75, 1.0, pixAng) + starLayer(d, 170.0, 0.11, 0.55, 0.9, pixAng);
    float bd = dot(d, normalize(vec3(0.55, 0.32, -0.77)))*3.2;
    float band = exp(-bd*bd);
    float mw = band*(0.35 + 0.65*vnoise3(d*5.0 + 3.0))*(0.6 + 0.4*vnoise3(d*17.0));
    c += vec3(0.0040, 0.0050, 0.0090)*mw*up*uStarGain;
    c += st*up*uStarGain*(1.0 + 1.4*band);
    float disc = smoothstep(0.99895, 0.99915, md);
    if (disc > 0.0) {
      vec3 t, b; onb(uMoonDir, t, b); vec2 mp = vec2(dot(d, t), dot(d, b))/0.0458;
      float mar = vnoise(mp*2.1 + 5.0)*0.55 + vnoise(mp*4.7 + 1.0)*0.30 + vnoise(mp*11.0)*0.15;
      float limb = sqrt(max(1.0 - dot(mp, mp), 0.0));
      vec3 mc = vec3(1.0, 0.95, 0.80)*(0.40 + 0.30*limb)*(0.66 + 0.34*smoothstep(0.38, 0.62, mar));
      c = mix(c, mc, disc*uMoonVis);
    }
  }
  float az = atan(d.z, d.x);
  float tl = 0.030 + 0.020*vnoise(vec2(az*9.0, 1.0)) + 0.012*vnoise(vec2(az*37.0, 4.0)) + 0.02*sin(az*2.0 + 1.0);
  float tm = 1.0 - smoothstep(tl - 0.004, tl + 0.004, d.y);
  c = mix(c, vec3(0.0020, 0.0032, 0.0070), tm*0.94);
  return c;
}
vec3 fogColor(vec3 rd){
  float md = max(dot(normalize(vec3(rd.x, max(rd.y, 0.0) + 0.05, rd.z)), uMoonDir), 0.0);
  float m2 = md*md; float m8 = m2*m2*m2*m2;
  return vec3(0.034, 0.050, 0.105)*uFogGain*(1.0 + 1.5*m8*uMoonVis);
}
vec3 airlight(vec3 ro, vec3 rd, float tt){
  vec3 L = vec3(0.0);
  if (uFfGlow > 0.0) {
    vec3 q = uFfLight - ro; float b = dot(q, rd); float h = sqrt(max(dot(q, q) - b*b, 0.0036));
    L += uFfCol*uFfGlow*uGlowFog*(atan((tt - b)/h) - atan(-b/h))/h;
  }
  if (uWin > 0.0) {
    vec3 q = WINL - ro; float b = dot(q, rd); float h = sqrt(max(dot(q, q) - b*b, 0.04));
    L += WIN_COL*uWin*uGlowFog*0.6*(atan((tt - b)/h) - atan(-b/h))/h;
  }
  return min(L, vec3(30.0));
}
vec3 waterNormal(vec3 p){
  vec2 q = p.xz; float t = uTime;
  vec2 g = vec2(0.0);
  g += 0.020*vec2(cos(q.x*2.1 + t*0.9 + q.y*0.7), cos(q.y*1.7 - t*0.7 + q.x*0.5));
  g += 0.012*vec2(cos(q.x*5.3 - t*1.3 + q.y*2.9), cos(q.y*4.7 + t*1.1 - q.x*2.1));
  // rings around the log
  float dlg = abs(q.y - mix(LOG_A.z, LOG_B.z, clamp((q.x - LOG_A.x)/(LOG_B.x - LOG_A.x), 0.0, 1.0)));
  g.y += 0.02*sin(dlg*9.0 - t*2.2)*exp(-dlg*0.9);
  return normalize(vec3(-g.x, 1.0, -g.y));
}

// ---------------------------------------------------------------- materials
struct Mat { vec3 alb; vec3 emi; float spec; float rough; float trans; };
struct Hit { float t; float id; vec3 n; vec3 info; };

float capDots(vec3 c, float scale){
  vec3 g = normalize(c)*scale; vec3 ce = floor(g) + 0.5; uint h = hash3u(ivec3(floor(g)));
  float r = 0.20 + 0.16*u2f(h);
  return 1.0 - smoothstep(r - 0.03, r + 0.03, length(g - ce - 0.18*(vec3(u2f(hashu(h + 1u)), u2f(hashu(h + 2u)), u2f(hashu(h + 3u))) - 0.5)));
}

void getMat(Hit h, vec3 p, vec3 rd, inout vec3 n, out Mat m){
  m.alb = vec3(0.5); m.emi = vec3(0.0); m.spec = 0.0; m.rough = 0.6; m.trans = 0.0;
  int id = int(h.id + 0.5);
  if (id == 40) {
    float u = h.info.x, hue = h.info.z;
    vec3 c = mix(vec3(0.030, 0.075, 0.020), vec3(0.085, 0.210, 0.040), smoothstep(0.0, 0.45, u));
    c = mix(c, vec3(0.200, 0.320, 0.065), smoothstep(0.45, 1.0, u));
    c = mix(c, c*vec3(1.5, 1.05, 0.55), smoothstep(0.62, 1.0, hue)*0.7);
    c = mix(c, c*vec3(0.55, 0.95, 1.35), smoothstep(0.38, 0.0, hue)*0.6);
    c *= 0.82 + 0.18*(1.0 - abs(h.info.y));
    m.alb = c; m.trans = 0.8; m.spec = 0.035; m.rough = 0.42;
  } else if (id == 1) {
    float n1 = vnoise(p.xz*0.55), n2 = vnoise(p.xz*3.3), n3 = vnoise(p.xz*11.0);
    vec3 soil = vec3(0.072, 0.056, 0.041), moss = vec3(0.040, 0.092, 0.036);
    vec3 c = mix(soil, moss, smoothstep(0.32, 0.68, n1*0.65 + n2*0.35));
    c *= 0.75 + 0.5*n3;
    float wet = 1.0 - smoothstep(WL - 0.05, WL + 0.45, p.y);
    c = mix(c, vec3(0.045, 0.040, 0.034), wet);
    float along = smoothstep(7.5, 10.0, p.x)*(1.0 - smoothstep(37.5, 39.5, p.x));
    c = mix(c, vec3(0.115, 0.092, 0.062)*(0.8 + 0.4*n3), along*(1.0 - smoothstep(0.35, 1.3, abs(p.z - pathZ(p.x))))*0.75);
    m.alb = c; m.rough = 0.9;
    vec2 e = vec2(0.06, 0.0);
    vec2 gb = vec2(vnoise((p.xz + e.xy)*6.0) - vnoise((p.xz - e.xy)*6.0), vnoise((p.xz + e.yx)*6.0) - vnoise((p.xz - e.yx)*6.0));
    n = normalize(n + vec3(-gb.x, 0.0, -gb.y)*0.55);
  } else if (id == 2 || id == 18 || id == 16) {
    float s = vnoise3(p*4.0), s2 = vnoise3(p*17.0);
    m.alb = mix(vec3(0.17, 0.18, 0.20), vec3(0.27, 0.27, 0.28), s)*(0.85 + 0.3*s2);
    if (id == 16) m.alb = vec3(0.32, 0.20, 0.14)*(0.8 + 0.4*s);
    m.spec = 0.03; m.rough = 0.55;
  } else if (id == 3 || id == 10) {
    float s = vnoise3(p*vec3(9.0, 1.5, 9.0));
    m.alb = mix(vec3(0.60, 0.54, 0.43), vec3(0.70, 0.64, 0.52), s);
    m.spec = 0.03; m.rough = 0.5;
  } else if (id == 4 || id == 11) {
    vec3 c; float var = 0.0; float capR = 3.7; float sc = 4.6;
    if (id == 11) { c = p - HOUSE - vec3(0.0, 2.85, 0.0); c.y /= 0.69; }
    else {
      float best = 1e9; c = vec3(0.0, 1.0, 0.0);
      for (int i = 0; i < NMUSH; i++) {
        vec4 a = MUSH_A[i]; vec4 b = MUSH_B[i]; vec3 cc = p - a.xyz - vec3(b.y, b.x - a.w*0.05, 0.0);
        float dd = dot(cc, cc)/(a.w*a.w);
        if (dd < best) { best = dd; c = cc; capR = a.w; var = b.z; }
      }
      c.y /= 0.74; sc = 3.4;
    }
    if (n.y < -0.25 && c.y < 0.3*capR) {
      float st = 0.5 + 0.5*sin(atan(c.z, c.x)*(id == 11 ? 90.0 : 46.0));
      m.alb = mix(vec3(0.50, 0.42, 0.33), vec3(0.66, 0.58, 0.47), st); m.rough = 0.7;
    } else {
      float dots = capDots(c, sc)*smoothstep(0.02, 0.2, c.y/capR);
      vec3 red = var > 0.5 ? vec3(0.62, 0.30, 0.07) : vec3(0.56, 0.055, 0.035);
      if (id == 11) red = vec3(0.60, 0.060, 0.040);
      red *= 0.82 + 0.3*vnoise3(c*3.0/capR*1.2);
      m.alb = mix(red, vec3(0.78, 0.74, 0.66), dots);
      m.spec = 0.06; m.rough = 0.28;
    }
  } else if (id == 6) {
    float s = vnoise3(p*vec3(1.6, 9.0, 9.0));
    m.alb = mix(vec3(0.10, 0.065, 0.040), vec3(0.20, 0.135, 0.080), s); m.rough = 0.8;
  } else if (id == 7) { m.alb = vec3(0.060, 0.220, 0.065)*(0.8 + 0.4*vnoise(p.xz*5.0)); m.spec = 0.05; m.rough = 0.25; }
  else if (id == 8) { m.alb = vec3(0.095, 0.180, 0.060); m.rough = 0.5; }
  else if (id == 9) { m.alb = vec3(0.150, 0.080, 0.040); m.rough = 0.9; }
  else if (id == 12) {
    vec3 q = p - HOUSE; float pl = 0.5 + 0.5*sin(q.z*26.0);
    m.alb = mix(vec3(0.20, 0.105, 0.050), vec3(0.29, 0.16, 0.075), smoothstep(0.08, 0.3, pl))*(0.8 + 0.4*vnoise3(q*vec3(3.0, 3.0, 30.0)));
    m.spec = 0.04; m.rough = 0.4;
  } else if (id == 13 || id == 15) { m.alb = vec3(0.43, 0.30, 0.17); m.spec = 0.04; m.rough = 0.4; }
  else if (id == 14) { m.alb = vec3(0.3, 0.2, 0.1); m.emi = WIN_COL*(0.35 + 2.4*uWin); }
  else if (id == 17) { m.alb = vec3(0.75, 0.52, 0.18); m.spec = 0.5; m.rough = 0.25; }
  else if (id == 19) { m.alb = vec3(0.42, 0.44, 0.50); m.rough = 1.0; }
  else if (id >= 20 && id <= 26) {
    vec3 q = (transpose(uMsRot)*(p - uMsPos))/uMsScale;
    if (id == 20) {
      float belly = (1.0 - smoothstep(0.20, 0.46, q.y))*smoothstep(-0.55, -0.1, q.x);
      float fur = vnoise3(q*42.0);
      m.alb = mix(vec3(0.335, 0.275, 0.235), vec3(0.62, 0.57, 0.50), belly)*(0.88 + 0.24*fur); m.rough = 0.9;
    } else if (id == 21) {
      vec3 nl = transpose(uMsRot)*n;
      m.alb = mix(vec3(0.335, 0.275, 0.235), vec3(0.64, 0.36, 0.34), smoothstep(0.1, 0.5, nl.x)); m.rough = 0.8; m.trans = 0.25;
    } else if (id == 22) {
      m.alb = vec3(0.012); m.spec = 0.10; m.rough = 0.08;
      vec3 k = normalize(normalize(uCamPos - p) + vec3(0.0, 0.5, 0.0) + 0.35*uCamR);
      m.emi = vec3(1.0)*uCatch*smoothstep(0.972, 0.99, dot(n, k));
    } else if (id == 23) { m.alb = vec3(0.56, 0.24, 0.25); m.spec = 0.06; m.rough = 0.25; }
    else if (id == 24) { m.alb = vec3(0.62, 0.40, 0.37); m.rough = 0.6; }
    else if (id == 25) { m.alb = vec3(0.54, 0.38, 0.35); m.rough = 0.6; }
    else { float kn = 0.5 + 0.5*sin(q.y*120.0 + q.z*40.0); m.alb = vec3(0.60, 0.060, 0.050)*(0.8 + 0.2*kn); m.rough = 0.95; }
  } else if (id >= 30 && id <= 36) {
    if (id == 30 || id == 35) { m.alb = vec3(0.090, 0.060, 0.046); m.spec = 0.07; m.rough = 0.3; }
    else if (id == 31) {
      vec3 q = (transpose(uFfRot)*(p - uFfPos))/uFfScale;
      float spot = 1.0 - smoothstep(0.03, 0.05, length(q.xz - vec2(0.10, 0.0)));
      m.alb = mix(vec3(0.66, 0.24, 0.05), vec3(0.09, 0.05, 0.03), spot); m.spec = 0.08; m.rough = 0.25;
    } else if (id == 32) {
      m.alb = vec3(0.012); m.spec = 0.10; m.rough = 0.08;
      vec3 k = normalize(normalize(uCamPos - p) + vec3(0.0, 0.5, 0.0) + 0.35*uCamR);
      m.emi = vec3(1.0)*uCatch*smoothstep(0.965, 0.988, dot(n, k));
    } else if (id == 33) {
      vec3 q = (transpose(uFfRot)*(p - uFfPos))/uFfScale;
      float band = 0.5 + 0.5*sin(q.x*75.0 + 1.5);
      float tip = smoothstep(-0.02, -0.30, q.x);
      m.alb = uFfCol*0.35; m.emi = uFfCol*uFfEmi*(0.50 + 0.30*band + 0.35*tip); m.rough = 0.5;
    }
    else if (id == 34) { m.alb = vec3(0.50, 0.56, 0.62); m.trans = 0.9; m.spec = 0.08; m.rough = 0.2; }
    else { m.alb = vec3(0.135, 0.085, 0.052); m.spec = 0.08; m.rough = 0.25; }
  }
  if (uClay > 0.5) { m.alb = vec3(0.5); m.spec = 0.0; if (id != 33 && id != 14) m.emi = vec3(0.0); }
}

float ggx(vec3 n, vec3 v, vec3 l, float a, float f0){
  vec3 h = normalize(v + l); float nh = max(dot(n, h), 0.0); float a2 = a*a; float d = nh*nh*(a2 - 1.0) + 1.0;
  float D = a2/(PI*d*d); float nv = max(dot(n, v), 1e-3), nl = max(dot(n, l), 1e-3); float k = a*0.5;
  float G = 1.0/((nv*(1.0 - k) + k)*(nl*(1.0 - k) + k));
  float F = f0 + (1.0 - f0)*pow(1.0 - max(dot(h, v), 0.0), 5.0);
  return D*G*F*0.25;
}
vec3 bsdf(Mat m, vec3 n, vec3 v, vec3 l, float c){
  if (c <= 0.0) return m.alb*m.trans*TRANS_TINT*(1.0/PI);
  vec3 f = m.alb*(1.0/PI);
  if (m.spec > 0.0) f += vec3(ggx(n, v, l, m.rough*m.rough + 0.02, m.spec));
  return f;
}

// ---------------------------------------------------------------- visibility
bool traceScene(vec3 ro, vec3 rd, float tmax, int steps, int gcells, out Hit h){
  h.t = tmax; h.id = 0.0; h.n = vec3(0.0, 1.0, 0.0); h.info = vec3(0.0); bool found = false;
  if (rd.y < -1e-4 && ro.y > WL) {
    float tw = (WL - ro.y)/rd.y;
    if (tw < h.t) { vec2 wp = ro.xz + rd.xz*tw; if (length(wp - POND) < PONDR + 0.5 && terrain(wp) < WL) { h.t = tw; h.id = 50.0; found = true; } }
  }
  float tt = terrainTrace(ro, rd, h.t);
  if (tt > 0.0 && tt < h.t) { h.t = tt; h.id = 1.0; found = true; }
  float tg; vec3 ng, ig;
  if (grassTrace(ro, rd, h.t, gcells, tg, ng, ig)) { h.t = tg; h.id = 40.0; h.n = ng; h.info = ig; found = true; }
  float id; float ts = march(ro, rd, h.t, steps, false, id);
  if (ts > 0.0 && ts < h.t) { h.t = ts; h.id = id; found = true; h.n = calcNormal(ro + rd*ts, ts, false); }
  else if (h.id > 0.5 && h.id < 1.5) h.n = terrainN((ro + rd*h.t).xz);
  return found;
}

vec3 shadowT(vec3 ro, vec3 rd, float tmax, bool skipFf){
  if (terrainTrace(ro, rd, tmax) > 0.0) return vec3(0.0);
  vec3 T = grassShadow(ro, rd, tmax);
  if (max(T.r, max(T.g, T.b)) < 0.02) return vec3(0.0);
  float id;
  if (march(ro, rd, tmax, SHADOW_STEPS, skipFf, id) > 0.0) return vec3(0.0);
  return T;
}

vec3 direct(vec3 p, vec3 n, vec3 v, Mat m, bool cheap){
  vec3 L = vec3(0.0);
  float pick = cheap ? rnd() : -1.0;
  float wgt = cheap ? 2.0 : 1.0;
  if (!cheap || pick < 0.5) {
    vec3 l = coneSample(uMoonDir, MOON_COSMAX, rnd2());
    float c = dot(n, l);
    if ((c > 0.0 || m.trans > 0.0) && uMoonCol.b > 0.0) {
      vec3 f = bsdf(m, n, v, l, c);
      vec3 T = shadowT(p + n*(c > 0.0 ? 0.006 : -0.006), l, 45.0, false);
      L += wgt*T*uMoonCol*f*abs(c);
    }
  }
  if (!cheap || pick >= 0.5) {
    vec3 d1 = uFfLight - p, d2v = WINL - p;
    float w1 = uFfGlow*lum(uFfCol)/(dot(d1, d1) + 0.3);
    float w2 = uWin/(dot(d2v, d2v) + 0.3);
    float ws = w1 + w2;
    if (ws > 1e-6) {
      bool pf = rnd()*ws < w1; float pdf = (pf ? w1 : w2)/ws;
      vec3 dv = pf ? d1 : d2v; float lr = pf ? FF_LR*uFfScale : 0.22;
      vec3 Lc = pf ? uFfCol*uFfGlow : WIN_COL*uWin;
      float d = max(length(dv), lr*1.3); float dd = d*d;
      float cosMax = sqrt(1.0 - clamp(lr*lr/dd, 0.0, 0.95));
      vec3 l = coneSample(normalize(dv), cosMax, rnd2());
      float c = dot(n, l);
      if (c > 0.0 || m.trans > 0.0) {
        vec3 f = bsdf(m, n, v, l, c);
        vec3 T = shadowT(p + n*(c > 0.0 ? 0.006 : -0.006), l, max(d - lr, 0.01), pf);
        L += wgt*T*Lc/dd*f*abs(c)/pdf;
      }
    }
  }
  return L;
}

void main(){
  ivec2 ip = ivec2(gl_FragCoord.xy);
  rs = hashu(uint(ip.x)*1973u + uint(ip.y)*9277u + uint(uSeed)*26699u + uint(uPass)*104729u) | 1u;
  pcg(); pcg();
  gWingT = uTime + (rnd() - 0.5)*uSlice;
  vec2 jit = vec2(tent(rnd()), tent(rnd()))*0.75;
  vec2 px = (gl_FragCoord.xy + jit - 0.5*uRes)/(0.5*uRes.y);
  vec3 dir = normalize(uCamF + uTanFov*(px.x*uCamR + px.y*uCamU));
  vec3 ro = uCamPos, rd = dir;
  if (uAperture > 0.0) {
    vec3 fp = uCamPos + dir*(uFocus/dot(dir, uCamF));
    vec2 l = uAperture*disk(rnd2());
    ro = uCamPos + l.x*uCamR + l.y*uCamU; rd = normalize(fp - ro);
  }
  vec3 rad = vec3(0.0), emi = vec3(0.0), thr = vec3(1.0);
  vec3 gA = vec3(0.0), gN = vec3(0.0); float gZ = 0.0; bool gSet = false; bool clean = true; float tAcc = 0.0;
  int diffuse = 0;
  for (int b = 0; b < BOUNCES + 3; b++) {
    Hit h;
    bool hit = traceScene(ro, rd, clean ? TMAX : 40.0, clean ? PRIMARY_STEPS : BOUNCE_STEPS, clean ? MAXC : MAXCB, h);
    if (b == 0) {
      float tt = hit ? h.t : TMAX;
      float T = exp(-uFog*tt);
      emi += fogColor(rd)*(1.0 - T) + airlight(ro, rd, tt);
      thr *= T;
    }
    if (!hit) {
      if (clean) emi += thr*skyFull(rd, true); else rad += thr*skyAmb(rd);
      if (!gSet) { gZ = 500.0; gSet = true; }
      break;
    }
    vec3 p = ro + rd*h.t; tAcc += h.t;
    if (h.id > 49.5) {
      vec3 wn = waterNormal(p);
      float cs = max(dot(-rd, wn), 0.0); float F = 0.06 + 0.94*pow(1.0 - cs, 3.0);
      vec3 base = thr*(1.0 - F)*WATER_COL*uSkyVis*2.0;
      if (clean) emi += base; else rad += base;
      thr *= F; ro = p + vec3(0.0, 0.004, 0.0); rd = reflect(rd, wn);
      if (rd.y < 0.01) { rd.y = 0.01; rd = normalize(rd); }
      continue;
    }
    vec3 n = h.n; if (dot(n, rd) > 0.0) n = -n;
    Mat m; getMat(h, p, rd, n, m);
    if (!gSet) { gA = m.alb + m.emi; gN = n; gZ = tAcc; gSet = true; }
    if (clean) emi += thr*m.emi;
    clean = false;
    rad += thr*direct(p, n, -rd, m, diffuse > 0);
    if (diffuse == 0) rad += thr*m.alb*uFillCol*(0.5 + 0.5*dot(n, uFillDir))*(1.0/PI);
    diffuse++;
    if (diffuse > BOUNCES) { rad += thr*m.alb*skyAmb(vec3(0.0, 1.0, 0.0))*0.55; break; }
    if (m.trans > 0.0 && rnd() < 0.35) { rd = -cosHemi(n); thr *= m.alb*m.trans*TRANS_TINT/0.35; ro = p - n*0.004; }
    else { rd = cosHemi(n); thr *= m.alb/(m.trans > 0.0 ? 0.65 : 1.0); ro = p + n*0.004; }
  }
  if (uSpike > 0.0) {
    vec3 v = uFfLight - uCamPos; float z = dot(v, uCamF);
    if (z > 0.1) {
      vec2 sp = vec2(dot(v, uCamR), dot(v, uCamU))/(z*uTanFov);
      vec2 dq = (gl_FragCoord.xy - 0.5*uRes)/(0.5*uRes.y) - sp;
      float a = abs(dq.x), b = abs(dq.y);
      float g = exp(-a*11.0)*exp(-b*b*26000.0) + exp(-b*11.0)*exp(-a*a*26000.0);
      vec2 dr = vec2(dq.x + dq.y, dq.x - dq.y)*0.7071; a = abs(dr.x); b = abs(dr.y);
      g += 0.35*(exp(-a*26.0)*exp(-b*b*40000.0) + exp(-b*26.0)*exp(-a*a*40000.0));
      emi += uFfCol*uSpike*g;
    }
  }
  float l = lum(rad); if (l > 9.0) rad *= 9.0/l;
  if (any(isnan(rad)) || any(isinf(rad))) rad = vec3(0.0);
  if (any(isnan(emi)) || any(isinf(emi))) emi = vec3(0.0);
  l = lum(rad);
  oRad = vec4(rad, l*l);
  oEmi = vec4(emi, 1.0);
  oAlb = vec4(gA, gZ);
  oNrm = vec4(gN, 1.0);
}
`;
}

// ---------------------------------------------------------------- post passes
const HEAD = `#version 300 es
precision highp float;
precision highp int;
uniform vec2 uRes;
out vec4 o;
float lum(vec3 c){ return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
`;

export const PREP_FS = HEAD + `
uniform sampler2D tRad; uniform float uN;
void main(){
  ivec2 p = ivec2(gl_FragCoord.xy); ivec2 mx = ivec2(uRes) - 1;
  vec4 c = texelFetch(tRad, p, 0)/uN;
  float v = 0.0, w = 0.0;
  for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
    vec4 s = texelFetch(tRad, clamp(p + ivec2(x, y), ivec2(0), mx), 0)/uN;
    float l = lum(s.rgb); float k = (x == 0 ? 2.0 : 1.0)*(y == 0 ? 2.0 : 1.0);
    v += k*max(s.a - l*l, 0.0)/max(uN - 1.0, 1.0); w += k;
  }
  o = vec4(c.rgb, v/w);
}`;

export const ATROUS_FS = HEAD + `
uniform sampler2D tCol, tAlb, tNrm; uniform float uN; uniform int uStep; uniform vec4 uSig;
void main(){
  ivec2 p = ivec2(gl_FragCoord.xy); ivec2 mx = ivec2(uRes) - 1;
  vec4 cc = texelFetch(tCol, p, 0); vec4 ac = texelFetch(tAlb, p, 0)/uN; vec3 nc = texelFetch(tNrm, p, 0).xyz/uN;
  float nl = length(nc);
  if (nl < 0.2) { o = cc; return; }
  nc /= nl; float zc = ac.a; float lc = lum(cc.rgb); float sdv = sqrt(max(cc.a, 0.0));
  float kern[3] = float[](0.375, 0.25, 0.0625);
  vec3 sum = vec3(0.0); float sv = 0.0, ws = 0.0;
  for (int y = -2; y <= 2; y++) for (int x = -2; x <= 2; x++) {
    ivec2 q = clamp(p + ivec2(x, y)*uStep, ivec2(0), mx);
    vec4 c = texelFetch(tCol, q, 0); vec4 a = texelFetch(tAlb, q, 0)/uN; vec3 n = texelFetch(tNrm, q, 0).xyz/uN;
    float l2 = length(n);
    float wn = l2 < 0.2 ? 0.0 : pow(max(dot(n/l2, nc), 0.0), uSig.y);
    float wz = exp(-abs(a.a - zc)/(uSig.x*zc + 1e-3));
    vec3 da = a.rgb - ac.rgb; float wa = exp(-dot(da, da)/uSig.z);
    float wl = exp(-abs(lum(c.rgb) - lc)/(uSig.w*sdv + 1e-4));
    float w = kern[abs(x)]*kern[abs(y)]*wn*wz*wa*wl;
    if (x == 0 && y == 0) w = kern[0]*kern[0];
    sum += c.rgb*w; sv += c.a*w*w; ws += w;
  }
  o = vec4(sum/ws, sv/(ws*ws));
}`;

export const COMP_FS = HEAD + `
uniform sampler2D tCol, tEmi, tAlb, tNrm, tRad; uniform float uN; uniform int uMode;
void main(){
  ivec2 p = ivec2(gl_FragCoord.xy);
  vec3 c = texelFetch(tCol, p, 0).rgb + texelFetch(tEmi, p, 0).rgb/uN;
  if (uMode == 1) c = texelFetch(tAlb, p, 0).rgb/uN;
  if (uMode == 2) { vec3 n = texelFetch(tNrm, p, 0).xyz/uN; c = length(n) < 0.2 ? vec3(0.015, 0.02, 0.05) : pow(normalize(n)*0.5 + 0.5, vec3(2.2)); }
  if (uMode == 3) { float z = texelFetch(tAlb, p, 0).a/uN; c = vec3(1.0/(1.0 + z*0.06)); c *= c; }
  if (uMode == 4) c = texelFetch(tRad, p, 0).rgb/uN + texelFetch(tEmi, p, 0).rgb/uN;
  o = vec4(max(c, 0.0), 1.0);
}`;

export const DOWN_FS = HEAD + `
uniform sampler2D tSrc; uniform vec2 uTexel; uniform float uThresh;
void main(){
  vec2 uv = gl_FragCoord.xy/uRes;
  vec3 s = texture(tSrc, uv).rgb*4.0;
  s += texture(tSrc, uv + uTexel*vec2(-1.0, -1.0)).rgb + texture(tSrc, uv + uTexel*vec2(1.0, -1.0)).rgb;
  s += texture(tSrc, uv + uTexel*vec2(-1.0, 1.0)).rgb + texture(tSrc, uv + uTexel*vec2(1.0, 1.0)).rgb;
  s /= 8.0;
  s = min(s, vec3(40.0));
  if (uThresh >= 0.0) { float l = lum(s); s *= max(l - uThresh, 0.0)/max(l, 1e-4); }
  o = vec4(s, 1.0);
}`;

export const UP_FS = HEAD + `
uniform sampler2D tSrc; uniform vec2 uTexel; uniform float uGain;
void main(){
  vec2 uv = gl_FragCoord.xy/uRes;
  vec3 s = texture(tSrc, uv + uTexel*vec2(-2.0, 0.0)).rgb + texture(tSrc, uv + uTexel*vec2(2.0, 0.0)).rgb;
  s += texture(tSrc, uv + uTexel*vec2(0.0, -2.0)).rgb + texture(tSrc, uv + uTexel*vec2(0.0, 2.0)).rgb;
  s += 2.0*(texture(tSrc, uv + uTexel*vec2(-1.0, -1.0)).rgb + texture(tSrc, uv + uTexel*vec2(1.0, -1.0)).rgb);
  s += 2.0*(texture(tSrc, uv + uTexel*vec2(-1.0, 1.0)).rgb + texture(tSrc, uv + uTexel*vec2(1.0, 1.0)).rgb);
  o = vec4(s/12.0*uGain, 1.0);
}`;

export const FINAL_FS = HEAD + `
uniform sampler2D tHdr, tBloom;
uniform float uExposure, uBloom, uVig, uGrain, uSat, uContrast, uFadeOut;
uniform vec3 uLift;
uniform int uRaw, uFrame;
uint hashu(uint x){ x ^= x >> 16u; x *= 0x7feb352du; x ^= x >> 15u; x *= 0x846ca68bu; x ^= x >> 16u; return x; }
vec3 tonemap(vec3 x){ x = max(x, 0.0); return clamp((x*(2.51*x + 0.03))/(x*(2.43*x + 0.59) + 0.14), 0.0, 1.0); }
void main(){
  ivec2 p = ivec2(int(gl_FragCoord.x), int(uRes.y) - 1 - int(gl_FragCoord.y));
  vec2 uv = (vec2(p) + 0.5)/uRes;
  vec3 c = texelFetch(tHdr, p, 0).rgb;
  uint h = hashu(uint(p.x) + 8192u*uint(p.y) + uint(uFrame)*7919u*65537u);
  float g1 = float(h >> 8u)*(1.0/16777216.0); h = hashu(h + 77u); float g2 = float(h >> 8u)*(1.0/16777216.0);
  if (uRaw == 0) {
    c += texture(tBloom, uv).rgb*uBloom;
    c *= uExposure;
    vec2 q = uv - 0.5; q.x *= uRes.x/uRes.y;
    c *= 1.0 - uVig*smoothstep(0.30, 1.05, length(q)*1.25);
    // keep hue in bright saturated light: tonemap luminance and channels, blend
    vec3 tc = tonemap(c);
    float l0 = lum(c); vec3 tl = c*(lum(tonemap(vec3(l0)))/max(l0, 1e-5));
    c = mix(tc, min(tl, vec3(1.0)), 0.35);
    float l = lum(c);
    c = mix(vec3(l), c, uSat);
    c = mix(c, c*c*(3.0 - 2.0*c), uContrast);
    c = pow(max(c, 0.0), vec3(1.0/2.2));
    c += uLift*(1.0 - c)*(1.0 - c);
    c += (g1 + g2 - 1.0)*uGrain*(1.0 - 0.6*lum(c));
  } else {
    c = pow(clamp(c, 0.0, 1.0), vec3(1.0/2.2));
  }
  c *= uFadeOut;
  c += (g1 - 0.5)/255.0;
  o = vec4(clamp(c, 0.0, 1.0), 1.0);
}`;
