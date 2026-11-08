# Resource Placement

**Purpose**: Put each piece of skill content in the file type that matches its responsibility.

## 1. Placement Matrix

| Content | Placement | Reason |
|---|---|---|
| When to use the skill | `description`, routing rule | Discovery and trigger signal |
| Job, boundary, top-level workflow, stop condition | `SKILL.md` | Always needed after activation |
| Reusable policies and repeated decisions | `rules/` | Applies across runs |
| Official docs, schemas, domain details, long examples | `references/` | Load only when needed |
| Deterministic validation or transformation | `scripts/` | More reliable than prose |
| Templates, reusable eval fixtures, static output resources | `assets/` or `assets/evals/` | Copied, filled, embedded into output, or reused by validators |
| Runtime metadata | `agents/` | Platform-specific display, invocation policy, and dependencies - for example Codex `agents/openai.yaml` - and only when a runtime consumes it |

## 2. Decision Order

Ask these in order:

1. Is this the core identity, trigger, boundary, or stop condition?
2. Is this reusable policy or repeated decision guidance?
3. Is this detailed knowledge loaded only when needed?
4. Is this better as deterministic execution?
5. Is this an output resource rather than reasoning context?
6. Is this platform metadata consumed by a runtime or UI?

## 3. Rules vs References

Use `rules/` for judgment:

- when to add scripts
- when a deterministic validator belongs in `scripts/`
- how to validate trigger examples
- how to handle source-sensitive claims
- how to split core and references

Use `references/` for knowledge:

- official documentation summaries
- API schemas
- long examples
- provider-specific edge cases
- domain glossary

## 4. Scripts

Add scripts only when one or more is true:

- the same check or transform repeats often
- a command sequence is fragile
- machine-readable output is needed
- failure messages help the agent self-correct
- version pinning or parameter normalization improves reliability

Document every script with purpose, usage, dependencies, expected output, and failure behavior.

Put deterministic validators in `scripts/`. For `hyper-skill`, the validator belongs in `scripts/validate-hyper-skill.sh` and should consume repo-local files and eval fixtures without network, credentials, commits, or product-file mutation.

Bundled scripts are bash. The rule is one runtime and one extension: every non-directory entry under a
package's `scripts/` directory is a `.sh` file, and a `.sh` script's first line is `#!/usr/bin/env bash`.

- Do not ship `.mjs`, `.py`, `.cjs`, `.js`, `.rb`, or extensionless executables under `scripts/`. A
  non-`.sh` file in that directory is a validation error, not a style preference.
- Do not invoke a second shell from a script. Pass values as quoted arguments, and never interpolate user
  input into a command line that a shell re-parses.
- Why bash and not another runtime: the harness that runs these scripts already supplies a POSIX shell
  (macOS `/bin/bash` 3.2 and Linux bash 4/5), so a bash script needs no separate runtime install. Stay
  inside bash 3.2 features - no associative arrays, `mapfile`/`readarray`, `${var,,}`/`${var^^}`, namerefs,
  or `wait -n` - and use only POSIX utilities plus `jq` for JSON, so one file runs on both platforms.
- Tell the consumer what the package needs: when a package bundles a script, state the shell and the
  external tools (for example bash 3.2+ and jq) in the `compatibility` frontmatter so a reader learns it
  before running anything.
- The deterministic validator enforces the extension rule and the bash shebang, so a bundled script that
  breaks either fails validation instead of shipping. It also fails closed: a `scripts/` directory it
  cannot read is an error, because the rule cannot be verified there.

## 5. Assets

Use assets for files that support output generation:

- report templates
- prompt templates
- JSON schemas
- reusable eval fixtures, especially JSONL cases under `assets/evals/`
- examples that are copied or filled

Do not use assets for reasoning-only documentation.

## 6. Placing Official References

Do not embed long official-documentation evidence in the core. Split it out:

```text
references/
└── official/
    ├── agent-skills-standard.md
    ├── openai.md
    └── anthropic.md
```

Each file includes the date checked, the source URL, the claims that affect this skill, drift caveats, and
the summary that was promoted into a core rule.

