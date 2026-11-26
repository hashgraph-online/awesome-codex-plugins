---
summary: "Measured anatomy of iOS 27 and Telegram screens (layout, lists, buttons, tab bar, sheets, alerts, empty states, fields) turned into rules; read to make a screen sit next to Telegram's own chrome."
verified: "2026-11-24"
bot_api: "10.5"
---

# How iOS 27 and Telegram build screens: measured anatomy

## Contents

- [1. Layout: margins, safe areas, widths](#1-layout-margins-safe-areas-widths)
- [2. Lists: rows, headers, footers](#2-lists-rows-headers-footers)
- [3. Buttons](#3-buttons)
- [4. Tab bar](#4-tab-bar)
- [5. Sheets](#5-sheets)
- [6. Alerts and dialogs](#6-alerts-and-dialogs)
- [7. Empty states](#7-empty-states)
- [8. Text fields](#8-text-fields)
- [9. How Telegram composes Mini App screens (TgKit templates)](#9-how-telegram-composes-mini-app-screens-tgkit-templates)
- [10. Checklist for a screen](#10-checklist-for-a-screen)

What the two design sources actually do, measured component by component through the Figma MCP on
**2026-11-24**, and the rule each measurement becomes in this skill. Use it to build a screen that sits next to
Telegram's own chrome without looking assembled, and to review one ("why does this look off?").

Sources:
- **[iOS27]** the Apple iOS and iPadOS 27 Figma kit (Figma Community 1651309003795292092; pages Layout Guides,
  Lists, Buttons, Tab Bars, Sheets, Alerts, Empty States). Proportions and behaviour only: Apple's artwork and
  SF Symbols are not shipped.
- **[TgKit]** the Telegram Mini Apps UI Kit (Community): its three template apps (Wallet and City Explorer on
  iOS, Job Finder on Android), drawn by Telegram before Liquid Glass.
- **[Heuristic]** this skill's decision where the two differ or a Mini App needs something else.

How to repeat the reading for another component or a newer kit: [figma-workflow.md](figma-workflow.md). Values
also sit in `data/mini-apps/design-sources.json` → `ios27.anatomy`.

## 1. Layout: margins, safe areas, widths

- **Margins.** 16 pt inside lists, rows, headers and footers; 20 pt layout margin on the iPhone Duo (the
  foldable) and on wide layouts **[iOS27]**. Kit: `--tma-margin` 16, rows pad 16.
- **The foldable iPhone (iPhone Duo).** Inner display 669 × 951 pt, outer 466 × 678 pt with a vertical bar of
  system controls on the outer one **[iOS27]**. A Mini App in Telegram on the inner display is about 669 pt
  wide: cap reading content at ~600 pt (`.tma-content-cap`), switch tile grids to 3 columns from 560 pt
  (layout rule L09), keep the tab bar a centred capsule (409 pt wide there, not full width). The stand has a
  669 width for this.
- **Top and bottom.** Telegram draws the header and the bottom bar; the app reads
  `--tg-safe-area-inset-*` and `--tg-content-safe-area-inset-*` and never hard-codes their heights
  ([design-system.md](design-system.md) §5).

## 2. Lists: rows, headers, footers

| Part | iOS 27 | Kit |
|---|---|---|
| Row height | 52 regular, 68 tall | `--tma-row` 52, `--tma-row-2` 68 |
| Row padding | 16 start and end | `.tma-cell` padding 16 |
| Leading image | regular: fill 52, circle 42, rounded 30, symbol 28 × 20; tall: fill 68, circle 60, rounded 44; 8 pt to the text | `.tma-row-thumb`, `.tma-avatar`, `.tma-icon-tile` |
| Title / subtitle | body 17/22; subheadline 15/20 in the secondary label colour | `.tma-cell__title`, `.tma-cell__subtitle` |
| Trailing | detail 17 secondary, then symbols, checkmark, chevron, 16 pt apart; chevron 8 pt wide in the tertiary label colour (30 %) | `.tma-cell__after`, `.tma-cell__chevron` |
| Separator | from the text column to the trailing edge, 1 px "vibrant" separator | `--tma-cell-text` inset |
| Header | **nested** 17 semibold secondary; **prominent** 20 semibold primary; **extra prominent** 22 bold primary; padding 10 / 16; an action at the end in the accent (15 regular) | `.tma-section__header` (nested by default), `.is-prominent`, `.is-extra`; `.is-small` = the older 13 pt caption |
| Footer | footnote 13/18 secondary, padding 8 top, 6 bottom, 16 sides | `.tma-section__footer` |
| Swipe actions | 60 pt per action (symbol), 84 (symbol and label) | not in Mini Apps: use an action sheet or a detail screen |
| Edit and reorder | 22 pt circle edit control; reorder grabber "line.3.horizontal" in the tertiary colour | rarely needed; reorder with explicit Up / Down |

Rules:
- **Headers in sentence case.** iOS 27 dropped the small uppercase header; the kit's default
  `.tma-section__header` is the nested header (17 semibold), prominent (`<strong>` or `.is-prominent`) marks
  the sections of a screen, extra prominent (`.is-extra`) appears once at the top of a long screen **[iOS27]**.
  Telegram's own templates still show small uppercase headers ("TRANSACTION HISTORY") because they predate the
  redesign **[TgKit]**; `.is-small` keeps that 13 pt caption, sentence case, for settings-like lists only. The
  colour follows `section_header_text_color` (Telegram Android paints it in the accent) **[Heuristic]**.
- **One trailing element that matters.** Detail text plus a chevron is the common pair; never more than two
  trailing items in a row.

## 3. Buttons

| Size | Height | Padding | Label |
|---|---|---|---|
| small | 28 | 10 × 4 | subheadline 15/20 regular |
| medium | 34 | 14 × 7 | subheadline 15/20 regular |
| large | 50 | 20 × 14 | body 17/22 regular |

- **Shape:** capsules everywhere (radius 1000) **[iOS27]**. Kit: `.tma-btn`, `.is-sm`, `.is-lg`.
- **Styles:** *borderless* (accent text only), *bordered* (tertiary fill `rgb(118 118 128 / .12)`, accent
  text), *bordered prominent* (accent fill, white text), each with a destructive and a disabled state
  **[iOS27]**. Kit: `.is-plain`, default and `.is-tonal`, `.is-filled`, `.is-danger`.
- **Liquid Glass buttons:** *glass* and *glass prominent*, 17 medium labels, a 94 % white backing under the
  tint, hairline side highlights and a soft `0 8 15 / 2 %` shadow; icon-only glass buttons are 50 pt circles
  **[iOS27]**. In a Mini App only floating controls are glass (`.tma-glass`); in-content buttons stay solid.
- **The screen's primary action is the MainButton**, Telegram's own large capsule at the bottom **[Official]**;
  an in-content large filled button appears only in a browser fallback or when the MainButton is used for
  something else (Telegram's Job Finder template puts "Apply" in content for this reason) **[TgKit]**.

## 4. Tab bar

- A floating Liquid Glass capsule with 25 pt side and bottom insets, tab items 54 pt tall, the selected tab
  a pill in the tertiary vibrant fill with the symbol and label in the accent; labels 10 semibold, symbols
  18 semibold; unselected labels in the primary label colour, not grey **[iOS27]**. Kit: `.tma-tabbar`
  (labels at our 11 px floor, semibold; 26 px symbols, the selected one heavier and tinted, so selection never
  rests on colour alone; Android draws unselected tabs in the hint colour, as Material does).
- **Search role:** search can be a separate 54 pt round glass button to the right of the bar, 16 pt away
  **[iOS27]**. In a Mini App: a search field at the top of the list it searches (layout rule L14), or a round
  floating button only when search is a whole section.
- **Prominent tab:** one action can sit in its own circle beside the bar (for example "New") **[iOS27]**. In a
  Mini App the primary action is the MainButton, which hides the tab bar; do not add a prominent tab.
- 2-5 tabs; the bar disappears on level-2 screens and while the MainButton shows ([components.md](components.md) §3).

## 5. Sheets

- **Medium detent floats:** 6 pt from the left, right and bottom edges, top corners 38, bottom corners follow
  the display (58 on the reference iPhone), a `0 8 48 / 25 %` shadow, the page dimmed with black at 20 %
  **[iOS27]**. Kit on iOS: `.tma-sheet` floats 6 pt from the edges with radius 38 on all corners (the Mini App
  cannot know the display radius) **[Heuristic]**; Android keeps the edge-to-edge sheet.
- **Grabber** 60 × 4, 6 pt from the top **[iOS27]**; the kit uses it on iOS and keeps 36 × 5 on Android.
- **Header:** a 44 pt round glass close button on the left, the title in headline 17 semibold centred, a
  prominent (accent) confirm button on the right; 16 pt padding, content starts 16 pt below **[iOS27]**.
  Kit: `.tma-sheet__head` (three columns, 44 pt ends).
- Large detent: the sheet reaches the top with the page behind it scaled back; a stacked sheet nests one more
  level **[iOS27]**. In a Mini App prefer a pushed screen over a stacked sheet.

## 6. Alerts and dialogs

Telegram draws `showAlert`, `showConfirm` and `showPopup` itself, so the app does not style them **[Official]**.
For reference, iOS 27 alerts: radius 34, 14 pt padding, title 17 semibold and message 17 regular **left
aligned**, capsule buttons 48 pt tall side by side (secondary fill for Cancel, accent fill for the default,
red text for destructive), stacked when the labels are long; an optional text field group in the secondary
fill with radius 26 and 52 pt rows **[iOS27]**. Write popup texts to that shape: a short title, one complete
sentence, buttons that name the outcome.

## 7. Empty states

Three iOS 27 variants: title and subtitle; a symbol in a 50 pt circle tinted at 15 % with the symbol in the
tint (22 semibold); a large symbol. The message is 22 semibold, the description secondary; the content is
centred vertically; the primary action is a full-width glass prominent capsule at the bottom **[iOS27]**.
Kit: `.tma-placeholder` with `.tma-placeholder__icon` (50 pt tonal circle), the title in title2 22, the
description in body hint (smaller than Apple's 22 medium, so it reads as a description in a narrow WebView)
**[Heuristic]**; the action is the MainButton when it is the screen's only action, else one tonal button.

## 8. Text fields

- **iOS 27:** grouped fields in the secondary fill `rgb(120 120 128 / .16)`, radius 26, 52 pt rows, the value
  17 medium, a separator between fields **[iOS27]**. Kit: `.tma-field` + `.tma-input` on the surface, or inside
  a list for grouped fields.
- **Android (Telegram's kit):** outlined fields with an 8 pt radius and the label above or in the border; form
  sections titled in the accent colour ("Personal information", "Files") **[TgKit]**. Kit on Android:
  outlined `.tma-field > .tma-input` (focus ring in the accent); section titles follow
  `section_header_text_color`.

## 9. How Telegram composes Mini App screens (TgKit templates)

| Template | Platform | What it shows |
|---|---|---|
| Wallet | iOS | a centred balance (caption, then a large figure with a currency icon above it); a row of 3-4 quick actions, icon above label, in the accent; each asset as its own inset row card; history as a list with avatars, amounts signed and coloured, the status under the amount; a detail screen with an avatar line, a giant signed amount, the date in hint and one key-value card; an empty block "Your orders will appear here" inside its section |
| City Explorer | iOS | horizontal carousels per section with the header and "See all" on one line; tall cards (image on top, then title, country, one line of description) and full-bleed image cards with a bottom scrim, title and subtitle on the image; a detail screen with an edge-to-edge photo and page dots, the title 22 bold with the subtitle in hint, two side-by-side tonal buttons with the icon above the label, an About section of label-above-value rows with an inline pill action ("Convert") |
| Job Finder | Android | full-width sections separated by gaps instead of rounded cards; bold section titles with "See all"; three-line rows with 32 pt app icons; chips for tags; an accordion FAQ; a form with outlined fields; file rows with an upload progress ring and a remove button; "Attach file" as an accent row |

Rules taken from them **[TgKit]/[Heuristic]**:
- **Balance screens:** caption → large figure → quick actions (3-4) → lists. The figure is the moment; the
  quick actions are icon-over-label in the accent, never filled tiles (kit `.tma-figure`, `.tma-quick-actions`).
- **Detail screens:** media or an identity line first, then the title, then actions as a row of equal tonal
  buttons (icon above label) when there are 2-3 of them, then label-above-value rows (`.tma-kv.is-stacked`).
- **Discovery screens:** one horizontal carousel per section at most (L10), the section header carries "See
  all"; text on an image only with a bottom scrim (L20).
- **Android:** edge-to-edge sections (`.tma-list.is-full`), accent section titles, outlined fields; iOS:
  inset rounded groups.
- **Empty blocks inside a section** say what will appear there ("Your orders will appear here"), in hint,
  centred in the section's surface.

## 10. Checklist for a screen

- [ ] 16 pt margins; rows 52 / 68; leading images at the iOS sizes; trailing items 16 pt apart, at most two.
- [ ] Section headers in sentence case: nested 17 by default, prominent or extra prominent where the screen needs them; footers 13/18.
- [ ] Buttons are capsules at 28 / 34 / 50; one filled button at most in content; the primary action is the MainButton.
- [ ] Floating controls (tab bar, round buttons) are glass with a solid fallback; content surfaces are solid.
- [ ] Sheets float on iOS with the 60 × 4 grabber; a close button, a title and at most one confirm in the head.
- [ ] Empty states: symbol in a tinted circle, a 22 pt message, the reason, one action.
- [ ] On Android: edge-to-edge sections, outlined fields, accent section titles where the theme gives them.
- [ ] Checked at 320, 390, 430 and 669 pt (foldable inner display) in the stand.
