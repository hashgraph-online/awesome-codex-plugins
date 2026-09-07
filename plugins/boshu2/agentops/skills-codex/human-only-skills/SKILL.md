---
name: human-only-skills
description: 'Name the skills reserved for people to Triggers: "human-only skills", "which skills must I run myself".'
---
# Human-only skills

Four skills carry `disable-model-invocation: true`. In runtimes that honor
that key, their descriptions stay out of the context window and the model
cannot invoke them — a person types the command. In runtimes without the
switch, the key is stripped at projection time and these remain ordinary
advertised skills (see docs/contracts/codex-skill-api.md); the pointer below
still tells a person which ones to run themselves. This skill **names**
skills. It never invokes one.

## The roster

| Skill | A person reaches for it when |
|---|---|
| `craft-goal` | authoring or linting a persistent goal prompt meant to drive many bounded experiments toward one outcome — a standing artifact a person owns, not this session's intent |
| `learn` | mining a *collection* of durable verdicts for recurring evidence, after the critical path, on purpose |
| `postmortem` | testing one retrospective causal question against verdict evidence that already exists |
| `toil-mining` | mining supplied usage history for repeated operational work worth automating |

What they share: each is off the critical path, each is started deliberately
rather than inferred from a task, and nothing else in the repository reaches
for any of them.

## When a model wants one

Say which skill applies and why, and stop. Reproducing the skill's procedure
by hand defeats the point of removing it from model reach — the command exists
so a person decides the timing.

## Before adding a row

Model invocation is load-bearing whenever anything else reaches for the skill,
so a skill joins this roster only after all four surfaces come back clean, with
the evidence recorded:

1. `ao skills consumers <slug>` and `ao skills graph` — declared `dependencies`
   and `consumes` edges.
2. `workflows/*.js` — a workflow that dispatches the slug.
3. Other skills' `SKILL.md` bodies — a "routes to `<slug>`" sentence or a
   `See Also` entry is a reach.
4. `evals/routing-probes/templates.json` — an `applicable` entry means a probe
   measures whether the *model* routes there, which stripping makes
   unmeasurable rather than merely cheaper.

Retire this skill when the roster is empty.
