#!/usr/bin/env python3
"""character_project.py: put the character kit and a scene into a HyperFrames project folder.

    python3 character_project.py --scene scene.json --skin cel-shaded --out project/
    npx hyperframes render project -o render.mp4 --quality delivery --fps 30

The scene file names the cast, their tracks, the backdrop and the captions (see characters/stage.js). A track may
carry "visemesFrom": { "words": "words.json", "from": 3.3, "to": 6, "lang": "en" }; it is turned into the
lip-sync track with scripts/lipsync.py. The same scene renders in any skin: pass --skin, or leave the scene's own.
Your own characters (SVG-style shapes or PNG part images) join a scene with --character-file FILE.json, repeatable.

As a module:

    from character_project import prepare_project
    prepare_project(project_dir, ["child", "crow"])      # runtime files, cast.js, vendor/gsap.min.js (+ three.js)
    prepare_project(project_dir, [], extra_cast={"mine": load_file("my-character.json")})

The runtime files are copied next to the page (characters/*.js) and the cast files are inlined as `cast.js`, so a
render never reads the network or a JSON file at run time. Standard library only; vendoring GSAP and three.js
uses scripts/vendor_libs.sh, as everywhere else in the skill.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
KIT = SKILL / "characters"
sys.path.insert(0, str(KIT))
import validate  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lipsync  # noqa: E402,F401
RUNTIME = ["poses.js", "rig.js", "shapes.js", "render.js", "skins.js", "skins-extra.js", "stage.js", "sheet.js"]


def cast_ids() -> list[str]:
    return sorted(p.stem for p in (KIT / "cast").glob("*.json"))


def check_id(cid: str) -> str:
    """An id ends up in file names, so it must be a plain name: lower case letters, digits and hyphens."""
    import re
    if not isinstance(cid, str) or not re.match(r"^[a-z][a-z0-9-]*$", cid):
        raise SystemExit(f"character_project: {cid!r} is not a character id (lower case letters, digits and hyphens, starting with a letter)")
    return cid


def load_cast(ids: list[str]) -> dict[str, dict]:
    cast = {}
    for cid in ids:
        path = KIT / "cast" / f"{check_id(cid)}.json"
        if not path.is_file():
            raise SystemExit(f"character_project: no character '{cid}'. Available: {', '.join(cast_ids())}")
        cast[cid] = json.loads(path.read_text(encoding="utf-8"))
    return cast


def _inline(pic: dict, base: Path) -> None:
    src = pic.get("src", "")
    problem = validate.picture_problem(src, base)
    if problem:
        raise ValueError(problem)
    if not src.startswith("data:"):
        mime = "image/webp" if src.lower().endswith(".webp") else "image/png"
        pic["src"] = f"data:{mime};base64," + base64.b64encode((base / src).resolve().read_bytes()).decode("ascii")


def inline_images(character: dict, base: Path) -> dict:
    """Replace every picture path in a character with a data: URI, so the page needs no file at render time."""
    for part in character["parts"]:
        for holder in [part] + list(part.get("variants", {}).values()):
            if "image" in holder:
                _inline(holder["image"], base)
            for pic in (holder.get("mouth") or {}).get("images", {}).values():
                _inline(pic, base)
    return character


def load_file(path: Path) -> dict:
    """Load a character file from anywhere (your own art, the image-parts demo): validate it, then inline its pictures.
    Raises ValueError listing the problems (a picture outside the file's folder, a file that is not a PNG or WebP...)."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    problems = validate.validate_character(data, path.resolve().parent)
    if problems:
        raise ValueError(f"{path}: {len(problems)} problem(s):\n  " + "\n  ".join(problems))
    return inline_images(data, path.resolve().parent)


def vendor_command(project: Path, three: bool = False, windows: bool | None = None) -> list[str]:
    """The command that copies GSAP (and three.js) into a project: bash on macOS and Linux, PowerShell on Windows."""
    if os.name == "nt" if windows is None else windows:
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SKILL / "scripts" / "vendor_libs.ps1"), "-Project", str(project)] + (["-Three"] if three else [])
    return ["bash", str(SKILL / "scripts" / "vendor_libs.sh"), str(project)] + (["--three"] if three else [])


