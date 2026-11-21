// b2m3d shot runtime: a deterministic, frame-seekable Three.js scene for HyperFrames.
// Everything visible is a pure function of time t. Config arrives as window.B2M3D_SHOT.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { HDRLoader } from "three/addons/loaders/HDRLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

const SHOT = window.B2M3D_SHOT;
const W = SHOT.width, H = SHOT.height;
const TONE = { aces: THREE.ACESFilmicToneMapping, agx: THREE.AgXToneMapping,
  neutral: THREE.NeutralToneMapping, none: THREE.NoToneMapping };

const ease = {
  linear: (x) => x,
  inOutCubic: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  outExpo: (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  inOutSine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
};
const clamp01 = (x) => Math.min(1, Math.max(0, x));
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);

function makeRenderer() {
  const canvas = document.getElementById("b2m3d-canvas");
  const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true,
    preserveDrawingBuffer: true, powerPreference: "high-performance" });
  r.setPixelRatio(1);
  r.setSize(W, H, false);
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = TONE[SHOT.tonemapping ?? "neutral"];
  r.toneMappingExposure = SHOT.exposure ?? 1.0;
  r.shadowMap.enabled = true;
  r.shadowMap.type = THREE.PCFSoftShadowMap;
  r.setClearColor(0x000000, 0);
  return r;
}

async function makeEnvironment(renderer, scene) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  let tex;
  if (SHOT.hdri) {
    const hdr = await new HDRLoader().loadAsync(SHOT.hdri);
    tex = pmrem.fromEquirectangular(hdr).texture;
    hdr.dispose();
  } else {
    tex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  }
  scene.environment = tex;
  scene.environmentIntensity = SHOT.envIntensity ?? 0.35;
  scene.environmentRotation.y = THREE.MathUtils.degToRad(SHOT.envRotation ?? 0);
  pmrem.dispose();
}

const LIGHT_RIGS = {
  studio: [{ type: "key", color: "#ffffff", intensity: 2.6, pos: [3, 5, 4] },
    { type: "rim", color: "#9fc4ff", intensity: 2.0, pos: [-4, 3, -4] },
    { type: "fill", color: "#ffe9d6", intensity: 0.4, pos: [-3, 1.5, 3] }],
  dramatic: [{ type: "key", color: "#fff4e6", intensity: 4.0, pos: [2.5, 6, 2] },
    { type: "rim", color: "#6f8cff", intensity: 3.5, pos: [-3, 2, -5] }],
  soft: [{ type: "key", color: "#ffffff", intensity: 1.4, pos: [2, 6, 3] },
    { type: "fill", color: "#ffffff", intensity: 0.8, pos: [-3, 3, 2] }],
};

function addLights(scene, bounds) {
  const rig = Array.isArray(SHOT.lights) ? SHOT.lights : LIGHT_RIGS[SHOT.lights ?? "dramatic"];
  const size = bounds.getSize(new THREE.Vector3()).length() || 1;
  const centre = bounds.getCenter(new THREE.Vector3());
  for (const l of rig) {
    const light = new THREE.DirectionalLight(l.color, l.intensity);
    light.position.copy(v3(l.pos).multiplyScalar(size * 0.6).add(centre));
    light.target.position.copy(centre);
    if (l.type === "key") {
      light.castShadow = true;
      const s = light.shadow;
      s.mapSize.set(4096, 4096);
      s.bias = -0.0002;
      s.normalBias = 0.02 * size;
      s.radius = 6;
      const half = size * 1.2;
      Object.assign(s.camera, { left: -half, right: half, top: half, bottom: -half,
        near: 0.01, far: size * 6 });
    }
    scene.add(light, light.target);
  }
}

function addGround(scene, bounds) {
  const g = SHOT.ground ?? { shadow: 0.35 };
  if (g === false) return;
  const size = bounds.getSize(new THREE.Vector3()).length() || 1;
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(size * 40, size * 40),
    g.color ? new THREE.MeshStandardMaterial({ color: g.color, roughness: g.roughness ?? 0.6, metalness: 0 })
            : new THREE.ShadowMaterial({ opacity: g.shadow ?? 0.35 }));
  plane.rotation.x = -Math.PI / 2;
  plane.position.y = g.y ?? bounds.min.y;
  plane.receiveShadow = true;
  scene.add(plane);
}

