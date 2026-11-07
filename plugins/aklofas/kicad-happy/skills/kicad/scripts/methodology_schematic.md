# Schematic Analyzer — Methodology

This document describes the analysis methodology used by `analyze_schematic.py` and its supporting modules. It covers the parsing pipeline, net-building algorithm, component classification heuristics, signal path detection, and design analysis checks in enough detail to understand what the analyzer does, why, and where it makes trade-offs.

## Design Philosophy

The analyzer is a **data extraction layer**, not a design rule checker. It outputs structured JSON containing neutral observations about circuit topology, component relationships, and design patterns. An LLM (or human reviewer) consumes this JSON alongside component datasheets to perform higher-level design review.

This means the analyzer:
- Reports what it finds, not what it thinks is wrong
- Avoids opinionated warnings in favor of factual observations
- Prioritizes completeness (extract everything) over filtering (show only problems)
- Casts a wide net for detection, but reported facts must be accurate — an undetected circuit is a blind spot for the reviewer; an incorrectly reported one is misinformation. Both are costly when PCB orders are at stake, so detectors favor thorough matching while keeping the reported values, connections, and classifications precise

## Architecture Overview

```
.kicad_sch file(s)
       |
       v
  kicad_core/sexp.py      Parse S-expressions into nested Python lists
       |
       v
  analyze_schematic.py     Multi-sheet recursive descent, extraction, analysis
   |       |       |
   v       v       v
kicad_core/     kicad_types.py  signal_detectors.py
(classification,  (AnalysisContext    (21 circuit pattern
 value parsing,    shared state)       detectors)
 net name rules)
       |
       v
  Structured JSON output
```

### Module Responsibilities

| Module | Role |
|--------|------|
| `kicad_core/sexp.py` | Generic S-expression tokenizer and parser. No KiCad-specific knowledge. |
| `kicad_core/` | Component classification (`classify.py`), engineering value parsing (`values.py`), power/ground net name detection (`netnames.py`). Stateless utility functions. |
| `kicad_types.py` | `AnalysisContext` dataclass — shared state built once and passed to all analysis functions. Holds components, nets, pin-net map, pre-computed lookups. |
| `signal_detectors.py` | 21 detector functions + 2 shared helpers. Each identifies a specific circuit pattern (voltage dividers, RC filters, regulators, etc.) from the connectivity graph. |
| `analyze_schematic.py` | Orchestrator. Handles file parsing, multi-sheet traversal, net building, BOM generation, and all analysis functions not in signal_detectors. Assembles the final JSON output. |

---

## 1. S-Expression Parsing

KiCad stores schematics in a Lisp-like S-expression format:

```lisp
(kicad_sch (version 20231120) (generator "eeschema")
  (symbol (lib_id "Device:R") (at 100 50 0)
    (property "Reference" "R1" ...)
    (property "Value" "10k" ...)
    (pin "1" (at 0 -1.27) ...)
    (pin "2" (at 0 1.27) ...)))
```

The parser (`kicad_core/sexp.py`) converts this to nested Python lists:

```python
["kicad_sch", ["version", "20231120"], ["generator", "eeschema"],
  ["symbol", ["lib_id", "Device:R"], ["at", "100", "50", "0"],
    ["property", "Reference", "R1", ...],
    ["property", "Value", "10k", ...], ...]]
```

**Key design decision**: All values are strings. The parser performs no type coercion, no schema validation, and no KiCad version-specific handling. This makes it robust across KiCad 5–10 format changes. Callers convert to `float`/`int` as needed.

Helper functions (`find_all`, `find_first`, `find_deep`, `get_value`, `get_property`) provide structured traversal of the parse tree without requiring callers to write index-based list access.

---

## 2. Multi-Sheet Parsing

KiCad schematics can span multiple `.kicad_sch` files in a hierarchy. The root sheet references sub-sheets via `(sheet ...)` blocks, each with a UUID.

### Traversal

The analyzer uses breadth-first traversal starting from the root sheet:

1. Parse the root file. Extract `(sheet ...)` blocks to find sub-sheet file paths and instance UUIDs.
2. For each sub-sheet, queue `(file_path, instance_path)` pairs.
3. Parse each sheet file once per instance. A single `.kicad_sch` file may be instantiated multiple times (e.g., three identical half-bridge phases) — each gets its own instance UUID and reference remapping.
4. Track `(file_path, instance_path)` pairs to prevent re-parsing the same instance.

### Multi-Instance Support

When a sub-sheet is instantiated multiple times, each symbol in it has per-instance reference assignments:

```lisp
(instances
  (project "proj"
    (path "/root_uuid/instance1_uuid" (reference "Q1") (unit 1))
    (path "/root_uuid/instance2_uuid" (reference "Q3") (unit 1))))
```

The analyzer matches the current instance path to extract the correct reference designator. Some KiCad projects (especially migrated ones) store these mappings only in the root schematic's centralized `(symbol_instances)` section rather than inline — both locations are checked as fallback.

### Sheet Isolation

Every extracted element (component, wire, label, junction) is tagged with a `_sheet` index. This prevents coordinate-based net building from merging unrelated elements that happen to share the same (x, y) position on different sheets.

---

## 3. Component Extraction

Each `(symbol ...)` block in the parse tree becomes a component dict:

```python
{
    "reference": "R1",
    "value": "10k",
    "lib_id": "Device:R",
    "footprint": "Resistor_SMD:R_0402_1005Metric",
    "x": 100.0, "y": 50.0, "angle": 0.0,
    "type": "resistor",           # from classify_component()
    "pins": [...],                 # computed absolute positions
    "properties": {...},           # all KiCad properties
    "dnp": False,                  # Do Not Populate flag
    "_sheet": 0                    # sheet index for net isolation
}
```

### Pin Position Computation

Library symbols define pin positions relative to the symbol origin. The analyzer transforms these to absolute schematic coordinates:

1. Look up the component's `lib_id` in the library symbol table.
2. For multi-unit symbols, merge unit-specific pins with unit 0 (shared pins — typically power/ground).
3. Apply rotation (symbol placement angle, counter-clockwise).
4. Apply the mirror to the rotated offset: `(mirror x)` flips the Y term, `(mirror y)` the X term.
5. Apply Y-axis inversion (symbol coordinates use math-up convention; schematic coordinates use screen-down).
6. Add the component's placement offset `(at x y)`.

Worked examples, with the formulas for each angle: `references/net-tracing.md`.

This gives each pin an absolute `(x, y)` in schematic space, which is how pins connect to wires in the net-building step.

### Legacy Format Support

KiCad 4/5 `.sch` files use a line-based format with `$Comp`/`$EndComp` blocks, `Wire Wire Line` entries, and `Text Label`/`Text GLabel` markers. The analyzer has a separate parser for this format that:

- Converts coordinates from mils (1/1000 inch) to mm
- Applies the component's 2x2 orientation matrix to each library pin once, as KiCad does, and reports the placement as rotation angle and mirror flags
- Extracts labels, wires, junctions, and no-connects with their own syntax
- Parses `.lib` files (cache libraries and project libs) to populate pin positions and types
- Reads `$Sheet` blocks: each sheet pin (`F<n>` line) becomes a hierarchical connection point on the parent sheet and joins the child's hierarchical label of the same name; a sheet used more than once contributes each instance's components, with the reference from the symbol's `AR` record for that instance (the `L` reference when there is none)
- Skips a sheet that includes itself or one of its ancestors, with one `diagnostics` record
- Performs subcircuit detection via `identify_subcircuits()`

The `.lib` resolution strategy: (1) prefer `*-cache.lib` alongside the root `.sch` (self-contained), and also read the project's `sym-lib-table` libraries, so a component named `nick:Name` takes its pins from the project library ahead of the cache's `nick_Name` copy; (2) without a cache, read the `sym-lib-table` libraries, or the `LIBS:` directives searching the project directory tree; (3) use built-in defaults for common standard library symbols (R, C, L, D, LED, transistors). Only pins from the built-in defaults may be snapped to a nearby free wire end (their offsets vary between KiCad versions); pins from a parsed library stay where KiCad puts them. Coverage is typically 92–100% depending on which `.lib` files are available in the repo.

---

## 4. Net Building (Union-Find)

The net-building algorithm is the core of the analyzer. It determines which pins are electrically connected by tracing wires, labels, junctions, and power symbols.

### Algorithm: Union-Find on Sheet-Aware Coordinates

Every electrical point in the schematic is assigned a coordinate key in KiCad's internal units (100 nm):

```python
key = (sheet_index, to_iu(x), to_iu(y))   # to_iu(mm) = round(mm * 10000), half away from zero
```

The sheet index prevents cross-sheet merges. Two points join only when their keys are equal, as in KiCad; the 100 nm rounding absorbs floating-point noise in coordinates.

A standard union-find (disjoint set) data structure with path compression groups connected points into equivalence classes:

```
find(p):  path compression to root
union(a, b):  merge two sets
```

### Connection Sources (in processing order)

1. **Component pins** — Each pin's absolute position becomes a point. PWR_FLAG symbols are excluded (they are ERC-only markers with no real electrical connection).

2. **Wire endpoints** — Each wire's `(x1, y1)` and `(x2, y2)` are added as points and unioned together. Wires are also indexed in a spatial grid (5mm cells) for fast mid-wire point lookup.

3. **Labels** — Added at their placement position. A label joins every wire it lies on, at an end or mid-wire, within 1 IU (100 nm).
   - **Local labels**: Only connect within the same sheet. Keyed by `(name, sheet)`.
   - **Global labels**: Connect across all sheets. Keyed by `(name,)`.
   - **Hierarchical labels**: Connect across sheets (parent ↔ child). Keyed by `(name,)`.

4. **Power symbols** — A global power symbol crosses sheets by name; a local one (lib symbol `(power local)`) joins only within its own sheet. The symbol's pin position (not its center) is used as the connection point. Like a component pin, it joins a wire only at a wire end. PWR_FLAG symbols are excluded.

5. **Junctions** — Added and unioned with every wire they lie exactly on (0 IU).

A component pin or power symbol that lies inside a wire, between its ends, does not join it, as in KiCad.

### Mid-Wire Detection and Near Misses

Labels and junctions can sit anywhere on a wire. The analyzer tests them against the wire segments with KiCad's integer distance test (`segment_hit_iu`): within 1 IU for a label, exactly on the segment for a junction. A spatial grid index (5mm cells) makes this efficient — only wire segments in the same grid cell are tested, avoiding O(W×P) full scans.

A point that is left unjoined within 0.01 mm of another point, or within 0.05 mm of a wire, is almost certainly a drawing slip. It is not joined; it is listed in `diagnostics` as a `CoordinateNearMiss` record (at most 20 per run, then one summary record).

