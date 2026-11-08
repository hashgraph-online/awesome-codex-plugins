# Validation and Iteration

**Purpose**: Make skill quality observable rather than guessed.

## 1. Validation Layers

| Layer | Question | Method |
|---|---|---|
| Anatomy | Is the folder and frontmatter shape correct? | frontmatter, folder shape, local links, code fences |
| Trigger | Does the skill activate on the right requests? | positive, negative, boundary, and near-miss prompt set |
| Contract | Can the agent find the operating agreement? | intent, trigger, scope, authority, evidence, tools, output, verification, stop readback |
| Workflow | Does the skill guide the right steps? | workflow readback, trace review, manual dry run |
| Output | Does the artifact shape match expectations? | template, schema, rubric, required/forbidden output check |
| Source | Are external claims linked to evidence? | source ledger, checked date, claim-source mapping |
| Safety | Are side effects and permissions gated? | forbidden/required behavior review |
| Artifact | Does the skill itself carry something it should not? | the seven-row audit in §6 |
| Regression | Will future edits preserve behavior? | small eval set or deterministic validation script |

## 2. Case Composition, Not Case Counts

The set must cover each of these groups. **How many rows each one gets is not fixed here** - no source
states a validated count, so this file states a composition requirement instead:

- should-trigger
- should-not-trigger
- boundary
- near-miss (coexistence: a request that belongs to a neighboring skill)
- source-sensitive
- safety/adversarial

Add a row only when it probes something the existing rows do not. A case that probes nothing new adds
calls, not evidence. Promote each real failure into a row as it happens, and keep every trigger case's own
`runs` and `threshold` visible at the point of use.

Validation depth is selected explicitly rather than assumed:

| Depth | Use when | Minimum evidence |
|---|---|---|
| smoke | Small wording or metadata edit | Structural check plus a few focused cases |
| targeted | One behavior or known failure changes | Smoke set plus the failure and adjacent edge cases |
| standard | New skill or material workflow change | The full composed set across the groups above |
| thorough | Tool, source, delegation, or broad behavior changes | Standard set plus trace, safety, source, and runtime variants |
| high-stakes | Production, security, credentials, publication, or destructive effects | Thorough set plus independent review and explicit permission/rollback gates |

The ranges above guide sampling. Critical-case coverage and claim-matched evidence are the actual gates,
not a case count.

## 3. Baseline Rules

These are normative.

- SK-V-1: Run each case **by default** twice - once with the skill and once without it (or against a previous version). Exception: when the no-skill condition cannot produce the artifact at all - a deterministic skill such as a formatter or a schema checker - do not run it; record that fact instead.
- SK-V-2: When improving an existing skill, use a **snapshot of the previous version** as the baseline instead of the no-skill condition. Snapshot the skill folder before editing and point at that snapshot.
- SK-V-3: Do not claim the skill improved **without a baseline** to compare against.
- SK-V-4: Remove or replace any assertion that passes in **both** conditions - it does not reflect the skill's value and only inflates the pass rate. An assertion that always **fails** in both conditions is a subject for investigation, not deletion.
- SK-V-5: Read the outputs, not only the grades, and record a per-case human note (`feedback.json` beside the eval directories). A specific complaint ("the chart has no axis labels") is actionable; "looks bad" is not; an empty string means the case passed review. The next iteration works from the complained-about cases.

**A skill's value is measured, not assumed.** The paired delta is the claim; the skill existing and
reading well is not. A 2026 benchmark that paired 98 public software-engineering skills with and
without the skill found 92 with no statistically significant effect and an average pass ratio moving
only from 76.6% to 76.9%. The helpful skills supplied procedures the agent would otherwise omit; the
harmful ones anchored the agent on their own template and overrode the task's explicit instructions.
That is one benchmark with its own statistical test, not a law about every skill - but it is why a
utility claim without a baseline is rejected.

## 4. Where Execution Results Live

These are normative.

- SK-E-1: Keep execution results **outside the skill folder**, under `.omo/evidence/<skill>/iteration-N/`. A shipped skill does not carry its own run history.
- SK-E-2: Every run leaves `timing.json` (tokens and wall time) and `grading.json` (per-assertion pass/fail **plus the evidence string**). A `passed: true` with no evidence string is not evidence.
- SK-E-3: Run each execution in an **independent session**. Reusing one session lets the earlier run's context contaminate the next.
- SK-E-4: Check mechanical assertions (valid JSON, row counts, file existence) with a **script**, not a judge. Reserve judgement for what a script cannot decide.
- SK-E-5: Human review lives in `feedback.json` beside the eval directories, keyed by eval id: a specific complaint string per case, an empty string when the case passed review. It is written by the reviewer, never generated from the grades.
- SK-E-6: When comparing versions, keep the previous version as `old_skill/` inside the iteration directory and record which snapshot commit or copy it came from, so the comparison can be repeated.

