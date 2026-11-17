# Verifying header signatures

A signature proves two things: the message was written by someone who holds the secret, and not one byte changed on the way. It does not prove that the message is new, that it is the first copy, or that what it says matches the app's records. Those are separate steps, covered in [process-events-once.md](process-events-once.md).

Query-string postbacks are verified differently. See [signed-postbacks.md](signed-postbacks.md).

## The order of work at the door

1. Refuse bodies above a size limit before reading them. One megabyte is far more than a webhook needs.
2. Take the raw bytes of the body.
3. Verify the signature over those bytes. On failure, answer 400 and stop.
4. Only now parse the body, check its shape and dispatch on the event type.

Nothing before step 3 may touch the database or depend on a value from the body. There is no switch that skips step 3: no debug flag, no query parameter, no "if the header is present".

## Getting the raw body

The provider signs the bytes it sent. A body that was parsed and serialized again has different bytes: key order, spacing and number formats change. Verify what arrived.

| Stack | The bytes as received |
| --- | --- |
| Express | `express.raw({ type: '*/*' })` on the webhook route, registered before `express.json()`. `req.body` is then a Buffer. |
| Fastify | A content type parser registered with `parseAs: 'buffer'` in the plugin scope of the webhook route. |
| Next.js route handler | `await request.text()` or `await request.arrayBuffer()`. Do not call `request.json()` first. |
| Flask | `request.get_data()` |
| Django | `request.body` |
| FastAPI, Starlette | `await request.body()` |
| PHP | `file_get_contents('php://input')` |
| Laravel | `$request->getContent()` |
| Rails | `request.raw_post` |
| Go | `io.ReadAll(http.MaxBytesReader(w, r.Body, 1<<20))` |

A proxy or middleware in front of the app that rewrites bodies (decompression is fine, reformatting JSON is not) breaks verification for the same reason. When genuine events fail, compare the length of the body the app sees with the `Content-Length` the provider sent before suspecting the secret.

Express wiring. The route is registered before the JSON parser, and a request without a content type leaves `req.body` as an empty object, so the handler checks for a Buffer:

```js
app.post('/webhooks/payments', express.raw({ type: '*/*', limit: '1mb' }), async (req, res, next) => {
  try {
    const result = await handlePaymentWebhook(pool, config, {
      rawBody: Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0),
      signatureHeader: req.get('x-signature'),
    });
    res.status(result.status).json(result.body);
  } catch (err) {
    next(err);
  }
});
app.use(express.json());
```

## Scheme one: timestamp and HMAC in one header

A common form: `X-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256 of "<t>.<raw body>">`. The timestamp is part of the signed text, so nobody can attach a fresh time to an old capture. The header name, the separator and the encoding differ by provider: check the provider's documentation for the exact signed text.

```js
import { createHmac, timingSafeEqual } from 'node:crypto';

// One or two secrets, comma separated. Two only while a rotation is in progress.
export function requireSecrets(name) {
  const secrets = String(process.env[name] ?? '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
  if (secrets.length === 0 || secrets.some((value) => value.length < 16)) {
    throw new Error(`${name} is missing or too short: the app does not start without it`);
  }
  return secrets;
}

// Header: t=<unix seconds>,v1=<hex HMAC-SHA256 of "<t>.<raw body>">
// rawBody is the Buffer that arrived, before any parser touched it.
export function verifyTimestamped(rawBody, header, secrets, toleranceSeconds = 300, nowSeconds = Date.now() / 1000) {
  let t = null;
  const given = [];
  for (const part of String(header ?? '').split(',')) {
    const [name, value = ''] = part.trim().split('=');
    if (name === 't' && /^\d{1,12}$/.test(value)) t = value;
    if (name === 'v1' && /^[a-f0-9]{64}$/i.test(value)) given.push(Buffer.from(value, 'hex'));
  }
  if (t === null || given.length === 0 || !Buffer.isBuffer(rawBody)) return false;
  if (Math.abs(nowSeconds - Number(t)) > toleranceSeconds) return false;

  let matched = false;
  for (const secret of secrets) {
    const expected = createHmac('sha256', secret).update(`${t}.`).update(rawBody).digest();
    for (const signature of given) {
      if (timingSafeEqual(signature, expected)) matched = true;
    }
  }
  return matched;
}
```

Call `requireSecrets` once when the process starts, not inside the handler. An app that boots without the secret and fails on the first event has already lost events.

**Tolerance.** Five minutes is the usual window. It bounds how long a captured request stays usable, and the stored event id covers the time inside the window. A timestamp too far in the future is refused as well. The server clock must be synchronized: a host that drifts by minutes rejects every genuine event.

**Retries.** Many providers that use this scheme sign each delivery attempt with a new timestamp, so a retry hours later still verifies. Check the provider's documentation. If retries reuse the first timestamp, the tolerance must be at least as long as the retry schedule, and the event id store is the replay protection.

