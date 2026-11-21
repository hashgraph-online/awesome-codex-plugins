# Score and outcomes

Counting attempts, turning signals into a score a person can read, and acting on it without locking out real users.

## Velocity

Count attempts, not accounts: every call to the sign-up endpoint counts, including the ones that are refused later. Three keys cover the common cases.

| Rule | Key | Limit | Window |
| --- | --- | ---: | --- |
| `ip-hour` | client address | 5 | 1 hour |
| `ip-day` | client address | 20 | 24 hours |
| `network-day` | IPv4 /24 or IPv6 /64 | 50 | 24 hours |
| `email-day` | keyed hash of the normalized email | 5 | 24 hours |

Why these keys: one address is one device or one shared exit. One home on IPv6 usually holds a whole /64 and can rotate inside it for free, so per-address limits alone are weak there. The email rule catches a script retrying one inbox with different passwords or referral codes. Fixed windows allow a burst at the edge of a window, which is why the short rule is paired with a long one.

A SQL table is enough. The window start is computed by the application, so the statement is the same in every dialect that has an upsert:

```sql
INSERT INTO velocity_counters (rule, subject, window_start) VALUES ($1, $2, $3)
ON CONFLICT (rule, subject, window_start) DO UPDATE SET hits = velocity_counters.hits + 1
RETURNING hits;
```

MySQL: `INSERT ... ON DUPLICATE KEY UPDATE hits = hits + 1`, then read the row back in the same transaction. SQLite accepts the statement as written from version 3.35. Delete rows older than the longest window with a daily job. If the project already runs Redis, one `INCR` with an `EXPIRE` set in the same script when the counter is created does the same work; a counter must never be left without an expiry.

```js
export const RULES = [
  { name: 'ip-hour', key: 'ip', limit: 5, windowSeconds: 3600 },
  { name: 'ip-day', key: 'ip', limit: 20, windowSeconds: 86400 },
  { name: 'network-day', key: 'network', limit: 50, windowSeconds: 86400 },
  { name: 'email-day', key: 'email', limit: 5, windowSeconds: 86400 },
];

// Counts this attempt under every rule and returns the keys that are over a limit.
// Call it before the decision and outside the sign-up transaction: a refused attempt still counts.
export async function countAttempt(db, subjects, nowSeconds, rules = RULES) {
  const exceeded = new Set();
  for (const rule of rules) {
    const subject = subjects[rule.key];
    if (!subject) continue;
    const windowStart = nowSeconds - (nowSeconds % rule.windowSeconds);
    const { rows } = await db.query(
      `INSERT INTO velocity_counters (rule, subject, window_start) VALUES ($1, $2, $3)
       ON CONFLICT (rule, subject, window_start) DO UPDATE SET hits = velocity_counters.hits + 1
       RETURNING hits`,
      [rule.name, subject, windowStart],
    );
    if (rows[0].hits > rule.limit) exceeded.add(rule.key);
  }
  return [...exceeded];
}
```

`nowSeconds` is Unix seconds. Passing milliseconds makes every window a thousand times shorter and no limit ever trips. Pass `null` for the address and network subjects when the client address is not public (see the client address section of [identity-and-signals.md](identity-and-signals.md)).

## The score

The score is the sum of the points of the reasons. Nothing else goes into it. Each reason has a code, its points, a detail line for staff and, where the user can do something about it, a hint.

| Code | Points | Added when | Hint for the user |
| --- | ---: | --- | --- |
| `email_invalid` | 100 | The address fails the syntax check | Check the email address for typos. |
| `email_disposable` | 70 | The domain or a parent is on the disposable list | Please use a permanent email address. |
| `ip_datacenter` | 40 | The address is in a cloud or hosting range | Turn off your VPN or proxy, or switch to your home or mobile connection, and try again. |
| `ip_tor` | 40 | The address is a Tor exit | Please sign up without Tor. |
| `ip_cdn` | 15 | The address is in a CDN edge range | If you use a VPN or a privacy service, turn it off and try again. |
| `ip_relay` | 0 | The address is a privacy relay | none |
| `velocity_ip` | 30 | An address rule is over its limit | Too many attempts. Please try again later. |
| `velocity_network` | 30 | The network rule is over its limit | same |
| `velocity_email` | 40 | The email rule is over its limit | same |

