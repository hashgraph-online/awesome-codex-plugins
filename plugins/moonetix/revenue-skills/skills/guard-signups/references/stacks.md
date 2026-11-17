# Promo codes and held bonuses in five stacks

The once-only rules from [bonuses-promos-trials.md](bonuses-promos-trials.md) in five common stacks. Two patterns carry them:

- **The promo redemption.** One transaction: insert the redemption under the unique (code, user) key, take one use from the code's counter with a conditional update, credit the amount stored on the code. A repeated redemption inserts nothing; the last use of a code goes to one account.
- **The bonus release.** A conditional move of the grant from `held` to `released`, and the credit only when that move changed a row.

Like the reference, the examples credit a `balance` column to stay short. With a ledger, post the same amounts through its posting function with the grant's key as the reference (`promo:<code>:<user id>`, `signup:<user id>`).

The keys, in each stack's schema language:

| Rule | Prisma | Django | Laravel migration | Rails migration |
| --- | --- | --- | --- | --- |
| One account per normalized email | `emailNormalized String? @unique` | `email_normalized = models.CharField(max_length=254, null=True, unique=True)` | `$table->string('email_normalized')->nullable()->unique()` | `add_index :users, :email_normalized, unique: true` |
| One redemption per account and code | `@@id([code, userId])` | `UniqueConstraint(fields=["code", "user"], name=...)` | `$table->primary(['code', 'user_id'])` | `create_table :promo_redemptions, primary_key: [:code, :user_id]` |
| One grant per account and kind | `@@id([userId, kind])` | `UniqueConstraint(fields=["user", "kind"], name=...)` | `$table->primary(['user_id', 'kind'])` | `primary_key: [:user_id, :kind]` |
| Amounts | `BigInt` | `BigIntegerField` | `bigInteger` | `bigint` |

## Next.js App Router with Prisma

PostgreSQL syntax.

```ts
// lib/promos.ts
import { prisma } from '@/lib/db';

class Refused extends Error {}

// Returns 'redeemed', 'unknown_code', 'already_redeemed' or 'code_used_up'.
export async function redeemPromo(userId: bigint, input: string): Promise<string> {
  const code = input.trim().toUpperCase();
  const promo = await prisma.promoCode.findFirst({
    where: { code, OR: [{ expiresAt: null }, { expiresAt: { gt: new Date() } }] },
  });
  if (!promo) return 'unknown_code';
  try {
    return await prisma.$transaction(async (tx) => {
      const claimed = await tx.$executeRaw`
        INSERT INTO promo_redemptions (code, user_id, amount) VALUES (${code}, ${userId}, ${promo.amount})
        ON CONFLICT (code, user_id) DO NOTHING`;
      if (claimed === 0) throw new Refused('already_redeemed');
      // Checked and taken in one statement: two accounts cannot both take the last use.
      const taken = await tx.$executeRaw`
        UPDATE promo_codes SET redeemed = redeemed + 1 WHERE code = ${code} AND redeemed < max_redemptions`;
      if (taken !== 1) throw new Refused('code_used_up'); // the throw rolls the redemption row back
      await tx.user.update({ where: { id: userId }, data: { balance: { increment: promo.amount } } });
      return 'redeemed';
    });
  } catch (err) {
    if (err instanceof Refused) return err.message;
    throw err;
  }
}

// Called when the grant's conditions are met, checked on the server from stored state. Safe to call twice.
export async function releaseBonus(userId: bigint, kind: string): Promise<boolean> {
  return prisma.$transaction(async (tx) => {
    const rows = await tx.$queryRaw<{ amount: bigint }[]>`
      UPDATE bonus_grants SET status = 'released', decided_at = now()
       WHERE user_id = ${userId} AND kind = ${kind} AND status = 'held'
      RETURNING amount`;
    if (rows.length !== 1) return false;
    await tx.user.update({ where: { id: userId }, data: { balance: { increment: rows[0].amount } } });
    return true;
  });
}
```

The route handler takes the user from the session and the code from the body, and counts failed attempts per account and per address before it calls `redeemPromo` (section "Promo codes" of the reference).

## Express with SQL

node-postgres. The SQL is the one in the reference; the route decides the transaction and the answers.

```js
import express from 'express';

export function promoRouter(pool) {
  const router = express.Router();
  router.post('/api/promo', express.json(), async (req, res, next) => {
    const code = String(req.body?.code ?? '').trim().toUpperCase();
    const userId = req.user.id; // from the session
    const tx = await pool.connect();
    try {
      await tx.query('BEGIN');
      const promo = await tx.query(
        'SELECT amount FROM promo_codes WHERE code = $1 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)',
        [code],
      );
      if (promo.rowCount === 0) {
        await tx.query('ROLLBACK');
        return res.status(404).json({ error: 'unknown_code' });
      }
      const amount = promo.rows[0].amount;
      const claimed = await tx.query(
        'INSERT INTO promo_redemptions (code, user_id, amount) VALUES ($1, $2, $3) ON CONFLICT (code, user_id) DO NOTHING',
        [code, userId, amount],
      );
      const taken = claimed.rowCount === 1
        ? await tx.query('UPDATE promo_codes SET redeemed = redeemed + 1 WHERE code = $1 AND redeemed < max_redemptions', [code])
        : null;
      if (taken?.rowCount !== 1) {
        await tx.query('ROLLBACK');
        return res.status(409).json({ error: claimed.rowCount === 1 ? 'code_used_up' : 'already_redeemed' });
      }
      await tx.query('UPDATE users SET balance = balance + $1 WHERE id = $2', [amount, userId]);
      await tx.query('COMMIT');
      res.json({ redeemed: true });
    } catch (err) {
      await tx.query('ROLLBACK');
      next(err);
    } finally {
      tx.release();
    }
  });
  return router;
}
```

