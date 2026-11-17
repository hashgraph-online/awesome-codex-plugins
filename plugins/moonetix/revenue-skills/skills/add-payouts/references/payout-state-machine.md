# The payout state machine

A payout is a row that moves through a fixed set of states. The funds leave the balance when the row is created, before any provider is called. From then on every step is a guarded change of status, and each guard answers one question: may this happen, and has it happened already?

## States

| Status | Meaning | Funds |
| --- | --- | --- |
| `in_review` | Waits for a staff decision | taken from the balance |
| `pending` | Cleared to send, not yet handed to the provider | taken |
| `sending` | Handed to the provider, or the hand-over has an unknown result | taken |
| `paid` | The provider confirmed that the money was sent | gone |
| `failed` | The provider stated that it did not and will not send | returned, once |
| `rejected` | Staff declined the request | returned, once |
| `canceled` | The user withdrew the request before it was sent | returned, once |

The allowed moves are the `MOVES` table in the code below, and nothing else. `sending` has exactly two exits, and both need a definite answer from the provider. A timeout is not an answer. There is no move from `sending` back to `pending`, and none out of `paid`, `failed`, `rejected` or `canceled`. If the provider can return a payout after reporting it as sent (a bounced bank transfer), handle that as a separate credit with its own kind and the provider's return id as reference. Check the provider's documentation for whether this exists.

The schema is in `assets/payouts-schema.sql`. Three columns carry the design. `id` is created by the server and is used three times: as primary key, as the idempotency key sent to the provider, and as the reference of the ledger entries `payout` and `payout_refund`. `request_key` with `UNIQUE (account_id, request_key)` makes a repeated request from the client return the first payout. `destination` is a copy of where the money goes, taken when the request is made, so a later change of destination cannot redirect a payout that is already on its way.

## One function changes the status

Node with node-postgres. `withTransaction`, `postEntry` and `InsufficientFunds` are the posting function and helpers of the project's ledger, as built by the `build-ledger` skill. The limit checks are in [limits-holds-and-destinations.md](limits-holds-and-destinations.md).

```js
import { randomUUID } from 'node:crypto';
import { InsufficientFunds, postEntry, withTransaction } from './ledger.mjs';
import { payoutRefusal, reviewReason } from './payout-limits.mjs';

const MOVES = {
  in_review: ['pending', 'rejected', 'canceled'],
  pending: ['sending', 'in_review', 'canceled'],
  sending: ['paid', 'failed'],
};
const FINAL = ['paid', 'failed', 'rejected', 'canceled'];

// Returns the payout when this call moved it, null when it was not in `from` any more:
// another worker, a provider event or a retry got there first.
export async function move(tx, payoutId, from, to, { providerRef = null, failureCode = null, reviewedBy = null } = {}) {
  if (!MOVES[from]?.includes(to)) throw new Error(`a payout cannot go from ${from} to ${to}`);
  const moved = await tx.query(
    `UPDATE payouts
        SET status = $3,
            provider_ref = COALESCE($4, provider_ref),
            failure_code = COALESCE($5, failure_code),
            reviewed_by = COALESCE($6, reviewed_by),
            settled_at = CASE WHEN $7 THEN now() ELSE settled_at END
      WHERE id = $1 AND status = $2
      RETURNING id, account_id, amount`,
    [payoutId, from, to, providerRef, failureCode, reviewedBy, FINAL.includes(to)],
  );
  return moved.rows[0] ?? null;
}

// The only place that gives payout funds back. Two guards make it happen once: the move
// succeeds for one caller, and the ledger accepts one payout_refund per payout id.
export async function endWithoutPaying(tx, payoutId, from, to, fields) {
  const payout = await move(tx, payoutId, from, to, fields);
  if (!payout) return false;
  await postEntry(tx, { accountId: payout.account_id, amount: Number(payout.amount), kind: 'payout_refund', ref: payoutId });
  return true;
}
```

Every write to `payouts.status` carries the status it expects in its `WHERE` clause: `move`, and the two statements of the claim in `sendPayout` below. The insert in `requestPayout` is the only other place the column is set. A reviewer can check that with one search.

## Request: take the funds, then create the row

