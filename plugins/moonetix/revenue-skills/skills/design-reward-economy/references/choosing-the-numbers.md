# Choosing the numbers

A rewards economy is a short list of numbers. Each one controls a different thing, and most mistakes come from changing one while believing it controls another. This file goes through them in the order they should be decided.

| Number | What it controls | What it does not control |
| --- | --- | --- |
| Rate (coins per dollar) | The size of the numbers users see, and how much rounding costs | The margin |
| User share | The margin on every conversion | How large rewards look |
| Bonuses | How much of the margin is given back, and to whom | Revenue |
| Redeem rate | What a coin is worth on the way out | Nothing else, which is why it should equal the rate |
| Payout minimum and fees | The fee per dollar paid, and how soon a user sees money | The share |
| Hold | How many reversals can be taken back before the money is gone | How many reversals happen |

The formula for one credit:

```text
coins = payout x rate x share x (1 + bonus), rounded down once
```

## Rate

Pick the rate from the smallest payout the app will credit, not from the largest.

Rounding down costs up to one coin per credit. On a reward of 5 coins that is up to 20 percent. On a reward of 100 coins it is under 1 percent. So the smallest reward should be at least 100 coins:

```text
smallest payout x rate x share >= 100
```

With a smallest payout of $0.05 and a 50 percent share, a rate of 1,000 gives 25 coins (too coarse) and 10,000 gives 250. If numbers that large do not suit the audience, keep the rate and store decimals instead: a currency with two or three decimal places is still an integer in the database, counted in its smallest unit.

A payout so small that it rounds to zero coins must not be shown as an offer at all. The check reports this as `smallest-reward-is-zero`.

The rate does not change the margin. Doubling it doubles every reward and every price.

## User share

The share is what is left of a dollar of revenue after everything else is paid for. Work it out from the costs, do not pick it from a competitor's landing page.

```text
share <= 1 - target margin
           - reversals that are never collected
           - bonuses, as a part of revenue
           - payout fees the app pays
           - other costs that grow with revenue
```

Every term is the app's own figure. The target margin is the owner's decision. The others come from the ledger and the payout provider's invoices (see measuring-from-your-data.md). When the app is new and has no history, enter the owner's planning figures, mark them as planned in the file, and replace them after the first full month.

The check prints the result of this arithmetic as "highest user share" for the target margin, and "user share at zero margin" as the point where the app stops earning anything.

## One conversion function

Dollars are held as whole micro-dollars and coins as whole units. The multiplication is exact, and one division rounds. The share and the bonus are basis points (6000 is 60 percent), so no fraction appears anywhere.

```js
const MICROS = 1_000_000n;

// "0.85" becomes 850000n. Anything that is not a plain decimal with up to 6 places is refused.
export function parseUsdMicros(text) {
  const m = /^(\d{1,12})(?:\.(\d{1,6}))?$/.exec(String(text));
  if (!m) throw new RangeError(`not a dollar amount: ${text}`);
  return BigInt(m[1]) * MICROS + BigInt((m[2] ?? '').padEnd(6, '0'));
}

export function coinsForPayout(payoutMicros, { coinsPerDollar, userShareBps, bonusBps = 0 }) {
  const product = payoutMicros * BigInt(coinsPerDollar) * BigInt(userShareBps) * BigInt(10_000 + bonusBps);
  return Number(product / (MICROS * 10_000n * 10_000n));
}

// The coin price of a dollar amount. Prices round up, so nothing is sold below cost.
export function coinsForUsd(usdMicros, { redeemCoinsPerDollar }) {
  return Number((usdMicros * BigInt(redeemCoinsPerDollar) + MICROS - 1n) / MICROS);
}
```

The same in Python, where integers are arbitrary precision:

```python
import re

MICROS = 1_000_000
_USD = re.compile(r"(\d{1,12})(?:\.(\d{1,6}))?")


def parse_usd_micros(text: str) -> int:
    m = _USD.fullmatch(text)
    if not m:
        raise ValueError(f"not a dollar amount: {text!r}")
    return int(m.group(1)) * MICROS + int((m.group(2) or "").ljust(6, "0"))


def coins_for_payout(payout_micros: int, coins_per_dollar: int, user_share_bps: int, bonus_bps: int = 0) -> int:
    return payout_micros * coins_per_dollar * user_share_bps * (10_000 + bonus_bps) // (MICROS * 10_000 * 10_000)


def coins_for_usd(usd_micros: int, redeem_coins_per_dollar: int) -> int:
    return -(-usd_micros * redeem_coins_per_dollar // MICROS)
```

`coinsForPayout(parseUsdMicros('0.85'), { coinsPerDollar: 1000, userShareBps: 6000, bonusBps: 1000 })` is 561: 0.85 x 1000 x 60% x 110%.

Rules for rounding:

- **Credits round down.** Users never receive more than the share, and a stream of tiny credits cannot be farmed for the rounding gain.
- **Prices round up.** The coin price of a payout or a gift card never sells a dollar for less than a dollar's worth of coins.
- **Round once, at the end.** Rounding `payout x rate` and then applying the share gives different results.
- **Each credit is rounded on its own.** An offer with several steps is several credits. Their sum can differ by a coin or two from the rounded total. That is expected.
- **If a network computes the reward for you** and sends it signed, credit what it sent. Use this function for previews and for checking that the network's settings match the economy file.

