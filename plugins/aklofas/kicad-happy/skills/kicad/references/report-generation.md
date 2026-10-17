# Design Review Report Generation

Guide for producing comprehensive design review reports from analyzer output + raw file cross-referencing. These reports help EE designers validate their designs before committing to fabrication.

## Minimum Review Contract

This reference is not optional reading for full design reviews. If the user asks for a complete review, ready-to-fab assessment, or comprehensive report, the resulting report must satisfy this minimum contract:

1. Name the analyzers that were actually run.
2. Name the applicable analyzers that were not run, and why.
3. Separate verified findings from inference-only findings.
4. Put blockers and warnings near the top.
5. Triage obvious false positives instead of repeating analyzer output unfiltered.
6. State verification gaps explicitly when datasheets, thermal, lifecycle, gerbers, or prior-review delta were not available.

If the review does not meet this contract, it is an incomplete review, not a full one.

## Required Sections for Full Reviews

These sections are expected in a complete design review unless genuinely not applicable:

- Overview
- Previous Review Delta, when a prior review or prior runs exist
- Critical Findings
- Component Summary
- Power Tree
- Analyzer Verification
- Deep Review, when `analysis/deep_review.json` exists
- Signal Analysis Review
- Power Analysis
- PCB Layout Analysis, when a PCB exists
- Thermal Analysis or an explicit note that thermal analysis was not performed
- EMC / Cross-Domain Analysis when schematic and PCB both exist
- Component Lifecycle or an explicit note that lifecycle audit was not performed
- Manufacturing / DFM / testability
- False Positives / reviewer overrides
- Not Performed / Review Limits
- Final verdict / readiness statement

## Evidence Basis Rules

Every substantive finding should make its evidence basis clear. Use these categories consistently:

- **Datasheet-verified** — checked against the manufacturer PDF, with page / figure / table / equation citation
- **Extraction-verified** — checked against structured datasheet extraction in `datasheets/extracted/`
- **Raw-file verified** — checked against the raw `.kicad_sch`, `.kicad_pcb`, or fabrication files
- **Analyzer-derived** — came from analyzer output and was accepted after review
- **Inference-only** — plausible engineering reasoning, but not directly verified against datasheet or raw file

Do not use the word "verified" for analyzer-only or inference-only claims.

## Skipped Analysis Disclosure

If any applicable analysis was not run, include a short section in the report that says so explicitly. Do not bury omissions in prose or leave them unstated.

Recommended format:

```markdown
## Not Performed / Review Limits

- Thermal analysis not performed — reason.
- Lifecycle audit not performed — reason.
- Gerber analysis not performed — no fabrication outputs present.
- Datasheet extraction not available — pin-level checks are datasheet-manual or inference-only.
```

## False-Positive Triage

A good design review is not a transcript of analyzer output. For findings likely to be layout artifacts, intentional keepouts, expected RF-module courtyard behavior, or known heuristic overreach:

- either dismiss them explicitly with reasoning
- or downgrade them and explain the residual risk

If a finding was reviewed and judged benign, keep it in a "False Positives / Reviewer Overrides" section so the reader can see that it was considered rather than missed.

## Contents

| Section | Line | Purpose |
|---------|------|---------|
| Report Structure | ~18 | Full report template (copy and fill in) |
| Analyzer Output Field Reference | ~364 | Maps every JSON output field to its report section — use as checklist |
| Severity Definitions | ~468 | CRITICAL / WARNING / SUGGESTION criteria |
| Writing Principles | ~476 | How to write actionable findings |
| Handling Different Design Domains | ~512 | Domain-specific focus areas (IoT, motor, RF, analog, industrial) |
| Cross-Referencing with Raw Schematic | ~529 | Mandatory verification steps |
| Known Analyzer Limitations | ~540 | What the tool can and can't catch |
| Report Length Guidelines | ~563 | Target report sizes by complexity |

## Report Structure

Use this template. Include sections that are relevant to the design — skip sections that genuinely don't apply (a battery-powered sensor board doesn't need an isolation barrier section). For sections where the analyzer returned empty data, briefly assess whether that's expected ("no mains input, creepage N/A") or a gap worth noting ("no ESD protection detected on external USB connector").

