"""b2m_fold: a sheet folds in half, then again, with shape keys.

Each fold is a short chain of shape keys, one per slice of the turn (fold_steps slices of 180 degrees in all),
and each key is relative to the one before it. Blender blends vertex positions in a straight line, so a single
key from flat to folded would squash the sheet; with a key every 30 degrees the free edge swings along the arc.
The crease is rounded over crease_radius, capped at 6 percent of the stack's width so later folds of a shrinking
stack keep their proportion (the sheet stretches a little there; area_ratio reports by how much and a smaller radius
with a larger grid_x is crisper). Folded layers stack layer_gap apart so they never touch, no crease point dips under
the layer it started on, and the slices are timed with a smooth ease so the fold starts and ends gently.

  blender -b --factory-startup -P b2m_fold.py -- --folds 3 --fold-frames 30 --out frames
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import b2m_common as c  # noqa: E402
from b2m_math import crease_radius, fold_positions  # noqa: E402  (pure functions, tested without Blender)

DEFAULTS = {
    "folds": 2,             # each fold halves the width of the current stack
    "sheet_width": 2.0,
    "sheet_height": 1.2,
    "grid_x": 64,           # vertex columns across the width; keep it even so a vertex sits on the first crease
    "grid_y": 8,
    "fold_frames": 30,      # frames for one fold
    "fold_steps": 6,        # shape keys per fold: 6 means a key every 30 degrees
    "pause": 8,             # frames between folds, and flat at the start and folded at the end
    "crease_radius": 0.06,  # how far the bend spreads on each side of the crease
    "layer_gap": 0.01,      # thickness of one layer of paper, in metres
    "back": "",             # colour of the underside (hex); empty means the same as the top, like plain paper
    "thickness": 0.0,       # render-only thickness of the sheet (a Solidify), under layer_gap; 0 = a bare surface
    "follow": True,         # the camera eases over to the stack and closes in as it halves, during each fold
}


def _paper(sheet, p):
    """Top colour, and the underside's own colour when `back` is set: that side shows wherever a fold turns it up.
    With thickness the underside is the Solidify shell; without it, a Backfacing switch in one material."""
    top = c.material("b2m_sheet", p["subject"], roughness=0.8)
    c.paint(sheet, top)
    thick = float(p["thickness"])
    if p["back"] and thick > 0:
        sheet.data.materials.append(c.material("b2m_sheet_back", p["back"], roughness=0.8))
    elif p["back"]:
        nodes, links = top.node_tree.nodes, top.node_tree.links
        bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        geo, mix = nodes.new("ShaderNodeNewGeometry"), nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        ins = {s.identifier: s for s in mix.inputs}               # by identifier: the colour sockets, never the float ones
        ins["A_Color"].default_value, ins["B_Color"].default_value = c.hex_rgba(p["subject"]), c.hex_rgba(p["back"])
        links.new(geo.outputs["Backfacing"], ins["Factor_Float"])
        links.new(next(o for o in mix.outputs if o.identifier == "Result_Color"), bsdf.inputs["Base Color"])
    if thick > 0:
        solid = sheet.modifiers.new("Thickness", "SOLIDIFY")    # render only: the measured shape keys are untouched
        solid.show_viewport, solid.thickness, solid.offset = False, thick, -1.0
        solid.material_offset = 1 if p["back"] else 0             # the new shell takes the underside colour


def _grid(p):
    nx, ny, w, h = int(p["grid_x"]), int(p["grid_y"]), float(p["sheet_width"]), float(p["sheet_height"])
    verts = [(-w / 2 + w * i / nx, -h / 2 + h * j / ny, 0.0) for j in range(ny + 1) for i in range(nx + 1)]
    faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
    return verts, faces


def _fold_keys(sheet, verts, p):
    """Add the shape-key chain. Returns (keys per fold, zone vertices, crease x per fold, axis z per fold)."""
    gap, steps = float(p["layer_gap"]), int(p["fold_steps"])
    sheet.shape_key_add(name="Basis", from_mix=False)
    prev, cur, zone, per_fold, creases, axes = sheet.data.shape_keys.key_blocks["Basis"], list(verts), set(), [], [], []
    for k in range(int(p["folds"])):
        xs = [v[0] for v in cur]
        crease = (min(xs) + max(xs)) / 2
        radius = crease_radius(float(p["crease_radius"]), max(xs) - min(xs))   # in proportion to the shrinking stack
        axis = max(v[2] for i, v in enumerate(cur) if i not in zone) + gap / 2   # above the flat layers, so the turning part clears them
        creases.append(crease)
        axes.append(axis)
        keys = []
        for s in range(1, steps + 1):
            pos, z_k = fold_positions(cur, crease, axis, s / steps, radius)
            zone |= z_k
            key = sheet.shape_key_add(name=f"fold{k + 1}_{s}", from_mix=False)
            key.relative_key = prev
            for vert, co in zip(key.data, pos):
                vert.co = co
            keys.append(key)
            prev = key
        cur, _ = fold_positions(cur, crease, axis, 1.0, radius)
        per_fold.append(keys)
    return per_fold, zone, creases, axes


def _animate(per_fold, p):
    """Key each slice's value 0 -> 1 in its own span of frames; the spans follow a smooth ease. Returns the frame range."""
    frame = 1 + int(p["pause"])
    steps, span = int(p["fold_steps"]), int(p["fold_frames"])
    starts = []
    for keys in per_fold:
        starts.append(frame)
        for s, key in enumerate(keys):
            t0, t1 = frame + span * c.smoothstep(s / steps), frame + span * c.smoothstep((s + 1) / steps)
            key.value = 0.0
            key.keyframe_insert("value", frame=t0)
            key.value = 1.0
            key.keyframe_insert("value", frame=t1)
        frame += span + int(p["pause"])
    c.set_interpolation([per_fold[0][0].id_data], "LINEAR")
    return frame, starts


