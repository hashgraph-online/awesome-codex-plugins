# KiCad Analysis Scripts — Developer Reference

This directory contains the core analysis scripts, shared utilities, the S-expression parser, and the rich-finding/trust-summary infrastructure. Each analyzer outputs a structured JSON envelope for the AI agent to consume during design reviews.

| Script | Input | Size | Purpose |
|--------|-------|------|---------|
| `analyze_schematic.py` | `.kicad_sch` / `.sch` | ~9,300 LOC | Component extraction, net building, subcircuit detection, signal/power/BOM/DFM analysis, audit detectors |
| `analyze_pcb.py` | `.kicad_pcb` | ~6,600 LOC | Footprint inventory, routing, signal integrity, power, thermal, placement, manufacturing, DFM, union-find connectivity graph, assembly/DFM checks |
| `analyze_gerbers.py` | Gerber dir (`.gbr`/`.drl`) | ~1,400 LOC | Layer completeness, drill holes, apertures, coordinate alignment, X2 attributes |
| `analyze_thermal.py` | schematic + PCB JSON | ~910 LOC | Junction-temperature estimator with package θJA, thermal via correction, proximity warnings |
| `cross_analysis.py` | schematic + PCB JSON | ~430 LOC | Cross-domain checks: CC-001 connector current, EG-001 ESD gaps, DA-001 decoupling adequacy, XV-001..003, PCB intelligence (NR/RP/TW/PS/VS/DP-005) |
| `lifecycle_audit.py` | schematic JSON + distributor API | ~855 LOC | Component obsolescence, temperature audit (LC-001..006, LT-001) |
| `sexp_parser.py` | — | ~220 LOC | S-expression parser shared by schematic and PCB analyzers |
| `kicad_utils.py` | — | ~860 LOC | Shared utilities: component classification, value parsing, net detection, switching-frequency table, Vref lookup |
| `kicad_types.py` | — | ~110 LOC | Typed dataclass (`AnalysisContext`) shared across detectors |
| `signal_detectors.py` | — | ~4,400 LOC | Core signal path detectors (regulators, filters, opamps, dividers, crystals, transistors, bridges, protection), plus v1.3 audit detectors (RS-001, LB-001, PP-001) |
| `domain_detectors.py` | — | ~6,100 LOC | Domain-specific detectors (RF, Ethernet, HDMI, memory, BMS, battery chargers, motor drivers, wireless modules, etc.) |
| `validation_detectors.py` | — | ~1,000 LOC | Validation detectors (PU-001, VM-001, PR-001..004, PS-001, LR-001, FS-001) |
| `finding_schema.py` | — | ~330 LOC | `make_finding()` factory, `Det.*` constants, `get_findings()` / `group_findings()` helpers, `trust_summary` aggregation, `sort_findings()` determinism |
| `output_filters.py` | — | ~460 LOC | Stage/audience filtering (`--stage schematic/layout/pre_fab/bring_up`, `--audience designer/reviewer/manager`) |
| `pcb_connectivity.py` | — | ~300 LOC | Union-find over pads/tracks/vias/zone fills for per-net island detection (used by `analyze_pcb.py --full`) |
| `project_config.py` | — | ~870 LOC | `.kicad-happy.json` loader, suppression matching, design intent resolution |
| `analysis_cache.py` | — | ~510 LOC | Analysis-folder convention, manifest-based run tracking, SHA-256 staleness detection |
| `diff_analysis.py` | two analyzer JSONs | ~950 LOC | Diff-aware design comparison (component/signal/EMC/SPICE) |
| `what_if.py` | analyzer JSON + patch spec | ~1,500 LOC | Parameter sweep + automated fix suggestions (inverse solvers with E-series snapping) |
| `summarize_findings.py` | analysis/manifest.json | ~200 LOC | Cross-run severity × count rollup |

Detailed methodology documentation for each analyzer:
- `methodology_schematic.md` — parsing pipeline, net building, component classification, detector inventory
- `methodology_pcb.md` — extraction, union-find connectivity, DFM scoring, thermal/placement/SI analysis, assembly/DFM checks
- `methodology_gerbers.md` — RS-274X/Excellon parsing, X2 attributes, layer identification, completeness/alignment checks

