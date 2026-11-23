# PlaceCall: Errors

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for every error status and code, and what to do about each.

JSON `{"detail":{...}}` with the HTTP status:
- `401` invalid key.
- `402` out of credits (see [When credits run out](credits.md#when-credits-run-out);
  never retry).
- `403` tier/entitlement not permitted.
- `409` `Idempotency-Key` conflict (see the idempotency key under [Connection](../SKILL.md#connection)). The
  concurrent-call limit does not refuse a call: extra calls wait with
  `status: "queued"` until one of yours finishes (raise it via
  `PUT /users/me/limits`).
- `422` validation (see `error_code` inside `detail`). `422 region_not_supported`
  means we do not call that country or state (`blocked_code` names it, e.g.
  `US-IN`): do not retry, tell the user.
- `429` rate limit (10 req/s, 120 req/min on free and paid keys) or daily call
  ceiling reached (distinguish by `detail.error`). The ceiling counts calls
  created per UTC day, depends on your tier, and resets at UTC midnight
  (`resets_at`).
- `503` maintenance window or transient refusal; retry later.

Codes inside `detail` (`error_code`, or `error` on some) not covered above or
by their own feature. None of them charges anything, and only the `502` may
have dialed:

| Status | Code | Meaning, what to do |
|---|---|---|
| 400 | `idempotency_key_invalid` | `Idempotency-Key` is not 1-255 characters |
| 403 | `freeform_disabled` | freeform calls are not enabled for this key: ask support to enable them |
| 403 | `account_suspended` | the account is suspended: stop, tell the user |
| 422 | `missing_target_phone`, `invalid_target_phone`, `missing_brief`, `scenario_brief_not_allowed` | fix the request (the `hint` says how) |
| 422 | `emergency_code_blocked`, `service_code_blocked`, `premium_rate_blocked`, `dial_control_syntax_blocked`, `region_not_supported`, `destination_unattributable`, `destination_unscannable`, `destination_blocked` | this number cannot be dialed as sent (`blocked_code`, `hint`): never retry it unchanged |
| 422 | `brief_policy_violation` | the pre-call check refused the brief: rewrite it |
| 422 | `brief_too_long` | the `brief` is over 4000 characters: shorten it |
| 422 | `too_many_items`, `item_too_long`, `items_invalid`, `items_duplicate`, `field_reserved` | `items` breaks a rule, or the body carries `output_schema`; `message` names the item and the rule ([Items](items.md)). Over MCP: `invalid_request` with the same `message` |
| 422 | `card_number_in_brief`, `request_text_uncheckable` | the request carries what looks like a payment card number (`field` says where), or could not be checked for one: remove it and resend. Never send a card number |
| 422 | `brief_incomplete` | the pre-dial read found a gap that blocks the call (`need` names it): add it and resend. Production only warns today, so you should not see it there |
| 422 | `field_removed` | the body sent `intent`, `slots`, `kind` or `skill`, removed on 2026-11-12. `removed_fields[].use_instead` is `brief` for `intent` and `slots` (state the whole task in the brief; the client's name goes in `disclosure.on_behalf_of`) and `null` for `kind` and `skill` (leave them out) |
| 410 | `endpoint_removed` | a removed endpoint: `POST /skills/{skill_id}/run`, `GET /skills`, `GET /skills/{skill_id}/manifest`, `GET /v1/booking/bookings[/{booking_id}]` (removed on 2026-11-12). `successor` names what to use: `POST /calls`, `GET /calls/{call_id}`, or `null` for the `/skills` reads |
| 422 | `ask_user_channel_required` | `ask_user_mode: "webhook"`, but the key has no webhook |
| 429 | `daily_call_ceiling_reached`, `global_daily_call_ceiling_reached` | daily ceiling: wait for `Retry-After` |
| 503 | `maintenance` | maintenance window: retry after `resume_at` |
| 503 | `brief_guard_unavailable`, `daily_call_ceiling_unavailable`, `dial_policy_unavailable` | a pre-call check could not run: retry shortly |
| 422 / 503 | `unsupported_mode` / `transport_error` (on `/answer`) | `mode: "context"` is refused, send a plain `answer` / retry the answer |
| 502 | `{"detail": "..."}` from the API, or `{"error": "backend error", "error_code": "BACKEND_ERROR"}` from the gateway | the call may have been placed: [check first](../SKILL.md#post-calls-failed-or-timed-out-the-call-may-still-have-been-placed) |

Blocked before it reaches the API is not an API error. A failure with no
JSON body and no HTTP status means the call never left the machine. That is
a sandbox or permission refusal, a refused or unresolvable connection (the
host was never reached), or an approval denial. Do not retry. Name which of the three
blocked it and give the fix; it is not a PlaceCall outage. (A timeout or a
connection that dropped after the request went out is the opposite case: the
call may have been placed. See
[`POST /calls` failed or timed out?](../SKILL.md#post-calls-failed-or-timed-out-the-call-may-still-have-been-placed).)

- Network refused / domain not allowed. Agent sandboxes allow no outbound
  hosts by default. On Claude Code the user adds `api.voygr.tech` to
  `sandbox.network.allowedDomains` in `~/.claude/settings.json`; on a managed
  machine an admin may have to, because `strictAllowlist` and
  `allowManagedDomainsOnly` block instead of prompting.
- Key missing and no shell to set it in (desktop apps never see your shell).
  The user puts `PLACECALL_API_KEY` in the `env` block of the same settings
  file.
- Refused for reading a credential file. Expected: never scan for `.env`
  files. Read only the one path the user names. With no key, sign the user up
  by [email code](sign-up.md) or send them to
  <https://api.voygr.tech/checkout>.