```js
export async function requestPayout(pool, { accountId, requestKey, amount, policy }) {
  try {
    return await withTransaction(pool, async (tx) => {
      // The row lock makes this account's requests take turns, so every check below sees
      // the payouts that were created before it.
      const account = (await tx.query('SELECT id, balance FROM accounts WHERE id = $1 FOR UPDATE', [accountId])).rows[0];
      const repeat = await tx.query(
        'SELECT id, status FROM payouts WHERE account_id = $1 AND request_key = $2',
        [accountId, requestKey],
      );
      if (repeat.rowCount > 0) return { payoutId: repeat.rows[0].id, status: repeat.rows[0].status, repeated: true };

      const usable = await tx.query(
        `SELECT id, method, details, fingerprint FROM payout_destinations
          WHERE account_id = $1 AND removed_at IS NULL AND usable_from <= now()`,
        [accountId],
      );
      const destination = usable.rows[0];
      const refusal = await payoutRefusal(tx, account, destination, amount, policy);
      if (refusal) return { refused: refusal };

      const payoutId = randomUUID();
      const review = await reviewReason(tx, account, destination, amount, policy);
      const status = review ? 'in_review' : 'pending';
      const sentTo = JSON.stringify({ method: destination.method, details: destination.details });
      await postEntry(tx, { accountId, amount: -amount, kind: 'payout', ref: payoutId });
      await tx.query(
        `INSERT INTO payouts (id, account_id, request_key, amount, currency, payout_minor,
                              destination_id, destination, status, review_reason)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [payoutId, accountId, requestKey, amount, policy.currency, amount / policy.unitsPerMinor,
         destination.id, sentTo, status, review],
      );
      return { payoutId, status };
    });
  } catch (err) {
    if (err instanceof InsufficientFunds) return { refused: 'insufficient_balance' };
    throw err;
  }
}
```

- The account comes from the session, the amount from the request body as a whole number, and `requestKey` from an `Idempotency-Key` header that the client creates once per click.
- The checks, the debit and the insert are one transaction. Ten parallel requests run one after another, and each sees the balance and the daily total that the one before it left.
- The transaction commits before anything is sent. Never hold it open across the provider call.
- The handler answers with the payout id and its status. The user sees "requested", not "paid".

## Send: claim, call, classify

```js
export async function sendPayout(pool, provider, payoutId) {
  // Claim in one statement. Of any number of workers and retries, one changes the row and
  // makes the call. Account flags are checked again here, not only when the request was made.
  const claimed = await pool.query(
    `UPDATE payouts
        SET status = 'sending', attempts = attempts + 1, sent_at = now(), next_check_at = now() + interval '10 minutes'
      WHERE id = $1 AND status = 'pending'
        AND EXISTS (SELECT 1 FROM users u WHERE u.id = payouts.account_id AND u.status = 'active')
      RETURNING id, payout_minor, currency, destination`,
    [payoutId],
  );
  if (claimed.rowCount === 0) {
    // Still pending means the account was flagged after the request: a person decides.
    await pool.query(
      `UPDATE payouts SET status = 'in_review', review_reason = 'account_flagged' WHERE id = $1 AND status = 'pending'`,
      [payoutId],
    );
    return 'not_sent';
  }
  return applyOutcome(pool, payoutId, await callProvider(provider, claimed.rows[0]));
}

async function callProvider(provider, payout) {
  try {
    const { id, payout_minor: minor, currency, destination } = payout;
    return await provider.createPayout({ idempotencyKey: id, amountMinor: Number(minor), currency, destination: JSON.parse(destination) });
  } catch {
    // A timeout, a dropped connection or an unreadable answer says nothing about the money.
    return { outcome: 'unknown' };
  }
}