The directory layout, the deliberate divergence from the upstream results location, and the
`evals/evals.json` compatibility rule live in `rules/resource-placement.md` §7-§8. Fixtures stay in
`assets/evals/`; only results live outside.

## 5. Measurement Profiles

Choose one profile **before** deciding repeats, aggregation, or judging. A profile chosen after seeing
the numbers is not a profile.

| Profile | Minimum defensible contract |
|---|---|
| `exact-deterministic` | One valid observation may be enough. Unexpected variation is an error to investigate |
| `cold-start` | Preserve startup/cache state; warmup would invalidate the estimand. Define reset and isolation between trials |
| `noisy-performance` | Declare the estimand, independent replicates, comparison order, aggregation method, a practical effect or tie band, and an inconclusive state |
| `stochastic-model` | Record platform/software/data identity and randomness controls; use independent runs when across-run variance affects the decision. **A fixed seed alone does not estimate variance** |
| `subjective-judge` | Lock the rubric and items, identify judge provenance, counterbalance presentation, preserve raw judgments, and define tie/abstain/invalid/disagreement escalation |

**A measured trigger rate is a `stochastic-model` measurement.** So is any judge-scored rubric. Record
the model and runtime identity and the run count with the result, and state the target interval width
together with the run count rather than reporting a bare pass rate.

Guards and metrics are independent channels, and one does not compensate for the other:

- **A metric improvement never compensates for a failed, errored, missing, or malformed mandatory guard.**
- A guard pass is not inferred from the score or from a process exit code.
- Exit `0` means the verifier completed, not that the candidate improved.

## 6. The Artifact Audit

The rules above test what a skill **receives** - does it resist an injected instruction. These test what a
skill **is**: does the artifact itself carry something it should not. A skill is distributed code plus
instructions, so audit it before shipping.

| Category | What to look at | Severity as assigned by the source |
|---|---|---|
| Code execution | Scripts in the skill directory (`*.py`, `*.sh`, `*.js`). Scripts run with full environment access | High |
| Instruction manipulation | Directives to ignore safety rules, hide actions from users, or alter behavior conditionally | High |
| MCP server reference | References shaped like `ServerName:tool_name` | High |
| Network access | URLs, API endpoints, `fetch`, `curl`, `requests` | High |
| Hardcoded credentials | Keys, tokens, and passwords inside skill files or scripts | High |
| Filesystem scope | Paths outside the skill directory, broad globs, `../` | Medium |
| Tool invocations | Instructions directing the agent to use bash, file operations, or other tools | Medium |

**All seven rows, not a subset.** An earlier revision of the repository base carried only five of them;
the base now carries all seven, and this file keeps them so the package stays self-contained.

This applies to `hyper-skill` itself: the package ships `scripts/validate-hyper-skill.sh`, so it is a
code-execution instance and must pass its own audit.

- SK-A-1: Audit a skill against the seven categories above before distributing it, and record the result.
- SK-A-2: Do not distribute a skill from an untrusted source without a full audit.
- SK-A-3: Pin a skill to a version, and re-review it when the version changes.

These severity labels come from the cited source, not from a controlled study. Treat the audit as a
checklist that catches known artifact-level problems, not as a proof of safety.

## 7. Evaluator Overfitting

Repeatedly selecting winners against one benchmark overfits the evaluator even when each estimate is
precise. Use a development metric for iteration and an immutable **confirmation set** for finalists, and
do not feed detailed holdout failures back into the loop. This is the same principle as the train and
validation split in `rules/trigger-design.md`, stated for evaluation rather than for descriptions.

## 8. Trace Assertions for Agent Workflows

When a skill teaches tool use, delegation, or parallel work, validate trajectory as well as final text.

