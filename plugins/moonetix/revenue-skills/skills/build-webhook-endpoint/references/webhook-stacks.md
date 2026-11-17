# Webhook routes per stack

The same route in five stacks: Next.js App Router, Express, Django, Laravel and Rails. Each does the same six things in the same order.

1. **Raw body.** The bytes as they arrived, with a size limit, before any parser.
2. **CSRF.** Exempt this route only. A signature replaces the CSRF token; every other form keeps its protection.
3. **Verify, then parse.** Signature or token first. On failure answer 400 and touch nothing.
4. **Once only.** One transaction: insert the event id under a unique constraint, stop when it was there, apply the effect, commit.
5. **Answer after the commit, quickly.** Slow work (mail, other services) runs after the commit, from a job or an outbox row the transaction wrote.
6. **Secret.** Read from the environment into configuration at start-up, as a list during a rotation, with no default. The app does not start without it.

`verifyTimestamped`, `verify_timestamped` and the like stand for the verification function of the provider's scheme. `applyEvent` stands for the content checks and the conditional updates. Both are the project's own code, as the `build-webhook-endpoint` skill builds them. A JWS or OIDC provider (App Store, Google Play) needs no raw body, but the other five points hold.

The event table, in any stack:

```sql
CREATE TABLE webhook_events (
  provider    text NOT NULL,
  event_id    text NOT NULL,
  type        text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, event_id)
);
```

## Node: one handler, two adapters

The work after the raw body does not depend on the framework. With the `pg` driver:

```js
// lib/payment-webhook.js. Returns the status and body to send.
export async function handlePaymentWebhook(pool, secrets, rawBody, signatureHeader) {
  if (!verifyTimestamped(rawBody, signatureHeader, secrets)) return { status: 400, body: { error: 'bad_signature' } };
  let event;
  try {
    event = JSON.parse(rawBody.toString('utf8'));
  } catch {
    return { status: 400, body: { error: 'invalid_json' } };
  }
  if (typeof event?.id !== 'string' || typeof event.type !== 'string') return { status: 400, body: { error: 'invalid_event' } };
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const stored = await client.query(
      'INSERT INTO webhook_events (provider, event_id, type) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING',
      ['payments', event.id, event.type],
    );
    if (stored.rowCount === 1) await applyEvent(client, event); // may also insert an outbox row
    await client.query('COMMIT');
  } catch (err) {
    await client.query('ROLLBACK');
    throw err; // the adapter answers 500 and the provider retries
  } finally {
    client.release();
  }
  return { status: 200, body: { received: true } };
}
```

**Express.** The route is registered with `express.raw` before `app.use(express.json())`. Express has no CSRF protection of its own; if the app adds a CSRF middleware globally, register the webhook route before it.

```js
const secrets = requireSecrets('WEBHOOK_SECRETS'); // at start-up: throws when missing

app.post('/webhooks/payments', express.raw({ type: '*/*', limit: '1mb' }), async (req, res, next) => {
  try {
    const rawBody = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);
    const result = await handlePaymentWebhook(pool, secrets, rawBody, req.get('x-signature'));
    res.status(result.status).json(result.body);
  } catch (err) {
    next(err);
  }
});
app.use(express.json());
```

**Next.js App Router.** Route handlers have no CSRF check to exempt, and nothing parses the body before the handler reads it. Use the Node.js runtime for `node:crypto` and the database driver. Check the secret in `instrumentation.ts`, whose `register` runs when the server starts, rather than at module load, which `next build` may run without the variables.

```ts
// app/api/webhooks/payments/route.ts
import { handlePaymentWebhook } from '@/lib/payment-webhook';
import { pool, webhookSecrets } from '@/lib/config';

export const runtime = 'nodejs';

export async function POST(request: Request): Promise<Response> {
  if (Number(request.headers.get('content-length') ?? 0) > 1_000_000) return new Response(null, { status: 413 });
  const rawBody = Buffer.from(await request.arrayBuffer()); // not request.json()
  const result = await handlePaymentWebhook(pool, webhookSecrets(), rawBody, request.headers.get('x-signature'));
  return Response.json(result.body, { status: result.status });
}
```

```ts
// instrumentation.ts
export async function register(): Promise<void> {
  const { webhookSecrets } = await import('@/lib/config');
  webhookSecrets(); // throws when WEBHOOK_SECRETS is missing or too short
}
```

Do not use `after()` from `next/server` for work that must happen: it runs in the same process after the answer, and a restart loses it.

## Django

`request.body` is the raw bytes. `csrf_exempt` on this view only. The inner `atomic()` is a savepoint, so a duplicate key does not abort the outer transaction on PostgreSQL.

```python
# settings.py: KeyError at start-up when the variable is missing.
import os

WEBHOOK_SECRETS = [s.encode() for s in os.environ["WEBHOOK_SECRETS"].split(",") if s]
```

