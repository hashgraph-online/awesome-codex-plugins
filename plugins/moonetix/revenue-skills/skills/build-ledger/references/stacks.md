# The posting function in five stacks

The pattern from [schema-and-posting.md](schema-and-posting.md) in five common stacks: the unique (kind, ref) key in the framework's own schema language, integer columns, one posting function that runs inside a transaction the caller opens, and a debit that changes a row only when the balance covers it. The ORM versions lock the account row first. That gives every writer the same lock order and avoids the MySQL foreign key deadlock described in the same reference. They target PostgreSQL and MySQL; for SQLite, follow the notes in that reference.

## Next.js App Router with Prisma

```prisma
model Account {
  id      BigInt        @id
  balance BigInt        @default(0)
  entries LedgerEntry[]

  @@map("accounts")
}

model LedgerEntry {
  id        BigInt   @id @default(autoincrement())
  accountId BigInt   @map("account_id")
  amount    BigInt
  kind      String
  ref       String
  actor     String   @default("system")
  createdAt DateTime @default(now()) @map("created_at")
  account   Account  @relation(fields: [accountId], references: [id])

  @@unique([kind, ref])
  @@map("ledger")
}
```

```ts
// lib/ledger.ts
import { Prisma, PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient();
export class InsufficientFunds extends Error {}

export type Entry = { accountId: bigint; amount: bigint; kind: string; ref: string; actor?: string; allowDebt?: boolean };

// Call inside prisma.$transaction(async (tx) => ...). Returns false when (kind, ref) is already posted.
// Throwing InsufficientFunds out of the callback is what rolls the inserted row back.
export async function postEntry(tx: Prisma.TransactionClient, e: Entry): Promise<boolean> {
  if (e.amount === 0n) throw new TypeError('amount must not be zero');
  await tx.$queryRaw`SELECT id FROM accounts WHERE id = ${e.accountId} FOR UPDATE`;
  // PostgreSQL. A caught unique violation would abort a PostgreSQL transaction, ON CONFLICT does not.
  const inserted = await tx.$executeRaw`
    INSERT INTO ledger (account_id, amount, kind, ref, actor)
    VALUES (${e.accountId}, ${e.amount}, ${e.kind}, ${e.ref}, ${e.actor ?? 'system'})
    ON CONFLICT (kind, ref) DO NOTHING`;
  if (inserted === 0) return false;
  const debit = e.amount < 0n && !e.allowDebt;
  const moved = await tx.account.updateMany({
    where: debit ? { id: e.accountId, balance: { gte: -e.amount } } : { id: e.accountId },
    data: { balance: { increment: e.amount } },
  });
  if (moved.count !== 1) throw debit ? new InsufficientFunds() : new Error(`account ${e.accountId} not found`);
  return true;
}
```

```ts
// app/api/spend/route.ts
import { NextResponse } from 'next/server';
import { InsufficientFunds, postEntry, prisma } from '@/lib/ledger';
import { getSession } from '@/lib/session'; // the project's own session helper

export const runtime = 'nodejs'; // Prisma runs in the Node.js runtime, not the edge
const PRICES: Record<string, bigint> = { theme: 300n, avatar: 150n };

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  const key = request.headers.get('idempotency-key') ?? '';
  if (!/^[\w-]{8,64}$/.test(key)) return NextResponse.json({ error: 'idempotency_key_required' }, { status: 400 });
  const { item } = await request.json();
  if (typeof item !== 'string' || !Object.hasOwn(PRICES, item)) return NextResponse.json({ error: 'unknown_item' }, { status: 400 });

  const accountId = BigInt(session.accountId);
  try {
    const posted = await prisma.$transaction((tx) =>
      postEntry(tx, { accountId, amount: -PRICES[item], kind: 'spend', ref: `${accountId}:${key}` }),
    );
    return NextResponse.json({ repeated: !posted });
  } catch (err) {
    if (err instanceof InsufficientFunds) return NextResponse.json({ error: 'insufficient_balance' }, { status: 402 });
    throw err;
  }
}
```

- On MySQL, `ON CONFLICT` does not exist: replace the raw insert with `tx.ledgerEntry.create(...)` and treat `Prisma.PrismaClientKnownRequestError` with code `P2002` as "already posted". InnoDB rolls back only that statement. Do not use `createMany({ skipDuplicates: true })` there: on MySQL it is `INSERT IGNORE`.
- Prisma returns `BigInt` columns as `bigint`. Keep amounts as `bigint` from the price table to the response, and convert with `String()` for JSON.

## Express with SQL

The posting function is the node-postgres one in [schema-and-posting.md](schema-and-posting.md). The route decides the transaction boundary and maps the error after the rollback.

