#!/usr/bin/env python3
"""make_map.py: a country or region map as an SVG for HyperFrames, with markers, labels and routes between points.

  python3 make_map.py --region Egypt --point "Alexandria=31.20,29.92" --point "Aswan=24.09,32.90" \\
        --route "Alexandria>Aswan" --out assets/maps/egypt.svg
  python3 make_map.py --region "France, Spain" --out assets/maps/iberia.svg --size 1296x740
  python3 make_map.py --region "bbox:-10,30,40,60" --out europe.svg          # min lon, min lat, max lon, max lat
  python3 make_map.py --list                                                   # every name and continent it knows

--region is a country name (aliases and three-letter codes work: USA, UK, FRA), several separated by commas, a
continent, "world", or bbox:minlon,minlat,maxlon,maxlat. --point is Name=lat,lon (latitude first, as maps are read).
--route is Name>Name>Name and draws one curved line through those points; the SVG holds the line's length in pixels
(data-len), which is what a frame-by-frame draw-on needs (references/render-traps.md, trap 7).

The boundaries are Natural Earth, public domain (data/NATURAL-EARTH.md), shipped as a 54 KB subset so this works offline.
Natural Earth draws boundaries by their de facto status (who controls the ground), not by any one country's claim. A map
of a disputed region (Kashmir, Crimea, Western Sahara and others) can be unacceptable to some audiences, and some
countries restrict how their borders may be shown: check before publishing such a map, or pass --geojson with an
outline that follows the rules where it will be shown.
The projection is chosen for the region: Equal Earth for the world and wide regions, Albers equal-area conic for wide
regions in the mid latitudes, Mercator for small areas and the tropics. Only the main body of a country sets the frame
(French Guiana does not stretch a map of France); points always fit. Next to the SVG it writes a .json with the
projection, the marker and label positions in pixels and the route lengths. Standard library only.
"""
from __future__ import annotations

import argparse
import difflib
import gzip
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_map_data import shrink  # noqa: E402
from map_projection import choose_projection, fit as _fit, projector  # noqa: E402,F401  (re-exported: choose_projection and projector are part of this module's use)

DATA = Path(__file__).resolve().parent.parent / "data" / "ne_110m_countries.json.gz"
CONTINENTS = ["Africa", "Antarctica", "Asia", "Europe", "North America", "Oceania", "South America"]
ALIASES = {"usa": "United States of America", "us": "United States of America", "united states": "United States of America", "america": "United States of America",
           "uk": "United Kingdom", "britain": "United Kingdom", "great britain": "United Kingdom", "turkiye": "Turkey", "drc": "Democratic Republic of the Congo",
           "congo kinshasa": "Democratic Republic of the Congo", "czech republic": "Czechia", "burma": "Myanmar", "swaziland": "eSwatini",
           "uae": "United Arab Emirates", "korea": "South Korea", "macedonia": "North Macedonia", "tanzania": "United Republic of Tanzania",
           "cote d ivoire": "Ivory Coast", "east timor": "East Timor", "bahamas": "The Bahamas", "serbia": "Republic of Serbia"}
MAIN_SHARE = 0.2          # a piece smaller than this share of the largest piece does not set the frame


class MapError(ValueError):
    """Anything the user can fix: an unknown name, a bad point, a route through a point that is not there."""


@dataclass(frozen=True)
class Region:
    selected: tuple
    bbox: tuple
    label: str


def norm(text: str) -> str:
    s = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower().replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


def load_countries(path=None) -> list[dict]:
    """The shipped subset, or any Natural Earth style GeoJSON (or a .json.gz from build_map_data.py) given as `path`."""
    src = Path(path) if path else DATA
    try:
        raw = src.read_bytes()
        data = json.loads((gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw).decode("utf-8"))
    except (OSError, ValueError) as err:
        raise MapError(f"cannot read the boundary data {src}: {err}")
    return shrink(data) if isinstance(data, dict) else data