### Net Naming Priority

After union-find, connected groups are named by priority:
1. **Global label name** — highest priority
2. **Power symbol name** (e.g., `+3V3`, `GND`)
3. **Local label**, then **hierarchical label**, then **sheet pin** name
4. **`__unnamed_N`** — auto-generated for nets with pins but no labels

Names of equal rank resolve to the shallower sheet, then the lower full name, as KiCad does.

When multiple disconnected wire groups share the same name (e.g., two separate `GND` networks), their pins are merged into a single net entry. This matches KiCad's behavior where same-named labels create global connectivity.

### Output

```python
nets = {
    "net_name": {
        "name": "net_name",
        "pins": [
            {"component": "R1", "pin_number": "1", "pin_name": "~", "pin_type": "passive"},
            {"component": "U1", "pin_number": "14", "pin_name": "VCC", "pin_type": "power_in"},
        ],
        "point_count": 7   # total coordinate points in this net (wires + junctions + labels + pins)
    }
}
```

---

## 5. Component Classification

`classify_component()` in `kicad_core/classify.py` assigns a type string to each component based on its reference designator, library ID, and value field.

### Classification Hierarchy

The classifier applies rules in priority order — first match wins:

1. **Power flag check**: `is_power` flag set, or `lib_id` starts with `"power:"` → `"power_symbol"`

2. **Reference prefix lookup**: The reference designator prefix (letters before digits) is matched against a type map:

   | Prefix | Type | Notes |
   |--------|------|-------|
   | `R`, `RS` | `resistor` | Standard resistors, shunts |
   | `RN`, `RM`, `RA` | `resistor_network` | Arrays and networks |
   | `C` | `capacitor` | |
   | `L` | `inductor` | |
   | `D` | `diode` | Unless overridden by LED check |
   | `Q`, `FET` | `transistor` | BJTs and FETs |
   | `U`, `IC` | `ic` | Integrated circuits |
   | `J`, `P` | `connector` | Jacks, plugs, headers |
   | `SW`, `S`, `BUT` | `switch` | |
   | `Y` | `crystal` | IEC standard prefix |
   | `F`, `FUSE` | `fuse` | |
   | `K` | `relay` | |
   | `OK`, `OC` | `optocoupler` | |
   | `LED` | `led` | |
   | `FB` | `ferrite_bead` | |
   | `TP` | `test_point` | |
   | `MH`, `H` | `mounting_hole` | |
   | `JP`, `SJ` | `jumper` | Solder jumpers |
   | `#PWR` | `power_flag` | |
   | `#FLG` | `flag` | |

3. **Library/value keyword overrides**: Certain combinations override the prefix-based type:
   - `D` prefix + `"led"` in lib → `"led"` (not diode)
   - `R` prefix + `"potentiometer"` in lib → `"resistor"` (not varistor)
   - `T` prefix + `"mosfet"`/`"transistor"` in lib → `"transistor"` (not transformer)
   - Thermistor + `"fuse"`/`"polyfuse"` in lib → `"fuse"`

4. **X prefix special handling** (crystal vs. oscillator vs. connector):
   - Contains `"oscillator"` but NOT `"crystal"`/`"xtal"` → `"oscillator"` (active IC)
   - Contains known active oscillator part numbers (DSC6, Si5, SiT8, etc.) → `"oscillator"`
   - Contains `"xtal"`/`"crystal"`/`"mhz"`/`"khz"` → `"crystal"` (passive)
   - Otherwise → `"connector"`

5. **Library-based fallback**: For non-standard prefixes, keyword search through `lib_id` and `value` for terms like `thermistor`, `varistor`, `optocoupler`, `jumper`, `connector`, `switch`, `relay`, `net_tie`, `transistor`, `diode`, `fuse`, `inductor`, `capacitor`, `resistor`.

6. **Non-standard connector prefixes**: `CON`, `USB`, `MICROSD`, `UEXT`, `LAN`, `HDMI`, `EXT`, `GPIO`, `CAN`, `SWD`, `JTAG`, `ANT`, `RJ`, `SUPPLY` → `"connector"`

7. **Default**: `"other"`

### Type Taxonomy

The full set of possible type values:

```
resistor, resistor_network, capacitor, inductor, diode, led, transistor,
ic, connector, switch, crystal, oscillator, fuse, relay, optocoupler,
ferrite_bead, test_point, mounting_hole, jumper, net_tie, transformer,
thermistor, varistor, buzzer, motor, antenna, power_symbol, power_flag,
flag, other
```

---

## 6. Value Parsing

`parse_value()` converts component values in engineering notation to numeric floats.

### Supported Formats

The accepted formats, unit handling and capacitor rules are in the Value Parser table in `README.md` (this directory).

### Unparseable Values

Returns `None` for:
- Part numbers: `"FDMT80080DC"`, `"STM32F407VGT6"`
- DNP markers: `"DNP"`, `"do not place"`
- Non-numeric strings: `"NTC"`, `"PTC"`, `"ANTENNA"`
- Empty strings