def vendor(project: Path, three: bool = False) -> None:
    done = subprocess.run(vendor_command(project, three), capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise SystemExit(f"character_project: vendoring GSAP failed (needs npm and the network once):\n{done.stderr[-600:]}")


def prepare_project(project: Path, ids: list[str], three: bool = False, extra_cast: dict | None = None) -> None:
    """Copy the runtime, inline the named characters as cast.js and vendor GSAP (and three.js)."""
    project = Path(project)
    (project / "characters").mkdir(parents=True, exist_ok=True)
    for name in RUNTIME:
        shutil.copyfile(KIT / name, project / "characters" / name)
    cast = load_cast(ids)
    for cid, character in (extra_cast or {}).items():
        cast[cid] = character
    text = "window.B2M_CAST = " + json.dumps(cast, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (project / "characters" / "cast.js").write_text(text, encoding="utf-8", newline="\n")
    if not (project / "vendor" / "gsap.min.js").exists() or (three and not (project / "vendor" / "three.module.js").exists()):
        vendor(project, three)


HF_JSON = '{"$schema":"https://hyperframes.heygen.com/schema/hyperframes.json","registry":"https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry","paths":{"blocks":"compositions","components":"compositions/components","assets":"assets"}}'


def write_hf_files(project: Path, name: str) -> None:
    """The two small files `npx hyperframes` expects next to index.html."""
    (project / "hyperframes.json").write_text(HF_JSON + "\n", encoding="utf-8", newline="\n")
    (project / "meta.json").write_text(json.dumps({"id": name, "name": name}) + "\n", encoding="utf-8", newline="\n")


class SceneError(ValueError):
    """A scene file with problems. `problems` lists each one, naming the field and what is allowed."""

    def __init__(self, problems: list[str]):
        super().__init__("the scene has %d problem(s):\n  %s" % (len(problems), "\n  ".join(problems)))
        self.problems = problems


def resolve_scene(scene: dict, base: Path) -> dict:
    """Expand each track's visemesFrom into a lip-sync track. A speaker whose words give no mouth shapes at all is an error."""
    import lipsync
    problems = []
    for n, member in enumerate(scene["cast"]):
        track = member.get("track")
        spec = isinstance(track, dict) and track.pop("visemesFrom", None)
        if spec:
            words = [w for w in lipsync.load_words(base / spec["words"]) if spec["from"] <= w["start"] < spec["to"]]
            skipped: list[str] = []
            track["visemes"] = lipsync.build_track(words, scene.get("fps", 30), spec.get("lang", "en"), skipped)
            for text in skipped:
                print(f'warning: scene.cast[{n}] ({member["id"]}): no mouth shapes for the word "{text}"; it is left out', file=sys.stderr)
            if words and not track["visemes"]:
                problems.append(f"scene.cast[{n}].track.visemesFrom: none of the {len(words)} word(s) between {spec['from']} s and {spec['to']} s gives a mouth shape; "
                                f"build the track from the voice's loudness instead: lipsync.py --wav voice.wav, and give it as visemes")
    if problems:
        raise SceneError(problems)
    return scene


_REPORT_JS = """
const fs = require('fs'); const B2M = require(process.argv[1]);
const scene = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), cast = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(B2M.sceneReport(scene, cast)));
"""


def _walk_scene(scene: dict, characters: dict[str, dict]) -> dict:
    """Run the kit's own scene report (B2M.sceneReport): where each cast member stands, which way it faces, its walks, its
    colour against the background and how many lines each caption needs, worked out by the rig and stage that render the film."""
    import tempfile
    node = shutil.which("node")
    if not node:
        raise SystemExit("character_project: node not found; install Node.js 22 or newer")
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "scene.json").write_text(json.dumps(scene), encoding="utf-8")
        (Path(tmp) / "cast.json").write_text(json.dumps(characters), encoding="utf-8")
        done = subprocess.run([node, "-e", _REPORT_JS, str(KIT / "index.js"), str(Path(tmp) / "scene.json"), str(Path(tmp) / "cast.json")], capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise SystemExit("character_project: could not trace the cast through the scene:\n" + done.stderr[-600:])
    return json.loads(done.stdout)


def screen_problems(scene: dict, characters: dict[str, dict] | None = None) -> tuple[list[str], list[str]]:
    """Errors and warnings about the picture: a character fully out of the frame for over half a second (error), feet below
    the frame (error), speakers facing away from each other, a figure close in tone to the background, a walk that needs a
    run's drawings, a caption that needs more than two lines (warnings). Positions in a move track are absolute pixels."""
    ids = sorted({m["character"] for m in scene["cast"]})
    report = _walk_scene(scene, characters if characters is not None else load_cast(ids))
    paths, errors, warnings = report["members"], [], []
    width, height, ground, step = scene["width"], scene["height"], scene["ground"], 0.1
    for n, m in enumerate(scene["cast"]):
        p = paths[m["id"]]
        feet = max(p["y"])
        if feet > height:
            errors.append(f"scene.cast[{n}] ({m['id']}, {m['character']}): its feet are at y = {feet:.0f}, below the bottom of the frame ({height}). y is the y of the feet on screen; leave it out to stand on the ground top ({ground})")
        elif feet > ground + 0.5 * (height - ground):
            warnings.append(f"{m['id']}: its feet are at y = {feet:.0f}, deep inside the ground band (the ground top is {ground}); leave y out to stand on the ground top")
        for w in p["walks"]:
            if w["steps"] > 12:
                warnings.append(f"{m['id']} walks {w['from']:.1f} s to {w['to']:.1f} s fast enough to need {w['steps']:.0f} drawings a second, which looks like a run: allow more time or a shorter distance")
        if p["low"]:
            low = p["low"]
            warnings.append(f"{m['id']} ({m['character']}) is hard to see: its tone {p['tone']} is close to the background behind it at {low['t']:.1f} s, which is {low['part']} {low['colour']} "
                            f"(contrast {low['ratio']:.1f}:1, aim for 1.6 or more); change the palette or the skin")
        if m.get("allowOffscreen"):
            continue
        run = None
        for i, x in enumerate(p["x"] + [None]):
            out = x is not None and (x + p["half"] < 0 or x - p["half"] > width)
            if out and run is None:
                run = i
            elif not out and run is not None:
                if (i - run) * step > 0.5 + 1e-9:
                    side = "left" if p["x"][run] < 0 else "right"
                    errors.append(f"scene.cast[{n}] ({m['id']}, {m['character']}) is fully outside the frame to the {side} from {run * step:.1f} s to {(i - 1) * step:.1f} s "
                                  f"(x = {p['x'][run]:.0f}, the frame is 0 to {width}). Positions in a move track are absolute screen pixels; fix x or the move keys, or set allowOffscreen: true if this is meant")
                run = None
    for c in report["captions"]:
        if c["lines"] > 2:
            warnings.append(f"scene.captions[{c['index']}] needs {c['lines']} lines at this frame size; captions read best in two lines or fewer, so shorten it or split it into two captions")
    speakers = [m for m in scene["cast"] if isinstance(m.get("track"), dict) and m["track"].get("visemes")]
    for a in speakers:
        i = min(len(paths[a["id"]]["x"]) - 1, int(a["track"]["visemes"][0]["t"] / step) + 3)
        for b in speakers:
            if a is b:
                continue
            toward = 1 if paths[b["id"]]["x"][i] > paths[a["id"]]["x"][i] else -1
            if paths[a["id"]]["flip"][i] != toward:
                warnings.append(f"{a['id']} faces {'right' if toward < 0 else 'left'} while speaking to {b['id']}, who stands to its {'right' if toward > 0 else 'left'}: speakers usually face each other (set facing: \"{'right' if toward > 0 else 'left'}\")")
    return errors, warnings


def build_scene_project(scene_path: Path, out: Path, skin: str | None = None, character_files=()) -> dict:
    """Write a complete HyperFrames project for the scene; return the scene as written. Raises SceneError for a bad scene.
    character_files are your own character JSON files (validated, pictures inlined); the scene can use their ids."""
    scene_path = Path(scene_path)
    import validate_scene
    raw = json.loads(scene_path.read_text(encoding="utf-8"))
    if skin:
        raw["skin"] = skin
    extras: dict[str, dict] = {}
    for file in character_files:
        try:
            character = load_file(Path(file))
        except ValueError as exc:
            raise SceneError([f"--character-file {file}: {exc}"]) from None
        if character["id"] in cast_ids():
            raise SceneError([f"--character-file {file}: the id '{character['id']}' clashes with the starter cast; give your character another id"])
        extras[character["id"]] = character
    problems = validate_scene.validate_scene(raw, scene_path.resolve().parent, extras)
    if problems:
        raise SceneError(problems)
    scene = resolve_scene(raw, scene_path.resolve().parent)
    used = sorted({m["character"] for m in scene["cast"]})
    builtin = [c for c in used if c not in extras]
    errors, warnings = screen_problems(scene, {**load_cast(builtin), **{c: extras[c] for c in used if c in extras}})
    if errors:
        raise SceneError(errors)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    out.mkdir(parents=True, exist_ok=True)
    prepare_project(out, builtin, extra_cast={c: extras[c] for c in used if c in extras})
    (out / "characters" / "scene.js").write_text("window.B2M_SCENE = " + json.dumps(scene, separators=(",", ":")) + ";\n", encoding="utf-8", newline="\n")
    html = (KIT / "stage.html").read_text(encoding="utf-8")
    for key, value in (("__WIDTH__", scene["width"]), ("__HEIGHT__", scene["height"]), ("__DURATION__", scene["duration"])):
        html = html.replace(key, str(value))
    (out / "index.html").write_text(html, encoding="utf-8", newline="\n")
    write_hf_files(out, "character-scene")
    return scene


def build_stage3d_project(ids: list[str], out: Path, seconds: float = 6.0) -> None:
    """Write a project from templates/threejs/characters-stage.html: rigged characters as planes in a Three.js set."""
    out.mkdir(parents=True, exist_ok=True)
    prepare_project(out, ids, three=True)
    html = (SKILL / "templates" / "threejs" / "characters-stage.html").read_text(encoding="utf-8").replace("__DURATION__", str(seconds))
    (out / "index.html").write_text(html, encoding="utf-8", newline="\n")
    write_hf_files(out, "character-stage-3d")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build a HyperFrames project from a character scene file.")
    ap.add_argument("--scene", help="scene JSON (see characters/stage.js)")
    ap.add_argument("--stage3d", action="store_true", help="instead of a scene: the 2D-in-3D starter, with --cast and --seconds")
    ap.add_argument("--cast", default="child,crow", help="with --stage3d: comma-separated character ids")
    ap.add_argument("--seconds", type=float, default=6.0, help="with --stage3d: duration")
    ap.add_argument("--out", required=True, help="project folder to write")
    ap.add_argument("--character-file", action="append", default=[], metavar="FILE.json", help="your own character file (repeatable); a scene can then use its id. Its pictures are validated and inlined")
    ap.add_argument("--skin", help="override the scene's skin (line-art, paper-cutout, shadow-puppet, cel-shaded, motion-comic, flat-explainer)")
    args = ap.parse_args(argv)
    if args.stage3d:
        build_stage3d_project([c for c in args.cast.split(",") if c], Path(args.out), args.seconds)
        print(f"2D-in-3D project written to {args.out}")
        return 0
    if not args.scene:
        ap.error("give --scene FILE, or --stage3d")
    try:
        scene = build_scene_project(Path(args.scene), Path(args.out), args.skin, args.character_file)
    except SceneError as exc:
        print(f"character_project: {exc}", file=sys.stderr)
        return 2
    print(f"project written to {args.out}: {scene['width']}x{scene['height']}, {scene['duration']} s, skin {scene['skin']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