```markdown
# [Project Name] Design Review

**Project:** [name] ([KiCad version], [single sheet | N hierarchical sheets], [N-layer PCB | no PCB])
**Date:** [analysis date]
**Analyzers:** [list scripts run: analyze_schematic.py, analyze_pcb.py, analyze_gerbers.py] ([modern/legacy format], [full signal analysis | legacy mode])

## Overview
[2-4 sentence description of the board: MCU, power architecture, key peripherals, domain (IoT/motor control/RF/instrumentation/etc.), form factor context]

## Previous Review Delta
[**Include when prior review files or analyzer JSON exist in the project directory.** Scan for `*review*.md`, `*design-review*.md`, and prior `*_analysis.json` files.

If prior analyzer JSON exists, run `diff_analysis.py old.json new.json` to generate a structured component/signal/EMC diff. Present as:]

| Status | Count |
|--------|-------|
| Fixed since last review | N |
| Still open | N |
| New findings | N |

[For each fixed item, note it as a positive finding ("Thermal via count on U3 increased from 14 to 18 — now meets IPC recommendation"). For still-open items, carry forward the original severity. For new findings, integrate into their normal sections below.

If prior analyzer JSON does not exist but a prior review markdown does, manually compare findings and track issue status (fixed/open/new) by reading both documents.

If no prior review exists, omit this section entirely.]

## Critical Findings
[**This section comes first** so the designer sees the most important issues immediately. Move here after completing the full analysis.]

| Severity | Issue | Section |
|----------|-------|---------|
| CRITICAL | [Board won't function, safety hazard, or fabrication failure] | [link to section with details] |
| WARNING  | [Suboptimal but board may work, potential reliability issue] | [link to section with details] |

[Only CRITICAL and WARNING items here. SUGGESTION-level items go in the Issues Found section later. If no CRITICAL or WARNING issues: "No critical or warning-level issues found." — this itself is a valuable finding.]

## Component Summary
[Table: Type | Count, broken down by resistors, capacitors, ICs, connectors, etc.]
[One-line stats: Nets, Wires, No-connects, Power rails, Sheets]
[Sourcing audit: MPN coverage %, missing distributor part numbers — do not recommend any specific distributor by name]

## Power Tree
[ASCII art showing the power distribution hierarchy]
[Include: input source, each regulator with type (LDO/buck/boost/inverting), input->output voltages, enable conditions, key caps with values, feedback divider calculations]
[Note vref_source for each regulator: "lookup" (datasheet-verified) or "heuristic" (needs manual verification)]

## Analyzer Verification
[Spot-checks proving the analyzer data is trustworthy]
### Component Count — [N/N match status]
### Component Pinout Verification — [Table: ALL components verified against raw schematic + **manufacturer PDF datasheets** (not KiCad library symbols): Ref | Value | Pins | Datasheet Verified | Verification Status | Match. Every component must be checked — not just ICs. Include connectors, transistors, diodes, and critical passives. The "Datasheet Verified" column must reference the actual PDF datasheet with page/section number — not the `.kicad_sym` library file. Use the following **Verification Status** categories:
- **Verified (datasheet)** — cross-checked against manufacturer PDF datasheet (cite page/section)
- **Verified (extraction)** — cross-checked against pre-extracted specs from `datasheets/extracted/` (extraction score >= 6.0)
- **Unverified** — no datasheet or extraction available; plausibility assessment only. State what was assessed and confidence level.
- **Skipped** — passive/mechanical component where pinout verification is not meaningful (2-pin passives, mounting holes)

Custom library symbols (e.g., `sacmap:TPS61023`) are highest priority for datasheet verification because there's no upstream KiCad library as a secondary check. When pre-extracted datasheet specs are available, use them for faster verification. Fall back to direct PDF reading when extraction score < 6.0 or when pin-level detail is insufficient. Each finding in the report should also indicate its evidence basis: datasheet-verified, extraction-verified, or inference-only.]
### Pinout Ambiguity & Plausibility — [Components where the symbol's pin assignment depends on the specific MPN. Table: Ref | lib_id | Footprint | MPN | Assumed Pinout | Datasheet Pinout | Plausibility | Status. When verification is possible (MPN + datasheet), verify directly. When it isn't, assess plausibility: does the assumed pinout match the dominant convention for this device type and package? Report confidence: "matches most common convention," "plausible but multiple variants exist," or "unusual — most parts in this category use a different pinout." Flag CRITICAL when no MPN is specified AND the assumed pinout is uncommon or genuinely ambiguous.]
### Connector Pin Tables — [For connectors with >2 pins (debug headers, programming ports, I/O connectors): table of Pin | Net | Function. The `ic_pin_analysis` section includes connector data — present it as a quick-reference table. Particularly valuable for debug/programming headers (EN, 3V3, TX, GND, RX, BOOT) where pin order matters for cable orientation.]
### Net Tracing — [All power rails + critical signal nets traced end-to-end: list all pins, verify connectivity, confirm correctness]
### PCB Verification — [If PCB analyzed: footprint count match, pad-net spot-check, board dimensions confirmed]
### Gerber Verification — [If gerbers analyzed: layer completeness, drill count, alignment check]

## Deep Review

Findings from the per-IC usage-vs-datasheet pass
(`analysis/deep_review.json`) — first-class findings, presented
before the detector baseline. Group by category. For each finding:
summary, severity/confidence, and the evidence inline — datasheet
quote with MPN + page, computation result, design anchors.
Quarantined entries render at the end under **Unverified claims**
with their quarantine reasons — never silently dropped. If the pass
was skipped or degraded (no datasheets), state the per-IC gaps here.

## Signal Analysis Review
[Walk through each detected subcircuit category, validate calculations, note any false positives]

### Power Regulators
[Each regulator: topology (LDO/buck/boost/inverting), input/output rails, Vout estimate, vref_source (lookup vs heuristic), vout_net_mismatch flag. Verify heuristic Vref values against datasheets.]

### Voltage Dividers & Feedback Networks
[Table: R_top | R_bottom | Ratio | Output voltage | Purpose | Verified status. For feedback dividers: Vref verification against datasheet lookup table. Flag any vout_net_mismatch where estimated Vout differs >15% from the output rail name voltage.]

### RC/LC Filters
[Cutoff frequencies, filter type (low-pass/high-pass), component values, purpose, verified status]

### Op-Amp Circuits
[Configuration (inverting/non-inverting/buffer/differential), gain from Rf/Ri, topology identification accuracy]

### Protection Devices
[ESD, TVS, varistors — placement coverage on external connectors, voltage ratings vs rail voltages]

### LED Circuits
[For each LED: verify current limiting resistor value provides correct forward current. Calculate: I_LED = (V_supply - V_f) / R_limit. Check against LED datasheet for typical V_f, V_f tolerance range, and maximum current rating. Flag cases where current margin is tight (operating near max or where V_f variation could push current out of spec). Consider supply voltage tolerance as well.]

### Transistor Circuits
[Type (N-ch/P-ch MOSFET, NPN/PNP BJT), load type classification (inductive/led/resistive/motor/heater/fan/solenoid/connector), gate/base drive analysis, protection (flyback diode, snubber)]

### Bridge Circuits
[Topology (half_bridge/h_bridge/three_phase), FET references, output nets, gate driver ICs. Note: cross-sheet bridge detection works through unified hierarchical nets.]

### Crystal Circuits
[Load cap analysis, frequency, Cload vs recommended values]

### Current Sense
[Shunt values, sense amplifier, measurement range]

### Simulation Verification
[**Include when ngspice is available.** Run `simulate_subcircuits.py` on the analyzer JSON output (from the `spice` skill). The output JSON has top-level key `simulation_results` (list). Each entry has `reference` (e.g. "R5/C3"), `components` (list), `subcircuit_type`, `status`, `expected` (dict of metric values like `cutoff_hz`), `simulated` (dict of measured values), and `delta` (dict of error percentages). Use `summary` for totals. Present results as a summary table grouped by status:]

[Summary line: "ngspice verified N subcircuits in X.Xs. N pass, N warn, N fail, N skip."]

[**Pass** — one line each, grouped: "RC filter R5/C3 (fc=15.9kHz): confirmed, <0.3% error." Build this from `result['reference']`, `result['expected']['cutoff_hz']`, and `result['delta']`.]

[**Warn** — explain context: "Opamp U4A (inverting, gain=-10): gain confirmed at 20.0dB. Bandwidth 98.8kHz (ideal model). Note: LM358 GBW is ~1MHz — actual bandwidth ~100kHz." Opamp and transistor results always carry model fidelity caveats.]

[**Fail** — investigate and explain: "RC filter R12/C8: simulated fc=3.2kHz vs expected 15.9kHz (80% deviation). Likely topology misdetection — verify R12's role in the circuit." Failures in passive circuits indicate analyzer bugs; in active circuits they may indicate real design issues.]

[**Skip** — note the gap: "Crystal Y1 (32.768kHz): active oscillator, no external load caps to validate." Skips are expected for unsimulatable configurations.]

[Model fidelity notes: passive circuit simulations (RC, LC, dividers, current sense) use ideal components and are mathematically exact. Active circuit simulations (opamps, transistors) use generic behavioral models — qualify bandwidth and threshold results with the actual part's specifications.]

### Decoupling Analysis
[Table: Rail | Cap Count | Total uF | Bulk | Bypass — one row per rail. Flag rails with inadequate decoupling.]

### Buzzer/Speaker Circuits
[Driver topology, frequency if applicable]

### Domain-Specific Detections
[Include subsections only when detected:]
- **RF Chains** — component chain, frequency bands, switch matrix
- **BMS Systems** — cell count, balance topology, protection
- **Ethernet Interfaces** — magnetics, PHY, termination
- **Memory Interfaces** — type, data bus width, address lines
- **Key Matrices** — row/column count, diode matrix
- **Isolation Barriers** — isolation voltage, optocoupler/digital isolator

### Design Observations
[Automated observations from the analyzer: decoupling coverage, I2C pull-ups, crystal load caps, regulator details, etc. Validate each against the raw schematic.]

## Power Analysis

### PDN Impedance
[Per-rail impedance profile (1kHz–1GHz), key impedance points, anti-resonances, SRF gaps, MLCC parasitic modeling]

### Power Budget
[Per-rail load estimates vs regulator capacity, flag any overloaded rails, regulator headroom]

### Power Sequencing
[Enable chains (EN/PG dependencies), startup order, missing PG feedback]

### Sleep Current Audit
[Per-rail estimated sleep current, dominant leakage paths (pull-up/pull-down resistors), regulator Iq estimates with EN pin detection. Present both the analyzer's worst-case figure (`total_estimated_sleep_uA`) and realistic estimate (`realistic_total_uA`). Use `realistic_total_uA` for expected battery life; use the worst-case for absolute-maximum calculations. Each current path has `likely_state` explaining whether it's active during sleep (e.g., "can be disabled via EN", "GPIO off during sleep", "rail disabled during sleep") and `realistic_uA` (0 for inactive paths). Explain which paths are inactive and why.]

### Inrush Analysis
[Power-on current analysis — not limited to regulators. Consider ALL current paths at power-on:]
- Per-regulator inrush (input capacitance, soft-start adequacy)
- IC supply pin absolute maximum ratings vs capacitor charging current (e.g., 74HC-series ±50mA VCC/GND limit, small MCUs with low abs max supply current)
- Bulk/decoupling capacitor charging through connectors (hot-plug scenarios produce fast voltage steps → high dI/dt)
- Source impedance: connector resistance, wire gauge, trace resistance — these limit peak inrush naturally
- Series resistance or soft-start mechanisms (or lack thereof)
- Multiple rails energizing simultaneously (total system inrush vs supply capability)
[Even designs with no regulators need this section — external supply rails still charge decoupling caps through IC supply pins at power-on. Check each IC's datasheet for absolute maximum continuous current through VCC/GND pins.]

### Voltage Derating
[Component voltage ratings vs applied voltages, capacitor derating at operating voltage]

## Standards Compliance
[Include when applicable — see `references/standards-compliance.md` for auto-trigger conditions and tables. Consider for all boards: even low-voltage designs benefit from a brief conductor spacing and current capacity check. For mains-connected or safety-isolated designs, this section is mandatory.]

### Product Classification
[Class 1/2/3 determination with rationale from BOM indicators]

### Conductor Spacing (IPC-2221A Table 6-1)
[High-voltage net pairs with required vs actual spacing. Skip for designs where all nets are ≤15V and traces meet minimums.]

### Current Capacity (IPC-2221A / IPC-2152)
[Power traces: expected current, trace width, copper weight, calculated capacity, margin. Flag <50% margin as WARNING, <20% as CRITICAL.]

### Creepage/Clearance (ECMA-287 / IEC 60664-1)
[Only for mains-connected or safety-isolated designs. Working voltage, OVC, pollution degree, material group, required vs actual distances.]

### Annular Ring (IPC-2221A Table 9-2)
[Via annular ring analysis, fab capability vs IPC minimums]

### Via Protection (IPC-4761)
[Only for via-in-pad designs: protection type, BGA/QFN thermal pad vias. The `thermal_pad_vias` output uses an `effective_via_count` that weights each via by `(drill/0.3mm)²` — see pcb-layout-analysis.md "Thermal via effective count methodology" for the full formula and thresholds. Designs using 0.2mm vias by intent (module footprints) may show "insufficient" adequacy despite adequate thermal performance — always cross-reference the datasheet before flagging.]

## Design Analysis

### Net Classification
[Power/ground/high_speed/data/analog/control/chip_select/interrupt/output_drive/debug/config/signal categorization. Verify output_drive nets (motor, heater, fan, solenoid, relay, lamp, LED, PWM, buzzer).]

### Cross-Domain Signals
[Signals crossing voltage domains, level shifter assessment. Uses voltage equivalence from rail name parsing to reduce false positives. Rails without parseable voltages may trigger false warnings.]

### ERC Warnings
[Total count, categorize: genuine issues vs benign/false positives. Covers: multi-driver nets, unconnected power pins, pin type conflicts.]

### Bus Topology
[I2C detection (SDA/SCL + pull-ups), SPI (SCK/MOSI/MISO/COPI/CIPO/SDI/SDO/CS), UART (TX/RX), CAN bus grouping accuracy]

### Differential Pairs
[Suffix-pair detection for USB (D+/D-), LVDS, Ethernet (TX+/TX-), HDMI, MIPI, PCIe, SATA, CAN, RS-485. Protocol guessing from net name keywords.]

### Connectivity Issues
[Unconnected pins, single-pin nets, multi-driver conflicts, power net summary]

### Label/Annotation Warnings
[Label shape warnings (input/output direction), PWR_FLAG coverage, annotation gaps, hierarchical label validation]

### Passive Warnings
[Unusual passive values, tolerance concerns]

### Footprint Filter Warnings
[Custom library vs standard filter mismatches]

## PCB Layout Analysis
[Include when a .kicad_pcb file was analyzed — skip for schematic-only reviews]

### Board Overview
[Dimensions, layer count (from tracks + vias + zones), copper layer names, stackup summary from .kicad_pro, board thickness]

### Footprint Placement
[Front/back side counts, SMD/THT ratio, placement density, courtyard overlaps, edge clearance warnings]

### Via Analysis
[Type breakdown (through/blind/micro), size distribution, annular ring checks, via-in-pad detection, BGA/QFN fanout patterns, current capacity, stitching via identification, tenting assessment]

### Trace Routing
[Per-net trace lengths, width distribution, layer distribution, power trace widths vs current requirements (IPC-2221)]

### Signal Integrity
[Layer transitions per net, ground return path assessment, trace proximity/crosstalk (with --proximity flag)]

Differential pair length matching: For each detected differential pair (USB D+/D-, Ethernet TX+/TX-, etc.), compute the length delta between the two traces and cite the protocol-specific tolerance. The delta and tolerance are more useful than the raw lengths alone — they tell the designer whether there's margin or a problem. Example format: "D+=75.8mm, D-=75.2mm (delta=0.6mm — within USB 2.0 FS tolerance of ±25mm)." For interfaces with tighter requirements: USB 3.x ±3mm, HDMI ±2mm, DDR ±0.5mm.

### Power & Ground
[Power net routing summary (width, length, current capacity), ground domain identification (AGND/DGND/PGND), zone stitching via density]

### Thermal Analysis
[Thermal pad detection, via counting and adequacy for QFN/DFN packages, zone stitching density, thermal relief settings, tombstoning risk assessment (0201/0402 thermal asymmetry). Cross-reference thermal via count and pad area against each IC's datasheet thermal management section — check recommended via count, via diameter, and exposed pad connection. Verify θJA assumptions match the datasheet's specified board conditions (e.g., JEDEC 2s2p vs actual layer count).

When `analyze_thermal.py` was run, include its junction temperature estimates (Tj per component, margin to Tj_max, thermal score). Cross-reference against datasheet Tj_max values. When the thermal script was not run, estimate manually from power dissipation and package θJA for components with significant power draw (regulators, drivers, power FETs).]

For every IC with an exposed/thermal pad, explicitly report the via count and adequacy in this format: "[Ref] pad [N] ([net]) connected through [count] thermal vias (recommended range: [min]–[max] per datasheet) — [adequate/insufficient]." Example: "U1 pad 41 (GND thermal pad) connected through 12 thermal vias (recommended range: 9–16) — adequate." The thermal via count is one of the most common QFN/DFN layout errors and is always worth calling out with a specific number, even when adequate — it confirms the designer got it right.

### Copper Presence
[Zone copper at component pad locations — from `copper_presence` section. Focus on `no_opposite_layer_copper` list: which components lack zone copper on the opposite layer? Verify this is intentional for capacitive touch pads and antennas (need isolation) vs unexpected for other components (might indicate a zone gap). Also note `same_layer_foreign_zones` — pads sitting on zones they're not connected to, which is normal for tightly-packed power island zones but worth flagging if unexpected.]

### Capacitive Touch Pads
[Include when TP-prefixed components or pad-only footprints appear in `copper_presence.no_opposite_layer_copper`, or when touch controller ICs are detected]

| Pad | Diameter/Size | Position | Opposite-Layer Copper | Keepout Zone? | GND Pour Clearance | Trace Width | Trace Length to Controller |
|-----|--------------|----------|----------------------|---------------|-------------------|-------------|--------------------------|
| [ref] | [mm] | [x, y] | [none / present (CRITICAL)] | [yes — (x1,y1) to (x2,y2) / NO — flag WARNING] | [distance mm vs app note min] | [mm] | [mm — compare across pads] |

Copper absence vs keepout enforcement: Confirming "no copper" under a touch pad is necessary but not sufficient. That absence could be accidental — a routing change or zone adjustment could fill in copper and kill touch sensitivity. A keepout zone is a DRC rule that prevents this permanently. Check the PCB file for explicit keepout/rule-area objects on the opposite layer under each touch pad. If none exist, flag as WARNING: "no explicit keepout zone under [ref] — copper absence is not enforced by a DRC rule."

Trace length asymmetry: Compute the trace length from each touch pad to the controller IC and compare across all pads. Significant asymmetry (>1.5×) means different parasitic capacitance per channel, which shifts baseline readings and may reduce dynamic range even with firmware calibration. Report the ratio: "TOUCH_2 (41.6mm) is 1.75× longer than TOUCH_1 (23.7mm)."

GND pour clearance: Use the `touch_pad_gnd_clearance` section in `copper_presence` for measured clearance values (`gnd_clearance_mm` per touch pad). Compare against the touch controller's recommended minimum (typically 1.0mm for Espressif, check the specific controller's app note). If the clearance is exactly at the minimum, note this: "GND clearance is 1.0mm — exactly the Espressif minimum. Consider increasing to 1.5mm if sensitivity is marginal." If `touch_pad_gnd_clearance` is not present, measure manually from the PCB layout.

### Antenna Layout
[Include when ANT-prefixed footprints, antenna lib_id patterns, or RF antenna footprints are detected, OR when wireless modules (ESP32, nRF, etc.) with integrated/PCB antennas are present]
- Keepout zone verification: check the `keepout_zones` section in the PCB analyzer output for restriction areas near the antenna footprint. Report the keepout zone coordinates, layer coverage, and restriction types explicitly: "Keepout zone on F.Cu+B.Cu: (x1, y1) to (x2, y2), restrictions: no copper pour, no tracks." The `nearby_components` field shows which components are near each keepout zone. Cross-reference dimensions against the manufacturer's reference layout — many antenna datasheets/app notes specify exact keepout areas.
- Ground plane termination: verify the ground plane ends at the antenna feed point and does not extend under the radiating element
- Matching network placement: components between antenna and RF IC should be close to the antenna with controlled-impedance traces
[If no keepout zones are defined around the antenna, flag as WARNING. For wireless modules (ESP32, nRF, etc.), the module vendor's reference design is the authoritative source for keepout dimensions — these are often the single most important layout constraint for RF performance. Always cite the specific antenna/module reference when verifying keepout adequacy: "Correct per Espressif guidelines" or "Matches nRF52840 reference layout."]

### Decoupling Placement
[Cap-to-IC distances for critical components, flag caps too far from IC power pins. Verify capacitor values and placement distances against each IC's datasheet requirements — many ICs specify maximum distance, minimum capacitance, and ESR limits for input/output decoupling. Flag any deviation from datasheet recommendations.

ESD protection ICs (entries with `category: "esd_bypass"` in the decoupling output) require a low-impedance bypass path for clamping. Their bypass cap should be within 3mm — flag WARNING if >5mm, SUGGESTION if 3-5mm. Common ESD ICs: USBLC6-2SC6, TPD4E05U06, PRTR5V0U2X, IP4220CZ6.]

### Current Capacity
[Per-net trace/via current capacity vs estimated load, narrow signal net warnings]

### DFM Assessment
[JLCPCB standard/advanced tier determination, DFM metrics (min trace width, min clearance, min drill, min annular ring), violation list. All threshold values MUST come from the "Fab House Capabilities" table in standards-compliance.md — do not substitute from memory.]

### Silkscreen
[Board text count, reference designator visibility, documentation warnings, values on silk]

### Connectivity
[Routing completeness, unrouted net count and list]

## Schematic ↔ PCB Cross-Reference
[Include when both schematic and PCB were analyzed — this catches the most dangerous bugs. Use `statistics.total_nets` from both analyzers for net count comparison — do not mix net counts from different sections or manual counting methods, as the schematic may include internal unnamed nets that the PCB doesn't.]
### Component Count Match — [Schematic (excl. power symbols) vs PCB footprint count]
### Pin-Net Verification — [ALL components: schematic pin mapping vs PCB pad mapping. Table: Ref | Pins | All Match | Mismatches. Do not sample — verify every component including connectors, transistors, diodes.]
This verification must happen at the PCB pad level, not just the schematic pin level. The schematic tells you pin 1 connects to net X; the PCB tells you pad 1 connects to net X. If the library footprint has pad numbering that doesn't match the symbol's pin numbering, the schematic and PCB will be internally consistent but the board will be wrong. For each IC, transistor, and connector, verify both directions: schematic pin N → net X, AND PCB pad N → net X, AND the physical pad position matches the datasheet's pin diagram for that specific package. Example format: "Q1: 1=G(MAP_RED), 2=S(GND), 3=D(+5V)." This catches the most dangerous class of bug — a library footprint with wrong pad numbering passes all consistency checks but produces a non-functional board.
### Connector Pinout Tables — [For connectors with >2 pins (debug headers, programming headers, multi-pin interfaces), include a pin mapping table]

| Connector | Pin | Net | Function |
|-----------|-----|-----|----------|
| J1 | 1 | RESET | MCU reset |
| ... | ... | ... | ... |

[This is especially important for programming/debug headers, USB connectors, and board-to-board interfaces where miswiring is common and consequences are severe.]

### Footprint Match — [Schematic Footprint property vs actual PCB footprint]
### Value/MPN Consistency — [Spot-check values and MPNs between schematic and PCB]
### DNP Consistency — [Components marked DNP in schematic should not have routing on PCB]

## Gerber Analysis
[Include when gerber directory was analyzed]
### Layer Completeness — [Found vs missing required/recommended layers, source identification]
### Drill Classification — [Via count, component holes, mounting holes, classification method]
### Alignment Verification — [Layer alignment check, extent comparison]
### Pad Summary — [SMD vs THT aperture counts, via apertures, heatsink apertures]
### Board Dimensions — [From gerber extents, compare against PCB if both analyzed]

## Interface Summary
[One-line summary of each external interface: connector type, protection, protocol, pin mapping]
[Examples: USB-C (ESD: yes, CC: 5.1kΩ), SWD (J1, no ESD), CAN (120Ω term, PESD2CAN)]

## Quality & Manufacturing

### Assembly Complexity
[Score, SMD/THT ratio, difficulty breakdown (fine-pitch, BGA, QFN), dominant package, unique footprint count]

### Sourcing Audit
[MPN coverage %, missing MPNs list, missing distributor part numbers. Do not recommend or prefer any specific distributor by name — keep sourcing observations neutral.]

### Component Lifecycle Status
[**Include when `--lifecycle` flag was used on the schematic analyzer.** Report any NRND (not recommended for new designs), EOL (end of life), or obsolete components from the `lifecycle_audit` output. For each flagged part: MPN, current status, last-buy date if known, and suggested action (find alternate, stock up, redesign). If lifecycle audit was not run, note: "Lifecycle audit not performed — [reason: no API keys / no network / no MPNs]."]

### BOM Optimization
[Unique passive value counts per type, total unique footprints, single-use passive values, consolidation opportunities]

### Test Coverage
[Test points found and nets covered, debug connectors, uncovered critical nets]

### USB Compliance
[If applicable: connector type, ESD protection, CC resistors, VBUS protection, D+/D- impedance]

### Simulation Readiness
[Components likely simulatable vs needing SPICE models, coverage percentage]

### Ordering Notes
[Practical manufacturing summary for ordering — this section bridges the design review and the fabrication order. Extract surface finish from the PCB stackup (`copper_finish` field in setup section), solder mask color from board setup, and board thickness from the stackup layer sum. Designers use this to configure their PCB order, so always include it when a PCB was analyzed.]
- Layer count: [N] layers, surface finish: [HASL/ENIG/OSP — from PCB stackup `copper_finish`], solder mask color: [green/black/etc. — from board setup]
- Stencil: [recommend if SMD components present, note if fine-pitch requires frameless stencil]
- Board thickness: [standard 1.6mm or custom — from stackup total thickness]
- DFM tier: [standard vs advanced capability requirements based on min trace/space/drill from DFM section]
- Copper weight: [1oz/2oz based on current requirements — from stackup copper layer thickness, 0.035mm = 1oz]
- Assembly notes: [reflow profile considerations, mixed SMD/THT implications]
- Special requirements: [impedance control, via-in-pad, castellated edges, etc. if applicable]

## All Issues & Suggestions
[Complete list of all findings. CRITICAL and WARNING items were already shown in the Critical Findings section at the top — repeat them here with full detail and context. SUGGESTION items appear here only.]

| Severity | Issue | Detail |
|----------|-------|--------|
| CRITICAL | [Board won't function, safety hazard, or fabrication failure] | [Full explanation, datasheet citation, affected components] |
| WARNING  | [Suboptimal but board may work, potential reliability issue] | [Full explanation, recommendation] |
| SUGGESTION | [Improvements, best practices, documentation gaps] | [Rationale, optional fix] |

## Positive Findings
[Numbered list of things the design does well — builds designer confidence and validates good practices. Examples:]
1. All ICs have local decoupling capacitors within 3mm — good EMC practice
2. USB differential pairs are length-matched within 0.2mm — well within USB 2.0 spec (25ps)
3. Feedback divider values for U3 (TPS61023) match the datasheet application circuit exactly (590K/200K → 2.37V)
4. Thermal vias under QFN packages: U1 has 9 vias (TI recommends 6-9) — adequate thermal path

## Analyzer Gaps
[Numbered list of things the analyzer missed, got wrong, or couldn't detect — transparency about tool limitations. Examples:]
1. Crystal Y1 (32.768 kHz) load capacitor validation skipped — no CL spec in analyzer output for this crystal
2. Connector J3 pinout could not be verified — no datasheet found for this custom connector
3. Analog ground (AGND) to digital ground (DGND) connection point not analyzed — single-point connection must be verified visually
4. U5 (custom library symbol from `mylib:XYZ123`) — pin mapping not verified against datasheet due to missing MPN
```

