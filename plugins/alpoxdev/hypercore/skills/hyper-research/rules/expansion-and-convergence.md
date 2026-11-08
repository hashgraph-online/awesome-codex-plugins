# Expansion And Convergence

Use this rule file once the first collection wave returns. It owns the `## EXPAND` lead format, expansion waves, excursions, and the only stop rules for collection. `--quick` runs no expansion wave and skips this file.

## 1. The Lead Format

Every collection return - a lane's reply or the leader's own pass over one axis - ends with this tail:

```markdown
## EXPAND
- LEAD: <discovery not yet investigated> - WHY: <why it matters to the core question> - ANGLE: <the distinct query or source to try>
- DEAD END: <lead explored to exhaustion>
```

A return with nothing to expand writes `## EXPAND` followed by `none - <one-line reason>`. A lane reply without the tail is incomplete: send one follow-up asking for it, and record the lane as a gap if it still does not arrive.

## 2. The Expansion Loop

| Element | Value |
|---|---|
| Feedback | New `LEAD` lines, plus claims that failed the claim gate (`rules/claim-verification.md`) |
| Metric | Unchecked leads in `expansion.md`, and the source floor of the depth |
| Guard | The claim gate and the authority rule: a lead never authorizes a side effect |
| Cap | The depth's expansion-wave budget (`SKILL.md`, depth modes) |
| Decision | Investigate, close as duplicate, or close as dead end, one line per lead |

Per wave:

1. Journal each return when it lands: the digest, new ledger rows, and the `## EXPAND` lines verbatim.
2. Deduplicate new leads against every lead ever seen in `expansion.md`, not only the confirmed ones, so a rejected lead does not resurface.
3. Investigate each new unchecked lead with a distinct query or a lane, inside the depth's lane cap.
4. Record the wave: lanes or searches run, leads gained, leads closed, and why.
5. Relay user steering: when the user changes scope, sources, language, or format mid-run, record the exact wording and pass it to every live lane before the next wave.

## 3. Excursions

An excursion is a bounded detour to chase a find that the wave plan did not schedule. The core question never changes during it.

Enter only on a named trigger, and write which one:

1. The find contradicts a claim already in the claim table.
2. It would change the final answer or recommendation if true.
3. It opens a source territory no axis owns.
4. The user's steering points at it (quote their words).

Interest alone is not a trigger; such a find stays a queued lead.

Before entering, write the budget: searches or lanes for this level. An excursion may open at most one nested excursion. A third level means the find is its own research question: surface, then either promote it to an axis within the depth's caps or record it as an out-of-scope gap.

Exit when any one of these holds:

- the trigger is resolved: the claim is confirmed, refuted, or its dependency closed
- two consecutive probes changed nothing in the parent answer
- the find stops moving any claim's status
- the stated budget is spent

Every exit writes one line saying what the excursion changed in the top-level answer; `none - <reason>` is a valid and required outcome. After each exit, re-read the core question and confirm the run still answers it. Three consecutive excursions that changed nothing end excursions for the run.

## 4. Stop Rules

These are the only stop rules for collection. A lane finishing is never one of them.

Converged - stop collecting when the source floor is met and any of these holds:

- zero unchecked leads remain, each investigated or closed
- two consecutive waves produced no new actionable lead
- the same results recur across three distinct queries with nothing new

When leads run dry while the source floor is still short, spend the remaining waves on targeted queries for the floor; if the cap arrives first, the run is `exhausted` and the shortfall is named.

Minimum: `--deep` runs at least two expansion waves whenever leads remain after the first wave.

Exhausted - stop when the depth's wave cap is reached with leads still open, or when the remaining time or context is needed for verification and the report (keep roughly the last fifth for them). Report the run as `exhausted`, never as converged, with four fields: the cap that was hit, the open leads, the last wave's result, and what an extension would investigate. In `--deep`, offer the extension as one question; do not run it without an answer.

Blocked - stop when progress needs a credential, an account action, a purchase, or another side effect outside this skill's authority. Name the missing access as a gap.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The `## EXPAND` tail, lead deduplication against every lead ever seen, expansion waves, excursion triggers, budgets, exit rules, fold-back lines, and steering relay, adapted from the `ulw-research` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| A stop condition carries a numeric cap; budget exhaustion is `exhausted`, not done; no progress is a stop; exhaustion reports its cap, distance, last verdict, and resume state | `instructions/loop-engineering/LOOP_ENGINEERING.md`, `instructions/loop-engineering/references/stop-conditions-and-verification.md` |
| Similar results recurring three times with no new information is a stop | `instructions/sourcing/reliable-search.md` |

### Evidence grade

`LOCAL` - this file states this package's own loop. The upstream skill runs expansion without a wave cap; this package keeps its convergence rules and adds the caps that the repository's loop rules require.
