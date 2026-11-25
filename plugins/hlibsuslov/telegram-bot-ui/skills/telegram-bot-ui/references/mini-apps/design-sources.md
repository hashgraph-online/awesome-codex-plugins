---
summary: "What the skill takes from each Mini App design source (Telegram guidelines, iOS 27 kit, UI kit, dark-fintech direction): colour, type, shape, Liquid Glass; read to see where design values come from."
verified: "2026-11-24"
bot_api: "10.5"
---

# Mini App design sources: what to take from each

How the skill turns its design references into one Mini App design system: Telegram for structure and
compatibility, iOS 27 for Liquid Glass and proportions, a dark-fintech direction for the look. Values were read
through the Figma MCP on **2026-11-23** and are in `data/mini-apps/design-sources.json`.

Labels: **[Official]** core.telegram.org/bots/webapps; **[iOS27]** Apple iOS and iPadOS 27 Figma kit;
**[TgKit]** Telegram Mini Apps UI Kit (Community); **[Heuristic]** this skill's decision.

## 1. Sources and their limits

| Source | Read? | Use it for | Do not use it for |
|---|---|---|---|
| Telegram Design Guidelines | yes | hard rules, rule by rule in [telegram-design-guidelines.md](telegram-design-guidelines.md) | — |
| Live `themeParams` | at runtime | every surface, text and accent colour | — |
| Telegram Mini Apps UI Kit | yes; the three template apps read 2026-11-24 ([native-anatomy.md](native-anatomy.md) §9) | `themeParams` role names, component inventory, iOS/Android pairs, cell slots, list layouts | chrome, radii, type scale: it predates the 2025-26 Liquid Glass redesign |
| iOS and iPadOS 27 kit | yes; components re-read page by page 2026-11-24 ([native-anatomy.md](native-anatomy.md)) | Liquid Glass placement, capsule shapes, tab bar, sheets, list rows, type scale, system colours as fallbacks | Mini App chrome (Telegram draws it); icons and images (Apple licence) |
| Telegram UI (community 1348989725141777736) | **no** | — | — |
| Appetite UI | **no** (no access; paid kit) | the general dark-fintech direction only, never its values | tokens, screens, screenshots: licence forbids redistribution |

Never describe an unread source as studied. When one becomes readable, add its findings here with the date.

## 2. Who draws what

Telegram draws the header (close or back, title, menu) and the bottom bar (MainButton, SecondaryButton). On iOS
they are already Liquid Glass. The app draws everything between them and colours the chrome with
`setHeaderColor`, `setBackgroundColor` and `setBottomBarColor`. **[Official]** Consequences:

- No own back arrow, close button or fixed bottom CTA while the native one is available.
- The app's own floating controls (a tab bar, a floating icon button) must look like siblings of Telegram's
  glass chrome, not like a web navbar.
- No hard-coded header heights: pad with `--tg-safe-area-inset-*` plus `--tg-content-safe-area-inset-*`.

## 3. Colour

Theme first. iOS 27 values are only fallbacks for roles Telegram does not send and for the browser preview.

| Role | Source | Fallback light / dark [iOS27] |
|---|---|---|
| grouped page | `--tg-theme-secondary-bg-color` | `#f2f2f7` / `#000000` |
| cell, card | `--tg-theme-section-bg-color` | `#ffffff` / `#1c1c1e` |
| raised inside a card | `color-mix()` from section bg toward text, 4-6 % | `#f2f2f7` / `#2c2c2e` |
| text / secondary text | `--tg-theme-text-color` / `--tg-theme-hint-color` | `#000` / `rgb(235 235 245/.7)` |
| separator | `--tg-theme-section-separator-color` | `rgb(0 0 0/.12)` / `rgb(255 255 255/.17)` |
| gray fill (segment track, gray button) | `color-mix(text 8 %)` | `rgb(118 118 128/.12)` / `/.24` |
| tonal fill (bezeled button, icon tint) | `color-mix(button_color 12 %)` | — |
| success / danger | `light-dark()` pair / `--tg-theme-destructive-text-color` | `#34c759`/`#30d158`, `#ff383c`/`#ff4245` |

Rules **[Heuristic]**: one accent (the theme button colour) used for the primary action, selection and links;
green and red only for direction of change and always with a sign or arrow; surfaces never tinted toward a hue.
Dark is designed first for the fintech direction, light is checked on every screen.

## 4. Type

System font only (`system-ui`, `-apple-system`, Roboto on Android). iOS 27 scale [iOS27], used for both
platforms with Roboto metrics on Android:

