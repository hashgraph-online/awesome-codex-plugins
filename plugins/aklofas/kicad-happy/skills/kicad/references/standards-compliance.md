# IPC/IEC Standards Compliance Reference

Reference tables and formulas for checking PCB designs against industry standards. All values are verified from the actual standard documents (source noted for each table). Values marked **[UNVERIFIED]** are from secondary sources and need primary document confirmation.

**When to use this reference:** Automatically for professional/industrial designs — projects with: 4+ layer boards, controlled impedance, high voltage (>50V), safety-critical functions, CE/UL certification targets, medical/automotive/aerospace applications, or any project where the user mentions standards compliance. For hobby/prototype boards, reference only when the user asks or when a specific concern (e.g., high voltage spacing) warrants it.

## Verification Status

| Section | Standard | Status |
|---|---|---|
| Product Classification | IPC-A-600G, IPC-2221A | VERIFIED |
| Conductor Spacing | IPC-2221A Table 6-1 | VERIFIED |
| Current Capacity (classic) | IPC-2221A §6.2 | VERIFIED |
| Current Capacity caveats | IPC-2221A / IPC-2152 history | VERIFIED |
| Annular Ring | IPC-2221A Tables 9-1/9-2 | VERIFIED |
| Hole Sizes | IPC-2221A Tables 9-3/9-4/9-5 | VERIFIED |
| Impedance Calculations | IPC-2221A §6.4 | VERIFIED |
| Dielectric Properties | IPC-2221A Table 6-2 | VERIFIED |
| Via Protection Types | IPC-4761 | VERIFIED |
| Mains Transient Voltages | ECMA-287 Table 3.3 | VERIFIED |
| Minimum Clearances | ECMA-287 Table 3.4 | VERIFIED |
| Minimum Creepage | ECMA-287 Table 3.5 | VERIFIED |
| Coated PCB Separations | ECMA-287 Table 3.9 | VERIFIED |
| Safety Definitions | ECMA-287 §2–3 | VERIFIED |
| Current Capacity (updated) | IPC-2152 | **PARTIALLY VERIFIED** |
| Safety Standard (modern) | IEC 62368-1 | **UNVERIFIED** |
| Land Pattern Density | IPC-7351B | **UNVERIFIED** |

### Remaining Gaps

1. **IPC-2152 formula** — The approximate formula `A = (117.555 × ΔT^(-0.913) + 1.15) × I^(0.84 × ΔT^(-0.108) + 1.159)` and correction factors for copper planes are from secondary sources (online calculators). The Jouppi article confirms the standard's methodology, test scope (≤25A), and limitations but does not reprint the formula. Impact: **Low** — the IPC-2221A formula is adequate for most reviews, and the caveats about when IPC-2152 matters are well documented.

2. **IEC 62368-1** — Energy source classification thresholds (ES1/ES2/ES3 current and voltage limits) and the hazard-based safety engineering approach are described from secondary sources. Impact: **Low** — the creepage/clearance tables from ECMA-287 (which derives from the same IEC 60664-1 framework) cover the PCB-relevant requirements. IEC 62368-1 mainly adds the energy-source classification layer on top.

3. **IPC-7351B** — Land pattern density levels (A/B/C) and courtyard excess values (0.50/0.25/0.10 mm) are from secondary sources. Impact: **Low** — these values are widely cited and unlikely to be wrong, but haven't been confirmed against the actual standard document.

## Contents

| Section | Line | Standard |
|---------|------|----------|
| Product Classification | ~56 | IPC-A-600G, IPC-2221A |
| Conductor Spacing | ~73 | IPC-2221A Table 6-1 |
| Current Carrying Capacity | ~109 | IPC-2221A Section 6.2 |
| Annular Ring Requirements | ~158 | IPC-2221A Tables 9-1, 9-2 |
| Hole Size Requirements | ~194 | IPC-2221A Tables 9-3, 9-4, 9-5 |
| Impedance Calculations | ~224 | IPC-2221A Section 6.4 |
| Dielectric Properties | ~262 | IPC-2221A Table 6-2 |
| Via Protection Types | ~279 | IPC-4761 |
| Creepage and Clearance | ~313 | ECMA-287 (derived from IEC 60664-1) |
| Safety Standards | ~446 | ECMA-287, IEC 62368-1 |
| Land Pattern Density | ~481 | IPC-7351B |
| Current Capacity (Updated) | ~501 | IPC-2152 |

---

## Product Classification

Three product classes determine acceptable imperfection levels. Source: IPC-A-600G Section 1.4, IPC-2221A.

| Class | Name | Description | Examples |
|-------|------|-------------|----------|
| 1 | General Electronic Products | Consumer products; cosmetic imperfections not important; function is primary requirement | Consumer electronics, toys, non-critical appliances |
| 2 | Dedicated Service Electronic Products | High performance and extended life required; uninterrupted service desired but not critical; cosmetic imperfections allowed | Communications equipment, business machines, instruments |
| 3 | High Reliability Electronic Products | Continued performance or on-demand performance critical; equipment downtime not tolerable; must function when required | Life support, flight control, military, medical implants |