## Analyzer Output Field Reference

Quick reference for what each analyzer produces, to ensure no analysis dimension is missed in the report.

### Schematic Analyzer (`analyze_schematic.py`)

| Output Section | Report Section | Key Fields |
|---|---|---|
| `statistics` | Component Summary | component_types, power_rails, missing_mpn |
| `bom` | Component Summary, BOM Optimization | deduplicated parts with quantities |
| `components` | IC Spot-Check, throughout | full component details with pin_uuids, parsed_value |
| `nets` | Net Tracing, throughout | per-net pin lists with pin_type |
| `subcircuits` | Power Tree | auto-detected power/signal subcircuits |
| `ic_pin_analysis` | MCU pin audit | per-IC pin utilization summary |
| `findings[] (detector: power_regulators)` | Power Regulators | topology, vref_source, vout_estimate, vout_net_mismatch, inverting |
| `findings[] (detector: feedback_networks)` | Feedback Networks | R_top, R_bottom, vref, vout, vref_source |
| `findings[] (detector: voltage_dividers)` | Voltage Dividers | ratio, output_voltage |
| `findings[] (detector: rc_filters)` | RC/LC Filters | cutoff_hz, filter_type |
| `findings[] (detector: lc_filters)` | RC/LC Filters | resonant_freq_hz |
| `findings[] (detector: opamp_circuits)` | Op-Amp Circuits | configuration, gain |
| `findings[] (detector: protection_devices)` | Protection Devices | type, placement |
| `findings[] (detector: transistor_circuits)` | Transistor Circuits | load_type (motor/heater/fan/solenoid/etc.), is_pchannel, gate_drive |
| `findings[] (detector: bridge_circuits)` | Bridge Circuits | topology, half_bridges, driver_ics |
| `findings[] (detector: crystal_circuits)` | Crystal Circuits | cload, frequency |
| `findings[] (detector: current_sense)` | Current Sense | shunt_value, gain |
| `findings[] (detector: decoupling_analysis)` | Decoupling Analysis | per-rail cap inventory |
| `findings[] (detector: buzzer_speaker_circuits)` | Buzzer/Speaker | driver topology |
| `findings[] (detector: rf_chains)` | RF Chains | component chain |
| `findings[] (detector: bms_systems)` | BMS Systems | cell monitoring |
| `findings[] (detector: ethernet_interfaces)` | Ethernet | magnetics, PHY |
| `findings[] (detector: memory_interfaces)` | Memory | bus width |
| `findings[] (detector: key_matrices)` | Key Matrices | row/col count |
| `findings[] (detector: isolation_barriers)` | Isolation | isolation type |
| `findings[] (detector: battery_chargers)` | Battery Chargers | charger_type, charge_current |
| `findings[] (detector: motor_drivers)` | Motor Drivers | driver_type (stepper/dc_brushed) |
| `findings[] (detector: esd_coverage_audit)` | ESD Coverage | per-connector coverage, risk_level |
| `findings[] (detector: debug_interfaces)` | Debug Interfaces | SWD/JTAG, target_ic |
| `findings[] (detector: power_path)` | Power Path | load switches, ideal diodes, USB PD |
| `findings[] (detector: adc_circuits)` | ADC Circuits | external ADCs, voltage references |
| `findings[] (detector: reset_supervisors)` | Reset/Supervisor | supervisors, watchdogs, RC reset |
| `findings[] (detector: clock_distribution)` | Clock Distribution | generators, PLLs, oscillator outputs |
| `findings[] (detector: display_interfaces)` | Display/Touch | display type, touch controller |
| `findings[] (detector: sensor_interfaces)` | Sensor Fusion | motion/environmental/magnetic, interrupt pins |
| `findings[] (detector: level_shifters)` | Level Shifters | IC + discrete, supply domains |
| `findings[] (detector: audio_circuits)` | Audio Circuits | amplifiers, codecs, I2S |
| `findings[] (detector: led_driver_ics)` | LED Driver ICs | PWM/matrix/constant-current |
| `findings[] (detector: rtc_circuits)` | RTC Circuits | battery backup, crystal pairing |
| `findings[] (detector: led_audit)` | LED Audit | current limiting validation |
| `findings[] (detector: thermocouple_rtd)` | Thermocouple/RTD | amplifiers, RTD interfaces |
| `findings[] (detector: power_sequencing_validation)` | Power Sequencing | power tree, enable chains, issues |
| `findings[] (detector: design_observations)` | Design Observations | automated findings |
| `design_analysis.net_classification` | Net Classification | per-net class (power/data/analog/output_drive/etc.) |
| `design_analysis.power_domains` | Power Domains | per-IC rail mapping with IO rails |
| `design_analysis.cross_domain_signals` | Cross-Domain Signals | voltage equivalence filtering |
| `design_analysis.bus_analysis` | Bus Topology | I2C/SPI/UART/CAN with COPI/CIPO support |
| `design_analysis.differential_pairs` | Differential Pairs | suffix-pair matching, protocol guessing |
| `design_analysis.erc_warnings` | ERC Warnings | type, severity |
| `design_analysis.passive_warnings` | Passive Warnings | unusual values |
| `connectivity_issues` | Connectivity Issues | unconnected, single-pin, multi-driver |
| `pdn_impedance` | PDN Impedance | per-rail impedance with MLCC parasitics |
| `power_budget` | Power Budget | load vs capacity |
| `power_sequencing` | Power Sequencing | EN/PG chains |
| `sleep_current_audit` | Sleep Current | per-rail with regulator Iq, EN detection |
| `inrush_analysis` | Inrush Analysis | per-regulator inrush (automated); also manually consider IC supply pin abs max ratings and capacitor charging through connectors |
| `ground_domains` | Power & Ground | AGND/DGND/PGND separation |
| `sourcing_audit` | Sourcing Audit | MPN and distributor PN coverage (report neutrally, no distributor preference) |
| `bom_optimization` | BOM Optimization | value consolidation |
| `test_coverage` | Test Coverage | test points, debug connectors |
| `assembly_complexity` | Assembly Complexity | score, difficulty breakdown |
| `usb_compliance` | USB Compliance | connector, ESD, CC |
| `simulation_readiness` | Simulation Readiness | SPICE model coverage |
| `label_shape_warnings` | Label Warnings | direction mismatches |
| `pwr_flag_warnings` | PWR_FLAG | missing flags |
| `footprint_filter_warnings` | Footprint Filters | library mismatches |
| `annotation_issues` | Label Warnings | duplicate/missing refs |
| `property_issues` | Quality | property pattern issues |
| `placement_analysis` | (spatial context) | component clusters, grid |
| `alternate_pin_summary` | MCU pin audit | alt function usage |