---

## sexp_parser.py

Parses KiCad's Lisp-like S-expression format into nested Python lists. Used by both `analyze_schematic.py` and `analyze_pcb.py`.

### API

| Function | Purpose |
|----------|---------|
| `parse_file(path)` | Parse a `.kicad_sch` or `.kicad_pcb` file → nested lists |
| `find_all(node, keyword)` | Find direct children starting with keyword |
| `find_first(node, keyword)` | Find first direct child starting with keyword |
| `find_deep(node, keyword)` | Recursive search at any depth |
| `get_value(node, keyword)` | Get value from `(keyword value)` pair |
| `get_property(node, prop_name)` | Get value from `(property "name" "value")` |
| `get_at(node)` | Get `(x, y, angle)` from `(at ...)` node |
| `get_xy(node)` | Get `(x, y)` from `(xy ...)` node |

**Design note**: The parser is intentionally simple — no schema validation, no type coercion beyond strings. All values come back as strings; callers convert to `float`/`int` as needed. This makes it robust against KiCad version differences.

**Pitfall**: `find_all` and `find_first` only search direct children. For nested structures, use `find_deep` — but be aware it can return matches from unrelated subtrees.

---

## analyze_pcb.py

Parses `.kicad_pcb` files (KiCad 5 `module` and KiCad 6+ `footprint` formats).

### Pipeline

```
.kicad_pcb file
    |
    v
 EXTRACTION (core data)
extract_layers()            -- Layer stack definitions (incl. jumper layers)
extract_setup()             -- Thickness, stackup, copper finish, paste ratio, teardrops
extract_nets()              -- Net number → name mapping
extract_footprints()        -- Footprints with pads, courtyards, attrs, sch cross-ref
extract_tracks()            -- Track segments and arcs with width/layer stats
extract_vias()              -- Vias with type, free flag, tenting
extract_zones()             -- Zones with fill areas, keepouts, priority, pad connection
extract_board_outline()     -- Edge.Cuts geometry, bounding box
extract_board_metadata()    -- Title block, properties, paper size
extract_dimensions()        -- Designer-placed dimension annotations
extract_groups()            -- Designer-defined component/routing groups
extract_net_classes()       -- Net class definitions (KiCad 5 legacy)
extract_silkscreen()        -- Board-level text on SilkS/Fab layers
    |
    v
 ANALYSIS (derived facts)
analyze_connectivity()      -- Unrouted nets (zone-aware)
analyze_net_lengths()       -- Per-net trace length (segments + arcs)
analyze_power_nets()        -- Power net routing summary
analyze_decoupling_placement() -- Cap-to-IC distance
analyze_ground_domains()    -- AGND/DGND split detection
analyze_current_capacity()  -- Track widths per net for IPC-2221
analyze_vias()              -- Type breakdown, annular ring, via-in-pad, fanout, current
analyze_thermal_vias()      -- Zone stitching density, thermal pad detection
analyze_layer_transitions() -- Signal net layer changes (ground return paths)
analyze_placement()         -- Courtyard overlaps, edge clearance, density
analyze_trace_proximity()   -- Spatial grid crosstalk assessment (optional)
compute_statistics()        -- Summary counts
    |
    v
JSON output (~50-300KB depending on board complexity)
```

### Key Design Decisions

