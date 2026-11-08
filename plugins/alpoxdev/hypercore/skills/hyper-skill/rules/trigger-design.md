# Trigger Design

**Purpose**: Make skills trigger on the right requests and stay out of the way on the wrong ones.

Trigger behaviour is probabilistic. Nothing in this file is proven by reading one sentence, so every rule
below is written to be checkable rather than asserted.

## 1. Description Rules

The `description` must explain:

- what the skill does
- when it should be used
- which neighboring requests it should not own when ambiguity is likely

Weak:

```yaml
description: Helps with skills.
```

Better:

```yaml
description: Use this skill when the user asks to create or refactor a reusable Codex skill folder, including SKILL.md trigger wording, rules, references, scripts, assets, and validation checks. Do not use for generic documentation that is not a skill.
```

Write the description in **third person**. It is injected into a system prompt, and a description that
shifts point of view ("I can help you…", "You can use this to…") causes discovery problems. Prefer the
imperative `Use this skill when…` shape used above, which is already third-person and outcome-first.

## 2. Writing Pattern

- Start with `Use this skill when...` when the runtime accepts prose descriptions.
- Put user intent and outcome before internal implementation details.
- Put the most important trigger terms in the **first sentence**. Every reviewed runtime may shorten or
  drop the tail of a long description (§6), so the trigger cannot depend on the closing clause.
- Include a short negative boundary when the skill has close neighbors. A description that says only
  when to fire gives the selector no way back.
- Avoid descriptions so broad they overlap every meta-skill.

## 3. The Two Axes

Build trigger examples along **two orthogonal axes**. They do not replace each other, and only crossing
both catches real failures.

| Axis | Values | What it verifies |
|---|---|---|
| Activation | positive / negative / boundary | Whether the description responds only to the right requests |
| Invocation mode | explicit / implicit / contextual / negative control | Whether it matches without the name, and does not misfire |

| Invocation mode | Meaning | Example |
|---|---|---|
| explicit | Names the skill directly | `Use $hyper-skill to build a skill` |
| implicit | Matches the description in natural language without the name | `Create a reusable skill folder for me` |
| contextual | A real work sentence mixed with domain context | `Make this migration review procedure run identically every time` |
| negative control | A similar request that must not activate | `Clean up this runbook so it reads better` |

## 4. Trigger Case Shape

A trigger case is not a boolean. Each case carries its own repetition count and threshold, and the run
records the resulting rate:

```json
[
  { "id": "p1", "prompt": "Create a Codex skill for SQL migration review", "expect": "trigger", "runs": 3, "threshold": 0.5 },
  { "id": "p2", "prompt": "Refactor this SKILL.md so it loads references correctly", "expect": "trigger", "runs": 3, "threshold": 0.5 },
  { "id": "p3", "prompt": "스킬 폴더를 새로 만들고 검증 규칙까지 넣어줘", "expect": "trigger", "runs": 3, "threshold": 0.5 },
  { "id": "n1", "prompt": "Rewrite this runbook for readability", "expect": "no_trigger", "runs": 3, "threshold": 0.5 },
  { "id": "n2", "prompt": "Summarize these OpenAI docs", "expect": "no_trigger", "runs": 3, "threshold": 0.5 },
  { "id": "b1", "prompt": "Create a guide for writing skills", "expect": "no_trigger", "runs": 3, "threshold": 0.5, "note": "depends on output shape" }
]
```

A run appends the measured `trigger_rate` to each case, so the result file carries the same keys plus the
outcome:

```json
{ "id": "p1", "expect": "trigger", "runs": 3, "threshold": 0.5, "trigger_rate": 1.0 }
```

Rules:

- **Every case states its own `runs` and `threshold`.** Do not let a case inherit a default; the value
  must be visible at the point of use, because `runs` changes what the rate means.
- `3` runs and a `0.5` threshold are the **starting point** the standard recommends, not a validated
  optimum. Raise `runs` when the observed spread is too wide to separate the case from its threshold.
- Do not pad the set to a target size. A case that probes nothing new adds calls, not evidence. Add a row
  only when it probes something the existing rows do not, and promote each real failure into a row.
- This is a `stochastic-model` measurement: record the model and runtime identity and the run count with
  the result, and note that a fixed seed alone does not estimate variance.

## 5. Description Optimization

Writing a description once is not the whole job; repeated edits overfit the examples they were tuned on.
These rules are normative.

- SK-O-1: Split the query set into **train and validation**. Improve against train; **select** by validation pass rate.
- SK-O-2: **The best description may not be the last one.** When a later iteration scores lower on validation, keep the earlier iteration.
- SK-O-3: Descriptions grow while you optimize. Re-check the **1024-character limit** on every edit.
- SK-O-4: When fine-tuning stops helping, **change the structure** - a different framing or a different sentence shape, not another adjective.

A run that reports only its final validation score is not evidence of improvement. Report the train and
validation numbers for each iteration so the selection is visible.

The source adds practical bounds, stated as recommendations rather than validated optima: about 20
queries (8-10 should-trigger, 8-10 should-not), a roughly 60/40 train/validation split held fixed across
iterations, only train failures fed back into the edits, about five iterations, then a re-test on 5-10
fresh queries. Near-miss queries are the most valuable negatives.

## 6. Description Budgets

The description competes for a listing budget, and each reviewed runtime measures and cuts it
differently.

