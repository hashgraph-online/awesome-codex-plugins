#!/usr/bin/env python3
"""check_clutter.py: is any frame crowded? Reads text and card boxes, applies four layout rules.

The rules (each sample time is checked on its own):
  1. No card on card: two card boxes never overlap (--allow-nested lets one sit fully inside another).
     A text box may sit fully inside a card or fully outside it, but never straddle its edge.
  2. At least 24 px between any two text blocks, zero tolerance. Overlapping text boxes always fail.
  3. At most 4 text blocks on screen at once. Two facts that both need the screen are shown one after the other.
  A text block is one box, or several lines stacked as one group: boxes whose x-ranges overlap and whose
  vertical gap is under 0.25x the shorter line's height (a title over its subtitle, the lines of a lockup).
  4. Nothing clipped: no text box may run past the frame edge, because a half-visible word reads as a bug.

Where the boxes come from:
  python3 check_clutter.py --boxes boxes.json
      a JSON file, written by hand or by any tool (a layout dump, a browser script). Format below.
  python3 check_clutter.py --dom index.html --at 1.5,4,7.2 [--frame 1920x1080]
      loads the page in headless Chrome, waits for its fonts and its timelines, seeks every timeline in
      window.__timelines to each time, and collects the boxes with dom_boxes.js. Needs Chrome, Chromium or Edge (set CHROME_BIN to choose one).
  python3 check_clutter.py --still frame.png --bg "#101114"
      pixels only: just rule 4, using bounds.py's ink measurement. Ink touching the outermost row or column fails.

Box file format. A list of samples, or {"frame": {"width": 1920, "height": 1080}, "samples": [...]}:
  {"t": 1.5, "boxes": [{"id": "title", "kind": "text", "x": 120, "y": 80, "w": 900, "h": 110},
                       {"id": "card1", "kind": "card", "x": 100, "y": 300, "w": 600, "h": 400}]}
kind is "text" or "card". x, y, w, h are in frame pixels, measured from the top-left. A bare list of boxes is one sample.

Sample at rest, after the entrances: text sliding in from off screen is, for a moment, clipped on purpose.
Prints one PASS / FAIL line per rule and exits 1 if any rule fails. A layout that was not measured is a FAIL, never a
pass: an empty box file, a page with no timeline in window.__timelines, a seek that throws, or no text at any sample.
Without Chrome, --dom prints SKIP and exits 3 (not measured). Only the Python standard library is used.
"""
import argparse
import html
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bounds  # noqa: E402  (reads PNGs and measures ink; the same module the still checks use)

MIN_GAP, MAX_BLOCKS, SHOW = 24.0, 4, 4


