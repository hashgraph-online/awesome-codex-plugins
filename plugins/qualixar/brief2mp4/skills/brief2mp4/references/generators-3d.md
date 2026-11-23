# Optional 3D generators: image or text to mesh, and liquids

Three optional routes that make 3D content brief2mp4 cannot make from code alone. brief2mp4 never includes their code or model weights. It ships small wrappers that call a tool you install yourself, the way each project's own README shows. Each tool has terms of its own, quoted below from the project's files as read on 22 Nov 2026. The notes are information, not legal advice: you decide, but read the licence before a commercial release, because all three have limits that matter, and TRELLIS's GLB export is research or evaluation use only.

| Route | Makes | Wrapper | Licence in one line |
|---|---|---|---|
| Hunyuan3D-2 (Tencent) | a mesh, optionally textured, from an image | `scripts/gen3d.py run hunyuan3d` | Tencent community licence: not valid in the EU, UK or South Korea; its Acceptable Use Policy asks you to label published output as machine-generated |
| TRELLIS (Microsoft) | a mesh from an image or a text prompt | `scripts/gen3d.py run trellis --non-commercial` | MIT for its own code and models, but **the GLB export runs non-commercial components** (nvdiffrast, a Gaussian rasterizer): research or evaluation use only |
| FLIP Fluids (Blender add-on) | a baked liquid simulation | `3d/templates/recipes/b2m_flip_bake.py` | GPL add-on, sold on Superhive, free watermarked demo |

When to reach for a generator: a one-off prop or hero object that would take an hour to model (a gnarled lamp, a toy, a statue) and that will sit in a 3D shot. When not to: anything the pack's own `model` command builds from numbers (brackets, gears, enclosures, logos), because a generated mesh has unknown scale, soft edges and no part names, so it cannot be exploded or measured. Text or image generators also invent detail: a generated product is not your product. Never use one to show a real product's real design.

After either generator, the GLB goes through the pack like any other: `b2m3d optimize in.glb out.glb --simplify 0.5`, then `b2m3d material assign`, then a shot. Check scale (generated meshes arrive at arbitrary size), floor contact (put the lowest point on y=0) and normals in a still before the full render.

## Hunyuan3D-2 (image to 3D)

Repository: https://github.com/Tencent-Hunyuan/Hunyuan3D-2 (about 15.5k stars). Weights on Hugging Face as `tencent/Hunyuan3D-2`. Its README says "Hunyuan3D 2.0 supports Macos, Windows, Linux" and "It takes 6 GB VRAM for shape generation and 16 GB for shape and texture generation in total". Its pipeline's `from_pretrained` defaults to `device='cuda'`, so on a Mac pass `--device mps` (or `cpu`). No route of it was tested here.

Install (its README): install PyTorch for your machine from pytorch.org first, then `git clone`, then `pip install -r requirements.txt` and `pip install -e .` inside the clone. `--texture` also needs its two texture extensions built: `python3 setup.py install` inside `hy3dgen/texgen/custom_rasterizer` and inside `hy3dgen/texgen/differentiable_renderer`. `gen3d.py doctor` prints the whole line.

```bash
export HUNYUAN3D_HOME=~/hunyuan3d-2          # the clone
export HUNYUAN3D_PYTHON=~/envs/hy3d/bin/python  # the Python you installed it into
python3 <skill>/scripts/gen3d.py doctor
python3 <skill>/scripts/gen3d.py run hunyuan3d --image lamp.png --out lamp.glb            # shape
python3 <skill>/scripts/gen3d.py run hunyuan3d --image lamp.png --out lamp.glb --texture  # shape and texture
python3 <skill>/scripts/gen3d.py run hunyuan3d --image photo.jpg --remove-background --out thing.glb
python3 <skill>/scripts/gen3d.py run hunyuan3d --image lamp.png --out lamp.glb --device mps          # on a Mac
```

The script calls `Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')` and `pipeline(image=...)`, and with `--texture` `Hunyuan3DPaintPipeline`, as the README shows, then exports the mesh. It has no text route: for text, make a picture first with an image tool you have the rights to use.

