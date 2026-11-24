# Mini App components: anatomy, states, native or own

Every component a Mini App screen needs, with its anatomy, kit class, states, the native Telegram control
that replaces it when one exists, platform differences and the matching TelegramUI component for projects
that already use that library. Tokens: [design-system.md](design-system.md). Machine-readable inventory (97 entries, with
status kit / native / pattern / avoid): `data/mini-apps/components.json`; every kit entry is rendered in
`examples/mini-apps/gallery`; the order of work: [orchestration.md](orchestration.md). Labels: **[Official]**,
**[Heuristic]**.

States column: **D** default, **P** pressed, **X** disabled, **L** loading, **E** error, **0** empty,
**S** skeleton. Every interactive component also has a visible keyboard focus (`:focus-visible`) for
desktop clients and works right-to-left (`dir="rtl"`: logical properties, mirrored chevrons and switches).

Measured sizes and how iOS 27 and Telegram compose screens: [native-anatomy.md](native-anatomy.md).

## 1. Native first

| Need | Native (version) | Own component only when |
|---|---|---|
| Primary action of the screen | `MainButton` (6.0) | outside Telegram (browser fallback `[data-tma-fallback="main-button"]`) |
| Second action next to it | `SecondaryButton` (7.10) | older clients: a tonal button in the content |
| Back one level | `BackButton` (6.1) | never: no own arrow |
| App settings | `SettingsButton` (7.0) | older clients: a settings row on the profile screen |
| Yes/no, alert, up to 3 choices | `showConfirm` / `showAlert` / `showPopup` (6.2) | the choice needs more than 3 options or rich content: own sheet |
| QR scan | `showScanQrPopup` (6.4) | never |
| Share to a chat | `shareMessage` (8.0) | — |
| Haptics | `HapticFeedback` (6.1) | never the Vibration API |

