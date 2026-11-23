#!/usr/bin/env python3
"""build_map_data.py: shrink a Natural Earth countries GeoJSON into the small file make_map.py ships with.

  python3 build_map_data.py ne_110m_admin_0_countries.geojson [--out data/ne_110m_countries.json.gz] [--digits 2]

Natural Earth (https://www.naturalearthdata.com) is public domain. This keeps, for every country, only the names, the
three-letter code, the continent and the outline rounded to --digits decimals (two decimals is about 1 km, finer than
a 110m map can show), then gzips the list. It prints the SHA-256 of the source so data/NATURAL-EARTH.md can record which
file the subset came from. Standard library only; run it only when the data changes.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "ne_110m_countries.json.gz"


def rounded(coords, digits: int):
    if coords and isinstance(coords[0], (int, float)):
        return [round(coords[0], digits), round(coords[1], digits)]
    return [rounded(c, digits) for c in coords]


def shrink(geojson: dict, digits: int = 2) -> list[dict]:
    out = []
    for feature in geojson.get("features", []):
        props, geom = feature.get("properties", {}), feature.get("geometry") or {}
        if geom.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        code = props.get("ISO_A3") if props.get("ISO_A3") not in (None, "-99") else props.get("ADM0_A3")
        out.append({"n": props.get("NAME"), "a": props.get("ADMIN"), "i": code, "c": props.get("CONTINENT"),
                    "g": {"t": geom["type"], "c": rounded(geom["coordinates"], digits)}})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="a Natural Earth admin-0 countries GeoJSON")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--digits", type=int, default=2)
    args = ap.parse_args(argv)
    raw = Path(args.source).read_bytes()
    countries = shrink(json.loads(raw.decode("utf-8")), args.digits)
    if not countries:
        print("FAIL  build_map_data: no country polygons found in that file")
        return 1
    text = json.dumps(countries, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "wb") as fh:          # mtime 0 so the same input gives the same bytes
        fh.write(gzip.compress(text, 9, mtime=0))
    print(f"PASS  {len(countries)} countries -> {args.out} ({Path(args.out).stat().st_size / 1024:.0f} KB gzipped, {len(text) / 1024:.0f} KB raw)")
    print(f"INFO  source sha256 {hashlib.sha256(raw).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
