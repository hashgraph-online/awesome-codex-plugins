# The economy file, the model and the rules

`scripts/economy-check.mjs` reads one JSON file and prints a verdict. This file explains every input, how the numbers are combined and what each rule means. The example input is `assets/economy.example.json`. Its values are placeholders that show the format.

```bash
node scripts/economy-check.mjs config/economy.json          # text report
node scripts/economy-check.mjs config/economy.json --json   # the same result as JSON
```

Exit code 0: the economy holds. 1: at least one rule is violated. 2: the file is missing, is not JSON, or has a wrong or unknown field. Every input problem is listed at once.

## Inputs

Percentages are numbers from 0 to 100. Money is in dollars. All volumes are per month. Keys that start with `_` or `$` are ignored, so the file can carry a note next to each number saying where it came from.

| Field | Meaning | Default |
| --- | --- | --- |
| `currency.coinsPerDollar` | Coins credited per $1 of payout at a 100 percent share | required |
| `currency.redeemCoinsPerDollar` | Coins that buy $1 at cash-out | same as the rate |
| `currency.name` | Used in the report | `coins` |
| `earning.userSharePct` | Share of each conversion's payout credited to the user | required |
| `earning.smallestPayoutUsd` | Smallest payout the app credits | not checked |
| `volume.monthlyRevenueUsd` | What the networks credited in a month, before reversals | required |
| `volume.activeUsers`, `volume.newUsers` | Needed by per-user bonuses and the time to the minimum | none |
| `payout.minimumUsd` | Smallest payout a user can request | required |
| `payout.feePct`, `payout.feeFixedUsd` | Provider fee: percent of the amount plus a fixed part per payout | 0 |
| `payout.feePaidBy` | `app` or `user` | `app` |
| `payout.averagePayoutUsd` | Average size of one payout | the minimum |
| `payout.redemptionPct` | Part of all credited coins that is redeemed | 100 |
| `reversals.ratePct` | Part of revenue that the networks take back | 0 |
| `reversals.holdDays` | Days before an earning can be cashed out | 0 |
| `reversals.arrival` | Cumulative curve: `{ "days": 30, "pct": 92 }` means 92 percent of all reversals arrived within 30 days of the credit | none |
| `reversals.lateRecoveryPct` | Part of late reversals that is still collected from remaining balances | 0 |
| `costs.otherPctOfRevenue` | Costs that grow with revenue | 0 |
| `costs.fixedMonthlyUsd` | Costs that do not | 0 |
| `cash.outstandingCoins` | Sum of all user balances | section optional |
| `cash.reserveUsd`, `cash.receivablesUsd` | Cash set aside, and revenue confirmed but not yet paid by the networks | 0 for receivables |
| `cash.networkPaymentDelayDays` | Days between a conversion and the network's payment for it | not checked |

Bonuses are a list. Each entry has a `type`, an optional `name` and:

| Type | Fields | Coins per month |
| --- | --- | --- |
| `per_new_user` | `coins`, `takeUpPct`, `requiresEarning` | new users x take-up x coins |
| `per_active_user_per_day` | `coins`, `takeUpPct`, `requiresEarning` | active users x 30 x take-up x coins |
| `per_active_user_per_month` | `coins`, `takeUpPct`, `requiresEarning` | active users x take-up x coins |
| `fixed_per_month` | `coins` | the budget itself |
| `earning_multiplier` | `pct`, `coveragePct` | offer rewards x pct x coverage |
| `referral` | `pct`, `coveragePct` | offer rewards x pct x coverage |

`takeUpPct` defaults to 100. For a daily bonus it is the part of active users who claim on an average day. `coveragePct` is the part of all offer earnings the bonus applies to: for a boost, earnings credited while it runs; for a referral commission, earnings made by referred users. `requiresEarning: true` says the bonus is credited only after the account has real earnings.

Targets are the owner's limits. Only `minMarginPct` has a default (0: the app must not lose money).

| Target | Rule it switches on |
| --- | --- |
| `minMarginPct` | `margin-below-target` |
| `maxEffectiveSharePct` | `effective-share-over-target` |
| `maxBonusPctOfRevenue` | `bonus-budget-over-target` |
| `maxDaysToMinimumPayout` | `minimum-payout-too-far` |
| `minReversalsInsideHoldPct` | `hold-misses-target` |
| `maxRoundingLossPct` | turns the `rounding-loss` warning into a violation |

## How the numbers are combined

All of it is per month, in dollars, with coins valued at the redeem rate.

```text
net revenue      = revenue x (1 - reversal rate)
rate ratio       = coinsPerDollar / redeemCoinsPerDollar
inside hold      = the arrival curve read at holdDays (straight lines between points)
uncollected      = (1 - inside hold) x (1 - late recovery)
standing         = 1 - reversal rate x (1 - uncollected)

offer rewards    = revenue x share x rate ratio x standing
earning bonuses  = offer rewards x (sum of pct x coverage over boosts and referral)
fixed bonuses    = bonus coins per month / redeemCoinsPerDollar
issued           = offer rewards + earning bonuses + fixed bonuses

fee rate         = feePct + feeFixedUsd / averagePayoutUsd      (0 when the user pays)
paid to users    = issued x redemption x (1 + fee rate)
other costs      = revenue x otherPctOfRevenue + fixedMonthlyUsd

margin           = net revenue - paid to users - other costs
effective share  = issued / net revenue
```