def rect(b):
    return (b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"])


def overlap_area(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def gap(a, b):
    """Shortest distance between two rectangles; 0 when they touch or overlap."""
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def inside(inner, outer, tol=0.5):
    return inner[0] >= outer[0] - tol and inner[1] >= outer[1] - tol and inner[2] <= outer[2] + tol and inner[3] <= outer[3] + tol


def name(b, i):
    return str(b.get("id") or b.get("text") or f"{b.get('kind', 'text')}#{i}")[:30]


GROUP_LEADING = 0.25  # lines closer than this x line height, stacked over each other, read as one block


def group_lines(texts):
    """Merge stacked lines into blocks (union-find). Boxes that overlap are never merged (their v_gap is negative)."""
    parent = list(range(len(texts)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, (_, a) in enumerate(texts):
        for j in range(i + 1, len(texts)):
            b = texts[j][1]
            x_shared = min(a[2], b[2]) - max(a[0], b[0]) > 0
            v_gap = max(a[1], b[1]) - min(a[3], b[3])
            line_h = min(a[3] - a[1], b[3] - b[1])
            if x_shared and 0 <= v_gap < GROUP_LEADING * line_h:  # v_gap >= 0 already excludes overlapping boxes
                parent[root(i)] = root(j)
    groups = {}
    for i, (n, r) in enumerate(texts):
        groups.setdefault(root(i), []).append((n, r))
    return [("+".join(n for n, _ in members),
             (min(r[0] for _, r in members), min(r[1] for _, r in members),
              max(r[2] for _, r in members), max(r[3] for _, r in members)))
            for members in groups.values()]


def check_sample(sample, frame, opts):
    """Return {rule: [message, ...]} for one sample."""
    boxes = [dict(b, kind=b.get("kind", "text")) for b in sample["boxes"]]
    texts = [(name(b, i), rect(b)) for i, b in enumerate(boxes) if b["kind"] == "text"]
    cards = [(name(b, i), rect(b)) for i, b in enumerate(boxes) if b["kind"] == "card"]
    full = (0.0, 0.0, float(frame[0]), float(frame[1]))
    found = {"card": [], "gap": [], "blocks": [], "clip": []}
    for i, (na, a) in enumerate(cards):
        for nb, b in cards[i + 1:]:
            if overlap_area(a, b) > 0 and not (opts["nested"] and (inside(a, b) or inside(b, a))):
                found["card"].append(f"card '{na}' overlaps card '{nb}'")
    for nt, t in texts:
        for nc, c in cards:
            if overlap_area(t, c) > 0 and not inside(t, c):
                found["card"].append(f"text '{nt}' straddles the edge of card '{nc}'")
    blocks = group_lines(texts)  # overlapping boxes are never merged, so they meet here with a gap of 0
    for i, (na, a) in enumerate(blocks):
        for nb, b in blocks[i + 1:]:
            g = gap(a, b)
            if g < opts["min_gap"]:
                found["gap"].append(f"'{na}' and '{nb}' are {g:.0f} px apart" + (" (overlapping)" if overlap_area(a, b) > 0 else ""))
    visible_blocks = [(n, t) for n, t in blocks if overlap_area(t, full) > 0]
    if len(visible_blocks) > opts["max_blocks"]:
        found["blocks"].append(f"{len(visible_blocks)} text blocks on screen: " + ", ".join(n for n, _ in visible_blocks[:6]))
    for n, t in [(n, t) for n, t in texts if overlap_area(t, full) > 0]:
        if not inside(t, full):
            found["clip"].append(f"text '{n}' runs past the frame edge")
    return found


RULES = (
    ("card", "no card on card, text stays inside or outside each card"),
    ("gap", "at least {min_gap:g} px between text blocks, no overlapping text"),
    ("blocks", "at most {max_blocks} text blocks per frame"),
    ("clip", "no text clipped at the frame edge"),
)


def report(samples, frame, opts):
    if not samples:
        print("FAIL  layout not measured: no samples (the box file is empty)")
        return 1
    per_rule = {key: [] for key, _ in RULES}
    for s in samples:
        for key, msgs in check_sample(s, frame, opts).items():
            per_rule[key].extend(f"t={s.get('t', '?')}s: {m}" for m in msgs)
    fails = 0
    for key, label in RULES:
        label = label.format(**opts)
        if per_rule[key]:
            fails += 1
            more = f" (+{len(per_rule[key]) - SHOW} more)" if len(per_rule[key]) > SHOW else ""
            print(f"FAIL  {label}: " + "; ".join(per_rule[key][:SHOW]) + more)
        else:
            print(f"PASS  {label} ({len(samples)} sample{'s' if len(samples) != 1 else ''})")
    return 1 if fails else 0


def load_boxes(path, frame):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        fr = data.get("frame") or {}
        frame = (fr.get("width", frame[0]), fr.get("height", frame[1]))
        data = data.get("samples", [])
    if data and "boxes" not in data[0]:
        data = [{"t": 0, "boxes": data}]
    return data, frame


def find_chrome():
    for cand in (os.environ.get("CHROME_BIN"), "google-chrome", "chromium", "chromium-browser", "chrome", "msedge",
                 "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                 "C:/Program Files/Google/Chrome/Application/chrome.exe",
                 "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                 "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"):
        if cand and (shutil.which(cand) or os.path.isfile(cand)):
            return shutil.which(cand) or cand
    return None


class Unmeasured(Exception):
    """The layout could not be measured. Printed as a FAIL line: a check that did not measure never passes."""


def collect_from_dom(html_path, times, frame):
    """Seek the page's timelines to each time in headless Chrome and read the boxes back. None if no Chrome."""
    chrome = find_chrome()
    if not chrome:
        return None
    src = Path(html_path).resolve()
    collector = (HERE / "dom_boxes.js").read_text(encoding="utf-8")
    runner = ("<script>" + collector + "\n(function () {\n"
              f"  var times = [{','.join(str(t) for t in times)}], tries = 0;\n"
              "  function collect() {\n"
              "    var tls = Object.values(window.__timelines || {}), out = { timelines: tls.length, errors: [], samples: [] };\n"
              "    times.forEach(function (t) {\n"
              "      try { tls.forEach(function (tl) { tl.pause(); tl.seek(t, false); }); } catch (e) { out.errors.push(t + 's: ' + e); }\n"
              "      out.samples.push({ t: t, boxes: window.b2mCollectBoxes() });\n"
              "    });\n"
              "    var pre = document.createElement('pre'); pre.id = 'b2m-out'; pre.textContent = JSON.stringify(out);\n"
              "    document.body.appendChild(pre);\n"
              "  }\n"
              "  function wait() {   // timelines are often registered after the fonts load: give them up to 3 s\n"
              "    if (Object.keys(window.__timelines || {}).length || ++tries > 60) collect(); else setTimeout(wait, 50);\n"
              "  }\n"
              "  window.addEventListener('load', function () {\n"
              "    (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () { setTimeout(wait, 0); });\n"
              "  });\n"
              "})();</script>")
    page = src.read_text(encoding="utf-8")
    base = f'<base href="{src.parent.as_uri()}/">'
    page = page.replace("<head>", "<head>" + base, 1) if "<head>" in page else base + page
    page = page.replace("</body>", runner + "</body>", 1) if "</body>" in page else page + runner
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.html"
        probe.write_text(page, encoding="utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
               f"--user-data-dir={Path(tmp) / 'profile'}", f"--window-size={frame[0]},{frame[1]}",
               "--force-device-scale-factor=1", "--virtual-time-budget=4000", "--allow-file-access-from-files",
               "--dump-dom", probe.as_uri()]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    marker = '<pre id="b2m-out">'
    if marker not in proc.stdout:
        raise Unmeasured("the page produced no boxes (did Chrome start, and does the page load without errors?)")
    raw = proc.stdout.split(marker, 1)[1].split("</pre>", 1)[0]
    data = json.loads(html.unescape(raw))
    if not data.get("timelines"):
        raise Unmeasured("no timeline in window.__timelines, so the page could not be seeked to the sample times "
                         "(register every GSAP timeline there, as HyperFrames compositions do)")
    if data.get("errors"):
        raise Unmeasured("seeking the timelines failed: " + "; ".join(data["errors"][:3]))
    if not any(b.get("kind") == "text" for s in data["samples"] for b in s["boxes"]):
        raise Unmeasured("no text was visible at any sample time: the times are outside the film, or the page did not draw")
    return data["samples"]



def check_still(png, bg, tol):
    w, h, ch, rows = bounds.read_png(png)
    strips = {"top": (0, 0, w, 1), "bottom": (0, h - 1, w, h), "left": (0, 0, 1, h), "right": (w - 1, 0, w, h)}
    touched = [side for side, region in strips.items()
               if bounds.bbox(rows, w, h, ch, bounds.hex_rgb(bg), tol, region)]
    if touched:
        print(f"FAIL  nothing clipped at the frame edge: ink touches the {', '.join(touched)} edge of {png}")
        return 1
    print("PASS  nothing clipped at the frame edge (pixels only; use --boxes or --dom for the other rules)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--boxes", help="JSON file of boxes")
    src.add_argument("--dom", help="an HTML composition to load in headless Chrome")
    src.add_argument("--still", help="a PNG: check ink at the frame edge only")
    ap.add_argument("--at", help="with --dom: comma-separated times in seconds")
    ap.add_argument("--frame", default="1920x1080", help="frame size WxH (default 1920x1080)")
    ap.add_argument("--bg", help="with --still: background colour #rrggbb")
    ap.add_argument("--tol", type=int, default=24, help="with --still: per-channel difference that counts as ink")
    ap.add_argument("--min-gap", type=float, default=MIN_GAP)
    ap.add_argument("--max-blocks", type=int, default=MAX_BLOCKS)
    ap.add_argument("--allow-nested", action="store_true", help="a card fully inside another card is allowed")
    args = ap.parse_args()
    frame = tuple(int(v) for v in args.frame.lower().split("x"))
    if args.still:
        if not args.bg:
            ap.error("--still needs --bg")
        return check_still(args.still, args.bg, args.tol)
    opts = {"min_gap": args.min_gap, "max_blocks": args.max_blocks, "nested": args.allow_nested}
    if args.dom:
        if not args.at:
            ap.error("--dom needs --at")
        try:
            at = [float(t) for t in args.at.split(",") if t.strip()]
        except ValueError:
            ap.error(f"--at must be comma-separated seconds, got '{args.at}'")
        try:
            samples = collect_from_dom(args.dom, at, frame)
        except (Unmeasured, OSError, subprocess.SubprocessError, ValueError) as err:
            print(f"FAIL  layout not measured: {err}")
            return 1
        if samples is None:
            print("SKIP  check_clutter --dom: no Chrome, Chromium or Edge found, so the layout was not measured. Install Google "
                  "Chrome, or set CHROME_BIN, or dump the boxes yourself and use --boxes (see dom_boxes.js)")
            return 3
    else:
        samples, frame = load_boxes(args.boxes, frame)
    return report(samples, frame, opts)


if __name__ == "__main__":
    sys.exit(main())
