# PPTX Internals

Read this when a deck must open without a repair prompt, when an edit must not disturb a template, or when someone asks why this package writes OOXML by hand instead of calling a library.

## Contents

- The package is a zip of parts
- The six parts every slide needs
- Why one blank layout and absolute geometry
- What makes PowerPoint offer to repair a file
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

`render-deck.sh` checks well-formedness of every XML part and every relationship target on disk, and exits 1 rather than delivering a package with a dangling reference. It cannot check the repair prompt itself, because PowerPoint is not available on this machine; that row is specification-based, not observed.

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
- No animation, transition, or SmartArt. Writing them is possible but unverifiable without PowerPoint, and delivering unverified XML is worse than omitting it.
- No image generation. An `image` slide takes an existing file path.
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
