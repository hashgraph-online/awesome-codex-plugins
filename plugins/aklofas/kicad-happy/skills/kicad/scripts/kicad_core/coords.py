"""Schematic coordinate identity in KiCad internal units (kicad_core).

KiCad schematics store every coordinate as an integer of 100 nm (1e4 per mm) and join
connection points only when those integers are equal. Analyzer output keeps millimetre
floats; these helpers give the integer identity used for joining.
"""

IU_PER_MM = 10000


def to_iu(mm: float) -> int:
    """Millimetres to schematic internal units, rounded half away from zero as KiCad's KiROUND."""
    v = mm * IU_PER_MM
    return int(v + 0.5) if v >= 0 else int(v - 0.5)


def _sq_distance(p, a, b) -> int:
    """Squared distance from point p to segment a-b, in IU squared, rounded as KiCad's SEG."""
    abx, aby = b[0] - a[0], b[1] - a[1]
    apx, apy = p[0] - a[0], p[1] - a[1]
    e = apx * abx + apy * aby
    if e <= 0:
        return apx * apx + apy * apy
    f = abx * abx + aby * aby
    if e >= f:
        bpx, bpy = p[0] - b[0], p[1] - b[1]
        return bpx * bpx + bpy * bpy
    cross = abx * apy - aby * apx
    q, r = divmod(cross * cross, f)
    return q + (1 if 2 * r >= f else 0)


def segment_hit_iu(p, a, b, dist_iu: int) -> bool:
    """Whether integer point p lies within dist_iu of segment a-b (KiCad's TestSegmentHit).

    dist_iu == 0 is KiCad's IsPointOnSegment: p exactly on the segment, ends included.
    """
    px, py = p
    ax, ay = a
    bx, by = b
    if dist_iu == 0:
        sx, sy = bx - ax, by - ay
        vx, vy = px - ax, py - ay
        if sx * vy - sy * vx:
            return False
        return sx * vx + sy * vy >= vx * vx + vy * vy
    xmin, xmax = (ax, bx) if ax <= bx else (bx, ax)
    ymin, ymax = (ay, by) if ay <= by else (by, ay)
    if ymin - py > dist_iu or py - ymax > dist_iu:
        return False
    if xmin - px > dist_iu or px - xmax > dist_iu:
        return False
    if ax == bx and ymin < py < ymax:
        return abs(ax - px) <= dist_iu
    if ay == by and xmin < px < xmax:
        return abs(ay - py) <= dist_iu
    return _sq_distance(p, a, b) < (dist_iu + 1) ** 2
