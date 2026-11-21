# Attribution and the reward in five stacks

Two places decide whether a referral pays more than once, shown in five common stacks:

- **Attribution at sign-up.** The referral row is written in the transaction that creates the account, keyed by the referred account, with the referrer looked up from the code on the server. A second attach, an unknown code and the account's own code change nothing, and none of them fails the sign-up.
- **The reward.** A guarded move from `qualified` to `rewarded` (or `blocked` when the cap is reached), compared with the database clock, under a lock on the referrer's account so the cap is counted correctly, and one ledger entry of kind `referral` with the referred account's id as reference.

The full life of a referral, the threshold and the reversal are in [rewards-and-reversals.md](rewards-and-reversals.md); codes and the same-person checks in [codes-and-attribution.md](codes-and-attribution.md). The ledger entry goes through the project's posting function (the `build-ledger` skill builds it). `normalizeCode` is the function from the codes reference.

The constraints, in each stack's schema language:

| Rule | Prisma | Django | Laravel migration | Rails migration |
| --- | --- | --- | --- | --- |
| One referrer per account, for good | `referredId BigInt @id` | `OneToOneField(Account, primary_key=True)` | `$table->unsignedBigInteger('referred_id')->primary()` | `create_table :referrals, primary_key: :referred_id` |
| Not your own referrer | raw `CHECK (referred_id <> referrer_id)` in the migration | a `CheckConstraint` that the two fields differ | `DB::statement('ALTER TABLE referrals ADD CHECK (referred_id <> referrer_id)')` | `add_check_constraint :referrals, "referred_id <> referrer_id"` |
| One reward per referred account | the ledger's unique (kind, ref) | the same | the same | the same |
| Amounts | `BigInt` | `BigIntegerField` | `bigInteger` | `bigint` |

## Next.js App Router with Prisma

```ts
// lib/referrals.ts
import type { Prisma } from '@prisma/client';
import { postEntry } from '@/lib/ledger';
import { normalizeCode } from '@/lib/referral-codes';

export const PROGRAM = { bonus: 500n, maxRewardsPer30Days: 20 };

// Call inside the sign-up transaction. A bad code returns null and never fails the sign-up.
export async function attachReferral(tx: Prisma.TransactionClient, referredId: bigint, code: string | null) {
  const normalized = normalizeCode(code);
  if (!normalized) return null;
  const owner = await tx.referralCode.findUnique({ where: { code: normalized } });
  if (!owner || owner.accountId === referredId) return null;
  const inserted = await tx.$executeRaw`
    INSERT INTO referrals (referred_id, referrer_id, code) VALUES (${referredId}, ${owner.accountId}, ${normalized})
    ON CONFLICT (referred_id) DO NOTHING`;
  return inserted === 1 ? owner.accountId : null;
}

// Call inside a transaction, from the settle function or the scheduled job.
export async function payReward(tx: Prisma.TransactionClient, referredId: bigint, referrerId: bigint) {
  await tx.$queryRaw`SELECT id FROM accounts WHERE id = ${referrerId} FOR UPDATE`;
  const recent = await tx.referral.count({
    where: { referrerId, status: 'rewarded', rewardedAt: { gt: new Date(Date.now() - 30 * 86_400_000) } },
  });
  const hold = recent >= PROGRAM.maxRewardsPer30Days ? 'referrer_cap' : null;
  // reward_at is compared with the database clock, so a server clock that is off cannot skip the hold.
  const moved = await tx.$executeRaw`
    UPDATE referrals SET status = ${hold ? 'blocked' : 'rewarded'}, blocked_reason = ${hold},
           rewarded_at = CASE WHEN ${hold === null} THEN now() ELSE NULL END
     WHERE referred_id = ${referredId} AND status = 'qualified' AND reward_at <= now()`;
  if (moved !== 1) return 'qualified';
  if (hold) return 'blocked';
  await postEntry(tx, { accountId: referrerId, amount: PROGRAM.bonus, kind: 'referral', ref: String(referredId) });
  return 'rewarded';
}
```

