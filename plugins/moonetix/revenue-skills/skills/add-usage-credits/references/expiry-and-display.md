# Expiry, what the user sees, and where entitlement is decided

Read this when some credits expire (a monthly allowance that resets, promotional credits with an end date, packs with a validity period), and in every build for the last two sections.

## When credits expire

A single balance cannot say which credits are old. Add one row per grant and consume the grants oldest expiry first. Users expect it: the allowance that lapses at the end of the month is used before the pack they paid for.

```sql
CREATE TABLE credit_grants (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES credit_accounts (account_id),
  kind        TEXT NOT NULL,
  ref         TEXT NOT NULL,
  amount      BIGINT NOT NULL CHECK (amount > 0),
  remaining   BIGINT NOT NULL CHECK (remaining >= 0 AND remaining <= amount),
  expires_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, ref)
);

CREATE INDEX credit_grants_spendable ON credit_grants (account_id, expires_at) WHERE remaining > 0;
```

- Every positive ledger entry inserts a grant with the same kind and ref. `expires_at` is NULL for credits that never expire.
- Every debit lowers `remaining` on the grants, soonest expiry first, grants without expiry last.
- The ledger and the cached balance stay exactly as before. The invariant grows by one line: for every account, `SUM(remaining)` equals the balance, or zero when the balance is negative.

MySQL has no `NULLS LAST`: write `ORDER BY expires_at IS NULL, expires_at, id`.

### The entry function with grants

This version replaces the plain entry function once the grants table exists. Python with psycopg 3. Open the connection with `autocommit=True` so that each `with conn.transaction():` block is one real transaction.

```python
class InsufficientCredits(Exception):
    pass


def post_entry(conn, account_id, amount, kind, ref, *, expires_at=None, allow_debt=False, first_grant=None):
    """Call inside `with conn.transaction():`. Returns False when (kind, ref) is already posted.

    InsufficientCredits must leave the transaction block, so that the block rolls back.
    """
    if not isinstance(amount, int) or isinstance(amount, bool) or amount == 0:
        raise ValueError("amount must be a non-zero whole number")
    cur = conn.execute(
        "INSERT INTO credit_ledger (account_id, amount, kind, ref) VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (kind, ref) DO NOTHING",
        (account_id, amount, kind, ref),
    )
    if cur.rowcount == 0:
        return False

    if amount > 0:
        balance = conn.execute(
            "UPDATE credit_accounts SET balance = balance + %s WHERE account_id = %s RETURNING balance",
            (amount, account_id),
        ).fetchone()[0]
        # A grant pays off debt first. Only what is left of it can be spent or can expire.
        remaining = max(0, min(amount, balance))
        conn.execute(
            "INSERT INTO credit_grants (account_id, kind, ref, amount, remaining, expires_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (account_id, kind, ref, amount, remaining, expires_at),
        )
        return True

    if allow_debt:
        cur = conn.execute(
            "UPDATE credit_accounts SET balance = balance - %s WHERE account_id = %s",
            (-amount, account_id),
        )
    else:
        cur = conn.execute(
            "UPDATE credit_accounts SET balance = balance - %s "
            "WHERE account_id = %s AND balance - reserved >= %s",
            (-amount, account_id, -amount),
        )
    if cur.rowcount == 0:
        raise InsufficientCredits()
    consume(conn, account_id, -amount, first_grant)
    return True


def consume(conn, account_id, credits, first_grant=None):
    # The account row was updated just above, so it is locked: no other transaction can
    # walk this account's grants until this one commits.
    grants = conn.execute(
        "SELECT id, remaining FROM credit_grants WHERE account_id = %s AND remaining > 0 "
        "ORDER BY expires_at ASC NULLS LAST, id ASC FOR UPDATE",
        (account_id,),
    ).fetchall()
    # Soonest expiry first. An expiry or a pack refund names its own grant, which then goes first.
    grants.sort(key=lambda grant: grant[0] != first_grant)
    for grant_id, remaining in grants:
        if credits == 0:
            break
        take = min(credits, remaining)
        conn.execute("UPDATE credit_grants SET remaining = remaining - %s WHERE id = %s", (take, grant_id))
        credits -= take
    # Anything left over is debt: the balance is below zero and no grant holds it.


def refund_pack(conn, account_id, order_id, credits):
    grant = conn.execute(
        "SELECT id FROM credit_grants WHERE kind = 'purchase' AND ref = %s", (order_id,)
    ).fetchone()
    return post_entry(
        conn, account_id, -credits, "purchase_refund", order_id,
        allow_debt=True, first_grant=grant[0] if grant else None,
    )
```

A reservation does not touch grants. Grants are consumed when the reservation is committed and the `usage` entry is posted.

Two details that are easy to get wrong:

- **Returned credits.** When credits expire, run work that can fail through reserve and commit even if its cost is fixed. A failure then releases the reservation and no grant was touched. A `usage_refund` posted after the fact becomes a new grant: pass it the expiry of the grant it came from (or the end of the current allowance period), otherwise a failing job turns expiring credits into permanent ones.
- **Refunded packs.** `refund_pack` first empties the grant that the pack created (same kind `purchase`, same order id), then takes the part that was already spent from the other grants, soonest expiry first. What is still missing becomes debt.

### Monthly allowances

