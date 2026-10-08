# Pose sheets and timing

Read this when generating a new reaction or extending an existing character.
Adapt the user's character, medium, background and action. A robot, animal or
2D character works just as well as the chibi character in the examples.

## Prompt scaffold

```text
Use case: illustration-story.
Asset type: production animation sprite sheet for a reaction sticker.
Create one [WIDTH]×[HEIGHT] image with exactly [COLUMNS] columns and [ROWS]
rows of equal [CELL_WIDTH]×[CELL_HEIGHT] cells, zero gutters and no separators.
Subject: the same original [CHARACTER DESCRIPTION] in every cell.
Identity invariants: [face / hair or silhouette / palette / clothing / props].
Style: [USER'S STYLE]. Backdrop: identical [BACKGROUND] in every cell.
Camera: [FRAMING], fixed size and anchor in every cell. Keep hands, ears,
props and feet comfortably inside cell edges. Same lighting/contact shadow.
Action: [REACTION]. Row-major stages: [ONE DISTINCT REAL POSE PER CELL].
Final pose returns toward the first. Change the relevant face/limbs;
do not substitute camera movement for character motion.
No text, numbers, panel labels, watermarks or grid lines unless requested.
Consistent anatomy, no extra or duplicated limbs.
```

Six poses in a 3×2 sheet are a useful baseline: neutral, anticipation, action,
peak, recovery, neutral. They are not a requirement. Use more real poses for a
smoother result, with a larger grid or several identity-preserving sheets.
Do not advertise six poses as continuous 3D skeletal animation. Raising FPS
only repeats existing poses. Avoid blending different eye/mouth/hand drawings
to simulate in-betweens.

For a recurring character, inspect the selected identity image before using it
as the reference for the next sheet. Tell image_gen which image is the identity
reference and list face, outfit, palette, camera and background invariants.
Save the complete prompt and selected sheet. Inspect every cell; generated
dimensions or a correct grid do not guarantee correct character/cell boundaries.

## Assembly choices

- Indexes are zero-based and row-major. A 3×2 sheet reads `0,1,2,3,4,5`.
- `--sequence` selects order and may repeat poses. Its default plays all
  declared cells and returns to cell 0, so other grid sizes work as well.
- `--durations` is one hold per entry. Give readable expressions longer holds
  and fast reactions shorter ones. Each hold must last at least one output
  frame. GIF timing is quantized to 10 ms.
- Supply `--cell-size 512` when the generation specification expects square
  512-pixel cells. Source dimensions must divide exactly into rows/columns.
  Without this option, equal rectangular cells fit into the square output.
- An evenly divisible but semantically wrong grid still needs visual review.
  The assembler cannot identify where the drawn panels actually begin.
- `--inset` removes the same border from every cell. Use it for measured
  gutters; it cannot repair an irregular grid or clipped character.
- Match `--background` to the sheet for letterboxing. The assembler uses an
  opaque RGB intermediate, so its GIF and yuv420p MP4 exports are opaque.
  Transparent stickers require actual alpha from image_gen and an
  alpha-preserving assembly pipeline, followed by inspection of GIF edges
  and transparency.

The [bundled examples](../assets/examples/) retain original generated sheets
and exact prompts. Timing lists are in `manifest.json`. New assembly runs may
produce different GIF bytes across FFmpeg versions.

## Inspect actual exports

The script writes a GIF-decoded contact sheet, first/middle/last images,
a 240-pixel preview and JSON with output/source hashes and timings.
Use those with playback to check emotion, identity, missing limbs,
neighbor-cell bleed, rhythm and loop seam. Equal first/last frames alone do
not prove that the movement reads well. Fix pose/identity problems through
image_gen; adjust holds/order when the poses are good but the rhythm is poor.