```ts
// app/api/signup/route.ts: the account and its referral in one transaction.
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/ledger';
import { attachReferral } from '@/lib/referrals';
import { validateSignup } from '@/lib/signup'; // the project's own checks, normalized email and password hash

export const runtime = 'nodejs';

export async function POST(request: Request) {
  const form = await request.formData();
  const input = await validateSignup(form);
  if (!input.ok) return NextResponse.json({ error: input.error }, { status: 400 });
  const typed = form.get('ref');
  const code = typeof typed === 'string' && typed !== '' ? typed : (await cookies()).get('ref')?.value ?? null;
  const user = await prisma.$transaction(async (tx) => {
    const created = await tx.user.create({ data: { email: input.email, emailNormalized: input.emailNormalized, passwordHash: input.passwordHash } });
    await attachReferral(tx, created.id, code);
    return created;
  });
  return NextResponse.json({ id: String(user.id) }, { status: 201 });
}
```

`cookies()` is awaited as in Next.js 15 and newer; on Next.js 14 it is synchronous.

## Express with SQL

`attachReferral` and `settleReferral` are the node-postgres functions in the two references. The route shows where the transaction opens.

```js
import express from 'express';
import { attachReferral } from './referrals.mjs';
import { withTransaction } from './ledger.mjs';

export function signupRouter(pool, createAccount) {
  const router = express.Router();
  router.post('/api/signup', express.json(), async (req, res, next) => {
    try {
      const account = await withTransaction(pool, async (tx) => {
        const created = await createAccount(tx, req.body); // the project's own sign-up insert
        // The code from the form, else from the first-party cookie. Never a referrer id from the body.
        await attachReferral(tx, { referredId: created.id, code: req.body?.ref ?? req.cookies?.ref ?? null });
        return created;
      });
      res.status(201).json({ id: account.id });
    } catch (err) {
      next(err);
    }
  });
  return router;
}
```

## Django ORM

```python
from datetime import timedelta

from django.db.models.functions import Now
from django.utils import timezone

from .ledger import post_entry
from .models import Account, Referral, ReferralCode
from .referral_codes import normalize_code

BONUS = 500
MAX_REWARDS_PER_30_DAYS = 20


def attach_referral(referred_id, code):
    """Call inside the sign-up's transaction.atomic(). Returns the referrer's id or None."""
    normalized = normalize_code(code)
    if not normalized:
        return None
    owner = ReferralCode.objects.filter(code=normalized).values_list("account_id", flat=True).first()
    if owner is None or owner == referred_id:
        return None
    _, created = Referral.objects.get_or_create(
        referred_id=referred_id, defaults={"referrer_id": owner, "code": normalized}
    )
    return owner if created else None


def pay_reward(referred_id, referrer_id):
    """Call inside transaction.atomic()."""
    Account.objects.select_for_update().only("id").get(pk=referrer_id)
    recent = Referral.objects.filter(
        referrer_id=referrer_id, status="rewarded", rewarded_at__gt=timezone.now() - timedelta(days=30)
    ).count()
    hold = "referrer_cap" if recent >= MAX_REWARDS_PER_30_DAYS else None
    moved = Referral.objects.filter(referred_id=referred_id, status="qualified", reward_at__lte=Now()).update(
        status="blocked" if hold else "rewarded", blocked_reason=hold, rewarded_at=None if hold else Now()
    )
    if moved != 1:
        return "qualified"
    if hold:
        return "blocked"
    post_entry(referrer_id, BONUS, "referral", str(referred_id))
    return "rewarded"
```

The sign-up view creates the user and calls `attach_referral` inside one `with transaction.atomic():` block, reading the code from the form or the cookie.

## Laravel Eloquent

