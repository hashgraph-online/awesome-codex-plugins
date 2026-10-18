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
   the product already does. A request an existing capability already covers
   is not new: record it under `overlaps` of the candidate it sharpens, or
   leave it out.
4. **One Given/When/Then per candidate**, a normal or edge case with an
   observable result.
5. **Do not rank, pick, schedule or start work.** The caller or Plan selects.
6. **Stop at saturation.** Merge equivalents, and run another pass only while
   it adds a materially new evidenced candidate. Zero candidates is valid.

State the question, constraints, non-goals and sources first; hydrate only the
sources this question needs and cite them, with no merged context store.
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
  "termination": {"reason": "novelty-saturated", "novel_candidates_last_pass": 0}
}
```

`overlaps` may be empty. When every idea overlaps or lacks support, set
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
2. For a one-way door, start at least two fresh contexts: separate subagents
   or sessions with no shared transcript, one prompt each carrying the frozen
   question and evidence paths. Record each native context id as `context_id`
   and collect every perspective before revealing any. When the caller pins
   perspectives to model profiles, record each `model_identity` (see the
   `agent-native` model-dispatch recipe); disclose an unavailable profile and
   continue single-model.
3. Reveal the sealed perspectives and cross-review each by evidence,
   reversibility, system fit, failure modes and cost.
4. Attempt concrete refutations. Keep disagreements, failed refutations and
   minority reasoning explicit.
5. Write `idea-challenge.v1`, validate it, and pass it to Plan as one optional
   input alongside research and operator intent.

For a cheap two-way door, emit the lightweight packet directly after one fresh
challenge. Do not manufacture panel ceremony.

### Output Specification

- **Artifact directory:** `.agents/scratch/ideas/<run-id>/`
- **Filename:** `idea-challenge.json`
- **Format:** `idea-challenge.v1` JSON with route-specific fields enforced by
  the validator; it carries no readiness field or decision
- **Validation command:** `scripts/validate-challenge.sh <idea-challenge.json>`
- **Downstream handoff:** `handoff.owner` is exactly `plan`; Plan may accept,
  reject, or combine the advisory evidence

## References

- [Idea Genie behavior](references/idea-genie.feature)
- [Idea challenge behavior](references/idea-challenge.feature)
