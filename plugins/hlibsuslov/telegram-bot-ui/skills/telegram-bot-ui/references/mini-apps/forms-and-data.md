# Forms, the keyboard and the app's own server

This file covers how a Mini App asks for input and talks to its server:
- which fields to use, and which to skip because Telegram already knows the answer;
- how the on-screen keyboard behaves inside Telegram;
- validation, drafts and closing;
- loading, caching and errors;
- making sure an action happens once.

Read it before building any screen that takes input or calls a server, and when the app "feels broken" on a
slow network.

Labels:
- **[Official]** https://core.telegram.org/bots/webapps;
- **[API]** the member catalog (`scripts/webapp_lookup.py`);
- **[Heuristic]** this skill's rule;
- **[Device]** behaviour you must check on a phone, because clients differ.

Kit: `tma.api()` with `ApiError` and `idempotencyKey()`, `tma.hideKeyboard()`, `tma.closingConfirmation()`,
`tma.store()`, `tma.mainButton()` (progress while the handler runs); `.tma-field`, `.tma-input`,
`.tma-field__error`. Stand: the **Network** select (slow, flaky, offline, 500, 401) breaks the app's own
requests, and `--api mock.json` answers them. Related: [security.md](security.md) (verifying `initData`),
[launch-and-lifecycle.md](launch-and-lifecycle.md) (sending results to the chat),
[layout-rules.md](layout-rules.md) L15 (form layout), [accessibility-and-language.md](accessibility-and-language.md).

## 0. Ask less

Every field costs a tap, a keyboard and a chance to leave. Before adding one **[Heuristic]**:

| The app needs | Do not ask; use |
|---|---|
| Who the user is, their name, language, photo | the verified `initData` on the server (`user`) |
| The phone number | `requestContact()` (6.9): one native tap, and the number reaches the bot verified by Telegram |
| Permission to message them (receipts, reminders) | `requestWriteAccess()` (6.9) at the moment it helps (payments.md step 9) |
| Where they are | `LocationManager` (8.0) after a tap, or a city list ([haptics-and-device.md](haptics-and-device.md) §3) |
| A QR or a code on paper | `showScanQrPopup()` (6.4) |
| Card details | never: the invoice sheet collects them (lint MA25) |
| One choice of a few, yes / no, a rating | maybe no Mini App at all: an inline keyboard ([decide.md](decide.md)) |

Then ask only what the action needs now. Offer "add later" for the rest.

## 1. Fields

One column, a visible label above each field, related fields grouped in a section (layout L15). The label is
never only a placeholder: the placeholder disappears as soon as the user types (lint MA24).

Every field sets the keyboard and autofill attributes **[Heuristic]**:

| Data | Markup | Why |
|---|---|---|
| Name | `autocomplete="name"` (or `given-name`) `autocapitalize="words"` | autofill; capital letters |
| Email | `type="email" autocomplete="email" autocapitalize="off" spellcheck="false"` | the @ keyboard |
| Phone (only if `requestContact` does not fit) | `type="tel" autocomplete="tel"` | digits keyboard; autofill |
| Amount, price, quantity | `type="text" inputmode="decimal"` (or `numeric`) + parse with the locale | `type="number"` scrolls on wheel, drops leading zeros, rejects "12,5" in comma locales, and screen readers announce it as a spin button |
| One-time code | `inputmode="numeric" autocomplete="one-time-code" maxlength="6"` | iOS offers the code from SMS |
| Search | `type="search" enterkeyhint="search"` | the keyboard says Search; Escape clears |
| Date, time | `type="date"` / `type="time"` (the platform picker), or kit chips for the next days | native wheels and calendars, already localized |
| Address | `autocomplete="street-address"` … `postal-code`, `country-name` | autofill fills all of them |
| Long text (a review, a comment) | `<textarea>` with a counter only near the limit | — |
| Password, PIN | do not have one: Telegram already signed the user in (lint MA20). For step-up, use `BiometricManager` (haptics-and-device §4) | — |

**The Enter key.** Use `enterkeyhint="next"` on every field but the last, and `done`, `send` or `search` on the
last. Enter on a middle field moves focus to the next field. Enter on the last field runs the same action as
the MainButton. A form is never submitted by Enter on a middle field.

## 2. The keyboard inside Telegram

The keyboard is where Mini App forms break most often, and the behaviour differs by client **[Device]**:

