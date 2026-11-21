# PPTX Internals

Read this when a deck must open without a repair prompt, when an edit must not disturb a template, or when someone asks why this package writes OOXML by hand instead of calling a library.

## Contents

- The package is a zip of parts
- The six parts every slide needs
- Why one blank layout and absolute geometry
- What makes PowerPoint offer to repair a file
- Where motion lives in a slide part
- Run splitting, the reason a text edit misses
- What this package deliberately does not do

## The Package Is a Zip of Parts

A `.pptx` is an OPC package: a zip whose entries are XML parts named by path, plus one `[Content_Types].xml` that declares every part's media type. Two rules follow, and both are load-bearing.

Every part must appear in `[Content_Types].xml`. A slide whose type is not declared is invisible to PowerPoint even though the XML is present and well-formed.

Every relationship target must exist. A `.rels` part maps a short id such as `rId2` to a path. If the target file is missing, the package is broken at open time, not at render time.

Zip entry order and timestamps do not matter, which is why the renderer fixes every timestamp to 1980-01-01 and uses `zip -X`, so the same spec produces byte-identical output and a diff of two builds is meaningful.

## The Six Parts Every Slide Needs

| Part | Holds | Measured effect when removed |
|---|---|---|
| `ppt/slides/slideN.xml` | shapes, background | open fails: `no relationship with key 'rId11'` |
| `ppt/slides/_rels/slideN.xml.rels` | layout, notes, chart, image relationships | opens, but reading `slide_layout` raises `KeyError: no relationship of type slideLayout` |
| `ppt/notesSlides/notesSlideN.xml` | speaker notes | opens; the notes pane has no content |
| `ppt/notesSlides/_rels/notesSlideN.xml.rels` | back-link to the slide | opens; notes still read |
| a `sldId` in `ppt/presentation.xml` | ordering and the relationship | opens with one fewer slide; the part stays orphaned in the zip |
| an `Override` in `[Content_Types].xml` | the slide's media type | opens to a part that is not a slide: `'Part' object has no attribute 'slide'` |

Those results come from deleting one part at a time from a known-good deck and reopening it in python-pptx. Two of the six fail loudly; the rest fail silently, which is the worse failure for an agent, because the file looks fine until a person opens it or a downstream tool walks the deck.

That is why `edit-deck.sh --drop-slide` removes all six and then re-verifies every XML part and every relationship, and why an orphaned part counts as a failure even when the deck still opens.

## Why One Blank Layout and Absolute Geometry

A template-driven writer sets placeholders and lets the layout decide position, size, and inheritance. That produces decks that match a corporate template, and it also produces surprises: text that inherits an 18-point size from a master, a title box that jumps when the layout changes, a body that overflows because the master's inset is 0.1 inch not 0.05.

This package does the opposite. It ships one blank layout, one master, and one theme, and writes every shape with absolute EMU coordinates. Consequences:

- The writer's coordinate always wins; nothing is inherited.
- The same resolved JSON drives the PPTX and the HTML preview, so the preview cannot drift from the file.
- A layout check computed in the browser is a valid check of the .pptx.
- A deck does not adopt the user's template. Editing an existing deck must therefore happen through `edit-deck.sh`, which preserves the original package and touches only what it names.

EMU is 914400 per inch, so a 13.333 × 7.5 inch slide is 12192000 × 6858000. Point sizes are a different unit: `sz` attributes and `spaceBefore` are hundredths of a point, and the browser needs pixels, so the conversion is `px = pt * 12700 / 9525`.

## What Makes PowerPoint Offer to Repair a File

