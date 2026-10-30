---
name: create-verifier
description: Use when a rule needs judgment a deterministic test cannot encode, such as tone or fit to the owner's taste. Writes a verification agent in verifiers/, registers it in verifiers/INDEX.md, and records the way to verify.
---

# Create a verifier

## Goal

Every rule that no test can check still gets checked on every verification round, by a fresh-context agent that sees only the artifact and returns a binary verdict with a location. Tone, fit to the owner's taste, whether a scene reads as intended, whether a summary is faithful: these are judgments, and a judgment made by the same context that produced the artifact is not a check. A verifier is narrow on purpose, one rule family per file, so that a change to one rule does not disturb the others and a failing verdict names one thing. It never sees the conversation, so it cannot be argued into a pass. A verifier is the second choice after a test, because it costs a model call per round and can disagree with itself, and it is retired the moment a mechanical proxy for the rule appears. Its verdict is PASS or FAIL, never a score, because a score invites the generating agent to call seven out of ten good enough. The measure of this skill is that the owner's judgment calls are enforced as reliably as their mechanical rules.

## Objective

Confirm that no deterministic check covers the property, so a verifier is not written where a test would do. Copy the template and write a verifier prompt for one rule family or one kind of artifact, naming the rule ids it enforces, the examples it may read, what counts as a failure and what does not. Register its trigger in the verifier index so the verify-generation skill runs it on matching artifacts. Add a verification entry only when the verifier checks a kind of claim no existing entry describes. Report the file path so the orchestrator can set `verified-by` on the entry. The verifier is done when a fresh agent given only its file and an artifact can reach a defensible verdict without asking anything.

## Tasks

1. Confirm with `skills/create-test/SKILL.md` that no deterministic check covers the property, by walking the catalog once more and recording why each item fails to apply. A property that splits into a mechanical part and a judgment part gets a test for the first and a verifier for the second only.
2. Copy `verifiers/_template.md` to `verifiers/<slug>.md`, named for the rule family, and fill every section. Name the rule ids it enforces, restate each rule in one line so the verifier does not need to open memory, name the approved examples under `memory/examples/` it may read, and describe what counts as a failure and what does not in observable terms.
3. Add a row to `verifiers/INDEX.md`: name, file, trigger as a glob or an artifact kind, the rule ids and `active`. The trigger decides when the verifier runs, so make it exactly as wide as the rule: a rule about captions triggers on scene files, not on everything.
4. Add a `V` entry to `memory/verification.md` only when the verifier checks a kind of claim that no existing `V` entry names, in the three-line format from `memory/MAP.md`. The index is the registry of verifiers; the verification file is the catalog of ways to verify kinds of claims.
5. Report the file path, the trigger and the rule ids so the orchestrator can set `verified-by` on the entry. Name the mechanical part that went to a test instead, if any. The report is the only channel back; what is not in it does not get linked.

## Instructions

- **A verifier sees only what its file lists.** It gets the artifact under review, the rule texts restated in the file, and the approved examples the file names, and nothing else. It never sees the generating conversation, the plan or the author's explanation, because those are how a wrong artifact gets talked into a pass. If the verifier needs more context to judge, write the context into the file as a rule restatement or an example, not as an instruction to go and read the conversation.
- **The verdict is binary and located.** PASS or FAIL, never a score, a grade or a "mostly". A FAIL quotes the location and names the rule id, so the generating agent can fix the exact place without re-reading the whole artifact. A property the verifier cannot check from the artifact is a FAIL with the reason, never a pass, because an unverifiable pass is the same as no verifier.
- **Keep the prompt under 120 lines with the fixed sections.** The sections are goal, objective, tasks, instructions, checklist, output and runtime behavior, in that order. The verifier is loaded on every round for every matching artifact, so every line costs tokens three to five times per step; write what a fresh agent needs and no more. Put the rule restatements and the failure criteria in the instructions, where the verifier looks for them.
- **One verifier per rule family.** A verifier for caption casing and length and another for narration pace can be changed, retired or triggered independently; one verifier for everything about films cannot. A family is the set of rules that share a trigger and a kind of judgment. When a new rule fits an existing family, extend that verifier's rule list and its index row rather than creating a second file.
- **Retire a verifier when a mechanical proxy appears.** When the feedback-test subagent later finds a deterministic check for the property, it writes the test, and the verifier's row in the index gets `status: retired` with the reason and the test path. The file stays, so history reads. Tests are cheaper and cannot drift, so the proxy wins even when the verifier was good.
- **Write the failure criteria as observations, not as taste.** "The caption uses more than three exclamation marks" can be judged; "the caption is too excited" cannot, until the file says what excited looks like. Give the verifier the owner's own examples of a pass and a fail where they exist. The boundary line exists so the verifier does not over-apply a rule to artifacts the owner never meant.

## Checklist

- [ ] **No deterministic check covers the property.** The create-test catalog was walked and the report records why each item does not apply. The mechanical part of the property, if any, has a test, and the verifier covers only the judgment that remains.
- [ ] **Every section of the template is filled and the rule ids are named.** The rules are restated in one line each inside the file, the examples are named by path, and the failure and non-failure criteria are observable. No placeholder from the template remains.
- [ ] **The trigger in `verifiers/INDEX.md` matches the artifacts the rule applies to.** It is as wide as the rule and no wider, and the row names the file, the rule ids and `active`. A verifier missing from the index never runs.
- [ ] **`memory/verification.md` has a `V` entry if the kind of claim was new.** The entry names the claim type, how to verify it and the verifier path, in the three-line format. An existing claim type was not duplicated.
- [ ] **The verifier path was reported for `verified-by`.** The orchestrator links the entry to the verifier only from the report, so a missing path means an entry with no named check. The path is copied from the file as written, and the trigger and rule ids are reported with it so the orchestrator can confirm the index row matches.

## Output

The verifier path, its trigger, the rule ids it enforces, the `V` entry id if one was added, and the mechanical part of the property that went to a test instead, if any.

## Runtime behavior

- Writes only to `verifiers/` and `memory/verification.md`. Setting `verified-by` on the entry is the orchestrator's job.
- Verifiers run only through `skills/verify-generation/SKILL.md`, in fresh context, never on their own and never from inside the generating context.
- Runs inside the feedback-test subagent during feedback handling, after the test search has come up short for a property, or on the owner's direct request.