@c.keeps_selection
def build(params=None, clear=False):
    p = c.merged(DEFAULTS, params)
    if p["folds"] < 1 or p["fold_steps"] < 6:
        raise ValueError("folds must be at least 1 and fold_steps at least 6: a shape key blends in a straight line, so "
                         "a key every 60 degrees (3 steps) squashes the half-fold edge by 13 percent, every 30 degrees by 3")
    if p["layer_gap"] <= 0 or p["crease_radius"] <= 0:
        raise ValueError("layer_gap and crease_radius must be above 0: with no gap the folded layers z-fight")
    k, gap = int(p["folds"]), float(p["layer_gap"])
    if (2 ** k - 1) * gap > float(p["sheet_width"]) / 2 ** k / 2:
        raise ValueError(f"{k} folds at layer_gap {gap:g} make a stack {(2 ** k - 1) * gap:g} m thick on a "
                         f"{float(p['sheet_width']) / 2 ** k:g} m wide sheet, thicker than half its width: lower layer_gap")
    coll = c.begin("fold", clear)
    scene = bpy.context.scene
    objs = c.stage(scene, coll, p, target=(0, 0, 0.2), cam=(0, -5.2, 3.1), lens=45)   # room above for the rising flap
    verts, faces = _grid(p)
    sheet = c.mesh_object(coll, "b2m_sheet", verts, faces, (0, 0, float(p["layer_gap"])))
    for poly in sheet.data.polygons:
        poly.use_smooth = True
    _paper(sheet, p)
    per_fold, zone, creases, axes = _fold_keys(sheet, verts, p)
    end, starts = _animate(per_fold, p)
    scene.frame_start, scene.frame_end = 1, end
    if p["follow"] and p["stage"]:
        _follow(objs["aim"], objs["camera"], creases, starts, -float(p["sheet_width"]) / 2, int(p["fold_frames"]))
    c.caption(scene, coll, p["caption"], p, objs["camera"])
    return {"p": p, "sheet": sheet, "scene": scene, "zone": zone, "starts": starts, "creases": creases,
            "axes": axes, "flat": verts}


