---
name: design-reward-economy
description: Design and check the numbers behind a rewards currency. Covers coins per dollar, the share of each conversion paid to users, bonus budgets (sign-up, daily, streak, referral, promo codes), the payout minimum and fees, and hold periods sized to how late reversals arrive. Its script reads the economy as JSON and reports margin, effective payout share, break-even points and every violated rule. Use when the user asks how many coins or points per dollar, what user share to pay, how large a bonus can be, what payout threshold or hold to set, or whether a rewards app pays out more than it earns.
license: MIT
compatibility: Needs Node 20 or newer to run the bundled economy check script.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Design a reward economy

This skill produces the numbers of a rewards currency and the proof that they fit together: one economy file with the app's own figures, a check that passes on it, one place in the code that every rate and bonus is read from, and a monthly comparison of the plan with what happened. The failure it prevents is an app that promises more than it earns. That rarely comes from one bad number. It comes from a share and three bonuses that each looked fine, a shop that sells a dollar for fewer coins than a dollar creates, fees and reversals nobody priced in, and balances that quietly grow into a debt the cash cannot cover.

## Before changing a number

Read the project first.

- **Where the numbers live today.** The rate and the share in a handler, an environment variable, an admin setting or a network's dashboard. Bonus amounts in several files. The payout minimum in the front end. List every copy.
- **Every source and sink of coins.** The kinds of ledger entries that add coins, and the ways coins leave: payouts, gift cards, spending inside the app.
- **What history exists.** A ledger, conversion records with the payout in dollars and the time of each reversal, payout records with fees. How many finished months.
- **How the app is paid.** Which networks, and how long each takes to pay.

Then gather the inputs. Measure what the data holds, ask the owner for the rest, and never fill a gap with a figure from an article or another app. The queries are in [references/measuring-from-your-data.md](references/measuring-from-your-data.md).

| Input | Source | With no data |
| --- | --- | --- |
| Monthly revenue, active and new users | Conversion records, users table | The owner's plan, marked as planned |
| Reversal rate and arrival curve | Conversion records | Ask each network for its reversal window. Leave the curve out: the check then counts every reversal as late |
| Bonus take-up and coverage | Ledger entries by kind | 100 percent |
| Redemption | Ledger | 100 percent |
| Payout fees, average payout | Provider price list, payout records | Ask. Average payout equals the minimum |
| Days until networks pay, cash, receivables | The owner | Ask. Without them the liability is not checked |

These decisions belong to the owner. Ask once, in one message, with the default.

| Decision | Default |
| --- | --- |
| Target margin | Ask. Until answered the check uses 0: the app must not lose money. |
| Rate | A round number that makes the smallest reward at least 100 coins. |
| Redeem rate | Equal to the rate. |
| Rounding | Credits round down, prices round up, once. |
| Who pays payout fees | The app, priced into the share. |
| Part of reversals the hold must catch | Ask. With no answer use 90 percent, say so, and size the hold from the app's own curve. |
| Sign-up and daily bonuses | Credited only after the first real earning, and never enough to reach the payout minimum alone. |
| Unredeemed coins | Owed in full. Expiry only under a stated rule that the owner has checked against the law where the app operates. |
| Existing balances when the rate changes | They keep their value. |

## Build

1. **Collect the inputs.** Run the queries in [references/measuring-from-your-data.md](references/measuring-from-your-data.md) against a copy or a read replica. Note for each number where it came from.

2. **Write the economy file.** Copy `assets/economy.example.json` into the project, for example as `config/economy.json`. Replace every value: the example holds placeholders. Record the source of each number in a `_note` key next to it. Fields and defaults are in [references/model-and-rules.md](references/model-and-rules.md).

3. **Run the check and read it with the owner.**

   ```bash
   node scripts/economy-check.mjs config/economy.json
   ```

   Each violation names a rule; the table in [references/model-and-rules.md](references/model-and-rules.md) says what moves it. Use the break-even lines to choose: the highest share that keeps the target margin, the room left for bonuses, the hold that catches the wanted part of reversals. Change numbers, never the rules, until the exit code is 0. How to choose each number is in [references/choosing-the-numbers.md](references/choosing-the-numbers.md).

4. **Give the numbers one home in the code.** One configuration module holds the rate, the share, each bonus amount, the payout minimum and the hold, with the same values as the economy file. Replace every other copy with a read from it. If a network's dashboard also holds the rate and the share, set it to the same values and write that down in the file.

5. **Use one conversion function.** Payout to coins and dollars to a coin price, in integer arithmetic, rounded once. The pattern in Node and Python is in [references/choosing-the-numbers.md](references/choosing-the-numbers.md), section "One conversion function". Follow the project's language.

