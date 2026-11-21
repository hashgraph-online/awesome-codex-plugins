# Report Template

Use this reference when drafting the saved research report.

## Contents

- File path
- Template
- Quick variant
- Writing rules

## File Path

Save to `.hyper/research/[NN].slug.md`, with the journal in `.hyper/research/[NN].slug/` for default, deep, and parallel runs.

Example: `.hyper/research/03.websocket-vs-sse.md` and `.hyper/research/03.websocket-vs-sse/`.

## Template

```markdown
# [Topic] Research Report

> As of: YYYY-MM-DD or version | Depth: quick/default/deep (+parallel) | Run state: converged/exhausted/blocked
> Sources reviewed: N | Sources cited: M | Domains: D | Waves: W | Excursions: X | Execution checks: V

## Executive Summary
[Answer the core question first in 2-4 sentences. Only verified claims appear here.]

## Scope And Fidelity
- Core question:
- Axes:
- Time window and as-of anchor:
- Source floor and derived-number policy:
- Evidence channels used:

## Key Findings
### 1. [Finding]
- Claim: [statement] [S1][S4] (C1)
- Numbers: [value] MEASURED [S1] | [value] DERIVED = [formula over inputs]
- Why it matters:

## Comparison
| Criteria | Option A | Option B | Sources |
|------|------|------|------|

## Expected Truths
| Expected truth | Result | Evidence |
|---|---|---|
| E1 | true / violated / unknown | |

## Verified Claims
| Claim | Kind | Verdict | Evidence |
|---|---|---|---|
| C3 | code | CONFIRMED | `[NN].slug/verify-<slug>.md` |
| C1 | non-code | supported (2 domains, primary S1, counter-search Q7) | [S1][S4] |

## Contradictions
- [Source A vs source B: resolution and evidence, or why it stays open]

## Debate record
| Claim | Verdict | Change to the claim |
|---|---|---|
| C1 | holds | |
| C5 | unverified (one debate attack) | moved to Unresolved |

- The full debate rows live in the journal file `debate.md`; this annex lists each high-risk claim with its verdict.

## Unresolved And Refuted
- Unresolved: [claim - what is missing]
- Refuted: [claim - the counter-evidence]

## Risks And Caveats
- [Limitation, weak-source caveat, assumption with its sensitivity line]

## Known Gaps
- [What the run could not answer; for an exhausted run, the open leads and what an extension would investigate]

## Recommendation
- [Decision or next action, drawn only from verified claims]

## Source Ledger
| # | Source | URL/path | Publisher | Published/updated | Accessed | Channel | Grade | Role | Used? |
|---:|---|---|---|---|---|---|---|---|---|

## Query Log
- [Distinct query, channel, and why it was used; for journaled runs, a pointer to `queries.md`]

## Expansion Trace
- Wave 1: [searches or lanes] -> [leads gained]; Wave 2: ...; stop reason: [rule]

## Validation Notes
- Gates: structure, citation, claim gate, lineage, recency, read-back - pass or residual defect
- Source floor: [met or shortfall, reviewed vs cited]
- Dedupe: [queries and duplicate sources handled]

## Report gates
| Gate | Status (pass / fail / not_run) | Open-defect severity (blocker / major / minor) | Reason |
|---|---|---|---|
| structure | | | |
| citation | | | |
| claim gate | | | |
| number lineage | | | |
| recency | | | |
| read-back | | | |

## References
- [S1] [Title](https://example.com/source), accessed YYYY-MM-DD
```

## Quick Variant

A `--quick` report keeps the header, Executive Summary, Scope And Fidelity, Key Findings, Risks And Caveats, Source Ledger, Query Log, Validation Notes, and References. It drops the sections a single pass cannot fill, and its claim-source matrix sits inside Key Findings.

## Writing Rules

- Put the answer before the backstory.
- Cite every non-obvious claim with `[S<n>]` ids that resolve to the ledger.
- Assert high-risk statements only from `verified-claims`; annex items appear only under Unresolved And Refuted.
- The `## Debate record` annex lists each high-risk claim with its verdict; the full debate rows live in the journal file `debate.md`.
- Label every number `MEASURED`, `ASSUMED`, or `DERIVED`.
- Use exact dates when recency matters, and state the as-of anchor in the header.
- Count a duplicate source once, even when several lanes found it.
- Quote sources verbatim in their original language, under 20 words, with a translation beside the quote when the report language differs.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The effort header, verified-claims and contradictions sections, the unresolved and refuted annex, the expansion trace, and short attributed quotes, adapted from the `ulw-research` synthesis layout | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The source ledger columns and the reviewed-versus-cited split | `instructions/sourcing/references/source-ledger.md` |
| The `## Debate record` annex that lists high-risk claims with their verdicts | `dbc-hbin/omp-ulw` at commit `74df40f` (2026-11-09); the source repository has no license, so the mechanism was re-authored in this package's own words and no text or code was copied |

### Evidence grade

`LOCAL` - this file carries this package's own template. The `https://example.com/source` destination is a placeholder host, not a source.
