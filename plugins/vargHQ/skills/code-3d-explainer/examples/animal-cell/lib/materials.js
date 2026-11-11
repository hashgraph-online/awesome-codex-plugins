// materials.js: the explainer look, as small ShaderMaterials (no textures, no env maps, seek-safe).
//   shell()  translucent x-ray membrane: fresnel rim, milky body, noisy reveal sweep with a glowing edge
//   solid()  stylized opaque part: wrap light + rim + soft spec, optional stripes (cristae), flat cut caps
//   glow()   additive emissive lines and filaments
//   bokeh()  soft out-of-focus points for depth
// All support clipping planes (cutaways) and a uDim focus uniform. Colours are THREE.Color (linear).
import * as THREE from 'three';

// 3D simplex noise, Ashima Arts / Stefan Gustavson (MIT), https://github.com/ashima/webgl-noise
export const NOISE = `
vec3 m289(vec3 x){return x-floor(x*(1./289.))*289.;} vec4 m289(vec4 x){return x-floor(x*(1./289.))*289.;}
vec4 perm(vec4 x){return m289(((x*34.)+1.)*x);} vec4 tis(vec4 r){return 1.79284291400159-0.85373472095314*r;}
float snoise(vec3 v){const vec2 C=vec2(1./6.,1./3.);const vec4 D=vec4(0.,.5,1.,2.);
 vec3 i=floor(v+dot(v,C.yyy));vec3 x0=v-i+dot(i,C.xxx);vec3 g=step(x0.yzx,x0.xyz);vec3 l=1.-g;
 vec3 i1=min(g.xyz,l.zxy);vec3 i2=max(g.xyz,l.zxy);vec3 x1=x0-i1+C.xxx;vec3 x2=x0-i2+C.yyy;vec3 x3=x0-D.yyy;
 i=m289(i);vec4 p=perm(perm(perm(i.z+vec4(0.,i1.z,i2.z,1.))+i.y+vec4(0.,i1.y,i2.y,1.))+i.x+vec4(0.,i1.x,i2.x,1.));
 float n_=.142857142857;vec3 ns=n_*D.wyz-D.xzx;vec4 j=p-49.*floor(p*ns.z*ns.z);vec4 x_=floor(j*ns.z);vec4 y_=floor(j-7.*x_);
 vec4 x=x_*ns.x+ns.yyyy;vec4 y=y_*ns.x+ns.yyyy;vec4 h=1.-abs(x)-abs(y);vec4 b0=vec4(x.xy,y.xy);vec4 b1=vec4(x.zw,y.zw);
 vec4 s0=floor(b0)*2.+1.;vec4 s1=floor(b1)*2.+1.;vec4 sh=-step(h,vec4(0.));vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
 vec3 p0=vec3(a0.xy,h.x);vec3 p1=vec3(a0.zw,h.y);vec3 p2=vec3(a1.xy,h.z);vec3 p3=vec3(a1.zw,h.w);
 vec4 norm=tis(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
 vec4 m=max(.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.);m=m*m;
 return 42.*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));}
`;

const VERT = `
#include <common>
#include <clipping_planes_pars_vertex>
varying vec3 vN; varying vec3 vW; varying vec3 vObj; varying vec2 vUv;
void main(){
  vec4 p = vec4(position, 1.0); vec3 n = normal;
  #ifdef USE_INSTANCING
    p = instanceMatrix * p; n = mat3(instanceMatrix) * n;
  #endif
  vObj = position; vUv = uv;
  vec4 w = modelMatrix * p; vW = w.xyz;
  vN = normalize(mat3(modelMatrix) * n);
  vec4 mvPosition = viewMatrix * w;
  gl_Position = projectionMatrix * mvPosition;
  #include <clipping_planes_vertex>
}`;

const col = (c) => new THREE.Color(c);
const LIGHT = new THREE.Vector3(-0.45, 0.75, 0.5).normalize();

