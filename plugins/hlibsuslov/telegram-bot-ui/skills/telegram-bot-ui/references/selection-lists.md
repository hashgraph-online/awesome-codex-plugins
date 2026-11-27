---
summary: "Choosing one or many options from a list in a bot: surface by option count, 2-column grid, native selection marks, summary, paging, inline search, Rich checkbox list, Mini App past ~30."
verified: "2026-11-26"
bot_api: "10.5"
---

# Choosing from a list: categories, filters, topics, tags

A screen where the user picks one or several options out of many: categories to study, filters, topics to
follow, tags. Facts are **[API]** (checked in the offline catalog, Bot API 10.5); the layout rules are this
skill's **[Heuristic]**. Runnable example: `examples/python/pick_categories.py` (both variants below, validated
in `tests/test_selection_lists.py`). Keyboard basics: [inline-keyboards.md](inline-keyboards.md); search
and paging at scale: [recipe 63](../recipes/63-search-and-long-lists.md).

## Contents

- [1. What a bad picker looks like](#1-what-a-bad-picker-looks-like)
- [2. Pick the surface by the number of options](#2-pick-the-surface-by-the-number-of-options)
- [3. The inline picker, strictly](#3-the-inline-picker-strictly)
- [4. The Rich Message picker](#4-the-rich-message-picker)
- [5. Past ~30 options: search or a Mini App](#5-past-30-options-search-or-a-mini-app)
- [6. Checks](#6-checks)

## 1. What a bad picker looks like

Eleven full-width rows, each `⚪ Delineator/marker signs · 17` or `✅ Mandatory signs · 11`, English names in a
Ukrainian interface, a green `🏁 Готово` at the bottom, and a message that says "✓ — у навчанні" instead of how
many are chosen. Every part is fixable:

| Tell | Why it is wrong | Do instead |
|---|---|---|
| ⚪ / ✅ / 🔘 / 🟢 as the checkbox | colour-emoji noise; the state reads as decoration; two different pictures for one control | a `✓` text mark before the chosen label, or a **static** custom emoji check from the bot's own family (`icon_custom_emoji_id`), the label plain |
| one option per row, 10+ rows | the list scrolls past the message; the eye reads a column of identical bars | two per row (three for very short tokens), short names, at most 8 rows per screen |
| names in another language | the user cannot recognise the option | the bot's own localised short names; the long official name in the detail or the message |
| "Усі категорії · 282" as a row of the list | a bulk action dressed as an option | Select all / Clear as one button that flips, beside Done |
| `🏁 Готово`, `✅ Done` | decoration on a control | the word, `style: "primary"`, and the outcome: `Готово · 3` |
| no summary | the user counts ticks | one line in the message: `Обрано 3 з 10 · 68 знаків` |

## 2. Pick the surface by the number of options

| Options | Single choice | Several at once |
|---|---|---|
| 2-6 | inline buttons, one row or 2-3 per row; the tap **is** the choice (no Done) | inline grid, 2 per row, ✓ marks, Done |
| 7-16 | inline grid 2 per row, one screen | inline grid 2 per row + Select all / Clear + Done; or the Rich Message picker (§4) when each option needs a line of explanation |
| 17-30 | inline grid with pages of 8 (`‹ Previous · 1/3 · Next ›`) | the same, the summary in the message counts across pages |
| > 30, or several filters at once, or the user types to find | inline search (`switch_inline_query_current_chat`) for one item; a **Mini App** picker for many items or combined filters | Mini App (search field, sections, chips, a MainButton "Show 68 signs") |
| typed often, a fixed short set | reply keyboard (it stays under the input field) | not for multi-select |

Never: a poll as a picker (polls are for opinions and quizzes), `sendChecklist` (it is **business-account only**
**[API]**: a bot's own chat cannot send a tickable checklist), a new message per tap.

## 3. The inline picker, strictly

```
<b>Категорії для навчання</b>
Обрано 3 з 9 · 68 знаків
Торкніться категорії, щоб додати її до навчання або прибрати.

[ ✓ Наказові · 11 ] [ Заборонні · 48 ]
[ Попереджувальні · 47 ] [ ✓ Сервісу · 23 ]
[ ‹ Попередні ] [ 1/2 ] [ Наступні › ]      only with more than 8 options
[ Очистити ] [ Готово · 3 ]                 Done is the only primary button
[ ← Назад ]
```

- **Layout:** two options per row; labels ≤ 24 characters in the longest locale (`Name · count`); at most 8 rows
  in the keyboard; navigation (Back) last. Options in a stable order (the bot's, or by count), never re-sorted
  by selection.
- **State:** the chosen option starts with `✓ ` (U+2713, a text mark), or carries a static custom emoji check
  of the bot's family through `icon_custom_emoji_id` with a plain label (custom emoji need an eligible bot:
  [custom-emoji.md](custom-emoji.md)). Never ⚪ ⚫ 🔘 ✅ ☑️ ❌ 🟢 🔴 ⬜. A button `style` is not a state: `primary`
  belongs to Done alone, `success` / `danger` are outcomes **[API]: style is primary, success or danger**.
- **Summary:** the message says how many are chosen and what that means (`Обрано 3 з 9 · 68 знаків`); with none
  chosen it says what to do ("Оберіть хоча б одну категорію") and Done is `disabled: {}` **[API, 10.3]**.
- **Bulk:** one button that flips between Select all and Clear; it sits beside Done, not in the list.
- **A tap** toggles one id on the server and edits the same message (`editMessageText` with the new keyboard, or
  `editMessageReplyMarkup` when the text is unchanged); answer every `callback_query` without a toast. The
  callback names the change (`cat:t:<id>`, `cat:all`, `cat:none`, `cat:p:<n>`, `cat:done`); the state is the
  server's, and an unknown id changes nothing.
- **Pages:** 8 options per page; the counter is a disabled button; the ends keep the row's shape with disabled
  buttons. Past 20 options add a search button (`switch_inline_query_current_chat: ""`) that lists matches as
  inline results.
- **Done** saves, edits the picker into a one-line result ("Навчання: 3 категорії · 68 знаків") with a way back
  to change it, and continues the flow. No `🏁`, no confetti.

## 4. The Rich Message picker

When each option deserves a line of its own (a description, a count, a status), or the choice belongs inside a
longer document, use a Rich Message (`sendRichMessage`, then `editMessageText` with `rich_message` on every tap
**[API]**):

- the options are a `list` block whose items have `has_checkbox: true` and `is_checked: true` for the chosen ones
  (`InputRichBlockListItem` **[API]**): Telegram draws real checkboxes, no emoji needed. They are display only:
  the user taps a button, not the box;
- each item's line ends with a quiet button in the text (`RichTextButton`, `style: "link"`, callback only
  **[API]**) that says the action: `Додати` / `Прибрати`;
- Select all / Clear and `Готово · 3` on the keyboard under the message (`reply_markup`), not as a row in the
  document: they act on the whole picker ([rich-message-buttons.md](rich-message-buttons.md)); Done takes
  `style: "primary"` there;
- a heading, then the summary in bold, then the list: the state is visible without counting.

Rich Messages need Bot API 10.3 clients; buttons with `web_app` work only in private chats **[API]**. The example
builds the payload as blocks so nothing is parsed from strings.

## 5. Past ~30 options: search or a Mini App

- **One item out of hundreds** (a city, a product, a sign): a search button with
  `switch_inline_query_current_chat` opens inline mode in the same chat; the results are the options
  ([inline-mode.md](inline-mode.md)). Not in channels **[API]**.
- **Many items or combined filters** (category + difficulty + status): a Mini App picker with a search field,
  sections and chips, the MainButton saying the outcome ("Показати 68 знаків"), and the result sent back to the
  chat ([mini-apps-bridge.md](mini-apps-bridge.md)).

## 6. Checks

`scripts/validate_keyboard.py` warns, without failing:

| Code | When |
|---|---|
| `SELECTION_EMOJI` | two or more labels start with a selection emoji (⚪ ✅ 🔘 🟢 ☑️ ⬜ …) |
| `LONG_COLUMN` | more than 6 consecutive one-button rows of short options |
| `DECORATED_CONTROL` | an emoji on Done, Apply, Save, Next, Back or Cancel (`🏁 Готово`); arrows on Back / Next pass |

Plus the general ones: more than 8 rows, more than one `primary`, a styled Back. For a bot-ui project,
`bot-ui validate` adds `ICON_MEANING_MISMATCH` when a button's custom emoji means something else than its label
([visual-language.md](visual-language.md)).
