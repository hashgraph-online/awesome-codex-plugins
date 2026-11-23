"""b2m_rigid: rigid bodies held together by constraints: a hinged chain that swings (links=1 is a pendulum).

A fixed anchor and `links` boxes. Each joint is an empty with a rigid-body constraint (hinge: swings about the
Y axis, so the chain stays in one plane; point: a ball joint, free in every direction). The chain is released
from release_angle degrees and falls under gravity. The result reports how far any joint opened, how far the
tip travelled and, for a pendulum, its period, so a script can tell a held joint from a broken one.

  blender -b --factory-startup -P b2m_rigid.py -- --links 6 --joint hinge --release-angle 80 --out frames
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

import b2m_common as c  # noqa: E402

DEFAULTS = {
    "frames": 120,
    "links": 5,
    "link_length": 0.5,     # metres
    "link_width": 0.12,
    "joint": "hinge",       # hinge or point
    "release_angle": 70.0,  # degrees from straight down, toward +X
    "mass": 1.0,            # kilograms per link
    "damping": 0.02,        # linear and angular damping; 0 swings forever
    "anchor_height": 2.6,
    "stand": True,          # a post and arm that hold the anchor, so the chain does not hang from nothing (looks only)
    "rounded": True,        # links drawn as rounded bars with a pin at each joint; the physics shape stays a box
}


def _box(coll, name, w, d, h, loc, rot_y=0.0):
    x, y, z = w / 2, d / 2, h / 2
    verts = [(sx * x, sy * y, sz * z) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    obj = c.mesh_object(coll, name, verts, faces, loc)
    obj.rotation_euler = (0, rot_y, 0)
    return obj


def _frame(top, total, theta, lens, ratio, sensor=36.0):
    """Aim and camera that keep the whole swing in frame: the arc reaches total to each side of the anchor and down
    to top - total; the frame keeps a margin all round and extra room at the bottom for a caption."""
    reach = total * max(math.sin(theta), 0.75)
    lo, hi = max(0.0, top - total) - 0.15, top + 0.35
    half_w, half_h = reach * 1.12, (hi - lo) / 2 * 1.12
    tan_w = sensor / 2 / lens
    dist = max(half_w / tan_w, half_h / (tan_w / ratio)) + 0.6
    mid = (lo + hi) / 2 - 0.08 * half_h
    return (0.0, 0.0, mid), (0.0, -dist, mid + 0.12 * dist)


def _rounded_link(coll, name, w, length, mid, rot_y, mat, pin):
    """A rounded bar with the same size as the box the physics uses, and a pin through the joint nearer the anchor."""
    obj = c.capsule(coll, name, w / 2, w / 2, length, mat)
    for v in obj.data.vertices:
        v.co.z += length / 2                     # centre it on its origin, like the box
    obj.location, obj.rotation_euler = mid, (0, rot_y, 0)
    peg = c.capsule(coll, name + "_pin", w * 0.32, w * 0.32, w * 1.5, pin, parent=obj, loc=(0, w * 0.75, -length / 2))
    peg.rotation_euler = (-math.pi / 2, 0, 0)
    return obj


def _stand(coll, top, mat):
    """A post behind the swing plane and an arm over to the anchor."""
    c.capsule(coll, "b2m_post", 0.05, 0.05, top + 0.25, mat, loc=(0, 0.45, top + 0.25))
    arm = c.capsule(coll, "b2m_arm", 0.04, 0.04, 0.5, mat, loc=(0, 0.5, top + 0.12))
    arm.rotation_euler = (-math.pi / 2, 0, 0)    # from the post toward the swing plane
    base = c.capsule(coll, "b2m_base", 0.28, 0.28, 0.56, mat, loc=(0, 0.45, 0.04))
    base.scale = (1, 1, 0.07)                    # a flat disc on the floor


def _activate(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def _body(obj, passive, p):
    _activate(obj)
    bpy.ops.rigidbody.object_add()
    rb = obj.rigid_body
    rb.type = "PASSIVE" if passive else "ACTIVE"
    rb.collision_shape = "BOX"
    rb.mass = float(p["mass"])
    rb.linear_damping = rb.angular_damping = float(p["damping"])


def _joint(coll, name, pivot, a, b, kind):
    e = c.empty(coll, name, pivot, size=0.12)
    if kind == "hinge":
        e.rotation_euler = (math.pi / 2, 0, 0)        # a hinge turns about its own Z axis: point that at world Y
    _activate(e)
    bpy.ops.rigidbody.constraint_add(type="HINGE" if kind == "hinge" else "POINT")
    con = e.rigid_body_constraint
    con.object1, con.object2, con.disable_collisions = a, b, True
    return e


def _check(p) -> None:
    if p["joint"] not in ("hinge", "point"):
        raise ValueError("joint must be hinge or point")
    n, length, width, top = int(p["links"]), float(p["link_length"]), float(p["link_width"]), float(p["anchor_height"])
    if n < 1 or length < 2 * width:
        raise ValueError(f"links must be at least 1 and link_length ({length:g}) at least twice link_width ({width:g}): "
                         "shorter links overlap at the joints and the chain jitters apart")
    if n * length + width >= top:
        raise ValueError(f"the chain hangs {n * length + width:g} m (links x link_length + link_width) from an anchor "
                         f"{top:g} m up, so it would swing through the floor: raise anchor_height above {n * length + width:g} "
                         "or shorten the chain")


@c.keeps_selection
def build(params=None, clear=False):
    p = c.merged(DEFAULTS, params)
    _check(p)
    coll = c.begin("rigid", clear)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, int(p["frames"])
    n, length, width = int(p["links"]), float(p["link_length"]), float(p["link_width"])
    top = float(p["anchor_height"])
    theta = math.radians(float(p["release_angle"]))
    target, cam = _frame(top, n * length, theta, 40.0, float(p["width"]) / float(p["height"]))
    objs = c.stage(scene, coll, p, target=target, cam=cam, lens=40)   # the whole swing in frame, the anchor included
    if scene.rigidbody_world is None:
        bpy.ops.rigidbody.world_add()
    world = scene.rigidbody_world
    world.substeps_per_frame, world.solver_iterations = 20, 60
    world.point_cache.frame_start, world.point_cache.frame_end = 1, int(p["frames"])
    d = (math.sin(theta), 0.0, -math.cos(theta))
    anchor = _box(coll, "b2m_anchor", 0.3, 0.3, 0.1, (0, 0, top))
    metal = c.material("b2m_anchor", p["ink"], roughness=0.35, metallic=0.6)
    c.paint(anchor, metal)
    _body(anchor, True, p)
    if p["stand"]:
        _stand(coll, top, metal)
    links, prev = [], anchor
    for i in range(n):
        mid = tuple(float(top * (k == 2)) + d[k] * (i + 0.5) * length for k in range(3))
        mat = c.material(f"b2m_link{i}", p["subject"] if i % 2 == 0 else p["accent"], roughness=0.3, metallic=0.2, coat=0.6)
        if p["rounded"]:
            link = _rounded_link(coll, f"b2m_link{i}", width, length, mid, math.pi - theta, mat, metal)
        else:
            link = _box(coll, f"b2m_link{i}", width, width, length, mid, math.pi - theta)
            c.paint(link, mat)
        _body(link, False, p)
        pivot = tuple(float(top * (k == 2)) + d[k] * i * length for k in range(3))
        _joint(coll, f"b2m_joint{i}", pivot, prev, link, p["joint"])
        links.append(link)
        prev = link
    c.caption(scene, coll, p["caption"], p, objs["camera"])
    return {"p": p, "scene": scene, "anchor": anchor, "links": links, "length": length, "top": top}


def _trace(state):
    """Step the simulation once, recording joint gaps, the tip's x and y, the first link's angle, and the smallest
    distance from any joint to the frame edge as a share of the frame (negative: something left the frame)."""
    scene, anchor, links, length = state["scene"], state["anchor"], state["links"], state["length"]
    gaps, tip_x, off_plane, angle, margin, low = [], [], [], [], 1.0, float("inf")
    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        far = [c.world_pos(anchor)] + [c.world_pos(lk, (0, 0, length / 2)) for lk in links]
        if scene.camera is not None:                # how close any joint or the tip comes to the frame edge (0..1)
            for pt in far:
                u = world_to_camera_view(scene, scene.camera, pt)
                margin = min(margin, u.x, 1 - u.x, u.y, 1 - u.y)
        near = [c.world_pos(lk, (0, 0, -length / 2)) for lk in links]
        low = min(low, min(pt.z for pt in far + near))
        gaps.append(max((a - b).length for a, b in zip(far, near)))
        tip_x.append(far[-1].x)
        off_plane.append(max(abs(c.world_pos(lk).y) for lk in links))
        first = far[1] - far[0]
        angle.append(math.atan2(first.x, -first.z))
    return gaps, tip_x, off_plane, angle, margin, low


def _period(angle, fps):
    """Mean time between successive downward zero crossings of the first link's angle, in seconds."""
    times = [(i + angle[i] / (angle[i] - angle[i + 1])) / fps for i in range(len(angle) - 1) if angle[i] > 0 >= angle[i + 1]]
    return sum(b - a for a, b in zip(times, times[1:])) / (len(times) - 1) if len(times) >= 2 else None


def measure(state):
    gaps, tip_x, off_plane, angle, margin, low = _trace(state)
    result = {"frame_margin": margin, "constraints": len(state["links"]), "max_joint_gap": max(gaps),
              "tip_travel_x": max(tip_x) - min(tip_x), "max_out_of_plane": max(off_plane), "min_z": low,
              "period_s": _period(angle, state["scene"].render.fps / state["scene"].render.fps_base)}
    problems = []
    if margin < 0:
        problems.append(f"the swing leaves the frame (frame_margin {margin:.3f}): fewer links, a smaller release_angle, "
                        "or a wider lens")
    if low < 0:
        problems.append(f"a link end reaches z = {low:.3f}, below the floor")
    if max(gaps) > 0.05 * state["length"]:
        problems.append(f"a joint opened {max(gaps):.4f} m, over 5% of a link: raise substeps or lower the mass ratio")
    return c.verdict(result, problems)


if __name__ == "__main__":
    c.run_main("rigid", DEFAULTS, __doc__.split("\n")[0], build, measure)
