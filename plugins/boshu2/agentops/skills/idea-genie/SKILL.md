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
output_contract: idea-portfolio.v1 JSON validated by skills/idea-genie/scripts/validate-output.sh (elicit mode), or idea-challenge.v1 JSON validated by skills/idea-genie/scripts/validate-challenge.sh (duel mode)
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
   must beat; if nobody is working around the problem today, say so.

State the question, constraints, non-goals and sources first; hydrate only the
sources this question needs and cite them, with no merged context store.
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
    "evidence": ["<cited sources behind this candidate>"],
    "overlaps": ["<existing capability it extends or repeats>"],
    "scenario": {"given": "<state>", "when": "<event>", "then": "<observable result>"}
  }],
  "dropped": [{"idea": "<short name>", "reason": "<overlap, no evidence, or why it lost>"}],
  "termination": {"reason": "novelty-saturated", "novel_candidates_last_pass": 0}
}
```

`overlaps` may be empty; `dropped` is optional. When every idea overlaps or lacks support, set
`status` to `no-new-work`, leave `candidates` empty and set `termination.reason`
to `all-overlap-or-unsupported`. For a person, render the same fields as a
short list, one block per candidate. When a file is wanted, write
`.agents/scratch/ideas/<run-id>/idea-portfolio.json` and run
`scripts/validate-output.sh` on it before handing it to the caller or Plan.
Plan alone may incorporate a selected option into the existing bead or caller
intent.

## Duel mode

Produce independent challenges for a consequential choice. The result is
advisory evidence for Plan. It never decides whether a plan is ready and never
turns a later optional Premortem challenge into an approval gate.

**Door class.** Ask what undoing the choice after it lands would cost. A
one-way door needs a migration, breaks a published contract or caller, loses
data, or has an external effect that cannot be recalled. A cheap two-way door
is undone by a revert or a flag.

### Constraints

- Seal generation: no perspective sees another until all are complete, so
  later proposals cannot anchor on earlier ones.
- Preserve dissent, failed refutations and minority reasoning; Plan must see
  the alternatives synthesis would otherwise erase.
- Keep a two-way door light: no pane manager, messaging service, council or
  model-family rule.
- Emit no readiness, approval, quorum, retry, budget, helper, delivery, or
  tracker state: this strategy supplies evidence, not lifecycle authority.
  Consensus, transport availability or a self-score never becomes readiness.

### Workflow

1. Freeze the question, constraints, evidence paths and comparison rubric.
   Leave unknowns open. An assumption only one approach needs stays with that
   approach; in the shared constraints it would rule rivals out unseen.
2. For a one-way door, start at least two fresh contexts: separate subagents
   or sessions with no shared transcript, one prompt each carrying the frozen
   question and evidence paths and asking for the return in
   [sealed perspectives](references/sealed-perspectives.md#brief). Record each
   native context id as `context_id` and collect every perspective before
   revealing any. When the caller pins perspectives to model profiles, record
   each `model_identity` (see the `agent-native` model-dispatch recipe);
   disclose an unavailable profile and continue single-model.
3. Reveal the sealed perspectives and cross-review each by evidence,
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
   Keep disagreements, failed refutations and minority reasoning explicit.
5. Write `idea-challenge.v1`, validate it, and pass it to Plan as one optional
   input alongside research and operator intent.

For a cheap two-way door, emit the lightweight packet directly after one fresh
challenge. Do not manufacture panel ceremony.

### Output Specification

- **Artifact directory:** `.agents/scratch/ideas/<run-id>/`
- **Filename:** `idea-challenge.json`
- **Format:** `idea-challenge.v1` JSON in one of the two shapes below; it
  carries no readiness field or decision
- **Validation command:** `scripts/validate-challenge.sh <idea-challenge.json>`
- **Downstream handoff:** `handoff.owner` is exactly `plan`; Plan may accept,
  reject, or combine the advisory evidence

A one-way packet:

```json
{
  "schema_version": "idea-challenge.v1",
  "door_class": "one-way",
  "sealed_generation": true,
  "perspectives": [
    {"id": "P1", "context_id": "<native context id>", "proposal": "<mechanism, evidence, tradeoff>"},
    {"id": "P2", "context_id": "<a different context id>", "proposal": "<mechanism, evidence, tradeoff>"}
  ],
  "cross_reviews": [{
    "reviewer": "P1",
    "subject": "P2",
    "dimensions": {"evidence": "<finding>", "reversibility": "<finding>", "system_fit": "<finding>", "failure_modes": "<finding>", "cost": "<finding>"}
  }],
  "disagreements": ["<where the perspectives still differ>"],
  "refutations": [{"claim": "<what was attacked>", "attempt": "<the concrete test>", "result": "<what the attempt showed>"}],
  "handoff": {"owner": "plan", "artifact_dir": ".agents/scratch/ideas/<run-id>/"}
}
```

It needs at least two perspectives, each with its own `id` and a distinct
`context_id`; a perspective may also carry `model_identity` and its proposal.
`cross_reviews`, `disagreements` and `refutations` each need at least one
entry. Each cross-review names two different perspective ids and at least one
dimension, and every dimension it lists holds a non-empty text finding; every
disagreement is a non-empty string, and every refutation fills `claim`,
`attempt` and `result`.
Leave `requires_ntm` out of a one-way packet.

A two-way packet keeps `sealed_generation` false and all four lists empty,
adds `"requires_ntm": false` to record that no pane manager was needed, and
names its route:

```json
{
  "schema_version": "idea-challenge.v1",
  "door_class": "two-way",
  "sealed_generation": false,
  "perspectives": [],
  "cross_reviews": [],
  "disagreements": [],
  "refutations": [],
  "requires_ntm": false,
  "handoff": {"owner": "plan", "artifact_dir": ".agents/scratch/ideas/<run-id>/", "route": "single-fresh-context"}
}
```

The two-way packet records the route, not the challenge, so pass the fresh
challenge's findings to Plan beside it. The validator rejects any other
top-level field, and `handoff` takes only `owner`, `artifact_dir` and `route`.

## References

- [Idea Genie behavior](references/idea-genie.feature)
- [Idea challenge behavior](references/idea-challenge.feature)
- [Sealed perspectives](references/sealed-perspectives.md)
