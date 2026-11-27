---
summary: "Buttons inside a Rich Message are the exception: only for a press that changes one element of the same message. Decision order, patterns, never-list, look, rework table, checks."
verified: "2026-11-27"
bot_api: "10.5"
---

# Buttons inside a Rich Message: the exception, not the default

`RichTextButton` (a button inside a sentence) and `<tg-button-row>` (`InputRichBlockButtons`, 1-8 buttons)
put buttons into the document itself. They are easy to overuse and often look worse than the keyboard. This
page decides where they belong. Facts are **[API]** / **[Official]** / **[News]**; the policy is this skill's
**[Heuristic, owner decision 2026-11-27]** and wins over any older advice in other pages.

## Contents

- [1. The rule](#1-the-rule)
- [2. What the platform says](#2-what-the-platform-says)
- [3. Why the keyboard is the default](#3-why-the-keyboard-is-the-default)
- [4. The decision, in order](#4-the-decision-in-order)
- [5. The six patterns that earn a button in the document](#5-the-six-patterns-that-earn-a-button-in-the-document)
- [6. Never in the document](#6-never-in-the-document)
- [7. How they look](#7-how-they-look)
- [8. After the press](#8-after-the-press)
- [9. Reworking an existing bot](#9-reworking-an-existing-bot)
- [10. Checks](#10-checks)

## 1. The rule

**Actions live in the inline keyboard under the message.** A button inside the document is allowed only when
the press **changes one specific part of this same message** (a step marked done, a section switched, an item
toggled, an answer revealed) and a keyboard would have to repeat that part's name to say which one, or when the
message **is the thing being answered or played** (a worksheet, a multi-question survey, a game board). Anything
else, including the message's main action, goes to the keyboard. When unsure: keyboard.

## 2. What the platform says

- **[API]** `RichMessageButton`: exactly one of url, callback_data, web_app, login_url, switch_inline_query*,
  copy_text, disabled; text is plain text, custom emoji or date-time only; `style` primary / success / danger
  or `link` (callback buttons only). A row holds 1-8 buttons and takes `align` left / center / right. A press of
  a callback button arrives as a normal `callback_query`; `answerCallbackQuery` answers it.
- **[API]** There is no method to edit one button: `editMessageText` with `rich_message` re-sends the whole
  document (up to 32,768 characters, 500 blocks). `editMessageReplyMarkup` edits only the keyboard under it.
- **[API]** `sendRichMessage` takes `reply_markup` too: a document can carry buttons and a keyboard.
- **[News]** Telegram announced them as making "any text interactive", with surveys, games, horoscopes, ordering
  and chess as examples: content the user plays with, not navigation.
- The docs state no purpose, no width or look of a row, and no look of an in-text button or of `style: link`.
  Treat the look as unknown until checked on iOS, Android and Desktop.

## 3. Why the keyboard is the default

| The keyboard | A button in the document |
|---|---|
| one known place for actions on every screen | a bubble in the middle of text: it interrupts reading |
| stays at the end of the message | scrolls away with its section in a long document |
| edited alone and cheaply (`editMessageReplyMarkup`) | every change re-renders the whole document |
| carries the accent (`style`) for the one forward action | filled styles inside text compete with the content |
| familiar on every client | its rendering is undocumented and differs by client |

So a button earns a place in the document only when position is the point: it must sit next to the one thing
it changes.

## 4. The decision, in order

Ask for every action. The first **yes** in questions 1-4 sends it to the keyboard.

1. Does it move to another screen or back (Back, Menu, Next page, Open list, Settings)? → **keyboard**.
2. Is it the message's main action or a commitment (Pay, Confirm, Approve, Book, Subscribe, Start, Submit,
   Delete, Roll back)? → **keyboard** with its `style`, or the MainButton in a Mini App.
3. Does it open something outside the chat (url, web_app, login, share, switch inline)? → a **text link**
   (`<a href>`) in the sentence for a reference; a **keyboard** button for a prominent "Open app" / "Open site".
4. Is it about the whole message rather than one element of it? → **keyboard**.
5. Does the press change this very message, or answer about this one element in place (a short toast), rather
   than send a new message or open a screen? No → **keyboard**.
6. Would a keyboard need the element's name to say which one ("Mark step 3 done", "Remove Flat white"), or more
   than about six such buttons? No → **keyboard**. Yes → **in the document**, as one of the patterns in §5.

Then choose the form: inside the sentence (`RichTextButton`, `style: "link"`) for a quiet per-line action; a row
right under the element for a choice among two to four options.

## 5. The six patterns that earn a button in the document

| Pattern | Example | Form |
|---|---|---|
| **Toggle an element** | a checklist step: "Rotate the signing key · Done"; include or exclude an item in a list | in-text `style: "link"` button after the element; after the press the line shows the new state and "Undo" |
| **Switch the view of one block** | Week / Month above a compact table; Staging / Production above a status table | a row of 2-4 options right above the block, the current one `disabled` |
| **Answer inside the content** | a worksheet of five questions, a survey with several questions, a game board | a row of options under each question; after the answer the row becomes the result text |
| **Expand one section on demand** | "Show all 24 rows" of one table when the full text is fetched or computed | an in-text link button; when the content is already known, use `<blockquote expandable>` instead: no button, no round trip |
| **Copy one exact value** | a promo code, an address, a command that must be copied exactly | a `copy_text` button next to the value, only when `<code>` (tap to copy) does not fit it |
| **Explain one element** | "Why this price?" after a total, "?" after a term | an in-text `style: "link"` callback; the answer is a toast (`answerCallbackQuery` text), the message stays as it is |

One message rarely needs more than one pattern. More than about eight buttons, or twenty per-line links, in a
document: a keyboard picker with pages, inline search, or a Mini App ([selection-lists.md](selection-lists.md)).

## 6. Never in the document

| Action | Where instead |
|---|---|
| Back, Menu, pages, "← List", "Open settings" | the keyboard |
| the main action or a commitment (Pay, Approve, Start quiz, Confirm, Subscribe, Roll back) | the keyboard, `style` by meaning; MainButton in a Mini App |
| a url to read more, a source, a runbook | `<a href>` in the sentence; a keyboard url button only when it is the call to action |
| Open app (`web_app`), login, share / switch inline | the keyboard |
| a destructive action | the keyboard, with a confirmation step |
| anything that is also on the keyboard | one place only (`RICH_BUTTON_ON_KEYBOARD`) |
| a button whose press sends a new message or opens another screen | the keyboard |
| decorative emoji on a label, an animated custom emoji | plain words; a static custom emoji from the bot's family, on every button of that row or none |

## 7. How they look

- In a sentence: `style: "link"` (callback only) so it reads as a link, one or two words ("Done", "Undo",
  "Details").
- In a row: two to four buttons (the API allows 8; more turns into a strip of slivers), `align` matching the
  text (left), placed right under or above the element it acts on, never as a footer of the document.
- No filled styles (`primary`, `success`, `danger`) inside the document: the keyboard carries the accent. A
  chosen option is shown as `disabled` or as text, not as a coloured button.
- Labels: the verb or the option itself, the user's language, no emoji decoration ([visual-language.md](visual-language.md)).
- Check the look on iOS, Android and Desktop before shipping a pattern: the docs do not describe it.

## 8. After the press

- Answer every callback (`answerCallbackQuery`), with a toast only when it adds information.
- Re-render the whole document with `editMessageText(rich_message=...)`; keep the keyboard as it was (repeat
  `reply_markup`) unless the press changed it.
- Replace the pressed control with its result: "✓ Done · Undo", the chosen answer with the explanation, the new
  view with its switch. Never leave a button that does nothing.
- Make handlers idempotent and treat a press on an old copy as stale; check state and rights on the server for
  every press (`disabled` is presentation).
- In groups and channels a press edits the message for everyone: use document buttons there only for shared
  state (a tally, a shared checklist); a personal answer goes to `answerCallbackQuery` or an ephemeral reply.
- Long documents: re-rendering 30,000 characters per tap is slow and costly; split the interactive part into
  its own short message.

## 9. Reworking an existing bot

| Found | Rework |
|---|---|
| "Approve" / "Pay" / "Start quiz" as a button row at the end of the document | keyboard button with `style`; after the press a disabled status or a new screen |
| "Runbook", "Read more", "Ask the owner" as url buttons in the text | `<a href>` in the sentence |
| "← List", "Menu", "Next" inside the document | keyboard |
| the same action in the document and on the keyboard | keep the keyboard one, unless it is a per-element action |
| a column of filled buttons between sections | keyboard, or a picker ([selection-lists.md](selection-lists.md)) |
| one button per list item, each with the item's name, on the keyboard (`Done: Rotate key`, `Done: Update CI`) | an in-text "Done" link after each item: the one place document buttons win |

Reference examples: [recipe 02](../recipes/02-interactive-document.md) (checklist steps toggled in place, a
view switch over the table, Approve on the keyboard), `examples/python/pick_categories.py` (Rich variant:
per-line toggles, Done on the keyboard).

## 10. Checks

`bot-ui validate` and `scripts/validate_rich.py` (also the MCP `check_rich_html`) warn:

| Code | Finds |
|---|---|
| `RICH_BUTTON_NAVIGATION` | a document button that goes back or to another screen |
| `RICH_BUTTON_MAIN_ACTION` | a filled style (`primary`, `success`, `danger`) on a document button: the main action belongs on the keyboard |
| `RICH_BUTTON_OUTSIDE` | url, web_app, login or switch-inline buttons in the document: a text link or the keyboard |
| `RICH_BUTTON_DENSITY` | a row of more than four buttons, more than eight buttons, or more than twenty per-line `link` buttons in one document |
| `RICH_BUTTON_ON_KEYBOARD` | the same action in the document and on the keyboard (bot-ui) |

A clean report means the obvious misuses are gone; whether a per-element button beats the keyboard is still
the question in §4.