```js
import express from 'express';
import { InsufficientFunds, postEntry, withTransaction } from './ledger.mjs';

const PRICES = { theme: 300, avatar: 150 };

export function spendRouter(pool) {
  const router = express.Router();
  router.post('/api/spend', express.json(), async (req, res, next) => {
    const key = req.get('Idempotency-Key') ?? '';
    if (!/^[\w-]{8,64}$/.test(key)) return res.status(400).json({ error: 'idempotency_key_required' });
    const item = req.body?.item;
    if (typeof item !== 'string' || !Object.hasOwn(PRICES, item)) return res.status(400).json({ error: 'unknown_item' });
    const accountId = req.user.accountId; // from the session, never from the body
    try {
      const posted = await withTransaction(pool, (tx) =>
        postEntry(tx, { accountId, amount: -PRICES[item], kind: 'spend', ref: `${accountId}:${key}` }),
      );
      res.json({ repeated: !posted });
    } catch (err) {
      if (err instanceof InsufficientFunds) return res.status(402).json({ error: 'insufficient_balance' });
      next(err);
    }
  });
  return router;
}
```

## Django ORM

```python
# models.py
from django.db import models


class Account(models.Model):
    balance = models.BigIntegerField(default=0)


class LedgerEntry(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    amount = models.BigIntegerField()
    kind = models.CharField(max_length=64)
    ref = models.CharField(max_length=191)
    actor = models.CharField(max_length=64, default="system")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger"
        constraints = [models.UniqueConstraint(fields=["kind", "ref"], name="ledger_kind_ref_unique")]
```

```python
# ledger.py
from django.db import IntegrityError, transaction
from django.db.models import F

from .models import Account, LedgerEntry


class InsufficientFunds(Exception):
    pass


def post_entry(account_id, amount, kind, ref, actor="system", allow_debt=False):
    """Call inside transaction.atomic(). Returns False when (kind, ref) is already posted."""
    if not isinstance(amount, int) or isinstance(amount, bool) or amount == 0:
        raise ValueError("amount must be a non-zero whole number")
    Account.objects.select_for_update().only("id").get(pk=account_id)
    try:
        with transaction.atomic():  # a savepoint: a duplicate rolls back only this insert
            LedgerEntry.objects.create(account_id=account_id, amount=amount, kind=kind, ref=ref, actor=actor)
    except IntegrityError:
        return False
    rows = Account.objects.filter(pk=account_id)
    if amount < 0 and not allow_debt:
        rows = rows.filter(balance__gte=-amount)
    if rows.update(balance=F("balance") + amount) != 1:
        raise InsufficientFunds()
    return True
```

```python
# views.py
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .ledger import InsufficientFunds, post_entry

PRICES = {"theme": 300, "avatar": 150}


@require_POST
@login_required
def spend(request):
    key = request.headers.get("Idempotency-Key", "")
    item = request.POST.get("item", "")
    if not (8 <= len(key) <= 64) or item not in PRICES:
        return JsonResponse({"error": "bad_request"}, status=400)
    account_id = request.user.account_id
    try:
        with transaction.atomic():
            posted = post_entry(account_id, -PRICES[item], "spend", f"{account_id}:{key}")
    except InsufficientFunds:
        return JsonResponse({"error": "insufficient_balance"}, status=402)
    return JsonResponse({"repeated": not posted})
```

With `ATOMIC_REQUESTS = True` the view already runs in a transaction, and the `atomic()` block above becomes a savepoint. `InsufficientFunds` still has to leave that block, so that the savepoint rolls back the ledger row.

## Laravel Eloquent

```php
<?php
// database/migrations/xxxx_create_ledger_table.php, inside up()
Schema::create('ledger', function (Blueprint $table) {
    $table->id();
    $table->foreignId('account_id')->constrained('accounts');
    $table->bigInteger('amount');
    $table->string('kind', 64);
    $table->string('ref', 191)->collation('utf8mb4_bin'); // MySQL: case-sensitive refs; drop on PostgreSQL
    $table->string('actor', 64)->default('system');
    $table->timestamp('created_at')->useCurrent();
    $table->unique(['kind', 'ref']);
});
```

```php
<?php
namespace App\Support;

use App\Models\Account;
use App\Models\LedgerEntry; // $guarded = [], $timestamps = false
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;

final class InsufficientFunds extends \RuntimeException {}

final class Ledger
{
    /** Call inside DB::transaction(). Returns false when (kind, ref) is already posted. */
    public static function post(int $accountId, int $amount, string $kind, string $ref, string $actor = 'system', bool $allowDebt = false): bool
    {
        if ($amount === 0) {
            throw new \InvalidArgumentException('amount must not be zero');
        }
        Account::whereKey($accountId)->lockForUpdate()->firstOrFail();
        try {
            // A nested transaction is a savepoint: a duplicate rolls back only this insert.
            DB::transaction(fn () => LedgerEntry::create(compact('amount', 'kind', 'ref', 'actor') + ['account_id' => $accountId]));
        } catch (UniqueConstraintViolationException) {
            return false;
        }
        if ($amount > 0 || $allowDebt) {
            Account::whereKey($accountId)->increment('balance', $amount);
            return true;
        }
        $taken = Account::whereKey($accountId)->where('balance', '>=', -$amount)->decrement('balance', -$amount);
        if ($taken !== 1) {
            throw new InsufficientFunds();
        }
        return true;
    }
}
```

