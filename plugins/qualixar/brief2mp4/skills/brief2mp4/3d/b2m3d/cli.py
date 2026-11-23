"""b2m3d: the optional 3D pack for brief2mp4. Every subcommand prints one JSON result."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .run import B2M3DError, last_json, node_script

P = Path


def _model(a):
    from . import model
    return model.build(P(a.spec), P(a.out), model.parse_params(a.param), a.units, a.up, a.tol, a.smooth)


def _optimize(a):
    args = [a.src, a.out, "--simplify", str(a.simplify), "--error", str(a.error)]
    args += ["--join"] if a.join else []
    args += ["--no-compress"] if a.no_compress else []
    return last_json(node_script("optimize.mjs", args), "B2M3D_OPTIMIZE")


def _material(a):
    from . import material
    if a.action == "presets":
        presets = material.load_presets()
        return {"presets": {n: p.get("description", "") for n, p in presets.items()}}
    if a.action == "linear":
        return {"srgb": a.src, "linear": material.srgb_to_linear(a.src)}
    if not (a.src and a.out):
        raise ValueError("material assign needs: in.glb out.glb --assign name=preset")
    return material.assign(P(a.src), P(a.out), material.parse_assignments(a.assign))


def _physics(a):
    from . import physics
    return physics.bake(P(a.scene), P(a.out))


def _hf(a):
    from . import hf
    return hf.scaffold(P(a.shot), P(a.out))


def _blender(a):
    from . import blender
    cfg = json.loads(a.config) if a.config else {}
    given = {"frames": a.frames, "fps": a.fps, "width": a.width, "height": a.height, "engine": a.engine,
             "samples": a.samples, "look": a.look, "transparent": a.transparent or None,
             "save_blend": a.save_blend}
    cfg.update({k: v for k, v in given.items() if v is not None})
    return blender.render(P(a.src), P(a.out_dir), mp4=P(a.mp4) if a.mp4 else None, **cfg)


def _recipe(a):
    from . import recipes
    if a.action == "list":
        return {"recipes": recipes.available()}
    if not a.name:
        raise ValueError("recipe run needs a name: b2m3d recipe run loop -- --loop-frames 73")
    return recipes.run_recipe(a.name, a.args)


def _doctor(_a):
    from . import doctor
    return doctor.run_all()


def _add_model(sub) -> None:
    s = sub.add_parser("model", help="parametric spec (CadQuery, Manifold or trimesh) -> GLB")
    s.add_argument("spec"); s.add_argument("out")
    s.add_argument("--param", action="append", default=[], help="key=value (JSON values ok)")
    s.add_argument("--units", default="mm", choices=["mm", "cm", "m"])
    s.add_argument("--up", default="z", choices=["z", "y"])
    s.add_argument("--tol", type=float, default=0.05, help="CAD tessellation tolerance (spec units)")
    s.add_argument("--smooth", type=float, default=None, help="smooth-shade angle in degrees")
    s.set_defaults(fn=_model)


def _add_assets(sub) -> None:
    s = sub.add_parser("optimize", help="glTF Transform + meshoptimizer (dedup, weld, simplify, compress)")
    s.add_argument("src"); s.add_argument("out")
    s.add_argument("--simplify", type=float, default=1.0, help="keep ratio, e.g. 0.5")
    s.add_argument("--error", type=float, default=0.001)
    s.add_argument("--join", action="store_true", help="merge meshes (breaks per-part explode)")
    s.add_argument("--no-compress", action="store_true", help="skip EXT_meshopt_compression")
    s.set_defaults(fn=_optimize)

    s = sub.add_parser("material", help="material presets -> glTF PBR materials")
    s.add_argument("action", choices=["presets", "assign", "linear"])
    s.add_argument("src", nargs="?", help="assign: in.glb; linear: '#rrggbb'")
    s.add_argument("out", nargs="?")
    s.add_argument("--assign", action="append", default=[], help="node=preset|file.json ('*' = all)")
    s.set_defaults(fn=_material)

    s = sub.add_parser("physics", help="bake a Jolt rigid-body scene to per-frame tracks")
    s.add_argument("scene"); s.add_argument("out")
    s.set_defaults(fn=_physics)


def _add_render(sub) -> None:
    s = sub.add_parser("hf", help="shot JSON -> self-contained HyperFrames project")
    s.add_argument("shot"); s.add_argument("out")
    s.set_defaults(fn=_hf)

    s = sub.add_parser("blender", help="Blender Cycles/EEVEE render -> PNG frames (+ video)")
    s.add_argument("src"); s.add_argument("out_dir")
    s.add_argument("--mp4"); s.add_argument("--frames", type=int); s.add_argument("--fps", type=int)
    s.add_argument("--width", type=int); s.add_argument("--height", type=int)
    s.add_argument("--engine", choices=["cycles", "eevee"]); s.add_argument("--samples", type=int)
    s.add_argument("--look", choices=["studio", "dramatic", "soft"])
    s.add_argument("--transparent", action="store_true", help="alpha output (ProRes 4444 .mov)")
    s.add_argument("--save-blend"); s.add_argument("--config", help="extra JSON config")
    s.set_defaults(fn=_blender)

    s = sub.add_parser("recipe", help="Blender motion recipes (loop, retime, cloth, rigid, fold, walk): list, or run one headless")
    s.add_argument("action", choices=["list", "run"])
    s.add_argument("name", nargs="?")
    s.add_argument("args", nargs=argparse.REMAINDER, help="options for the recipe, after --")
    s.set_defaults(fn=_recipe)

    s = sub.add_parser("doctor", help="report each component as ok or missing, with install commands")
    s.set_defaults(fn=_doctor)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="b2m3d", description="Optional 3D pack for brief2mp4: model, "
                                 "material, optimize, physics, HyperFrames shot, Blender render, Blender motion recipes, doctor.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add_model(sub)
    _add_assets(sub)
    _add_render(sub)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.fn(args)
    except (B2M3DError, ValueError, KeyError, FileNotFoundError, TypeError, RuntimeError, ImportError) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, default=str))
    if args.cmd == "doctor":
        return 0  # a report, not a check: the JSON carries ok/missing
    return 0 if result.get("ok", True) else 2