### PCB Analyzer (`analyze_pcb.py`)

| Output Section | Report Section | Key Fields |
|---|---|---|
| `statistics` | Board Overview | copper_layers_used (tracks+vias+zones), layer names, SMD/THT counts |
| `layers` | Board Overview | full layer stack |
| `setup` | Board Overview | thickness, mask clearance |
| `board_outline` | Board Overview | bounding box, edge geometry |
| `board_metadata` | Board Overview | title block, paper |
| `footprints` | Footprint Placement | per-footprint pads, nets, schematic cross-ref (sch_path, sch_sheetname) |
| `component_groups` | Footprint Placement | grouped by reference prefix |
| `tracks` | Trace Routing | width/layer distribution |
| `vias` | Via Analysis | size distribution, via_analysis (types, annular ring, via-in-pad, tenting) |
| `zones` | Power & Ground | per-zone net, layers, outline/filled bbox, fill area, fill_ratio, thermal settings |
| `connectivity` | Connectivity | routing completeness, unrouted list |
| `net_lengths` | Signal Integrity | per-net trace length and layer transitions |
| `power_net_routing` | Power & Ground | power net width/length/current capacity |
| `ground_domains` | Power & Ground | AGND/DGND domains, multi-domain components |
| `findings[] (detector: analyze_current_capacity)` | Current Capacity | per-net capacity vs load |
| `findings[] (detector: analyze_thermal_vias)` | Thermal Analysis | zone stitching density |
| `findings[] (detector: analyze_thermal_pad_vias)` | Thermal Analysis | per-footprint thermal pad via count and adequacy; `effective_via_count` weights by `(drill/0.3)²` — see pcb-layout-analysis.md for methodology |
| `decoupling_placement` | Decoupling Placement | cap-to-IC distances |
| `findings[] (detector: analyze_placement)` | Footprint Placement | courtyard overlaps, edge clearance |
| `placement_density` | Footprint Placement | density metrics |
| `layer_transitions` | Signal Integrity | per-net layer change tracking |
| `silkscreen` | Silkscreen | ref visibility, documentation warnings |
| `dfm_summary` | DFM Assessment | tier, metrics, violation_count |
| `findings[] (category: dfm)` | DFM Assessment | individual violations |
| `findings[] (detector: analyze_tombstoning_risk)` | Manufacturing | at-risk 0201/0402 components, thermal asymmetry reasons |
| `findings[] (detector: analyze_copper_presence)` | Copper Presence | no_opposite_layer_copper, same_layer_foreign_zones, touch_pad_gnd_clearance |
| `copper_presence_summary` | Copper Presence | opposite_layer_summary |

