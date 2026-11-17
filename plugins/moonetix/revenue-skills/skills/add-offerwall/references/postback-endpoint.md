# The postback endpoint

When a user completes an offer, the network calls a URL on your server: the postback. It is the only thing that may credit a reward. This file covers the route, authentication, the amount, the credit, the reversal, the answer and the hold. The examples use a network that sends `tx`, `user`, `payout`, `status` and `hash` as query parameters, where `hash` is an HMAC-SHA256 of `tx:user:payout:status`. Real names and schemes are in network-facts.md and in the network's documentation.

## The route

- Register it outside session, login and CSRF middleware, and outside per-address rate limits and bot protection. Every call comes from the network's servers, without cookies.
- Give the network the final URL. Many senders do not follow redirects, so an `http` to `https` redirect or a trailing-slash redirect loses the postback.
- Read each parameter as exactly one string, as it arrived. Frameworks turn `?tx=a&tx=b` into an array; refuse that. Do not trim, lowercase or reformat before authenticating: `150` and `150.00` hash differently.
- When the signature covers the whole URL or the body, authenticate the raw query string or the raw body, not a parsed and rebuilt copy. Behind a proxy, take the scheme and host from configuration.
- Load the secret from the environment at start-up and refuse to start without it. It is a different secret from the one that signs wall links.

## Authenticate first

Nothing runs before this check: no database read, no parsing of amounts.

| Scheme | Expected value | Notes |
| --- | --- | --- |
| HMAC over named fields | `HMAC(key, field1 + sep + field2 ...)` | Only the named fields are protected |
| HMAC over the URL or body | `HMAC(key, url without the signature parameter)` or `HMAC(key, raw body)` | Everything is protected. Needs the raw bytes |
| Keyed digest | `sha256(field1 + field2 + ... + secret)`, also seen with SHA-1 and MD5 | Only the named fields are protected |
| Shared secret in the URL | The secret itself arrives as a parameter | Compare it in constant time. Keep it out of logs. Add the address allowlist |
| No signature | Nothing | An unguessable path plus the address allowlist is all there is. Prefer a network that signs |

```js
import { createHash, createHmac, timingSafeEqual } from 'node:crypto';

// Comparing digests keeps the comparison constant-time for inputs of any length.
export function safeEqual(a, b) {
  const digest = (value) => createHash('sha256').update(String(value)).digest();
  return timingSafeEqual(digest(a), digest(b));
}

export const hmacOfFields = (key, fields, separator = ':') =>
  createHmac('sha256', key).update(fields.join(separator)).digest('hex');

// rawUrl is the URL exactly as the network called it. Only the signature parameter is cut off.
export function hmacOfUrl(key, rawUrl, parameter = 'hash') {
  const at = rawUrl.lastIndexOf(`&${parameter}=`);
  return createHmac('sha256', key).update(at < 0 ? rawUrl : rawUrl.slice(0, at)).digest('hex');
}

export const digestOfFields = (algorithm, fields, secret) =>
  createHash(algorithm).update(fields.join('') + secret).digest('hex');
```

## The record of each conversion

One row per network transaction. Its primary key is what makes a repeated postback harmless.

```sql
CREATE TABLE offer_conversions (
  network       TEXT        NOT NULL,
  tx_id         TEXT        NOT NULL,
  user_id       BIGINT      NOT NULL REFERENCES users (id),
  payout_micros BIGINT      NOT NULL CHECK (payout_micros >= 0),
  coins         BIGINT      NOT NULL CHECK (coins >= 0),
  status        TEXT        NOT NULL CHECK (status IN ('credited', 'reversed')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reversed_at   TIMESTAMPTZ,
  PRIMARY KEY (network, tx_id)
);
```

MySQL: `VARCHAR(32)` and `VARCHAR(191)` for the key columns, `DATETIME` for the times. SQLite: `INTEGER` and `TEXT`, with times as UTC text. `payout_micros` is what the network pays you, in millionths of a dollar. `coins` is what the user was given. Both are stored so that a reversal, a report and a dispute never recompute anything.

## Deciding the amount

The reward is decided on the server, from authenticated fields and the app's own rate and share. A field outside the signature (often the offer name or the country, sometimes the payout) is information for logs, never an input to the amount.

- **The signature covers the payout.** Compute `coins = payout x coins per dollar x user share`, in integers, rounded down once. This is the default below.
- **The signature covers only a reward in your currency**, which the network computed from the rate set in its dashboard. Credit the signed reward as received, after checking that it is a non-negative number in the currency's precision and in range. Keep the dashboard's rate and share equal to the app's configuration, and log a warning when the reward differs from the app's own computation by more than one unit.
- **Never** take the amount from an unsigned parameter, from the browser or the app, or from the wall page.

Whatever the wall showed the user is what the user expects. If the network displays rewards on the wall, its dashboard settings and the app's configuration must produce the same number.