```php
<?php
namespace App\Http\Controllers;

use App\Support\InsufficientFunds;
use App\Support\Ledger;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

final class SpendController extends Controller
{
    private const PRICES = ['theme' => 300, 'avatar' => 150];

    public function __invoke(Request $request): JsonResponse
    {
        $key = (string) $request->header('Idempotency-Key');
        $price = self::PRICES[(string) $request->input('item')] ?? null;
        if (preg_match('/^[\w-]{8,64}$/', $key) !== 1 || $price === null) {
            return response()->json(['error' => 'bad_request'], 400);
        }
        $accountId = $request->user()->account_id; // from the session
        try {
            $posted = DB::transaction(fn () => Ledger::post($accountId, -$price, 'spend', "{$accountId}:{$key}"));
        } catch (InsufficientFunds) {
            return response()->json(['error' => 'insufficient_balance'], 402);
        }
        return response()->json(['repeated' => !$posted]);
    }
}
```

Where `UniqueConstraintViolationException` does not exist yet, catch `QueryException` and check `errorInfo[1] === 1062` (MySQL) or SQLSTATE `23505` (PostgreSQL). Do not use `insertOrIgnore()` on MySQL: it is `INSERT IGNORE`.

## Rails ActiveRecord

Not syntax-checked here: keep the shape, check it with the project's own test run.

```ruby
# db/migrate/xxxx_create_ledger.rb, inside change
create_table :ledger do |t|
  t.references :account, null: false, foreign_key: true
  t.bigint :amount, null: false
  t.string :kind, null: false
  t.string :ref, null: false
  t.string :actor, null: false, default: "system"
  t.datetime :created_at, null: false, default: -> { "CURRENT_TIMESTAMP" }
end
add_index :ledger, [:kind, :ref], unique: true
```

```ruby
module Ledger
  class InsufficientFunds < StandardError; end

  # Call inside Account.transaction. Returns false when (kind, ref) is already posted.
  def self.post(account_id:, amount:, kind:, ref:, actor: "system", allow_debt: false)
    raise ArgumentError, "amount must be a non-zero integer" unless amount.is_a?(Integer) && amount != 0
    Account.lock.find(account_id) # SELECT ... FOR UPDATE
    begin
      LedgerEntry.transaction(requires_new: true) do # a savepoint
        LedgerEntry.create!(account_id: account_id, amount: amount, kind: kind, ref: ref, actor: actor)
      end
    rescue ActiveRecord::RecordNotUnique
      return false
    end
    scope = Account.where(id: account_id)
    scope = scope.where("balance >= ?", -amount) if amount.negative? && !allow_debt
    raise InsufficientFunds if scope.update_all(["balance = balance + ?", amount]) != 1
    true
  end
end

# In the controller.
def spend
  key = request.headers["Idempotency-Key"].to_s
  price = PRICES[params[:item].to_s]
  return head(:bad_request) unless key.match?(/\A[\w-]{8,64}\z/) && price
  account_id = current_user.account_id
  posted = Account.transaction { Ledger.post(account_id: account_id, amount: -price, kind: "spend", ref: "#{account_id}:#{key}") }
  render json: { repeated: !posted }
rescue Ledger::InsufficientFunds
  render json: { error: "insufficient_balance" }, status: :payment_required
end
```

## Where each check sits

| Check | Prisma | Express + SQL | Django | Laravel | Rails |
| --- | --- | --- | --- | --- | --- |
| Transaction | `prisma.$transaction` in the route | `withTransaction` in the route | `transaction.atomic()` in the view | `DB::transaction` in the controller | `Account.transaction` in the controller |
| Lock order | `$queryRaw ... FOR UPDATE` | the debit's own row lock | `select_for_update()` | `lockForUpdate()` | `Account.lock.find` |
| Once | `@@unique([kind, ref])` and `ON CONFLICT DO NOTHING` | `UNIQUE (kind, ref)` and `ON CONFLICT DO NOTHING` | `UniqueConstraint` and a savepoint | `unique()` and a savepoint | unique index and `requires_new` |
| No overdraw | `updateMany` with `gte`, `count` checked | `WHERE balance >= $1`, `rowCount` checked | `filter(balance__gte=)`, `update()` count | `where()->decrement()` count | `update_all` count |
| Amount | `bigint` from the server's price table | integer from the price table | `int` from the price table | `int` from the price table | `Integer` from the price table |

In every stack the debit error leaves the transaction block as an exception, the route maps it to 402 after the rollback, and the account comes from the session.
