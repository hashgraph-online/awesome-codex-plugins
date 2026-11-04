# Deep PCB Layout Analysis (`.kicad_pcb`)

This reference covers in-depth PCB analysis techniques beyond what the `analyze_pcb.py` script provides automatically. For routine analysis, run the script first — it handles via classification, annular ring checks, connectivity, placement, thermal vias, current capacity, and signal integrity automatically.

Use this reference for:
- **Impedance calculations** from stackup parameters
- **DRC/net class auditing** against manufacturer capabilities
- **Power electronics design review** (trace current, sense routing, thermal management)
- **Differential pair validation** (impedance, length matching)
- **Manual script-writing patterns** when building custom analysis tools

For the PCB file format details (S-expression structure, fields, layer definitions), see `file-formats.md`.

## Table of Contents

1. [Setup and Stackup](#setup-and-stackup)
2. [Net Classes and Design Rules](#net-classes-and-design-rules)
3. [Differential Pairs](#differential-pairs)
4. [PCB Review Techniques](#pcb-review-techniques) (includes Power Electronics Design Review)
5. [Return Path Analysis](#return-path-analysis) — Reference plane continuity for high-speed signals
6. [Copper Balance Assessment](#copper-balance-assessment) — Layer symmetry for warp prevention
7. [Board Edge Clearance](#board-edge-clearance) — DFM clearance from board edges and depaneling features
8. [Writing Analysis Scripts](#writing-analysis-scripts) (S-expr parsing, coordinate transforms, spatial queries)

---

## Setup and Stackup

The `(setup ...)` section contains board-level configuration. The analyzer extracts layer count, thickness, copper finish, and paste ratios automatically. Use this section for **impedance calculations** which require the full stackup detail.

### Stackup Structure
```
(setup
  (stackup
    (layer "F.Cu" (type "copper") (thickness 0.035))
    (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
    (layer "B.Cu" (type "copper") (thickness 0.035))
    (copper_finish "None")
    (dielectric_constraints no)
  )
)
```

### Key Stackup Fields

| Field | Description |
|-------|-------------|
| `thickness` | Layer thickness in mm (copper: typically 0.035 = 1oz) |
| `material` | Dielectric material (FR4, Rogers, etc.) |
| `epsilon_r` | Relative permittivity (affects impedance calculations) |
| `loss_tangent` | Dielectric loss (affects high-frequency signal integrity) |
| `copper_finish` | Surface finish: `None`, `HASL`, `ENIG`, `OSP`, etc. |

### Impedance Analysis

- Total board thickness = sum of all layer thicknesses
- Copper weight: 0.035mm = 1oz, 0.070mm = 2oz
- For impedance control, you need `epsilon_r` and dielectric thickness between signal and reference layers
- Compare stackup to manufacturer capabilities (e.g., JLCPCB standard 4-layer stackup)
- Use an impedance calculator with the board's specific `epsilon_r` and dielectric thickness

---

## Net Classes and Design Rules

Net classes define per-net routing constraints. They appear in the `.kicad_pro` file (JSON) rather than the `.kicad_pcb` file, but the PCB enforces them.

In `.kicad_pro`:
```json
"net_settings": {
  "classes": [
    {
      "name": "Default",
      "clearance": 0.2,
      "track_width": 0.2,
      "via_diameter": 0.6,
      "via_drill": 0.3,
      "microvia_diameter": 0.3,
      "microvia_drill": 0.1,
      "diff_pair_width": 0.2,
      "diff_pair_gap": 0.15
    },
    {
      "name": "Power",
      "clearance": 0.25,
      "track_width": 0.5,
      "via_diameter": 0.8,
      "via_drill": 0.4,
      "nets": ["+3V3", "+5V", "+VBAT", "GND"]
    }
  ]
}
```

### Verifying Track Widths Against Net Classes

To check if all tracks comply with their net class:
1. Read net class definitions from `.kicad_pro`
2. Build a mapping: net name -> net class -> min track width
3. Read all `(net N "name")` declarations in the PCB
4. For each `(segment ... (width W) ... (net N) ...)`, verify W >= net class minimum
5. Flag violations

### Netclass Audit for Power Electronics

Power electronics designs should have multiple netclasses. A single "Default" netclass is a red flag for any design with high-current paths. Expected netclasses: Power (wide traces), GateDrive (controlled routing), Sense (guarded/matched).

---

## Differential Pairs

Differential pairs in KiCad use a naming convention: nets ending in `+` and `-` (e.g., `USB_D+`/`USB_D-`) or `_P`/`_N`.

### Identifying Differential Pairs

1. Scan all net names for matching +/- or _P/_N pairs
2. For each pair, collect all segments on both nets
3. Verify routing:
   - Both traces should be on the same layer
   - Widths should match (from diff_pair_width in net class)
   - Gap should be consistent (from diff_pair_gap in net class)
   - Length should be matched (within tolerance, typically < 0.1mm)

### Common Differential Pairs

| Interface | Impedance | Typical Width/Gap (FR4 1.6mm) |
|-----------|-----------|-------------------------------|
| USB 2.0 | 90 ohm diff | 0.2mm / 0.15mm |
| USB 3.0 | 85 ohm diff | varies by stackup |
| HDMI | 100 ohm diff | varies by stackup |
| Ethernet | 100 ohm diff | varies by stackup |
| LVDS | 100 ohm diff | varies by stackup |

Actual dimensions depend on stackup — use an impedance calculator with the board's `epsilon_r` and dielectric thickness.

---

## PCB Review Techniques

### Power Electronics Design Review

For motor controllers, power supplies, and other high-current designs, check these additional items beyond what the analyzer provides.

#### Net Function Verification

**Critical — do this before flagging trace widths.** Net names alone are unreliable indicators of current level. In power electronics, sense/feedback nets often run parallel to power nets with similar names. Before flagging a net for insufficient trace width:

1. Check what components the net connects to (from analyzer output). Resistors, capacitors, and op-amp inputs indicate a sense/filter network carrying microamps — 0.2mm is fine.
2. Check the schematic: trace the net from its label to the actual pins. Power nets connect directly to MOSFET drain/source, connector pins, or inductor terminals. Sense nets connect through resistor dividers to ADC/comparator inputs.
3. Common sense net patterns: resistor dividers off motor phases (back-EMF sensing), Kelvin sense traces from shunt resistors, voltage monitor taps.

#### Trace Width vs Current Capacity

The analyzer provides `current_capacity` data with min/max track widths per net. Cross-reference against net function:

| Net Function | Minimum Width (1oz Cu, 10°C rise) | Notes |
|---|---|---|
| Signal (< 100mA) | 0.15-0.2mm | Default netclass is fine |
| Low power (100mA-1A) | 0.3-0.5mm | LED drives, logic power |
| Medium power (1-5A) | 0.5-1.0mm | Motor phases (small motors) |
| High power (5-20A) | 1.0-3.0mm or copper pour | Motor phases, battery, VM |
| Very high power (>20A) | Copper pour + via stitching | Power MOSFETs, motor outputs |

Internal layers carry ~50% of external layer current. These are rough estimates — use an IPC-2221 calculator for precise values.

#### Voltage Derating

Cross-reference capacitor voltage ratings (from schematic Value field) against the power rail they connect to:
- Electrolytic: derate to 80% of rated voltage (63V cap → max 50V rail)
- Ceramic (Class II): derate to 80% or less (DC bias causes capacitance drop)
- Film: derate to 70-80%
- Flag any cap at >80% of its voltage rating on a power rail

#### Current Sense Routing

For shunt resistor current sensing (common in motor control):
- Sense traces (to op-amp inputs) should be Kelvin-connected — routed directly from the resistor pads, not from the power trace
- Check for zones on sense nets — these provide low-impedance Kelvin sensing
- Sense traces should be routed as a pair, away from switching nodes

### Signal Integrity Checks

The analyzer provides trace proximity data (with `--proximity`) and layer transition tracking. For deeper analysis:

1. **Return path continuity**: For high-speed signals, check that the reference plane (usually GND) is continuous under the signal trace. Look for zone splits or cutouts on the GND layer beneath high-speed traces.

2. **Via stubs**: Through-hole vias used for inner-layer connections have stubs that can cause signal reflections above ~3 GHz. Check if any high-speed signals use through vias to inner layers.

3. **Trace length matching**: For parallel buses (DDR, RGMII), traces should be length-matched. Use the analyzer's `net_lengths` data to compare.

4. **90-degree corners**: Sharp 90-degree bends are acceptable for most designs but should be avoided for high-speed signals (>1 GHz).

### Copper Balance Analysis

Check that copper is roughly balanced between layers — imbalanced copper can cause board warping during manufacturing. Use the analyzer's per-layer segment counts and zone data.

---

## Return Path Analysis

For high-speed signals, the return current flows on the nearest reference plane directly beneath the trace. Any discontinuity in this return path creates a loop antenna that radiates EMI and degrades signal integrity.

### Procedure

1. **Identify high-speed nets**: USB data pairs, SPI CLK/MOSI/MISO (>10 MHz), UART at high baud rates (>1 Mbaud), DDR signals, clock distribution nets, RMII/RGMII
2. **Determine trace layer**: from the analyzer output or PCB file, identify which copper layer each high-speed signal is routed on
3. **Check reference plane coverage**: verify that the adjacent plane layer (usually GND) has continuous copper fill beneath the entire trace path. Look for:
   - Zone cutouts or keepout areas under the signal trace
   - Splits in the ground plane (caused by routing power traces on the ground layer)
   - Missing zone fill (unfilled areas due to clearance rules around other pads/vias)
4. **Flag violations**: any high-speed trace that crosses a plane split or gap

### Layer Transitions (Via Return Path)

Every via that moves a signal to a different layer changes its reference plane. If the reference planes on the two layers are different nets (e.g., signal moves from a layer referenced to GND to a layer referenced to VCC), the return current has no low-impedance path between the planes at the via location.

**Check for each high-speed signal via:**
- What is the reference plane on the departure layer?
- What is the reference plane on the arrival layer?
- If they differ, is there a stitching capacitor (100nF between the two planes) near the via?

For 2-layer boards, this is less applicable since both layers reference the same planes (or have no continuous plane at all — which is itself a concern for signals >10 MHz).

### High-Risk Patterns

| Pattern | Risk | Mitigation |
|---------|------|------------|
| Signal crossing a ground plane split | Return current detours around the split, creating a large loop | Route signal around the split, or bridge the split with a stitching via |
| Signal via between GND-referenced and VCC-referenced layers | Return current has no path between planes | Place 100nF stitching cap between GND and VCC near the via |
| High-speed trace on a layer with no adjacent plane | No defined return path, uncontrolled impedance | Route high-speed signals only on layers adjacent to continuous planes |
| Multiple high-speed signals sharing a narrow ground corridor | Return currents overlap, causing crosstalk | Widen the ground area or separate the signals |

---

## Copper Balance Assessment

Imbalanced copper distribution between layers causes board warping during reflow soldering due to differential thermal expansion. This is a manufacturing concern, not an electrical one, but warped boards can cause assembly defects.

### Procedure

1. **Estimate per-layer copper coverage**: Use the analyzer's zone data and segment counts. Approximate copper fill percentage as: (total zone area + total trace area) / board area. Exact calculation requires zone polygon analysis, but a rough comparison between layers is usually sufficient.
2. **Compare corresponding layer pairs**:
   - 2-layer board: F.Cu vs B.Cu
   - 4-layer board: F.Cu vs B.Cu (outer pair), In1.Cu vs In2.Cu (inner pair)
3. **Flag imbalances**: if one layer in a pair has significantly more copper than the other

### Guidelines

| Board Type | Acceptable Imbalance | Common Issue |
|------------|---------------------|--------------|
| 2-layer | <15% difference between F.Cu and B.Cu | One side has large ground pour, other side has only traces |
| 4-layer | Inner layers usually balanced (full planes); check outer layers <15% | Component-heavy front with sparse back |

### Mitigation

- Add copper fill (ground pour) to the sparse layer — this is the most common fix
- For 2-layer boards, add a ground pour on the component side as well as the solder side
- Thieving (non-functional copper patterns) can be added in empty areas but is less common in hobby designs

### Severity

Flag as **Suggestion** for <20% imbalance, **Warning** for >20% imbalance. Boards with large power planes on one side and minimal copper on the other are most at risk.

---

## Board Edge Clearance

Components placed too close to the board edge risk damage during depaneling (V-score, tab routing, or saw cutting). This is a DFM (Design for Manufacturing) check.

### Minimum Clearances

| Component Type | Min Distance from Board Edge | Rationale |
|----------------|----------------------------|-----------|
| SMD (low profile) | 1 mm | Mechanical stress during handling |
| SMD (tall, e.g., electrolytic caps) | 3 mm | Leverage from tall components amplifies stress |
| Through-hole | 2 mm | Leads extend through board, vulnerable to flex |
| BGA | 3 mm | Solder joints are stress-sensitive |
| Connectors (edge-mounted) | 0 mm (intentionally at edge) | Verify they extend to/past edge as designed |
| Mounting holes | 3 mm to nearest component | Board flexes around mounting points |

### Depaneling Method Considerations

| Method | Keep-out from Score/Tab | Notes |
|--------|------------------------|-------|
| V-score | 2 mm from V-score line | 0.3mm residual web can crack nearby joints during snap |
| Tab routing (breakaway tabs) | 3 mm from tab connections | Mechanical stress during break-out radiates outward |
| Saw cutting | 1 mm from cut line | Clean cut, minimal stress |
| Laser cutting | 0.5 mm from cut line | Precision cut, heat-affected zone is small |

### Procedure

1. Get the board outline from the Edge.Cuts layer (the analyzer provides board dimensions)
2. For each component, compute the minimum distance from any pad to the nearest board edge
3. Compare against the clearance table above
4. For panelized designs, also check clearance from panel rails and mouse bites

### Severity

Flag as **Warning** if components violate the minimums above. Flag as **Info** for edge-mounted connectors (intentional placement) — just verify they're oriented correctly.

---

## Writing Analysis Scripts

When the analyzer doesn't cover a specific check, build a custom script. The `analyze_pcb.py` script uses the `kicad_core/sexp.py` shared parser — import it directly rather than writing regex-based parsing.

### Using the Shared Parser

```python
import sys
sys.path.insert(0, '<skill-path>/scripts')
from kicad_core.sexp import parse_file, find_all, find_first, get_value, get_property, get_at
from pcb.reader import extract_footprints, extract_tracks, extract_vias, extract_nets

# Parse and extract in one shot
tree = parse_file('board.kicad_pcb')
footprints = extract_footprints(tree)
tracks = extract_tracks(tree)
```

If you can't import the shared parser (e.g., standalone script), see `manual-pcb-parsing.md` for regex-based patterns.

### Coordinate Transforms

Pad positions in footprint definitions are **relative to the footprint origin**. To get absolute board coordinates:

```python
import math

def pad_to_absolute(fp_x, fp_y, fp_angle_deg, pad_rx, pad_ry):
    """Transform pad-relative coords to absolute board coords."""
    rad = math.radians(-fp_angle_deg)  # KiCad angles: CW positive in layout
    abs_x = fp_x + pad_rx * math.cos(rad) - pad_ry * math.sin(rad)
    abs_y = fp_y + pad_rx * math.sin(rad) + pad_ry * math.cos(rad)
    return abs_x, abs_y
```

### Net Function Classification

Before making current-capacity claims about a net, verify what the net actually does:

```python
def classify_net(net_name, connected_refs):
    """Classify a net as power, sense, signal, or ground."""
    ref_prefixes = {ref[0] for ref in connected_refs}
    passive_only = ref_prefixes <= {'R', 'C', 'L'}
    has_mosfets = 'Q' in ref_prefixes
    has_connectors = 'J' in ref_prefixes

    if passive_only:
        return 'sense'  # Likely voltage divider / filter, microamp current
    if has_mosfets and has_connectors:
        return 'power'  # Motor phase, power output
    return 'signal'
```

### Spatial Queries

**Point-in-polygon** (for zone containment checks):
```python
def point_in_polygon(x, y, polygon_pts):
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(polygon_pts)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon_pts[i]
        xj, yj = polygon_pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside
```

**Bounding box containment** (faster pre-filter):
```python
def point_in_bbox(x, y, cx, cy, half_w, half_h, angle_deg=0):
    """Check if point is within a rotated rectangle (pad bounding box)."""
    dx, dy = x - cx, y - cy
    if angle_deg != 0:
        rad = math.radians(angle_deg)
        dx, dy = dx*math.cos(rad) + dy*math.sin(rad), -dx*math.sin(rad) + dy*math.cos(rad)
    return abs(dx) <= half_w and abs(dy) <= half_h
```

### Common Pitfalls

1. **Confusing pad-relative and absolute coordinates** — pad `(at ...)` inside a footprint is relative; segment/via `(start/at ...)` is absolute. Always transform pads before comparing.
2. **Ignoring footprint rotation** — a pad at `(at 3 0)` in a footprint rotated 90° is actually at a different absolute position. The transform is not optional.
3. **Net name vs net ID** — in KiCad ≤9, segments reference nets by numeric ID; build the ID→name map from `(net N "name")` declarations. In KiCad 10, nets are referenced by name string directly (no declarations section). The analyzer handles both formats transparently.
4. **Zone polygon vs filled polygon** — `(polygon ...)` is the user-drawn boundary; `(filled_polygon ...)` is the actual copper after DRC clearance carving. Always use filled polygons for containment tests. The PCB analyzer extracts both: `outline_bbox`/`outline_area_mm2` for the boundary, `filled_bbox`/`filled_area_mm2`/`fill_ratio` for actual copper. The `copper_presence` section reports which components have zone copper on the opposite layer — use this instead of inferring from zone outlines. Zone fills can go stale if the board was edited after the last Fill All Zones (shortcut `B`).
5. **Assuming net function from name** — net names like VPH*, VSENSE*, etc. can look like power nets but may be sense lines. Always verify by checking connected component types.
6. **Measuring decoupling distance to IC center** — large modules (ESP32, etc.) can be 18+ mm long with power pins at one edge. Always measure to the IC's actual power pin positions.

### Copper-Sensitive Components

Some components require careful copper management on both layers. Use the analyzer's `copper_presence` data to verify these — don't infer from zone outlines.

**Capacitive touch pads** (TP prefix, or pad-only footprints on touch nets):
- Need NO copper on the opposite layer — ground planes under touch pads drastically reduce sensitivity by adding parasitic capacitance. But confirming copper absence isn't enough: check that **keepout zones** (rule areas) enforce this on the opposite layer. Without a keepout zone, the copper absence is accidental and one zone refill after a routing change could break touch sensitivity. If no keepout zones exist, flag as WARNING.
- Need controlled clearance in same-layer ground pour (typically ≥1mm, check the controller's app note). Measure the actual clearance and compare against the spec minimum — if it's at the exact minimum, note the sensitivity margin concern and recommend increasing to 1.5× the minimum.
- Trace to the controller should be thin (narrow reduces parasitic capacitance) and direct (no unnecessary length). Compare trace lengths across ALL touch pads — asymmetry >1.5× means different parasitic capacitance per channel, shifting baseline readings even with firmware calibration. Report the ratio.
- Hatched ground pour around the pad is sometimes used instead of solid clearance — check the fill type
- Report physical details for each pad: diameter/size, position, GND clearance (measured vs spec), trace width, trace length to controller

**Antennas** (ANT prefix, antenna footprints, or wireless modules with PCB/integrated antennas like ESP32, nRF):
- PCB trace antennas and module antennas need copper keep-out on ALL relevant layers for the antenna area — verify keepout zones exist and report their coordinates and layer coverage (e.g., "Keepout zone on F.Cu+B.Cu: (8.49, 98.05) to (29.49, 146.05)")
- Ground plane should end at the antenna feed point, not extend under the radiating element
- Check manufacturer's reference design for ground plane requirements — the module vendor's layout guide is the authoritative source for keepout dimensions. Always cite the reference when verifying: "Correct per Espressif guidelines"

**RF components** (matching networks, baluns near antenna):
- Controlled impedance traces need consistent ground reference
- Ground plane voids under matching components can detune the network

In all cases, the `copper_presence.no_opposite_layer_copper` list in the analyzer output identifies components without opposite-layer zone copper — these are the isolation points to verify against the design intent.

---

## Datasheet-Driven PCB Validation

The schematic analysis methodology already prompts for datasheet cross-referencing (Vref lookup, pin verification, component values). PCB layout review needs the same rigor — many layout bugs are only visible when checked against the IC's datasheet recommendations.

### Thermal Management

- **Thermal vias**: Compare the number, size, and pattern of thermal vias under QFN/DFN/PowerPAD packages against the IC datasheet's recommended layout. Many datasheets specify exact via count, diameter, and grid pattern (e.g., TI's PowerPAD guidelines: 4×4 array of 0.3mm vias on 1.2mm pitch).
- **Thermal via effective count methodology**: The `thermal_pad_vias` analyzer output includes an `effective_via_count` that weights each via by its plated barrel cross-section area relative to a 0.3mm reference drill: `(drill_diameter / 0.3)² per via`. Examples: 0.3mm via = 1.0 effective, 0.2mm = 0.44, 0.5mm = 2.78, 1.0mm = 11.1. The `recommended_min_vias` and `recommended_ideal_vias` thresholds are calibrated for 0.3mm reference vias and scale by pad area (pad <10mm²: min 5/ideal 9; 10-25mm²: min 9/ideal 16; >25mm²: 0.5×area/0.8×area). When interpreting the adequacy rating, note that designs intentionally using smaller vias (e.g., 0.2mm to prevent solder wicking through vias during reflow, common in module footprints like ESP32) may appear "insufficient" despite adequate thermal performance. Always cross-reference the via count and drill size against the component datasheet's specific recommendations before flagging as a concern.
- **θJA validation**: The datasheet's θJA is measured on a specific test board (usually JEDEC 2s2p for 4-layer). If the actual design has fewer layers or smaller copper area, θJA will be worse — note this when assessing thermal adequacy.
- **Power dissipation check**: Calculate actual power dissipation from the circuit operating conditions (Vin, Vout, Iload for regulators; RDS(on) × I² for MOSFETs) and verify the thermal design can handle it. Flag when junction temperature exceeds the datasheet's maximum rating with margin.

### Decoupling Requirements

- **Capacitor values**: Many ICs specify minimum and maximum input/output capacitance, ESR range, and capacitor type (ceramic vs tantalum). Verify the schematic values match and that the PCB places them within the datasheet's maximum allowed distance.
- **Placement distance**: Some datasheets specify "place within X mm of pin Y" — check the PCB analyzer's `decoupling_placement` distances against these requirements. LDOs and high-speed switching regulators are particularly sensitive.
- **Capacitor type**: Datasheets that specify "low-ESR ceramic" or "X5R/X7R minimum" should be cross-checked against the schematic's capacitor specifications. Class II ceramics (Y5V/Z5U) lose significant capacitance under DC bias and may not meet minimum requirements.

### Keepout Zones

- **Antenna keepout**: Check the antenna manufacturer's datasheet for required copper-free area dimensions. The keepout must cover both the antenna element and a margin around it (often 5-10mm beyond the radiating element). Verify on all layers, not just the opposite layer.
- **Touch controller keepout**: Capacitive touch controller datasheets specify clearance requirements for sensor pads, guard rings, and routing. Cross-reference pad layout against the controller's application note.
- **Sensitive analog**: High-resolution ADCs and precision references often specify keepout zones or restricted routing areas near analog input pins. Check for digital traces routed under or near these components.

### Component-Specific Layout Rules

- **Crystal oscillator**: Datasheet specifies load capacitance; the PCB layout affects stray capacitance (typically 1-5pF). Route crystal traces short and direct, with ground guard if specified. Some crystals require no traces routed under the crystal body.
- **Switching regulator power loop**: The hot loop (input cap → high-side switch → inductor → output cap → input cap return) must be minimized. Measure the loop area from the PCB layout and flag if the input capacitor is placed far from the IC or the inductor return path is indirect.
- **USB impedance**: USB 2.0 requires 90Ω differential impedance; USB 3.x requires 85Ω. Verify trace width and spacing against the board stackup using the impedance parameters from the setup section. Check that D+/D- traces are length-matched per the USB spec tolerance.
- **Exposed pad connection**: ICs with exposed thermal/ground pads (QFN, DFN, QFP-EP) require the pad to be soldered to the PCB. Verify the footprint has the pad connected to the correct net (usually GND) and has adequate thermal vias. A floating or poorly-connected exposed pad is both a thermal and electrical failure.
