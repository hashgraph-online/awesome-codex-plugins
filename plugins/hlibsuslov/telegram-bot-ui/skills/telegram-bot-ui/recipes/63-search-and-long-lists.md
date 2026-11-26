# 63 — Search and long lists: a job board with filters, paging, detail and compare

Product recipe (combines mechanisms; no registry row of its own). Uses `InlineKeyboardMarkup.force_reply`
(10.3), disabled buttons (10.3), compact Rich tables (10.3) and rich button rows, 9.4 button
`style`. Verified 2026-11-15 against Bot API 10.4 (newest release on that date, 2026-11-09).
Index of all product recipes: `references/use-case-playbooks.md`.
Tags: **[API]** = API requirement, **[official]** = official recommendation, **[heuristic]** =
design heuristic of this skill.

1. **Request and visible result.** “Our job board has hundreds of vacancies. Let people search
   by typing, narrow by Remote / Junior / Senior, page through results, open one, and come
   back to the same place.” — Home shows recent searches and *New search* (reply field
   already open). Results show 5 jobs per page with number buttons, a pager
   `← 2/3 →`, *Filters (n)* and *Compare* (one Rich message with a compact table). An empty
   result says why and offers *Remove filter: Remote* in one tap; more than 200 results asks
   to narrow down, showing the top 5 and facet buttons with counts; a vacancy opens as a card
   with *Open vacancy* and *← Back* to the very same page.
2. **Why these features.**
   - `force_reply` on the inline keyboard (10.3): the query prompt shows the reply field and a
     *Back* button together; always a **new** message because the flag cannot be changed by an
     edit **[API]**.
   - Pager with **disabled** `←` / `→` at the ends and a disabled counter button (10.3): the
     row keeps its shape and the end of the list is visible **[heuristic]**.
   - `style: "primary"` on one button per screen: *New search* on home, *Apply · n* on the
     filters screen, the first helpful *Remove filter* on an empty result (9.4)
     **[heuristic]**. A filter toggle shows its state with a leading `✓`: a style is not a
     state **[heuristic]**.
   - *Compare* is a Rich Message with an `is_compact` table (10.3) and a button row
     (`InputRichBlockButtons`, 1-8 buttons): a comparison, not a list **[heuristic]**. Plain
     rich text is not HTML: titles are inserted as they are, only clipped.
   - The query text stays on the server: `callback_data` is 1-64 **bytes**, Cyrillic is two
     bytes per letter **[API]**; the callbacks carry an id (`sr:<ver>:recent:q2`).
3. **Requirements.** Bot API ≥ 10.3 for force_reply keyboards, disabled buttons, compact
   tables. Production. Private chat with the bot. The catalog comes from your search backend;
   the recipe reads `examples/fixtures/usecase_search_jobs.json` and generates filler jobs for
   the “too many” case.
4. **Payload.** Full request sequence: `examples/payloads/r63-search-lists.json`. Incoming
   fixture (the catalog the search runs over): `examples/fixtures/usecase_search_jobs.json`.

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | home | “Job search …” | one row per recent query (`🕘 …`) · `New search` primary | ask, results |
   | ask | “What are you looking for?” + reply field | `← Back` + force_reply | results (new message) |
   | results | `«q» · n jobs · page p/N`, filters line, 5 items | number buttons 1-5 · `← 2/3 →` · `Filters (n)` `Compare` · `New search` | detail, page, filters, compare |
   | results, empty | “Nothing for «q»” + why | `Remove filter: Remote` primary (only filters whose removal helps) · `New search` | results |
   | results, > 200 | “Too many to browse”, top 5 | `Remote (116)` `Junior (78)` `Senior (76)` · `New search` | results (filtered) |
   | filters | “Pick what to keep” | `✓ Remote` · `Junior` · `Senior` · `Apply · n` primary (disabled at 0) `Reset` | results |
   | detail | title, company, city, level, salary, summary | `Open vacancy` (url) · `← Back` | results (same page) |
   | compare | rich: heading, compact table | `← List` (rich button) | results (same page) |

   Key parts:
   ```json
   {"method": "sendRichMessage", "params": {"chat_id": 111111111, "rich_message": {"blocks": [
     {"type": "heading", "size": 2, "text": "Compare · page 1/1"},
     {"type": "table", "is_compact": true, "is_bordered": true, "cells": [[{"text": "Job", "is_header": true, …}, …],
       [{"text": "Senior Backend Engineer, Payments &…", …}, {"text": "Warsaw", …}, {"text": "Senior", …}, {"text": "€6-8k", …}]]},
     {"type": "buttons", "buttons": [{"text": "← List", "callback_data": "sr:d:back"}], "align": "left"}]}}}
   {"method": "sendMessage", "params": {"chat_id": 111111111, "parse_mode": "HTML",
     "text": "<b>«support» · 231 jobs</b>\nToo many to browse. Narrow it down; the top 5 for now:\n\n1. <b>Support Specialist (night shift)</b>\n    Lviv · Junior · remote …",
     "reply_markup": {"inline_keyboard": [[{"text": "Remote (116)", "callback_data": "sr:q:facet:remote"}], …]}}}
   ```
