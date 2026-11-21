"""b2m3d material: named presets -> glTF PBR materials (+ KHR extensions), applied by node name.

Presets are plain JSON in presets/materials/ with LINEAR colours, which is what glTF expects.
A colour picked in sRGB must be converted first: ``linear = (srgb / 255) ** 2.2``
(``b2m3d material linear "#rrggbb"`` does it). Skipping this renders dark colours about two
stops too light. Extensions written: clearcoat, transmission (+ volume), ior,
emissive_strength and sheen, which three.js and Blender's glTF importer both read.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from . import paths
from .run import B2M3DError, last_json, node_script

SRGB_GAMMA = 2.2


def srgb_to_linear(hex_color: str) -> list[float]:
    """'#1a2b3c' -> linear [r, g, b] using the pure 2.2 power curve."""
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", hex_color.strip())
    if not m:
        raise ValueError(f"expected a #rrggbb colour, got {hex_color!r}")
    raw = m.group(1)
    return [round((int(raw[i:i + 2], 16) / 255) ** SRGB_GAMMA, 5) for i in (0, 2, 4)]


def load_presets(folder: Path | None = None) -> dict[str, dict]:
    folder = folder or paths.PRESETS
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))}


def to_gltf(preset: dict, name: str | None = None) -> dict:
    """Preset JSON -> glTF material JSON (core metallic-roughness + KHR extensions)."""
    mat: dict = {
        "name": name or preset["name"],
        "baseColorFactor": [*preset["baseColor"], 1.0],
        "metallicFactor": preset.get("metallic", 0.0),
        "roughnessFactor": preset.get("roughness", 0.5),
        "extensions": {},
    }
    ext = mat["extensions"]
    if preset.get("clearcoat", 0) > 0:
        ext["KHR_materials_clearcoat"] = {"clearcoatFactor": preset["clearcoat"],
                                          "clearcoatRoughnessFactor": preset.get("clearcoatRoughness", 0.1)}
    if preset.get("transmission", 0) > 0:
        ext["KHR_materials_transmission"] = {"transmissionFactor": preset["transmission"]}
        ext["KHR_materials_volume"] = {"thicknessFactor": 0.01}
    if "ior" in preset:
        ext["KHR_materials_ior"] = {"ior": preset["ior"]}
    if preset.get("emissiveStrength", 0) > 0:
        mat["emissiveFactor"] = list(preset.get("emissive", (1, 1, 1)))
        ext["KHR_materials_emissive_strength"] = {"emissiveStrength": preset["emissiveStrength"]}
    if preset.get("sheen", 0) > 0:
        color = preset.get("sheenColor", (1, 1, 1))
        ext["KHR_materials_sheen"] = {"sheenColorFactor": [c * preset["sheen"] for c in color],
                                      "sheenRoughnessFactor": preset.get("sheenRoughness", 0.3)}
    return mat


def resolve(spec: str) -> dict:
    """'gold' (a preset) or 'path/to/preset.json' -> glTF material JSON."""
    path = Path(spec)
    if path.suffix == ".json" and path.exists():
        return to_gltf(json.loads(path.read_text(encoding="utf-8")), path.stem)
    presets = load_presets()
    if spec in presets:
        return to_gltf(presets[spec], spec)
    raise KeyError(f"unknown material {spec!r}; presets: {', '.join(presets)}")


def parse_assignments(pairs: list[str]) -> dict[str, str]:
    out = {}
    for pair in pairs:
        key, sep, val = pair.partition("=")
        if not sep or not key or not val:
            raise ValueError(f"--assign expects name=preset (or '*=preset'), got {pair!r}")
        out[key] = val
    return out


def assign(src: Path, out: Path, mapping: dict[str, str]) -> dict:
    """mapping: node/mesh name (or '*') -> preset name or preset .json. Applied with glTF Transform."""
    if not mapping:
        raise B2M3DError("nothing to assign: pass --assign name=preset")
    resolved = {k: resolve(v) for k, v in mapping.items()}
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(resolved, fh)
        tmp = Path(fh.name)
    try:
        stdout = node_script("material_apply.mjs", [str(src), str(out), str(tmp)])
    finally:
        tmp.unlink(missing_ok=True)
    return last_json(stdout, "B2M3D_MATERIAL")
