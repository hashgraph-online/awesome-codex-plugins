# Plugin client checks

Read the checks in the order `SKILL.md` gives: the first FAIL is the cause
to fix. Every action below is the user's to take or approve; the skill
names it and does not run it.

| check | FAIL means | next action |
|---|---|---|
| `ensure-node.sh --check` | no Node 18+ on PATH, under a version manager or in the usual install directories, so no hook runs and the MCP entry gets no token ("needs authentication") | a Node the check missed: set `LOOM_NODE=/path/to/node` where the agent starts; none or too old: with the user's yes, run `ensure-node.sh` without `--check`; then restart the session |
| `server` | nothing answers at the URL checked: in Claude Code the one the MCP entry calls (the plugin's `server_url` option when a session saved it, else `LOOM_BASE_URL`, else localhost); in Codex the hooks' server (`LOOM_BASE_URL`, else `url` in `~/.loom/config.json`, else the plugin's default) | Claude Code: point the entry at the reachable server with the `server_url` option or `LOOM_BASE_URL`. Codex: set the entry's URL in `~/.codex/config.toml` and the hooks' in `~/.loom/config.json` |
| `server version` (WARN) | the server reports an older version than the plugin's `minServerVersion` | upgrade the server; until then the hooks that need a newer op fail one call at a time |
| `token` | no readable JWT, or it expired | get a new writer token from Settings → Tokens in the dashboard and update the plugin config; for an agent (`LOOM_CLIENT_ID` with a workload token) never a person's token: check the trust (`loom bot list`), that the workload token is current, and that the server answers `/oauth/token` |
| `source` (WARN, Claude Code only) | `~/.loom/config.json` holds a token saved for another server than the MCP entry calls (see `server`); the MCP header helper sends it there, so the loom MCP server shows "needs authentication" | when nothing named the entry's server (it is on localhost), point the entry at the file's server with the `server_url` option or `LOOM_BASE_URL`; otherwise put the entry's server's writer token in that file or in `LOOM_API_KEY`; then restart the session |
| `auth` | the server rejects the bearer (401/403) | refresh the token; hooks fail open and otherwise lose captures |
| `namespace` | the token's listed grant cannot write the hook namespace | get a writer grant, or set `LOOM_NAMESPACE` / `namespace` in `~/.loom/config.json` to one it can write |
| plugin registration | `loom` is not an enabled plugin, or its MCP server is not connected | `claude plugin enable loom` (Codex: `codex plugin add loom`), then restart the session; a failed MCP connection with every check above passing points at the URL the MCP entry uses (Claude Code: the `server_url` option; Codex: the plugin's `.mcp.json`) |
| `flush` (WARN) | capture jobs older than ten minutes never reached the server (the flusher that owned them died) | fix the lines above, then replay each file with `sh "<root>/bin/loom-node" "<root>/hooks/loom-flush.mjs" <file>`; it deletes the file when done. Conversation turns also retry on the next Stop, deduplicated by message id |

**Claude Code shows "needs authentication" or "SDK auth failed: ZodError" for
the loom MCP server.** The header helper sent no token the server accepted,
and Claude Code fell back to a browser sign-in that the server has off; the
ZodError is that fallback failing, not the cause. The `token` and `source`
lines say which lookup supplied the token and whether the config names
another server. Note the install option never reaches the header helper: it
reads `LOOM_API_KEY`, then `~/.loom/config.json`, then `~/.loom/token`.

`loom doctor --client` may add more checks when the optional Python CLI is
installed. Never report a namespace write as verified from a listed grant.
