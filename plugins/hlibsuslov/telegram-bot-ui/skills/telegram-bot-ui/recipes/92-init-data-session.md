# 92 — Verify initData on the server and keep a session

Product recipe (no registry row). Verified 2026-11-23 against the Mini Apps page (“Validating data received
via the Mini App”, “Validating data for Third-Party Use”). Reference: `references/mini-apps/security.md`.
Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Make sure only real Telegram users can place orders from our Mini App,
   and that nobody can post on someone else's behalf.” — Every API call carries `Authorization: tma
   <initData>`; the server answers 401 to a forged or stale string, posts the order confirmation into the
   chat once per `query_id`, and refuses a replay; a partner service verifies the same string without the
   bot token.
2. **Why these features.** `initData` is the only thing the client cannot forge **[official]**: HMAC with
   `secret = HMAC_SHA256("WebAppData", token)` over every field except `hash` (so `signature` stays in) for
   your server; Ed25519 over `"<bot_id>:WebAppData\n" + fields without hash and signature` for third parties
   (8.0) **[official]**. `auth_date` has no official lifetime; this skill uses ≤ 24 h for reading and ≤ 1 h to
   start money or rights sessions **[heuristic]**. `query_id` is answered once **[heuristic]**.
3. **Requirements.** Any Mini App launch with `initData` (keyboard-button and inline-mode launches send it
   empty **[official]**). Server: Python stdlib or Node `node:crypto`; no packages.
4. **Payload.** `examples/payloads/r92-init-data-session.json`: one `answerWebAppQuery` (the replay and the
   forged string produce none). Test vectors: `examples/mini-apps/server/vectors.json` (test token and
   test Ed25519 seed; RFC 8032 vectors).
5. **Code.** `examples/mini-apps/server/python/verify_init_data.py` (`verify_hmac`, `verify_ed25519`, stdlib
   Ed25519 verifier from RFC 8032) and `examples/mini-apps/server/ts/verifyInitData.ts` (`verifyHmac`,
   `verifyEd25519`, `fromAuthorization`); scenario `r90_99_mini_apps.py::r92`; bot side
   `bot_side.py::MiniAppBot.answer_query_once`. Client: the kit sends `tma.initData`
   (`references/mini-apps/security.md` §5 has the fetch wrapper).
6. **Sequence and state.**
   ```mermaid
   sequenceDiagram
     participant A as Mini App
     participant S as Your server
     participant T as Telegram
     A->>S: POST /orders  Authorization: tma <initData>
     S->>S: verify hash (or signature) + auth_date, duplicates rejected
     S->>T: answerWebAppQuery(query_id) once
     S-->>A: 200 (or 401 / 409 replay)
   ```
   Stored: answered `query_id`s; optionally a 15-60 min session token in memory or `SecureStorage`.
7. **Result.** `401 hash mismatch` for a changed `start_param`; `409 already answered` for a replay; the
   user sees one message “via @bot” in the chat.
8. **Typical mistake, limits, alternative.** Trusting `initDataUnsafe`; removing `signature` from the HMAC
   string; comparing with `==`; a parser that keeps the last duplicate key; tokens in the front-end; logging
   raw `initData`; using `platform` for decisions. Library alternative: `@tma.js/init-data`. Telegram
   Serverless validates `initData` for you **[official]**.
9. **Run and verify.** `py -3 -m unittest tests/test_init_data.py` (15 tests: vectors, tampering, expiry,
   order, padding, RFC 8032) · `node --test server/ts/verifyInitData.test.ts` in `examples/mini-apps` ·
   `py -3 examples/mini-apps/server/make_vectors.py --check`. Evidence: offline vectors (self-signed test
   key); not verified against a string signed by Telegram's production key.
10. **Adapt.** Keep: strict parsing, constant-time compare, the age policy, one answer per query. Replace:
    the environment variable for the token (never in code), your session store. Related:
    `references/mini-apps-bridge.md` (bot side), recipe 98 (sharing).
