---
name: skill-builder
description: Scaffold or absorb new SKILL.md files
---
# $skill-builder — Scaffold or absorb a new SKILL.md

Materializes a new skill against the unified template at `references/skill-template.md` (extracted from anthropics/financial-services). Runs the heal-skill deep audit on the new skill as a self-check before declaring success.

> **If unsure whether the work should be a skill, a Workflow, or an NTM swarm, run `$automation-shape-routing` first** — it is the front door that decides the shape and hands off to the right builder.

> **Before creating, search for an existing owner.** `ms search` the proposed skill's trigger phrases (fast path when available — `command -v ms`, or the `mcp__ms__search` tool is attached; else grep `skills/**/SKILL.md` + `docs/SKILLS.md`). A strong hit means **extend that skill, don't create a new one** — this is one item of the fuller skill-admission checklist (bead age-7d3r).

## ⚠️ Critical Constraints

- **Template is canonical.** All four modes produce SKILL.md files conforming to `references/skill-template.md`. Do not invent ad-hoc structures. **Why:** the heal-skill deep audit validates against this template; drift creates audit false-fails.
- **Self-audit is mandatory.** After every successful build, the build script invokes the heal-skill deep audit (`audit.sh` in `skills/heal-skill/`) against the new skill directory. A FAIL verdict aborts the build. **Why:** PR-002 (external validation gate) — the builder must not declare its own work complete.
- **Codex parity is day-1, not later.** `from-scratch`, `from-template`, and `absorb-external` modes must produce both `skills/<name>/SKILL.md` AND `skills-codex/<name>/SKILL.md` + `skills-codex/<name>/prompt.md`. **Why:** finding `2026-05-03-codex-skill-shape-is-dual-file` — codex SKILL.md uses slim frontmatter (no `skill_api_version`); prompt.md is mandatory; `audit-codex-parity.sh` is a content scanner that won't catch frontmatter drift.
- **Editing an EXISTING skill also needs a manual twin mirror.** When you change `skills/<name>/references/*.md` or `SKILL.md`, manually mirror the content into `skills-codex/<name>/` (runtime-native), THEN run `scripts/regen-codex-hashes.sh --only <name>`. `make regen-all` only refreshes the twin's *hash record*, not its prose — a green `✓ codex hashes` over a stale twin looks handled but isn't. Verify with a content diff (`grep -c <new-token>` on both copies), not the hash exit code. **Why:** finding `2026-06-16-codex-twin-content-not-auto-mirrored` (age-aqu/age-yxl) — regen made the marker self-consistent with a stale twin (0-vs-2 token divergence) and nothing complained. The parity gate now blocks an un-mirrored `references/**` edit, but the mirror is still a manual step.
- **250-line ceiling on new SKILL.md.** Use `references/` for overflow. **Why:** finding `f-2026-05-01-025` — every Skill() invocation reloads 5-15KB; multi-lifecycle sessions compound to 150-200KB+ pure scaffolding.
- **Clean-room factory inputs only.** When using lessons learned from external corpora, read [references/agentops-skill-factory.md](references/agentops-skill-factory.md) and use only AgentOps-owned summaries, scripts, and rubrics. **Why:** productization must improve structure without copying protected third-party skill content.
- **Real gate means exit code.** Validate with `heal-skill --check --strict <skill-dir>` and the heal-skill deep audit (`audit.sh`); never infer green from grep/regex output. **Why:** regex presence checks created false-greens during the 2026-06 scale build.
- **One skill directory = one writer.** Bulk builds fan out only when each worker owns a distinct new `skills/<name>/` plus `skills-codex/<name>/`; edits to existing skill dirs run in a later serial wave. **Why:** concurrent writers deleted untracked work and flipped HEAD mid-task.
- **Trust repository state, not subagent reports.** Before declaring success, inspect `git status`, generated hashes, final files, and gate exit codes. **Why:** sandbox-overlay and stale self-reports can claim work that never persisted.
- **Clean-room includes names.** Do not reuse exact third-party skill names; mint AgentOps-owned names before source skills, Codex mirrors, or wrappers are keyed. **Why:** provenance/IP safety applies to labels as well as prose and scripts.
- **Do not use the Workflow tool as the skill factory.** For scale authoring, use deterministic wave scripts or NTM/Agent Mail lanes with one worker per skill. **Why:** skill creation needs file ownership and durable git evidence, not opaque background self-reporting.

## Modes

| Mode | Status | Description |
|------|--------|-------------|
| `from-scratch` | stable | Interactive scaffold from canonical template. Produces full skill skeleton + scripts/validate.sh + codex parity. |
| `from-template` | stable | `--like <existing-skill>` copies structure from a sibling skill, swaps domain-specific sections. |
| `absorb-external` | stable | Reads external SKILL.md (e.g., from `~/dev/financial-services/<some-dir>/<skill>/SKILL.md`), wraps in AgentOps frontmatter, invokes `$converter` for codex parity. |
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

