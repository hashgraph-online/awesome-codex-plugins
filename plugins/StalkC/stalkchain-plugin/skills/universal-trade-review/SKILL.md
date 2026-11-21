---
name: universal-trade-review
description: Review a trader's fills, positions or a trading session in depth, trade by trade, across execution, risk, thesis and behaviour. Use when the user asks to review, audit or break down how a trader (or they themselves) traded over a period, what they did well or badly, or to keep a running trade journal. For a quick profit-and-wallets check use trader-check; for a trader's general habits use trader-playbook.
argument-hint: "<trader handle or wallet> [time window]"
---
# Universal Trade Review

A reusable panel for analyzing **any** trader’s activity: what they traded, what they did, and how they did it. Stay platform-agnostic. Do not bake in a specific handle, chain, exchange, or personal standing orders — those belong in the routine or chat that invokes this skill.

## Whose trades

- **Someone else's** (a tracked trader, a wallet): describe what they did and how it turned out. No standing orders, no `behavior_action`, no mental-state tags: observable patterns only. This is research about a public trader, not coaching them.
- **The user's own**, when they say so: the full review, including draft standing orders for their own process. Still never a call to buy, sell or hold any token.

## Get the data from StalkChain

Resolve a handle first with `stalkchain_fomo_search` (`q`, 250 credits); it returns the userId and wallets. Then, cheapest first:

- `stalkchain_fomo_trader_positions` with `trader` (and `status`): opens and closes with entry and exit, cost basis and PnL. Usually enough on its own.
- `stalkchain_fomo_trader_swaps` with `trader` (or `tokenAddress` for one token): the individual fills, for timing and sizing.
- `stalkchain_fomo_trader_report` with `trader`: profit, win rate on a closed sample and the current book in one call. In Claude and ChatGPT it renders as a card, so add the reading rather than re-listing its numbers.
- `stalkchain_fomo_theses_by_trader` with `trader` (1,250 credits a page): only when the thesis seat matters.
- A raw Solana wallet with no handle: `stalkchain_wallet_pnl` with `wallet`. EVM transfers in and out: `stalkchain_wallet_transfers` with `wallet` and `chain`.

Data the user pastes is used as given, with its source recorded. Data neither returned nor supplied is unknown.

## Inputs (gather first)

Collect whatever source is available; missing fields are fine — flag gaps instead of inventing:

- **Identity:** trader / account label (opaque id or handle as given)
- **Window:** time range under review (prefer an explicit start/end)
- **Fills / swaps:** time, side, size (units + notional), instrument, fees if known
- **Positions:** opens and closes in window; cost basis; realized / unrealized PnL
- **Optional:** written thesis or notes, tags, transfer-in vs bought, hold time

Normalize each closed (and meaningful open) trade into a **trade card**:

| Field | Notes |
| --- | --- |
| `tradeId` | Stable id if available |
| `instrument` | Symbol / contract / pair |
| `side / path` | Long/short or buy→sell path |
| `size` | Notional and % of book if estimable |
| `entry / exit` | Price + time |
| `hold` | Duration, or null if entry/exit timing is incomplete |
| `pnl` | Realized/unrealized separately, numeraire and valuation time; R = PnL / documented positive initial risk ONLY; return on cost = PnL / known positive cost basis, reported separately |
| `thesis` | Supplied / explicitly absent / unknown; lack of supplied notes does not prove no thesis existed |
| `source_flags` | e.g. transfer-in, scratch, partial, stuck, unsellable; each with source id/row/transaction, observed facts and limits |
| `evidence` | Source/record locators supporting every material flag, metric, score and conclusion; distinguish observations, self-reports and hypotheses |

Tag transfers, airdrops and non-discretionary events separately; **transfers are not sales**. Unknown basis is null, never zero, and prevents an unsupported realized-PnL calculation. Reconcile acquisition, disposal, fees and valuation in a stated numeraire. Do not double-count partial exits or count unrelated incoming transfers as profit.

**No survivorship exclusion:** bought positions that become stuck/unsellable remain in economic PnL and the reviewed population. Record residual inventory and an evidence-backed realizable valuation or explicit valuation range/unknown, not an invented executable mark. Separate realized PnL from unrealized impairment and disclose incomplete totals. A closed-trade win rate may exclude still-open positions only under a declared closed-trade definition; show the impaired open inventory alongside it. Process-only cohorts may be reported separately with exact inclusion/exclusion reasons, never substituted for whole-account performance.