### Gerber Analyzer (`analyze_gerbers.py`)

| Output Section | Report Section | Key Fields |
|---|---|---|
| `statistics` | Gerber Analysis | file counts, total holes/flashes/draws |
| `completeness` | Layer Completeness | found/missing layers, source |
| `alignment` | Alignment Verification | aligned status, layer extents |
| `drill_classification` | Drill Classification | vias, component holes, mounting holes |
| `pad_summary` | Pad Summary | SMD/THT/via/heatsink apertures |
| `board_dimensions` | Board Dimensions | from gerber extents |
| `gerbers` | (per-layer detail) | aperture functions, trace widths, X2 attributes |
| `drills` | (per-file detail) | tool list, hole counts |

## Severity Definitions

Use these consistently across all reports:

- **CRITICAL**: The board will not function as designed, or there is a safety/damage risk. Examples: swapped pins in symbol library, output contention from shorted op-amp outputs, regulator can't start, missing power path, thermal pad without ground vias on QFN.
- **WARNING**: The board may work but has a reliability, performance, or compliance concern. Examples: floating digital inputs, missing flyback diode on inductive load, cross-domain signal without level shifter, inadequate decoupling, regulator thermal margin tight.
- **SUGGESTION**: Best-practice improvement or documentation gap that doesn't affect functionality. Examples: missing MPNs, no test points on power rails, DNP components not marked, footprint filter mismatch with custom library.

