<p align="center">
  <img src="https://rbraga01.github.io/Quality-Engineering-Skills/assets/qes-logo.jpg" alt="Quality Engineering Skills" width="160">
</p>

# Quality Engineering Skills v2.0.0

**22 structured quality engineering skills for automotive and manufacturing.**

ISO 9001 · IATF 16949 · AIAG-VDA FMEA · VDA 6.3 · PPAP · APQP · SPC · MSA

Works with Claude Code, Codex CLI, Cursor, Gemini CLI, and any agentskills.io-compatible AI tool.

**[→ rbraga01.github.io/Quality-Engineering-Skills](https://rbraga01.github.io/Quality-Engineering-Skills/)**

---

## Install

```bash
npx skills add RBraga01/Quality-Engineering-Skills
```

Or clone directly:

```bash
git clone https://github.com/RBraga01/Quality-Engineering-Skills.git
```

---

## What it solves

AI agents are powerful — but they don't know 8D from PDCA, can't apply the AIAG-VDA Action Priority table, and generate generic NCR text that no auditor would accept.

Quality Engineering Skills packages decades of hands-on quality engineering expertise into structured skills your AI agent can load and apply immediately. Every skill maps to specific standard clauses. Every agent validates methodology, not just format.

---

## Skills (22)

| Domain | Skills | Standards |
|--------|--------|-----------|
| Problem Solving | 8D (D0–D8), 5-Why, Fishbone, Is/Is-Not, PDCA, DMAIC | ISO 9001 §10.2, IATF 16949 §10.2.3 |
| Risk Analysis | PFMEA, DFMEA, Action Priority (AP) | AIAG-VDA FMEA 2019, IATF 16949 §8.3 |
| Planning | PPAP (5 levels, 18 elements), APQP, Control Plan, DVP&R | AIAG PPAP 4th Ed, IATF 16949 §8.3.4 |
| Measurement | MSA / Gauge R&R, SPC / Control Charts | AIAG MSA 4th Ed, AIAG SPC 2nd Ed |
| Documentation | NCR, CAR, 8D Customer Report | ISO 9001 §7.5, §8.7, §10.2 |
| Audit | ISO 9001 Internal, IATF 16949 Supplemental, VDA 6.3 | ISO 9001:2015, IATF 16949:2016, VDA 6.3 2023 |
| Supplier Quality | Supplier SCAR | ISO 9001 §8.4 |

## Agents (8)

| Agent | What it does |
|-------|-------------|
| `/8d-coach` | Interactive D0–D8 coach with validation gates |
| `/fmea-reviewer` | PFMEA/DFMEA gap audit against AIAG-VDA 2019 |
| `/rca-facilitator` | Structured 5-Why with evidence validation |
| `/ncr-writer` | Professional NCR generator from bullet inputs |
| `/audit-guide` | Interactive ISO 9001 / IATF internal audit |
| `/ppap-checker` | Interactive 18-element PPAP completeness checker |
| `/control-plan-builder` | Row-by-row Control Plan builder from PFMEA data |
| `/skill-auditor` | Automated audit and scoring of SKILL.md files |

---

## Industries

Automotive · Electronics · Aerospace · Medical Devices · General Manufacturing

---

## Links

- [GitHub repository](https://github.com/RBraga01/Quality-Engineering-Skills)
- [Landing page](https://rbraga01.github.io/Quality-Engineering-Skills/)
- [Full skill index](https://github.com/RBraga01/Quality-Engineering-Skills#skill-index)

## License

MIT — see [LICENSE](LICENSE).
