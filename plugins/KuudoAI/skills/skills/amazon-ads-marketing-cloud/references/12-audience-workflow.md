# Audience workflow: plan, build, activate, measure

Work these six steps in order for any request to plan, size, build, activate, or measure an AMC audience. The approval gates, evidence labels, and privacy rules are in SKILL.md → Guardrails and apply at every step.

Contents: 1. Frame the decision · 2. Check readiness · 3. Pick the smallest analysis · 4. Define and draft the audience · 5. Plan one activation change · 6. Measure, review, retire

An AMC audience is worth building when it serves a decision: who to reach, who to suppress, who to expand to, and how you'll know it worked. Start from that decision, check that the account can support it, pick the smallest analysis that informs it, draft the audience and its SQL, plan one activation change, and set up measurement before anything goes live. The failure this prevents is the reverse order: building an audience from a template or a case study, then looking for a reason it worked.

## 1. Frame the decision

Note the decision and who makes it, the deadline, the advertiser, AMC instance, Ads profile, marketplace, brand or ASINs, ad products in play, time window, and time zone. Then rewrite the ask as a question data can answer:

| The ask | An answerable question |
|---|---|
| "Which audience is best?" | "Among shoppers who viewed our detail pages in the last N days without buying, does a Sponsored Products bid boost raise conversions enough to cover its extra cost?" |
| "Should we retarget after Prime Day?" | "Do shoppers our ads reached during Prime Day who didn't buy convert at a profitable cost over the next N weeks, compared with a holdout?" |
| "How many touches does it take?" | "What is the distribution of days and ad touches from first exposure to purchase for ASIN X, by ad product?" |

N comes from this account's data (step 3), not from a benchmark.

## 2. Check readiness

Work through `03-readiness-checks.md`. In short:

- The advertiser, Ads profile, AMC instance, and marketplace belong together.
- Four separate states are in place: the instance is visible, AMC terms are accepted, the user can edit the target campaigns, and AMC audiences are available in the target console. Having one doesn't imply the others.
- The data covers the question: the ad products loaded in the instance, the backfill, conversion maturity, and breaks such as renamed campaigns, stockouts, promotions, or price changes. Reads that compare against shoppers with no ad exposure need base `conversions_all`, a paid feature; audience queries on `conversions_all_for_audiences` don't.
- The listing can take the traffic: in stock, winning the Buy Box, and profitable after returns.
- Each marketplace stands alone unless there is an explicit basis for combining them.

The verdict is one of `READY_FOR_ANALYSIS`, `READY_FOR_AUDIENCE_DRAFT`, `READY_FOR_APPROVAL`, or `HOLD`, with the gaps and what would lift them. "No results returned" is not zero. AMC drops any output group behind fewer than about 100 shoppers, so a small account, a short window, or a fine grouping can come back empty; filters, permissions, and data latency do it too. Pick a window and grouping big enough to clear that floor, and diagnose an empty result before you interpret it.

## 3. Pick the smallest analysis

Run only what the decision needs. Playbook IDs refer to `07-playbooks.md`; quoted names are Atlas instructional queries, found by title.

| Decision question | Analysis | Output | Start from |
|---|---|---|---|
| How long and how many touches before purchase? | Time to conversion | Distribution, not a single average | Playbook M1; "Time to Conversion" |
| How often do customers rebuy? | Repurchase interval | Gap distribution | Playbook M4 |
| Which ad sequences precede purchase? | Path to conversion | Paths, reach, conversions, NTB, cost basis | Playbook M5; "Path to conversion by campaign groups" |
| Are ad products reaching the same shoppers? | Ad-type overlap | Exclusive and combined reach and conversion | Playbook M2; "Sponsored ads and DSP overlap" |
| Are we over- or under-exposing? | Reach and frequency | Conversion by frequency bucket | Playbook M6; "Reach and impression frequency" |
| Are we recruiting new customers? | New-to-brand | NTB purchases, sales, and share, reported separately | Playbook M3; "New-to-brand customers" |
| Which touch gets credit? | Custom attribution | First- versus last-touch credit by campaign | Playbook M7; "Custom attribution overview" |
| Who is worth seeding or protecting? | High-value segments | Value tiers for lookalike seeds or suppression | Playbook A5; "Identify high value customer segments" |
| Is an existing bid boost working? | Bid boost performance | Boosted versus unboosted traffic | Playbook M8 |

`04-analyses-and-misreadings.md` has what each analysis needs, what to compare it against, and how each is commonly misread. If the analysis already answers the decision without an audience, stop there; not every insight needs one.

