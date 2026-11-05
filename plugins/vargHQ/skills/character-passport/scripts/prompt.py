#!/usr/bin/env python3
"""Build shot prompts from passports, and check that every prompt carries them word for word.

Passports live in cast/<id>.md as a fenced block that starts with ```passport (characters and props alike).
The look block (light, palette, film stock) lives in a fenced ```look block, usually in moodboard.md.
A prop's ```motion block (how it moves and sounds) is added only with --video.

  python3 prompt.py build --shot "Close-up, 50mm: ..." --cast cast/vesna.md --cast cast/umbrella.md \
      --look moodboard.md [--sheet "Vesna"] [--video] [--max 2000]
  python3 prompt.py check prompts/*.txt --cast cast/vesna.md --cast cast/umbrella.md
  python3 prompt.py show cast/vesna.md          # print the passport block and its length
"""
import argparse, difflib, pathlib, re, sys

FENCE = re.compile(r"```(passport|look|motion|voice)[^\n]*\n(.*?)```", re.S)

def block(path, kind, required=True):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    found = [b.strip() for k, b in FENCE.findall(text) if k == kind]
    if not found:
        if not required:
            return ""
        sys.exit(f"{path}: no ```{kind} block found")
    return " ".join(" ".join(found).split())

def build(a):
    parts = []
    if a.sheet:
        parts.append(f"Image 1 is the character sheet of {a.sheet}: use it for identity only (face, hair, body, "
                     "clothes); do not copy its layout, panels or background.")
    parts.append(a.shot.strip())
    for i, c in enumerate(a.cast):
        p = block(c, "passport")
        parts.append(("SUBJECT: " if i == 0 else "") + p)
    if a.video:  # video prompts also carry how each prop moves and sounds
        parts += [m for m in (block(c, "motion", required=False) for c in a.cast) if m]
    if a.look:
        parts.append(block(a.look, "look"))
    prompt = " ".join(parts)
    print(prompt)
    n = len(prompt)
    msg = f"[{n} characters, limit {a.max}]"
    if n > a.max:
        sys.exit(f"{msg} too long: shorten the shot line or the look block, never the passport")
    print(msg, file=sys.stderr)

def check(a):
    passports = {c: block(c, "passport") for c in a.cast}
    bad = 0
    for f in a.prompts:
        text = " ".join(pathlib.Path(f).read_text(encoding="utf-8").split())
        for c, p in passports.items():
            if p in text:
                print(f"ok    {f}  carries {pathlib.Path(c).stem} word for word")
                continue
            bad += 1
            # find the closest window to show what drifted
            sm = difflib.SequenceMatcher(None, text, p, autojunk=False)
            ratio = sm.ratio()
            words_p, words_t = p.split(), set(text.split())
            missing = [w for w in words_p if w not in words_t]
            print(f"DRIFT {f}  {pathlib.Path(c).stem}: passport not found verbatim "
                  f"(missing words: {' '.join(missing[:25]) or 'none, order changed'})")
    sys.exit(1 if bad else 0)

def show(a):
    for c in a.cast:
        p = block(c, "passport")
        print(f"{c}  ({len(p)} characters)\n{p}\n")

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = ap.add_subparsers(dest="cmd", required=True)
b = sub.add_parser("build"); b.add_argument("--shot", required=True); b.add_argument("--cast", action="append", default=[])
b.add_argument("--look"); b.add_argument("--sheet"); b.add_argument("--video", action="store_true", help="append ```motion blocks"); b.add_argument("--max", type=int, default=2000); b.set_defaults(fn=build)
c = sub.add_parser("check"); c.add_argument("prompts", nargs="+"); c.add_argument("--cast", action="append", required=True); c.set_defaults(fn=check)
s = sub.add_parser("show"); s.add_argument("cast", nargs="+"); s.set_defaults(fn=show)
a = ap.parse_args(); a.fn(a)
