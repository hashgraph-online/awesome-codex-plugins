"""GLB helpers: make compressed GLBs readable by Python tools.

``b2m3d optimize`` writes EXT_meshopt_compression by default (small and fast in the browser),
but trimesh cannot decode it. ``readable`` returns a plain copy when needed.
"""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
from pathlib import Path

from .run import last_json, node_script

COMPRESSED = {"EXT_meshopt_compression", "KHR_mesh_quantization", "KHR_draco_mesh_compression"}


def gltf_json(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"glTF":
        return json.loads(data) if path.suffix == ".gltf" else {}
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + length])


def is_compressed(path: Path) -> bool:
    if path.suffix.lower() not in {".glb", ".gltf"}:
        return False
    return bool(COMPRESSED & set(gltf_json(path).get("extensionsUsed", [])))


def readable(path: Path) -> Path:
    """The path itself if plain, else a cached decompressed copy."""
    path = Path(path).resolve()
    if not is_compressed(path):
        return path
    key = hashlib.sha1(f"{path}:{path.stat().st_mtime_ns}".encode()).hexdigest()[:16]
    out = Path(tempfile.gettempdir()) / "b2m3d-plain" / f"{path.stem}-{key}.glb"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        last_json(node_script("decompress.mjs", [str(path), str(out)]), "B2M3D_DECOMPRESS")
    return out
