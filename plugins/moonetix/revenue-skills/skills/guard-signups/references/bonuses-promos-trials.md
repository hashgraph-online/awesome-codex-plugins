# Bonuses, promo codes and trials

Screening lowers how many fake accounts get through. The rules in this file decide what an account that got through can collect: each grant once, under a key the database enforces.

The examples change a `balance` column directly to stay short. If the project has a ledger with unique references, post the same amounts through it instead and use the grant's key as the reference (`signup:<user id>`, `promo:<code>:<user id>`), so the ledger enforces the same once-only rule a second time.

## A bonus is a promise before it is a balance

Create the grant when the account is created, in the same transaction, with status `held`. Move it into the balance when its conditions are met. The primary key `(user_id, kind)` makes a second sign-up bonus for the same account impossible, whatever the calling code does.

```sql
CREATE TABLE bonus_grants (
  user_id     BIGINT      NOT NULL REFERENCES users (id),
  kind        TEXT        NOT NULL,            -- 'signup', or 'referral:<invited user id>'
  amount      BIGINT      NOT NULL CHECK (amount > 0),
  status      TEXT        NOT NULL CHECK (status IN ('held', 'released', 'void')),
  hold_reason TEXT,                            -- 'email_unverified', 'review', ...
  created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  decided_at  TIMESTAMPTZ,
  PRIMARY KEY (user_id, kind)
);
```

Release is a conditional transition. The `WHERE status = 'held'` clause is the guard: of two requests that arrive together, one changes the row and credits, the other changes nothing.

```js
// Called when a condition is met (email verified, review cleared). Safe to call twice.
export async function releaseBonus(db, userId, kind) {
  await db.query('BEGIN');
  try {
    const { rows } = await db.query(
      `UPDATE bonus_grants SET status = 'released', decided_at = CURRENT_TIMESTAMP
        WHERE user_id = $1 AND kind = $2 AND status = 'held'
       RETURNING amount`,
      [userId, kind],
    );
    if (rows.length === 1) {
      await db.query('UPDATE users SET balance = balance + $1 WHERE id = $2', [rows[0].amount, userId]);
    }
    await db.query('COMMIT');
    return rows.length === 1;
  } catch (err) {
    await db.query('ROLLBACK');
    throw err;
  }
}
```

MySQL has no `RETURNING`: run the `UPDATE`, check that one row was affected, then read `amount` inside the same transaction.

Before calling it, the caller checks the conditions for that grant's `hold_reason`: a verified email for `email_unverified`; a verified email and the second proof for `review`. Check them on the server from stored state, never from a flag in the request.

Two more rules for any bonus:

- **It can be spent, not cashed out.** Bonus value that can be withdrawn or transferred turns many accounts into one cash-out. If the product pays out, only earned value is withdrawable; the `add-payouts` skill covers that side.
- **It dies with its cause.** When an account is closed for abuse, void its held grants in the same action.

## Promo codes

Two constraints, both enforced by the database in one transaction: one redemption per account per code, and a cap on redemptions per code.

```sql
CREATE TABLE promo_codes (
  code            TEXT        PRIMARY KEY,     -- stored in upper case
  amount          BIGINT      NOT NULL CHECK (amount > 0),
  max_redemptions INTEGER     NOT NULL CHECK (max_redemptions > 0),
  redeemed        INTEGER     NOT NULL DEFAULT 0,
  expires_at      TIMESTAMPTZ,
  CHECK (redeemed >= 0 AND redeemed <= max_redemptions)
);

CREATE TABLE promo_redemptions (
  code       TEXT        NOT NULL REFERENCES promo_codes (code),
  user_id    BIGINT      NOT NULL REFERENCES users (id),
  amount     BIGINT      NOT NULL CHECK (amount > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (code, user_id)
);
```

The redemption, in order:

```sql
BEGIN;
INSERT INTO promo_redemptions (code, user_id, amount) VALUES ($1, $2, $3)
ON CONFLICT (code, user_id) DO NOTHING;
-- 0 rows: this account already redeemed the code. ROLLBACK and answer 409.

UPDATE promo_codes SET redeemed = redeemed + 1
 WHERE code = $1 AND redeemed < max_redemptions;
-- 0 rows: the code is used up. ROLLBACK, which also removes the redemption row. Answer 409.

UPDATE users SET balance = balance + $3 WHERE id = $2;
COMMIT;
```

Why a counter and not `SELECT COUNT(*)`: under PostgreSQL's default isolation, two transactions can both count 499 redemptions of a code capped at 500 and both insert. The conditional `UPDATE` takes a row lock, so the second transaction waits, re-reads the counter and finds the cap reached. The `CHECK` on the table is a second line behind it.

PHP with PDO:

