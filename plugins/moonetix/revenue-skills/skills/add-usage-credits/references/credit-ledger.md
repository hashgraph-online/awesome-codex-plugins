# Credit ledger: schema, grants and spends with a known cost

Every change to a credit balance is one row in an append-only ledger plus one update of a cached balance, in the same transaction. A unique key on the ledger turns a repeated grant or a retried spend into a no-op. The balance is lowered by one conditional statement, so parallel requests cannot spend the same credits.

## Schema

The whole schema is in `assets/credits-schema.sql`. Every build needs these two tables (reservations and expiring grants are covered in the other references):

```sql
CREATE TABLE credit_accounts (
  account_id  BIGINT PRIMARY KEY,
  balance     BIGINT NOT NULL DEFAULT 0,
  reserved    BIGINT NOT NULL DEFAULT 0 CHECK (reserved >= 0)
);

CREATE TABLE credit_ledger (
  id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES credit_accounts (account_id),
  amount      BIGINT NOT NULL CHECK (amount <> 0),
  kind        TEXT NOT NULL,
  ref         TEXT NOT NULL,
  actor       TEXT NOT NULL DEFAULT 'system',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, ref)
);
```

- An **account** is whoever owns the credits: a user, a team, a workspace. Create its `credit_accounts` row when the owner is created.
- `balance` is a cache of `SUM(amount)` over the account's ledger rows. `reserved` is the sum of its open reservations. What can be spent right now is `balance - reserved`, called **available** below.
- Amounts are whole credits. No floats, no decimals. If a price needs fractions, store a smaller unit.
- There is no `CHECK (balance >= 0)`. A refunded purchase whose credits are already spent must be able to push the balance below zero. Spending is stopped by the conditional update instead.
- **With a ledger already in place** whose unit is the credit (for example one built with the `build-ledger` skill): keep its tables and its posting function, and skip the two tables above. Add the `reserved` column to its account table and change the debit condition in the posting function from `balance >= amount` to `balance - reserved >= amount`.
- **Without one,** these two tables, the `entry` function below and the reconcile queries are the minimum. Credits never ship as a bare counter column that handlers update. Ledger rows are never updated or deleted: a correction is a new entry.

Each entry has a kind and a reference. Together they are the idempotency key.

| Kind | Sign | Ref | Posted when |
| --- | --- | --- | --- |
| `purchase` | + | order id | the payment provider's verified event marks the order paid |
| `plan_allowance` | + | `<subscription id>:<period start>` | a verified renewal starts a paid period |
| `promo` | + | `<code>:<account id>` | a code is redeemed or a campaign grants credits |
| `usage` | - | `<account id>:<idempotency key>`, or the reservation id | metered work is charged |
| `usage_refund` | + | the ref of the usage it returns | work with a known cost failed after the debit |
| `purchase_refund` | - | order id | the payment was refunded or charged back |
| `expiry` | - | grant id | unused credits passed their expiry date |
| `adjustment` | + or - | support request id | staff corrects a balance, with a name and a reason in `actor` |

### What differs in MySQL and SQLite

- **MySQL 8:** `BIGINT AUTO_INCREMENT` for ids, `DATETIME(6)` in UTC for times, `VARCHAR(191)` with a binary collation for `kind` and `ref` (the default collations ignore case, so `tx_AbC` and `tx_abc` would collide). There is no `ON CONFLICT`: use a plain `INSERT` and treat error 1062 (duplicate key) as already posted. Avoid `INSERT IGNORE`, which hides other errors too. Lock the account row with `SELECT ... FOR UPDATE` before inserting a ledger or reservation row: the foreign key check takes a shared lock on it, and two transactions that both hold one and then update the row deadlock. There is no `RETURNING`: select under the lock, then update. Partial indexes become plain indexes. `now() + make_interval(secs => ?)` becomes `NOW(6) + INTERVAL ? SECOND`.
- **SQLite:** `INTEGER PRIMARY KEY` for ids, times as ISO text or integer seconds. `ON CONFLICT ... DO NOTHING` and `RETURNING` work as shown (3.35 or newer). There is no `FOR UPDATE`: open every writing transaction with `BEGIN IMMEDIATE` so writers queue up.

