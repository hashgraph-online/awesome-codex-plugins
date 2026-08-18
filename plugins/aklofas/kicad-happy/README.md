# ⚡ kicad-happy

[![CI](https://github.com/aklofas/kicad-happy/actions/workflows/ci.yml/badge.svg)](https://github.com/aklofas/kicad-happy/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Mentioned in Awesome KiCad](https://awesome.re/mentioned-badge.svg)](https://github.com/joanbono/awesome-kicad)

AI-powered design review for KiCad. Analyzes schematics, PCB layouts, and Gerbers. Catches real bugs before you order boards.

Works with **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)**, **[OpenAI Codex](https://github.com/openai/codex)**, **[GitHub Copilot CLI](https://docs.github.com/en/copilot)**, **[Gemini CLI](https://github.com/google-gemini/gemini-cli)**, and **[opencode](https://github.com/sst/opencode)**, as a **GitHub Action** for automated PR reviews, or as standalone Python scripts you can run anywhere.

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

`gemini skills install <url>` does not recurse into this monorepo's `skills/` directory. Clone and link all 11 at once:

```bash
git clone https://github.com/aklofas/kicad-happy.git
gemini skills link ./kicad-happy/skills
```

Or install all 11 skills directly from the URL using `--path` (requires Gemini CLI ≥ Jan 13 2026):

```bash
for skill in kicad spice emc datasheets bom digikey mouser lcsc element14 jlcpcb pcbway; do
  gemini skills install https://github.com/aklofas/kicad-happy.git --path skills/$skill
done
```

See [install-guidance.md](install-guidance.md#google-gemini-cli) for workspace-scope installs and upgrade notes.

**opencode:**

```bash
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
opencode
```

The repo ships `.opencode/opencode.json`, which opencode auto-discovers and uses to load all 11 skills from `./skills/`. For global availability across all projects, see [install-guidance.md](install-guidance.md#opencode).

<details>
<summary><strong>Manual install & other platforms</strong></summary>

**Claude Code (macOS / Linux):**

```bash
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
mkdir -p ~/.claude/skills
for skill in kicad spice emc datasheets bom digikey mouser lcsc element14 jlcpcb pcbway; do
  ln -sf "$(pwd)/skills/$skill" ~/.claude/skills/$skill
done
```

**OpenAI Codex — global install (macOS / Linux):**

```bash
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
mkdir -p ~/.codex/skills
for skill in kicad spice emc datasheets bom digikey mouser lcsc element14 jlcpcb pcbway; do
  ln -sf "$(pwd)/skills/$skill" ~/.codex/skills/$skill
done
```

**Windows PowerShell (Codex):**

```powershell
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
"kicad","spice","emc","datasheets","bom","digikey","mouser","lcsc","element14","jlcpcb","pcbway" | ForEach-Object {
  New-Item -ItemType SymbolicLink -Path "$HOME\.codex\skills\$_" -Target "$(Get-Location)\skills\$_" -Force | Out-Null
}
```

Note: Windows symlinks may require Developer Mode or elevated privileges.

</details>

The analysis scripts are **pure Python 3.10+** with zero required dependencies. No pip install, no Docker, no KiCad installation needed.

### Release candidates

The stable install commands above always resolve to the latest stable release on `main` (currently v2.1.0). When a release candidate is active, opt in by appending `#<tag>` to the marketplace ref:

**Claude Code:**

```
/plugin marketplace add aklofas/kicad-happy#vX.Y.Z-rc.N
/plugin install kicad-happy@kicad-happy
```

This pins to the RC tag. Stable users on the un-suffixed marketplace are unaffected. To switch back to stable, remove the marketplace and re-add it without the `#` suffix.

**Codex / Gemini CLI / opencode:** clone the repo and check out the RC tag before running the install above:

```bash
git clone https://github.com/aklofas/kicad-happy.git
cd kicad-happy
git checkout vX.Y.Z-rc.N
# then run the symlink install for your agent
```

> [!IMPORTANT]
> Release candidates are pre-release builds intended for evaluation and feedback. They have passed the corpus regression gate and contract test suite but haven't completed extended manual validation. File issues on GitHub if you hit problems.

## ⚙️ GitHub Action

Also available as a **GitHub Action** for automated PR reviews. Every push and PR that touches KiCad files gets a commit status check and a structured review comment — power tree, SPICE results, EMC risk, thermal analysis, and more. Optionally chain with Claude for AI-powered natural-language reviews.

See the **[GitHub Action setup guide](github-action.md)** for workflow examples, diff-based PR reviews, and AI-powered review configuration.

## 📦 Skills

| Skill         | What it does                                                                                                                                                                             |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **kicad**     | ⚡ Parse and analyze KiCad schematics, PCB layouts, Gerbers, and PDF reference designs. Automated subcircuit detection, design review, DFM.                                               |
| **spice**     | 🔬 SPICE simulation — generates testbenches for detected subcircuits, validates filter frequencies, opamp gains, divider ratios. Monte Carlo tolerance analysis. ngspice, LTspice, Xyce. |
| **emc**       | 📡 EMC pre-compliance — 44 rule checks for radiated emission risks, PDN impedance, diff pair skew, ESD paths. FCC/CISPR/automotive/military.                                             |
| **datasheets**| 📄 Extract structured specs from datasheet PDFs — pinouts, electrical characteristics, peripherals, topology. Per-MPN caching with quality scoring. Consumed by kicad/emc/spice/thermal. |
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

**Extract (parse).** The **datasheets** skill turns those PDFs into structured JSON — pinouts, voltage ratings, electrical characteristics, peripherals, topology, SPICE model coefficients. Extractions are cached per-MPN under `<project>/datasheets/extracted/` and scored on a five-dimension quality rubric. Analyzer skills (`kicad`, `emc`, `spice`, `thermal`) consume the cache through a shared helper API with trust gates — so a schematic finding tagged `confidence: datasheet-backed` means a scored extraction produced the underlying fact, not a keyword match on the part number.

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

## 🎯 Release notes

**Current release: v2.1.0 — correctness batch.** Seventeen analyzer fixes from field reports and external reviews: inner power planes no longer fragment into false islands on 4+ layer boards (#24), via-in-pad and courtyard-overlap checks use real pad/courtyard geometry instead of bounding boxes (#28, #29), USB compliance failures surface as findings (new UC-001..UC-004), plus a dozen false-positive fixes across sleep-current, decoupling, derating, and lifecycle checks. Includes three fixes ported from Anya Sabo's fork. Upgrading from v2.0.0: expect finding churn in exactly those classes — overwhelmingly false positives disappearing; four additive JSON fields, no breaking schema changes.

Per-release stories are in [release-notes.md](release-notes.md); line-level detail in the [CHANGELOG](CHANGELOG.md).

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
