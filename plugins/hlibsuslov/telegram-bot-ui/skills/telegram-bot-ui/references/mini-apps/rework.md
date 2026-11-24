# Rework a Mini App into classic Telegram design

The procedure for "make our Mini App look and work like Telegram": a web-style app (own header, drawer,
gradients, a fixed CTA, emoji labels, its own palette) becomes a Telegram-native one without breaking its
logic. [orchestration.md](orchestration.md) §3 is the short version; this file is the full one, with the
tools, the translation table, the framework bridge and the acceptance score. Labels: **[Official]**,
**[API]**, **[Heuristic]**.

Worked example: `tests/fixtures/miniapp_rework/before` (a generated gym-booking app, lint 9 errors and 89
warnings) and `examples/mini-apps/rework` (the same app reworked on the kit by an agent that had only this
skill: 0 and 0, the full payment flow running in the stand with `--api rework/mock-api.json`).
`examples/mini-apps/rework/FRICTION.md` is that agent's log of where the skill fell short, and what was fixed.

## 1. The loop

1. **Freeze the contracts.** Write down what must not change: API routes and payloads, `startapp` values,
   CloudStorage keys, analytics events, the booking and payment logic. The rework changes how things look and
   which Telegram surfaces they use, not what they do.

   **Except stage 1.** A security or payment finding (MA02, MA25-MA27, MA33) means the contract itself is
   unsafe: the client sends a price or the user object, the server trusts it, the app unlocks on the invoice
   status. Change it, and change the app and the server in the same release:
   - the client sends ids and `Authorization: tma <initData>`; the server verifies `initData` and prices
     ([security.md](security.md), [payments.md](payments.md) §2);
   - the checkout answers `{order_id, link}`; add `GET /orders/<id>` for the app to watch;
   - during the rollout the server accepts the old body but ignores its `price` and `user`;
   - list every changed route in the report as "contract changed: why".

   A payment option the rules forbid is not kept "as is": digital goods priced in TON or a card form become
   Stars. A real TON flow moves to the bot's wallet features ([../wallet-and-ton.md](../wallet-and-ton.md));
   the report says it was removed from the app and why.
2. **Plan.** `py -3 scripts/miniapp_rework.py plan <app>` prints:
   - the lint baseline;
   - every finding sorted into six stages, each with the Telegram replacement, the kit part and the reference;
   - patterns the lint does not judge: stat-card grids, nested cards, ribbons, price pills, sticky top bars,
     carousels, modals, toasts, Tailwind or shadcn tokens;
   - a colour map (each literal → a kit role, the brand candidate, what to drop);
   - a type map (each size → a type role).

   Keep the output as the baseline (`--json` for a diff later).
3. **Describe the screens.** One screen JSON per list or detail screen, before and after, and
   `py -3 scripts/miniapp_layout.py review <screen.json>` ([layout-rules.md](layout-rules.md)). The keys and
   values are fixed (`miniapp_layout.py schema`); an unknown key or value fails with exit 2. Describe every
   key that applies: the review only judges what is written, so a thin description proves little.
   Map the app's screens to tab roots (2-5) and level-2 screens; give each screen one primary action
   (MainButton or none). The MainButton hides the floating tab bar while it shows
   ([components.md](components.md) §3), so a root tab has no primary action: "Subscribe" belongs on a
   level-2 plan screen, not on the Membership tab.
4. **Fix in stage order**: §2. Structure before style: a screen with native chrome and grouped lists but the
   old colours is a better intermediate state than a recoloured web page.
5. **Rebuild on the kit**: `_kit/tma.css`, `_kit/tma.ts`, `_kit/tg-values.ts`, `_kit/icons.svg`. For a React,
   Vue or Tailwind app keep the framework and bridge the tokens (§6); do not rewrite the stack.
6. **Check**:
   - `miniapp_lint.py <app> --strict` (0 findings) and `miniapp_layout.py review` for each screen JSON;
   - the preview matrix (`preview_miniapp.py <app> --serve 8790`, `/?view=matrix`) in both themes and both
     platforms;
   - the server flows in the stand: `--api mock.json` answers the app's requests (checkout, order status)
     and the Invoice control (`?invoice=paid|failed|pending|cancelled`) drives the order the mock returns;
     walk each outcome to its screen;
   - unit tests of the logic that had to move (storage, payments).

   The app is served at `/app/<folder>/index.html` under the stand's root, for curl checks.
