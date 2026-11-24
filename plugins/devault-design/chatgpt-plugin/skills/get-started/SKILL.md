---
name: get-started
description: Introduce the Devault plugin and get a first result. Use when the user has just installed or connected Devault, asks what Devault can do here, or asks how to start.
---

Use this skill when the user is new to the Devault plugin or asks what it can do.

1. Say in two or three sentences what Devault is: a library of UI design
   references (screens from real websites and apps, user flows, marketing
   emails, redesign histories and original concepts), and a library of
   ready-made design systems.
2. Offer three things to try, in the user's own field if you know it:
   - Find references: "Find onboarding screens from fintech apps."
   - Study a pattern: "How do apps design paywalls?"
   - Get a design system: "Get a dark dashboard design system as Tailwind tokens."
3. If the user picks one, or has already asked for something specific, do it
   straight away with the matching tool: `search_screens`, `analyze_pattern`
   or `get_style`.

What to know before the first call:

- Devault works with the user's own Devault account. If a tool reports that
  the account is not connected, or that its plan does not include these tools,
  say so plainly and stop. Do not suggest a way around it.
- Every tool only reads. Nothing here changes the user's account.
- `search_screens` returns one page of results. To see different results,
  change the query or the filters; there is no next page.
- Images are counted per day. Fetch a larger image with `get_screen_image`
  only for the screens worth a closer look.
- The images the tools return are for you to look at. The user does not see
  them. Describe what a screen shows and link it by its `url`, which opens the
  screen on devault.design; do not say that a screen is shown above.

Do not describe a screen you have not retrieved, and do not say that the
companies shown endorse Devault or work with it.