- **Pad positions are absolute**: Pad `(at)` is relative to footprint; the code rotates by footprint angle and adds footprint position to compute absolute coordinates.
- **Footprint summary omits raw pads by default**: The JSON output includes `connected_nets` per footprint instead of full pad arrays. Use `--full` for individual track/via data.
- **Zone fill areas computed without storing coordinates**: Shoelace formula applied directly to parsed S-expression nodes — the parse tree is already in memory, we just iterate and accumulate. Avoids the massive memory cost of storing filled polygon coordinate arrays.
- **Keepout zones distinguished from copper zones**: Zones with `(keepout ...)` blocks are flagged with `is_keepout: true` and their restriction types (tracks, vias, pads, copperpour, footprints).
- **Extended footprint attributes**: Parses full `(attr ...)` node including `dnp`, `board_only`, `exclude_from_bom`, `exclude_from_pos_files`. Also extracts schematic cross-reference (`path`, `sheetname`, `sheetfile`), net ties, 3D model references, and manufacturer/MPN properties.
- **Custom pad copper area**: Pads with `custom` shape have their `(primitives (gr_poly ...))` areas computed via shoelace, giving accurate copper area for power MOSFET pads.
- **Free vias identified**: Vias with `(free yes)` are flagged — typically stitching or thermal vias not anchored to tracks.
- **Pin function/type carried from schematic**: Pad-level `pinfunction` and `pintype` enable power-pin vs signal-pin differentiation without needing the schematic.
- **KiCad 5 compatibility**: Handles `(module ...)`, `(fp_text reference ...)`, `(net_class ...)`, and `(dimension ...)` in addition to KiCad 6+ equivalents.
- **Unrouted detection**: Zone-aware — nets routed only through copper pours are not flagged as unrouted.
- **Facts over judgement**: Analysis functions provide raw facts (track widths, via counts, distances) rather than pass/fail verdicts, enabling flexible higher-level analysis.

### Usage

```bash
python3 analyze_pcb.py board.kicad_pcb                    # JSON to stdout
python3 analyze_pcb.py board.kicad_pcb --output out.json  # JSON to file
python3 analyze_pcb.py board.kicad_pcb --compact          # Minified JSON
python3 analyze_pcb.py board.kicad_pcb --full              # Include individual tracks/vias
python3 analyze_pcb.py board.kicad_pcb --proximity        # Add crosstalk proximity analysis
```

---

## analyze_gerbers.py

Parses a directory of Gerber RS-274X files and Excellon drill files. Does NOT render the gerbers — it extracts metadata, counts, and performs sanity checks.

### Pipeline

```
gerber directory
    |
    v
parse_gerber()          -- Per-file: apertures, X2 attributes, flash/draw counts, coord range
parse_drill()           -- Per-file: tool definitions, hole counts, coord range, PTH/NPTH type
scan_zip_archives()     -- Zip contents inventory + timestamp comparison vs loose files
    |
    v
identify_layer_type()   -- Map filename/X2 attributes to KiCad layer names (F.Cu, B.Mask, etc.)
check_completeness()    -- Verify required layers present (F.Cu, B.Cu, F.Mask, B.Mask, Edge.Cuts)
check_alignment()       -- Compare coordinate extents across copper/edge layers
    |
    v
JSON output
```

### Layer Identification

Uses two strategies, in order:
1. **X2 attributes**: `%TF.FileFunction,...*%` headers (modern gerbers from KiCad 6+)
2. **Filename patterns**: Maps common suffixes/extensions to layers (e.g., `.gtl` → F.Cu, `.gbl` → B.Cu, `F_Cu.gbr` → F.Cu)

**Pitfall**: The filename patterns dictionary is case-insensitive substring matching. Non-standard naming (e.g., a file called `top_copper.ger`) won't be identified. Add patterns to the `patterns` dict in `identify_layer_type()` as needed.

### Alignment Check

Compares bounding box extents across copper and edge layers. Only checks F.Cu, B.Cu, and Edge.Cuts — paste, silk, mask, and drill layers naturally have smaller extents. A >2mm difference flags an alignment issue.

### Drill File Parsing

- Handles both metric and inch formats (auto-detects from `METRIC`/`INCH` keywords)
- Inch values are converted to mm internally
- PTH vs NPTH is determined from filename (`-PTH.drl` vs `-NPTH.drl`)
- Individual hole coordinates are parsed for coordinate range but not included in output (too verbose)

### Usage

```bash
python3 analyze_gerbers.py ./gerbers/                    # JSON to stdout
python3 analyze_gerbers.py ./gerbers/ --output out.json  # JSON to file
python3 analyze_gerbers.py ./gerbers/ --compact          # Minified JSON
```

