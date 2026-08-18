---
name: third-party-integrations
description: Use when a val talks to an external service — Slack, Discord, Telegram, Stripe, GitHub, Gmail, Google Sheets, Postgres/Supabase/Upstash/Neon, browser automation (Playwright, Browserbase, Kernel, Steel), web scraping, PDF generation, push notifications, RSS, or any other third-party API. Covers the required workflow (fetch the Val Town guide, get credentials, test, store secrets) and the catalog of available guides.
triggers: [integration, third-party, external, service, api, slack, discord, telegram, stripe, github, gmail, sheets, google, neon, postgres, supabase, upstash, database, playwright, browser, browserbase, kernel, steel, browserless, scraping, scrape, pdf, rss, push, notification, webhook]
---

# Third-Party Integrations

When a val uses any external service, follow this order — do not skip steps and do not write integration code from training-data memory alone. Val Town's guides have platform-specific patterns and required workarounds that won't be in your training data.

## Workflow

1. **Fetch the Val Town guide first.** Guides live under `https://docs.val.town/guides/`, but the slug isn't always just the service name — some are grouped under a category (e.g. `databases/neon-postgres/`, `browser-automation/kernel/`) or live on a sub-page (`slack/agent/`). Don't guess the URL: fetch the docs sitemap at `https://docs.val.town/sitemap-0.xml` (it lists every docs URL), find the `guides/…` entry that matches the service, and fetch that page before writing any integration code.
2. **Help the user get credentials.** Provide direct links to create API keys or step-by-step OAuth setup instructions. Don't make the user hunt.
3. **Test the connection** with a minimal script (a single fetch / SDK call that returns one record) before building features on top. This isolates auth/setup problems from feature bugs.
4. **Store secrets in env vars.** Use `Deno.env.get("KEY_NAME")` to read them, and document the required env vars in the README so the user (or anyone remixing the val) knows what to set. Whenever you reference an env var the user needs to set, show the raw, full URL to the prefilled Val Town env var editor on its own line, in this exact format: `👉 Add KEY_NAME here: https://www.val.town/x/HANDLE/VAL_NAME/environment-variables?key=KEY_NAME`. Keep the URL visible (not hidden behind link text) — it's the call-to-action.

## Available guides

Services with dedicated guides today — not exhaustive, so use the sitemap from step 1 as the current source of truth:

- **Messaging / chat:** Slack, Discord, Telegram
- **Payments:** Stripe
- **Email:** Gmail (for sending via a user's account; for built-in mail use `std/email` instead — see the `email` skill)
- **Google:** Google Sheets
- **External databases:** Neon Postgres, Supabase, Upstash (for SQLite use built-in `std/sqlite` instead — see the `sqlite-storage` skill)
- **Browser automation:** Kernel (recommended for Playwright), Browserbase, Steel, Browserless
- **Source control / webhooks:** GitHub (including webhooks)
- **Content / output:** RSS feeds, PDF generation, web scraping
- **Notifications:** push notifications
- **Auth:** OAuth providers (for logging in with a Val Town account use `std/oauth` instead)

## Why this matters

Integration code is the most common place models hallucinate. APIs change, auth flows get reworked, and platform constraints (no filesystem, no subprocess) break naive approaches. The Val Town guide is the source of truth for what currently works on the platform.