## Writing Principles

### Be specific and actionable
Bad: "Power supply may have issues"
Good: "LMR51450 (U7) feedback divider R12/R13 gives Vout = 0.6*(1+100k/47k) = 1.88V, but target rail is 3.3V. Vref for LMR51450 is 1.0V (not 0.6V assumed by analyzer), giving actual Vout = 1.0*(1+100k/47k) = 3.13V — still 5% below target."

### Show your work
Include the calculation, the datasheet reference, and the conclusion. EE designers want to verify your reasoning, not just trust a pass/fail label.

### Distinguish analyzer findings from manual findings
Make it clear what came from the analyzer JSON vs what you found by reading the raw schematic. This helps designers understand the tool's coverage.

### Call out false positives explicitly
When the analyzer flags something that isn't actually a problem, explain why it's a false positive. This prevents designers from wasting time investigating non-issues and helps calibrate trust in the analyzer.

### Validate calculations, don't just echo them
When the analyzer reports a voltage divider ratio or filter cutoff, verify the calculation: check the formula, confirm the component values against the schematic, and validate the result against the datasheet's expected values (Vref, recommended output voltage, etc.).

### Cross-check against datasheets
The highest-value findings come from verifying component connections and values against datasheets. Check IC pin assignments against the datasheet pinout, feedback divider values against regulator recommendations, capacitor selections against min/max requirements, and pull-up/pull-down values against acceptable ranges. These checks catch the bugs that internal consistency checks miss.

