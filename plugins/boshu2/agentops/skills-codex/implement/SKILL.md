---
name: implement
description: 'Implement authorized work and repair understood defects; return derived subject identity and check facts. Triggers: "implement", "implement this bead", "run the experiment". Full plan-to-validation requests route to rpi.'
---
# Implement

Implement the authorized outcome, including ordinary direct repairs. Use the
resolved bead or caller intent; do not turn every failed check into a new phase.
Implement owns subject edits and factual evidence; the runtime derives identity
and receipts. A clear trivial change needs no Plan, Recall or Learn worksheet.

## Prompt

```text
Implement bead ag-1234 from its text: acceptance "ao gate check lists
skill.probe-coverage", scope cli/internal/gates/** plus regen outputs, first
check `cd cli && go test ./internal/gates/...`. RED first, smallest change,
return the manifest digest and check receipts, stop.
```

## It's working if

- After source activation and startup association, the first behavior check
  is the acceptance check; its output shows the expected failure (or an honest
  green structural baseline for documentation, relocation, or refactor work).
- Every path in `git diff --stat` falls inside the declared scope; an outside
  consumer is reported as `file:line`, not absorbed.
- The response carries the `subject-manifest.v1` digest, author context ID,
  and verbatim check output; no `git commit` or `git push` appears.

## Workflow

1. Read the intent, acceptance, and scope from their existing source; before
   the first write, read `boundaries.md` in the rpi skill's `references`
   directory for what Implement does not own. Before execution can fail, the
   caller passes source-store/project/work identity and permitted intent
   locators at dispatch/start. At startup, return observed native runtime,
   session/context identity (or explicit unknowns) through the caller-owned
   runtime channel for native comments/metadata recording; do not defer this
   association until handoff. Follow the fact distinctions in
   [session associations](../cass/references/SESSION_FORMATS.md#work-to-session-associations).
   Parent and resume links need observed provenance; controller dispatch alone
   does not establish native parentage. If startup observation or recording
   fails, preserve that failure and the pre-execution reference with the caller,
   leaving unobserved IDs unknown. Startup association applies when the caller selected episode tracking; a
   trivial edit does not need a new tracking worksheet. Use the caller-owned
   runtime channel for handoff facts, without a second work account.
2. Run the declared first acceptance check before changing behavior. RED-first
   applies when acceptance is behavioral: preserve evidence that the check
   fails for the expected missing behavior. Relocations, doc merges, and pure
   refactors record an honest green pre-change baseline instead.
3. Make the smallest in-scope change that satisfies the active behavior. Repair
   ordinary known defects directly. A failed test with an understood cause needs
   a fix and another discriminating check, not a helper or fresh planning lane.
   If evidence disproves an assumption, revise the approach within unchanged
   acceptance and scope; use Plan only to resolve consequential uncertainty.
4. Run the targeted acceptance checks and capture factual results.
5. Refactor only while those checks stay green. Refactoring does not change the
   acceptance test.
6. Have the runtime derive actual changed paths and `subject-manifest.v1` from
   the before/after subject.
7. When changed files affect bound acceptance evidence, run `ao provenance evidence-orphans --root <repo-root>` with one
   `--changed <path>` per changed path the runtime derived, and put its JSON
   output in the check receipts the validator reads, so orphaned evidence
   arrives as a receipt rather than as a surprise at verify time. Run it again after every repair round, over the
   paths as they stand, because a repair can orphan evidence the first pass did
   not. Read the output as written and never hand-list the orphans instead.
8. Return the manifest digest, author context ID, and exact check receipts in the
   response or runtime channel. Stop.

Specialists (standards, domain, test, refactor, security) advise only. During
edits, run the smallest deterministic checks that can falsify the change,
reuse exact-input receipts whose subject and tool identity still match, and
run the full suite at the integration boundary unless the intent makes it the
first check.

## Scope conflict rule

On discovering a live consumer of the change outside the declared write scope
(a test asserting the old path, a generated twin, a gate reading the moved
file), stop and report the exact file and line to the caller for a scope amendment; continue independent authorized work. A different
acceptance contract needs caller authority. Generated outputs already included
as a scope class need no new permission.

Before declaring GREEN, self-audit the diff for mocks, placeholders, TODO
stubs, hardcoded fixture values, weakened assertions, regenerated goldens,
widened tolerances, suppression directives, or specification edits standing
in for real behavior. A changed test, gate, fixture, golden, or acceptance
source must be required by the original intent, with green coming from the
implemented behavior; a check that passes against a substitute or weakened
oracle is not evidence: finish the behavior or report it as not built.

## Boundary

Do not issue semantic PASS or infer Git, tracker or delivery permission from
this skill. Follow the caller's existing authority and repository policy.
An implement-only handoff returns facts to its caller; a full outcome request
uses RPI through fresh final validation. Known defects stay implementation work.
On a genuine causal stall, use RPI's at-most-one bounded helper rule, never a
helper chain. Reserve finishing capacity and respect actual caller/native bounds;
a retry count alone is not a spent time or quota budget.
