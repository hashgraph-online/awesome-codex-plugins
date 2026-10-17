# PCB Layout Analyzer — Methodology

This document describes the analysis methodology used by `analyze_pcb.py`. It covers parsing, extraction, connectivity analysis, DFM scoring, and all physical layout analyses.

## Design Philosophy

Same as the schematic analyzer — this is a **data extraction layer**. It outputs structured JSON containing neutral observations about the physical PCB layout. An LLM (or human reviewer) consumes this alongside the schematic analysis and datasheets for design review.

The PCB analyzer focuses on what can be determined from the `.kicad_pcb` file alone, without requiring the schematic. Cross-referencing with schematic data (component types, net functions) is performed by the consuming LLM.

Detection should be thorough — an undetected DFM issue or thermal problem is a blind spot that can cost hundreds of dollars at fab. At the same time, every reported measurement (trace width, clearance, via count, distance) must be accurate, because incorrect data leads to incorrect review conclusions. The analyzer favors comprehensive extraction with precise facts over selective reporting with opinions.

---

## 1. Parsing Pipeline

The PCB analyzer uses the same `sexp_parser.py` as the schematic analyzer. A `.kicad_pcb` file is parsed into nested Python lists, then traversed using `find_all`, `find_first`, `get_value`, `get_property`, and `get_at`.

### Format Compatibility

The analyzer handles both:
- **KiCad 6+**: `(footprint ...)` blocks, `(property "Reference" "R1")` syntax
- **KiCad 5**: `(module ...)` blocks, `(fp_text reference "R1")` syntax

Detection is automatic — `find_all(root, "footprint") or find_all(root, "module")`.

---

## 2. Core Extraction

### 2.1 Layer Stack

Extracts from `(layers ...)` block: layer numbers, names, types (signal, user, etc.), and whether visible. Used to determine copper layer count and stackup.

### 2.2 Setup / Design Rules

Extracts from `(setup ...)` block:
- Board thickness, copper weight
- Default trace width, via size/drill, clearance
- Solder mask/paste margins
- Zone fill settings (thermal relief, spoke width)
- DRC settings (min track width, min drill, min clearance)

### 2.3 Net Definitions

KiCad ≤9: Extracts `(net N "name")` entries — maps net numbers to names. Net numbers are used throughout the file to identify which net a pad, track, via, or zone belongs to.

KiCad 10: No net declarations section. Nets are identified by name strings directly in pads, tracks, vias, and zones. The analyzer builds a synthetic integer mapping from all unique net names for internal use.

### 2.4 Footprint Extraction

Each `(footprint ...)` or `(module ...)` block produces:

```python
{
    "library": "Resistor_SMD:R_0402_1005Metric",
    "reference": "R1",
    "value": "10k",
    "mpn": "RC0402FR-0710KL",
    "x": 100.0, "y": 50.0, "angle": 90.0,
    "layer": "F.Cu",
    "type": "smd",                # or "through_hole"
    "pad_count": 2,
    "pads": [...],                 # detailed pad list
    "dnp": False,
    "exclude_from_bom": False,
    "courtyard": {"min_x": ..., "max_x": ..., ...},
    "connected_nets": ["GND", "+3V3"],
    "models_3d": ["${KICAD8_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_0402.wrl"],
}
```

**Pad extraction** per footprint includes:
- Pad number, type (`smd`, `thru_hole`, `np_thru_hole`), shape (`circle`, `rect`, `oval`, `roundrect`, `custom`)
- Absolute position (footprint-relative position rotated by footprint angle, then translated)
- Size (width, height), drill diameter and shape (round vs. oval)
- Net assignment (KiCad ≤9: net number + name; KiCad 10: net name only)
- Layer list (which copper/mask/paste layers the pad spans)
- Pin function and type (from schematic cross-reference: `pinfunction`, `pintype`)
- Custom pad copper area estimation (from primitives)
- Solder mask/paste margin overrides
- Zone connection override

**SMD vs. through-hole classification**: Determined from `(attr smd)` or `(attr through_hole)`. Falls back to pad type inspection for KiCad 5 files.

