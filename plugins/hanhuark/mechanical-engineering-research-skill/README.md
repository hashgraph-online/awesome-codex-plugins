# Thermal-Fluid Research Workflow Plugin

**A cross-agent research workflow plugin for thermal-fluid mechanical engineering research, proposal development, technical writing, data analysis, research coding, presentations, and AI-assisted workflows.**

This repository packages the `mechanical-engineering-research` skill as a lightweight workflow plugin. The skill remains the domain judgment layer; the plugin adds cleaner install targets and reusable workflow prompts for common research tasks.

**Works with:** OpenAI Codex plugins/skills and Claude Code plugins/skills

[![Plugin](https://img.shields.io/badge/Codex-Plugin-blue?style=for-the-badge)](.codex-plugin/plugin.json)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-purple?style=for-the-badge)](.claude-plugin/plugin.json)
[![Skill](https://img.shields.io/badge/Codex-Skill-teal?style=for-the-badge)](skills/mechanical-engineering-research/SKILL.md)
[![Domain](https://img.shields.io/badge/Domain-Thermal--Fluids-orange?style=for-the-badge)](#capabilities)
[![Validation](https://img.shields.io/badge/Plugin-Validated-brightgreen?style=for-the-badge)](#validation)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/hanhuark/mechanical-engineering-research-skill?style=for-the-badge)](https://github.com/hanhuark/mechanical-engineering-research-skill/stargazers)

---

## What Is This?

This repository is now a plugin-style distribution for a single canonical skill:

```text
skills/mechanical-engineering-research/
```

The plugin is designed around a simple principle:

```text
academic research workflow = process scaffold
mechanical-engineering-research = thermal-fluid domain judgment layer
```

Use it to help Codex reason more carefully about thermal-fluid research: source quality, physical assumptions, literature synthesis, methodology detail, data-analysis logic, figure discussion, proposal significance, reproducible code, and AI/ML tools connected back to physics.

---

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

or:

```text
Install the Codex skill from https://github.com/hanhuark/mechanical-engineering-research-skill/tree/main/skills/mechanical-engineering-research
```

Do not ask Codex to install only `mechanical-engineering-research-skill` as a curated skill name. That is the repository name, not a curated Codex skill name.

### Manual Skill Installation

Clone the repository:

```powershell
git clone https://github.com/hanhuark/mechanical-engineering-research-skill.git
cd mechanical-engineering-research-skill
```

Copy the skill into your Codex skills directory:

```powershell
Copy-Item -Recurse .\skills\mechanical-engineering-research "$env:USERPROFILE\.codex\skills\mechanical-engineering-research" -Force
```

Restart Codex if the skill is not discovered immediately.

### Claude Code

Claude Code can use the same repository as a plugin because it includes:

```text
.claude-plugin/plugin.json
skills/mechanical-engineering-research/SKILL.md
commands/*.md
```

For local testing, clone the repository and launch Claude Code with the plugin directory:

```bash
git clone https://github.com/hanhuark/mechanical-engineering-research-skill.git
claude --plugin-dir ./mechanical-engineering-research-skill
```

Then invoke the skill or workflow prompts through the plugin namespace:

```text
/thermal-fluid-research-workflow:mechanical-engineering-research
/thermal-fluid-research-workflow:me-lit-review
/thermal-fluid-research-workflow:me-write-section
/thermal-fluid-research-workflow:me-data-analysis
/thermal-fluid-research-workflow:me-build-slides
/thermal-fluid-research-workflow:me-code-review
```

Claude Code should also discover the skill automatically when a task involves thermal-fluid research, mechanical-engineering literature review, manuscript writing, proposal development, research coding, plotting, or presentation planning.

---

## Capabilities

| Area | What The Plugin Helps With | Reference |
|---|---|---|
| Research workflow | Source-aware thermal-fluid research, assumptions, correlations, trade studies, validation | [`SKILL.md`](skills/mechanical-engineering-research/SKILL.md) |
| Literature review | Critical review, seminal-work tracing, citation past/future, review figures, benchmark tables | [`literature-review.md`](skills/mechanical-engineering-research/references/literature-review.md) |
| Paper writing style | Preferred journal-paper structure, abstract pattern, figure-led results, conclusions, AI/ML paper style | [`paper-writing-style.md`](skills/mechanical-engineering-research/references/paper-writing-style.md) |
| Technical writing | Introduction logic, methodology detail, modeling assumptions, results discussion | [`technical-writing-analysis.md`](skills/mechanical-engineering-research/references/technical-writing-analysis.md) |
| Proposal development | DOE/NSF/NASA-style proposal narratives, solicitation alignment, review criteria, preliminary results, milestones | [`proposal-development.md`](skills/mechanical-engineering-research/references/proposal-development.md) |
| Data analysis | Baseline case analysis, hypothesis-driven DOE, plotting, figure interpretation | [`technical-writing-analysis.md`](skills/mechanical-engineering-research/references/technical-writing-analysis.md) |
| Research coding | Reproducible scripts, notebooks, data pipelines, plotting code, simulation automation, code review | [`research-coding.md`](skills/mechanical-engineering-research/references/research-coding.md) |
| Presentations | Slide logic, graphics-first storytelling, speaker notes, videos/animations, backup slides | [`presentation-slides.md`](skills/mechanical-engineering-research/references/presentation-slides.md) |
| AI/ML tools | BubbleID, SeqReg, CFDTwin, DataDroid-LAM, sensor fusion, surrogate modeling | [`ai-tools-thermal-fluids.md`](skills/mechanical-engineering-research/references/ai-tools-thermal-fluids.md) |
| Toolchain | Overleaf, VS Code, GitHub, git, releases, archival workflow, reproducibility hygiene | [`research-toolchain.md`](skills/mechanical-engineering-research/references/research-toolchain.md) |
| Innovation | Invention disclosure, patent-support packets, commercialization briefs, non-confidential summaries | [`innovation-commercialization.md`](skills/mechanical-engineering-research/references/innovation-commercialization.md) |
| Briefs | Concise research brief structure for decision-ready engineering summaries | [`brief-template.md`](skills/mechanical-engineering-research/references/brief-template.md) |

---

## Plugin Structure

```text
mechanical-engineering-research-skill/
  .codex-plugin/
    plugin.json
  .claude-plugin/
    plugin.json
  commands/
    me-build-slides.md
    me-code-review.md
    me-data-analysis.md
    me-lit-review.md
    me-proposal.md
    me-write-section.md
  skills/
    mechanical-engineering-research/
      SKILL.md
      agents/
        openai.yaml
      references/
        ai-tools-thermal-fluids.md
        brief-template.md
        innovation-commercialization.md
        literature-review.md
        paper-writing-style.md
        presentation-slides.md
        proposal-development.md
        research-coding.md
        research-toolchain.md
        technical-writing-analysis.md
```

---

## Workflow Prompts

The `commands/` folder contains reusable workflow prompts that can be copied into Codex or adapted into future slash commands:

| Prompt | Use |
|---|---|
| [`me-lit-review.md`](commands/me-lit-review.md) | Critical literature review and gap synthesis; Claude command `/thermal-fluid-research-workflow:me-lit-review` |
| [`me-proposal.md`](commands/me-proposal.md) | Solicitation-aligned proposal development, figure planning, preliminary-results integration, milestones, and risk mitigation; Claude command `/thermal-fluid-research-workflow:me-proposal` |
| [`me-write-section.md`](commands/me-write-section.md) | Manuscript, proposal, report, or thesis-section drafting; Claude command `/thermal-fluid-research-workflow:me-write-section` |
| [`me-data-analysis.md`](commands/me-data-analysis.md) | Baseline-first analysis and hypothesis-driven DOE; Claude command `/thermal-fluid-research-workflow:me-data-analysis` |
| [`me-build-slides.md`](commands/me-build-slides.md) | Graphics-first research presentations; Claude command `/thermal-fluid-research-workflow:me-build-slides` |
| [`me-code-review.md`](commands/me-code-review.md) | Reproducible research code review and refactoring; Claude command `/thermal-fluid-research-workflow:me-code-review` |

---

## Usage Examples

### Literature Review

```text
Use the mechanical-engineering-research skill to develop a critical literature review on this thermal-fluid research topic. Synthesize the main theories, methods, limitations, unresolved challenges, and future directions instead of writing a paper-by-paper summary.
```

### Federal Proposal Development

```text
Use the mechanical-engineering-research skill to expand this DOE EPSCoR pre-application into a full proposal narrative. Follow the solicitation structure, map the narrative to review criteria, integrate preliminary results under each thrust, add quantifiable milestones, and cite seminal, recent, and team-relevant papers.
```

Or use the proposal workflow command:

```text
/thermal-fluid-research-workflow:me-proposal
```

### Data Analysis Plan

```text
Use the mechanical-engineering-research skill to design a hypothesis-driven DOE for these experiments or simulations. Start from a baseline case, identify the mechanism being tested, and choose cases that can support or refute the hypothesis.
```

### Figure Discussion

```text
Use the mechanical-engineering-research skill to write the results discussion for this figure. Follow description, observation, physical explanation, and comparison with existing work.
```

### Research Coding

```text
Use the mechanical-engineering-research skill to write a reproducible Python analysis pipeline for this experiment. Start with one baseline case, preserve raw data, make units explicit, and generate publication-quality plots.
```

### Research Presentation

```text
Use the mechanical-engineering-research skill to create a 12-slide conference talk outline from this paper, with graphics-first slides and complementary speaker notes.
```

### AI For Thermal Fluids

```text
Use the mechanical-engineering-research skill to plan a BubbleID/SeqReg workflow for extracting boiling interface dynamics and predicting heat flux from videos and acoustic signals.
```

---

## Update Workflow

Use this repository as the canonical source for future improvements.

```powershell
cd mechanical-engineering-research-skill
git pull
```

Edit files under:

```text
skills/mechanical-engineering-research/
```

Validate the skill:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\skills\mechanical-engineering-research"
```

Validate the plugin:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" "."
```

Commit and push:

```powershell
git add .codex-plugin .claude-plugin commands skills README.md CONTRIBUTING.md
git commit -m "Improve thermal-fluid research workflow plugin"
git push
```

Copy the updated skill into your local Codex skills directory when you want to use the latest skill version directly:

```powershell
Copy-Item -Recurse .\skills\mechanical-engineering-research "$env:USERPROFILE\.codex\skills\mechanical-engineering-research" -Force
```

---

## Validation

Validate the skill:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" ".\skills\mechanical-engineering-research"
```

Validate the plugin:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" "."
```

Expected result:

```text
Skill is valid!
Plugin is valid!
```

---

## Related Tools And References

The AI/ML guidance references several thermal-fluid and mechanical-engineering tools:

| Tool | Use |
|---|---|
| [BubbleID](https://github.com/cldunlap73/BubbleID) | Computer vision for bubble and interface dynamics |
| [SeqReg](https://github.com/cldunlap73/SeqReg) | Sequence regression for boiling and sensor data |
| [CFDTwin](https://github.com/UARK-NED3/CFDTwin) | CFD surrogate modeling and digital-twin workflows |
| [DataDroid-LAM](https://github.com/spier16/DataDroid-LAM) | Lab analysis and automation tooling |
| [MEEG-54403](https://github.com/hanhuark/MEEG-54403) | Machine Learning for Mechanical Engineers course material |

---

## FAQ

**Is this still a Codex skill?**

Yes. The canonical skill now lives at [`skills/mechanical-engineering-research`](skills/mechanical-engineering-research/). The plugin wraps it with metadata and workflow prompts.

**Why convert it to a plugin?**

The plugin form gives the project a clearer install target, room for workflow prompts, and a path toward future commands, scripts, assets, or additional skills.

**Does the plugin replace academic-research workflow tools?**

No. For full papers and proposals, use academic-research workflow tools as the process scaffold when available. Use this plugin as the thermal-fluid/mechanical-engineering judgment layer.

**Can I use this with Claude Code, Cursor, or other agents?**

Yes for Claude Code. This repository includes `.claude-plugin/plugin.json` and the standard `skills/<skill-name>/SKILL.md` structure. Claude Code users can load it with `claude --plugin-dir` or install it through a compatible Claude Code marketplace if listed there. Other agents can adapt the markdown skill manually.

**How should I contribute improvements?**

Add reusable guidance, not one-off facts. Keep `SKILL.md` concise and put detailed workflows in `references/`. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Contributing

Contributions are welcome. Good contributions improve reusable research practice:

- clearer thermal-fluid research workflows
- stronger literature-review synthesis methods
- proposal development and review-criteria guidance
- technical writing and results-discussion guidance
- data-analysis, plotting, and DOE practices
- reproducible research coding practices
- presentation design patterns
- AI/ML workflows for mechanical engineering

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

---

## License

MIT License. See [`LICENSE`](LICENSE) for details.