## Bonuses

A bonus is paid from the app's share. Revenue does not change; users get more coins for it. Every bonus therefore has a budget, and the budget is part of the economy file.

| Bonus | What it costs per month | What keeps it inside the budget |
| --- | --- | --- |
| Sign-up | new users x take-up x coins | Credited once per account, and only after the first real earning |
| Daily check-in | active users x 30 x daily take-up x coins | One ledger entry per account and day |
| Streak | active users x take-up x coins | One entry per account and streak period |
| Promo codes | the monthly coin budget | A cap on redemptions, enforced in the database |
| Earning boost | boost x the part of earnings credited while it runs | A start and an end time, checked when the credit is posted |
| Referral commission | commission x the part of earnings made by referred users | Paid on earned rewards only, and reversed with them |

Points that are easy to get wrong:

- **A boost multiplies the share.** A 100 percent boost on a 50 percent share pays out the whole payout. The check counts it by `coveragePct`, the part of all earnings credited while the boost applies.
- **Boosts do not stack.** When two are active, apply the larger one. Stacked boosts are the usual way an economy goes above 100 percent without anyone deciding it.
- **Evaluate the boost at the time of the credit,** not when the user started the offer, and store the coins that were credited. A reversal takes back the stored amount, never a value recomputed with today's settings.
- **Bonuses alone must not reach the payout minimum.** If an account that completes nothing can collect the minimum in sign-up and daily bonuses, the app pays people to create accounts. The check reports this as `bonus-only-payout`. Fixes: smaller bonuses, a higher minimum, or bonuses that are credited only after real earnings (`requiresEarning` in the file).
- **Take-up is measured, not guessed.** Until there is data, use 100 percent. An economy that only holds if few people claim a bonus does not hold.
- **Each bonus is a ledger entry** with a kind of its own and a reference that expresses its rule: `<account>` for once per account, `<account>:<date>` for once per day, `<code>:<account>` for once per code and account. The unique key then enforces the rule.

## Redeem rate

The redeem rate is how many coins buy one dollar at cash-out. Keep it equal to the rate. If the shop sells a dollar for fewer coins than a dollar of payout creates at a 100 percent share, the real share is `share x rate / redeem rate`, and the stated share is fiction. A "discounted gift card" is a bonus under another name: give it a budget and enter it as one.

A redeem rate above the rate (coins buy less than they cost) lowers the real share. It is honest only when the app says so where users can see it.

## Payout minimum and fees

Set the minimum in dollars and convert it with the price function, which rounds up.

- **Fixed fees decide the minimum.** A provider fee of $0.25 on a $1 payout is 25 percent of it. On $10 it is 2.5 percent. The check prints the fee at the minimum payout and at the average payout.
- **Decide who pays.** If the app pays, the fee is a cost and belongs in the share calculation. If the user pays, show the fee before the user confirms, and deduct it from what is sent, not from the balance on top.
- **The minimum must be reachable.** The check prints how many days an average active user needs to reach it. Averages hide that most users earn less than the average, so treat the figure as the best case and let the owner set `maxDaysToMinimumPayout`.
- **Prices are computed, not typed.** A price list of gift cards is the face value run through the price function. A hand-typed list drifts from the redeem rate.

## Hold

A hold is the time between a credit and the day it can be cashed out. It exists because networks take conversions back, sometimes weeks later. A reversal that arrives while the coins are still held costs nothing. One that arrives after the payout is a loss unless the user earns the debt back.

Size the hold from the app's own reversal data: the arrival curve says what part of all reversals had arrived within N days of the credit. The owner names the part to catch, and the hold is the day the curve reaches it. The check does this arithmetic (`minReversalsInsideHoldPct`, and "needs N days" in the violation message).

- A longer hold catches more reversals and makes users wait longer for their first payout. Both effects are printed; the owner chooses.
- The hold applies to earnings that can be reversed. It does not need to apply to spending inside the app when nothing bought there can be turned into money.
- A hold shorter than the time the networks take to pay the app means users are paid before the app is. The check prints the cash this needs (`payment-gap-not-funded`).
- Show held coins as pending, with the date they become available. A balance that cannot be withdrawn, with no explanation, is a support ticket.
- A hold does not remove late reversals. Keep the rule that a reversal may take the balance below zero and that payouts are refused while it is.

## Unspent balances

Every coin in a user's balance is money the app owes. The total is a liability, and it grows every month in which users earn more than they redeem.

- Count unredeemed coins as owed in full. The check computes the margin twice: with the measured redemption rate, and with every coin redeemed. The second number must not be negative.
- Money that was earned for coins still in balances is not profit yet. Keep cash, or receivables from the networks, at least equal to the value of all balances.
- Whether old balances may expire depends on the app's terms and on the rules for stored value where it operates. That is the owner's decision. Until coins have expired under a stated rule, they stay in the liability.

## Changing a number later

- Change the economy file first, run the check, then change the code. The file is the record of why.
- New rates apply to new credits. Stored credits keep the coins they were given.
- When the rate changes, decide what happens to existing balances: keep the redeem rate (old coins keep their value) or convert every balance by the ratio of old to new in one migration that posts ledger entries. Never change only the shop price.
- Announce a lower share or a higher minimum before it applies. Users notice, and the terms of the app usually require notice.
