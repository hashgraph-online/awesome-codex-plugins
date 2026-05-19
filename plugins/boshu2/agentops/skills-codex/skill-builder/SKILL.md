---
name: skill-builder
description: 'Scaffold a new SKILL.md.'
---
# $skill-builder — Scaffold or absorb a new SKILL.md

Materializes a new skill against the unified template at `references/skill-template.md` (extracted from anthropics/financial-services). Runs `skill-auditor` on the new skill as a self-check before declaring success.

## ⚠️ Critical Constraints

- **Template is canonical.** All four modes produce SKILL.md files conforming to `references/skill-template.md`. Do not invent ad-hoc structures. **Why:** `skill-auditor` validates against this template; drift creates auditor false-fails.
- **Self-audit is mandatory.** After every successful build, the build script invokes `$skill-auditor` against the new skill directory. A FAIL verdict aborts the build. **Why:** PR-002 (external validation gate) — the builder must not declare its own work complete.
- **Codex parity is day-1, not later.** `from-scratch`, `from-template`, and `absorb-external` modes must produce both `skills/<name>/SKILL.md` AND `skills-codex/<name>/SKILL.md` + `skills-codex/<name>/prompt.md`. **Why:** finding `2026-05-03-codex-skill-shape-is-dual-file` — codex SKILL.md uses slim frontmatter (no `skill_api_version`); prompt.md is mandatory; `audit-codex-parity.sh` is a content scanner that won't catch frontmatter drift.
- **250-line ceiling on new SKILL.md.** Use `references/` for overflow. **Why:** finding `f-2026-05-01-025` — every skill invocation reloads 5-15KB; multi-lifecycle sessions compound to 150-200KB+ pure scaffolding.
- **Clean-room factory inputs only.** When using JSM-informed lessons, read [references/agentops-skill-factory.md](references/agentops-skill-factory.md) and use only AgentOps-owned summaries, scripts, and rubrics. **Why:** productization must improve structure without copying protected third-party skill content.

## Modes

| Mode | Status | Description |
|------|--------|-------------|
| `from-scratch` | stable | Interactive scaffold from canonical template. Produces full skill skeleton + scripts/validate.sh + codex parity. |
| `from-template` | stable | `--like <existing-skill>` copies structure from a sibling skill, swaps domain-specific sections. |
| `absorb-external` | stable | Reads external SKILL.md (e.g., from `~/dev/financial-services/.../<skill>/SKILL.md`), wraps in AgentOps frontmatter, invokes `$converter` for codex parity. |
| `from-pattern` | **alpha (passthrough)** | Delegates to `ao flywheel close-loop`. Outputs land at `.agents/knowledge/promoted/` per flywheel rules — they are NOT yet shaped as SKILL.md drafts. v2 will add skill-specific synthesis. Use `from-scratch` or `absorb-external` for SKILL.md output today. |

## Workflow

### Phase 1: Mode dispatch

`scripts/build.sh` reads `$1` and routes:

```bash
build.sh from-scratch <new-skill-name>          # → init.sh --interactive
build.sh from-template <new-skill-name> --like council
build.sh absorb-external <new-skill-name> --from /path/to/SKILL.md
build.sh from-pattern                            # → ao flywheel close-loop
```

**Checkpoint:** Confirm with user the new skill's `metadata.tier` and `metadata.dependencies` before generation.

### Phase 2: Materialize from template

`scripts/init.sh` reads `references/skill-template.md` (the canonical template section) and renders a SKILL.md skeleton with frontmatter pre-filled. For `from-template`, structure is copied from the source skill; section bodies are blanked and replaced with template stubs.

For `absorb-external`, the external SKILL.md's content (Constraints / Workflow / Output / Quality sections) is preserved verbatim where possible; AgentOps' structured frontmatter is added on top; the external description is reformatted to satisfy `description-has-triggers`.

**Checkpoint:** `$heal-skill --check skills/<new-name>` returns clean.

### Phase 3: Codex parity

`scripts/init.sh` invokes `$converter skills/<new-name> codex` to produce `skills-codex/<new-name>/{SKILL.md,prompt.md}`. Then trims `skill_api_version` from the codex SKILL.md (converter may preserve it). Asserts `prompt.md` exists.

