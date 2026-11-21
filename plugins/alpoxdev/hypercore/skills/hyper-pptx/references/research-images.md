# Research: Images

Picture placement is where generated decks most often look wrong: a stretched photo, a letterbox the author did not expect, a caption on top of the picture it describes, or a hero that reads as a dark rectangle because the scrim is too strong. This file records the geometry rules this package follows and why.

## 1. The Two Operations

A picture is fitted into a box in exactly two ways, and the choice is about what may be lost.

| Operation | Keeps | Loses | Use when |
|---|---|---|---|
| `contain` | the whole picture | part of the box (letterbox) | the picture is evidence and must not be cropped, e.g. a screenshot |
| `fill` | the whole box | part of the picture (crop) | the picture is texture or mood, e.g. a hero background |

Both centring decisions come from the same two ratios: the source aspect $R = w_s/h_s$ and the box aspect $Q = W/H$.

For `contain`:

$$w = \min(W,\; H \cdot R), \qquad h = w / R$$

For `fill`, the crop is symmetric and expressed as a percentage of the source, which is what `a:srcRect` takes:

$$c_l = c_r = \frac{1 - Q/R}{2} \times 100\%, \qquad c_t = c_b = 0 \quad (R > Q)$$

The percentages, not pixels, matter because `srcRect` is defined in thousandths of a percent of the source. Writing the crop there means PowerPoint, and any converter, shows the same window.

## 2. Dimensions Come From The File

The package reads the pixel dimensions from the file header before layout: PNG from the `IHDR` chunk, JPEG from the first `SOFn` marker. The author's `aspect` is only a fallback for a file that cannot be read.

A wrong aspect is not a cosmetic error. With `contain` it letterboxes a correct crop into a wrongly shaped box; with `fill` it crops the wrong band off the picture. Both look like a broken deck and neither is visible in the spec.

## 3. Captions Reserve Their Band

A caption under a picture is a real text shape with its own height. The picture's height is computed after the caption band is subtracted, so a caption can never land on the picture above it. This is why a gallery's pictures shrink when captions are added: the captions took the space first.

## 4. The Scrim

A hero puts text over a photograph. Text directly on a picture fails on any busy image, so the package inserts a flat black overlay at a fixed alpha and draws the text on that, at full contrast.

| `scrim` | Result |
|---|---|
| 0.35 to 0.45 | light image, text must be short and large |
| 0.55 (default) | safe over most photographs |
| 0.70 and above | near-solid, image becomes texture |

The rule is not "add a gradient": a gradient scrim is invisible over a picture with its own light gradient, and it cannot be checked by reading a value. A flat alpha can be reasoned about and measured.

## 5. What The Render Checks

| Check | Condition |
|---|---|
| `IMAGE_SMALL` | a source under 320 × 180 will look soft when projected |
| `IMAGE_EXTREME` | an aspect under 1:5 crops badly in any box |
| `IMAGE_NO_ALT` | a picture with no alternative text is a delivery defect |
| `IMAGE_REMOTE` | a remote URL is refused, so a deck never depends on a network |
| `IMAGE_UNREADABLE` | a file whose pixel size cannot be read is refused, not guessed |

Alt text is written into the picture as `descr`, which is what a screen reader announces and what a reader sees when the image fails to load.

## 6. What Was Rejected

- **Automatic side selection.** Deciding left vs right from content type is a guess that reads as arbitrariness. The author names the side.
- **Background-image cropping via shapes.** Some generators put a picture as a shape fill with a texture offset. `srcRect` on a `p:pic` is simpler, survives round-tripping, and keeps the picture as a picture.
- **Stretched to fit.** Filling the box regardless of aspect is the single most recognisable mark of a generated deck.

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| `a:srcRect` crop is expressed as a percentage of the source | <http://www.datypic.com/sc/ooxml/e-a_srcRect-1.html> |
| Picture part structure and `descr` alternative text | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| Contain and cover geometry with source aspect ratios | <https://github.com/hugohe3/ppt-master> |
| Alt text as a delivery requirement for generated decks | <https://github.com/microsoft/Resource2Skill> |
| Image placement pipeline and its review rules | <https://github.com/eddyzzl/imagegen-pptx-pipeline> |

### Evidence grade

`LOCAL` — the geometry is implemented in `assets/runtime/layout.jq` and verified against rendered slides on 2026-11-14; `srcRect` percentages were checked by unzipping the output and reading the picture XML. The projection thresholds (320 × 180, 1:5) are this package's choices, not measurements from the sources.
