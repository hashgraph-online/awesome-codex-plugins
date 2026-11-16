"""b2m3d physics: prepare a scene (hulls from GLB nodes) and bake it with Jolt (WASM)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import trimesh

from .glbio import readable
from .run import last_json, node_script

MAX_HULL_POINTS = 200


def hull_points(glb: Path, node: str | None, max_points: int = MAX_HULL_POINTS) -> list[list[float]]:
    """Convex-hull vertices of one node (or the whole file) in metres, in the model's own space."""
    scene = trimesh.load(readable(glb), force="scene")
    meshes = []
    for name in scene.graph.nodes_geometry:
        if node is None or name == node or name.split("/")[-1] == node:
            xf, geom = scene.graph[name]
            meshes.append(scene.geometry[geom].copy().apply_transform(xf))
    if not meshes:
        raise KeyError(f"node {node!r} not found in {glb}")
    pts = np.asarray(trimesh.util.concatenate(meshes).convex_hull.vertices)
    if len(pts) > max_points:
        pts = pts[np.linspace(0, len(pts) - 1, max_points).astype(int)]
    return pts.round(6).tolist()


def prepare(scene: dict, base: Path) -> dict:
    bodies = []
    for b in scene["bodies"]:
        if b.get("shape") == "hull" and "points" not in b:
            b = {**b, "points": hull_points((base / b["glb"]).resolve(), b.get("node"))}
        bodies.append(b)
    return {**scene, "bodies": bodies}


def bake(scene_path: Path, out: Path) -> dict:
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    ready = prepare(scene, scene_path.parent)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(ready, fh)
        tmp = Path(fh.name)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        return last_json(node_script("jolt_bake.mjs", [str(tmp), str(out)]), "B2M3D_PHYSICS")
    finally:
        tmp.unlink(missing_ok=True)
