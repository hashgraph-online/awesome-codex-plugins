#!/usr/bin/env python3
"""Audit staging.json with numbers, before any render. Python standard library only.

  python3 check_staging.py staging.json

For every shot (start, middle, end) it reports the shot size, angle, lens and move, and whether each subject is in
frame, blocked by a box, or has the camera inside geometry. It also runs the pin check (where a key point lands in
the frame against where it sits in the reference) and flags a timeline with gaps or the same move in every shot.
Exit code 1 means there is an error to fix. Numbers catch mistakes, not taste: look at the frames afterwards.
"""
import json
import math
import sys
from pathlib import Path


def add(a, b): return [x + y for x, y in zip(a, b)]
def sub(a, b): return [x - y for x, y in zip(a, b)]
def mul(a, k): return [x * k for x in a]
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def norm(a): return math.sqrt(dot(a, a))
def unit(a): n = norm(a) or 1e-9; return [x / n for x in a]


def smooth(x): return x * x * (3 - 2 * x)


def ease(kind, x):
    x = max(0, min(1, x))
    return {"linear": x, "in": x * x, "out": 1 - (1 - x) ** 2, "hold": 0}.get(kind, smooth(x))


def lerp_keys(keys, t, get):
    if t <= keys[0]["t"]:
        return get(keys[0])
    for a, b in zip(keys, keys[1:]):
        if t <= b["t"]:
            x = smooth((t - a["t"]) / max(b["t"] - a["t"], 1e-6))
            return [u + (v - u) * x for u, v in zip(get(a), get(b))]
    return get(keys[-1])


def cam_at(s, lt):
    if "keys" in s:
        K = s["keys"]
        i = 0
        while i < len(K) - 2 and lt > K[i + 1]["t"]:
            i += 1
        p, q = K[i], K[min(i + 1, len(K) - 1)]
        x = ease(s.get("ease", "linear"), (lt - p["t"]) / max(q["t"] - p["t"], 1e-6))
        L0, L1 = p.get("lens", s.get("lens", 35)), q.get("lens", s.get("lens", 35))
        return ([u + (v - u) * x for u, v in zip(p["pos"], q["pos"])], [u + (v - u) * x for u, v in zip(p["look"], q["look"])],
                L0 + (L1 - L0) * x, p.get("roll", 0) + (q.get("roll", 0) - p.get("roll", 0)) * x)
    x = ease(s.get("ease", "smooth"), lt / max(s["end"] - s["start"], 1e-6))
    a, b = s["from"], s.get("to", s["from"])
    look = [u + (v - u) * x for u, v in zip(a["look"], b["look"])]
    if s.get("path") == "arc":
        pa, pb = sub(a["pos"], look), sub(b["pos"], look)
        aa, ab = math.atan2(pa[1], pa[0]), math.atan2(pb[1], pb[0])
        d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
        ra, rb = math.hypot(pa[0], pa[1]), math.hypot(pb[0], pb[1])
        r, ang = ra + (rb - ra) * x, aa + d * x
        pos = [look[0] + r * math.cos(ang), look[1] + r * math.sin(ang), look[2] + pa[2] + (pb[2] - pa[2]) * x]
    else:
        pos = [u + (v - u) * x for u, v in zip(a["pos"], b["pos"])]
    la, lb = a.get("lens", s.get("lens", 35)), b.get("lens", s.get("lens", 35))
    return pos, look, la + (lb - la) * x, a.get("roll", 0) + (b.get("roll", 0) - a.get("roll", 0)) * x


class Cam:
    def __init__(self, pos, look, lens, W, H, sensor=36, vp=(.5, .5), roll=0):
        self.p, self.W, self.H, self.vp = pos, W, H, vp
        self.f = unit(sub(look, pos))
        r = unit(cross(self.f, [0, 0, 1]))
        u = cross(r, self.f)
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        self.r, self.u = add(mul(r, c), mul(u, s)), add(mul(r, -s), mul(u, c))
        self.fpx = lens / sensor * max(W, H)
        self.lens = lens

    def project(self, w):
        d = sub(w, self.p)
        z = dot(d, self.f)
        if z <= 1e-4:
            return None
        return (self.vp[0] + dot(d, self.r) * self.fpx / z / self.W, self.vp[1] - dot(d, self.u) * self.fpx / z / self.H, z)


def size_word(h_m):
    for lim, w in ((.2, "ECU"), (.4, "CU"), (.7, "MCU"), (1.1, "MS"), (1.5, "MLS"), (2.4, "FS"), (8, "WS")):
        if h_m < lim:
            return w
    return "EWS"


def angle_word(pitch):
    if pitch < -60: return "top"
    if pitch < -15: return "high"
    if pitch <= 15: return "eye level"
    if pitch <= 60: return "low"
    return "worm's eye"