```php
// Returns 'redeemed', 'unknown_code', 'already_redeemed' or 'code_used_up'.
function redeem_promo(PDO $db, int $userId, string $input): string
{
    $code = strtoupper(trim($input));
    $find = $db->prepare(
        'SELECT amount FROM promo_codes WHERE code = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)'
    );
    $find->execute([$code]);
    $amount = $find->fetchColumn();
    if ($amount === false) {
        return 'unknown_code';
    }

    $db->beginTransaction();
    try {
        // The primary key (code, user_id) decides. A second request from the same account inserts nothing.
        $claim = $db->prepare(
            'INSERT INTO promo_redemptions (code, user_id, amount) VALUES (?, ?, ?) ON CONFLICT (code, user_id) DO NOTHING'
        );
        $claim->execute([$code, $userId, $amount]);
        if ($claim->rowCount() === 0) {
            $db->rollBack();
            return 'already_redeemed';
        }
        // The cap is checked and taken in one statement, so two accounts cannot both take the last one.
        $cap = $db->prepare('UPDATE promo_codes SET redeemed = redeemed + 1 WHERE code = ? AND redeemed < max_redemptions');
        $cap->execute([$code]);
        if ($cap->rowCount() === 0) {
            $db->rollBack(); // also removes the redemption row inserted above
            return 'code_used_up';
        }
        $db->prepare('UPDATE users SET balance = balance + ? WHERE id = ?')->execute([$amount, $userId]);
        $db->commit();
        return 'redeemed';
    } catch (Throwable $e) {
        $db->rollBack();
        throw $e;
    }
}
```

Dialect notes:

- **MySQL.** There is no `ON CONFLICT`. Use a plain `INSERT` and treat the duplicate-key error (1062) as "already redeemed". `INSERT IGNORE` also works but hides other errors. Use InnoDB; MyISAM has no transactions.
- **SQLite.** The statements run as written. Open the transaction with `BEGIN IMMEDIATE` so that two writers queue instead of one failing with "database is locked" halfway through.

Around the redemption:

- **The amount comes from the code's row.** Never from the request.
- **The account must be eligible.** Decide with the user whether a held sign-up bonus, an unverified email or a `review` decision blocks redemption. The default: codes need a verified email.
- **Codes are not guessable.** Campaign codes that are meant to be public (`WELCOME100`) rely on the cap and the per-account key. Codes that carry real value each are random: at least 10 characters from an alphabet of 32, generated with a cryptographic random source.
- **Attempts are limited.** Count failed redemptions per account and per address with the velocity table (a rule such as 10 unknown codes per hour), and answer 429 past it. Without this, a script can search the code space.
- **One code per order** when codes are discounts: store the applied code on the order under a unique key, and recompute the discount on the server from the code's row.

## Trials that do not restart

A trial keyed to an account restarts with every new account. Key it to the identities behind the account, and keep the claim after the account is gone.

```sql
CREATE TABLE trial_claims (
  product       TEXT        NOT NULL,
  identity_kind TEXT        NOT NULL,          -- 'email', 'card', 'phone'
  identity_key  TEXT        NOT NULL,          -- keyed hash of the normalized value
  user_id       BIGINT      NOT NULL,
  claimed_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (product, identity_kind, identity_key)
);
```

There is no foreign key to `users` on purpose: deleting the account must not delete the claim. The table stores a keyed hash, so it can be kept after account deletion without keeping the address or the card.

```python
import hashlib
import hmac


def identity_key(secret: bytes, kind: str, value: str) -> str:
    """A keyed hash, so the table alone is not a list of emails, cards or phone numbers."""
    return hmac.new(secret, f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()


def claim_trial(conn, secret, product, user_id, identities):
    """identities: {"email": normalized address, "card": provider fingerprint, "phone": E.164 number}.

    Returns True when the trial may start. Every identity is claimed in one transaction,
    so a card that was already used blocks the trial even with a fresh email, and nothing
    is claimed when the answer is no.
    """
    cur = conn.cursor()
    try:
        for kind, value in identities.items():
            cur.execute(
                "INSERT INTO trial_claims (product, identity_kind, identity_key, user_id) VALUES (?, ?, ?, ?)"
                " ON CONFLICT (product, identity_kind, identity_key) DO NOTHING",
                (product, kind, identity_key(secret, kind, value), user_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return False
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
```

The placeholders are `?` for `sqlite3` and `%s` for the PostgreSQL and MySQL drivers. The secret is a server-side value from the environment with no default; changing it orphans every existing claim, so treat it like a key that is never rotated casually.

Which identities to claim:

- **Normalized email.** Always. It closes plus tags, dots and delete-and-recreate.
- **Card fingerprint.** When the trial collects a card. Payment providers expose a fingerprint that is the same for one card across customers; check the provider's documentation for the field name and for how stable it is. This is the strongest of the three, because cards cost effort to mint.
- **Verified phone number.** When the product verifies phones. Normalize to E.164 first.

A refused trial is not a refused customer: start the paid plan, or offer it. Cancel and resubscribe is covered by the same table, because the claim row for that account's identities already exists.

## Referral rewards

A reward paid when an invited account is created is a reward for an email string. Three rules:

1. **Pay for verified activity.** The referrer's grant is created when the invited user's verified payments or earnings pass a threshold the user chooses, never at sign-up.
2. **Pay once.** The grant's key is `(referrer id, 'referral:<invited user id>')` in `bonus_grants`, so a second qualifying event inserts nothing.
3. **Follow the money back.** If the activity that qualified the invited user is refunded or reversed below the threshold, void or reverse the grant.

Hold a referral grant for review when the referrer and the invited account share a normalized email, a card fingerprint, or a client address at sign-up. The last one is common in real households, so it is a hold, not a refusal.
