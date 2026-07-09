#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path


def _parse_registry(path: Path) -> dict:
    data = {"docs_features_prefix": "docs/features/", "docs_features": [], "groups": {}}
    cur = None
    in_docs = False
    in_groups = False
    in_anchors = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("docs_features_prefix:"):
            data["docs_features_prefix"] = line.split(":", 1)[1].strip().strip("'\"")
        if line == "docs_features:":
            in_docs = True
            in_groups = False
            continue
        if line == "groups:":
            in_docs = False
            in_groups = True
            continue

        if in_docs and line.startswith("  - "):
            data["docs_features"].append(line[4:].strip().strip("'\""))
            continue

        if in_groups:
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
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    reg = _parse_registry(Path(args.registry))
    groups = reg["groups"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Feature Catalog")
    lines.append("")
    lines.append(f"- Generated: {_dt.date.today().isoformat()}")
    lines.append(f"- Groups: {len(groups)}")
    lines.append("")
    lines.append("| Group | impl | anchors | notes |")
    lines.append("|---|---|---:|---|")
    for g in sorted(groups.keys()):
        ent = groups[g]
        impl = ent.get("impl") or ""
        anchors = ent.get("anchors") or []
        notes = (ent.get("notes") or "").replace("\n", " ")
        lines.append(f"| `{g}` | `{impl}` | {len(anchors)} | {notes} |")
    lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

