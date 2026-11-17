# Reserve and settle in five stacks

The two transactions from [reserve-commit-release.md](reserve-commit-release.md) in five common stacks: the reserve, which creates the reservation under its id and raises `reserved` only if `balance - reserved` covers the bound, and the settle, which locks the reservation, moves it out of `open` once, and posts the `usage` entry under the ledger's unique (kind, ref) key. A settle with a cost of zero is the release. The work itself runs between the two, outside any transaction.

Schema in each stack: `credit_accounts.balance` and `reserved` and `credit_reservations.amount` and `used` are 64-bit integers (`BigInt`, `BigIntegerField`, `bigInteger`, `bigint`), the reservation id is the primary key, and the ledger has a unique index on (kind, ref), as in `assets/credits-schema.sql`. The late commit after the sweeper released a reservation (section "Stale reservations" of the same reference) adds one branch to each settle: status `released` and a cost above zero posts the entry without touching `reserved`.

## Next.js App Router with Prisma

Prisma's `updateMany` cannot compare an expression of two columns with a value, so the reserve condition is raw SQL. PostgreSQL syntax.

```ts
// lib/credits.ts
import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient();
export class InsufficientCredits extends Error {}

export async function reserve(accountId: bigint, reservationId: string, amount: bigint, ttlSeconds: number): Promise<boolean> {
  return prisma.$transaction(async (tx) => {
    const created = await tx.$executeRaw`
      INSERT INTO credit_reservations (id, account_id, feature, amount, expires_at)
      VALUES (${reservationId}, ${accountId}, 'generate', ${amount}, now() + make_interval(secs => ${ttlSeconds}))
      ON CONFLICT (id) DO NOTHING`;
    if (created === 0) return false; // a retry of the same action
    const held = await tx.$executeRaw`
      UPDATE credit_accounts SET reserved = reserved + ${amount}
       WHERE account_id = ${accountId} AND balance - reserved >= ${amount}`;
    if (held !== 1) throw new InsufficientCredits(); // rolls the reservation row back
    return true;
  });
}

// cost 0 releases. Returns the credits charged.
export async function settle(reservationId: string, cost: bigint): Promise<bigint> {
  return prisma.$transaction(async (tx) => {
    const [row] = await tx.$queryRaw<{ account_id: bigint; amount: bigint; status: string }[]>`
      SELECT account_id, amount, status FROM credit_reservations WHERE id = ${reservationId} FOR UPDATE`;
    if (!row || row.status !== 'open') return 0n;
    const used = cost < row.amount ? cost : row.amount;
    await tx.$executeRaw`
      UPDATE credit_reservations SET status = ${used > 0n ? 'committed' : 'released'}, used = ${used}, settled_at = now()
       WHERE id = ${reservationId}`;
    await tx.$executeRaw`UPDATE credit_accounts SET reserved = reserved - ${row.amount} WHERE account_id = ${row.account_id}`;
    if (used > 0n) {
      const posted = await tx.$executeRaw`
        INSERT INTO credit_ledger (account_id, amount, kind, ref) VALUES (${row.account_id}, ${-used}, 'usage', ${reservationId})
        ON CONFLICT (kind, ref) DO NOTHING`;
      if (posted === 1) {
        await tx.$executeRaw`UPDATE credit_accounts SET balance = balance - ${used} WHERE account_id = ${row.account_id}`;
      }
    }
    return used;
  });
}
```

```ts
// app/api/generate/route.ts
import { NextResponse } from 'next/server';
import { InsufficientCredits, reserve, settle } from '@/lib/credits';
import { getSession } from '@/lib/session';
import { creditsFor, generate, MAX_OUTPUT_TOKENS } from '@/lib/model'; // the project's own work and price list

export const runtime = 'nodejs';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  const key = request.headers.get('idempotency-key') ?? '';
  if (!/^[\w-]{8,64}$/.test(key)) return NextResponse.json({ error: 'idempotency_key_required' }, { status: 400 });
  const { prompt } = await request.json();
  const accountId = BigInt(session.accountId);
  const reservationId = `${accountId}:${key}`;
  const bound = creditsFor({ prompt, outputTokens: MAX_OUTPUT_TOKENS });
  try {
    if (!(await reserve(accountId, reservationId, bound, 180))) {
      return NextResponse.json({ error: 'already_started' }, { status: 409 });
    }
  } catch (err) {
    if (err instanceof InsufficientCredits) return NextResponse.json({ error: 'insufficient_credits', needed: String(bound) }, { status: 402 });
    throw err;
  }
  let cost = 0n;
  try {
    const result = await generate({ prompt, maxOutputTokens: MAX_OUTPUT_TOKENS, timeoutMs: 120_000 });
    cost = creditsFor(result.usage);
    return NextResponse.json({ text: result.text, credits: String(cost) });
  } finally {
    await settle(reservationId, cost); // runs on success, error and timeout alike
  }
}
```

