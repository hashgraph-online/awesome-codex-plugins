"""b2m_walk: a figure walks forward: a leg cycle plus root travel, with each planted foot staying put on the ground.

The body moves at a constant speed. A foot that is on the ground is held at one world position until it lifts
(the "plant"), and each leg is solved to reach it with two-bone IK; a foot in the air swings from one plant to the
next with a lift. So the stride is fitted to the speed (stride = speed x cycle time) and nothing slides. Every frame
is keyed, so the result is plain keyframes with no rig or add-on needed. With --naive the feet follow the body
instead, which makes the slide the checks catch.

  blender -b --factory-startup -P b2m_walk.py -- --speed 1.2 --cycle-frames 32 --frames 120 --out frames
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import b2m_common as c  # noqa: E402
from b2m_math import foot_target, solve_leg  # noqa: E402,F401  (pure functions, tested without Blender)

DEFAULTS = {
    "frames": 96,
    "speed": 1.2,          # metres per second
    "cycle_frames": 32,    # frames for one foot to come round again (a left step plus a right step)
    "duty": 0.6,           # share of the cycle a foot spends on the ground
    "step_height": 0.12,   # how high the swing foot lifts, metres
    "thigh": 0.45,
    "shin": 0.45,
    "hip_height": 0.82,    # under thigh + shin, so the legs reach the stride without locking
    "bob": 0.02,           # vertical bounce of the hips, twice a cycle: lowest with both feet down, highest over one foot
    "arm_swing": 0.6,      # arm swing as a share of the opposite thigh's swing
    "twist": 0.1,          # radians the chest turns against the hips each step
    "lead": 0.4,           # metres the camera's aim runs ahead of the body, leaving room in the direction of travel
    "naive": False,        # feet follow the body instead of planting (shows foot slide)
}


def _figure(coll, p):
    """A jointed mannequin: tapered rounded limbs, ball joints, an egg head. Hip, knee, ankle, shoulder and elbow
    are empties, so the walk keys plain rotations. Proportions follow the leg length (thigh + shin)."""
    body = c.material("b2m_body", p["subject"], roughness=0.42, coat=0.3)
    joint = c.material("b2m_joint", p["accent"], roughness=0.3, metallic=0.2, coat=0.5)
    sole = c.material("b2m_sole", p["ink"], roughness=0.6)
    l1, l2 = float(p["thigh"]), float(p["shin"])
    u = (l1 + l2) / 0.94                                  # body scale: 1.0 for a 0.94 m leg, about 1.78 m tall
    pelvis = c.empty(coll, "b2m_pelvis", (0, 0, float(p["hip_height"])))
    c.capsule(coll, "b2m_hips", 0.115 * u, 0.1 * u, 0.2 * u, body, pelvis, (0, 0, 0.09 * u), squash=0.62)
    torso = c.empty(coll, "b2m_torso", (0, 0, 0.06 * u), pelvis)
    c.capsule(coll, "b2m_chest", 0.17 * u, 0.12 * u, 0.44 * u, body, torso, (0, 0, 0.52 * u), squash=0.68)
    c.capsule(coll, "b2m_neck", 0.045 * u, 0.05 * u, 0.12 * u, body, torso, (0, 0, 0.62 * u))
    head = c.capsule(coll, "b2m_head", 0.1 * u, 0.09 * u, 0.24 * u, body, torso, (0.01 * u, 0, 0.86 * u), squash=0.9)
    head.rotation_euler = (0, 0.12, 0)
    rig = {"pelvis": pelvis, "torso": torso, "legs": {}, "arms": {}}
    for side, y in (("L", 0.095 * u), ("R", -0.095 * u)):
        hip = c.empty(coll, f"b2m_hip{side}", (0, y, 0), pelvis)
        knee = c.empty(coll, f"b2m_knee{side}", (0, 0, -l1), hip)
        ankle = c.empty(coll, f"b2m_ankle{side}", (0, 0, -l2), knee)
        c.capsule(coll, f"b2m_thigh{side}", 0.075 * u, 0.052 * u, l1, body, hip)
        c.capsule(coll, f"b2m_shin{side}", 0.05 * u, 0.036 * u, l2 - 0.05 * u, body, knee)
        c.capsule(coll, f"b2m_kneecap{side}", 0.056 * u, 0.056 * u, 0.112 * u, joint, knee, (0, 0, 0.056 * u))
        foot = c.empty(coll, f"b2m_foot{side}", (0, 0, 0), ankle)          # keyed to keep the sole flat
        shoe = c.capsule(coll, f"b2m_shoe{side}", 0.045 * u, 0.045 * u, 0.25 * u, sole, foot, (-0.06 * u, 0, 0.034 * u))
        shoe.rotation_euler = (0, -math.pi / 2, 0)       # lying along +x: heel behind the ankle, toes forward
        shoe.scale = (0.75, 1.0, 1.0)
        rig["legs"][side] = {"hip": hip, "knee": knee, "ankle": ankle, "foot": foot}
        shoulder = c.empty(coll, f"b2m_shoulder{side}", (0, y * 1.95, 0.46 * u), torso)
        c.capsule(coll, f"b2m_ball{side}", 0.055 * u, 0.055 * u, 0.11 * u, joint, shoulder, (0, 0, 0.055 * u))
        c.capsule(coll, f"b2m_upper{side}", 0.048 * u, 0.04 * u, 0.29 * u, body, shoulder)
        elbow = c.empty(coll, f"b2m_elbow{side}", (0, 0, -0.29 * u), shoulder)
        c.capsule(coll, f"b2m_elbowcap{side}", 0.042 * u, 0.042 * u, 0.084 * u, joint, elbow, (0, 0, 0.042 * u))
        c.capsule(coll, f"b2m_fore{side}", 0.04 * u, 0.032 * u, 0.26 * u, body, elbow)
        c.capsule(coll, f"b2m_hand{side}", 0.045 * u, 0.04 * u, 0.13 * u, body, elbow, (0, 0, -0.25 * u), squash=0.6)
        rig["arms"][side] = {"shoulder": shoulder, "elbow": elbow}
    return rig


def _key(obj, path, index, value, frame):
    vec = getattr(obj, path)
    vec[index] = value
    setattr(obj, path, vec)
    obj.keyframe_insert(path, index=index, frame=frame)


def _animate(rig, p):
    """Key every frame. Returns the targets and the largest IK overshoot, for the measurements."""
    l1, l2, fps, speed = float(p["thigh"]), float(p["shin"]), float(p["fps"]), float(p["speed"])
    hip_x = lambda k: speed * k / fps  # noqa: E731  (the hip's world x at frame index k)
    targets, worst = {"L": [], "R": []}, 0.0
    for f in range(1, int(p["frames"]) + 1):
        k = f - 1
        phase = (k / float(p["cycle_frames"])) % 1.0
        low = (float(p["duty"]) - 0.5) / 2                # the middle of the double support, when both feet are down
        hz = float(p["hip_height"]) - float(p["bob"]) * math.cos(2 * c.TAU * (phase - low))
        _key(rig["pelvis"], "location", 0, hip_x(k), f)
        _key(rig["pelvis"], "location", 2, hz, f)
        angles = {}
        for side, offset in (("L", 0.0), ("R", 0.5)):
            tx, tz = foot_target(k, offset, p, hip_x)
            t1, t2, over, reached = solve_leg((hip_x(k), hz), (tx, tz), l1, l2)
            worst = max(worst, over)
            targets[side].append(reached)
            leg = rig["legs"][side]
            _key(leg["hip"], "rotation_euler", 1, -t1, f)
            _key(leg["knee"], "rotation_euler", 1, -(t2 - t1), f)
            _key(leg["foot"], "rotation_euler", 1, t2, f)        # undo the shin's tilt: the sole stays flat
            angles[side] = t1
        for side, other in (("L", "R"), ("R", "L")):
            swing = angles[other] * float(p["arm_swing"])                          # the arm swings with the opposite leg
            _key(rig["arms"][side]["shoulder"], "rotation_euler", 1, -swing, f)
            _key(rig["arms"][side]["elbow"], "rotation_euler", 1, -(0.25 + 0.6 * max(0.0, swing)), f)   # bends more going forward
        _key(rig["torso"], "rotation_euler", 1, 0.06, f)                           # a slight forward lean
        _key(rig["torso"], "rotation_euler", 2, float(p["twist"]) * (angles["L"] - angles["R"]), f)  # chest turns with the arms
    c.set_interpolation(list(_ids(rig)), "LINEAR")
    return targets, worst


def _ids(rig):
    yield rig["pelvis"]
    yield rig["torso"]
    for leg in rig["legs"].values():
        yield from (leg["hip"], leg["knee"], leg["foot"])
    for arm in rig["arms"].values():
        yield from (arm["shoulder"], arm["elbow"])


def _ruler(coll, p, length):
    """A row of thin bars across the floor every half metre, so the travel is visible."""
    verts, faces = [], []
    for i in range(int(length / 0.5) + 4):
        x = -1.0 + i * 0.5
        base = len(verts)
        verts += [(x, -0.9, 0.002), (x + 0.02, -0.9, 0.002), (x + 0.02, 0.9, 0.002), (x, 0.9, 0.002)]
        faces.append((base, base + 1, base + 2, base + 3))
    bars = c.mesh_object(coll, "b2m_ruler", verts, faces)
    c.paint(bars, c.material("b2m_ruler", c.mix_hex(p["floor"], p["ink"], 0.22), roughness=0.8))


@c.keeps_selection
def build(params=None, clear=False):
    p = c.merged(DEFAULTS, params)
    if float(p["hip_height"]) + float(p["bob"]) >= float(p["thigh"]) + float(p["shin"]):
        raise ValueError(f"hip_height + bob ({float(p['hip_height']) + float(p['bob']):g}) must be under thigh + shin "
                         f"({float(p['thigh']) + float(p['shin']):g}), or the feet never reach the ground")
    if not 0.5 < float(p["duty"]) < 1.0:
        raise ValueError("duty must be between 0.5 and 1: a walk always has a foot on the ground")
    coll = c.begin("walk", clear)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, int(p["frames"])
    objs = c.stage(scene, coll, p, target=(0, 0, 0.72), cam=(1.4, -4.6, 1.5), lens=40)
    rig = _figure(coll, p)
    travel = float(p["speed"]) * (int(p["frames"]) - 1) / float(p["fps"])
    _ruler(coll, p, travel + 4)
    targets, worst = _animate(rig, p)
    aim, cam = objs["aim"], objs["camera"]            # the camera and lights ride the aim point, which follows the body
    if cam is not None and p["stage"]:
        cam.location = (0.7, -5.2, 0.6)              # relative to the orbit pivot, which sits on the aim
    for f in (1, int(p["frames"])):
        _key(aim, "location", 0, float(p["lead"]) + float(p["speed"]) * (f - 1) / float(p["fps"]), f)
    c.set_interpolation([aim], "LINEAR")
    c.caption(scene, coll, p["caption"], p, cam)
    return {"p": p, "scene": scene, "rig": rig, "targets": targets, "overshoot": worst}


def measure(state):
    scene, rig, p = state["scene"], state["rig"], state["p"]
    trace = {"L": [], "R": []}
    root, err = [], 0.0
    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        root.append(c.world_pos(rig["pelvis"]).x)
        for side in trace:
            a = c.world_pos(rig["legs"][side]["ankle"])
            trace[side].append((a.x, a.z))
            tx, tz = state["targets"][side][f - 1]
            err = max(err, math.hypot(a.x - tx, a.z - tz))
    slide, contact, plants, lift = 0.0, 0, [], 0.0
    for side, pts in trace.items():
        run: list = []
        for i, (x, z) in enumerate(pts):
            lift = max(lift, z)
            if z < 0.004:
                contact += 1
                slide = max(slide, abs(x - pts[i - 1][0]) if run else 0.0)
                run.append(x)
            elif run:
                plants.append((i - len(run), sum(run) / len(run)))
                run = []
    plants.sort()
    steps = [b[1] - a[1] for a, b in zip(plants, plants[1:])]
    result = {"root_distance": root[-1] - root[0], "contact_frames": contact, "max_slide_per_frame": slide,
              "min_foot_z": min(z for pts in trace.values() for _, z in pts), "max_foot_lift": lift,
              "max_leg_stretch": state["overshoot"], "max_ik_error": err, "plants": len(plants),
              "step_length": sum(steps) / len(steps) if steps else 0.0}
    problems = []
    if state["overshoot"] > 1e-6:      # the solver could not reach the plant: the foot floats or drags where slide is blind
        problems.append(f"the legs cannot reach the stride (max_leg_stretch {state['overshoot']:.3f} m): lower speed, "
                        "cycle_frames or hip_height, or lengthen the legs")
    if contact == 0 or len(plants) < 2:
        problems.append("the feet never plant on the ground, so the slide check saw nothing: lower hip_height")
    return c.verdict(result, problems)


if __name__ == "__main__":
    c.run_main("walk", DEFAULTS, __doc__.split("\n")[0], build, measure)
