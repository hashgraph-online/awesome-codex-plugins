# The postback endpoint in five stacks

The handler from [postback-endpoint.md](postback-endpoint.md) in five common stacks, with the example network of that reference: `tx`, `user`, `payout`, `status` and `hash`, where `hash` is an HMAC-SHA256 of `tx:user:payout:status`. Real names and schemes are in [network-facts.md](network-facts.md) and the network's documentation. What each stack has to get right:

- **The route** sits outside session, login, CSRF and rate-limit middleware, and answers on the exact URL given to the network.
- **Authentication first,** in constant time, over the values exactly as they arrived. A parameter that arrives twice is refused.
- **The credit** inserts the conversion under the primary key (network, tx_id) and posts the `offer` ledger entry only when the insert created a row, in one transaction. The amount comes from the signed payout and the app's own rate, in integers.
- **The reversal** flips `credited` to `reversed` with a conditional update and takes back the stored coins from the stored account, once. A reversal with no credit leaves a `reversed` row, so a late credit pays nothing.
- **The answer** is 2xx after the commit, also for duplicates; 4xx for a bad signature; 5xx when storing failed.

The ledger entry goes through the project's posting function (the `build-ledger` skill builds it). `payout_micros` and `coins` are 64-bit integers in every schema below.

## Next.js App Router with Prisma

```ts
// app/api/postback/examplenet/route.ts
import { createHash, createHmac, timingSafeEqual } from 'node:crypto';
import { prisma } from '@/lib/db';
import { postEntry } from '@/lib/ledger';
import { CONFIG } from '@/lib/offerwall-config'; // postbackKey from the environment, coinsPerDollar, userShareBps

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const NETWORK = 'examplenet';
const same = (a: string, b: string) =>
  timingSafeEqual(createHash('sha256').update(a).digest(), createHash('sha256').update(b).digest());
const text = (body: string, status = 200) => new Response(body, { status, headers: { 'content-type': 'text/plain' } });

export async function GET(request: Request) {
  const query = new URL(request.url).searchParams;
  const names = ['tx', 'user', 'payout', 'status', 'hash'];
  if (names.some((name) => query.getAll(name).length !== 1)) return text('BAD REQUEST', 400);
  const [tx, user, payout, status, hash] = names.map((name) => query.get(name) as string);
  if (!same(hash, createHmac('sha256', CONFIG.postbackKey).update(`${tx}:${user}:${payout}:${status}`).digest('hex'))) {
    return text('BAD HASH', 403);
  }
  if (status !== '1' && status !== '2') return text('IGNORED');
  const m = /^(\d{1,9})(?:\.(\d{1,6}))?$/.exec(payout);
  if (!m || !/^[\w.:-]{1,191}$/.test(tx) || !/^[1-9]\d{0,14}$/.test(user)) return text('BAD REQUEST', 400);
  const micros = BigInt(m[1]) * 1_000_000n + BigInt((m[2] ?? '').padEnd(6, '0'));
  const coins = (micros * BigInt(CONFIG.coinsPerDollar) * BigInt(CONFIG.userShareBps)) / 10_000_000_000n;
  const userId = BigInt(user);

  // A thrown error leaves the transaction rolled back and Next.js answers 500: the network retries.
  const body = await prisma.$transaction(async (db) => {
    if ((await db.user.count({ where: { id: userId } })) === 0) return 'UNKNOWN USER';
    if (status === '1') {
      const inserted = await db.$executeRaw`
        INSERT INTO offer_conversions (network, tx_id, user_id, payout_micros, coins, status)
        VALUES (${NETWORK}, ${tx}, ${userId}, ${micros}, ${coins}, 'credited')
        ON CONFLICT (network, tx_id) DO NOTHING`;
      if (inserted === 0) return 'DUPLICATE';
      if (coins > 0n) await postEntry(db, { accountId: userId, amount: coins, kind: 'offer', ref: `${NETWORK}:${tx}`, actor: NETWORK });
      return 'OK';
    }
    for (let attempt = 0; attempt < 2; attempt += 1) {
      const flipped = await db.$queryRaw<{ user_id: bigint; coins: bigint }[]>`
        UPDATE offer_conversions SET status = 'reversed', reversed_at = now()
         WHERE network = ${NETWORK} AND tx_id = ${tx} AND status = 'credited'
        RETURNING user_id, coins`;
      if (flipped.length === 1) {
        const stored = flipped[0];
        if (stored.coins > 0n) {
          await postEntry(db, { accountId: stored.user_id, amount: -stored.coins, kind: 'offer_reversal', ref: `${NETWORK}:${tx}`, actor: NETWORK, allowDebt: true });
        }
        return 'OK';
      }
      const marked = await db.$executeRaw`
        INSERT INTO offer_conversions (network, tx_id, user_id, payout_micros, coins, status, reversed_at)
        VALUES (${NETWORK}, ${tx}, ${userId}, 0, 0, 'reversed', now())
        ON CONFLICT (network, tx_id) DO NOTHING`;
      if (marked === 1) return 'NOTHING TO REVERSE';
    }
    return 'DUPLICATE';
  });
  return text(body);
}
```

