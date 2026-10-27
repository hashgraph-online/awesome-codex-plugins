#!/usr/bin/env python3
"""Gate for any web page / landing page / hero preview. Run before the first site-code commit (build) and before
sending anything to the user (--ship). Reason: on 2026-10-24 three site heroes were coded from memory, references
were found afterwards only to grade them, and Jack said "差距也太大了吧，完全不是一个事情". The method that was then
accepted ("这回真的很好") is encoded here as files that must exist, in this order.

usage: web_gate.py <project> [--dir docs/site] [--code site] [--restart <git-rev>] [--ship]

build checks (all must pass before site code is committed):
  1. <dir>/refs/*.json  ≥1 layer dump from scripts/web_layers.js (the liked reference was decoded, not imagined)
  2. <dir>/technique-sheets.md  ≥3 entries ("### ") each with: hero, layer sandwich, what code adds, signature, borrow
  3. <dir>/style-frames.md  has "Register: 克制|风格化", "Picked:", and ≥1 existing *-vs-ref.jpg
  4. git: technique-sheets.md was committed no later than the first commit touching --code
     (after the user rejects a round, pass --restart <rev> so only code after that rev must follow new refs)
--ship adds (before showing the user):
  5. every *-vs-ref entry in style-frames.md has a "Core gap:" line; none of the live ones (not marked 已被否/rejected) is structural
  6. a phone recording (*.mp4) and a phone screenshot sheet exist under <dir>
  7. the code honours prefers-reduced-motion
"""
import glob, os, re, subprocess, sys

a = sys.argv[1:]
if not a:
    sys.exit(__doc__)
proj = a[0]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
d, code, restart, ship = opt("--dir", "docs/site"), opt("--code", "site"), opt("--restart"), "--ship" in a
D = os.path.join(proj, d)
read = lambda p: open(p, encoding="utf-8").read() if os.path.exists(p) else ""
bad = []

dumps = glob.glob(os.path.join(D, "refs", "*.json"))
if not dumps:
    bad.append(f"no layer dump in {d}/refs/ — run: node scripts/web_layers.js <liked-ref-url> <name> {d}/refs")

ts = read(os.path.join(D, "technique-sheets.md"))
need = {"hero": r"hero", "layer sandwich": r"layer sandwich|层次", "what code adds": r"what code adds|代码加了", "signature": r"signature", "borrow": r"borrow|借"}
entries = re.split(r"(?m)^### ", ts)[1:]
full = [e.split("\n", 1)[0][:50] for e in entries if all(re.search(p, e, re.I) for p in need.values())]
if len(full) < 3:
    bad.append(f"technique-sheets.md: {len(full)} complete entries (need 3, each with {', '.join(need)})")

sf = read(os.path.join(D, "style-frames.md"))
if not re.search(r"(?mi)^\W*register:\s*(克制|风格化|restraint|stylized)", sf):
    bad.append("style-frames.md: no 'Register: 克制|风格化' line (decide from the refs the USER liked)")
if not re.search(r"(?mi)^\W*picked:\s*\S", sf):
    bad.append("style-frames.md: no 'Picked:' line — show style frames and let the user pick before building")
vs = [v for v in set(re.findall(r"[\w./-]+-vs-ref\.jpg", sf)) if glob.glob(os.path.join(D, "**", os.path.basename(v)), recursive=True)]
if not vs:
    bad.append("style-frames.md links no existing *-vs-ref.jpg comparison")


def first_commit(path, since=None):
    cmd = ["git", "-C", proj, "log", "--format=%ct"] + ([f"{since}..HEAD"] if since else ["--diff-filter=A"]) + ["--", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    t = [int(x) for x in r.stdout.split()] if r.returncode == 0 else []
    return min(t) if t else None


t_ts, t_code = first_commit(os.path.join(d, "technique-sheets.md")), first_commit(code, restart)
if t_ts is None:
    bad.append("technique-sheets.md is not committed yet — commit it before any site code")
elif t_code is not None and t_ts > t_code:
    bad.append(f"site code under {code}/ was committed before the technique sheet (refs must come first; after a rejected round use --restart <rev>)")

if ship:
    secs = re.split(r"(?m)^[-#*]", sf)
    vs_secs = [s for s in secs if "-vs-ref" in s]
    if not vs_secs or not all(re.search(r"core gap|核心差距", s, re.I) for s in vs_secs):
        bad.append("each *-vs-ref entry needs a 'Core gap:' line (are the gaps element-level only?)")
    live = [l for l in sf.splitlines() if re.search(r"core gap|核心差距", l, re.I) and not re.search(r"rejected|已被否", l, re.I)]
    if any(re.search(r"structural|结构级|不是一个事情", l, re.I) for l in live):
        bad.append("a core gap is structural — do not show this frame; rebuild from the technique sheet")
    if not glob.glob(os.path.join(D, "**", "*.mp4"), recursive=True):
        bad.append(f"no phone recording (*.mp4) under {d}/ — record drag + taps at 390×844 (see references/web-craft.md W5)")
    src = " ".join(read(p) for p in glob.glob(os.path.join(proj, code, "**", "*.*"), recursive=True) if p.endswith((".js", ".html", ".css")) and "node_modules" not in p)
    if "prefers-reduced-motion" not in src:
        bad.append("code never checks prefers-reduced-motion")

if bad:
    sys.exit("✗ web gate (" + ("ship" if ship else "build") + "):\n  - " + "\n  - ".join(bad))
print(f"✓ web gate {'ship' if ship else 'build'}: {len(dumps)} layer dump(s), {len(full)} technique entries ({', '.join(full[:4])}), {len(vs)} vs-ref")
