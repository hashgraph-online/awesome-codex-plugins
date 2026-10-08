#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path


def _group_from_slug(slug: str, docs_features_prefix: str) -> str | None:
    prefix = docs_features_prefix.strip("/").rstrip("/") + "/"
    s = slug.strip().lstrip("/")
    if not s.startswith(prefix):
        return None
    rest = s[len(prefix) :]
    if not rest:
        return None
    group = rest.split("/", 1)[0].strip()
    return group or None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-name", required=True)
    ap.add_argument("--docs-features-prefix", required=True)
    ap.add_argument("--docs-features", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    docs_features_prefix = args.docs_features_prefix
    slugs = [ln.strip() for ln in Path(args.docs_features).read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]

    groups: list[str] = []
    seen = set()
    for slug in slugs:
        g = _group_from_slug(slug, docs_features_prefix)
        if not g:
            continue
        if g not in seen:
            groups.append(g)
            seen.add(g)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Minimal YAML that is still easy to mechanically validate.
    lines: list[str] = []
    lines.append("schema_version: 1")
    lines.append(f"product_name: {args.product_name!r}")
    lines.append(f"generated_at: {_dt.date.today().isoformat()!r}")
    lines.append(f"docs_features_prefix: {docs_features_prefix!r}")
    lines.append("docs_features:")
    for s in slugs:
        lines.append(f"  - {s!r}")
    lines.append("groups:")
    if not groups and slugs:
        # Slugs existed but no groups parsed; keep explicit empty mapping to fail validation loudly later.
        lines.append("  {}")
    elif not groups:
        lines.append("  {}")
    else:
        for g in groups:
            lines.append(f"  {g!s}:")
            lines.append("    impl: control-plane")
            lines.append("    anchors: []")
            lines.append("    notes: \"\"")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