**Courtyard extraction**: Bounding box computed from `fp_line`, `fp_rect`, `fp_circle` on `CrtYd` layers, transformed to absolute coordinates.

### 2.5 Track Extraction

Extracts `(segment ...)` and `(arc ...)` blocks:
- Start/end coordinates, width, layer, net
- For arcs: start, mid, and end points (3-point arc definition)
- Width distribution histogram
- Layer distribution histogram
- Arc length computed via 3-point circle reconstruction

### 2.6 Via Extraction

Extracts `(via ...)` blocks:
- Position, pad size, drill diameter, net
- Layer span (e.g., `F.Cu` to `B.Cu` for through-hole, or specific layers for blind/micro vias)
- Via type: through, blind, or micro
- Tenting status (solder mask coverage)
- Free via flag (unanchored — typically stitching or thermal)
- Size distribution histogram

### 2.7 Zone Extraction

Extracts `(zone ...)` blocks — copper pours / fills:
- Net assignment, layer(s), fill type
- Zone outline polygon and bounding box
- Filled polygon regions (actual copper after zone fill)
- Outline area (user-drawn boundary) and filled area (actual copper)
- Thermal relief settings (spoke width, gap)
- Min thickness, clearance, pad connection type

**ZoneFills spatial index**: Filled polygon coordinates are stored in a `ZoneFills` class for efficient point-in-polygon queries. This allows checking whether copper actually exists at a specific (x, y) location on a given layer. Uses bounding box pre-filtering + ray-casting for the actual test.

**Important caveat**: Zone fill data is only accurate if zones were filled in KiCad (`Edit → Fill All Zones`) before saving. Stale fills produce incorrect copper presence results.

### 2.8 Board Outline

Extracts from `Edge.Cuts` layer: `gr_line`, `gr_arc`, `gr_circle`, `gr_rect` elements. Computes bounding box from all edge points to determine board dimensions (width × height).

---

## 3. Connectivity Analysis

Two levels of connectivity checking are performed:

### 3.1 Basic Routing Completeness

For each net with ≥2 pads, checks whether ANY routing exists (tracks, vias, or zones on that net). Fast but coarse — doesn't detect partially routed nets.

### 3.2 Full Union-Find Connectivity

Uses union-find (same algorithm concept as the schematic net builder) on `(x, y, layer)` coordinates snapped to a 1µm grid:

1. **Register pad locations** — each pad gets a point on each of its copper layers
2. **Union track segments** — each segment's start and end points are unioned on their layer
3. **Union vias** — a via unions its position across all layers it spans
4. **Account for zones** — for each net with a zone, union all pads on that net + layer (approximation: assumes zone covers all pads)

Then count connected components per net:
- **1 component** → fully routed
- **>1 components** → partially routed (some pads connected, others isolated)
- **No routing at all** → unrouted

This catches cases where a net is partially routed (e.g., 5 of 8 pads connected, 3 floating).

**Zone approximation**: Zones are assumed to connect all pads on the same net + layer. This is accurate for ground/power planes but may overcount for partial zone fills. A more precise check would use the `ZoneFills` spatial index to verify each pad is within the fill, but thermal relief clearances complicate point-in-fill tests.

---

## 4. Per-Net Trace Length

Measures total routing length per net:
- Segment length: `√((x2-x1)² + (y2-y1)²)`
- Arc length: 3-point circle reconstruction → radius × arc angle
- Per-layer breakdown (length and segment count)
- Via count per net

Enables differential pair matching, bus length matching, and routing completeness assessment.

---

## 5. Power Net Analysis

For nets classified as power/ground (by name heuristics — same as schematic analyzer):
- Track widths used (min, max, all widths)
- Total track length
- Track count
- Via counts and drill sizes
- Zone coverage (layers, filled area)

Reports minimum track width per power net — the current bottleneck.

---

## 6. Decoupling Placement Analysis

