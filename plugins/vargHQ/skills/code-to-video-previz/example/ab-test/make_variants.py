#!/usr/bin/env python3
"""Write 4 staging files for one 5 s shot: grey or colour, capsule or jointed. Same camera, same paths, same timing.

Run one short generation per variant with the same prompt and references, then compare. This settles, for your model,
two open questions: does a guide clip work better grey or in colour, and do stand-ins work better with or without limbs.

  python3 make_variants.py              writes grey_capsule.json, colour_capsule.json, grey_joints.json, colour_joints.json
  bun ../../scripts/stage_three.ts grey_capsule.json film all grey_capsule.mp4 --flat --grey
  bun ../../scripts/stage_three.ts colour_capsule.json film all colour_capsule.mp4 --flat
"""
import json
import math
from pathlib import Path

DUR, STEP = 5.0, .125
HERE = Path(__file__).parent


def walk_joints(x, y, heading_x, t, height=1.75):
    """A plain walk cycle in world coordinates: one figure walking along x."""
    s = 2.0 * math.pi * t / 1.05         # one stride cycle in 1.05 s
    d = 1 if heading_x >= 0 else -1
    swing = .30 * math.sin(s)
    h = height / 1.75
    hip = [x, y, .95 * h]
    neck = [x + .02 * d, y, 1.45 * h]
    head = [x + .03 * d, y, 1.62 * h]
    shL, shR = [x, y + .19, 1.42 * h], [x, y - .19, 1.42 * h]
    elL = [x - swing * .55 * d, y + .21, 1.14 * h]
    haL = [x - swing * d, y + .22, .90 * h]
    elR = [x + swing * .55 * d, y - .21, 1.14 * h]
    haR = [x + swing * d, y - .22, .90 * h]
    lift = lambda a: max(0, a) * .12
    knL = [x + swing * .55 * d, y + .10, .50 * h + lift(math.cos(s))]
    ftL = [x + swing * 1.1 * d, y + .10, .05 + lift(math.cos(s))]
    knR = [x - swing * .55 * d, y - .10, .50 * h + lift(-math.cos(s))]
    ftR = [x - swing * 1.1 * d, y - .10, .05 + lift(-math.cos(s))]
    return dict(head=head, neck=neck, hip=hip, shL=shL, shR=shR, elL=elL, elR=elR, haL=haL, haR=haR,
                knL=knL, knR=knR, ftL=ftL, ftR=ftR)


PEOPLE = [
    dict(name="a", x0=-3.2, x1=.4, y=2.0, grey=.82, colour=[.85, .12, .10]),
    dict(name="b", x0=3.2, x1=-.2, y=3.2, grey=.22, colour=[.10, .22, .80]),
]


def figure(p, style, colour):
    c = p["colour"] if colour else p["grey"]
    head = .65 if not colour else None
    if style == "capsule":
        f = dict(name=p["name"], height=1.75, color=c, keys=[
            dict(t=0, pos=[p["x0"], p["y"], 0], heading=90 if p["x1"] > p["x0"] else 270),
            dict(t=DUR, pos=[p["x1"], p["y"], 0], heading=90 if p["x1"] > p["x0"] else 270)])
        if head:
            f["head"] = head
        return f
    keys = []
    n = int(DUR / STEP)
    for i in range(n + 1):
        t = i * STEP
        keys.append(dict(t=round(t, 3), joints=walk_joints(p["x0"] + (p["x1"] - p["x0"]) * t / DUR, p["y"], p["x1"] - p["x0"], t)))
    return dict(name=p["name"], style="joints", top=c, legs=c, keys=keys)


def scene(style, colour):
    return dict(
        title=f"A/B test: {'colour' if colour else 'grey'} {style}", frame=dict(w=854, h=480, fps=24),
        shots=[dict(id="s01", start=0, end=DUR, lens=35, ease="smooth", subjects=["a", "b"],
                    **{"from": dict(pos=[0, -5.5, 1.5], look=[0, 2.5, 1.2]), "to": dict(pos=[.2, -3.8, 1.45], look=[.1, 2.5, 1.2])})],
        boxes=[dict(name="floor", center=[0, 3, -.05], size=[20, 20, .1], grey=.45),
               dict(name="wall", center=[0, 6.1, 2], size=[20, .2, 4], grey=.6),
               dict(name="door", center=[-2.5, 6, 1.05], size=[1, .1, 2.1], grey=.3),
               dict(name="pillar", center=[2.6, 5, 1.5], size=[.5, .5, 3], grey=.5, no_block=True)],
        figures=[figure(p, style, colour) for p in PEOPLE],
        skin=.65, fill=.5)


for style in ("capsule", "joints"):
    for colour in (False, True):
        name = f"{'colour' if colour else 'grey'}_{style}.json"
        (HERE / name).write_text(json.dumps(scene(style, colour)))
        print("wrote", name)