`standing` is the part of all credits that stays with users: credits for conversions that were not reversed, plus credits for reversed conversions that could not be taken back. With no arrival curve, every reversal is counted as uncollected.

The report shows the margin twice. "margin" uses `redemptionPct`. "margin if every coin is redeemed" uses 100 percent, because unredeemed coins are still owed.

## The report

- **Per $1.00 of revenue.** What is kept after reversals, what goes to users as offer rewards and as bonuses, fees, other costs and the margin. The lines add up.
- **Paid to users.** The share on each conversion, and the effective share once bonuses and the rate ratio are counted, as a part of the revenue that is kept. Each bonus with its monthly cost.
- **Break-even.** Each line moves one input and leaves the rest as given:
  - highest user share that still meets the target margin, and the share at which the margin is zero,
  - lowest monthly revenue at which fixed bonuses and fixed costs are covered (per-user bonuses are held at the user numbers in the file),
  - highest reversal rate the margin can absorb with the current hold,
  - room for more bonuses, in coins per month, before the margin falls to the target (negative: over budget by that much),
  - highest redemption rate at which the target is still met.
- **Hold and payout.** What part of reversals the hold catches, what uncollected reversals cost per month, the minimum in coins, the days an average active user needs to reach it, and the fee at the minimum.
- **Unspent balances.** The liability added per month, and with a `cash` section what is owed now against cash plus receivables, and the cash needed while users can cash out before the networks pay.

## Violations

A violation makes the exit code 1.

| Rule | It fires when | What to change |
| --- | --- | --- |
| `pays-more-than-it-earns` | The margin with every coin redeemed is below zero | Lower the share or the bonuses, or bring the redeem rate back to the rate |
| `margin-below-target` | The expected margin is below `minMarginPct` | Use the break-even lines to pick the input to move |
| `effective-share-over-target` | Share plus bonuses exceeds `maxEffectiveSharePct` | Cut the bonus that costs most |
| `bonus-budget-over-target` | Bonuses exceed `maxBonusPctOfRevenue` of kept revenue | Lower amounts, coverage or budgets |
| `smallest-reward-is-zero` | The smallest payout is worth less than one coin | Raise the rate, add decimals, or hide offers that small |
| `bonus-only-payout` | An account that completes nothing reaches the payout minimum within 30 days on bonuses alone | Smaller bonuses, a higher minimum, or `requiresEarning` |
| `no-hold` | Reversals happen and `holdDays` is 0 | Add a hold |
| `hold-misses-target` | The hold catches less than `minReversalsInsideHoldPct` | The message names the hold that would meet it |
| `fee-consumes-minimum-payout` | The user pays the fee and it is as large as the minimum payout | Raise the minimum or change who pays |
| `minimum-payout-too-far` | An average active user needs longer than `maxDaysToMinimumPayout` | Lower the minimum |
| `liability-not-covered` | Balances, with fees, are worth more than cash plus receivables | Hold more cash, or slow what is issued |
| `payment-gap-not-funded` | The reserve is smaller than what is paid out during the days between the hold and the network's payment | A longer hold, or more reserve |

## Warnings

A warning does not change the exit code. Read each one and either act or note in the file why it is accepted.

| Warning | Meaning |
| --- | --- |
| `margin-relies-on-unredeemed-coins` | The target is met only because part of the coins is assumed never to be redeemed |
| `redeem-rate-below-earn-rate` | Coins are worth more at cash-out than they cost, so the real share is higher than the stated one |
| `rounding-loss` | Rounding down can take more than 1 percent of the smallest reward (or more than `maxRoundingLossPct`) |
| `no-arrival-data` | There is a hold but no arrival curve, so no reversal is counted as caught |
| `fees-at-minimum-payout` | If every payout were at the minimum, fees would turn the full-redemption margin negative |
| `minimum-payout-not-checked` | The target needs `volume.activeUsers` |
| `cash-not-checked` | No `cash` section, so the liability and the payment gap were not checked |

## What the model does not do

- It does not forecast revenue or user numbers. It checks whether the numbers it is given fit together.
- It is one month in a steady state. A launch month with many sign-ups and little revenue looks worse than this, and should be entered as its own file.
- It works with averages. A few accounts that earn far more than the average, or a bonus claimed mostly by accounts that never earn, need the per-account queries in measuring-from-your-data.md.
- It does not know about spending inside the app. If coins buy things that cost the app nothing, enter only the part that leaves as money in `redemptionPct`.

## Using the functions from code

The script exports its calculation, so a project test can assert on the result instead of parsing text:

```js
import { readFileSync } from 'node:fs';
import { checkEconomy } from './economy-check.mjs';

const result = checkEconomy(JSON.parse(readFileSync('config/economy.json', 'utf8')));
if (!result.ok) throw new Error(result.violations.map((v) => `${v.rule}: ${v.message}`).join('\n'));
```

`checkEconomy(input)` returns `ok`, `perDollarOfRevenue`, `monthly`, `share`, `bonuses`, `breakEven`, `hold`, `payout`, `rounding`, `cash`, `violations` and `warnings`. It throws `InputError` with a `problems` list when the input is wrong. `formatReport(result)` gives the text report.
