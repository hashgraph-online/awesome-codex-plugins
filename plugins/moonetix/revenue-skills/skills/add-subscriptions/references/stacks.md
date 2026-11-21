# Subscription events and access checks in five stacks

The pattern from [events-in-any-order.md](events-in-any-order.md) in five common stacks, for Stripe Billing: verify the event with the official library over the raw body, find the subscription it names, fetch the subscription from Stripe outside any transaction, then in one transaction store the event id under its unique key, write the subscription only when the fetch is newer than the stored one, and grant the period's credits under the ledger's (kind, ref) key. The access check reads the stored rows at the time of use. The same shape works for the other providers: replace the verification and the fetch with the calls in their references.

Schema in each stack: the `subscriptions`, `subscription_checkouts` and `subscription_events` tables of `assets/subscriptions.postgres.sql`, and the project's credit ledger with its unique (kind, ref) index. `provider_version` holds the fetch time in milliseconds. Times are stored as UTC. The route, raw body and CSRF exemption of each framework follow the `build-webhook-endpoint` skill.

Each block calls three project functions it does not define: `toRow` maps a Stripe subscription onto the columns (plan from the price id, `paid_through` from the item's `current_period_end`, `grace_until` from the last paid period while `past_due`), `periodCredits` returns the credits and ref for a paid `subscription_create` or `subscription_cycle` invoice or nothing, and the ledger's posting function.

## Next.js App Router with Prisma

```ts
// app/api/webhooks/stripe/route.ts
import Stripe from 'stripe';
import { prisma } from '@/lib/db';
import { periodCredits, postEntry, toRow } from '@/lib/subscriptions';

export const runtime = 'nodejs';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2026-11-18.endive' as Stripe.LatestApiVersion });
const SUBSCRIPTION_EVENTS = new Set([
  'customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted',
  'invoice.paid', 'invoice.payment_failed',
]);

function subscriptionIdOf(event: Stripe.Event): string | null {
  const object = event.data.object as { object?: string; id?: string; parent?: { subscription_details?: { subscription?: string } } };
  if (object.object === 'subscription') return object.id ?? null;
  return object.parent?.subscription_details?.subscription ?? null;
}

export async function POST(request: Request) {
  const raw = await request.text();
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(raw, request.headers.get('stripe-signature') ?? '', process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return new Response('bad signature', { status: 400 });
  }
  if (!SUBSCRIPTION_EVENTS.has(event.type)) return Response.json({ received: true });
  const subscriptionId = subscriptionIdOf(event);
  if (!subscriptionId) return Response.json({ received: true });

  const fetchedAt = BigInt(Date.now());
  const sub = await stripe.subscriptions.retrieve(subscriptionId); // a failure throws: 500, Stripe retries

  await prisma.$transaction(async (tx) => {
    const stored = await tx.$executeRaw`
      INSERT INTO subscription_events (provider, event_id, type) VALUES ('stripe', ${event.id}, ${event.type})
      ON CONFLICT (provider, event_id) DO NOTHING`;
    if (stored === 0) return; // seen before
    const row = await toRow(tx, sub); // null when the checkout is not ours
    if (!row) return;
    await tx.$executeRaw`
      INSERT INTO subscriptions (provider, provider_id, user_id, plan, status, period_start, paid_through, grace_until,
                                 cancel_at_period_end, provider_version)
      VALUES ('stripe', ${sub.id}, ${row.userId}, ${row.plan}, ${row.status}, ${row.periodStart}, ${row.paidThrough},
              ${row.graceUntil}, ${row.cancelAtPeriodEnd}, ${fetchedAt})
      ON CONFLICT (provider, provider_id) DO UPDATE
         SET plan = EXCLUDED.plan, status = EXCLUDED.status, period_start = EXCLUDED.period_start,
             paid_through = EXCLUDED.paid_through, grace_until = EXCLUDED.grace_until,
             cancel_at_period_end = EXCLUDED.cancel_at_period_end, provider_version = EXCLUDED.provider_version
       WHERE subscriptions.provider_version <= EXCLUDED.provider_version`;
    if (event.type === 'invoice.paid') {
      const grant = periodCredits(event.data.object as Stripe.Invoice, row);
      if (grant) await postEntry(tx, { accountId: row.userId, amount: grant.amount, kind: 'plan_allowance', ref: grant.ref });
    }
  });
  return Response.json({ received: true });
}
```

```ts
// lib/entitlements.ts: the one access check, called by every gated route and server action.
import { prisma } from '@/lib/db';

const KEEPS_ACCESS = new Set(['active', 'trialing', 'past_due']);

export async function hasPlan(userId: bigint, plan: string, now = new Date()): Promise<boolean> {
  const rows = await prisma.subscription.findMany({
    where: { userId, plan, revokedAt: null },
    select: { status: true, paidThrough: true, graceUntil: true },
  });
  return rows.some((s) => {
    if (!KEEPS_ACCESS.has(s.status)) return false;
    const until = s.graceUntil ?? s.paidThrough;
    return until !== null && now < until;
  });
}
```

## Express with SQL

```js
// routes/stripe-subscriptions.js. Registered before express.json(), with express.raw for this route.
import express from 'express';
import Stripe from 'stripe';
import { pool, withTransaction } from '../db.js';
import { periodCredits, postEntry, toRow } from '../subscriptions.js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, { apiVersion: '2026-11-18.endive' });
export const router = express.Router();

router.post('/webhooks/stripe', express.raw({ type: 'application/json', limit: '1mb' }), async (req, res, next) => {
  let event;
  try {
    event = stripe.webhooks.constructEvent(req.body, req.get('stripe-signature') ?? '', process.env.STRIPE_WEBHOOK_SECRET);
  } catch {
    return res.status(400).send('bad signature');
  }
  try {
    const object = event.data.object;
    const subscriptionId = object.object === 'subscription' ? object.id : object.parent?.subscription_details?.subscription;
    if (!subscriptionId) return res.json({ received: true });
    const fetchedAt = Date.now();
    const sub = await stripe.subscriptions.retrieve(subscriptionId);

    await withTransaction(pool, async (tx) => {
      const stored = await tx.query(
        "INSERT INTO subscription_events (provider, event_id, type) VALUES ('stripe', $1, $2) ON CONFLICT DO NOTHING",
        [event.id, event.type],
      );
      if (stored.rowCount === 0) return;
      const row = await toRow(tx, sub);
      if (!row) return;
      await tx.query(
        `INSERT INTO subscriptions (provider, provider_id, user_id, plan, status, period_start, paid_through, grace_until,
                                    cancel_at_period_end, provider_version)
         VALUES ('stripe', $1, $2, $3, $4, $5, $6, $7, $8, $9)
         ON CONFLICT (provider, provider_id) DO UPDATE
            SET plan = EXCLUDED.plan, status = EXCLUDED.status, period_start = EXCLUDED.period_start,
                paid_through = EXCLUDED.paid_through, grace_until = EXCLUDED.grace_until,
                cancel_at_period_end = EXCLUDED.cancel_at_period_end, provider_version = EXCLUDED.provider_version
          WHERE subscriptions.provider_version <= EXCLUDED.provider_version`,
        [sub.id, row.userId, row.plan, row.status, row.periodStart, row.paidThrough, row.graceUntil, row.cancelAtPeriodEnd, fetchedAt],
      );
      if (event.type === 'invoice.paid') {
        const grant = periodCredits(object, row);
        if (grant) await postEntry(tx, { accountId: row.userId, amount: grant.amount, kind: 'plan_allowance', ref: grant.ref });
      }
    });
    res.json({ received: true });
  } catch (err) {
    next(err); // 500: Stripe delivers the event again
  }
});

// Middleware for gated routes. The check runs on every request; nothing is cached in the session.
export const requirePlan = (plan) => async (req, res, next) => {
  const { rows } = await pool.query(
    `SELECT 1 FROM subscriptions
      WHERE user_id = $1 AND plan = $2 AND revoked_at IS NULL
        AND status IN ('active', 'trialing', 'past_due')
        AND COALESCE(grace_until, paid_through) > now()
      LIMIT 1`,
    [req.user.id, plan],
  );
  if (rows.length === 0) return res.status(403).json({ error: 'plan_required', plan });
  next();
};
```

## Django

```python
# billing/views.py
import time

import stripe
from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Subscription, SubscriptionEvent
from .subscriptions import period_credits, post_entry, to_row

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = "2026-11-18.endive"
KEEPS_ACCESS = ("active", "trialing", "past_due")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        event = stripe.Webhook.construct_event(
            request.body, request.headers.get("Stripe-Signature", ""), settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)
    obj = event["data"]["object"]
    if obj.get("object") == "subscription":
        subscription_id = obj.get("id")
    else:
        subscription_id = ((obj.get("parent") or {}).get("subscription_details") or {}).get("subscription")
    if not subscription_id:
        return JsonResponse({"received": True})
    fetched_at = int(time.time() * 1000)
    sub = stripe.Subscription.retrieve(subscription_id)  # an error here answers 500 and Stripe retries

    with transaction.atomic():
        try:
            with transaction.atomic():  # a savepoint, so a duplicate does not abort the outer transaction
                SubscriptionEvent.objects.create(provider="stripe", event_id=event["id"], type=event["type"])
        except IntegrityError:
            return JsonResponse({"received": True, "duplicate": True})
        row = to_row(sub)
        if row is None:
            return JsonResponse({"received": True})
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscriptions (provider, provider_id, user_id, plan, status, period_start, paid_through,
                                           grace_until, cancel_at_period_end, provider_version)
                VALUES ('stripe', %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider, provider_id) DO UPDATE
                   SET plan = EXCLUDED.plan, status = EXCLUDED.status, period_start = EXCLUDED.period_start,
                       paid_through = EXCLUDED.paid_through, grace_until = EXCLUDED.grace_until,
                       cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                       provider_version = EXCLUDED.provider_version
                 WHERE subscriptions.provider_version <= EXCLUDED.provider_version
                """,
                [sub["id"], row.user_id, row.plan, row.status, row.period_start, row.paid_through,
                 row.grace_until, row.cancel_at_period_end, fetched_at],
            )
        if event["type"] == "invoice.paid":
            grant = period_credits(obj, row)
            if grant:
                post_entry(account_id=row.user_id, amount=grant.amount, kind="plan_allowance", ref=grant.ref)
    return JsonResponse({"received": True})


def has_plan(user_id, plan, now=None):
    now = now or timezone.now()
    for s in Subscription.objects.filter(user_id=user_id, plan=plan, revoked_at__isnull=True, status__in=KEEPS_ACCESS):
        until = s.grace_until or s.paid_through
        if until is not None and now < until:
            return True
    return False
```

## Laravel

```php
<?php
// app/Http/Controllers/StripeWebhookController.php. The route is excluded from CSRF verification.

namespace App\Http\Controllers;

use App\Billing\Subscriptions;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Stripe\Exception\SignatureVerificationException;
use Stripe\StripeClient;
use Stripe\Webhook;

class StripeWebhookController extends Controller
{
    public function __invoke(Request $request, Subscriptions $subscriptions)
    {
        try {
            $event = Webhook::constructEvent(
                $request->getContent(),
                (string) $request->header('Stripe-Signature'),
                config('services.stripe.webhook_secret')
            );
        } catch (\UnexpectedValueException | SignatureVerificationException $e) {
            return response('bad signature', 400);
        }
        $object = $event->data->object;
        $subscriptionId = $object->object === 'subscription'
            ? $object->id
            : ($object->parent->subscription_details->subscription ?? null);
        if (! $subscriptionId) {
            return response()->json(['received' => true]);
        }
        $fetchedAt = (int) floor(microtime(true) * 1000);
        $stripe = new StripeClient(['api_key' => config('services.stripe.secret'), 'stripe_version' => '2026-11-18.endive']);
        $sub = $stripe->subscriptions->retrieve($subscriptionId); // an exception answers 500 and Stripe retries

        DB::transaction(function () use ($event, $object, $sub, $fetchedAt, $subscriptions) {
            $stored = DB::table('subscription_events')->insertOrIgnore([
                'provider' => 'stripe', 'event_id' => $event->id, 'type' => $event->type,
            ]);
            if ($stored === 0) {
                return;
            }
            $row = $subscriptions->toRow($sub);
            if ($row === null) {
                return;
            }
            DB::statement(
                'INSERT INTO subscriptions (provider, provider_id, user_id, plan, status, period_start, paid_through,
                                            grace_until, cancel_at_period_end, provider_version)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT (provider, provider_id) DO UPDATE
                    SET plan = EXCLUDED.plan, status = EXCLUDED.status, period_start = EXCLUDED.period_start,
                        paid_through = EXCLUDED.paid_through, grace_until = EXCLUDED.grace_until,
                        cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                        provider_version = EXCLUDED.provider_version
                  WHERE subscriptions.provider_version <= EXCLUDED.provider_version',
                ['stripe', $sub->id, $row->userId, $row->plan, $row->status, $row->periodStart, $row->paidThrough,
                 $row->graceUntil, $row->cancelAtPeriodEnd, $fetchedAt]
            );
            if ($event->type === 'invoice.paid' && ($grant = $subscriptions->periodCredits($object, $row))) {
                $subscriptions->postEntry($row->userId, $grant->amount, 'plan_allowance', $grant->ref);
            }
        });

        return response()->json(['received' => true]);
    }
}

```

```php
<?php
// app/Billing/Entitlements.php: the one access check, used by a middleware on every gated route.

namespace App\Billing;

use Illuminate\Support\Facades\DB;

class Entitlements
{
    public function hasPlan(int $userId, string $plan): bool
    {
        return DB::table('subscriptions')
            ->where('user_id', $userId)
            ->where('plan', $plan)
            ->whereNull('revoked_at')
            ->whereIn('status', ['active', 'trialing', 'past_due'])
            ->whereRaw('COALESCE(grace_until, paid_through) > now()')
            ->exists();
    }
}
```

On MySQL, `insertOrIgnore` hides other errors: insert and catch error 1062 instead, as the `build-webhook-endpoint` skill shows, and replace `ON CONFLICT` with `INSERT ... ON DUPLICATE KEY UPDATE` whose assignments test `provider_version`.

## Rails

```ruby
# app/controllers/stripe_webhooks_controller.rb
class StripeWebhooksController < ActionController::API
  KEEPS_ACCESS = %w[active trialing past_due].freeze

  def create
    event = Stripe::Webhook.construct_event(
      request.raw_post, request.headers["Stripe-Signature"].to_s, ENV.fetch("STRIPE_WEBHOOK_SECRET")
    )
  rescue JSON::ParserError, Stripe::SignatureVerificationError
    head :bad_request
  else
    object = event.data.object
    subscription_id = object.object == "subscription" ? object.id : object.dig("parent", "subscription_details", "subscription")
    return render(json: { received: true }) if subscription_id.blank?

    fetched_at = (Time.now.to_f * 1000).floor
    sub = Stripe::Subscription.retrieve(subscription_id) # an exception answers 500 and Stripe retries

    ActiveRecord::Base.transaction do
      stored = SubscriptionEvent.insert({ provider: "stripe", event_id: event.id, type: event.type },
                                        unique_by: %i[provider event_id], returning: %w[event_id])
      next if stored.rows.empty? # seen before

      row = Billing::Subscriptions.to_row(sub)
      next if row.nil?

      Subscription.connection.exec_update(<<~SQL, "subscription upsert", [
        sub.id, row.user_id, row.plan, row.status, row.period_start, row.paid_through,
        row.grace_until, row.cancel_at_period_end, fetched_at
      ])
        INSERT INTO subscriptions (provider, provider_id, user_id, plan, status, period_start, paid_through,
                                   grace_until, cancel_at_period_end, provider_version)
        VALUES ('stripe', $1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (provider, provider_id) DO UPDATE
           SET plan = EXCLUDED.plan, status = EXCLUDED.status, period_start = EXCLUDED.period_start,
               paid_through = EXCLUDED.paid_through, grace_until = EXCLUDED.grace_until,
               cancel_at_period_end = EXCLUDED.cancel_at_period_end, provider_version = EXCLUDED.provider_version
         WHERE subscriptions.provider_version <= EXCLUDED.provider_version
      SQL

      if event.type == "invoice.paid" && (grant = Billing::Subscriptions.period_credits(object, row))
        Billing::Ledger.post!(account_id: row.user_id, amount: grant.amount, kind: "plan_allowance", ref: grant.ref)
      end
    end
    render json: { received: true }
  end

  def self.plan?(user_id, plan, now: Time.current)
    Subscription.where(user_id: user_id, plan: plan, revoked_at: nil, status: KEEPS_ACCESS)
                .where("COALESCE(grace_until, paid_through) > ?", now)
                .exists?
  end
end
```

`insert` with `unique_by` runs `ON CONFLICT DO NOTHING` on PostgreSQL and SQLite; MySQL ignores `unique_by`, so there insert and rescue `ActiveRecord::RecordNotUnique` inside `transaction(requires_new: true)`.

## Where each check sits

| Check | Where |
| --- | --- |
| A forged or replayed event changes nothing | The library's `constructEvent` over the raw body, before anything is read; the event id under the (provider, event_id) primary key |
| Arrival order decides nothing | The subscription is fetched from Stripe for every event; the upsert's `WHERE provider_version <= EXCLUDED.provider_version` keeps a slower, older fetch from overwriting |
| No provider call inside a transaction | `retrieve` runs before the transaction opens; a failure answers 500 before the event id is stored |
| One entitlement per subscription | The (provider, provider_id) primary key; the access check looks at every row of the user |
| Credits once per paid period | The ledger's unique (kind, ref) key with the subscription and the period start as ref |
| Access ends on time | `COALESCE(grace_until, paid_through) > now()` in the check, at the time of use |
| A refund or chargeback ends access | `revoked_at IS NULL` in the check; the upsert never writes `revoked_at` |
| The user is the app's own | `toRow` resolves the user from the checkout id in the subscription's metadata; `user_id` is not in the update clause |