/** translucent x-ray shell (membranes, envelopes, ER sheets) */
export function shell(o = {}) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide, clipping: true,
    uniforms: {
      uColor: { value: col(o.color ?? '#1aa6a0') }, uRim: { value: col(o.rim ?? '#5ff5e6') }, uEdge: { value: col(o.edge ?? '#ff5315') },
      uOpacity: { value: o.opacity ?? 0.25 }, uRimPower: { value: o.rimPower ?? 2.6 }, uRimStrength: { value: o.rimStrength ?? 1.2 },
      uReveal: { value: 1 }, uMode: { value: o.mode ?? 0 }, uAxis: { value: (o.axis ?? new THREE.Vector3(0, 1, 0)).clone() },
      uOrigin: { value: (o.origin ?? new THREE.Vector3()).clone() }, uRange: { value: new THREE.Vector2(...(o.range ?? [-1, 1])) },
      uNoise: { value: o.noise ?? 0.6 }, uSpeck: { value: o.speck ?? 0.35 }, uEdgeFade: { value: o.edgeFade ?? 0 },
      uSpecular: { value: o.specular ?? 0.6 }, uRevealNoise: { value: o.revealNoise ?? 0.08 }, uEdgeWidth: { value: o.edgeWidth ?? 0.045 }, uDim: { value: 1 }, uFade: { value: 1 }, uLight: { value: LIGHT },
    },
    vertexShader: VERT,
    fragmentShader: `
      #include <common>
      #include <clipping_planes_pars_fragment>
      ${NOISE}
      uniform vec3 uColor, uRim, uEdge, uAxis, uOrigin, uLight; uniform vec2 uRange;
      uniform float uOpacity, uRimPower, uRimStrength, uReveal, uMode, uNoise, uSpeck, uEdgeFade, uSpecular, uRevealNoise, uEdgeWidth, uDim, uFade;
      varying vec3 vN; varying vec3 vW; varying vec3 vObj; varying vec2 vUv;
      void main(){
        #include <clipping_planes_fragment>
        vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
        float back = gl_FrontFacing ? 0.0 : 1.0; if (back > 0.5) N = -N;
        float f = 1.0 - clamp(dot(N, V), 0.0, 1.0);
        float rim = pow(f, uRimPower);
        float n = snoise(vObj * uNoise);
        float coord = uMode < 0.5 ? (dot(vObj, uAxis) - uRange.x) / (uRange.y - uRange.x) : (length(vW - uOrigin) - uRange.x) / (uRange.y - uRange.x);
        float d = (uReveal * 1.3 - 0.15) - (coord + n * uRevealNoise);
        if (d < 0.0) discard;
        float edge = (1.0 - smoothstep(0.0, uEdgeWidth, d)) * step(uReveal, 0.999);
        float ef = 1.0;
        if (uEdgeFade > 0.0) { float e = min(min(vUv.x, 1.0 - vUv.x), min(vUv.y, 1.0 - vUv.y)); float r = uEdgeFade * (0.55 + 0.45 * snoise(vObj * 1.7)); if (e < r * 0.35) discard; ef = smoothstep(r * 0.35, r, e); rim = max(rim, (1.0 - ef) * 0.9); }
        // two-scale mottling (lipid/protein texture) and half-lambert form from one key light
        float speck = (0.6 * smoothstep(-0.2, 0.8, n) + 0.4 * smoothstep(0.3, 0.9, snoise(vObj * uNoise * 5.0))) * uSpeck;
        float lam = 0.18 + 0.82 * pow(clamp(0.5 + 0.5 * dot(N, uLight), 0.0, 1.0), 1.5);
        float spec = (1.0 - back) * pow(clamp(dot(N, normalize(uLight + V)), 0.0, 1.0), 36.0) * uSpecular;
        vec3 c = uColor * lam * (0.7 + 0.6 * speck) + uRim * rim * uRimStrength + vec3(spec) + uEdge * edge * 2.5;
        float a = uOpacity * (1.0 - 0.55 * back) * (0.8 + 0.5 * speck) + rim * 0.75 * (1.0 - 0.4 * back) + edge + spec * 0.6;
        gl_FragColor = vec4(c * uDim, clamp(a, 0.0, 1.0) * uFade);
      }`,
  });
}