**Checkpoint:** `heal-skill --check --strict skills/<new-name>` exits 0.

### Phase 3: Codex parity

`scripts/init.sh` invokes `$converter skills/<new-name> codex` to produce `skills-codex/<new-name>/{SKILL.md,prompt.md}`. Then trims `skill_api_version` from the codex SKILL.md (converter may preserve it). Asserts `prompt.md` exists.

**Checkpoint:** `bash scripts/audit-codex-parity.sh` returns clean AND `grep -q "^skill_api_version:" skills-codex/<name>/SKILL.md` returns nothing.

### Phase 4: Self-audit

The build script tail invokes the heal-skill deep audit on `skills/<new-name>`. WARN is acceptable for v1 skills (e.g., `experimental` stability). FAIL aborts.

**Checkpoint:** `audit_pass=true` in build report.

### Phase 5: Factory score overlay

For AgentOps skill upgrades, use the productization score as a patch selector,
not as a replacement for the deep audit:

```bash
python3 skills/heal-skill/scripts/score_agentops_skill.py skills/<name> --markdown
```

Choose the smallest patch that improves the score while preserving the
canonical template and Codex parity constraints.

### Phase 6: Scale factory discipline

For more than one skill, run in ownership waves:

1. Create-only wave: one worker per new skill directory.
2. Mutate wave: existing skill directories only after source creation settles.
3. Mirror/package wave: Codex mirrors and generated hashes after the canonical
   source corpus is complete.

Every wave ends with `git status`, `scripts/regen-all.sh --check`, and the
relevant target gates by exit code. If ownership overlaps, stop and rescope.

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

- [ ] All four modes produce skills that pass the heal-skill deep audit with PASS or WARN (not FAIL)
- [ ] `heal-skill --check --strict` exits 0 for every generated source and Codex skill directory
- [ ] Codex parity files exist and pass slim-frontmatter check
- [ ] Batch authoring has one writer per skill directory and validates persisted git state
- [ ] Clean-room review covers exact names as well as prose, scripts, and examples
- [ ] No SKILL.md exceeds 250 lines (overflow goes to `references/`)
- [ ] Build report JSON validates against `schemas/build-report.json`
- [ ] `from-pattern` mode prominently marked alpha/passthrough in user output

## Examples

**Create a new skill from scratch:**

```bash
$skill-builder from-scratch hello-world
# → interactive prompt: tier? deps? primary deliverable?
# → writes skills/hello-world/SKILL.md + skills-codex/hello-world/{SKILL.md,prompt.md}
# → runs the heal-skill deep audit on the new skill
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

## Corpus authoring health

Skill selection is pure LLM reasoning over the `description` field, so a missing
trigger phrase is a skill that silently never fires. The per-skill auditor checks
this only as a WARN, so the gap accumulates. Audit the whole corpus at once:

```bash
python3 skills/skill-builder/scripts/scan_descriptions.py skills          # remediation report
python3 skills/skill-builder/scripts/scan_descriptions.py skills --strict # exit 1 on any miss
```

The scanner mirrors the deep audit's three-form trigger detection and adds a
suggested `Triggers:` stub per offender. See
[references/skill-authoring-standard.md](references/skill-authoring-standard.md)
for the full authoring doctrine and the best-practice-to-enforcement crosswalk.

## See Also

- [heal-skill](../heal-skill/SKILL.md) — structural hygiene (heal.sh) + companion deep-audit gate (audit.sh), invoked by build self-check
- [converter](../converter/SKILL.md) — produces codex parity artifacts
- [scaffold](../scaffold/SKILL.md) — scaffolds projects/components/CI (NOT skills)
- [curate](../post-mortem/SKILL.md) — `--mode=forge` mines transcripts into learnings (different layer)

## References

- [references/skill-template.md](references/skill-template.md) — canonical SKILL.md template + auditor checklist + PRODUCT.md alignment
- [references/agentops-skill-factory.md](references/agentops-skill-factory.md) — clean-room factory workflow and productization rules
- [references/skill-authoring-standard.md](references/skill-authoring-standard.md) — clean-room best-practices doctrine + best-practice-to-enforcement crosswalk; backs the `scan_descriptions.py` trigger scanner
- [references/skill-builder.feature](references/skill-builder.feature) — Executable spec: mode dispatch, materialize from template, Codex parity bundle, self-audit + factory score (soc-qk4b)
- [references/hyper-extract-design-steals.md](references/hyper-extract-design-steals.md) — authoring rules stolen from Hyper-Extract: the WHAT-vs-HOW (schema vs guideline) contract, canonical `{from}\|{rel}\|{to}` identifier dedup-key form, and folded graph-designer/yaml-validator/template-optimizer patterns (age-bp1)
