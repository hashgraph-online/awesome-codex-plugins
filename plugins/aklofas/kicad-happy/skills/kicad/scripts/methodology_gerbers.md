# Gerber & Drill File Analyzer — Methodology

This document describes the analysis methodology used by `analyze_gerbers.py`. It covers Gerber RS-274X parsing, Excellon drill parsing, layer identification, X2 attribute extraction, and all higher-level analyses performed on a fabrication output directory.

## Design Philosophy

Same as the schematic and PCB analyzers — this is a **data extraction layer**. It outputs structured JSON containing neutral observations about the fabrication files. An LLM (or human reviewer) consumes this alongside the schematic and PCB layout analyses for design review.

The Gerber analyzer is the last line of defense before a board order — the fabrication files are what the manufacturer actually builds. Thorough detection matters: a missing layer, stale zip archive, or misaligned coordinate range that goes unreported can result in costly respins. Every reported fact (layer identification, drill classification, coordinate extents) must be accurate, since the reviewer is making go/no-go ordering decisions based on this data.

The analyzer operates on manufactured output files, not source design files. It answers the question "what did the CAD tool actually produce?" rather than "what did the designer intend?" This makes it useful for:
- Verifying that exported Gerbers match the design (cross-reference with PCB analysis)
- Checking fabrication file completeness before ordering
- Extracting board specs and design rules from machine-readable metadata
- Identifying layer alignment issues that would cause manufacturing defects

---

## 1. Input Discovery

### File Collection

`analyze_gerbers()` scans the target directory for three file categories:

| Category | Extensions | Purpose |
|---|---|---|
| Gerber files | `.gbr`, `.g*` (including Protel: `.gtl`, `.gbl`, `.gts`, `.gbs`, `.gto`, `.gbo`, `.gko`, `.gm1`, `.g1`–`.g4`) | Copper, mask, paste, silk, edge layers |
| Drill files | `.drl` | Excellon hole data (PTH and NPTH) |
| Job files | `.gbrjob` | KiCad-generated JSON metadata |
| Zip archives | `.zip` | Packaged Gerber sets (scanned for staleness, not extracted) |

Both lowercase and uppercase extensions are collected. Duplicates are removed, and non-Gerber files (`.drl`, `.gbrjob`, `.zip`, `.pos`) are filtered from the Gerber list.

### Processing Order

1. Parse all Gerber files → `gerbers[]`
2. Parse all drill files → `drills[]`
3. Parse job file (first `.gbrjob` found, if any) → `job_info`
4. Run analysis functions over the parsed data

Individual file parse errors are caught and recorded as `{"error": "..."}` entries — a corrupt file doesn't abort the entire analysis.

---

## 2. Gerber RS-274X Parsing

`parse_gerber()` performs a single stateful pass over each Gerber file, extracting format information, aperture definitions, X2 attributes, operation counts, and coordinate ranges.

### 2.1 Format and Units

Extracted via regex from the file content:

- **Format specification** (`%FS...%`): Zero omission mode (leading/trailing), coordinate notation (absolute/incremental), and integer/decimal digit counts for X and Y axes. These are needed to interpret raw coordinate integers.
- **Units** (`%MOIN*%` or `%MOMM*%`): Inch or millimeter. Determines whether aperture dimensions need conversion.

### 2.2 Two-Phase Architecture

**Phase 1** (regex over full content): Extracts format, units, and X2 file attributes (`%TF.*%` and `G04 #@! TF.*` comment format). These are needed before the line-by-line pass can interpret coordinates.

**Phase 2** (stateful line-by-line): Tracks aperture state, object attributes, and operations:

| State Machine | Tracked By | Purpose |
|---|---|---|
| Aperture attributes | `pending_aper_function` | TA.AperFunction preceding AD definition |
| Current component | `current_component` | TO.C object attribute (non-pad objects; pads carry their ref in TO.P) |
| Current net | `current_net` | TO.N object attribute |
| Component pad counts | `component_pads{}` | Flash count per component ref |
| Component net sets | `component_nets{}` | Which nets each component connects to |
| Pin mappings | `pin_mappings[]` | TO.P ref/pin/pin_name/net tuples |