## One function writes the balance

Node with node-postgres. node-postgres returns `BIGINT` columns as strings: convert with `Number()` before doing arithmetic. Credit amounts stay far below 2^53.

```js
export class InsufficientCredits extends Error {}

export async function withTransaction(pool, work) {
  const tx = await pool.connect();
  try {
    await tx.query('BEGIN');
    const result = await work(tx);
    await tx.query('COMMIT');
    return result;
  } catch (err) {
    await tx.query('ROLLBACK');
    throw err;
  } finally {
    tx.release();
  }
}

// Call inside withTransaction. Returns true when the entry was posted and false when
// (kind, ref) is already in the ledger. InsufficientCredits has to leave withTransaction
// as an exception, because the rollback is what removes the row inserted just before it.
export async function entry(tx, { accountId, amount, kind, ref, actor = 'system', allowDebt = false }) {
  if (!Number.isSafeInteger(amount) || amount === 0) throw new TypeError('amount must be a non-zero whole number');
  const inserted = await tx.query(
    `INSERT INTO credit_ledger (account_id, amount, kind, ref, actor) VALUES ($1, $2, $3, $4, $5)
     ON CONFLICT (kind, ref) DO NOTHING`,
    [accountId, amount, kind, String(ref), actor],
  );
  if (inserted.rowCount === 0) return false;
  const moved =
    amount > 0 || allowDebt
      ? await tx.query('UPDATE credit_accounts SET balance = balance + $2 WHERE account_id = $1', [accountId, amount])
      : await tx.query(
          'UPDATE credit_accounts SET balance = balance - $2 WHERE account_id = $1 AND balance - reserved >= $2',
          [accountId, -amount],
        );
  if (moved.rowCount === 0) throw new InsufficientCredits();
  return true;
}
```

The debit is one statement: the database compares and subtracts under the row lock, and a second request waits, sees the new balance and changes zero rows. Never read the balance into the application, compare there, and write the result back.

`allowDebt` is for reversals only (a refund, a chargeback, a charge for work already delivered). No path a user can call directly passes it.

## Granting credits

Credits enter in three ways. Each is posted by the server on evidence it checked, under a ref that the same evidence always produces.

**Purchased packs.** Create the order on the server from the server's own pack table. Grant inside the handler for the payment provider's verified event, in the same transaction that marks the order paid. The redirect back from checkout shows a "thank you" page and grants nothing.

**Plan allowances.** Grant when the provider's verified renewal event starts a paid period, never from a calendar job alone: a renewal that failed must not refill. The ref carries the period, so the event delivered twice grants once, and next month's event grants again. For a free plan with a monthly allowance, a scheduled job posts under `free:<account id>:<YYYY-MM>`.

**Promotional grants.** One per account per code or campaign, by the ref. Enforce a total cap for the code in the same transaction (a counter row updated with a condition).

```js
// The order row was written at checkout from the server's price list. Its credits column,
// not anything in the event or the request, decides how much is granted.
export function grantPack(tx, order) {
  return entry(tx, { accountId: order.account_id, amount: Number(order.credits), kind: 'purchase', ref: order.id });
}

export function grantAllowance(tx, { accountId, subscriptionId, periodStart, credits }) {
  return entry(tx, { accountId, amount: credits, kind: 'plan_allowance', ref: `${subscriptionId}:${periodStart}` });
}

export function grantPromo(tx, { accountId, code, credits }) {
  return entry(tx, { accountId, amount: credits, kind: 'promo', ref: `${code}:${accountId}` });
}
```

When a pack is refunded or charged back, post `purchase_refund` for the amount the `purchase` entry granted, under the same order id, with `allowDebt: true`. An account in debt cannot spend until it is topped up.

## The price list lives on the server

The client says what it wants done. The server decides what that costs.

```js
export const COSTS = { export_pdf: 2, image_standard: 5, image_large: 12 };
```

Read the cost with `Object.hasOwn(COSTS, feature)`, reject unknown features, and ignore any `cost`, `credits` or `price` field in the request. If prices change, change this table. Entries already in the ledger keep the amount that was charged.

## Spending when the cost is known up front