def box_hit(p, q, b):
    """Does the segment p->q pass through this box? rot_z is ignored: a slight rotation won't change the answer much."""
    tmin, tmax = 0.0, 1.0
    for i in range(3):
        lo, hi = b["center"][i] - b["size"][i] / 2, b["center"][i] + b["size"][i] / 2
        d = q[i] - p[i]
        if abs(d) < 1e-9:
            if p[i] < lo or p[i] > hi:
                return False
        else:
            t1, t2 = (lo - p[i]) / d, (hi - p[i]) / d
            tmin, tmax = max(tmin, min(t1, t2)), min(tmax, max(t1, t2))
            if tmin > tmax:
                return False
    return True


def inside(p, b, pad=.02):
    return all(abs(p[i] - b["center"][i]) < b["size"][i] / 2 - pad for i in range(3))


def fig_points(f, t):
    """Head and feet points of a figure at time t."""
    if f.get("style") == "joints":
        head = lerp_keys(f["keys"], t, lambda k: k["joints"]["head"])
        ft = lerp_keys(f["keys"], t, lambda k: k["joints"]["ftL"])
        return head, ft, norm(sub(head, ft)) + .11
    h = f.get("height", 1.75)
    p = lerp_keys(f["keys"], t, lambda k: k["pos"])
    return add(p, [0, 0, h * .9]), p, h


