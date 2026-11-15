# Widget patterns: state, data, interaction (Bot API 10.4)

> Checked 2026-11-15 against the [Widgets guide](https://core.telegram.org/bots/widgets) and the
> Bot API methods `sendWidget`, `sendSharedWidget`, `answerWidgetQuery`, `editMessageWidgetData`,
> `editSharedWidgetData`. Bot API 10.4 is the newest version on that date. **API** = Bot API
> requirement, **Guide** = Widgets guide, **Heuristic** = this skill's advice. Code:
> `examples/python/widget_gallery/` (handlers), `examples/widgets/_kit/runtime.js` (widget side),
> gallery `examples/widgets/*.html`. Design: `widget-design-system.md`. Basics: `widgets.md`.

## 1. Decision guide: widget, keyboard, Rich Message or Mini App

Ask in order; take the first "yes".

| # | Question | Surface | Why |
|---|---|---|---|
| 1 | Does it need typed text, files, login, network data at view time, or more than ~560 px? | **Mini App** (or the chat itself for text) | widgets have no inputs, no network, clip at 600 px (Guide) |
| 2 | Must it work in a **group, channel, inline or a forward** in production today? | **inline keyboard / Rich Message** | production widgets: private chat with the bot only (Guide, 2026-11-15) |
| 3 | Is it mostly text to read, quote, search or copy (a document, a table, a long answer)? | **Rich Message** | text-first, quotable, accessible |
| 4 | Is it "choose one of a few options, then move on"? | **inline keyboard** | cheapest, works everywhere, accessible |
| 5 | Does one card change **in place** many times (status, progress, counts), or need a custom layout or a chart, taps on a grid, a slider or a carousel? | **widget** | live state in one bubble, drawn in the chat theme |

A widget always ships with a caption and a keyboard/command alternative (Guide: unsupported
apps show the caption; widgets have no accessibility semantics).

## 2. State architecture

```
             authoritative record (bot DB)            the widget
             ───────────────────────────             ───────────
 send   ──►  {full record, owner, rev 0}  ──state──► draws from chat_data / public_data (≤1024 B)
 tap    ◄──  widget_query {from, data:"t:3@7"}   ◄── request(data ≤64 B) on a tap
 decide      check from + data against the record (never trust the widget's view)
 edit   ──►  editMessageWidgetData(state rev 8) ──push─► chatDataChanged → redraw
 commit      record = new (only after the edit went through)
 answer ──►  answerWidgetQuery({ok, s: state rev 8, r: 8}) ─► promise resolves → take(s) if newer
```

| Rule | Status |
|---|---|
| Only the bot writes state; the widget asks. The query **never carries the widget's state**: keep the authoritative record server-side, keyed by message (`chat_id:message_id`, `inline_message_id`) or `widget_id`. | API / Guide |
| `chat_data` and `public_data` are each ≤ 1024 **UTF-8 bytes**; put a *projection* there (what to draw), never the full record, owner ids, secrets or other users' data. | API / Guide |
| Answer `data` ≤ 1024 bytes. If the answer carries the new state, keep states ≤ ~900 bytes so `{"ok":true,"s":…,"r":n}` fits. | API / Heuristic |
| Put a revision `r` in every state and answer; the widget keeps the newest (`K.take`). Polls and pushes may arrive older than an answer. | Guide |
| `answerWidgetQuery` **does not change state**. Edit first, then answer with the new state for the asking widget; others get it through the push. | API / Guide |
| Commit after the edit: a failed edit (flood wait) must not consume the user's action. `message is not modified` counts as done. | Guide |
| An omitted field in an edit stays; an empty string clears it; the widget sees `null` for no state. | API / Guide |

### Per-user data vs public data

| Data | Where | Example |
|---|---|---|
| what this user sees in their chat | `chat_data` (private chat: only them) | their order, their settings |
| the same for everyone, wherever shown | `public_data` (shared widget: one for all copies) | poll counts, a leaderboard top 5, a price |
| this user's result in a shared widget | the **answer** to their request (+ `localStorage` to remember it on this device) | "your vote: Sushi", "your rank: 14" |
| per message of a shared widget | `chat_data` set at `sendSharedWidget` | the recipient's id, their language |

`localStorage` is per message per device, 4 KB, never synced, never sent to the bot (Guide):
only for this user's own conveniences ("voted", best score), inside `try`.

### Answer vs edit: which one carries the change

| Situation | Edit state? | Answer carries |
|---|---|---|
| the action changes what everyone/this message shows | yes, before the answer | `s` (new state) so the asker redraws at once |
| a lookup that changes nothing persistent (an agenda for a tapped day, a price quote) | **no** | the data itself (≤ 1024 B) — the "answer-only" pattern (`schedule-calendar`) |
| refused (not the owner, invalid data) | no | `{"ok":false,"err":"not_allowed"|"bad_request"}` |
| stale (the user acted on an old view) | no | `{"err":"stale","s":fresh}` — the widget redraws and asks the user to look again |
| the edit failed | no | `{"ok":false,"err":"failed"|"busy","r":old}` |

### Stale and duplicate queries

* **Duplicate**: Telegram may redeliver an update; remember answered query ids and skip the
  second one (the id is valid 15 s — API). `tgkit.widgets.handle_widget_query` does this.
* **Stale**: the widget appends the revision it drew to relative actions — `t:3@7` ("toggle task
  3 as I saw it at revision 7"). The handler refuses relative verbs (toggle, increment, pick by
  index, "next question") when `@7` is not the current revision and answers the fresh state.
  Absolute actions (`set:above:5.50`, `tg:sound:1`) are idempotent and need no revision
  (Heuristic; the gallery's `Spec.stale_verbs`).
* **Concurrent**: two queries for one widget must not both decide from the same revision:
  serialize read → decide → edit → commit per widget key, and in async code reserve the query id
  before the first `await` (Heuristic; see `examples/ts/tgkit.ts`).

### The 15-second window

Answer every query exactly once within 15 s, also on failure; after that the id is dead ("query
is too old") and the widget shows `TIMEOUT` (API / Guide). Do slow work **after** answering
("Export started"), then push progress with edits (Guide: "Do slow work after answering").
After a wallet `TIMEOUT` the payment may have gone out: never offer to pay again blindly (Guide).

### Optimistic UI with rollback

For cheap, reversible toggles (settings, checklist), flip the control at once, mark it pending,
and send the request in the same tap handler:

```js
b.onclick = function () {
  var was = S.on[k]; S.on[k] = !was; pending[k] = 1; draw();          // optimistic
  K.ask("tg:" + k + ":" + (was ? 0 : 1), {
    then: function (r) { delete pending[k]; if (!r.ok) S.on[k] = was; },   // the answer's s wins anyway
    fail: function () { delete pending[k]; S.on[k] = was; }                // TIMEOUT, RATE_LIMITED, ...
  });
};
```

Never be optimistic about money, bookings, votes or anything another user competes for: show
"Sending…" and draw the server's answer (Heuristic).

## 3. Requests from the widget

| Rule | Status |
|---|---|
| `request(data)` with 1–64 bytes; on a tap it must be called **synchronously** in the handler — not after `await`, a timer or a promise. One tap unlocks one call, shared with `openLink`, `openTelegramLink`, `copyText`. | Guide |
| One request in flight (`BUSY`); 5 per 5 s per user and bot (`RATE_LIMITED`). | Guide |
| Background requests: only the original in the private chat, one when it appears, then ≤ 1 per 5 s while visible. Use them to refresh (`K.sync("sync")` on start and on `activated`). | Guide |
| Show every outcome: "Sending…", the answer, and `NOT_ALLOWED`, `BUSY`, `RATE_LIMITED`, `TIMEOUT`, `FAILED`, `INVALID_ANSWER` (+ `REJECTED`, `BAD_REQUEST` for the wallet). | Guide |
| Data grammar `verb[:arg][@rev]`: short verbs, positional args, no JSON. Treat it as untrusted input like `callback_data`. | Heuristic / Guide |

## 4. Charts and data-viz without libraries

No library is bundled or fetched (Guide: Chart.js and D3 by CDN do not run). Draw with inline
SVG strings (`_kit/chart.js`: `K.spark`, `K.bars`, ~600 compressed bytes) or canvas 2D.

* **Budget**: ship ≤ 24 points per series in state (`[171,168,…]` ≈ 4 bytes a point); aggregate on
  the bot. Two series of 24 + four KPIs ≈ 350 bytes of `chat_data`.
* SVG: `viewBox` + `preserveAspectRatio="none"` + `vector-effect:non-scaling-stroke` scales to any
  bubble width; colours via `currentColor` and `var(--k-*)`; area fills with `fill-opacity`, not
  `opacity` (no heavy elements). `clipPath`, `mask`, `pattern`, `marker`, SMIL are out (Guide).
* Canvas: scale by `devicePixelRatio`, ≤ 4000 commands per task, 2048×2048 px in total; no
  `getImageData`, shadows or composite modes (Guide). Prefer SVG for static charts (DOM nodes
  count toward 2000; a 24-bar chart is 25 nodes).
* Label the extremes in text (`168–214 ms`) instead of axes; mark thresholds with
  `--k-bad`; the caption states the headline number.

## 5. Lists and pagination

Nothing scrolls (Guide). Show ≤ 5–7 rows at 320 px, then:

* **local paging**: all items are in the state; ‹ › or "Show all 9" re-renders locally (no request);
* **server paging**: the page index is a request (`pg:2`) whose answer carries the page
  (answer-only), or an edit when everyone should see the same page;
* **"+3 more" line** plus a fallback button that opens the full list in the chat or a Mini App.

Growing height: by default the top edge stays; a log that grows at the bottom calls
`TelegramWidget.setResizeAnchor('bottom')` behind `typeof … === 'function'` (Guide).

## 6. Forms and input constraints

There is no keyboard and no form control: `input`, `select`, `textarea` are removed (Guide).

| Need | Widget pattern |
|---|---|
| pick one | chips (`.ch`) / segmented row |
| pick many | chips with `.on`, sent as a bitmask (`r:4:5` = tags 1 and 3) |
| number | stepper − value + (absolute value sent), or a **horizontal** slider with `touch-action: pan-y` and a button alternative |
| date / time | day strip + slot grid; months with ‹ › |
| free text | a button that leaves to the chat (`openTelegramLink('https://t.me/<bot>?start=comment')`) or a Mini App |
| confirm a destructive step | two-tap in-widget confirm ("Tap again to cancel", resets after 3 s) — `confirm()` returns `false` in widgets (Guide) |

Vertical drags always belong to the chat: no vertical sliders, wheel pickers or drawing (Guide).
Handle `pointercancel` by undoing what `pointerdown` started (Guide).

## 7. Timers that survive re-render and re-creation

A widget can be destroyed and re-created at any time; only its state and Web Storage survive
(Guide). So:

* derive time from **state timestamps** (`start`, `eta`, `deadline` in Unix seconds), never from
  a counter: `elapsed = Date.now()/1000 - S.start`;
* one `setInterval(draw, 1000)` that redraws only the clock text; ≤ 64 live timers (Guide);
* off screen, timers fire at most once per second and animation frames stop (Guide) — fine for a
  clock; pause games on `deactivated`;
* the clock on the device can be wrong: show "~2 min" rather than seconds for server ETAs.

## 8. Images and icons within the budget

* `data:` images barely compress (Guide): a 1 KB PNG costs ~1 KB of the 4096. Allowed: PNG,
  JPEG, GIF, WebP as `data:` URLs (≤ 1024×1024 px); **not** `data:image/svg+xml` (Guide).
* Icons: inline `<svg><path>` with `stroke="currentColor"` (`.ic`), defined once in
  `<svg><symbol id>` + `<use href="#id">` when reused (Guide: `symbol`/`use` are in the profile).
* Product "photos": CSS gradients and SVG shapes; real photos belong in a photo message above
  the widget or in a Mini App.
* Emoji are free (text) but render per platform; prefer SVG for UI glyphs.

## 9. Wallet / TON actions (only what Telegram documents)

From the Widgets guide "Payments with the wallet" and `wallet-and-ton.md`:

1. Draw Pay only when `TelegramWidget.wallet` is not `null`.
2. On a tap: `request("pay:<order>", {wallet: true})`; the bot's query has `type.wallet_card`.
3. The bot answers a fresh TON Connect `sendTransaction` request (no `from`, amounts in nanotons as
   strings).
4. In the answer's handler (within 10 s) call `wallet.sendTransaction(tx, "paid:<order>")`; the bot
   then gets `type: sent_transaction` — a notification, not proof: check the chain, then push the
   state.
5. `REJECTED`, `BAD_REQUEST`, `TIMEOUT` are outcomes to show; after `TIMEOUT` keep Pay disabled
   until a sync says otherwise.

The gallery's `cart-checkout` hands payment to the bot's normal flow (invoice/wallet in the chat);
`examples/widgets/wallet-pay.html` and recipe 07 show the wallet calls.

## 10. Shared widgets at a glance

`sendWidget(is_shared, allow_queries)` once → read `widget.id` → `sendSharedWidget(widget_id,
chat_data, caption)` to each private chat (API). Counting: one record per `widget_id`, votes keyed
on `(widget_id, from.id)` (Guide). Writes coalesced to ≤ 1 per second (`SharedWidgetWriter`), the
voter gets the new state in the answer, everyone else through the refresh period (`cache_time`
5–3600 s, default 30 s) while their widget called `watchPublicData()` (Guide). Forwards and
inline results that ask are test-server only today.

## 11. Widget as the front end of a backend

A widget **cannot reach any service**: `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`,
`sendBeacon`, `Worker` throw `NetworkDisabledError`, nothing external loads, and the widget cannot
navigate (Guide "What a widget is", "JavaScript", checked 2026-11-15). The **bot server is the only
bridge**. Gallery widget `api-browser` + [recipe 56](../recipes/56-api-data-browser.md)
(`examples/python/widget_gallery/h_api_browser.py`: a mock REST backend, and `RestTicketsApi` to
copy for a real endpoint).

```
tap -> request("f:mine") -> widget_query -> handler -> REST/DB call (timeout <= 6 s)
                                              |            ok | fail: cached page, stale:1, msg
                                              v
                    editMessageWidgetData(view state, r+1) -> answerWidgetQuery({ok,s,r[,msg]})
backend webhook / job -> bot -> editMessageWidgetData (push) -> chatDataChanged in the open widget
```

| Concern | Rule | Status |
|---|---|---|
| Contract | Queries are commands, not URLs: `f:<filter>`, `pg:<n>`, `o:<id>`, `b`, `x:<id>:<action>`, `sync` (≤ 64 bytes). The handler maps them to endpoints; the widget never knows the API's shape. | API (64 B) / Heuristic |
| Projection | The state is the **view**: ≤ 5 rows of `[id, title, status, meta]` plus the open detail, ≤ ~900 bytes. Full records stay on the server. | API (1024 B) / Heuristic |
| Pagination, filtering | Through queries; the answer carries the new view (`s`). A lookup that does not change the view can be answer-only (≤ 1024 B). | API / Heuristic |
| Answer window | Call upstream with a timeout well inside 15 s (e.g. 6 s), then edit and answer. On timeout answer cached data marked `stale`, or `{err:"upstream", msg}` — never let the widget reach `TIMEOUT`. Slow jobs: answer "Started", push results later. | API (15 s) / Guide ("do slow work after answering") |
| Caching | Cache reads per (backend user, filter, page) for a short TTL (30 s); invalidate on writes; show "Cached data from 10:12" when stale. | Heuristic |
| Refresh cadence | Open widget: background `sync` on appear and on `activated` (private original, ≤ 1 per 5 s — Guide). Server side: push on real changes (webhooks), not on a timer; `editMessageWidgetData` counts as a sent message (Guide). Same-for-everyone data: a shared widget with `cache_time` instead of requests. | Guide |
| Auth | Telegram authenticates `from` (Guide: cannot be forged). Map `from.id` to the backend account on the server and call the API with the **bot's** credentials on the user's behalf. Never put API keys, tokens, sessions or backend ids in widget code, `chat_data` or `public_data`: code and state are readable by the user, and public state travels with forwards. | Guide / Heuristic |
| Authorization | Re-check every action against the backend (the ticket may be closed already: `{err:"conflict", msg}`); `data` is untrusted input. | Guide |
| Rate limits | Widget side: 5 requests per 5 s per user and bot, one in flight (Guide). Backend side: your API's limits — coalesce, cache, and answer `busy` rather than queue past 15 s. | Guide / Heuristic |
| States in the widget | sending (`K.busy` + "Sending…"), the error sentence from `msg`, a stale banner from `stale` + `at`, an empty-list sentence, disabled actions in copies that cannot ask. | Guide / Heuristic |

An answer that reports a failure keeps the envelope `{"ok":true,"err":…}` in the gallery core
(`tgkit.widgets.handle_widget_query` wraps decisions as `ok`); the kit treats **any `err`** as not done.

## 12. Widget vs Mini App hand-off

Keep the widget a **summary card** and open a Mini App for real network, uploads, long forms,
text input, routing, or anything taller than ~560 px.

* From the widget, on a tap: `TelegramWidget.openTelegramLink("https://t.me/<bot>?startapp=<param>")`
  opens the bot's main Mini App in the current chat; `startapp` reaches the app as `start_param` and
  `tgWebAppStartParam` (Mini Apps docs "Direct link Mini Apps", checked 2026-11-15). A named app:
  `https://t.me/<bot>/<app>?startapp=<param>`. URLs ≤ 256 characters, one link per tap (Guide).
* From the message: the inline keyboard under the widget can carry a `web_app` button
  (`sendWidget` accepts an `InlineKeyboardMarkup` in `reply_markup` — API).
* **What crosses the boundary**: only an opaque reference (`t_4104`, an order id) in `startapp`.
  The Mini App authenticates the user with its signed `initData` and loads everything from your
  backend. Never pass tokens, prices to trust or personal data in the link: it is visible and
  replayable.
* **Coming back**: the Mini App changes data in your backend, the backend tells the bot, the bot
  pushes the widget's state (`editMessageWidgetData`). The widget reflects; the Mini App edits.
* A Mini App opened by a direct link cannot send messages to the chat (Mini Apps docs): the widget
  is how the result stays visible in the conversation.

## 13. Where widgets can be sent, and channel-safe variants

Checked 2026-11-15 against the Widgets guide ("Where widgets live", "Availability") and `sendWidget`:

| Place | Production | Test server | Source |
|---|:-:|:-:|---|
| private chat with the bot | **yes** (protected content: cannot be forwarded) | yes | Guide; `sendWidget` description |
| groups / supergroups (`can_send_other_messages`) | no | yes | Guide |
| inline mode (any chat **except channels**) | no | yes | Guide |
| forwards by users, **channels included** | no | yes | Guide |
| **channels, posted by the bot directly or via the bot** | **no** | **no** | Guide: "Widgets cannot be posted in channels, directly or via the bot" |

A bot **cannot post a widget to a channel** in any environment today; a channel can only show a
user's forward (test server). `TelegramWidget.chatType` lists `channel` as a value (Guide), which
only matters for such forwards. Do not present channel widgets as available.

**Channel-safe variant path** — every gallery widget can degrade to this:

| Property | Channel-safe rule |
|---|---|
| state | `public_data` only; no `chat_data` (forwards never get it — Guide); no per-user fields |
| interaction | read-only by default; if live, a shared widget with `watchPublicData()` and a `cache_time`; votes keyed on `(widget_id, from.id)` via `shared_widget_query` |
| viewer | assume `viewer = null` and `chatType = null` (forwards — Guide); never personalize |
| caption | carries the **full meaning** (headline, numbers, call to action): notifications and the chat list show only it |
| snapshot | a static widget's forward is frozen: draw "as of 19:40" from a timestamp in the state |
| fallback | a Rich Message or text post with a URL/`startapp` button is the real channel content today |

The kit supports this already: `K.can()` is false without a viewer, every gallery widget draws a
read-only view from its data alone, and the demo captions mirror the main fact. If Telegram ever
allows channel widgets, expect to change: a send path for channels (refused today), a rights check
for channel admins, channel posting limits, and how queries from anonymous channel readers arrive.
Re-check the changelog and this table before building on it.