Order of work: take the credits, do the work, give the credits back if the work fails. Never the other way round.

A client that retries (a double click, a timeout, a flaky connection) must not pay twice. The client creates one key per user action and sends it in an `Idempotency-Key` header on every attempt. The server scopes it to the account and uses it as the ledger ref.

```js
const IDEMPOTENCY_KEY = /^[A-Za-z0-9_-]{8,64}$/;

export async function spend(pool, { accountId, cost, ref }) {
  try {
    const posted = await withTransaction(pool, (tx) => entry(tx, { accountId, amount: -cost, kind: 'usage', ref }));
    return posted ? 'charged' : 'repeated';
  } catch (err) {
    if (err instanceof InsufficientCredits) return 'insufficient';
    throw err;
  }
}

export function returnSpend(pool, { accountId, cost, ref }) {
  return withTransaction(pool, (tx) => entry(tx, { accountId, amount: cost, kind: 'usage_refund', ref }));
}

// Express-style handler. findExport and renderExport are the project's own functions;
// the export row is stored under the same ref, so a retry can find the first result.
export async function exportPdf(req, res) {
  const accountId = req.user.accountId;
  const key = req.get('Idempotency-Key') ?? '';
  if (!IDEMPOTENCY_KEY.test(key)) return res.status(400).json({ error: 'idempotency_key_required' });
  const ref = `${accountId}:${key}`;
  const cost = COSTS.export_pdf;

  const outcome = await spend(pool, { accountId, cost, ref });
  if (outcome === 'insufficient') return res.status(402).json({ error: 'insufficient_credits', needed: cost });
  if (outcome === 'repeated') return res.json(await findExport(ref));

  try {
    res.json(await renderExport(accountId, req.body.documentId, ref));
  } catch {
    await returnSpend(pool, { accountId, cost, ref });
    res.status(502).json({ error: 'export_failed_credits_returned' });
  }
}
```

- A repeated key answers with the state of the first attempt: the finished result, "still running", or "failed, credits returned". It never runs the work again and never debits again.
- The `usage_refund` shares the ref of its `usage`, so the unique key lets it post once.
- First-party clients always send the key. For public API clients either require it, or create one on the server when it is missing and accept that such a request has no retry protection.
- The account comes from the session or the API key, never from the request body.

## Parallel requests

Ten requests at once against a balance that covers three: three change a row and proceed, seven change none and get 402. Nothing in the application serializes them and nothing needs to. The same holds across several app servers, because the decision is made by the database.

Things that reopen the race, all of which a reviewer should reject:

- `SELECT balance`, an `if` in the application, then `UPDATE ... SET balance = <computed value>`.
- An ORM `load, modify, save` on the account row.
- A balance kept in a cache or an in-process variable and written back later.
- Doing the work first and debiting afterwards.

## Reconcile

Run these on a schedule and alert when either returns a row. They work on all three databases.

```sql
SELECT a.account_id, a.balance, COALESCE(SUM(l.amount), 0) AS ledger_total
  FROM credit_accounts a
  LEFT JOIN credit_ledger l ON l.account_id = a.account_id
 GROUP BY a.account_id, a.balance
HAVING a.balance <> COALESCE(SUM(l.amount), 0);

SELECT a.account_id, a.reserved, COALESCE(SUM(r.amount), 0) AS open_total
  FROM credit_accounts a
  LEFT JOIN credit_reservations r ON r.account_id = a.account_id AND r.status = 'open'
 GROUP BY a.account_id, a.reserved
HAVING a.reserved <> COALESCE(SUM(r.amount), 0);
```

## Moving an existing balance into the ledger

If the app already has a credits column that code updates directly, give every account an opening entry so that the ledger explains the balance from day one, then route every writer through `entry`.

```sql
INSERT INTO credit_accounts (account_id, balance)
SELECT id, credits FROM users;

INSERT INTO credit_ledger (account_id, amount, kind, ref, actor)
SELECT id, credits, 'opening_balance', CAST(id AS TEXT), 'migration' FROM users WHERE credits <> 0;
```

On MySQL write `CAST(id AS CHAR)`. Search the codebase for every statement that writes the old column. One writer left behind makes the reconcile query fail, which is how you find it.
