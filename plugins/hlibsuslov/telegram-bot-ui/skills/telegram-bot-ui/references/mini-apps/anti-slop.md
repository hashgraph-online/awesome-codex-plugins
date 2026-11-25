---
summary: "How a Mini App ends up looking generated and what to do instead: Telegram-specific tells, conflicts and decisions, general AI-UI tells, polish pass, checklist; read when polishing or reviewing."
verified: "2026-11-24"
bot_api: "10.5"
---

# Anti-slop for Mini Apps

## Contents

- [1. The two principles](#1-the-two-principles)
- [2. Telegram-specific tells](#2-telegram-specific-tells)
- [3. Conflicts and decisions [Heuristic]](#3-conflicts-and-decisions-heuristic)
- [4. General tells, adapted (unslop, impeccable)](#4-general-tells-adapted-unslop-impeccable)
- [5. The polish pass ("make it premium / cleaner / nicer")](#5-the-polish-pass-make-it-premium--cleaner--nicer)
- [6. Checklist](#6-checklist)
- [Linter rules](#linter-rules)

How a Mini App ends up looking generated or "like a website in a sheet", and what to do instead. It joins
three sources: Telegram's Design Guidelines (always first), the craft floor of the impeccable skill
(contrast, states, browser surfaces) and the unslop catalogue of AI-UI tells (Damir Sokolovsky, CC BY 4.0,
adapted). A Mini App is almost always an **Operate** product (people come to do a task), with small
**Persuade** moments (onboarding, a promo) inside it. Labels: **[Official]**, **[Heuristic]**.

## 1. The two principles

1. **Telegram-native beats general taste.** Where a general design rule and Telegram's own UI disagree,
   Telegram wins (§3).
2. **Quiet chrome, one moment.** Grouped lists, system type, the theme's colours; one rich element per
   screen (a figure, a promo, an illustration, a chart). Everything else stays calm.

## 2. Telegram-specific tells

| Tell | Fix |
|---|---|
| Own header with a back or close arrow | `BackButton`; Telegram draws the header |
| Own fixed CTA at the bottom while the MainButton is available | `MainButton` / `SecondaryButton` |
| Hard-coded `#fff` / `#000` surfaces; a white flash in dark mode | theme roles; chrome colours before `ready()` |
| `100vh` | `var(--tg-viewport-stable-height)` and safe-area variables |
| Content under the notch or Telegram's buttons in fullscreen | `--tg-safe-area-inset-*` + `--tg-content-safe-area-inset-*` |
| Splash screen with a logo, a landing hero on every launch | straight to a useful screen with skeletons; onboarding once |
| Hamburger menu, sidebar, desktop grid | tab bar 2-5, sections, BackButton |
| `alert()`, own confirmation dialogs for a yes/no | `showConfirm`, `showPopup` |
| Hover-only hints, cursor effects | taps and long-press |
| Confetti, pulsing dots, endless loops | one success animation + `notificationOccurred('success')` |
| Haptics on everything | the table in [design-system.md](design-system.md) §7 |
| Custom fonts in lists and buttons; web fonts from a CDN | the system font |
| "Login with Telegram" inside the app; asking for a phone without a reason | `initData` already identifies the user; `requestContact` only with a visible reason |
| Tokens in the client; trusting `initDataUnsafe` | [security.md](security.md) |
| `localStorage` for user data or session tokens | `CloudStorage` / `DeviceStorage`; secrets in `SecureStorage` |
| The app inside another site's iframe, a redirect to another domain | one origin (Bot API 10.2) |
| Launch params read after the router rewrote the hash | read them on the first line |
| An own splash over Telegram's loading screen | loading screen in @BotFather; `ready()` after the first useful screen |
| BackButton that does nothing, Android back that leaves the app | one navigation stack, `BackButton.onClick` |
| A blank screen on a network error | an error state with retry; plain offline text |
| A brand-blue button in a user's green theme | the theme's `button_color`; brand on one moment only |

## 3. Conflicts and decisions [Heuristic]

| Conflict | Decision |
|---|---|
| "No emoji" vs Telegram, where emoji is a native language | **No Unicode emoji anywhere in a Mini App's interface**: not as icons, not in titles, labels, buttons, list rows, empty states, toasts or popups. Icons come from the kit or one open SVG library ([components.md](components.md) §6c). The only exceptions: animated or premium stickers from the bot's packs (TGS / WEBM, `iconCustomEmojiId` 9.5, `setEmojiStatus`) as the illustration of one moment per screen, and the Stars character in plain-text-only surfaces (next row). Bot messages follow the bot-side rules |
| "No coloured gradients" vs a brand header and CTA | only a tonal gradient of one hue on one moment (hero, promo), fading into the page; buttons solid; cross-hue gradients and gradient text banned |
| "No glass as decoration" vs Telegram's glass chrome on iOS | glass only on floating controls over scrolling content (tab bar, side circle), with a solid fallback; cards and cells solid |
| "No NEW badges" vs a coachmark in the reference | a one-time coachmark naming the new feature, remembered; no permanent badges |
| Own "verified" ticks, Premium-like star badges next to names | trust signals in text; Telegram draws its marks ([telegram-elements.md](telegram-elements.md)) |
| Stars prices vs "no emoji" | In markup the Stars sign is the kit's SVG glyph (`.tma-star`, [telegram-elements.md](telegram-elements.md) T1), never the character. `⭐ 250` as text only where no markup exists: the MainButton and SecondaryButton text and native popups (`starsText()`). Lint MA13 flags every other emoji, the star included |
| "Primary is off-white on dark" | in a Mini App the primary action is the MainButton in the theme's `button_color` |
| "Own typeface for an own world" | a Mini App operates inside Telegram: system font; a brand face only inside the one moment |
| Corner ribbons on cards (reference) | a quiet tag text, one per card |

## 4. General tells, adapted (unslop, impeccable)

- **Surfaces and colour:** purple-to-blue gradients, glows, blurred blobs, neon borders, many tints of one
  hue, everything highlighted → one neutral surface ramp from the theme, one accent used once or twice.
- **Type:** weights 800-900, uppercase tracked labels, many sizes, mixed number formats, italics for
  emphasis → the scale in design-system §4, weights 400/500/600, one number format in tabular figures.
- **Icons:** emoji as icons or status, icons of mixed sizes and strokes, a sparkle for AI → one line set
  (stroke 1.8), one size per context, same icon box in every row.
- **Spacing:** arbitrary values, uneven rows, groups closer to neighbours than to their own items → the
  4 px steps, one row height per list, smaller gaps inside groups than between them.
- **Copy:** greetings ("Welcome back! 👋"), exclamation marks, changes without a reference ("+12%!!"),
  hype words, trailing periods on buttons, fake data ("$123,456") → the screen's title, plain statements,
  "+12 % vs last month", what the thing does, plausible numbers.
- **Components:** same-size icon-heading-text cards as the page, cards in cards, a sparkline on every stat,
  pills on everything → grouped lists, one main chart, radius by size.
- **Motion:** `transition: all`, `hover:scale`, bouncy springs, everything flying in, animating layout →
  one ease-out curve, transform and opacity, one entrance at most.
- **Browser surfaces (impeccable craft floor):** default text selection, caret, scrollbars, focus ring and
  proportional digits in tables give away an assembled page → the kit themes `::selection`, `caret-color`,
  `:focus-visible`, scrollbars and `tabular-nums` from the theme.
- **States:** a screen with only the happy path → loading, empty, error, disabled and success for every
  list and action (design-system §8).
- **Decoration standing in for structure (impeccable craft floor):**
  - a coloured stripe on one side of a card, row or callout (`border-left` of 2 px or more) → a tag, an
    icon or the section header says what kind it is (MA42);
  - hard offset shadows (`4px 4px 0`) and zero-offset coloured halos → the theme's surfaces, and glass only
    for floating controls (MA43, MA32);
  - a small "eyebrow" label above a heading → the heading alone (MA44);
  - section numbers (01 / 02 / 03) where order means nothing → none;
  - sparklines and progress rings in place of a number → the number, its change and the period.
- **Glass as decoration:** blur on cards, rows or the page, glass on glass → solid surfaces, glass only on
  floating controls as a token material ([materials-and-trends.md](materials-and-trends.md) §2).
- **Trend chasing:** bento pages, mesh gradients, 3D orbs, neumorphism, parallax → the decisions in
  [materials-and-trends.md](materials-and-trends.md) §3.

## 5. The polish pass ("make it premium / cleaner / nicer")

Polish refines what is there. It is never a redesign in disguise. If the concept is wrong (the wrong surface,
a dashboard where a list belongs), say so and propose a rework ([rework.md](rework.md)) instead.
Adapted from impeccable's polish pass (Apache 2.0) for Mini Apps **[Heuristic]**.

**1. Evidence first.** Open every screen in the stand in both themes, iOS and Android, at 320 and 390 px.
Read computed values (gaps, sizes, colours) with devtools instead of judging from the screenshot. Run the
lint. Use the app as a user would, including errors (stand Network) and long content.

**2. Classify each problem before fixing it.** The class decides where the fix goes:

| Class | Example | Fix at |
|---|---|---|
| Kit defect | a component's own `margin: 0` eats the stack gap | the kit, with a test (helps every app) |
| Missing token | the same 20 px radius written in three places | a token in the app's style, or a kit token if it is general |
| One-off implementation | an own toggle next to the kit's `.tma-switch` | replace it with the kit component |
| Conceptual mismatch | Settings built as cards, Orders as a grouped list | the pattern the neighbouring screens use ([screen-patterns.md](screen-patterns.md)) |
| Local defect | a missing `alt`, a cut label | that line |

**3. Fix in this order,** and bring every screen to the same bar before perfecting one:
1. broken tasks, data loss, misleading states, inaccessible paths;
2. missing states: loading, empty, error, success, disabled, permission;
3. structure and hierarchy: native buttons, grouped lists, one primary action, one moment, the type scale;
4. copy: the first line of each screen, buttons that name the action, errors that name the fix;
5. colour roles, the style ([design-system.md](design-system.md) §9), materials;
6. icons, imagery and motion;
7. cleanup: dead styles, duplicated values, debug output.

**4. Quieter, not emptier.** When a screen is loud:
- lower weights (700 → 600, 600 → 500);
- fewer colours;
- flatter surfaces;
- shorter motion.

Keep the hierarchy and the one moment. Quiet without intent turns into grey text on white and a grid of
identical cards, which is just another template.

**5. Verify the whole path again:** both themes, both platforms, 320 and 669 px, large text, reduced motion
and transparency, a screen reader pass on one screen, every Network setting on one action. Then a source
diff with no accidental churn. A clean lint does not replace looking.

## 6. Checklist

- [ ] No tell from §2 on any screen.
- [ ] One moment per screen; the rest grouped and quiet.
- [ ] Copy without greetings, exclamation marks, hype or fake data.
- [ ] One icon set, no emoji in UI chrome or button labels.
- [ ] Browser surfaces themed; numbers tabular.
- [ ] `py -3 scripts/miniapp_lint.py <app> --strict` clean.

## Linter rules

`scripts/miniapp_lint.py` checks what is visible in code. Pattern-based: a clean report is static evidence,
not proof of how real clients render.

| Rule | Level | Catches | Source |
|---|---|---|---|
| MA01 bot-token | error | a bot token or `BOT_TOKEN` in client code | security §2 |
| MA02 unsafe-server | error | `initDataUnsafe` in server code | security §1 |
| MA03 native-dialog | error | `alert()`, `confirm()`, `prompt()` | G3 |
| MA04 script-order | error | `telegram-web-app.js` missing from `<head>` or not first | Official |
| MA05 raw-color | warning | colour literal outside `var()` fallbacks, `light-dark()`, `--tma-fb-*`, neutral alpha greys | G1 |
| MA06 vh | warning | `100vh` / `dvh` / `svh` outside a `var(--tg-viewport-*)` fallback | G2 |
| MA07 fixed-cta | warning | own fixed bottom button not marked `data-tma-fallback` | G3 |
| MA08 safe-area | warning | `requestFullscreen` with no safe-area insets in CSS | G6 |
| MA09 transition-all | warning | `transition: all`, `animate-pulse`, `animate-ping` | G4 |
| MA10 infinite | warning | infinite animation on a non-loader | G4 |
| MA11 gradient-text | warning | `background-clip: text` | §4 |
| MA12 glass-fallback | warning | `backdrop-filter` without a solid fallback | §3 |
| MA13 emoji-ui | warning | any Unicode emoji in visible markup or a UI string (including ★ and ⭐ in markup); `⭐ <amount>` only in MainButton / popup text | §3 |
| MA14 local-storage | warning | `localStorage`, `sessionStorage` | security §6 |
| MA15 version-gate | warning | a member newer than 6.0 used with no gate in the file (`isVersionAtLeast`, the kit's `has()`, or the third-party `@tma.js/sdk` `isAvailable()` / `ifAvailable()`) | webapp-api §2 |
| MA16 web-font | warning | `@font-face`, web-font CDNs | §3 |
| MA17 reduced-motion | warning | motion with no `prefers-reduced-motion` rule | G4 |
| MA18 ready | warning | `ready()` never called | Official |
| MA19 own-back | warning | `history.back()`, an own back button or an own sticky / fixed top bar | G3 |
| MA20 web-login | warning | Telegram login widget inside the app | security |
| MA21 hover-only | warning | content revealed only on `:hover` | G2 |
| MA22 small-text | warning | font size below 11 px | G5 |
| MA23 viewport-meta | warning | no `<meta name="viewport">` | G2 |
| MA24 label | warning | `<input>` without a label, `<img>` without `alt` | G5 |
| MA25 pay-form | error | own card fields (`autocomplete="cc-*"`, card number or CVV inputs) | payments §4 |
| MA26 client-price | warning | `price` / `amount` / `total` sent to a checkout, invoice or order endpoint | payments §2 |
| MA27 paid-unlock | warning | unlocking on invoice status `paid` without asking the server for the order | payments §3 |
| MA28 currency-label | warning | `XTR`, `Toncoin` or `12.5 TON` shown to users ("formerly Toncoin" is fine) | telegram-elements T1-T2 |
| MA29 trust-mark | error | an own verified or Premium badge (class, id, `aria-label`, `title`) | telegram-elements T7-T8 |
| MA30 nav-drawer | warning | hamburger, drawer, sidebar or off-canvas navigation | components §3, rework §3 |
| MA31 hype-copy | warning | greetings, `!` in headings and buttons, hype words ("unleash", "crush it", "!!") | §4 |
| MA32 glow | warning | coloured shadows with a blur of 20 px or more; `:hover` scale effects | §4 |
| MA33 client-identity | error | `initDataUnsafe` sent to the server instead of the raw `initData` | security §1 |
| MA34 caps-label | warning | `text-transform: uppercase` with `letter-spacing` (tracked caps labels) | §4 |
| MA35 nested-surface | warning | a surface inside a surface in markup: card in card, list or key-value block inside a card, `*-card-inner`, panels in panels | design-system §3 |
| MA36 haptic-stream | warning | `impactOccurred` / `selectionChanged` / `tma.haptic.*` inside scroll, pointermove or input handlers, timers or animation frames | haptics-and-device §1 |
| MA37 sensor-stop | warning | `Accelerometer` / `Gyroscope` / `DeviceOrientation.start` or `tma.motion()` with no stop in the file | haptics-and-device §2 |
| MA38 icon-name | warning | a `<button>` or `<a>` holding only an icon, with no `aria-label`, `title` or hidden text | accessibility-and-language §2 |
| MA39 physical-side | warning | `margin-left`, `padding-right`, `text-align: left`, `float: right` in app CSS | accessibility-and-language §8 |
| MA40 number-input | warning | `<input type="number">` or `type: 'number'` | forms-and-data §1 |
| MA41 autofocus | warning | `autofocus` / `autoFocus` on an input, textarea or select | forms-and-data §2 |
| MA42 side-stripe | warning | `border-left` / `border-right` / `border-inline-start` of 2 px or more on a card, row, callout or alert | §4 |
| MA43 hard-shadow | warning | a `box-shadow` with an offset and no blur (`4px 4px 0`) | §4 |
| MA44 eyebrow | warning | an eyebrow, kicker or overline label class above a heading | §4 |
