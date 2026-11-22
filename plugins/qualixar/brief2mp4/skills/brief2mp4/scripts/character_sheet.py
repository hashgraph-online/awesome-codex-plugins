#!/usr/bin/env python3
"""character_sheet.py: render character sheets as PNG: the standing view, six poses and nine mouth shapes.

    python3 character_sheet.py --character child --skin paper-cutout --out sheets/
    python3 character_sheet.py --all --out sheets/            # every character in every skin
    python3 character_sheet.py --character crow --skin all    # one character, every skin
    python3 character_sheet.py --file my-art/hero.json --skin cel-shaded    # a character file of your own

Writes <out>/<character>-<skin>.png at 1920x1080. All sheets of one call come from a single HyperFrames
snapshot run (second i of one composition shows sheet i). Use them to check that a character stays recognisable
across art forms, and as thumbnail material. Needs Node.js (npx) and, once, the network for GSAP.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_project as cp  # noqa: E402

HYPERFRAMES = "hyperframes@0.8.216"


def skin_ids() -> list[str]:
    text = "".join((cp.KIT / name).read_text(encoding="utf-8") for name in ("skins.js", "skins-extra.js"))
    return re.findall(r"^  SKINS\['([a-z-]+)'\] = \{", text, re.M)


def build_page(project: Path, sheets: list[tuple[str, str]]) -> None:
    import json
    html = (cp.KIT / "sheet.html").read_text(encoding="utf-8")
    html = html.replace("__DURATION__", str(len(sheets))).replace("__SHEETS__", json.dumps([{"character": c, "skin": s} for c, s in sheets]))
    (project / "index.html").write_text(html, encoding="utf-8", newline="\n")
    cp.write_hf_files(project, "character-sheet")


def snapshot(project: Path, count: int) -> list[Path]:
    npx = shutil.which("npx")
    if not npx:
        raise SystemExit("character_sheet: npx not found; install Node.js 22 or newer")
    at = ",".join(str(i + 0.5) for i in range(count))
    done = subprocess.run([npx, "--yes", HYPERFRAMES, "snapshot", str(project), "--at", at], capture_output=True, text=True, encoding="utf-8", cwd=project, timeout=900)
    if done.returncode != 0:
        raise SystemExit(f"character_sheet: snapshot failed:\n{done.stdout[-800:]}\n{done.stderr[-800:]}")
    shots = sorted((project / ".hyperframes" / "artifacts" / "snapshots").rglob("*.png"), key=lambda p: float(re.search(r"([0-9]+(?:\.[0-9]+)?)s?\.png$", p.name).group(1)) if re.search(r"([0-9]+(?:\.[0-9]+)?)s?\.png$", p.name) else 0)
    if len(shots) < count:
        raise SystemExit(f"character_sheet: expected {count} snapshots, found {len(shots)} under {project}")
    return shots[:count]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--character", help="a character id from characters/cast/")
    ap.add_argument("--skin", default="all", help="a skin id, or 'all' (default)")
    ap.add_argument("--file", help="a character JSON file of your own (its pictures, if any, are read from beside it)")
    ap.add_argument("--all", action="store_true", help="every character in every skin")
    ap.add_argument("--out", default="character-sheets", help="folder for the PNG files")
    args = ap.parse_args(argv)
    extra = {}
    if args.file:
        try:
            extra_char = cp.load_file(Path(args.file))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"character_sheet: {exc}")
        extra[extra_char["id"]] = extra_char
    if args.character:
        cp.check_id(args.character)                         # an id becomes part of a file name
    chars = cp.cast_ids() if args.all else [args.character] if args.character else list(extra)
    if not chars:
        ap.error("give --character ID, --file FILE or --all")
    skins = skin_ids() if args.all or args.skin == "all" else [args.skin]
    for s in skins:
        if s not in skin_ids():
            ap.error(f"unknown skin '{s}'. Skins: {', '.join(skin_ids())}")
    sheets = [(c, s) for c in chars for s in skins]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="b2m-sheet-") as tmp:
        project = Path(tmp)
        cp.prepare_project(project, [c for c in chars if c not in extra], extra_cast=extra)
        build_page(project, sheets)
        for (c, s), shot in zip(sheets, snapshot(project, len(sheets))):
            dest = out / f"{c}-{s}.png"
            shutil.copyfile(shot, dest)
            print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
