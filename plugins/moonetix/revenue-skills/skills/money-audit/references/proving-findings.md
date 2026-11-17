# Proving findings

A proof is something another person can repeat and get the same result. Prefer a live request, then a test, then a code trace.

## Before proving, try to disprove

Most false findings die here. For each candidate, look for the guard somewhere other than the handler:

- **Schema:** a unique index or a check constraint the handler relies on without mentioning.
- **Middleware and gateways:** signature verification, authentication or rate limits applied before the route.
- **Framework behavior:** a request-wide database transaction, an ORM version column, a queue that delivers one message per key at a time.
- **Later steps:** an amount taken from the client but replaced with the server's price before it is charged.

If the guard exists, record the class as clear and name the guard. If you cannot find one, prove the bug.

## Run the app locally

- Use the project's development or test configuration, a local or in-memory database, and test keys. Never point it at production data or live provider accounts.
- If the app cannot start without a third party, stub that one call, or fall back to a trace.
- To prove a secret with a working default, start the app with that variable unset. The default is the finding, and the proof signs with it.
- If the project has no test framework, do not add one for the audit. Use a probe or a trace.
- A path behind a hold or a waiting period may be reached with a setting the app already has, such as a shorter hold in its test configuration. Say in the proof which setting was changed. Do not edit the database or the code to get there.
- Create your own test users through the app's normal sign-up. Do not edit the database by hand to set up a proof: the proof should use only what an attacker has.

## The probe script

`scripts/probe.mjs` sends one request once (`send`), several times in order (`replay`) or several times at once (`race`). It refuses targets that are not loopback addresses unless the host is named with `--allow-host`, caps `--times` at 20 and `--parallel` at 50, and never follows redirects.

Describe the request in a JSON file:

```json
{
  "method": "POST",
  "url": "http://127.0.0.1:3000/api/spend",
  "headers": { "authorization": "Bearer {{TOKEN}}" },
  "body": { "item": "boost" }
}
```

`{{TOKEN}}` is filled in from the command line with `--var TOKEN=...`. Keep tokens and keys out of request files this way: the files stay safe to keep, and the probe prints `{{TOKEN}}` instead of the value in its output. Fields named like a token, secret, password or API key in a response are printed as `***`; read one with `--extract`. Keep request files and any signing helper you write under `money-audit/evidence/`. Inside a URL a value is percent-encoded, except at the very start: `"url": "{{BASE}}/api/me"` with `--var BASE=http://127.0.0.1:3000` lets one file serve any port.

Use `"rawBody": "..."` instead of `"body"` when the exact bytes matter, as they do for a signed webhook.

To watch a number change, describe how to read it:

```json
{ "url": "http://127.0.0.1:3000/api/me", "headers": { "authorization": "Bearer {{TOKEN}}" }, "path": "balance" }
```

Then:

```bash
node scripts/probe.mjs send   spend.json --var TOKEN=$TOKEN --observe me.json
node scripts/probe.mjs replay webhook.json --times 2 --var TOKEN=$TOKEN --observe me.json
node scripts/probe.mjs race   spend.json --parallel 10 --var TOKEN=$TOKEN --observe me.json
```

`--observe` can be repeated, for example to watch the attacker's balance and the victim's in one run; give each an optional `"name"`. A path may end in `.length` to count a list, which is how to count what left the system: `"path": "payouts.length"`.

Setting up a proof usually takes a few calls: sign up, read an id, create an order. `--extract` prints one value from a response so it can feed the next call:

```bash
TOKEN=$(node scripts/probe.mjs send signup.json --extract token)
ORDER=$(node scripts/probe.mjs send checkout.json --var TOKEN=$TOKEN --extract order_id)
```

Edit the request without touching the file:

```bash
node scripts/probe.mjs send webhook.json --drop-header x-signature              # no signature at all
node scripts/probe.mjs send webhook.json --set-body data.amount_cents=1       # body changed, old signature kept
node scripts/probe.mjs send checkout.json --set-body coins=1000000            # extra field the client should not control
node scripts/probe.mjs send postback.json --set-query reward=99999            # parameter changed, old hash kept
node scripts/probe.mjs send transfer.json --set-body amount=-400              # sign
```

`--set-body` reads its value as JSON where it can: `amount=-400` and `amount=1e3` are sent as numbers. To send a string, quote it: `--set-body 'amount="1e3"'`.

The output is JSON: how many requests were sent, the status codes, sample response bodies, and the watched number before and after.

```json
{
  "probe": "race",
  "request": "POST http://127.0.0.1:3000/api/spend",
  "sent": 10,
  "statuses": { "200": 10 },
  "observed": { "path": "balance", "before": 300, "after": 0, "delta": -300 }
}
```

Ten purchases succeeded and the balance fell by the price of one. That is the proof.

