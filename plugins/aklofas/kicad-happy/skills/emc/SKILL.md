---
name: emc
description: >-
  EMC pre-compliance risk analysis for KiCad PCB designs — 18 check categories,
  44 rule IDs covering ground planes, decoupling, I/O filtering, switching
  harmonics, clock routing, differential pair skew, board edge radiation, PDN
  impedance, return paths, crosstalk, ESD protection, shielding, and magnetic
  leakage from switching inductors. Produces
  severity-ranked risk report with pre-compliance test plan. Supports FCC
  Part 15, CISPR 32, CISPR 25 (automotive), MIL-STD-461G. SPICE-enhanced when
  available. Use when the user asks about EMC, EMI, radiated/conducted
  emissions, FCC compliance, CE marking, CISPR, ground plane issues, decoupling
  strategy, clock routing EMC, switching noise, differential pair skew, or
  whether their board will pass EMC testing. Also for "will this pass FCC?",
  "check my EMC", "is my ground plane okay?", "check my decoupling", or
  "generate an EMC test plan".
---

# EMC Pre-Compliance Skill

Automated EMC risk analysis for KiCad PCB designs. Identifies the most common causes of EMC test failures using geometric rule checks, analytical emission formulas, and optional SPICE simulation.

**This is a risk analyzer, not a compliance predictor.** It catches ~70% of common EMC design mistakes before fabrication. It cannot guarantee FCC/CISPR compliance — only a calibrated measurement in an accredited lab can do that. But it can reduce the first-spin failure rate from ~50% toward ~20-30%, potentially saving $5K-$50K per avoided board respin.

## Related Skills

| Skill | Purpose |
|-------|---------|
| `kicad` | Schematic/PCB analysis — produces the analyzer JSON this skill consumes |
| `kicad` (thermal) | Thermal hotspot analysis — MLCC derating and ferrite/inductor overheating findings can amplify EMC decoupling and filter issues (an over-stressed MLCC degrades; a hot ferrite drifts impedance). Worth cross-checking when EMC flags DC-001/DC-002 or EF-001/EF-002. |
| `spice` | SPICE simulation — provides simulator backend for SPICE-enhanced PDN/filter checks |

**Handoff guidance:** Run the `kicad` skill's `analyze_schematic.py` and `analyze_pcb.py` first — this skill consumes their JSON output. Use `--full` on the PCB analyzer for best results (enables per-track coordinates for ground plane crossing, edge proximity, and return path checks). During a design review, run EMC analysis after the schematic/PCB analyzers, SPICE simulation, and thermal analysis, then incorporate EMC findings into the report.

## Requirements

- **Python 3.10+** — stdlib only, no pip dependencies
- **Schematic analyzer JSON** — from `analyze_schematic.py --output`
- **PCB analyzer JSON** — from `analyze_pcb.py --full --output` (recommended with `--full`)
- **SPICE simulator** *(optional)* — ngspice, LTspice, or Xyce for SPICE-enhanced PDN/filter checks. Auto-detected. Without one, analytical models run unchanged.

## Workflow

### Step 1: Run the analyzers

```bash
python3 <kicad-skill-path>/scripts/analyze_schematic.py design.kicad_sch --analysis-dir analysis/
python3 <kicad-skill-path>/scripts/analyze_pcb.py design.kicad_pcb --full --analysis-dir analysis/
```

### Step 2: Run EMC analysis

Pass `--analysis-dir analysis/` — the script auto-resolves `schematic.json`
and `pcb.json` from the manifest's current run, and writes `emc.json` into
the same folder so the manifest tracks it.

```bash
# Recommended: auto-resolve inputs from the current run
python3 <skill-path>/scripts/analyze_emc.py --analysis-dir analysis/

# Equivalent — explicit paths still accepted (and required if you want to
# point at a non-current run or override one input)
python3 <skill-path>/scripts/analyze_emc.py \
    --schematic analysis/<run_id>/schematic.json \
    --pcb analysis/<run_id>/pcb.json \
    --analysis-dir analysis/

# One-off JSON (bypasses the cache)
python3 <skill-path>/scripts/analyze_emc.py --schematic schematic.json --pcb pcb.json --output emc.json

# SPICE-enhanced (improved PDN and filter accuracy)
python3 <skill-path>/scripts/analyze_emc.py --analysis-dir analysis/ --spice-enhanced

# Select target standard
python3 <skill-path>/scripts/analyze_emc.py --analysis-dir analysis/ --standard cispr-class-b

# Select target market (sets all applicable standards)
python3 <skill-path>/scripts/analyze_emc.py --analysis-dir analysis/ --market eu

# Filter by severity
python3 <skill-path>/scripts/analyze_emc.py --analysis-dir analysis/ --severity high

# Human-readable text output
python3 <skill-path>/scripts/analyze_emc.py --analysis-dir analysis/ --text
```

### Step 3: Interpret results

Read the JSON report and incorporate findings into the design review. Each finding has a severity, rule ID, description, and actionable recommendation. See "Interpreting Results" below.

## What Gets Checked

44 rule IDs across 18 categories. Each rule has a specific threshold, rationale, and source citation — see `references/pcb-emc-rules.md` for full details.

