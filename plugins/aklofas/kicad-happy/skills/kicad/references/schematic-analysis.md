# Deep Schematic Analysis

Methodology for validating KiCad schematics against datasheets, common design patterns, and electrical engineering best practices. This goes far beyond ERC — it catches design errors that only a human reviewer (or a thorough AI analysis) would find.

## Table of Contents

1. [Analysis Workflow](#analysis-workflow) — Steps 1-9 including script verification and manual fallback
2. [Subcircuit Identification](#subcircuit-identification)
3. [Datasheet-Driven Validation](#datasheet-driven-validation)
4. [Design Pattern Library](#design-pattern-library)
5. [Value Computation Verification](#value-computation-verification)
6. [Error Taxonomy](#error-taxonomy)
7. [Manufacturing & Sourcing Review](#manufacturing--sourcing-review)
8. [Battery-Powered Design Considerations](#battery-powered-design-considerations)
9. [Worst-Case Tolerance Stack Analysis](#worst-case-tolerance-stack-analysis) — Combined tolerance effects on critical values
10. [GPIO Multiplexing Audit](#gpio-multiplexing-audit) — MCU pin assignment conflicts
11. [Connector Pinout Verification](#connector-pinout-verification) — Standard pinout checks
12. [Clock Tree Analysis](#clock-tree-analysis) — Clock distribution and integrity
13. [Motor Control Design Review](#motor-control-design-review) — H-bridge, bootstrap, current sense
14. [Battery Life Estimation](#battery-life-estimation) — Power budget and runtime calculation
15. [Supply Chain Risk Assessment](#supply-chain-risk-assessment) — Sole-source and obsolescence checks
16. [Report Format](#report-format)

**Fallback methodology**: If `analyze_schematic.py` fails, see [`manual-schematic-parsing.md`](manual-schematic-parsing.md) for direct file parsing instructions.

**For full design reviews:** read `report-generation.md` before writing conclusions. The report format, evidence-basis labeling, skipped-analysis disclosure, and false-positive triage expectations are part of the review method, not post-processing.

---

## Analysis Workflow

Follow this sequence for a thorough schematic review. Each step builds on the previous.

### Step 1: Run the schematic analyzer

Run `analyze_schematic.py` on the schematic file (see SKILL.md for the command). The JSON output provides:
- Component inventory grouped by type, with values, footprints, MPNs
- Full net connectivity map with pin-to-net mapping
- **Automated subcircuit detection** (in `findings[]`, filtered by `detector` field): power regulators, voltage dividers, RC/LC filters, op-amp circuits, transistor circuits, bridge circuits, protection devices, current sense, crystal circuits, feedback networks, decoupling analysis, plus domain-specific detections (RF chains/matching, BMS, Ethernet, HDMI/DVI, memory interfaces, key matrices, isolation barriers, addressable LEDs, battery chargers, motor drivers, ESD protection audit, debug interfaces, power path/load switches, ADC signal conditioning, reset/supervisor circuits, clock distribution, display/touch interfaces, sensor fusion, level shifters, audio circuits, LED driver ICs, RTC circuits, LED lighting audit, thermocouple/RTD, power sequencing validation)
- Design observations (decoupling coverage, I2C pull-ups, crystal load caps, etc.)

Use this structured data as the starting point — it replaces manual component extraction and most subcircuit identification.

**If the script fails or returns unexpected results** (0 components, crash, etc.), fall back to manual parsing. See `manual-schematic-parsing.md` for the complete fallback methodology.

**If the script returns incomplete data** (some components missing pins — typically due to `.lib` files not being available in the repo for legacy KiCad 5 projects), use supplementary project files to recover the missing data. See `supplementary-data-sources.md` for the netlist parsing and PCB cross-reference workflow.

### Step 2: Verify script output against the raw schematic

Perform thorough verification of the analyzer output against the raw schematic. This is not a quick spot-check — it's the primary defense against silent misparsing that leads to incorrect analysis.

1. **Component count**: Read the raw `.kicad_sch` file and count `(symbol (lib_id ...))` blocks in the placed symbols section (after `(lib_symbols)`). Subtract power symbols (`#PWR`, `#FLG`). Compare against the analyzer's component count — must match exactly.

2. **Complete pinout verification for ALL components**: For **every** component in the design (ICs, connectors, transistors, diodes, multi-pin passives), verify:
   - Value, lib_id, and footprint match the raw file
   - **Every pin's net assignment** matches the raw schematic (trace wires/labels from each pin position). This is the most critical check — a single swapped pin produces a non-functional board and passes DRC/ERC silently.
   - For ICs: cross-reference pin assignments against the manufacturer's datasheet pin table (not just the KiCad library). Library symbols can have wrong pin mappings.
   - Multi-unit symbols (op-amps, MCUs) list each unit separately with correct pin assignments
   - Pin count matches between the library symbol and the analyzer output
   - For transistors: verify pinout matches datasheet (SOT-23 pinout varies: BCE vs BEC vs CBE)
   - For polarized components: verify anode/cathode and +/- orientation
   - For 2-pin passives in critical positions (voltage dividers, feedback networks, filter caps): verify they connect between the correct nets

   Do not sample or limit this to "key" components. The part you skip is the one with the problem. Verify all of them.

3. **Full net tracing**: Trace all power rails and critical signal nets end-to-end through the raw file — follow wires from pin coordinates through labels and junctions. Verify the analyzer's pin list for each net is complete. Don't limit to 2-3 nets; trace every power rail and every bus.

4. **Regulator sanity**: For each detected power regulator, verify in the raw file that the component actually has VIN/VOUT (or FB/SW) pins and connects to the reported power rails. Custom-library regulators without standard keywords are a known edge case — check that the analyzer didn't miss any obvious LDOs or converters.

5. **Connector pinout verification**: For every connector, verify pin-to-net mapping against the relevant standard or mating connector. Connector pinout errors are among the most common mistakes (see Connector Pinout Verification section below).

This thorough verification catches the cases where the analyzer silently drops components, misidentifies subcircuits, or — most dangerously — reports wrong pin-to-net mappings.

**Evidence classification during Step 2:** as you verify items, keep track of which bucket each conclusion belongs to:
- datasheet-verified
- extraction-verified
- raw-file verified
- analyzer-derived
- inference-only

Do not collapse these into a generic "verified" label in the final report.

### Step 3: Review and augment subcircuit identification

The analyzer's `findings[]` array automatically identifies most subcircuits (filter by `detector` field). Review its output and augment with any subcircuits it may have missed. Spot-check a few detected subcircuits against the raw schematic — verify the components and nets are correct. Common subcircuit boundaries:
- Each voltage regulator + its input/output caps + feedback resistors = one block
- Each IC + its decoupling caps + supporting passives = one block
- Each connector + its ESD protection + filtering = one block
- Crystal/oscillator + load caps = one block
- Each LED + current-limiting resistor = one block

### Step 4: Fetch and analyze datasheets

**Datasheets are mandatory for verification — not optional reference material.** Without datasheets, you cannot confirm that the schematic's pin assignments match reality. Every IC pinout verification in Step 2 requires the datasheet's pin table as ground truth.

**Automated sync (preferred):** If the `digikey` skill is installed, run `sync_datasheets.py` on the schematic. This should have been done in the workflow's Step 3 (see SKILL.md). If not done yet, run it now:

```bash
python3 <digikey-skill-path>/scripts/sync_datasheets.py <file.kicad_sch>
```

**Check for existing datasheets:** Before downloading, look for:
- `<project>/datasheets/` with `manifest.json` (legacy name `index.json`) from a previous sync
- `<project>/docs/` or `<project>/documentation/`
- PDF files in the project directory whose names contain MPNs
- `Datasheet` property URLs embedded in the KiCad symbols (the digikey skill names them as `<MPN>_<Description>.pdf`)

**If datasheets are missing for any component:** Use these fallback methods in order:
1. Use the `Datasheet` property URL from the schematic symbol
2. Use the `digikey` skill to search by MPN and download
3. Use web search to find the manufacturer's datasheet page
4. **Ask the user** — do not silently skip verification. Tell them: "I need datasheets for [list of parts] to verify the pinout and application circuit. Can you provide them or point me to a datasheets directory?"

For each IC and active component, extract and **note the page/section numbers** for later citation:
- **Pin function table** (pin number → name → function) — this is the ground truth for pinout verification
- Absolute maximum ratings (voltage, current, temperature)
- Recommended operating conditions
- Typical/reference application circuit (note the figure number, e.g., "Figure 8-1")
- Required external components (with recommended values and the equation number, e.g., "Equation 4")
- Thermal characteristics (junction-to-ambient, power dissipation limits)

**For passives:** Individual resistor/capacitor datasheets aren't usually needed, but verify passive values against the IC datasheets that specify them. If an IC datasheet says "use 10µF X5R on VIN" and the schematic has 1µF or Y5V, that's a bug.

These references are essential for the report — every design validation claim should cite the specific datasheet section, page, figure, or equation it was checked against.

### Step 5: Validate each subcircuit

Compare the actual schematic against the datasheet's reference design. Check:
- Are all required external components present?
- Do component values match datasheet recommendations?
- Are pins connected correctly (no swaps)?
- Are optional features (enable, power-good, soft-start) handled appropriately?
- Are absolute maximum ratings respected with margin?

When a datasheet recommendation is absent or ambiguous, say so. Do not overstate confidence just because the topology looks conventional.

### Step 6: Verify computed values

For every value that derives from a formula (resistor dividers, RC filters, current limits, etc.), compute the expected result and compare to the design intent. Flag discrepancies.

### Step 7: Check cross-cutting concerns

After subcircuit validation, check system-level issues:
- Power sequencing across all regulators
- Signal level compatibility between ICs (3.3V vs 5V logic). Note: the analyzer's `cross_domain_signals` detects these, but `needs_level_shifter: False` when the only cross-domain IC is an ESD protection device (e.g., USBLC6 on USB lines — USB signaling is 3.3V regardless of VBUS rail)
- Decoupling strategy completeness
- ESD protection on all external interfaces
- Thermal budget (total power dissipation vs cooling)
- Inductive loads driven from GPIOs: buzzers/speakers/relays driven directly from GPIO without a transistor driver or flyback diode. The analyzer's `buzzer_speaker_circuits` flags `direct_gpio_drive: true` for these.
- LED driver completeness: the analyzer's transistor circuits include `led_driver` when a MOSFET drives an LED through a current-limiting resistor. Verify current levels are within LED and GPIO limits.
- Battery-powered considerations:
  - Verify battery voltage range covers the regulator's input range (including UVLO startup threshold vs minimum battery voltage). Note: the battery component type alone doesn't tell you the cell configuration (single cell vs multi-cell series) — check the footprint and schematic context.
  - Check if USB or external power can operate the device when the battery is dead (look for power-path ORing or a charging circuit)
  - Verify shutdown/quiescent current is acceptable for battery life
  - Check that EN pins on unused regulators have proper pull-down/pull-up for safe default state

### Step 8: Validate coordinate-based findings before reporting

**Any finding that relies on coordinate math (pin positions, wire tracing, no-connect matching) is error-prone and must be validated before reporting as Critical or Warning.** The most common errors:

1. **Y-axis inversion bug**: Forgetting that `absolute_Y = symbol_Y - pin_Y` (not `+`). This inverts the entire pin map and causes every pin to appear connected to the wrong net. See `net-tracing.md` for the correct transform.
2. **Label offset**: Global labels connect to pins via wires, not at pin endpoints. A label placed 5mm from a pin along a wire stub is still connected — checking only the pin coordinate will miss it.
3. **Wire extraction bugs**: KiCad 9 spreads `(wire`, `(pts`, and coordinates across multiple lines. A regex that only checks the next line will miss coordinates on line +2 or +3.
4. **Reference designator reuse**: A reference (e.g., R13) may be reused for a completely different component between schematic revisions. Always check the actual circuit context, not just the designator name.

If your coordinate-based analysis finds "critical" issues (floating pins, wrong connections) but the user says the schematic is correct, **assume your coordinate math is wrong** and re-derive from scratch with the Y-axis formula from `net-tracing.md`.

### Step 8b: Triage analyzer false positives before ranking severity

Before turning analyzer output into blockers, explicitly classify each notable finding as one of:
- real issue
- likely false positive
- expected-by-design tradeoff
- unresolved / needs more evidence

Common sources of false positives:
- RF module courtyard / antenna keepout overlaps
- intentional copper under bypass caps or local power islands
- general USB resistor heuristics that do not apply to the specific PHY
- board-edge warnings triggered by intentional antenna placement
- inferred lifecycle or sourcing warnings based on partial distributor coverage

A strong review explains why a finding was accepted, downgraded, or dismissed.

### Step 9: Produce the report

Organize findings by severity (Critical / Warning / Suggestion / Info) and by subcircuit. For each finding, show the reasoning — not just the conclusion:

- **Cite datasheet sources**: Reference the specific datasheet section, page, figure, table, or equation that supports the finding (e.g., "per TPS61023 datasheet Table 6.3, page 4: VREF = 595mV typical").
- **Show formulas**: When validating computed values (feedback dividers, RC filters, current limits), write out the equation with the actual component values substituted in (e.g., "VOUT = VREF × (1 + R_top/R_bottom) = 0.595V × (1 + 732k/100k) = 4.95V").
- **Compare against spec**: Show the design's value alongside the datasheet's recommended range so the reader can see the margin (e.g., "L = 1µH, datasheet recommends 0.37-2.9µH ✓").
- **Explain the chain of reasoning** for non-obvious issues: if something looks wrong, explain how you traced the net, what you expected to find, and what you found instead.
- **Disclose review limits**: If thermal, lifecycle, gerber, prior-review delta, or datasheet extraction work was not performed, state that explicitly in the report.
- **Separate evidence from judgment**: A finding can be well-supported and still not be a blocker. Distinguish the factual observation from the severity judgment.

---

## Subcircuit Identification

### How to identify subcircuit boundaries

Trace nets outward from each IC. The IC plus everything directly connected to its pins (within 1-2 hops) typically forms a subcircuit. Shared nets like power rails and ground are boundaries — they connect subcircuits but don't belong to any single one.

### Common subcircuit types

| Type | Key Components | Identifying Features |
|------|---------------|---------------------|
| **Linear regulator (LDO)** | Regulator IC, Cin, Cout, feedback divider (if adjustable) | IC with VIN, VOUT, GND pins; caps on input and output |
| **Switching regulator (buck/boost)** | Controller IC, inductor, diode/FET, Cin, Cout, feedback divider | Inductor in the power path, SW/LX pin |
| **Crystal oscillator** | Crystal (Y), 2 load caps | Connected to XIN/XOUT or OSC1/OSC2 pins of an MCU |
| **USB interface** | Connector, ESD diode, series resistors, decoupling | D+/D- nets, VBUS, shield/shell ground |
| **I2C bus** | Pull-up resistors, bus devices | SDA/SCL nets with pull-ups to VCC |
| **SPI bus** | Chip select resistors, bus devices | MOSI/MISO/SCK/CS nets |
| **UART** | Level shifter (if needed), connector | TX/RX nets |
| **LED indicator** | LED, current-limiting resistor | LED symbol with series resistor to GPIO or power |
| **Reset circuit** | Pull-up resistor, cap, optional supervisor IC | Connected to RESET/nRST pin |
| **Decoupling** | Ceramic cap (100nF typical), bulk cap | Connected between VCC and GND near IC |
| **ESD protection** | TVS diode array | Connected to external-facing signal lines |
| **Motor/relay driver** | MOSFET or driver IC, flyback diode | Inductive load with freewheeling diode |
| **Analog sensing** | Op-amp or ADC input, voltage divider, filter cap | Signal conditioning into ADC pin |
| **Battery management** | Charge controller IC, sense resistor, protection FET | Battery connector, charge/discharge paths |
| **Level shifting** | Level shifter IC or MOSFET + pull-ups | Bridges two different voltage domains |

---

## Using Pre-Extracted Datasheet Specs

When `datasheets/extracted/<MPN>.json` files are available (produced by the `datasheets` skill — see its `references/extraction-schema.md` for the canonical field layout), use them to accelerate pin-by-pin verification:

1. **Load the extraction** for each IC alongside the analyzer's `ic_pin_analysis` output
2. **Join on pin number** — the extraction's `pins[].number` matches the analyzer's `pins[].pin_number`
3. **For each pin, check:**
   - **Voltage compatibility:** Is the net voltage within the pin's `voltage_operating_min`/`voltage_operating_max`?
   - **Required externals:** Does the extraction's `required_external` field match what's actually connected?
   - **Power pins:** Does every VDD pin have a decoupling cap?
   - **Digital thresholds:** For digital inputs, are `threshold_high_v`/`threshold_low_v` met?
   - **NC pins:** Are pins marked as no-connect actually unconnected?
4. **Cite extraction data** in findings

Pre-extracted data is especially valuable for large designs (10+ ICs). For small designs, direct PDF reading is equally effective.

## Datasheet-Driven Validation

For each component type, here is what to extract from the datasheet and what to validate.

### Voltage Regulators (LDO and Switching)

**Extract from datasheet:**
- Input voltage range (VIN min/max)
- Output voltage (fixed or adjustable)
- Maximum output current
- Dropout voltage (LDO) or duty cycle limits (switching)
- Required input capacitor: value, ESR range, type (ceramic OK? tantalum needed?)
- Required output capacitor: value, ESR range, stability requirements
- Feedback divider formula (adjustable types): `VOUT = VREF * (1 + R_TOP/R_BOTTOM)` or similar
- Enable pin behavior (active high/low, threshold, internal pull-up/down)
- Soft-start capacitor (if applicable)
- Thermal shutdown temperature
- Power-good output (if present)

**Validate:**
- Input voltage from upstream supply is within VIN min/max range
- Output voltage matches design intent (compute from feedback divider if adjustable)
- Load current (sum of all downstream consumers) is within rated maximum, with margin
- Input cap meets datasheet requirements (value, type, voltage rating >= VIN_max * 1.5)
- Output cap meets datasheet requirements (value, ESR, voltage rating >= VOUT * 1.5)
- Enable pin is properly driven or tied (not floating)
- Power dissipation is within package thermal limits: `P = (VIN - VOUT) * ILOAD` for LDO
- For switching regulators: inductor value and saturation current meet requirements

**Common errors:**
- Output cap ESR too low or too high for regulator stability (some LDOs need ESR > 0.1 ohm)
- Input cap missing or too small — causes input voltage ringing
- Feedback divider resistors swapped (output voltage way off)
- Dropout not accounted for — LDO can't regulate when VIN - VOUT < dropout
- VOUT cap voltage rating too close to VOUT (no margin for transients)

### Microcontrollers / SoCs

**Extract from datasheet:**
- Power supply pins: all VDD/VSS pairs, analog supply (VDDA), USB supply, etc.
- Decoupling requirements per pin group
- Bulk capacitance requirements
- Crystal/oscillator requirements: frequency range, load capacitance (CL), ESR max, drive level
- Boot mode pin configuration
- Reset circuit requirements (external cap, pull-up value, minimum pulse width)
- I/O voltage levels (VIH, VIL, VOH, VOL) for each GPIO bank
- Maximum GPIO source/sink current (per pin and total)
- Special pin requirements (USB D+/D- bias, ADC reference, etc.)

**Validate:**
- Every VDD/VSS pair has a 100nF ceramic cap placed close to the pins
- VDDA has its own filtering (ferrite bead + cap, or LC filter)
- Bulk cap present on main supply (4.7uF-10uF typical)
- Crystal load caps are correct: `CL_cap = 2 * (CL_crystal - C_stray)` where C_stray ~ 2-5pF
- Boot pins are configured for the desired boot mode (not floating)
- Reset pin has proper pull-up (typically 10k) and optional 100nF cap to ground
- Unused GPIO pins are set to a known state (not floating) — either pulled up/down or marked no-connect
- Total GPIO current draw doesn't exceed chip maximum
- Signal voltage levels are compatible with connected ICs

**Common errors:**
- Missing decoupling on one VDD/VSS pair (especially on large BGA packages)
- Crystal load caps computed wrong (using CL directly instead of the formula)
- VDDA connected directly to VDD without filtering
- Boot pins floating — MCU enters wrong boot mode randomly
- ADC reference pin left unfiltered
- USB VBUS not properly handled (missing 5V tolerance, or no decoupling)

### Passive Components (Resistors, Capacitors, Inductors)

**Validate for resistors:**
- Power rating: `P = V^2 / R` or `P = I^2 * R` — must be within component's rated power with 50% derating
- Voltage rating: voltage across resistor must not exceed maximum working voltage (relevant for high-value resistors in voltage dividers off high-voltage rails)
- Tolerance is appropriate for the application (1% for feedback dividers, 5% OK for pull-ups)

**Validate for capacitors:**
- Voltage rating >= 1.5x maximum applied voltage (accounts for DC bias derating in ceramics)
- DC bias derating: MLCC capacitance drops significantly at applied voltage (a 10uF 6.3V X5R cap at 5V may only provide 3-4uF actual). For critical applications, check the manufacturer's DC bias curves.
- Dielectric type is appropriate: C0G/NP0 for precision/timing, X7R for general bypass, X5R for bulk (never Y5V for anything critical)
- Temperature range matches application
- ESR is appropriate (low ESR for bypass, may need higher ESR for LDO stability)

**Validate for inductors:**
- Saturation current >= peak current * 1.3 (derating)
- DC resistance acceptable for power loss budget
- Inductance value matches switching regulator requirements
- Shielded vs unshielded appropriate for the application (shielded preferred near sensitive circuits)

### Diodes and TVS

**Validate:**
- Forward voltage drop at operating current doesn't cause problems
- Reverse voltage rating exceeds maximum reverse voltage with margin
- For TVS: clamping voltage at peak pulse current is within protected IC's absolute max
- For Schottky (power supply): reverse leakage at temperature is acceptable
- For Zener: power dissipation = (VIN - VZ) * IZ is within rated power
- For flyback diodes: reverse voltage rating > supply voltage, forward current rating > load current

### Connectors

**Validate:**
- Pin mapping matches the cable/mating connector pinout (this is a very common error source)
- ESD protection on all external-facing signal pins
- Proper filtering on power input (bulk cap + ceramic)
- USB connectors: CC resistors for type-C (5.1k to GND for UFP/sink), D+/D- series resistors if required
- Power connectors: reverse polarity protection (Schottky, P-FET, or ideal diode)
- Debug/programming headers: confirm pinout matches the programmer (JTAG/SWD pin order varies!)

### MOSFETs

**Validate:**
- VDS rating >= maximum drain-source voltage * 1.5
- VGS rating: gate drive voltage is within VGS max and above VGS(th) with margin
- RDS(on) at actual VGS drive voltage (not the datasheet minimum test condition)
- ID rating at operating temperature (derate from 25C spec)
- Gate resistor present if needed (prevents ringing, limits di/dt)
- For P-channel high-side: gate is pulled to VCC when off, driven to GND (or lower) when on
- Gate-source pull-down/pull-up resistor to prevent floating during power-up

---

## Design Pattern Library

These are reference patterns for common subcircuits. Compare the schematic against these to detect deviations.

### LDO Voltage Regulator (Fixed Output)

```
VIN ──┬── [Cin 1-10uF] ──┬── GND
      │                    │
      └── VIN [REG] VOUT ─┬── [Cout 1-22uF] ──┬── GND
              │            │                     │
              GND ─────────┤                     │
              EN ── VIN or GPIO                  │
              PG ── pull-up to VOUT (optional)   │
                                                 └── VOUT rail
```

**Expected values:**
- Cin: 1uF minimum ceramic (often 4.7-10uF), voltage rating > VIN
- Cout: per datasheet (1-22uF typical), ESR within specified range
- EN: tied to VIN (always on) or driven by sequencing logic; never floating
- Feedback divider (adjustable): 1% resistors, bottom resistor typically 10k-100k

### Buck Converter

```
VIN ──┬── [Cin 10-22uF] ──┬── GND
      │                     │
      └── VIN [CTRL] SW ───┬── [L 1-47uH] ──┬── VOUT
              │             │                  │
              GND           [Boot cap]         ├── [Cout 22-100uF] ── GND
              FB ── divider ┘                  │
              EN                               └── VOUT rail
              COMP ── RC network (if external)
```

**Expected values:**
- L: per datasheet, saturation current > peak load current * 1.3
- Cin: low ESR ceramic, voltage rating > VIN, value per datasheet
- Cout: low ESR ceramic or polymer, value per datasheet
- Bootstrap cap: typically 100nF ceramic (for integrated FET controllers)
- Feedback divider: `VOUT = VREF * (1 + RTOP/RBOT)`, 1% resistors

### Crystal Oscillator

```
MCU_XIN ──┬── [Y1 crystal] ──┬── MCU_XOUT
           │                    │
           [CL1] ── GND        [CL2] ── GND
```

**Expected values:**
- Load cap formula: `CL1 = CL2 = 2 * (CL - Cstray)` where:
  - CL = crystal's rated load capacitance (from crystal datasheet, typically 8-20pF)
  - Cstray = stray/parasitic capacitance (typically 2-5pF for PCB + MCU pin)
- Example: crystal CL = 12pF, Cstray = 3pF → CL1 = CL2 = 2 * (12 - 3) = 18pF
- Feedback resistor (1M, optional): some MCUs require it across XIN/XOUT for startup
- Series resistor on XOUT (optional): limits drive level for low-power crystals

**Common mistakes:**
- Using the crystal CL value directly as the cap value (should be ~2x CL minus stray)
- Missing load caps entirely (oscillator won't start or runs at wrong frequency)
- Routing long traces to crystal (adds stray capacitance, picks up noise)

### USB Type-C (Device/UFP)

```
VBUS ──┬── [ESD/TVS] ──┬── 5V rail
        │                │
        [Cin 10uF]       [100nF]
        │                │
        GND              GND

CC1 ──── [5.1k] ──── GND     (identifies as UFP/sink)
CC2 ──── [5.1k] ──── GND

D+ ──── [series R 22-27 ohm] ──── MCU_DP
D- ──── [series R 22-27 ohm] ──── MCU_DN

Shield/Shell ──── GND (via 1M + 4.7nF to GND, or direct)
```

**Key checks:**
- CC1 and CC2 each have 5.1k pull-down to GND (mandatory for device mode)
- ESD protection on VBUS, D+, D-, CC lines
- Series resistors on D+/D- (some MCU USB PHYs include these internally — check datasheet)
- VBUS decoupling close to connector

### I2C Bus

```
VCC ──┬── [Rp1 2.2-10k] ──── SDA bus
      │
      └── [Rp2 2.2-10k] ──── SCL bus
```

**Expected values:**
- Pull-up resistor: `Rp_min = (VCC - VOL) / IOL` and `Rp_max = tr / (0.8473 * Cb)`
  - VOL = 0.4V, IOL = 3mA (standard), Cb = bus capacitance
- Typical values: 2.2k (400kHz fast mode), 4.7k (100kHz standard), 10k (low power)
- Only ONE set of pull-ups per bus (not per device!)
- Bus capacitance limit: 400pF (standard mode), affects maximum pull-up resistance

**Common errors:**
- Multiple pull-up pairs on the same bus (each device adding its own)
- Pull-ups to wrong voltage rail (3.3V pull-up on a 5V bus or vice versa)
- Pull-up value too high for the bus speed (rise time too slow)
- Missing pull-ups entirely (bus floats, random data)

### LED Indicator

```
GPIO ──── [R] ──── [LED] ──── GND    (active high, sourcing)
    or
VCC ──── [R] ──── [LED] ──── GPIO    (active low, sinking)
```

**Expected values:**
- `R = (VSUPPLY - VLED - VOL_or_VOH) / ILED`
- Typical: VLED ≈ 2.0V (red), 2.1V (yellow), 3.0V (green/blue/white)
- Typical: ILED = 2-5mA for indicators (not full 20mA unless brightness needed)
- Check GPIO source/sink current limit

**Worst-case overcurrent check (critical for high-brightness LEDs):**
When the supply comes from a switching regulator with tolerance, you must check LED current at the combined worst case: maximum supply voltage AND minimum LED forward voltage. This is the maximum current the LED will ever see.

1. Compute worst-case high supply: use VREF_max and resistor tolerances (see "Tolerance Stacking" below)
2. Get Vf_min from the LED datasheet (often significantly lower than typical — e.g., 2.7V min vs 3.3V typ for blue/green)
3. `I_worst = (Vsupply_max - Vf_min) / R`
4. This must be below the LED's absolute maximum current rating
5. If not, increase R until `R >= (Vsupply_max - Vf_min) / I_abs_max`, then round up to next E24 value
6. Re-verify typical current is still acceptable for desired brightness

### Reset Circuit

```
VCC ──── [R 10k] ──┬──── MCU_RESET
                     │
                    [C 100nF] ──── GND    (optional, delays reset release)
                     │
                    [Switch] ──── GND      (optional manual reset)
```

**Key checks:**
- Pull-up resistor present (10k typical, check MCU datasheet)
- Filter cap if environment is noisy (100nF typical, creates RC delay)
- If supervisor IC is used: threshold voltage matches supply rail, reset pulse width meets MCU requirement
- Open-drain reset outputs from multiple sources can be wire-OR'd

### Voltage Divider for ADC

```
VIN ──── [R_TOP] ──┬── ADC_INPUT
                     │
                    [R_BOT] ──── GND
                     │
                    [C_FILTER 100nF] ──── GND    (optional anti-alias)
```

**Expected values:**
- `V_ADC = VIN * R_BOT / (R_TOP + R_BOT)`
- V_ADC must be <= ADC reference voltage (usually VDDA)
- Total impedance (R_TOP + R_BOT) should be reasonable:
  - Too low (< 1k): wastes power, loads the source
  - Too high (> 1M): ADC sampling capacitor can't charge fast enough
  - Typical: 10k-100k total
- Filter cap: `f_cutoff = 1 / (2 * pi * R_parallel * C)` where R_parallel = R_TOP * R_BOT / (R_TOP + R_BOT)

**Source impedance and ADC accuracy:**
MCU ADCs have a sample-and-hold capacitor (typically a few pF) that must charge through the source impedance during the sampling window. If source impedance is too high, the capacitor doesn't fully settle and readings are inaccurate.

- Source impedance = `R_TOP × R_BOT / (R_TOP + R_BOT)` (parallel combination)
- Check the MCU datasheet for maximum recommended source impedance (ESP32-S3: ~13kΩ)
- If source impedance exceeds the limit, a filter capacitor (e.g., 100nF) at the ADC input helps: the cap pre-charges to the correct voltage, and the ADC samples from the cap instead of through the resistors
- Verify the RC settling time (`τ = R_parallel × C_filter`) allows sufficient settling between readings
- For battery-powered designs, balance accuracy vs sleep current: 100K/100K (50kΩ source, 15µA at 3V) is a reasonable compromise with a 100nF filter cap providing ~5ms settling

### Power Input with Reverse Polarity Protection

```
VIN ──── [F1 fuse or PTC] ──┬── [D1 Schottky] ──── VCC_PROTECTED
                              │
                              [C_BULK 10-100uF]
                              │
                              GND
```
or (lower loss, P-FET method):
```
VIN ──── [F1] ──── S [Q1 P-FET] D ──── VCC_PROTECTED
                        │
                        G ── GND (via R, optional TVS across G-S)
```

**Key checks:**
- Fuse/PTC rating matches maximum expected current with margin
- Schottky drop is acceptable at max current (or use P-FET for lower drop)
- Bulk cap voltage rating > VIN max
- P-FET VGS is sufficient to fully enhance with the given VIN

---

## Value Computation Verification

For every computed value in the schematic, verify the math. Show your work so the user can check it.

### Resistor Divider (General)

```
VOUT = VIN * R_BOTTOM / (R_TOP + R_BOTTOM)
```
Or equivalently: `R_TOP / R_BOTTOM = (VIN / VOUT) - 1`

### Regulator Feedback Divider

Different ICs use different formulas. Common patterns:
- `VOUT = VREF * (1 + R1/R2)` — R1 from VOUT to FB, R2 from FB to GND
- `VOUT = VREF * (R1 + R2) / R2` — same thing, different notation
- Always check which resistor is "top" (VOUT to FB) and which is "bottom" (FB to GND)
- VREF is from the regulator datasheet (commonly 0.6V, 0.8V, or 1.25V)

**Feedforward capacitor** (boost/buck converters): Some switching regulators recommend a small capacitor across the upper feedback resistor to add a zero that improves transient response. Formula: `C_FF = 1 / (2π × f_FFZ × R_upper)`, where f_FFZ is the target zero frequency (typically ~1kHz, per datasheet). Always verify this against the specific regulator's datasheet — not all converters benefit from feedforward.

### Tolerance Stacking for Regulator Output

Regulator output voltage has combined tolerance from VREF accuracy and feedback resistor tolerance. Always compute the full range:

```
Vout_max = VREF_max × (1 + R_upper×(1+tol) / (R_lower×(1-tol)))
Vout_min = VREF_min × (1 + R_upper×(1-tol) / (R_lower×(1+tol)))
```

Where `tol` is the resistor tolerance (0.01 for 1%). This matters because:
- Downstream components (LEDs, ICs) must tolerate the full Vout range
- The high-side voltage determines worst-case overcurrent through current-limited loads
- The low-side voltage determines whether downstream regulators have enough headroom

Example: VREF = 595mV ±2.5%, R_upper = 820K ±1%, R_lower = 110K ±1%:
- Vout_nom = 0.595 × (1 + 820/110) = 5.03V
- Vout_max = 0.610 × (1 + 828.2/108.9) = 5.26V
- Vout_min = 0.580 × (1 + 811.8/111.1) = 4.82V

Use Vout_max when checking downstream current limits. Use Vout_min when checking regulator headroom.

### Current Limiting Resistor

```
R = (V_SOURCE - V_LOAD) / I_TARGET
P_RESISTOR = (V_SOURCE - V_LOAD) * I_TARGET = I_TARGET^2 * R
```

### RC Filter Cutoff

```
f_cutoff = 1 / (2 * pi * R * C)
```
- Low-pass: R in series, C to ground
- High-pass: C in series, R to ground

### Crystal Load Capacitors

```
CL_each = 2 * (CL_crystal - C_stray)
```
Where C_stray includes PCB trace capacitance (~1-2pF) and MCU pin capacitance (~1-3pF from MCU datasheet).

### Pull-up Resistor for Open-Drain

```
R_min = (VCC - VOL_max) / IOL_max
R_max = VCC / (I_leakage * N_devices)     (rough guide)
```
For timing-critical buses (I2C), rise time constraint:
```
R_max = t_rise / (0.8473 * C_bus)
```

### MOSFET Gate Drive

Verify VGS at the actual drive voltage exceeds VGS(th) with margin:
- For logic-level FETs: VGS(th) max should be well below drive voltage
- Check RDS(on) at the actual VGS, not the minimum datasheet value
- Gate charge (Qg) determines switching speed and driver current requirement

### Voltage Divider Power Dissipation

```
P_total = VIN^2 / (R_TOP + R_BOTTOM)
P_R_TOP = P_total * R_TOP / (R_TOP + R_BOTTOM)
P_R_BOTTOM = P_total * R_BOTTOM / (R_TOP + R_BOTTOM)
```

---

## Error Taxonomy

Categorize findings by severity to help the user prioritize.

### Critical (design will not work or is unsafe)

- Absolute maximum rating exceeded (voltage, current, temperature)
- Missing essential component (no output cap on regulator, no decoupling on IC)
- Wrong pin connections (swapped pins, connected to wrong net)
- Short circuit path (power rail shorted to ground through missing component)
- Reversed polarity on polarized components without protection
- Floating power pins on ICs
- Missing ground connections
- Feedback divider gives dangerously wrong voltage (overvoltage on downstream IC)

### Warning (design may work but has significant risk)

- Component values outside datasheet recommendations
- Insufficient voltage/current rating margins (< 20% margin)
- Missing but recommended components (e.g., input cap on LDO where output is close to input)
- Pull-up/pull-down values outside optimal range (will work but may be unreliable)
- DC bias derating not accounted for (ceramic cap actual capacitance much lower than nominal)
- Thermal margin tight (power dissipation close to package limit)
- Missing ESD protection on external interfaces
- Crystal load caps slightly off (oscillator will start but frequency accuracy suffers)

### Suggestion (improvements that aren't required)

- Better component selection available (lower cost, better specs, more common)
- Value optimization (pull-up could be lower for faster bus speed)
- Additional filtering would improve performance (e.g., pi filter on analog supply)
- Test points recommended for debugging
- Consider adding power-good monitoring
- LED current could be reduced (2mA is sufficient for most indicators, saves power)
- Consider adding second-source alternatives for sole-source components

### Info (observations, not actionable)

- Component identification notes (what each subcircuit does)
- Design pattern recognition (this is a standard buck converter topology)
- Cross-references to datasheets and application notes
- Notes on KiCad-specific issues (symbol doesn't match pinout, footprint mismatch)

---

## Manufacturing & Sourcing Review

Beyond electrical correctness, check for practical manufacturing issues.

### Component Availability

- Are all parts currently in production? (check for obsolete/NRND status)
- Are any parts sole-source with long lead times?
- For JLCPCB assembly: are LCSC equivalents available for all parts?
- Are any parts unusually expensive? (suggest alternatives)

### Footprint Concerns

- Do all footprints match the actual component package?
- Are any footprints hand-solder unfriendly? (0201, QFN with no exposed pads, fine-pitch BGA)
- For prototype hand assembly: are there through-hole alternatives for difficult SMD parts?
- Are thermal pads properly handled (vias under QFN exposed pads)?

### Design for Assembly

- Are designators and polarity markers on silkscreen?
- Are pin-1 indicators consistent and visible?
- Are test points accessible?
- For mixed-voltage designs: are voltage domains clearly marked on the schematic?

### Consolidation Opportunities

- Can multiple resistor values be consolidated? (e.g., 9.8k and 10k → both 10k if tolerance allows)
- Can different cap values be consolidated to reduce BOM line count?
- Are there parts that differ only by value where a single value would work for all?
- Fewer unique parts = lower assembly cost and simpler sourcing

---

## Battery-Powered Design Considerations

For battery-powered designs, check these additional concerns beyond basic electrical correctness.

### Sleep Current Budget

Enumerate all current draws during deep sleep / low-power mode:
- MCU sleep current (from datasheet, at actual voltage and temperature)
- Voltage dividers (always-on resistive paths): `I = Vbatt / (R_top + R_bot)`
- Regulator quiescent current (if always enabled)
- Pull-up/pull-down resistors that create current paths
- Leakage through protection diodes, FETs, ESD devices
- LED indicator leakage (if any)

Sum all contributions and compute battery life:
```
Life (hours) = Battery_capacity_mAh / Total_sleep_current_mA
```
For AA alkaline: ~2500-3000 mAh usable (derate from nominal depending on drain rate and cutoff voltage).

Flag any single contributor that is >10% of the total sleep budget — it may be worth optimizing (e.g., higher-value divider resistors, FET-gated sensing circuits, lower-Iq regulator).

### Minimum Battery Voltage (Low-Battery Threshold)

Compute the minimum battery voltage at which the system can still function under peak load:

1. Identify peak current events (WiFi TX, motor drive, LED animation)
2. Look up battery internal resistance at end-of-life (AA alkaline: ~1-2Ω per cell at 1.0V)
3. Calculate voltage sag: `V_sag = I_peak × R_internal_total`
4. Check regulator minimum input voltage at peak output current (from efficiency curves, not just Vin_min spec — boost converters lose regulation when input current exceeds capability)
5. Minimum battery voltage = regulator Vin_min + V_sag + margin

This threshold should be checked in firmware before high-current operations. Going below it risks brownout, corrupted flash writes, or incomplete WiFi transmissions.

### Active Power Sequencing

Battery-powered designs often power-gate subsystems to save energy:
- Verify enable pins have pull-downs to keep regulators off during boot
- Check for inrush current when multiple regulators enable simultaneously
- Verify USB host power sequencing (if applicable — host must install before VBUS powers the device)
- Check that GPIO states during deep sleep don't create parasitic current paths (unused GPIOs should be parked as outputs driven low, with `gpio_deep_sleep_hold_en()` or equivalent)

---

## Worst-Case Tolerance Stack Analysis

Beyond individual component validation, compute how combined tolerances affect critical circuit parameters. This catches designs where each component is individually "in spec" but the combined worst case exceeds safe limits.

### General Methodology

For any computed value that depends on multiple components, substitute worst-case values simultaneously:
- Maximum output: use all component tolerances that increase the result
- Minimum output: use all component tolerances that decrease the result
- Include the IC's internal reference tolerance (VREF min/max from datasheet electrical characteristics table)

### Voltage Divider with Tolerance Stacking

The regulator feedback divider tolerance stacking formula is covered in [Tolerance Stacking for Regulator Output](#tolerance-stacking-for-regulator-output). Apply the same approach to any voltage divider — ADC scaling, level detection thresholds, comparator references:

```
V_max = VIN_max × R_bot×(1+tol) / (R_top×(1-tol) + R_bot×(1+tol))
V_min = VIN_min × R_bot×(1-tol) / (R_top×(1+tol) + R_bot×(1-tol))
```

**When to worry:** Compare the tolerance-stacked output range against downstream absolute maximum ratings. If Vout_max approaches an abs max, the design needs tighter-tolerance components or a wider safety margin.

### RC Filter Cutoff with Tolerance

Both R and C have manufacturing tolerances. The cutoff frequency range is:

```
f_max = 1 / (2π × R_min × C_min) = 1 / (2π × R×(1-tol_R) × C×(1-tol_C))
f_min = 1 / (2π × R_max × C_max) = 1 / (2π × R×(1+tol_R) × C×(1+tol_C))
```

Example: 10k (5%) + 100nF (10%) low-pass filter:
- f_nom = 1/(2π × 10k × 100n) = 159 Hz
- f_max = 1/(2π × 9.5k × 90n) = 186 Hz (+17%)
- f_min = 1/(2π × 10.5k × 110n) = 138 Hz (-13%)

For anti-alias filters before ADCs, ensure f_min is still above the Nyquist frequency. For EMI filters, ensure f_max still attenuates the target frequency.

### Crystal Load Capacitor Tolerance Effects

Crystal frequency accuracy depends on correct load capacitance. With cap tolerance:

```
CL_actual_max = CL_cap×(1+tol)/2 + C_stray
CL_actual_min = CL_cap×(1-tol)/2 + C_stray
```

A 10% tolerance on 18pF caps (16.2-19.8pF) with 3pF stray yields CL_actual = 11.1-12.9pF vs target 12pF. Frequency error is roughly ±(CL_delta/CL) × crystal trim sensitivity (typically 5-20 ppm/pF). For most applications this is acceptable; for precision timing (GPS, RF), use C0G/NP0 caps with 1-2% tolerance.

### When to Escalate

Flag tolerance stacking as a **Warning** or **Critical** when:
- The worst-case output exceeds a downstream component's absolute maximum rating
- The worst-case output falls below a minimum operating threshold (regulator dropout, logic VIH)
- Safety margins shrink below 10% at worst case
- The application requires precision (current limiting, battery charging voltage)

---

## GPIO Multiplexing Audit

MCU pins serve multiple functions (alternate function muxing). A pin assigned to SPI_CLK cannot simultaneously serve as UART_TX. This analysis catches pin conflicts that ERC won't flag because both peripherals are electrically valid on the pin.

### Procedure

1. **Get the MCU's pin mux table** from the datasheet (usually titled "Alternate Function Mapping" or "Pin Multiplexing"). This table lists which alternate function (AF0-AF15 on STM32, IO_MUX on ESP32, etc.) maps each peripheral signal to each pin.

2. **Extract all used pins from the schematic**: From the analyzer output, list every net connected to the MCU. Map each net name to its peripheral function (e.g., `SPI1_MOSI`, `UART2_TX`, `I2C1_SDA`, `ADC1_CH3`).

3. **Check for conflicts**: For each pin, verify the assigned peripheral signal is available on that pin's alternate function list. Flag:
   - Two peripherals that require the same pin (e.g., SPI1_SCK and TIM2_CH1 both need PA5)
   - A peripheral signal routed to a pin that doesn't support it (e.g., UART_TX on a pin that only has SPI alternates)
   - ADC channels that conflict with digital peripherals (ADC is typically on AF0/analog mode — using the pin for SPI disables ADC)

4. **Check boot-mode pin conflicts**: Some MCU pins have special behavior during reset/boot (STM32 BOOT0, ESP32 strapping pins). Verify that peripherals connected to these pins don't interfere with boot.

### Common Conflict Patterns

| Conflict | Example | Risk |
|----------|---------|------|
| SPI + UART on same pin | SPI1_MISO and USART1_RX both on PA10 | Only one works at a time |
| I2C + ADC on same pin | I2C1_SDA on a pin also used for ADC input | Can't do both |
| Timer PWM + SPI | TIM1_CH1 and SPI1_NSS on same pin | PWM output conflicts with chip select |
| JTAG/SWD + GPIO | JTAG pins used as regular GPIO | Debugging no longer possible |
| Boot strapping + peripheral | ESP32 GPIO0 used for SPI CS | Must be high during boot, SPI may pull low |

---

## Connector Pinout Verification

Connector pinout errors are among the most common schematic mistakes and often aren't caught until board bring-up. Verify every connector's pin-to-net mapping against the relevant standard.

### Procedure

1. **Identify connector type** from the footprint or symbol library name (e.g., `USB_C_Receptacle`, `Conn_ARM_JTAG_SWD_10`, `Conn_01x06_FTDI`)
2. **Extract pin-to-net mapping** from the analyzer output for that connector's reference designator
3. **Compare against the standard pinout** (see table below)
4. **Check orientation**: KiCad symbols may show the pinout from the connector side or the PCB side — verify which convention the library uses

### Standard Pinouts

| Connector | Key Pins | Common Errors |
|-----------|----------|---------------|
| **USB Type-A** | 1=VBUS, 2=D-, 3=D+, 4=GND | D+/D- swap |
| **USB Type-B** | Same as Type-A | D+/D- swap |
| **USB Micro-B** | 1=VBUS, 2=D-, 3=D+, 4=ID, 5=GND | D+/D- swap, ID left floating (should be NC for device) |
| **USB Type-C** | A6/B6=D+, A7/B7=D-, A5=CC1, B5=CC2 | Missing CC resistors (5.1k to GND for UFP), TX/RX lane swap for USB3 |
| **ARM JTAG 20-pin** | 1=VTref, 3=nTRST, 5=TDI, 7=TMS, 9=TCK, 13=TDO, 15=nRST | Pin numbering varies between ARM standard and legacy |
| **ARM SWD 10-pin** (Cortex Debug) | 1=VTref, 2=SWDIO, 4=SWCLK, 6=SWO, 10=nRST | SWDIO/SWCLK swap, missing VTref connection |
| **FTDI 6-pin** | 1=GND, 2=CTS, 3=VCC, 4=TXD, 5=RXD, 6=DTR | TX/RX labeled from FTDI cable perspective — board TX connects to cable RXD (pin 5) |
| **Qwiic/STEMMA QT** (I2C) | 1=GND, 2=VCC(3.3V), 3=SDA, 4=SCL | VCC/GND swap, SDA/SCL swap |
| **SPI header** | No universal standard | MOSI/MISO naming ambiguity (use SDI/SDO relative to device) |
| **CAN bus** | CANH, CANL (2-wire) | H/L swap, missing 120 ohm termination resistor |
| **RS-485** | A(+), B(-), GND | A/B polarity swap (varies between manufacturers) |

### FTDI TX/RX Convention

This is the single most common connector pinout error. The FTDI cable labels pins from its own perspective:
- Cable pin "TXD" (pin 4) = data the cable **transmits** = connect to **board RX**
- Cable pin "RXD" (pin 5) = data the cable **receives** = connect to **board TX**

If the schematic labels match the FTDI cable labeling, the connections are **crossed** (correct). If the schematic connects board TX to cable TXD, the connections are **straight** (wrong — both sides transmit on the same wire).

---

## Clock Tree Analysis

Clock integrity is critical for reliable digital operation. Marginal clock circuits can cause intermittent failures that are extremely difficult to debug.

### Procedure

1. **Identify all clock sources**: crystals, crystal oscillators (packaged), MEMS oscillators, PLL outputs, clock buffers/distributors, RC oscillators
2. **Trace clock distribution**: from each source, follow the clock net to all consumers (MCU, FPGA, ADC, communication ICs)
3. **Check fan-out loading**: each clock output has a maximum number of inputs it can drive. Sum input capacitance of all loads and compare against the source's drive capability
4. **Check AC coupling**: some clock inputs require AC coupling (series cap) — particularly LVDS and LVPECL clock inputs
5. **Check termination**: series termination at the source (22-33 ohm typical) damps reflections for traces longer than λ/10

### Transmission Line Threshold

A clock trace must be treated as a transmission line (requiring impedance control and termination) when trace length exceeds λ/10:

```
λ = c / (f × √εr)
```

For FR4 (εr ≈ 4.5):
```
λ ≈ 141mm / f_GHz
```

| Clock Frequency | λ (FR4) | λ/10 (trace threshold) |
|----------------|---------|----------------------|
| 8 MHz | 17.7 m | 1.77 m (never an issue) |
| 25 MHz | 5.65 m | 565 mm (rarely an issue) |
| 48 MHz | 2.94 m | 294 mm (rarely an issue) |
| 100 MHz | 1.41 m | 141 mm (possible on large boards) |
| 500 MHz | 283 mm | 28.3 mm (likely needs controlled impedance) |
| 1 GHz | 141 mm | 14.1 mm (always needs controlled impedance) |

Most hobby/prototype boards with clocks ≤25 MHz don't need transmission line treatment. Flag it as a **Suggestion** for 25–100 MHz clocks and a **Warning** for >100 MHz.

### Common Clock Issues

- Missing series termination on oscillator output driving a long trace
- Crystal traces routed too far from MCU (adds stray capacitance, picks up noise)
- Clock buffer powered from noisy rail (use filtered/dedicated supply)
- Multiple clock frequencies creating beat interference (route apart, use ground guard traces)

---

## Motor Control Design Review

Motor control circuits combine high-current power switching with precision analog sensing. This section covers the key validation checks beyond basic component ratings.

### Dead-Time Verification (H-Bridge / Half-Bridge)

Shoot-through (both high-side and low-side FETs on simultaneously) destroys the bridge. Dead-time must exceed the slower FET's turn-off time:

1. Get turn-off delay (`td(off)`) and fall time (`tf`) from the MOSFET datasheet
2. Total turn-off time = `td(off) + tf` (at the actual gate drive voltage and load current)
3. Dead-time (from gate driver datasheet or PWM controller config) must exceed total turn-off time with margin
4. **Check at worst case**: turn-off time increases at higher temperature and higher load current

Flag as **Critical** if the dead-time is less than the worst-case turn-off time.

### Bootstrap Circuit Validation

For high-side N-channel MOSFET gate drive with a bootstrap circuit:

1. **Bootstrap capacitor sizing**: `C_boot >= Q_gate / ΔV_boot`, where ΔV_boot is the acceptable voltage droop (typically 0.5-1V). Use 10× minimum as a rule of thumb.
2. **Bootstrap diode**: reverse recovery time must be fast enough that the diode doesn't conduct during the switch node transition. Use Schottky or ultrafast recovery.
3. **Startup**: the bootstrap cap charges during low-side on-time. If the first PWM cycle starts with high-side on, the cap is uncharged — verify the controller forces a low-side pulse at startup.
4. **100% duty cycle limitation**: bootstrap circuits cannot sustain 100% high-side on-time (cap voltage decays). Check if the application requires this.

### Current Sense Validation

For shunt-resistor current sensing:

1. **Shunt power rating**: `P = I_peak² × R_shunt`. Derate to 50% of rated power for reliability. A 10mΩ shunt at 10A dissipates 1W — needs ≥2W rating.
2. **Sense amplifier CMRR**: the common-mode voltage on the shunt equals the motor voltage (potentially tens of volts). Verify the sense amp's CMRR is adequate and its common-mode input range covers the full swing.
3. **Kelvin routing**: sense traces must connect directly to the shunt resistor pads, not tap off the power trace. This is a PCB layout concern but should be noted in schematic review as a requirement.
4. **Sense voltage at full scale**: `V_sense = I_max × R_shunt`. This should match the sense amplifier's input range and the ADC's resolution requirements.

### Gate Drive Verification

1. **VGS vs VGS(th)**: gate drive voltage must exceed VGS(th)_max (worst case, not typical) with margin. For logic-level FETs with 3.3V drive: verify VGS(th)_max < 2.5V.
2. **Gate resistor**: limits di/dt to reduce ringing. Typical 2.2-10Ω. Missing gate resistors cause EMI and voltage spikes on the gate.
3. **Gate pull-down**: 10k-100k pull-down resistor on the gate to prevent floating during power-up (before the driver IC initializes). The gate driver's internal pull-down may not be active during power-up.

### Protection Circuits

Verify the presence and correctness of:
- **Overcurrent shutdown**: comparator or driver IC feature, threshold set by reference resistor. Verify threshold matches the current limit requirement.
- **Undervoltage lockout (UVLO)**: prevents operating the bridge with insufficient gate drive voltage (partial enhancement = high RDS(on) = thermal runaway). Usually built into the gate driver.
- **Thermal shutdown**: either in the driver IC or via an NTC + comparator. Verify NTC placement is thermally coupled to the FETs.
- **Flyback/freewheeling diodes**: for inductive loads, verify diodes across each switch or across the load. Body diodes in MOSFETs provide this, but external Schottky diodes may be needed for faster recovery.

### Common Motor Control Errors

| Error | Consequence | Check |
|-------|-------------|-------|
| Bootstrap cap too small | High-side gate voltage sags, FET partially on, overheats | C_boot >> Q_gate / ΔV |
| Shunt resistor under-rated for power | Resistor overheats, value drifts, possible open circuit | P_shunt = I² × R at peak current |
| Missing gate resistor | Gate ringing, EMI, false triggering | Every gate should have series R |
| Gate pull-down missing | FETs turn on uncontrolled during power-up | 10k-100k to source on each gate |
| Sense traces not Kelvin routed | Current measurement error from IR drop in power trace | Note for PCB layout review |

---

## Battery Life Estimation

For battery-powered designs, estimate operational lifetime to validate the design is practical. This builds on the sleep current audit in [Battery-Powered Design Considerations](#battery-powered-design-considerations).

### Step-by-Step Procedure

1. **Enumerate active mode current**: Sum the typical operating current for all ICs from their datasheets (at the actual supply voltage and clock frequency). Include:
   - MCU at operating frequency (e.g., ESP32-S3 at 240MHz: ~40-80mA)
   - Radio (WiFi TX: 180-380mA peak for ESP32; BLE TX: 20-30mA)
   - Sensors, ADCs, displays, LEDs
   - Regulator efficiency losses: `I_battery = I_load / η_regulator`

2. **Enumerate sleep mode current**: Use the sleep current audit from the analyzer output, plus datasheet sleep/shutdown currents for each IC. Don't forget:
   - Voltage divider quiescent current (always-on resistive paths)
   - Regulator quiescent current
   - Pull-up/pull-down leakage paths

3. **Estimate duty cycle**: What fraction of time is the device active vs sleeping? This is application-dependent — ask the user if not documented. Example: sensor that wakes every 60s, takes 2s to measure and transmit → duty = 2/60 = 3.3%.

4. **Compute weighted average current**:
   ```
   I_avg = I_active × duty + I_sleep × (1 - duty)
   ```

5. **Compute battery life**:
   ```
   Life_hours = Capacity_mAh / I_avg_mA
   Life_days = Life_hours / 24
   ```

### Battery Capacity Derating

Nominal capacity is measured under ideal conditions. Actual usable capacity depends on discharge rate, temperature, and cutoff voltage:

| Chemistry | Nominal | Usable Capacity | Notes |
|-----------|---------|-----------------|-------|
| LiPo 3.7V single cell | rated mAh | 90-95% (3.0V cutoff) | Linear down to ~3.4V, then drops fast |
| AA alkaline 1.5V | ~2500 mAh | 60-80% depending on drain | Voltage sags under load; 1.0V cutoff typical |
| CR2032 coin cell | ~220 mAh | ~200 mAh at <2mA | Capacity drops sharply above 2mA continuous draw |
| 18650 Li-ion | rated mAh | ~90% (2.5-3.0V cutoff) | High pulse capability |
| AAA alkaline 1.5V | ~1000 mAh | 50-70% | Less capacity than AA, same derating factors |
| LiFePO4 3.2V | rated mAh | ~95% (2.5V cutoff) | Very flat discharge curve, excellent for regulated supplies |

### Peak Current Considerations

Even if average current is low, peak current events can cause problems:
- **WiFi TX bursts**: 180-380mA for 100-500ms. Battery internal resistance causes voltage sag. Verify the regulator input voltage stays above minimum during peaks (see [Minimum Battery Voltage](#minimum-battery-voltage-low-battery-threshold)).
- **Motor start**: inrush current can be 5-10× running current. May need a bulk capacitor to supply the peak.
- **LED animations**: WS2812B strips draw 60mA/LED at full white. 10 LEDs = 600mA peak.
- **Bulk capacitor sizing**: for short peaks, `C = I_peak × t_peak / ΔV_allowed`. A 100µF cap supplies 200mA for 1ms with 2V droop.

### Report Format for Battery Life

Include a power budget table in the analysis report:

| Mode | Current | Duty Cycle | Weighted |
|------|---------|-----------|----------|
| Active (MCU + WiFi TX) | 250 mA | 3% | 7.5 mA |
| Active (MCU only) | 50 mA | 2% | 1.0 mA |
| Deep sleep | 15 µA | 95% | 14.3 µA |
| **Weighted average** | | | **8.5 mA** |
| **Battery life** (1000mAh LiPo) | | | **~5 days** |

---

## Supply Chain Risk Assessment

Identify components that pose sourcing risks — sole-source parts, obsolete components, or parts with historically constrained supply.

### Procedure

1. **For each IC in the BOM**, determine:
   - How many manufacturers make pin-compatible alternatives?
   - Is the part listed as active, NRND (Not Recommended for New Designs), or obsolete?
   - Are there recent stock-out or allocation events? (check DigiKey/Mouser stock levels and lead times)

2. **Flag sole-source components**: if only one manufacturer makes a part with no pin-compatible alternative, it's a supply chain risk. Common sole-source categories:
   - Specialized sensor ICs (IMU, environmental sensors)
   - Application-specific PMICs
   - Wireless SoCs (ESP32, nRF52 — popular but single-source)
   - Specialized motor drivers

3. **Suggest alternatives where available**:
   - Voltage regulators: many LDO/buck families have pin-compatible options across manufacturers (e.g., AP2112 ↔ ME6211 ↔ XC6220)
   - MOSFETs: generally interchangeable if VDS, ID, RDS(on), and package match
   - Passives: resistors, capacitors, inductors are multi-source by nature (use generic values, not custom)
   - Connectors: specify by mechanical standard (USB-C, JST-PH, etc.) rather than single MPN

4. **Check for obsolescence indicators**:
   - Datasheet marked "Not for new designs" or "End of life"
   - Last datasheet revision date >5 years ago with no updates
   - Distributor listing shows "Last Time Buy" or zero stock across all distributors
   - Part has been superseded by a newer version (check manufacturer's cross-reference)

### Severity Levels

| Situation | Severity | Action |
|-----------|----------|--------|
| Obsolete/EOL part | **Warning** | Must find replacement before production |
| NRND part | **Suggestion** | Plan migration, current stock usually available |
| Sole-source, active, good stock | **Info** | Note the risk, suggest monitoring |
| Sole-source, constrained supply | **Warning** | Identify alternatives or stock buffer |
| Generic passive (0402 10k 1%) | No flag | Multi-source by nature |

---

## Report Format

Structure the analysis report as follows:

```markdown
# Schematic Analysis Report: [Project Name]

## Summary
- Components: [N] unique parts, [M] total placements, [D] DNP
- Subcircuits identified: [list]
- Findings: [X] critical, [Y] warnings, [Z] suggestions

## Subcircuit Analysis

### [Subcircuit Name] (e.g., "3.3V LDO — U2, C3, C4, R5, R6")

**Function:** [what it does]
**Datasheet:** [URL or MPN]
**Reference circuit comparison:** [matches/deviates from datasheet Fig. N]

**Findings:**
- [CRITICAL] ... (cite: datasheet §X.Y, page Z, Figure/Table N)
- [WARNING] ...
- [SUGGESTION] ...

**Value verification** (show the work, cite the source equation):
- VOUT = VREF × (1 + R_top/R_bottom) = 0.595V × (1 + 732k/100k) = 4.95V
  Target: 5.0V. Per TPS61023 datasheet Eq. 4 (page 13), VREF = 595mV typ (Table 6.5, page 5: 580-610mV range). ✓
- Feedforward cap: C = 1/(2π × f_FFZ × R1) = 1/(2π × 1kHz × 732kΩ) = 218pF → 220pF (std value)
  Per TPS61023 datasheet Eq. 10 (page 15), TI recommends f_FFZ ≈ 1kHz. ✓
- Cout ESR: X7R ceramic, ESR < 10mΩ — datasheet requires ESR > 100mΩ for stability ✗

[repeat for each subcircuit]

## Cross-Cutting Issues

### Power Budget
| Rail | Regulator | Max Output | Estimated Load | Margin |
|------|-----------|-----------|----------------|--------|
| 3.3V | U2 (AP2112) | 600mA | ~120mA | 80% ✓ |

### Signal Level Compatibility
[any cross-domain voltage issues]

### Missing Protection
[ESD, reverse polarity, overcurrent gaps]

## BOM Observations
[consolidation opportunities, sourcing risks, cost notes]
```

Adapt the depth and detail to the complexity of the design. A simple LED blinker doesn't need a 10-page report. A battery-powered IoT sensor with multiple regulators, wireless, and analog sensing does.