**How to determine class from a design:** Look for indicators in the schematic/BOM:
- Medical ICs, MIL-spec parts, automotive-grade parts → likely Class 3
- Industrial MCUs, commercial-grade with redundancy → likely Class 2
- ESP32/Arduino, consumer-grade parts, 2-layer hobby boards → likely Class 1

---

## Conductor Spacing (Electrical Clearance)

Source: **IPC-2221A Table 6-1** (page 43), verified from PDF.

Minimum spacing in mm between uninsulated conductors. Columns B1-B4 are bare board conditions; A5-A7 are assembly conditions.

| Voltage (DC or AC peak) | B1: Internal | B2: External, uncoated, sea level | B3: External, uncoated, >3050m | B4: External, polymer coated, sea level | A5: External, conformal coated over assembly | A6: External, uncoated, sea level | A7: External, uncoated, >3050m |
|---|---|---|---|---|---|---|---|
| 0–15 V | 0.05 | 0.1 | 0.1 | 0.05 | 0.13 | 0.13 | 0.13 |
| 16–30 V | 0.05 | 0.1 | 0.1 | 0.05 | 0.13 | 0.25 | 0.13 |
| 31–50 V | 0.1 | 0.6 | 0.6 | 0.13 | 0.13 | 0.4 | 0.13 |
| 51–100 V | 0.1 | 0.6 | 1.5 | 0.13 | 0.13 | 0.5 | 0.13 |
| 101–150 V | 0.2 | 0.6 | 3.2 | 0.4 | 0.4 | 0.8 | 0.4 |
| 151–170 V | 0.2 | 1.25 | 3.2 | 0.4 | 0.4 | 0.8 | 0.4 |
| 171–250 V | 0.2 | 1.25 | 6.4 | 0.4 | 0.4 | 0.8 | 0.4 |
| 251–300 V | 0.2 | 1.25 | 12.5 | 0.8 | 0.8 | 1.5 | 0.8 |
| 301–500 V | 0.25 | 2.5 | 12.5 | 0.8 | 0.8 | 1.5 | 0.8 |
| >500 V | 0.0005/V | 0.005/V | 0.025/V | 0.00167/V | 0.00167/V | 0.003/V | 0.00167/V |

**Column selection guide:**
- **B1** (Internal): Traces on inner layers of multilayer boards
- **B2** (External, uncoated, sea level): Bare board traces at normal altitude, no coating
- **B3** (External, uncoated, >3050m): High altitude operation — much larger spacing required
- **B4** (External, polymer coated): Bare board with conformal coating (before assembly)
- **A5** (Conformal coated assembly): Assembled board with conformal coating applied
- **A6** (External, uncoated assembly): Assembled board, no coating — the common case for most designs
- **A7** (External, uncoated assembly, >3050m): Assembled, no coating, high altitude

**Usage in design review:** Extract the maximum voltage on each net from the schematic's power analysis. For each pair of adjacent nets at different potentials, verify the PCB track spacing meets the appropriate column. Pay special attention to:
- Power supply input (often highest voltage)
- Switch-node nets on DC-DC converters
- Any net with voltage >50V
- Mains-referenced circuits (require IEC 60664-1 creepage/clearance instead — see below)

---

## Current Carrying Capacity

Source: **IPC-2221A Section 6.2** (page 40), verified from PDF. These are the classic "IPC-2221 charts" widely used in PCB design.

### Formula (from IPC-2221A Section 6.2)

```
I = k × ΔT^0.44 × A^0.725
```

Where:
- `I` = current capacity (Amperes)
- `k` = 0.048 for external (outer) layers; 0.024 for internal layers
- `ΔT` = temperature rise above ambient (°C)
- `A` = cross-sectional area of the conductor (square mils; 1 mil = 0.0254 mm)

**Converting trace width to cross-sectional area:**
```
A (sq. mils) = width_mils × thickness_mils
```
For 1 oz copper: thickness = 1.378 mils (0.035 mm = 35 µm)
For 2 oz copper: thickness = 2.756 mils (0.070 mm = 70 µm)

### Quick Reference Table (IPC-2221 external layer, 1 oz = 35 µm, 10°C rise)

| Trace Width (mm) | Trace Width (mils) | Area (sq. mils) | Current (A) |
|---|---|---|---|
| 0.15 | 5.9 | 8.1 | 0.60 |
| 0.25 | 9.8 | 13.6 | 0.88 |
| 0.5 | 19.7 | 27.1 | 1.45 |
| 1.0 | 39.4 | 54.3 | 2.39 |
| 2.0 | 78.7 | 108.5 | 3.95 |
| 3.0 | 118.1 | 162.8 | 5.30 |
| 5.0 | 196.9 | 271.3 | 7.68 |