export async function applyOutcome(pool, payoutId, { outcome, providerRef = null, failureCode = null }) {
  return withTransaction(pool, async (tx) => {
    if (outcome === 'paid' || outcome === 'failed') {
      const done =
        outcome === 'paid'
          ? await move(tx, payoutId, 'sending', 'paid', { providerRef })
          : await endWithoutPaying(tx, payoutId, 'sending', 'failed', { providerRef, failureCode });
      if (done) return outcome;
      const current = (await tx.query('SELECT status FROM payouts WHERE id = $1', [payoutId])).rows[0];
      // The same answer again is a repeat. A different final answer is never applied by
      // code: it is an incident, and reconciliation will show it too.
      return current?.status === outcome ? 'repeated' : 'conflict';
    }
    await tx.query(
      `UPDATE payouts SET provider_ref = COALESCE($2, provider_ref), next_check_at = now() + interval '15 minutes'
        WHERE id = $1 AND status = 'sending'`,
      [payoutId, providerRef],
    );
    return 'sending';
  });
}
```

`provider` is the project's own adapter around the payout provider's API. It sends the payout id in the field the provider documents for idempotency, sets a request timeout, and turns every answer into one of four outcomes:

| Outcome | When | Effect |
| --- | --- | --- |
| `paid` | The provider states that the transfer is complete | `sending` to `paid` |
| `accepted` | The provider took the request and reports the result later | stays `sending`, the provider's id is stored |
| `failed` | The provider states that nothing was sent and nothing will be | `sending` to `failed`, funds returned |
| `unknown` | Everything else: timeout, connection error, 5xx, an answer the adapter does not recognize | stays `sending` |

Which answers are a definite failure differs by provider. Check the provider's documentation for the list of final error codes, and treat every code that is not on it as `unknown`. A wrong `unknown` costs a delay. A wrong `failed` pays the user twice: once by the provider and once by the refund.

Run `sendPayout` right after the request commits, from a queue worker, or both. The claim makes that safe.

## Resolve what is unknown: ask, do not send again

```js
export async function resolveSending(pool, provider, policy, limit = 50) {
  const due = await pool.query(
    `SELECT id FROM payouts WHERE status = 'sending' AND next_check_at <= now() ORDER BY next_check_at LIMIT $1`,
    [limit],
  );
  const needsPerson = [];
  for (const { id } of due.rows) {
    let answer;
    try {
      answer = await provider.findPayout(id);
    } catch {
      answer = { outcome: 'unknown' };
    }
    if (answer.outcome === 'not_found') {
      // The provider has no record, so the first call may never have arrived. Repeat it
      // with the same key, and only while the provider still honors that key.
      const again = await pool.query(
        `UPDATE payouts SET attempts = attempts + 1
          WHERE id = $1 AND status = 'sending' AND attempts < $2 AND sent_at > now() - make_interval(secs => $3)
          RETURNING id, payout_minor, currency, destination`,
        [id, policy.maxAttempts, policy.idempotencyKeyLifetimeSeconds],
      );
      if (again.rowCount === 0) needsPerson.push(id);
      answer = again.rowCount === 0 ? { outcome: 'unknown' } : await callProvider(provider, again.rows[0]);
    }
    await applyOutcome(pool, id, answer);
  }
  return needsPerson;
}
```

- `provider.findPayout` asks the provider for the payout by the id you sent or by the stored `provider_ref`, and returns the same four outcomes or `not_found`. Check the provider's documentation for how to look a payout up by your own reference and for how long an idempotency key is honored.
- A repeat is allowed only with the same key and inside that lifetime. A new key for the same payout is a second transfer. Past the lifetime, the payout stays `sending` and goes to a person.
- Asking is always safe, and so is a repeat with the same key once your own call has returned or timed out, because the provider deduplicates by the key. Do not hold a payout back from the resolver for a quiet period after its last attempt: when support runs the resolver by hand, it must ask the provider right away. If scheduled checks use a backoff (`next_check_at`), let a manual run ignore it.
- Never refund on `unknown` or on `not_found`. Only a stated failure returns funds.
- Alert on every id in `needsPerson` and on any payout that has been `sending` for more than a few hours.
- If the user wants to try again after a failure, that is a new request with a new payout id.

- **Provider events.** If the provider reports results through events, receive them on an endpoint that verifies the signature (the `build-webhook-endpoint` skill covers that), map the event to a payout by your id or by `provider_ref`, and call `applyOutcome`. A repeated or late event finds the payout already moved and changes nothing. Keep the resolver even when events exist: events get lost.

## MySQL and SQLite

- **MySQL 8:** there is no `RETURNING`. Inside a transaction, run the guarded `UPDATE`, check that one row changed, then `SELECT` the row. `now() + interval '10 minutes'` becomes `NOW() + INTERVAL 10 MINUTE`. Partial indexes become plain indexes, and the one open destination per account is enforced in code under the account lock. Use `VARCHAR(64)` for ids and keys.
- **SQLite:** `RETURNING` works from 3.35. There is no `FOR UPDATE`: open writing transactions with `BEGIN IMMEDIATE`. Store times as integer seconds or ISO text and compare them the same way everywhere.

## Without a ledger

If the app has only a balance column, the minimum is still the same order of work:

```sql
BEGIN;
UPDATE users SET balance = balance - :amount WHERE id = :id AND balance >= :amount;  -- 0 rows: refuse and roll back
INSERT INTO payouts (id, account_id, request_key, amount, currency, payout_minor, destination_id, destination, status)
VALUES (:payout_id, :id, :request_key, :amount, :currency, :payout_minor, :destination_id, :destination, 'pending');
COMMIT;
```

The refund is `UPDATE users SET balance = balance + :amount` in the same transaction as the guarded move to `failed`, `rejected` or `canceled`, and only when that move changed one row. This pays once and refunds once. It cannot say which part of a balance was earned or when, so the hold and the earned-only rule need a dated record of earnings. Build the ledger first if there is none.
