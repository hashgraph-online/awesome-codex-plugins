# Current OpenAI notes

Last reviewed: 2026-09-18.

These notes are documentation context, not hard-coded logic. Re-check official docs when publishing a release.

- Codex usage varies with model, task complexity, context, reasoning, speed, and tools.
- Plus/Pro can share an agentic allowance across supported features such as Codex and ChatGPT Work.
- Official pricing currently presents estimated local messages per five-hour window rather than a guaranteed fixed message count.
- Current model guidance: Luna for clear/repeatable work, Terra for everyday work, Sol for complex/open-ended work, Astra for hardest multi-step/tool work.
- Higher reasoning effort consumes more time/tokens; official guidance recommends using the lowest effort that achieves the result.
- `/status` can show session/configuration information; account usage dashboard is the source for current limits/reset state.

Official sources:
- https://developers.openai.com/docs/pricing
- https://developers.openai.com/docs/models
- https://developers.openai.com/docs/build-skills
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro
