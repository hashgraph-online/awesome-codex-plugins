# Worked example: one metered LLM call

The reserve, call, settle flow for one streamed model call, in TypeScript on Node with node-postgres and in Python with psycopg 3, against a generic provider client. The SQL is PostgreSQL. It uses the tables of `assets/credits-schema.sql`, the price tables and the `price_version` column from [ai-pricing.md](ai-pricing.md), and the columns below. The rules behind each step are in [ai-calls-and-streams.md](ai-calls-and-streams.md).

```sql
ALTER TABLE credit_reservations
  ADD COLUMN recorded_cost   BIGINT CHECK (recorded_cost >= 0),
  ADD COLUMN provider_micros BIGINT,
  ADD COLUMN usage           JSONB,
  ADD COLUMN estimated       BOOLEAN NOT NULL DEFAULT false;
```

`recorded_cost` is written as soon as the cost is known, before the commit. If the commit fails or the process dies, the sweeper commits the recorded cost instead of releasing it.

## The provider client

Each provider gets an adapter that maps its stream onto three events. The mapping of usage fields per provider is in [ai-pricing.md](ai-pricing.md), and where a stream reports usage in [ai-calls-and-streams.md](ai-calls-and-streams.md).

- `{ type: 'delta', text }` for every piece of output the app uses, text and tool call arguments alike.
- `{ type: 'usage', usage, final }` with usage already mapped to kinds. `final` is true only for the provider's report of the whole call.
- The end of the iteration. An error is thrown.

## TypeScript

`costOf`, `boundUsage` and `promptBound` are the functions from [ai-pricing.md](ai-pricing.md), kept in `llm-pricing.js`.

```ts
import type { Pool, PoolClient } from 'pg';
import { boundUsage, costOf, promptBound } from './llm-pricing.js';

export type TokenKind = 'input' | 'cached_input' | 'cache_write' | 'cache_write_long' | 'output';
export type Usage = { tokens: Partial<Record<TokenKind, number>>; calls?: Record<string, number> };
export type Rates = { versionId: number; markupBps: number; perMTok: Partial<Record<TokenKind, bigint>>; perCall: Record<string, bigint> };
export type ModelEvent = { type: 'delta'; text: string } | { type: 'usage'; usage: Usage; final: boolean };
export type ModelRequest = { model: string; messages: unknown[]; maxOutputTokens: number };

export interface ModelClient {
  countPromptTokens(request: ModelRequest): Promise<number>;
  countOutputTokens(model: string, text: string): Promise<number>;
  stream(request: ModelRequest, signal: AbortSignal): AsyncIterable<ModelEvent>;
}

export class InsufficientCredits extends Error {
  needed: number;
  constructor(needed: number) {
    super('insufficient_credits');
    this.needed = needed;
  }
}

const MAX_OUTPUT_TOKENS = 2048;
const CALL_TIMEOUT_MS = 120_000;
const RESERVATION_TTL_SECONDS = CALL_TIMEOUT_MS / 1000 + 60;
const PROMPT_KINDS: TokenKind[] = ['input', 'cached_input', 'cache_write', 'cache_write_long'];

async function inTransaction<T>(pool: Pool, work: (tx: PoolClient) => Promise<T>): Promise<T> {
  const tx = await pool.connect();
  try {
    await tx.query('BEGIN');
    const result = await work(tx);
    await tx.query('COMMIT');
    return result;
  } catch (err) {
    await tx.query('ROLLBACK');
    throw err;
  } finally {
    tx.release();
  }
}

// The prices of one model in the band its prompt falls into. Without versionId: the version in force now.
export async function loadRates(pool: Pool, model: string, promptTokens: number, versionId?: number): Promise<Rates> {
  const version = versionId === undefined
    ? await pool.query('SELECT id, markup_bps FROM price_versions WHERE effective_from <= now() ORDER BY effective_from DESC LIMIT 1')
    : await pool.query('SELECT id, markup_bps FROM price_versions WHERE id = $1', [versionId]);
  if (version.rowCount !== 1) throw new Error('no price version');
  const id = Number(version.rows[0].id);
  const prices = await pool.query(
    `SELECT kind, micros FROM model_prices
      WHERE version_id = $1 AND model = $2
        AND band_from = (SELECT MAX(band_from) FROM model_prices WHERE version_id = $1 AND model = $2 AND band_from <= $3)`,
    [id, model, promptTokens],
  );
  if (prices.rowCount === 0) throw new Error(`no prices for ${model}`);
  const rates: Rates = { versionId: id, markupBps: Number(version.rows[0].markup_bps), perMTok: {}, perCall: {} };
  for (const { kind, micros } of prices.rows) {
    if (kind.startsWith('call:')) rates.perCall[kind.slice(5)] = BigInt(micros);
    else rates.perMTok[kind as TokenKind] = BigInt(micros);
  }
  return rates;
}

async function reserve(pool: Pool, accountId: number, reservationId: string, amount: number, versionId: number): Promise<boolean> {
  return inTransaction(pool, async (tx) => {
    const created = await tx.query(
      `INSERT INTO credit_reservations (id, account_id, feature, amount, price_version, expires_at)
       VALUES ($1, $2, 'llm', $3, $4, now() + make_interval(secs => $5))
       ON CONFLICT (id) DO NOTHING`,
      [reservationId, accountId, amount, versionId, RESERVATION_TTL_SECONDS],
    );
    if (created.rowCount === 0) return false; // this action was reserved before: a retry
    // One conditional statement. Parallel reservations wait for the account row and see
    // what the one before them reserved.
    const held = await tx.query(
      'UPDATE credit_accounts SET reserved = reserved + $2 WHERE account_id = $1 AND balance - reserved >= $2',
      [accountId, amount],
    );
    if (held.rowCount === 0) throw new InsufficientCredits(amount); // the rollback removes the reservation row
    return true;
  });
}

async function recordCost(pool: Pool, reservationId: string, credits: number, providerMicros: number, usage: Usage, estimated: boolean) {
  await pool.query(
    `UPDATE credit_reservations SET recorded_cost = $2, provider_micros = $3, usage = $4, estimated = $5
      WHERE id = $1 AND status <> 'committed' AND recorded_cost IS NULL`,
    [reservationId, credits, providerMicros, JSON.stringify(usage), estimated],
  );
}

// Commits the recorded cost, or releases when none was recorded. Settles once; the sweeper calls it too.
export async function settle(pool: Pool, reservationId: string): Promise<{ charged: number; repeated?: boolean; late?: boolean }> {
  return inTransaction(pool, async (tx) => {
    const found = await tx.query(
      'SELECT account_id, amount, status, recorded_cost FROM credit_reservations WHERE id = $1 FOR UPDATE',
      [reservationId],
    );
    const row = found.rows[0];
    if (!row || row.status === 'committed') return { charged: 0, repeated: true };
    const bound = Number(row.amount);
    const cost = row.recorded_cost === null ? 0 : Math.min(Number(row.recorded_cost), bound);
    const late = row.status === 'released'; // the sweeper released it, then the cost arrived
    if (late && cost === 0) return { charged: 0, repeated: true };
    if (!late) {
      await tx.query('UPDATE credit_accounts SET reserved = reserved - $2 WHERE account_id = $1', [row.account_id, bound]);
    }
    if (cost === 0) {
      await tx.query(`UPDATE credit_reservations SET status = 'released', used = 0, settled_at = now() WHERE id = $1`, [reservationId]);
      return { charged: 0 };
    }
    await tx.query(`UPDATE credit_reservations SET status = 'committed', used = $2, settled_at = now() WHERE id = $1`, [reservationId, cost]);
    const entry = await tx.query(
      `INSERT INTO credit_ledger (account_id, amount, kind, ref) VALUES ($1, $2, 'usage', $3)
       ON CONFLICT (kind, ref) DO NOTHING`,
      [row.account_id, -cost, reservationId],
    );
    // No balance condition: the reservation set these credits aside. Only a refund that ran
    // in the meantime can take the balance below zero here.
    if (entry.rowCount === 1) {
      await tx.query('UPDATE credit_accounts SET balance = balance - $2 WHERE account_id = $1', [row.account_id, cost]);
    }
    return { charged: cost, late };
  });
}

export async function runMetered(
  pool: Pool,
  client: ModelClient,
  call: { accountId: number; idempotencyKey: string; model: string; messages: unknown[]; onDelta: (text: string) => void; clientGone: AbortSignal },
) {
  const reservationId = `${call.accountId}:${call.idempotencyKey}`;
  const request: ModelRequest = { model: call.model, messages: call.messages, maxOutputTokens: MAX_OUTPUT_TOKENS };
  const counted = await client.countPromptTokens(request);
  const promptTokens = promptBound(counted);
  const rates = await loadRates(pool, call.model, promptTokens);
  const bound = costOf(rates, boundUsage(rates, { promptTokens, maxOutputTokens: MAX_OUTPUT_TOKENS })).credits;

  if (!(await reserve(pool, call.accountId, reservationId, bound, rates.versionId))) {
    return { repeated: true as const, reservationId };
  }

  const signal = AbortSignal.any([call.clientGone, AbortSignal.timeout(CALL_TIMEOUT_MS)]);
  let delivered = '';
  let reported: { usage: Usage; final: boolean } | null = null;
  let failure: unknown = null;
  try {
    for await (const event of client.stream(request, signal)) {
      if (event.type === 'delta') {
        delivered += event.text;
        call.onDelta(event.text);
      } else {
        reported = { usage: event.usage, final: event.final };
      }
    }
  } catch (err) {
    failure = err; // a provider error, the timeout, or the user leaving
  }

  // Nothing delivered: nothing charged, whatever the provider reported.
  if (delivered !== '') {
    let usage: Usage;
    let estimated = false;
    if (reported?.final) {
      usage = reported.usage;
    } else {
      // Cut stream: the last running report, raised to our own count of what was delivered.
      estimated = true;
      const running = reported?.usage.tokens ?? {};
      const knownPrompt = PROMPT_KINDS.some((kind) => running[kind] !== undefined);
      const output = Math.max(running.output ?? 0, await client.countOutputTokens(call.model, delivered));
      usage = { tokens: { ...(knownPrompt ? running : { input: counted }), output }, calls: reported?.usage.calls };
    }
    const promptTotal = PROMPT_KINDS.reduce((sum, kind) => sum + (usage.tokens[kind] ?? 0), 0);
    const cost = costOf(await loadRates(pool, call.model, promptTotal, rates.versionId), usage);
    await recordCost(pool, reservationId, cost.credits, cost.providerMicros, usage, estimated);
  }
  const settled = await settle(pool, reservationId);
  if (failure !== null && delivered === '') throw failure;
  return { repeated: false as const, reservationId, charged: settled.charged, cut: failure !== null };
}

// Scheduled every minute. Commits a recorded cost, releases the rest.
export async function sweep(pool: Pool, limit = 200): Promise<number> {
  const due = await pool.query(
    `SELECT id FROM credit_reservations WHERE status = 'open' AND expires_at < now() ORDER BY expires_at LIMIT $1`,
    [limit],
  );
  for (const { id } of due.rows) await settle(pool, id);
  return due.rowCount ?? 0;
}
```

An Express-style route around it. The account comes from the session, the model and the output limit from the server.

```ts
import type { Request, Response } from 'express';
import { InsufficientCredits, runMetered } from './llm-credits.js';
import type { ModelClient } from './llm-credits.js';
import type { Pool } from 'pg';

const KEY = /^[A-Za-z0-9_-]{8,64}$/;

export function generateRoute(pool: Pool, client: ModelClient, model: string) {
  return async (req: Request & { user: { accountId: number } }, res: Response) => {
    const key = req.get('Idempotency-Key') ?? '';
    if (!KEY.test(key)) return res.status(400).json({ error: 'idempotency_key_required' });
    const gone = new AbortController();
    res.on('close', () => {
      if (!res.writableEnded) gone.abort();
    });
    try {
      const result = await runMetered(pool, client, {
        accountId: req.user.accountId,
        idempotencyKey: key,
        model,
        messages: req.body.messages,
        onDelta: (text) => res.write(text),
        clientGone: gone.signal,
      });
      if (result.repeated) return res.status(409).json({ error: 'already_started', id: result.reservationId });
      res.end();
    } catch (err) {
      if (err instanceof InsufficientCredits) return res.status(402).json({ error: 'insufficient_credits', needed: err.needed });
      if (res.headersSent) return res.end();
      res.status(502).json({ error: 'model_failed_credits_returned' });
    }
  };
}
```

A repeated key here answers 409 with the id. A product that can replay a finished answer stores it under the reservation id and returns it instead.

## Python

Synchronous psycopg 3, with the connection opened with `autocommit=True` so that each `with conn.transaction():` block is one transaction. `client.stream` yields the same three events as dictionaries, and `client_gone` is a `threading.Event` set by the web layer when the user disconnects. The SQL is the same as above. With `psycopg.AsyncConnection` and `async for` it carries over to FastAPI unchanged.