---

## analyze_schematic.py

The largest and most complex script. The rest of this document focuses on its architecture and pitfalls.

### Pipeline

```
.kicad_sch file(s)
    |
    v
parse_single_sheet()          -- S-expression parsing, component/wire/label extraction
    |
    v
analyze_schematic()           -- Multi-sheet orchestration, instance remapping
    |  Builds: all_components, all_wires, all_labels, all_junctions
    |
    v
build_net_map()               -- Union-find net building (sheet-aware coordinates)
    |  Produces: nets dict {name -> {pins, labels, ...}}
    |
    v
analyze_signal_paths()        -- Subcircuit detection (VD, RC, regulators, bridges, etc.)
analyze_design_rules()        -- Bus detection, diff pairs, power domains, ERC
analyze_ic_pinouts()          -- Per-IC pin connectivity summary
compute_statistics()          -- Counts, BOM dedup
    |
    v
Output harmonization           -- All detections → flat findings[] with rich envelopes
                                  (detector, rule_id, severity, confidence, recommendation)
                                  rail_voltages/net_classifications promoted to top level
    |
    v
JSON output                    -- {analyzer_type, summary, findings[], components, nets, ...}
```

### Key Data Structures

- **`nets`**: `{net_name: {"pins": [{component, pin_number, pin_name, pin_type, x, y}], ...}}`
- **`pin_net`**: `{(reference, pin_number): (net_name, pin_type)}` — reverse lookup from `build_pin_to_net_map()`
- **`comp_lookup`**: `{reference: component_dict}` — built locally in analysis functions
- **`parsed_values`**: `{reference: float}` — numeric values for passive components

## File Format Support

### Modern `.kicad_sch` (KiCad 6+)
Full support. S-expression format parsed by `sexp_parser.py`.

### Legacy `.sch` (KiCad 4/5)
Line-based format. Components, wires, labels, power symbols parsed. `.lib` symbol libraries are parsed for pin definitions (`parse_legacy_lib()`), enabling pin-to-net mapping via geometric snapping. Library resolution searches cache-lib, sym-lib-table, LIBS: directives, and built-in defaults. Pin geometry uses a snapping radius (up to 12mm) when parsed symbols are incomplete — results are heuristic and carry reduced confidence compared to KiCad 6+ native pin data.

### Eagle `.sch`
Not supported (binary and XML formats). Returns 0 components gracefully.

## Critical Concepts

### Sheet-Aware Coordinate Keys

**Problem**: Different hierarchical sheets can have wires at identical coordinates. Without sheet separation, the union-find merges nets across sheets (e.g., +3V3 and +5V merge because wires at (100,50) exist on both sheets).

**Solution**: Every element (component, wire, label, junction) is tagged with `_sheet` index. All coordinate-based keys in `build_net_map()` include the sheet index: `(x, y, sheet)` not `(x, y)`.

**Pitfall**: If you add new coordinate-based lookups, always include `_sheet` in the key. Forgetting this causes silent cross-sheet net merges that are extremely hard to debug.

### Multi-Instance Hierarchical Sheets

**Problem**: A parent sheet can reference the same sub-sheet file multiple times (e.g., 3 instances of `h_bridge.kicad_sch` for 3 motor phases). Each instance has different component references (Q1/Q2, Q3/Q4, Q5/Q6).

**How it works**:
1. `parse_single_sheet()` returns sub-sheet entries as `(path, uuid)` tuples
2. The main loop tracks `(file_path, instance_uuid)` pairs — same file with different UUIDs gets parsed separately
3. `extract_components()` reads the `(instances)` block in each symbol to remap the reference designator for the specific instance UUID
4. Each instance gets its own `_sheet` index

**KiCad storage format**: Each symbol in a sub-sheet has:
```
(instances
  (project "project_name"
    (path "/root_uuid/sheet_instance_uuid"
      (reference "Q4")
      (unit 1))
    (path "/root_uuid/other_instance_uuid"
      (reference "Q6")
      (unit 1))))
```

