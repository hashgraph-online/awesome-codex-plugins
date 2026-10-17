#!/usr/bin/env python3
"""Check/apply/rollback the hash-guarded BabelDOC 0.6.4 compatibility fixes.

Run with the engine's own virtual-environment Python. No engine import, network
access or automatic installation; unknown or locally modified files are refused.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import tempfile

PATCHES = Path(__file__).resolve().parent.parent / "patches" / "babeldoc-0.6.4"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def apply_diff(original, patch):
    """Apply a unified text diff, checking every hunk and its declared counts."""
    source = original.decode("utf-8").splitlines(keepends=True)
    lines = patch.splitlines(keepends=True)
    if not (lines[0].startswith("--- ") and lines[1].startswith("+++ ")):
        raise ValueError("Invalid patch header")
    result, cursor, i = [], 0, 2
    while i < len(lines):
        match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n?", lines[i])
        if not match:
            raise ValueError("Invalid patch hunk")
        start = int(match[1]) - 1
        if start < cursor or start > len(source):
            raise ValueError("Overlapping or out-of-range patch")
        result.extend(source[cursor:start])
        cursor, old_count, new_count = start, 0, 0
        i += 1
        while i < len(lines) and not lines[i].startswith("@@ "):
            line = lines[i]
            if line[:1] not in (" ", "+", "-"):
                raise ValueError("Invalid patch line")
            if line[0] in " -":
                if cursor >= len(source) or source[cursor] != line[1:]:
                    raise ValueError("Patch context mismatch")
                cursor += 1
                old_count += 1
            if line[0] in " +":
                result.append(line[1:])
                new_count += 1
            i += 1
        if old_count != int(match[2] or 1) or new_count != int(match[4] or 1):
            raise ValueError("Patch hunk count mismatch")
    result.extend(source[cursor:])
    return "".join(result).encode("utf-8")


def atomic_write(path, data, mode=0o644):
    fd, name = tempfile.mkstemp(prefix=".pdf-translate-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def repair(distribution, action, patches=PATCHES):
    manifest = json.loads((patches / "manifest.json").read_text(encoding="utf-8"))
    if distribution.version != manifest["version"]:
        raise ValueError(f"Expected BabelDOC {manifest['version']}; found {distribution.version}")
    root = Path(distribution.locate_file("")).resolve()
    backup = root / ".babeldoc-pdf-translate-compat" / manifest["id"]
    records = []
    # Preflight every file before changing any of them.
    for item in manifest["files"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "babeldoc":
            raise ValueError("Unsafe patch path")
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Refusing a linked engine source")
        current = path.read_bytes()
        current_hash = sha(current)
        if current_hash not in (item["original_sha256"], item["patched_sha256"]):
            raise ValueError(f"Unknown engine file; no changes made: {relative}")
        saved = backup / relative
        if current_hash == item["original_sha256"]:
            original = current
        else:
            if not saved.is_file() or sha(saved.read_bytes()) != item["original_sha256"]:
                raise ValueError(f"Verified rollback copy missing: {relative}")
            original = saved.read_bytes()
        patch = patches / item["patch"]
        if not patch.resolve().is_relative_to(patches.resolve()):
            raise ValueError("Unsafe patch filename")
        candidate = apply_diff(original, patch.read_text(encoding="utf-8"))
        if sha(candidate) != item["patched_sha256"]:
            raise ValueError(f"Patch result hash mismatch: {relative}")
        compile(candidate, str(path), "exec")
        records.append((path, saved, original, candidate, current))
    applied = all(current == candidate for _, _, _, candidate, current in records)
    if action != "check":
        changed = []
        try:
            for path, saved, original, candidate, current in records:
                desired = candidate if action == "apply" else original
                if current == desired:
                    continue
                if path.read_bytes() != current:
                    raise ValueError("Engine changed during repair")
                saved.parent.mkdir(parents=True, exist_ok=True)
                if saved.exists() and saved.read_bytes() != original:
                    raise ValueError("Refusing to overwrite a different rollback copy")
                if not saved.exists():
                    atomic_write(saved, original, 0o600)
                atomic_write(path, desired, path.stat().st_mode & 0o777)
                changed.append((path, current))
        except Exception:
            for path, current in reversed(changed):
                atomic_write(path, current, path.stat().st_mode & 0o777)
            raise
        applied = action == "apply"
    return {"compatibility": manifest["id"], "applied": applied,
            "files": len(records), "action": action, "backup": str(backup)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("check", "apply", "rollback"):
        actions.add_argument("--" + name, action="store_true")
    args = parser.parse_args()
    action = next(name for name in ("check", "apply", "rollback") if getattr(args, name))
    try:
        result = repair(importlib.metadata.distribution("babeldoc"), action)
    except Exception as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(result, indent=2))
    return 1 if action == "check" and not result["applied"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