Note: Internal layer capacity is approximately half of external (k=0.024 vs k=0.048).

### Important Caveats

- The external trace chart originates from **NBS (National Bureau of Standards) test data from 1954–1956** (NBS Report 4283). The test boards were phenolic, epoxy, and G-5 materials in thicknesses from 1/32" to 1/8", tested in still air. (Source: Mike Jouppi, IPC 1-10b task group chairman, PCDFCA July 2022.)
- The **internal trace chart was NOT derived from test data** — it was created by halving the current from the external chart. This arbitrary factor was never documented or justified. (Verified from same source.)
- These charts are for **single isolated conductors** in still air. Real-world conditions (adjacent traces, enclosed housing, elevated ambient, copper planes) significantly affect results.
- **IPC-2152** is the successor standard with updated test methodology. See the IPC-2152 section below.
- The formula assumes steady-state DC current. For pulsed/transient currents, the RMS equivalent should be used.

**Usage in design review:** Extract power net trace widths from the PCB analyzer's `power_net_routing` list. Calculate current capacity using the formula and compare against expected current from the schematic's power analysis. Flag any traces with <50% margin as WARNING, <20% margin as CRITICAL.

---

## Annular Ring Requirements

Source: **IPC-2221A Tables 9-1 and 9-2** (page 74), verified from PDF.

### Table 9-1: Fabrication Allowance

| Producibility Level | Min Fabrication Allowance |
|---|---|
| Level A (Preferred/Standard) | 0.4 mm |
| Level B (Standard/Moderate) | 0.25 mm |
| Level C (Reduced/Advanced) | 0.2 mm |

### Table 9-2: Minimum Annular Ring

| Feature | Minimum Annular Ring |
|---|---|
| External, Supported (plated through) | 0.050 mm |
| External, Unsupported (non-plated) | 0.150 mm |
| Internal, Supported | 0.025 mm |

**"Supported"** means the hole has plating connecting to the land (plated-through hole). **"Unsupported"** means no plating support (non-plated through hole).

**Annular ring calculation:**
```
Annular ring = (pad diameter - drill diameter) / 2
```

The fabrication allowance must be added to account for drill registration tolerance:
```
Minimum pad diameter = drill diameter + (2 × annular ring) + fabrication allowance
```

**Usage in design review:** The PCB analyzer reports annular ring values in the via analysis section. Compare against these minimums. For JLCPCB and similar budget fabs, their actual capability is typically Level B or C. Check the fab's DFM specs against these IPC minimums.

---

## Hole Size Requirements

Source: **IPC-2221A Tables 9-3, 9-4, 9-5** (page 76), verified from PDF.

### Table 9-3: Min Drilled Hole Size — Buried Vias

| Board Thickness at Via | Level A | Level B | Level C |
|---|---|---|---|
| ≤1.0 mm | 0.25 mm | 0.20 mm | 0.15 mm |
| >1.0 mm to ≤2.0 mm | 0.30 mm | 0.25 mm | 0.20 mm |
| >2.0 mm | 0.35 mm | 0.30 mm | 0.25 mm |

### Table 9-4: Min Drilled Hole Size — Blind Vias

| Board Thickness at Via | Level A | Level B | Level C |
|---|---|---|---|
| ≤1.0 mm | 0.25 mm | 0.20 mm | 0.15 mm |
| >1.0 mm to ≤2.0 mm | 0.30 mm | 0.25 mm | 0.20 mm |
| >2.0 mm | 0.35 mm | 0.30 mm | 0.25 mm |

### Table 9-5: Hole Location Tolerance

| Producibility Level | Hole Location Tolerance |
|---|---|
| Level A (Preferred) | ±0.25 mm |
| Level B (Standard) | ±0.20 mm |
| Level C (Reduced) | ±0.15 mm |

---

## Impedance Calculations

Source: **IPC-2221A Section 6.4** (pages 43-48), verified from PDF. These are first-order approximations — use a field solver for production designs.

### Microstrip (outer layer trace over ground plane)

```
Z₀ = (87 / √(εᵣ + 1.41)) × ln(5.98h / (0.8w + t))
```

Where:
- `Z₀` = characteristic impedance (Ω)
- `εᵣ` = relative dielectric constant of substrate
- `h` = height of trace above ground plane (dielectric thickness)
- `w` = trace width
- `t` = trace thickness
- All dimensions in the same units

Valid for: `w/h < 1` (narrow trace relative to dielectric height)

### Embedded Microstrip (inner trace with reference plane)

```
Z₀ = (60 / √εᵣ) × ln(4h / (0.67(0.8w + t)))
```

### Stripline (inner trace between two ground planes)