The sheet's UUID comes from the parent's `(sheet ... (uuid "xxx"))` block.

### Multi-Unit Symbols

**Problem**: ICs like STM32 have multiple units (GPIO unit, power unit, etc.) placed as separate symbols on the schematic. Each unit has different pins, but they share the same reference (e.g., U1).

**Solution**:
- `extract_lib_symbols()` stores pins per unit in `unit_pins` dict
- `extract_components()` reads `(unit N)` from each placed symbol
- `compute_pin_positions()` filters pins by unit number
- `generate_bom()` and `compute_statistics()` deduplicate by reference (count U1 once, not per unit)

**Pitfall**: Multi-unit components appear multiple times in `all_components`. Always use reference-based dedup when counting unique components.

### Label Scoping Rules

- **Local labels** (`label`): Connect only within their sheet (`_sheet` index must match)
- **Global labels** (`global_label`): Connect across all sheets
- **Hierarchical labels** (`hierarchical_label`): Connect via parent sheet's hierarchical pin
- **Power symbols**: Behave like global labels (connect across all sheets by name)

In `build_net_map()`, local labels use `(name, sheet)` as their union key, while global/hierarchical labels and power symbols use `(name,)` (no sheet).

### Net Name Assignment

Nets are assigned names with this priority:
1. Power symbol name (e.g., "GND", "+3V3")
2. Global/hierarchical label name
3. Local label name
4. `__unnamed_N` for nets with no label

**Duplicate name handling**: When multiple disconnected wire groups share the same net name (e.g., two separate "GND" connections via local labels), the second group's pins are merged into the first's net entry rather than overwriting it. This was a previous bug (commit f8ae22b).

## Value Parser

`parse_value()` converts component value strings to floats:

| Input | Output | Notes |
|-------|--------|-------|
| `"4.7k"` | 4700.0 | SI prefix |
| `"4K7"` | 4700.0 | Embedded multiplier |
| `"0R1"` | 0.1 | R as decimal point |
| `"100n"` | 1e-7 | |
| `"300µ"` | 0.0003 | Unicode micro |
| `"0.3mOhm"` | 0.0003 | Ohm suffix stripped |
| `"220k/R0402"` | 220000.0 | Splits on "/" first |
| `"4.7k 1%"` | 4700.0 | Tolerance stripped |
| `"DNP"` | None | Not parseable |

**Pitfall**: The parser is generous — it will parse the first numeric-looking thing it finds. Value fields like "FDMT80080DC" (a MOSFET part number) may parse to a number. Always check `c["type"]` before using parsed values.

## Signal Analysis Patterns

### Detection Pattern: Two Resistors Sharing a Net (Voltage Dividers)

Iterates all resistor pairs, finds shared nets (mid-point), checks endpoints for power/ground.

**Known pitfalls**:
- **R_top/R_bottom assignment**: After swapping r1/r2 to fix orientation, must re-derive net membership from current r1/r2 (not stale `r1_n1` variables). Previous bug: stale variables caused ratio inversion.
- **Power rail mid-point filter**: If the mid-point has >4 connections and is a power/ground net, reject — it's a bus, not a divider output.
- **Solder jumper gaps**: Dividers gated by solder jumpers (SJ) break the direct R-R series topology. Accepted limitation.

### Detection Pattern: IC Pin Matching (Regulators, Op-amps)

Scans IC pins by name (FB, SW, BOOT, VIN, VOUT, etc.) to classify function.

**Key rule**: Strip trailing digits before matching (`pn_base = pname.rstrip("0123456789")`). Multi-channel regulators have pins like FB1, SW2, ADJ2.

**Regulator false positive prevention**: ICs without FB/SW/BOOT pins require regulator keywords in lib_id/value. ICs with SW pin but no inductor on the SW net also require keywords. This prevents analog ICs with "SW" pins (like AD8233 gain switch) from being classified as regulators.

### Detection Pattern: Component on Both Sides (Current Sense, Bridges)

Finds ICs connected to both nets of a 2-terminal component (shunt resistor for current sense, transistors for bridges).

