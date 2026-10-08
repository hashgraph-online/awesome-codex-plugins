---
name: anime-reaction-gif
description: Create original anime-style reaction stickers as looping GIFs and MP4 previews, using generated character pose sheets and timed key poses. Use for expressive character reactions or matching sticker sets.
---

# Anime Reaction GIF

Create a recognizable character reaction with distinct facial/limb poses,
readable holds and a return to the starting pose. Match the user's character,
style, action and palette; the bundled cat-eared chibi is an example, not a preset
every request must use. These are key-pose reaction stickers, not continuous
3D skeletal animation.

## Make the pose sheet

Read [references/spritesheets.md](references/spritesheets.md) for the prompt
scaffold, identity invariants and timing choices. Use the built-in `image_gen`
tool for original bitmap poses. Follow the installed imagegen skill when
available; it is not a dependency of this package. Built-in generation does
not require an API key. If that tool is unavailable, report the missing
capability rather than silently choosing a different paid API.

Inspect a local identity/reference image before passing it to image_gen. For a
matching set, reuse the selected original character as the identity reference.
Generate one sheet per reaction with exact dimensions, equal row-major cells,
no gutters, stable camera/anchor and every body part inside each cell. Save
the chosen generated sheet and complete prompt in the user's output directory.
Six poses / 3×2 is a quick baseline; use a different grid or more real poses
when the action needs them. Inspect the actual sheet before slicing it.

## Assemble

Requires Python 3 and system FFmpeg/ffprobe with PNG, GIF, FFV1 and libx264.
The assembler uses the standard library only; no pip install is needed.
Resolve script and asset paths from **this skill directory**, which also works
when only this folder has been installed:

```sh
python3 <skill-dir>/scripts/assemble_sheet.py <output-dir>/reaction-sheet.png \
  --output <output-dir>/reaction.gif \
  --columns 3 --rows 2 --cell-size 512 --size 384 --fps 12 \
  --sequence 0,1,2,3,4,5,0 \
  --durations .4,.25,.25,.65,.3,.4,.35 --background 0xf5caba
```

Choose holds/order for the reaction; omit them to play all cells with default
holds. Grid, expected cell size, output size, FPS and inset are configurable.
The script checks equal pixel cells and expected dimensions before writing;
visual review is still needed for a wrongly drawn grid. Crops, scaling,
palette creation and encoding run sequentially through FFmpeg without Python
full-frame caches. It exports a looping GIF, an opaque H.264 MP4 preview,
pose crops and decoded proof. Choose a fresh output name unless replacement
is intended; `--overwrite` replaces that output's artifacts.

## Inspect and deliver

Play the actual exports and inspect their decoded contact sheet, first/last
frames and mobile preview. Check emotion, identity, limbs, cell bleed, timing
and seam. The report records frames, duration, infinite loop and source/output
hashes. More output FPS cannot replace missing poses. Add real intermediate
poses when smoother animation is required.

Keep artwork free of captions/branding by default; write social copy separately
unless the user requests in-art text. Supply clickable GIF/MP4/proof paths and
the generation prompt(s), naming built-in image_gen as the generation mode.
Publishing requires authorization; prior explicit publishing instructions
remain valid.

Bundled [examples](assets/examples/) contain three approved reactions, their
source sheets, exact prompts and metadata. They can be assembled offline;
creating a new original character requires image generation.