For each IC (U-prefix footprint), finds capacitors (C-prefix) within 10mm:
- Distance from IC center to cap center
- Whether cap shares a net with the IC (likely decoupling)
- Whether cap is on the same PCB side as the IC
- Reports closest capacitor distance per IC

---

## 7. Ground Domain Analysis

Identifies ground domain splits:
- Separate ground nets (GND, AGND, DGND, PGND, etc.)
- Components connected to each ground domain
- Ground zones per domain (layers covered)
- Components connected to multiple ground domains (potential star-ground or errors)

---

## 8. Trace Proximity Analysis

Optional analysis (enabled with `--proximity` flag). Uses a spatial grid (default 0.5mm cells) to find signal net pairs with traces running close together on the same layer:

1. Rasterize all track segments into grid cells, recording which nets occupy each cell
2. For cells with multiple signal nets, count shared-cell pairs
3. Report pairs sorted by approximate coupling length (`shared_cells × grid_size`)
4. Exclude power/ground nets (expected to be everywhere)

Useful for crosstalk risk assessment.

---

## 9. Current Capacity Analysis

Provides facts for IPC-2221 current capacity assessment:

**Per power/ground net**:
- Minimum and maximum track widths
- All track widths used
- Copper layers used
- Via count and drill sizes
- Zone coverage (layers, filled area, min thickness)

**Per via drill size**:
- Plating barrel cross-section: `A = π × d × t` (where `t = 25µm` typical plating)
- Approximate current rating at 10°C rise

**Narrow signal net flagging**: Signal nets with traces ≤0.15mm and ≥5 segments are flagged as potential current bottlenecks.

---

## 10. Thermal Analysis

### 10.1 Zone Stitching Vias

For each copper zone: counts vias on the same net, computes via density (vias/cm²), and reports drill sizes. Indicates thermal conductivity between zone layers.

### 10.2 Thermal Pad Detection

Identifies exposed/thermal pads on QFN, BGA, DFN packages:

**Detection criteria** (all must be met):
- SMD pad type
- Pad area > 4mm² (if numbered EP or 0) or > 9mm² (other pads)
- At least 2× the average pad area for the same component
- Connected to a power or ground net

For each thermal pad:
- Pad size and area
- Net assignment
- Nearby standalone vias (within 1.5× pad dimension)
- Footprint-embedded thermal via pads (thru_hole pads on same net within footprint)

### 10.3 Thermal Pad Via Adequacy

Extended analysis per thermal pad:
- Via count within pad area (rotation-aware containment check)
- Via density (vias/mm²)
- Tenting status (tented vs. untented — affects solder wicking risk)
- Recommendations based on pad area (rule of thumb: ~1 via per 1–2mm²)

---

## 11. Via Analysis

Comprehensive via characterization:

### Type Breakdown
Through-hole vs. blind vs. micro via counts and size distributions.

### Annular Ring
`(pad_size - drill) / 2` for every via. Reports min/max, distribution, and counts below common manufacturer minimums (0.125mm, 0.100mm).

### Via-in-Pad Detection
Identifies vias located within SMD pad bounding boxes. For each match: component, pad, whether same net (intentional via-in-pad vs. error).

### Fanout Pattern Detection
For BGA/QFN/QFP packages (≥16 pads), counts vias within 2mm of the component courtyard. Reports fanout via count and unique net count — useful for assessing BGA breakout routing.

### Current Capacity
Per drill size: plating barrel area and approximate current rating (25µm plating, conservative 10°C rise).

---

## 12. Layer Transition Analysis

For each signal net that uses multiple copper layers:
- Which copper layers are used
- Via count and positions
- Via layer spans

Useful for ground return path analysis — a via forces return current to find a path between reference planes. If no nearby stitching via exists, the return current loop area increases, raising EMI.

Power/ground nets are excluded (layer transitions are expected for planes).

---

## 13. Placement Analysis

### Courtyard Overlap Detection
Checks all footprint pairs for courtyard bounding box overlap. Uses spatial bucketing (10mm cells) to avoid O(n²) comparisons. Reports overlapping pairs with overlap area.