def _follow(aim, cam, creases, starts, left, span):
    """During each fold, ease the aim to the middle of the stack it leaves and bring the camera in by the same share
    as the width shrinks (to 0.82 of the distance per fold), so the subject keeps its place and size in frame."""
    offset, height = tuple(cam.location), aim.location.z
    centre, scale = 0.0, 1.0
    for crease, start in zip(creases, starts):
        for frame, x, k in ((start, centre, scale), (start + span, (left + crease) / 2, scale * 0.82)):
            aim.location.x, aim.location.z = x, height * k
            aim.keyframe_insert("location", frame=frame)
            cam.location = tuple(v * k for v in offset)
            cam.keyframe_insert("location", frame=frame)
        centre, scale = (left + crease) / 2, scale * 0.82


def _evaluated(sheet):
    ev = sheet.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    pts, area = [tuple(v.co) for v in mesh.vertices], sum(f.area for f in mesh.polygons)
    ev.to_mesh_clear()
    return pts, area


def _extent(pts, axis):
    vals = [q[axis] for q in pts]
    return max(vals) - min(vals)


WIDTH_TOLERANCE = 0.08   # final width within 8 percent of width / 2**folds
AREA_LIMIT = 1.20        # the creases may stretch the sheet by at most 20 percent (a thick stack wraps, so it stretches)


def expected_width(p) -> float:
    """width / 2**folds, plus the bulge of the last crease, which wraps the folded stack: half its final thickness."""
    k = int(p["folds"])
    return float(p["sheet_width"]) / 2 ** k + (2 ** k - 1) * float(p["layer_gap"]) / 2


def measure(state):
    scene, sheet, p = state["scene"], state["sheet"], state["p"]
    scene.frame_set(1)
    flat, flat_area = _evaluated(sheet)
    lowest = min(q[2] for q in flat)
    half_frame = state["starts"][0] + int(p["fold_frames"]) // 2
    for f in range(scene.frame_start, scene.frame_end + 1):       # every frame: the crease must never dip under the sheet
        scene.frame_set(f)
        pts, _ = _evaluated(sheet)
        lowest = min(lowest, min(q[2] for q in pts))
        if f == half_frame:
            half = pts
    final, final_area = _evaluated(sheet)
    levels = sorted({round(q[2], 5) for i, q in enumerate(final) if i not in state["zone"]})
    free_edge = max(range(len(state["flat"])), key=lambda i: state["flat"][i][0])
    expected = expected_width(p)
    result = {"flat_width": _extent(flat, 0), "flat_thickness": _extent(flat, 2), "final_width": _extent(final, 0),
              "expected_width": expected, "final_height": _extent(final, 1), "final_thickness": levels[-1] - levels[0],
              "layer_gap": float(p["layer_gap"]), "layers": len(levels),
              "min_layer_separation": min((b - a for a, b in zip(levels, levels[1:])), default=0.0),
              "half_fold_edge_z": half[free_edge][2],
              "half_fold_expected_z": (state["flat"][free_edge][0] - state["creases"][0]) + state["axes"][0],
              "area_ratio": final_area / flat_area, "shape_keys": len(sheet.data.shape_keys.key_blocks),
              "min_z": lowest + sheet.matrix_world.translation.z, "min_local_z": lowest}
    problems = []
    if abs(result["final_width"] / expected - 1) > WIDTH_TOLERANCE:
        problems.append(f"final width {result['final_width']:.3f} m is not within {WIDTH_TOLERANCE:.0%} of {expected:.3f} m: "
                        "lower crease_radius or raise grid_x")
    if result["area_ratio"] > AREA_LIMIT:
        problems.append(f"the creases stretch the sheet {result['area_ratio'] - 1:.0%} (limit {AREA_LIMIT - 1:.0%}): "
                        "lower crease_radius or raise grid_x")
    if lowest < -1e-6:
        problems.append(f"a crease dips {-lowest * 1000:.1f} mm under the bottom layer")
    return c.verdict(result, problems)


if __name__ == "__main__":
    c.run_main("fold", DEFAULTS, __doc__.split("\n")[0], build, measure)
