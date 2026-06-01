---
name: templates
description: Use when creating a new val and choosing which starter to fork. Covers the catalog of official starter templates, which project shape each one fits, and when forking an existing val is the better starting point.
triggers: [template, starter, remix, scaffold, boilerplate, new, create, fork, example]
---

# Templates

**Always start from a template** with `remix_val` — never build from scratch. Templates handle the boilerplate (entrypoints, imports, build config) and are kept up to date with Val Town's current patterns. Pick the closest match and customize from there.

## Catalog

Map the user's intent to the closest starter:

| Project shape | Template |
| --- | --- |
| Interactive web app (dashboard, SaaS, CRUD, form, anything with client-side state) | `templates/react-hono-starter` |
| Static page (landing page, link-in-bio, simple docs) | `templates/basic-html-starter` |
| AI agent built with OpenAI Agents SDK | `templates/openai-agents` |
| AI agent, model-agnostic (Vercel AI SDK) | `templates/vercel-ai-agent-demo` |
| Webhook + AI + dashboard (lead qualification, enrichment) | `templates/leads` |
| Webhook + enrichment + Slack | `templates/new-user-enrichment` |
| Telegram bot | `templates/telegram-bot-starter` |

Full list of official starters: https://www.val.town/orgs/templates

## When to skip a template

Simple cron jobs (monitoring, alerts, periodic polling) don't need a template — create a new val with a single `interval`-type file directly. Templates exist to scaffold complex shapes (UI, multi-file apps, integrations); a one-file cron isn't one of them.

## Forking an existing val

When the user references an existing val or asks to build something "like" another val, use `remix_val` to fork that val as the starting point instead of an official starter. The user's own prior work is often a closer match than any generic template.

## After remixing

Share the live URL immediately so the user can watch the work come together, then customize files one at a time. Update the README last.