Calculate with tools, not mental arithmetic. Define denominators, break-even counts, sample size, observation coverage and costs. Expectancy must specify units and cohort (e.g. mean net PnL per eligible closed trade, or mean R only where initial risk is documented). Unknown inputs yield null/partial coverage, not fabricated zeros or scores. Cost basis and position notional are not initial risk. If initial risk is zero, absent or unreconstructable, R is null.

## Four seats (same cards, structured flags)

Each seat must emit **machine-readable flags** plus one short spoken line. No vibes-only commentary.

### 1. Tape / execution — “What did they actually do on the trade?”

- `entry_quality`: early | mid | chase | transfer_in | unknown
- `size_bucket`: dust | small | standard | heavy | account_risk | unknown
- `exit_style`: scalp | trim | full_exit | stop_like | held_to_zeroish | still_open | unknown
- `tape_note`: ≤140 chars
- `execution_score`: 1–5 or null (5 = would repeat the *process*, not the outcome); non-null scores require stated rubric and supporting evidence, never outcome alone

### 2. Risk — “What did this do to the book?”

- `risk_pct_of_book`: number or null
- `hold_hours`: number or null
- `r_multiple`: number or null
- `correlation_cluster`: free label or unknown (e.g. same sector / same narrative family)
- `rule_break`: none | oversized | no_invalidation | revenge_size | add_to_loser | overtrade_burst | other | unknown
- `risk_verdict`: pass | warn | fail | unknown; missing rules/risk inputs are unknown, not a rule violation

### 3. Thesis / narrative — “What story were they buying?”

- `thesis_present`: bool or null; false requires evidence of absence, not merely missing supplied notes
- `thesis_quality`: none | meme_or_slogan | thesis | detailed | unknown
- `narrative_family`: short label or unknown
- `narrative_phase`: emerging | crowding | exhausting | dead | unknown
- `dependency`: none | external_catalyst_required | copycat | other | unknown
- `mismatch`: bool or null (story moved while they held); requires dated thesis and event evidence

### 4. Behavior — “What pattern showed up in the trader?”

- `behavior_tags`: subset of `[discipline, patience, impulse, fomo_chase, revenge, size_up_after_win, size_up_after_loss, cut_winner_early, hold_loser_long, average_down, probe_then_stop]`
- `cluster_id`: optional link to a same-session burst
- `emotion_guess`: calm | greedy | fearful | tilted | numb | unknown — retained field name for compatibility, but **not permission to guess**. Default unknown; only attribute emotions from the trader's explicit self-report, with a citation.
- `behavior_action`: reinforce | interrupt | hard_rule_candidate | unknown; a review suggestion, not execution authority

Observed size increases, entry timing or averaging down do not establish impulse, FOMO, revenge or another mental state. Label observable patterns separately from hypotheses; emotional/intent tags require self-report. A `rule_break` needs the actual applicable rule and evidence of breach; absent rules are unknown. Cite evidence locators for every flag; do not fabricate a score to fill a seat.

After all seats: one `consensus_line` ≤200 chars citing the trade id or symbol.

## Session shape

1. **Open book** — concentration, largest uPnL winners/losers, total risk.
2. **Closed tape** — walk closes in the window (newest first); deep-dive evidenced process failures / self-reported revenge / oversizing against supplied limits.
3. **Pattern board** — repeating clusters, rule-break counts, thesis coverage on large size.
4. **Standing orders (draft)** — up to 3 evidence-supported, concrete, testable proposals for the *next* window (not motivational advice). Insufficient evidence can justify fewer or none. Drafts never automatically change live rules or account settings.

## Deliverables

1. **Spoken / chat brief** — short: headline PnL, seat highlights, top winners/losers, open watch, next-window orders.
2. **Structured memory JSON** (append-only by date), schema sketch:

```json
{
  "review_id": "<unique-review-id>",
  "date": "YYYY-MM-DD",
  "trader": "<label>",
  "account_id": "<stable-account-key>",
  "window": { "start": null, "end": null, "timezone": null },
  "sources": [],
  "coverage": { "status": "unknown", "gaps": [], "cohort_definition": null },
  "stats": {
    "closed_n": null,
    "win_n": null,
    "loss_n": null,
    "breakeven_n": null,
    "sum_realized_pnl": null,
    "unrealized_pnl": null,
    "economic_pnl": null,
    "numeraire": null,
    "expectancy": null,
    "expectancy_units": null,
    "eligible_n": null,
    "rule_breaks": {},
    "behavior_tag_counts": {},
    "evidence": []
  },
  "trade_reviews": [
    {
      "tradeId": "<source-trade-id>",
      "source_flags": [],
      "evidence": [],
      "flags": {
        "execution": { "execution_score": null },
        "risk": { "risk_pct_of_book": null, "hold_hours": null, "r_multiple": null, "rule_break": "unknown" },
        "thesis": { "thesis_present": null, "thesis_quality": "unknown", "mismatch": null },
        "behavior": { "behavior_tags": [], "emotion_guess": "unknown" }
      },
      "consensus_line": null
    }
  ],
  "standing_orders": [],
  "standing_orders_status": "draft_requires_user_approval",
  "hypotheses": [],
  "pending_questions": []
}
```

Save only in Claude Code, Cowork or Cursor, with a project folder, and only when the user asks to keep the review; in chat apps give the brief and skip saving. Store under the caller's approved path; otherwise default to local `trade-review/memory/<trader-account-key>/YYYY-MM-DD/<review-id>.json`. This sketch is a template, not observed data. Choose a collision-resistant review id; validate the account key and id as safe path components, not raw user text. Create new files exclusively (fail on existing paths), never overwrite a previous review. Confirm identity and scope before persistence; if identity is ambiguous, keep a draft rather than mingle traders. Revisions get new ids and a `supersedes_review_id` link. Read back the exact new record to confirm trader/account, window and id. Never replace the whole date's history. If the caller supplies a single file, agree on an append-only record format or unique sibling path rather than silently clobber it.

Each source gets an id, origin/file/transaction locator, retrieval or observation time and coverage limits. Each `source_flags` entry includes its flag, supporting source ids and record locators, and observed vs self-reported vs hypothesized status. `evidence` ties each material flag/metric to those sources and its calculation/rubric. A trade id alone identifies a subject, not proof of an emotion, rule violation or financial metric.

## Self-learning loop (universal)

1. Load last ~7 days of memory for this exact trader/account only, plus explicitly approved active standing orders and hypotheses. Do not treat a past draft as active.
2. Evaluate each new trade against applicable approved standing orders → `order_respected` | `order_broken` | `unknown`; cite the rule version and evidence. No supplied rule is not proof that no rule existed.
3. Append hypothesis evidence/counter deltas when an eligible tagged condition appears; deduplicate by account and source trade/event id across overlapping windows. Preserve prior records.
4. Propose promoting or retiring hypotheses only with clear evidence; user approval is required to alter active standing orders. Never automatically modify live rules, risk limits or account settings.
5. Every flag must cite source evidence and the relevant trade id; a running counter must disclose eligible events, denominator and deduplication. Ban generic advice and unsupported psychological inference.

## Introspection questions (optional)

If asking the trader questions about chosen trades:

- Scope questions to the **most recent ~24h** of *their* tape (or same session), not the full stats window.
- Keep a pending-questions list; **re-ask unanswered** before opening a new set.
- Prefer trades that teach (large R, rule break, thin thesis, behavior cluster).

## Intellectual lineage (use as lenses, not name-drops)

- **Schwager / Market Wizards** — interview for method + psychology; many edges, shared risk discipline.
- **Livermore / Reminiscences** — crowd, cutting losers, not fighting the tape.
- **Van Tharp** — R-multiples and size from risk, not conviction theater.
- **Douglas / Steenbarger** — execution psychology; review decisions, not just PnL.

When framing findings, prefer: process quality, R, invalidation, size, and repeatable patterns over “genius” or “luck” narratives.

## Hard rules

- Never tell the user to buy, sell, hold, copy or follow anything. Reviews describe process and outcomes; they are data, not financial advice.
- Coaching (standing orders, `behavior_action`) is for the user's own trades only.
- Never invent fills, PnL, or quotes.
- Never change the trader’s live account settings.
- Separate process cohorts from whole-account economic accounting; transfers are not closes, unknown basis is not zero, and bought stuck/unsellable losses must not disappear.
- Keep this skill generic: no hardcoded person, venue, or meme-coin rules.
