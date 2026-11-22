#!/usr/bin/env python3
"""build_character_docs.py: write the pose, cycle, mouth-shape and ease tables in characters/README-CHARACTERS.md
from the code (characters/poses.js and rig.js), so the README can never drift from it.

    python3 scripts/build_character_docs.py            # rewrite the generated blocks
    python3 scripts/build_character_docs.py --check    # exit 1 if the README is out of date (a test runs this)

Each block sits between `<!-- BEGIN generated: NAME -->` and `<!-- END generated: NAME -->`. Standard library only;
it runs the kit under Node to read the tables.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent / "characters"
README = KIT / "README-CHARACTERS.md"
JS = """
const B = require(process.argv[1]);
console.log(JSON.stringify({ poses: Object.keys(B.POSES).map((n) => [n, B.POSE_INFO[n]]), eases: B.EASES.map((n) => [n, B.EASE_INFO[n]]),
  visemes: B.VISEMES.map((n) => [n, B.VISEME_INFO[n]]), skins: Object.keys(B.SKINS),
  cycles: Object.keys(B.CYCLES).map((n) => [n, B.CYCLES[n].frames, B.CYCLES[n].steps, B.CYCLE_INFO[n]]), extra: ['talk', 'blink'].map((n) => [n, B.CYCLE_INFO[n]]) }));
"""


def kit_tables() -> dict:
    node = shutil.which("node")
    if not node:
        raise SystemExit("build_character_docs: node not found; install Node.js 22 or newer")
    done = subprocess.run([node, "-e", JS, str(KIT / "index.js")], capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise SystemExit("build_character_docs: could not read the kit:\n" + done.stderr[-600:])
    return json.loads(done.stdout)


def blocks(t: dict) -> dict[str, str]:
    def table(head: list[str], rows: list[list[str]]) -> str:
        lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
        return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows])
    cycles = [[f"`{n}`", str(frames), str(steps), info] for n, frames, steps, info in t["cycles"]] + [[f"`{n}`", "", "", info] for n, info in t["extra"]]
    return {
        "poses": table(["Pose", "What it shows"], [[f"`{n}`", info] for n, info in t["poses"]]),
        "cycles": table(["Cycle (a `layers` entry)", "Drawings", "Default steps a second", "What it does"], cycles),
        "mouths": table(["Mouth shape (`v` in a viseme track, `mouth` on a key)", "What it looks like"], [[f"`{n}`", info] for n, info in t["visemes"]]),
        "eases": table(["Ease", "Feel"], [[f"`{n}`", info] for n, info in t["eases"]]),
    }


def rewrite(text: str, new: dict[str, str]) -> str:
    for name, body in new.items():
        pattern = re.compile(r"(<!-- BEGIN generated: %s -->\n).*?(<!-- END generated: %s -->)" % (name, name), re.S)
        if not pattern.search(text):
            raise SystemExit(f"build_character_docs: README-CHARACTERS.md has no generated block named '{name}'")
        text = pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)
    return text


def main(argv: list[str]) -> int:
    current = README.read_text(encoding="utf-8")
    updated = rewrite(current, blocks(kit_tables()))
    if "--check" in argv:
        if updated != current:
            print("README-CHARACTERS.md is out of date with poses.js and rig.js. Run: python3 scripts/build_character_docs.py")
            return 1
        print("README-CHARACTERS.md tables are current")
        return 0
    README.write_text(updated, encoding="utf-8", newline="\n")
    print("rewrote the generated tables in README-CHARACTERS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