def main():
    S = json.loads(Path(sys.argv[1]).read_text())
    W, H = S["frame"]["w"], S["frame"]["h"]
    errors, warnings = [], []
    figs = {f["name"]: f for f in S.get("figures", [])}
    solid = [b for b in S.get("boxes", []) if not b.get("no_block")]
    moves = []
    prev_end = None
    print(f"{S.get('title', '')}: {W}x{H}, {S['frame']['fps']} fps, {len(S['shots'])} shots")
    for s in S["shots"]:
        if prev_end is not None and abs(s["start"] - prev_end) > 1e-3:
            warnings.append(f"{s['id']}: starts at {s['start']} but the shot before ends at {prev_end}")
        prev_end = s["end"]
        dur = s["end"] - s["start"]
        pa, la, ln0, ro0 = cam_at(s, 0)
        pb, lb, ln1, _ = cam_at(s, dur)
        travel = norm(sub(pb, pa))
        dpa, dpb = norm(sub(la, pa)), norm(sub(lb, pb))
        turn = math.degrees(math.acos(max(-1, min(1, dot(unit(sub(la, pa)), unit(sub(lb, pb)))))))
        if s.get("path") == "arc": mv = "orbit"
        elif travel < .02 and turn < .5 and abs(ln1 - ln0) < .5: mv = "locked"
        elif abs(ln1 - ln0) >= .5 and travel < .02: mv = "zoom"
        elif travel < .02: mv = "pan/tilt"
        elif dpb < dpa - .05: mv = "push in"
        elif dpb > dpa + .05: mv = "pull out"
        else: mv = "track"
        moves.append(mv)
        vp = s.get("vp", (.5, .5))
        cam0 = Cam(pa, la, ln0, W, H, vp=vp, roll=ro0)
        pitch = math.degrees(math.asin(max(-1, min(1, -cam0.f[2]))))
        # frame height at the first subject, else at the look point
        d0 = norm(sub(la, pa))
        for name in s.get("subjects", []):
            if name in figs:
                pj = cam0.project(fig_points(figs[name], s["start"])[0])
                if pj:
                    d0 = pj[2]
                break
        vis_h = 2 * d0 * (H / 2) / cam0.fpx
        print(f"{s['id']} {s['start']:.2f}-{s['end']:.2f}s  {size_word(vis_h)}  {angle_word(pitch)}  {ln0:.0f}"
              + (f"-{ln1:.0f}" if abs(ln1 - ln0) >= .5 else "") + f" mm  {mv}, travels {travel:.2f} m, turns {turn:.1f} deg")
        for lt in (0, dur / 2, max(dur - 1 / S["frame"]["fps"], 0)):
            pos, look, ln, ro = cam_at(s, lt)
            cam = Cam(pos, look, ln, W, H, vp=vp, roll=ro)
            for b in solid:
                if inside(pos, b):
                    errors.append(f"{s['id']} t={lt:.2f}: camera is inside '{b['name']}'")
            for name in s.get("subjects", []):
                f = figs.get(name)
                if lt < s.get("visible_from", {}).get(name, 0):
                    continue      # a deliberate reveal: this subject only has to be seen from that moment
                if not f:
                    errors.append(f"{s['id']}: subject '{name}' does not exist")
                    continue
                head, feet, _ = fig_points(f, s["start"] + lt)
                pj = cam.project(head)
                if pj is None:
                    errors.append(f"{s['id']} t={lt:.2f}: {name} is behind the camera")
                    continue
                u, v, z = pj
                if not (0 <= u <= 1 and 0 <= v <= 1):
                    errors.append(f"{s['id']} t={lt:.2f}: {name}'s head is out of frame at ({u:.2f}, {v:.2f})")
                elif not (.05 <= u <= .95 and .05 <= v <= .95):
                    warnings.append(f"{s['id']} t={lt:.2f}: {name}'s head is on the edge at ({u:.2f}, {v:.2f})")
                for b in solid:
                    if box_hit(pos, head, b):
                        errors.append(f"{s['id']} t={lt:.2f}: '{b['name']}' blocks {name}'s head")
                if z < .35:
                    warnings.append(f"{s['id']} t={lt:.2f}: the camera is {z:.2f} m from {name}'s head")
    # Frames can look clean while a figure walks through the set between them, so check every eighth of a second
    still_boxes = [b for b in solid if "keys" not in b]
    end = max(s["end"] for s in S["shots"])
    for name, f in figs.items():
        hits = {}
        for i in range(int(end * 8) + 1):
            T = i / 8
            head, feet, h = fig_points(f, T)
            for share in (.2, .5, .8):
                pt = [feet[k] + (head[k] - feet[k]) * share for k in range(3)]
                for b in still_boxes:
                    if inside(pt, b, pad=.01):
                        hits.setdefault(b["name"], T)
        for bname, T in hits.items():
            errors.append(f"{name} passes through '{bname}' at about {T:.2f} s")
    # Figures that overlap in frame must differ in brightness, or they merge in a greyscale clip
    def lum(c):
        return c if isinstance(c, (int, float)) else .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
    def bright(f):
        return lum(f.get("top", .3)) if f.get("style") == "joints" else lum(f.get("color", .5))
    names = list(figs)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if abs(bright(figs[a]) - bright(figs[b])) >= .12:
                continue
            for s in S["shots"]:
                hit = False
                for k in range(9):
                    lt = (s["end"] - s["start"]) * k / 8
                    pos, look, ln, ro = cam_at(s, lt)
                    cam = Cam(pos, look, ln, W, H, vp=s.get("vp", (.5, .5)), roll=ro)
                    pa_, pb_ = cam.project(fig_points(figs[a], s["start"] + lt)[0]), cam.project(fig_points(figs[b], s["start"] + lt)[0])
                    if pa_ and pb_ and abs(pa_[0] - pb_[0]) < .08 and 0 <= pa_[0] <= 1:
                        hit = True
                if hit:
                    warnings.append(f"{s['id']}: {a} and {b} overlap with nearly the same brightness: they merge in greyscale")
    if len(moves) >= 3 and len(set(moves)) == 1:
        warnings.append(f"every shot has the same move ('{moves[0]}'): vary the coverage")
    for f in S.get("figures", []):
        if f.get("style") != "joints":
            h = f.get("height", 1.75)
            if not .8 <= h <= 2.3:
                warnings.append(f"{f['name']}: height {h} m, is that right?")
            z = f["keys"][0]["pos"][2]
            if z < -.02:
                errors.append(f"{f['name']}: below the ground at z={z}")
    worst = 0.0
    if S.get("pins"):
        print("pins (where it lands vs where the reference has it; % of the frame). A pin placed from its own reading proves only the maths:")
        for name, pin in S["pins"].items():
            w, want = pin[0], pin[1]
            T = pin[2] if len(pin) > 2 else S.get("pins_at", 0)    # a third value is the time on the film, in seconds
            s0 = next((x for x in S["shots"] if x["start"] <= T < x["end"]), S["shots"][0])
            pos, look, ln, ro = cam_at(s0, T - s0["start"])
            cam = Cam(pos, look, ln, W, H, vp=s0.get("vp", (.5, .5)), roll=ro)
            pj = cam.project(w)
            if pj is None:
                errors.append(f"pin {name}: behind the camera")
                continue
            e = 100 * math.hypot(pj[0] - want[0], pj[1] - want[1])
            worst = max(worst, e)
            print(f"  {name:20s} got ({pj[0]:.3f}, {pj[1]:.3f})  want ({want[0]:.3f}, {want[1]:.3f})  off {e:.1f}%")
        if worst > 5:
            warnings.append(f"worst pin is {worst:.1f}% off: fix the staging before rendering")
    for w in sorted(set(warnings)):
        print("warning:", w)
    for e in sorted(set(errors)):
        print("ERROR:", e)
    print("check ok" if not errors else f"{len(set(errors))} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
