# Thermal-Fluid Research Workflow Plugin

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

**A domain-rigor layer and modular skill suite for thermal-fluid mechanical engineering research with AI agents.**

Generic research agents can summarize papers and draft prose. This plugin helps them do the harder mechanical-engineering work: check heat-transfer and fluid-flow assumptions, catch invalid correlation use, question CFD validation, protect uncertainty analysis, explain mechanisms, and turn evidence into decision-ready research artifacts.

Use it when a thermal-fluid answer needs to be physically defensible, not just well written.

The suite keeps task-specific instructions small and discoverable while retaining one coordinator for work that crosses boundaries:

| Skill | Primary use |
|---|---|
| [`mechanical-engineering-research`](skills/mechanical-engineering-research/SKILL.md) | Cross-cutting thermal-fluid research coordination and rigor gates |
| [`thermal-fluid-analysis`](skills/thermal-fluid-analysis/SKILL.md) | Physics, experiments, CFD, correlations, uncertainty, and trade studies |
| [`research-writing-literature`](skills/research-writing-literature/SKILL.md) | Literature reviews, citations, manuscript sections, and figure discussion |
| [`research-proposal-development`](skills/research-proposal-development/SKILL.md) | Solicitation-aligned narratives, milestones, risks, and proposal figures |
| [`research-data-analysis`](skills/research-data-analysis/SKILL.md) | Baseline-first DOE, data processing, plots, and ML/CFD/experimental analysis |
| [`research-slide-design`](skills/research-slide-design/SKILL.md) | Graphics-first talks, posters, speaker notes, and visual QA |
| [`research-schematic-design`](skills/research-schematic-design/SKILL.md) | Editable scientific schematics, graphical abstracts, and facility or workflow figures |
| [`research-mentor-review`](skills/research-mentor-review/SKILL.md) | Constructive, actionable student-facing research feedback |
| [`reviewer-author-loop`](skills/reviewer-author-loop/SKILL.md) | Iterative peer review, revision, verification, and re-review |

