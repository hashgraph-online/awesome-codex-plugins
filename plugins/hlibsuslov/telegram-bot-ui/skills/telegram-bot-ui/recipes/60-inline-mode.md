# 60 — Inline mode: share a place card into any chat, then let the chat vote on it

Product recipe (combines mechanisms; no registry row of its own). Uses inline results with
inline keyboards, `chosen_inline_result`, `editMessageText` by `inline_message_id`, 9.4 button
`style`. Verified 2026-11-15 against Bot API 10.4 (newest release on that date, 2026-11-09).
Inline-mode depth: `references/inline-mode.md` (inline stream); index of all product recipes:
`references/use-case-playbooks.md`.
Tags: **[API]** = API requirement, **[official]** = official recommendation, **[heuristic]** =
design heuristic of this skill.

1. **Request and visible result.** “Friends keep asking where to get coffee. Let me type
   `@placecards_bot coffee` in any chat, pick a place, and let everyone in the chat tap ‘I'm in’.”
   — Typing the bot name opens a list of place cards (three at a time, scrolling loads more);
   picking one posts a card with an **👍 I'm in** button. Every tap by any chat member updates
   the same card: the button shows the count (“👍 I'm in · 3 going”), the text lists who is
   going, a second tap by the same person removes their vote. An empty query shows popular
   places; a query with no match shows only a button that opens the bot.
2. **Why these features.**
   - Every article carries an **inline keyboard**: `ChosenInlineResult.inline_message_id` is
     present only if a keyboard is attached, and without it the sent message can never be
     edited **[API]**.
   - `is_personal: true` because titles are localized to the asker's `language_code`; the
     default lets the server cache one answer for everybody who types the same text **[API]**.
   - `next_offset` paging: the client sends the offset back with the same query text; `""`
     means no more pages, the value is at most 64 bytes, at most 50 results per answer **[API]**.
   - `button` with `start_parameter` above the results for the empty and the no-result state:
     a tap opens the bot's private chat with `/start <parameter>` (1-64 chars, `A-Z a-z 0-9 _ -`)
     **[API]**. The empty list is better than a fake “Nothing found” article, which people would
     send into a chat **[heuristic]**.
   - `style: "primary"` on the one action of the card (9.4) **[heuristic: one primary per
     message]**. The button label is the **same for every reader**: an inline message is one
     message for all, so a per-user “✓ You're in” label is impossible; the personal answer is
     the toast (`answerCallbackQuery`) **[heuristic]**.
   - Widgets are **not** available in production inline results (10.4), so the card is plain
     HTML text and buttons **[API, 10.4]**.
3. **Requirements.** Bot API ≥ 9.4 for `style` (everything else is older). Inline mode enabled
   in @BotFather (`/setinline`) and **inline feedback** enabled (`/setinlinefeedback`), otherwise
   no `chosen_inline_result` arrives **[official]**. `allowed_updates` must include
   `inline_query`, `chosen_inline_result` and `callback_query`. Works in any chat, including ones
   the bot is not a member of. Production.
4. **Payload.** Full request sequence: `examples/payloads/r60-inline-mode.json`. Incoming
   fixtures: `examples/fixtures/usecase_inline_query_empty.json`,
   `usecase_inline_query_text.json`, `usecase_inline_query_page2.json`,
   `usecase_inline_query_none.json`, `usecase_chosen_inline_result.json` (all in
   `examples/fixtures/`).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | empty query | 3 popular place articles | `Open the bot for more` (results button, `start_parameter`) | pick an article |
   | query “coffee”, page 1 | 3 articles, `next_offset: "3"` | per article: `👍 I'm in` primary · `Open in the bot` (url) | page 2, pick |
   | page 2 (`offset: "3"`) | 1 article, `next_offset: ""` | same | pick |
   | no match | `results: []` | `Nothing found: open the bot` (results button) | the bot's chat |
   | posted card | name, area, note, “Who is in? …” | `👍 I'm in` · `Open in the bot` | vote edits (below) |
   | card after votes | same + “Going (3): Alice, Богдан, Eve” | `👍 I'm in · 3 going` | toggle |

   Key parts:
   ```json
   {"method": "answerInlineQuery", "params": {"inline_query_id": "6000000000000960001",
     "is_personal": true, "cache_time": 60,
     "button": {"text": "Open the bot for more", "start_parameter": "search"},
     "results": [{"type": "article", "id": "kaffa", "title": "Kaffa Roasters",
       "description": "Podil · Filter coffee, oat milk",
       "input_message_content": {"message_text": "<b>Kaffa Roasters</b>\nPodil · …", "parse_mode": "HTML"},
       "reply_markup": {"inline_keyboard": [[{"text": "👍 I'm in", "callback_data": "pl:vote:kaffa", "style": "primary"}],
         [{"text": "Open in the bot", "url": "https://t.me/placecards_bot?start=place_kaffa"}]]}}, …],
     "next_offset": ""}}
   {"method": "editMessageText", "params": {"inline_message_id": "AQAAAKx2nwABCDEF",
     "text": "<b>Kaffa Roasters</b>\nPodil · Filter coffee, oat milk\n\nGoing (1): Alice", "parse_mode": "HTML",
     "reply_markup": {"inline_keyboard": [[{"text": "👍 I'm in · 1 going", "callback_data": "pl:vote:kaffa", "style": "primary"}], …]}}}
   ```
5. **Code.** `examples/python/recipes/r60_inline_mode.py` (`PlaceBot.on_inline_query`,
   `on_chosen`, `on_callback`) on top of `examples/python/tgkit/flows.py` (`pack`, `UpdateDedup`,
   `btn`, `kb`, `I18n`). It does not use `ScreenFlow`: an inline message has no `message`, no
   chat id and no single owner, and a per-render version would make a second voter's tap stale
   **[heuristic]**. TypeScript twin: `examples/ts/usecases/inline.ts` (replays this payload; `examples/ts/usecases/usecases.test.ts`).
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> typing: @bot query
     typing --> answered: inline_query -> answerInlineQuery (page 1)
     answered --> answered: scroll -> same query, offset "3"
     answered --> posted: user picks a card
     posted --> tracked: chosen_inline_result (state by inline_message_id)
     tracked --> tracked: callback (inline_message_id) -> toggle vote -> editMessageText
     tracked --> toast: unknown message / removed place -> answerCallbackQuery text
   ```
   State: `msgs[inline_message_id] = {item, lang, voters: {user_id: first_name}}`. The card's
   language is the author's (the message is shared); the toast is in the tapper's language.
   Voters live in a dict keyed by user id: one vote per user by construction, the second tap
   deletes the key. `chosen_inline_result` and callbacks are separate updates, so the state
   is created on the first and a redelivered one is ignored (`duplicate`), not reset.
   The callback data is `pl:vote:<place id>` (13 bytes): no screen version, because every
   member taps the same button.
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   @placecards_bot coffee                    @placecards_bot кава
   [ Kaffa Roasters — Podil · Filter … ]     [ Каффа Ростерс — Поділ · Фільтр-кава … ]
   [ Jam Espresso   — Centre · …       ]     [ Джем Еспресо   — Центр · …           ]
   [ Bean There     — Pechersk · …     ]     [ Бін Дер        — Печерськ · …        ]
   posted card                               posted card
   Kaffa Roasters                            Каффа Ростерс
   Podil · Filter coffee, oat milk           Поділ · Фільтр-кава, вівсяне молоко
   Going (3): Alice, Богдан, Eve             Йдуть (3): Alice, Богдан, Eve
   [ 👍 I'm in · 3 going ]                   [ 👍 Я йду · 3 ]
   [ Open in the bot ]                       [ Відкрити в боті ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: articles without an inline keyboard (then
   `inline_message_id` never arrives and the card is frozen); a “Nothing found” article that
   people post into the chat; `next_offset` forgotten (the list stops at the first page) or
   longer than 64 bytes; personalized results without `is_personal`; result ids over 64 bytes
   or repeated across pages; per-user button labels on a shared message; user names inserted
   into HTML unescaped (the run uses a voter called `Eve <script>` and the text shows
   `Eve &lt;script&gt;`). Limits **[API]**: ≤ 50 results per answer, result `id` 1-64 bytes,
   `next_offset` ≤ 64 bytes, `callback_data` ≤ 64 bytes, `start_parameter` 1-64 chars. Failure
   paths in the run: callback for an unknown inline message (bot restarted, state lost) →
   “no longer tracked” toast in the tapper's language; callback for a place that no longer
   exists → “out of date”; the same update delivered twice → counted once; a chosen result
   that is not ours or has no `inline_message_id` → ignored and logged. Alternative: for one
   private user, a normal bot chat with a catalog (recipe 63); for a poll, `sendPoll`.
9. **Run and verify.** `py -3 examples/python/recipes/r60_inline_mode.py` (10 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every markup including the inline
   results' keyboards, 64-byte callbacks, copy in en/uk, payload drift). Evidence: offline
   contract; a real `/setinlinefeedback` bot and real clients were not exercised.
10. **Adapt.** Keep: an inline keyboard on every article, `is_personal`, `next_offset` paging,
    the `button` for empty/no-result states, state keyed by `inline_message_id`, toast for
    expired state. Replace: `PLACES` with your search index (query it with the offset),
    the card text, the vote with your own action (RSVP, claim, “I'll take it”). Persist
    `msgs` in a database with a TTL: after a restart an in-memory map answers “no longer
    tracked”. Related: `references/inline-mode.md`, `recipes/04-shared-card-personal-panel.md`
    (personal replies to a shared card), `references/inline-keyboards.md`,
    `references/buttons-and-styles.md`.