```python
import json

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import WebhookEvent
from .payments import apply_event, send_receipt
from .signatures import verify_timestamped


@csrf_exempt
@require_POST
def payments_webhook(request):
    raw = request.body
    if not verify_timestamped(raw, request.headers.get("X-Signature"), settings.WEBHOOK_SECRETS):
        return HttpResponseBadRequest()
    try:
        event = json.loads(raw)
    except ValueError:
        return HttpResponseBadRequest()
    if not isinstance(event, dict) or not isinstance(event.get("id"), str):
        return HttpResponseBadRequest()
    with transaction.atomic():
        try:
            with transaction.atomic():
                WebhookEvent.objects.create(provider="payments", event_id=event["id"], type=str(event.get("type")))
        except IntegrityError:
            return HttpResponse(status=200)  # seen before
        apply_event(event)
        transaction.on_commit(lambda: send_receipt.delay(event["id"]))
    return HttpResponse(status=200)
```

The model declares `models.UniqueConstraint(fields=["provider", "event_id"], name="webhook_events_once")` in its `Meta.constraints`.

## Laravel

Place the route outside the `web` middleware group (for example in `routes/api.php`), or exclude only its URI with `$middleware->validateCsrfTokens(except: ['webhooks/*'])` in `bootstrap/app.php`. Read the secret with `env()` only inside a config file, because `env()` returns null once the configuration is cached. A service provider's `boot` method can throw when the configured list is empty.

```php
<?php
// config/services.php (merged into the existing array)
return [
    'payments' => [
        'webhook_secrets' => array_values(array_filter(explode(',', (string) env('PAYMENTS_WEBHOOK_SECRETS')))),
    ],
];
```

```php
<?php

namespace App\Http\Controllers;

use App\Jobs\SendReceipt;
use App\Webhooks\PaymentEvents;
use App\Webhooks\Signature;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\DB;

class PaymentWebhookController
{
    public function __invoke(Request $request, PaymentEvents $events): Response
    {
        $raw = $request->getContent();
        if (!Signature::verifyTimestamped($raw, $request->header('X-Signature'), config('services.payments.webhook_secrets'))) {
            return response('', 400);
        }
        $event = json_decode($raw, true);
        if (!is_array($event) || !is_string($event['id'] ?? null)) {
            return response('', 400);
        }
        DB::transaction(function () use ($event, $events) {
            try {
                DB::transaction(fn () => DB::table('webhook_events')->insert([
                    'provider' => 'payments',
                    'event_id' => $event['id'],
                    'type' => (string) ($event['type'] ?? ''),
                ]));
            } catch (UniqueConstraintViolationException) {
                return; // seen before
            }
            $events->apply($event);
            SendReceipt::dispatch($event['id'])->afterCommit();
        });
        return response('', 200);
    }
}
```

The nested `DB::transaction` is a savepoint. Without it, the failed insert aborts the outer transaction on PostgreSQL.

## Rails

`request.raw_post` is the raw body. `skip_forgery_protection` in this controller only; a controller that inherits from `ActionController::API` has no CSRF check to skip. Do not `return` from inside a transaction block: whether that commits or rolls back has changed between Rails versions. This snippet was not run through a Ruby syntax check.

```ruby
# config/initializers/webhooks.rb: KeyError at boot when the variable is missing.
Rails.configuration.x.webhook_secrets = ENV.fetch("WEBHOOK_SECRETS").split(",").reject(&:empty?)
```

```ruby
class PaymentWebhooksController < ApplicationController
  skip_forgery_protection

  def create
    raw = request.raw_post
    unless WebhookSignature.verify_timestamped(raw, request.headers["X-Signature"], Rails.configuration.x.webhook_secrets)
      return head :bad_request
    end

    event = JSON.parse(raw)
    stored = false
    WebhookEvent.transaction do
      stored = begin
        WebhookEvent.transaction(requires_new: true) do
          WebhookEvent.create!(provider: "payments", event_id: event.fetch("id"), event_type: event.fetch("type"))
        end
        true
      rescue ActiveRecord::RecordNotUnique
        false
      end
      PaymentEvents.apply(event) if stored
    end
    SendReceiptJob.perform_later(event.fetch("id")) if stored
    head :ok
  rescue JSON::ParserError, KeyError
    head :bad_request
  end
end
```

The migration adds `add_index :webhook_events, [:provider, :event_id], unique: true`.

## Work after the commit

A job enqueued after the commit (`on_commit`, `afterCommit`, after the transaction block) is lost if the process dies between the commit and the enqueue. When the follow-up matters to money or to the customer, insert an outbox row inside the transaction and let a worker deliver it. In every stack, keep the transaction short: the provider's timeout is seconds, not minutes.