## 4. Define and draft the audience

Write each audience as a definition card: purpose, type, include and exclude rules, lookback and whether it rolls forward, marketplace, ASIN or brand scope, size status, refresh cadence, activation target, and review date. Derive the lookback from this account's time to conversion or repurchase cycle. A window that worked for another brand is an `EXTERNAL_BENCHMARK`; if this account's data isn't in yet, propose a starting window labeled `HYPOTHESIS` and say which analysis will confirm it.

Then draft the SQL from the closest audience playbook (A1 to A8 in `07-playbooks.md`), with its sizing companion, following `06-amc-sql-rules.md`:

- **Rule-based** audiences read `_for_audiences` tables, and their final `SELECT` returns only `user_id`. Exclude purchases from `conversions_all_for_audiences`, so shoppers who bought without an ad are excluded too.
- **Event audiences** pin the event dates inside the SQL, converted to UTC, and keep purchase exclusions running from the event start to each refresh. A rolling lookback alone drifts off the event.
- **Lookalike** audiences expand from a seed of 500 to 500,000 users. Seed quality matters more than seed size. Reach runs in tiers from most similar to broadest, so change one tier step at a time. Keep the seed's existing buyers out of the lookalike's spend with a campaign exclusion, unless the lookalike's settings already exclude the seed.
- **Size before creating.** Every audience gets a companion count against the current minimum, and a lookalike seed gets one against its bounds. Say up front what you'd widen if it falls short: a longer window, more ASINs or the brand's full catalog, or dropping a restriction such as "reached by our ads"; for a seed over the upper bound, tighten the condition. Sizing runs are real executions, so list them in one itemized ask. A dry run validates the audience SQL with no ask, but a real run of it outside audience creation is rejected, so sizing reads the companion tables.
- **Refresh is not expiry.** AMC audiences refresh on a schedule (the API defaults to every 21 days) and overwrite themselves on each run until deleted. The only built-in end is a rule-based audience's `refreshRateDays: 0`, which deactivates it after 30 days, so set the cadence deliberately and put a review date on the card.
- **No-code templates** vary by instance. If one isn't visible on this instance, keep the business definition, mark it `TEMPLATE_NOT_VERIFIED`, and don't invent a template name.

Patterns for engaged non-buyers, seasonal audiences, intent tiers, lifecycle and cross-sell, suppression, and lookalike seeds are in `05-audience-design.md`.

## 5. Plan one activation change

What an audience does depends on where it is used. Confirm that the audience appears in the target console and that the action is supported there before you plan on it, and label that check `CURRENT_POLICY`.

| Channel | What the audience does | What to measure |
|---|---|---|
| DSP | Targets or excludes the audience directly | Reach and conversions against a holdout |
| Sponsored Display | Targets the audience directly | Conversions and cost against a holdout or prior baseline |
| Sponsored Products, Sponsored Brands | A bid boost raises bids when an audience member matches the campaign's existing keyword or product targeting. It doesn't restrict who is eligible to see the ad. | Effect of the boost: boosted versus unboosted traffic on cost per click, conversion, and profit |

Write each change as a single-variable action card: current, proposed, and rollback values; evidence; baseline and measurement windows, including attribution lag; primary metric; guardrails; and stop conditions. Give the proposed value as a number, such as a +20% boost, labeled `HYPOTHESIS` with the reason for it. A change is one of: add or exclude one audience, set one bid adjustment, activate one lookalike, or change one window or refresh cadence. Changing the seed, window, and bid together leaves no way to tell which one moved the result. Details are in `08-activation-and-testing.md`.

## 6. Measure, review, retire

Record the baseline before activation. Prefer a randomized holdout over a before-and-after comparison, and wait for conversions to mature before reading results. Report absolute and relative lift with sample sizes. On the review date choose `KEEP`, `ITERATE`, `ROLLBACK`, or `EXPIRE`, and retire expired audiences so an old window doesn't keep refreshing. Deleting an AMC audience also removes it from the DSP and Sponsored Ads consoles, so a deletion is a write with its own ask.

End audience and measurement work with one verdict in plain words (proceed to analysis, proceed to review, hold, or no-go; the code `PROCEED_TO_ANALYSIS`, `PROCEED_TO_REVIEW`, `HOLD`, or `NO_GO` can follow in parentheses), and say in a few lines what rests on account facts, what is an external benchmark or hypothesis, which Amazon rules still need checking, whether the evidence is only correlational, and which writes wait for approval and how each rolls back.
