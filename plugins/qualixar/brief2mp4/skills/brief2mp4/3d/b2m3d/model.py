"""b2m3d model: run a parametric spec (CadQuery / Manifold / trimesh) and write a GLB.

Spec contract: a Python file with ``build(params: dict)`` returning any of
  manifold3d.Manifold, trimesh.Trimesh, trimesh.Scene, cadquery Workplane / Shape / Assembly
  (CadQuery is the optional ``cad`` component), or a list of Part dicts
  {"name", "geom", "color", "metallic", "roughness"}.
The file may also set PARAMS (defaults), UNITS ("mm" | "cm" | "m") and UP ("z" | "y").
CAD convention is millimetres, Z-up; glTF is metres, Y-up. ``units``/``up`` convert.
Colours in a Part are LINEAR RGBA (see README-3D.md for the sRGB conversion).
"""
from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from .run import B2M3DError

Z_UP_TO_Y_UP = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
UNIT_SCALE = {"mm": 0.001, "cm": 0.01, "m": 1.0}
DEFAULT_COLOR = (0.8, 0.8, 0.82, 1.0)


@dataclass(frozen=True)
class Part:
    name: str
    mesh: trimesh.Trimesh
    color: tuple[float, float, float, float] = DEFAULT_COLOR
    metallic: float = 0.0
    roughness: float = 0.5


def load_spec(path: Path):
    spec = importlib.util.spec_from_file_location(f"b2m3d_spec_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import spec {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise ValueError(f"{path} must define build(params)")
    return mod


def _cq_shape_to_mesh(shape: Any, tol: float) -> trimesh.Trimesh:
    verts, tris = shape.tessellate(tol, 0.2)
    v = np.array([(p.x, p.y, p.z) for p in verts], dtype=np.float64)
    f = np.array(tris, dtype=np.int64)
    return trimesh.Trimesh(v, f, process=False)


def _cq_to_parts(obj: Any, name: str, tol: float) -> list[Part]:
    try:
        import cadquery as cq
    except ImportError as exc:
        raise B2M3DError("this spec returns a CadQuery object but the `cad` component is not "
                         "installed (run `python -m b2m3d doctor` for the command)") from exc
    if isinstance(obj, cq.Assembly):
        parts = []
        for shape, pname, loc, color in obj:  # flattened traversal
            moved = shape.moved(loc) if loc is not None else shape
            rgba = tuple(color.toTuple()) if color is not None else DEFAULT_COLOR
            parts.append(Part(pname or name, _cq_shape_to_mesh(moved, tol), rgba))
        return parts
    if isinstance(obj, cq.Workplane):
        shapes = [s for s in obj.vals() if isinstance(s, cq.Shape)]
        obj = cq.Compound.makeCompound(shapes)
    return [Part(name, _cq_shape_to_mesh(obj, tol))]


def _manifold_to_mesh(m: Any) -> trimesh.Trimesh:
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    return trimesh.Trimesh(v, f, process=False)


def _dict_part(item: dict, tol: float, name: str, index: int) -> list[Part]:
    pname = item.get("name", f"{name}_{index}")
    base = to_parts(item["geom"], tol, pname)
    return [Part(pname if len(base) == 1 else p.name, p.mesh,
                 tuple(item.get("color", p.color)),
                 float(item.get("metallic", p.metallic)),
                 float(item.get("roughness", p.roughness))) for p in base]


def to_parts(obj: Any, tol: float = 0.05, name: str = "part") -> list[Part]:
    if isinstance(obj, list):
        out: list[Part] = []
        for i, item in enumerate(obj):
            out += _dict_part(item, tol, name, i) if isinstance(item, dict) else to_parts(item, tol, f"{name}_{i}")
        return out
    if isinstance(obj, trimesh.Trimesh):
        return [Part(name, obj)]
    if isinstance(obj, trimesh.Scene):
        return [Part(m.metadata.get("name", f"{name}_{i}"), m) for i, m in enumerate(obj.dump())]
    module = type(obj).__module__
    if module.startswith("manifold3d"):
        return [Part(name, _manifold_to_mesh(obj))]
    if module.startswith(("cadquery", "OCP")):
        return _cq_to_parts(obj, name, tol)
    raise TypeError(f"build() returned unsupported type {type(obj)!r}")


def _material(p: Part) -> trimesh.visual.material.PBRMaterial:
    rgba = [int(round(c * 255)) for c in (list(p.color) + [1.0])[:4]]
    return trimesh.visual.material.PBRMaterial(
        name=f"{p.name}_mat", baseColorFactor=rgba,
        metallicFactor=p.metallic, roughnessFactor=p.roughness)


def write_glb(parts: list[Part], out: Path, units: str = "mm", up: str = "z",
              smooth_angle: float | None = None) -> dict:
    scene = trimesh.Scene()
    xf = np.eye(4)
    xf[:3, :3] *= UNIT_SCALE[units]
    if up == "z":
        xf = Z_UP_TO_Y_UP @ xf
    for p in parts:
        mesh = p.mesh.copy()
        mesh.apply_transform(xf)
        if smooth_angle is not None:
            mesh = trimesh.graph.smooth_shade(mesh, angle=np.radians(smooth_angle))
        _ = mesh.vertex_normals  # cache them: they are only exported when cached, and three.js goes flat-shaded without
        mesh.visual = trimesh.visual.TextureVisuals(material=_material(p))
        scene.add_geometry(mesh, node_name=p.name, geom_name=p.name)
    out.parent.mkdir(parents=True, exist_ok=True)
    scene.export(out)
    lo, hi = scene.bounds
    return {"out": str(out), "parts": len(parts),
            "triangles": int(sum(len(p.mesh.faces) for p in parts)),
            "bounds_m": [lo.round(4).tolist(), hi.round(4).tolist()]}


def build(spec_path: Path, out: Path, params: dict | None = None, units: str = "mm",
          up: str = "z", tol: float = 0.05, smooth_angle: float | None = None) -> dict:
    mod = load_spec(spec_path)
    defaults = getattr(mod, "PARAMS", {})
    result = mod.build({**defaults, **(params or {})})
    parts = to_parts(result, tol, spec_path.stem)
    return write_glb(parts, out, getattr(mod, "UNITS", units), getattr(mod, "UP", up), smooth_angle)


def parse_params(raw: list[str]) -> dict:
    out: dict = {}
    for item in raw:
        key, sep, val = item.partition("=")
        if not sep:
            raise ValueError(f"--param expects key=value, got {item!r}")
        try:
            out[key] = json.loads(val)
        except json.JSONDecodeError:
            out[key] = val
    return out