## Express with SQL

The node-postgres version is the code in [reserve-commit-release.md](reserve-commit-release.md). This is the same pair on MySQL 8 with `mysql2`: no `ON CONFLICT` and no `RETURNING`, the account row locked before the insert, and error 1062 as "seen before".

```js
export class InsufficientCredits extends Error {}

export async function withTransaction(pool, work) {
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    const result = await work(conn);
    await conn.commit();
    return result;
  } catch (err) {
    await conn.rollback();
    throw err;
  } finally {
    conn.release();
  }
}

export function reserve(pool, { accountId, reservationId, amount, ttlSeconds }) {
  return withTransaction(pool, async (conn) => {
    // The insert's foreign key check takes a shared lock on the account row; take it exclusively first.
    await conn.query('SELECT account_id FROM credit_accounts WHERE account_id = ? FOR UPDATE', [accountId]);
    try {
      await conn.query(
        `INSERT INTO credit_reservations (id, account_id, feature, amount, expires_at)
         VALUES (?, ?, 'generate', ?, NOW(6) + INTERVAL ? SECOND)`,
        [reservationId, accountId, amount, ttlSeconds],
      );
    } catch (err) {
      if (err.errno === 1062) return false; // a retry of the same action
      throw err;
    }
    const [held] = await conn.query(
      'UPDATE credit_accounts SET reserved = reserved + ? WHERE account_id = ? AND balance - reserved >= ?',
      [amount, accountId, amount],
    );
    if (held.affectedRows !== 1) throw new InsufficientCredits();
    return true;
  });
}

export function settle(pool, reservationId, cost) {
  return withTransaction(pool, async (conn) => {
    const [rows] = await conn.query('SELECT account_id, amount, status FROM credit_reservations WHERE id = ? FOR UPDATE', [reservationId]);
    const row = rows[0];
    if (!row || row.status !== 'open') return 0;
    const used = Math.min(cost, Number(row.amount));
    await conn.query('UPDATE credit_reservations SET status = ?, used = ?, settled_at = NOW(6) WHERE id = ?', [used > 0 ? 'committed' : 'released', used, reservationId]);
    // Account row before the ledger insert, so the insert's foreign key check finds it already locked.
    await conn.query('UPDATE credit_accounts SET reserved = reserved - ?, balance = balance - ? WHERE account_id = ?', [row.amount, used, row.account_id]);
    if (used > 0) {
      await conn.query(`INSERT INTO credit_ledger (account_id, amount, kind, ref) VALUES (?, ?, 'usage', ?)`, [row.account_id, -used, reservationId]);
    }
    return used;
  });
}
```

The status guard makes the settle happen once. The unique (kind, ref) key is the second guard: a duplicate insert fails with 1062 and rolls the whole settle back.

## Django ORM

```python
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import CreditAccount, CreditLedger, CreditReservation


class InsufficientCredits(Exception):
    pass


def reserve(account_id, reservation_id, amount, ttl_seconds):
    with transaction.atomic():
        _, created = CreditReservation.objects.get_or_create(
            id=reservation_id,
            defaults={"account_id": account_id, "feature": "generate", "amount": amount,
                      "expires_at": timezone.now() + timedelta(seconds=ttl_seconds)},
        )
        if not created:
            return False  # a retry of the same action
        held = CreditAccount.objects.filter(
            account_id=account_id, balance__gte=F("reserved") + amount
        ).update(reserved=F("reserved") + amount)
        if held != 1:
            raise InsufficientCredits()  # leaves the block: the reservation row rolls back
        return True


def settle(reservation_id, cost):
    """cost 0 releases. Returns the credits charged."""
    with transaction.atomic():
        r = CreditReservation.objects.select_for_update().filter(pk=reservation_id).first()
        if r is None or r.status != "open":
            return 0
        used = min(cost, r.amount)
        r.status, r.used, r.settled_at = ("committed" if used else "released"), used, timezone.now()
        r.save(update_fields=["status", "used", "settled_at"])
        CreditAccount.objects.filter(pk=r.account_id).update(
            reserved=F("reserved") - r.amount, balance=F("balance") - used
        )
        if used:
            CreditLedger.objects.create(account_id=r.account_id, amount=-used, kind="usage", ref=reservation_id)
        return used
```

`get_or_create` runs its insert in a savepoint, so a concurrent reserve with the same id ends in `created = False` and not in a broken transaction. The reservation row is saved with `save()` here because the row lock is held; the balance columns are never saved from a loaded object.