| Category | Rules | What it detects |
|----------|-------|-----------------|
| **Ground plane** | GP-001 to GP-005 | Signal crossing voids, zone fragmentation, missing ground planes, low fill ratio, multiple ground domains |
| **Decoupling** | DC-001 to DC-003 | Cap too far from IC, IC with no decoupling cap, cap too far from via |
| **I/O filtering** | IO-001, IO-002 | Connector without filtering, insufficient ground pins |
| **Switching EMC** | SW-001 to SW-003 | Harmonic overlap, switching node copper area, input cap loop area |
| **Clock routing** | CK-001 to CK-003 | Clock on outer layer, long trace, clock near connector |
| **Via stitching** | VS-001 | Ground via spacing exceeds λ/20 at highest frequency |
| **Stackup** | SU-001 to SU-003 | Adjacent signal layers, signal far from reference plane, thin interplane capacitance |
| **Diff pair** | DP-001 to DP-004 | Intra-pair skew vs protocol limits, CM radiation, reference plane change, outer layer routing |
| **Board edge** | BE-001 to BE-003 | Signal near edge, incomplete ground pour ring, connector area stitching |
| **PDN impedance** | PD-001 to PD-004 | Anti-resonance peaks, distributed rail impedance at IC load points, cross-rail coupling from downstream switching regulators |
| **Return path** | RP-001 | Layer transition via without nearby ground stitching via |
| **Crosstalk** | XT-001 | 3H spacing violation, aggressor-victim pairs |
| **EMI filter** | EF-001, EF-002 | Filter cutoff too close to switching frequency (analytical or SPICE insertion loss) |
| **ESD path** | ES-001, ES-002 | TVS too far from connector, insufficient ground vias near TVS |
| **Thermal-EMC** | TH-001, TH-002 | MLCC DC bias derating (SRF shift), ferrite near heat source |
| **Shielding** | SH-001 | Connector aperture slot resonance near emission source |
| **Emission estimates** | EE-001, EE-002 | Board cavity resonance, switching harmonic envelope |

**Advisory outputs** (not findings):
- **Pre-compliance test plan** — frequency band prioritization, interface risk ranking, near-field probe points
- **Regulatory coverage** — market-to-standards mapping, coverage matrix (what the tool checks vs what requires lab testing)

## Output Format

```json
{
  "summary": {
    "total_checks": 42,
    "critical": 2, "high": 5, "medium": 8, "low": 12, "info": 15,
    "emc_risk_score": 73
  },
  "target_standard": "fcc-class-b",
  "findings": [
    {
      "category": "ground_plane",
      "severity": "CRITICAL",
      "rule_id": "GP-001",
      "title": "Signal crosses ground plane void",
      "description": "Net SPI_CLK crosses a 3.2mm gap in GND on In1.Cu",
      "components": ["U3", "U7"],
      "nets": ["SPI_CLK"],
      "recommendation": "Route around the gap, or fill the void"
    }
  ],
  "per_net_scores": [
    {"net": "SPI_CLK", "score": 67, "finding_count": 3, "rules": ["GP-001", "CK-001", "BE-001"]}
  ],
  "test_plan": {
    "frequency_bands": [{"band": "30-88 MHz", "risk_level": "high", "source_count": 12}],
    "interface_risks": [{"connector": "J1", "protocol": "USB", "risk_score": 8}],
    "probe_points": [{"ref": "L1", "x": 45.2, "y": 32.1, "reason": "switching inductor"}]
  },
  "regulatory_coverage": {
    "market": "us",
    "applicable_standards": ["FCC Part 15 Class B"],
    "coverage_matrix": [{"standard": "...", "coverage": "partial", "note": "..."}]
  }
}
```

### Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| **CRITICAL** | Almost certain to cause EMC failure | Must fix before fabrication |
| **HIGH** | Very likely to cause issues | Strongly recommend fixing |
| **MEDIUM** | May cause issues depending on specifics | Review and assess |
| **LOW** | Minor risk, good practice | Fix if convenient |
| **INFO** | Informational — frequencies, estimates | Useful for lab prep |

### Risk Score

Each rule ID contributes at most 3 findings to the score (worst severity first). This prevents per-net rules like GP-001 from saturating the score on 2-layer boards. All findings are still reported — only the score is capped.

`penalty = sum(worst 3 per rule × severity weight)`, `score = max(0, 100 - penalty)`. Scores below 50 indicate significant EMC risk.

## Interpreting Results

**Ground plane findings** — Any CRITICAL finding (signal crossing a void) is almost always a real problem. Fix unconditionally.

**Decoupling findings** — Distance-based findings have moderate false positive rates. A cap at 6mm may be fine for a low-speed IC but problematic for a 100MHz clock buffer. Use frequency context to prioritize.

**I/O filtering** — Highly relevant for cable-connected products. For board-to-board connections inside an enclosure, the risk is lower.

**Diff pair findings** — Protocol-specific skew limits are well-defined. USB HS (25ps), PCIe (5ps), Ethernet (50ps). Findings exceeding these limits are real issues.

**PDN findings** — Anti-resonance peaks are real and cause voltage droop. SPICE-verified findings are more accurate than analytical. If a peak is flagged, add a capacitor with SRF near the peak frequency.

**Emission estimates** — Order-of-magnitude estimates (±10-20 dB). Use them to prioritize frequency bands for pre-compliance testing, not to predict pass/fail.

## EMC Standards

| Standard | Flag | Use Case |
|----------|------|----------|
| FCC Part 15 Class B | `fcc-class-b` | US residential (default) |
| FCC Part 15 Class A | `fcc-class-a` | US commercial/industrial |
| CISPR 32 Class B | `cispr-class-b` | International (EU CE marking) |
| CISPR 32 Class A | `cispr-class-a` | International commercial |
| CISPR 25 Class 5 | `cispr-25` | Automotive (strictest) |
| MIL-STD-461G RE102 | `mil-std-461` | Military/defense |

The `--market` flag maps markets to all applicable standards: `us`, `eu`, `automotive`, `medical`, `military`.

## Limitations

- Cannot predict absolute emission levels better than ±10-20 dB
- Cannot account for enclosure effects (shielding, apertures, seams)
- Cannot predict cable radiation without knowing external cable routing
- Cannot replace full-wave simulation for complex geometries
- Cannot guarantee compliance — only accredited lab measurement can
