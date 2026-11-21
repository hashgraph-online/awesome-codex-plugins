"""Switching-regulator hot-loop area proxies, shared by the PCB analyzer and EMC SW-003.

The PCB analyzer measures a polygon through six pads in loop order: input-cap
supply pad, regulator supply pad, regulator SW pad, inductor SW pad, regulator
ground pad, input-cap ground pad (polygon_loop_area). The SW -> inductor ->
ground leg folds back across the input side, so the polygon often crosses
itself; the shoelace area then nets the crossing lobes against each other. It
is a placement proxy, not the exact loop (which also runs through vias and the
ground return).

EMC SW-003 without pad positions falls back to the triangle through the
footprint centres of the input capacitor, the regulator and the inductor
(triangle_loop_area).

Neither proxy gives an area when it is degenerate: under 1 mm² across a reach
of 2 mm or more. For the triangle that means the centres lie in a line; for
the polygon, the pads lie in a line or the loop crosses itself and its lobes
cancel. Either way the area says nothing about the loop.
"""

# Below this area, with two points at least DEGENERATE_MIN_SPAN_MM apart, the
# points lie in a line or a crossing loop's lobes cancel: not a compact loop.
DEGENERATE_MAX_AREA_MM2 = 1.0
DEGENERATE_MIN_SPAN_MM = 2.0


def triangle_loop_area(vertices) -> float | None:
    """Shoelace area in mm² of three (x, y) centres, or None when the triangle is degenerate.

    Degenerate: two centres coincide, or the area is under DEGENERATE_MAX_AREA_MM2
    while the longest side is at least DEGENERATE_MIN_SPAN_MM.
    """
    (ax, ay), (bx, by), (cx, cy) = vertices
    if (ax, ay) == (bx, by) or (bx, by) == (cx, cy) or (ax, ay) == (cx, cy):
        return None
    twice = 0.0
    for i in range(3):
        j = (i + 1) % 3
        twice += vertices[i][0] * vertices[j][1]
        twice -= vertices[j][0] * vertices[i][1]
    area = abs(twice) / 2.0
    longest = max(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5,
                  ((cx - bx) ** 2 + (cy - by) ** 2) ** 0.5,
                  ((ax - cx) ** 2 + (ay - cy) ** 2) ** 0.5)
    if area < DEGENERATE_MAX_AREA_MM2 and longest >= DEGENERATE_MIN_SPAN_MM:
        return None
    return area


def polygon_area(vertices) -> float:
    """Shoelace area in mm² of a closed polygon of (x, y) points in loop order."""
    n = len(vertices)
    twice = 0.0
    for i in range(n):
        j = (i + 1) % n
        twice += vertices[i][0] * vertices[j][1] - vertices[j][0] * vertices[i][1]
    return abs(twice) / 2.0


def polygon_loop_area(vertices) -> float | None:
    """polygon_area, or None when the polygon is degenerate.

    Degenerate: fewer than three distinct points, or an area under
    DEGENERATE_MAX_AREA_MM2 while two points are at least
    DEGENERATE_MIN_SPAN_MM apart. The pads then lie in a line, or the loop
    crosses itself and its lobes cancel.
    """
    if len(set(vertices)) < 3:
        return None
    area = polygon_area(vertices)
    span = max(((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
               for ax, ay in vertices for bx, by in vertices)
    if area < DEGENERATE_MAX_AREA_MM2 and span >= DEGENERATE_MIN_SPAN_MM:
        return None
    return area