If the project has a `middleware.ts`, exclude the route from its matcher (for example `matcher: ['/((?!api/postback).*)']`), so that no login redirect, locale rewrite or bot check reaches it.

## Express with SQL

`handlePostback` is the node-postgres function in [postback-endpoint.md](postback-endpoint.md). What the Express side adds: the route registered before session, CSRF and rate-limit middleware, and the parameters read from the raw query string so that a repeated one is visible.

```js
import express from 'express';
import { handlePostback } from './postback.mjs';

export function createApp({ pool, config, sessionMiddleware, csrfMiddleware }) {
  const app = express();
  // Before every middleware that needs a cookie, a token or a browser.
  app.get('/postback/examplenet', async (req, res) => {
    const query = new URL(req.originalUrl, 'http://postback.invalid').searchParams;
    const params = {};
    for (const name of ['tx', 'user', 'payout', 'status', 'hash']) {
      const values = query.getAll(name);
      if (values.length === 1) params[name] = values[0];
    }
    try {
      const { status, body } = await handlePostback(params, { pool, config });
      res.status(status).type('text/plain').send(body);
    } catch (err) {
      req.log?.error(err);
      res.status(500).type('text/plain').send('RETRY');
    }
  });
  app.use(sessionMiddleware);
  app.use(csrfMiddleware);
  return app;
}
```

A parameter that arrived twice is left out of `params`, and `handlePostback` refuses a request with a missing field. `req.query` is not used: its parser turns repeated parameters into arrays and bracketed names into objects.

## Django ORM