## What the probe cannot do

The probe sends JSON and plain text over HTTP, and nothing more. When a proof needs one of the following, write a failing test in the project's own framework instead, or a small script under `money-audit/evidence/`:

- **Bodies other than JSON.** `--set-body`, `--drop-body`, `--observe` and `--extract` read JSON only. A form or multipart body can be sent byte for byte as `rawBody`, but not edited.
- **Sessions kept in cookies.** There is no cookie jar and no form login, and `--extract` cannot read a `Set-Cookie` header. Sign in once by other means, such as `curl -i`, and pass the session cookie as a `cookie` header filled with `--var`. A CSRF token that changes with every page is beyond it.
- **Requests that differ.** `race` and `replay` send the same request each time, apart from `{{i}}`, which is replaced with the number of each request (1 to N) in the URL, headers and body. Use it to give each request its own idempotency key or account. Anything else that must differ per request, such as a per-request signature, needs a script.
- **Races the server serializes.** A per-session lock (PHP's file sessions hold one), an idempotency key shared by every copy, or a per-account cap can make a race come back clear when the code is not. Send each copy with its own session or key before you call a class clear, and when that is not possible, prove it with a test or a trace.
- **Long responses.** Sample bodies are cut at 300 characters. Save the full output with `--out`, or read the value you need with `--extract`.

## Signed events

To test replay, tampering and reversal handling you need one correctly signed event. Sign it yourself with the **test** secret from the local configuration, the way the provider's documentation describes. For a timestamped HMAC scheme:

```bash
node -e '
const { createHmac } = require("node:crypto");
const body = JSON.stringify({ id: "evt_test_1", type: "payment.succeeded", data: { order_id: process.argv[1] } });
const t = Math.floor(Date.now() / 1000);
const v1 = createHmac("sha256", process.env.WEBHOOK_TEST_SECRET).update(`${t}.${body}`).digest("hex");
console.log(JSON.stringify({ method: "POST", url: "http://127.0.0.1:3000/webhooks/pay",
  headers: { "content-type": "application/json", "x-signature": `t=${t},v1=${v1}` }, rawBody: body }));
' ORDER_ID > webhook.json
```

Then `replay` it (duplicate credit), `send` it with a changed body and the old signature (verification), and `send` it with the signature header dropped.

Postbacks usually carry a hash of named fields in the query string. Read the formula in the handler or the network's documentation and build one the same way:

```bash
node -e '
const { createHmac } = require("node:crypto");
const [user, tx, reward, status] = process.argv.slice(1);
const hash = createHmac("sha256", process.env.POSTBACK_TEST_KEY).update([user, tx, reward, status].join(":")).digest("hex");
console.log(JSON.stringify({ url: `http://127.0.0.1:3000/postback?user_id=${user}&tx=${tx}&reward=${reward}&status=${status}&hash=${hash}` }));
' 42 tx-1001 200 1 > postback.json
```

The field order, the separator and the hash function differ between networks. Use the handler's own formula.

## Reading the result

- **State the expectation first.** "One purchase of 300 should lower the balance by 300 and deliver one item." Then compare.
- **Count what left the system,** not only what the response said: items delivered, payouts created, rows inserted.
- **Races are probabilistic.** Run a race probe three times. If it triggers once, it is proven. If it never triggers but the code checks and writes in separate steps with I/O between them and nothing serializes them, record it with a trace: a race that is hard to hit on one laptop is easy to hit with fifty connections.

## Test proofs

When the project has a test suite, a failing test is a strong proof and a useful gift: it becomes the regression test for the fix. Put it where the project keeps tests, name it for the behavior ("refunded order returns its credits"), and record the file and the command that runs it.

## Trace proofs

Use a trace when nothing can be run. It needs at least two steps, each with file, line and quoted code:

1. Where the attacker's value enters.
2. Each place it passes without a check that would stop it.
3. Where money or value moves.

Say where you looked for the missing guard ("no unique index on `transactions.tx_id` in `schema.sql`; no transaction around lines 30 to 44").

## Clean up

Stop the app. Delete anything that holds a session token or a key. Leave `money-audit/` with the map, `findings.json`, the report, and optionally an `evidence/` folder with saved probe output (`--out`), which a finding can name as `output_file`.

## Commands in findings

Write `proof.command` so that someone else can run it: the probe call with `--var TOKEN=$TOKEN` style placeholders, never a literal token or key. Describe once, in the report's `environment` field, how the app was started and how the test accounts were made, instead of repeating it in every finding.

## Never

- Send probes to a system you were not asked to test, or to any shared or production environment.
- Call a real payment or payout API to see what happens.
- Loop the probe to simulate load. The caps exist because the goal is a proof, not pressure.
- Put a live secret, a real user's data or a session token into a finding.
