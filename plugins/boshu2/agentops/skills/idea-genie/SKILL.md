---
name: idea-genie
description: 'Brainstorm evidence-backed options for what to build, or stress-test an idea. Use when: deciding what to build next, comparing options or testing an idea.'
practices: [lean-startup, bdd-gherkin, design-by-contract, llm-eval-harness, adr]
hexagonal_role: domain
consumes: [repo-context, task-question, idea-portfolio.v1]
produces: [idea-portfolio.v1, idea-challenge.v1]
context_rel:
- kind: customer-of
  with: research
- kind: supplier-to
  with: plan
skill_api_version: 1
user-invocable: true
metadata:
  tier: execution
  dependencies: []
  capabilities: [generate_evidenced_options, dueling_idea_genies]
  effects: [write_idea_portfolio]
  canonical_status: canonical
  disposition: keep_strategy
output_contract: idea-portfolio.v1 JSON validated by this skill's scripts/validate-output.sh (elicit mode), or idea-challenge.v1 JSON validated by this skill's scripts/validate-challenge.sh (duel mode)
---

# Idea Genie

One canonical root for idea work: elicit an evidence-grounded portfolio of
options, or challenge a consequential idea with sealed independent
perspectives. Both modes explore and advise; neither selects, schedules,
tracks, implements, or validates work.

## Modes

| Trigger phrases | Mode | Output contract |
|---|---|---|
| "idea genie", "what should we build next", "brainstorm options", "supported opportunities" | elicit | `idea-portfolio.v1` |
| "challenge this idea", "compare independent proposals", "stress-test a one-way door" | duel | `idea-challenge.v1` |

Elicit is the entry mode. Duel is an optional escalation for a consequential
choice, typically consuming an `idea-portfolio.v1` or a framed question. A
scored multi-member duel, where members score each other's ideas, is
[Council](../council/SKILL.md)'s duel mode; a plan's failure modes belong to
[Premortem](../premortem/SKILL.md).

Both validators live in this skill's `scripts/` directory and need `jq`.
Without `jq`, check the fields by hand against the shape and say the validator
did not run.

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows it
as "Base directory for this skill"; Codex lists this skill's SKILL.md path; in
an AgentOps source checkout it is `skills/idea-genie`. Replace `<skill-dir>`
with that absolute path before running a command. The working directory stays
the user's repository. If the host did not show where this skill is installed,
use the directory of the SKILL.md you read. If you cannot determine it, do not
guess a path or run a same-named script from the current repository; say the
bundled script is unavailable and check the fields by hand against the shape,
as without `jq`.

## Elicit mode

These rules carry the value:

1. **Observations cite a source:** a file and line, issue, doc or measurement.
   Anything uncited is an assumption, listed apart and never used as support.
2. **Every candidate cites the observations behind it.** No cited support, no
   candidate; an unsupported idea may stay listed as an assumption. Never pad
   the list to a count.
3. **Check overlap before claiming novelty.** Compare each candidate with what
   the product already does and with earlier decisions that still apply (an
   ADR, closed issue or recorded lesson). A request an existing capability
   already covers is not new: record it under `overlaps` of the candidate it
   sharpens, or leave it out. Keep an idea a decision rejected only with new
   evidence that answers its reason, citing the decision under `overlaps`.
4. **One Given/When/Then per candidate**, a normal or edge case whose Then
   shows the cited problem easing; a Then that could hold while the problem
   remains aims at a proxy. A goal or a symptom is not yet the problem: cite
   its cause, or list the cause as an assumption and let the Then show the
   cited symptom easing.
5. **Do not rank, pick, schedule or start work.** The caller or Plan selects.
6. **Stop at saturation.** Merge equivalents, and run another pass only while
   it adds a materially new evidenced candidate. Zero candidates is valid.
7. **Generate before judging.** Split the subject into the parts its evidence
   shows, named in its own words rather than as a directory listing, and draft
   across each before filtering. Then reshape the predictable first ideas:
   remove or invert a step, break an assumption treated as fixed, push a
   constraint to an extreme, borrow how another field solves the same problem,
   or find a move that makes later moves cheaper. A candidate any project could
   list unchanged gets a specific observation or is dropped. Keep a one-line
   reason for each dropped idea in `dropped` so a later pass does not
   regenerate it, and list there any part left with no supported candidate.
8. **Behavior outweighs stated interest.** "Users asked for it" is weaker than
   what they do now: the workaround they already use, what it costs them, and
   observed adoption of anything similar. Name the status quo each candidate
   must beat in `status_quo`; if nobody is working around the problem today,
   say so there.

State the question, constraints, non-goals and sources first. Read only the
sources this question needs and cite each one; do not build a merged context
store.

Inside a named part (a flow, command, page or stage), go as far as the
evidence allows: a candidate that reshapes the wider product is a scope
overrun, and one that swaps the subject for another domain replaces it. Drop
either with that reason unless a cited observation shows the part cannot
change without it. With no named subject, sample each top-level area and the
recent commits instead of guessing one focus, and let each candidate's
evidence show why its subject deserves attention.

Return the portfolio in this shape:

```json
{
  "schema_version": "idea-portfolio.v1",
  "status": "candidates",
  "observations": [{"claim": "<what is true>", "evidence": "<cited source>"}],
  "assumptions": ["<belief no cited source supports>"],
  "candidates": [{
    "id": "I1",
    "idea": "<short name>",
    "evidence": ["<cited source>"],
    "overlaps": ["<existing capability or decision it extends or repeats>"],
    "status_quo": "<what people do today instead, or none>",
    "scenario": {"given": "<state>", "when": "<event>", "then": "<observable result>"}
  }],
  "dropped": [{"idea": "<short name>", "reason": "<overlap, no evidence, or why it lost>"}]
}
```

