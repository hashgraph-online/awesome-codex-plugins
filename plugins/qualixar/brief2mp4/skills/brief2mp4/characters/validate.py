#!/usr/bin/env python3
"""validate.py: check a character file against schema/character.schema.json, then check what a schema cannot.

    python3 validate.py cast/child.json [more.json ...]

Standard library only. It implements the part of JSON Schema the character schema uses (type, required,
properties, additionalProperties, items, enum, pattern, minimum, exclusiveMinimum, min/max sizes and $ref), then
adds the checks that need the whole file: unique part ids, parents that exist, one root, no cycles, every colour
key defined in the palette, and the fields each shape type needs. It prints one line per problem and exits 1 if
there is any.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "character.schema.json"
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
# The colour names every character may use without defining them (shapes.js DEFAULT_PALETTE has the same names; a test keeps them equal).
BUILTIN_COLOURS = {"ink", "mouth", "teeth", "tongue", "lip", "white"}
NEEDS = {"path": ["d"], "ellipse": ["c", "r"], "circle": ["c", "r"], "capsule": ["a", "b", "ra"], "rect": ["x", "y", "w", "h"], "poly": ["pts"]}


def _is(value, name: str) -> bool:
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def _resolve(ref: str, root: dict) -> dict:
    node = root
    for key in ref.lstrip("#/").split("/"):
        node = node[key]
    return node


def _name(value) -> str:
    return "null" if value is None else "boolean" if isinstance(value, bool) else "number" if _is(value, "number") else "string" if isinstance(value, str) else "list" if isinstance(value, list) else "object"


def _check(value, schema: dict, root: dict, where: str, errors: list[str]) -> None:
    if "$ref" in schema:
        schema = _resolve(schema["$ref"], root)
    hint = f" ({schema['x-hint']})" if "x-hint" in schema else ""
    kinds = schema.get("type")
    if kinds is not None:
        kinds = [kinds] if isinstance(kinds, str) else kinds
        if not any(_is(value, k) for k in kinds):
            errors.append(f"{where}: expected {' or '.join(kinds)}, got {_name(value)}{hint}")
            return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} is not allowed. Allowed: {', '.join(str(v) for v in schema['enum'])}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{where}: {value!r} is not valid{hint or ' (must match ' + schema['pattern'] + ')'}")
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{where}: too short")
    if _is(value, "number"):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{where}: {value} is below the minimum of {schema['minimum']}{hint}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{where}: {value} is above the maximum of {schema['maximum']}{hint}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{where}: {value} must be above {schema['exclusiveMinimum']}{hint}")
    if isinstance(value, list):
        _check_array(value, schema, root, where, errors)
    if isinstance(value, dict):
        _check_object(value, schema, root, where, errors)


def _check_array(value: list, schema: dict, root: dict, where: str, errors: list[str]) -> None:
    if len(value) < schema.get("minItems", 0):
        errors.append(f"{where}: needs at least {schema['minItems']} items")
    if len(value) > schema.get("maxItems", 10**9):
        errors.append(f"{where}: allows at most {schema['maxItems']} items")
    if "items" in schema:
        for i, item in enumerate(value):
            _check(item, schema["items"], root, f"{where}[{i}]", errors)


def _check_object(value: dict, schema: dict, root: dict, where: str, errors: list[str]) -> None:
    for key in schema.get("required", []):
        if key not in value:
            errors.append(f"{where}: missing required field '{key}'")
    if len(value) < schema.get("minProperties", 0):
        errors.append(f"{where}: needs at least {schema['minProperties']} entries")
    props = schema.get("properties", {})
    extra = schema.get("additionalProperties", True)
    for key, item in value.items():
        if key in props:
            _check(item, props[key], root, f"{where}.{key}", errors)
        elif extra is False:
            errors.append(f"{where}: unknown field '{key}'. Allowed: {', '.join(props) or 'none'}")
        elif isinstance(extra, dict):
            _check(item, extra, root, f"{where}.{key}", errors)


def check(value, schema: dict, where: str) -> list[str]:
    """Check a value against any schema this kit ships (character or scene); the problems name the field and say what is allowed."""
    errors: list[str] = []
    _check(value, schema, schema, where, errors)
    return errors


def schema_errors(character: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    _check(character, schema, schema, "character", errors)
    return errors


def _structure_errors(parts: list[dict]) -> list[str]:
    errors: list[str] = []
    ids = [p.get("id") for p in parts]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate part id '{dup}'")
    by_id = {p["id"]: p for p in parts if "id" in p}
    roots = [p["id"] for p in parts if p.get("parent") is None]
    if len(roots) != 1:
        errors.append(f"needs exactly one root part (parent null), found {len(roots)}")
    for p in parts:
        if p.get("parent") is not None and p["parent"] not in by_id:
            errors.append(f"part '{p['id']}': parent '{p['parent']}' does not exist")
    for p in parts:
        seen, node = set(), p
        while node is not None and node.get("parent") is not None:
            if node["id"] in seen:
                errors.append(f"part '{p['id']}': parent chain has a cycle")
                break
            seen.add(node["id"])
            node = by_id.get(node["parent"])
    for need in ("hip", "torso", "head", "mouth"):
        if need not in by_id:
            errors.append(f"missing the standard part '{need}'")
    return errors


def _shapes_in(where: str, shapes: list, palette: set) -> list[str]:
    errors: list[str] = []
    for i, shape in enumerate(shapes):
        for key in NEEDS.get(shape.get("type"), []):
            if key not in shape:
                errors.append(f"{where} shape {i}: a {shape['type']} needs '{key}'")
        if "calm" in shape and len(shape["calm"]) != len(shape.get("pts", [])):
            errors.append(f"{where} shape {i}: calm needs as many points as pts")
        for key in ("fill", "stroke"):
            if shape.get(key) and shape[key] not in palette:
                errors.append(f"{where} shape {i}: {key} colour '{shape[key]}' is not in the palette")
    return errors


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def picture_problem(src: str, base_dir: Path | None) -> str | None:
    """Why a picture reference cannot be used, or None. A file must be a real PNG or WebP that sits inside the
    character file's folder (no ../ and no absolute path); a data: URI must be data:image/png or data:image/webp, base64."""
    if src.startswith("data:"):
        if not re.match(r"data:image/(png|webp);base64,[A-Za-z0-9+/=]*$", src):
            return "only data:image/png;base64, and data:image/webp;base64, pictures are accepted"
        return None
    if base_dir is None:
        return None
    root = base_dir.resolve()
    target = (root / src).resolve()
    if target != root and root not in target.parents:
        return f"picture '{src}' must stay inside the character file's folder"
    if not target.is_file():
        return f"picture '{src}' not found next to the character file"
    with open(target, "rb") as fh:
        head = fh.read(12)
    ext = target.suffix.lower()
    if not ((ext == ".png" and head[:8] == PNG_MAGIC) or (ext == ".webp" and head[:4] == b"RIFF" and head[8:12] == b"WEBP")):
        return f"picture '{src}' is not a PNG or WebP file (its first bytes are not a PNG or WebP header)"
    return None


