"""Build example 04 end to end: parts -> materials -> optimise -> physics -> HyperFrames project.

    python build.py WORKDIR

Copies the spec, scene and shot into WORKDIR, runs every b2m3d step (the same commands you would
type), and leaves a ready project in WORKDIR/project. Render it with
`npx hyperframes render WORKDIR/project`.
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATERIALS = {"shell": "matte_plastic", "cell": "brushed_aluminum", "board": "pcb_green",
             "cover": "ceramic_white", "lens": "smoked_glass"}


def b2m3d(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "b2m3d", *args], check=True, stdout=subprocess.DEVNULL)


def main(work: Path) -> None:
    (work / "build").mkdir(parents=True, exist_ok=True)
    for name in ("device.py", "scene.json", "shot.json"):
        shutil.copy2(HERE / name, work / name)
    for part, preset in MATERIALS.items():
        raw, coloured, final = (work / "build" / f"{part}{s}.glb" for s in ("_raw", "_mat", ""))
        b2m3d("model", str(work / "device.py"), str(raw), "--param", f"part={part}")
        b2m3d("material", "assign", str(raw), str(coloured), "--assign", f"*={preset}")
        b2m3d("optimize", str(coloured), str(final))
    b2m3d("physics", str(work / "scene.json"), str(work / "build" / "track.json"))
    b2m3d("hf", str(work / "shot.json"), str(work / "project"))
    print(f"ready: {work / 'project'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