### 2.3 X2 File Attributes

Two formats are supported:

- **Native X2** (KiCad 5.1+ with X2 output on): `%TF.Key,Value*%` — standard X2 extended attributes
- **Comment format** (X2 output off, and older KiCad 5): `G04 #@! TF.Key,Value*` — same data embedded in G-code comments

The comment format is checked second, so modern attributes take precedence if both exist.

Common file attributes extracted:
- `FileFunction` — layer type (Copper, SolderMask, Legend, Profile, etc.)
- `FilePolarity` — Positive or Negative
- `GenerationSoftware` — CAD tool identification
- `CreationDate` — when the file was generated

### 2.4 X2 Object Attributes

Object attributes (`TO.*`) track which component, net, and pin are associated with subsequent operations:

- **`TO.C,RefDes`** — sets the current component reference (e.g., `TO.C,R1`)
- **`TO.N,NetName`** — sets the current net name
- **`TO.P,Ref,Pin[,PinName]`** — records a pin-to-net mapping

These are accumulated across all flashes and draws. When a flash (D03) occurs while `current_component` is set, the pad count for that component increments. This builds a component-level view of which pads exist on each layer.

### 2.5 Aperture Definitions

Each `%AD...%` definition is parsed for:
- **D-code**: The aperture identifier (D10, D11, ...)
- **Type**: C (circle), R (rectangle), O (obround), RoundRect (macro), or custom
- **Parameters**: Dimensions in file units
- **Function**: If a `TA.AperFunction` preceded the definition, it's attached (e.g., `Conductor`, `SMDPad,CuDef`, `ViaPad`, `HeatsinkPad`)

### 2.6 Aperture Dimension Parsing

`_parse_aperture_dimension()` extracts the primary dimension (in mm) from standard aperture types:

| Aperture Type | Dimension Extracted |
|---|---|
| C (circle) | Diameter |
| R (rectangle) | Smaller of width/height |
| O (obround) | Smaller of width/height |
| RoundRect | 2× corner radius (conservative estimate) |

Inch dimensions are converted to mm. These are used for trace width distribution and minimum feature size analysis.

### 2.7 Operation Counting

Three operation types are counted:
- **Flashes** (D03): Pad/via placements — counted globally and per component
- **Draws** (D01): Trace segments, arcs
- **Regions** (G36): Copper fills/pours

### 2.8 Coordinate Range

Only points where copper is put update a running min/max bounding box: a D01 draw's start and end, a D03 flash, and the axis extremes an arc sweeps. D02 moves are skipped. Coordinates are modal X/Y, with or without a leading `G01`/`G02`/`G03`, and the box is kept in millimetres: coordinates are divided by the format's decimal precision and inch files (`%MOIN*%`) are multiplied by 25.4. An arc under `G75` is swept from start to end, and an arc whose start equals its end is a full circle. The box is used later for layer alignment checking and board dimension estimation.

### 2.9 Aperture Analysis Summary

After the line-by-line pass, aperture data is aggregated:
- **By function**: Count of apertures per function category (SMDPad, ViaPad, Conductor, HeatsinkPad, etc.)
- **Conductor widths**: Set of unique trace widths (mm) from Conductor-tagged apertures
- **Minimum feature**: Smallest aperture dimension across all types

---

## 3. Excellon Drill Parsing

`parse_drill()` parses Excellon drill files in a single pass.

### 3.1 Header Parsing

The header (before the `%` end-of-header marker) contains:
- **Units**: Detected from `METRIC`/`MOMM` or `INCH` keywords
- **Tool definitions**: `TnnCddd.ddd` — tool number and diameter. Diameters in inches are converted to mm.
- **X2 attributes**: Same `; #@! TF.*` comment format as Gerber files
- **Per-tool aperture functions**: `; #@! TA.AperFunction,Plated,PTH,ViaDrill` etc. — attached to the next tool definition

