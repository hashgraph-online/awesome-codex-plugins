#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-name", required=True)
    ap.add_argument("--docs-features", required=True, help="Text file: one docs/features slug per line (may be empty).")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    slugs_path = Path(args.docs_features)
    slugs = [ln.strip() for ln in slugs_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# Feature Inventory: {args.product_name}")
    lines.append("")
    lines.append(f"- Generated: {_dt.date.today().isoformat()}")
    lines.append("- Source: docs sitemap inventory (if provided); otherwise empty/incomplete by design.")
    lines.append(f"- Count: {len(slugs)}")
    lines.append("")
    lines.append("## Docs Slugs")
    lines.append("")
    if slugs:
        for s in slugs:
            lines.append(f"- `{s}`")
    else:
        lines.append("_No docs sitemap provided (or no matching `docs/features/` entries)._")
    lines.append("")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

