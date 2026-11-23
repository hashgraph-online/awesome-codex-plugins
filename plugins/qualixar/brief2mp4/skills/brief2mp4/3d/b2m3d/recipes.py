"""b2m3d recipe: the Blender motion recipes (loop, retime, cloth, rigid, fold, walk, flip_bake) run headless.

`recipe list` needs no Blender. `recipe run NAME -- <recipe options>` runs templates/recipes/b2m_NAME.py in the
system Blender and returns the recipe's own result JSON (its measurements, and the frames it wrote).
"""
from __future__ import annotations

import ast
from pathlib import Path

from . import paths
from .run import B2M3DError, last_json, run

MARKER = "B2M3D_RECIPE"
HELPERS = {"common", "math"}     # b2m_common.py and b2m_math.py are shared helpers, not recipes


def folder() -> Path:
    return paths.TEMPLATES / "recipes"


def available() -> list[dict]:
    """Every b2m_<name>.py, with the first line of its docstring (read without importing: it needs bpy)."""
    found = []
    for path in sorted(folder().glob("b2m_*.py")):
        name = path.stem.removeprefix("b2m_")
        if name in HELPERS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        doc = ast.get_docstring(tree) or ""
        factory = next((n.value.value for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                        and n.targets[0].id == "FACTORY_STARTUP"), True)     # a recipe that needs the user's add-ons says False
        found.append({"name": name, "summary": doc.splitlines()[0].removeprefix(f"b2m_{name}: "), "script": str(path),
                      "factory_startup": factory})
    return found


def run_recipe(name: str, args: list[str], timeout: int = 7200) -> dict:
    known = {r["name"]: r for r in available()}
    if name not in known:
        raise B2M3DError(f"no recipe called {name!r}; the recipes are: {', '.join(known)}")
    exe = paths.blender()
    if not exe:
        raise B2M3DError("Blender was not found. Install it, or set B2M3D_BLENDER to its executable "
                         "(run `python -m b2m3d doctor` for the install command).")
    args = args[1:] if args[:1] == ["--"] else list(args)       # only the separator; a `--` inside the options is kept
    return last_json(run(command(exe, known[name], args), timeout=timeout), MARKER)


def command(exe: str, recipe: dict, args: list[str]) -> list[str]:
    """The Blender command line for one recipe. --python-exit-code 1 makes a recipe that raises exit 1, so the error and
    its traceback reach the caller instead of a missing result line; --factory-startup unless the recipe needs the
    person's own add-ons (FACTORY_STARTUP = False)."""
    startup = ["--factory-startup"] if recipe["factory_startup"] else []
    return [exe, "-b", *startup, "--python-exit-code", "1", "-P", recipe["script"], "--", *args]