7. **Score** with §7 and **report** with §8.

## 2. Stages

| Stage | What | Typical fixes |
|---|---|---|
| 1. Security and payments | MA01-MA02, MA25-MA27, MA33, MA20 | raw `initData` to the server; no card fields; the server prices; unlock from the order |
| 2. Native behaviour | MA03-MA04, MA06-MA08, MA14-MA15, MA18-MA19, MA23, MA30, sticky top bars, modals, toasts, top tabs | BackButton, MainButton, tab bar, `showConfirm`, CloudStorage, `ready()` |
| 3. Telegram's values and trust | MA28-MA29 | `⭐ 250`, `12.5 GRAM`, no own verified marks ([telegram-elements.md](telegram-elements.md)) |
| 4. Theme and type | MA05, MA16, MA22, Tailwind / shadcn tokens | colour map → roles, type map → roles, system font |
| 5. Slop | MA09-MA13, MA21, MA31-MA32, stat cards, nested cards, ribbons, price pills, carousels | grouped lists, one moment, plain copy, line icons |
| 6. Accessibility and language | MA17, MA24, MA38, MA39 | labels, `alt`, icon names, reduced motion, focus, `tma.locale()`, logical sides ([accessibility-and-language.md](accessibility-and-language.md)) |

States (loading, empty, error, success) are not detectable from code: add them for every list and action
whatever the plan says ([design-system.md](design-system.md) §8). Data that never loads (constants in the
bundle) needs no skeleton; its lists still need an empty state, and every action that calls a server needs
pending, error and success.

## 3. Translation table: web pattern → Telegram

The full table with kit parts and references is `data/mini-apps/rework-map.json` (`rules` and `patterns`);
the plan prints the rows that apply. The ones every rework meets:

| Web pattern | Telegram-native replacement |
|---|---|
| Own top bar with logo, back arrow, burger | Telegram's header (colour via `tma.chrome`), a large title in the page, BackButton on level 2 |
| Hamburger / drawer / sidebar | floating tab bar with 2-5 roots; everything else is a row that pushes a screen |
| Fixed "Book now" button | MainButton (`tma.mainButton`), text says what happens and the price: `Book HIIT · ⭐ 120` |
| Hero banner with greeting and stat cards | large title + one figure (the number that matters) + rows or a key-value list |
| Grid of cards with images, pills and hover details | list rows with thumbnails or a 2-column tile grid by the entity's ratio (layout rules), price as text, details on the detail screen |
| Plans as three bordered cards with a ribbon | plan cards (`.tma-plan`, L25): one selected, a quiet tag, the MainButton names the plan and price |
| `alert` / `confirm` / modal | `showAlert` / `showConfirm` / `showPopup`; content in a bottom sheet |
| Toast library | snackbar + haptic |
| `localStorage` | CloudStorage (synced) or DeviceStorage; secrets in SecureStorage |
| Card form, `openInvoice` with a client price | `tma.pay(link)` with a server-created invoice, `tma.watchOrder()` |
| `XTR` / `TON` amounts, own verified tick | `⭐ 250`, `12.5 GRAM`, trust in words |
| A digital good priced in TON, "Pay with Toncoin" | Stars in the app; a TON flow, if the product needs one, through the bot's wallet features |
| A full item hidden, or only greyed by colour | listed, `aria-disabled="true"` (the kit dims it), the reason in text, the MainButton says why |
| Emoji in headings, nav and buttons | line icons from the kit; text labels |
| Web font | the system font |

## 4. Colours and type

- **Colours.** Take the plan's colour map literally first, then review it on screen:
  - neutrals become surface, page, text, hint and separator roles;
  - red and green become danger and success;
  - decoration (gradients, glows, shadows, filters) is dropped.
  - The most used saturated colour is the **brand candidate**: the project's own colour, kept (never swapped
    for a palette the agent prefers). It keeps one moment per screen (hero, promo) through a style profile:
    the plan prints the `style.json` to check with `miniapp_style.py check`. Buttons and links take the
    user's theme (`--tma-accent`, `--tma-link`), never the brand **[Official: G1]**. A project with no colour
    of its own picks a named palette ([design-system.md](design-system.md) §9.4).
- **Surfaces.** One level: flatten cards in cards, stat-card grids and tinted panels into one grouped list or
  one card with rows (design-system §3, lint MA35).
