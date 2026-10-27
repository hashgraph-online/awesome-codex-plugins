---
name: owner-intent-audit
description: "Check agent-produced plans, tests, or code against the owner's actual intent. Find missing meaning, unrequested work, stale truth, unreachable decisions, unsupported completion claims, and implementation debt. Use before approval or merge."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# Owner Intent Audit

The question this review answers is not "is the artifact good" but **"is this what the owner
meant, and what did the agent leave behind while making it?"** (The owner is whoever owns the
work and decides what it should be; often that is the user.) An agent can produce a PRD (product
requirements document), a plan, or a diff that is locally excellent and still specify a different product, carry work
nobody asked for, or hide the debts agents characteristically create. Reviewing the artifact
for its own defects — bugs, security holes, silent death — is peer-review's job, not this one;
the two are run separately and neither substitutes for the other.

- **Plan mode:** PRDs, designs, specs, task lists, refactor plans, and test plans.
- **Code mode:** diffs, files, tests, or subsystems substantially written by agents.

Start with the ordinary user and system flow. Realistic common-path failure outranks exotic
edge cases.

## What must be established

### 0. Did the artifact preserve the product meaning?

This is not “did every source bullet appear?” A locally plausible artifact can retain the
same nouns while specifying a different product.

Determine:

- who needs the outcome and who decides;
- what result they actually need;
- when the behavior applies and when it must not;
- which exceptions, prohibitions, priorities, and trade-offs matter;
- how separate answers constrain or explain each other;
- what observable result distinguishes success from an easier proxy.

Find that meaning in the owner's raw request, the complete question-and-answer record, and the
settled decisions. If the project keeps no such record, say so and use `incomplete-evidence`.
Find loss of meaning in the target's requirements, ordinary flow, boundaries,
design choices, and acceptance criteria. In code mode, also look through the governing
contract (the spec, interface, or acceptance text the code is supposed to satisfy), callers, state changes, and user-visible result.

Important shapes include a condition becoming unconditional, an actor changing, an example
becoming the whole boundary, a prohibition disappearing, related answers becoming isolated
facts, or a familiar implementation replacing the requested outcome.

Keyword overlap and row-count traceability are not proof. Return real ambiguity to the owner;
do not invent meaning.

### 1. What did the agent over-build?

Run the `less-is-more` skill in cut mode on the diff (code mode). In plan mode, apply its cut
list to the plan as a checklist: what is proposed that the owner did not ask for, and what could
be deleted without losing the requested outcome. Every item it reports is a finding here. In plan mode, also ask what wording would invite
a literal agent to build it. Work that is necessary but belongs in a runbook, an orchestration
step, or a test harness rather than the product contract is misplaced process work: report where
it should move, without dropping its constraint.

### 2. Does the artifact graph resolve to one identity?

The plan or spec and everything tied to it must name the same current artifact by path, hash, and
status, and every referenced file must exist. For example, where the project has them: a PRD, its
acceptance file, its test commands, its evidence, and its status header. A stale identity or an
unreachable verifier is a finding. Validate an absence check with a known positive control.

### 3. What is current truth?

Separate **current contract** (what must be delivered), **current state** (what ran, passed, or
remains), and **historical narrative** (why it changed). History may explain current truth; it
cannot override it. A load-bearing claim that no longer matches reality — in a PRD, plan,
comment, default, or completed task — is a finding, because it misleads the next agent.

### 4. Is the decision model executable?

Check decision tables, state machines, ordered guards, schemas, fixtures, and tests. Every
claimed branch must be reachable, branches claimed as exclusive must not overlap, and duplicate
or shadowed branches must not masquerade as distinct outcomes.

### 5. Did claimed work run and reach its consumer?

“Ran,” “wired,” “enabled,” “deployed,” or “passed” require effect proof, not a flag, log line,
or clean exit. Trace the ordinary entrypoint to an observable result; run the
`agentic-walkthrough` skill when it is installed.

## Evidence and judgment boundaries

Owner-intent preservation needs the raw request, complete Q&A, and settled decisions. Missing,
partial, stale, or non-blind intent evidence means `incomplete-evidence`, not `clean`; it limits
only the semantic verdict, and every other check still runs and reports. Intent evidence is
non-blind when the reviewer had already read the artifact under review before reconstructing the
owner's meaning, so the comparison is not independent; say so.

A behavior finding needs a realistic trigger and a material consequence; test it against
guards and reachability before keeping it. An over-build finding from `less-is-more` needs no
trigger: the extra code is the consequence. Do not report style debt.

## Output

By default this audit is one judgment pass: do not rerun it, or run another model review, to
confirm the edits that follow it; a project may choose otherwise. Never write a `clean` verdict
before the audit has run. Keep the actual report immutable, record how each finding was handled,
fix the material blockers in the work under review, prove the fixes deterministically, and
continue without a model confirmation review (unless the project requires one).

```markdown
## Owner Intent Audit — <target>
Mode: plan | code
Verdict: clean | findings | incomplete-evidence
### Semantic preservation
Owner-intent status: preserved | findings | not-assessable | non-blind
Contract-conformance status: preserved | findings | not-assessable
Evidence: <what supports the judgment and what is missing>
### Over-built
<the less-is-more cut output, plus any misplaced process work, or "Lean already.">
### Findings
[critical|high|medium] <finding> — <location>
Scenario: <realistic trigger and concrete consequence; omit for over-build>
Correction: <smallest outcome that removes the risk>
### Guardrails
<plan mode only; concise outcome constraints for the implementing agent>
```

`clean` requires every check, adequate intent evidence, and no unresolved material blocker in the
work under review—not zero raw findings. Resolved findings and non-blocking debt never force another review.
