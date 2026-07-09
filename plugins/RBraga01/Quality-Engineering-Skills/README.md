<p align="center">
  <img src="assets/qes-logo.jpg" alt="Quality Engineering Skills" width="160">
</p>

# Quality-Engineering-Skills

**22 structured quality engineering skills and 8 agents for AI — ISO 9001, IATF 16949, AIAG-VDA FMEA, VDA 6.3, PPAP, APQP, SPC, MSA.**
Works with Claude Code, Codex CLI, Cursor, Gemini CLI, and any agentskills.io-compatible AI tool.

**[→ rbraga01.github.io/Quality-Engineering-Skills](https://rbraga01.github.io/Quality-Engineering-Skills/)**

[![Skills](https://img.shields.io/badge/skills-22-orange)](skills/)
[![Agents](https://img.shields.io/badge/agents-8-purple)](skills/agents/)
[![agentskills.io](https://img.shields.io/badge/format-agentskills.io-0ea5e9)](https://agentskills.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Install in 30 seconds

```bash
npx skills add RBraga01/Quality-Engineering-Skills
```

Or clone directly:

```bash
git clone https://github.com/RBraga01/Quality-Engineering-Skills.git
```

Or [download as ZIP](https://github.com/RBraga01/Quality-Engineering-Skills/archive/refs/heads/master.zip).

---

## What this solves

AI agents are powerful — but they don't know 8D from PDCA, can't apply the AIAG-VDA Action Priority table, and generate generic NCR text that no auditor would accept.

**Quality-Engineering-Skills packages decades of hands-on quality engineering expertise** — automotive supplier quality, claims management, 8D, FMEA, PPAP, and ISO 9001 auditing — into structured skills your AI agent can load and apply immediately.

Every skill maps to specific standard clauses. Every agent validates methodology, not just format.

---

## Coverage

| Domain | Skills | Standards |
|--------|--------|-----------|
| Problem Solving | 8D (D0–D8), 5-Why, Fishbone, Is/Is-Not, PDCA, DMAIC | ISO 9001 §10.2, IATF 16949 §10.2.3 |
| Risk Analysis | PFMEA, DFMEA, Action Priority (AP) | AIAG-VDA FMEA 2019, IATF 16949 §8.3 |
| Planning | PPAP (5 levels, 18 elements), APQP (5 phases), Control Plan, DVP&R | AIAG PPAP 4th Ed, IATF 16949 §8.3.4 |
| Measurement | MSA / Gauge R&R, SPC / Control Charts | AIAG MSA 4th Ed, AIAG SPC 2nd Ed |
| Documentation | NCR, CAR, 8D Customer Report | ISO 9001 §7.5, §8.7, §10.2 |
| Audit | ISO 9001 Internal, IATF 16949 Supplemental, VDA 6.3 | ISO 9001:2015, IATF 16949:2016, VDA 6.3 2023 |
| Supplier Quality | Supplier SCAR, corrective action escalation | ISO 9001 §8.4, IATF 16949 §8.4.1 |

| Industries covered |
|----|
| Automotive · Electronics · Aerospace · Medical Devices · General Manufacturing |

---

## 8 Agents

Drop these into any project and your AI becomes a trained quality professional.

### `/8d-coach`
Guides you through a full 8D — D0 emergency response to D8 team recognition. Validates root cause depth (rejects "human error" without systemic analysis), verifies containment before moving to D4, and checks D7 prevention updates.

```
/8d-coach
> D0: Is this a safety or regulatory issue? [Y/N]
> D1: List team members by function (minimum: quality, production, engineering)
> D2: Describe the defect — What? Where? When? How many? ...
```

### `/fmea-reviewer`
Audits an existing PFMEA or DFMEA against AIAG-VDA 2019. Returns a structured gap report: missing failure modes, incorrect AP ratings, unaddressed H-AP items, missing special characteristics.

### `/rca-facilitator`
Runs a structured 5-Why with chain validation. Challenges each answer with evidence requirements. Detects symptomatic vs. systemic root causes. Catches circular reasoning. Produces a validated, reversible Why chain.

### `/ncr-writer`
Takes bullet-point observations and generates professional NCR text: objective evidence language, severity classification (Critical/Major/Minor), and disposition recommendation. No more "part looks wrong."

### `/audit-guide`
Interactive internal audit for ISO 9001 or IATF 16949. Works clause by clause, scores findings (Major/Minor/OFI), generates a structured audit report with evidence references.

### `/ppap-checker`
Interactive PPAP completeness checker — walks through all 18 PPAP elements for the requested submission level, flags missing or incomplete items, and generates a gap report before PSW signature.

### `/control-plan-builder`
Builds a Control Plan row by row from PFMEA failure modes and process flow steps. Validates reaction plans, sample plans, and special characteristic coverage. Supports D7 update mode after corrective actions.

### `/skill-auditor`
Automated audit and scoring of SKILL.md and REFERENCE files against framework standards.

---

## Skill index

<details>
<summary><strong>Problem Solving</strong> (ISO 9001 §10.2)</summary>

| Skill | Description |
|-------|-------------|
| [8d-problem-solving](skills/problem-solving/8d-problem-solving/) | Full D0–D8 methodology with discipline-by-discipline instructions, templates, and validation criteria |
| [5why-root-cause](skills/problem-solving/5why-root-cause/) | Structured 5-Why chain construction, evidence validation, systemic vs. symptomatic detection |
| [fishbone-analysis](skills/problem-solving/fishbone-analysis/) | Ishikawa diagram using 6M (Man, Machine, Method, Material, Measurement, Environment) |
| [is-is-not-scoping](skills/problem-solving/is-is-not-scoping/) | Ford D2 problem scoping tool — defines problem boundary and eliminates hypotheses |
| [pdca-improvement](skills/problem-solving/pdca-improvement/) | Plan-Do-Check-Act cycle structure with gate criteria for continuous improvement |
| [dmaic](skills/problem-solving/dmaic/) | Six Sigma DMAIC — five-phase structured improvement for chronic, data-driven problems |

</details>

<details>
<summary><strong>Risk Analysis</strong> (AIAG-VDA FMEA 2019)</summary>

| Skill | Description |
|-------|-------------|
| [pfmea-process](skills/risk-analysis/pfmea-process/) | 7-step Process FMEA per AIAG-VDA 2019: Structure → Function → Failure → Risk → Optimization |
| [dfmea-design](skills/risk-analysis/dfmea-design/) | Design FMEA with interface matrix and design intent failure analysis |
| [action-priority-ap](skills/risk-analysis/action-priority-ap/) | AP table logic replacing legacy RPN — H/M/L classification with action requirements |

</details>

<details>
<summary><strong>Planning</strong> (AIAG PPAP 4th Ed · APQP 2nd Ed · IATF 16949 §8.3)</summary>

| Skill | Description |
|-------|-------------|
| [ppap](skills/planning/ppap/) | PPAP 5 levels, 18 elements, OEM-specific requirements (Ford, BMW, VW, Stellantis) |
| [apqp](skills/planning/apqp/) | APQP 5 phases with gate criteria, deliverables per phase, and timing guidelines |
| [control-plan](skills/planning/control-plan/) | Control Plan structure, PFMEA linkage, reaction plan requirements, audit checklist |
| [dvp-test-plan](skills/planning/dvp-test-plan/) | Design Verification Plan linked to DFMEA failure modes — test categories, criteria, tracking |

</details>

<details>
<summary><strong>Measurement</strong> (AIAG MSA 4th Ed · SPC 2nd Ed)</summary>

| Skill | Description |
|-------|-------------|
| [msa-gauge-rr](skills/measurement/msa-gauge-rr/) | Gauge R&R study types, %GRR interpretation, ndc, attribute MSA — PPAP requirement |
| [spc-control-charts](skills/measurement/spc-control-charts/) | Chart selection, Western Electric rules, Cp/Cpk/Pp/Ppk calculation and interpretation |

</details>

<details>
<summary><strong>Documentation</strong> (ISO 9001 §7.5, §8.7, §10.2)</summary>

| Skill | Description |
|-------|-------------|
| [ncr-writing](skills/documentation/ncr-writing/) | Non-Conformance Report: objective evidence language, severity grading, disposition |
| [car-corrective-action](skills/documentation/car-corrective-action/) | Corrective Action Request with effectiveness verification requirements |
| [8d-report-writing](skills/documentation/8d-report-writing/) | Customer-facing 8D report writing for OEM submission (Ford, BMW, VW, Stellantis) |

</details>

<details>
<summary><strong>Audit</strong> (ISO 9001 §9.2 · IATF 16949 §9.2.2 · VDA 6.3)</summary>

| Skill | Description |
|-------|-------------|
| [iso-9001-internal-audit](skills/audit/iso-9001-internal-audit/) | §4–§10 internal audit question bank with finding classification |
| [iatf-16949-audit](skills/audit/iatf-16949-audit/) | IATF 16949 supplemental requirements audit — CSR, contingency plans, error-proofing |
| [vda-6-3-audit](skills/audit/vda-6-3-audit/) | VDA 6.3 process audit P1–P7, 0–10 rating, A/B/C degree of fulfillment — 4th ed 2023 |

</details>

<details>
<summary><strong>Supplier Quality</strong> (ISO 9001 §8.4)</summary>

| Skill | Description |
|-------|-------------|
| [supplier-scar](skills/supplier-quality/supplier-scar/) | Supplier Corrective Action Request — escalation criteria, 8D response evaluation, effectiveness verification |

</details>

<details>
<summary><strong>Agents</strong></summary>

| Agent | Description |
|-------|-------------|
| [8d-coach](skills/agents/8d-coach/) | Interactive D0–D8 coach with validation gates |
| [fmea-reviewer](skills/agents/fmea-reviewer/) | PFMEA/DFMEA gap audit against AIAG-VDA 2019 |
| [rca-facilitator](skills/agents/rca-facilitator/) | Structured 5-Why with evidence validation |
| [ncr-writer](skills/agents/ncr-writer/) | Professional NCR generator from bullet inputs |
| [audit-guide](skills/agents/audit-guide/) | Interactive ISO 9001 / IATF internal audit |
| [ppap-checker](skills/agents/ppap-checker/) | Interactive 18-element PPAP completeness checker with OEM-specific gates |
| [control-plan-builder](skills/agents/control-plan-builder/) | Row-by-row Control Plan builder from PFMEA data — includes D7 update mode |
| [skill-auditor](skills/agents/skill-auditor/) | Automated audit and scoring of SKILL.md and REFERENCE files against framework standards |

</details>

---

## Framework mapping

Every `SKILL.md` carries metadata linking it to the standards it implements.

```yaml
metadata:
  iso-9001: "10.2"
  iatf-16949: "10.2.3"
  domain: quality-engineering
  industries: automotive,electronics,aerospace,medical,general
```

---

## Roadmap

**v2 (current):** Problem solving · Risk analysis · PPAP · APQP · Control Plan · DVP&R · MSA · SPC · VDA 6.3 · DMAIC · Supplier SCAR — 22 skills, 8 agents

**v3:** AS9100 Rev D (aerospace) · ISO 13485 (medical devices) · HACCP / ISO 22000 (food safety)

**v4:** Supplier qualification workflows · AQL sampling plans · VDA 6.5 product audit

**Multilingual:** PT · DE · ES · ZH

---

## Contributing

Quality engineering is global. If you have domain expertise to add:

- **Aerospace:** AS9100, AS13100, RCCA
- **Medical devices:** ISO 13485, FDA 21 CFR Part 820
- **Food safety:** HACCP, ISO 22000, FSSC 22000
- **Statistics:** AQL sampling plans, attribute SPC
- **Automotive:** OEM customer-specific requirements (Ford CSR, BMW, VW QMSS)

See [CONTRIBUTING.md](CONTRIBUTING.md) for the skill format and submission process.

---

## Authors

**[@RBraga01](https://github.com/RBraga01)** — 15+ years in quality engineering. Claim manager for ~30 electronic component suppliers — receives OEM customer complaints and manages the full escalation to the respective suppliers. Created Quality Engineering Skills to bring structured methodology to AI agents in the quality domain.

**[@migmcc](https://github.com/migmcc)** — 25+ years in quality engineering. Claim manager handling OEM customer complaints and escalations across electromechanical and mechanical suppliers. 8D and problem-solving expert. Responsible for the skill content that makes the methodology accurate and practitioner-grade.