**Checkpoint:** `bash scripts/audit-codex-parity.sh` returns clean AND `grep -q "^skill_api_version:" skills-codex/<name>/SKILL.md` returns nothing.

### Phase 4: Self-audit

The build script tail invokes `$skill-auditor` on `skills/<new-name>`. WARN is acceptable for v1 skills (e.g., `experimental` stability). FAIL aborts.

**Checkpoint:** `audit_pass=true` in build report.

### Phase 5: Factory score overlay

For AgentOps skill upgrades, use the productization score as a patch selector,
not as a replacement for `$skill-auditor`:

```bash
python3 skills-codex/skill-auditor/scripts/score_agentops_skill.py skills/<name> --markdown
```

Choose the smallest patch that improves the score while preserving the
canonical template and Codex parity constraints.

## Output Specification

**Format:** JSON conforming to `schemas/build-report.json` written to stdout; markdown audit report written to `.agents/audits/<skill>-build.md`.

**Files created (from-scratch mode):**

```
skills/<name>/
├── SKILL.md                         (≤250 lines, full template spine)
├── scripts/
│   └── validate.sh                  (self-validation per AgentOps convention)
└── references/                      (only if expected to exceed 400 lines)
skills-codex/<name>/
├── SKILL.md                         (slim frontmatter — no skill_api_version)
└── prompt.md                        (~10-20 line Execution Profile)
```

## Quality Rubric

- [ ] All four modes produce skills that pass `skill-auditor` PASS or WARN (not FAIL)
- [ ] Codex parity files exist and pass slim-frontmatter check
- [ ] No SKILL.md exceeds 250 lines (overflow goes to `references/`)
- [ ] Build report JSON validates against `schemas/build-report.json`
- [ ] `from-pattern` mode prominently marked alpha/passthrough in user output

## Examples

**Create a new skill from scratch:**

```bash
$skill-builder from-scratch hello-world
# → interactive prompt: tier? deps? primary deliverable?
# → writes skills/hello-world/SKILL.md + skills-codex/hello-world/{SKILL.md,prompt.md}
# → runs $skill-auditor on the new skill
```

**Clone structure from an existing skill:**

```bash
$skill-builder from-template my-new-skill --like council
# → mirrors council's section spine; substitutes new metadata
```

**Absorb a skill from anthropics/financial-services:**

```bash
$skill-builder absorb-external dcf-helper \
  --from ~/dev/financial-services/plugins/vertical-plugins/financial-analysis/skills/dcf-model/SKILL.md
# → preserves Constraints/Workflow/Output content, wraps in AgentOps frontmatter
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Self-audit FAIL | Generated SKILL.md missing required Pass-2 check | Re-run with `--verbose`; inspect which check failed; usually `output-spec-explicit` or `trigger-clarity` |
| Codex parity drift | `$converter` preserved `skill_api_version` | `init.sh` runs `sed -i '/^skill_api_version:/d' skills-codex/<name>/SKILL.md`; verify with grep |
| SKILL.md > 250 lines | Mode generated too much inline content | Move section bodies to `references/<topic>.md`; reference inline as `[text](references/<topic>.md)` |
| `from-pattern` produces no SKILL.md | Expected behavior — passthrough only in v1 | Use `from-scratch` or `absorb-external` if you need a SKILL.md draft |

## See Also

- skill-auditor — companion audit gate, invoked by build self-check
- heal-skill — structural hygiene (Pass 1 of skill-auditor wraps heal.sh)
- converter — produces codex parity artifacts
- scaffold — scaffolds projects/components/CI (NOT skills)
- forge — mines transcripts into learnings (different layer)

## Local Resources

### references/

- [references/skill-template.md](references/skill-template.md) — canonical SKILL.md template + auditor checklist + PRODUCT.md alignment
- [references/agentops-skill-factory.md](references/agentops-skill-factory.md) — clean-room factory workflow and productization rules

### scripts/

- `scripts/build.sh`
- `scripts/init.sh`
- `scripts/validate.sh`
