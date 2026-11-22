#!/usr/bin/env python3
"""validate_scene.py: check a character scene file against schema/scene.schema.json, then check what a schema cannot.

    python3 validate_scene.py scene.json

Every problem names the field and says what is allowed ("cast[1].track.keys[2].pose: 'wavee' is not allowed.
Allowed: idle, wave, ..."). Beyond the schema it checks that each cast member names a real character, that colours
used by hills and set shapes are in the palette, that props belong to the character, that a words file exists, and
that captions run forwards. Standard library only; character_project.py runs it before it builds anything.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

KIT = Path(__file__).resolve().parent
SCHEMA = json.loads((KIT / "schema" / "scene.schema.json").read_text(encoding="utf-8"))
BUILTIN_COLOURS = validate.BUILTIN_COLOURS


def character_ids(extra: dict | None = None) -> list[str]:
    return sorted({p.stem for p in (KIT / "cast").glob("*.json")} | set(extra or {}))


def _prop_ids(character: str, extra: dict | None = None) -> list[str]:
    if extra and character in extra:
        return [p["id"] for p in extra[character]["parts"] if p.get("prop")]
    path = KIT / "cast" / f"{character}.json"
    if not path.is_file():
        return []
    return [p["id"] for p in json.loads(path.read_text(encoding="utf-8"))["parts"] if p.get("prop")]


def _visemes_errors(where: str, visemes: list) -> list[str]:
    """Mouth keys must run forwards in time: the rig reads them with a binary search."""
    times = [k.get("t") for k in visemes if isinstance(k, dict)]
    for n, (a, b) in enumerate(zip(times, times[1:])):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and b < a:
            return [f"{where}: keys must be in time order, but key {n + 1} ({b} s) comes after key {n} ({a} s); sort them by t"]
    return []


def _cast_errors(scene: dict, base_dir: Path | None, extra: dict | None = None) -> list[str]:
    errors: list[str] = []
    ids = character_ids(extra)
    seen: set[str] = set()
    for i, member in enumerate(scene.get("cast", [])):
        where = f"scene.cast[{i}]"
        if member.get("id") in seen:
            errors.append(f"{where}.id: '{member['id']}' is used twice; every cast member needs its own id")
        seen.add(member.get("id"))
        if member.get("character") not in ids:
            errors.append(f"{where}.character: {member.get('character')!r} is not a character. Allowed: {', '.join(ids)} (files in characters/cast/). "
                          f"To use your own character file, pass --character-file FILE.json to character_project.py")
        track = member.get("track", {})
        track = {"keys": track} if isinstance(track, list) else track
        errors += validate.check(track, SCHEMA["$defs"]["track"], f"{where}.track")
        allowed = _prop_ids(member.get("character", ""), extra)
        if isinstance(track, dict) and isinstance(track.get("visemes"), list):
            errors += _visemes_errors(f"{where}.track.visemes", track["visemes"])
        for n, prop in enumerate(track.get("props", []) if isinstance(track, dict) else []):
            name = prop if isinstance(prop, str) else prop.get("id")
            if name not in allowed:
                errors.append(f"{where}.track.props[{n}]: {name!r} is not a prop of {member.get('character')}. Allowed: {', '.join(allowed) or 'none (this character has no props)'}")
        spec = track.get("visemesFrom") if isinstance(track, dict) else None
        if spec and base_dir is not None and not (base_dir / spec.get("words", "")).is_file():
            errors.append(f"{where}.track.visemesFrom.words: file {spec.get('words')!r} not found next to the scene file ({base_dir})")
        if spec and spec.get("to", 1) <= spec.get("from", 0):
            errors.append(f"{where}.track.visemesFrom: 'to' must be after 'from'")
    return errors


def _palette_errors(scene: dict) -> list[str]:
    keys = set(scene.get("palette", {})) | BUILTIN_COLOURS
    names = ", ".join(sorted(scene.get("palette", {})))
    errors: list[str] = []
    for i, hill in enumerate(scene.get("hills", [])):
        if hill.get("fill") not in keys:
            errors.append(f"scene.hills[{i}].fill: {hill.get('fill')!r} is not in the palette. Palette keys: {names}")
    for i, shape in enumerate(scene.get("set", [])):
        for field in ("fill", "stroke"):
            if shape.get(field) and shape[field] not in keys:
                errors.append(f"scene.set[{i}].{field}: {shape[field]!r} is not in the palette. Palette keys: {names}")
        need = {"circle": ["c", "r"], "ellipse": ["c", "r"], "rect": ["x", "y", "w", "h"], "poly": ["pts"], "path": ["d"], "capsule": ["a", "b", "ra"]}.get(shape.get("type"), [])
        errors += [f"scene.set[{i}]: a {shape['type']} needs '{n}'" for n in need if n not in shape]
    return errors


def validate_scene(scene: dict, base_dir: Path | None = None, extra_characters: dict | None = None) -> list[str]:
    """Return every problem in a scene; an empty list means it is valid. base_dir is the scene file's folder;
    extra_characters maps ids to character files loaded with --character-file."""
    errors = validate.check(scene, SCHEMA, "scene")
    if not isinstance(scene.get("cast"), list) or not isinstance(scene.get("palette"), dict):
        return errors
    errors += _cast_errors(scene, base_dir, extra_characters) + _palette_errors(scene)
    for i, cap in enumerate(scene.get("captions", [])):
        if isinstance(cap, dict) and isinstance(cap.get("from"), (int, float)) and isinstance(cap.get("to"), (int, float)):
            if cap["to"] <= cap["from"]:
                errors.append(f"scene.captions[{i}]: 'to' ({cap['to']}) must be after 'from' ({cap['from']})")
            elif isinstance(scene.get("duration"), (int, float)) and cap["from"] >= scene["duration"]:
                errors.append(f"scene.captions[{i}].from: {cap['from']} is after the end of the scene ({scene['duration']} s)")
    return errors


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    failed = 0
    for name in argv:
        path = Path(name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"{name}: cannot read: {exc}")
            failed += 1
            continue
        problems = validate_scene(data, path.resolve().parent)
        print("\n".join(f"{name}: {p}" for p in problems) + ("\n" if problems else ""), end="")
        print(f"{name}: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