```
Z₀ = (60 / √εᵣ) × ln(4b / (0.67π(0.8w + t)))
```

Where `b` = distance between the two reference planes.

**Usage in design review:** For USB (90Ω differential), DDR, LVDS, and other controlled-impedance signals, verify the trace width against the board stackup using these formulas. With `--full`, the PCB analyzer adds a first-order microstrip estimate (`impedance_ohm` on `net_lengths[].trace_segments[]`) from the board or inferred stackup; check it with a field solver or the fab's calculator before relying on it.

---

## Dielectric Properties

Source: **IPC-2221A Table 6-2** (page 45), verified from PDF.

| Material | Dielectric Constant (εᵣ) at 1 MHz |
|---|---|
| FR-4 (glass epoxy) | 4.2–4.9 |
| Polyimide (Kapton) | 3.2–3.5 |
| BT/Epoxy | 3.9–4.2 |
| PTFE (Teflon) | 2.0–2.3 |
| Ceramic (alumina) | 8.0–10.5 |
| Cyanate Ester | 3.5–3.8 |

Note: Dielectric constant varies with frequency. At GHz frequencies, FR-4 εᵣ is typically 4.2-4.4 (lower than the 1 MHz value). For high-frequency designs (>1 GHz), use frequency-dependent data from the laminate manufacturer's datasheet (e.g., Isola, Rogers).

---

## Via Protection Types

Source: **IPC-4761** (July 2006), verified from PDF. Complete document (12 pages).

Seven via protection types identified by the IPC D-33d Via Protection Task Group:

| Type | Name | Description | Via-in-Pad? |
|---|---|---|---|
| I | Tented | Dry film mask bridging over via, no fill material | No |
| II | Tented and Covered | Type I + secondary mask covering | No |
| III | Plugged | Material partially penetrates via (screened/roller coated) | No |
| IV | Plugged and Covered | Type III + secondary mask covering | No |
| V | Filled | Full penetration with conductive or non-conductive material | Precursor |
| VI | Filled and Covered | Type V + secondary mask (liquid or dry film) | Yes |
| VII | Filled and Capped | Type V + metallized coating (plated over) | Yes (preferred) |

**Key rules from IPC-4761:**
- **Single-sided** types (Ia, IIa, IIIa, IVa) are **NOT RECOMMENDED** — they leave bare copper exposed on the unprotected side, leading to corrosion
- **Via-in-Pad** designs should use **Type VII** (filled and capped with metallization)
- Bump height from via fill must be ≤0.076 mm (0.003 in) to avoid stencil contact issues
- Dry film thickness for tenting: 0.058 mm as applied, 0.046 mm cured
- LPI (Liquid Photo-Imageable) solder mask thickness: 0.018–0.030 mm

**Application guidelines** (from Table 5-1):
- Preventing solder ball blowout → Types Ib, IIb, IIIb, IVb, V, VI, VII
- Via-in-pad for BGA → Type VII (filled and capped)
- Keeping chemistry from passing through via → Types Ib, IIb, IIIb, IVb, V, VI, VII
- Best thermal conductivity → Types V, VII (use thermally conductive fill ink)
- Preventing migration of adhesives → Types Ib, IIb, IVb, VII

**Usage in design review:** Check the PCB analyzer's via analysis for via-in-pad usage. If BGA/QFN components have vias in their pads, verify the fab notes specify Type VII. Flag unprotected vias under components as a manufacturing risk.

---

## Creepage and Clearance (Insulation Coordination)

Sources: **ECMA-287** (1st edition, June 1999) — Safety of electronic equipment, Tables 3.3–3.5, 3.9. Verified from PDF. ECMA-287 references and derives its values from the **IEC 60664 series** framework (overvoltage categories, pollution degrees, material groups are defined in IEC 60664-1).

These requirements apply to mains-connected equipment and safety-critical insulation. IPC-2221A Table 6-1 is sufficient for most low-voltage PCB designs; creepage/clearance from this section applies when the design involves:
- Mains voltage (AC line input)
- Safety isolation barriers (primary-to-secondary)
- Medical equipment (IEC 60601)
- IT/AV equipment (IEC 62368-1 / ECMA-287)

### Key Concepts

- **Clearance**: Shortest distance in air between two conductive parts (ECMA-287 §2.4)
- **Creepage**: Shortest distance along the surface of insulating material between two conductive parts (ECMA-287 §2.5)
- **Pollution Degree (PD)**: Environmental contamination level (ECMA-287 §2.25–2.28)
  - PD1: No pollution or only dry, non-conductive pollution (sealed components/assemblies)
  - PD2: Normally only non-conductive pollution; occasional temporary conductivity from condensation (default for equipment within scope of ECMA-287)
  - PD3: Conductive pollution or dry non-conductive pollution that becomes conductive due to condensation
