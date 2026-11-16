"""Spec for example 04: a small desk gadget made of five stacked parts (Manifold booleans).

Millimetres, Z-up. Every part is centred on its own origin, because a physics body is placed by
its origin and the part then falls and settles into the stack. Run one part at a time:

    python -m b2m3d model device.py build/shell.glb --param part=shell

Colours here are placeholders; `b2m3d material assign` gives each part its real material.
"""
from manifold3d import CrossSection, JoinType, Manifold

PARAMS = {"part": "all"}


def slab(width, depth, height, radius):
    """Rounded-rectangle prism, centred on the origin."""
    outline = CrossSection.square((width - 2 * radius, depth - 2 * radius), True).offset(
        radius, JoinType.Round, 2.0, 32)
    solid = Manifold.extrude(outline, height)
    return solid.translate([0, 0, -height / 2])


def centred(solid):
    x0, y0, z0, x1, y1, z1 = solid.bounding_box()
    return solid.translate([-(x0 + x1) / 2, -(y0 + y1) / 2, -(z0 + z1) / 2])


def shell():
    tray = slab(60, 40, 10, 7)
    pocket = slab(52, 32, 2, 4).translate([0, 0, 4.5])
    return tray - pocket


def cell():
    return slab(50, 30, 6, 4)


def board():
    base = slab(56, 36, 2, 3)
    chips = [Manifold.cube([10, 10, 1.2], True).translate([-12, 0, 1.6]),
             Manifold.cube([14, 6, 1.0], True).translate([10, 7, 1.5]),
             Manifold.cube([6, 6, 1.4], True).translate([13, -8, 1.7])]
    for chip in chips:
        base = base + chip
    return centred(base)


def cover():
    return slab(60, 40, 5, 7)


def lens():
    return Manifold.cylinder(3, 9, 8, 64, True)


PARTS = {
    "shell": (shell, [0.05, 0.05, 0.055, 1.0], 0.0, 0.7),
    "cell": (cell, [0.8, 0.8, 0.82, 1.0], 1.0, 0.35),
    "board": (board, [0.006, 0.045, 0.02, 1.0], 0.0, 0.4),
    "cover": (cover, [0.9, 0.9, 0.88, 1.0], 0.0, 0.25),
    "lens": (lens, [0.2, 0.2, 0.24, 1.0], 0.0, 0.1),
}


def build(params):
    wanted = list(PARTS) if params["part"] == "all" else [params["part"]]
    unknown = [w for w in wanted if w not in PARTS]
    if unknown:
        raise ValueError(f"unknown part {unknown}; choose one of {', '.join(PARTS)} or 'all'")
    out = []
    for name in wanted:
        make, color, metallic, roughness = PARTS[name]
        out.append({"name": name, "geom": make(), "color": color, "metallic": metallic,
                    "roughness": roughness})
    return out
