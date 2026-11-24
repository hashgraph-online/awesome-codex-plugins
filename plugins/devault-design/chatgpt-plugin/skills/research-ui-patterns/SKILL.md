---
name: research-ui-patterns
description: Research how real products design a screen, flow or pattern using Devault's library, and report findings with the screens that support them. Use when the user asks how apps or websites handle something (onboarding, paywalls, checkout, empty states, pricing pages), wants UI references or examples, or wants a design decision grounded in real products.
---

Use this skill for questions such as "how do fintech apps handle onboarding?",
"show me paywall examples" or "what do good empty states have in common?".

## Steps

1. Pin down the subject: the pattern or screen type, and any platform (`ios`,
   `android`, `web`, `email`), industry or company the user named. If the
   request is too broad to search, for example "show me good design", ask one
   question to narrow it.
2. If you plan to filter by industry or screen type and are not sure of the
   value, call `list_taxonomy` once and use a value it returns.
3. For "how do products do X" questions, call `analyze_pattern` with the
   pattern as a short phrase, for example "paywall". Its statistics give the
   overall picture: how many screens, which platforms and industries, which
   components appear with the pattern, and the split between light and dark.
4. Call `search_screens` for specific examples. Use two to five keywords, not
   a sentence, and put constraints in the filters (`platform`, `industry`,
   `screen_type`, `brand`) instead of the query. If nothing matches, drop a
   word or a filter and try once more.
5. Look closer only where it helps. Call `get_screen_image` with a result's
   `view_token` for the two to four screens that matter most. A token works
   once and for five minutes; call `get_screen` with the `screen_id` for a
   fresh one. For tall captures such as emails and landing pages, pass
   `section` (`top`, `middle` or `bottom`).
6. To widen the search from one good example, call `get_similar_screens` with
   its `screen_id`.
7. For a single company, `get_brand_overview` shows what the library holds
   before you search with `brand`.

## What to report

- Start with the answer: the two to four things the examples have in common,
  or the main ways they differ.
- Support each point with screens you retrieved: the title, the company, and
  what to notice, each linked to its page (`url`).
- The images the tools return are for you to look at. The user does not see
  them, so describe what a screen shows and link it; do not say that a screen
  is shown above or attached.
- When you used `analyze_pattern`, give its numbers as returned.
- If the user said what they are building, end with what this suggests for
  their design.

## Rules

- Cite only screens returned in this conversation. Never invent a screen, a
  company's design or a statistic.
- If the library has little or nothing on the subject, say so.
- The screens are references for study. Do not present them as templates to
  copy, and do not say the companies shown are affiliated with Devault.
- Do not try to list or export the library. Each search is one page of
  results by design.
- If a tool says a limit was reached, tell the user and carry on with what you
  already have.
- An explicit instruction from the user takes priority over these steps.