- **Overvoltage Category (OVC)**: Position in the power distribution system (defined in IEC 60664-1)
  - OVC I: Equipment with transient protection (signal-level circuits)
  - OVC II: Energy-consuming equipment (appliances, portable tools) — **default for most equipment**
  - OVC III: Equipment in fixed installations (distribution panels)
  - OVC IV: Equipment at the origin of installation (meters, primary overcurrent protection)
- **Material Group**: Based on Comparative Tracking Index (CTI) per IEC 60112 (ECMA-287 §3.2.2)
  - Group I: CTI ≥ 600V
  - Group II: 400V ≤ CTI < 600V
  - Group IIIa: 175V ≤ CTI < 400V
  - Group IIIb: 100V ≤ CTI < 175V
  - FR-4 is typically **Material Group IIIb** (CTI 100-175V) unless high-CTI grade is specified
  - If material group is unknown, assume IIIb (worst case)

### Mains Transient Voltages (for Clearance Determination)

Source: **ECMA-287 Table 3.3**, verified from PDF.

| Nominal AC Mains (line-to-neutral) | OVC I | OVC II | OVC III | OVC IV |
|---|---|---|---|---|
| ≤50 V rms | 330 V pk | 500 V pk | 800 V pk | 1500 V pk |
| ≤100 V rms | 500 V pk | 800 V pk | 1500 V pk | 2500 V pk |
| ≤150 V rms ¹ | 800 V pk | 1500 V pk | 2500 V pk | 4000 V pk |
| ≤300 V rms ² | 1500 V pk | 2500 V pk | 4000 V pk | 6000 V pk |
| ≤600 V rms ³ | 2500 V pk | 4000 V pk | 6000 V pk | 8000 V pk |

¹ Including 120/208 or 120/240 V. ² Including 230/400 or 277/480 V. ³ Including 400/690 V.

Use this table to determine the **required withstand voltage** for clearance lookup (Table 3.4 below).

### Minimum Clearances (up to 2000m altitude)

Source: **ECMA-287 Table 3.4**, verified from PDF.

| Required Withstand Voltage | Basic/Supplementary Insulation | Reinforced Insulation |
|---|---|---|
| ≤400 V peak/dc | 0.2 mm (0.1 mm) | 0.4 mm (0.2 mm) |
| ≤800 V | 0.2 mm | 0.4 mm |
| ≤1000 V | 0.3 mm | 0.6 mm |
| ≤1200 V | 0.4 mm | 0.8 mm |
| ≤1500 V | 0.8 mm (0.5 mm) | 1.6 mm (1 mm) |
| ≤2000 V | 1.3 mm (1 mm) | 2.6 mm (2 mm) |
| ≤2500 V | 2 mm (1.5 mm) | 4 mm (3 mm) |
| ≤3000 V | 2.6 mm (2 mm) | 5.2 mm (4 mm) |
| ≤4000 V | 4 mm (3 mm) | 6 mm |
| ≤6000 V | 7.5 mm | 11 mm |
| ≤8000 V | 11 mm | 16 mm |
| ≤10000 V | 15 mm | 22 mm |
| ≤12000 V | 19 mm | 28 mm |
| ≤15000 V | 24 mm | 36 mm |

Values in parentheses apply only with routine dielectric strength testing under a quality control programme. Linear interpolation permitted between table entries (round up to 0.1 mm).

**Example:** 120V AC mains, OVC II → Table 3.3 gives 1500V peak withstand → Table 3.4 gives 0.8 mm basic, 1.6 mm reinforced clearance.

### Minimum Creepage Distance

Source: **ECMA-287 Table 3.5**, verified from PDF. Values for basic and supplementary insulation. For **reinforced insulation**, use **2× the basic insulation values**.

| Working Voltage (rms/dc) | PD1 (all groups) | PD2, Grp I | PD2, Grp II | PD2, Grp IIIa/IIIb | PD3, Grp I | PD3, Grp II | PD3, Grp IIIa/IIIb |
|---|---|---|---|---|---|---|---|
| 50 V | Use clearance | 0.6 mm | 0.9 mm | 1.2 mm | 1.5 mm | 1.7 mm | 1.9 mm |
| 100 V | value from | 0.7 mm | 1.0 mm | 1.4 mm | 1.8 mm | 2.0 mm | 2.2 mm |
| 125 V | appropriate | 0.8 mm | 1.1 mm | 1.5 mm | 1.9 mm | 2.1 mm | 2.4 mm |
| 150 V | table | 0.8 mm | 1.1 mm | 1.6 mm | 2.0 mm | 2.2 mm | 2.5 mm |
| 200 V | | 1.0 mm | 1.4 mm | 2.0 mm | 2.5 mm | 2.8 mm | 3.2 mm |
| 250 V | | 1.3 mm | 1.8 mm | 2.5 mm | 3.2 mm | 3.6 mm | 4.0 mm |
| 300 V | | 1.6 mm | 2.2 mm | 3.2 mm | 4.0 mm | 4.5 mm | 5.0 mm |
| 400 V | | 2.0 mm | 2.8 mm | 4.0 mm | 5.0 mm | 5.6 mm | 6.3 mm |
| 600 V | | 3.2 mm | 4.5 mm | 6.3 mm | 8.0 mm | 9.0 mm | 10.0 mm |
| 800 V | | 4.0 mm | 5.6 mm | 8.0 mm | 10.0 mm | 11.0 mm | 12.5 mm |
| 1000 V | | 5.0 mm | 7.1 mm | 10.0 mm | 12.5 mm | 14.0 mm | 16.0 mm |

