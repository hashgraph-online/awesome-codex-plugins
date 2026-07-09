# AgentOps Skill Authoring Standard

Clean-room distillation of the broadly accepted SKILL.md best practices
(Anthropic Agent Skills guidance and the wider community consensus), restated in
AgentOps's own words and cross-walked to what AgentOps tooling *actually*
enforces. This is the doctrine layer behind `skill-builder`, the heal-skill deep audit,
and `heal-skill` — read it before authoring or absorbing a skill.

This file contains only AgentOps-owned summaries and rules. It does not copy any
third-party skill content (see [agentops-skill-factory.md](agentops-skill-factory.md)).

## Contents

- [Mental model: three loading levels](#mental-model-three-loading-levels)
- [The description is the trigger mechanism](#the-description-is-the-trigger-mechanism)
- [Naming (AgentOps house style)](#naming-agentops-house-style)
- [Progressive disclosure](#progressive-disclosure)
- [Degrees of freedom](#degrees-of-freedom)
- [Anti-patterns](#anti-patterns)
- [Crosswalk: best practice to AgentOps enforcement](#crosswalk-best-practice-to-agentops-enforcement)

## Mental model: three loading levels

A skill costs context in three tiers, and good authoring minimizes the lower
tiers:

1. **Metadata** (`name` + `description`) — always in the system prompt. ~100
   tokens. This is the only thing the runtime sees when *deciding* whether to
   load the skill.
2. **SKILL.md body** — loaded only after the skill triggers. Keep it under the
   250-line ceiling; push overflow into `references/`.
3. **Bundled `references/` and `scripts/`** — read or executed only when the
   body points to them. Effectively unlimited, because they load on demand.

The implication that drives every rule below: the description does all the
selection work, and the body is read far less often than authors assume.

## The description is the trigger mechanism

Skill selection is **pure LLM reasoning over descriptions** — no embeddings, no
keyword index. A description without explicit trigger phrases is a skill that
silently never fires. This is the single largest latent gap in the corpus: most
skills score 1/3 on trigger quality because they describe *what* the skill does
but never *when* to invoke it.

Write descriptions that are:

- **Third person.** "Scaffolds a new skill", not "I help you scaffold".
- **Specific.** Name the artifact and the domain, not "helps with skills".
- **Trigger-bearing.** Include the phrases a user or agent would actually say.

The deep audit (`heal-skill/scripts/audit.sh`) accepts a trigger in any of three forms; satisfy at least one:

- **Block scalar** — `description: |` with `**Use when:**` / `**Triggers:**`
  lines inside the folded value.
- **Explicit marker** — a `Triggers:` or `Use when:` clause in the
  single-line description (the most common AgentOps form).
- **Triggers list** — a `metadata.triggers:` YAML list with three or more items.

Audit the whole corpus for this gap at any time:

```bash
python3 skills/skill-builder/scripts/scan_descriptions.py skills
python3 skills/skill-builder/scripts/scan_descriptions.py skills --strict   # exit 1 on any miss
python3 skills/skill-builder/scripts/scan_descriptions.py skills --json     # robot mode
```

The scanner applies the exact detection logic of `heal-skill/scripts/audit.sh`,
so its verdict never contradicts the per-skill auditor; it adds the prioritized
remediation list and a suggested `Triggers:` stub the auditor does not provide.

## Naming (AgentOps house style)

The external standard prefers gerund names (`processing-pdfs`). **AgentOps
deliberately diverges**: skills are named for the noun or verb of the workflow
(`skill-builder`, `bug-hunt`, `crank`, `council`) so they read as commands in
the `/skill` slash-menu. This is an intentional, documented deviation — keep new
skills consistent with the existing corpus rather than introducing gerunds.

## Progressive disclosure

- Keep `references/` **one level deep**. No chains
  (`SKILL.md -> a.md -> b.md`); the runtime may partial-read a deep file.
- Reference files over ~100 lines should open with a short table of contents.
- A SKILL.md over ~250 lines must externalize the overflow into `references/`.
  the deep audit warns (`references-modularization`) above 400 lines with no
  `references/` directory.
- Distinguish **execute** from **read** when pointing at a script: "Run
  `python scripts/x.py`" versus "See `scripts/x.py` for the algorithm".

## Degrees of freedom

Match instruction specificity to how fragile the task is:

- **High freedom** — multiple valid approaches (e.g. review guidelines). Give
  direction, not steps.
- **Medium freedom** — a preferred pattern with acceptable variation (e.g.
  report templates). Give a default and an escape hatch.
- **Low freedom** — error-prone, consistency-critical (e.g. a migration
  command). Give the exact invocation and forbid alternatives.

## Anti-patterns

- **Multiple options, no default.** Pick one tool, name it, then offer the
  escape hatch ("for scanned PDFs, use X instead").
- **Human docs in the skill.** No README / CHANGELOG / install guide; skills are
  for agents.
- **Inconsistent terminology.** Choose one term for a concept and use it
  throughout.
- **Time-sensitive claims.** "Currently" and dated facts rot; move volatile
  detail to an "old patterns" section or a generated artifact.
- **Hardcoded absolute paths.** Use repo-relative paths so the skill is portable.
- **Vague descriptions.** The fastest way to ship a skill that never triggers.

## Crosswalk: best practice to AgentOps enforcement

| Best practice | AgentOps enforcement | Gate |
|---------------|----------------------|------|
| Description carries triggers | `description-has-triggers`, `trigger-clarity` | auditor WARN (corpus drift accumulates) |
| `name` matches directory | `heal.sh` NAME_MISMATCH | CI FAIL (`skills-integrity`) |
| `name` + `description` present | `heal.sh` MISSING_NAME / MISSING_DESC | CI FAIL |
| Output spec names format + path | `output-spec-explicit` | auditor FAIL |
| Constraints front-loaded with rationale | `constraints-frontloaded`, `rationale-present` | auditor WARN |
| References one level deep, linked | `heal.sh` UNLINKED_REF / DEAD_REF | CI FAIL / WARN |
| 250-line ceiling | `skill-builder` build rejects > 250 | build-time only (no CI gate) |
| Frontmatter schema valid | `validate-skill-schema.sh`, v2 frontmatter | CI FAIL |
| Dependencies resolve | dependency-resolution check | CI FAIL |
| Codex parity (dual-file) | manual `skills-codex/`, parity-drift audit | CI FAIL (semantic), manual mirror |
| Registry / catalog current | `generate-registry.sh`, `generate-skill-catalog.sh` | CI FAIL (registry) / advisory (catalog) |

WARN-severity checks do not block a merge, which is exactly why trigger quality
drifted across the corpus. Treat a WARN as a real finding, not noise — run the
scanner and close the backlog incrementally.
