# Agent Skills Standard References for Skill-Maker

## Contents

- Refresh Policy
- Agent Skills Specification
- Best Practices for Skill Creators
- Evaluating Skill Output Quality
- Optimizing Skill Descriptions
- Using Scripts in Skills
- Distribution Through the Skills CLI
- Sources

The open standard every reviewed runtime builds on. This snapshot is the `PRIMARY` source for
frontmatter constraints and for the progressive-disclosure budgets; the provider snapshots next to it
record what each vendor adds on top.

## Refresh Policy

- last_verified_at: 2026-11-03
- refresh_when:
  - the specification changes a frontmatter constraint (name, description, compatibility, allowed-tools)
  - a progressive-disclosure budget changes (the listing-stage, instructions-stage, or line limits)
  - the reference validator (`skills-ref`) changes what it checks
  - the script-authoring page changes materially
- supports_rules:
  - `rules/skill-anatomy.md`
  - `rules/trigger-design.md`
  - `rules/progressive-disclosure.md`
  - `rules/resource-placement.md`
  - `rules/validation-and-iteration.md`

## Agent Skills Specification

- source_url: https://agentskills.io/specification
- last_verified_at: 2026-11-03
- applies_to: frontmatter fields and their constraints, directory conventions, progressive disclosure, file-reference depth, the reference validator. The page carries no visible date; its embedded `dateModified` metadata reads 2026-08-04.
- summary: A skill is a directory containing at minimum `SKILL.md`, with YAML frontmatter followed by
  Markdown body content. `name` and `description` are required; `license`, `compatibility`, `metadata`,
  and `allowed-tools` are optional. The body has no format restrictions. `scripts/`, `references/`, and
  `assets/` are optional conventions, not requirements.
- implication_for_hyper_skill: Enforce the required-field and constraint set exactly as stated below,
  and treat the optional directories as conventions this repository chose rather than as spec mandates.

### Frontmatter constraints as stated by the source

| Field | Required | Constraint |
|---|---|---|
| `name` | Yes | 1-64 characters. Lowercase letters, digits, and hyphens only. Must not start or end with a hyphen. Must not contain consecutive hyphens. **Must match the parent directory name** |
| `description` | Yes | 1-1024 characters. Non-empty. Describes both what the skill does and when to use it, and should carry the keywords an agent would match against |
| `license` | No | A license name or a reference to a bundled license file. Keep it short |
| `compatibility` | No | **1-500 characters if provided.** Only when the skill has environment requirements such as intended product, system packages, or network access |
| `metadata` | No | A map from string keys to string values. Keep keys unique to avoid collisions |
| `allowed-tools` | No | A space-separated string of pre-approved tools. **Experimental** - support varies between implementations |

- implication_for_hyper_skill: `name` matching the parent directory is a spec requirement, not a
  stylistic preference, so the rule text must say **must** and the validator must enforce it.

### Progressive disclosure and file references

- Three stages: metadata (`name` + `description`, loaded for all skills at startup, about 100 tokens),
  then the full `SKILL.md` body when the skill activates (under 5,000 tokens recommended), then
  `scripts/`, `references/`, and `assets/` as needed.
- Keep the main `SKILL.md` under 500 lines; move detailed material to separate files.
- Reference other files by relative path from the skill root, and keep references **one level deep**
  from `SKILL.md`; avoid deeply nested reference chains.
- implication_for_hyper_skill: the 500-line and 5,000-token figures are the source's; this repository
  additionally gates at 300 lines in `scripts/check-sources.sh`, which scopes to `instructions` only.
  Keep the two figures distinct rather than presenting 300 as sourced.

### Validation

- The source names a reference implementation, `skills-ref validate ./my-skill`, which checks that
  `SKILL.md` frontmatter is valid and follows the naming conventions.
- implication_for_hyper_skill: this repository runs it through `uvx` from
  `scripts/validate-skills.sh`, which is network-dependent and is **not** part of
  `bash scripts/verify.sh`; do not fold it into the offline gate silently.

## Best Practices for Skill Creators

- source_url: https://agentskills.io/skill-creation/best-practices
- last_verified_at: 2026-11-03
- applies_to: where a skill's content should come from, iterating against real execution, spending context wisely, gotchas, read cues, defaults
- summary: Skills should be grounded in real expertise rather than generated from general knowledge:
  extract from a hands-on task, or synthesize from existing project artifacts (internal docs, runbooks,
  API specifications, code-review comments, version-control history, real failure cases). Refine by
  running the skill against real tasks and reading execution traces, not just final outputs. For each
  piece of content ask "Would the agent get this wrong without this instruction?" and cut it if not.
  Match specificity to the fragility of the task, calibrating each part independently. Keep gotchas in
  `SKILL.md` where the agent reads them before meeting the situation; write read cues as conditions
  ("Read `references/api-errors.md` if the API returns a non-200 status code"). Provide defaults, not
  menus. It states the 500-line and 5,000-token budgets.
- implication_for_hyper_skill: require a named source of domain expertise before drafting a skill,
  require reading traces rather than outputs when a skill is refined, and keep gotchas in the core.

## Evaluating Skill Output Quality