```python
from psycopg.types.json import Jsonb

PER_MTOK = 1_000_000
BPS = 10_000
MICROS_PER_CREDIT = 1_000
MAX_OUTPUT_TOKENS = 2048
CALL_TIMEOUT_SECONDS = 120
RESERVATION_TTL_SECONDS = CALL_TIMEOUT_SECONDS + 60
PROMPT_KINDS = ("input", "cached_input", "cache_write", "cache_write_long")


class InsufficientCredits(Exception):
    def __init__(self, needed):
        super().__init__("insufficient_credits")
        self.needed = needed


def cost_of(rates, usage):
    scaled = 0
    for kind, count in usage["tokens"].items():
        if count:
            scaled += count * rates["per_mtok"][kind]  # KeyError: no price for this kind
    for tool, count in usage.get("calls", {}).items():
        if count:
            scaled += count * rates["per_call"][tool] * PER_MTOK
    divisor = PER_MTOK * BPS * MICROS_PER_CREDIT
    credits = -(-scaled * rates["markup_bps"] // divisor)  # round up, once
    return credits, -(-scaled // PER_MTOK)


def prompt_bound(counted):
    return counted + -(-counted // 20) + 64


def bound_usage(rates, prompt_tokens, max_output_tokens):
    kinds = [k for k in ("cache_write_long", "cache_write", "input") if k in rates["per_mtok"]]
    prompt_kind = max(kinds, key=lambda k: rates["per_mtok"][k])
    return {"tokens": {prompt_kind: prompt_tokens, "output": max_output_tokens}}


def load_rates(conn, model, prompt_tokens, version_id=None):
    if version_id is None:
        version = conn.execute(
            "SELECT id, markup_bps FROM price_versions WHERE effective_from <= now() "
            "ORDER BY effective_from DESC LIMIT 1"
        ).fetchone()
    else:
        version = conn.execute("SELECT id, markup_bps FROM price_versions WHERE id = %s", (version_id,)).fetchone()
    if version is None:
        raise LookupError("no price version")
    rows = conn.execute(
        "SELECT kind, micros FROM model_prices WHERE version_id = %s AND model = %s AND band_from = "
        "(SELECT MAX(band_from) FROM model_prices WHERE version_id = %s AND model = %s AND band_from <= %s)",
        (version[0], model, version[0], model, prompt_tokens),
    ).fetchall()
    if not rows:
        raise LookupError(f"no prices for {model}")
    rates = {"version_id": version[0], "markup_bps": version[1], "per_mtok": {}, "per_call": {}}
    for kind, micros in rows:
        if kind.startswith("call:"):
            rates["per_call"][kind[5:]] = micros
        else:
            rates["per_mtok"][kind] = micros
    return rates


def reserve(conn, account_id, reservation_id, amount, version_id):
    with conn.transaction():
        created = conn.execute(
            "INSERT INTO credit_reservations (id, account_id, feature, amount, price_version, expires_at) "
            "VALUES (%s, %s, 'llm', %s, %s, now() + make_interval(secs => %s)) ON CONFLICT (id) DO NOTHING",
            (reservation_id, account_id, amount, version_id, RESERVATION_TTL_SECONDS),
        )
        if created.rowcount == 0:
            return False
        held = conn.execute(
            "UPDATE credit_accounts SET reserved = reserved + %s WHERE account_id = %s AND balance - reserved >= %s",
            (amount, account_id, amount),
        )
        if held.rowcount == 0:
            raise InsufficientCredits(amount)  # leaves the block, which rolls the insert back
        return True


def record_cost(conn, reservation_id, credits, provider_micros, usage, estimated):
    conn.execute(
        "UPDATE credit_reservations SET recorded_cost = %s, provider_micros = %s, usage = %s, estimated = %s "
        "WHERE id = %s AND status <> 'committed' AND recorded_cost IS NULL",
        (credits, provider_micros, Jsonb(usage), estimated, reservation_id),
    )


def settle(conn, reservation_id):
    with conn.transaction():
        row = conn.execute(
            "SELECT account_id, amount, status, recorded_cost FROM credit_reservations WHERE id = %s FOR UPDATE",
            (reservation_id,),
        ).fetchone()
        if row is None or row[2] == "committed":
            return 0
        account_id, bound, status, recorded = row
        cost = 0 if recorded is None else min(recorded, bound)
        late = status == "released"
        if late and cost == 0:
            return 0
        if not late:
            conn.execute("UPDATE credit_accounts SET reserved = reserved - %s WHERE account_id = %s", (bound, account_id))
        if cost == 0:
            conn.execute(
                "UPDATE credit_reservations SET status = 'released', used = 0, settled_at = now() WHERE id = %s",
                (reservation_id,),
            )
            return 0
        conn.execute(
            "UPDATE credit_reservations SET status = 'committed', used = %s, settled_at = now() WHERE id = %s",
            (cost, reservation_id),
        )
        entry = conn.execute(
            "INSERT INTO credit_ledger (account_id, amount, kind, ref) VALUES (%s, %s, 'usage', %s) "
            "ON CONFLICT (kind, ref) DO NOTHING",
            (account_id, -cost, reservation_id),
        )
        if entry.rowcount == 1:
            conn.execute("UPDATE credit_accounts SET balance = balance - %s WHERE account_id = %s", (cost, account_id))
        return cost


def run_metered(conn, client, account_id, idempotency_key, model, messages, on_delta, client_gone):
    reservation_id = f"{account_id}:{idempotency_key}"
    request = {"model": model, "messages": messages, "max_output_tokens": MAX_OUTPUT_TOKENS}
    counted = client.count_prompt_tokens(request)
    prompt_tokens = prompt_bound(counted)
    rates = load_rates(conn, model, prompt_tokens)
    bound, _ = cost_of(rates, bound_usage(rates, prompt_tokens, MAX_OUTPUT_TOKENS))
    if not reserve(conn, account_id, reservation_id, bound, rates["version_id"]):
        return {"repeated": True, "reservation_id": reservation_id}

    delivered, reported, failure = "", None, None
    stream = client.stream(request, timeout=CALL_TIMEOUT_SECONDS)
    try:
        for event in stream:
            if client_gone.is_set():
                raise ConnectionAbortedError("client gone")
            if event["type"] == "delta":
                delivered += event["text"]
                on_delta(event["text"])
            else:
                reported = event
    except Exception as err:  # a provider error, the timeout, or the user leaving
        failure = err
    finally:
        stream.close()  # stops the provider request if it is still running

    if delivered:
        estimated = not (reported and reported["final"])
        if not estimated:
            usage = reported["usage"]
        else:
            running = reported["usage"]["tokens"] if reported else {}
            known_prompt = any(kind in running for kind in PROMPT_KINDS)
            output = max(running.get("output", 0), client.count_output_tokens(model, delivered))
            usage = {"tokens": {**(running if known_prompt else {"input": counted}), "output": output},
                     "calls": reported["usage"].get("calls", {}) if reported else {}}
        prompt_total = sum(usage["tokens"].get(kind, 0) for kind in PROMPT_KINDS)
        credits, provider_micros = cost_of(load_rates(conn, model, prompt_total, rates["version_id"]), usage)
        record_cost(conn, reservation_id, credits, provider_micros, usage, estimated)
    charged = settle(conn, reservation_id)
    if failure is not None and not delivered:
        raise failure
    return {"repeated": False, "reservation_id": reservation_id, "charged": charged, "cut": failure is not None}
```

## Tests to write

With a stand-in client that can finish, fail before output, fail after some output, report running usage only, and hang until aborted:

1. A finished call: one `usage` entry for the cost of the reported usage, `reserved` back to 0, the cost stored next to the provider cost.
2. The same idempotency key again: no second model call, no second entry.
3. An error before output: released, balance unchanged, the error reaches the route.
4. A stream cut after output with no final report: committed for the counted prompt and the counted output, marked estimated, at most the bound.
5. The user disconnects during the stream: the stand-in sees its signal aborted, and the delivered part is charged.
6. A balance that covers two bounds and ten parallel calls with different keys: two model calls, eight 402s, a balance that never goes below zero.
7. The same ten calls through code that checks the balance, calls the model and charges afterwards: more calls than the balance covers. Keep this test as the reason the reservation exists.
8. A reservation past its expiry with a recorded cost is committed by the sweeper; one without is released. Settling twice changes nothing.
9. A price version that takes effect during a call: the call is priced with the version stored on its reservation.
10. After every test, both reconcile queries from [credit-ledger.md](credit-ledger.md) return no rows.
