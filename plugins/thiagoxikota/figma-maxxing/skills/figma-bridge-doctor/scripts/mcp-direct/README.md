# mcp-direct: direct client fallback

Fallback for when the figma-console tools **do not exist in the session** (a layer 1 failure:
Claude Code freezes the tool list at session start). It talks to `figma-console-mcp` over stdio,
without depending on the MCP registration and without asking the user for a `/mcp` reconnect.

**Opt-in.** The daemon is a local HTTP proxy that can run any figma-console tool against the open
Figma file. An agent starts it only after telling the user what it is and getting an explicit yes,
and stops it when the task is done. When to reach for it: [layer 1 recovery](../../references/layer1-recovery.md).

Run these from this directory (`scripts/mcp-direct/` inside the `figma-bridge-doctor` skill):

```bash
WS_PORT=9231 HTTP_PORT=8791 node daemon.mjs &                 # start and pair
python3 fx.py script.js [timeout_ms]                           # figma_execute
python3 shot.py <nodeId> out.png [scale>=0.5]                  # screenshot

# raw call: JSON content type plus the bearer token the daemon wrote at boot
# (printf is a shell builtin and curl reads the header from stdin, so the token stays out of ps)
TOKEN_FILE="${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}/mcp-direct-${HTTP_PORT:-8791}.token"
printf 'authorization: Bearer %s\n' "$(cat "$TOKEN_FILE")" |
  curl -s -X POST "http://127.0.0.1:${HTTP_PORT:-8791}" -H @- -H 'content-type: application/json' \
    -d '{"name":"figma_get_status","arguments":{"probe":true}}'
```

After starting the daemon, trigger the plugin once (menu `Plugins > Development > Figma Desktop
Bridge`, through the osascript in Step T of the skill). The plugin connects to **all** live servers
in the 9223-9232 range, so this **does not steal the bridge** from other sessions. Choose a free
port: `lsof -nP -iTCP -sTCP:LISTEN | grep -E '922[3-9]|923[0-2]'`.

## Environment

| Variable | Default | Read by | Meaning |
|---|---|---|---|
| `WS_PORT` | `9231` | `daemon.mjs` | WebSocket port handed to the server as `FIGMA_WS_PORT`. Pick a free one in 9223-9232. |
| `HTTP_PORT` | `8791` | `daemon.mjs`, `fx.py`, `shot.py` | Local HTTP port of the daemon. Set the same value for the daemon and the two clients. |
| `FIGMA_MCP_ENTRY` | resolved from the npx cache | `daemon.mjs` | Path to `dist/local.js` of `figma-console-mcp`, to skip the cache lookup. |
| `FIGMA_ACCESS_TOKEN` | none | the server | Figma personal access token, inherited from the shell that starts the daemon. Needed for REST backed tools such as comments. Never printed, never written to a file. |
| `FIGMA_MAXXING_STATE_DIR` | `~/.config/figma-maxxing` | `daemon.mjs`, `fx.py`, `shot.py` | State dir shared with the rest of the skill. The daemon writes its bearer token to `mcp-direct-<HTTP_PORT>.token` there. Set the same value for the daemon and the two clients. |

There is no secrets loader: the token comes only from the environment of the shell that starts
the daemon. Export `FIGMA_ACCESS_TOKEN` there before starting it, the same variable the
figma-console MCP server reads in a normal session.

## The HTTP endpoint is local and token gated

`daemon.mjs` listens on `127.0.0.1` only. Listening on loopback is not enough on its own: a web
page open in the browser can send a `text/plain` POST to `127.0.0.1` without a CORS preflight,
and every tool, `figma_execute` included, runs against the open Figma file. So every request must
pass three checks before it reaches a tool:

| Check | Refused with | Why |
|---|---|---|
| No `Origin` header | `403` | Browsers send `Origin` on cross-site POSTs. `fx.py`, `shot.py` and `curl` do not. |
| `content-type: application/json` on anything but `GET` | `415` | A browser only sends that type cross-site after a CORS preflight, and the daemon never answers one. |
| `Authorization: Bearer <token>` | `401` | The token is random per boot (`crypto.randomBytes`). |

The daemon writes the token, mode `0600`, to `<state-dir>/mcp-direct-<HTTP_PORT>.token` once the
port is bound, and removes the file when it exits (`kill <pid>` included). `<state-dir>` is
`${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}`, the same state dir as the rest of the
skill. `fx.py` and `shot.py` read the file for their `HTTP_PORT` and send both headers. Any process
running as the same user can still read that file: start the daemon for the task, stop it when
the task is done, and never bind it to another interface.

`GET /tools` lists the tools the server registered (name and input schema). Any other request is
a `POST` with `{"name": "<tool>", "arguments": {...}}` and returns the tool result. Both need the
bearer token. When a request fails inside the daemon, the client gets a `500` with a fixed
message (body not valid JSON, server timeout, or internal error) and the detail goes to the
daemon's stderr only.

## The daemon resolves the npx cache by VERSION, never by mtime (field note, 2026-09)

The original `ls -t` lookup picked the cache with the newest mtime, which was **1.35.0** while the
correct cache was 1.40.0. Every server, on boot, rewrites `~/.figma-console-mcp/plugin/` with its
own bundle: starting the wrong daemon **downgraded the plugin on disk**, and the next trigger loaded
1.35.0 inside Figma. The plugin started announcing `Plugin update available` without saying that
the move was backwards. Now the resolver reads `package.json` of each cache and sorts by semver;
the chosen version is printed to stderr at boot (`mcp-direct: using figma-console-mcp <v>`).

The cache directory is resolved at runtime as `<npm cache>/_npx`, because the npm cache location
differs per machine. `<npm cache>` is `npm_config_cache` when npm exported it, else the output of
`npm config get cache` (run with a fixed argument list and no shell), else `~/.npm`.

After starting this daemon, check `bash ../figma-status.sh | grep plugin_`: `plugin_drift=true`
means some server downgraded the disk. The fix is in the skill:
[references/plugin-version-drift.md](../../references/plugin-version-drift.md), section "Plugin
version: THREE layers, and the banner does not say the direction".

## Platform

Exercised on macOS only. The daemon runs on Node.js and the two clients on Python 3. The
osascript plugin trigger is macOS only, needs the Accessibility permission and assumes the English
Figma UI.

Field note, 2026-08: 16 screens written on one project with no native Figma tool in the session.
