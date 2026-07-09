---
name: haunt-web-extraction
description: Use Haunt MCP to extract structured JSON, clean Markdown, article fields, metadata, or usage from permitted public web pages.
disable-model-invocation: true
---

# Haunt Web Extraction

Use this skill when the user needs data from a permitted public web page inside Claude Code, Cursor, Codex, OpenCode, or another MCP-aware coding agent.

## First action

If the Haunt MCP server is installed but no API key is configured yet, call `try_demo_extract` first. It proves the server is wired correctly and returns docs, signup, pricing, MCP info, and free-tier links without using credits.

## Live extraction

For live pages, require `HAUNT_API_KEY` in the MCP server environment. Use:

- `extract_url` or `extract` for structured JSON from a permitted public URL.
- `extract_markdown` for readable page text for RAG, notes, docs ingestion, or `.md` files.
- `extract_article` for public article pages.
- `extract_metadata` for titles, descriptions, Open Graph, Twitter Card, and canonical URL metadata.
- `get_usage` after live calls to check plan and remaining credits.

## Boundaries

Haunt is for permitted public pages and supported rendered pages. It does not promise CAPTCHA solving, login-wall access, paywall access, restricted-page access, or anti-bot circumvention. If a page is blocked, login-required, CAPTCHA-gated, paywalled, restricted, or too thin to verify, treat Haunt's clear failure signal as the correct result. Do not fabricate extracted data.

## Good prompt pattern

"Use Haunt to extract the product name, price, availability, and review count from this permitted public URL: <url>. Return JSON and tell me if the page was blocked or unverifiable."
