#!/usr/bin/env python3
"""Stage Caravaggio's The Calling of Saint Matthew (1600, public domain) from picture coordinates: staging.json.

Every joint is read off the painting as (u, v) plus a depth. A standing man's head and feet gave the depth (3.1 m) and
the eye height (1.37 m). Check: the table top then comes out at 0.76 m with no one asking for it.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from place import Frame

F = Frame(1000, 1028, lens=35, eye=1.37)
U = F.world


def fig(name, d, top, legs, **j):
    return dict(name=name, style="joints", top=top, legs=legs,
                keys=[dict(t=0, joints={k: U(v[0], v[1], v[2] if len(v) > 2 else d) for k, v in j.items()})])


figures = [
    fig("peter", 3.1, .42, .14, head=(.79, .415), neck=(.80, .475), hip=(.86, .69), shL=(.76, .49), shR=(.85, .50),
        elL=(.775, .53, 2.95), haL=(.735, .54, 2.85), elR=(.85, .61), haR=(.78, .665), knL=(.85, .84), knR=(.92, .80),
        ftL=(.86, .93), ftR=(.97, .97)),
    fig("christ", 3.5, .05, .05, head=(.865, .385), neck=(.87, .44), hip=(.92, .70), shL=(.815, .47), shR=(.93, .49),
        elL=(.72, .445, 3.4), haL=(.645, .425, 3.3), elR=(.95, .6), haR=(.95, .7), knL=(.90, .85), knR=(.97, .85),
        ftL=(.91, .90), ftR=(.98, .90)),
    fig("swordsman", 3.0, .04, .50, head=(.575, .52), neck=(.56, .58), hip=(.50, .76), shL=(.47, .60), shR=(.60, .62),
        elL=(.44, .63), haL=(.43, .68), elR=(.58, .70), haR=(.52, .72), knL=(.42, .81), knR=(.585, .78),
        ftL=(.44, .96), ftR=(.555, .93)),
    fig("youth", 3.75, .34, .34, head=(.42, .49), neck=(.42, .535), hip=(.40, .66), shL=(.36, .535), shR=(.50, .56),
        elL=(.35, .60), haL=(.38, .585), elR=(.46, .60), haR=(.42, .635), knL=(.34, .73), knR=(.46, .73),
        ftL=(.36, .87), ftR=(.45, .885)),
    fig("bearded", 3.8, .03, .24, head=(.265, .475), neck=(.27, .53), hip=(.27, .66), shL=(.23, .55), shR=(.33, .54),
        elL=(.24, .62), haL=(.30, .65), elR=(.35, .57), haR=(.30, .555), knL=(.26, .75), knR=(.33, .75),
        ftL=(.21, .88), ftR=(.37, .89)),
    fig("old", 4.0, .04, .12, head=(.16, .455), neck=(.15, .52), hip=(.10, .66), shL=(.09, .54), shR=(.21, .52),
        elL=(.07, .62), haL=(.15, .655), elR=(.235, .50), haR=(.20, .47), knL=(.08, .72), knR=(.14, .72),
        ftL=(.10, .86), ftR=(.16, .86)),
    fig("coins", 3.3, .30, .30, head=(.19, .555), neck=(.14, .58), hip=(.05, .72), shL=(.07, .58), shR=(.19, .61),
        elL=(.06, .66), haL=(.10, .64), elR=(.20, .62), haR=(.20, .65), knL=(.15, .77), knR=(.12, .75),
        ftL=(.10, .95), ftR=(.06, .93)),
]


def box(name, x0, x1, y0, y1, z0, z1, grey):
    return dict(name=name, center=[(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], size=[x1 - x0, y1 - y0, z1 - z0], grey=grey)


WALL = 5.0
wx = lambda u: U(u, .5, WALL)[0]
wz = lambda v: U(.5, v, WALL)[2]
l, r, sill, top = wx(.565), wx(.785), wz(.34), wz(-.02)
boxes = [
    box("floor", -8, 8, -3, 9, -.1, 0, .07),
    box("back_wall", -8, 8, WALL, WALL + .2, 0, 6, .30),
    box("window", l, r, WALL - .06, WALL, sill, top, .42),
    box("mullion_v", (l + r) / 2 - .04, (l + r) / 2 + .04, WALL - .1, WALL - .06, sill, top, .05),
    box("mullion_h", l, r, WALL - .1, WALL - .06, (sill + top) / 2 - .04, (sill + top) / 2 + .04, .05),
    box("shutter", wx(.465), wx(.565), WALL - .35, WALL - .29, sill, top, .10),
    box("table", -1.2, -.35, 3.15, 3.95, .735, .775, .18),
    dict(box("table_body", -1.15, -.40, 3.25, 3.85, 0, .735, .06), no_block=True),   # the painted figures sit into it
    dict(box("stool", -.12, .15, 2.85, 3.15, 0, .5, .13), no_block=True),
]

# One hard source, high and right, outside the frame. Its shadow edge is the composition. Two flags cut it.
L = [3.6, -.6, 4.6]
through = lambda p, t=.35: [L[i] + t * (p[i] - L[i]) for i in range(3)]
a, b = [wx(1.08), WALL, wz(.27)], [wx(.48), WALL, wz(.46)]
diag = [through(a), through(b), through([b[0], WALL, b[2] - 1.0]), through([a[0], WALL, a[2] - 3.0])]
c, d = [wx(-.3), WALL, wz(.35)], [wx(.47), WALL, wz(.35)]
top_flag = [through(c), through(d), through([d[0], WALL, 8]), through([c[0], WALL, 8])]

scene = dict(
    title="The Calling of Saint Matthew: staging",
    frame=dict(w=1000, h=1028, fps=24),
    shots=[dict(id="s01", start=0, end=4, lens=35, subjects=["peter", "youth", "bearded", "swordsman"],
                ease="smooth", **{"from": dict(pos=[0, 0, 1.37], look=[0, 10, 1.37]),
                                  "to": dict(pos=[.12, 1.1, 1.37], look=[.30, 10, 1.32])})],
    boxes=boxes,
    flags=[dict(name="flag_diagonal", verts=diag), dict(name="flag_top", verts=top_flag)],
    figures=figures,
    skin=.60,
    key=dict(pos=L, aim=[-.2, 4, 1.5], angle_deg=62, power_three=320, power_blender=3800, color=[1.0, .80, .55]),
    fill=.012,
    pins={
        "pointing_hand": [U(.645, .425, 3.3), [.645, .425]],
        "peter_head": [U(.79, .415, 3.1), [.79, .415]],
        "youth_head": [U(.42, .49, 3.75), [.42, .49]],
        "bearded_head": [U(.265, .475, 3.8), [.265, .475]],
        "swordsman_head": [U(.575, .52, 3.0), [.575, .52]],
        "window_sill_left": [[l, WALL - .06, sill], [.565, .34]],
        "table_right": [[-.35, 3.55, .775], [.405, .68]],
    },
)
out = Path(__file__).with_name("staging.json")
out.write_text(json.dumps(scene, indent=1))
print("wrote", out)
