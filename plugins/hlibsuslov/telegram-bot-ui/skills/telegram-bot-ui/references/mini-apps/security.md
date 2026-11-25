---
summary: "Mini App security contract: what the client controls, initData verification (token and Ed25519), freshness, sessions, storage, inputs, hosting, logging; read before writing a Mini App backend."
verified: "2026-11-23"
bot_api: "10.5"
---

# Mini App security: initData, sessions, inputs, hosting

## Contents

- [1. What the client controls](#1-what-the-client-controls)
- [2. Verifying initData on your own server (bot token) [Official]](#2-verifying-initdata-on-your-own-server-bot-token-official)
- [3. Verifying without the token (Ed25519, since 8.0) [Official]](#3-verifying-without-the-token-ed25519-since-80-official)
- [4. Freshness: `auth_date`](#4-freshness-auth_date)
- [5. After verification: the session](#5-after-verification-the-session)
- [6. Where data lives on the device](#6-where-data-lives-on-the-device)
- [7. Inputs that look harmless](#7-inputs-that-look-harmless)
- [8. Hosting, headers and origins](#8-hosting-headers-and-origins)
- [9. Telegram Serverless](#9-telegram-serverless)
- [10. Logging and errors](#10-logging-and-errors)
- [11. Checklist](#11-checklist)

A Mini App is a public web page running on the user's device. Everything it sends to your server can be
forged except the signature Telegram puts on `initData`. This page is the server's contract. Checked on
**2026-11-23** against https://core.telegram.org/bots/webapps ("Validating data received via the Mini App",
"Validating data for Third-Party Use") and the Bot API 10.5 changelog.

Labels: **[Official]** Mini Apps page; **[API]** Bot API; **[Heuristic]** this skill's rule.

## 1. What the client controls

| Input | Trust |
|---|---|
| `Telegram.WebApp.initData` (raw string) | trusted **only after** your server verifies `hash` (or `signature`) and `auth_date` |
| `initDataUnsafe` and anything the client computed from it | never; it is the same data without a check **[Official]** |
| `start_param` / `tgWebAppStartParam` | text from a link anyone can craft: allowlist-parse it |
| `sendData` → `web_app_data.data` | delivered by Telegram (authentic sender) but its **content** is user-controlled |
| request bodies, prices, quantities, user ids in JSON | never; recompute on the server |
| `colorScheme`, `platform`, `version` | layout hints, never security decisions |
| `invoiceClosed` status `paid` | a UI hint; the order is paid only when the bot receives `successful_payment` ([../payments-and-stars.md](../payments-and-stars.md)) |

## 2. Verifying initData on your own server (bot token) [Official]

1. Parse the raw `initData` as a query string; values are URL-decoded.
2. Take out `hash`. Build the data-check-string from **all other received fields** (so `signature`, when
   present, stays in), sorted by key, as `key=value`, joined with `\n` (0x0A).
3. `secret_key = HMAC_SHA256(key = "WebAppData", message = bot_token)` (raw 32 bytes, not hex).
4. Valid when `hex(HMAC_SHA256(key = secret_key, message = data_check_string)) == hash`. Compare in
   constant time.
5. Check `auth_date` (§4).

Rules on top **[Heuristic]**:

- Reject a string with a repeated key, an empty or non-hex `hash`, or no `auth_date`; a parser that keeps
  the last duplicate verifies something other than what you read.
- Reject field names outside `[a-z_]` and any value that contains a newline. The check string joins
  `key=value` pairs with `\n`, so a value with `%0A` could fold the next field into it (dropping `user`, for
  example) while the signed text stays the same. Telegram never sends a raw newline: JSON escapes it.
- Decode `signature` strictly (base64url, 86 characters, optional `==`); never use it as an identifier.
- Use the decoded `user` JSON only after the check; read `user.id` as a 64-bit integer (up to 52
  significant bits) **[Official]**.
- The token comes from the environment and stays on the server; store only the derived `secret_key` in
  memory if you can. It never appears in the front-end bundle, a URL, a log line or an error message.

## 3. Verifying without the token (Ed25519, since 8.0) [Official]

For a third party (a builder, an analytics or auth service) that knows only the `bot_id`. The version comes from
the page's changelog (Bot API 8.0, November 17, 2024: third parties "are now able to validate it without knowing
the App's bot token"); the `signature` row and the validation section carry no version mark of their own.

- data-check-string = `"<bot_id>:WebAppData\n"` + every field **except `hash` and `signature`**, sorted,
  `key=value`, joined with `\n`.
- `signature` is the base64url Ed25519 signature of that string, sent **without padding**; add `=` before a
  strict decoder.
- Public keys (hex): production `e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d`, test
  environment `40055058a4ee38156a06562e52eece92a771bcd8346a8c4615cb7376eddf72ec`. Pick the key from
  configuration, never from the request.
- Check `auth_date` as well.

Reference implementations without dependencies (Python stdlib with an RFC 8032 verifier, and
`node:crypto`), with HMAC and Ed25519 test vectors, expiry and tampering tests, live in
`examples/mini-apps/server/`. The vectors are self-made (a test token and a test Ed25519 seed): the code follows
the official algorithm and the Ed25519 part passes the RFC 8032 vectors, but no Telegram-signed `initData` is in the
repo, so agreement with a real one is **[Unverified]** until a test-environment capture is added. Library
alternative for Node: `@tma.js/init-data` (the 4.x name of `@tma.js/init-data-node`; `validate`, `validate3rd`,
`expiresIn`). **[Third-party]**

## 4. Freshness: `auth_date`

Telegram sets no lifetime; it only says to check the field "to prevent the use of outdated data".
**[Third-party]** `@tma.js/init-data` defaults to 24 hours. This skill's rule **[Heuristic]**:

| Action | Maximum age of `initData` |
|---|---|
| Reading the user's own non-sensitive data | 24 h |
| Starting a session that can spend money, change rights or show private data | 1 h |
| Inside an established session | your own session token (§5), not an old `initData` |
| `auth_date` in the future | reject beyond 60 s of clock skew |

## 5. After verification: the session

- Transport: send the raw string on every request as `Authorization: tma <initData>`, the convention of the
  Mini Apps ecosystem (docs.telegram-mini-apps.com), not a Telegram requirement. **[Third-party]** Telegram's own
  script sends a different form for `WebApp.Serverless.call`: `'Authorization': 'TMA ' + window.btoa(webAppInitData)`
  (uppercase scheme, base64 value; telegram-web-app.js, read 2026-11-25) **[Official]**. A server that may see
  both reads the scheme case-insensitively and decodes a value without `hash=` as base64
  (`fromAuthorization` in `server/ts/verifyInitData.ts`). **[Heuristic]**
- Simplest correct model: verify `initData` on every request (it is one HMAC) and apply §4. **[Heuristic]**
- For long sessions or step-up actions, exchange verified `initData` for your own short-lived token
  (15-60 min), bound to `user.id`, kept in memory (or `SecureStorage` on 9.0+ clients), never in
  `localStorage`. Telegram Web opens the app in a cross-site iframe, so a cookie session is a third-party
  cookie there and may be blocked; prefer the header. **[Heuristic]**
- Authorise every request on the server: the resource belongs to the verified `user.id`, the action is
  allowed in its current state. A hidden button is not authorisation. **[Heuristic]**
- `query_id` is single use: answer it once (`answerWebAppQuery`), record it in a durable store shared by all
  workers only after the call succeeded, reject a replay. Build the answer on the server: it appears in the
  chat under the bot's name, so client-supplied text there is a phishing vector. **[Heuristic]**
- A verified `initData` works like a bearer credential until it expires: actions that move money or change
  state also carry an idempotency key. **[Heuristic]**

The kit's `tma.api()` does this with a timeout, safe retries, idempotency keys and typed errors
([forms-and-data.md](forms-and-data.md) §5-7). Without the kit:

```js
// Client: one fetch wrapper for every API call.
export async function api(path, body) {
  const res = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: { Authorization: `tma ${Telegram.WebApp.initData}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) throw new Error('session-expired');  // reopen the app: initData is refreshed on launch
  if (!res.ok) throw new Error(`http-${res.status}`);
  return res.json();
}
```

## 6. Where data lives on the device

| Data | Store **[Heuristic]** |
|---|---|
| Session token, refresh token, API key of the user's own account | `SecureStorage` (9.0, Keychain/Keystore, 10 items); else memory only |
| Draft form, UI preferences, "coachmark seen" | `CloudStorage` (6.9, synced) or `DeviceStorage` (9.0, 5 MB) |
| Cache of server data | memory or `DeviceStorage`; always revalidate |
| The bot token, payment provider secrets, other users' data | never on the device |

`localStorage` is shared by everything on your origin and survives logouts; it is not a place for tokens
or personal data. `scripts/miniapp_lint.py` flags it.

## 7. Inputs that look harmless

- `start_param`: up to 512 chars `[A-Za-z0-9_-]` **[Official]**; match it against known patterns
  (`^order-[0-9]{1,12}$`), then load the order **and check it belongs to the user**.
- `web_app_data.data` (≤ 4096 bytes): parse JSON with a size limit and a schema; the user can send any
  string through a modified client.
- Prices and totals: the client sends item ids and quantities; the server prices them and creates the
  invoice link (`createInvoiceLink`). Digital goods are sold in Stars; the whole Mini App payment flow, with
  a signed payload bound to the user: [payments.md](payments.md).
- Rendering user or model text in the app: text nodes or a sanitiser; never `innerHTML` with raw input.

## 8. Hosting, headers and origins

- HTTPS only in production (plain HTTP is allowed on the test server). **[Official]**
- Since Bot API 10.2 Mini App methods are refused when called from an origin other than the app's own;
  enabled for all apps on 2026-07-20, switchable off in @BotFather (then you own the risk of untrusted
  sites using your app). Keep one origin; do not frame other sites that call `Telegram.WebApp`. **[API]**
- Content-Security-Policy **[Heuristic, verify in Telegram Web]**:
  `script-src 'self' https://telegram.org; frame-ancestors 'self' https://web.telegram.org;
  connect-src 'self' https://api.example.com`. Do not send `X-Frame-Options: DENY`: Telegram Web embeds the
  app in an iframe (Serverless docs **[Official]**).
- `telegram-web-app.js` is changed by Telegram in place, so a Subresource Integrity hash would break the
  app on the next update; pin the host with CSP instead. **[Heuristic]**
- CORS: allow only your own front-end origin; `downloadFile` additionally needs
  `Access-Control-Allow-Origin: https://web.telegram.org` on the file response. **[Official]**

## 9. Telegram Serverless

On Telegram Serverless the platform validates `initData` before an endpoint runs and rejects bad calls with
`UNAUTHORIZED`; the endpoint receives the verified data in its context. **[Official]** Still authorise each
action against that user and validate the endpoint input like any request.

## 10. Logging and errors

- Log the verified `user.id`, the route and the outcome; never the raw `initData` (it contains the
  signature and personal fields), never the token. **[Heuristic]**
- A failed check returns a generic `401` with no detail about which step failed. **[Heuristic]**

## 11. Checklist

- [ ] Every API route verifies `initData` (HMAC or Ed25519) and `auth_date` before reading the body.
- [ ] Duplicate keys and missing fields are rejected; comparison is constant time.
- [ ] The bot token is only on the server; `scripts/miniapp_lint.py` finds no token pattern in client code.
- [ ] No server code reads `initDataUnsafe`; no decision uses `platform` or `colorScheme`.
- [ ] `start_param`, `web_app_data` and every body field are allowlist-parsed.
- [ ] Prices are computed on the server; orders are paid only after `successful_payment`.
- [ ] Tokens live in memory or `SecureStorage`, never `localStorage`.
- [ ] One origin; CSP allows `telegram.org` scripts and Telegram Web framing.
- [ ] Logs carry user ids, not `initData`.