### Edge Clearance
Checks component courtyard proximity to board Edge.Cuts outline. Reports components closer than 0.5mm to board edge.

### Density Metrics
Component density per unit area, front/back distribution.

---

## 14. Silkscreen Analysis

### Board-Level Text
Extracts `gr_text` on SilkS/Silkscreen layers — project names, version labels, logos.

### Per-Footprint Reference Visibility
For each footprint: whether its reference designator is visible on the silkscreen (checks both KiCad 9 `property` nodes and KiCad 5–8 `fp_text` nodes for hide flags).

### Documentation Audit
Checks for:
- Missing board name/project identifier
- Missing revision marking (Rev, V1, V2, etc.)
- Connectors without function labels
- Switches without on/off indicators
- Polarized components (LEDs, electrolytic caps) without polarity markers on silk
- Test points without labels

---

## 15. DFM (Design for Manufacturing) Scoring

Compares actual design parameters against JLCPCB standard and advanced process limits.

### Checked Parameters

| Parameter | Standard Limit | Advanced Limit |
|-----------|---------------|----------------|
| Min track width | 0.127mm (5 mil) | 0.100mm (4 mil) |
| Min track spacing | 0.127mm (5 mil) | 0.100mm (4 mil) |
| Min via drill | 0.200mm | 0.150mm |
| Min annular ring | 0.125mm | 0.100mm |
| Board size | 100×100mm pricing threshold | — |
| Min board dimension | 10mm | — |

### Track Spacing Estimation

Approximate minimum spacing computed from endpoint-to-endpoint distances between different-net segments on the same layer. Edge-to-edge spacing: `center_distance - (width_a + width_b) / 2`. Sampling limited to 2000 segments per layer for performance.

### DFM Tier Classification

- **Standard**: All parameters within standard limits
- **Advanced**: One or more parameters require advanced process
- **Challenging**: One or more parameters exceed even advanced limits

---

## 16. Tombstoning Risk Assessment

Evaluates thermal asymmetry for small passive components (0201, 0402):

**Thermal mass analysis per pad**:
- Total copper area (track width × length) connected to each pad
- Whether pad connects to a zone (high thermal mass)
- Via proximity (vias add thermal mass on the connected side)

**Risk classification**:
- **High**: One pad on ground/power zone, other on thin signal trace (large thermal imbalance)
- **Medium**: Asymmetric track widths or via proximity
- **Low**: Reasonable thermal symmetry

**Copper ratio**: Computed as `min(pad_copper) / max(pad_copper)`. Ratios below 0.3 indicate high risk, 0.3–0.6 medium risk.

---

## 17. Thermal Pad Via Adequacy

Extended per-component assessment for packages with exposed thermal pads:
- Rotation-aware via containment (via positions transformed into pad-local coordinates)
- Via count vs. recommended count based on pad area
- Tenting status audit (untented thermal pad vias risk solder wicking)

---

## 18. Copper Presence Analysis

Uses the `ZoneFills` spatial index to check actual filled copper at pad locations across layers. For power/ground pads on ICs, verifies that zone fills actually reach the pad location (not just that a zone exists on the net).

---

## 19. Additional Extractions

### Board Metadata
Title block (title, revision, date, company), comments, board-level custom properties, paper size.

### Dimension Annotations
Designer-placed measurements: connector spacing, board dimensions, mounting hole distances. Extracts value, type, text label, and feature line endpoints.

### Groups
Designer-defined component/routing groupings (KiCad 7+).

### Net Classes
Legacy KiCad 5 net class definitions (stored in PCB file): default and named classes with clearance, track width, via size/drill settings.

---

## 20. Geometry Helpers

- **Shoelace formula**: Polygon area from vertex coordinates. Used for zone outline and fill area computation.
- **Point-in-polygon**: Ray-casting algorithm with bounding box pre-filtering. Used by ZoneFills for spatial queries.
- **Arc length (3-point)**: Reconstructs circle from start/mid/end points, computes arc angle × radius. Handles degenerate (collinear) cases as straight lines.

---

## 21. Output Structure

