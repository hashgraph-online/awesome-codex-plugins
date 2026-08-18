# Phase 7.1: Issue Premise Verification (#730/H3)

> Sub-file of the session-start skill. Referenced from SKILL.md Phase 7.1.

## Claim Extraction

For each candidate issue (title + body), scan for state-claim keywords:
`fehlt|missing`, `dormant|stale|abandoned|tot`, `existiert nicht|does not exist|never shipped`,
`is broken|kaputt`, `N of M`, `all|every|none|100%`, `blockiert|blocked by`.
Each match is one core claim to verify. Cap: 3 claims per issue — pick the
load-bearing ones the issue's ask depends on (a claim whose falsity would
change the issue's scope or kill it).

## Verification (one grep/Read per claim — PSA-006 discipline)

For each claim, run exactly ONE Grep or Read against the actual codebase (or
`git log` for activity claims). Quote pattern + scope + result inline — same
transcript discipline as `.claude/rules/parallel-sessions.md` § PSA-006.
Budget: this phase is a spot-check, not a deep audit. If one grep cannot
ground the claim, mark UNVERIFIED and move on — do not rabbit-hole.

## Verdicts

| Verdict | Meaning | Downstream effect |
|---|---|---|
| SHIPPED | Claimed-missing feature is found implemented | Issue (or item) is stale — surface in Phase 8 as "needs re-scoping / close candidate" |
| GAP | Claim confirmed — feature genuinely absent | Issue premise holds — safe to plan |
| FALSCH-PRÄMISSE | State claim objectively contradicted by evidence | Surface prominently in Phase 8 — user decides re-scope or drop |
| UNVERIFIED | No groundable claim, or grep inconclusive | Note only — no flag |

## Emission Block

### Premise Verification Result (Phase 7.1)
- #<N>: "<claim>" → <tool>: `<pattern>` in <scope> → <VERDICT> (<1-line evidence>)
- #<M>: ...

FALSCH-PRÄMISSE / SHIPPED entries MUST surface explicitly in Phase 8's
alignment AUQ as a "premise flag" on the affected option — never silently
dropped; the user decides. session-plan Step 1 treats the verdicts as binding
input (re-scope or drop tasks whose verdict is FALSCH-PRÄMISSE/SHIPPED before
decomposing) without re-running the greps.

## Anti-Patterns

- Re-verifying every sentence of every issue — cap 3 claims/issue, 8 issues.
- Treating UNVERIFIED as a blocker — it is informational only.
- Running this for housekeeping sessions — predefined tasks carry no premise risk worth the latency.