### 3.2 Drill Hits

After the header, tool selections (`Tnn`) and coordinate lines (`Xnnn.nnnYnnn.nnn`) are tracked. Each coordinate line increments the hole count for the current tool and updates the coordinate bounding box.

### 3.3 PTH/NPTH Classification

Each drill file is classified as PTH (plated through-hole) or NPTH (non-plated) using:
1. **X2 FileFunction attribute** — `Plated` or `NonPlated` (authoritative)
2. **Filename pattern** — `pth`/`npth` in the filename (fallback)
3. **Unknown** — if neither source provides classification

### 3.4 Layer Span

From `FileFunction` values like `Plated,1,4,PTH`, the layer span is extracted (e.g., layers 1–4). This indicates which copper layers the drill connects and is used to determine total layer count.

---

## 4. Layer Identification

`identify_layer_type()` maps each Gerber file to a KiCad-style layer name. Three identification methods are tried in priority order:

### 4.1 X2 FileFunction (Highest Priority)

The `FileFunction` attribute provides authoritative layer identification:

| FileFunction Contains | Mapped Layer |
|---|---|
| `copper` + `top` | F.Cu |
| `copper` + `bot` | B.Cu |
| `copper,Ln,inr` | In(n-1).Cu (L2→In1, L3→In2, etc.) |
| `soldermask` + `top`/`bot` | F.Mask / B.Mask |
| `paste`/`solderpaste` + `top`/`bot` | F.Paste / B.Paste |
| `legend`/`silkscreen` + `top`/`bot` | F.SilkS / B.SilkS |
| `profile` | Edge.Cuts |

Inner copper layer mapping: X2 uses absolute layer positions (L2 = second copper layer), while KiCad names inner layers starting at In1.Cu. The conversion is `In(L-1).Cu`.

### 4.2 KiCad Filename Patterns (Second Priority)

If no X2 attributes are present, the filename is checked against KiCad-style patterns:
- Inner copper: `In1_Cu`, `In1.Cu`, etc.
- Outer layers: `F_Cu`, `F.Cu`, `Front_Cu`, `B_Cu`, etc.
- Masks/paste/silk/edge: Similar patterns with layer prefixes

### 4.3 Protel-Style Extensions (Lowest Priority)

Classic Protel/Altium extensions as a final fallback:

| Extension | Layer |
|---|---|
| `.gtl` / `.gbl` | F.Cu / B.Cu |
| `.gts` / `.gbs` | F.Mask / B.Mask |
| `.gtp` / `.gbp` | F.Paste / B.Paste |
| `.gto` / `.gbo` | F.SilkS / B.SilkS |
| `.gm1` / `.gko` | Edge.Cuts |
| `.g1`–`.g4` | In1.Cu–In4.Cu |

Files that match none of these patterns get `"unknown"` and are still included in the output.

---

## 5. Job File Parsing

`parse_job_file()` parses the `.gbrjob` file (JSON format, generated by KiCad alongside Gerbers).

### Extracted Fields

| JSON Path | Output Field | Purpose |
|---|---|---|
| `Header.GenerationSoftware` | `generator`, `vendor` | CAD tool identification |
| `Header.CreationDate` | `creation_date` | Timestamp |
| `GeneralSpecs.Size` | `board_width_mm`, `board_height_mm` | Authoritative board dimensions |
| `GeneralSpecs.LayerNumber` | `layer_count` | Total copper layers |
| `GeneralSpecs.BoardThickness` | `board_thickness_mm` | Stackup thickness |
| `GeneralSpecs.Finish` | `finish` | Surface finish (HASL, ENIG, etc.) |
| `GeneralSpecs.ProjectId` | `project_name` | KiCad project name |
| `DesignRules[]` | `design_rules[]` | Pad-to-pad, track-to-track, min width, etc. |
| `FilesAttributes[]` | `expected_files[]` | What files should exist (for completeness check) |
| `MaterialStackup[]` | `stackup[]` | Layer types, thicknesses, materials |