**`references/official/agent-skills-standard.md` is the canonical filename for the open standard's
snapshot.** The standard is the primary source for frontmatter constraints and for the disclosure
budgets, so a package that cites it must carry it under that name rather than folding it into a
vendor file.

## 7. Placing Eval Resources

Split eval material into "explanations you read" and "fixtures you run or compare".

```text
assets/
└── evals/
    ├── trigger-cases.jsonl
    └── workflow-cases.jsonl

references/
└── eval-rubric.md
```

- `assets/evals/*.jsonl` holds machine-readable cases a parser or runner can read.
- `references/eval-rubric.md` holds human-readable scoring criteria and caveats.
- When a deterministic runner exists, put it in `scripts/run-evals.*` and document its dependencies and expected output.
- When an eval case requires an external source, link the source URL, accessed date, and freshness caveat inside the case or in the source ledger.

**Compatibility with packaged eval tooling.** `assets/evals/` is this repository's convention, and no
packaged tool reads it. Anthropic's `skill-creator` reads `evals/evals.json` at the skill root, whose
entries carry prompts, input files, expected behavior, and assertions. Claude Code's `claude plugin
eval` uses its own case format, and the vendor states the two formats are **not interchangeable**. So
keep `assets/evals/` as the set this repository's runner reads; when a skill is also evaluated by one of
those tools, add that tool's file **and** keep it in sync with `assets/evals/`, or generate it from
`assets/evals/` with a script. Two eval sets that have drifted apart are worse than one canonical set.

## 8. Where Execution Results Go

The fixtures above are inputs. The **results** of running them live outside the skill folder.

These are normative.

- SK-E-1: Keep execution results **outside the skill folder**, under `.omo/evidence/<skill>/iteration-N/`. A shipped skill does not carry its own run history.
- SK-E-2: Every run leaves `timing.json` (tokens and wall time) and `grading.json` (per-assertion pass/fail **plus the evidence string**). A `passed: true` with no evidence string is not evidence.
- SK-E-3: Run each execution in an **independent session**. Reusing one session lets the earlier run's context contaminate the next.
- SK-E-4: Check mechanical assertions (valid JSON, row counts, file existence) with a **script**, not a judge.
- SK-E-5: Human review lives in `feedback.json` beside the eval directories, keyed by eval id: a specific complaint string per case, an empty string when the case passed review. It is written by the reviewer, never generated from the grades.
- SK-E-6: When comparing versions, keep the previous version as `old_skill/` inside the iteration directory and record which snapshot commit or copy it came from, so the comparison can be repeated.

The layout:

```text
.omo/evidence/<skill>/iteration-N/
├── benchmark.json
├── feedback.json
└── eval-<case>/
    ├── with_skill/
    │   ├── outputs/
    │   ├── timing.json
    │   └── grading.json
    └── without_skill/
        ├── outputs/
        ├── timing.json
        └── grading.json
