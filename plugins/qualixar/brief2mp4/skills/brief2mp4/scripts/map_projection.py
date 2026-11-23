"""map_projection.py: the three projections make_map.py chooses between, and the fit of a region to the frame.

Equal Earth (Savric, Patterson and Jenny 2018) for the world and wide regions, Albers equal-area conic for wide regions in the mid
latitudes, Mercator for small areas and the tropics. Each projector maps (longitude, latitude) in degrees to (x, y) with y pointing
north; `fit` scales and centres a region's box in a frame, flipping y. Standard library only.
"""
from __future__ import annotations

import math

PAD = 0.06                # blank margin around the map, as a share of the frame
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796


def choose_projection(bbox: tuple) -> tuple[str, dict]:
    x0, y0, x1, y1 = bbox
    lon_span, lat_span, mid_lon, mid_lat = x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2
    if lon_span >= 120 or lat_span >= 80:
        return "equal_earth", {"lon0": 0.0 if lon_span > 300 else round(mid_lon, 3)}
    if abs(mid_lat) >= 20 and lon_span >= 12:
        return "albers", {"lon0": round(mid_lon, 3), "lat0": round(mid_lat, 3), "phi1": round(y0 + lat_span / 6, 3), "phi2": round(y1 - lat_span / 6, 3)}
    return "mercator", {"lon0": round(mid_lon, 3)}


def _wrap(lon: float, lon0: float) -> float:
    """Degrees east of the centre meridian, within -180..180; a point exactly on the seam keeps its own side."""
    d = lon - lon0
    while d > 180.0:
        d -= 360.0
    while d < -180.0:
        d += 360.0
    return d


def projector(name: str, p: dict):
    """A function (lon, lat) -> (x, y), y pointing north, in radians-scale units; the caller fits it to the frame."""
    lon0 = p.get("lon0", 0.0)
    if name == "mercator":
        return lambda lon, lat: (math.radians(_wrap(lon, lon0)), math.asinh(math.tan(math.radians(max(-85.0, min(85.0, lat))))))
    if name == "equal_earth":
        def ee(lon, lat):
            t = math.asin(math.sqrt(3) / 2 * math.sin(math.radians(lat)))
            x = 2 * math.sqrt(3) * math.radians(_wrap(lon, lon0)) * math.cos(t) / (3 * (A1 + 3 * A2 * t ** 2 + t ** 6 * (7 * A3 + 9 * A4 * t ** 2)))
            return x, t * (A1 + A2 * t ** 2 + t ** 6 * (A3 + A4 * t ** 2))
        return ee
    if name == "albers":
        f1, f2, f0 = (math.radians(p[k]) for k in ("phi1", "phi2", "lat0"))
        n = (math.sin(f1) + math.sin(f2)) / 2 or 1e-9
        c = math.cos(f1) ** 2 + 2 * n * math.sin(f1)
        rho0 = math.sqrt(c - 2 * n * math.sin(f0)) / n

        def alb(lon, lat):
            rho = math.sqrt(max(0.0, c - 2 * n * math.sin(math.radians(lat)))) / n
            th = n * math.radians(_wrap(lon, lon0))
            return rho * math.sin(th), rho0 - rho * math.cos(th)
        return alb
    raise ValueError(f"unknown projection '{name}'")




def fit(proj, bbox: tuple, size: tuple):
    x0, y0, x1, y1 = bbox
    steps = 24
    edge = [(x0 + (x1 - x0) * i / steps, y) for i in range(steps + 1) for y in (y0, y1)] + [(x, y0 + (y1 - y0) * i / steps) for i in range(steps + 1) for x in (x0, x1)]
    xs, ys = zip(*(proj(lon, lat) for lon, lat in edge))
    w, h = size
    s = min(w * (1 - 2 * PAD) / ((max(xs) - min(xs)) or 1e-9), h * (1 - 2 * PAD) / ((max(ys) - min(ys)) or 1e-9))
    ox, oy = (w - s * (max(xs) + min(xs))) / 2, (h + s * (max(ys) + min(ys))) / 2
    return lambda lon, lat: (ox + s * proj(lon, lat)[0], oy - s * proj(lon, lat)[1])
