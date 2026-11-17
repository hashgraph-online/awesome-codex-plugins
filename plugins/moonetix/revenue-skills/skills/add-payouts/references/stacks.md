# The payout request and the send claim in five stacks

The two steps of [payout-state-machine.md](payout-state-machine.md) that decide whether money leaves twice, in five common stacks:

- **The request.** One transaction under a lock on the account row: return the earlier payout for a repeated request key, run the checks, post the `payout` ledger entry, insert the row as `pending` or `in_review`. It commits before the provider is called.
- **The claim.** One conditional statement moves `pending` to `sending` and checks the account's state again. Only the caller that changed the row calls the provider, with the payout id as the idempotency key.

`checkPayout` stands for the project's limit, hold and destination checks from [limits-holds-and-destinations.md](limits-holds-and-destinations.md). It returns a refusal, or the destination and the status to start in. The ledger debit goes through the project's posting function (the `build-ledger` skill builds it), which throws when the balance does not cover the amount. Amounts are 64-bit integers in the ledger's unit, and `payouts` has the unique key (account_id, request_key) from `assets/payouts-schema.sql`.

## Next.js App Router with Prisma

```prisma
model Payout {
  id            String   @id
  accountId     BigInt   @map("account_id")
  requestKey    String   @map("request_key")
  amount        BigInt
  currency      String
  payoutMinor   BigInt   @map("payout_minor")
  destinationId BigInt   @map("destination_id")
  destination   String
  status        String
  attempts      Int      @default(0)
  createdAt     DateTime @default(now()) @map("created_at")
  sentAt        DateTime? @map("sent_at")

  @@unique([accountId, requestKey])
  @@map("payouts")
}
```

```ts
// lib/payouts.ts
import { randomUUID } from 'node:crypto';
import { InsufficientFunds, postEntry, prisma } from '@/lib/ledger';
import { checkPayout, POLICY } from '@/lib/payout-policy';

export async function requestPayout(accountId: bigint, requestKey: string, amount: bigint) {
  try {
    return await prisma.$transaction(async (tx) => {
      // This account's requests take turns from here on, so every check sees the payouts before it.
      await tx.$queryRaw`SELECT id FROM accounts WHERE id = ${accountId} FOR UPDATE`;
      const repeat = await tx.payout.findUnique({ where: { accountId_requestKey: { accountId, requestKey } } });
      if (repeat) return { payoutId: repeat.id, status: repeat.status, repeated: true };

      const check = await checkPayout(tx, accountId, amount);
      if ('refused' in check) return check;

      const payoutId = randomUUID();
      await postEntry(tx, { accountId, amount: -amount, kind: 'payout', ref: payoutId });
      await tx.payout.create({
        data: {
          id: payoutId, accountId, requestKey, amount, currency: POLICY.currency,
          payoutMinor: amount / POLICY.unitsPerMinor, destinationId: check.destination.id,
          destination: check.destination.snapshot, status: check.status,
        },
      });
      return { payoutId, status: check.status };
    });
  } catch (err) {
    if (err instanceof InsufficientFunds) return { refused: 'insufficient_balance' };
    throw err;
  }
}

// One statement. Of any number of workers and retries, one gets true and calls the provider.
export async function claimForSending(payoutId: string): Promise<boolean> {
  const claimed = await prisma.$executeRaw`
    UPDATE payouts SET status = 'sending', attempts = attempts + 1, sent_at = now()
     WHERE id = ${payoutId} AND status = 'pending'
       AND EXISTS (SELECT 1 FROM users u WHERE u.id = payouts.account_id AND u.status = 'active')`;
  return claimed === 1;
}
```

The route handler reads the account from the session, the amount from the body as a whole number, and the request key from the `Idempotency-Key` header, calls `requestPayout`, and after it returns starts the send (a queue job or a direct call to `sendPayout`). It answers with the payout id and its status, never "paid".

## Express with SQL

