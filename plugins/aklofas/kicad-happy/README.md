# ⚡ kicad-happy

[![CI](https://github.com/aklofas/kicad-happy/actions/workflows/ci.yml/badge.svg)](https://github.com/aklofas/kicad-happy/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Mentioned in Awesome KiCad](https://awesome.re/mentioned-badge.svg)](https://github.com/joanbono/awesome-kicad)

AI-powered design review for KiCad. Analyzes schematics, PCB layouts, and Gerbers. Catches real bugs before you order boards.

Works with **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**, **[OpenAI Codex](https://github.com/openai/codex)**, **[GitHub Copilot CLI](https://docs.github.com/en/copilot)**, and **[Gemini CLI](https://github.com/google-gemini/gemini-cli)**, as a **GitHub Action** for automated PR reviews, or as standalone Python scripts you can run anywhere.

These skills turn your AI coding agent into a full-fledged electronics design assistant that understands your KiCad projects at a deep level: parses schematics and PCB layouts into structured data, cross-references component values against datasheets, detects common design errors, and walks you through the full prototype-to-production workflow.

## 🔬 What it looks like in practice

Point your agent at a KiCad project and it does the rest — parses every schematic and PCB file, traces every net, computes every voltage, and tells you what's wrong before you spend money on boards.

> "Analyze my KiCad project at `hardware/rev2/`"

Here's a condensed example from an open-source robot controller board. The agent found all of this automatically:

**It builds your power tree** — tracing every regulator from input to load, computing output voltages from feedback dividers:

```
VBUS (USB-C / battery input, fused)
├── AP63357 buck (500kHz switching) → 5V
│   └── Feedback: R8/R9 ratio=0.155 → Vout=3.87V
│       Power dissipation: ~0.15W (85% efficiency assumed)
└── RT9080-3.3 LDO → 3.3V
    └── Decoupling: 16 caps, 10.8µF total
```

**It identifies every subcircuit** — not just passives, but the functional blocks and how they connect:

| Subcircuit  | Details                                                                                       |
| ----------- | --------------------------------------------------------------------------------------------- |
| Motor drive | 9x P-MOSFET switches (DMG2305UX), transistor-driven H-bridges                                |
| Filters     | RC signal conditioning at 16Hz, 169Hz, and 1.03kHz (input filtering and debounce)             |
| Lighting    | WS2812B addressable LED chain on GPIO, 60mA estimated draw                                    |
| Sensors     | Onboard sensor interface, crystal oscillator with load cap validation                         |
| Protection  | ESD clamp on USB D+/D-, dual input fuses (0.75A signal, 2.5A motor)                          |

**It audits every connector for ESD protection** — and flags the ones that are exposed:

```
ESD coverage: 19 connectors audited

  USB-C:     ESD clamp on D+/D-  ✓ (partial — 13 signal pins per ground ⚠️)
  Fuse F1:   2.5A motor input  ✓
  Fuse F2:   0.75A signal input  ✓
  ⚠️ 6-pin header:    no protection (exposed signals)
  ⚠️ Motor outputs:   no protection (exposed to back-EMF)
  ⚠️ Servo connectors: no protection (exposed signals)
  ⚠️ Sensor port:     no protection
  ... 19 of 19 connectors have coverage gaps
```

**It validates your passive networks** — computing actual circuit behavior from component values:

| Detection | Components | Computed Value | What It Means |
|-----------|-----------|---------------|---------------|
| RC filter | R21/C31   | fc = 15.9 Hz  | Low-pass for slow analog signal |
| RC filter | R1/C13    | fc = 169 Hz   | Debounce / noise rejection |
| RC filter | R2/C14    | fc = 1.03 kHz | Signal conditioning |
| Feedback  | R8/R9     | ratio = 0.155 | Buck converter output voltage set |
| Divider   | R42/R43   | ratio = 0.500 | Voltage sensing (half) |
| Crystal   | Y1        | CL = 14.0 pF  | Load cap status: ok (target: 18 pF, -22%) |

**It suggests applicable certifications** — based on what it detects in the design:

```
Suggested certifications:
  FCC Part 15 Subpart B (US) — unintentional radiator compliance
  CISPR 32 / CE EMC Directive (EU) — EMC compliance for EU market
```

**It checks production readiness** — BOM lock status, connector ground distribution, decoupling adequacy:

```
BOM lock: 0% — no MPNs assigned (prototype stage)
Decoupling: 5 rails, 34 caps total (132µF motor, 110µF logic, 10.8µF 3.3V)
Connector ground: USB-C has 13:1 signal-to-ground ratio (recommended ≤3:1)
```

For complete examples with all sections, see:
- [Example 1: Robot controller](example-report-1.md) — schematic + PCB + EMC + SPICE, 184 components
- [Example 2: GNSS disciplined oscillator](example-report-2.md) — full workflow including datasheet sync, 296 components, 10 power rails, Ethernet + USB + SMA

For the end-to-end walkthrough from S-expression parsing through signal detection and datasheet cross-referencing, see [How It Works](how-it-works.md).

## 🚀 Install

> [!TIP]
> For detailed installation, upgrade, and troubleshooting guidance across all platforms, have your AI agent read [`install-guidance.md`](install-guidance.md). It covers platform-specific quirks, known bugs, workarounds, and OS-specific issues.

**Claude Code:**

```
/plugin marketplace add aklofas/kicad-happy
/plugin install kicad-happy@kicad-happy
```

> [!NOTE]
> `/plugin update` may not detect new versions due to a [known Claude Code issue](https://github.com/anthropics/claude-code/issues/36317).
> To get the latest version, clear the cache and reinstall:
> ```
> rm -rf ~/.claude/plugins/cache/kicad-happy ~/.claude/plugins/marketplaces/kicad-happy
> /plugin marketplace add aklofas/kicad-happy
> /plugin install kicad-happy@kicad-happy
> ```

**OpenAI Codex:**

Use Codex's built-in skill installer first:

> "Use $skill-installer to install the kicad-happy skills from https://github.com/aklofas/kicad-happy"

If you prefer a manual install, install the skills into `~/.codex/skills/`.

**Google Gemini CLI:**

`gemini skills install <url>` does not recurse into this monorepo's `skills/` directory. Clone and link all 12 at once:

```bash
git clone https://github.com/aklofas/kicad-happy.git
gemini skills link ./kicad-happy/skills
```

Or install all 12 skills directly from the URL using `--path` (requires Gemini CLI ≥ Jan 13 2026):

```bash
for skill in kicad spice emc datasheets bom digikey mouser lcsc element14 jlcpcb pcbway kidoc; do
  gemini skills install https://github.com/aklofas/kicad-happy.git --path skills/$skill
done
```

See [install-guidance.md](install-guidance.md#google-gemini-cli) for workspace-scope installs and upgrade notes.

<details>
<summary><strong>Manual install & other platforms</strong></summary>

**Claude Code (macOS / Linux):**

```bash
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
mkdir -p ~/.claude/skills
for skill in kicad spice emc datasheets bom digikey mouser lcsc element14 jlcpcb pcbway kidoc; do
  ln -sf "$(pwd)/skills/$skill" ~/.claude/skills/$skill
done
```

**OpenAI Codex — global install (macOS / Linux):**

```bash
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
mkdir -p ~/.codex/skills
for skill in kicad spice emc datasheets bom digikey mouser lcsc element14 jlcpcb pcbway kidoc; do
  ln -sf "$(pwd)/skills/$skill" ~/.codex/skills/$skill
done
```

**Windows PowerShell (Codex):**

```powershell
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
"kicad","spice","emc","datasheets","bom","digikey","mouser","lcsc","element14","jlcpcb","pcbway","kidoc" | ForEach-Object {
  New-Item -ItemType SymbolicLink -Path "$HOME\.codex\skills\$_" -Target "$(Get-Location)\skills\$_" -Force | Out-Null
}
```

Note: Windows symlinks may require Developer Mode or elevated privileges.

</details>

The analysis scripts are **pure Python 3.10+** with zero required dependencies. No pip install, no Docker, no KiCad installation needed.

## ⚙️ GitHub Action

Also available as a **GitHub Action** for automated PR reviews. Every push and PR that touches KiCad files gets a commit status check and a structured review comment — power tree, SPICE results, EMC risk, thermal analysis, and more. Optionally chain with Claude for AI-powered natural-language reviews.

See the **[GitHub Action setup guide](github-action.md)** for workflow examples, diff-based PR reviews, and AI-powered review configuration.

## 📦 Skills

| Skill         | What it does                                                                                                                                                                             |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **kicad**     | ⚡ Parse and analyze KiCad schematics, PCB layouts, Gerbers, and PDF reference designs. Automated subcircuit detection, design review, DFM.                                               |
| **spice**     | 🔬 SPICE simulation — generates testbenches for detected subcircuits, validates filter frequencies, opamp gains, divider ratios. Monte Carlo tolerance analysis. ngspice, LTspice, Xyce. |
| **emc**       | 📡 EMC pre-compliance — 44 rule checks for radiated emission risks, PDN impedance, diff pair skew, ESD paths. FCC/CISPR/automotive/military.                                             |
| **datasheets**| 📄 Extract structured specs from datasheet PDFs — pinouts, electrical characteristics, peripherals, topology. Per-MPN caching with quality scoring. Consumed by kicad/emc/spice/thermal/kidoc. |
| **kidoc**     | 📄 **(beta)** Engineering documentation — HDD, CE technical file, ICD, design review, manufacturing, and more. Auto-generated figures, PDF/DOCX/ODT/HTML output.                         |
| **bom**       | 📋 Full BOM lifecycle — analyze, source, price, export tracking CSVs, generate per-supplier order files.                                                                                 |
| **digikey**   | 🔎 Search DigiKey for components and download datasheets via API.                                                                                                                        |
| **mouser**    | 🔎 Search Mouser for components and download datasheets.                                                                                                                                 |
| **lcsc**      | 🔎 Search LCSC for components (production sourcing, JLCPCB parts library).                                                                                                               |
| **element14** | 🔎 Search Newark/Farnell/element14 (one API, three storefronts).                                                                                                                         |
| **jlcpcb**    | 🏭 JLCPCB fabrication and assembly — design rules, BOM/CPL format, ordering workflow.                                                                                                    |
| **pcbway**    | 🏭 PCBWay fabrication and assembly — turnkey with MPN-based sourcing.                                                                                                                    |

## 🖐️ Ask about specific circuits

You don't have to ask for a full design review — just point the agent at whatever you're working on:

> "Check the two capacitive touch buttons on my PCB for routing or placement issues"

> "Is my boost converter loop area going to cause EMI problems?"

> "Trace the enable chain for my power sequencing — is the order correct?"

> "Are the differential pairs on my USB routed correctly?"

The agent runs the analysis scripts, then autonomously digs deeper — tracing nets, analyzing zone fills, calculating clearances, reading datasheets.

## What the analysis covers

| Domain            | What it checks                                                                                                                                                                                                 |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Power**         | Regulator Vout from feedback dividers (~65 Vref families), power sequencing, enable chains, inrush, sleep current                                                                                              |
| **Analog**        | Opamp gain/bandwidth (per-part behavioral models), voltage dividers, RC/LC filters, crystal load caps                                                                                                          |
| **Protection**    | TVS/ESD mapping, reverse polarity FETs, fuse sizing, clamping voltage                                                                                                                                          |
| **Digital**       | I2C pull-up validation with rise time calculation, SPI CS counts, UART voltage domains, CAN termination                                                                                                        |
| **Domain**        | RF chains, Ethernet, HDMI, memory, BMS, motor drivers, sensors, display/touch, audio, LED drivers, debug interfaces, and more (40 detectors total)                                                             |
| **Derating**      | Capacitor voltage (ceramic 50%/electrolytic 80%), IC abs max, resistor power. Commercial/military/automotive profiles. Over-designed component detection.                                                      |
| **PCB**           | Thermal via adequacy, zone stitching, trace width vs current, DFM scoring, impedance, proximity/crosstalk                                                                                                      |
| **Manufacturing** | MPN coverage audit, JLCPCB/PCBWay format export, assembly complexity scoring                                                                                                                                   |
| **Lifecycle**     | Component EOL/NRND/obsolescence alerts, temperature grade audit, alternative part suggestions                                                                                                                  |
| **Thermal**       | Junction temperature estimation for LDOs, switching regulators, shunt resistors. Package Rθ_JA lookup, PCB thermal via correction, proximity warnings for caps near hotspots.                                  |
| **EMC**           | Ground plane voids, decoupling, I/O filtering, switching harmonics, clock routing, diff pair skew, board edge radiation, PDN impedance, ESD paths, crosstalk, thermal derating. FCC/CISPR/automotive/military. |

## 🔬 SPICE simulation

> "Sweep my LC matching network and show me where it actually resonates vs where I designed it"

> "What's the actual phase margin on my opamp filter stage with this TL072?"

> "Run SPICE on everything the analyzer detected and tell me what doesn't look right"

The **spice** skill goes beyond static analysis. It automatically generates SPICE testbenches for detected subcircuits — RC/LC filters, voltage dividers, opamp stages, feedback networks, transistor switches, crystal oscillators — runs them, and reports whether simulated behavior matches calculated values.

For recognized opamps (~100 parts), it uses **per-part behavioral models** with the real GBW, slew rate, and output swing from distributor APIs or a built-in lookup table. When both schematic and PCB exist, it injects **PCB trace parasitics** into the simulation.

```
Simulation: 14 pass, 1 warn, 0 fail
  RC filter R5/C3 (fc=15.9kHz): confirmed, <0.3% error
  Opamp U4A (inverting, gain=-10): 20.0dB confirmed
    Bandwidth 98.8kHz (LM324 behavioral, GBW=1.0MHz)
    Note: signal frequency should stay below 85kHz for <1dB gain error
```

**Monte Carlo tolerance analysis** — run N simulations per subcircuit with randomized component values within tolerance bands. Shows which component dominates output variation:

```
Monte Carlo (N=100): RC filter R5/C3
  fc: 15.9kHz ± 1.8kHz (3σ), spread 22.6%
  Sensitivity: C3 (10%) contributes 68%, R5 (5%) contributes 32%
```

**What-if parameter sweep** — instantly see the impact of component changes without editing the schematic:

```
> "What happens if I change R5 from 10k to 4.7k?"

  RC filter R5/C3: cutoff 1.59kHz → 3.39kHz (+112.8%)
  Voltage divider R5/R6: ratio 0.32 → 0.50 (+56.4%)
```

Requires ngspice, LTspice, or Xyce (auto-detected). Without one, simulation is skipped — the rest of the analysis still works. For the full methodology — see **[SPICE Integration Guide](spice-integration.md)**.

## 📡 EMC pre-compliance

> "Will my board pass FCC Class B? Check for EMC issues."

> "Analyze my switching regulator layout for EMI problems"

> "Check my differential pairs for skew-induced common-mode radiation"

The **emc** skill predicts the most common causes of EMC test failures — ground plane voids, insufficient decoupling, unfiltered I/O cables, switching regulator harmonics, differential pair skew, and more. It operates on the schematic and PCB analyzer output using geometric rule checks and analytical emission formulas (Ott, Paul, Bogatin). When ngspice is available, PDN impedance and EMI filter checks are SPICE-verified for higher accuracy — otherwise analytical models are used as fallback.

```
EMC risk score: 73/100
  CRITICAL: 1 — SPI_CLK crosses ground plane void on In1.Cu
  HIGH:     2 — USB diff pair 5.2mm skew (exceeds 25ps limit),
                no ground via near TVS U5
  MEDIUM:   3 — decoupling cap 7mm from U3, clock on outer layer,
                via stitching gap near J2
  INFO:     4 — cavity resonance at 715 MHz, switching harmonics
                in 30-88 MHz band

Pre-compliance test plan:
  Focus band: 30-88 MHz (12 switching harmonics from U1, U4)
  Highest risk interface: J1 (USB-C, unfiltered, 480 Mbps)
  Probe points: L1 (45.2, 32.1)mm, Y1 (62.0, 18.5)mm
```

44 rule checks across power integrity, signal integrity, and radiation. Includes full-board PDN impedance with power tree analysis — traces impedance from regulator output through PCB traces to IC load points, and detects cross-rail coupling when a downstream switching regulator injects transients onto the upstream rail. Supports FCC, CISPR, automotive (CISPR 25), and military (MIL-STD-461G) standards. Generates a pre-compliance test plan with frequency band priorities, interface risk rankings, and near-field probe points. For the full methodology — see **[EMC Pre-Compliance Guide](emc-precompliance.md)**.

## 📄 Datasheets — sync and extract

> "Sync datasheets for my board at `hardware/rev2/`"

> "What's the EN-pin threshold on the LDO I'm using?"

Datasheets flow through kicad-happy in two stages:

**Sync (download).** Pulls PDFs for every component with an MPN from DigiKey, LCSC, element14, or Mouser into a local `datasheets/` directory. 96% success rate across 240+ manufacturers. Each PDF is verified against the expected part number.

**Extract (parse).** The **datasheets** skill turns those PDFs into structured JSON — pinouts, voltage ratings, electrical characteristics, peripherals, topology, SPICE model coefficients. Extractions are cached per-MPN under `<project>/datasheets/extracted/` and scored on a five-dimension quality rubric. Analyzer skills (`kicad`, `emc`, `spice`, `thermal`, `kidoc`) consume the cache through a shared helper API with trust gates — so a schematic finding tagged `confidence: datasheet-backed` means a scored extraction produced the underlying fact, not a keyword match on the part number.

For the full pipeline — page selection, the quality rubric, the consumer API, and what it deliberately doesn't do — see **[Datasheet Extraction Guide](datasheet-extraction.md)**.

## 📋 BOM management — from schematic to order

> "Source all the parts for my board, I'm building 5 prototypes"

The BOM skill manages the full lifecycle of your bill of materials — using your KiCad schematic as the single source of truth. No separate spreadsheets to keep in sync, no copy-pasting between tabs.

The agent analyzes your schematic to detect which distributor fields are populated (and which naming convention you're using — it handles dozens of variants like `Digi-Key_PN`, `DigiKey Part Number`, `DK`, etc.), identifies gaps, searches distributors to fill them, validates every match, and exports per-supplier order files in the exact upload format each distributor expects.

> "I need a 3.3V LDO that can do 500mA in SOT-223, under $1"

```
AZ1117CH-3.3TRG1 — Arizona Microdevices
  3.3V Fixed, 1A, SOT-223-3
  $0.45 @ qty 1, $0.32 @ qty 100
  In stock: 15,000+

AP2114H-3.3TRG1 — Diodes Incorporated
  3.3V Fixed, 1A, SOT-223
  $0.38 @ qty 1, $0.28 @ qty 100
  In stock: 42,000+
```

## 🏭 Manufacturing

> "Is this board ready to order?"

> "Generate the BOM for JLCPCB assembly"

**Fab release gate** — an automated pre-order checklist that cross-references your schematic, PCB, and Gerber data:

```
Fabrication Release Gate — 8 check categories

  Routing completeness     ✓ PASS  All 240 nets routed
  BOM readiness            ⚠ WARN  3 components missing MPN
  DFM compliance           ✓ PASS  No spacing violations, standard tier compatible
  Documentation            ✓ PASS  Title block, revision, fab notes present
  Schematic ↔ PCB match    ✓ PASS  296 components matched, 0 orphans
  Gerber verification      ✓ PASS  All layers present, drill file valid
  Thermal analysis         ⚠ WARN  U3 junction temp 92°C (margin: 18°C)
  EMC pre-compliance       ⚠ WARN  Score 73/100 — 2 HIGH findings

  Result: CONDITIONAL PASS (3 warnings to review before ordering)
```

**BOM export** — cross-references LCSC part numbers, formats to JLCPCB's exact spec, flags basic vs extended parts. Per-supplier upload files — DigiKey bulk-add CSV, Mouser cart format, LCSC BOM — with quantities already computed for your board count + spares.

## 📄 KiDoc — Engineering documentation (beta)

> "Generate an HDD for my board"

> "Create a CE technical file for this design"

The **KiDoc** skill generates professional engineering documents from your KiCad project. It auto-runs all analyses (schematic, PCB, EMC, thermal), renders publication-quality figures, and produces a structured markdown scaffold that you fill in with engineering narrative — then outputs PDF, DOCX, ODT, or HTML.

**8 document types:**

| Document              | What it covers                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------- |
| **HDD**               | Hardware Design Description — power, signal, analog, thermal, EMC, PCB, BOM               |
| **CE Technical File** | EU compliance — product ID, essential requirements, harmonized standards, risk assessment |
| **Design Review**     | Review package with summary, action items, go/no-go assessment                            |
| **ICD**               | Interface control — connector details, electrical characteristics, signal levels          |
| **Manufacturing**     | Assembly overview, PCB fab notes, assembly instructions, test procedures                  |
| **Power Analysis**    | Power distribution, regulator design, thermal margins, sequencing                         |
| **Schematic Review**  | Focused schematic-only review with signal analysis                                        |
| **EMC Report**        | Pre-compliance findings, mitigation recommendations, test plan                            |

**11 auto-generated figure types:**

- Power distribution trees
- System architecture block diagrams
- Bus topology (I2C/SPI/UART/CAN)
- Connector pinout diagrams
- Schematic overviews
- Subsystem crops
- PCB layer views
- Thermal margin charts
- EMC severity charts
- SPICE validation scatter plots
- Monte Carlo histograms

```
> "Generate documentation for my board at hardware/rev2/"

  Analyzing schematic... 187 components, 12 regulators, 4 buses
  Analyzing PCB... 6-layer, 56x56mm, routing complete
  EMC pre-compliance... 73/100, 10 findings
  Thermal analysis... 3 components above 85°C
  Generating figures... 23 SVGs (power tree, architecture, 14 pinouts, ...)
  Building scaffold... HDD.md (14 sections, 96 lines)
  Generating PDF... HDD.pdf (24 pages)
```

The scaffold separates auto-generated data sections (component tables, power trees, signal analysis) from narrative sections where you write engineering prose. On regeneration, data sections update automatically while your narrative is preserved. A built-in context builder prepares focused data summaries for each section so the agent can help write the narrative.

Figures use a prepare/render pipeline with hash-based caching — if the analysis data hasn't changed, figures aren't re-rendered.

**Beta status:** KiDoc is an early skill that is being actively developed. The figure engine and document pipeline are functional and tested against 100+ real projects, but expect rough edges — some figure types may not render cleanly for all designs, narrative context quality varies by document type, and the PDF styling is still being refined. Feedback and bug reports welcome.

For the full guide — all 8 document types, 12 figure generators, output formats, configuration options, and the prepare/edit/render workflow — see [KiDoc Documentation](kidoc-documentation.md).

## 🗺️ Workflow

1. **Design** your schematic and lay out the PCB in KiCad
2. **Sync datasheets** — the agent downloads PDFs and extracts structured specs for every MPN
3. **Design review** — the agent runs schematic, PCB, cross-analysis, EMC, SPICE, and thermal analyzers, cross-references against datasheets, and writes a structured report with findings ranked by severity
4. **Iterate** — fix issues, re-run the review, compare against the previous run with built-in diff analysis
5. **Source** components from DigiKey/Mouser (prototype) or LCSC (production)
6. **Export** BOM + per-supplier order files for your assembler
7. **Order** from JLCPCB or PCBWay with generated BOM/CPL files

Or set up the [GitHub Action](github-action.md) and get automated analysis on every PR.

## Optional setup

**SPICE simulator** (for the spice skill): `apt install ngspice` or LTspice or Xyce. Auto-detected.

**API keys** (for distributor skills — falls back to web search without them):

| Service   | Env variable                                 | Notes                                                   |
| --------- | -------------------------------------------- | ------------------------------------------------------- |
| DigiKey   | `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET` | [developer.digikey.com](https://developer.digikey.com/) |
| Mouser    | `MOUSER_SEARCH_API_KEY`                      | My Mouser → APIs                                        |
| element14 | `ELEMENT14_API_KEY`                          | [partner.element14.com](https://partner.element14.com/) |
| LCSC      | *none*                                       | Free community API                                      |

**Optional Python packages**: `requests` (better HTTP), `playwright` (JS-heavy datasheet sites), `pdftotext` (PDF text extraction).

## ✅ KiCad version support

| Version  | Schematic                     | PCB  | Gerber |
| -------- | ----------------------------- | ---- | ------ |
| KiCad 10 | Full                          | Full | Full   |
| KiCad 9  | Full                          | Full | Full   |
| KiCad 8  | Full                          | Full | Full   |
| KiCad 7  | Full                          | Full | Full   |
| KiCad 6  | Full                          | Full | Full   |
| KiCad 5  | Full (legacy `.sch` + `.lib`) | Full | Full   |

## v1.3.1 — Bug fixes + Connectivity

- Fix `format-report.py` crash on dict-shaped `power_rails` (issues #16, #20).
- Add `.kicad_pro` `top_level_sheets` support for Altium flat multi-page imports (#19).
- PCB connectivity rewrite: track-as-node model, compound pads, `*.Cu` wildcards.
- Fix pad rotation sign; unify analysis-dir resolution.
- KH-147: suppress LED-driver false positives when the current resistor's value field has a suffix the parser can't read (e.g. `215k_0402_…`).
- Bump minimum Python to 3.10; add cross-agent install guidance (Claude Code, Codex, Gemini).

## 🎯 v1.3 — Harmonized Analysis

v1.2 made findings trustworthy. v1.3 makes them uniform and traceable. **Every analyzer** — schematic, PCB, Gerber, thermal, EMC, cross-analysis, SPICE, lifecycle — now produces the same flat `findings[]` format with rich envelopes (`detector`, `rule_id`, `severity`, `confidence`, `evidence_source`, `recommendation`, `report_context`). Every finding carries its own provenance. One schema to query, filter, export, and audit.

168 commits. 22 new detectors. Trust infrastructure (confidence + evidence taxonomies, trust_summary, per-finding provenance). PCB intelligence (union-find connectivity, 6 cross-domain checks, 7 DFM/assembly checks). Stage/audience filtering. Datasheet pipeline promoted to its own skill. KiCad 10 format compatibility. Full harness regression at 2M+ assertions, 99.98% pass.

**Highlights:**

| Category | Capabilities |
| --- | --- |
| **Harmonized output** | All 8 analyzers produce `{analyzer_type, schema_version, summary, findings[], trust_summary}`. Flat finding envelope with detector/rule_id/severity/confidence/evidence_source/recommendation/report_context. `signal_analysis` wrapper removed. |
| **Trust infrastructure** | Confidence taxonomy (`deterministic`, `heuristic`, `datasheet-backed`). Evidence source taxonomy. `make_provenance()` on all 61 detectors. `trust_summary` rollup on every output. Risk scores weight heuristic findings 0.5x. |
| **22 new detectors** | 7 validation (pull-ups, voltage mismatch, protocol buses, power sequencing, LED resistor, feedback stability) + 6 domain (wireless, transformer SMPS, I2C conflicts, supercaps, PWM LEDs, headphone jacks) + 9 audit (SS-001/002 sourcing, DS-001/002/003 datasheet coverage, RS-001/002 rail sources, LB-001 label aliases, PP-001 power pin DC paths). |
| **PCB intelligence** | Union-find copper connectivity graph. 6 new cross-domain checks: critical net routing, return path continuity, trace width vs current, power island detection, voltage plane splits, differential pair return paths. |
| **PCB DFM/assembly** | 7 new checks: fiducial presence, test point coverage, orientation consistency, silkscreen-pad overlap, via-in-pad tenting, board-edge via clearance, keepout violations. |
| **Stage/audience filtering** | `--stage schematic\|layout\|pre_fab\|bring_up` and `--audience designer\|reviewer\|manager` flags on all analyzers. |
| **Datasheet pipeline** | Promoted to its own top-level skill. Structured per-MPN extraction cache, heuristic page selection, five-dimension quality scoring, consumer helper API with trust gates. |
| **Cross-analysis** | `cross_analysis.py` consumes schematic + PCB JSON. 6 cross-domain checks: connector current, ESD gaps, decoupling adequacy, 3-way schematic/PCB cross-validation. |
| **KiCad 10 compat** | KH-318 via type detection (blind/buried/micro now correctly classified, buried split out in KiCad 10). KH-319 `(hide yes)` boolean form handled. |
| **Schema hardening** | `schema_version: "1.3.0"` on every output. `--schema` synced to real emitted JSON on all analyzers. Deterministic `findings[]` ordering. Stable `detection_id`. |
| **Tools** | `summarize_findings.py` (cross-run rollup), `export_issues.py` (GitHub Issues), `--mpn-list` batch mode on all 4 distributor sync scripts. |
| **Test corpus** | 5,829 repos, 2M+ regression assertions at 99.98% pass, 972 unit tests, schema drift regression across all 8 analyzers. |

See the full [CHANGELOG](CHANGELOG.md) for details.

## 🎯 v1.2 — Trust + Reach

v1.1 shipped the analysis engine. v1.2 makes it something you'd actually hand to a teammate. **Trust** — every finding now carries a confidence label, can be suppressed with a reason, and is cross-checked against datasheets and a 5,829-project regression corpus. When it says there's a problem, you can believe it. **Reach** — first-class Codex support, analysis caching with manifests, and CI infrastructure mean it works wherever your team works, not just on one developer's machine.

102 commits. New skill: **KiDoc** (beta) for engineering documentation. 15+ new domain detectors. Datasheet verification bridge. What-if sweep/tolerance/fix tools. Full protocol electrical parameter coverage. Cross-verification. Analysis cache. 25 bug fixes.

**Highlights:**

| Category | Capabilities |
| --- | --- |
| **Codex support** | First-class OpenAI Codex support with agent-neutral docs, skill-installer compatibility, and global installs via `~/.codex/skills/`. |
| **KiDoc (beta)** | 8 document types, 12 figure generators, PDF/DOCX/ODT/HTML output. Scaffolds with auto-updating data + narrative placeholders. |
| **Datasheet verification** | Pin voltage enforcement, required external component checks, per-IC decoupling validation against manufacturer specs. |
| **What-if tools** | Sweep tables, tolerance analysis, fix suggestions with E-series snapping, EMC impact preview, PCB parasitic awareness. |
| **Protocol checks** | I2C, SPI, UART, USB, Ethernet, HDMI, LVDS, CAN — complete electrical parameter validation. |
| **Cross-verification** | 7 schematic-to-PCB cross-checks: component matching, diff pairs, power traces, decoupling, thermal vias. |
| **Professional checks** | Fab notes, silkscreen completeness, BOM lock, connector ground distribution, certification suggestions. |
| **Test corpus** | 5,829 repos, 1.2M+ regression assertions at 100% pass, 400+ unit tests, 0 open issues. |

## 🎯 v1.1 — EMC Pre-Compliance + Analysis Toolkit

New skill: **EMC pre-compliance risk analysis** — predicts the most common causes of EMC test failures from your KiCad schematic and PCB layout. Plus four new analysis tools for tolerance, diffing, thermal, and what-if exploration.

**What's in v1.1:**

| Category                  | Capabilities                                                                                                                                                                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **EMC pre-compliance**    | 44 rule checks across ground plane integrity, decoupling, I/O filtering, switching harmonics, diff pair skew, PDN impedance, ESD paths, crosstalk, board edge radiation, thermal-EMC, shielding, and magnetic leakage from switching inductors. SPICE-enhanced when ngspice is available. FCC/CISPR/automotive/military. |
| **Plugin install**        | Available as a Claude Code plugin marketplace — `/plugin marketplace add aklofas/kicad-happy`.                                                                                                                                                                            |
| **Monte Carlo tolerance** | `--monte-carlo N` runs N simulations with randomized component values within tolerance bands. Reports 3σ bounds and per-component sensitivity analysis.                                                                                                                   |
| **Design diff**           | Compares two analysis JSONs — component changes, signal parameter shifts, EMC finding deltas. GitHub Action `diff-base: true` for automatic PR comparison.                                                                                                                |
| **Thermal hotspots**      | Junction temperature estimation for LDOs, switching regulators, shunt resistors. Package Rθ_JA lookup, thermal via correction, proximity warnings.                                                                                                                        |
| **No-connect detection**  | Correctly identifies NC markers, library-defined NC pins, and KiCad `unconnected` pin types. Eliminates false floating-pin warnings across 2,253 files.                                                                                                                   |
| **Code audit**            | 22 bug fixes (trace inductance 25x overestimate, PDN target impedance, regulator voltage suffix parser, inner-layer reference planes, and more). Full AnalysisContext migration for cleaner internals.                                                                    |
| **Validation**            | 6,853 EMC analyses across 1,035 repos (zero crashes), 96 equations verified against primary sources, 404K+ regression assertions at 100% pass rate.                                                                                                                       |

## 🎯 v1.0 — First Stable Release

This is the first stable release of kicad-happy. It marks the point where every piece of the analysis pipeline — schematic parsing, PCB layout review, Gerber verification, SPICE simulation, datasheet cross-referencing, BOM sourcing, and manufacturing prep — has been built, tested against 1,035 real-world KiCad projects, and validated with 294K+ regression assertions. Zero analyzer crashes across the full corpus.

This isn't a beta or a preview. It's production-ready. If you're designing boards in KiCad, this is the version to start with.

**What's in v1.0:**

| Category                 | Capabilities                                                                                                                                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Schematic analysis**   | 25+ subcircuit detectors (regulators, filters, opamps, bridges, protection, buses, crystals, current sense) with mathematical verification                                                                           |
| **Voltage derating**     | Ceramic (50%), electrolytic (80%), tantalum capacitors. IC absolute max voltage. Resistor power dissipation. Commercial, military, and automotive profiles. Over-designed component detection for cost optimization. |
| **Protocol validation**  | I2C pull-up value and rise time calculation, SPI chip select counts, UART voltage domain crossing, CAN 120Ω termination                                                                                              |
| **Op-amp checks**        | Bias current path detection, capacitive output loading, high-impedance feedback warning, unused channel detection for dual/quad parts                                                                                |
| **SPICE simulation**     | Auto-generated testbenches for 17 subcircuit types, per-part behavioral models (~100 opamps), PCB parasitic injection, ngspice/LTspice/Xyce                                                                          |
| **Datasheet extraction** | Structured extraction cache with quality scoring, heuristic page selection, SPICE spec integration                                                                                                                   |
| **Lifecycle audit**      | Component EOL/NRND/obsolescence alerts from 4 distributor APIs, temperature grade auditing (commercial/industrial/automotive/military), alternative part suggestions                                                 |
| **PCB layout**           | DFM scoring, thermal via adequacy, impedance calculation, differential pair matching, proximity/crosstalk, zone stitching, tombstoning risk                                                                          |
| **BOM sourcing**         | DigiKey, Mouser, LCSC, element14 — per-supplier order file export, pricing comparison, datasheet sync (96% download success rate)                                                                                    |
| **Manufacturing**        | JLCPCB and PCBWay format export, design rule validation, rotation offset tables, basic vs extended parts classification                                                                                              |
| **GitHub Action**        | Two-tier automated PR reviews: deterministic analysis (free, no API key) + optional AI-powered review via Claude (`ANTHROPIC_API_KEY`). Datasheet download from LCSC (free) and optional DigiKey/Mouser/element14.   |
| **KiCad support**        | KiCad 5 through 10, including legacy `.sch` format. Single-sheet and multi-sheet hierarchical designs.                                                                                                               |

## 🧪 Test harness

Everything above was validated against a [corpus of 5,800+ open-source KiCad projects](https://github.com/aklofas/kicad-happy-testharness) — the kind of designs real engineers actually build. The corpus spans hobby boards, production hardware, motor controllers, RF frontends, battery management systems, IoT devices, audio amplifiers, and everything in between. KiCad 5 through 10. Single-sheet and multi-sheet hierarchical. 2-layer through 6-layer. For full methodology and reproducibility instructions, see [VALIDATION.md](VALIDATION.md).

**The numbers:**

| Metric                       | Value                                        |
| ---------------------------- | -------------------------------------------- |
| Repos in corpus              | 5,800+                                       |
| Schematic files analyzed     | 6,845 (100% success)                         |
| PCB files analyzed           | 3,498 (99.9%)                                |
| Gerber directories analyzed  | 1,050 (100% success)                         |
| EMC pre-compliance analyses  | 6,853 (100% success, 141K+ findings)         |
| Components parsed            | 312,956                                      |
| Nets traced                  | 531,418                                      |
| SPICE subcircuit simulations | 30,646 across 17 types                       |
| SPICE-verified EMC findings  | 169 (PDN impedance via ngspice)              |
| Regression assertions        | 808K+ at 100% pass rate                      |
| Equations tracked & verified | 86 with source citations                     |
| Bugfix regression guards     | 67 (100% pass — no fixed bugs have returned) |
| Closed analyzer issues       | 193                                          |

Three-layer regression testing catches drift at every level:

| Layer          | What it catches                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------- |
| **Baselines**  | Output drift between analyzer versions                                                            |
| **Assertions** | Hard regressions on known-good results (component counts, detected subcircuits, signal paths)     |
| **LLM review** | Semantic issues deterministic checks miss — findings get promoted to machine-checkable assertions |

## 🎨 Why KiCad?

This project exists because **KiCad is absolutely incredible**. Fully open-source, cross-platform, backed by CERN, with a community that ships features faster than most commercial tools. It's used everywhere from weekend hobby projects to production hardware at real companies.

But what makes KiCad truly special for AI-assisted design — and the entire reason this project can exist — is its **beautifully open file format**. Every schematic, PCB layout, symbol, and footprint is stored as clean, human-readable S-expressions. No proprietary binary blobs. No vendor lock-in. No $500 "export plugin" just to read your own data.

This means your AI agent can read your KiCad files directly, understand every component, trace every net, and reason about your design at the same level a human engineer would. No KiCad export plugins, no export steps, no intermediary formats. Just your KiCad project and a terminal.

Try doing that with Altium or OrCAD. 😉

## 📜 License

MIT — see [CHANGELOG.md](CHANGELOG.md) for release history and [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

*Built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [OpenAI Codex](https://github.com/openai/codex).* 🤖