---

## 6. Analysis Functions

### 6.1 Drill Classification

`classify_drill_tools()` categorizes every drill tool across all drill files into three groups:

**Classification priority:**
1. **NPTH file** → all tools classified as mounting holes (regardless of diameter)
2. **X2 AperFunction** — `ViaDrill` → via, `ComponentDrill` → component hole
3. **Diameter heuristic** (fallback when no X2 data):

| Diameter Range | Classification | Rationale |
|---|---|---|
| ≤ 0.45 mm | Via | Standard via drill sizes |
| 0.45–1.3 mm | Component hole | THT component pin sizes |
| > 1.3 mm | Mounting hole | Screws, standoffs |

The output records which method was used (`x2_attributes` or `diameter_heuristic`), so the consumer knows confidence level.

### 6.2 Layer Completeness

`check_completeness()` verifies that all necessary layers are present.

**With `.gbrjob`:** Compares found layers against the `expected_files` list from the job file. Reports missing and extra layers. Source is tagged as `"gbrjob"`.

**Without `.gbrjob`:** Checks against a default required set:
- **Required**: F.Cu, B.Cu, F.Mask, B.Mask, Edge.Cuts, plus any inner copper layers found
- **Recommended**: F.SilkS, F.Paste
- **Drill**: At least one PTH drill file

A board is `"complete": true` only when all required layers are present and a PTH drill exists.

### 6.3 Layer Alignment

`check_alignment()` checks that every copper layer lies inside the board outline.

**Method:**
1. Record the width and height (mm) of the coordinate bounding box of each identified layer and drill file in `layer_extents`
2. Take the Edge.Cuts bounding box (the union when there are several outline files); with no Edge.Cuts there is nothing to check
3. Flag each copper layer (F.Cu, B.Cu, inner copper) whose box extends past the outline box by more than **max(2 mm, 5 % of that side)**: `"<layer> extends <d>mm outside the board outline"` (GR-002)

Layers of one export are registered by construction and need not have the same size: copper rarely reaches the board edge. Copper outside the board profile is what a fab rejects (KiCad DRC `copper_edge_clearance`). A pure shift smaller than the tolerance is not reported. Drill file extents are recorded but not compared: drill files from other tools often use another origin or unit.

### 6.4 Board Dimensions

`compute_board_dimensions()` determines board width, height, and area.

**Priority:**
1. **`.gbrjob`** — `GeneralSpecs.Size.X` and `.Y` (authoritative, computed by KiCad)
2. **Edge.Cuts extents** — bounding box of the board outline Gerber file (fallback)

The source is tagged in the output so the consumer knows which method was used. The Edge.Cuts fallback gives bounding-box dimensions, which are correct for rectangular boards but overestimate for boards with cutouts or non-rectangular outlines.

### 6.5 Component Analysis

`build_component_analysis()` merges X2 object attribute data across all Gerber layers to build a board-level view of components.

**Only produces output when X2 TO attributes are present** (KiCad 5.1+ exports). Without X2 data, no component analysis is possible from Gerbers alone.

**Merging logic:**
- Component references are collected from all layers: `TO.C` refs plus the `TO.P` refs that KiCad writes on pads
- Front/back side assignment: refs (`TO.C`) on F.Cu/F.Mask/F.SilkS/F.Paste are front-side and on the B.* layers back-side. A copper pad's `TO.P` ref names a side only when the part has copper on one side alone (through-hole pads appear on both). Components appearing only on the back are counted as back-only.
- Pad counts: maximum pad count per component across all layers (same pad appears on copper, mask, and paste layers)
- Nets per component: union of all nets associated with each component across layers

