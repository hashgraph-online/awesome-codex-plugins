---
summary: "Mini App accessibility and language: screen readers, text size, contrast, motion, touch targets, localization, RTL, testing, checklist; read before building or reviewing any Mini App screen."
verified: "2026-11-24"
bot_api: "10.5"
---

# Accessibility and language in Mini Apps

## Contents

- [0. Native first](#0-native-first)
- [1. Who uses what, and what breaks](#1-who-uses-what-and-what-breaks)
- [2. Screen readers: VoiceOver and TalkBack](#2-screen-readers-voiceover-and-talkback)
- [3. Text size](#3-text-size)
- [4. Contrast and colour](#4-contrast-and-colour)
- [5. Motion and transparency](#5-motion-and-transparency)
- [6. Touch targets and one-handed use](#6-touch-targets-and-one-handed-use)
- [7. Language](#7-language)
- [8. Right to left: Arabic, Hebrew, Persian](#8-right-to-left-arabic-hebrew-persian)
- [9. Testing](#9-testing)
- [10. Digging deeper](#10-digging-deeper)
- [11. Checklist](#11-checklist)

How a Mini App works for everyone who opens it from Telegram. That includes people who use VoiceOver or
TalkBack, large text, increased contrast or reduced motion, people with one free hand, and people who read
Russian, German, Arabic or Persian. Read it before you build any screen, before a rework's stage 5 (states)
and stage 3 (layout), and when reviewing. Telegram's audience is global and mobile, and a Mini App is a web
page inside the client, so nothing here comes for free: the native chat gets it from iOS and Android, the
WebView only from the markup.

Labels:
- **[WCAG]** WCAG 2.2, level AA.
- **[HIG]** Apple Human Interface Guidelines, Accessibility.
- **[M3]** Material Design 3, Accessibility.
- **[Official]** https://core.telegram.org/bots/webapps.
- **[Heuristic]** this skill's rule.
- **[Device]** behaviour you must check on a real phone, because clients and OS versions differ.

Kit pieces:
- `tma.locale()` sets `<html lang dir>`;
- `.tma-sr-only` holds hidden words;
- the RTL mirroring rules in `tma.css`;
- the `--tma-fs-*` type roles in rem.

Stand: the **Language** select (en, ru, uk, de, ar, he, fa) sets the mock user's `language_code`. Lint:
MA24 (labels and alt), MA38 (icon-only controls), MA39 (physical left / right).

## 0. Native first

Telegram's own controls are already accessible in every language: the MainButton, SecondaryButton,
BackButton, SettingsButton, `showPopup` / `showConfirm` / `showAlert`, the invoice sheet, the QR scanner,
`requestContact` and the permission prompts.

- They are read by the system screen reader;
- they are drawn by the client, so they follow its text size and its direction **[Device]**;
- Telegram translates their chrome (the popup frame, the scanner, the permission prompts).

So the cheapest accessibility work is to use them instead of drawing your own **[Heuristic]**:
- the screen's main action is the MainButton (lint MA07);
- back is the BackButton (MA19);
- a destructive confirmation is `showConfirm`, not an own modal (MA03).

Their text is plain and comes from the app, so it must be localized too (§7).

## 1. Who uses what, and what breaks

| Person | Setting | What breaks in a typical web app |
|---|---|---|
| Blind or low vision | VoiceOver (iOS), TalkBack (Android) | icon buttons read as "button"; prices read as "120" without the currency; custom toggles not announced; focus lost after a sheet opens; toasts never spoken |
| Low vision | Larger text, bold text, zoom | fixed heights clip text; a row with a price and a title overlaps; text in px never grows |
| Low vision, glare, older screens | Increased contrast | hint-grey text on a tinted surface disappears; state shown by colour only |
| Vestibular disorders, migraines | Reduce motion / reduce transparency | parallax, tilt, big transitions, blur behind text |
| Tremor, one hand, a bus | — | 24 px targets, swipe-only actions, controls at the top edge |
| Reads another language | Telegram language, `language_code` | concatenated strings, English plurals, `$12.00` everywhere, labels cut at 30 % longer text |
| Reads right to left | Arabic, Hebrew, Persian | chevrons pointing the wrong way, numbers and names jumbled, padding on the wrong side |

## 2. Screen readers: VoiceOver and TalkBack

A screen reader reads the accessibility tree built from the markup. It reads the name, the role, the state
and the value. Every control needs all four that apply **[WCAG 4.1.2]**.

### 2.1 Names, roles and states for kit components

| Component (kit) | Markup | Screen reader hears |
|---|---|---|
| Icon-only button | `<button aria-label="Search"><svg aria-hidden="true">…</svg></button>` | "Search, button" (MA38) |
| Row that opens a screen (`.tma-cell` + chevron) | `<a href>` or `<button>` around the row; chevron `aria-hidden` | "Order history, button" |
| Row with a value (`.tma-cell__after`) | the value is text inside the same control | "Language, English, button" |
| Toggle (`.tma-switch`) | `<input type="checkbox" role="switch">` in a `<label>` | "Notifications, switch, on" |
| Segmented control | `role="radiogroup"` with `role="radio"` + `aria-checked`, or `role="tablist"` when it switches panels | "Week, radio button, 2 of 3, selected" |
| Tab bar (`.tma-tabbar`) | `<nav aria-label="Sections">`, the current item `aria-current="page"` | "Profile, current page" |
| Stepper (`.tma-stepper`) | buttons `aria-label="Remove one"` / `"Add one"`, the count in `<output aria-live="polite">` | "Add one, button", then "3" |
| Sheet (`.tma-sheet`) | `role="dialog" aria-modal="true" aria-labelledby` its title | "Filters, dialog" |
| Toast / snackbar | `role="status"` (polite); errors that block work `role="alert"` | the text, once |
| Skeleton while loading | the region `aria-busy="true"`, the skeleton `aria-hidden="true"` | nothing until content arrives |
| Image (`.tma-media`) | `alt` names what it shows; decoration `alt=""` (MA24, layout L22) | "Trainer Anna Berg" |
| Stars amount (T1) | glyph `aria-hidden`, the number as text, `<span class="tma-sr-only"> Stars</span>` | "120 Stars" |
| Gram amount (T2) | the same with " Gram" | "12.5 Gram" |
| Rating (`.tma-rating`) | `role="radiogroup" aria-label="Rating"`, each star `role="radio" aria-label="4 stars"` | "4 stars, radio button, 4 of 5" |
| Avatar with initials | `aria-hidden="true"` when the name is next to it | the name, once |

Rules **[Heuristic]**:

- **A name says the action, not the icon.** Write "Close", "Add to cart", "More actions"; never "X icon",
  "cart" or "dots". Translate the name like any other string.
- **`aria-label` goes on an element that has a role**, such as a button, a link, an input, `role="img"`, a
  dialog or a landmark. On a plain `<span>` or `<div>` it has no effect in some screen readers: ARIA
  prohibits naming the generic role. Use hidden text instead (`.tma-sr-only`). This is why the Stars amount
  uses hidden text.
- **One stop per row.** A list row is one control. Wrap it in one `<a>` or `<button>`, and mark the inner
  icons, chevrons and avatars `aria-hidden`. VoiceOver users swipe through rows; five stops per row makes a
  list unusable.
- **Prefer native elements.** Use `<button>`, `<a href>`, `<input type="checkbox">`, `<select>` and `<dialog>`
  over a `div` with `role` and key handlers. A clickable `<div>` is invisible to TalkBack's "buttons" menu.
- **Hide decoration completely:** sparkles, gift backdrops, tilt layers, background patterns. Use
  `aria-hidden="true"` on the element, not just `alt=""` inside it.

### 2.2 Focus and announcements

A Mini App changes screens without page loads, so the screen reader does not know a new screen appeared
unless the app tells it **[WCAG 2.4.3, 4.1.3]**.

| Moment | Do |
|---|---|
| New screen (route change) | Move focus to its title: `<h1 tabindex="-1">` then `.focus()`. Update `document.title` |
| Sheet or dialog opens | Focus its title or first control. Keep focus inside (`inert` on the page behind). Close on the BackButton |
| Sheet closes | Return focus to the control that opened it |
| An item is added, saved or removed | A `role="status"` region announces it ("Added to cart") |
| Validation fails | `aria-invalid="true"` + `aria-describedby` pointing to the message; focus the first wrong field |
| The server confirmed a payment or an order | Announce the result, then the screen changes. Haptics are not a substitute (haptics-and-device §1) |
| Content loads after a skeleton | `aria-busy` off. Do not move focus; announce only if the user asked for it ("12 results") |

Do not announce everything. A live region that speaks on every keystroke or every scroll is as bad as the
haptic stream lint MA36 catches.

### 2.3 Gestures

VoiceOver and TalkBack take over touch: a swipe moves focus, a double tap activates. So **[WCAG 2.5.1]**:
- every swipe action (swipe to delete, swipe between cards, pull to refresh) needs a button or menu that does
  the same;
- a carousel needs previous / next buttons or must be a scrollable list;
- a long press needs an explicit "More" button.

`disableVerticalSwipes()` (7.7) does not change this; it only stops the sheet from closing on a drag.

## 3. Text size

Telegram has its own text size setting, and iOS and Android have system ones. How much of either reaches the
WebView differs by client and OS version **[Device]**. So the layout must survive text the app did not plan
for **[WCAG 1.4.4, 1.4.10]**:

- **Type in rem through the kit roles** (`--tma-fs-body` = 17 px at 100 %). Never put a px font size on a
  component. On iOS, the kit's root may use `font: -apple-system-body` so Dynamic Type can reach it;
  check this on the device (design-system §4).
- **Test at 200 %.** In the browser, set the root font size to 34 px. On a phone, set the largest
  accessibility size and open the app again. Nothing may clip, overlap or need horizontal scrolling. The
  MainButton is native and grows by itself.
- **No fixed heights on anything with text.** Use `min-height` for rows (52 / 68, native-anatomy §2), never
  `height`. Let rows wrap: at large sizes the value (`.tma-cell__after`) moves under the title. `.tma-kv.is-stacked`
  does this for key-value rows.
- **Truncate only what has a full view.** A title clamped to two lines is fine if the detail screen shows all
  of it. A price, a date or a button label is never truncated.
- **Icons grow with text** when they sit inside text (`1em`). Control icons stay 24 px; their target is 44 px
  anyway (§6).

## 4. Contrast and colour

- **Contrast:** 4.5:1 for body text and 3:1 for large text (≥ 24 px, or ≥ 19 px semibold), icons, control
  borders and focus rings **[WCAG 1.4.3, 1.4.11]**. `palettes.json` stores contrast-checked pairs, and
  `"brand"` resolves to one that passes (design-system §9).
- **Telegram's theme is the user's, and it can be custom.** `--tg-theme-*` values come from whatever theme
  the user picked, including community themes with low-contrast pairs. Rules **[Heuristic]**:
  - essential information never uses `hint_color` on `secondary_bg_color`;
  - text on `button_color` always uses `button_text_color`, never white;
  - a brand colour gets its own checked text colour, never the theme's `text_color`.
- **Increased contrast.** On `prefers-contrast: more` the kit drops translucent fills and blur
  (`tma.css`, the same rule as reduced transparency). An app's own tinted surfaces must do the same.
- **Never colour alone** **[WCAG 1.4.1]**:
  - a failed field gets a message and an icon, not just a red border;
  - a price drop says "−12 %", not only green;
  - a chart series gets a label or a pattern;
  - an order status gets a word.
- **Focus is visible.** The kit draws `:focus-visible` with the accent colour. Never remove an outline without
  a replacement. Keyboard and switch-control users on Desktop and iPad rely on it.

## 5. Motion and transparency

- `prefers-reduced-motion: reduce`:
  - no parallax, no tilt (`.tma-tilt` turns off), no slide-in of whole screens; use crossfades or nothing;
  - the gift sparkles stop (T1);
  - auto-advancing carousels stop.

  Lint MA17 requires the rule to exist. Check that each animation is inside it.
- `prefers-reduced-transparency: reduce`: solid surfaces instead of blur (lint MA12).
- Nothing flashes more than three times a second **[WCAG 2.3.1]**. Confetti and shimmer are decoration (anti-slop).
- Haptics are never the only signal (haptics-and-device §1). Every haptic comes with a visible change and,
  for outcomes, an announcement (§2.2).

## 6. Touch targets and one-handed use

- **Targets:** at least 44 × 44 pt on iOS **[HIG]** and 48 × 48 dp on Android **[M3]**. WCAG 2.5.8 sets the
  floor at 24 × 24 px. The kit's rows, stepper buttons, chips and the rating meet 44. A small visual (a 24 px
  icon) gets padding to reach the target.
- **8 px between targets**, so a tremor does not hit the neighbour.
- **Main actions within reach, at the bottom:** the MainButton and the tab bar. Telegram's header and close
  button take the top. Do not put the only "Save" at the top end of the screen.
- **No time limits** on reading or acting, unless the deal really expires (a held booking). Then show the
  time left and let the user extend it **[WCAG 2.2.1]**.

## 7. Language

### 7.1 Which language

The order **[Heuristic]**:

1. **The user's choice inside the app**, if the app offers one. Store it in CloudStorage so every device
   gets it.
2. **`initDataUnsafe.user.language_code`.** This is the IETF tag of the user's Telegram language **[Official]**.
   It is optional and can be missing. It is the language of Telegram's interface, not necessarily the
   language the person reads best.
3. **The browser's `navigator.languages`.**
4. **The app's default.**

`tma.locale(supported, { override })` does this. It matches an exact tag first (`pt-BR`), then the base language
(`pt-PT` → `pt-BR`, `ru-UA` → `ru`), and sets `<html lang dir>`. `lang` lets the screen reader pick the right
voice and the browser pick hyphenation and quotes; `dir` mirrors the kit (§8).

On the server, read `language_code` from the **verified** `initData`, never from what the client sends
(security §2). Use it when the server renders text: emails, receipts, messages the bot sends after an
action.

**The bot and the Mini App speak the same language.**
- If the bot localizes commands (`setMyCommands` with `language_code`, see `references/localization-and-rtl.md`),
  the app uses the same catalog keys and the same terms.
- A button "Open shop" in the chat that opens an app in English is a broken promise.

### 7.2 Strings

- **One catalog, keys not sentences.** No string in a component; every visible text, every `aria-label`,
  every MainButton text, every `showPopup` message and every `alt` comes from it.
- **Never concatenate.** `"You have " + n + " items"` cannot be translated: word order differs. Use one
  string with placeholders: `"You have {count} items"`.
- **Plurals by the language's rules.** Use `Intl.PluralRules`:
  - English has two forms;
  - Russian and Ukrainian have four categories (one, few, many, other);
  - Arabic has six;
  - Japanese has one.

  ```ts
  const forms = { one: '{n} товар', few: '{n} товара', many: '{n} товаров', other: '{n} товара' };
  const text = forms[new Intl.PluralRules('ru').select(n) as keyof typeof forms].replace('{n}', fmt(n));
  ```
- **Room for longer text.** German, Russian and Finnish run 30-60 % longer than English. Design every label
  against the longest language. The MainButton is one line and Telegram cuts long text
  **[Device]**, so write a verb of two or three words ("Pay", "Book a table").
- **Formality is per language** (formal or informal address). Pick one per language, check how Telegram's
  own strings in that language address the user (translations.telegram.org), and keep it across every string.
- **Telegram's own terms in Telegram's own words.** "Stars", "Gifts", "Premium", "Mini App" and "channel"
  already have official translations in every Telegram language. Look them up on
  https://translations.telegram.org (search the English term, then open the language). Use them exactly, so
  the app and the client never disagree. Do not translate "Stars" yourself.

### 7.3 Numbers, money, dates

Everything locale-dependent goes through `Intl` with the chosen language **[Heuristic]**:

| What | How | Never |
|---|---|---|
| Numbers | `new Intl.NumberFormat(lang).format(n)`; `tabular-nums` in columns | `n.toFixed(2)` shown to users, a hard-coded `,` or `.` |
| Fiat money | `Intl.NumberFormat(lang, { style: 'currency', currency })`. The currency comes from the order, not the language | "$" pasted in front |
| Stars | `formatStars(n, lang)` and the glyph; `starsText()` for plain-text surfaces (T1) | "XTR", "250 ⭐" in markup |
| Gram | `formatGrams(nano, { locale: lang })` (T2) | "TON" or "Toncoin" shown to users |
| Dates | `Intl.DateTimeFormat(lang, { dateStyle: 'medium' })`, in the user's time zone | `MM/DD/YYYY` |
| Relative time | `Intl.RelativeTimeFormat(lang, { numeric: 'auto' })`: "yesterday", "вчера" | "1 days ago" |
| Lists | `Intl.ListFormat(lang)`: "A, B and C", "A, B и C" | `.join(', ')` with " and " |
| Sorting names | `Intl.Collator(lang).compare` | `a < b` |

## 8. Right to left: Arabic, Hebrew, Persian

When `dir="rtl"`, the whole layout mirrors: the start is on the right. Telegram mirrors its own interface,
the header and bottom buttons included, when its language is RTL **[Device]**. The app must mirror the rest
**[Heuristic]**.

- **Logical properties only:** `margin-inline-start`, `padding-inline-end`, `inset-inline-start`,
  `text-align: start`, `border-start-start-radius`. The kit uses them throughout. Lint MA39 flags
  `margin-left`, `padding-right`, `text-align: left` and `float` in app CSS.
- **Mirror what points along the reading direction:**
  - chevrons on rows;
  - back / forward arrows, "next" in a pager;
  - send, sign out;
  - progress that fills from the start;
  - a horizontal carousel's order.

  The kit flips `.tma-cell__chevron`, the arrow, send and sign-out icons, and anything with `.tma-flip-rtl`.
- **Do not mirror:**
  - media controls (play, fast-forward: they follow the tape, not the text);
  - clocks and circular progress;
  - check marks;
  - logos and the Stars glyph;
  - charts' time axis (most RTL readers expect time left to right);
  - phone numbers and code.
- **Numbers stay left to right** inside RTL text. Prices, card endings and versions are LTR runs, and the
  browser handles them when the markup is clean.
- **User content gets `dir="auto"`:** names, messages, reviews, search queries. An Arabic name in an English
  app and an English name in an Arabic app both render right. Wrap an inline user value in `<bdi>`
  ("Paid by <bdi>{name}</bdi>"), so a name ending in a number or punctuation does not jump.
- **Switch knob, sheet grabber, tab order:** the switch knob starts at the inline start (kit). Tab bar items
  run right to left, so the first tab is on the right. Swipe-back gestures come from the right edge (the
  client handles them).
- **Fonts:** the system font covers Arabic, Hebrew and Persian. Do not set a Latin-only web font (lint MA16).
  Arabic script needs more line height. Keep the kit's line heights; do not tighten them.

## 9. Testing

| Check | How |
|---|---|
| Lint | `py -3 scripts/miniapp_lint.py <app>`: MA24, MA38, MA39, MA17, MA12 |
| Language and direction | Stand → Language `ar`, `de`, `ru`. Read every screen: mirrored, nothing clipped, plurals right, `lang` on `<html>` |
| Longest text | Stand → `de`, width 320. Or fake a catalog with every string padded by 40 % |
| Text size | Root font size 34 px in devtools; on a phone, the largest accessibility size |
| Contrast | Stand, scheme light and dark; devtools contrast checker on hint text, prices and buttons. Also a custom Telegram theme on a phone **[Device]** |
| Screen reader | iPhone: VoiceOver (triple-click the side button if set up). Swipe through each screen: every stop has a name, rows are one stop, sheets trap focus, results are spoken. Android: TalkBack, the same **[Device]** |
| Reduced motion and transparency | OS settings, or devtools rendering emulation; tilt, sparkles and carousels stop |
| Keyboard | Telegram Desktop or the web client: Tab reaches every control in order, focus is visible, Escape or BackButton closes sheets |

The stand cannot reproduce screen readers or the client's text-size setting. Report those checks as not done
unless a real device was used.

## 10. Digging deeper

When a question is not answered here, go to the source, in this order:

1. **The control's pattern:** WAI-ARIA Authoring Practices, https://www.w3.org/WAI/ARIA/apg/patterns/. Look up
   the pattern (switch, radio group, tabs, dialog, carousel) and copy its roles, states and keys.
2. **The success criterion:** WCAG 2.2 Understanding pages, https://www.w3.org/WAI/WCAG22/Understanding/.
   They explain the intent and the failures for each criterion cited above.
3. **Platform expectations:**
   - Apple HIG Accessibility, https://developer.apple.com/design/human-interface-guidelines/accessibility;
   - Material 3 Accessibility, https://m3.material.io/foundations/designing/overview;
   - for right to left, the HIG "Right to left" page and Material's "Bidirectionality".
4. **Telegram's words:** https://translations.telegram.org for every Telegram term in every language; the
   Mini Apps page for `language_code` and the native controls.
5. **Locale data:**
   - MDN `Intl` (NumberFormat, PluralRules, RelativeTimeFormat, ListFormat, Collator, DateTimeFormat);
   - Unicode CLDR plural rules, https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html;
   - for direction, the W3C "Structural markup and right-to-left text in HTML".
6. **Device behaviour:** when a rule here is marked **[Device]**, test it on a phone and write down the client
   version and OS. When the result contradicts this file, update the file and its test.

## 11. Checklist

- [ ] Native controls for the main action, back, confirmations and permissions; their texts localized.
- [ ] Every control has a name, a role and a state. Icon-only controls have `aria-label` (MA38). Decoration is `aria-hidden`.
- [ ] Rows are one stop. Stars and Gram amounts read as "120 Stars". Images have meaningful `alt` (MA24).
- [ ] Route changes move focus to the title. Sheets trap focus and return it. Results are announced once.
- [ ] Every swipe or long-press action has a button.
- [ ] The layout survives 200 % text and the longest language at 320 px; no fixed heights on text.
- [ ] Contrast passes in light, dark and increased contrast; nothing is told by colour alone.
- [ ] Reduced motion and reduced transparency are honoured for every effect.
- [ ] Targets are 44 pt with 8 px between them; main actions at the bottom.
- [ ] Language from the app's choice, `language_code`, the browser, then the default (`tma.locale`). `lang` and `dir` are on `<html>`. Bot and app use the same terms.
- [ ] Strings come from a catalog: no concatenation, plurals by `Intl.PluralRules`, Telegram's own terms from translations.telegram.org.
- [ ] Numbers, money, dates, lists and sorting through `Intl` with the chosen language.
- [ ] RTL: logical properties (MA39); directional icons mirrored, media and clocks not; `dir="auto"` and `<bdi>` for user content.
- [ ] Screen reader and text-size checks done on a device, or reported as not done.