async function loadModels(scene) {
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const out = [];
  for (const m of SHOT.models ?? []) {
    const gltf = await loader.loadAsync(m.src);
    const root = gltf.scene;
    root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    if (m.position) root.position.copy(v3(m.position));
    if (m.rotation) root.rotation.set(...m.rotation.map(THREE.MathUtils.degToRad));
    if (m.scale) root.scale.setScalar(m.scale);
    const pivot = new THREE.Group();
    pivot.add(root);
    scene.add(pivot);
    const mixer = gltf.animations.length ? new THREE.AnimationMixer(root) : null;
    if (mixer) gltf.animations.forEach((clip) => mixer.clipAction(clip).play());
    out.push({ cfg: m, pivot, root, mixer, rest: root.position.clone() });
  }
  return out;
}

function trackPose(track, fps, t) {
  const f = Math.min(track.length - 1, Math.max(0, t * fps));
  const i = Math.floor(f), j = Math.min(track.length - 1, i + 1), a = f - i;
  const p = v3(track[i]).lerp(v3(track[j]), a);
  const qa = new THREE.Quaternion(...track[i].slice(3)), qb = new THREE.Quaternion(...track[j].slice(3));
  return { p, q: qa.slerp(qb, a) };
}

// The parts of an exploded view are the children of the first node that has several; exporters
// often wrap everything in one root node, so skip down through single-child wrappers.
function explodeParts(root) {
  let node = root;
  while (node.children.length === 1) node = node.children[0];
  return node.children.length ? node.children : [node];
}

function animateModel(m, t, physics) {
  const c = m.cfg;
  if (c.track && physics) {
    const { p, q } = trackPose(physics.tracks[c.track], physics.fps, t - (c.trackStart ?? 0));
    m.pivot.position.copy(p);
    m.pivot.quaternion.copy(q);
  }
  if (c.spin) m.pivot.rotation.y = THREE.MathUtils.degToRad(c.spin) * t + (c.spinOffset ?? 0);
  if (c.float) m.pivot.position.y = Math.sin(t * (c.float.speed ?? 1.2)) * (c.float.amp ?? 0.01);
  if (c.reveal) {
    const k = ease[c.reveal.ease ?? "outExpo"](clamp01((t - (c.reveal.start ?? 0)) / (c.reveal.duration ?? 0.8)));
    m.pivot.scale.setScalar(Math.max(1e-4, k));
  }
  if (c.explode) {
    const e = c.explode;
    const k = ease.inOutCubic(clamp01((t - (e.start ?? 0)) / (e.duration ?? 1)));
    explodeParts(m.root).forEach((child, idx) => {
      const dir = e.dirs?.[child.name] ?? [0, idx * (e.step ?? 0.03), 0];
      child.userData.rest ??= child.position.clone();
      child.position.copy(child.userData.rest).addScaledVector(v3(dir), k);
    });
  }
  if (m.mixer) m.mixer.setTime(t);
}

function fitBox(box, auto, fov) {
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const az = THREE.MathUtils.degToRad(auto.azimuth ?? 35), el = THREE.MathUtils.degToRad(auto.elevation ?? 22);
  const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
  const dist = (sphere.radius / Math.sin(THREE.MathUtils.degToRad(fov) / 2)) * (auto.padding ?? 1.15);
  return { pos: sphere.center.clone().addScaledVector(dir, dist), target: sphere.center.clone() };
}

// camera.auto: frame everything at t=0 and the settled pose at the end (from the physics bake).
function autoCamera(t, bounds, physics, auto) {
  const fov = SHOT.camera.fov ?? 28;
  const endBox = new THREE.Box3();
  if (physics) {
    for (const [name, tr] of Object.entries(physics.tracks)) {
      if ((auto.ignore ?? ["floor"]).includes(name)) continue;
      endBox.expandByPoint(v3(tr[tr.length - 1]));
    }
    endBox.expandByScalar(auto.margin ?? 0.03);
  }
  // Start wide on the landing zone (parts fall INTO frame), end tight on the settled pile.
  const land = endBox.isEmpty() ? bounds : endBox;
  const a = fitBox(land, { ...auto, padding: auto.startPadding ?? 1.8,
    azimuth: auto.startAzimuth ?? auto.azimuth, elevation: auto.startElevation ?? auto.elevation }, fov);
  const b = fitBox(land, auto, fov);
  const x = ease[auto.ease ?? "inOutSine"](clamp01((t - (auto.start ?? 0)) / (auto.duration ?? SHOT.duration)));
  return { pos: a.pos.lerp(b.pos, x), target: a.target.lerp(b.target, x), fov };
}

