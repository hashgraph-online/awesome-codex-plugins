#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


ALLOWED_IMPL = {"client", "mixed", "control-plane"}


def _group_from_slug(slug: str, docs_features_prefix: str) -> str | None:
    prefix = docs_features_prefix.strip("/").rstrip("/") + "/"
    s = slug.strip().lstrip("/")
    if not s.startswith(prefix):
        return None
    rest = s[len(prefix) :]
    if not rest:
        return None
    return rest.split("/", 1)[0] or None


def _parse_registry(path: Path) -> dict:
    data = {"docs_features_prefix": "docs/features/", "groups": {}}
    cur = None
    in_groups = False
    in_anchors = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("docs_features_prefix:"):
            data["docs_features_prefix"] = line.split(":", 1)[1].strip().strip("'\"")
        if line == "groups:":
            in_groups = True
            continue
        if not in_groups:
            continue

        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            name = line.strip()[:-1]
            cur = {"impl": None, "anchors": [], "notes": ""}
            data["groups"][name] = cur
            in_anchors = False
            continue

        if cur is None:
            continue

        s = line.strip()
        if s.startswith("impl:"):
            cur["impl"] = s.split(":", 1)[1].strip()
        elif s.startswith("anchors:"):
            in_anchors = True
            if s.endswith("[]"):
                cur["anchors"] = []
        elif in_anchors and s.startswith("- "):
            cur["anchors"].append(s[2:].strip().strip("'\""))
        elif s.startswith("notes:"):
            cur["notes"] = s.split(":", 1)[1].strip().strip("'\"")
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature-registry", required=True)
    ap.add_argument("--docs-features", required=True)
    ap.add_argument("--local-clone-dir", required=True)
    args = ap.parse_args()

    feature_registry_path = Path(args.feature_registry).resolve()
    artifact_dir = feature_registry_path.parent
    reg = _parse_registry(feature_registry_path)
    prefix = reg["docs_features_prefix"]
    groups = reg["groups"]
    docs_slugs = [ln.strip() for ln in Path(args.docs_features).read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    root = Path(args.local_clone_dir).resolve()

    errs: list[str] = []

    # Rule: every docs/features slug maps to a group.
    for slug in docs_slugs:
        g = _group_from_slug(slug, prefix)
        if not g:
            errs.append(f"docs slug not under prefix {prefix!r}: {slug!r}")
            continue
        if g not in groups:
            errs.append(f"docs slug group missing from registry: group={g!r} slug={slug!r}")

    # Rule: every group has impl; client/mixed must have anchors.
    for g, ent in groups.items():
        impl = (ent.get("impl") or "").strip()
        if impl not in ALLOWED_IMPL:
            errs.append(f"group {g!r} has invalid impl {impl!r} (allowed: {sorted(ALLOWED_IMPL)})")
        anchors = ent.get("anchors") or []
        if impl in ("client", "mixed") and len(anchors) < 1:
            errs.append(f"group {g!r} impl={impl!r} requires >=1 anchor")

        for a in anchors:
            # Allow line/col suffix like "path/to/file.py:123"
            p = a.split(":", 1)[0]
            if p.startswith("/"):
                abs_path = Path(p).resolve()
                if not abs_path.exists():
                    errs.append(f"group {g!r} anchor missing: {a!r} (checked {abs_path})")
                continue

            # Relative anchors may reference either the analysis root or the artifact bundle dir.
            candidates = [
                (artifact_dir, (artifact_dir / p).resolve(), "artifact_dir"),
                (root, (root / p).resolve(), "analysis_root"),
            ]
            path_ok = False
            missing_paths: list[str] = []
            for base, resolved, _label in candidates:
                base_resolved = base.resolve()
                if not (resolved == base_resolved or str(resolved).startswith(str(base_resolved) + os.sep)):
                    continue
                if resolved.exists():
                    path_ok = True
                    break
                missing_paths.append(str(resolved))

            if not path_ok:
                checked = ", ".join(missing_paths) if missing_paths else "(no safe candidate paths)"
                errs.append(f"group {g!r} anchor missing: {a!r} (checked {checked})")

    # Completeness guard: if docs/ exists with markdown content, empty docs feature inventory is likely bad prefix selection.
    docs_dir = root / "docs"
    if docs_dir.exists():
        has_docs_markdown = any(docs_dir.rglob("*.md")) or any(docs_dir.rglob("*.mdx"))
        if has_docs_markdown and len(docs_slugs) == 0:
            errs.append(
                "docs-features inventory is empty while docs/ contains markdown; "
                "likely wrong docs_features_prefix or extraction failure"
            )

    # Completeness guard: reject unresolved placeholder code-map specs.
    spec_code_map = artifact_dir / "spec-code-map.md"
    if spec_code_map.exists():
        text = spec_code_map.read_text(encoding="utf-8", errors="replace")
        if "_TBD_" in text or re.search(r"\|\s*_TBD_\s*\|", text):
            errs.append(f"spec-code-map contains unresolved placeholders: {spec_code_map}")

    if errs:
        for e in errs:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("OK: feature registry validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