- source_url: https://agentskills.io/skill-creation/evaluating-skills
- last_verified_at: 2026-11-03
- applies_to: test-case design, the with-skill/without-skill pair, per-run timing and grading records, human review, assertions, the iteration workspace
- summary: A test case is a prompt plus a human-readable expected output plus optional input files,
  stored in `evals/evals.json` inside the skill directory. Run each case twice - once with the skill and
  once without it, or against a previous version saved as `old_skill/` - in a clean context per run.
  Results go in a workspace beside the skill, one `iteration-N/` directory per pass, with `timing.json`
  (tokens and duration), `grading.json` (PASS or FAIL **with specific evidence**), and an aggregated
  `benchmark.json`. Human review goes in `feedback.json`; "Empty feedback means the output looked fine".
  Mechanical checks belong in a script. Remove or replace assertions that pass in both configurations.
  Start with 2-3 cases. Stop when results satisfy, feedback is consistently empty, or iterations stop
  improving meaningfully.
- implication_for_hyper_skill: the paired run, the evidence string, and the human feedback record are
  the load-bearing parts; a `passed: true` with no evidence string is not a record. This repository keeps
  the filenames but puts results under `.omo/evidence/` (`rules/resource-placement.md` §8).

## Optimizing Skill Descriptions

- source_url: https://agentskills.io/skill-creation/optimizing-descriptions
- last_verified_at: 2026-11-03
- applies_to: trigger rate as the metric, per-case runs and thresholds, train/validation selection, the description length limit
- summary: Trigger behaviour is probabilistic: run each query multiple times ("3 is a reasonable
  starting point") and pass a should-trigger query when its rate is above a threshold ("0.5 is a
  reasonable default"). Aim for about 20 queries, 8-10 each way; near-misses are the most valuable
  negatives. Split ~60/40 into train and validation, change the description only from train failures,
  and select by validation pass rate - the best description may not be the last. Re-check the
  1024-character limit on every edit. Five iterations is usually enough; then re-test on 5-10 fresh
  queries. Use imperative phrasing ("Use this skill when...").
- implication_for_hyper_skill: a run that reports only its final score is not evidence of improvement;
  report the per-iteration train and validation numbers.

## Using Scripts in Skills

- source_url: https://agentskills.io/skill-creation/using-scripts
- last_verified_at: 2026-11-03
- applies_to: how bundled code should be written and documented
- summary: Scripts must be non-interactive - "a hard requirement of the agent execution environment" -
  because a script that blocks on input hangs. `--help` is the primary way an agent learns the
  interface. Write helpful error messages that say what went wrong, what was expected, and what to try;
  reject ambiguous input with a clear error rather than guessing. Send structured data to stdout and
  diagnostics to stderr, use distinct exit codes, prefer idempotent operations, and bound output size.
  Paths in code blocks are relative to the skill root. Declare dependencies inline or state
  prerequisites in `SKILL.md`. The specification's `scripts/` section adds that scripts should be
  self-contained or document dependencies and handle edge cases gracefully.
- implication_for_hyper_skill: a script's interface is its `--help`, its exit codes, and its stdout;
  those are what the reviewer reads and what the validator should exercise.

## Distribution Through the Skills CLI

- source_url: https://github.com/vercel-labs/skills
- last_verified_at: 2026-11-03
- applies_to: installing, updating, and removing skills in the shared format across agents
- summary: `npx skills add`, `find`, `update`, `remove`, and `init` manage skills for OpenCode, Claude
  Code, Codex, Cursor, "and 75 more" agents; it requires Node.js 22.20 or later. Many agents share
  `.agents/skills/` as the project path and `~/.agents/skills/` as the global path; `-g`/`--global`
  installs to the user directory. Duplicate handling differs from Codex: when two skills share a name,
  the CLI keeps only the first one found.
- implication_for_hyper_skill: the install path differs per agent while the file does not, and
  duplicate-name behaviour is runtime-specific, so never write one rule for both.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The frontmatter field table and every constraint in it, the required/optional split, the directory conventions, the three-stage disclosure model, the 500-line guidance, the one-level-deep file reference rule, the `scripts/` self-containment and edge-case guidance, and the `dateModified` metadata | <https://agentskills.io/specification> |
| Grounding a skill in real expertise, refining it against traces, the removal question, specificity matched to fragility, gotchas in `SKILL.md`, conditional read cues, defaults over menus, and the 5,000-token budget | <https://agentskills.io/skill-creation/best-practices> |
| The test-case shape, `evals/evals.json`, the with-skill/without-skill or `old_skill/` pair, clean context per run, `timing.json`, `grading.json` with evidence, `benchmark.json`, `feedback.json`, the iteration workspace, the 2-3 case start, and the stop conditions | <https://agentskills.io/skill-creation/evaluating-skills> |
| Trigger rate, 3 runs, the 0.5 threshold, the ~20-query set, the ~60/40 split, train-only feedback, "the best may not be the last", the 1024-character re-check, five iterations, and 5-10 fresh queries | <https://agentskills.io/skill-creation/optimizing-descriptions> |
| Non-interactive scripts, `--help`, helpful errors, input rejection, stdout/stderr separation, exit codes, idempotency, output bounds, and skill-root-relative paths | <https://agentskills.io/skill-creation/using-scripts> |
| The skills CLI command set, the agent count wording, the shared project and global paths, the Node.js 22.20 requirement, and first-found duplicate handling | <https://github.com/vercel-labs/skills> |

### Evidence grade

`PRIMARY` - the specification page states the frontmatter constraints and the disclosure budgets
directly. The skills CLI row is `VENDOR` - one tool's statement about its own behaviour. An earlier
revision of this file attributed "handle edge cases" to the using-scripts page; the 2026-11-03 pass found
that sentence on the specification page, and the attribution is corrected above.
