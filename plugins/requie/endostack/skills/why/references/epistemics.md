# Epistemics for why

Code records behavior. It does not record the reason for that behavior. Reasons are scattered across commit messages, tickets, documents, chat and telemetry, and every one of those records is incomplete, written from one person's angle, and sometimes deleted. This page sets how the why skill grades its confidence in each historical claim and how each grade is worded, so that a guess never reaches the user dressed as a fact.

The synthesizer reads this page in full before drafting. Investigators follow its evidence rules. The [teach](../../teach/SKILL.md) and [recall](../../recall/SKILL.md) skills relay why's confidence wording unchanged.

## The five grades

Every claim gets exactly one grade. The grade decides which section the claim appears in and how it is worded.

### Direct

A person wrote the reason down: a PR description, a ticket, a comment in the code, a design doc, a chat message from the author. Working out the purpose from what the code does never counts as Direct.

Wording is plain, assured and present tense, with the citation next to the claim.

> The 30-second ceiling on export jobs exists to keep them under the load balancer's idle timeout (PR #4127: "exports were getting cut at 60s by the ALB, capping at 30 so we fail cleanly first").

### Supported

No record states the reason, but several independent indirect clues point the same way. Examples: a PR titled "speed up search", its ticket labeled `perf`, and three neighboring commits that all touch the same query path; a set of new tests that all feed malformed UTF-8; four PRs by the same author in one week that each reference the same outage ticket.

Wording is assured but shows that it was derived, and names each clue.

> The batching in `flushEvents` was added for throughput. Three signals agree: the PR title "batch event writes" (#2210), the `performance` label on ticket ENG-881, and the benchmark file added in the same commit (a1c9e07).

### Inferred

A reasonable reading of context that no record states. Examples: a commit merged the same afternoon as a production outage and touching the failing service suggests an emergency fix; a retry count of 5 that matches the value the team uses in four other clients suggests a house default rather than a tuned number.

Wording is hedged and lays out each premise and the step from premises to conclusion.

> The guard was probably an incident response. It merged at 16:40 on 3 March (PR #3301), the `checkout-api` error-rate monitor fired at 14:05 that day, and the guard rejects the exact payload shape in that monitor's sample events. No record links the two.

### Speculative

Plausible but thinly supported, with other explanations fitting just as well. Raise it, because the user may recognize it, but tag it as conjecture and normally place it under rival hypotheses.

> One possibility, with little evidence, is that the field was kept for a partner integration; the only hint is a 2022 chat message mentioning "the partner export" without naming the field.

### Unknown

Searched and not found. This is a valid result and must be reported precisely: which sources, which search terms, how many PRs were read, which repository searches ran, and that none produced a reason.

> No reason found for the `MAX_TAGS = 12` value. Searched: blame and history of `tags.ts` (9 commits, PRs #812, #1040, #1777), ticket tracker for "tag limit" and "MAX_TAGS", docs for "tags", chat for "12 tags" in the year around the commit. None states why 12.

## Wording rules

Causal and intentional language belongs only to Direct and Supported claims, and the citation must sit beside it. This covers "because", "the reason", "in order to", "designed to", "was added to", verbs claiming a fix worked, and phrases stating that a team decided something.

Hedging language belongs in the inference section and should be used freely there: appears, seems, probably, likely, points toward, fits with, plausibly, may have.

Do not use filler that assumes a point is self-evident or makes it look small ("obviously", "clearly", "of course", a dismissive "just"), and do not use first-person belief phrases ("I think", "I believe"). Replace them with wording centered on the evidence: "the PR states", "the ticket labels it", "no record mentions".

## Against rationalization

Do not build a tidy motive for untidy history. Code often accretes through hurried fixes and abandoned plans.

Do not assume the author chose well and then argue backwards to a reason.

Do not read consistency as intent. Five call sites doing the same thing may be one design or five copies.

Do not treat silence as proof. Nobody objecting in review does not show that nobody had the concern.

## Against agreeing by default

If the user's question contains a guess ("was this added for the SOC 2 audit?"), treat the guess as one hypothesis among several and test it like the others. Confirm it only with cited evidence. Otherwise say the evidence does not support it and give what the evidence does support.

## Conflicting sources

Show both sides, each cited. Do not keep only the one that makes a cleaner story. Say whether both can be true at once (a ticket gives the business driver and the PR gives the author's technical framing) or whether one is probably wrong. The user decides.

## Absent evidence

An honest "unknown" is useful. It tells the user the answer is not in the expected places and who to ask next (the author, the owning product manager, the team lead), or it lets them drop the question. Filling the gap with a confident guess does harm, because the user will act on it.

Each gap states the question, the sources tried, the terms used in each source, and the result.

## Synthesizer's final pass

For every claim in the findings and inference sections, check that:

1. It is cited, or it has been moved down to inference or rival hypotheses.
2. Its wording matches its grade.
3. It does not use the code as evidence of the code's own purpose.

The unknowns section must exist. If it is empty, treat that as a warning: either the record was unusually complete, or a gap is being hidden. Check which before sending.
