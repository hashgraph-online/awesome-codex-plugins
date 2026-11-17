# Money arithmetic

**Class id:** `money-arithmetic`

Amounts go wrong in small ways that add up: binary floating point, rounding in the user's favor, a negative number where only positive ones were imagined, a value too large for its column.

## Where to look

Column types in the schema. Every place an amount is parsed from input, multiplied by a rate or a percentage, split between parties, converted between currencies or units, or formatted for a provider.

## Shapes that are bugs

**Floating point storage or math.** `REAL`, `FLOAT`, `DOUBLE` columns, JavaScript numbers holding dollars, Python `float`. `0.1 + 0.2` is not `0.3`, and sums of many such values drift.

**Rounding that can be farmed.**

```js
const usd = Number((coins / 100).toFixed(2));    // 0.5 coins becomes $0.01
```

If an operation accepts a fractional or tiny amount and rounds the payout up, repeating it turns nothing into something. Look at every `round`, `ceil`, `toFixed` and integer division on the way out, and ask which side each one favors.

**Sign and zero.**

```python
def transfer(sender, recipient, amount):
    if sender.balance < amount:          # -400 passes: any balance is greater than a negative number
        raise Insufficient()
    sender.balance -= amount             # subtracting a negative adds
    recipient.balance += amount
```

Check every amount that comes from a request for `> 0`. Check quantities, too.

**Not a number.** `Number("abc")` is `NaN`, and `NaN < price` is false, so a balance check written as `if (balance < price) reject` lets it through. `Infinity`, `"1e9"`, `"0x10"`, a numeric string concatenated instead of added, and `parseInt("12abc")` returning 12 all belong here.

**Range.** A 32-bit integer column overflows at about 2.1 billion minor units. JavaScript integers are exact only up to 2^53. A multiplication can leave the safe range even when its inputs are inside it.

**Units.** Cents in one place and dollars in another. Zero-decimal currencies such as JPY sent as if they had two decimals, or three-decimal currencies such as KWD truncated to two. A provider API that expects minor units receiving major units, or the reverse.

**Splits that do not add up.** A commission computed as `amount * 0.3` and the remainder as `amount * 0.7`, each rounded separately. The parts can exceed the whole or lose a unit on every transaction.

**Percentages applied twice or in the wrong order.** A discount after tax in one code path and before tax in another. A fee computed on the gross in the charge and on the net in the refund.

**Stale or caller-supplied rates.** An exchange rate cached without expiry, or read from the request.

## What correct looks like

- Store amounts as integers in the smallest unit (cents, coins) or as a decimal type with fixed scale. Never as floating point.
- Parse input strictly: an integer within an explicit range, greater than zero. Reject everything else.
- Round once, at a defined point, in a defined direction, and write the rule down. Payouts round down.
- For splits, compute one part and derive the other by subtraction, so the parts always sum to the whole.
- Keep the currency next to every amount and convert with a rate the server fetched.

## How to prove it

```bash
node scripts/probe.mjs send transfer.json --set-body amount=-400 --observe me.json
node scripts/probe.mjs send payout.json --set-body amount=0.5 --observe me.json
node scripts/probe.mjs send spend.json --set-body quantity=1e21
node scripts/probe.mjs send transfer.json --set-body 'amount="abc"'
```

For rounding, show one operation where the value paid out exceeds the value deducted, and state how often it can be repeated. For storage type alone, a trace from the schema line to an arithmetic line is enough.

## Not a bug

- Floating point used only for display, analytics or a progress bar, never written back to a balance or sent to a provider.
- A decimal type (`NUMERIC`, `DECIMAL`, a big-decimal library) used consistently.
- Rounding in the business's favor that is documented and shown to the user.

## Severity

Negative or malformed amounts that move value: critical. Farmable rounding: high, or medium when a minimum amount elsewhere makes it impractical. Floating point storage with no demonstrated loss: medium.
