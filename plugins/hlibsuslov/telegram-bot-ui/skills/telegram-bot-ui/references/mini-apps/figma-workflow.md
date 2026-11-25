---
summary: "How an agent reads a Figma file through the Figma MCP and turns it into rules, tokens or screens without copying what it must not; read when given a Figma design or kit."
verified: "2026-11-24"
bot_api: "10.5"
---

# Reading designs through the Figma MCP

How an agent reads a Figma file (a design kit, or the person's own Mini App design) and turns it into rules,
kit tokens or screens, without copying what it must not copy. This is how
[native-anatomy.md](native-anatomy.md) and `data/mini-apps/design-sources.json` were made. Labels:
**[Official]** Figma MCP documentation; **[Heuristic]** this skill's practice.

## 1. Which file, which rights

| File | What it gives | What not to take |
|---|---|---|
| Apple iOS and iPadOS 27 kit (Community 1651309003795292092) | sizes, paddings, radii, type roles, Liquid Glass recipes, component states, layout margins (also for the foldable iPhone) | SF Symbols and other artwork, product bezels (Apple licence) |
| Telegram Mini Apps UI Kit (Community) | `themeParams` roles, component inventory, iOS and Android pairs, how Telegram composes screens (Wallet, City Explorer, Job Finder) | its pre-Liquid-Glass chrome as the current look |
| The person's own design file | their screens, brand colour, content, any decisions they made | nothing to avoid; still map colours to theme roles |
| Paid kits (Appetite UI and others) | only what the person may share | values and screens copied into this skill (licence) |

Community files are read from the person's own copy (a draft): the MCP needs a file key in a `/design/` URL.
Record each file key and the date read in `design-sources.json`; never claim a file was read when it was not.

## 2. The reading order

1. **Session.** `create_session` with the file key and a one-line goal, once per task; pass its id to every
   later call **[Official]**.
2. **Pages.** `get_metadata` without a node id lists the pages. Pick the pages for the task (for a kit:
   Layout Guides, Lists, Buttons, Tab Bars, Sheets, Alerts, Empty States, Text Fields, Materials).
3. **Structure.** `get_metadata` on a page gives components, variants and their sizes in an XML tree. Sizes
   alone already answer many questions: row heights, button heights, image sizes, safe areas. Large pages
   overflow; save the output and query it with a script rather than reading it whole.
4. **Values.** Load the `figma-design-to-code` skill, then `get_design_context` on one component set or one
   variant. The reference code carries paddings, radii, font sizes, weights, line heights, letter spacing,
   colours by variable name, shadows and the component's documentation link. Ask for the screenshot with it.
5. **Tokens.** `get_variable_defs` on a node lists the variables it uses (colour, size, spacing); use it to name
   values by role ("labels/secondary"), not by hex.
6. **Look.** `get_screenshot` for whole screens or templates (download the PNG with curl, then view it): how
   parts are composed is learnt from screens, not from components.
7. **Write down.** Each measurement becomes a sentence with its source label and, where the kit differs, the
   change or the reason to differ. Put numbers in `design-sources.json`, rules in the references, CSS in the kit.

## 3. Translating values into the kit

- **Colours become roles.** `labels/secondary` → `--tma-hint` / `--tma-subtitle`; `fills/tertiary` →
  `--tma-fill`; `accents/blue` → `--tma-accent` (the theme's `button_color`); a kit hex only as a fallback
  in `--tma-fb-*`. Never paste a design's hex into a component (lint MA05).
- **Type becomes the scale.** Every size maps to a role of the iOS 27 scale (`.tma-text-<role>`); weights
  400 / 500 / 600 / 700 only; letter spacing comes from the system font, not from CSS.
- **Sizes become tokens.** Row 52 / 68, margins 16, radii (group 26, inner 14, sheet 38) live in
  `tma.css` custom properties; a new value enters as a token first.
- **Glass stays a recipe.** Figma draws Liquid Glass with layered fills and blend modes; the web
  approximation is `.tma-glass` (backdrop blur, saturation, hairline highlights) with a solid fallback, on
  floating controls only.
- **Symbols become own icons.** An SF Symbol name maps to the kit icon or the Lucide name in
  `data/mini-apps/icons.json`; the symbol's artwork is never exported.
- **Platform pairs stay pairs.** iOS and Android variants become `:root[data-tma-platform="android"]` rules,
  not two components.

## 4. The person's own design

When the person shares a Figma link for their Mini App:

1. Read the screens (metadata, then design context per screen) and list the content types and actions.
2. Map every element to the catalogue (`data/mini-apps/components.json`); anything without a match is either a
   new kit part (add it, with the gallery and a test) or a web pattern to replace ([rework.md](rework.md) §3).
3. Take their brand colour as `--tma-brand` through a style profile (one moment per screen); surfaces, text,
   buttons and links follow the user's Telegram theme regardless of the mock-up's colours.
4. Their own header, tab bar or bottom button in the mock-up become Telegram's header, the kit's floating tab
   bar and the MainButton; say so in the report.
5. Build, lint, compare with the screenshot in the stand at the same width, list the deliberate differences.

## 5. Keeping it current

- Re-read the iOS kit when Apple ships a new one: the change log page lists what moved. Check row heights,
  button heights, header styles, sheet shape, glass recipe and the system colours first.
- Re-read the Telegram kit when Telegram updates it, and check the live Design Guidelines
  ([telegram-design-guidelines.md](telegram-design-guidelines.md)).
- Each re-read updates the date in [design-sources.md](design-sources.md), `design-sources.json` and
  [native-anatomy.md](native-anatomy.md); kit changes go through the gallery, the lint and the stand.