**Important caveat**: The parser is generous — it extracts the first numeric-looking substring. Always check component type before using the parsed value (e.g., a transistor's `"2N3904"` might parse as `2.0` if not guarded).

---

## 7. Power Net and Ground Detection

### Power Rail Identification

A net is classified as a power rail by three methods:

**Method 1 — Power symbol registration**: Any net that has a pin from a `#PWR` or `#FLG` component is added to the `known_power_rails` set. This is authoritative — it captures whatever the designer connected via power symbols. Membership is by the net's full name: a sheet-local net `/Sheet/X` is its own net, not the rail `X`.

**Method 2 — Name heuristics** (`is_power_net_name()`): Checks the net name against common power naming conventions:

- **Exact matches**: `VCC`, `VDD`, `AVCC`, `AVDD`, `DVCC`, `DVDD`, `VBUS`, `VIO`, `VMAIN`, `VPWR`, `VSYS`, `VBAT`, `VCORE`, `VIN`, `VOUT`, `VREG`
- **Patterns**: Names starting with `+` (e.g., `+3V3`, `+5V`, `+12V`), `V` followed by digits (e.g., `V3V3`, `V1V8`)
- **Prefixes**: `VDD_*`, `VCC_*`, `VBAT_*`, `VSYS_*`, `VBUS_*`, etc.
- **Negative, decimal and prefixed rails**: `-12V`, `-5V_F`, `-BATT`, `-VIN`, `3.3V`, `1.25V_REF`, `VEE`, `VPP`, `VM`, `VNEG`, `MCU3V3`, `D+5V`. A leading `-` before anything but a voltage or a supply name (`-RESET`) is an active-low signal; a control prefix (`PWM3V3`, `PG3V3`) or a signal word after a decimal level (`3.3V_SDA`) keeps the name a signal. `VPP` and `VM` also follow the pins: an IC pin on the net and no power pin (a PIC's ~MCLR/VPP, an op-amp node `Vm`) make it a signal unless a power symbol names it.
- **Control suffixes win**: a name whose last `_` part is a control or status word (`VCC_EN`, `3V3_PG`, `VBUS_SENSE`, `PWR_ON`) is a signal about the rail, not the rail, unless the net is in the power-symbol or project power-rail set.

**Method 3 — Rails recognised by their pins** (`topology_rail_nets()`): a named net that no name rule or power symbol makes a rail is still a power net to most schematic detectors when its pins make it a supply. Every IC pin on it is a supply input (`power_in` named like a supply), a supply-named passive pin, or a power output, and a capacitor on it goes to ground. Other passive pins are allowed only beside a pin KiCad types as power (a load-switch FET drawn as an IC). A resistor to ground (a divider midpoint), `REF` in the name, or a motor-driver output keeps the net a signal, as does a bridge-named `power_out` (`OUT1` beside an `OUT2` on another net) of a part that is not a power-management IC: it is not a supply by itself. This is how `CAN_VCC_PROTECTED` or `4.5V-28V IN` become rails. These rails are not listed in `statistics.power_rails`, and `rail_voltages` reads no voltage from their names (one comes only from a regulator that drives the net or from the project config), so a PCB run given `--schematic` does not see them.

A net is considered a power net if **any** of the three methods matches, except where a check reads rails by name only (methods 1 and 2), for example current-sense detection (which sides of a shunt are supply or ground), solder-jumper detection, RS-001 (a net counts by name or by a `power_in` pin), LB-001 label aliases, the rail voltages read from net names (`rail_voltages`), the IC logic level VM-001 takes from the IC's rails, and the PP-001 rule that a name-recognised rail is always a DC rail, where a rail known only by its pins is a DC rail only if it has a source or is not AC-coupled.

### Ground Net Identification

`is_ground_name()` checks:
- **Exact matches**: `GND`, `VSS`, `AGND`, `DGND`, `PGND`, `GNDPWR`, `GNDA`, `GNDD`
- **Patterns**: Starts or ends with `GND`, starts with `VSS`

---

## 8. AnalysisContext

`AnalysisContext` (in `kicad_types.py`) is a dataclass that holds shared state built once and passed to all analysis functions. Production code builds it with `build_analysis_context(components, nets, lib_symbols, ...)`, which constructs `pin_net` and every index, so detectors never complete it themselves:

```python
@dataclass
class AnalysisContext:
    components: list[dict]          # All components across all sheets
    nets: dict[str, dict]           # Net connectivity map
    lib_symbols: dict               # Library symbol definitions
    pin_net: dict                   # (ref, pin_num) → (net_name, pin_name) map
    comp_lookup: dict[str, dict]    # {reference: component}, built by build_analysis_context
    parsed_values: dict[str, float] # {reference: numeric_value}, built by build_analysis_context
    known_power_rails: set[str]     # Power rail names, built by build_analysis_context
    ref_pins: dict[str, dict]       # {reference: {pin_num: (net_name, net_record)}}
    no_connects: list[dict]         # No-connect markers
    nq: NetlistQueries              # Net-query layer installed by build_analysis_context
    rail_by_net / rail_overrides / rail_ignore  # Rail voltages and the project's power-rail config
```

The indexes (`comp_lookup`, `parsed_values`, `known_power_rails`, `ref_pins`) are built once, so detectors don't rebuild them.

---

## 9. Signal Path Detection

The `analyze_signal_paths()` function (in `schematic/pipeline.py`) runs the 12 topology detectors of `detect_topologies`, then `reconcile_detections`, then the domain detectors and audits of `run_domain_detectors`; together they identify common analog and mixed-signal circuit patterns from the connectivity graph. Each detector is a pure function that takes `AnalysisContext` (and optionally prior detector results) and returns structured detection results.

### Execution Order and Dependencies

Detectors run in a specific order because some consume results from earlier detectors:

```
1. voltage_dividers          ← standalone
2. rc_filters                ← excludes resistors in voltage dividers
3. lc_filters                ← standalone
4. crystal_circuits          ← standalone
5. decoupling                ← standalone
6. current_sense             ← standalone
7. power_regulators          ← matches feedback dividers from (1)
8. protection_devices        ← standalone
9. opamp_circuits            ← standalone
10. bridge_circuits          ← standalone
11. transistor_circuits      ← excludes bridge FETs from (10)
12. postfilter_vd_and_dedup  ← modifies (1) using (11)
13. led_drivers              ← enriches (11)
14. buzzer_speakers          ← standalone
15. key_matrices             ← standalone
16. isolation_barriers       ← standalone
17. ethernet_interfaces      ← standalone
18. memory_interfaces        ← standalone
19. rf_chains                ← standalone
20. bms_systems              ← standalone
21. design_observations      ← reads all prior results
```

### Shared Helpers

Detectors share one netlist query method and one helper function:

- `ctx.nq.components_on_net(net_name, exclude_refs={ref})` — Returns all components connected to a net, optionally excluding some references. Used to find what else connects to a node.
- `_classify_load(ctx, net_name, exclude_ref)` — Classifies the load on a net by examining connected component types and net name keywords. Returns labels like `"motor"`, `"relay"`, `"led"`, `"speaker"`, `"resistive"`, `"capacitive"`, etc.

### Detector Details

#### 9.1 Voltage Dividers

**Pattern**: Two resistors sharing a mid-point net, with the other ends on power/ground.

**Algorithm**:
1. Index all resistors by their two nets (from `get_two_pin_nets()`).
2. For each net, find resistor pairs that share it as a common node.
3. For each pair, check if the non-shared nets are power-on-one-end and ground-or-power-on-the-other.
4. Calculate voltage divider ratio: `R_bottom / (R_top + R_bottom)`.

**Rejection filters**:
- Mid-point net has >4 pins and is a named power rail → bus, not divider output
- Either resistor is 0Ω → wire jumper, not divider
- Both non-shared nets are ground → not meaningful

**Feedback network separation**: If the mid-point net connects to an IC pin named `"FB"`, `"ADJ"`, or `"COMP"`, the divider is tagged as a feedback network and separated from generic voltage dividers.

#### 9.2 RC Filters

**Pattern**: Resistor and capacitor sharing exactly one non-power signal net.

**Algorithm**:
1. For each resistor, get its two nets.
2. For each capacitor, get its two nets.
3. Find R-C pairs sharing exactly one net that is NOT a power rail or ground.
4. Classify filter type based on grounding:
   - Capacitor's other pin to ground → **low-pass** (most common: decoupling + series R)
   - Resistor's other pin to ground → **high-pass**
   - Neither to ground → **RC-network** (coupling, etc.)

**Rejection filters**:
- Shared net only is ground → would match every R near every C
- Resistor already in a voltage divider → false positive (VD output + cap)
- Shared net has >6 pins → bus, not filter node
- R < 10Ω → likely series termination, not filter

**Cutoff frequency**: `f = 1 / (2π × R × C)`

**Parallel cap merging**: When the same resistor pairs with multiple capacitors on the same shared net, they are combined into one entry with summed capacitance.

#### 9.3 LC Filters

**Pattern**: Inductor and capacitor sharing one non-power net.

Same approach as RC filters but for L-C pairs. Computes resonant frequency: `f = 1 / (2π × √(L × C))` and characteristic impedance: `Z = √(L / C)`.

#### 9.4 Crystal Circuits

**Pattern**: Crystal with load capacitors.

1. Find all crystals (type `"crystal"`).
2. For each crystal, identify its two signal nets (non-power).
3. On each signal net, find capacitors with their other end to ground — these are load caps.
4. Compute effective load capacitance: `CL_eff = (C1 × C2) / (C1 + C2) + C_stray` where `C_stray ≈ 3pF`.

#### 9.5 Decoupling Analysis

**Pattern**: Capacitors directly between a power rail and ground.

1. Iterate all nets classified as power rails (not ground, not unnamed).
2. For each rail, find capacitors with one pin on the rail and the other on ground.
3. Group by rail. Sum total capacitance per rail.
4. Estimate self-resonant frequency per cap: `f_SRF = 1 / (2π × √(ESL × C))` where `ESL ≈ 1nH` (typical for SMD caps).

#### 9.6 Current Sense

**Pattern**: Low-value shunt resistor with sense IC.

1. Find resistors with value ≤ 0.5Ω and > 0Ω.
2. For each shunt, check both nets for connected ICs.
3. Support both 2-pin and 4-pin Kelvin sense configurations:
   - 2-pin: pins 1, 2 are the current path (sense tapped from same nets)
   - 4-pin: pins 1, 4 are current path; pins 2, 3 are Kelvin sense
4. Accept only if an IC connects to both sides of the shunt (directly or through a 1-hop filter resistor).
5. Reject if both nets are ground (bulk decoupling, not current sense).

**Calculated values**: Max current at 50mV and 100mV drop: `I = V / R_shunt`.

#### 9.7 Power Regulators

**Pattern**: IC with power conversion pins identified by name.

**Pin name scanning**: Each IC's pins are checked for keywords indicating a regulator:
- `FB`, `ADJ`, `COMP` — feedback/compensation
- `SW`, `BOOT`, `BST` — switching node / bootstrap
- `VIN`, `VOUT` — input/output power
- `EN`, `ENABLE`, `SHDN` — enable/shutdown
- `PG`, `PGOOD` — power good output
- `SS`, `SOFTSTART` — soft-start

Pin names are normalized (trailing digits stripped: `FB1` → `FB`, `SW2` → `SW`).

**Regulator type classification**:
- **LDO**: Has FB pin + ≥2 power pins, no SW/BOOT pins
- **Switching**: Has SW + BOOT pin, or SW + inductor on output net
- **Charge pump**: Has BOOST pin, no FB
- **Generic**: Has regulation pins but doesn't match a specific topology

**False positive prevention**: An IC with `SW` but no inductor on the switch net and no regulator keywords in its lib_id/value is NOT classified as a switching regulator. This prevents motor driver ICs or other switchers from being misidentified.

**Output voltage estimation**:
1. Look up the part number in `_REGULATOR_VREF` — a 150+ entry table of known regulators and their reference voltages.
2. If a feedback divider connects to the IC's FB pin, compute: `Vout = Vref × (1 + R_top / R_bottom)`.
3. If no feedback divider, check if the net name encodes a voltage (e.g., `+3V3` → 3.3V).

#### 9.8 Protection Devices

**Pattern**: Components providing ESD, overvoltage, overcurrent, or surge protection.

Identifies:
- **TVS diodes**: Diode type with `"tvs"`, `"esd"`, `"transient"` in lib_id/value
- **Varistors/MOVs**: Varistor type or `V` prefix
- **Polyfuses/PTCs**: Thermistor type with `"fuse"`, `"polyfuse"`, `"pptc"` keywords
- **ESD protection ICs**: IC type with ESD-related keywords (TI TPD series, ON Semi, etc.)
- **Series termination resistors**: R ≤ 100Ω on high-speed nets (USB, CAN, Ethernet)

#### 9.9 Op-Amp Circuits

**Pattern**: IC identified as op-amp/comparator with feedback network.

1. Identify op-amps by keywords in lib_id: `"opamp"`, `"op-amp"`, `"comparator"`, `"OPA"`, `"LM358"`, `"TL07"`, etc.
2. Find inverting and non-inverting input pins.
3. Trace feedback path from output to input.
4. Classify configuration:
   - Resistive feedback from output to inverting input → **inverting amplifier** or **non-inverting amplifier**
   - Capacitor in feedback → **integrator** or **differentiator**
   - No feedback → **comparator**
5. Calculate gain from feedback resistor ratio: `G = -Rf/Rin` (inverting) or `G = 1 + Rf/Rin` (non-inverting).

#### 9.10 Bridge Circuits

**Pattern**: 4 matched transistors in H-bridge or half-bridge topology.

1. Find transistor pairs sharing the same net (potential bridge leg).
2. Look for two legs sharing supply and return nets.
3. Identify gate/base drive signals.
4. Classify topology: full H-bridge, half-bridge, boost, or buck based on configuration.

#### 9.11 Transistor Circuits

**Pattern**: Single transistor (not part of a bridge) acting as switch or amplifier.

1. Skip transistors already matched as bridge components.
2. Identify collector/drain, emitter/source, base/gate nets.
3. Classify load type by connected components and net name keywords.
4. Detect biasing: base/gate resistor, emitter/source degeneration.
5. Classify circuit: switching (motor, relay, solenoid), LED driver, amplifier, level shifter, etc.

#### 9.12 Post-Filter and Deduplication

Cleans up voltage divider and feedback network results:
- Removes voltage dividers that are actually feedback networks (already in feedback list)
- Filters dividers whose mid-point connects to a transistor gate/base (likely bias network, not standalone divider)
- Deduplicates entries that were detected from multiple net perspectives

#### 9.13 LED Drivers

Post-processes transistor circuits to add LED-specific information when `load_type == "led"`:
- PWM control signal identification
- Multi-LED configurations
- Current limiting resistor value

#### 9.14 Buzzer/Speaker Circuits

Identifies transistors driving buzzers or speakers:
- Net name keywords: `BUZZ`, `SPK`, `SPEAK`, `BEEP`
- Connected component type matching
- Identifies frequency generation and power supply

#### 9.15 Key Matrices

Detects keyboard matrix input arrangements:
- Resistor networks (RN type) or diode arrays in row/column patterns
- Cross-references with MCU GPIO pins for matrix dimension inference

#### 9.16 Isolation Barriers

Identifies galvanic isolation components:
- **Optocouplers**: OK/OC reference prefix or keywords
- **Transformers**: TR reference or transformer type
- **Digital isolators**: IC with `"isolator"`, `"galvanic"`, `"iso"` keywords
- Verifies that the component connects to different power domains (not single-domain)

#### 9.17 Ethernet Interfaces

Detects Ethernet interface chains:
- RJ45 connector (J prefix with `"RJ45"`/`"LAN"` in value)
- Magnetics (transformer or inductor on data pins)
- PHY IC identification by known part numbers
- Differential pair and termination checks

#### 9.18 Memory Interfaces

Identifies memory ICs and their bus connections:
- Address, data, and control bus topology
- Known memory types by keywords: SRAM, DRAM, Flash, EEPROM
- Pull-up/pull-down resistors on open-drain pins (e.g., I2C EEPROM)

#### 9.19 RF Chains

Detects RF amplifier chains:
- RF amplifier keywords: `"rf_amp"`, `"mmic"`, `"lna"`, `"pa"`
- Input/output matching networks (L-C combinations)
- Bias networks and stability compensation

#### 9.20 BMS (Battery Management Systems)

Identifies battery management circuits:
- BMS IC keywords: `"bq76"`, `"MAX17"`, etc.
- Cross-references current sense results (shunt resistors)
- Cell tap voltage divider networks
- Balancing topology detection (active vs. passive)

#### 9.21 Design Observations

Meta-analysis that reads all prior detector results and generates high-level observations:
- Unusual patterns (e.g., multiple regulators with identical output voltage)
- Missing support components (e.g., regulator without compensation network)
- Statistical summaries across all detected circuits

---

## 10. Design Analysis

Beyond signal path detection, the analyzer performs several categories of design analysis.

### 10.1 Connectivity Analysis

- **Unconnected pins**: Pins not on any net and not marked with a no-connect symbol
- **Single-pin nets**: Nets with only one connected pin (likely unfinished wiring)
- **Multi-driver nets**: Multiple output-type pins driving the same net
- **Power net summary**: Per-rail listing of connected components (for power budget analysis)

### 10.2 Design Rule Analysis

**Net Classification**: Every net is tagged with a functional class based on its name:

| Class | Keywords/Patterns |
|-------|-------------------|
| `ground` | GND, VSS, AGND, DGND |
| `power` | VCC, VDD, +3V3, VBUS, etc. |
| `clock` | SCL, SCK, CLK, MCLK, XTAL, OSC |
| `data` | SDA, MOSI, MISO, UART, TX, RX |
| `high_speed` | USB, CAN, LVDS, ETH |
| `analog` | ADC, AIN, VREF, VSENSE |
| `control` | RESET, NRST, EN, ENABLE |
| `chip_select` | CS, SS, NSS, CE, SEL |
| `interrupt` | INT, IRQ, ALERT, DRDY |
| `debug` | SWD, SWCLK, JTAG, TCK, TMS |
| `config` | BOOT, TEST |
| `signal` | Everything else |

**Power Domain Mapping**: For each IC, determines which power rails it connects to. Distinguishes IO-level pins (`VDDIO`, `VIO`, `VCCA`, `VCCB`) from internal supplies (`VCC`, `VDD`) — the IO rail determines signal levels for cross-domain analysis.

**Cross-Domain Signal Detection**: Identifies signals that cross between ICs powered by different voltage rails. Filters out signals that pass through level translators.

**Bus Protocol Analysis**:
- **I2C**: Checks for pull-up resistors on SDA/SCL lines, verifies pull-up to VCC
- **SPI**: Maps chip select assignments (CS per device)
- **UART**: Pairs TX/RX lines

**Differential Pair Analysis**: Identifies USB D+/D-, CAN H/L, LVDS pairs. Checks for proper termination resistors.

**ERC-Like Checks**:
- Input-to-input conflicts (net with only input pins, no driver)
- Output-to-output shorts (multiple output pins on same net)
- Undriven inputs (input pin on a net with no output or bidirectional pin)

### 10.3 Annotation Completeness

- Duplicate reference designators
- Unannotated references (containing `?`)
- Missing reference designators

### 10.4 Label Shape Validation

Checks for label type mismatches:
- Global labels used for local connections (only on one sheet)
- Local labels that appear to need global scope (same name on multiple sheets but not connected)

### 10.5 PWR_FLAG Audit

Identifies power nets that lack a PWR_FLAG symbol. KiCad's ERC requires PWR_FLAG on nets driven only by power pins (e.g., a connector providing power) — without it, ERC reports "power pin not driven."

### 10.6 Footprint Filter Validation

Checks whether assigned footprints match the library symbol's `ki_fp_filters` patterns. Reports mismatches that may indicate wrong footprint selection.

### 10.7 Sourcing Audit

Checks component properties for manufacturing readiness:
- Missing MPN (Manufacturer Part Number)
- Missing footprint
- Components without vendor/supplier fields
- DNP (Do Not Populate) markers

### 10.8 Ground Domain Classification

Groups ground nets into domains (analog ground, digital ground, power ground, chassis ground) and maps which components connect to each domain.

### 10.9 Bus Topology Analysis

Analyzes bus wire, bus entry, and bus alias elements:
- Validates bus aliases have corresponding labels
- Checks bus entry placement and connectivity
- Resolves alias member names against actual nets

### 10.10 Wire Geometry

Analyzes physical wire routing in the schematic:
- Total wire count and total length
- Diagonal wire detection (non-orthogonal wires — unusual in schematics)
- Wire segment length statistics

### 10.11 Property Pattern Audit

- Components where `value == reference` (often indicates unset value)
- Missing or suspicious property values
- Inconsistent property naming

### 10.12 Hierarchical Label Validation

- Hierarchical labels without matching sheet pins
- Sheet pins without matching hierarchical labels
- Orphaned hierarchical connections

---

## 11. Tier 3 Analyses

Higher-level analyses that build on the core extraction and signal detection results.

### 11.1 PDN Impedance Analysis

Estimates power distribution network impedance for each rail:
- Counts bulk and decoupling capacitors per rail
- Estimates impedance at various frequencies using parallel cap model
- Identifies rails with potentially insufficient decoupling

### 11.2 Sleep Current Audit

Estimates quiescent/sleep current by examining:
- IC leakage on each rail (using typical values by IC type)
- Pull-up/pull-down resistor current: `I = V / R`
- Voltage divider bias current
- LED indicator current
- Reports per-rail and total estimated sleep current

### 11.3 Voltage Derating

Cross-references component voltage ratings (from value or part number) with rail voltages:
- Capacitor voltage rating vs. applied voltage
- Identifies components operating near their voltage limit

### 11.4 Power Budget

Estimates power consumption per rail:
- IC current draw (estimated from typical values)
- LED current
- Resistive loads
- Total power per rail

### 11.5 Power Sequencing

Identifies enable pin chains and power-good signals:
- Maps which regulators' PG outputs connect to which regulators' EN inputs
- Detects sequencing order
- Identifies regulators without sequencing control

### 11.6 BOM Optimization

Identifies consolidation opportunities:
- Multiple resistors/capacitors with similar values that could be unified
- Components with non-standard values that could use preferred values
- Package size consistency within component types

### 11.7 Test Coverage

Evaluates design testability:
- Test point placement relative to key nets
- Accessible probe points
- Nets without test access

### 11.8 Assembly Complexity

Estimates assembly difficulty:
- Component count by package type (SMD vs. through-hole)
- Fine-pitch component identification
- BGA presence
- Mixed-technology boards

### 11.9 USB Compliance

Checks USB-specific design requirements:
- D+/D- series resistors (typically 22Ω–27Ω)
- Pull-up resistor on D+ (full-speed) or D- (low-speed)
- ESD protection on USB lines
- VBUS decoupling

### 11.10 Inrush Current Analysis

Estimates inrush current at power-on:
- Total input capacitance per rail
- Identifies hot-plug scenarios (USB, connector power)
- Checks for inrush limiting (NTC thermistors, soft-start circuits)

---

## 12. BOM Generation

Components are grouped by `(value, footprint, lib_id)` tuple. Each BOM entry contains:

```python
{
    "value": "10k",
    "footprint": "Resistor_SMD:R_0402_1005Metric",
    "lib_id": "Device:R",
    "references": ["R1", "R2", "R5"],
    "quantity": 3,
    "type": "resistor",
    "mpn": "RC0402FR-0710KL",    # if present in properties
    "dnp": False
}
```

Power symbols (`#PWR`, `#FLG`) and DNP components are excluded from the BOM count but DNP components are listed separately.

---

## 13. Known Limitations

1. **Legacy `.sch` format**: Pin-level connectivity depends on the `.lib` files in the repo. Symbols found in no library fall back to a built-in table of common parts, whose pin offsets are snapped to nearby free wire ends; a symbol missing from both has no pins and joins no net.

2. **Value parsing generosity**: `parse_value()` extracts the first numeric-looking substring. A transistor's `"2N3904"` could be parsed as `2.0` if the caller doesn't check component type first. All signal detectors guard against this by checking type before using parsed values.

3. **Coordinate identity**: Points join only at identical 100 nm coordinates, as in KiCad. A point that misses another by a few micrometres is not joined; it is reported as a `CoordinateNearMiss` diagnostic (at most 20 per run) rather than silently merged.

4. **High-fanout filter rejection**: RC/LC filters on nets with >6 connections are rejected as likely buses. This may miss legitimate filters on high-fanout nets (e.g., a filter feeding multiple ICs).

5. **Regulator Vout estimation**: Uses a lookup table + heuristic sweep, not actual SPICE simulation. Accuracy depends on the part being in the lookup table or the feedback divider being properly detected.

6. **Set iteration order**: Some analyses iterate over Python sets, which have non-deterministic ordering. This can cause output field order to vary between runs for certain sections (e.g., `protection_devices`, `pwr_flag_warnings`). The data is identical when sorted.

7. **External libraries only for KiCad 5**: a `.kicad_sch` is read with its embedded `(lib_symbols)`; external `.kicad_sym` libraries are not read (KiCad embeds every used symbol when it saves). A KiCad 5 `.sch` project takes its pins from the `<project>-cache.lib`, the `sym-lib-table` or `.pro` libraries (`.lib` files), and a built-in table for common symbols.

8. **Solder jumper gates**: Voltage dividers gated by solder jumpers (where opening/closing a jumper changes the divider ratio) are not detected as conditional configurations.

9. **find_deep() false positives**: The `find_deep()` S-expression search function matches at any depth, which can return nodes from unrelated subtrees. Analysis code uses `find_all()` (direct children only) where possible and validates context when `find_deep()` is necessary.

---

## 14. Verification

The analyzer is tested against a corpus of 1,053 open-source KiCad schematics spanning KiCad 4–9, including:
- Simple single-sheet designs (< 10 components)
- Complex multi-sheet hierarchical designs (> 500 components)
- Multi-instance designs (repeated sub-sheets)
- Legacy `.sch` format files (KiCad 4/5)
- Migrated designs (KiCad 5 → 9 format)

All 1,053 schematics parse and analyze successfully (100% pass rate). A structural validation suite checks:
- Required output keys present
- Component/net counts plausible
- BOM quantities consistent with component counts
- Signal analysis sections present for modern files with components
- No absurd values (>200 entries in any signal analysis category, >500-pin nets, etc.)