**4-pin Kelvin shunts**: Check for pin 3/4 presence *before* using `get_two_pin_nets()`. Kelvin shunts have pins 1,4 (current path) and pins 2,3 (sense). `get_two_pin_nets()` returns pins 1,2 which is wrong for Kelvin.

**1-hop tracing**: For current sense, if no IC is found directly on both sides of the shunt, trace through resistors (filter resistors between shunt and sense IC are common in BMS designs).

### Detection Pattern: Keyword Matching (ESD, Memory, RF)

Many detectors use keyword lists to identify component types from value/lib_id strings. When adding new keywords:
- Use lowercase matching (`val.lower()`)
- Test against the batch suite to check false positive rates
- Substring matching can be too broad (e.g., `"power"` matched `"dc-power-supply-rescue"` — fixed by requiring exact prefix match or `_power` suffix)

### Component Type Classification

`classify_component()` uses reference prefix → type mapping, then fallback keyword checks on value/lib_id.

**X prefix ambiguity**: X can mean crystal (IEC standard) or connector (some designers). The code checks value/lib keywords. Active oscillators (MEMS, TCXO) with "oscillator" in lib but not "crystal"/"xtal" get typed as `"oscillator"` (an IC-like active device), not `"crystal"` (passive).

**Power symbols**: Detected by `(power)` flag in lib_symbol definition, or `#PWR`/`#FLG` reference prefix, or `lib_prefix == "power"` / `lib_prefix.endswith("_power")`. The substring check was previously too broad.

## Adding New Detection Features

1. **Start with the net graph**. Most detections work by finding components sharing nets with specific topologies.

2. **Use `get_two_pin_nets()`** for passive 2-terminal components. For multi-pin ICs, iterate `pin_net.get((ref, pin_number))`.

3. **Filter high-fanout nets**. Power rails (+3V3, GND) connect to many components. Most detection patterns should skip or special-case nets with >4-6 connections, or nets identified as power/ground by `is_power_net()`/`is_ground()`.

4. **Test against the harness**. See `kicad-happy-testharness` repo — `run_tests.py --smoke` runs the 565-test PR-gate subset in ~30s with no corpus dependency, `run_tests.py --quick-sanity` runs 5-repo assertions, and `run/run_schematic.py --jobs 16` runs the full 5,829-repo corpus regression (~30 min).

5. **Count detections across the corpus** to calibrate sensitivity. Too many detections (>1000 for a specific pattern across the 36,000+ schematic files) suggests false positives. Too few (<5) might mean overly narrow keywords. Use `run/run_schematic.py --cross-section smoke` or `--cross-section quick_200` for faster calibration passes.

6. **Validate manually** against 2-3 known schematics where the pattern definitely exists. Check that component references, net names, and computed values match what you see in the raw schematic.

## Test Harness

Location: `kicad-happy-testharness` sibling repo.

- 5,829 open-source KiCad projects spanning KiCad 5 through 10
- ~36,500 schematic files, ~18,700 PCB files, ~5,500 gerber dirs
- 2M+ regression assertions at 99.98%+ pass, 565-test smoke subset, 5-repo quick-sanity
- Schema drift tests across all 8 analyzer types
- Equation audit (107 tagged equations), constants audit (105+ switching freqs), bugfix guards

The harness is the authoritative validation layer. For the legacy `batchtest` directory some older scripts reference — the 1,053-file subset that lived under `~/Projects/sandbox/batchtest/` — is retired. All new detector work validates against the harness corpus.

## Known Remaining Limitations

- **Legacy pin mapping**: `.sch` pin-to-net mapping uses heuristic geometry snapping (up to 12mm radius) when `.lib` symbols are incomplete or resolved from fallback sources
- **Vout estimation**: Feedback divider Vout uses hardcoded Vref guesses (0.6, 0.8, 1.0, 1.22, 1.25V) without a component database
- **Regulator output_rail**: Switching regulators sometimes show null output_rail when the power net is on the inductor output side
- **Eagle files**: Not parseable — output 0 components
