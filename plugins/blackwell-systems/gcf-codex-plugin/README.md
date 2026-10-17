# gcf-codex-plugin

Codex plugin for [GCF Proxy](https://github.com/blackwell-systems/gcf-proxy). Reduces MCP tool call token costs by 71%.

## Install

```bash
codex plugin add gcf-proxy
```

## What it does

Every MCP tool call returns JSON. This plugin wraps your MCP servers with [GCF Proxy](https://github.com/blackwell-systems/gcf-proxy), which re-encodes those JSON responses as GCF before they reach the model.

**The savings:**

| Metric | Value |
|--------|-------|
| Token reduction vs JSON | **71%** |
| Token reduction vs TOON | **25%** |
| Session dedup (warm session) | **up to 92%** |
| Comprehension accuracy | **100%** across 1,700+ LLM evaluations |

## Skills

| Skill | Description |
|-------|-------------|
| `/gcf-proxy:setup <server>` | Wrap any MCP server with gcf-proxy |
| `/gcf-proxy:stats` | Show token savings for the current session |

## Hooks

- **SessionStart**: Clears stale stats from previous sessions
- **Stop**: Shows notification with calls rewritten, % saved, and tokens saved

## Quick start

After installing, wrap any MCP server:

```
/gcf-proxy:setup github
```

This modifies your MCP config to route the server through gcf-proxy. The original config is preserved (disabled, with a `-raw` suffix) so you can revert anytime.

## How the savings work

1. **First call (71% savings):** GCF encodes the same structured data in 71% fewer tokens than JSON. The model reads GCF natively with 100% comprehension accuracy.
2. **Subsequent calls (up to 92%):** Session deduplication detects repeated structure. Only deltas are transmitted.
3. **Zero code changes:** The proxy wraps any MCP server. The server still outputs JSON; the proxy re-encodes before it reaches the model.

## Cost example

A team running 1,000 queries/day with GPT-5.5 ($5/MTok input):

| Format | Monthly cost | Annual cost |
|--------|-------------|-------------|
| JSON | $12,098 | $145,171 |
| GCF | $3,549 | $42,583 |
| **Savings** | **$8,549/mo** | **$102,588/yr** |

[Try the cost calculator](https://gcformat.com/calculator) with your own numbers.

## Links

- [GCF Spec](https://gcformat.com)
- [GCF Proxy](https://github.com/blackwell-systems/gcf-proxy)
- [Claude Code Plugin](https://github.com/blackwell-systems/gcf-claude-plugin)
- [Benchmarks](https://gcformat.com/guide/benchmarks.html)
- [Cost Calculator](https://gcformat.com/calculator)

## License

MIT