Licence, from its LICENSE file (title "TENCENT HUNYUAN 3D 2.0 COMMUNITY LICENSE AGREEMENT"):

> THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA AND IS EXPRESSLY LIMITED TO THE TERRITORY, AS DEFINED BELOW.

> "Territory" shall mean the worldwide territory, excluding the territory of the European Union, United Kingdom and South Korea.

> You must not use, reproduce, modify, distribute, or display the Tencent Hunyuan 3D 2.0 Works, Output or results of the Tencent Hunyuan 3D 2.0 Works outside the Territory. Any such use outside the Territory is unlicensed and unauthorized under this Agreement. (section 5c)

Also in the file: if, on the Hunyuan3D 2.0 version release date, your products or services had more than 1 million monthly active users in the preceding month, you need a licence from Tencent (section 4), and the tool or its output may not be used to improve another AI model (section 5b). Section 5a makes its Acceptable Use Policy (Exhibit A) part of the licence. Two of its items bear on publishing video: item 12 forbids placing generated content "in any public context ... without expressly and conspicuously identifying that the information and/or content is machine generated", and item 19 forbids use "For military purposes"; the others bar harm, deception, impersonation and the like. The same file says "Tencent claims no rights in Outputs You generate" (section 6d). In plain words: if you are in the EU, UK or South Korea, this licence does not cover you, including for the meshes it produces; elsewhere it is a community licence with the limits above, and a published video that shows a Hunyuan3D mesh should say the mesh is machine-generated. The repository's example script still carries an older header calling it a "NON-COMMERCIAL" licence, so read the LICENSE file for the version you downloaded and do not rely on the script header.

Credit when you publish, which also labels it as machine-generated: "3D mesh generated with Hunyuan3D-2 (Tencent)". Section 3 of the licence encourages a "Powered by Tencent Hunyuan" mark and requires a notice file when you distribute the model itself; the wrapper writes `<out>.source.json` with the credit line and licence summary next to the GLB.

## TRELLIS (image or text to 3D)

**Non-commercial in practice.** TRELLIS's own code and weights are MIT, but the GLB export it documents, and that the wrapper calls, runs components whose licences allow research or evaluation use only (quoted below). So `gen3d.py` runs TRELLIS only with `--non-commercial`, printing the warning first, and its default install line leaves those components out; `gen3d.py doctor --non-commercial` prints their install line after the same warning. Do not use a TRELLIS mesh made this way in a commercial video.

Repository: https://github.com/microsoft/TRELLIS (about 14.4k stars). Models on Hugging Face: `microsoft/TRELLIS-image-large`, `TRELLIS-text-base`, `-large` and `-xlarge`. Its README documents "an NVIDIA GPU with at least 16GB of memory" and CUDA Toolkit 11.8 or 12.2; its `setup.sh` builds several CUDA submodules. Not tested on a Mac.

```bash
export TRELLIS_HOME=~/TRELLIS
export TRELLIS_PYTHON=~/miniconda3/envs/trellis/bin/python
python3 <skill>/scripts/gen3d.py doctor --non-commercial        # prints the research-only install line after a warning
python3 <skill>/scripts/gen3d.py run trellis --image lamp.png --out lamp.glb --non-commercial
python3 <skill>/scripts/gen3d.py run trellis --prompt "a lamp that looks like a mushroom" --out lamp.glb --non-commercial
```

The script calls `TrellisImageTo3DPipeline` or `TrellisTextTo3DPipeline` from `from_pretrained`, `pipeline.run(source, seed=1)` and `postprocessing_utils.to_glb(...)` (`--simplify` 0.95, `--texture-size` 1024 by default), as the README and its `example.py` and `example_text.py` show.

Licence, from the README: "TRELLIS models and the majority of the code are licensed under the MIT License. The following submodules may have different licenses:" followed by `diffoctreerast` and a modified FlexiCubes from NVIDIA. The LICENSE file is "MIT License, Copyright (c) Microsoft Corporation", and the Hugging Face model cards for `TRELLIS-image-large` and `TRELLIS-text-xlarge` carry `license: mit` in their metadata. So the weights are MIT as the project states them. The components the GLB export needs are not:

- `postprocessing_utils.to_glb` imports `nvdiffrast.torch` and bakes the texture with a `GaussianRenderer`. nvdiffrast's LICENSE is the "Nvidia Source Code License (1-Way Commercial)": "The Work and any derivative works thereof only may be used or intended for use non-commercially", where "non-commercially" means "for research or evaluation purposes only and not for any direct or indirect monetary gain".
- The Gaussian rasterizer that `setup.sh --mipgaussian` builds is mip-splatting's `diff-gaussian-rasterization`, under the Inria and MPII Gaussian-Splatting licence: "The *Software* may be used "non-commercially", i.e., for research and/or evaluation purposes only."
- `diffoctreerast` (`setup.sh --diffoctreerast`), named in the README above, carries the same Inria sentence in its LICENSE.

These limit use, not only redistribution: running them to make a mesh for a paid or monetised video is outside their terms. That is a reading of the licence text, not legal advice.

Credit: "3D mesh generated with TRELLIS (Microsoft)", sidecar as above.

## FLIP Fluids (liquids, a Blender add-on)

Project: https://github.com/rlguy/Blender-FLIP-Fluids (about 2k stars); bought on Superhive (formerly Blender Market), https://superhivemarket.com/products/flipfluids. It simulates liquids: pouring, splashes, a glass filling. It is a Blender add-on, so brief2mp4 neither includes nor wraps its code; it only runs Blender with it.

Licence, from the repository's README: "This program uses multiple licenses." "The Blender addon code is licensed under the GPL." "The FLIP Fluids simulation engine is licensed under the MIT license." Some bundled content (example scenes, media, features such as colour blending) is under a "Standard Royalty Free" licence and ships only with the paid add-on. The full add-on is sold; a free Demo add-on "can do almost everything that the full version can" with limits, the main one being that "simulation meshes are watermarked with FLIP Fluids Addon text", baked into the meshes. Use the demo to test the pipeline and buy the full add-on before a published film. GPL governs the add-on's code if you redistribute it; as a general rule of the GPL, running a GPL program to make a video does not put the video under the GPL, but that is not legal advice, and the bundled royalty-free content has its own licence file.

The recipe runs without `--factory-startup`, so every add-on you enabled loads with it (an MCP add-on that starts its own server, for one), and if "Auto Run Python Scripts" is on in your Preferences, scripts saved inside the `.blend` run too: open only files you trust. It keeps the file's own engine, samples and view transform unless you pass `--engine` or `--samples`, and renders the whole range as one animation render, like the add-on's wiki (`blender -b file.blend -a`).

How it fits: the liquid is set up in Blender with the add-on's own tools (a Domain, a Fluid object, Obstacles), which is a window workflow and the right place for it, so the live route (`references/blender-live.md`) suits it. Save the `.blend`. Then bake and render headless with the recipe:

```bash
# enable the add-on in Blender's Preferences first; do NOT use --factory-startup, it would unload it
blender -b pour.blend -P <skill>/3d/templates/recipes/b2m_flip_bake.py -- --out frames --render-frames 1-120
```

`b2m_flip_bake.py` runs the add-on's documented command-line operator `bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()` and renders PNG frames. With `--bake 0` it renders an existing cache. When the add-on is not enabled it prints a `skipped` result with the reason and exits normally. What was tested, with a real Blender: that skip path, and, with a stand-in operator in place of the add-on, that the file's Cycles samples and view transform survive and the whole range renders. The real bake was not run, because the add-on is not installed on the build machine; the operator name is taken from the add-on's wiki page "Baking from the Command Line".

A liquid bake can be slow and large on disk. Bake a short span first, look at three stills, then the full range.

## Credit lines

Every tool named here is in `references/ecosystem.md` with its licence, and each generated file carries its own credit sidecar. Add the credit to a video's description when a generated mesh or a simulated liquid is on screen.