Gate each by version (`isVersionAtLeast`, or the kit's `tma.has()`). **[Official]**/**[Heuristic]**

## 2. Structure

| Component | Anatomy | Kit | States | Notes |
|---|---|---|---|---|
| Page | safe-area padding, bottom space for a tab bar | `.tma-page` | D | `min-height: var(--tg-viewport-stable-height)`, never `100vh` |
| Screen (level 2+) | page that pushes in | `.tma-screen` (+`.is-back`) | D | shows BackButton; hides the tab bar |
| Section | header (left: title, right: total or link), list, footer | `.tma-section`, `__header`, `__footer` | D, S | headers in sentence case; a total on the right in hint colour |
| List | inset group on the page | `.tma-list` (`.is-full` on Android) | D, 0, S | separators start at the text column |
| Cell | leading (avatar / icon tile / none), title, subtitle, trailing (value, chevron, switch, check, stepper) | `.tma-cell`, `.is-2` | D, P, X, S | 52 / 68 px; title and subtitle truncate with ellipsis, values never wrap |
| Button cell | an action as a row | `.tma-cell.is-button` / `.is-danger` | D, P, X | for actions inside settings; destructive asks with `showConfirm` |
| Divider | hairline | separator rule of `.tma-list` | D | half-pixel via `scaleY(.5)` |
| Placeholder | icon tile, title, one line, one action | `.tma-placeholder` | 0, E | names what is missing and the way forward |

## 3. Navigation

| Component | Anatomy | Kit | States | Rules |
|---|---|---|---|---|
| Tab bar | floating glass capsule, 2-5 tabs: icon + label, selected = fill + accent | `.tma-tabbar.tma-glass` | D, selected | sections only, never actions; hidden on level-2 screens and while the MainButton shows; content gets its height plus the bottom inset |
| Segmented control | 2-5 options in a track | `.tma-segmented` | D, selected | switches views of one dataset (period, active/finished); `selectionChanged` |
| Tabs / chips row | scrolling chips | `.tma-scroll-x` + `.tma-chip` | D, selected | filters; selected `aria-pressed="true"` |
| Back | Telegram's BackButton | `tma.nav` | — | one stack: sheet closes before the screen |

## 4. Actions

| Component | Anatomy | Kit | States | Rules |
|---|---|---|---|---|
| MainButton | Telegram's bottom button: text, optional custom emoji (9.5), progress | `tma.mainButton()` | D, X, L | verb + object ("Place order · €8.40"); disabled with the reason in the content; progress over ~300 ms |
| SecondaryButton | second bottom button; `position` left/right/top/bottom | `tma.secondaryButton()` | D, X, L | short text; no `style` field and no promised shape |
| Button in content | capsule 28 / 34 / 50 | `.tma-btn` `.is-filled` / `.is-tonal` / `.is-plain` / `.is-danger` | D, P, X | at most one filled per screen; tonal for secondary actions; never fixed to the bottom |
| Quick actions | 2-4 equal tiles: 48 px accent circle + verb label | `.tma-actions` (`--tma-cols`) / `.tma-action` | D, P, X | same width; labels are verbs ("Send", "Top up") |
| Chip | capsule label, optional icon | `.tma-chip` (`.is-success`) | D, P, selected | a toggle or a filter; one cross-sell chip per screen at most |
| Icon button | 44 px circle | `.tma-icon-btn` | D, P, X | `aria-label` required |

## 5. Input

| Component | Kit | States | Rules |
|---|---|---|---|
| Text field ([forms-and-data.md](forms-and-data.md) §1-3) | `.tma-field` + `.tma-field__label` + `.tma-input` + `.tma-field__error` | D, focus, X, E | visible label (G5); error under the field names the fix; `autocomplete` and `inputmode` set |
| Textarea | `textarea.tma-input` | D, focus, E | counter only near the limit |
| Select / picker | a cell that opens a sheet or a radio list | D, selected | native `<select>` only for long, plain lists |
| Switch | `.tma-switch` (in a cell, label = the row title) | on, off, X | changes apply at once; `selectionChanged` |
| Radio / check | `.tma-check` | D, checked, X | single choice in a list → radio rows |
| Slider | `.tma-slider` | D, X | show the value next to it |
| Stepper | `.tma-stepper` | D, X at limits | quantity; the minus becomes "Remove" at 1 when it removes |
| Search | `.tma-search` | D, focus, 0 results | placeholder "Search"; results update as you type; empty result explains |

Unsaved input turns on `enableClosingConfirmation()`; it goes off after saving. Drafts go to `CloudStorage`
(design-system §8, [security.md](security.md) §6).

## 6. Display

| Component | Kit | States | Rules |
|---|---|---|---|
| Avatar | `.tma-avatar` (`.is-48`, `.is-56`) | D, S | image with `alt`, or initials; never an emoji |
| Icon tile | `.tma-icon-tile` | D | tint from the accent; icons from one line set |
| Badge | `.tma-badge` | D | a count only; no "NEW" badges (a one-time coachmark instead) |
| Tag | `.tma-tag` | D | quiet text fact ("Ends 30 Nov"), one per card; no corner ribbons |
| Figure | `.tma-figure` + `.tma-figure__minor` | D, L (skeleton), E ("—") | one per screen; tabular numbers |
| Delta | `.tma-delta.is-up` / `.is-down` | D | sign or arrow always, plus period ("+2.53 % today") |
| Card | `.tma-card` | D, S | content groups that are not rows; never cards inside cards |
| Banner / promo | `.tma-banner` + close | D, dismissed | the screen's one moment; dismissal remembered in `CloudStorage`; carousel auto-advance off on reduced motion and Android `LOW` |
| Hero | `.tma-hero` | D | brand moment at the top of a section root; header colour follows it |
| Chart | `svg.tma-chart` (`.is-down`) | D, L, E | one series, colour by direction, muted grid, labels in hint; no gradient fill or glow |
| Countdown | `.tma-figure` or text in tabular numbers | live | ticks once a second, pauses on `deactivated` |
| Progress | `.tma-progress` | D | only for measurable progress |
| Spinner | `.tma-spinner` | L | inside a control; whole screens use skeletons |
| Skeleton | `.tma-skeleton` | S | the real layout's shapes; stops on reduced motion |
| Coachmark | `.tma-coachmark` | shown once | points at a new feature once; "seen" stored in `CloudStorage` |
| Snackbar | `.tma-snackbar` | shown | confirms an off-screen change; ~2 s; above the tab bar and insets |

## 6a. Media

| Component | Kit | Variants | Rules |
|---|---|---|---|
| Image | `.tma-media` + `<img>` | 16:9 default, `.is-square`, `.is-portrait` (4:5), `.is-circle`, `.is-fill` (edge to edge), `.is-contain` | `alt` (`alt=""` for decoration), `width`/`height`, `loading="lazy"` below the fold, sized for the slot |
| Video | `.tma-media` + `<video poster>` + `.tma-media__play` + `.tma-media__badge` | poster with play and duration | `playsinline`; autoplay only muted and silent; pause on `deactivated` |
| Photo grid | `.tma-gallery` | 3 columns, 2 px gaps | tap opens a full view screen with BackButton |
| Carousel | `.tma-carousel` + `.tma-dots` | snap, 86 % cards | no auto-advance with reduced motion or Android `LOW`; dots are decoration (`aria-hidden`) |
| Audio | `.tma-audio` in a cell | play, track, duration | play button with a label naming the clip and its length |
| File | `.tma-file__icon` in a two-line cell | name, size, download icon | `downloadFile` (8.0) in a tap; the server sends `Content-Disposition` and CORS |
| Sticker moment | `.tma-moment` | TGS, WEBM, Lottie, static fallback | one per screen; static on reduced motion and `LOW`; `role="img"` + label |
| Map | `.tma-map` | static image, interactive | `disableVerticalSwipes` only while the user pans; location via `LocationManager` (8.0) |
| QR code | `.tma-qr` | show; scan via `showScanQrPopup` (6.4) | white quiet zone in both themes (scanners need contrast) |
| Avatar stack | `.tma-avatar-stack` | 2-4 faces | label the count ("3 friends") |

## 6b. Tables

A table only when people compare values across columns; two to five facts read once stay a list or a
key-value list. **[Heuristic]**

| Component | Kit | Rules |
|---|---|---|
| Data table | `.tma-table-wrap` > `table.tma-table` with `<caption>` | numbers right-aligned (`.is-num`), tabular figures, header in hint colour; scrolls sideways inside its group, never the page |
| Compact table | `.tma-table.is-compact` | dense style screens; rows still ≥ 32 px with 44 px tap targets on interactive rows |
| Sortable header | `th[aria-sort]` | `aria-sort` on the active column, a sort control in the header |
| Sticky first column | `tbody th[scope="row"]` | wide comparisons; the row label stays visible |
| Leaderboard | `.tma-rank` + `tr.is-me` | the user's own row tinted and present even when outside the top |
| Key-value list | `dl.tma-kv` | receipts, order details |
| Comparison (plans) | data table with check icons and text | never colour alone for yes/no |

## 6c. Icons

`examples/mini-apps/_kit/icons.svg` is an own line set: 83 icons on a 24 px grid, stroke 1.8, round caps,
drawn with `currentColor` (the Stars sign `i-stars` is the one filled glyph). `data/mini-apps/icons.json` maps
every id to the SF Symbol, Material Symbols and **Lucide** name with the same meaning, so a brief that names
"magnifyingglass" or "shopping_cart" maps to `i-search` or `i-cart`. **[Heuristic]**

**Icons always come from SVG, never from emoji.** The order:

1. The kit's own set (`_kit/icons.svg`).
2. An icon the kit lacks: **one open-licence SVG library per app**, Lucide first (ISC, same 24 px line grid;
   set `stroke-width: 1.8`), else Tabler (MIT), Phosphor (MIT, one weight) or Material Symbols Outlined
   (Apache-2.0, for Android-first apps). Inline the SVG or add it to the sprite; no icon font from a CDN for a
   few glyphs. Names for every kit id: `icons.json` → `lucide`. Libraries and licences: `icons.json` →
   `open_libraries`.
3. Never: Unicode emoji (★ ⭐ 🔥 ✅ included) as icons, bullets, status or decoration; SF Symbols artwork
   (Apple licence: names only, for mapping); two libraries on one screen.

- One size per context (22 in rows and tabs, 16 inline in chips and pills); the same stroke everywhere.
- Icon-only buttons carry `aria-label`; decorative icons `aria-hidden="true"`.
- Ratings draw the filled `i-stars` glyph (`.tma-rating-inline__star`) before the number, not the ★ character.
- Animated or premium stickers from the bot's packs only as the one moment ([anti-slop.md](anti-slop.md) §3).

## 6d. Settings rows (iOS 27 trailing types)

| Trailing | Kit | Example |
|---|---|---|
| Default detail | `.tma-cell__after` | Language · English |
| Disclosure | `.tma-cell__chevron` (+ detail) | Payment methods · 2 › |
| Button | `.tma-cell.is-button` / `.is-danger` | Invite a friend; Delete history |
| Date / time / value pill | `.tma-pill-select` over a native `input type=date|time` or `select` | Pickup time · 10:30 |
| Pop-up menu | `.tma-popup-trigger` + `.tma-menu` | Default size · Medium ⌄ |
| Stepper | `.tma-stepper` | Extra shots − 1 + |
| Toggle | `.tma-switch` (`role="switch"`) | Order is ready ● |
| Checkmark | `.tma-cell__check` in `role="option"` rows | Whole milk ✓ |

Every element above is rendered in `examples/mini-apps/gallery` (open it in the preview stand) and listed in
`data/mini-apps/components.json` with its status, variants, states and native replacement.

## 6e. Telegram's own values

Stars amounts, gram amounts, gift cards, unique gifts with rarity, limited counters (kit); paid content,
Premium perks, rating levels and boosts (patterns); verification marks (never drawn by the app). Rules,
data and the kit functions: [telegram-elements.md](telegram-elements.md); catalogue group `telegram`.

## 7. Overlays

| Component | Kit | Rules |
|---|---|---|
| Native popup | `showPopup` / `showConfirm` / `showAlert` | title ≤ 64, message 1-256, 1-3 buttons (`default`, `ok`, `close`, `cancel`, `destructive`) |
| Bottom sheet | `.tma-scrim` + `.tma-sheet` | grabber, header (close left, title centre, confirm right), focus moves in and returns; BackButton and swipe down close it, except with unsaved input; bottom bar colour = sheet surface while it uses the MainButton |
| Onboarding sheet | sheet + illustration moment + 2-3 benefit rows + MainButton "Continue" | once per section; legal line in footnote with `openLink`; consent recorded on the server |

## 8. iOS and Android differences

| | iOS | Android |
|---|---|---|
| Lists | inset, radius 26 | inset radius 16 or full width |
| Switch | 51×31 capsule (kit) | the same kit switch is acceptable; Material track proportions are optional |
| Section headers | footnote size, hint colour | Telegram Android themes colour them (`section_header_text_color`) |
| Back | edge swipe stays free | system back triggers `backButtonClicked` |
| Glass | yes | yes, off on `LOW` |

## 9. Mapping to TelegramUI (`@telegram-apps/telegram-ui`)

TelegramUI (MIT, React 18 peer, last release v2.1.13 on 2025-10-14) is not a dependency of this skill: it
predates the 7.6 and 7.10 theme keys (`section_separator_color`, `bottom_bar_bg_color`) and React 19. For a
project that already uses it, the equivalents:

| Kit | TelegramUI |
|---|---|
| `.tma-list` + `.tma-section` | `List`, `Section` (`Section.Header`, `Section.Footer`) |
| `.tma-cell` | `Cell` (`before`, `after`, `subtitle`, `description`); `Navigation` for chevrons; `ButtonCell`; `Info` for trailing values |
| `.tma-placeholder` | `Placeholder` |
| `.tma-btn` | `Button` (`mode`: filled / bezeled / plain / gray), `IconButton` |
| `.tma-segmented` | `SegmentedControl` |
| `.tma-tabbar` | `Tabbar` |
| `.tma-chip` | `Chip` |
| `.tma-avatar` / `.tma-badge` | `Avatar`, `Badge` |
| `.tma-banner` | `Banner` |
| `.tma-card` | `Card` |
| `.tma-input` / `.tma-switch` / `.tma-check` / `.tma-slider` | `Input`, `Textarea`, `Switch`, `Checkbox`, `Radio`, `Slider` |
| `.tma-skeleton` / `.tma-spinner` / `.tma-progress` | `Skeleton`, `Spinner`, `Progress` |
| `.tma-snackbar` | `Snackbar` |
| `.tma-sheet` | `Modal` |
| `.tma-figure` | `LargeTitle` / `Title` with `tabular-nums` |

Map the two newer keys yourself when using TelegramUI:
`--tgui--divider: var(--tg-theme-section-separator-color)` and a bottom-bar surface from
`--tg-theme-bottom-bar-bg-color`. **[Heuristic]**