[![Version](https://img.shields.io/badge/version-v0.4.0-blue?style=for-the-badge)](CHANGELOG.md)
[![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-blue?style=for-the-badge)](.codex-plugin/plugin.json)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple?style=for-the-badge)](.claude-plugin/plugin.json)
[![Skill](https://img.shields.io/badge/Codex-Skill-teal?style=for-the-badge)](skills/mechanical-engineering-research/SKILL.md)
[![Domain](https://img.shields.io/badge/Domain-Thermal--Fluids-orange?style=for-the-badge)](#what-it-catches)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/hanhuark/mechanical-engineering-research-skill?style=for-the-badge)](https://github.com/hanhuark/mechanical-engineering-research-skill/stargazers)

If this helps your research workflow, please star the repo so other mechanical-engineering researchers can find it.

Want the fastest path? Start with [`QUICKSTART.md`](QUICKSTART.md).

## Two-Minute Demo

Paste a prompt like this after installing the skill:

```text
Use the mechanical-engineering-research skill to review this claim:

"The CFD model proves that the new microchannel heat sink is optimal because
the average Nusselt number is 40% higher than the baseline. The simulation used
k-epsilon turbulence, a coarse wall mesh, constant water properties, and three
flow rates between Re = 350 and 900. Pressure drop is not discussed."
```

Expected style of response:

```text
Bottom line: The claim is overconfident. The result may indicate better heat
transfer in the tested cases, but it does not prove optimality.

Key issues:
- Re = 350-900 may be laminar or transitional for the stated geometry, so a
  k-epsilon turbulence model needs justification.
- A coarse wall mesh weakens confidence in wall heat flux and Nusselt number.
- Constant water properties may be acceptable only over a small temperature
  range; the temperature span must be stated.
- A 40% Nusselt increase is incomplete without pressure drop, pumping power,
  and thermal resistance.
- "Optimal" requires a design space, objective function, constraints, and
  uncertainty or grid-independence evidence.

Next checks: compare against laminar correlations or a conjugate heat-transfer
baseline, report y+ or wall treatment, run mesh independence, include pressure
drop and pumping power, and rewrite the claim as evidence from a limited CFD
study rather than proof of global optimality.
```

## Workflow

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial, sans-serif", "primaryColor": "#ecfeff", "primaryTextColor": "#0f172a", "primaryBorderColor": "#0f766e", "lineColor": "#475569", "secondaryColor": "#fff7ed", "tertiaryColor": "#f8fafc", "clusterBkg": "#ffffff", "clusterBorder": "#cbd5e1", "edgeLabelBackground": "#ffffff"}}}%%
flowchart TB
    A["Research Request"]:::input
    B["Plugin Router"]:::core

    C["Academic Scaffold"]:::scaffold
    D["ME Judgment Layer"]:::core

    A --> B
    C -. "process" .-> B
    B --> D

    D --> E{"Mode"}:::gate

    E --> F1["Literature Map"]:::lane
    E --> F2["Analysis + DOE"]:::lane
    E --> F3["CFD + Tests"]:::lane
    E --> F4["Writing + Proposals"]:::lane
    E --> F5["Code + AI/ML"]:::lane
    E --> F6["Slides + IP"]:::lane

    F1 --> G
    F2 --> G
    F3 --> G
    F4 --> G
    F5 --> G
    F6 --> G

    G["Rigor Gate"]:::gate
    H["Decision Output"]:::output
    I["Reusable Artifact"]:::artifact

    G --> H --> I

    classDef input fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#0f172a;
    classDef core fill:#ccfbf1,stroke:#0f766e,stroke-width:3px,color:#0f172a;
    classDef scaffold fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#0f172a;
    classDef lane fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#0f172a;
    classDef gate fill:#fef3c7,stroke:#d97706,stroke-width:3px,color:#0f172a;
    classDef output fill:#ecfdf5,stroke:#16a34a,stroke-width:3px,color:#0f172a;
    classDef artifact fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px,color:#0f172a;
```

Editable Mermaid source: [`assets/workflow.mmd`](assets/workflow.mmd).

## What It Catches

- Correlations used outside their Reynolds, Prandtl, geometry, roughness, orientation, or phase-change validity range.
- CFD claims without mesh independence, wall treatment, convergence, boundary-condition, property-model, or validation evidence.
- Experiment plans missing sensor calibration, uncertainty propagation, repeatability, heat-loss correction, or flow-development checks.
- AI/ML workflows with leakage across videos, surfaces, experiments, geometries, pressures, or simulation families.
- Literature reviews that list papers chronologically instead of synthesizing mechanisms, methods, gaps, and benchmark evidence.
- Proposal sections that describe ambitious methods but do not connect barrier, capability, validation, metrics, risk, and impact.
- Results discussions that report trends without explaining the dominant physics.

## Quick Install

### OpenAI Codex

Ask Codex to install the plugin from GitHub:

```text
Install the Codex plugin from https://github.com/hanhuark/mechanical-engineering-research-skill
```

If your Codex environment does not yet support community plugin installation from a GitHub repo, install the skill folder directly:

```text
Install the Codex skill from GitHub repo hanhuark/mechanical-engineering-research-skill, path skills/mechanical-engineering-research.
```

For a focused task, replace `mechanical-engineering-research` with a folder from the skill-suite table above. Install the full plugin when you want all skills and workflow prompts available together.

Manual install on Windows:

```powershell
git clone https://github.com/hanhuark/mechanical-engineering-research-skill.git
cd mechanical-engineering-research-skill
$skillRoot = "$env:USERPROFILE\.codex\skills"
Copy-Item -Recurse .\skills\mechanical-engineering-research $skillRoot -Force
Copy-Item -Recurse .\skills\thermal-fluid-analysis $skillRoot -Force
Copy-Item -Recurse .\skills\research-writing-literature $skillRoot -Force
Copy-Item -Recurse .\skills\research-proposal-development $skillRoot -Force
Copy-Item -Recurse .\skills\research-data-analysis $skillRoot -Force
Copy-Item -Recurse .\skills\research-slide-design $skillRoot -Force
Copy-Item -Recurse .\skills\research-schematic-design $skillRoot -Force
Copy-Item -Recurse .\skills\research-mentor-review $skillRoot -Force
Copy-Item -Recurse .\skills\reviewer-author-loop $skillRoot -Force
```

### Claude Code

Clone the repository and launch Claude Code with the plugin directory:

```bash
git clone https://github.com/hanhuark/mechanical-engineering-research-skill.git
claude --plugin-dir ./mechanical-engineering-research-skill
```

Then invoke one of the workflow prompts, for example:

```text
/thermal-fluid-research-workflow:me-cfd-review
/thermal-fluid-research-workflow:me-correlation-check
/thermal-fluid-research-workflow:me-figure-discussion
/thermal-fluid-research-workflow:me-build-schematic
/thermal-fluid-research-workflow:reviewer-author-loop
```

## Use With Generic Academic Workflows

This plugin does not replace broad academic-research tools. Use generic academic workflows for process scaffolding: outline, citation management, drafting sequence, peer-review loop, and finalization. Use this plugin when the work depends on thermal-fluid validity: regimes, assumptions, correlations, property variation, scaling, CFD credibility, experiment design, uncertainty, and engineering tradeoffs.

```text
academic research workflow = process scaffold
mechanical-engineering-research = thermal-fluid domain judgment layer
focused skills = task-specific guidance
```

## Workflow Prompts

| Prompt | Use |
|---|---|
| [`reviewer-author-loop.md`](commands/reviewer-author-loop.md) | Run a manuscript review, revision, verification, and re-review loop until acceptance or human input is needed. |
| [`me-correlation-check.md`](commands/me-correlation-check.md) | Check whether equations, correlations, and dimensionless groups are being used within valid limits. |
| [`me-cfd-review.md`](commands/me-cfd-review.md) | Review CFD setup, mesh, wall treatment, convergence, validation, and claim strength. |
| [`me-experiment-plan.md`](commands/me-experiment-plan.md) | Plan thermal-fluid experiments around instrumentation, calibration, uncertainty, repeatability, and safety. |
| [`me-lit-matrix.md`](commands/me-lit-matrix.md) | Build a mechanism-based literature matrix with methods, metrics, validity limits, and gaps. |
| [`me-figure-discussion.md`](commands/me-figure-discussion.md) | Turn a figure into a physical explanation with claims, comparisons, and limitations. |
| [`me-proposal-aims.md`](commands/me-proposal-aims.md) | Rewrite aims around barrier, hypothesis, approach, metrics, risk, and impact. |
| [`me-code-sanity.md`](commands/me-code-sanity.md) | Run a fast preflight for units, leakage, baselines, and physics checks. |
| [`me-lit-review.md`](commands/me-lit-review.md) | Develop a critical thermal-fluid literature review and gap synthesis. |
| [`me-proposal.md`](commands/me-proposal.md) | Develop or revise a solicitation-aligned research proposal. |
| [`me-write-section.md`](commands/me-write-section.md) | Draft or revise manuscript, proposal, report, or thesis sections. |
| [`me-han-hu-draft.md`](commands/me-han-hu-draft.md) | Draft a manuscript section using Han Hu manuscript mode and the private style corpus. |
| [`me-han-hu-revise.md`](commands/me-han-hu-revise.md) | Revise a manuscript while preserving evidence and applying Han Hu manuscript mode. |
| [`me-data-analysis.md`](commands/me-data-analysis.md) | Plan baseline-first thermal-fluid data analysis and hypothesis-driven DOE. |
| [`me-build-slides.md`](commands/me-build-slides.md) | Build graphics-first research presentations and speaker notes. |
| [`me-build-schematic.md`](commands/me-build-schematic.md) | Build editable scientific schematics, graphical abstracts, and facility or workflow figures. |
| [`me-code-review.md`](commands/me-code-review.md) | Perform a full architecture, reproducibility, testing, and release review. |

## Showcase

The examples are synthetic, public-safe artifacts designed to show the plugin's expected behavior:

| Artifact | What it demonstrates |
|---|---|
| [`cfd-review-memo.md`](examples/showcase/cfd-review-memo.md) | How to downshift overclaimed CFD evidence into a defensible review memo. |
| [`heat-exchanger-design-matrix.md`](examples/showcase/heat-exchanger-design-matrix.md) | How to compare design options by mechanism, pressure drop, manufacturability, and risk. |
| [`boiling-literature-matrix.md`](examples/showcase/boiling-literature-matrix.md) | How to synthesize a boiling literature review by mechanism rather than paper order. |
| [`proposal-aims-rewrite.md`](examples/showcase/proposal-aims-rewrite.md) | How to convert vague proposal aims into reviewer-ready technical aims. |
| [`figure-discussion-before-after.md`](examples/showcase/figure-discussion-before-after.md) | How to rewrite a weak results paragraph into a physical explanation. |

## Capabilities

| Area | What the plugin helps with | Reference |
|---|---|---|
| Skill coordinator | Cross-cutting research routing, evidence classification, and integrity gates | [`SKILL.md`](skills/mechanical-engineering-research/SKILL.md) |
| Thermal-fluid analysis | Physics, experiments, CFD, correlations, uncertainty, and engineering tradeoffs | [`SKILL.md`](skills/thermal-fluid-analysis/SKILL.md) |
| Writing and literature | Research narratives, critical reviews, citations, and figure-led discussion | [`SKILL.md`](skills/research-writing-literature/SKILL.md) |
| Proposal development | Solicitation alignment, reviewer criteria, preliminary evidence, milestones, risks, and figures | [`SKILL.md`](skills/research-proposal-development/SKILL.md) |
| Data analysis | Baseline-first DOE, traceable data work, plots, CFD/experimental analysis, and ML evaluation | [`SKILL.md`](skills/research-data-analysis/SKILL.md) |
| Slide design | Research talks and posters with clean visual logic and complementary speaker notes | [`SKILL.md`](skills/research-slide-design/SKILL.md) |
| Mentor review | Constructive feedback that distinguishes required revisions, recommendations, and author questions | [`SKILL.md`](skills/research-mentor-review/SKILL.md) |
| Reviewer-author loop | Repeated review, revision, verification, re-review, rebuttal planning, and pause decisions | [`SKILL.md`](skills/reviewer-author-loop/SKILL.md) |
| Research workflow | Source-aware thermal-fluid research, assumptions, correlations, trade studies, validation | [`SKILL.md`](skills/mechanical-engineering-research/SKILL.md) |
| Literature review | Critical review, seminal-work tracing, citation path, review figures, benchmark tables | [`literature-review.md`](skills/mechanical-engineering-research/references/literature-review.md) |
| Citation integrity | Claim-level support, bibliography checks, numeric citation repair | [`citation-integrity.md`](skills/mechanical-engineering-research/references/citation-integrity.md) |
| Dataset/software reviews | Multi-channel discovery, maturity labels, benchmark and repository synthesis | [`dataset-software-review.md`](skills/mechanical-engineering-research/references/dataset-software-review.md) |
| Paper writing style | Abstracts, methods, figure-led results, conclusions, AI/ML paper style | [`paper-writing-style.md`](skills/mechanical-engineering-research/references/paper-writing-style.md) |
| Revision and submission | Reviewer responses, highlighted manuscripts, source packages, release audits | [`manuscript-revision-submission.md`](skills/mechanical-engineering-research/references/manuscript-revision-submission.md) |
| Technical writing | Methodology detail, modeling assumptions, results discussion | [`technical-writing-analysis.md`](skills/mechanical-engineering-research/references/technical-writing-analysis.md) |
| Experiments and uncertainty | Measurement models, DOE, calibration, synchronization, uncertainty budgets | [`experimental-design-and-uncertainty.md`](skills/mechanical-engineering-research/references/experimental-design-and-uncertainty.md) |
| Model credibility | CFD verification/validation, ROMs, surrogates, ML generalization | [`model-verification-and-ml-credibility.md`](skills/mechanical-engineering-research/references/model-verification-and-ml-credibility.md) |
| Result-change audit | Construct, boundary, data, code, and assumption root-cause checks | [`result-change-and-construct-audit.md`](skills/mechanical-engineering-research/references/result-change-and-construct-audit.md) |
| Data and release | Provenance, rights, benchmark design, reproducibility, public packages | [`data-provenance-and-release.md`](skills/mechanical-engineering-research/references/data-provenance-and-release.md) |
| Figure and artifact QA | Final-size figures, tables, PDFs, Word, spreadsheets, and slides | [`scientific-figure-and-artifact-qa.md`](skills/mechanical-engineering-research/references/scientific-figure-and-artifact-qa.md) |
| Proposal development | DOE/NSF/NASA-style narratives, solicitation alignment, milestones, risks | [`proposal-development.md`](skills/mechanical-engineering-research/references/proposal-development.md) |
| Research coding | Reproducible scripts, notebooks, plotting, simulation automation, code review | [`research-coding.md`](skills/mechanical-engineering-research/references/research-coding.md) |
| Presentations | Graphics-first research talks, slide logic, speaker notes, backup slides | [`presentation-slides.md`](skills/mechanical-engineering-research/references/presentation-slides.md) |
| AI/ML tools | Computer vision, sequence models, sensor fusion, surrogate modeling | [`ai-tools-thermal-fluids.md`](skills/mechanical-engineering-research/references/ai-tools-thermal-fluids.md) |
| Teaching | Engineering-first explanations, derivations, code, and transfer tasks | [`teaching-mechanical-engineering.md`](skills/mechanical-engineering-research/references/teaching-mechanical-engineering.md) |
| Toolchain | Overleaf, VS Code, GitHub, git, releases, reproducibility hygiene | [`research-toolchain.md`](skills/mechanical-engineering-research/references/research-toolchain.md) |
| Innovation | Invention disclosure, patent-support packets, commercialization briefs | [`innovation-commercialization.md`](skills/mechanical-engineering-research/references/innovation-commercialization.md) |

## Validation

Run repository validation:

```powershell
python scripts\validate_repo.py
python -m unittest -v tests.test_skill_scripts
```

Optional local Codex/plugin validation:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\skills\mechanical-engineering-research"
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" "."
```

The CI workflow in [`.github/workflows/validate.yml`](.github/workflows/validate.yml) runs the repository validation script and checks the thermal-fluid eval fixtures.

## Release Notes

See [`CHANGELOG.md`](CHANGELOG.md). The `v0.3.1` release line adds the anti-formulaic editorial pass to the modular suite; `v0.3.0` introduced the focused skills while retaining the original coordinator for existing users.

## Related Tools

| Tool | Use |
|---|---|
| [BubbleID](https://github.com/cldunlap73/BubbleID) | Computer vision for bubble and interface dynamics |
| [SeqReg](https://github.com/cldunlap73/SeqReg) | Sequence regression for boiling and sensor data |
| [CFDTwin](https://github.com/UARK-NED3/CFDTwin) | CFD surrogate modeling and digital-twin workflows |
| [DataDroid-LAM](https://github.com/spier16/DataDroid-LAM) | Lab analysis and automation tooling |
| [MEEG-54403](https://github.com/hanhuark/MEEG-54403) | Machine Learning for Mechanical Engineers course material |

## Contributing

Contributions are welcome when they improve reusable thermal-fluid research practice: stronger validity checks, better examples, clearer workflows, more robust eval fixtures, or better installation documentation. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT License. See [`LICENSE`](LICENSE).
