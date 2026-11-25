---
summary: "HTML widgets (Bot API 10.4): when to use them, availability, code and state, sending, query flow, shared widgets, runtime limits, design rules, testing; read first for any widget task."
verified: "2026-11-15"
bot_api: "10.4"
---

# HTML widgets (Bot API 10.4)

> Verified 2026-11-12 against the [Widgets guide](https://core.telegram.org/bots/widgets) and the
> Bot API pages for `sendWidget` … `editSharedWidgetData`. Status of each rule: **API** = Bot API
> requirement, **Guide** = official recommendation, **Heuristic** = this skill's design advice.

## Contents

- [Gallery, kit and tools (re-checked 2026-11-15)](#gallery-kit-and-tools-re-checked-2026-11-15)
- [When a widget is the right surface](#when-a-widget-is-the-right-surface)
- [Availability](#availability)
- [Code and state](#code-and-state)
- [Sending a widget](#sending-a-widget)
- [Query flow](#query-flow)
- [Changing state](#changing-state)
- [Shared widgets](#shared-widgets)
- [Groups, inline and forwards (test server)](#groups-inline-and-forwards-test-server)
- [Runtime limits (design for them)](#runtime-limits-design-for-them)
- [Design rules](#design-rules)
- [Testing](#testing)
- [Writing widgets with an LLM (Telegram's official prompt)](#writing-widgets-with-an-llm-telegrams-official-prompt)

A widget is **one self-contained HTML document drawn inside a message**: fixed code plus
state that only the bot writes. It runs in Telegram's QuickJS sandbox, **with no network**,
no keyboard input and no scrolling. It is a new UI surface — not a small Mini App and not a
web page. "A bot has no CSS" still holds for regular messages; widgets are the exception, and
only for their own bubble.

Recipes: [05 private widget](../recipes/05-private-widget.md) ·
[06 shared widget](../recipes/06-shared-widget.md) · [07 wallet](../recipes/07-wallet.md) ·
[50 dashboard](../recipes/50-monitoring-dashboard-widget.md) · [51 booking](../recipes/51-booking-widget.md) ·
[52 shop to checkout](../recipes/52-shop-card-to-checkout.md) · [53 shared quiz and leaderboard](../recipes/53-shared-quiz-leaderboard.md) ·
[54 job progress](../recipes/54-job-progress-widget.md) · [55 design a new widget](../recipes/55-design-a-widget.md).
Checker: `scripts/validate_widget.py` (`--strict` adds `scripts/widget_lint.py`).
Design: [widget-design-system.md](widget-design-system.md) · state and interaction:
[widget-patterns.md](widget-patterns.md).

## Gallery, kit and tools (re-checked 2026-11-15)

| Piece | Path | What it gives an agent |
|---|---|---|
| Kit | `examples/widgets/_kit/` (`tokens.css`, `runtime.js`, `i18n.js`, `chart.js`) | theme tokens and primitives, state with revisions, `K.ask` with every outcome, `K.sync`, `Intl` formatting, SVG sparkline/bars |
| Sources | `examples/widgets/src/*.html` | readable widgets with `<!--@kit …-->` / `/*@kit …*/` includes and `/*@lang xx*/…/*@end*/` string blocks |
| Built widgets | `examples/widgets/*.html` | minified, self-contained, English build; what `sendWidget` sends |
| Demo state | `examples/widgets/demo/*.json` | caption, fallback keyboard, named states, sample request data |
| Handlers | `examples/python/widget_gallery/h_*.py` + `core.py` | `decide()` per widget; owner check, stale revisions, answer once, coalesced shared edits |
| Build | `py -3 scripts/build_widget.py SRC --strict --lang ru --payload p.json` | inlines the kit, prunes unused kit CSS, minifies, measures zlib-9, fails on runtime gaps, writes a `sendWidget`/`sendSharedWidget` payload |
| Preview | `py -3 scripts/preview_widget.py SRC [--serve 8765]` | a **mock** runtime page: schemes, RTL, 200–600 px, states, places, bot failures, request log |

`py -3 scripts/build_widget.py --all --check` rebuilds the gallery, checks every language against
the 3800-byte working budget and fails if a committed build drifted from its source.

## When a widget is the right surface

| Need | Use | Why |
|---|---|---|
| Choose one of a few options, then go on | inline keyboard | cheapest, works everywhere, accessible |
| A card whose content changes in place (order, score, timer, poll bars) | **widget** | live state without re-sending; one bubble |
| Interaction that needs taps/drags on a custom layout (board game, slider, carousel) | **widget** | pointer events, canvas, CSS |
| Text input, forms, login, network data, anything > ~600 px tall | Mini App | widgets have no inputs, no network, clip at 600 px |
| Long readable document with tables | Rich Message | text-first, quotable, searchable |

Do not make widgets the default. Every widget needs a **text/button alternative** (caption +
inline keyboard or a command) because older apps show "unsupported media" with the caption,
and widgets have no accessibility semantics in profile 1 (Guide).

## Availability

| Where | Production (2026-11-12) | Test server |
|---|:-:|:-:|
| Private chat with the bot (requests, background requests, wallet) | **yes** | yes |
| Groups / supergroups (needs `can_send_other_messages`) | no | yes |
| Inline mode results (`InputWidgetMessageContent`, `InputSharedWidgetMessageContent`) | no | yes |
| Forwards of widget messages | no (production widgets are protected content) | yes |

Never present group/inline/forward scenarios as shippable to production users. Build and test
them on the [test server](https://core.telegram.org/bots/webapps#using-bots-in-the-test-environment)
(`/bot<token>/test/<method>`; `TELEGRAM_TEST_ENV=1` in `examples/python/tgkit/transport.py`).

## Code and state

| | `chat_data` (chat state) | `public_data` (shared state) |
|---|---|---|
| Audience | one message, its chat (all members in a group) | everyone who sees the widget, forwards included |
| In a forward | never | a frozen copy (static) / the live value (shared widget) |
| Size | ≤ 1024 **UTF-8 bytes** (512 Cyrillic letters) — API | same |
| Never put there | secrets, other users' data | secrets, anything personal |

* HTML is **immutable after sending** (API: no method replaces it). A new layout = a new widget.
  The caption can be edited (`editMessageCaption`).
* The widget can't write state; it asks the bot with `TelegramWidget.request(data)` (1–64 bytes).
* Keep the **authoritative state on the bot**, keyed by message (`chat_id:message_id`,
  `inline_message_id`) or `widget_id`. The query never carries the widget's state (Guide).
* Put a **revision** `r` in every state and answer; the widget ignores anything older (Guide: polls
  can deliver older shared state).

## Sending a widget

`sendWidget(chat_id, html, chat_data?, public_data?, caption?, allow_queries?, is_shared?, width?, height?, reply_markup?, …)`
returns a `Message` with `widget` (`Widget`: `id` for shared widgets, `html`, sizes, state).
Incoming messages and `ExternalReplyInfo` can carry `widget` too (a reply to a forwarded copy).

* `allow_queries: true` only if the widget talks to the bot; without it every request is refused.
* Size check is the server's algorithm: ≤ 32768 bytes of UTF-8 **and** ≤ 4096 bytes after
  **zlib level 9** (API + Guide). Count with Python's zlib (`validate_widget.py`); Node's zlib may
  differ by a few dozen bytes near the limit. No NUL characters.
* **Always send a caption** (chat list, notifications, search, accessibility, unsupported apps).
* `copyMessage` / `copyMessages` refuse widget messages (API) — re-send by `widget_id`.

## Query flow

```
user taps  ->  widget: request("ship:fast")         (one call per tap, one in flight: BUSY)
Telegram   ->  bot: Update.widget_query {id, from, chat, message_id, chat_instance, type, data, widget_id?}
bot        ->  check data + from against YOUR state  (data is untrusted, like callback_data)
bot        ->  editMessageWidgetData(...)            (only if state changes; commit after success)
bot        ->  answerWidgetQuery(id, data≤1024B)     (EXACTLY once, within 15 s, also on failure)
widget     <-  promise resolves {result} / rejects NOT_ALLOWED|BUSY|RATE_LIMITED|TIMEOUT|FAILED|INVALID_ANSWER
```

* **The answer does not change state** (API) — it is only for the widget that asked. Others see
  the change through `chatDataChanged` / `publicDataChanged` after an edit.
* `from` and `widget_id` are set by Telegram and can't be forged (Guide); key per-user actions on
  `(widget_id, from.id)`.
* Concurrency: reserve the query id before the first `await` and serialize read → decide →
  edit → commit per widget key; otherwise two in-flight queries both start from the same revision.
* Redelivered updates: remember answered query ids; a late answer fails with "query is too old"
  — the widget already showed `TIMEOUT`.
* Limits: 5 requests / 5 s per user and bot; background requests only for the original in the
  private chat, one on appear then ≤ 1 per 5 s (Guide).
* **Subscribe explicitly**: include `widget_query` and `shared_widget_query` in
  `allowed_updates` on every `getUpdates`/`setWebhook`. SDKs that predate 10.4 drop or never
  request them (`sdk-compatibility.md#update-delivery-and-new-update-types`).

Implementation: `examples/python/tgkit/widgets.py::handle_widget_query` (+ TS twin).

## Changing state

| Message | Chat state | Shared state |
|---|---|---|
| original (private / group) | `editMessageWidgetData(chat_id, message_id, chat_data)` | same call with `public_data`, or `editSharedWidgetData(widget_id)` |
| sent via the bot | `editMessageWidgetData(inline_message_id, …)` | `editSharedWidgetData(widget_id)` |
| forward | — | `editSharedWidgetData(widget_id)` |

Edits are silent (no "edited" mark). `message is not modified` = done. `editMessageWidgetData`
counts as a sent message against limits; a shared widget accepts ≤ 1 edit per second — coalesce
(`SharedWidgetWriter`). An omitted field stays, an empty string clears it (API).

## Shared widgets

Created by the first `sendWidget` with `is_shared: true`; read `message.widget.id`. Re-send with
`sendSharedWidget(widget_id, chat_data?, caption?)`. Code, size and `allow_queries` are fixed for
all copies; only `chat_data` is per message. It outlives its messages. Refresh period: 30 s by
default, `cache_time` 5–3600 in `editSharedWidgetData`; on-screen widgets get live public state
only after `TelegramWidget.watchPublicData()`.

## Groups, inline and forwards (test server)

* Groups: the bot needs `can_send_other_messages` (10.4 extended this right to widgets); chat state
  is shared by all members — render per user with `TelegramWidget.viewer.id`; requests on tap only.
* Inline: `answerInlineQuery` with `InputWidgetMessageContent` (each send = new shared widget, its id
  arrives only in later queries) or `InputSharedWidgetMessageContent` (an existing widget). Queries
  come with `inline_message_id`, `chat_instance`, `chat_type`. Previews take no taps.
* Forwards: no chat state ever; only shared widgets with `allow_queries` can ask, via
  `shared_widget_query` (`id`, `from`, `type`, `data`, `widget_id`): no chat or message.

## Runtime limits (design for them)

Bubble 200–600 px wide (phones ≈ 320–430), height 50–600 px, overflow is **clipped**. No `vh`,
no scrolling, no inputs, no hover reliance, no keyboard/touch/wheel events (pointer events +
`click`), vertical drags belong to the chat, `touch-action: pan-y|none` to claim horizontal
drags/holds, keep the leading 20 px free (back gesture). Palette via `--tg-theme-*` variables;
`prefers-color-scheme` follows the **chat** theme; test light/dark and outgoing bubbles. RTL:
`dir`, mirrored safe-area corner. The time badge sits over the bottom corner without a caption
below: pad with `env(safe-area-inset-bottom)` / `--tg-content-safe-area-corner-*`. 2000 nodes,
8 MB, 300 ms CPU/s, 16 "heavy" elements (blur/filter/opacity<1); field: one JS task over
~500 ms, a widget that redraws non-stop, and canvas on desktop clients also misbehave. A widget past a limit, or one
that crashes, is stopped with a "Widget stopped" badge and rebuilt when shown again; **after two
crashes in a row it stays stopped until the app restarts** (Guide). Storage: `localStorage` 4 KB per
message per device, never synced. Links only on a tap (`openLink` https ≤256 chars,
`openTelegramLink`). Full table: the Guide's "Limits".

## Design rules

Draw the first state synchronously from state; show "Sending…" and every error code; mute with
color, not opacity; `em` sizes, system fonts; render forwards as snapshots ("as of 19:40");
treat code and `public_data` as public; respect `prefers-reduced-motion`. Send numbers with
fractions as ready strings (field: clients showed `$NaN` or dropped the fraction). Games and
live apps on one shared widget (versioning by HTML hash, lost answers, move numbers, clock lag):
[widget-patterns.md §16](widget-patterns.md#16-games-and-live-apps-on-one-shared-widget-field-report). Heuristic: keep under
~560 px tall at 320 px width.

## Testing

Offline: `validate_widget.py --strict`, `build_widget.py --all --check`, `tests/test_widgets.py`,
`tests/test_widget_*.py`, and `preview_widget.py` — an extended version of the Guide's browser
stand-in (a browser is **not** a Telegram client — it renders things apps remove). Closest to a
client without a phone: Telegram's own harness in [widget-sandbox](https://github.com/TelegramMessenger/widget-sandbox)
(`corepack pnpm tsx packages/core/scripts/sandbox-node.ts widget.html --width 360`) runs the real
validator and renderer and prints what the profile removed, gesture claims and heavy-element
counts; it is the user's checkout, not part of this skill. Live: production
private chat; groups/inline/forwards on the test server; both color schemes, largest text, a
narrow phone, desktop with mouse, RTL, an old phone. Report which of these were actually done.

## Writing widgets with an LLM (Telegram's official prompt)

The Widgets guide ships an official system-prompt block for models that write widgets
("Writing widgets with an LLM", https://core.telegram.org/bots/widgets#writing-widgets-with-an-llm;
raw text: https://core.telegram.org/bots/widgets.md). When an agent writes widget HTML:

1. Load that block (fetch the `.md` page; don't rely on memory — it is versioned by profile).
2. Give the model the bot's contract: JSON shapes of `chat_data`, `public_data` and answers,
   the request `data` values, static vs `is_shared`, `allow_queries`; whether it must call
   `watchPublicData()` and keep the newest revision; what to show in a forward, a group
   (per `viewer.id`) and a preview.
3. Check the result: `scripts/validate_widget.py` (server size algorithm + profile gaps), then a
   real Telegram client. Notable "out" items an LLM tends to use: CDN libraries (Chart.js, D3 —
   nothing is fetched), `vh`, `input`, `:checked`, `color-mix()`, `text-shadow`, `clip-path`,
   `-webkit-line-clamp`, `navigator.clipboard`, element ids as globals, logical properties
   (`margin-inline-*`), SVG `clipPath`/`mask`/SMIL, canvas `getImageData`/shadows/compositing.
   The validator flags all of these; `--strict` adds `request` from `pointerdown`, state written
   with `innerHTML` and canvas arcs past 2π.

