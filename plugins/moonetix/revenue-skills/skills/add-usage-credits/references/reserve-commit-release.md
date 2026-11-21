# Reserve, commit, release

Some work has a cost that is known only when it is done: model tokens, minutes of transcription, rows processed, pages rendered. Charging afterwards with no reservation lets parallel jobs start on the same credits and finish with nothing left to pay for them. Charging a guess up front is wrong in both directions. The pattern: reserve an upper bound before the work starts, commit the real cost when it ends, and release whatever was not used.

## The lifecycle

| Step | When | Account | Reservation |
| --- | --- | --- | --- |
| reserve | before the work starts | `reserved` rises by the upper bound, only if `balance - reserved` covers it | `open` |
| commit | the work finished and the cost is known | `reserved` falls by the upper bound, one `usage` entry lowers `balance` by the real cost | `committed` |
| release | the work failed or was cancelled before anything was delivered | `reserved` falls by the upper bound, `balance` untouched | `released` |
| expire | neither happened before `expires_at` | the same as release, done by a scheduled job | `released` |

The balance does not move until commit, so the ledger shows real usage only. Each reservation is settled once: the status change is a guarded transition, and a second commit or release finds nothing to do.

```sql
CREATE TABLE credit_reservations (
  id          TEXT PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES credit_accounts (account_id),
  feature     TEXT NOT NULL,
  amount      BIGINT NOT NULL CHECK (amount > 0),
  used        BIGINT CHECK (used >= 0 AND used <= amount),
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'committed', 'released')),
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  settled_at  TIMESTAMPTZ
);

CREATE INDEX credit_reservations_open ON credit_reservations (expires_at) WHERE status = 'open';
```

The reservation id is `<account id>:<idempotency key>` for work a client starts, so a retried request finds the reservation it made the first time. For work the server starts on its own (a scheduled job, a queue consumer) use the job id.

## The upper bound

- **Bound the work, then price the bound.** The limit that goes into the reservation is the same limit that is passed to the work: maximum output tokens, maximum duration, maximum rows. A bound the work can exceed is a guess.
- **Price it from the server's price list,** with integer arithmetic, rounding up once at the end.
- **Overestimate what you cannot measure exactly.** If the input size is an estimate, take a ceiling. The difference comes back at commit.
- **If the bound is not affordable,** refuse with 402 before any work starts and say how much is needed. A product that can give a shorter result may instead lower the work's limit to what `balance - reserved` covers. Never start the work unreserved.

## Reserve, commit and release

Node with node-postgres. `withTransaction`, `entry` and `InsufficientCredits` are the ledger functions from [credit-ledger.md](credit-ledger.md).

```js
import { InsufficientCredits, entry, withTransaction } from './credit-ledger.mjs';

// Returns true when the credits were reserved now, false when this id was reserved before
// (a retry). Throws InsufficientCredits, and keeps no row, when available credits are short.
export async function reserve(pool, { accountId, reservationId, feature, amount, ttlSeconds }) {
  if (!Number.isSafeInteger(amount) || amount <= 0) throw new TypeError('amount must be a positive whole number');
  return withTransaction(pool, async (tx) => {
    const created = await tx.query(
      `INSERT INTO credit_reservations (id, account_id, feature, amount, expires_at)
       VALUES ($1, $2, $3, $4, now() + make_interval(secs => $5))
       ON CONFLICT (id) DO NOTHING`,
      [reservationId, accountId, feature, amount, ttlSeconds],
    );
    if (created.rowCount === 0) return false;
    const held = await tx.query(
      'UPDATE credit_accounts SET reserved = reserved + $2 WHERE account_id = $1 AND balance - reserved >= $2',
      [accountId, amount],
    );
    if (held.rowCount === 0) throw new InsufficientCredits();
    return true;
  });
}

export async function commit(pool, reservationId, actualCost) {
  if (!Number.isSafeInteger(actualCost) || actualCost < 0) throw new TypeError('actualCost must be a whole number');
  return withTransaction(pool, async (tx) => {
    const found = await tx.query(
      'SELECT account_id, amount, status FROM credit_reservations WHERE id = $1 FOR UPDATE',
      [reservationId],
    );
    const row = found.rows[0];
    if (!row || row.status === 'committed') return { charged: 0, repeated: true };
    const bound = Number(row.amount);
    const used = Math.min(actualCost, bound);
    // Released and now committed: the sweeper gave up on work that finished after all.
    const late = row.status === 'released';
    if (late && used === 0) return { charged: 0, repeated: true };

    await tx.query(
      `UPDATE credit_reservations SET status = 'committed', used = $2, settled_at = now() WHERE id = $1`,
      [reservationId, used],
    );
    if (!late) {
      await tx.query('UPDATE credit_accounts SET reserved = reserved - $2 WHERE account_id = $1', [row.account_id, bound]);
    }
    if (used > 0) {
      // The reservation set these credits aside, so the charge always lands. allowDebt covers
      // the rare account whose balance was taken by a refund while the work was running.
      await entry(tx, { accountId: row.account_id, amount: -used, kind: 'usage', ref: reservationId, allowDebt: true });
    }
    return { charged: used, late, overage: Math.max(0, actualCost - bound) };
  });
}

export async function release(pool, reservationId) {
  return withTransaction(pool, async (tx) => {
    const settled = await tx.query(
      `UPDATE credit_reservations SET status = 'released', used = 0, settled_at = now()
        WHERE id = $1 AND status = 'open'
        RETURNING account_id, amount`,
      [reservationId],
    );
    if (settled.rowCount === 0) return false;
    const { account_id: accountId, amount } = settled.rows[0];
    await tx.query('UPDATE credit_accounts SET reserved = reserved - $2 WHERE account_id = $1', [accountId, amount]);
    return true;
  });
}
```

