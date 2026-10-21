# Skill Authoring Doctrine

Use this reference when a sentence, description or reference split creates a
concrete authoring uncertainty. The [source template](skill-template.md) and
[audit checks](audit-checks.md) own structural requirements. Layout is a choice;
applicability, necessary inputs, authority/effects, result, completion and failure
must be clear in whichever form fits the operation.

Idea provenance: clean-room consideration of authoring ideas at
<https://github.com/mattpocock/skills> (MIT), reconciled with this repository's
accepted contract. No upstream prose, names, prompts, scripts or examples are
copied. Wording theories below are hypotheses, not established improvements.

## Make the instruction change a decision

Prefer an observable action over an intensifier: when a selected operation
requires a boundary reference, read that reference before the dependent action.
Do not require every reference on every invocation. If necessary material is
missing, name it and stop the dependent action; unrelated authorized work can
continue. Re-read when contents changed, context was lost or the next decision
requires it, rather than once per invented phase.

A phrase's benefit depends on the task, model and host. Preserve a necessary
obligation even when a detector dislikes its wording. A comparison with the
unchanged task and a plausible wrong outcome is evidence; author preference or
word count is not.

## State authority and a usable failure path

Use direct positive instructions where they are clearer. Keep explicit
prohibitions when they define an authority, disclosure or mutation boundary, and
name a safe alternative or incomplete response when useful. The theory that
negation primes forbidden behavior needs task-specific evidence; it is not a
reason to remove a necessary ban or to require paired wording everywhere.

Completion must cover the promised result. Add intermediate checkpoints only
when final completion cannot protect a consequential action or handoff. A
reference supplying judgment criteria need not invent workflow phases, and a
concise adapter can express success and failure in one paragraph.

## Use concrete language before compressed cues

Familiar domain terms can save repetition when their meaning is shared. A
leading word's effect on behavior remains a hypothesis; words are not free
context and a vague cue must not replace an input, stop condition or authority
boundary. Define unfamiliar terms only when the operation needs them. Test
actual outcomes before claiming a wording change improves execution.

## Separate description, invocation policy and content

A description says what the skill does and when it applies. For implicit
selection, test distinctive task states, neighboring jobs and false activation;
for explicit selection, describe scope without synonym padding. Neither a tier
nor `user-invocable` proves what a particular host discovers or loads.

Use the existing source/host invocation fields, including Codex
`agents/openai.yaml` policy where needed; see [Codex parity](codex-parity.md).
Explicit-only policy does not prove zero catalog context cost or prohibit
composition. Verify loaded bytes and policy on each claimed host. Canonical
source and exported portable packages have separate profiles.

Measure actual descriptions, bodies, references, repeated reads and tool output
on the task path. A shorter root can cost more overall. Split only when a
conditional operation or independently useful route makes navigation clearer;
optional folders and assets earn no quality credit.

## Interpret audit advice as evidence to inspect

The default v2 audit reports located authoring suspicions separately from
conformance and unmeasured behavioral evidence. Historical `noop-phrase`,
`negation-without-positive` and `step-missing-done-condition` detectors remain
available through `audit.sh --legacy` for compatibility. Their tokens, headings
and phrase counts neither prove quality nor mandate prose repairs. Keep legacy
consumer compatibility separate from the decision to retain or revise a skill.

## Change existing text at its owning layer

Most skill edits add a line after a miss. Before adding, check whether the
miss is a missing condition or a missing case.

- **State the condition, not another case.** When a rule is about to gain
  "and also when X", name what X stands for and state that instead. A rule
  that lists its cases will need another case next month.
- **Put a mechanism where it is owned.** Commands, exit codes and state
  changes belong to the skill or tool that owns them. A skill that delegates
  states the outcome it needs, the safe failure direction and the facts the
  callee cannot derive, and links the owner.
- **Check provenance before cutting.** Look for a test that asserts the line,
  a commit or incident that added it, or a document that records why. If one
  exists, the line protects something: keep it unless that consumer is gone,
  and say what it protects. If none exists, apply the admission test below,
  and say which cuts rest only on absence of evidence.
- **Name what decides after a cut.** When you remove a "must", say what now
  decides whether that step happens. If the answer is "the model, at its
  discretion" and the step is required, the line stays.
- **Admission test.** A line earns its place when it states a constraint a
  run could visibly break, counters a tendency agents have shown, or supplies
  a fact the agent cannot derive from the repository. Restated capability,
  effort language and rationale after a self-sufficient directive do not.
- **The description is the routing pointer.** Most hosts keep it in context
  with the catalog, so it is read far more often than the body (verify per host,
  as above). Its first sentence names what this skill produces that a sibling
  would not; then the work states that should trigger it; then the sibling to
  use for the neighboring job, when the same words could fire both.
- **Shrink by moving, not compressing.** When a body must get smaller, move a
  coherent conditional block to a reference named where it is needed, or
  delete true duplication. Fused clauses and dropped articles save bytes and
  cost comprehension.