Linear interpolation between entries is permitted (round up to 0.1 mm).

**Common case for FR-4 PCB at 120V AC mains:** Use the 125V row (closest standard voltage). PD2, Material Group IIIb → creepage = 1.5 mm basic, 3.0 mm reinforced. At 230V AC (use 250V row): 2.5 mm basic, 5.0 mm reinforced.

### Minimum Separation for Coated Printed Boards

Source: **ECMA-287 Table 3.9**, verified from PDF. Applies to Type II coated boards (section 3.2.4.2) where ≥80% of the distance between conductive parts is coated. Requires routine dielectric strength testing for double/reinforced insulation.

| Working Voltage (rms/dc) | Basic/Supplementary | Reinforced |
|---|---|---|
| ≤63 V | 0.1 mm | 0.2 mm |
| ≤125 V | 0.2 mm | 0.4 mm |
| ≤160 V | 0.3 mm | 0.6 mm |
| ≤200 V | 0.4 mm | 0.8 mm |
| ≤250 V | 0.6 mm | 1.2 mm |
| ≤320 V | 0.8 mm | 1.6 mm |
| ≤400 V | 1.0 mm | 2.0 mm |
| ≤500 V | 1.3 mm | 2.6 mm |
| ≤630 V | 1.8 mm | 3.6 mm |
| ≤800 V | 2.4 mm | 3.8 mm |
| ≤1000 V | 2.8 mm | 4.0 mm |

Three coating types (ECMA-287 §3.2.4):
- **Type I**: Coating only improves pollution degree to PD1 (use PD1 clearance/creepage)
- **Type II**: Uses reduced separation distances from table above (requires quality control)
- **Type III**: Solid insulation enclosing conductors — no minimum separation distances (requires dielectric testing)

### Determining Required Clearance/Creepage

1. Identify the **working voltage** (highest RMS or DC voltage across the insulation)
2. Determine the **overvoltage category** (typically OVC II for most equipment)
3. Look up the **mains transient voltage** from Table 3.3 (this is the required withstand voltage for clearance)
4. Look up **minimum clearance** from Table 3.4 using the required withstand voltage
5. Determine **pollution degree** (PD2 for most indoor electronics)
6. Determine **material group** (IIIb for standard FR-4)
7. Look up **minimum creepage** from Table 3.5 using working voltage, pollution degree, and material group
8. For reinforced insulation (safety isolation barriers): double the basic creepage values
9. The creepage distance must always be ≥ the applicable clearance distance

**Usage in design review:** For mains-connected or safety-isolated designs, identify the primary-to-secondary boundary on the schematic (usually at the transformer, optocoupler, or isolated DC-DC). Measure the minimum spacing in the PCB layout across this boundary. Compare against both creepage and clearance requirements. Common failure: slot/groove in the PCB at the isolation boundary is present but too narrow, or components bridge the gap.

---

## Safety Standards

### ECMA-287 (verified)

Source: **ECMA-287, 1st edition, June 1999** — Safety of electronic equipment. Verified from PDF.

ECMA-287 is a freely available safety standard for electronic equipment with rated voltage ≤600V RMS, covering office equipment, consumer electronics, and telecom terminal equipment. It addresses:
- Electric shock hazards (§3) — clearance, creepage, solid insulation, coated PCBs
- Mechanical hazards (§4)
- Fire hazards (§5)
- Burn hazards (§6)
- Chemical hazards (§7)
- Radiation (§8)

Key definitions for PCB design review (from §2):
- **Hazardous voltage**: Exceeds ELV criteria (>42.4V AC peak or >60V DC) AND exceeds limited current criteria
- **ELV circuit**: Secondary circuit ≤42.4V AC peak or ≤60V DC, separated from hazardous voltage by basic insulation
- **SELV circuit**: ELV circuit designed so voltage doesn't exceed safe value under normal AND single fault conditions
- **Class I**: Protection by basic insulation + protective earthing
- **Class II**: Protection by double or reinforced insulation (no earth required)

### IEC 62368-1 [UNVERIFIED]

IEC 62368-1 is the safety standard for audio/video, information, and communication technology equipment. It replaces IEC 60950-1 (IT equipment) and IEC 60065 (audio/video equipment). It is the modern successor to standards like ECMA-287/IEC 60950.

