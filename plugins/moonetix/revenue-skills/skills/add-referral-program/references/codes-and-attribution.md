# Codes, attribution and same-person checks

Three questions are settled before any reward exists: what a code looks like, when the link between two accounts is made, and whether the two accounts are one person. All three are answered at sign-up or earlier. None of them pays anything.

## Tables

The schema is in `assets/referrals-schema.sql`.

| Table | Holds | The constraint that matters |
| --- | --- | --- |
| `referral_codes` | one code per account | the code is the primary key, the account is unique |
| `referrals` | one row per referred account, with a status | `referred_id` is the primary key: one referrer per account, for good. `CHECK (referred_id <> referrer_id)` |
| `account_signals` | facts that tie an account to a person or device | primary key (account, kind, value), index on (kind, value) |
| `referral_commissions` | one row per earning that paid a commission | `earning_ref` is the primary key |

Differences from PostgreSQL:

- **MySQL 8:** `BIGINT AUTO_INCREMENT` where an id is generated, `DATETIME(6)` in UTC, `VARCHAR(64)` with a binary collation for codes, kinds and values. There is no `ON CONFLICT`: use a plain `INSERT` and treat error 1062 (duplicate key) as "already there". There is no `RETURNING`: select under `FOR UPDATE`, then update. Partial indexes become plain indexes. `now() + make_interval(secs => ?)` becomes `NOW(6) + INTERVAL ? SECOND`.
- **SQLite:** `ON CONFLICT ... DO NOTHING` and `RETURNING` work as shown (3.35 or newer). There is no `FOR UPDATE`: open writing transactions with `BEGIN IMMEDIATE`. Store times as ISO text or integer seconds, the same way everywhere.

## Codes

- **Random, not derived.** A code that is the user id, a counter or a hash of the email can be enumerated or guessed. Draw it from a cryptographic random source.
- **Readable.** People type codes and read them aloud. Use capitals and digits without the look-alikes, and forgive the common slips when reading input.
- **Long enough that guessing is pointless.** Eight characters from 33 symbols are about 1.4 trillion codes. Rate-limit lookups anyway, with the project's existing limiter.
- **One per account, never reassigned.** A code that changes owner moves attribution to a stranger. If users may pick a custom code, it is a second row for the same account, checked against reserved words and brand names.

Node with node-postgres:

```js
import { randomInt } from 'node:crypto';

// No I, L or O: they are read as 1 and 0, and normalizeCode maps them back.
const ALPHABET = '0123456789ABCDEFGHJKMNPQRSTUVWXYZ';

export function generateCode(length = 8) {
  let code = '';
  for (let i = 0; i < length; i += 1) code += ALPHABET[randomInt(ALPHABET.length)];
  return code;
}

// Returns the stored form of what a person typed or a link carried, or null.
export function normalizeCode(input) {
  if (typeof input !== 'string' || input.length > 32) return null;
  const code = input.toUpperCase().replace(/[\s-]/g, '').replace(/O/g, '0').replace(/[IL]/g, '1');
  return /^[0-9A-HJKMNP-Z]{8}$/.test(code) ? code : null;
}

export async function codeFor(tx, accountId) {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const existing = await tx.query('SELECT code FROM referral_codes WHERE account_id = $1', [accountId]);
    if (existing.rowCount > 0) return existing.rows[0].code;
    // A collision with another account's code inserts nothing, and the loop draws again.
    await tx.query('INSERT INTO referral_codes (code, account_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', [
      generateCode(),
      accountId,
    ]);
  }
  throw new Error('could not create a referral code');
}
```

## Attribution happens once, at sign-up

The link is made in the same transaction that creates the account, and never afterwards.

1. **Capture.** A visit to `/?ref=CODE` stores the normalized code in a first-party cookie or in the server-side session, with an expiry (30 days is common). A later visit with another code replaces it: last touch wins. The sign-up form may also offer a field to type a code.
2. **Attach.** Sign-up reads the code from the form field, else from the cookie, and calls `attachReferral` inside its transaction.
3. **Nothing else writes the row.** No "add a referrer" setting on an existing account, no update of `referrer_id`, no merge. If support must attach a referral after the fact, that is a staff action with a name and a reason, allowed only while the account has no verified activity.

```js
// Call inside the transaction that creates the account. Returns the referrer's account id,
// or null when there is no usable code. A bad code never fails the sign-up.
export async function attachReferral(tx, { referredId, code }) {
  const normalized = normalizeCode(code);
  if (!normalized) return null;
  const owner = await tx.query('SELECT account_id FROM referral_codes WHERE code = $1', [normalized]);
  if (owner.rowCount === 0) return null;
  const referrerId = owner.rows[0].account_id;
  if (String(referrerId) === String(referredId)) return null;
  const inserted = await tx.query(
    `INSERT INTO referrals (referred_id, referrer_id, code) VALUES ($1, $2, $3)
     ON CONFLICT (referred_id) DO NOTHING`,
    [referredId, referrerId, normalized],
  );
  return inserted.rowCount === 1 ? referrerId : null;
}
```