- `commit` charges at most the reserved amount. A non-zero `overage` means the work exceeded its bound: log it and fix the bound. Do not bill the user more than was reserved.
- `commit` with a cost of zero settles the reservation and posts no entry.
- On SQLite drop `FOR UPDATE` and open the transaction with `BEGIN IMMEDIATE`. On MySQL replace `RETURNING` in `release` with a `SELECT ... FOR UPDATE` followed by the update, as `commit` does.

## Around the work

```js
const RATES = { inputPer1k: 1, outputPer1k: 4 }; // credits per 1,000 tokens, from the server's price list
const MAX_OUTPUT_TOKENS = 1024;
const WORK_TIMEOUT_MS = 120_000;

export function creditsFor({ inputTokens, outputTokens }) {
  return Math.max(1, Math.ceil((inputTokens * RATES.inputPer1k + outputTokens * RATES.outputPer1k) / 1000));
}

// countTokens, callModel and findGeneration are the project's own functions. callModel
// returns the usage the model provider reported, as { inputTokens, outputTokens }.
export async function generate(pool, { accountId, idempotencyKey, prompt }) {
  const reservationId = `${accountId}:${idempotencyKey}`;
  const bound = creditsFor({ inputTokens: countTokens(prompt), outputTokens: MAX_OUTPUT_TOKENS });

  const fresh = await reserve(pool, {
    accountId,
    reservationId,
    feature: 'generate',
    amount: bound,
    ttlSeconds: WORK_TIMEOUT_MS / 1000 + 60,
  });
  if (!fresh) return findGeneration(reservationId);

  let result;
  try {
    result = await callModel({ prompt, maxOutputTokens: MAX_OUTPUT_TOKENS, timeoutMs: WORK_TIMEOUT_MS });
  } catch (err) {
    await release(pool, reservationId);
    throw err;
  }
  const charge = await commit(pool, reservationId, creditsFor(result.usage));
  return { ...result, credits: charge.charged };
}
```

The route handler maps `InsufficientCredits` to 402 with the bound in the body, the same way as for a spend with a known cost. A repeated key returns the first attempt's state and starts nothing.

Where the real cost comes from differs by provider. Check the provider's documentation for where usage is reported, and whether it is reported for streamed, cancelled and failed requests. Price the provider's reported usage, not your own count, whenever it is available.

## Streaming, cancels and partial results

- **Nothing was delivered** (the call failed, timed out, or was refused): release everything.
- **Part was delivered** (the user stopped a stream, the connection dropped): stop the work if the provider allows it, then commit what was used. If the provider reports no usage for an interrupted call, commit your own count of what was sent to the user.
- **Settle on the server, in a path that always runs.** A commit that happens only when the browser reads the last chunk never happens for the users who close the tab.
- **Record the cost before committing** when the commit can fail separately from the work (another service, a queue). Store the reported usage on the job row first, so the commit can be retried from it.

## Stale reservations

A process can die between reserve and commit. Without a sweeper its credits stay reserved forever.

```js
export async function releaseStale(pool, limit = 200) {
  const stale = await pool.query(
    `SELECT id FROM credit_reservations WHERE status = 'open' AND expires_at < now() ORDER BY expires_at LIMIT $1`,
    [limit],
  );
  let released = 0;
  for (const { id } of stale.rows) {
    if (await release(pool, id)) released += 1;
  }
  return released;
}
```

- Run it every minute or so from the project's scheduler. It is safe to run on several machines: `release` settles each reservation once.
- **Lifetime:** the hard timeout of the work plus a margin. Enforce that timeout on the work itself, so a job cannot outlive its reservation.
- **Late commit:** if work finishes after its reservation expired, `commit` still charges it, once, under the same ref, and reports `late: true`. Count these. More than a handful means the lifetime is too short.
- If the job row holds a recorded cost, have the sweeper commit that cost instead of releasing.

## Parallel requests

- Two jobs started at the same moment both reserve. The second succeeds only if `balance - reserved` still covers its bound after the first. The sum of open reservations can never exceed the balance.
- Spends with a known cost use the same `balance - reserved` condition, so they cannot take credits that a running job has reserved.
- A large bound blocks other work while it is open. Keep bounds honest, and cap the number of open reservations per account if one user could otherwise tie up their own balance by accident: count the account's open rows inside the reserve transaction, after the update has locked the account row.

## Tests to write

1. Reserve 50 of 100, commit 30: balance 70, reserved 0, one `usage` entry of -30 under the reservation id.
2. Reserve, then release: balance unchanged, reserved 0, no ledger entry.
3. Commit twice, release twice, commit after release with cost zero: the second call changes nothing.
4. Two reservations of 60 against a balance of 100, started together: exactly one succeeds.
5. A spend with a known cost of 60 while 50 of 100 is reserved: refused.
6. The work throws: the reservation is released and the error reaches the caller.
7. A reservation past `expires_at`: the sweeper releases it; a commit that arrives later charges once and reports `late`.
8. Actual cost above the bound: charged the bound, `overage` reported.
9. The same idempotency key sent twice: one reservation, the work runs once.