```php
<?php
namespace App\Support;

use App\Models\Account;
use App\Models\Referral;
use App\Models\ReferralCode;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;

final class Referrals
{
    public const BONUS = 500;
    public const MAX_REWARDS_PER_30_DAYS = 20;

    /** Call inside the sign-up's DB::transaction(). Returns the referrer's id or null. */
    public static function attach(int $referredId, ?string $code): ?int
    {
        $normalized = ReferralCodes::normalize($code);
        if ($normalized === null) {
            return null;
        }
        $owner = ReferralCode::where('code', $normalized)->value('account_id');
        if ($owner === null || (int) $owner === $referredId) {
            return null;
        }
        try {
            DB::transaction(fn () => Referral::create(['referred_id' => $referredId, 'referrer_id' => $owner, 'code' => $normalized]));
        } catch (UniqueConstraintViolationException) {
            return null;
        }
        return (int) $owner;
    }

    /** Call inside DB::transaction(). */
    public static function payReward(int $referredId, int $referrerId): string
    {
        Account::whereKey($referrerId)->lockForUpdate()->firstOrFail();
        $recent = Referral::where('referrer_id', $referrerId)->where('status', 'rewarded')
            ->where('rewarded_at', '>', now()->subDays(30))->count();
        $hold = $recent >= self::MAX_REWARDS_PER_30_DAYS ? 'referrer_cap' : null;
        $moved = Referral::whereKey($referredId)->where('status', 'qualified')
            ->whereRaw('reward_at <= CURRENT_TIMESTAMP')
            ->update([
                'status' => $hold === null ? 'rewarded' : 'blocked',
                'blocked_reason' => $hold,
                'rewarded_at' => $hold === null ? DB::raw('CURRENT_TIMESTAMP') : null,
            ]);
        if ($moved !== 1) {
            return 'qualified';
        }
        if ($hold !== null) {
            return 'blocked';
        }
        Ledger::post($referrerId, self::BONUS, 'referral', (string) $referredId);
        return 'rewarded';
    }
}
```

`Referral` has `$primaryKey = 'referred_id'` and `$incrementing = false`. The sign-up controller wraps the user insert and `Referrals::attach($user->id, $request->input('ref') ?? $request->cookie('ref'))` in one `DB::transaction()`.

## Rails ActiveRecord

Not syntax-checked here: keep the shape, check it with the project's own test run.

```ruby
module Referrals
  BONUS = 500
  MAX_REWARDS_PER_30_DAYS = 20

  # Call inside the sign-up's transaction. Returns the referrer's id or nil.
  def self.attach(referred_id:, code:)
    normalized = ReferralCodes.normalize(code)
    return nil if normalized.nil?
    owner = ReferralCode.where(code: normalized).pick(:account_id)
    return nil if owner.nil? || owner == referred_id
    Referral.transaction(requires_new: true) do
      Referral.create!(referred_id: referred_id, referrer_id: owner, code: normalized)
    end
    owner
  rescue ActiveRecord::RecordNotUnique
    nil
  end

  # Call inside a transaction.
  def self.pay_reward(referred_id:, referrer_id:)
    Account.lock.find(referrer_id)
    recent = Referral.where(referrer_id: referrer_id, status: "rewarded")
                     .where("rewarded_at > ?", 30.days.ago).count
    hold = recent >= MAX_REWARDS_PER_30_DAYS ? "referrer_cap" : nil
    moved = Referral.where(referred_id: referred_id, status: "qualified").where("reward_at <= CURRENT_TIMESTAMP")
                    .update_all(hold ? ["status = 'blocked', blocked_reason = ?", hold]
                                     : "status = 'rewarded', rewarded_at = CURRENT_TIMESTAMP")
    return "qualified" if moved != 1
    return "blocked" if hold
    Ledger.post(account_id: referrer_id, amount: BONUS, kind: "referral", ref: referred_id.to_s)
    "rewarded"
  end
end
```

`Referral` declares `self.primary_key = "referred_id"`. The sign-up controller creates the user and calls `Referrals.attach` inside one `User.transaction` block.

## Where each check sits

| Check | Where |
| --- | --- |
| Attribution once, at sign-up | The referral insert in the sign-up transaction, keyed by the referred account; no other code path writes the row |
| Referrer from a code only | The code lookup on the server; the request carries no referrer id that is read |
| Not your own referrer | The id comparison in the attach, and the check constraint |
| The hold is respected | `reward_at <= now()` in the guarded update, with the database clock |
| The cap holds in parallel | The referrer's account row locked before the count |
| One reward per referred account | The guarded move from `qualified`, and the ledger's unique (kind, ref) with the referred id as ref |