Thresholds: 30 and above is `review`, 70 and above is `block`. Read the table against them:

- No network signal reaches 70 alone. A datacenter address is review. Two tripped address limits on a campus network are 60: still review.
- A disposable or invalid email blocks alone, and the user can fix it at once.
- A block from network signals needs two that agree, such as a datacenter address that is also over its limit.
- A zero-point reason is still recorded. It explains the account later.

Weights and thresholds are integers in configuration. When the user wants a different policy, change a number in the table. Do not add logic that bypasses the sum.

```js
export const WEIGHTS = {
  email_invalid: 100,
  email_disposable: 70,
  ip_datacenter: 40,
  ip_tor: 40,
  ip_cdn: 15,
  ip_relay: 0,
  velocity_ip: 30,
  velocity_network: 30,
  velocity_email: 40,
};
export const THRESHOLDS = { review: 30, block: 70 };

// signals: { email: { normalized, domain } | { problem }, disposable: boolean,
//            network: { public, categories }, exceeded: ['ip', 'network', 'email'] }
export function assess(signals, weights = WEIGHTS, thresholds = THRESHOLDS) {
  const reasons = [];
  const add = (code, detail) => reasons.push({ code, points: weights[code], detail });

  if (!signals.email.normalized) add('email_invalid', 'The address failed the syntax check.');
  else if (signals.disposable) add('email_disposable', `${signals.email.domain} is on the disposable domain list.`);

  const seen = signals.network.categories;
  if (seen.includes('datacenter')) add('ip_datacenter', 'The address is in a published cloud or hosting range.');
  if (seen.includes('tor')) add('ip_tor', 'The address is a Tor exit.');
  if (seen.includes('cdn')) add('ip_cdn', 'The address is in a CDN edge range.');
  if (seen.includes('relay')) add('ip_relay', 'The address is a privacy relay shared by many real users.');

  for (const key of signals.exceeded) add(`velocity_${key}`, `More sign-up attempts than the ${key} limit allows.`);

  const score = reasons.reduce((sum, r) => sum + r.points, 0);
  const decision = score >= thresholds.block ? 'block' : score >= thresholds.review ? 'review' : 'allow';
  return { score, decision, reasons };
}
```

## The three outcomes

| Decision | The account | The bonus | What the user sees |
| --- | --- | --- | --- |
| `allow` | Created. | Held until the email is verified, then released. | The normal flow. |
| `review` | Created and usable. | Held until the email is verified and one more proof is given. | "Verify your account to receive your bonus", with the steps. |
| `block` | Not created. | None. | The hints from the table, and a way to reach a person. |

Review is the outcome that needs care, because it is where real users on unusual networks land. It means three things in practice:

1. **Hold the bonus.** The grant exists with status `held`. It is not in the balance and cannot be spent, transferred or withdrawn.
2. **Ask for verification.** Email verification plus one more proof the product can check: a verified phone number, a bot challenge verified on the server, or the first verified payment or earning. Pick the proof by what the bonus is worth; a challenge alone is thin for anything redeemable for cash.
3. **Keep the account usable.** The user can sign in, use the product, pay and earn. Nothing that costs you nothing is withheld. A reviewed account that turns out to be a real customer has lost a few minutes, not the product.

A held grant that is never claimed becomes `void` after a period the user chooses (30 days is a reasonable default). Staff can release or void a grant by hand, and that action is recorded with their identity.

