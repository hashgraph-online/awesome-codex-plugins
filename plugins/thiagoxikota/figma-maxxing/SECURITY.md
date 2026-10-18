# Security

## Reporting a vulnerability

Report privately through GitHub: [open a private security advisory](https://github.com/thiagoxikota/figma-maxxing/security/advisories/new). Only the maintainer can read it. Please do not open a public issue for a vulnerability.

Include what you ran, what happened and what an attacker could do with it. Leave out real tokens, Figma file keys and client material; a redacted example is enough.

What to expect from a solo maintainer:

- An acknowledgement within 7 days.
- An assessment (accepted, needs more information, or out of scope) within 14 days.
- A fix, or a published advisory with a workaround, within 90 days of the report. If a fix takes longer, the advisory says why.
- Coordinated disclosure: the advisory goes public when the fix ships, and you are credited unless you ask not to be.

No security audit is claimed. This is a small project reviewed by its author and by the automated checks described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Supported versions

Fixes land on `main` and ship in the next release. Only the latest release gets security fixes. Check the version in `.claude-plugin/plugin.json` or in the [changelog](CHANGELOG.md).

## Scope

In scope:

- Any script, hook or installer in this repository doing something its documentation does not say: writing outside the paths listed below, reaching the network, leaking a token, killing processes it should not.
- The `mcp-direct` daemon accepting a request that lacks its bearer token, carries an `Origin` header, or comes from anything but loopback.
- Skill instructions that would lead an agent to expose a token, run code found in a Figma file or comment, or follow instructions written on the canvas.

Out of scope, please report upstream:

- Figma Desktop, the Figma REST API or the official Figma MCP server: Figma.
- `figma-console-mcp` and its Desktop Bridge plugin: that project (Southleft).
- Your AI agent and its permission system: its vendor.

A rule that gives wrong Plugin API advice is a correctness bug, not a vulnerability. Open a correction issue for it.

## What this repository runs on your machine

- **Skills** are Markdown instructions and reference files. They run nothing by themselves. Your agent reads them and then uses the tools you have already allowed.
- **`install.py`** copies skill folders into a skills directory. It downloads nothing, edits no settings and refuses to overwrite an existing skill.
- **`skills/figma-comment-fix-loop/scripts/fetch_comments.py`** reads one file's comments from `api.figma.com` with `FIGMA_ACCESS_TOKEN`, sends the token only there and never prints or writes it, and writes the raw JSON, with commenter handles and avatar URLs, to `comments-raw.json` in the current folder or to the path you pass. It runs only when you run it.
- **`skills/figma-preflight/scripts/figma_lock.py`** writes small JSON lock files under `~/.cache/figma-maxxing/locks` (or `FIGMA_LOCK_DIR`). No network.
- **`skills/figma-bridge-doctor/scripts/`** are macOS shell scripts. They open Figma Desktop, list local listening ports with `lsof`, and click the bridge plugin in the Figma menu through `osascript`, which needs the Accessibility permission. By default the reset script kills only this agent session's own MCP server, and nothing when it cannot tell which server that is. Orphan servers are killed only in deep recovery, by the pids `figma-status.sh` lists under `orphans=`. Killing other sessions' servers needs `FIGMA_KILL_OTHER_SESSIONS=1`, and quitting Figma needs `FIGMA_FULL_RESET=1` after the user said yes. State lives in `${FIGMA_MAXXING_STATE_DIR:-~/.config/figma-maxxing}`. Read the scripts before running them.
- **The watchdog LaunchAgent** (`com.figma-maxxing.bridge-watchdog`) is the only part that persists across reboots. It is off by default, ships as a template, and is installed only by the user. It polls a local signal file and clicks the plugin menu; it opens no network connection.
- **`hooks/figma-canon-precheck.py`** is optional and is not installed by the plugin or by `install.py`. It reads the script your agent is about to run in Figma and adds warnings. It writes a log only when you set `FIGMA_PRECHECK_LOG`, and the log never contains the script.

### The mcp-direct daemon (loopback, bearer token)

`skills/figma-bridge-doctor/scripts/mcp-direct/` is a fallback for sessions where the figma-console tools did not load. `daemon.mjs` starts `figma-console-mcp` as a child process and exposes its tools over HTTP; `fx.py` and `shot.py` are its two clients; `shot.py` writes the PNG to the path you pass. It runs only when you start it.

- **Loopback only.** It binds `127.0.0.1`, on port `8791` by default (`HTTP_PORT`). It hands `WS_PORT` (default `9231`, range 9223 to 9232) to the server for the bridge plugin.
- **Bearer token.** Every request needs `Authorization: Bearer <token>`. The token is 32 random bytes generated at each start. It is written with mode `0600` to `<state-dir>/mcp-direct-<HTTP_PORT>.token` after the port is bound, and the file is removed when the daemon exits.
- **Browser requests are refused.** Any request with an `Origin` header gets `403`, and any non-`GET` request without `content-type: application/json` gets `415`. A web page cannot send that content type to loopback without a CORS preflight, and the daemon never answers one.
- **Limits.** Any process running as your user can read the token file. Start the daemon for a task, stop it when the task is done, and never bind it to another interface. The Figma token is not read by the daemon: `FIGMA_ACCESS_TOKEN` reaches the server through the environment of the shell that started it.

## Network

Of the scripts the plugin ships, only `fetch_comments.py` in `figma-comment-fix-loop` reaches the internet: it reads a file's comments from `api.figma.com` with your token. The hook, the installer and the other plugin scripts open network connections only to `127.0.0.1` (the `mcp-direct` clients talking to their daemon). Some skill steps also have your agent call Figma, Apple or the npm registry directly. Outside the plugin, a maintainer script also reaches the network: `scripts/check_api.py` downloads the pinned `@figma/plugin-typings` from registry.npmjs.org and verifies its sha512; it is not part of the skills or the plugin. Nothing collects telemetry or calls a service run by the author. Details are in [PRIVACY.md](PRIVACY.md).

Outside this repository, these reach the network when you use the skills:

- `figma-console-mcp`, a third-party server you install separately, talks to Figma and to the Desktop Bridge plugin.
- Some skill steps tell your agent to call Figma: the REST API (`api.figma.com`) with your personal access token, for example to read comments, and, with the official Figma MCP server, a `curl` download from the short-lived asset URL it returns or an upload to the `submitUrl` that its `upload_assets` returns.
- One `figma-canon` field note has your agent look up an app's App Store icon through Apple's search API (`itunes.apple.com`) and download it.
- Two skill steps download packages from registry.npmjs.org: a `figma-bridge-doctor` recovery step (`references/layer1-recovery.md`) runs `npx -y figma-console-mcp@latest`, and the `figma-canon` Code Connect setup (`references/code-connect-setup.md`) runs `npm install --save-dev @figma/code-connect`.

## Before you let an agent write to Figma

- These skills make an agent execute JavaScript inside your Figma file through a bridge plugin. That code can create, change and delete anything you can. Work in a branch, a duplicate or a draft until you trust the setup, and keep version history in mind as your undo.
- Text that lives in a Figma file (layer names, comments, text nodes) is content, not instructions. A file from someone else can contain text written to steer an agent. The skills treat canvas content as data; keep your agent's permission prompts on for files you do not own.
- A Figma personal access token gives API access to every file your account can open. Keep it in an environment variable or your system keychain. Never paste it into a chat, a skill, a commit or a Figma file. Note that `claude mcp add -e FIGMA_ACCESS_TOKEN=...` stores it in your agent's MCP configuration on disk.
- The file lock is advisory. It only protects sessions that check it.