- **iOS.** The keyboard usually slides over the WebView and the layout viewport does not shrink. Fixed
  elements at the bottom end up under the keyboard or jump above it.
- **Android.** The WebView usually resizes. `viewportChanged` fires and `viewportHeight` drops.
  `viewportStableHeight` changes once the keyboard settles.
- **Desktop and Web.** There is no on-screen keyboard. Enter and Tab matter instead (§1, accessibility §4).

Rules **[Heuristic]**:

1. **The focused field stays visible.** After `focus`, wait for the keyboard (about 300 ms, or the next
   `viewportChanged` with `isStateStable`), then `field.scrollIntoView({ block: 'center' })`. Do this only if
   the field is covered: check its rectangle against `visualViewport.height`.
2. **Nothing of your own is fixed to the bottom while typing.** The MainButton is native and Telegram places
   it. An own sticky bar, toast or cart badge at `bottom: 0` jumps or hides the field. Hide such elements on
   `focusin` and show them on `focusout` (lint MA07 already forbids an own bottom CTA).
3. **No autofocus when the screen opens.** The keyboard would cover half the app before the user has seen
   it, and in compact mode it covers all of it. Focus a field only when the user taps it, or right after
   they asked for it ("Add a comment"). Lint MA41 flags `autofocus`.
4. **Close the keyboard after submit:** `tma.hideKeyboard()` (9.1; it blurs the field on older clients). The
   result or the error must be visible, not hidden behind the keyboard.
5. **Do not size the layout from the viewport while the keyboard is open.** Use `--tg-viewport-stable-height`
   (lint MA06), never `100vh` and never `window.innerHeight` read at focus time.
6. **Vertical swipes.** On a long form, a drag that starts on a field may minimise the app. While a form
   has unsaved input, `disableVerticalSwipes()` (7.7) prevents that. Re-enable swipes when the form is done.
   The closing confirmation (§4) still guards the close button.

## 3. Validation

- **When:**
  - format errors on blur (leaving the field) or on submit, never on every keystroke;
  - a field that was wrong is re-checked as the user types, so the error disappears as soon as it is fixed;
  - availability (a username, a time slot) is checked on the server, debounced by 400 ms.
- **Where:** under the field in `.tma-field__error`, linked with `aria-describedby`, with `aria-invalid="true"`
  on the field. The text names the fix: write "Enter a date after today", not "Invalid date".
- **On submit with errors:**
  - focus the first wrong field;
  - announce the number of errors (accessibility §2.2);
  - play `tma.haptic.error()` once;
  - do not clear anything the user typed.