For a block, show hints and nothing else: never the score, the threshold, the list name or the limit. Each of those is a tuning aid for whoever is scripting the sign-ups. Give a contact path, and review what appeals overturn: a rule that keeps losing appeals needs a lower weight.

## The sign-up flow

The order matters: count first, then decide, then record, then act. `db` is one database connection, not a pool, so that `BEGIN` and `COMMIT` reach the same session.

```js
import { createHmac } from 'node:crypto';

// deps: { db, classify, disposableDomains, identitySecret, signupBonus, now }
export async function signUp(deps, { email: typed, ip }) {
  const { db } = deps;
  const email = normalizeEmail(typed);
  const network = deps.classify(ip);
  const emailKey = email.normalized
    ? createHmac('sha256', deps.identitySecret).update(`email:${email.normalized}`).digest('hex')
    : '';

  const exceeded = await countAttempt(
    db,
    { ip: network.public ? ip : null, network: network.public ? networkPrefix(ip) : null, email: emailKey },
    deps.now(),
  );
  const disposable = Boolean(email.normalized) && isDisposable(email.domain, deps.disposableDomains);
  const result = assess({ email, disposable, network, exceeded });

  const record = (userId) =>
    db.query(
      `INSERT INTO signup_assessments (user_id, email_key, ip, network_prefix, score, decision, reasons)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [userId, emailKey, ip, network.public ? networkPrefix(ip) : null, result.score, result.decision,
        JSON.stringify(result.reasons)],
    );

  if (result.decision === 'block') {
    await record(null);
    const hints = [...new Set(result.reasons.map((r) => HINTS[r.code]).filter(Boolean))];
    return { status: 422, body: { error: 'signup_refused', hints } };
  }

  await db.query('BEGIN');
  try {
    const created = await db.query(
      `INSERT INTO users (email, email_normalized) VALUES ($1, $2)
       ON CONFLICT DO NOTHING RETURNING id`,
      [typed.trim(), email.normalized],
    );
    if (created.rowCount === 0) {
      await db.query('ROLLBACK');
      return { status: 409, body: { error: 'email_taken' } };
    }
    const userId = created.rows[0].id;
    // Every bonus starts held. 'review' adds a second condition on top of email verification.
    await db.query(
      `INSERT INTO bonus_grants (user_id, kind, amount, status, hold_reason) VALUES ($1, 'signup', $2, 'held', $3)`,
      [userId, deps.signupBonus, result.decision === 'review' ? 'review' : 'email_unverified'],
    );
    await record(userId);
    await db.query('COMMIT');
    return { status: 201, body: { user_id: userId, verification_required: true } };
  } catch (err) {
    await db.query('ROLLBACK');
    throw err;
  }
}
```

`HINTS` is the hint column of the score table as an object keyed by code. `email_taken` is answered for a normalized collision exactly as for a typed duplicate; if the project hides whether an address is registered, keep doing that here. Password handling, sessions and the verification email are the project's own and are left out.

## Shared networks

The users most at risk from this build are real people behind an address they share: a mobile carrier's NAT, a university, an office, a hotel, a privacy relay. Rules that protect them:

- Velocity on addresses adds review points. It never blocks alone, at any count.
- The network limit is deliberately loose. Raise it further if the audience is students or one employer.
- Privacy relay addresses score zero. The provider asks services to treat them like carrier NAT.
- Private and carrier NAT client addresses are not counted at all, because they mean the app is reading its proxy.
- Limits count attempts in a window, not accounts ever created. A family on one address can all have accounts.
- Keep an allow list for networks the user vouches for (their own office, a partner's campus) that skips the address reasons.

## What to record, and for how long

One `signup_assessments` row per attempt: the keyed email hash, the address and prefix, the score, the decision and the reasons as stored JSON. This is the answer to "why did my bonus not arrive" and the data for tuning weights. Addresses and email hashes are personal data: keep the rows for a stated period (90 days by default), delete older ones with a scheduled job, and mention the processing in the privacy policy.