/** stylized opaque part; back faces render as a flat cut cap so clipped parts look solid */
export function solid(o = {}) {
  return new THREE.ShaderMaterial({
    side: THREE.DoubleSide, clipping: true, transparent: !!o.transparent, depthWrite: !o.transparent,
    uniforms: {
      uColor: { value: col(o.color ?? '#ff5315') }, uRim: { value: col(o.rim ?? '#ffd2b8') }, uCap: { value: col(o.cap ?? o.color ?? '#ff5315').multiplyScalar(0.55) },
      uEmissive: { value: col(o.emissive ?? '#000000') }, uRimStrength: { value: o.rimStrength ?? 0.6 }, uSpec: { value: o.spec ?? 0.35 },
      uStripes: { value: o.stripes ?? 0 }, uStripeFreq: { value: o.stripeFreq ?? 14 }, uStripeAxis: { value: (o.stripeAxis ?? new THREE.Vector3(0, 1, 0)).clone() },
      uGrain: { value: o.grain ?? 0.0 }, uUvShade: { value: o.uvShade ?? 0.0 }, uDim: { value: 1 }, uFade: { value: 1 }, uLight: { value: LIGHT },
    },
    vertexShader: VERT,
    fragmentShader: `
      #include <common>
      #include <clipping_planes_pars_fragment>
      ${NOISE}
      uniform vec3 uColor, uRim, uCap, uEmissive, uStripeAxis, uLight; uniform float uRimStrength, uSpec, uStripes, uStripeFreq, uGrain, uUvShade, uDim, uFade;
      varying vec3 vN; varying vec3 vW; varying vec3 vObj; varying vec2 vUv;
      void main(){
        #include <clipping_planes_fragment>
        if (!gl_FrontFacing) { gl_FragColor = vec4(uCap * uDim, uFade); return; }
        vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
        float ndl = dot(N, uLight);
        float wrap = clamp((ndl + 0.45) / 1.45, 0.0, 1.0);
        float sky = 0.5 + 0.5 * N.y;
        float spec = pow(clamp(dot(N, normalize(uLight + V)), 0.0, 1.0), 48.0) * uSpec;
        float rim = pow(1.0 - clamp(dot(N, V), 0.0, 1.0), 3.0) * uRimStrength;
        vec3 base = uColor;
        if (uStripes > 0.0) {
          float s = sin(dot(vObj, uStripeAxis) * uStripeFreq + snoise(vObj * 2.2) * 2.2);
          base = mix(base, base * 0.3, smoothstep(0.72, 0.95, s) * uStripes);
          base = mix(base, base * 1.25, smoothstep(0.2, -0.6, s) * 0.35 * uStripes);
        }
        if (uGrain > 0.0) base *= 1.0 - uGrain * smoothstep(0.2, 0.9, snoise(vObj * 7.0));
        if (uUvShade > 0.0) base *= mix(1.0, 0.35 + 0.9 * sqrt(clamp(1.0 - abs(vUv.y - 0.5) * 2.0, 0.0, 1.0)), uUvShade); // lathe parts: dark centre, bright rim
        vec3 c = base * (0.16 + 0.62 * wrap + 0.22 * sky) + vec3(spec) + uRim * rim + uEmissive;
        gl_FragColor = vec4(c * uDim, uFade);
      }`,
  });
}

/** additive glow for filaments, chromatin, rims */
export function glow(o = {}) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, clipping: true,
    uniforms: { uColor: { value: col(o.color ?? '#7ff0e4') }, uStrength: { value: o.strength ?? 1 }, uDim: { value: 1 }, uFade: { value: 1 } },
    vertexShader: VERT,
    fragmentShader: `
      #include <common>
      #include <clipping_planes_pars_fragment>
      uniform vec3 uColor; uniform float uStrength, uDim, uFade; varying vec3 vN; varying vec3 vW; varying vec3 vObj; varying vec2 vUv;
      void main(){
        #include <clipping_planes_fragment>
        vec3 N = normalize(vN); vec3 V = normalize(cameraPosition - vW);
        float core = 0.35 + 0.65 * abs(dot(N, V));
        gl_FragColor = vec4(uColor * core * uStrength * uDim * uFade, 1.0);
      }`,
  });
}

/** soft round points, sized in world units, additive (depth haze and bokeh) */
export function bokeh(o = {}) {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uScale: { value: o.scale ?? 540 }, uFade: { value: 1 }, uRing: { value: o.ring ?? 0.35 } },
    vertexShader: `attribute float aSize; attribute vec3 aColor; varying vec3 vC; uniform float uScale;
      void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;
        gl_PointSize = clamp(aSize * uScale / -mv.z, 1.0, 160.0); vC = aColor; }`,
    fragmentShader: `varying vec3 vC; uniform float uFade, uRing;
      void main(){ vec2 q = gl_PointCoord - 0.5; float r = length(q) * 2.0; if (r > 1.0) discard;
        float a = smoothstep(1.0, 0.72, r) * (1.0 - uRing + uRing * smoothstep(0.45, 0.95, r));
        gl_FragColor = vec4(vC * a * uFade, 1.0); }`,
  });
}

/** set a uniform on one material or every material under an object */
export function setU(target, name, value) {
  const apply = (m) => { if (m && m.uniforms && m.uniforms[name]) { const u = m.uniforms[name]; if (u.value && u.value.copy && value && value.isColor) u.value.copy(value); else u.value = value; } };
  if (target.isMaterial) return apply(target);
  target.traverse(o => { if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(apply); });
}