```json
{
    "analyzer_type": "pcb",
    "summary": { "total_findings": 42, "by_severity": { "error": 2, "warning": 15, "info": 25 } },
    "findings": [{ "detector", "rule_id", "category", "severity", "confidence",
                    "summary", "description", "components", "nets", "recommendation",
                    "report_context": { "section", "impact", "standard_ref" }, ... }],
    "file": "path/to/board.kicad_pcb",
    "kicad_version": "9.0.0",
    "statistics": { "footprint_count", "smd_count", "tht_count", "copper_layers_used",
                    "track_segments", "via_count", "zone_count", "total_track_length_mm",
                    "board_width_mm", "board_height_mm", "routing_complete" },
    "layers": [...],
    "setup": { "board_thickness_mm", "design_rules", "defaults", ... },
    "nets": { "net_name": net_number, ... },
    "board_outline": { "edges", "bounding_box" },
    "component_groups": { "R": {"count": 45, "references": [...]}, ... },
    "footprints": [{ "reference", "value", "x", "y", "layer", "type", "connected_nets", ... }],
    "tracks": { "segment_count", "arc_count", "width_distribution", "layer_distribution" },
    "vias": { "count", "size_distribution", "via_analysis": { "type_breakdown", "annular_ring",
              "via_in_pad", "fanout_patterns", "current_capacity" } },
    "zones": [...],
    "connectivity": { "fully_routed", "partially_routed", "routing_complete" },
    "net_lengths": [{ "net", "total_length_mm", "layers", "via_count" }],
    "power_net_routing": [...],
    "decoupling_placement": [...],
    "ground_domains": { "domains", "multi_domain_components" },
    "layer_transitions": [...],
    "silkscreen": { "board_texts", "refs_visible", "hidden_refs", "documentation_warnings" },
    "board_metadata": { "title", "rev", "date", ... },
    "dfm_summary": { "dfm_tier", "metrics", "violation_count", "ipc_class_compliance" },
    "placement_density": { ... },
    "copper_presence_summary": { ... },
    "board_thickness_mm": 1.6
}
```

Sections previously at top level (`thermal_analysis`, `thermal_pad_vias`, `tombstoning_risk`, `placement_analysis`, `current_capacity`, `copper_presence`, `dfm`) are now flattened into `findings[]`. Summary data is preserved in `dfm_summary`, `placement_density`, `copper_presence_summary`, and `board_thickness_mm`.

---

## 22. Known Limitations

1. **No netlist cross-check**: The PCB analyzer doesn't read the schematic. Net names and pad assignments come from the PCB file itself. Cross-referencing with the schematic (e.g., detecting unplaced components) requires running both analyzers.

2. **Zone fill staleness**: Zone fill polygons in the PCB file may be stale (not refilled after layout changes). The analyzer trusts whatever fill data is present. If zones haven't been refilled, copper presence analysis may be inaccurate.

3. **Track spacing approximation**: Minimum trace spacing is estimated from endpoint-to-endpoint distances, not full segment-to-segment geometry. The actual minimum spacing could be smaller (e.g., traces running parallel but sampled at endpoints). The DFM report notes this approximation.

4. **Zone connectivity approximation**: In union-find connectivity analysis, zones are assumed to connect all pads on the same net + layer. This is accurate for filled planes but may overcount for partial zones with cutouts.

5. **No impedance calculation**: The analyzer doesn't compute controlled impedance from stackup data. It reports trace widths and layer assignments; impedance calculation requires knowing dielectric thickness and Er, which are in the stackup but not processed into impedance values.

6. **Single-file analysis**: Only processes one `.kicad_pcb` file. Doesn't handle multi-board projects or panelized designs.

7. **Courtyard-only overlap detection**: Component overlap uses courtyard bounding boxes, not actual pad/silk geometry. Components without courtyards aren't checked.

8. **Tombstoning risk is heuristic**: Thermal mass estimation uses track width × length as a proxy. Actual thermal behavior depends on copper weight, zone connections, and thermal relief geometry that aren't fully modeled.