## Laravel Eloquent

```php
<?php
namespace App\Support;

use App\Models\CreditAccount;
use App\Models\CreditReservation;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;

final class InsufficientCredits extends \RuntimeException {}

final class Credits
{
    public static function reserve(int $accountId, string $id, int $amount, int $ttlSeconds): bool
    {
        return DB::transaction(function () use ($accountId, $id, $amount, $ttlSeconds) {
            CreditAccount::whereKey($accountId)->lockForUpdate()->firstOrFail();
            try {
                DB::transaction(fn () => CreditReservation::create([
                    'id' => $id, 'account_id' => $accountId, 'feature' => 'generate',
                    'amount' => $amount, 'expires_at' => now()->addSeconds($ttlSeconds),
                ]));
            } catch (UniqueConstraintViolationException) {
                return false; // a retry of the same action
            }
            $held = CreditAccount::whereKey($accountId)
                ->whereRaw('balance - reserved >= ?', [$amount])
                ->increment('reserved', $amount);
            if ($held !== 1) {
                throw new InsufficientCredits();
            }
            return true;
        });
    }

    /** $cost 0 releases. Returns the credits charged. */
    public static function settle(string $id, int $cost): int
    {
        return DB::transaction(function () use ($id, $cost) {
            $r = CreditReservation::whereKey($id)->lockForUpdate()->first();
            if ($r === null || $r->status !== 'open') {
                return 0;
            }
            $used = min($cost, (int) $r->amount);
            CreditReservation::whereKey($id)->update(['status' => $used > 0 ? 'committed' : 'released', 'used' => $used, 'settled_at' => now()]);
            CreditAccount::whereKey($r->account_id)->update([
                'reserved' => DB::raw('reserved - '.(int) $r->amount),
                'balance' => DB::raw('balance - '.$used),
            ]);
            if ($used > 0) {
                DB::table('credit_ledger')->insert(['account_id' => $r->account_id, 'amount' => -$used, 'kind' => 'usage', 'ref' => $id]);
            }
            return $used;
        });
    }
}
```

Both values in `DB::raw` are integers cast in PHP, never request input. The model's primary key is a string: set `$incrementing = false` and `$keyType = 'string'` on `CreditReservation`.

## Rails ActiveRecord

Not syntax-checked here: keep the shape, check it with the project's own test run.

```ruby
module Credits
  class InsufficientCredits < StandardError; end

  def self.reserve(account_id:, reservation_id:, amount:, ttl_seconds:)
    CreditAccount.transaction do
      CreditAccount.lock.find(account_id)
      begin
        CreditReservation.transaction(requires_new: true) do
          CreditReservation.create!(id: reservation_id, account_id: account_id, feature: "generate",
                                    amount: amount, expires_at: Time.current + ttl_seconds)
        end
      rescue ActiveRecord::RecordNotUnique
        next false # a retry of the same action; nothing was written
      end
      held = CreditAccount.where(account_id: account_id).where("balance - reserved >= ?", amount)
                          .update_all(["reserved = reserved + ?", amount])
      raise InsufficientCredits if held != 1
      true
    end
  end

  # cost 0 releases. Returns the credits charged.
  def self.settle(reservation_id, cost)
    CreditReservation.transaction do
      r = CreditReservation.lock.find_by(id: reservation_id)
      next 0 if r.nil? || r.status != "open"
      used = [cost, r.amount].min
      r.update_columns(status: used.positive? ? "committed" : "released", used: used, settled_at: Time.current)
      CreditAccount.where(account_id: r.account_id)
                   .update_all(["reserved = reserved - ?, balance = balance - ?", r.amount, used])
      CreditLedger.create!(account_id: r.account_id, amount: -used, kind: "usage", ref: reservation_id) if used.positive?
      used
    end
  end
end
```

## Where each check sits

| Check | Where |
| --- | --- |
| A retried action reserves once | The reservation id `<account>:<idempotency key>` as primary key: `ON CONFLICT DO NOTHING`, error 1062, `get_or_create`, or a caught unique violation in a savepoint |
| Parallel actions cannot overspend | One conditional update of `reserved` on `balance - reserved`, with the changed-row count checked, in the reserve transaction |
| The work runs unreserved never | The route calls the work only after the reserve committed |
| Settled once | The reservation row locked (`FOR UPDATE`, `select_for_update`, `lockForUpdate`, `lock`) and its status checked before any change |
| Charged once | The ledger's unique (kind, ref) key with the reservation id as ref |
| Never more than the bound | `min(cost, amount)` in the settle |
| Settled on every path | A `finally` block in the route, and the sweeper for the processes that died |
