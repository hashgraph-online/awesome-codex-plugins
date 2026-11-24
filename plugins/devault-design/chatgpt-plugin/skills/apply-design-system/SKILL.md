---
name: apply-design-system
description: Find a ready-made design system in Devault's DESIGN.md library and deliver it in the format the user's project needs. Use when the user wants a palette, design tokens, a theme, a DESIGN.md file or a starting visual style for a build, in Tailwind, CSS variables, shadcn/ui, design tokens, Figma variables, SwiftUI or Android.
---

Use this skill when the user wants a design system or tokens to build with,
for example "give me a dark fintech theme for Tailwind" or "I need a DESIGN.md
for a warm editorial site".

## Steps

1. Work out two things: the feel the user wants (for example "dark saas
   dashboard" or "warm editorial") and the format. The formats are
   `design-md`, `tailwind`, `css`, `shadcn`, `tokens`, `figma`, `swiftui`,
   `android` and `image-prompt`. If the user's stack makes the format obvious,
   use it. Otherwise ask, or use `design-md`.
2. Call `get_style` with `query` set to the feel and `format` set to the
   format. If the user named an exact system, or pasted a link to a page under
   devault.design/design-md, pass its slug as `style` instead.
3. If the user wants to choose from several, call `list_styles`, with a
   `category` if they named one, and show the names and taglines. Fetch the one
   they pick with `get_style`.
4. To look at the design the system was derived from, call `get_screen_image`
   with the `view_token` from the `get_style` result. The image is for you:
   describe it, and point the user to the system's page (`url`) to see it.

## What to deliver

- The system's name, one line on its character, and its page (`url`).
- The `content` exactly as returned, in a code block, ready to paste. Do not
  rename tokens or change colour values.
- The contrast results that matter (`contrast`): which text colours pass on
  which surfaces, and any pair that fails.
- If `alternatives` came back, name one or two in case the first is not right.

## Rules

- Do not invent a system, a token or a contrast grade. Use what the tool
  returned.
- If nothing matches the query, say so and suggest a broader phrase.
- When you apply the system to the user's code, keep the token names from the
  export so that a later export stays compatible.
- An explicit instruction from the user takes priority over these steps.
