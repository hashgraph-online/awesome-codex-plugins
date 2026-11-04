---
name: bindry-connect
description: One-time setup connecting Codex to the Bindry MCP server, for live-mode skills. Use when the user wants to enable live mode for Bindry skills or asks to connect Codex to Bindry's MCP server.
---

Connect this machine to the Bindry MCP server so `--mode live` skills (compiled by the `bindry-sync` skill)
actually work. This is a one-time, per-machine/user step — it isn't tied to any particular project or Binder,
and only needs to happen once even if the user syncs several Binders live later.

1. Explain up front: this needs an API key — the same one already used for pinned `bindry-sync` works here
   too, no separate scope or permission to grant. Generate one from the workspace's team page in Bindry (not
   Account settings — a key is scoped to whichever workspace's team page made it). Recommend the user put it
   in a `BINDRY_API_TOKEN` environment variable rather than pasting it directly.
2. Need `--api-base <url>` (the Bindry API's base URL — ask if not obvious from context, e.g. from an existing
   `bindry.config.json` in a project this user has already synced).
3. This changes standing local CLI configuration (adds an MCP server to this machine's Codex config) — state
   the exact command below and get explicit confirmation before running it, don't run it silently:
   ```
   codex mcp add bindry --url <api-base>/api/mcp --bearer-token-env-var BINDRY_API_TOKEN
   ```
4. After running it, confirm the server shows as connected (list configured MCP servers and check `bindry`'s
   status). If it reports a connection failure, report exactly what it said (bad API base, network issue, or
   an invalid/expired key show up as different failures — don't guess which without checking).
5. Once connected, tell the user live-mode skills are ready to use — syncing a Binder with `--mode live` will now
   compile skills the agent can actually call MCP tools through, and the `bindry-check` skill will report them
   as "live (always current)" rather than stale or unknown.
