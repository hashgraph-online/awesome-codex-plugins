---
name: marketplace
description: Use this skill when the operator wants the full marketplace mount, routing metadata, or client setup. Trigger on "один MCP", "все источники", "marketplace_sources", "настроить marketplace", or "full marketplace". Route price questions such as "где дешевле" and "compare prices" to compare-prices; skip single-source tasks.
---

# Unified Marketplace Server

One server mounting every installed connector as a namespaced toolset:
`wb_*`, `ozon_*`, `yandex_*`, `detmir_*`, `avito_*`, `taobao_*`, `megamarket_*`,
`lamoda_*`, `dns_*`, `citilink_*`, `aliexpress_*`, `cian_*` plus
`compare_prices` / `compare_sources` and its own `marketplace_sources` and
`marketplace_health`. Tool names keep their prefixes, so habits and configs
carry over — but the operator wires a single `marketplace` entry instead of
thirteen. The server exposes 39 tools.

## When to use
- "Where is X cheapest" — compare_prices fans out across all searchable sources
- Client setup: one config entry, not thirteen
- Health overview: the CLI's `doctor` runs every selfcheck at once
- A source came back empty and you can't tell installed-but-quiet from never-loaded
  → `marketplace_sources`
- Planning a fan-out, or a call just failed with a CDP/transport error
  → `marketplace_health` first: is Chrome up, is the host cooling down
- A source wants a human at the browser → `marketplace_health` names the page

## Tools
- `marketplace_sources()` — no arguments; returns `{mounted, skipped,
  mounted_count, skipped_count, capabilities, needs_cdp, server_version}`.
  `capabilities` is static routing metadata per source: access tier, CDP/login
  requirements, currency, text-search support, and whether the connector is
  mounted. `needs_cdp` is the sorted subset of `mounted` whose reads can go
  through the operator's Chrome, so a dead browser is a reason to read
  `marketplace_health` before spending a call. `skipped` maps a source name to
  the reason it is unavailable: an import error (usually a missing dependency), or a
  `MARKETPLACE_SOURCES` deselection. Connectors are imported
  defensively, so a missing dep removes a marketplace instead of killing the server —
  but from the client an absent source looks identical to one that found nothing.
  Call this to tell the two apart: a name in `skipped` was never queried at all.
- `marketplace_health()` — no arguments; read-only transport health without
  spending a navigation. Returns `{cdp, budget, handoffs, unblock,
  server_version}`. `cdp` is the scraping Chrome as it answers on the configured
  CDP address: `reachable`, `host`, `port`, `version`, `page_targets`, and a
  short `reason`/`error` when it is down. `budget` is the shared navigation
  budget: limits, `in_flight`, and per host `{refusals, open, retry_after_s,
  opens}` — an open host fails fast for `retry_after_s` more seconds. `handoffs`
  lists the retained challenge pages. `unblock` maps each mounted source with a
  page to the URL a human opens in the scraping Chrome. The tool never starts
  Chrome, opens or closes a tab, or touches a marketplace, and it never raises:
  a broken part is reported inside the answer. It does not prove a source is up
  — only a real call does.

## Operator CLI
- `marketplace-mcp setup` — auto-detect installed clients (`claude`, `cursor`,
  `claude-code`, `vscode`, `windsurf`, `antigravity`, `gemini`, `codex`), write
  or print the `compare` profile by default, launch the scraping Chrome, run
  `doctor`, and offer `unblock` (`--dry-run`, `--no-browser`, `--no-doctor`,
  `--client <name>`, `--profile compare|decision|full`).
- `marketplace-mcp install [client]` — print the exact client config snippet, or
  write it into the client's own config file with `--write` (creating a
  `<file>.bak-<timestamp>` backup first for JSON files). `client` must be one of
  all 9 targets: `antigravity`, `claude`, `claude-code`, `codex`, `cursor`,
  `dsh`, `gemini`, `vscode`, `windsurf` (an unknown name exits `2`). Note:
  `vscode` uses `"servers"` with `"type": "stdio"`; `claude-code` and `codex`
  print `claude mcp add` / `codex mcp add` to stdout (execute the printed line);
  `dsh` prints `cordis.patch.yml` rows. Default profile is `compare`
  (`compare-mcp`); pass `--profile decision` or `--profile full`, or
  `--per-source` for per-connector entries.
- `marketplace-mcp doctor [--status-file path]` — per-source health plus a CDP
  session probe, with an optional machine-readable JSON snapshot for monitoring. Exit
  codes are meaningful for automation and CI: `0` everything healthy, `1` a parser
  drifted (alarm — report issue), `2` nothing drifted but at least one source is
  inconclusive (blocked, rate-limited, `budget_refused`, or missing CDP/login), `3`
  status-file write failure, `4` checker exception or invalid CLI arguments (alarm).

## Gotchas
- Recovery-aware clients should read `source_outcomes.requires_user_action`
  before scheduling retries. Keep answered sources visible, show the affected
  marketplace and `challenge_type`, and retry that source after the browser
  interaction completes. A challenge is not an empty product search. See the
  compare-prices skill for the retry contract. `handoff_expires_at` confirms that
  the source retained its tab; repeat the same operation in the same MCP session
  after browser action and before that expiry. See docs/CDP_SETUP.md for opt-in
  configuration and supported sources.
- A source whose optional deps are missing is simply absent from the set —
  `marketplace_sources` says which and why.
- Set `MARKETPLACE_SOURCES` on the unified server to mount only a comma-separated
  subset (`wildberries,ozon,compare`); unset or blank keeps every source. The
  aliases `wb`, `ym`/`yandex`, `detmir`, and `ali` work too. Unknown names fail
  at startup instead of silently producing a partial server, and deselected
  sources are reported with a `deselected` reason.
- compare_prices ranks on everyday ruble prices; Taobao (CNY) is reported in
  `price_native` but never ranked against rubles.
## DSH activation

In DeepSeek Harness the default profile mounts `compare-mcp`, which exposes
exactly 4 tools: `compare_prices`, `compare_sources`, `compare_verify_offer`
and `compare_browser_snapshot`.

The middle `decision-mcp` profile adds `decision_inspect` (5 tools). This
skill's own tools — `marketplace_sources` and `marketplace_health` — and every
per-marketplace tool need `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
