# The before and after board

Step 7 shows the user the render before they read about it. This file sets how the board is filled, captured, read back, made to stand alone and delivered. The AFTER pane is the applied change captured, never redrawn from memory.

## Fill the template

The board is the skill's `assets/board.html`. Copy it next to the two pane images and fill in the JSON block inside it. Change nothing else: the layout, the type and the marks are set there. Rewriting them spends tokens on CSS and loses the type rules that keep the words readable. The data carries:

- **The two panes.** Paths to the BEFORE and AFTER captures, made however the environment allows: screenshots of the running source, exports of the original and the new frame, or an HTML mockup of the target in the source's palette, type and spacing, then captured. Both show the full target at the same scale and crop, and nothing outside the region differs. The board holds those captures as images and never rebuilds the UI itself, so what the user reads about is what was applied.
- **One entry per move**, numbered in the problem list's order, which is the report's order. A cut move has no entry. Each entry carries:
  - its bold lead-in, one-line explainer and References line from the report, the last as each app's name and `mobbin_url` so the comparison file links to them;
  - the part it touched as a rect on every pane it is on: a removed part on BEFORE only, a new one on AFTER only, a changed one on both.
- **The theme** the baseline was captured in. A second board in the source's other theme follows only when the source exposes it and the render can be produced in it.
- **The meta line**, top right beside the stamp: platform and target, the number of changes and of references ("iOS paywall, 2 changes, 3 references").
- **The mark colour**, `--call` in the template, is the design system's blue. When the product's accent is close to that blue, set `--call` to `var(--warning)`, the system's amber: a mark in the accent reads as part of the render instead of a note on it. The rest of the board is the Mobbin design system and does not change.

## Rects

Rects are percentages of the pane, so they hold at any capture scale. Each row's crops are cut from the same two panes, so a move needs no screenshot of its own.

A rect is measured, never estimated from the picture: the element's bounding rectangle from the browser for a codebase or live page, or the node's bounds for a design file, each divided by the pane's size. Where nothing can measure it, as on an image-only source, the entry carries no rect for that pane. The badge and the row's lead-in still say which part, and the row's crops are cut from the region you can name. A loose crop reads fine; a guessed outline reads broken.

## Capture

Capture it with whatever the host drives a browser with. Aim for three things: the fonts and both panes loaded before the shot, the whole board in frame, and twice the pixel scale, which makes it readable at about 2000 px wide.

- **A browser you can script** gives all three: wait for `document.fonts.ready` and for both images to complete, then shoot the `.board` element at a device pixel ratio of 2.
- **A tool that only captures a page as it stands** gets the same detail from `--board-zoom: 2` at the top of the file, which renders every pixel twice over.

Either way the type stays its on-screen size, since growing it to reach the width makes a wall of heavy text. Never rasterise through an SVG to PNG converter: it fetches neither the fonts nor the panes.

Then look at the capture. A board much under 2000 px wide, a blank pane, or a line you cannot read at full size means the capture missed. The board file then goes to the user in its place, with one line in the report saying the image could not be captured.

## Read it back

Read the composed image before writing a word about it.

1. **The marks.** Every outline encloses its whole part and cuts no text, every badge sits on a corner and covers nothing, and the marks read as notes on the render, not part of it. On a miss, correct the rect and capture again, once.
2. **Row by row.** Where a row's BEFORE and AFTER crops read the same at that scale, the move did not visibly answer its problem. Either shrink its report entry to what the crops show, or cut the move: the row goes, the problem's entry says it stayed and why, and the problem goes back in the Deferred record.
3. **The top block.** Credit a visible difference there to the move that made it. A landing the eye finds because of one move is not written up under another.

## Embed the images

The board names its panes by path, so it only shows them while they sit beside it. A host that sends files one at a time, or a user who forwards the board, leaves them behind, and every pane and crop goes blank. Once the marks pass and the last capture is taken, put the images inside the file:

```
python3 <this skill's folder>/scripts/embed-images.py board.html
```

It swaps each image path in the JSON for the image itself and prints the count and the new size. A path that names no file stops it with the path named and the board unchanged: fix the path and run it again. Where Python cannot run, make the same change with what the host has: each path becomes `data:<the image's type>;base64,` followed by the file's bytes in base64, such as `data:image/png;base64,iVBOR…`.

Embed last. The board then runs to hundreds of kilobytes, too large to read back or edit, so a rect that still needs fixing is fixed first. Never deliver a board before this step: on its own it shows nothing.

## Deliver

Deliver by what the host can show, handing the files over as [report.md](report.md) says.

| Host | Deliverable |
| --- | --- |
| Shows images in the reply | the PNG, and the board file beside it past three moves, since the chat scales a 2000 px image down past reading size |
| Shows no image inline | the board file, with the PNG attached |
| Cannot capture | the board file alone |

When the source is an image and not even the board file can be produced, the report's Degraded line names it. For any other source, a render that cannot be captured is described in the report and is not a degraded run.