6. **Post bonuses through the ledger.** Each bonus is an entry with its own kind and a reference that expresses its rule (once per account, once per day, once per code and account), posted through the posting function that the `build-ledger` skill builds. Budgeted bonuses stop at their cap in the database. The `guard-signups` skill covers who may claim them.

7. **Put the check into the project's tests.** One test runs the check on the committed economy file and fails on a violation. One test asserts that the configuration module and the economy file hold the same values. A change to a rate or a bonus then cannot ship without the check.

8. **Schedule the comparison with actuals.** Once a month the measured numbers of the last finished month go through the same check, and a failure reaches a person. See "Plan against actuals" in [references/measuring-from-your-data.md](references/measuring-from-your-data.md).

## Rules that must hold

- The check exits with 0 on the committed economy file.
- The margin with every coin redeemed is not negative. Coins nobody has redeemed yet are still owed.
- Every number in the file has a stated source: a query on the app's data, or the owner, with a date. None comes from another app or an article.
- Each number exists once in the code. A search for the rate, the share and each bonus amount finds the configuration module and nothing else.
- The redeem rate equals the rate, or the difference is in the file and the check has passed with it.
- Conversion uses integers and rounds once. Credits round down, prices round up. No floating point touches an amount.
- A reversal takes back the coins that were stored with the credit, never an amount recomputed with today's numbers.
- Each bonus is a ledger entry whose unique reference enforces how often it can be claimed, and budgeted bonuses are capped in the database.
- Bonuses alone cannot reach the payout minimum.
- The hold in the code is the hold in the file, and it applies to every earning that a network can reverse.
- Boosts do not stack. The larger one applies.
- A change to any number is a commit that changes the economy file and passes the check.
- Text shown to users states what an offer pays. It does not promise what a user will earn.

## Verify

This skill is verified with the economy check and with tests, not with requests against the running app.

Write these tests in the project's own test framework:

- The conversion function, with a table of payouts and expected coins: the smallest payout, a payout with six decimals, a payout that rounds down to zero, a boost, and two steps whose sum differs from the rounded total.
- The price function rounds up: the payout minimum in coins, and one price that is not a whole number of coins before rounding.
- The configuration module equals the economy file, value by value.
- Each bonus: a second claim under the same rule posts nothing, and a claim beyond the budget is refused.
- An earning younger than the hold is not withdrawable, and one older than the hold is.
- The economy file passes: the test imports `checkEconomy` from the script or runs it and asserts on the exit code.

Then run the check by hand, on the plan and on a worst case. `scripts/economy-check.mjs` is in this skill's folder: run it by its full path, `node <skill directory>/scripts/economy-check.mjs`, from the project directory.

```bash
node scripts/economy-check.mjs config/economy.json            # exit code 0
node scripts/economy-check.mjs config/economy.json --json     # the same verdict for CI
node scripts/economy-check.mjs config/economy.worst.json      # see below
```

`economy.worst.json` is a copy with every bonus `takeUpPct` at 100, `redemptionPct` at 100, `averagePayoutUsd` at the minimum and the highest reversal rate of any finished month. Expected:

- The plan exits with 0 and prints "VERDICT: the economy holds."
- The worst case exits with 0 as well, or the owner has confirmed in writing which assumption the margin depends on, and that is recorded in the file.
- A deliberately broken copy (double the largest bonus) exits with 1 and names the rule. This shows the check is wired to the file the code uses.

Done when:

- the tests above pass in the project's test run,
- the check passes on the committed file and the owner has seen the report,
- every warning is either fixed or noted in the file as accepted,
- a search finds no second copy of any number,
- the monthly comparison is scheduled and its failure reaches a person.

## Out of scope / do not

- This skill sets and checks numbers. The code that receives conversions, keeps balances, pays out and pays referral commissions belongs to the `add-offerwall`, `build-ledger`, `add-payouts` and `add-referral-program` skills.
- It does not forecast revenue or user numbers, and nothing it prints is a promise of earnings. It checks whether the numbers it is given fit together.
- Do not use an industry average as an input. Measure, or ask the owner, or use the safe default.
- Do not count unredeemed coins as profit. They are owed until they are redeemed or have expired under a stated rule.
- Do not make the shop cheaper than the rate as a promotion. Run a bonus with a budget instead.
- Do not loosen a target to make the check pass. Targets are the owner's decision, not the agent's.
- Do not change the rate on one side only. Earning, redeeming and existing balances move together or not at all.
- Do not compute rewards in the client, and do not send the share or the margin to it.
- Do not recompute old credits when a number changes. Stored credits keep their coins.

Further reading: [reward-economy-kit](https://github.com/moonetix/reward-economy-kit) implements the integer conversion, bonus windows and reversal arithmetic as a library for JavaScript and PHP, with shared test vectors.