| Runtime | Limit that binds | What happens when it overflows |
|---|---|---|
| Agent Skills spec | `description` 1-1024 characters | Not defined; the field is validated, not trimmed |
| Codex | Initial list at 2% of the context window, or 8,000 characters when the window is unknown; `skills.max_context_tokens` raises it to at most 10,000 tokens | Descriptions are **shortened first**; for large skill sets some skills may then be **omitted from the initial list entirely**, with a warning |
| Claude Code | 1% of the context window, with each entry's `description` + `when_to_use` truncated at **1,536 characters** | Descriptions are dropped starting with the **least-invoked** skills; every name survives |
| Claude API | At most 20 skills per request | Consolidate skills or route requests to different skill sets |

Consequences:

- The 1,024-character spec limit and the 1,536-character Claude Code listing cut are different limits.
  Fit the description to the tightest limit of every runtime the skill will be installed in.
- Lead with the key trigger. A description whose distinguishing words sit at the end can lose them before
  a request is ever matched against it.
- The Codex failure mode is not only truncation. A skill that does not appear in the initial list is not
  a candidate at all, so a description that is merely long is a real availability risk.
- Neither runtime reports a cut description as an error: a skill that lost its keywords looks the same
  as one that never matched.
- **This repository is already over the Codex budget** when the context window is unknown - see the
  measurement under Sources. A longer description needs a reason.

## 6a. Manual-Only Skills

A skill whose automatic activation could cause damage the user did not intend - deploying, publishing,
deleting, sending - should be marked manual so only explicit invocation runs it:
`disable-model-invocation: true` in Claude Code, `policy.allow_implicit_invocation: false` in Codex
`agents/openai.yaml`. Both are runtime-only switches (`rules/skill-anatomy.md`, SK-P-3): name the runtime
beside each, and keep the side-effect gate in the skill's own contract as well, because a runtime that
ignores the switch will still auto-select the skill.

## 7. Coexistence

A skill does not trigger in isolation. Adding one can degrade another by taking its requests.

- **Coexistence is an evaluation dimension, not an afterthought.** The question is: does adding this
  skill degrade existing skills? The named failure is a new description broad enough to **steal triggers**
  from an existing skill.
- Measure it with a near-miss case: a request that shares the new skill's verbs and nouns but belongs to
  a neighbor. That is the case that fails when a description is too broad, and it is the case a plain
  negative example cannot catch.

The measured overlap in this repository is recorded under Sources. The token `refactor` is shared by
this skill and several sibling artifact-authoring skills, so the coexistence case must distinguish a
reusable *skill folder* from a reusable *prompt*, *document*, or *instruction file*. The measurement
names counts, not the neighbors: a rule file that names them would stop being usable on its own
(`rules/self-containment.md`, SK-S-2).

## 8. Scope Boundaries

State what the skill does not own. Describe every boundary by the output shape, never by naming the skill
that owns it (`rules/self-containment.md`, SK-S-2).

Examples:

- this skill owns a skill folder or a skill refactor
- a general document, runbook, or guide is out of scope
- a reusable prompt artifact is out of scope
- source-backed fact-finding is out of scope
- planning before implementation is out of scope
- commit creation is out of scope

## 9. Anti-Patterns

- vague descriptions
- descriptions that list tools but not the job
- descriptions that list jobs but not trigger timing
- no should-not-trigger examples
- descriptions so broad they overlap neighboring skills
- a trigger case that inherits its `runs` or `threshold` instead of stating them
- reporting only the final validation score, so the selection between iterations is invisible
- growing a description without re-checking the length limit
- no near-miss case, so trigger stealing is never measured
- a deploy, publish, or delete skill left open to automatic activation without a manual-only switch and a contract gate

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The four invocation modes (explicit, implicit, contextual, negative control), the 10-20 prompt starting set, and the four evaluation axes | <https://developers.openai.com/blog/eval-skills> |
| Trigger rate as the metric, 3 runs, the 0.5 default threshold, the train/validation split, "the best may not be the last", the 1024-character re-check, the structural-change fallback behind `SK-O-1` to `SK-O-4`, the ~20-query / five-iteration / 5-10 fresh-query bounds, and near-misses as the most valuable negatives | <https://agentskills.io/skill-creation/optimizing-descriptions> |
| The 1024-character `description` limit, and `name` matching the parent directory | <https://agentskills.io/specification> |
| The Codex 2% / 8,000-character listing budget, `skills.max_context_tokens` up to 10,000 tokens, shorten-then-omit, the omission warning, and `allow_implicit_invocation` | <https://learn.chatgpt.com/docs/build-skills> |
| The Claude Code 1% listing budget, the 1,536-character per-entry cut, least-invoked-first dropping, and `disable-model-invocation` | <https://code.claude.com/docs/en/skills> |
| Coexistence as an evaluation dimension, the trigger-stealing failure, and the 20-skills-per-request API limit | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise> |
| The `stochastic-model` measurement contract for a measured rate | `instructions/autoresearch/references/config-and-metrics.md` §2 |
| Repository measurement, 2026-11-03: 40 skills whose `description` fields total 15,869 characters (over the 8,000-character fallback); `refactor` appears in 7 descriptions and `create` in 14 | this repository |

### Evidence grade

The optimization rules are `PRIMARY` - the specification site states them directly. The 10-20 prompt
figure and the ~20-query bound are starting points that sources recommend, not validated optima, and
this file does not state a required case count for that reason. The listing behaviour is `VENDOR`: each
runtime describes its own cut, and they differ. The repository figures are measurements of this
repository, kept here at the bottom so refreshing them does not touch the rule text above.
