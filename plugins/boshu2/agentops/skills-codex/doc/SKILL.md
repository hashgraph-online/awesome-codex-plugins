---
name: doc
description: Generate and validate repo docs, READMEs
---
# Doc Skill

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Generate and validate documentation for any project. `--mode` selects the artifact family — the default mode handles code/API docs and code-maps; `--mode=readme` generates a gold-standard README; `--mode=oss` scaffolds and audits the open-source doc pack.

## Constraints

- Ground every documentation claim in the current repository, because plausible but stale prose is a documentation defect.
- In OSS scaffold mode, create missing docs only by default; never update or overwrite an existing doc unless the user explicitly confirms, because these files may contain operator-owned policy and project history. Treat `refresh` as a separate opt-in path and confirm its target writes with the user before proceeding.
- Keep mode boundaries explicit and run the selected mode's validation, because default, README, and OSS outputs have different completion criteria.

## Modes

| `--mode` | Artifact | Read first |
|----------|----------|-----------|
| *(default)* | API docs, code-maps, doc coverage/validate | this file |
| `readme` | Gold-standard README (interview → generate → deterministic checks) | [references/readme-craft.md](references/readme-craft.md) |
| `oss` | OSS doc pack (CONTRIBUTING/CHANGELOG/AGENTS.md, audit + scaffold) | [references/oss-pack.md](references/oss-pack.md) |

**Mode routing (absorbed skills):**

| You typed | Runs |
|-----------|------|
| "readme", "rewrite the README", "validate the README" | Doc in `readme` mode |
| "oss docs", "scaffold contributing", "audit OSS docs" | Doc in `oss` mode |

When invoked with `--mode=readme` or `--mode=oss`, read the corresponding reference above and follow its workflow verbatim. The default-mode steps below apply only when no mode (or the implied code-docs mode) is selected.

## Execution Steps (default mode — code/API docs)

Default mode is deliberately thin. Given a Doc command and target:

1. **Detect project type** — `ls package.json pyproject.toml go.mod Cargo.toml` + existing `docs/`; classify CODING / INFORMATIONAL / OPS.
2. **Run the command** — `discover` (grep undocumented funcs), `coverage` (documented vs total), `gen [feature]` (read code → stamp function/class markdown), `all`, or `validate`.
3. **Write the report** to `.agents/doc/YYYY-MM-DD-<target>.md` (coverage %, generated, gaps, validation issues), then report coverage + gaps to the user.

Full step-by-step detail — grep recipes, function/class + code-map templates, the report skeleton, key rules, worked examples, and the troubleshooting table — lives in **[references/default-mode.md](references/default-mode.md)** (moved there in the generic-craft trim). Read it when you need the exact shapes; otherwise just do the three steps.

## Output Specification

- **Path:** default-mode reports go to the artifact directory `.agents/doc/`; README mode updates the repository `README.md`; OSS scaffold mode creates missing root documentation only by default. The separate OSS `refresh` path may update an existing doc only after explicit user confirmation.
- **Filename:** default reports use the filename convention `YYYY-MM-DD-<target>.md`; README and OSS filenames follow their mode references.
- **Format:** outputs are Markdown; the default report schema records coverage percentage, generated artifacts, gaps, and validation issues.
- **Validation command:** validate the skill contract with `bash skills/doc/scripts/validate.sh`, then run the mode-specific validation required by its reference before reporting completion.
- **Downstream handoff:** return changed paths, validation results, coverage or remaining gaps, and any blocked decision to the requesting caller or evidence consumer.

## Quality Checklist

- Every factual claim is traceable to inspected code, configuration, or existing documentation.
- Generated documentation follows the selected mode's templates and preserves useful existing depth.
- Completion reports name the validators run and disclose unresolved gaps rather than implying full coverage.

## Reference Documents

- [references/default-mode.md](references/default-mode.md) — default mode (code/API docs): the full Steps 1-7 detail — grep recipes, function/class + code-map templates, report skeleton, worked examples, troubleshooting (moved out of SKILL.md in the generic-craft trim)
- [references/doc.feature](references/doc.feature) — Executable spec: detect project type, generate type-appropriate docs from the repo, validate existing docs against source (soc-qk4b)
- [references/readme.feature](references/readme.feature) — Executable spec (`--mode=readme`): mode detection, problem-first lead, trust block near install, collapse-don't-delete depth, evidence reporting, and anti-pattern detection
- [references/oss-docs.feature](references/oss-docs.feature) — Executable spec (`--mode=oss`): audit existing/missing OSS docs, scaffold missing without overwrite, project-type-tailored (soc-qk4b)

- [references/readme-craft.md](references/readme-craft.md) — `--mode=readme`: the 8 gold-standard README patterns, interview, generation structure, deterministic checks, and anti-pattern table
- [references/oss-pack.md](references/oss-pack.md) — `--mode=oss`: audit + scaffold the OSS doc pack (CONTRIBUTING/CHANGELOG/AGENTS.md), project-type templates
- [references/oss-documentation-tiers.md](references/oss-documentation-tiers.md) — OSS doc tier definitions (core/standard/enhanced)
- [references/oss-project-types.md](references/oss-project-types.md) — Per-type OSS scaffolding templates (cli/operator/service/library/helm)
- [references/generation-templates.md](references/generation-templates.md)
- [references/prose-and-report-workmanship.md](references/prose-and-report-workmanship.md)
- [references/project-types.md](references/project-types.md)
- [references/validation-rules.md](references/validation-rules.md)
- [references/de-slopify.md](references/de-slopify.md) — Remove AI writing artifacts from docs
- [references/architecture-report.md](references/architecture-report.md) — Generate technical architecture documents

## Examples

- Default mode documents the changed surface using `references/default-mode.md`.
- `readme` mode creates or revises the repository README.
- `oss` mode creates the explicitly requested open-source documentation pack.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Default mode feels heavyweight | Read [references/default-mode.md](references/default-mode.md) — or just ask the model directly for simple docs |
| README evidence has gaps | Report the concrete gaps; the caller decides whether to start a revision |
