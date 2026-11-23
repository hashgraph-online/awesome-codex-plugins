#!/usr/bin/env python3
"""gen3d.py: make a GLB from an image or a text prompt with a generator YOU installed (Hunyuan3D-2 or TRELLIS).

brief2mp4 never bundles these tools or their model weights. This script only calls them, the way their own
README shows, and writes the mesh where you ask. Each has terms of its own; the note for each is printed before
a run and saved next to the result as <out>.source.json, so the credit and the licence travel with the file.

  gen3d.py doctor                                              # installed or not, licence line, install command
  gen3d.py run hunyuan3d --image part.png --out part.glb       # Hunyuan3D-2: image in, mesh out (--texture to paint it)
  gen3d.py run hunyuan3d --image part.png --out part.glb --device mps   # on a Mac (the tool's default device is cuda)
  gen3d.py run trellis   --image part.png --out part.glb --non-commercial   # TRELLIS: research or evaluation use only (see below)
  gen3d.py run trellis   --prompt "a lamp like a mushroom" --out lamp.glb --non-commercial
  gen3d.py run trellis   --prompt "..." --out lamp.glb --non-commercial --dry-run   # show what would run, run nothing

TRELLIS's own code and weights are MIT, but its GLB export needs nvdiffrast and a Gaussian rasterizer whose licences
allow research or evaluation use only. The script prints that warning and runs TRELLIS only with --non-commercial;
`doctor` prints the install line for those parts only with --non-commercial.

Where the tool lives: set HUNYUAN3D_HOME or TRELLIS_HOME to its folder, and HUNYUAN3D_PYTHON or TRELLIS_PYTHON to
the Python of the environment you installed it in (default: this Python). When the tool is missing the script
prints how to install it and exits 0 with a SKIP line, so an optional route never fails a build.

Next steps for the GLB: `b2m3d optimize`, then `b2m3d material assign` (3d/README-3D.md). A generated mesh is
a starting point: check its scale, its floor contact and its normals before it goes into a shot.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = {
    "hunyuan3d": {
        "name": "Hunyuan3D-2", "by": "Tencent", "repo": "https://github.com/Tencent-Hunyuan/Hunyuan3D-2",
        "home_env": "HUNYUAN3D_HOME", "python_env": "HUNYUAN3D_PYTHON", "module": "hy3dgen",
        "licence": ("Tencent Hunyuan 3D 2.0 Community License: not valid in the European Union, United Kingdom and South Korea "
                    "(its text: \"does not apply in the European Union, United Kingdom and South Korea\"); use of the tool or "
                    "its output outside the Territory is unlicensed (section 5c); if your products had more than 1 million "
                    "monthly active users on the Hunyuan3D 2.0 release date you need a licence from Tencent (section 4); the "
                    "output may not be used to improve another AI model (section 5b). Its Acceptable Use Policy (Exhibit A, "
                    "part of the licence by section 5a) applies too: label published output as machine-generated (item 12), "
                    "no military use (item 19), no use to harm, deceive or impersonate. Read LICENSE in the repository "
                    "before a commercial release."),
        "install": ("install PyTorch for your machine first (pytorch.org), then: git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2 "
                    "&& cd Hunyuan3D-2 && pip install -r requirements.txt && pip install -e .   For --texture also build its two "
                    "texture extensions: (cd hy3dgen/texgen/custom_rasterizer && python3 setup.py install) && "
                    "(cd hy3dgen/texgen/differentiable_renderer && python3 setup.py install).   Its README: macOS, Windows "
                    "and Linux; 6 GB of VRAM for shape, 16 GB with texture; on a Mac pass --device mps"),
        "inputs": ["image"],
    },
    "trellis": {
        "name": "TRELLIS", "by": "Microsoft", "repo": "https://github.com/microsoft/TRELLIS",
        "home_env": "TRELLIS_HOME", "python_env": "TRELLIS_PYTHON", "module": "trellis",
        "licence": ("TRELLIS code and models: MIT (Microsoft Corporation; the Hugging Face model cards say license: mit). "
                    "NON-COMMERCIAL PARTS: the GLB export this wrapper calls (postprocessing_utils.to_glb) imports nvdiffrast "
                    "(NVIDIA Source Code License: \"non-commercially\" means \"for research or evaluation purposes only\") "
                    "and renders with a Gaussian rasterizer (mip-splatting's diff-gaussian-rasterization, Inria and MPII "
                    "licence: \"research and/or evaluation purposes only\"); diffoctreerast, another setup.sh option, has "
                    "the same Inria terms. So making a GLB this way is for research or evaluation, not for a commercial video. "
                    "Requires an NVIDIA GPU with at least 16 GB of memory per its README."),
        "install": ("git clone --recurse-submodules https://github.com/microsoft/TRELLIS && cd TRELLIS && "
                    ". ./setup.sh --new-env --basic --xformers --flash-attn --spconv --kaolin"
                    "   (its README: NVIDIA GPU with 16 GB or more, CUDA Toolkit 11.8 or 12.2)"),
        "noncommercial": ("WARNING: the TRELLIS GLB export needs nvdiffrast, mip-splatting's diff-gaussian-rasterization and "
                          "(optionally) diffoctreerast. Their licences allow research or evaluation use only, not commercial "
                          "use. Install them only if that is your use."),
        "install_noncommercial": "cd TRELLIS && conda activate trellis && . ./setup.sh --nvdiffrast --mipgaussian --diffoctreerast   (research or evaluation use only)",
        "inputs": ["image", "prompt"],
    },
}

HUNYUAN_RUNNER = '''
import json, sys
cfg = json.load(open(sys.argv[1]))
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
extra = {"device": cfg["device"]} if cfg["device"] else {}       # the tool's default is cuda; a Mac needs mps
shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(cfg["model"], **extra)
image = cfg["image"]
if cfg["remove_background"]:
    from PIL import Image
    from hy3dgen.rembg import BackgroundRemover
    image = BackgroundRemover()(Image.open(image).convert("RGB"))
mesh = shape(image=image)[0]
if cfg["texture"]:
    from hy3dgen.texgen import Hunyuan3DPaintPipeline
    mesh = Hunyuan3DPaintPipeline.from_pretrained(cfg["model"])(mesh, image=image)
mesh.export(cfg["out"])
'''

TRELLIS_RUNNER = '''
import json, os, sys
os.environ.setdefault("SPCONV_ALGO", "native")
cfg = json.load(open(sys.argv[1]))
from trellis.utils import postprocessing_utils
if cfg["prompt"]:
    from trellis.pipelines import TrellisTextTo3DPipeline as Pipeline
    source = cfg["prompt"]
else:
    from PIL import Image
    from trellis.pipelines import TrellisImageTo3DPipeline as Pipeline
    source = Image.open(cfg["image"])
pipeline = Pipeline.from_pretrained(cfg["model"])
pipeline.cuda()
outputs = pipeline.run(source, seed=cfg["seed"])
glb = postprocessing_utils.to_glb(outputs["gaussian"][0], outputs["mesh"][0], simplify=cfg["simplify"], texture_size=cfg["texture_size"])
glb.export(cfg["out"])
'''


def python_for(tool: dict) -> str:
    return os.environ.get(tool["python_env"]) or sys.executable


def home_for(tool: dict) -> Path | None:
    value = os.environ.get(tool["home_env"])
    return Path(value).expanduser() if value else None


def is_installed(tool: dict) -> bool:
    home = home_for(tool)
    if home and (home / tool["module"] / "__init__.py").is_file():
        return True
    code = f"import importlib.util, sys; sys.exit(0 if importlib.util.find_spec({tool['module']!r}) else 1)"
    try:
        return subprocess.run([python_for(tool), "-c", code], capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def doctor(non_commercial: bool = False) -> dict:
    """Each tool's state, licence and install line. A non-commercial install line appears only when asked for, after its
    warning."""
    out = {}
    for key, t in TOOLS.items():
        row = {"name": t["name"], "by": t["by"], "repo": t["repo"], "installed": is_installed(t), "licence": t["licence"],
               "install": t["install"], "home_env": t["home_env"], "python_env": t["python_env"]}
        if "noncommercial" in t:
            row["noncommercial"] = t["noncommercial"]
            row["install_noncommercial"] = t["install_noncommercial"] if non_commercial else \
                "not shown: run `gen3d.py doctor --non-commercial` to print it, after reading the warning"
        out[key] = row
    return out


def config(key: str, a: argparse.Namespace) -> dict:
    if key == "hunyuan3d":
        return {"model": a.model or "tencent/Hunyuan3D-2", "image": str(Path(a.image).resolve()), "out": str(Path(a.out).resolve()),
                "texture": a.texture, "remove_background": a.remove_background, "device": a.device or ""}
    default = "microsoft/TRELLIS-text-xlarge" if a.prompt else "microsoft/TRELLIS-image-large"
    return {"model": a.model or default, "image": str(Path(a.image).resolve()) if a.image else "", "prompt": a.prompt or "",
            "out": str(Path(a.out).resolve()), "seed": a.seed, "simplify": a.simplify, "texture_size": a.texture_size}


def note(key: str) -> str:
    t = TOOLS[key]
    return f"{t['name']} ({t['by']}, {t['repo']}). {t['licence']}"


def write_sidecar(key: str, a: argparse.Namespace) -> Path:
    t = TOOLS[key]
    side = Path(str(a.out) + ".source.json")
    side.write_text(json.dumps({
        "tool": t["name"], "by": t["by"], "repo": t["repo"], "licence": t["licence"],
        "input": Path(a.image).name if a.image else None, "prompt": a.prompt or None,
        "made": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "credit": f"3D mesh generated with {t['name']} ({t['by']})."}, indent=2), encoding="utf-8")
    return side


def run(key: str, a: argparse.Namespace) -> int:
    tool = TOOLS[key]
    if bool(a.image) == bool(a.prompt) or (a.prompt and "prompt" not in tool["inputs"]) or (a.image and not Path(a.image).is_file()):
        wanted = " or ".join(f"--{i}" for i in tool["inputs"])
        print(f"gen3d.py: {tool['name']} takes one of {wanted}; a text prompt needs a generator with a text route "
              f"(for {tool['name']}, make an image first), and the image file must exist", file=sys.stderr)
        return 2
    if "noncommercial" in tool and not a.non_commercial:          # opt in before any research-only code is installed or run
        print(f"{tool['noncommercial']}\ngen3d.py: {tool['name']} runs that code to make the GLB; pass --non-commercial to "
              "confirm research or evaluation use", file=sys.stderr)
        return 2
    if not is_installed(tool):
        print(f"SKIP gen3d: {tool['name']} is not installed. Install it yourself, then set {tool['home_env']} to its folder and "
              f"{tool['python_env']} to its Python.\n  {tool['install']}")
        if "noncommercial" in tool:
            print(f"{tool['noncommercial']}\n  {tool['install_noncommercial']}")
        return 0
    runner = HUNYUAN_RUNNER if key == "hunyuan3d" else TRELLIS_RUNNER
    cfg = config(key, a)
    print("NOTE " + note(key), flush=True)
    if a.dry_run:
        print(f"DRY RUN: {python_for(tool)} runner.py config.json\nconfig: {json.dumps(cfg)}\n{runner}")
        return 0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    home = home_for(tool)
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(home) if home else "", os.environ.get("PYTHONPATH", "")]))}
    with tempfile.TemporaryDirectory(prefix="gen3d-") as tmp:      # the runner is ours; the tool is the user's
        script, conf = Path(tmp) / "runner.py", Path(tmp) / "config.json"
        script.write_text(runner, encoding="utf-8")
        conf.write_text(json.dumps(cfg), encoding="utf-8")
        proc = subprocess.run([python_for(tool), str(script), str(conf)], env=env, cwd=str(home) if home else None)
    if proc.returncode != 0 or not Path(a.out).is_file():
        print(f"gen3d.py: {tool['name']} did not produce {a.out} (exit {proc.returncode})", file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "out": str(a.out), "source": str(write_sidecar(key, a))}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor", help="installed or not, licence line and install command for each tool")
    d.add_argument("--non-commercial", action="store_true", help="also print install lines for research-only components")
    r = sub.add_parser("run", help="generate a GLB")
    r.add_argument("tool", choices=sorted(TOOLS))
    r.add_argument("--image")
    r.add_argument("--prompt", help="text prompt (TRELLIS only)")
    r.add_argument("--out", required=True, help="the GLB to write; a .source.json with credit and licence goes beside it")
    r.add_argument("--model", help="model name or folder (default: the tool's own default)")
    r.add_argument("--texture", action="store_true", help="Hunyuan3D: also run its texture model")
    r.add_argument("--remove-background", action="store_true", help="Hunyuan3D: cut out the subject first (for a photo with a background)")
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--simplify", type=float, default=0.95, help="TRELLIS: share of triangles removed")
    r.add_argument("--texture-size", type=int, default=1024, help="TRELLIS: texture size in pixels")
    r.add_argument("--device", help="Hunyuan3D: torch device for the shape model (its default is cuda; mps on a Mac, or cpu)")
    r.add_argument("--non-commercial", action="store_true",
                   help="TRELLIS: confirm research or evaluation use; its GLB export runs non-commercial components")
    r.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "doctor":
        print(json.dumps(doctor(a.non_commercial), indent=2))
        return 0
    return run(a.tool, a)


if __name__ == "__main__":
    sys.exit(main())