Key concepts relevant to PCB design review:
- **Energy source classification**: ES1 (safe), ES2 (limited), ES3 (hazardous)
- **Primary circuit**: Connected to mains (ES3)
- **Secondary circuit**: Isolated from mains via a safety barrier
- **Safeguards**: Basic insulation (1× barrier), supplementary (1× redundant), reinforced (2× single barrier equivalent), double (basic + supplementary)

**Insulation requirements** determine the creepage/clearance at isolation barriers. Reinforced insulation requires 2× the basic insulation clearance. The creepage/clearance tables in ECMA-287 (derived from IEC 60664-1) provide verified reference values that are consistent with IEC 62368-1 requirements.

---

## Land Pattern Density Levels [UNVERIFIED]

Source: IPC-7351B — Generic Requirements for Surface Mount Design and Land Pattern Standard.

**[UNVERIFIED — need IPC-7351B PDF to confirm these values.]**

Three density levels for component footprint land patterns:

| Level | Name | Courtyard Excess | Application |
|---|---|---|---|
| A | Most (Maximum) | 0.50 mm | Hand soldering, prototyping, maximum reliability |
| B | Nominal | 0.25 mm | Typical production, wave or reflow |
| C | Least (Minimum) | 0.10 mm | High-density, miniaturized products |

"Courtyard excess" is the additional clearance around the component body and pads that defines the component's keep-out zone.

**Usage in design review:** The PCB analyzer reports courtyard overlaps. When violations are found, determine the target density level and compare. Level C designs may intentionally have tighter courtyards but require more precise placement equipment.

---

## Current Carrying Capacity (Updated) — IPC-2152

Source: IPC-2152 — Standard for Determining Current Carrying Capacity in Printed Board Design. Context verified from article by **Mike Jouppi** (IPC 1-10b task group chairman, 1999–2016) in *Printed Circuit Design & Fab*, July 2022.

**[PARTIALLY VERIFIED — the formula below is from secondary sources. The article confirms the methodology and limitations but does not reprint the exact formula. The IPC-2152 PDF with full charts/appendix would be needed for complete verification.]**

IPC-2152 supersedes the current capacity charts in IPC-2221A. The IPC-2221A charts originated from NBS (National Bureau of Standards) test data from **1954–1956** (documented in NBS Report 4283). Key historical facts (verified from article):

- The IPC-2221A **external trace chart** was derived from NBS test data on bare conductors
- The IPC-2221A **internal trace chart was NOT based on test data** — it was created by halving the current from the external chart. This was an arbitrary choice whose logic was never documented.
- IPC-2152 test data was collected on boards up to **25A** — calculations above 25A are extrapolations
- Board material, thickness, width, copper weight, and **copper planes** all significantly affect trace temperature rise
- A copper plane 0.005" from the trace causes a **significant drop** in trace temperature rise
- The IPC-2152 design charts are technology-specific: "A single design chart cannot be expected to describe the temperature rise of traces in all printed circuit board applications"
- Mounting configuration (bolted, wedgelocks) also impacts thermal performance but was not tested

Approximate formula (from secondary sources, commonly used in online calculators):

```
A = (117.555 × ΔT^(-0.913) + 1.15) × I^(0.84 × ΔT^(-0.108) + 1.159)
```

Where:
- `A` = cross-sectional area (sq. mils)
- `ΔT` = temperature rise (°C)
- `I` = current (Amperes)

This solves for the required area given current and acceptable temperature rise (the inverse of the IPC-2221A formula which solves for current given area).

Key differences from IPC-2221A:
- Generally more conservative results (larger traces required for the same current)
- Based on modern test data (FR-4, polyimide, and BT boards in multiple thicknesses)
- The IPC-2152 Appendix includes charts for various configurations (Table 1 in article lists 60+ test configurations across FR-4, polyimide, and BT materials, with board sizes from 3×3" to 14×1")
- Correction factors for copper planes: 1oz plane 0.005" from trace, 2oz plane 0.005" from trace
- For **parallel conductors** (multiple traces carrying current side by side), IPC-2221A dramatically overpredicts temperature rise; IPC-2152 provides better guidance

**When to use IPC-2152 vs IPC-2221A:**
- For currents **≤5A** on standard FR-4: IPC-2221A formula is adequate (minor differences)
- For currents **5–25A**: IPC-2152 gives more accurate results, especially with copper planes
- For currents **>25A**: Both are extrapolations — thermal modeling recommended
- For **flex circuits** without copper planes: IPC-2221A internal chart (the one derived by halving) accidentally gives reasonable results
- For safety-critical designs: always use IPC-2152 or thermal modeling

**Usage in design review:** When the IPC-2221A calculation shows a trace is marginal (less than 2× safety margin), note that IPC-2152 should be consulted for a more accurate assessment. If copper planes are present adjacent to the trace, the actual temperature rise may be significantly lower than IPC-2221A predicts.