```python
import hashlib
import hmac
import re

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models.functions import Now
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .ledger import post_entry
from .models import OfferConversion, User

NETWORK = "examplenet"
PAYOUT = re.compile(r"^(\d{1,9})(?:\.(\d{1,6}))?$")


@csrf_exempt
@require_GET
def postback(request):
    names = ("tx", "user", "payout", "status", "hash")
    if any(len(request.GET.getlist(name)) != 1 for name in names):
        return HttpResponse("BAD REQUEST", status=400, content_type="text/plain")
    tx, user, payout, status, sig = (request.GET[name] for name in names)
    expected = hmac.new(settings.POSTBACK_KEY.encode(), f"{tx}:{user}:{payout}:{status}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig.encode(), expected.encode()):
        return HttpResponse("BAD HASH", status=403, content_type="text/plain")
    if status not in ("1", "2"):
        return HttpResponse("IGNORED", content_type="text/plain")
    m = PAYOUT.match(payout)
    if not m or not re.fullmatch(r"[\w.:-]{1,191}", tx) or not re.fullmatch(r"[1-9]\d{0,14}", user):
        return HttpResponse("BAD REQUEST", status=400, content_type="text/plain")
    micros = int(m[1]) * 1_000_000 + int((m[2] or "").ljust(6, "0"))
    coins = micros * settings.COINS_PER_DOLLAR * settings.USER_SHARE_BPS // 10_000_000_000
    with transaction.atomic():  # an exception here answers 500, and the network retries
        if not User.objects.filter(pk=int(user)).exists():
            body = "UNKNOWN USER"
        elif status == "1":
            body = credit(tx, int(user), micros, coins)
        else:
            body = reverse(tx, int(user))
    return HttpResponse(body, content_type="text/plain")


def credit(tx, user_id, micros, coins):
    try:
        with transaction.atomic():  # a savepoint: a duplicate rolls back only this insert
            OfferConversion.objects.create(network=NETWORK, tx_id=tx, user_id=user_id,
                                           payout_micros=micros, coins=coins, status="credited")
    except IntegrityError:
        return "DUPLICATE"
    if coins > 0:
        post_entry(user_id, coins, "offer", f"{NETWORK}:{tx}", actor=NETWORK)
    return "OK"


def reverse(tx, user_id):
    for _ in range(2):
        row = OfferConversion.objects.select_for_update().filter(network=NETWORK, tx_id=tx).first()
        if row is not None and row.status == "credited":
            OfferConversion.objects.filter(pk=row.pk, status="credited").update(status="reversed", reversed_at=Now())
            if row.coins > 0:
                post_entry(row.user_id, -row.coins, "offer_reversal", f"{NETWORK}:{tx}", actor=NETWORK, allow_debt=True)
            return "OK"
        if row is not None:
            return "DUPLICATE"
        try:
            with transaction.atomic():
                OfferConversion.objects.create(network=NETWORK, tx_id=tx, user_id=user_id, payout_micros=0,
                                               coins=0, status="reversed", reversed_at=Now())
            return "NOTHING TO REVERSE"
        except IntegrityError:
            continue  # the credit was committed a moment ago: the second pass reverses it
    return "DUPLICATE"
```

The model declares `models.UniqueConstraint(fields=["network", "tx_id"], name="offer_conversions_tx_unique")`. Route it in `urls.py` outside any login-required wrapper.

## Laravel Eloquent

```php
<?php
// routes/api.php: the api group has no session and no CSRF check. Keep throttling off this route.
Route::get('/postback/examplenet', \App\Http\Controllers\ExamplenetPostback::class)->withoutMiddleware('throttle:api');
```