## The handler

Node with PostgreSQL. `postEntry` and `withTransaction` are the ledger's posting function and transaction helper, as the `build-ledger` skill builds them. `signatures.mjs` is the block above.

```js
import { postEntry, withTransaction } from './ledger.mjs';
import { hmacOfFields, safeEqual } from './signatures.mjs';

const NETWORK = 'examplenet';
const EVENTS = new Map([['1', 'credit'], ['2', 'reversal']]);
const MICROS = 1_000_000n;

export function parseUsdMicros(text) {
  const m = /^(\d{1,9})(?:\.(\d{1,6}))?$/.exec(text);
  if (!m) return null;
  return BigInt(m[1]) * MICROS + BigInt((m[2] ?? '').padEnd(6, '0'));
}

export const coinsForPayout = (payoutMicros, { coinsPerDollar, userShareBps }) =>
  Number((payoutMicros * BigInt(coinsPerDollar) * BigInt(userShareBps)) / (MICROS * 10_000n));

// params holds the query parameters as they arrived. Returns the status and body to answer with.
// A thrown error means nothing was stored: answer 500 and the network sends it again.
export async function handlePostback(params, { pool, config }) {
  const { tx, user, payout, status, hash } = params;
  if (![tx, user, payout, status, hash].every((value) => typeof value === 'string')) return { status: 400, body: 'BAD REQUEST' };
  if (!safeEqual(hash, hmacOfFields(config.postbackKey, [tx, user, payout, status]))) return { status: 403, body: 'BAD HASH' };

  const event = EVENTS.get(status);
  if (!event) return { status: 200, body: 'IGNORED' };
  if (!/^[\w.:-]{1,191}$/.test(tx) || !/^[1-9]\d{0,14}$/.test(user)) return { status: 400, body: 'BAD REQUEST' };
  const payoutMicros = parseUsdMicros(payout);
  if (payoutMicros === null) return { status: 400, body: 'BAD REQUEST' };

  const body = await withTransaction(pool, async (db) => {
    const known = await db.query('SELECT id FROM users WHERE id = $1', [user]);
    if (known.rowCount === 0) return 'UNKNOWN USER';
    return event === 'credit' ? credit(db, config, tx, user, payoutMicros) : reverse(db, tx, user);
  });
  return { status: 200, body };
}

async function credit(db, config, tx, user, payoutMicros) {
  const coins = coinsForPayout(payoutMicros, config);
  const inserted = await db.query(
    `INSERT INTO offer_conversions (network, tx_id, user_id, payout_micros, coins, status)
     VALUES ($1, $2, $3, $4, $5, 'credited')
     ON CONFLICT (network, tx_id) DO NOTHING`,
    [NETWORK, tx, user, String(payoutMicros), coins],
  );
  if (inserted.rowCount === 0) return 'DUPLICATE';
  if (coins > 0) await postEntry(db, { accountId: Number(user), amount: coins, kind: 'offer', ref: `${NETWORK}:${tx}`, actor: NETWORK });
  return 'OK';
}

// Takes back what this transaction credited, from the account it credited, once. Only the id is read from the request.
async function reverse(db, tx, user) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const flipped = await db.query(
      `UPDATE offer_conversions SET status = 'reversed', reversed_at = CURRENT_TIMESTAMP
       WHERE network = $1 AND tx_id = $2 AND status = 'credited'
       RETURNING user_id, coins`,
      [NETWORK, tx],
    );
    if (flipped.rowCount === 1) {
      const { user_id: accountId, coins } = flipped.rows[0];
      if (Number(coins) > 0) {
        await postEntry(db, { accountId: Number(accountId), amount: -Number(coins), kind: 'offer_reversal', ref: `${NETWORK}:${tx}`, actor: NETWORK, allowDebt: true });
      }
      return 'OK';
    }
    // Nothing is credited under this id. Record the reversal, so that a credit arriving late
    // for the same id pays nothing.
    const marked = await db.query(
      `INSERT INTO offer_conversions (network, tx_id, user_id, payout_micros, coins, status, reversed_at)
       VALUES ($1, $2, $3, 0, 0, 'reversed', CURRENT_TIMESTAMP)
       ON CONFLICT (network, tx_id) DO NOTHING`,
      [NETWORK, tx, user],
    );
    if (marked.rowCount === 1) return 'NOTHING TO REVERSE';
    // The insert lost to a row that was committed a moment ago. If that was the credit,
    // the second pass reverses it. If it was another reversal, the second pass changes nothing.
  }
  return 'DUPLICATE';
}
```