`requestPayout` and `sendPayout` are the node-postgres functions in [payout-state-machine.md](payout-state-machine.md). The route sits between them: the request transaction has committed before the send starts.

```js
import express from 'express';
import { requestPayout, sendPayout } from './payouts.mjs';

export function payoutRouter(pool, provider, policy) {
  const router = express.Router();
  router.post('/api/payouts', express.json(), async (req, res, next) => {
    const requestKey = req.get('Idempotency-Key') ?? '';
    const amount = req.body?.amount;
    if (!/^[\w-]{8,64}$/.test(requestKey) || !Number.isSafeInteger(amount) || amount <= 0) {
      return res.status(400).json({ error: 'bad_request' });
    }
    try {
      const result = await requestPayout(pool, { accountId: req.user.accountId, requestKey, amount, policy });
      if (result.refused) return res.status(422).json({ error: result.refused });
      res.status(result.repeated ? 200 : 201).json({ id: result.payoutId, status: result.status });
      if (result.status === 'pending' && !result.repeated) {
        // After the answer, outside the request transaction. A queue worker can do the same; the claim makes both safe.
        sendPayout(pool, provider, result.payoutId).catch((err) => req.log?.error(err));
      }
    } catch (err) {
      next(err);
    }
  });
  return router;
}
```

## Django ORM

```python
import uuid

from django.db import transaction
from django.db.models import Exists, F, OuterRef
from django.utils import timezone

from .ledger import InsufficientFunds, post_entry
from .models import Account, Payout, User  # User: the project's user model, with its status field
from .payout_policy import POLICY, check_payout


def request_payout(account_id, request_key, amount):
    try:
        with transaction.atomic():
            Account.objects.select_for_update().only("id").get(pk=account_id)
            repeat = Payout.objects.filter(account_id=account_id, request_key=request_key).first()
            if repeat is not None:
                return {"payout_id": repeat.id, "status": repeat.status, "repeated": True}
            check = check_payout(account_id, amount)
            if check.refused:
                return {"refused": check.refused}
            payout_id = str(uuid.uuid4())
            post_entry(account_id, -amount, "payout", payout_id)
            Payout.objects.create(
                id=payout_id, account_id=account_id, request_key=request_key, amount=amount,
                currency=POLICY.currency, payout_minor=amount // POLICY.units_per_minor,
                destination_id=check.destination.id, destination=check.destination.snapshot, status=check.status,
            )
            return {"payout_id": payout_id, "status": check.status}
    except InsufficientFunds:
        return {"refused": "insufficient_balance"}


def claim_for_sending(payout_id):
    active = User.objects.filter(pk=OuterRef("account_id"), status="active")
    return Payout.objects.filter(pk=payout_id, status="pending").filter(Exists(active)).update(
        status="sending", attempts=F("attempts") + 1, sent_at=timezone.now()
    ) == 1
```

The model declares `models.UniqueConstraint(fields=["account", "request_key"], name="payouts_request_key_unique")` and `amount = models.BigIntegerField()`. Call `request_payout` from the view, and enqueue the send with `transaction.on_commit` if the view runs inside a transaction (`ATOMIC_REQUESTS`), so the worker never sees a payout that is not committed yet.

## Laravel Eloquent