def polygons(country: dict) -> list[list]:
    g = country["g"]
    return [g["c"]] if g["t"] == "Polygon" else list(g["c"])


def ring_area(ring: list) -> float:
    """Area of a ring in square degrees, shrunk by the cosine of its latitude so high-latitude pieces are not overrated."""
    s = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1])) / 2
    return abs(s) * math.cos(math.radians(sum(p[1] for p in ring) / len(ring)))


def main_pieces(countries: list[dict]) -> list[list]:
    pieces = [p for c in countries for p in polygons(c)]
    if not pieces:
        return []
    biggest = max(ring_area(p[0]) for p in pieces)
    return [p for p in pieces if ring_area(p[0]) >= MAIN_SHARE * biggest]


def bbox_of(pieces: list[list]) -> tuple:
    pts = [pt for p in pieces for pt in p[0]]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def _index(countries: list[dict]) -> dict:
    idx = {}
    for c in countries:
        for key in (c["n"], c["a"], c["i"]):
            if key:
                idx.setdefault(norm(key), c)
    for alias, target in ALIASES.items():
        hit = idx.get(norm(target))
        if hit:
            idx.setdefault(alias, hit)
    return idx


def resolve_region(spec: str, countries: list[dict]) -> Region:
    spec = (spec or "").strip()
    if spec.lower().startswith("bbox:"):
        try:
            x0, y0, x1, y1 = (float(v) for v in spec[5:].split(","))
        except ValueError:
            raise MapError(f"bad bbox '{spec}': use bbox:minlon,minlat,maxlon,maxlat")
        if not (-180 <= x0 < x1 <= 180 and -90 <= y0 < y1 <= 90):
            raise MapError(f"bad bbox '{spec}': the minimums must be below the maximums, longitudes within +-180 and latitudes within +-90")
        return Region((), (x0, y0, x1, y1), "the area")
    if norm(spec) == "world":
        shown = [c for c in countries if c["c"] != "Antarctica"]
        return Region(tuple(countries), (-180.0, -57.0, 180.0, 84.0), "the world") if shown else Region((), (-180, -90, 180, 90), "the world")
    idx, picked, names = _index(countries), [], []
    for token in (t for t in re.split(r"[;,]", spec) if t.strip()):
        key = norm(token)
        cont = next((c for c in CONTINENTS if norm(c) == key), None)
        found = [c for c in countries if c["c"] == cont] if cont else ([idx[key]] if key in idx else [])
        if not found:
            raise MapError(_unknown(token.strip(), idx))
        picked += [c for c in found if c not in picked]
        names.append(cont or found[0]["a"])
    if not picked:
        raise MapError("no region given: use a country, a continent, world or bbox:minlon,minlat,maxlon,maxlat")
    return Region(tuple(picked), bbox_of(main_pieces(picked)), ", ".join(names))


def _unknown(token: str, idx: dict) -> str:
    close = difflib.get_close_matches(norm(token), list(idx) + [norm(c) for c in CONTINENTS], n=3, cutoff=0.7)
    names = [idx[k]["a"] if k in idx else next(c for c in CONTINENTS if norm(c) == k) for k in close]
    base = f"unknown country or region '{token}'."
    if names:
        return f"{base} Did you mean: {', '.join(dict.fromkeys(names))}?"
    return f"{base} `make_map.py --list` prints every name the data knows; very small countries are not in the 110m set (pass --geojson with a finer Natural Earth file)."


# ---- points, routes, geometry on the page ---------------------------------------------------------------------------

def parse_point(text: str) -> dict:
    name, eq, coords = str(text).rpartition("=")
    try:
        lat, lon = (float(v) for v in coords.split(","))
    except ValueError:
        lat = lon = float("nan")
    if not eq or not name.strip() or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise MapError(f"bad point '{text}': use Name=lat,lon with latitude between -90 and 90 and longitude between -180 and 180")
    return {"name": name.strip(), "lat": lat, "lon": lon}