def _images_in(where: str, holder: dict, base_dir: Path | None) -> list[str]:
    """Check the pictures a part, variant or mouth block points at (files are checked when the file's folder is known)."""
    errors: list[str] = []
    mouth = holder.get("mouth") or {}
    if mouth.get("kind") == "images" and "rest" not in mouth.get("images", {}):
        errors.append(f"{where}: an image mouth needs a 'rest' picture")
    pictures = [holder["image"]] if "image" in holder else []
    pictures += list((mouth.get("images") or {}).values())
    for pic in pictures:
        problem = picture_problem(pic.get("src", ""), base_dir)
        if problem:
            errors.append(f"{where}: {problem}")
    return errors


def _shape_errors(character: dict, base_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    palette = set(character.get("palette", {})) | BUILTIN_COLOURS
    for part in character.get("parts", []):
        pid = part.get("id")
        if pid == "mouth" and "mouth" not in part:
            errors.append("part 'mouth' needs a 'mouth' block (kind lips, jaw or images)")
        errors += _shapes_in(f"part '{pid}'", part.get("shapes", []), palette) + _images_in(f"part '{pid}'", part, base_dir)
        for name, variant in part.get("variants", {}).items():
            where = f"part '{pid}' variant '{name}'"
            errors += _shapes_in(where, variant.get("shapes", []), palette) + _images_in(where, variant, base_dir)
    return errors


def validate_character(character: dict, base_dir: Path | None = None) -> list[str]:
    """Return a list of problems; an empty list means the character is valid. Give base_dir (the folder of the
    character file) to also check that every picture file it names exists."""
    errors = schema_errors(character)
    if errors and not isinstance(character.get("parts"), list):
        return errors
    parts = [p for p in character.get("parts", []) if isinstance(p, dict)]
    return errors + _structure_errors(parts) + _shape_errors(character, base_dir)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    failed = 0
    for name in argv:
        try:
            data = json.loads(Path(name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"{name}: cannot read: {exc}")
            failed += 1
            continue
        problems = validate_character(data, Path(name).resolve().parent)
        for line in problems:
            print(f"{name}: {line}")
        print(f"{name}: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