**Net classification** uses keyword matching:
- **Power nets**: Names matching `vcc`, `vdd`, `gnd`, `agnd`, `vss`, `vbat`, `vbus`, `vin`, or starting with `+`/`-`
- **Unnamed nets**: Starting with `Net-(` or `unconnected-(`
- **Signal nets**: Everything else

### 6.6 Net Analysis

`build_net_analysis()` merges net and pin data from copper layers only (mask/paste/silk layers don't carry meaningful net data).

Output includes:
- Total unique nets, named vs unnamed count
- Power and signal net lists (same classification as component analysis)
- Total pin-to-net mappings (deduplicated across layers)

### 6.7 Trace Width Analysis

`build_trace_analysis()` aggregates conductor aperture data from copper layers:
- **Unique widths**: Set of all trace widths used (from Conductor-tagged apertures)
- **Min/max trace**: Smallest and largest trace widths
- **Minimum feature**: Smallest aperture dimension of any type on copper layers

### 6.8 Pad Summary

`build_pad_summary()` counts pad types by aperture function across copper layers:

| Counter | Source |
|---|---|
| SMD apertures | `SMDPad` function on copper layers |
| Via apertures | `ViaPad` function on copper layers |
| Heatsink apertures | `HeatsinkPad` function on copper layers |
| THT holes | Component hole count from drill classification |

When both SMD and THT counts are available, an `smd_ratio` is computed (0.0 = all THT, 1.0 = all SMD).

### 6.9 Zip Archive Scanning

`scan_zip_archives()` detects `.zip` files in the Gerber directory and reports metadata to help identify stale archives or stale loose files. Gerber directories commonly contain zip archives — manufacturers require zipped uploads, and designers often snapshot Gerbers at different design stages.

**Per-archive data:**
- Filename, file size, filesystem modification time
- Total files inside, broken down by gerber/drill/other
- Newest member date (from the zip directory entries, not filesystem mtime)
- Comparison against loose Gerber files: `loose_files_newer`, `archive_newer`, or `same_age`
- Time delta in hours when ages differ (threshold: 60 seconds to ignore trivial filesystem jitter)

**Comparison logic:** The newest internal member date is preferred over the zip's filesystem mtime for comparison, since filesystem mtime can change from a copy/move without reflecting the actual export time. The loose file side uses the latest filesystem mtime across all gerber and drill files.

The analyzer does not extract or parse files from inside zip archives — it only inspects the zip directory. This is intentional: the loose files are what gets analyzed, and the zip scan exists to flag when those loose files may not match what was (or will be) uploaded to the manufacturer.

Only present in output when zip files exist in the directory.

---

## 7. Layer Count Determination

The total copper layer count is determined from the maximum of three sources:
1. **Parsed Gerber files**: Count of files identified as copper layers (`*.Cu`)
2. **Job file**: `GeneralSpecs.LayerNumber` from `.gbrjob`
3. **Drill layer span**: Maximum layer number from drill file `FileFunction` (e.g., `Plated,1,4` → 4 layers)

This handles cases where inner layer Gerbers might be missing or misidentified — the drill span and job file still report the correct count.

---

## 8. Output Structure

### Top-Level Keys

| Key | Type | Description |
|---|---|---|
| `directory` | string | Input directory path |
| `generator` | string\|null | CAD tool that produced the files |
| `layer_count` | int | Total copper layers |
| `board_dimensions` | object | Width, height, area, source |
| `statistics` | object | File counts, total holes/flashes/draws |
| `completeness` | object | Missing/extra layers, complete flag |
| `alignment` | object | Aligned flag, issues, per-layer extents |
| `drill_classification` | object | Vias/component/mounting holes with tools |
| `pad_summary` | object | SMD/via/heatsink/THT aperture counts |
| `trace_widths` | object | Width distribution, min feature (if available) |
| `component_analysis` | object | Component refs, front/back counts (X2 only) |
| `net_analysis` | object | Net counts, power/signal lists (X2 only) |
| `gerbers` | array | Per-file summary (compact) |
| `drills` | array | Per-file summary with tool details |
| `drill_tools` | object | Aggregated drill sizes and counts |
| `job_file` | object | Full `.gbrjob` metadata (if present) |
| `zip_archives` | array | Zip files with contents summary and staleness comparison (if present) |
| `connectivity` | array | Pin-to-net mappings (`--full` mode only) |

### Per-Gerber Summary

Each entry in the `gerbers` array contains:
- Filename, identified layer type, units
- Aperture count, flash/draw/region counts
- X2 file attributes (if present)
- Aperture analysis (function counts, conductor widths, min feature)
- X2 component/net/pin counts per layer (if present)

### Per-Drill Summary

Each entry in the `drills` array contains:
- Filename, PTH/NPTH type, units
- Total hole count
- Tool definitions with diameters and per-tool hole counts
- Layer span (if available from X2)
- X2 attributes

### Output Modes

- **Default**: Compact per-file summaries with board-level analysis
- **`--full`**: Adds raw pin-to-net connectivity data (every TO.P mapping)
- **`--compact`**: Minified JSON (no indentation)

---

## 9. Known Limitations

### Format Coverage

- **RS-274X only**: Does not parse legacy RS-274D (no embedded aperture definitions). RS-274D requires external aperture files — virtually all modern CAD tools export RS-274X.
- **Aperture macros**: Custom macro apertures (AM commands) beyond RoundRect are not dimension-parsed. They are still recorded as aperture definitions, but their dimensions don't contribute to trace width or min feature analysis.
- **Step-and-repeat**: SR commands (array replication) are not interpreted. The coordinate range will reflect the base pattern, not the replicated extent.
- **Block apertures**: AB (aperture block) commands are not interpreted.

### Coordinate Interpretation

- **Incremental mode**: The parser assumes absolute notation. Files using incremental coordinates (rare in modern output) will produce incorrect coordinate ranges.
- **Bounding box only**: Coordinate ranges are axis-aligned bounding boxes, not actual board geometry. Non-rectangular boards and cutouts are not detected.

### X2 Attribute Dependency

- Component analysis, net analysis and pin connectivity require X2 object attributes (`TO.C`, `TO.N`, `TO.P`), either native (`%TO…*%`) or as `G04 #@! TO…` comments (X2 output off). KiCad 5.1 and later write them; for pads KiCad writes `TO.P` and `TO.N` and no `TO.C`. Gerbers without object attributes (older KiCad, some other tools) get layer identification and statistics but no component or net data.

### Drill Interpretation

- **Routing commands**: a routed slot (`G00` move, `M15` plunge, cut, `M16` retract) counts as one hole of its tool at the plunge point; its length is not measured. A `G85` slot is not interpreted: it counts as one hole at its first point.
- **Multiple drill files**: Some exports split PTH and NPTH into separate files, others combine them. The analyzer handles both — it parses all `.drl` files and merges results. But if a combined file has no X2 attributes and no filename hint, it defaults to `"unknown"` type.

### Cross-Layer Analysis

- The analyzer does not perform geometric cross-referencing between layers (e.g., checking that a drill hole aligns with pads on copper layers, or that solder mask openings match pad sizes). These checks require spatial correlation that the Gerber format does not natively support without full coordinate parsing and matching.

---

## 10. Verification

The analyzer can be verified by:
1. **Round-trip comparison**: Run on Gerbers exported from a KiCad project, then compare component/net counts against the schematic and PCB analyses of the same project
2. **Job file cross-check**: Board dimensions and layer count from the analyzer should match `.gbrjob` values
3. **Completeness**: The completeness check itself verifies that the expected file list from `.gbrjob` matches what was found on disk
4. **Alignment**: Running on known-good Gerber sets should always report `"aligned": true`