```

When the baseline is a previous version rather than "no skill", replace `without_skill/` with
`old_skill/` and keep the snapshot the run pointed at.

**The upstream results location differs, and the divergence is deliberate.** The source puts results in
a workspace beside the skill folder. This repository already had two competing placements for eval
material; adding a third would leave no single answer, and the evidence directory has precedent here.
The trade-off is real: results do not travel with a distributed skill, so a reader outside this
repository cannot see them. The filenames come from the source; only the location is this
repository's choice.

## 8a. Placing Volatile Values

A runtime that keeps skill names, descriptions, or an invoked `SKILL.md` in every session makes that
text part of a reused prompt prefix. Edits to it invalidate cached reuse for every session that loads it.

- Keep the loaded head stable: edit the `name`, the `description`, and the top of `SKILL.md`
  deliberately and in batches, not on every refresh.
- Move volatile values - "last checked" dates, version pins, counts, machine paths - to the bottom of a
  file or into `references/`. A refreshed date then touches the tail, not the head.
- Split by stability, not only by length: stable contract text in `SKILL.md`, fast-moving provider detail
  in `references/`.
- List bundled files in a stable order under stable names.

These rules never outrank correctness: a wrong head is fixed regardless of cache cost.

## 9. Install Trust and Provenance

Where a skill came from is part of what it is.

- A project-scoped skill directory is **not** a trust boundary by itself. A documented runtime gates
  project skills behind an explicit trust step and quarantines a skill that fails its scan.
- Record install provenance - source identifier, content hash, and scanner result - rather than relying on
  the directory's location.
- Third-party skills and bundled scripts are subjects of **code review**, not prompt snippets.
- Prefer scripts with explicit inputs over dynamic shell interpolation, and never embed credentials in a
  skill file, example, or script.
- Mutable state must never be written into the install tree.

## 10. Forbidden Patterns

- `SKILL.md` becoming a reference knowledge base
- a `references/` file requiring several further reference hops
- creating scripts without stating their usage condition in `SKILL.md`
- assets not connected to the actual workflow
- copying long passages of official documentation verbatim
- leaving eval fixtures as a prose checklist so they cannot be re-run
- writing the safety boundary only as a final-answer tone rule without connecting it to a tool gate
- execution results committed inside the shipped skill folder
- two eval sets (`assets/evals/` and a packaged tool's case file) that have drifted apart
- volatile dates, counts, or version pins placed in the loaded head of `SKILL.md`

## 11. Completion Criteria

- [ ] Every support file has a placement reason.
- [ ] Every support file is discoverable from `SKILL.md` or a directly linked rule.
- [ ] Scripts/assets have usage and validation notes.
- [ ] Deterministic validators live in `scripts/`; reusable eval fixtures live in `assets/evals/`.
- [ ] Provider-sensitive content is isolated into references.
- [ ] Core trigger logic is not hidden in references.
- [ ] The standard snapshot exists at `references/official/agent-skills-standard.md`.
- [ ] Eval execution results are written outside the skill folder, with per-run timing, grading, and human feedback records.
- [ ] If the skill is evaluated by `skill-creator` or `claude plugin eval`, that tool's case file exists and matches the fixtures the repository runner reads.
- [ ] Volatile values sit outside the loaded head of `SKILL.md`.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| Execution results kept outside the skill folder, per-run `timing.json` and `grading.json` with evidence strings, an independent session per run, mechanical assertions checked by script, human review in `feedback.json`, and `old_skill/` as the previous-version arm - the basis of `SK-E-1` to `SK-E-6` | <https://agentskills.io/skill-creation/evaluating-skills> |
| The sibling-workspace results layout, which this repository diverges from deliberately | <https://agentskills.io/skill-creation/evaluating-skills> |
| `evals/evals.json` as the `skill-creator` input, and the `claude plugin eval` format being a different, non-interchangeable one | <https://code.claude.com/docs/en/skills> |
| Keeping the loaded head stable and moving volatile values out of it | `instructions/cache/CACHE.md` §3 |
| The `references/official/` convention and its per-file contents | `instructions/skill/references/resource-placement.md` §5 |
| Project-skill trust gating, scan quarantine, and recorded install provenance | <https://github.com/alpoxdev/hypercore/blob/01be78de5973eb75a616e5156058621a6fabbc97/instructions/cli/hermes-agent/SKILLS.md> |
| Skills registered read-only, namespaced, and never written to in the install tree | <https://github.com/alpoxdev/hypercore/blob/01be78de5973eb75a616e5156058621a6fabbc97/instructions/cli/hermes-agent/PLUGIN_AUTHORING.md> |
| `skills-ref validate` as the reference validator for a skill directory | <https://agentskills.io/specification> |
| Windows hosts Command Prompt and Windows PowerShell as its console applications; the page names those two, not a POSIX `sh` | <https://support.microsoft.com/en-us/windows/apps/command-prompt-and-windows-powershell> |
| A harness on native Windows uses Git for Windows for its Bash tool and falls back to PowerShell when it is absent, so a `sh` script may not run at all | <https://code.claude.com/docs/en/setup> |

### Evidence grade

The placement and cost-recording rules are `PRIMARY` - the evaluating-skills page states them. The
specific directory layout is a **repository decision**, not a sourced one: it records the choice and its
trade-off rather than presenting itself as the standard's layout.