| Role | px / line | Weight | Use |
|---|---|---|---|
| Large Title | 34/41 | Regular-Bold | screen title on a tab root |
| Title 1 | 28/34 | Semibold | hero figure label, sheet title in onboarding |
| Title 2 | 22/28 | Semibold | section hero |
| Title 3 | 20/25 | Semibold | section header (large) |
| Headline | 17/22 | Semibold | cell title emphasis |
| Body | 17/22 | Regular | cell title, text |
| Callout | 16/21 | Regular | secondary blocks |
| Subheadline | 15/20 | Regular | cell subtitle |
| Footnote | 13/18 | Regular | section footer, legal |
| Caption 1 / 2 | 12/16, 11/13 | Regular | tab labels, meta; nothing below 11 |

Hero figures (balances, prices) go above the scale: 48-64 px Semibold, `tabular-nums`, fraction and currency in
the hint colour at about 60 % of the integer size. Follow the user's text size: on iOS WebKit
`html{font:-apple-system-body}` then size in `rem` **[Heuristic, check on device]**.

## 5. Shape, spacing, touch [iOS27]

- Side margin 16. Grouped lists: inset cards on the grouped page, 16 px from the edges.
- Row heights 52 (one line) and 68 (title + subtitle), horizontal padding 16. Separators start at the text column.
- Capsules for buttons, chips, segmented controls and the tab bar; radius = half the height. Cards and inset
  groups use a large continuous radius (about 24-26 on iPhone); nested radius = outer − padding.
- Sheets: top radius 38, grabber 60×4, header = glass close on the left, title in the centre, prominent confirm
  on the right. Detents medium and large.
- Button heights 28 / 34 / 50. Primary actions in content use 50; MainButton replaces a full-width primary at the bottom.
- Touch targets ≥ 44 px; tab hit area 40 inside a 48 capsule.
- Android: same structure, Material proportions (48 dp targets), full-width sections are acceptable **[TgKit]**.

## 6. Liquid Glass on the web

The kit now builds glass from tokens with three levels and records the values in `design-sources.json` →
`web_materials`; how to use and update it: [materials-and-trends.md](materials-and-trends.md) §2. The recipe below
is the regular level written out.

The Figma effect (frost 6 regular / 16 medium-large, refraction .7, depth 30, dispersion .2) is a native shader.
CSS can only approximate the frost and the rim light. Do not fake refraction or dispersion with SVG displacement
filters: costly, inconsistent across WebViews. **[Heuristic]**

```css
.glass {
  background: color-mix(in srgb, var(--tg-theme-bg-color, #1c1c1e) 62%, transparent);
  -webkit-backdrop-filter: blur(16px) saturate(1.8);
  backdrop-filter: blur(16px) saturate(1.8);
  border-radius: 999px;
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / .35),   /* top rim light */
    inset 0 -1px 0 rgb(0 0 0 / .08),        /* bottom rim */
    0 8px 24px rgb(0 0 0 / .14);            /* lift over content */
}
@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .glass { background: var(--tg-theme-section-bg-color); -webkit-backdrop-filter: none; backdrop-filter: none; }
}
```

Where glass is allowed: the app's floating tab bar (48 capsule, 2-5 tabs, selected tab = fill capsule + accent),
a separate floating circle next to it (search or one prominent action), floating icon buttons over media,
sticky segmented controls over scrolling content. Everything else is solid: cells, cards, sheets' content,
text blocks. Add a scroll-edge fade (≈ 10 px blur band, mask gradient) under sticky glass so text does not
collide with it. Turn glass off on Android performance class LOW and when `backdrop-filter` is unsupported.

## 7. Dark-fintech direction (Walt-like)

Derived from the reference screenshots and the principles above, not from any paid kit:

- Near-black grouped page, cells one step lighter, no gradients on surfaces.
- One large figure per screen (balance, price), its change as a tinted pill with sign and period.
- Quick actions: 2-4 equal tiles, icon in an accent circle, verb label.
- One rich moment per screen: a promo banner, a 3D sticker or a chart. The rest stays quiet.
- Charts: one line, colour by direction, muted grid, segmented period control under it.
- Asset rows: 40-48 avatar, title, `ticker · price` subtitle, value on the right in `tabular-nums`.

## 8. Checklist before a screen ships

- [ ] Every colour resolves from a `--tg-theme-*` variable or a derived `color-mix()`; fallbacks only.
- [ ] Light and dark checked; Increased Contrast does not break text on glass.
- [ ] No own header, back or fixed CTA; native buttons configured per screen.
- [ ] Safe area and content safe area applied in fullscreen and compact modes.
- [ ] Glass only on floating controls, with the reduced-transparency fallback.
- [ ] Type from the scale, nothing under 11 px, figures in `tabular-nums`.
- [ ] Capsules and radii consistent; nested radii add up.
- [ ] Android check: Roboto metrics, 48 dp targets, glass off on LOW.