## Scheme two: HMAC of the body in a single header

No timestamp. The header carries the HMAC of the raw body, hex or base64 encoded. Python:

```python
import base64
import hashlib
import hmac


def verify_body_hmac(raw_body: bytes, header: str | None, secrets: list[bytes]) -> bool:
    """The header carries base64(HMAC-SHA256(secret, raw body)). True when a current secret matches."""
    try:
        given = base64.b64decode(header or "", validate=True)
    except ValueError:
        return False
    matched = False
    for secret in secrets:
        expected = hmac.new(secret, raw_body, hashlib.sha256).digest()
        if hmac.compare_digest(given, expected):
            matched = True
    return matched
```

```python
SECRETS = [s.encode() for s in os.environ["WEBHOOK_SECRETS"].split(",") if s]   # KeyError at start-up when unset
if not SECRETS or any(len(s) < 16 for s in SECRETS):
    raise RuntimeError("WEBHOOK_SECRETS is empty or too short")


@app.post("/webhooks/payments")
def payments_webhook():
    raw = request.get_data()   # the bytes as received; read them before anything parses the body
    if not verify_body_hmac(raw, request.headers.get("X-Signature"), SECRETS):
        abort(400)
    event = json.loads(raw)
    return handle_event(event)   # the event store and the handlers
```

Without a signed timestamp a captured event verifies forever. The stored event id is then the only replay protection, so event ids are never deleted while the secret that signed them is still accepted.

## Comparing in constant time

An ordinary string comparison stops at the first differing character, and the time it takes tells an attacker how much of a guess was right. Use the function made for it.

| Language | Function | Note |
| --- | --- | --- |
| Node | `crypto.timingSafeEqual(a, b)` | Throws when the lengths differ. Compare decoded digests, whose length is fixed, or hash both sides first. |
| Python | `hmac.compare_digest(a, b)` | Both arguments bytes, or both ASCII strings. |
| PHP | `hash_equals($expected, $given)` | The value the app computed goes first. |
| Go | `hmac.Equal(a, b)` | |
| Ruby | `OpenSSL.secure_compare(a, b)` or `Rack::Utils.secure_compare` | |
| Java | `MessageDigest.isEqual(a, b)` | |

Compare bytes, or normalize first. Some providers send hex in upper case, and a lower-case comparison of strings then rejects genuine events. Decode both sides, or lower-case the received value before comparing strings.

## Secrets

- One secret per provider and per environment. The test secret never verifies production events, and the other way round.
- Required at start-up, with a minimum length, and no default. `process.env.WEBHOOK_SECRET || 'changeme'` turns a missing variable into a public key.
- Read from the environment or the project's secret store. Never committed, never sent to a browser or a mobile app, never written to a log, an error message or an alert.
- Some providers hand out the secret in an encoded form with a prefix. Check the provider's documentation for whether the key of the HMAC is the string as shown or the decoded bytes.
- Log that verification failed, with the provider name and the request id. Do not log the received signature next to the expected one.

## Rotation

The verifier takes a list so that a rotation loses no events.

1. Create the new secret at the provider. Some providers keep the old one valid for a period, some switch at once, and some send two signatures per event during the overlap. Check the provider's documentation.
2. Deploy with both secrets in the list, new one first.
3. Switch the provider to the new secret, if step 1 did not do it.
4. Watch for events verified by the old secret. Log which position in the list matched, never the value. When none has matched for longer than the provider's retry schedule, remove the old secret and deploy again.

A planned rotation keeps both for a day or a few. After a leak there is no overlap: the old secret is removed at once, and events signed with it fail until the provider sends them again under the new one. Because event ids are stored, anything an attacker replays from before the leak is already known.

## Other schemes

- **The provider's SDK.** When the project already uses the provider's official library and it ships a verification helper, call it instead of writing the HMAC by hand. Give it the raw body. Check what it throws or returns, and treat every failure as a refusal.
- **A signed token (JWS) as the payload,** as some app stores send. Decoding the payload is not verifying it. Verify the signature and the certificate chain up to the vendor's root certificate, with the vendor's library where one exists, then check that the bundle or package id and the environment in the payload are the app's own.
- **A shared value in the `Authorization` header.** Compare it in constant time. It proves the sender, not the body, so it relies on TLS for integrity.
- **No signature at all.** Treat the message as a hint. Read the id from it, ask the provider's API for the object with the app's own credentials, and act on the answer.
- **Sender addresses, mutual TLS.** Useful as a second layer, never as the only check. An address list must be matched against the socket peer, or against a forwarding header only when the peer is a proxy the app trusts.

## Answering a failed check

Answer 400 (401 and 403 are equally fine) with a body that says nothing about why. Do not parse the body, do not store the event, do not answer 2xx. A burst of failures is worth an alert: it is either an attack or a broken rotation.
