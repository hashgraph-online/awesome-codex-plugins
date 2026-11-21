# Research: Verification

A deck that opens is not a deck that is right. This package proves four separate things before it hands over a file, and each one catches a defect the others miss.

## 1. The Four Gates

| Gate | Question | How it is answered | Failure code |
|---|---|---|---|
| Structure | will a strict reader accept the XML? | every slide and chart part validated against the ECMA-376 XSD | build fails |
| Layout | does the text fit the shape it was given? | the preview measures each text box after layout | `LAYOUT_OVERFLOW` |
| Placement | is anything off the canvas or on top of something else? | absolute rectangles compared on the rendered stage | `LAYOUT_OUTSIDE`, `LAYOUT_OVERLAP` |
| Balance | is the page actually used? | the bounding box of all content as a share of the canvas | `LAYOUT_SPARSE` |

The four are independent on purpose. Text that fits can still sit on top of a caption; a full page can still be unbalanced; both can be produced by XML that validates perfectly.

## 2. Why Measurement, Not Estimation

An estimate of text height from a character count is wrong for every script that does not use a fixed advance width. This package measures the advance of each character against the font family and the point size, then counts the lines the box will take, and uses that number to decide card heights before anyone looks at the render.

The measurement is a model, so the render is the check. The preview draws the same boxes at 1/9525 scale (one EMU to one CSS pixel is exact at 9525 EMU per point, and the stage is 1280 × 720 for a 12192000 × 6858000 canvas), then reads `scrollHeight` and `scrollWidth` from each text element. Where the model and the browser disagree, the browser wins, and the report says which shape.

## 3. Determinism

Two renders of the same spec must produce byte-identical files, or a diff of two decks shows changes that are not changes.

Three things break this in a `.pptx`: the zip archive records a modification time, file order inside the archive is whatever the filesystem returns, and document properties often carry a creation date.

This package fixes the timestamp of every part to `1980-01-01 00:00` before archiving, sorts the member list, and uses `zip -X` to strip the extra attributes. Two consecutive renders of a 17-slide demo deck then hash identically — that comparison was run, not assumed.

## 4. What The Inspector Adds

`inspect-deck.sh` reads a deck it did not produce. It answers: how many slides, what each one says, whether a shape leaves the canvas, whether a chart carries cached values, whether speaker notes exist.

It reads slides in the order `presentation.xml` declares them, not the order their file names sort. A lexical listing puts `slide10.xml` before `slide2.xml`, so a 17-slide deck reported its outline out of order — a real defect found while reviewing this package's own output.

## 5. What Is Not Proven Here

- **PowerPoint itself.** No PowerPoint, and no LibreOffice, on the machine that built this. Schema validity and cached values are a specification-based argument that a real reader opens the file; they are not an observation of one doing it.
- **Font rendering.** The deck records font names. A reader without the font substitutes one, and the substituted font's line breaking differs from the measured one.
- **Projector colour.** Contrast is computed from the token values; how a specific projector renders them is not measured.

Each of these is stated in the delivery report rather than glossed over.

## 6. The Repair Loop

Render, read the report and every PNG, fix the spec, render again — at most three passes. A pass that raises the number of checks is reverted, because an edit that fixes one overflow and creates two is a wrong edit. When the cap is spent the deck is not delivered and the remaining defects are named with the slide and shape id.

Looking at the PNGs is not optional. Three of the defects fixed while building this package — a combo that drew no bars, a scatter plotted as a diagonal, an area chart filled with an opaque block — passed every automated check and were visible only in the image.

The bundled example caught two more that the gates did catch, which is the argument for shipping a checked spec alongside the code. Its bullets slide failed `LAYOUT_OVERLAP` because a centred text box kept the full body height and so slid its bottom edge into the footer: the box now takes the height of its block. Its timeline rendered with no detail line at all, silently, because the layout read `detail` while the documented field is `text` — a missing field is not a crash, it is an empty box, and only reading the rendered page shows the difference between an empty field and an unset one.

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| View every slide thumbnail before delivery | <https://github.com/anthropics/skills> |
| Inspect / edit / verify loop over one deck file | <https://github.com/EveryInc/hands-on-deck> |
| Package part structure and relationship resolution | <https://github.com/scanny/python-pptx> |
| Rendering round trip as a verification step | <https://github.com/iOfficeAI/OfficeCLI> |
| Deck review checklist | <https://github.com/liustack/pptwise> |
| A `pptx` is a zip of XML parts with a declared slide order | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |

### Evidence grade

`LOCAL` — every gate described here runs in this package; the determinism hash, the schema sweep, and the slide-order defect were all produced by running the scripts on 2026-11-14. The limits in section 5 are absences observed on the build machine, not claims about other environments.