def parse_route(text: str, points: list[dict]) -> list[str]:
    names = [n.strip() for n in str(text).split(">") if n.strip()]
    known = {p["name"].lower(): p["name"] for p in points}
    if len(names) < 2:
        raise MapError(f"route '{text}' needs at least two points: Name>Name")
    for n in names:
        if n.lower() not in known:
            raise MapError(f"route '{text}' names '{n}', which is not one of the points ({', '.join(known.values()) or 'none given'})")
    return [known[n.lower()] for n in names]


def quad_path(pts: list[tuple], lift: float = 0.18) -> tuple[str, float]:
    """One quadratic arc per leg, bowed to the left of travel; returns the path data and its length in pixels."""
    d, length = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}", 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dist = math.dist((ax, ay), (bx, by))
        cx, cy = (ax + bx) / 2 + (ay - by) * lift, (ay + by) / 2 + (bx - ax) * lift
        d += f"Q{cx:.1f} {cy:.1f} {bx:.1f} {by:.1f}"
        prev = (ax, ay)
        for i in range(1, 65):
            t = i / 64
            cur = ((1 - t) ** 2 * ax + 2 * t * (1 - t) * cx + t * t * bx, (1 - t) ** 2 * ay + 2 * t * (1 - t) * cy + t * t * by)
            length += math.dist(prev, cur)
            prev = cur
        if dist == 0:
            length += 0
    return d, length


def place_labels(markers: list[dict], size: tuple, font: int) -> list[dict]:
    """Put each label beside its dot where it hits no other label, no dot and not the frame edge."""
    w, h = size
    dots = [(m["x"] - 14, m["y"] - 14, 28, 28) for m in markers]
    boxes: list[tuple] = []
    out = []
    hit = lambda a, b: not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])
    for m in markers:
        bw, bh = len(m["name"]) * font * 0.56, font * 1.15
        for k in range(0, 40):
            side = ("right", "left", "above", "below")[k % 4]
            row = k // 4
            gap = 20 + row * bh * 0.5
            x = {"right": m["x"] + gap, "left": m["x"] - gap - bw, "above": m["x"] - bw / 2, "below": m["x"] - bw / 2}[side]
            y = {"right": m["y"] - bh / 2, "left": m["y"] - bh / 2, "above": m["y"] - gap - bh, "below": m["y"] + gap}[side]
            box = (x, y, bw, bh)
            if 0 <= x and x + bw <= w and 0 <= y and y + bh <= h and not any(hit(box, o) for o in boxes + dots):
                break
        boxes.append(box)
        out.append({"name": m["name"], "x": round(x, 1), "y": round(y, 1), "w": round(bw, 1), "h": round(bh, 1),
                    "anchor": "start", "baseline": round(y + bh * 0.8, 1)})
    return out


def ring_d(ring: list, to_px, size: tuple) -> str:
    pts, last = [], None
    for lon, lat in ring:
        x, y = to_px(lon, lat)
        if last is None or abs(x - last[0]) + abs(y - last[1]) >= 0.5:
            pts.append((x, y))
            last = (x, y)
    if len(pts) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def near_view(poly: list, bbox: tuple) -> bool:
    """False for a piece of land well outside the view (it would only add weight, and in a conic map it can fill the frame)."""
    x0, y0, x1, y1 = bbox
    mx, my = (x1 - x0) * 0.4 + 2, (y1 - y0) * 0.4 + 2
    lons, lats = [p[0] for p in poly[0]], [p[1] for p in poly[0]]
    return not (max(lons) < x0 - mx or min(lons) > x1 + mx or max(lats) < y0 - my or min(lats) > y1 + my)