5. **Code.** `examples/python/recipes/r63_search_lists.py` (`JobBoard.search`, screens `results`,
   `filters`, `detail`, `compare`, actions `page`, `open`, `unfilter`, `facet`) on top of
   `examples/python/tgkit/flows.py` (`ScreenFlow` with its back stack, `paginate`, `pager_row`,
   `btn`, `kb`, `b36`, `I18n`) and `examples/python/tgkit/rich.py` (`table`, `button_row`,
   `rich_button`). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> home: /start
     home --> ask: New search (new message, force_reply)
     home --> results: recent query
     ask --> ask: invalid text (error on the same step)
     ask --> results: valid query (stored server-side, id in callbacks)
     results --> results: page n (snapshot must match) / facet / remove filter
     results --> filters: Filters
     filters --> results: Apply (page 0)
     results --> detail: job n
     detail --> results: Back (same page, same filters)
     results --> compare: Compare
     compare --> results: ← List
   ```
   State per user: `q` (query id), `filters` (a set, kept across searches), `recent` (3 ids),
   plus the screen's `page` in `ScreenFlow` args. `ScreenFlow` pushes `(results, {page})` on
   its back stack when opening the detail, so **Back** restores page and filters without
   any extra code. The catalog has a **snapshot version**: page buttons carry it
   (`sr:<screen ver>:page:<n>:<snapshot>`). A tap with an older snapshot answers “The list was
   updated”, re-renders from the new data and clamps the page; a tap on a job that has
   disappeared answers “no longer available” and re-renders. Over `MAX_BROWSE = 200`
   results there is no pager: top 5 and facet buttons whose labels show the count after
   applying them.
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   «engineer» · 12 jobs · page 2/3           «інженер» · вакансій: 2 · сторінка 1/1
   6. Staff Engineer, Search & Ranking <Core> Pla…   1. Інженер даних (Python, Airflow)
       Berlin · Senior · remote                  Київ · Middle · віддалено
   7. DevOps Engineer                        2. Інженер з автоматизації тестування
       Kraków · Middle · remote                  Львів · Junior
   [6][7][8][9][10]                          [1][2]
   [ ← ] [ 2/3 ] [ → ]                       [ Фільтри ] [ Порівняти ]
   [ Filters ] [ Compare ]               [ Новий пошук ]
   [ New search ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: the query in `callback_data` (a Cyrillic
   query overflows 64 bytes and the whole keyboard is rejected); a page button that silently
   shows different jobs after the data changed; Back that returns to page 1 or loses the
   filters; clipping after escaping (`&amp;` cut to `&am`) or inside a tag; hiding the pager
   instead of disabling its ends; paging through 5000 results; an empty result with only
   “Nothing found”; suggesting a filter whose removal still gives nothing; unvalidated query
   length. Limits **[API]**: `callback_data` ≤ 64 bytes, message text ≤ 4096 chars (5 jobs of
   ≈ 150 chars each stay far below), Rich table ≤ 20 columns, button row 1-8 buttons. Failure
   paths in the run: 100-character query → error on the same step; filters that empty the
   result → one-tap *Remove filter: Remote* (not Senior, which would not help); removed job →
   toast; old snapshot → refused and re-rendered; another user's tap on Alice's list → “belongs
   to someone else”; a stale render → “screen has changed”. Alternative: **inline mode**
   (`references/inline-mode.md`, recipe 60) when results are meant to be shared into a chat,
   or a Mini App for faceted search with many filters.
9. **Run and verify.** `py -3 examples/python/recipes/r63_search_lists.py` (11 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every keyboard and the compare
   table, 64-byte callbacks, copy in en/uk, payload drift). Evidence: offline contract.
10. **Adapt.** Keep: server-side query ids, snapshot version in page callbacks, `ScreenFlow`
    back stack with the page in args, disabled pager ends, “remove filter” suggestions computed
    from real counts, `MAX_BROWSE` guard, clip-then-escape. Replace: `search()` with your index
    (return ids plus a snapshot/etag from the backend), `FILTERS`, the job fields, the
    in-memory `queries` with a table keyed per user. For cursor-based backends replace page
    numbers by a cursor id stored server-side (callback `page:<cursor id>`). Related:
    `references/selection-lists.md` (multi-select pickers: grid, marks, Rich checkbox list),
   `recipes/20-shop.md` (catalog and cart), `recipes/24-settings.md` (toggle screens),
    `references/navigation-and-flows.md`, `references/tables.md#compact-tables`,
    `references/buttons-and-styles.md#disabled-buttons`.