- **Emoji and icons.** Every emoji goes: icons from the kit or one open SVG library (Lucide first,
  [components.md](components.md) §6c), the Stars sign as the SVG glyph.
- **Dark mode.** Delete the app's dark palette: the theme comes from Telegram. A literal dark surface is
  always wrong.
- **Type.** Each size maps to the nearest iOS 27 role (`.tma-text-<role>`); nothing below caption2 (11 px).
  Headings: one large title per root screen, title3 or headline for sections; weights 400, 500 and 600 only.

## 5. Copy

- The first line of a screen says what it is: "Classes", "Membership", not "Unleash your potential".
- Buttons say what happens, with the object and the price: "Book HIIT · ⭐ 120", "Join Pro · ⭐ 450 / month".
- No greetings, exclamation marks, "!!", rocket or fire emoji, invented progress ("+340%").
- Numbers come from data, formatted by the kit (tabular figures, Stars and grams by `tg-values.ts`).
- Dialogs ask a question and name both outcomes: "Book HIIT Blast at 07:00?" with "Book" and "Cancel".

## 6. React, Vue, Tailwind, shadcn/ui

Keep the stack and swap the tokens:

- **shadcn/ui.** Load `_kit/tma.css` and then `_kit/tma-bridge.css` after the app's token file. Delete the
  app's `:root` and `.dark` palettes. Tailwind v4 needs nothing else. Tailwind v3 keeps HSL triplets
  (`hsl(var(--primary))`): first change `tailwind.config` colours to `var(--primary)`.
- **Tailwind classes.** Replace palette classes with the bridge names: `bg-white` → `bg-tg-surface`,
  `text-gray-500` → `text-tg-hint`, `bg-indigo-600` on a button → the MainButton, or `bg-tg-accent` inside
  content. Same for radius (`rounded-tg-group`) and the font (`font-sans` is the system font).
- **React.** Use the React example's `kit.tsx` hooks or `@tma.js/sdk-react` for the MainButton, BackButton
  and theme; keep components, replace their markup with the kit classes or the bridged tokens.
- **Native first.** A component library's dialog, toast, drawer or date picker is still a web pattern: replace
  it per §3 even when it is themed.

## 7. Acceptance: is it classic Telegram?

Score every item pass or fail, with the evidence named. **Classic Telegram** = groups A, B and G all pass,
and at least 14 of 16 items overall. Anything less is "improved", not "Telegram-native".

| # | Group | Item | Evidence |
|---|---|---|---|
| R1 | A chrome | no own header, back control or drawer; Telegram's header coloured | lint MA19, MA30; plan has no sticky-header |
| R2 | A chrome | the screen's primary action is the MainButton (or none) | code; preview |
| R3 | A chrome | BackButton on every level-2 screen, one navigation stack | preview: push and back |
| R4 | A chrome | header, background and bottom bar colours set before `ready()` | code; stand log |
| R5 | B theme | no literal colours outside the kit fallbacks; brand on one moment | lint MA05 = 0; style check |
| R6 | B theme | readable in light, dark and a custom theme, iOS and Android | preview matrix |
| R7 | B theme | system font, type roles only, nothing below 11 px | lint MA16, MA22; type map |
| R8 | C structure | grouped lists for data; no cards in cards, no stat-card grids | plan patterns = 0 |
| R9 | C structure | each list and detail screen passes `miniapp_layout.py review` | review output |
| R10 | C structure | one moment per screen (figure, hero, promo or chart) | screenshot |
| R11 | D states | loading, empty, error with retry, success for every list and action | code; stand |
| R12 | E values | Stars, grams and gifts as Telegram shows them; no own trust marks | lint MA28, MA29 |
| R13 | F copy | plain titles and buttons that name the action and price | lint MA31; read-through |
| R14 | G security | raw `initData` to the server, verified there | lint MA02, MA33; server code |
| R15 | G payments | server prices, invoice link, unlock from the order | lint MA25-MA27 |
| R16 | H evidence | lint `--strict` clean, unit tests, matrix screenshots | command output |

## 8. Report

Before and after lint counts; the plan's stages with what changed per screen; contracts changed and why
(stage 1); options removed and why; the score from §7 with the failing items; what was left alone and why;
inputs that are missing and block a rule (a terms URL for the payment footnote, a support handle, a
waitlist API); evidence level (lint, review, mock preview, test server, devices) and what was not verified.