- The referrer is looked up by code on the server. The request never carries a referrer id.
- The row starts as `pending`. Creating it credits nobody.
- The response to a wrong code is the same as to no code. Do not build an endpoint that tells a script which codes exist, beyond what the sign-up page needs to show "invited by Anna".
- An account that existed before the visitor clicked the link is not referred. Attribution is for new accounts.

## One person, two accounts

A referral pays for a new person. The cheapest fraud is the same person signing up again with their own code. No check proves identity. Each one raises the cost, and the reward rules in [rewards-and-reversals.md](rewards-and-reversals.md) make the remaining cost real: a second account also has to pay or earn for real before anything is paid.

Record what ties an account to a person or a device as signals, and compare both sides of every referral whenever a new signal arrives.

| Signal | Recorded when | Strength |
| --- | --- | --- |
| Normalized email | sign-up, email change | strong for exact matches |
| Device or installation id | sign-up, sign-in | strong on mobile, medium on the web |
| Network prefix of the address (/24 for IPv4, /64 for IPv6) | sign-up | weak alone: households, offices and mobile carriers share one |
| Payment instrument fingerprint from the payment provider | first payment | strong |
| Payout destination | when it is set or changed | strong |

```js
export function normalizeEmail(email) {
  const [local, domain] = email.trim().toLowerCase().split('@');
  const base = local.split('+')[0];
  const gmail = domain === 'gmail.com' || domain === 'googlemail.com';
  return `${gmail ? base.replace(/\./g, '') : base}@${gmail ? 'gmail.com' : domain}`;
}

// Stores one signal and holds every unpaid referral in which the other side has the same
// value. Call it in the transaction that learned the fact. With hold: false the signal is
// only stored, for the staff view.
export async function recordSignal(tx, accountId, kind, value, { hold = true } = {}) {
  await tx.query(
    'INSERT INTO account_signals (account_id, kind, value) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING',
    [accountId, kind, value],
  );
  if (!hold) return 0;
  const held = await tx.query(
    `UPDATE referrals SET status = 'blocked', blocked_reason = $2
      WHERE status IN ('pending', 'qualified')
        AND (   (referred_id = $1 AND referrer_id IN
                  (SELECT account_id FROM account_signals WHERE kind = $3 AND value = $4 AND account_id <> $1))
             OR (referrer_id = $1 AND referred_id IN
                  (SELECT account_id FROM account_signals WHERE kind = $3 AND value = $4 AND account_id <> $1)))`,
    [accountId, `same_${kind}`, kind, value],
  );
  return held.rowCount;
}
```

At sign-up the order is: create the account, `attachReferral`, then `recordSignal` for the email and the device, and for the network prefix with `hold: false`. The payment handler records the payment fingerprint, and the payout code records the destination. Each call re-checks the referrals of that account in both directions.

- **`blocked` holds, it does not punish.** The referred account works as before, and no reward is paid to the referrer. Staff can release a blocked referral, see [visibility-and-staff.md](visibility-and-staff.md). A weak signal such as the network prefix is stored without a hold: it is a reason to look, not proof.
- **A match found after the reward was paid** changes nothing by itself. It shows up in the staff view, and a person decides whether to revoke.
- **Email normalization is a heuristic.** Dots are ignored only by some providers, and plus tags by most. Keep the address the user typed for sending mail, and use the normalized form only for comparison.
- **Do not tell the user which signal matched.** The referrer sees a referral that is not eligible, nothing more. A precise message is a manual for the next attempt.
- **Store hashes where the raw value is not needed** (device ids, payment fingerprints), and list these signals in the privacy policy. Some of them are personal data.
- Sign-up abuse in general (disposable email domains, velocity, automation) is a wider subject than referrals. The `guard-signups` skill covers it.

## Tests to write

1. A generated code survives `normalizeCode` unchanged. Lower case, spaces, hyphens, and O, I and L typed for 0 and 1 normalize to the stored code. Anything else gives null.
2. Sign-up with a valid code creates one `pending` referral and changes no balance.
3. Sign-up with an unknown or malformed code creates the account and no referral.
4. A second attach for the same referred account, with any code, changes nothing.
5. An account cannot be attached to its own code.
6. A sign-up whose normalized email, device or payment fingerprint equals the referrer's ends as `blocked` with the reason stored. A shared network prefix alone does not block.
7. A signal recorded later on either side blocks a `pending` or `qualified` referral and leaves a `rewarded` one as it is.