### Assess plausibility when verification isn't possible
When a component can't be fully verified (missing MPN, missing datasheet), don't just report "unverified" and move on — assess how likely the design choice is to be correct. Use domain knowledge: typical pinouts for that device/package combination, standard passive values for the application, common circuit topologies. Report the assessment alongside the ambiguity. "Q1 uses Q_NPN_BEC (SOT-23) with no MPN — BCE is the most common SOT-23 NPN pinout, so this is likely correct but should be confirmed" is far more useful than "Q1 pinout is unverified." The principle: ambiguity is not uniform risk. Some unverified choices align with strong conventions and are low risk; others are genuinely ambiguous or go against convention and deserve higher suspicion.

### Verify battery and power source configurations
Don't assume a battery holder is a single cell. Check the footprint, part number, and trace connectivity to determine the actual battery configuration (series vs parallel, cell count). A 2×AA holder provides ~3V nominal, not 1.5V — getting this wrong invalidates the entire power tree analysis.

### Check thermal vias in footprints
Thermal vias for QFN/BGA/module packages may be embedded in the footprint definition as thru_hole pads (sharing the thermal pad's net and number) rather than standalone vias. The PCB analyzer counts both types. When reviewing thermal via adequacy, confirm you're counting footprint-embedded via pads in addition to standalone vias.

### Distributor neutrality
Never recommend or prefer any specific component distributor (DigiKey, LCSC, Mouser, etc.) by name in the report. Keep sourcing observations neutral — report MPN coverage and missing part numbers without directing the user toward a particular source.

### Power tree is king
For almost every board, the power tree section is the most valuable. Draw the complete hierarchy from input to every rail, including regulator types, enable conditions, and output capacitance. This single diagram often reveals the most critical issues (missing paths, wrong sequencing, inadequate capacitance).

## Handling Different Design Domains

### IoT / Battery-Powered
Focus on: sleep current budget (validate against analyzer's worst-case estimates), startup voltage thresholds, power path (USB vs battery), regulator quiescent current (check Iq estimates), deep sleep GPIO configuration.

### Motor Control
Focus on: H-bridge/3-phase topology detection, gate driver bootstrap, current sense chain, MOSFET load classification (motor/heater/fan/solenoid), ground domain separation (analog/power), bulk capacitance adequacy, reverse polarity protection, thermal considerations.

### RF / SDR
Focus on: RF chain path tracing through switches, LNA/mixer/filter identification, frequency planning, decoupling tier analysis (bulk + bypass + HF), reference clock distribution, ground plane continuity.

### Precision Analog / Instrumentation
Focus on: op-amp configurations and gain accuracy, reference voltage chain, input protection on measurement channels, ADC/DAC interface verification, PGA detection, bipolar supply generation, guard traces.

### Industrial / Multi-rail
Focus on: power sequencing (EN/PG chains from analyzer), input protection (TVS, MOV, fuses), communication buses (CAN, RS485, Ethernet — check bus analysis), isolation barriers, creepage/clearance for high voltage. The Standards Compliance section in the report template is especially important here — fill in all subsections including creepage/clearance.

## Cross-Referencing with Raw Schematic

The analyzer can silently produce plausible but incorrect results. Cross-reference against the raw `.kicad_sch` AND manufacturer PDF datasheets to catch these. Internal consistency checks (schematic matches PCB matches analyzer) are necessary but not sufficient — they only prove the design agrees with itself, not that it matches the real-world parts. The full verification procedure is in SKILL.md — the key checks are:

1. **Component count**: Analyzer total vs `grep -c '(lib_id' file.kicad_sch` (subtract power symbols)
2. **Pin-to-net mapping**: Verify against raw schematic for each component. Cross-reference IC pin assignments against **manufacturer PDF datasheets** (not KiCad library symbols — the library is the potential source of error). Cite datasheet page/section numbers.
3. **Physical correctness**: For components with package-dependent pinouts (transistors in SOT-23 etc.), verify symbol assumptions against the MPN's datasheet — consistency checks alone don't catch wrong pinout assumptions. Custom/community library symbols are highest risk.
4. **Net connectivity**: Trace power rails and critical signal nets end-to-end.
5. **Signal analysis**: Confirm detected subcircuit topologies against the raw schematic.
6. **Hierarchical sheets**: Verify all sub-sheets were parsed (`grep -c '(sheet ' file.kicad_sch`).

## Known Analyzer Limitations

Document these when they affect the report — it helps the designer understand what the tool can and can't catch:

- **Vref coverage**: Feedback divider Vout calculations use a lookup table (~60 regulator families) with heuristic fallback. When `vref_source` is `"heuristic"`, the assumed Vref may be wrong — always verify against the datasheet. The `vout_net_mismatch` field flags cases where estimated Vout differs >15% from the output rail name voltage.
- **Legacy format**: KiCad 5 `.sch` files get full analysis when `.lib` files are available in the repo (92–100% typical coverage). Components whose `.lib` files are missing will lack pin data and won't participate in signal analysis or subcircuit detection.
- **Sleep current model**: Reports both worst-case (`total_estimated_sleep_uA`) and realistic (`realistic_total_uA`) estimates. Worst-case assumes all pull-ups driven low simultaneously; realistic uses topology-aware state estimation (LEDs off, disableable regulators off, rails from EN-equipped regulators disabled). The realistic estimate may still overcount if the design has additional sleep-mode controls not visible in the schematic topology.
- **Cross-domain analysis**: Uses voltage equivalence (parsing voltage from rail names) to reduce false positives, but rails without parseable voltages in their names may still trigger false cross-domain warnings.
- **MOSFET load classification**: Net name keyword detection covers common patterns (motor, heater, fan, solenoid, valve, pump, relay, speaker, buzzer, lamp) but may miss unusual naming conventions.
- **Bridge circuits**: Cross-sheet detection works through unified hierarchical nets. Topology classification is based on half-bridge count (1=half, 2=H-bridge, 3+=3-phase) which may misclassify independent half-bridges as an H-bridge.

## Fabrication Notes (Optional)

[Include when DFM analysis was performed and the user is preparing for manufacturing. Practical guidance specific to the board:]

- **Fab tier**: Standard vs advanced process capability (based on DFM scoring from PCB analyzer)
- **Recommended settings**: Copper weight, surface finish, impedance control (if controlled-impedance traces detected)
- **Stencil guidance**: If fine-pitch components detected (QFN, BGA), note stencil thickness recommendations
- **Assembly notes**: Component placement order, reflow considerations, hand-solder items
- **Specific assembler notes**: JLCPCB basic vs extended parts count, PCBWay turnkey vs consigned

This section bridges the design review into the ordering workflow — the `jlcpcb` and `pcbway` skills handle the ordering specifics, but the report should flag anything the designer needs to address before ordering.

## Report Length Guidelines

Typical report lengths by design complexity:

| Design | Components | Typical Report |
|--------|-----------|---------------|
| Simple (IoT, single sheet) | 30-100 | 150-250 lines |
| Medium (motor control, few sheets) | 100-300 | 200-350 lines |
| Complex (DAQ, RF, many sheets) | 300-700 | 300-450 lines |

Keep it thorough but avoid padding. Every line should provide information the designer can act on or use to build confidence in the design.
