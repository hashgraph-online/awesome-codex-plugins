#!/usr/bin/env python3
"""Gate before any style frame: real reference frames must exist and be written up.
usage: refs_gate.py <project-dir> [--min 6]
Passes only if <project>/refs/ has at least N contact sheets (*_sheet.jpg/png from ref_frames.sh)
and a technique sheet (refs/technique-sheets.md or research.md) with at least N entries ("### ")
that each name a palette, a transition and a signature move. Frames drawn from memory failed
every time ("都好丑，你没好好找参考吧")."""
import glob, os, re, sys

a = sys.argv[1:]
if not a:
    sys.exit(__doc__)
proj, need = a[0], int(a[a.index("--min") + 1]) if "--min" in a else 6
refs = os.path.join(proj, "refs")
sheets = glob.glob(os.path.join(refs, "**", "*_sheet.*"), recursive=True)
notes = next((p for p in (os.path.join(refs, "technique-sheets.md"), os.path.join(proj, "research.md")) if os.path.exists(p)), None)
entries = re.split(r"^### ", open(notes).read(), flags=re.M)[1:] if notes else []
fields = {"palette": r"palette|配色", "transition": r"transition|转场", "signature": r"signature|招牌"}
complete = [e.split("\n", 1)[0].strip() for e in entries if all(re.search(p, e, re.I) for p in fields.values())]
problems = []
if len(sheets) < need:
    problems.append(f"{len(sheets)} contact sheets in refs/ (need {need}); run scripts/ref_frames.sh on official uploads")
if not notes:
    problems.append("no refs/technique-sheets.md")
elif len(complete) < need:
    problems.append(f"{len(complete)} complete technique entries (need {need}, each with palette, transition, signature move)")
if problems:
    sys.exit("✗ not ready for style frames:\n  - " + "\n  - ".join(problems))
print(f"✓ {len(sheets)} contact sheets, {len(complete)} technique entries: " + ", ".join(complete[:8]))