- **The MainButton:**
  - keep it active and show the errors on tap;
  - or make it inactive (`active: false`) **only** when the reason is visible on the screen ("Choose a time
    to continue").

  An inactive button with no visible reason looks broken (design-system §8).
- **The server validates again.** The client's checks are for the user's convenience. The server's checks are
  the real ones, and its rejection comes back as `ApiError` kind `rejected` with a `reason` (§6).

## 4. Drafts and closing

- **Unsaved input + close = lost work.**
  - Turn on `tma.closingConfirmation(true)` as soon as the form differs from what was saved, and off after
    a successful save. Telegram then asks before closing (6.2) **[Official]**.
  - Do not turn it on for a screen without input. A confirmation on every close is an annoyance.
- **Long forms keep a draft.**
  - Save it to `tma.store()` (CloudStorage, so it follows the user to another device), debounced by about
    1 s, under one key per form.
  - CloudStorage takes up to 1024 keys per user, values of up to 4096 characters, and keys of 1-128
    characters from `A-Z a-z 0-9 _ -` **[Official]**.
  - Restore the draft on open and say so ("Draft restored", with a way to discard it). Delete it after a
    successful submit.
- **Never put secrets in a draft:** codes, document numbers or anything payment-related (security §6).

## 5. Talking to the server: `tma.api()`

```ts
import { createTma, ApiError, idempotencyKey } from '../_kit/tma.ts';
const tma = createTma();

const slots = await tma.api<Slot[]>('/api/slots?day=2026-11-25');                 // GET, retried
const key = idempotencyKey();                                                     // one per tap
const booking = await tma.api<Booking>('/api/bookings', { body: { slotId }, idempotencyKey: key });
```

What it does, and why **[Heuristic]**:

- **Raw `initData` on every request** (`Authorization: tma <initData>`). The server verifies it (security §2)
  and never trusts `initDataUnsafe` (lint MA33).
- **A timeout** (10 s by default) aborts the request. Without one, a request on a dead mobile connection can
  hang for minutes with a spinner.
- **Retries only what is safe to repeat:**
  - a GET is retried twice, after 0.6 and 1.8 s;
  - a write is retried only with an idempotency key (§7);
  - 4xx and 401 are never retried.
- **Five kinds of failure** the screen can explain (§6), instead of one "Something went wrong".

### 5.1 Loading

| Situation | Show |
|---|---|
| The first load of a list or a screen | the skeleton of that screen at once (`.tma-skeleton`), never a full-screen spinner; `aria-busy` on the region |
| An action from the MainButton | the MainButton's own progress (the kit shows it while the handler runs); the screen stays as it is |
| An action from a row or a chip | that control's pending state (spinner in place of the chevron, `aria-disabled`) |
| Refreshing data already on screen | nothing, or a quiet indicator; never replace content with a skeleton |
| Anything under ~300 ms | nothing at all: a flash of skeleton looks worse than a short wait |

Call `tma.ready()` when the first useful screen is drawn. A skeleton counts as useful.

### 5.2 Cache and freshness

- **Draw what you have, then refresh.**
  - Keep the last answer for each list in memory, and in `DeviceStorage` (9.0) if it is not sensitive.
  - Show it instantly on the next open and refresh in the background (stale-while-revalidate).
  - Prices, stock and order states are always revalidated before an action (security §6).
- **Refresh when the user comes back.** On `activated` (the app returns from the background), reload what can
  change: the order list, the balance, the queue.
- **Optimistic updates only for cheap, reversible actions:** a like, a favourite, a toggle, reordering a list.
  Update the screen at once, send the request, and roll back with a short message if it fails. Never for
  money, bookings, sending messages or anything the server can refuse for stock or rights. Those wait for the
  server (MA27 for payments).

### 5.3 Lists that grow

- Load pages of 20-50 with a cursor from the server, not an offset (items change while the user scrolls).
- Load the next page when the last few rows come into view (`IntersectionObserver`), with a "Show more" button
  as the fallback and for screen readers.
- Keep the scroll position when the user opens an item and comes back (BackButton).
- The end of the list is stated ("That's all orders"), not just a stop.

## 6. Errors: what to say and what to do

| `ApiError.kind` | Means | Screen **[Heuristic]** | Keep | Haptic |
|---|---|---|---|---|
| `offline` | nothing reached the server | "No connection. Nothing was sent." + Retry | everything typed | `error` once, only after a user action |
| `timeout` | no answer in time; the server may or may not have done it | "This is taking too long." + Retry (safe with the same idempotency key) | everything typed | `error` |
| `rejected` | the server said no (4xx): sold out, slot taken, invalid input | the server's `reason`, next to the field or the item it concerns; offer the nearest alternative | everything typed | `error` or `warning` |
| `server` | the server failed (5xx) | "Couldn't save. Nothing was charged. Try again in a minute." | everything typed | `error` |
| `session` | `initData` too old or refused (401/403) | "This page is out of date. Close it and open it again from the chat." + a button that calls `close()` | the draft (§4) | `error` |

Rules:

- **Name the consequence:** "Nothing was charged", "Your booking is not confirmed yet". Users fear double
  charges more than errors.
- **Never blame the user's connection** when the server failed. Never show a status code, a stack trace or
  "Error: undefined".
- **A list that failed to load** shows the error state in place of the list, with Retry
  (`.tma-placeholder`, design-system §8). It does not show an empty state: "No orders" is a lie when the
  orders did not load.
- **`session` cannot be fixed inside the app.** `initData` is issued when the app is opened, so only reopening
  gives a fresh one **[Heuristic]**. Long sessions exchange it for the app's own token (security §5).

## 7. Doing an action once

A user taps Pay on a slow network, nothing happens, they tap again. Or the request succeeded but the answer
was lost, and Retry repeats it. Without protection, that is two bookings or two charges **[Heuristic]**:

1. **Block the second tap.** Run the action from the MainButton: the kit shows progress and ignores taps
   until the handler finishes. An own button is `aria-disabled` while pending.
2. **An idempotency key per user action.** Create it with `idempotencyKey()` when the user taps, and reuse it
   for every retry of that tap. It is sent as `Idempotency-Key`. The server stores the key with the result
   and returns the same result for a repeat, without doing the action again.
3. **Ask the server for the outcome when in doubt.** After a `timeout` on a payment or a booking, check the
   order's state (`tma.watchOrder()`) before offering Retry.
4. **The chat is the receipt.** After the server confirms, the bot sends the confirmation message
   (`requestWriteAccess` first). If the app is closed mid-way, the user still learns what happened.

## 8. Sending the result to the chat

How the result leaves the app depends on how the app was opened ([launch-and-lifecycle.md](launch-and-lifecycle.md)):
- reply-keyboard launches use `sendData()`, up to 4096 bytes; it closes the app;
- inline-button launches use the server's `answerWebAppQuery` with the `query_id`;
- otherwise the bot sends a message after the server saved the result.

Do not put the form's data in a `startapp` link or a URL: it ends up in logs and in other people's chats.

## 9. Testing

| Check | How |
|---|---|
| Every failure state | Stand → Network: `offline`, `500`, `401`, `flaky` (every other request fails), `slow` (3 s). Each screen shows the right state, keeps the input, and Retry works |
| Double tap | Stand → Network `slow`, tap the action twice: one request (stand log), one result |
| Server answers | `--api mock.json` with `"status": 409, "body": {"reason": "…"}` for a rejection; `"delay_ms"` for a timeout |
| Keyboard | On an iPhone and an Android phone: focus every field, including the last one; the field stays visible, nothing of the app jumps over it, Enter moves on and submits at the end, the keyboard closes after submit **[Device]** |
| Autofill | iOS: name, email, phone and address fill from the contact card; the code fills from SMS **[Device]** |
| Closing | Type, then tap Close: Telegram asks; save, then Close: it does not |
| Draft | Type, close, reopen: the draft is back and says so |
| Lint | `scripts/miniapp_lint.py`: MA24 labels, MA40 number inputs, MA41 autofocus, MA07 own bottom buttons, MA06 viewport units |

## 10. Digging deeper

1. **Telegram:**
   - the Mini Apps page for `hideKeyboard`, `viewportChanged`, `enableClosingConfirmation`,
     `disableVerticalSwipes`, CloudStorage limits, `requestContact`, `sendData`;
   - `py -3 scripts/webapp_lookup.py show WebApp.hideKeyboard` for versions offline.
2. **Fields:**
   - the HTML autofill tokens (the WHATWG "autofill" section) for every `autocomplete` value;
   - MDN for `inputmode`, `enterkeyhint`, `autocapitalize`, `visualViewport`.
3. **Platform forms:** Apple HIG "Entering data" and "Text fields"; Material 3 "Text fields".
4. **Idempotency:** the IETF draft "The Idempotency-Key HTTP Header Field". Read it for how the server should
   store keys, how long to keep them, and what to answer for a key reused with a different body.
5. **Real keyboards:** when a client behaves differently from §2, record the client version, the OS and what
   happened in this file, and adjust the rule. Use Safari Web Inspector or `chrome://inspect`
   (performance-and-testing) to watch `visualViewport` while typing.

## 11. Checklist

- [ ] Nothing asked that `initData`, `requestContact`, location or the QR scanner already give.
- [ ] Visible labels; `autocomplete`, `inputmode`, `enterkeyhint` on every field; no `type="number"` for amounts or codes (MA40).
- [ ] No autofocus on open (MA41); the focused field stays visible; nothing of the app fixed to the bottom while typing; `hideKeyboard()` after submit.
- [ ] Errors on blur or submit, under the field, naming the fix; focus the first; input kept; the server validates again.
- [ ] MainButton active with errors on tap, or inactive with the reason on screen.
- [ ] Closing confirmation while the form is dirty; drafts in CloudStorage for long forms, restored with a notice, removed after submit.
- [ ] Every request through `tma.api()` (raw `initData`, timeout, safe retries); a skeleton for first loads, MainButton progress for actions.
- [ ] Cached data shown at once and refreshed on open and on `activated`; optimistic only for reversible actions.
- [ ] Each `ApiError` kind has its own screen text and action; a failed list is an error state, not an empty one.
- [ ] Actions with consequences carry an idempotency key, block a second tap, and check the order state after a timeout.
- [ ] Every Network setting tested in the stand; the keyboard and autofill tested on a phone, or reported as not done.