function cameraAt(t, bounds, physics) {
  const cam = SHOT.camera ?? {};
  if (cam.auto) return autoCamera(t, bounds, physics, cam.auto);
  const centre = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3()).length() || 1;
  if (cam.keys?.length) {
    const keys = cam.keys;
    let k = keys.length - 1;
    for (let i = 0; i < keys.length - 1; i++) if (t < keys[i + 1].t) { k = i; break; }
    const a = keys[k], b = keys[Math.min(k + 1, keys.length - 1)];
    const span = Math.max(1e-6, b.t - a.t);
    const x = ease[b.ease ?? cam.ease ?? "inOutCubic"](clamp01((t - a.t) / span));
    return { pos: v3(a.pos).lerp(v3(b.pos), x), target: v3(a.target ?? centre.toArray()).lerp(v3(b.target ?? centre.toArray()), x),
      fov: (a.fov ?? cam.fov ?? 30) + ((b.fov ?? cam.fov ?? 30) - (a.fov ?? cam.fov ?? 30)) * x };
  }
  const o = cam.orbit ?? {};
  const x = ease[o.ease ?? "inOutSine"](clamp01(t / SHOT.duration));
  const deg = (o.from ?? -35) + ((o.to ?? 35) - (o.from ?? -35)) * x;
  const r = (o.radius ?? 1.6) * size, h = (o.height ?? 0.45) * size;
  const ang = THREE.MathUtils.degToRad(deg);
  return { pos: new THREE.Vector3(Math.sin(ang) * r, h, Math.cos(ang) * r).add(centre),
    target: o.target ? v3(o.target) : centre, fov: cam.fov ?? 30 };
}

// Bounds that drive lights, shadow map and ground height: each model at rest, plus where every
// tracked body ends up (its last pose, with its own height). The fall itself is left out on purpose,
// or a part dropped from far above would stretch the box and blur the shadows. The physics floor
// is not a model, so it never counts.
function sceneBounds(models, physics) {
  const box = new THREE.Box3();
  models.forEach((m) => box.expandByObject(m.pivot));
  if (physics) {
    for (const m of models) {
      const track = m.cfg.track && physics.tracks[m.cfg.track];
      if (!track) continue;
      const local = new THREE.Box3().setFromObject(m.pivot);
      const end = v3(track[track.length - 1]);
      box.expandByPoint(end.clone().add(new THREE.Vector3(local.min.x, local.min.y, local.min.z)));
      box.expandByPoint(end.clone().add(new THREE.Vector3(local.max.x, local.max.y, local.max.z)));
    }
  }
  if (SHOT.bounds) return new THREE.Box3(v3(SHOT.bounds[0]), v3(SHOT.bounds[1]));
  return box.isEmpty() ? new THREE.Box3(v3([-1, -1, -1]), v3([1, 1, 1])) : box;
}

async function build() {
  const renderer = makeRenderer();
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, W / H, 0.001, 1000);
  await makeEnvironment(renderer, scene);
  const physics = window.B2M3D_PHYSICS ?? null;
  const models = await loadModels(scene);
  const bounds = sceneBounds(models, physics); // rest pose, before reveal/explode
  models.forEach((m) => animateModel(m, 0, physics));
  addLights(scene, bounds);
  addGround(scene, bounds);

  const composer = new EffectComposer(renderer);
  composer.setPixelRatio(1);
  composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  if (SHOT.bloom) {
    const b = SHOT.bloom;
    composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), b.strength ?? 0.35, b.radius ?? 0.4, b.threshold ?? 0.85));
  }
  composer.addPass(new OutputPass());

  function renderAt(t) {
    models.forEach((m) => animateModel(m, t, physics));
    const c = cameraAt(t, bounds, physics);
    camera.position.copy(c.pos);
    camera.fov = c.fov;
    camera.updateProjectionMatrix();
    camera.lookAt(c.target);
    composer.render();
  }
  renderer.compile(scene, camera);
  renderAt(window.__hfThreeTime || 0);
  window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
  window.__b2m3dRenderAt = renderAt;
  return true;
}

window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};
window.__hf.buildReady["b2m3d-scene"] = build();
