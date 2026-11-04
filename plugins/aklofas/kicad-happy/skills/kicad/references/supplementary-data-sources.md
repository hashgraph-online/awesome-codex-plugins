# Supplementary Data Sources

When `analyze_schematic.py` returns incomplete data — typically for legacy KiCad 5 `.sch` projects where some `.lib` files are missing from the repo — use these additional project files to recover full analysis capability.

For analyzing external PDF schematics (manufacturer reference designs, eval boards, application notes) as a primary input source, see `pdf-schematic-extraction.md`.

## Table of Contents

1. [When You Need Supplementary Data](#when-you-need-supplementary-data)
2. [Netlist File (.net)](#netlist-file-net)
3. [Cache Library (-cache.lib)](#cache-library--cachelib)
4. [PCB Cross-Reference](#pcb-cross-reference)
5. [PDF Schematic Exports](#pdf-schematic-exports)
6. [Combined Workflow for Legacy Designs](#combined-workflow-for-legacy-designs)

---

## When You Need Supplementary Data

The schematic analyzer supports both formats with pin-level analysis:

| Format | Components | Nets | Pin-to-Net | Signal Analysis | Subcircuits |
|--------|-----------|------|-----------|----------------|-------------|
| Modern `.kicad_sch` (KiCad 6+) | Full | Full | Full | Full | Full |
| Legacy `.sch` (KiCad 4/5) | Full | Full | Near-full* | Near-full* | Near-full* |

\* The legacy analyzer parses `.lib` files (cache libraries, project libs, and built-in fallbacks for common symbols) to populate pin data. Coverage is typically 92–100% depending on which `.lib` files are available in the repo. Components whose `.lib` files are missing won't have pin data.

**Indicators that you may need supplementary sources:**
- Some components in the output have empty `pins` arrays
- Standard KiCad system library symbols (uncommon symbols from `power`, `device`, `conn` beyond R/C/L/D/LED/transistors) lack pin data
- Component inventory looks complete but specific ICs are missing from signal analysis

---

## Netlist File (`.net`)

**The most valuable supplementary source when `.lib` files are incomplete.** A KiCad 5 netlist export provides explicit pin-to-net mapping for all components, filling gaps where `.lib` files are missing from the repo.

### Finding the Netlist

Look for a `.net` file in the project directory, named after the project (e.g., `myboard.net`). Generated via KiCad 5's `Tools → Generate Netlist`. Not all projects have one — it's an optional export step.

### Netlist Structure

```
(export (version D)
  (components
    (comp (ref U1)
      (value STM32F407ZGTx)
      (footprint Package_QFP:LQFP-144_20x20mm_P0.5mm)
      (libsource (lib MCU_ST_STM32F4) (part STM32F407ZGTx) (description "..."))
      (sheetpath (names /) (tstamps /))
      (tstamp HEXID)
    )
    ...
  )
  (nets
    (net (code 1) (name GND)
      (node (ref U1) (pin 12))
      (node (ref C1) (pin 2))
      (node (ref R5) (pin 1))
    )
    (net (code 2) (name +3V3)
      (node (ref U1) (pin 100))
      (node (ref U1) (pin 28))
      (node (ref C3) (pin 1))
    )
    ...
  )
)
```

### What the Netlist Provides

| Data | How to Extract | Analysis Use |
|------|---------------|-------------|
| Pin-to-net mapping | `(node (ref U1) (pin 12))` in each `(net ...)` | Which pin of which component connects to which net |
| Complete net list | All `(net (code N) (name "..."))` entries | Every named and unnamed net in the design |
| Pin-level connectivity | All `(node ...)` entries per net | Full connectivity graph for subcircuit detection |
| Component verification | `(comp ...)` entries with ref, value, footprint | Cross-check against schematic analyzer output |

### Parsing the Netlist

The netlist is S-expression format — use the skill's `kicad_core/sexp.py`:

```python
from kicad_core.sexp import parse_file, find_all, find_first, get_value

tree = parse_file('project.net')
export = tree  # Root is the (export ...) node

# Extract component list
components = find_all(find_first(export, 'components'), 'comp')
for comp in components:
    ref = get_value(comp, 'ref')
    value = get_value(comp, 'value')
    footprint = get_value(comp, 'footprint')

# Build pin-to-net map
nets = find_all(find_first(export, 'nets'), 'net')
pin_net_map = {}  # (ref, pin) -> net_name
for net in nets:
    net_name = get_value(net, 'name')
    for node in find_all(net, 'node'):
        ref = get_value(node, 'ref')
        pin = get_value(node, 'pin')
        pin_net_map[(ref, pin)] = net_name
```

With this map, you can perform the same subcircuit detection as the modern analyzer: find voltage dividers by checking shared nets between resistor pairs, identify regulator topologies by tracing VIN/VOUT/FB pin connections, etc.

### Limitations

- Netlist files are snapshots — they may be stale if the schematic was edited after the last export
- Pin numbers in the netlist use the **symbol** pin numbering, which may not match physical pad numbering if the symbol library has errors
- Unnamed nets get auto-generated names like `Net-(U1-Pad12)` that differ between exports

---

## Cache Library (`-cache.lib`)

KiCad 5 projects include a `-cache.lib` file containing embedded copies of all symbol definitions used in the project. **The analyzer now parses cache libraries automatically** — this section documents the format for cases where you need to manually inspect or supplement the data.

### Finding the Cache Library

Look for `<project-name>-cache.lib` in the project directory. It's auto-generated by KiCad 5 and should always exist alongside a `.sch` file. The analyzer checks for this file first and uses it as the preferred source of pin data.

### Cache Library Structure

```
EESchema-LIBRARY Version 2.4
#
# STM32F407ZGTx
#
DEF STM32F407ZGTx U 0 20 Y Y 9 L N
F0 "U" ... reference
F1 "STM32F407ZGTx" ... value
F2 "Package_QFP:LQFP-144_20x20mm_P0.5mm" ... footprint
DRAW
...graphics...
X PA0 34 -1600 900 200 R 50 50 1 1 B      ; Pin definition
X PA1 35 -1600 800 200 R 50 50 1 1 B      ; X name number x y length orient sizeN sizeP unit convert type
...
ENDDRAW
ENDDEF
```

### Pin Definition Fields

The `X` lines define each pin:

```
X <name> <number> <x> <y> <length> <orientation> <sizeN> <sizeP> <unit> <convert> <type>
```

| Field | Example | Meaning |
|-------|---------|---------|
| name | `PA0`, `VDD`, `BOOT0` | Pin function name |
| number | `34`, `100` | Physical pin number (should match footprint pad) |
| unit | `1`-`N` | Which unit of a multi-unit symbol |
| type | `B`, `I`, `O`, `P`, `W`, `w`, `U` | Electrical type |

**Pin electrical types:**
| Code | Type | Description |
|------|------|-------------|
| `I` | Input | Logic input |
| `O` | Output | Logic output |
| `B` | Bidirectional | I/O, GPIO |
| `T` | Tri-state | Tri-state output |
| `P` | Passive | Resistor, capacitor |
| `W` | Power input | VDD, GND (power consumer) |
| `w` | Power output | Regulator output |
| `U` | Unspecified | Unknown function |
| `C` | Open collector | Requires pull-up |
| `E` | Open emitter | Requires pull-down |
| `N` | Not connected | NC pin |

### Analysis Uses

1. **Verify pin definitions**: Cross-reference pin numbers and names against the IC datasheet. Library pin mapping errors (symbol pin numbers not matching physical footprint pads) are a common source of manufacturing defects.

2. **Identify pin functions**: Pin names like `VIN`, `VOUT`, `FB`, `EN`, `SW`, `SDA`, `SCL` help classify component functions when the analyzer can't auto-detect them.

3. **Multi-unit verification**: Count `X` lines per unit number to verify all units of multi-unit symbols (quad op-amps, MCU pin banks) have the correct pins.

4. **Power pin identification**: Pins with type `W` (power input) tell you which pins need decoupling caps. Pins with type `w` (power output) identify regulator output pins.

---

## PCB Cross-Reference

When schematic analysis is incomplete, the PCB file provides an independent source of truth for net assignments — because PCB footprints use the physical pad numbering from the datasheet.

### Cross-Reference Workflow

1. Run `analyze_pcb.py` on the `.kicad_pcb` file
2. For each component, compare the PCB's pad-to-net assignments against:
   - The schematic analyzer's component list (same refs, same values?)
   - The netlist file's pin-to-net map (same pin→net associations?)
   - The cache library's pin definitions (pin numbers match pad numbers?)

### What Mismatches Reveal

| PCB Data | Schematic Data | Problem |
|----------|---------------|---------|
| Pad 3 = `+3V3` | Pin 3 = `GND` | **Library pin mapping error** — symbol pin numbers don't match footprint pads |
| Pad exists, net assigned | Component missing from schematic | Schematic out of sync with PCB |
| Component on PCB | Component has `(dnp yes)` in schematic | DNP not cleaned up, or intentional |
| Pad has net | Pin appears unconnected in netlist | Netlist is stale |

### Key PCB Fields for Cross-Reference

From `analyze_pcb.py` output, each footprint includes:
- `reference` — component designator (should match schematic)
- `value` — component value (should match schematic)
- `pads[].net_name` — net assigned to each pad
- `pads[].number` — pad number (physical pin number from datasheet)
- `sch_path` — UUID linking back to the schematic symbol
- `sheetname` / `sheetfile` — source schematic sheet

### Library Error Detection Pattern

The most dangerous bugs are library pin mapping errors. Detect them by:

1. From the cache library: build map of `(pin_name, pin_number)` for each component
2. From the netlist: build map of `(ref, pin_number) → net_name`
3. From the PCB: build map of `(ref, pad_number) → net_name`
4. For each component, verify that the netlist's pin_number→net matches the PCB's pad_number→net for the same physical pin

If pin N in the netlist connects to net A, but pad N in the PCB connects to net B, the symbol library has a pin mapping error.

---

## PDF Schematic Exports

If the project includes a PDF export of the schematic (or if you can visually compare against KiCad's schematic viewer), use it for visual verification of circuit topology.

### When PDF Helps

- **Confirming connections**: When the analyzer output is ambiguous about how components connect, the visual schematic makes it clear
- **Tracing signal paths**: Follow wires visually from IC pin to passive component to connector
- **Verifying design intent**: Designer annotations, notes, and layout on the schematic reveal what the circuit is supposed to do
- **Catching parser errors**: If the analyzer reports something that looks wrong, the PDF shows whether the schematic actually has that connection

### How to Use

Read the PDF pages (using page range selection if available), then correlate visual observations with the analyzer output. Focus on:
1. Key IC connections (power, signal, control pins)
2. Subcircuit boundaries (which passives belong to which IC)
3. Net labels and power symbols
4. Any designer annotations or notes

For comprehensive PDF schematic analysis techniques (when the PDF is the primary input, not just a supplement), see `pdf-schematic-extraction.md`.

---

## Combined Workflow for Legacy Designs

When working with a KiCad 5 legacy project, the analyzer handles most of the work automatically:

### Step 1: Run the schematic analyzer

```bash
python3 <skill-path>/scripts/analyze_schematic.py project.sch
```

The analyzer automatically parses `.lib` files (cache libraries and project libs), populates pin data, builds pin-to-net mapping, runs signal analysis, and detects subcircuits. Check the output for components with empty `pins` arrays — these are the ones missing `.lib` data.

### Step 2: Parse the netlist (if needed)

If some components lack pin data (their `.lib` files aren't in the repo), look for `project.net` in the project directory. Parse it to get explicit pin-to-net mapping for those components (see parsing instructions above).

### Step 3: Cross-reference with PCB

Run `analyze_pcb.py` on the `.kicad_pcb` file. Compare pad-to-net assignments against the analyzer's pin-to-net data to catch library pin mapping errors.

### Step 4: Visual verification (optional)

If a PDF export exists, use it to spot-check critical connections and verify your understanding of the circuit topology.

### Data Recovery Matrix

| Supplementary Source | What It Recovers | Priority |
|---------------------|-----------------|----------|
| Netlist (`.net`) | Pin-to-net mapping for components missing `.lib` data | **Highest** — fills remaining gaps |
| PCB (`.kicad_pcb`) | Pad-to-net verification, library error detection | Medium — cross-check, not primary source |
| PDF export | Visual circuit topology verification | Low — supplement, not data source |