```php
<?php
namespace App\Support;

use App\Models\Account;
use App\Models\Payout;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

final class Payouts
{
    public static function request(int $accountId, string $requestKey, int $amount): array
    {
        try {
            return DB::transaction(function () use ($accountId, $requestKey, $amount) {
                Account::whereKey($accountId)->lockForUpdate()->firstOrFail();
                $repeat = Payout::where('account_id', $accountId)->where('request_key', $requestKey)->first();
                if ($repeat !== null) {
                    return ['payout_id' => $repeat->id, 'status' => $repeat->status, 'repeated' => true];
                }
                $check = PayoutPolicy::check($accountId, $amount);
                if (isset($check['refused'])) {
                    return $check;
                }
                $payoutId = (string) Str::uuid();
                Ledger::post($accountId, -$amount, 'payout', $payoutId);
                Payout::create([
                    'id' => $payoutId, 'account_id' => $accountId, 'request_key' => $requestKey, 'amount' => $amount,
                    'currency' => PayoutPolicy::CURRENCY, 'payout_minor' => intdiv($amount, PayoutPolicy::UNITS_PER_MINOR),
                    'destination_id' => $check['destination']['id'], 'destination' => $check['destination']['snapshot'],
                    'status' => $check['status'],
                ]);
                return ['payout_id' => $payoutId, 'status' => $check['status']];
            });
        } catch (InsufficientFunds) {
            return ['refused' => 'insufficient_balance'];
        }
    }

    public static function claimForSending(string $payoutId): bool
    {
        return Payout::whereKey($payoutId)
            ->where('status', 'pending')
            ->whereExists(fn ($q) => $q->selectRaw('1')->from('users')->whereColumn('users.id', 'payouts.account_id')->where('users.status', 'active'))
            ->update(['status' => 'sending', 'attempts' => DB::raw('attempts + 1'), 'sent_at' => now()]) === 1;
    }
}
```

The migration declares `$table->bigInteger('amount')` and `$table->unique(['account_id', 'request_key'])`. Dispatch the send job with `->afterCommit()` so it runs only once the request has committed.

## Rails ActiveRecord

Not syntax-checked here: keep the shape, check it with the project's own test run.

```ruby
module Payouts
  def self.request(account_id:, request_key:, amount:)
    Account.transaction do
      Account.lock.find(account_id)
      repeat = Payout.find_by(account_id: account_id, request_key: request_key)
      next({ payout_id: repeat.id, status: repeat.status, repeated: true }) if repeat
      check = PayoutPolicy.check(account_id, amount)
      next check if check[:refused]
      payout_id = SecureRandom.uuid
      Ledger.post(account_id: account_id, amount: -amount, kind: "payout", ref: payout_id)
      Payout.create!(id: payout_id, account_id: account_id, request_key: request_key, amount: amount,
                     currency: PayoutPolicy::CURRENCY, payout_minor: amount / PayoutPolicy::UNITS_PER_MINOR,
                     destination_id: check[:destination].id, destination: check[:destination].snapshot,
                     status: check[:status])
      { payout_id: payout_id, status: check[:status] }
    end
  rescue Ledger::InsufficientFunds
    { refused: "insufficient_balance" }
  end

  def self.claim_for_sending(payout_id)
    Payout.where(id: payout_id, status: "pending")
          .where("EXISTS (SELECT 1 FROM users WHERE users.id = payouts.account_id AND users.status = 'active')")
          .update_all(["status = 'sending', attempts = attempts + 1, sent_at = ?", Time.current]) == 1
  end
end
```

The migration declares `t.bigint :amount, null: false` and `add_index :payouts, [:account_id, :request_key], unique: true`. Enqueue the send job after the transaction commits (`after_commit`, or `ActiveRecord.after_all_transactions_commit` on Rails 7.2 and newer).

## Where each check sits

| Check | Where |
| --- | --- |
| A double click pays once | The unique (account_id, request_key) key, and the lookup of an earlier payout under the account lock |
| Parallel requests see each other | The account row lock taken first in the request transaction (`FOR UPDATE`, `select_for_update`, `lockForUpdate`, `lock`) |
| Funds before money | The `payout` ledger entry and the payout row in the same transaction, committed before any provider call |
| No overdraw | The posting function's conditional debit, its error mapped to a refusal after the rollback |
| One provider call per payout | The claim's `WHERE status = 'pending'`, with the changed-row count checked |
| A flagged account is not paid | The account state checked in the claim, not only in the request |
| The provider call after the commit | After `requestPayout` returns in Express and Next.js, `transaction.on_commit` in Django, `afterCommit()` in Laravel, an after-commit callback in Rails |