```php
<?php
namespace App\Http\Controllers;

use App\Models\User;
use App\Support\Ledger;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\DB;

final class ExamplenetPostback
{
    private const NETWORK = 'examplenet';

    public function __invoke(Request $request): Response
    {
        // PHP keeps only the last of two equal names, so count them in the raw query string.
        $seen = [];
        foreach (explode('&', (string) $request->server('QUERY_STRING')) as $pair) {
            $key = urldecode(explode('=', $pair, 2)[0]);
            $seen[$key] = ($seen[$key] ?? 0) + 1;
        }
        $values = [];
        foreach (['tx', 'user', 'payout', 'status', 'hash'] as $name) {
            $value = $request->query($name);
            if (($seen[$name] ?? 0) !== 1 || !is_string($value)) {
                return response('BAD REQUEST', 400);
            }
            $values[$name] = $value;
        }
        ['tx' => $tx, 'user' => $user, 'payout' => $payout, 'status' => $status, 'hash' => $hash] = $values;
        $expected = hash_hmac('sha256', "{$tx}:{$user}:{$payout}:{$status}", (string) config('offerwall.postback_key'));
        if (!hash_equals($expected, $hash)) {
            return response('BAD HASH', 403);
        }
        if ($status !== '1' && $status !== '2') {
            return response('IGNORED');
        }
        if (preg_match('/^(\d{1,9})(?:\.(\d{1,6}))?$/', $payout, $m) !== 1
            || preg_match('/^[\w.:-]{1,191}$/', $tx) !== 1 || preg_match('/^[1-9]\d{0,14}$/', $user) !== 1) {
            return response('BAD REQUEST', 400);
        }
        $micros = (int) $m[1] * 1_000_000 + (int) str_pad($m[2] ?? '', 6, '0');
        $factor = (int) config('offerwall.coins_per_dollar') * (int) config('offerwall.user_share_bps');
        if ($micros > intdiv(PHP_INT_MAX, $factor)) {
            return response('BAD REQUEST', 400); // would overflow a 64-bit integer
        }
        $coins = intdiv($micros * $factor, 10_000_000_000); // rounded down, once

        // An exception rolls back and answers 500, and the network retries.
        $body = DB::transaction(function () use ($tx, $user, $micros, $coins, $status) {
            if (!User::whereKey((int) $user)->exists()) {
                return 'UNKNOWN USER';
            }
            return $status === '1' ? $this->credit($tx, (int) $user, $micros, $coins) : $this->reverse($tx, (int) $user);
        });
        return response($body);
    }

    private function credit(string $tx, int $userId, int $micros, int $coins): string
    {
        try {
            DB::transaction(fn () => DB::table('offer_conversions')->insert([
                'network' => self::NETWORK, 'tx_id' => $tx, 'user_id' => $userId,
                'payout_micros' => $micros, 'coins' => $coins, 'status' => 'credited',
            ]));
        } catch (UniqueConstraintViolationException) {
            return 'DUPLICATE';
        }
        if ($coins > 0) {
            Ledger::post($userId, $coins, 'offer', self::NETWORK.":{$tx}", self::NETWORK);
        }
        return 'OK';
    }

    private function reverse(string $tx, int $userId): string
    {
        for ($attempt = 0; $attempt < 2; $attempt++) {
            $row = DB::table('offer_conversions')->where('network', self::NETWORK)->where('tx_id', $tx)->lockForUpdate()->first();
            if ($row !== null && $row->status === 'credited') {
                DB::table('offer_conversions')->where('network', self::NETWORK)->where('tx_id', $tx)
                    ->where('status', 'credited')->update(['status' => 'reversed', 'reversed_at' => now()]);
                if ((int) $row->coins > 0) {
                    Ledger::post((int) $row->user_id, -(int) $row->coins, 'offer_reversal', self::NETWORK.":{$tx}", self::NETWORK, allowDebt: true);
                }
                return 'OK';
            }
            if ($row !== null) {
                return 'DUPLICATE';
            }
            try {
                DB::transaction(fn () => DB::table('offer_conversions')->insert([
                    'network' => self::NETWORK, 'tx_id' => $tx, 'user_id' => $userId, 'payout_micros' => 0,
                    'coins' => 0, 'status' => 'reversed', 'reversed_at' => now(),
                ]));
                return 'NOTHING TO REVERSE';
            } catch (UniqueConstraintViolationException) {
                continue; // the credit was committed a moment ago: the second pass reverses it
            }
        }
        return 'DUPLICATE';
    }
}
```

The migration declares `$table->primary(['network', 'tx_id'])`, with `bigInteger` for `payout_micros` and `coins`. PHP integers are 64-bit and turn into floats on overflow, so the product is checked against `PHP_INT_MAX` before it is computed. A payout that large is a malformed postback.

## Rails ActiveRecord

Not syntax-checked here: keep the shape, check it with the project's own test run.