- **Reset (the default).** Grant the allowance with `expires_at` set to the end of the paid period. The expiry job removes what was not used, and the renewal event grants the next one. Take the period end from the provider's verified event. Check the provider's documentation for the field that carries it.
- **Roll over.** Grant without expiry, or with an expiry several periods ahead. If there is a ceiling, grant `min(allowance, ceiling - unexpired allowance credits)` and skip the grant when that is zero.
- **Plan change in the middle of a period.** Decide once and write it down: the usual rule is that an upgrade grants the difference at once and a downgrade takes effect at the next renewal.
- **Cancelled or unpaid subscription.** No renewal event, no grant. The last allowance expires with its period.

### The expiry job

Expiry is applied by a job, not by the clock: a grant is spendable until the job posts its `expiry` entry. The job posts through the same function as every other change, so the balance still has one writer. Run the job every few minutes to every hour, and show expiry as a date, not as a time of day.

```python
def expire_grants(conn, limit=500):
    due = conn.execute(
        "SELECT id, account_id FROM credit_grants "
        "WHERE remaining > 0 AND expires_at <= now() ORDER BY expires_at LIMIT %s",
        (limit,),
    ).fetchall()
    expired = 0
    for grant_id, account_id in due:
        try:
            with conn.transaction():
                # Lock the account before reading the grant, the order every other writer uses.
                conn.execute("SELECT 1 FROM credit_accounts WHERE account_id = %s FOR UPDATE", (account_id,))
                row = conn.execute(
                    "SELECT remaining FROM credit_grants WHERE id = %s AND remaining > 0", (grant_id,)
                ).fetchone()
                if row is not None:
                    post_entry(conn, account_id, -row[0], "expiry", str(grant_id), first_grant=grant_id)
                    expired += 1
        except InsufficientCredits:
            # Part of this grant is reserved by running work. It is not expired from under the
            # job: the grant comes up again on the next run, after the reservation has settled.
            continue
    return expired
```

Paid credits that expire can fall under consumer protection or stored value rules in some countries. Whether purchased credits expire, and after how long, is the owner's decision, not a technical default.

## What to show the user

One endpoint returns everything the interface needs. All of it is read from the server's tables at request time.

```json
{
  "available": 1840,
  "in_use": 60,
  "expiring": [{ "credits": 340, "on": "2026-03-31" }],
  "allowance": { "per_period": 2000, "renews_on": "2026-03-31" }
}
```

```sql
SELECT balance, reserved FROM credit_accounts WHERE account_id = $1;

SELECT expires_at, SUM(remaining) AS credits
  FROM credit_grants
 WHERE account_id = $1 AND remaining > 0 AND expires_at IS NOT NULL
 GROUP BY expires_at
 ORDER BY expires_at
 LIMIT 3;
```

- **Available** is `balance - reserved`, shown as zero when it is negative. Credits reserved by running work are "in use", not gone and not spendable.
- **Before the work:** the cost when it is fixed, the maximum when it is not ("up to 12 credits"). **After the work:** what was charged.
- **History** comes from the ledger: one line per entry with date, description and signed amount. For reserved work show the committed `usage` entry only. Released reservations never reach the history.
- **Not enough credits:** HTTP 402 with a machine-readable body, such as `{"error": "insufficient_credits", "needed": 12, "available": 7}`, and a way to top up. Do not start the work and fail halfway.
- **Debt** (a refund after the credits were spent): show zero available and say why, in words.
- **Low balance and upcoming expiry** deserve a notice before they bite, not after.
- After a spend, show the balance the server returned. Do not subtract in the browser and hope the two agree.

### AI usage on the credits screen

Model calls add a few things to show. The pricing and the bound behind them are in [ai-pricing.md](ai-pricing.md).

- **Before a call:** "up to N credits", the price of the bound. Before an agent run: the run's cap, which the user accepts once.
- **During a stream:** a live counter is a display the client computes from what it received. The charge is what the server commits at the end.
- **After a call:** what was charged, and on request the token counts per kind from the stored usage. A cut stream says "charged for the part delivered".
- **History:** one line per call, or per agent run instead of per step, with the model's display name and the charged amount.
- **Price changes:** announce a new price version before its `effective_from`. Calls that started before it keep the old prices, so the screen never shows a charge that changed afterwards.
- **Refused for credits:** the 402 body carries the bound that was needed, so the interface can offer a shorter answer, a smaller model, or a top-up.

## Entitlement is decided on the server

The client belongs to the user. Anything it holds or sends can be changed.

- The metered work runs on the server, after the debit or the reservation has succeeded. If a mobile or desktop app calls a paid third-party API directly with a key shipped in the app, move that call behind your server first: there is nothing to meter otherwise, and the key is public.
- The request names the feature and carries the input. It never carries a cost, a credit amount, a plan, an account id or an "is premium" flag that the server believes.
- The balance in the interface is a display. Greying out a button when it reads zero is a courtesy. The 402 from the server is the control.
- A balance in local storage, in a cookie the client can write, or in a token claim that is not re-checked against the database is the same display, not a second source of truth.
- Purchases made through an app store are granted after the server has validated the purchase with the store, under the store's transaction id as the ref.
- Free-tier limits ("20 runs a day") are enforced by the same mechanism: a scheduled grant under a dated ref, or a counter row updated with a condition. Never a counter the client keeps.