Why it holds: the primary key decides whether a credit happens, so ten copies of one postback at the same moment post one entry. The conditional `UPDATE` decides whether a reversal happens, so a second reversal finds no `credited` row. The retry pass relies on READ COMMITTED, the PostgreSQL default, where each statement sees rows committed before it started. MySQL has no `RETURNING`: run the conditional update, check the row count, then read the stored row, as in the next example. Networks signal reversals in different ways; network-facts.md lists the shapes and how to map them onto this function.

## Without a ledger: the minimum

If the project has only a balance column, the minimum is the table above: its primary key on the network and the transaction id is the unique key, and the balance changes only when the insert created a row, in the same transaction. PHP with MySQL:

```php
<?php
declare(strict_types=1);

function credit_conversion(PDO $db, string $tx, int $userId, int $payoutMicros, int $coins): string
{
    // Lock the user row first. The foreign key check of the insert takes a shared lock on it,
    // and two transactions that hold one and then update the balance would deadlock.
    $user = $db->prepare('SELECT id FROM users WHERE id = ? FOR UPDATE');
    $user->execute([$userId]);
    if ($user->fetchColumn() === false) {
        return 'UNKNOWN USER';
    }
    try {
        $db->prepare(
            "INSERT INTO offer_conversions (network, tx_id, user_id, payout_micros, coins, status)
             VALUES ('examplenet', ?, ?, ?, ?, 'credited')"
        )->execute([$tx, $userId, $payoutMicros, $coins]);
    } catch (PDOException $e) {
        if (($e->errorInfo[1] ?? null) === 1062) {
            return 'DUPLICATE';
        }
        throw $e;
    }
    $db->prepare('UPDATE users SET balance = balance + ? WHERE id = ?')->execute([$coins, $userId]);
    return 'OK';
}

function reverse_conversion(PDO $db, string $tx): string
{
    $flip = $db->prepare(
        "UPDATE offer_conversions SET status = 'reversed', reversed_at = CURRENT_TIMESTAMP
         WHERE network = 'examplenet' AND tx_id = ? AND status = 'credited'"
    );
    $flip->execute([$tx]);
    if ($flip->rowCount() !== 1) {
        return 'NOTHING TO REVERSE';
    }
    $find = $db->prepare("SELECT user_id, coins FROM offer_conversions WHERE network = 'examplenet' AND tx_id = ?");
    $find->execute([$tx]);
    $row = $find->fetch(PDO::FETCH_ASSOC);
    // The stored amount, from the stored account. The balance may go below zero.
    $db->prepare('UPDATE users SET balance = balance - ? WHERE id = ?')
       ->execute([(int) $row['coins'], (int) $row['user_id']]);
    return 'OK';
}
```

Both run inside `beginTransaction()` and `commit()`, with `rollBack()` and a 500 answer on any exception. For a reversal that finds nothing, insert the `reversed` row as the handler above does, so that a late credit pays nothing. This closes double credits and double reversals. It does not give a history of other balance changes or a reconciliation check: the `build-ledger` skill adds those.

## What to answer

| Situation | Answer |
| --- | --- |
| Stored: credit or reversal | 2xx, after the commit |
| Seen before, nothing to reverse, unknown user, a status that is not settled money | 2xx. A retry would not change anything. Log unknown users |
| Signature missing or wrong, or signed but malformed | 4xx. For a signed malformed request also alert: the URL template is probably wrong |
| The database failed | 5xx, so that the network retries |

Some networks require an exact body, such as `ok` or `1`. Check the network's documentation and return it for every success, including duplicates.

## The hold

Fresh earnings can still be reversed, so they cannot be cashed out yet. What may leave is the offer earnings older than the hold, minus everything already reversed or paid out, and never more than the balance:

```sql
SELECT COALESCE(SUM(CASE WHEN kind = 'offer' AND created_at > :cutoff THEN 0 ELSE amount END), 0) AS matured
FROM ledger
WHERE account_id = :account_id
  AND kind IN ('offer', 'offer_reversal', 'payout', 'payout_refund');
```

`:cutoff` is now minus the hold, computed by the application. `withdrawable = max(0, min(balance, matured))`. A reversal counts at once, also when the credit it belongs to is still held, which errs on the safe side. Evaluate this inside the transaction that takes the funds for a payout (the `add-payouts` skill), and show held coins to the user as pending with the date they mature. Without a ledger, compute the same from `offer_conversions` and the payouts table.

## Around the handler

- **Log every call:** the raw query string, the source address, the answer. Redact a shared secret, not the hash. A macro that arrives literally, such as `{user_id}`, means the URL template is misspelled.
- **Address allowlist as a second layer** where the network publishes its addresses. Read the address from the connection or from the trusted proxy's header, never from a header the caller can set.
- **Test postbacks from the network's dashboard** in production: authenticate, log, and do not credit real accounts.
- **Side effects after the commit:** notifications, and nothing that can fail the credit. Rewards that depend on the credit, such as a referral commission, are posted in the same transaction and reversed with it (the `add-referral-program` skill).