## Django ORM

```python
from django.db import transaction
from django.db.models import F, Q
from django.db.models.functions import Now

from .models import BonusGrant, PromoCode, PromoRedemption, User


class _Refused(Exception):
    pass


def redeem_promo(user_id, raw):
    code = raw.strip().upper()
    promo = PromoCode.objects.filter(code=code).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=Now())).first()
    if promo is None:
        return "unknown_code"
    try:
        with transaction.atomic():
            _, created = PromoRedemption.objects.get_or_create(code_id=code, user_id=user_id, defaults={"amount": promo.amount})
            if not created:
                raise _Refused("already_redeemed")
            taken = PromoCode.objects.filter(code=code, redeemed__lt=F("max_redemptions")).update(redeemed=F("redeemed") + 1)
            if taken != 1:
                raise _Refused("code_used_up")  # leaves the block: the redemption row rolls back
            User.objects.filter(pk=user_id).update(balance=F("balance") + promo.amount)
            return "redeemed"
    except _Refused as refused:
        return str(refused)


def release_bonus(user_id, kind):
    with transaction.atomic():
        moved = BonusGrant.objects.filter(user_id=user_id, kind=kind, status="held").update(
            status="released", decided_at=Now()
        )
        if moved != 1:
            return False
        amount = BonusGrant.objects.values_list("amount", flat=True).get(user_id=user_id, kind=kind)
        User.objects.filter(pk=user_id).update(balance=F("balance") + amount)
        return True
```

## Laravel Eloquent

The two tables have composite keys, so the writes use the query builder.

```php
<?php
namespace App\Support;

use App\Models\PromoCode;
use App\Models\User;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;

final class PromoRefused extends \RuntimeException {}

final class Promos
{
    public static function redeem(int $userId, string $input): string
    {
        $code = strtoupper(trim($input));
        $promo = PromoCode::whereKey($code)
            ->where(fn ($q) => $q->whereNull('expires_at')->orWhere('expires_at', '>', now()))
            ->first();
        if ($promo === null) {
            return 'unknown_code';
        }
        try {
            return DB::transaction(function () use ($userId, $code, $promo) {
                try {
                    DB::transaction(fn () => DB::table('promo_redemptions')->insert(['code' => $code, 'user_id' => $userId, 'amount' => $promo->amount]));
                } catch (UniqueConstraintViolationException) {
                    throw new PromoRefused('already_redeemed');
                }
                $taken = PromoCode::whereKey($code)->whereColumn('redeemed', '<', 'max_redemptions')->increment('redeemed');
                if ($taken !== 1) {
                    throw new PromoRefused('code_used_up');
                }
                User::whereKey($userId)->increment('balance', (int) $promo->amount);
                return 'redeemed';
            });
        } catch (PromoRefused $refused) {
            return $refused->getMessage();
        }
    }

    public static function releaseBonus(int $userId, string $kind): bool
    {
        return DB::transaction(function () use ($userId, $kind) {
            $grant = DB::table('bonus_grants')->where('user_id', $userId)->where('kind', $kind);
            $moved = (clone $grant)->where('status', 'held')->update(['status' => 'released', 'decided_at' => now()]);
            if ($moved !== 1) {
                return false;
            }
            User::whereKey($userId)->increment('balance', (int) $grant->value('amount'));
            return true;
        });
    }
}
```

## Rails ActiveRecord

Not syntax-checked here: keep the shape, check it with the project's own test run. Composite primary keys need Rails 7.1 or newer.

```ruby
module Promos
  class Refused < StandardError; end

  def self.redeem(user_id:, input:)
    code = input.to_s.strip.upcase
    promo = PromoCode.where(code: code).where("expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP").first
    return "unknown_code" if promo.nil?
    PromoCode.transaction do
      begin
        PromoRedemption.transaction(requires_new: true) do
          PromoRedemption.create!(code: code, user_id: user_id, amount: promo.amount)
        end
      rescue ActiveRecord::RecordNotUnique
        raise Refused, "already_redeemed"
      end
      taken = PromoCode.where(code: code).where("redeemed < max_redemptions").update_all("redeemed = redeemed + 1")
      raise Refused, "code_used_up" if taken != 1
      User.where(id: user_id).update_all(["balance = balance + ?", promo.amount])
      "redeemed"
    end
  rescue Refused => refused
    refused.message
  end

  def self.release_bonus(user_id:, kind:)
    BonusGrant.transaction do
      moved = BonusGrant.where(user_id: user_id, kind: kind, status: "held")
                        .update_all(["status = 'released', decided_at = ?", Time.current])
      next false if moved != 1
      amount = BonusGrant.where(user_id: user_id, kind: kind).pick(:amount)
      User.where(id: user_id).update_all(["balance = balance + ?", amount])
      true
    end
  end
end
```

## Where each check sits

| Check | Where |
| --- | --- |
| One account per person's email | The unique index on the normalized email, written in the same statement as the address on every path that creates an account or changes an email |
| One redemption per account | The unique (code, user) key; the duplicate is detected by the insert, never by a lookup before it |
| The cap holds in parallel | `redeemed < max_redemptions` in the update, with the changed-row count checked |
| No half redemption | A refusal leaves the transaction as an exception (or an explicit rollback), which removes the redemption row |
| The amount | Read from the code's row or the grant's row, never from the request |
| A bonus enters the balance once | The conditional move from `held`, with the credit only when it changed a row |