def land_paths(countries: list[dict], selected: set, to_px, size: tuple, whole: bool, bbox: tuple) -> list[str]:
    w, h = size
    out = []
    for c in countries:
        if whole and c["c"] == "Antarctica":
            continue                                  # a world map is about where people are; ask for Antarctica by name
        cls = "mm-land" if whole else ("mm-hl" if c["a"] in selected else "mm-ctx")
        ds = []
        for poly in polygons(c):
            if not near_view(poly, bbox):
                continue
            px = [to_px(lon, lat) for lon, lat in poly[0][::max(1, len(poly[0]) // 60)]]
            if max(p[0] for p in px) < -w * 0.1 or min(p[0] for p in px) > w * 1.1 or max(p[1] for p in px) < -h * 0.1 or min(p[1] for p in px) > h * 1.1:
                continue
            ds += [ring_d(r, to_px, size) for r in poly]
        d = "".join(ds)
        if d:
            out.append(f'<path class="{cls}" data-name={quoteattr(c["a"])} fill-rule="evenodd" d="{d}"/>')
    return out


def graticule(bbox: tuple, to_px) -> str:
    x0, y0, x1, y1 = bbox
    span = max(x1 - x0, y1 - y0)
    step = 10 if span < 40 else 20 if span < 100 else 30
    mx, my = (x1 - x0) * 0.3, (y1 - y0) * 0.3
    lons = range(int(math.floor((x0 - mx) / step)) * step, int(x1 + mx) + 1, step)
    lats = range(int(math.floor((y0 - my) / step)) * step, int(y1 + my) + 1, step)
    ds = []
    for lon in lons:
        if -180 <= lon <= 180:
            ds.append("M" + "L".join("%.1f %.1f" % to_px(lon, max(-85, min(85, y0 - my + (y1 - y0 + 2 * my) * i / 40))) for i in range(41)))
    for lat in lats:
        if -85 <= lat <= 85:
            ds.append("M" + "L".join("%.1f %.1f" % to_px(max(-180, min(180, x0 - mx + (x1 - x0 + 2 * mx) * i / 60)), lat) for i in range(61)))
    return f'<path class="mm-grid" d="{"".join(ds)}"/>'


STYLE = """.mm-sea{fill:var(--map-sea,none)}.mm-grid{fill:none;stroke:var(--map-grid,#8a8f99);stroke-opacity:.18;stroke-width:1}
.mm-land{fill:var(--map-land,#2f3238);stroke:var(--map-edge,#4a4e57);stroke-width:1.2;stroke-linejoin:round}
.mm-ctx{fill:var(--map-ctx,#25282d);stroke:var(--map-edge,#3b3f46);stroke-width:1;stroke-linejoin:round}
.mm-hl{fill:var(--map-hl,#4b4635);stroke:var(--map-hl-edge,#c8a24a);stroke-width:1.6;stroke-linejoin:round}
.mm-route{fill:none;stroke:var(--map-route,#e0b84f);stroke-width:5;stroke-linecap:round;stroke-linejoin:round}
.mm-dot{fill:var(--map-dot,#f3eee2);stroke:var(--map-halo,#14161a);stroke-width:3}.mm-ring{fill:none;stroke:var(--map-route,#e0b84f);stroke-width:2.5;opacity:.0}
.mm-label{font-family:var(--map-font,Georgia,serif);fill:var(--map-text,#f3eee2);paint-order:stroke;stroke:var(--map-halo,#14161a);stroke-width:7px;stroke-linejoin:round}"""


def build_map(region_spec: str, points: list, routes: list, size: tuple = (1600, 900), countries: list | None = None,
              font: int = 40, grid: bool = True) -> tuple[str, dict]:
    countries = countries if countries is not None else load_countries()
    pts = [parse_point(p) if isinstance(p, str) else p for p in points]
    legs = [parse_route(r, pts) for r in routes]
    region = resolve_region(region_spec, countries)
    x0, y0, x1, y1 = region.bbox
    if pts:
        x0, y0 = min(x0, min(p["lon"] for p in pts)), min(y0, min(p["lat"] for p in pts))
        x1, y1 = max(x1, max(p["lon"] for p in pts)), max(y1, max(p["lat"] for p in pts))
    bbox = (x0, y0, x1, y1)
    name, params = choose_projection(bbox)
    to_px = _fit(projector(name, params), bbox, size)
    whole = len(region.selected) == len(countries) or not region.selected
    body = [f'<rect class="mm-sea" width="{size[0]}" height="{size[1]}"/>']
    if grid:
        body.append(graticule(bbox, to_px))
    body += land_paths(countries, {c["a"] for c in region.selected}, to_px, size, whole, bbox)
    markers = [{**p, "x": round(to_px(p["lon"], p["lat"])[0], 1), "y": round(to_px(p["lon"], p["lat"])[1], 1)} for p in pts]
    by_name = {m["name"]: m for m in markers}
    route_meta = []
    for i, leg in enumerate(legs, 1):
        d, length = quad_path([(by_name[n]["x"], by_name[n]["y"]) for n in leg])
        route_meta.append({"id": f"route-{i}", "points": leg, "length": round(length, 1)})
        body.append(f'<path id="route-{i}" class="mm-route" data-from={quoteattr(leg[0])} data-to={quoteattr(leg[-1])} data-len="{length:.1f}" d="{d}"/>')
    labels = place_labels(markers, size, font)
    for m in markers:
        body.append(f'<circle class="mm-ring" data-name={quoteattr(m["name"])} cx="{m["x"]}" cy="{m["y"]}" r="22"/>'
                    f'<circle class="mm-dot" data-name={quoteattr(m["name"])} cx="{m["x"]}" cy="{m["y"]}" r="9"/>')
    for lab in labels:
        body.append(f'<text class="mm-label" data-name={quoteattr(lab["name"])} x="{lab["x"]}" y="{lab["baseline"]}" font-size="{font}">{escape(lab["name"])}</text>')
    title = f"Map of {region.label}"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size[0]} {size[1]}" width="{size[0]}" height="{size[1]}" role="img">'
           f"<title>{escape(title)}</title><style>{STYLE}</style>" + "".join(body) + "</svg>\n")
    meta = {"region": region.label, "projection": {"name": name, "params": params}, "bbox": [round(v, 3) for v in bbox], "size": list(size),
            "markers": markers, "labels": labels, "routes": route_meta, "data": "Natural Earth, public domain"}
    return svg, meta


def list_names(countries: list[dict]) -> str:
    return "Continents: " + ", ".join(CONTINENTS) + ", and world\nCountries: " + ", ".join(sorted(c["a"] for c in countries))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", help="country, countries, continent, world or bbox:minlon,minlat,maxlon,maxlat")
    ap.add_argument("--point", action="append", default=[], help="Name=lat,lon (repeat)")
    ap.add_argument("--route", action="append", default=[], help="Name>Name>Name (repeat)")
    ap.add_argument("--out", help="the SVG to write; a .json with the positions is written next to it")
    ap.add_argument("--size", default="1600x900", help="WxH in pixels (default 1600x900)")
    ap.add_argument("--font", type=int, default=40, help="label size in pixels (default 40)")
    ap.add_argument("--no-grid", action="store_true", help="leave out the faint latitude and longitude lines")
    ap.add_argument("--geojson", help="use this Natural Earth style file instead of the shipped subset")
    ap.add_argument("--list", action="store_true", help="print every name the data knows")
    args = ap.parse_args(argv)
    try:
        countries = load_countries(args.geojson)
        if args.list:
            print(list_names(countries))
            return 0
        if not (args.region and args.out):
            ap.error("--region and --out are required (or --list)")
        w, h = (int(v) for v in args.size.lower().split("x"))
        svg, meta = build_map(args.region, args.point, args.route, (w, h), countries, args.font, not args.no_grid)
    except (MapError, ValueError) as err:
        print(f"FAIL  make_map: {err}")
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8", newline="\n")
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS  {out} ({len(svg) / 1024:.0f} KB, {meta['projection']['name']}, {len(meta['markers'])} marker(s), {len(meta['routes'])} route(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
