# Debate and majority selection

Loaded by [Council](../SKILL.md) when the caller selects a bounded debate or a
voting rule. Independent comparison of sealed initial views needs neither.

## Rounds

Every round uses fresh contexts with new observed IDs, distinct from the author,
synthesizer, and prior rounds. Initial participants must not see peer answers or
the author's preferred conclusion. Seal all initial responses before sharing
any. Reused or colliding IDs stop reliance on that round: repair the isolation
within remaining bounds or disclose it as non-independent.

For debate, synthesize a candidate from sealed proposals and later objections;
the synthesizer does not vote. Share the same prior responses, evidence, and
exact candidate with every participant in the next round. Require substantive
challenges to competing claims, evidence for changed positions, and remaining
objections. Do not share partial current-round responses with peers. Fresh
contexts that receive earlier answers are **peer-informed deliberation**, not
new independent confirmations; label them separately from the initial views.

Before debate, fix the maximum rounds and total deadline from the caller/native
bounds; clarify missing bounds before launching. Initial independent proposals
are round zero, outside the debate-round count. New contexts, revisions, and
retries never renew the deadline or round allowance. Stop at the agreed
condition or exhausted bound and report unresolved disagreement honestly.

## Majority selection

If the caller requests majority selection, record the fixed participant roster,
threshold, and whether distinct models or judges are counted. A majority means
more than half of that fixed denominator; count each selected model once for a
model majority. Each participant returns support, oppose, or abstain for the
**same exact candidate digest**; only unconditional support counts. Required
amendments mean oppose, not support for a private revision. A changed candidate
requires a new digest and fresh round; never carry old votes forward. Do not
shrink the denominator for missing responses, errors, or abstentions, and never
replace a required model with an available one. All caller-required legs must
return eligible views before claiming the requested council is complete. Stop
once a completed round meets the selected threshold; otherwise return no agreed
recommendation at the cap.

Report the tally as **deliberative agreement** and retain minority objections,
even when unanimous. A majority can select an advisory design recommendation;
it cannot establish factual truth, measured benefit, validation acceptance, or
resolve a failed required validation leg. Without a caller-selected voting
rule, synthesize the evidence without inventing a vote.

Record round, mode and candidate digest in each `judgment`, and bounds, roster,
threshold, tally and stop reason in the synthesis prose; keep initial and
deliberative support distinguishable. No new schema is needed.
