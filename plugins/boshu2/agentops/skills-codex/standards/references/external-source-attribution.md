---
type: reference
parent_skill: standards
title: External-source attribution patterns (ACFS/gstack/...)
---

# Attribution Patterns for External-Source Absorption

When a skill or reference absorbs patterns from an external corpus (ACFS, gstack, or any third-party knowledge source), attribution is required even when the absorption is pattern-only and contains no verbatim text. Two attribution patterns are supported. Pick one per skill based on source-count.

## Pattern A — Skill-level `LICENSE.md`

Use when the skill is **primarily derived from a single external source**.

- Place at `skills/<name>/LICENSE.md`.
- Reference from `SKILL.md` as **plain text**, never as a relative markdown link:
  - ✅ `See \`LICENSE.md\` in this skill directory for attribution.`
  - ❌ `See [LICENSE.md](LICENSE.md) for attribution.`
- The relative-link form breaks `mkdocs --strict` because mkdocs flattens skill directories during build (`skills/<name>/SKILL.md` → `skills/<name>.md`), so the sibling-file link `[LICENSE.md](LICENSE.md)` resolves to `skills/LICENSE.md` which does not exist.
- Example path: `skills/<name>/LICENSE.md` (the former `system-tuning` skill used this pattern before its 2026-06 retirement).

## Pattern B — Per-reference footer

Use when the skill's `references/*.md` files draw from **two or more external sources**.

- Each `references/<topic>.md` file gets a footer block at the bottom:
  ```markdown
  ---
  **Source:** Adapted from <corpus> / <doc-name>. Pattern-only, no verbatim text.
  ```
- The skill's `SKILL.md` does not need its own attribution — the per-ref footers cover all absorbed material.

## Choice rule

| If | Use |
|---|---|
| All references in the skill share one source | Pattern A (skill-level `LICENSE.md`) |
| References draw from 2+ sources | Pattern B (per-reference footer) |
| Mix: skill body has one primary source but one reference is from another | Pattern A for the skill + Pattern B footer on the divergent reference |

## Constraints (binding for any pattern)

- **Pattern-only, no verbatim text.** Do not copy >5 consecutive words from the external source.
- **Attribute the canonical pattern title** when one exists (e.g., "Asuper-style sync" → cite Asupersync corpus).
- **Do not use relative markdown links to root-level co-located files in `SKILL.md`** — `references/` subdir works (`[name](references/name.md)`), but root-level files (`LICENSE.md`, `notes.md`) do not. mkdocs `--strict` will fail the build.
- **Apply a clean-room policy for any external-corpus-derived work.** Allowed observations are counts, paths, filenames, metadata, package shape, validation outcomes, CLI behavior, and derived categories. Do not copy external prose, prompts, examples, references, scripts, templates, or role text.

## Cross-references

- Pattern A example: any skill carrying a single-source `LICENSE.md` at its root (see the path rule above).
