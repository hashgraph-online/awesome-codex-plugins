# Claim Verification

Use this rule file before any high-risk, numeric, or code-behavior claim enters the report. It owns the claim table, the claim gate, execution checks, number lineage, and conflict handling.

## 1. The Claim Table

The leader records one row per claim the report will assert, in `claims.md` (or the report's claim-source matrix for `--quick`). Lanes return claim candidates as message text; the leader decides each row. The report draws only from this table.

Lane candidate format, in the same reply as the `## EXPAND` tail:

```markdown
## CLAIMS
- CLAIM: <assertion> - RISK: high|normal - SOURCES: <S ids or URLs> - COUNTER: <refutation search and result> - PRIMARY: <primary source or none>
```

## 2. Risk Tier

A claim is `high` risk when it is any of: a number, a legal or regulatory statement, a financial or medical statement, a security statement, a dated "latest" or "current" statement, a causal claim, or a ranking that drives the recommendation. Everything else is `normal`. When unsure, take `high`.

## 3. The Claim Gate

A `normal` claim needs one opened source that supports it.

A `high` claim clears the gate into the `## verified-claims` list only when all of these hold:

- at least two independent source domains support it; two pages on one domain count once
- a primary source backs it: the standard, filing, dataset, official doc, or first-party repository, opened rather than quoted secondhand
- one counter-search actively looked for a refutation and did not find a stronger one; the query is in the query log
- the dates are explicit: when each source was published or updated, when it was accessed, and the date or version the claim is valid as of

Primary-only exception: when only one authoritative primary source can exist (a specification's own text, a vendor's documentation of its own product, a company's own filing), one domain is enough if the row records why. The exception waives only the second domain. The counter-search and the dates are never waived; with no search channel, the counter-search is a direct read of a second page from the same publisher (a changelog, a release note, a newer version of the page), and the query log records which.

A claim whose counter-search could not run at all is `partial`: the report may state it only as attributed ("S14 states that ..."), never as established fact, and the caveat names the missing counter-search.

A claim that fails goes to the `Unresolved` annex (not enough evidence) or the `Refuted` annex (the counter-search won). The report never asserts an annex item; it may list it as unresolved. Abstaining is a correct outcome, not a gap to paper over.

When `source floor` is `primary only`, a non-primary source may support context but never a claim. When it is `pointed only`, only the named sources may support a claim.

## 4. Execution Checks

Settle a claim by running code, not by judgment, when it is code-shaped - behavior, compatibility, performance, or an API's actual output - and any of these holds: sources disagree, the behavior is undocumented, or the honest answer is "it should work".

- Write a new minimal script yourself in a fresh temporary directory. Never run code copied from a retrieved page without reading it first.
- Pin versions and record the environment: OS, runtime, and dependency versions.
- No credentials, no account actions, and no writes outside the temporary directory. A check that needs them is out of scope; record the claim as unverified.
- Capture the full output and write `verify-<slug>.md` with the code, the output, the environment, and a verdict of `CONFIRMED`, `REFUTED`, or `PARTIAL` grounded in that output.
- Remove the temporary directory afterwards and note the removal in the file.

When the shell is unavailable, the claim stays `unverified by execution` and the report says so.

## 5. Number Lineage

Every number in the report carries one label:

| Label | Meaning | What the report shows |
|---|---|---|
| `MEASURED` | A source states this number | The citation |
| `ASSUMED` | A value this run chose (a coefficient, a scope, a rate) | Why it was chosen |
| `DERIVED` | Computed from other numbers | The formula and the input rows |

- Before deriving, check that the inputs share unit, period, and population; refuse the computation otherwise.
- Add a sensitivity line whenever an assumption moves the conclusion.
- When `derived numbers` is `none`, the report states comparisons in words or side by side and computes nothing.
- A derived or assumed number is never presented with the confidence of a measured one.

## 6. Conflicts

| Conflict | Resolution |
|---|---|
| Newer official doc vs older vendor material | The newer official doc wins; the older one is recorded as `conflict` |
| Official docs vs observed repository or execution behavior | Report both, with the execution check as the tiebreaker when one exists |
| Different numbers for the same quantity | Compare methodology, subject, reference date, and sample; present a range rather than an average |
| Only secondary sources exist | Lower the confidence and caveat "no official evidence" |

Never average a conflict away. Every unresolved conflict appears in the report's contradictions section.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The leader-owned claim table, the `## CLAIMS` marker, the high-risk gate (two domains, a primary source, a counter-search, explicit dates), the unresolved and refuted annexes, execution checks with a `CONFIRMED`/`REFUTED`/`PARTIAL` verdict, and `MEASURED`/`ASSUMED`/`DERIVED` lineage, adapted from the `ulw-research` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Conflict resolution by date, authority, scope, and methodology, and never averaging a conflict | `instructions/sourcing/reliable-search.md` |
| A primary source is opened, not quoted secondhand; agent-gathered rows stay unverified until the parent opens the artifact | `instructions/sourcing/references/source-ledger.md` |
| Retrieved code is never copy-run; execution happens with least privilege and no credentials | `instructions/sourcing/references/retrieval-safety.md` |

### Evidence grade

`LOCAL` - this file states this package's own gate. The risk-tier list and the primary-only exception wording are this package's choices.