Each candidate `evidence` entry repeats an observation's `evidence` exactly.
Candidate ids are unique and `overlaps` may be empty. `dropped` is optional
while there are candidates. When every idea overlaps or lacks support, set
`status` to `no-new-work`, leave `candidates` empty and list each idea in
`dropped` with the capability, decision or missing evidence that removed it.
The validator rejects any other field, so no rank or winner rides along. For a
person, render the same fields as a short list, one block per candidate. When
a file is wanted, write `.agents/scratch/ideas/<run-id>/idea-portfolio.json`
and check it with `bash "<skill-dir>/scripts/validate-output.sh" <path>` before
returning it to the caller.

## Duel mode

Produce independent challenges for a consequential choice. The result is
advisory evidence for Plan: return it to the caller, who may supply it to
Plan beside research and operator intent. It never decides whether a plan is
ready and never turns a later optional Premortem challenge into an approval
gate. Emit no readiness, approval, quorum, retry, budget, helper, delivery, or
tracker state: this strategy supplies evidence, not lifecycle authority.
Consensus, transport availability or a self-score never becomes readiness.

**Door class.** Ask what undoing the choice after it lands would cost. A
one-way door needs a migration, breaks a published contract or caller, loses
data, or has an external effect that cannot be recalled: run the workflow
below. A cheap two-way door is undone by a revert or a flag: run Plan's
[one fresh challenge](../plan/references/challenge.md) instead and return its
findings, with no packet, panel, pane manager or model-family rule.

### Workflow

1. Freeze the question, constraints, evidence paths and comparison rubric.
   Leave unknowns open. An assumption only one approach needs stays with that
   approach; in the shared constraints it would rule rivals out unseen.
2. Start at least two fresh contexts: separate subagents or sessions with no
   shared transcript, one prompt each carrying the frozen question and
   evidence paths and asking for the return in
   [sealed perspectives](references/sealed-perspectives.md#brief). Record each
   native context id as `context_id`, and collect every perspective before
   revealing any, so later proposals cannot anchor on earlier ones. When the
   caller pins perspectives to model profiles, dispatch them as
   [model-dispatch](../agent-native/references/model-dispatch.md) describes
   and record each profile name as `model_identity`; disclose an unavailable
   profile and continue single-model.
3. Reveal the sealed perspectives and cross-review every one by evidence,
   reversibility, system fit, failure modes and cost.
   Compare perspectives by mechanism, not by name: two that rely on the same
   mechanism count as one alternative, and fewer than two distinct ones is an
   incomplete comparison, not a winner; one bounded recovery is in
   [convergence](references/sealed-perspectives.md#convergence). A perspective
   that breaks a frozen constraint is out, whatever its other strengths.
   A combination of parts from several perspectives is a new candidate with no
   inherited support: walk one concrete example through each guarantee the
   combined design needs before listing it, or list it as unchecked so Plan
   does not combine on trust.
4. Attempt concrete refutations. A premise of the frozen question that every
   perspective builds on gains no support from their agreement: check it at
   its source. Refute a stateful mechanism with a
   [state trace](references/sealed-perspectives.md#state-trace), not prose.
   Keep disagreements, failed refutations and minority reasoning explicit, so
   the caller sees the alternatives a synthesis would erase.
5. Return the packet below. When a file is wanted, write
   `.agents/scratch/ideas/<run-id>/idea-challenge.json` and check it with
   `bash "<skill-dir>/scripts/validate-challenge.sh" <path>`.

```json
{
  "schema_version": "idea-challenge.v1",
  "door_class": "one-way",
  "sealed_generation": true,
  "perspectives": [
    {"id": "P1", "context_id": "<native context id>", "proposal": "<mechanism, evidence, tradeoff>"},
    {"id": "P2", "context_id": "<a different context id>", "proposal": "<mechanism, evidence, tradeoff>"}
  ],
  "cross_reviews": [
    {"reviewer": "P1", "subject": "P2", "dimensions": {"evidence": "<finding>", "reversibility": "<finding>", "system_fit": "<finding>", "failure_modes": "<finding>", "cost": "<finding>"}},
    {"reviewer": "P2", "subject": "P1", "dimensions": {"evidence": "<finding>", "reversibility": "<finding>", "system_fit": "<finding>", "failure_modes": "<finding>", "cost": "<finding>"}}
  ],
  "disagreements": ["<where the perspectives still differ>"],
  "refutations": [{"claim": "<what was attacked>", "attempt": "<the concrete test>", "result": "<what the attempt showed>"}]
}
```

Each perspective has a distinct `id` and `context_id` and a `proposal`, plus
`model_identity` when pinned. Every perspective is the `subject` of at least
one cross-review by another; `dimensions` uses only the five rubric keys, each
holding a text finding. `disagreements` and `refutations` each need at least
one entry. The validator rejects any other field; an older packet's `handoff`
(`owner` `plan`, `artifact_dir`, optional `route`) still validates.

## References

- [Idea Genie behavior](references/idea-genie.feature)
- [Idea challenge behavior](references/idea-challenge.feature)
- [Sealed perspectives](references/sealed-perspectives.md)
