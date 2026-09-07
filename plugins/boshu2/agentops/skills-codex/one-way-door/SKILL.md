---
name: one-way-door
description: 'Classify a pending decision as reversible or Triggers: "is this a one-way door", "can we undo this", "should I just decide this", "the models disagree with me", before any auto-decided approval gate.'
---
# $one-way-door

Classify one pending decision as **two-way** (cheap to undo, may be auto-decided)
or **one-way** (expensive or impossible to undo, always surfaced to the caller).
Return the classification and stop. This skill decides *who decides*. It never
decides the underlying question and it never performs the action.

**Insight:** an agent's confidence is uncorrelated with a decision's
reversibility, so confidence is the wrong gate. Reversibility is a property of
the decision itself, is knowable before acting, and can be declared in advance
instead of inferred from how the question happened to be worded.

**The failure mode this exists to prevent:** an agent auto-approves an
irreversible step because the surrounding batch of decisions was routine and the
step read as one more item in the list. Dropped table, force-push over a
colleague's work, rotated credential, published post. The batch is why it
happens: nineteen two-way decisions train the reflex that answers the twentieth.

`dcg` guards destructive **commands** at the shell boundary. This guards
destructive **decisions** at the judgment boundary, before any command exists.

## Modes

| Trigger phrases | Mode | Entry point |
|---|---|---|
| "is this a one-way door", "can we undo this", "classify this decision" | classify | the four layers below |
| "should I just decide this", "auto-decide the rest" | gate a batch | classify each, act only on `two-way` |
| "the models disagree with me", "both reviewers say I'm wrong" | user challenge | the packet below |

## Inputs

Required: a one-line summary of the pending decision, and the effect it would
have if answered wrong.

Optional: a declared decision id from `references/decision-registry.md`, and the
skill or lane raising it.

**Non-goals.** This skill does not answer the decision, rank options, execute
anything, or record the caller's answer. It does not gate shell commands — that
is `dcg`. It does not model caller preferences or build a profile of how the
caller usually answers; a preference that suppresses questions is exactly the
mechanism that must never reach a one-way door.

## Procedure

Apply the four layers in order and stop at the first that fires.

1. **Declared registry (primary).** Look the decision id up in
   `references/decision-registry.md`. If present, use its declared `door`. A
   declaration in a checked-in file outranks anything inferred from prose,
   because prose gets reworded and a reworded question must not silently change
   class.
2. **Effect class.** If the decision authorizes an effect the skill catalog
   declares as mutating outside the working tree — publishing, credential use,
   external mutation, remote deletion, release — it is one-way regardless of
   wording.
3. **Pattern fallback.** For decisions with no registry entry, match the summary
   against `references/patterns.md`. This layer is deliberately over-eager: a
   false positive costs the caller one extra question; a false negative costs
   them the thing that cannot be undone.
4. **Default two-way.** No evidence of irreversibility in any layer means the
   decision may be auto-decided.

Then report: `door`, the layer that fired, and — for one-way — the specific
undo cost that makes it one-way.

Layers 1 and 3 read checked-in files, so the lookup is reproducible by anyone
reviewing the classification:

```bash
# Layer 1 — is this decision already declared?
grep -niF "deploy key" skills/one-way-door/references/decision-registry.md

# Layer 3 — which pattern would fire on this wording?
grep -niE "revoke|rotate|force-push|publish|delete" skills/one-way-door/references/patterns.md
```

### The user challenge packet

One decision class is never auto-decided at any confidence: **the reviewers agree
the caller's stated direction is wrong.** Independent agreement is a strong
signal. It is not authority — the caller holds context the reviewers do not, and
a synthesis that quietly adopts the reviewers' position deletes that context
without telling anyone.

When it fires, emit exactly these five fields and stop:

- **What the caller stated:** their original direction, in their words.
- **What the reviewers recommend:** the change, and how many independently reached it.
- **Why:** the reasoning, at its strongest.
- **What we might be missing:** the context the reviewers provably did not have.
- **If we are wrong, the cost is:** what breaks if the caller's direction was right.

The caller's direction is the default and stays the default. The reviewers carry
the burden of argument. The one adjustment: if the reviewers classify the change
as a security or feasibility defect rather than a preference, say so in the
packet — the caller still decides, but they decide knowing which kind of
disagreement this is.

## Anti-patterns

| Anti-pattern | Corrective |
|---|---|
| Reading the summary's wording as the primary signal | Registry first; wording is layer 3, and only for undeclared decisions |
| "I'm confident, so I'll decide it" | Confidence does not make a decision reversible; classify, then route |
| Auto-deciding the whole batch because the first nineteen were routine | Classify every item independently; batches are the failure mode, not the exception |
| Suppressing a repeated question because the caller answered it the same way twice | Preferences apply to two-way only; a one-way door has no suppression path |
| Synthesizing the reviewers' position into the plan when they agree against the caller | Emit the user challenge packet; never fold it into a recommendation |

## Output

One classification per decision:

```json
{
  "decision": "rotate the deploy key before shipping",
  "door": "one-way",
  "layer": "pattern",
  "undo_cost": "revoked key cannot be un-revoked; every consumer must be re-issued",
  "auto_decidable": false
}
```

**Done when:** every decision in the batch carries a `door` and a `layer`, and no
decision with `door: one-way` was answered by the agent. A batch is correctly
gated when every `one-way` line went back to the caller unanswered.

## It's working if

Observable in the trace, without reading the prose — and the rubric a fresh
independent judge scores this skill against:

- Every item in a batch carries its own `door` and `layer`; none inherits the
  class of the item before it.
- No item classified `one-way` was answered by the agent — each one went back to
  the caller unanswered.
- Every `one-way` line names a concrete undo cost, not a category label.
- The registry lookup appears in the trace before the pattern match, not after.

## Checks

- Every one-way classification names a concrete undo cost, not a category label.
- No decision was both classified one-way and auto-decided.
- The registry was consulted before the pattern layer, not after.
- The user challenge packet, when emitted, contains all five fields including
  "what we might be missing" — the field that is easiest to drop and the one that
  makes the packet honest.

## Provenance

- Mechanism analysis and the layering rationale (§2.2, §2.3): not on main; read it at `git show 9872483bd:docs/research/gstack-teardown-2026-08-08.md` (branch `recover/gstack-clean-room`).
- Shell-boundary sibling: [`skills/dcg/SKILL.md`](../dcg/SKILL.md).
- Caller-sovereignty floor: `CLAUDE.md` → Authority and trust; the operating
  contract's rule that repository access does not authorize destructive
  operations, publishing, credential use, or external mutation.

## Failure behavior

If the decision summary is missing or the registry is unreadable, classify as
one-way and report why. Failing toward asking is the only safe direction: an
unclassifiable decision is an unknown, and an unknown that gets auto-decided is
indistinguishable from an unguarded one.
