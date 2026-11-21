// b2m3d physics: deterministic Jolt rigid-body bake -> per-frame transforms.
// HyperFrames seeks frames out of order across parallel workers, so physics can't
// run live in the page. We simulate once here at a fixed step and store a pose per
// frame; the page just reads track[frame].
// usage: node jolt_bake.mjs <scene.json> <out.json>
// Prints: B2M3D_PHYSICS {json summary}
import initJolt from "jolt-physics/wasm-compat";
import { readFileSync, writeFileSync } from "node:fs";

const [scenePath, outPath] = process.argv.slice(2);
const scene = JSON.parse(readFileSync(scenePath, "utf8"));
const Jolt = await initJolt();

const NON_MOVING = 0, MOVING = 1;
function makeInterface() {
  const settings = new Jolt.JoltSettings();
  const pairs = new Jolt.ObjectLayerPairFilterTable(2);
  pairs.EnableCollision(NON_MOVING, MOVING);
  pairs.EnableCollision(MOVING, MOVING);
  const bp = new Jolt.BroadPhaseLayerInterfaceTable(2, 2);
  bp.MapObjectToBroadPhaseLayer(NON_MOVING, new Jolt.BroadPhaseLayer(0));
  bp.MapObjectToBroadPhaseLayer(MOVING, new Jolt.BroadPhaseLayer(1));
  settings.mObjectLayerPairFilter = pairs;
  settings.mBroadPhaseLayerInterface = bp;
  settings.mObjectVsBroadPhaseLayerFilter =
    new Jolt.ObjectVsBroadPhaseLayerFilterTable(bp, 2, pairs, 2);
  const jolt = new Jolt.JoltInterface(settings);
  Jolt.destroy(settings);
  return jolt;
}

function makeShape(b) {
  const s = b.shape;
  if (s === "box") {
    const [x, y, z] = b.size;
    return new Jolt.BoxShape(new Jolt.Vec3(x / 2, y / 2, z / 2), Math.min(0.05, x / 10, y / 10, z / 10));
  }
  if (s === "sphere") return new Jolt.SphereShape(b.radius);
  if (s === "cylinder") return new Jolt.CylinderShape(b.height / 2, b.radius, Math.min(0.05, b.radius / 10));
  if (s === "hull") {
    const hs = new Jolt.ConvexHullShapeSettings();
    for (const [x, y, z] of b.points) hs.mPoints.push_back(new Jolt.Vec3(x, y, z));
    const res = hs.Create();
    if (res.HasError()) throw new Error(`hull for ${b.name}: ${res.GetError().c_str()}`);
    return res.Get();
  }
  throw new Error(`unknown shape ${s} for body ${b.name}`);
}

const MOTION = {
  static: Jolt.EMotionType_Static,
  dynamic: Jolt.EMotionType_Dynamic,
  kinematic: Jolt.EMotionType_Kinematic,
};

const jolt = makeInterface();
const system = jolt.GetPhysicsSystem();
const bodies = system.GetBodyInterface();
const g = scene.gravity ?? [0, -9.81, 0];
system.SetGravity(new Jolt.Vec3(g[0], g[1], g[2]));

const handles = [];
for (const b of scene.bodies) {
  const motion = b.motion ?? "dynamic";
  const [px, py, pz] = b.position ?? [0, 0, 0];
  const [qx, qy, qz, qw] = b.rotation ?? [0, 0, 0, 1];
  const cs = new Jolt.BodyCreationSettings(makeShape(b), new Jolt.RVec3(px, py, pz),
    new Jolt.Quat(qx, qy, qz, qw), MOTION[motion], motion === "static" ? NON_MOVING : MOVING);
  cs.mFriction = b.friction ?? 0.5;
  cs.mRestitution = b.restitution ?? 0.2;
  cs.mLinearDamping = b.linearDamping ?? 0.05;
  cs.mAngularDamping = b.angularDamping ?? 0.05;
  if (motion !== "static") cs.mMotionQuality = Jolt.EMotionQuality_LinearCast;
  const body = bodies.CreateBody(cs);
  Jolt.destroy(cs);
  const id = body.GetID();
  bodies.AddBody(id, motion === "static" ? Jolt.EActivation_DontActivate : Jolt.EActivation_Activate);
  if (b.velocity) bodies.SetLinearVelocity(id, new Jolt.Vec3(...b.velocity));
  if (b.angular) bodies.SetAngularVelocity(id, new Jolt.Vec3(...b.angular));
  handles.push({ name: b.name, id, body, motion });
}

const fps = scene.fps ?? 30;
const frames = Math.round((scene.duration ?? 4) * fps);
const substeps = scene.substeps ?? 4;
const dt = 1 / fps / substeps;
const tracks = Object.fromEntries(handles.map((h) => [h.name, []]));
const r = (v) => Math.round(v * 1e5) / 1e5;

function record() {
  for (const h of handles) {
    const p = h.body.GetPosition();
    const q = h.body.GetRotation();
    tracks[h.name].push([r(p.GetX()), r(p.GetY()), r(p.GetZ()), r(q.GetX()), r(q.GetY()), r(q.GetZ()), r(q.GetW())]);
  }
}

record();
let maxSpeed = 0;
for (let f = 1; f < frames; f++) {
  for (let s = 0; s < substeps; s++) jolt.Step(dt, 1);
  record();
}
for (const h of handles) {
  const v = h.body.GetLinearVelocity();
  maxSpeed = Math.max(maxSpeed, Math.hypot(v.GetX(), v.GetY(), v.GetZ()));
}

const out = { fps, frames, substeps, tracks };
writeFileSync(outPath, JSON.stringify(out));
const settled = maxSpeed < 0.05;
console.log("B2M3D_PHYSICS " + JSON.stringify({
  out: outPath, fps, frames, bodies: handles.length,
  final_max_speed: r(maxSpeed), settled,
}));