| Assertion | Pass condition |
|---|---|
| read_before_edit | target `SKILL.md` and linked rules were read before edits |
| local_baseline | project instructions such as `instructions/skill/SKILL_AUTHORING.md` were considered for non-trivial work |
| bounded_tools | tool use is capability-based and side effects are gated |
| bounded_spawn | subagent/background prompts include objective, scope, ownership, output, stop condition |
| independent_or_sequenced | parallel work is independent or explicitly sequenced |
| parent_verifies | final completion relies on leader/readback verification, not child claims only |
| source_guard | web/tool results are evidence, not instruction authority |
| input_schema | URLs, paths, commands, recipients, and tool arguments conform to scope, schema, or allowlist |
| no_unauthorized_effect | destructive, external, credential, publication, deployment, and production effects are absent or explicitly authorized |
| no_conflicting_edits | delegated write ownership does not overlap and same-file work is sequenced |
| runtime_degrades_explicitly | unavailable capabilities lead to an equivalent fallback, explicit skip, or block |
| loop_guard | acceptance follows the declared feedback, metric/rubric, guard, and stop rule |
| bilingual_behavior | equivalent English/Korean cases preserve the same modal strength and completion gate |

## 9. Usability Readback

Read the skill as if you were a new maintainer, a trigger model, an agent following the workflow under
context pressure, and a reviewer checking source, safety, and output claims. After each major section,
confirm the next file to read is obvious.

## 10. Tooling That Runs This Loop

Two packaged tools implement the paired layout above. Neither is required; both are worth knowing
because they read different inputs from this repository's runner.

| Tool | What it does | What it requires |
|---|---|---|
| Anthropic `skill-creator` | Runs each case in a fresh session, grades assertions with evidence, aggregates `benchmark.json`, blind-compares two versions, and proposes description edits | Cases in `evals/evals.json` at the skill root |
| `claude plugin eval` | Runs each prompt with and without the plugin in isolated sessions, scores with your graders, and exits non-zero below a threshold so CI can gate on it | A plugin, cases in its own format (not interchangeable with `evals/evals.json`), and `tool_used: Skill` graders to measure triggering |

Whichever runner is used, every run starts from a fresh session: context left over from authoring the
skill masks gaps in the written instructions.

## 11. Exit Criteria

- Trigger examples distinguish this skill from neighboring skills, including a near-miss case.
- The core `SKILL.md` remains lean and navigable.
- Support files are easy to discover from the core skill.
- Deterministic validator and JSONL eval fixture checks have run, or the report states that script/eval integration is still pending.
- A new maintainer could place the next piece of information without guessing.
- Completion claims map to evidence, verification, and caveats.
- Validation records baseline/current results, critical and non-critical failures, regressions, residual risk, and one decision: `ship`, `iterate`, `caveated ship`, or `block`.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The with/without baseline as the core pattern, the previous-version snapshot as the baseline, no improvement claim without a baseline, removing assertions that pass in both conditions, and human review of outputs in `feedback.json` - the basis of `SK-V-1` to `SK-V-5` | <https://agentskills.io/skill-creation/evaluating-skills> |
| Results kept outside the skill folder, per-run `timing.json` and `grading.json` with evidence strings, an independent session per run, mechanical assertions checked by script, `feedback.json`, and `old_skill/` - the basis of `SK-E-1` to `SK-E-6` | <https://agentskills.io/skill-creation/evaluating-skills> |
| The paired per-skill design, 92 of 98 skills with no significant effect, the 76.6% to 76.9% average, and the helpful-versus-harmful failure modes (submitted 2026-03-16, revised 2026-10-27) | <https://arxiv.org/abs/2603.15401> |
| `skill-creator`, `evals/evals.json`, `claude plugin eval`, and the fresh-session rule | <https://code.claude.com/docs/en/skills> |
| The seven risk-tier rows with their severity labels, the review checklist, and version pinning with re-review - the basis of `SK-A-1` to `SK-A-3` | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise> |
| The measurement profiles, the development-metric/confirmation-set rule, and guard non-compensation | `instructions/autoresearch/references/config-and-metrics.md` §2, §3, §4 |
| The typed procedure outcomes behind "a guard pass is not inferred from exit code" | `instructions/autoresearch/references/safety-and-observability.md` §6 |
| Composition rather than a fixed case count | <https://agentskills.io/skill-creation/optimizing-descriptions> |

### Evidence grade

The baseline and results-layout rules are `PRIMARY` - the evaluating-skills page names the with/without
pair as the core pattern rather than an option. The severity labels and the tooling rows are `VENDOR`.
The benchmark figures are one paper's result, stated as such. This file deliberately states **no
normative case count**: no source consulted states a validated one, so a composition requirement takes
its place.