---

## How to Apply Standards in Design Review

### Automatic Triggers

Include a standards compliance section in the design review report when any of these conditions are met:

1. **High voltage present** (any net >50V DC or >30V AC peak) → Check IPC-2221A Table 6-1 conductor spacing
2. **Mains input** (AC line connection detected) → Check IEC 60664-1 creepage/clearance, IEC 62368-1 insulation requirements
3. **Power traces** (>1A expected on any net) → Verify current capacity per IPC-2221A Section 6.2 or IPC-2152
4. **Safety isolation** (transformer, optocoupler, or isolated DC-DC in schematic) → Check creepage/clearance at barrier per IEC 60664-1
5. **Class 2/3 indicators** (industrial MCU, automotive parts, MIL-spec components, medical ICs) → Apply tighter tolerances per product class
6. **Impedance-controlled signals** (USB, DDR, LVDS, Ethernet) → Verify trace geometry per IPC-2221A Section 6.4
7. **Via-in-pad** (BGA/QFN with vias in pads) → Verify via protection type per IPC-4761

### Report Section Template

When standards checking is triggered, add this section to the report (after the power analysis section):

```markdown
## Standards Compliance

### Product Classification
[Class 1/2/3 determination and rationale]

### Conductor Spacing (IPC-2221A Table 6-1)
| Net Pair | Voltage Difference | Required Spacing (column) | Actual Spacing | Status |
|---|---|---|---|---|
| [net1] / [net2] | [V] | [mm] ([column]) | [mm] | PASS/FAIL |

### Current Capacity (IPC-2221A / IPC-2152)
| Net | Expected Current | Trace Width | Copper Weight | Layer | Calculated Capacity | Margin | Status |
|---|---|---|---|---|---|---|---|
| [net] | [A] | [mm] | [oz] | [ext/int] | [A] | [%] | PASS/FAIL |

### Annular Ring (IPC-2221A Table 9-2)
[Via annular ring analysis results]

### Creepage/Clearance (IEC 60664-1) — if applicable
[Only for mains/safety isolation designs]

### Via Protection (IPC-4761) — if applicable
[Only for via-in-pad designs]
```

### What NOT to Check

- Do not apply IEC 60664-1 creepage/clearance to low-voltage battery/USB-powered designs — IPC-2221A Table 6-1 is sufficient
- Do not require Class 3 tolerances on hobby/prototype boards unless specifically requested
- Do not flag conductor spacing on low-voltage designs (<15V) unless traces are below the absolute minimum (0.05mm internal, 0.1mm external)
- Do not apply IPC-2152 for low-current digital signals — the classic IPC-2221A formula is adequate for non-critical traces

---

## Fab House Capabilities (DFM Tier Classification)

Canonical reference for DFM tier determination. The analyzer (`analyze_pcb.py`) uses these values in its `LIMITS_STD` and `LIMITS_ADV` constants. Report generation must cite values from this table — do not substitute values from training data.

**Source:** JLCPCB capabilities page (verified 2025-01), PCBWay capabilities page (verified 2025-01). Fab capabilities change periodically — check the fab's website for the latest values before making DFM decisions.

### JLCPCB

| Parameter | Standard Tier | Advanced Tier |
|-----------|---------------|---------------|
| Min trace width | 0.127 mm (5 mil) | 0.1 mm (4 mil) |
| Min trace spacing | 0.127 mm (5 mil) | 0.1 mm (4 mil) |
| Min PTH drill | 0.2 mm | 0.15 mm |
| Min via annular ring | 0.125 mm | 0.1 mm |
| Min NPTH drill | 0.5 mm | 0.5 mm |
| Min via diameter (drill+ring) | 0.45 mm | 0.35 mm |
| Max copper weight | 2 oz | 2 oz |
| Max layers | 20 | 20 |
| Min solder mask bridge | 0.1 mm | 0.075 mm |
| Min silkscreen width | 0.15 mm | 0.1 mm |
| Board size (no surcharge) | ≤100×100 mm | ≤100×100 mm |
| Min board dimension | 10 mm | 10 mm |

**Tier determination:** If any metric falls below the standard tier limit, classify as "advanced". If any metric falls below the advanced tier limit, classify as "challenging" (may require manual review or alternative fab).

### PCBWay

| Parameter | Standard |
|-----------|----------|
| Min trace width | 0.1 mm (4 mil) |
| Min trace spacing | 0.1 mm (4 mil) |
| Min PTH drill | 0.2 mm |
| Min annular ring | 0.1 mm |
| Min NPTH drill | 0.8 mm |
| Max copper weight | 6 oz |
| Max layers | 14 |
| Min solder mask bridge | 0.1 mm |
| Board size (no surcharge) | ≤100×100 mm |
