# Manual Schematic Parsing (Script Fallback)

When `analyze_schematic.py` fails (unsupported format, newer KiCad version, corrupted file), fall back to direct file parsing. This is more expensive (reading raw S-expressions) but always works as long as the file is valid KiCad.

## Table of Contents

1. [When to Use Manual Parsing](#when-to-use-manual-parsing)
2. [File Format Quick Reference](#file-format-quick-reference)
3. [Component Extraction](#component-extraction)
4. [Net Building](#net-building)
5. [Signal Analysis Patterns](#signal-analysis-patterns)
6. [Legacy .sch Format](#legacy-sch-format)
7. [Validation Methodology](#validation-methodology)

---

## When to Use Manual Parsing

Use manual parsing when:
- `analyze_schematic.py` crashes or returns 0 components on a file you know has content
- The schematic is from a KiCad version newer than the script supports
- You need to validate script output against raw file data
- The file is partially corrupt but still readable

Always try the script first — it handles coordinate transforms, multi-unit symbols, hierarchical sheets, and net building automatically.

---

## File Format Quick Reference

### Modern `.kicad_sch` (KiCad 6+)

S-expression format. Key sections in order:

```
(kicad_sch (version N) (generator ...) (uuid ...)
  (lib_symbols ...)        ; Library symbol definitions (pin data, shapes)
  (junction ...)           ; Wire junction points
  (no_connect ...)         ; Explicit no-connect markers
  (wire ...)               ; Wire segments (coordinate pairs)
  (label ...)              ; Local net labels
  (global_label ...)       ; Cross-sheet net labels
  (hierarchical_label ...) ; Sheet-to-sheet pin labels
  (symbol ...)             ; Placed component instances
  (sheet ...)              ; Sub-sheet references (hierarchical designs)
)
```

### Legacy `.sch` (KiCad 4/5)

Line-based format. Key block types:

```
EESchema Schematic File Version N
$Comp / $EndComp          ; Component blocks
Wire Wire Line / x1 y1 x2 y2  ; Wire segments
Text Label / Text GLabel   ; Labels
NoConn ~ x y              ; No-connect markers
$Sheet / $EndSheet         ; Sub-sheet references
```

---

## Component Extraction

### Modern Format

Each placed component is a `(symbol ...)` block after the `(lib_symbols)` section:

```lisp
(symbol (lib_id "Device:R") (at 152.4 176.53 90) (unit 1)
  (property "Reference" "R13" ...)
  (property "Value" "10k" ...)
  (property "Footprint" "Resistor_SMD:R_0402_1005Metric" ...)
  (property "Datasheet" "~" ...)
  (pin "1" (uuid ...))
  (pin "2" (uuid ...))
)
```

**Extract for each component:**
- `lib_id` — library:symbol name
- `at` — placement position (X, Y, rotation angle)
- `unit` — which unit of a multi-unit symbol (1-based, e.g., LM324 unit 1-4 + power unit 5)
- Properties: Reference, Value, Footprint, Datasheet, MPN, Manufacturer, etc.

**Filtering:**
- Skip power symbols: `lib_id` contains `:power:` or the lib_symbol has a `(power)` flag
- Skip power flag markers: Reference starts with `#PWR` or `#FLG`
- Respect DNP: check for `(dnp yes)` attribute or `"DNP"` property

**Multi-unit symbols (critical):**
Symbols like LM324 (quad op-amp), STM32 (multi-bank MCU), dual inductors, relays — each unit is a separate `(symbol ...)` placement sharing the same Reference. Count unique References for BOM, not placements.

The `lib_symbols` section contains sub-symbols named `SymName_U_V` where U = unit number. `_0_1` sub-symbols contain pins shared by ALL units (typically power pins).

### Legacy Format

Components are in `$Comp`/`$EndComp` blocks:

```
$Comp
L library:SymbolName Reference
U unit_number convert_num timestamp
P x y
F 0 "R1" ...          ; Reference
F 1 "10k" ...         ; Value
F 2 "footprint" ...   ; Footprint
F 3 "datasheet" ...   ; Datasheet
F 4 "custom" ...      ; Custom field (MPN, Manufacturer, etc.)
    1    x y
$EndComp
```

**Custom fields (F4+):** May contain MPN (`manf#`, `MPN`, `MFG Part`), Manufacturer (`Manufacturer`, `MFG`), distributor part numbers (`DigiKey`, `Mouser`, `LCSC`), or DNP flag.

---

## Net Building

### Coordinate-Based Union-Find (Modern Format)

KiCad schematics don't store netlists — connectivity is implicit through coordinate matching. Build nets by:

1. **Extract all wire endpoints** from `(wire (pts (xy X1 Y1) (xy X2 Y2)))` blocks
2. **Compute absolute pin positions** for each component (see `net-tracing.md` for transforms)
3. **Union-find**: merge coordinate groups connected by wires, junctions, and shared endpoints
4. **Assign net names** from labels (local, global, hierarchical) and power symbols at group endpoints

**Critical rules:**
- **Y-axis inversion**: `absolute_Y = symbol_Y - pin_Y` (not `+`)
- **Sheet isolation**: Each sheet has a separate coordinate space. Only global labels and global power symbols connect across sheets. Local labels are scoped to their sheet.
- **Junctions**: Wires crossing at a point only connect if there's an explicit `(junction (at X Y))`. T-junctions (wire endpoint touching mid-wire) also connect.
- **Power symbols connect globally**: All instances of `GND`, `+3V3`, etc. are the same net regardless of sheet. The exception is a local power symbol (lib symbol `(power local)`), which joins only within its own sheet.

### Net Names

Nets are named by (priority order):
1. Global label name
2. Power symbol name (e.g., `GND`, `+3V3`)
3. Local label name
4. Hierarchical label name
5. Sheet pin name
6. Unnamed (auto-generated `__unnamed_N`)

### Legacy Format

Wires: `Wire Wire Line` followed by `X1 Y1 X2 Y2` on next line.
Labels: `Text Label X Y orientation 0 ~ 0 "NetName"` or `Text GLabel ...`.
No-connects: `NoConn ~ X Y`.

---

## Signal Analysis Patterns

When scripts can't detect subcircuits, look for these patterns manually in the component/net data.

### Power Regulators

**LDO pattern:** IC with pins named VIN, VOUT, GND (and optionally EN, PG, ADJ/FB). VIN and VOUT connect to different named power nets.

**Switching regulator pattern:** IC with SW/LX/PH pin connected to an inductor. May also have FB pin with voltage divider, BOOT/BST pin with bootstrap capacitor.

**Pin name variants:**
| Function | Pin names |
|----------|-----------|
| Input | VIN, VI, IN, PVIN, AVIN, INPUT |
| Output | VOUT, VO, OUT, OUTPUT |
| Feedback | FB, VFB, ADJ, VADJ (may have numeric suffix: FB1, ADJ2) |
| Switch | SW, PH, LX (may have numeric suffix: SW1, SW2) |
| Enable | EN, ENABLE, ON, ~{SHDN}, SHDN, ~{EN} |
| Bootstrap | BOOT, BST, BOOTSTRAP, CBST |

**Custom library detection:** If the IC has both VIN and VOUT connected to distinct recognized power nets (e.g., +5V and +3V3), it's almost certainly a regulator even without keyword matches in the library name.

### Voltage Dividers

Two resistors in series: R1_pin1→Net_top, R1_pin2→R2_pin1→Mid_net, R2_pin2→Net_bottom. The mid-point net should NOT be a power rail with many connections (that's pull-ups sharing a bus, not a divider).

`ratio = R_bottom / (R_top + R_bottom)`

### Op-Amp Circuits

Look for ICs with `+IN`/`IN+`, `-IN`/`IN-`, `OUT` pins (or bare `+`, `-`, `~` pin names for KiCad standard library op-amps).

**Multi-unit op-amps (LM324, TL082, etc.):** Each unit has its own +IN/-IN/OUT pins with different pin numbers. When analyzing manually, check the `lib_symbols` section for `SymName_N_1` sub-symbols to identify which pins belong to which unit.

**Configurations:**
- **Buffer**: OUT connected directly to -IN
- **Inverting**: Feedback R from OUT to -IN, input R to -IN, +IN to reference/ground
- **Non-inverting**: Feedback R from OUT to -IN, +IN to signal, -IN to ground via R
- **Comparator/open-loop**: No feedback resistor from OUT to -IN

**Common false positives:**
- Current sense amps (INA180/181/185/186/190/199): Have IN+/IN- pins but are fixed-gain, not user-configurable op-amps
- Digital power monitors (INA219/226/229): Have I2C interface, not analog op-amp pins
- Analog front-ends (AD8233): Complex ICs with internal op-amps that don't follow standard topology

### Transistor Circuits

**N-channel MOSFET:** Look for Q references with `NMOS`/`N-Channel` in lib_id or ki_keywords. Gate→drive signal, Drain→load, Source→GND (low-side switch).

**P-channel MOSFET:** `PMOS`/`P-Channel` in lib_id or ki_keywords. Source→power rail, Drain→load, Gate→control (inverted logic). Used as high-side switches.

**Reliable P-channel detection (priority order):**
1. `ki_keywords` from lib_symbol containing "P-Channel" — most reliable
2. lib_id containing `pmos`, `p-channel`, `q_pmos`
3. Value containing unambiguous P-channel family names (DMP series from Diodes Inc)

**Bridge circuits:** Look for transistor pairs where one drain connects to another's source (half-bridge mid-point). Two such pairs = H-bridge. Three = 3-phase.

### Protection Devices

TVS/ESD diodes: Keywords `TVS`, `ESD`, `PESD`, `PRTR`, `USBLC`, `SMAJ`, `SMBJ`, `LESD` in value or lib_id. Connected between signal line and ground/power.

ESD protection ICs: `USBLC6`, `PRTR5V`, `SP0502`, `TPD4E05` etc. Multi-channel protection arrays.

### Bus Detection

**I2C:** Nets named `SDA`/`SCL` (or containing these substrings), or IC pins named `SDA`/`SCL`. Look for pull-up resistors (2.2k-10k) to VCC. Exclude `SCLK`/`SCK` pins (SPI, not I2C).

**SPI:** Nets named `MOSI`/`MISO`/`SCK`/`CS` or `COPI`/`CIPO`/`SCK`/`CS`.

**UART:** Nets named `TX`/`RX`/`TXD`/`RXD` (exclude nets also containing `CAN`, `SPI`, `I2C`).

**CAN:** Nets named `CANH`/`CANL` or CAN transceiver ICs (MCP2551, SN65HVD230, TJA1050, etc.). Don't confuse with RS-485 (SN65HVD75 is RS-485, not CAN).

---

## Legacy .sch Format

### What the Analyzer Provides

The analyzer now parses `.lib` files (cache libraries and project libs) to populate pin data for legacy schematics. When `.lib` files are available:

- All component references, values, footprints, lib_ids
- Pin positions, pin names, and pin types (from `.lib` files)
- Pin-to-net mapping via wire connectivity + pin positions
- Signal analysis (voltage dividers, regulators, op-amp circuits, etc.)
- Subcircuit detection (IC + 1-hop neighbors)
- Net names from labels, power symbols, and pin associations
- Custom properties (F4+ fields: MPN, manufacturer, distributor PNs)

### Remaining Limitations

- **Pin coverage depends on `.lib` availability** — components whose `.lib` files aren't in the repo (standard KiCad system libs like `power`, `device`, `conn`) use built-in fallbacks for common symbols (R, C, L, D, LED, transistors). Uncommon standard library symbols may lack pin data.
- **No ki_keywords** — P-channel detection relies on lib_id and value only

### Hierarchical Legacy Designs

Top-level `.sch` has `$Sheet` blocks with `F1 "subsheet.sch"` pointing to sub-sheet files. Parse all sub-sheets. Hierarchical labels in sub-sheets connect to pins on the sheet block in the parent.

---

## Validation Methodology

When verifying analyzer output (or your own manual parse) against the raw schematic:

### Component Count Validation

1. Count all `(symbol (lib_id ...))` blocks after `(lib_symbols)` section
2. Leave out power symbols and power flags (`#PWR`, `#FLG` references)
3. Count each reference once: the units of a multi-unit part (U1A, U1B) are one component
4. The result should match the analyzer's `statistics.total_components`

### Net Count Validation

1. Count all `(wire ...)` blocks to verify wire count
2. The number of unique named nets should match approximately (unnamed nets may differ in grouping)
3. Spot-check 3-5 specific nets by tracing pins → wires → labels manually

### Signal Analysis Validation

For each detected subcircuit:
1. Verify the component IS what the analyzer says (check lib_id, value)
2. Verify the pin connections are as reported (trace through nets)
3. Check for false positives: is this detection actually correct?
4. Check for false negatives: are there obvious subcircuits the analyzer missed?

**Severity guide:**
- **HIGH**: Wrong component data (extraction bug) or grossly incorrect detection
- **MEDIUM**: Misleading detection (regulator classified wrong topology, wrong gain)
- **LOW**: Minor cosmetic issue (missing unit number, suboptimal configuration label)

### Known Edge Cases

- **Custom libraries**: Components from project-specific libraries may lack keywords that standard KiCad libraries have. Regulators, op-amps, and transistors from custom libs may not be detected.
- **Multi-unit symbols**: LM324 (quad op-amp), dual inductors, relays — each unit needs separate analysis. Pin numbers are unit-specific.
- **Unit-0 shared pins**: In KiCad lib_symbols, `_0_1` sub-symbols contain pins shared by all units (typically power: VCC, GND). These must be included with every placed unit.
- **Rescue libraries**: KiCad creates `*-rescue` libraries during migration. Check for `lib_prefix == "power"` exactly, not substring match (e.g., `dc-power-supply-rescue` is NOT a power library).
- **Eagle .sch files**: Not KiCad format — will output 0 components. These are XML or binary and require separate tools.