```ruby
# config/routes.rb: get "/postback/examplenet", to: "examplenet_postbacks#create"
class ExamplenetPostbacksController < ActionController::API # no session, no CSRF check
  NETWORK = "examplenet"
  NAMES = %w[tx user payout status hash].freeze

  def create
    query = Rack::Utils.parse_query(request.query_string) # a repeated name becomes an Array
    values = NAMES.map { |name| query[name] }
    return render(plain: "BAD REQUEST", status: :bad_request) unless values.all?(String)
    tx, user, payout, status, sig = values
    expected = OpenSSL::HMAC.hexdigest("SHA256", ENV.fetch("POSTBACK_KEY"), "#{tx}:#{user}:#{payout}:#{status}")
    return render(plain: "BAD HASH", status: :forbidden) unless ActiveSupport::SecurityUtils.secure_compare(sig, expected)
    return render(plain: "IGNORED") unless %w[1 2].include?(status)
    m = /\A(\d{1,9})(?:\.(\d{1,6}))?\z/.match(payout)
    return render(plain: "BAD REQUEST", status: :bad_request) unless m && tx.match?(/\A[\w.:-]{1,191}\z/) && user.match?(/\A[1-9]\d{0,14}\z/)
    micros = m[1].to_i * 1_000_000 + m[2].to_s.ljust(6, "0").to_i
    coins = micros * COINS_PER_DOLLAR * USER_SHARE_BPS / 10_000_000_000
    body = OfferConversion.transaction do # an exception answers 500, and the network retries
      if !User.exists?(user.to_i) then "UNKNOWN USER"
      elsif status == "1" then credit(tx, user.to_i, micros, coins)
      else reverse(tx, user.to_i)
      end
    end
    render plain: body
  end

  private

  def credit(tx, user_id, micros, coins)
    OfferConversion.transaction(requires_new: true) do
      OfferConversion.create!(network: NETWORK, tx_id: tx, user_id: user_id, payout_micros: micros, coins: coins, status: "credited")
    end
    Ledger.post(account_id: user_id, amount: coins, kind: "offer", ref: "#{NETWORK}:#{tx}", actor: NETWORK) if coins.positive?
    "OK"
  rescue ActiveRecord::RecordNotUnique
    "DUPLICATE"
  end

  def reverse(tx, user_id)
    2.times do
      row = OfferConversion.lock.find_by(network: NETWORK, tx_id: tx)
      if row&.status == "credited"
        OfferConversion.where(network: NETWORK, tx_id: tx, status: "credited").update_all(status: "reversed", reversed_at: Time.current)
        Ledger.post(account_id: row.user_id, amount: -row.coins, kind: "offer_reversal", ref: "#{NETWORK}:#{tx}", actor: NETWORK, allow_debt: true) if row.coins.positive?
        return "OK"
      end
      return "DUPLICATE" if row
      begin
        OfferConversion.transaction(requires_new: true) do
          OfferConversion.create!(network: NETWORK, tx_id: tx, user_id: user_id, payout_micros: 0, coins: 0, status: "reversed", reversed_at: Time.current)
        end
        return "NOTHING TO REVERSE"
      rescue ActiveRecord::RecordNotUnique
        next # the credit was committed a moment ago: the second pass reverses it
      end
    end
    "DUPLICATE"
  end
end
```

The migration declares `add_index :offer_conversions, [:network, :tx_id], unique: true` and `bigint` for `payout_micros` and `coins`. In a full Rails controller instead of `ActionController::API`, add `skip_forgery_protection` and skip the authentication callbacks for this action.

## Where each check sits

| Check | Where |
| --- | --- |
| Reachable by the network | The route outside session, CSRF, login and throttling: before the middleware in Express, excluded from `middleware.ts` in Next.js, `csrf_exempt` in Django, the api group in Laravel, `ActionController::API` in Rails |
| Forged postbacks refused | The HMAC compared in constant time (`timingSafeEqual`, `hmac.compare_digest`, `hash_equals`, `secure_compare`) before any database read |
| Repeated parameters refused | `getAll`, `getlist`, a non-string query value, an `Array` from `parse_query` |
| Amount decided on the server | Integer micros from the signed payout, times the app's rate and share, rounded down once |
| Credited once | The (network, tx_id) key and the ledger entry only after the insert created a row |
| Reversed once, by the stored amount | The conditional flip from `credited`, and the `reversed` marker for a reversal that came first |
| The network retries a failure | Any exception inside the transaction answers 500 |