| Symptom | Cause |
|---|---|
| repair prompt on open | a part has no `[Content_Types].xml` entry |
| repair prompt on open | a `.rels` target path does not exist |
| repair prompt, then slides vanish | a `sldId` points at a removed relationship |
| missing image | `r:embed` id with no image relationship, or an undeclared image extension |
| chart shows no data | chart part missing its cached categories and values |
| notes pane empty | `notesSlide` part exists but the slide has no relationship to it |
| repair prompt after a transition, then slides vanish | a `p:transition` child that is not an ECMA-376 effect element |
| repair prompt after an animation | a duplicated `p:cTn id`, or a `p:spTgt spid` with no such shape |
| picture shows the wrong crop | a `srcRect` whose fractions are outside 0 through 1 |

`render-deck.sh` checks well-formedness of every XML part, every relationship target on disk, and the three motion rules described below, and exits 1 rather than delivering a package with a dangling reference. It cannot check the repair prompt itself, because PowerPoint is not available on this machine; that row is specification-based, not observed.

## Where Motion Lives in a Slide Part

`p:sld` ends with an optional `p:timing`, and before it an optional `p:transition`. In the written part that means, in order: `p:cSld` with the shape tree, `p:clrMapOvr`, `p:transition`, `p:timing`. The `transition` element sits outside `p:cSld`; a transition written inside the shape tree is ignored by PowerPoint and the slide shows a hard cut with no error.

A slide with `n` animated targets has one timing tree whose `p:tnLst` holds one `p:par` per click group. Within a group, each target contributes a `p:par` with one `p:cTn` row, and the row's `p:childTnLst` holds the behaviours that do the work.

Ids are unique per slide, not per deck: two slides can both use `id="1"`. Ids `1` through `3` are also used by the slide's own `p:cTn` root chain, so animation rows start at `4`. Each row reserves four ids and each click-group wrapper takes one, which is why the check for a repeated id runs per slide.

A `p:spTgt` names a `p:cNvPr id`, the same number a shape carries in the shape tree. That id is assigned once in the layout pass, so the animation target and the shape it animates cannot drift apart; two passes computing the number separately is the bug that writes a target pointing at a shape that is not there.

Picture parts follow the same pattern. The first `n` image relationships are `rId10` and up, one per picture, and each `p:pic` carries its own crop in `a:srcRect` rather than rewriting the file. The relationship id order is the order the pictures appear in the spec, so an edit that removes the first picture renumbers the rest.

Full coverage of the schema and the effects is in `motion.md`.

## Run Splitting, the Reason a Text Edit Misses

Word processing stores a paragraph as one or more runs, and a run is a span with one set of formatting. `카드 인증 단계 실패 47%` may be stored as three runs when part of it was bolded, pasted, or spell-checked. A search for the whole phrase then finds nothing even though a reader sees it.

`edit-deck.sh` therefore reports a miss instead of guessing. The honest options when a miss occurs:

1. Search a shorter string that lies inside one run, and repeat.
2. Replace the whole paragraph by rewriting the slide in a fresh spec, when there are many edits.
3. Open the deck in PowerPoint and split the replacement into multiple `--replace` calls.

Do not join runs to force a match: merging changes formatting and loses the reason the runs were split.

## What This Package Deliberately Does Not Do

- No template inheritance, no placeholder reuse, no theme switching of an existing deck.
- No font embedding; a requested font must exist on the reader's machine.
- No SmartArt. Transitions and element animations are written, but only from a closed list of names and effects whose XML was compared against the schema; playback is still unverified, and `motion.md` says so.
- No motion paths, per-character builds, or slide-master animation.
- No picture generation: a placeholder image in the examples is a flat geometric stand-in, not a photograph.
- No `.pptx` rendering through a third-party engine; the preview is our own renderer, and it is checked against the file's structure, not the reverse.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| OPC package structure and `[Content_Types].xml` role | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| Slide, notes, and relationship parts | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |
| Chart parts carry cached categories and values | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| DrawingML run structure and why text splits into runs | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.text> |
| EMU and point conversions | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |

### Evidence grade

`LOCAL` — every row of the removal table was measured on 2026-11-13 by deleting exactly one part from a rendered deck and reopening it with python-pptx. The repair-prompt rows are inferred from the OOXML specification, because PowerPoint is not available on this machine.
