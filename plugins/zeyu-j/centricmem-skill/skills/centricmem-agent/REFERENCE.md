# CentricMem Agent — how to use

The session loop lives in [SKILL.md](SKILL.md) (When to Use, classify, sweep, Typical Workflows). This file is the branches. Host MCP tool schemas are the live contract — if a tool exists on the server but not in SKILL’s list, the schema wins. Agents talk to the hosted librarian **only through host MCP** at `https://mem.centricmem.com/mcp` (Bearer: the default key, or an extra key with shelf grants). This agent (and each client you install into) tries `/connect?device=` first. OAuth (add that URL with no Bearer and finish a browser prompt) only if minting that URL failed **and** this agent will receive the login. You do not curl librarian HTTP.

## Typical Workflows

Replay these. Do not invent a hub, curl, or CLI-write.

**First connect** (`cm_*` missing this chat **and** they have no Bearer and no finished OAuth login in this agent — plugin `mcp.json` / `mcp add` with no Bearer counts here):

1. This same reply sends https://centricmem.com/login?signup=1 **and** tries to send a `/connect?device=` URL **and** tells them to save a backup of the key (Keys shows it only once). Plugin `mcp.json` is not a completed connect. **This agent** (and each client you install into) mints that URL this turn when it can — do not skip minting because OAuth or `mcp login` exists.
2. Mint the device URL. Prefer `centricmem connect --device --url-only` when that flag exists (prints the URL and exits). Later `centricmem connect --claim` (add `--target <this-host-mcp.json>` for an unlisted host). Blocking `centricmem connect --device` is still valid. If `connect --device` is missing, POST `/connect/device` `{hostname}` once and send JSON `url`. If `centricmem` is on PATH but has no `connect --device`, ignore that leftover npm binary — do not npm-install. Keep `secret` off chat. They enter the key on that page (ten minutes). Claim off-chat; never print the token. Optional: `centricmem connect --verify` prints grants/tool count, never the key.
3. **If minting that URL fails** (error, leftover CLI, blocked shell): if the shell works but `centricmem` is missing (no Node / no CLI), mint via **POST** `https://mem.centricmem.com/connect/device` as in Reach below — do **not** start with `doctor connect`. If `centricmem` is on PATH: run `centricmem doctor connect` and tell them to email zeyu@poppyg.com with that output (which agent; never a key or token). Do not send that mail for them. **Then MCP OAuth** only if this agent will receive the login after they finish a browser prompt: add `https://mem.centricmem.com/mcp` with no Bearer (Cursor: Add to Cursor on https://centricmem.com; Codex on this machine: `codex mcp add` then `codex mcp login`; Hermes: `hermes mcp add --url https://mem.centricmem.com/mcp --auth oauth centricmem`; cloud agents that can have them operate a browser this agent is waiting on — Grok Bot, Manus, Cursor Cloud, Claude). Do not send a Loopback `127.0.0.1` authorize link when this agent is not listening there. After a failed mint with no receivable browser login: they paste Bearer in this agent's MCP settings.
4. Retry `cm_health` here. New chat only if still 401. If connect still fails, or they have a usage problem this Skill cannot fix: tell them to email zeyu@poppyg.com (which agent + what they saw; never a key or token). Do not send that mail for them. Legal/privacy mail stays poppy@poppyg.com on the website.

**Already added** a Bearer or a finished OAuth login in this agent, but `cm_*` are still missing: do not mint a new `/connect?device=`. Do not tell them to re-add `https://mem.centricmem.com/mcp` with no Bearer (that drops the key). Ask for a **new chat** so this session loads MCP. URL-only `mcp.json` / `codex mcp add` is **not** already added. Codex: a Bearer in `~/.codex/config.toml` `[mcp_servers.centricmem]` `http_headers` is a completed connect — restart/new thread. A finished `codex mcp login` on **this** machine is too. Still missing after that → email zeyu@poppyg.com (never a key).

**Daily cite and file:** SKILL.md §2 (start / resume) then §4 Sweep. Do not restate the batch here.

**Empty shelf → cards:** offer once (Existing memory below). Capture stays. They may skip. You file.

**1Password / vault MCP** is not a fourth recipe — see Reach. MCP aggregators (Composio and similar), HashiCorp Vault, and AWS Secrets Manager are the same class: a customer who already has them may inject an extra key in **their** worker. They do not replace OAuth or `/connect?device=`.

## What you are filing

```text
Library  (one per person — login, billing, delete)
  └── Shelf  (pass shelf=<id> or library=<id>)
        └── Card  (.md or one ##)
              **Summary** (`title`; `cm_done` `summary=`)
              **Key points** (body — what later agents cm_show)
              Identity / Details / Tags
              Original (optional) — pointer in Details; bytes in object storage
```

Inbox is gone. Do not mint `unclassified`. Leftover Inbox on an old hub: `cm_copy` `{from:unclassified,to:<named>}` then `cm_delete` `{id:unclassified}`. Never copy **to** Inbox. Tags are about the work. `project:` / `type:` / `#id` in search are index shortcuts, not extra types. Corpus YAML is that shelf’s Details.

**Card contract.** Every write is a card later agents `cm_show`. Required: (1) **summary** — `title`, and `cm_done` `summary=`; one line later search can hit; (2) **key points** — `cm_note` `body`, `cm_log_decision` `decision` / `context` / `consequences`, import `items[].body`; rules, facts, quotes, do/don't they can follow without the original. Not a card: title-only keep stub, empty headings, OCR slice, dump of the whole file.

**Writing style is not CentricMem's.** This Skill fixes structure (summary + key points) and filing rules — not voice, length, evidence density, language, or whether a card looks like nanobot's research notes vs a short Cursor decision. Those come from **this agent** (host norms, model, session) and **the human** (how they ask, house rules, charter). Different agents on the same shelf will write differently; that is expected. If they ask why cards differ, say that once — do not invent a CentricMem house style or tell them another agent wrote "wrong." A shelf charter may say *what* belongs here; it does not dictate prose style unless they put style in the charter themselves.

## Shelf routing

Decision **#0180**. Mechanism is fixed for every agent; content lives on each shelf.

| Order | Basis | Notes |
| --- | --- | --- |
| 1 | User explicit | This turn: named shelf / `shelf=` / `corpus=<slug>` / already-linked project they own |
| 2 | Charter match | Each shelf's `charter` (takes / rejects / axis / aliases). Match that line; if empty, fall back to `displayName` + ambient `libraries=` topic |
| 3 | Path proximity | cwd / repo / corpus dir — **tiebreak only** among charter matches. Never the primary key (#0092 only made unmatched cwd → `library=none`; it did not make cwd a classifier) |
| 4 | Mint | Only when the human is present and supplies the id/name |
| Forbidden | — | Agent's own folder as classifier; guessing a name; silent mint |

**Self-check.** Before writing, cite the charter line (or displayName/topic) you matched. No cite = you are guessing — ask.

**Charter (per shelf).** One short line (max 280): what it takes / what it rejects / axis / aliases. Axes include project/repo, topic/discipline, machine, person/customer. Type (decision/lesson/session) is already `docType` — do not invent a shelf per type. Set via `cm_library` `{id, charter}` or the Keys / Library desk. Empty clears.

**One read.** Prefer charter on each shelf in `cm_library` list / `cm_ambient` `libraries` rows (product path). **If `charter` is absent** on a row, treat it as unset — fall back to `displayName` + ambient topic; do not invent a charter or claim the API is broken. Do **not** treat a library-level "Shelf map" lesson as authoritative — those go stale (2026-09-07 inventory). An owner may keep a current topical lesson as interim help for this library only.

`cm_library` omit `id` lists `{id, displayName, charter?}`. Extra keys list grants only. Pass `share:` ids exactly as listed — do not mint that string.

## Reach

MCP tools must be present: `cm_health` `cm_ambient` `cm_doctor` `cm_search` `cm_show` `cm_note` `cm_log_decision` `cm_done` `cm_keep` `cm_library` `cm_copy` `cm_move` `cm_delete` `cm_rename` `cm_import` `cm_index` `cm_ops`.

If they are missing: **Already added** a Bearer or finished OAuth login in this agent → new chat, do not strip Bearer (Typical Workflows). URL-only MCP → first connect this turn. Never paste the key in chat. Never copy JSON into chat. Do not curl card/search APIs. Do not CLI-write. Do not bootstrap. Do not send a loopback `/connect` or a bare `/connect` with no `device=`.

**First connect, this same reply** sends https://centricmem.com/login?signup=1 **and** tries to send a `/connect?device=` URL **and** tells them to save a backup of the key — Keys shows it only once; never paste it here. Plugin `mcp.json` is URL-only: it is **not** a completed connect. **This agent** (and each client you install into) mints that connect URL this turn when it can.

**If minting that URL fails:** prefer the no-CLI path first. **Detail on demand.** Host-specific install, refresh, sandbox and failure detail is not shipped in this copy: read `cm_ops` with the MCP tools, or ask zeyu@poppyg.com. The rules and shapes below are what you need to connect and to stay safe.

**Shell works, `centricmem` missing** (no Node / no CLI): do **not** run `doctor connect` — follow the POST `/connect/device` branch immediately below. **`centricmem` on PATH:** run `centricmem doctor connect` and tell them to email zeyu@poppyg.com with that output (which agent; never a key). Do not email on their behalf. **Then MCP OAuth** only if this agent will receive the login after they finish a browser prompt: add `https://mem.centricmem.com/mcp` **with no Bearer**. Cursor may use Add to Cursor on https://centricmem.com (URL only, then the same prompt). Codex on this machine: `codex mcp add centricmem --url https://mem.centricmem.com/mcp` then `codex mcp login centricmem`. Hermes: `hermes mcp add --url https://mem.centricmem.com/mcp --auth oauth centricmem` (or `auth: oauth` in `~/.hermes/config.yaml`). Cloud agents that can have them operate a browser this agent is waiting on (Grok Bot, Manus, Cursor Cloud, Claude) may use that same URL-only add. **Do not skip `/connect?device=` because OAuth exists.** Do not send a Loopback `127.0.0.1` authorize link when this agent is not listening there. Do not curl OAuth or librarian HTTP. Do not download or open a settings file that contains a key, and do not ask them to send you that path. A URL-only `mcp.json` or Codex `config.toml` (url, no `Authorization`) may be copied or opened. After they finish the prompt, retry `cm_health`. Still failing, or a usage problem you cannot fix: they email zeyu@poppyg.com (never a key). Do not email on their behalf.

**Shell blocked** (Grok Bot, some web bots): minting `device=` failed. Send signup, tell them to email zeyu@poppyg.com with that error (never a key), then OAuth if this agent will receive a browser login they can finish (Grok Bot / Manus may). Otherwise they paste Bearer **only** in this agent’s MCP / plugin settings (`https://mem.centricmem.com/mcp`). Never here.

**Remote / cloud / sandbox — OAuth vs paste key.** “Remote” does **not** mean paste-key only. Split on whether **this agent** receives the browser login:

| This agent | Connect |
| --- | --- |
| Cloud/remote **and** it will receive the Approve / OAuth callback (human can operate the browser this agent is waiting on — e.g. Grok Bot, Manus, Cursor Cloud, Claude) | **OAuth** is fine: URL-only `https://mem.centricmem.com/mcp`, no Bearer. Same rule as desktop when mint failed. |
| Cloud/remote/headless **and** it will **not** receive that login (common: `127.0.0.1` loopback while this agent is not listening there; CI; no waiting OAuth session) | **Bearer** in that agent’s MCP / plugin settings (or host injects an extra key). Never paste the key in chat. |
| Sandbox can mint `/connect?device=` but **claim cannot write** client MCP files (EPERM outside the workspace) | Do not treat claim as done. Human runs `centricmem connect --claim` (with `--target` if needed) **outside** the sandbox, or OAuth if this agent receives the login, or paste Bearer in settings. Sandbox chats then use the already-wired MCP. |

Do not tell them “remote can only paste a key.” Do not send a loopback authorize link when this agent is not listening there.

**Shell works, `centricmem` missing** (Hermes, Codex, WorkBuddy, Pi, OpenClaw, DSH, Manus when a shell exists — also the first fallback when mint fails and there is no CLI): do not npm-install the CLI. Mint `/connect?device=` this turn: fetch **POST** `https://mem.centricmem.com/connect/device` with `{hostname}` once — authenticate bootstrap, not a card write. Send JSON `url` (`https://centricmem.com/connect?device=…`). Keep `secret` off chat (agent memory / a local file outside the git repo). They sign up, copy the key from the box at the **top** of Agent keys (once — tell them to save a backup), enter it on that page (ten minutes). Poll GET `https://mem.centricmem.com/connect/device/<id>` until `status=ready`, then POST `…/claim` `{secret}`. Write the claimed Bearer into this agent’s MCP file. Never print the token. If claim write fails (sandbox EPERM): follow **Remote / cloud / sandbox** above. If that mint fails: they email zeyu@poppyg.com with the error; then OAuth only if this agent will receive the browser login. Retry `cm_health`. “Do not call `/register` `/login`” means do not POST those HTTP APIs; you **do** send the signup URL and you **do** POST `/connect/device`.

**`centricmem` on PATH:** only if `connect --device` exists. Prefer `centricmem connect --device --url-only` (print URL, exit) then `centricmem connect --claim` after they submit the key. Blocking `centricmem connect --device` still waits up to ten minutes. Send **only** the printed `/connect?device=` URL — never the secret, never the key. Tell them to save a backup — the secret appears only once. They enter **any** agent key on that page (default = every shelf, extra key = granted shelves). Unknown host: `centricmem connect --claim --target <that-host-config.json>` (JSON `mcpServers` map). Do not read another client’s `mcp.json` to copy a key. If the binary has no `connect --device` (leftover npm 0.14.x), ignore it. Do not npm-install the CLI on a guest. Mint failure with CLI present → `centricmem doctor connect` then email zeyu@poppyg.com (never a key).

**Any other Agent Skills host.** Machine-readable recipe: repo-root `install.json`. Copy `skills/centricmem-agent/` so the file is `<skills-root>/centricmem-agent/SKILL.md`. Host MCP is streamable-HTTP at `https://mem.centricmem.com/mcp`. **goose** reads only `name` and `description` from the frontmatter, so `requirements.mcps` is ignored there - §0 Reach is what actually enforces the dependency on that host, not the frontmatter. A goose plugin also cannot declare a remote MCP server at all (its plugin MCP parser is stdio-only), so the endpoint is added as an extension or with `--with-streamable-http-extension`. After device claim, merge Bearer with `centricmem connect --claim --target <this-host-config>` (or `CENTRICMEM_MCP_TARGETS`). Confirm with `centricmem connect --verify` (grants/tool count, never the key). Do not scrape a 17-row client table and guess the skills root.

Config (agent key stays off git). URL-only MCP (not a completed connect). Plugin / Agent Plugins `mcp.json` uses client `type` **`http`** (wire is still streamable HTTP on the librarian):

```json
{
  "mcpServers": {
    "centricmem": {
      "type": "http",
      "url": "https://mem.centricmem.com/mcp"
    }
  }
}
```

Cursor desktop may set `"auth": { "CLIENT_ID": "centricmem-cursor" }` on that entry (Add to Cursor on https://centricmem.com does this). Claude custom connectors add the same URL; the host uses DCR or CIMD. Do not put a Bearer in git or in a deeplink.

Codex (`~/.codex/config.toml`) — URL only is **not** a completed connect. This agent (and each client you install into), including Codex, mints `/connect?device=` when `cm_*` are missing. `codex mcp login centricmem` is only after that mint fails, and only when this Codex will receive the loopback callback (this machine). Do not skip the connect URL for login:

```toml
[mcp_servers.centricmem]
url = "https://mem.centricmem.com/mcp"
```

Do not put `http_headers` Authorization in that file when writing URL-only. Device-connect or a paste key may still write a Bearer there — that **is** a completed connect. If `cm_*` are missing after a Bearer or a finished local login, a new Codex thread, not a second `codex mcp add` with no Bearer.

Codex / ChatGPT **OAuth vs Mixed**: Mixed is not “OAuth plus paste a key”. Mixed means the client may `initialize` / `tools/list` with **no** token, then OAuth later. We 401 unauthenticated MCP — Mixed fails. Pick **OAuth** for the browser prompt (`codex mcp login`). To paste a Keys agent key, put Bearer in `http_headers` (or `bearer_token_env_var`) **instead of** OAuth — Codex skips OAuth when Authorization is already set. An empty Mixed still tries anonymous discovery.

HTTPS `redirect_uri` not already on the static list (loopback, Cursor Cloud, Claude, ChatGPT Apps connectors): they sign in at https://centricmem.com/oauth/callbacks, submit the exact URL, then publish `/.well-known/centricmem-oauth-callback` or send it for operator review. Do not email a callback URL. Librarian **>=0.21.55**.

Authorize (after login) lists live agent keys. They pick an existing key (default = every shelf plus `share:`) or mint a new extra. Extra keys do not see invited `share:`. Sign-in is not the grant — they still click **Approve**. Librarian **>=0.21.56**.

After **Approve**, Codex on this machine waits on `http://127.0.0.1:<port>/callback` (some builds append `/<callback_id>`). The authorize page hops through same-origin `/oauth/continue` then 302s to that loopback URL. ChatGPT Apps waits on `https://chatgpt.com/connector/oauth/{id}`. If the agent is still waiting, they click **Open the agent callback**. That hop is the **browser host**. Do not send a loopback link when this agent is not listening there. Do not re-add the MCP URL with no Bearer. Librarian **>=0.21.51**. ChatGPT Apps directory Skill is a Scan Tools snapshot of this folder via host MCP `skills/list` (not a live GitHub pull). After a Skill bump, origin deploy then Scan Tools then a new plugin version. Do not `npx skills add` inside ChatGPT to refresh the listed plugin.

**Approved, but the agent stays "connecting".** A known, common failure - not the human's mistake, and not a wrong key. The browser finished and the agent is still waiting on a callback that never lands. Say it in those words, then:

1. Ask them to copy the **callback URL from the browser address bar** - the address the page tried to jump to - and email it to **zeyu@poppyg.com** so it can be added to the callback allow-list. **Redact `code=` and `state=` first**: those are secrets, and only the shape matters (scheme, host, path, port, e.g. `http://127.0.0.1:PORT/callback` or `https://host/.../callback`).
2. Unblock them now - do not wait for that email. `/connect?device=` works on every host and is a completed connect.
3. Before they try OAuth at all, know which shape needs permission: a **loopback** callback (`http://127.0.0.1:<any port>/<any path>` or `localhost`) is accepted as it stands - it is never "unlisted", so do not send the human to email one. Only an **HTTPS/remote** callback that is not a documented host (Cursor, Claude, Codex / ChatGPT connectors) needs verifying first, per host, at /oauth/callbacks. Where that is missing, prefer `/connect?device=`.
4. Do not guess a callback URL, do not paste a redirect into chat as if it were verified, and do not retry the same OAuth flow in a loop - a retry restarts the wait.

Hermes `<HERMES_HOME>/config.yaml` — `HERMES_HOME` wins, else the platform default, which on Windows is `%LOCALAPPDATA%\hermes` and on macOS/Linux `~/.hermes`. A `~/.hermes/config.yaml` is silently ignored when the default points elsewhere, as it does on Windows; `hermes hooks list` prints the file it actually loaded. Mint `/connect?device=` first when `cm_*` are missing. OAuth (`auth: oauth`; tokens land under `<HERMES_HOME>/mcp-tokens/`) only after that mint fails, and only if this Hermes will receive the browser login:

```yaml
mcp_servers:
  centricmem:
    url: "https://mem.centricmem.com/mcp"
    auth: oauth
```

Same as `hermes mcp add --url https://mem.centricmem.com/mcp --auth oauth centricmem`. Use that OAuth block only after `/connect?device=` minting failed and this Hermes will receive the browser login. When OAuth is unavailable, device-connect then Bearer. In **docs / install plans / git**, prefer an env placeholder — never a literal hex:

Hermes with a key instead of OAuth: the same yaml with `headers.Authorization: "Bearer \${CENTRICMEM_API_KEY}"`.

Other agents (`mcp.json`) paste-key fallback (same rule — placeholder in shareable text; host may expand from env):

Any other `mcp.json` host: the canonical object above plus `headers.Authorization = "Bearer \${CENTRICMEM_API_KEY}"`. Placeholder in shareable text; the host writes the real value.

**Bearer: where plaintext is OK vs not.** These are different layers — do not treat them as a conflict.

| Layer | Rule |
| --- | --- |
| Chat, git, deeplink, plugin `mcp.json` in the public repo, install-plan **snippets** | Never a raw agent-key hex. Prefer URL-only (OAuth) or `Bearer ${CENTRICMEM_API_KEY}` (host expands from env / `.env`). |
| `centricmem connect --claim` (or equivalent off-chat claim) writing **this machine’s** private client MCP file (`.cursor/mcp.json`, `.claude.json`, Codex `config.toml`, a plugin host's `config.toml`, etc.) | May write a literal `Authorization: Bearer …`. That is a completed connect. Do not copy that file into chat or git. |
| A private MCP side-copy a host may keep beside its own config | Same class as claim-written private MCP: may hold a literal Bearer. It is a **duplicate** of the host’s MCP entry, not a second product. Prefer one canonical client file; if MCP already works from the host config, delete this side-copy. Do not copy into chat or git. |
| Host install tools that **propose** headers and will probe `https://mem.centricmem.com/mcp` | Prefer `${VAR}` in the plan. If the host marks “sends auth headers” as high risk, that gate is about **sending** Authorization on apply — not a ban on claim-written local files. Confirm with the human before apply when the host requires it. Do not put a raw hex into the proposed plan. |

**Redact.** Some hosts **redact** `Authorization` when echoing config or when headers land in card text — you may see `Authorization=[redacted]` (with or without a value). That marker is **not** a usable key and must not be filed, searched as a secret, or treated as “the Bearer changed.” Do not paste Authorization lines into cards. Readback after redact ≠ what you wrote; trust the host’s private MCP file / Keys, not the redacted echo.

**Never echo a credential (agent side).** Reading a key to use it is fine; printing it is not. Tool output becomes transcript text, and the host may also persist it in a session log or database, so a printed key is a leaked key.

- **Do not dump a credential file.** `cat` / `type` / `Get-Content -Raw` / a whole-object `ConvertFrom-Json` on `mcp.json`, `config.toml`, `*.env`, `api.json`, `keys*`, `*.pem` is the most common way a key reaches the transcript. Extract the single field you need and fingerprint it inside the same command.
- **Do not redact by threshold.** "Mask anything longer than N characters" fails on short keys: a 36-character `x-api-key` UUID and a 32-character local token both survive a 60-character rule. Redact by shape - replace the value, never pass it through.
- **Do not copy a key into a script, plan, snippet, note, card, or commit.** Read it at runtime from the environment (`CENTRICMEM_API_KEY` / `CENTRICMEM_TOKEN`) or from this machine's private client MCP file.
- **If you did print one, say so in the same turn and name which key it was.** It is already out; silence only delays rotation.

Fingerprint idioms (confirm which key, never print it):

- PowerShell: `"{0}... len={1} fp={2}" -f $v.Substring(0,4), $v.Length, ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($v))).Replace('-','')).Substring(0,8)`
- bash: `printf "%s... len=%s fp=%s\n" "${v:0:4}" "${#v}" "$(printf %s "$v" | sha256sum | cut -c1-8)"`
- node: `console.log(v.slice(0,4)+"... len="+v.length+" fp="+require("crypto").createHash("sha256").update(v).digest("hex").slice(0,8))`

**Blast radius and rotation.** Treat a printed credential as public and rotate it (Manager -> Keys). To size the spread first, scan the host's own history for the exact value and report file names and counts only, never the match:

- PowerShell: `Select-String -Path <logs> -SimpleMatch -Pattern $token | Group-Object Path | ForEach-Object { "$($_.Name) x$($_.Count)" }`

Scan the session database and transcripts, not only request logs: those rotate, so a zero-hit scan is not proof of containment. Rotation invalidates that key alone; other machines and other keys are unaffected.

`setup --install-skill` on a guest copies Skill files only (CLI >=0.21.46 also writes `~/.claude/skills/` and `~/.pi/agent/skills/`). It must not merge leftover catalog pairing tokens into Cursor `mcp.json`. Host MCP on a guest: every agent tries `/connect?device=` when `cm_*` are missing (`centricmem connect --device` when the CLI works; if the shell works but `centricmem` is missing, fetch POST `/connect/device` and send the JSON `url`). If minting that URL fails, they email zeyu@poppyg.com with the error; then OAuth only if this agent will receive the browser login (add that URL with no Bearer). If the shell is blocked and there is no receivable browser login, the human adds `https://mem.centricmem.com/mcp` in this agent’s settings with Bearer from Keys, never in chat. Local librarian hosts may still merge loopback MCP when `/health` advertises `mcp`. Never ask them to paste a token in chat. Never one-click install. Never a dashboard “connect this computer”. After they connect, retry `cm_health` in this chat; a new chat only if tools still 401. Token failure: say once; connect again (CLI or signup+settings); if still failing they email zeyu@poppyg.com (never a key); **hold the sweep** (this agent’s memory `CentricMem deferred sweep` + transcript path) until `cm_health` works. Only drop the hold if they said don't log or they stopped using this Skill.

### Client recipes (same MCP URL)

Skill folder name is always `centricmem-agent` (Agent Skills `name` = directory). That is **this Skill**, not the CLI (`centricmem`) and not the GitHub package (`centricmem-skill`). Install example: `npx skills add zeyu-j/centricmem-skill --skill centricmem-agent`. Say “CentricMem skill” to humans; keep `centricmem-agent` in paths and `--skill`. Plugin `mcp.json` is URL-only — not a completed connect. Do not list this Skill on ClawHub.

**Pi.** `pi install https://github.com/zeyu-j/centricmem-skill` (discovers `skills/`; also loads `~/.agents/skills/`). MCP is not in the package. Write URL-only `~/.pi/agent/mcp.json`:

```json
{
  "mcpServers": {
    "centricmem": {
      "url": "https://mem.centricmem.com/mcp",
      "type": "streamable-http"
    }
  }
}
```

If `cm_*` are missing, mint `/connect?device=` this turn. Paste-key fallback may use `"Authorization": "Bearer ${CENTRICMEM_API_KEY}"` (env placeholder — never a literal in git).

**OpenClaw.** Compatible **bundle** (Agent Plugins / `.claude-plugin` / `.codex-plugin` / `.cursor-plugin`). Not a native in-process plugin — do not add `openclaw.plugin.json`. Not ClawHub. `openclaw plugins install git:github.com/zeyu-j/centricmem-skill` or `openclaw plugins install centricmem-skill --marketplace zeyu-j/centricmem-skill`. Restart the gateway if tools stay missing. Then the same connect as other plugin clients.

**DSH.** Cordis **funnel** only. Needs `pnpm` on PATH (`npm i -g pnpm` if missing; `corepack enable pnpm` fails on Windows Program Files). Pin: `dsh plugin --profile web add github:zeyu-j/centricmem-skill#v1.0.32`. That mounts URL-only `@deepseek-ai/dsh-mcp-client` from `dsh/cordis.patch.yml` (`failOnStartupError: true` — missing Bearer aborts boot, it does not register 0 tools). The Skill is MIT from 1.0.7; the patch is MIT glue. The funnel does **not** load SKILL.md from `node_modules`: from the profile dir run `node node_modules/centricmem-skill/dsh/copy-skill.mjs` so `$DSH_HOME/skills/centricmem-agent/` exists. Never `npx skills add -g` (writes `~/.agents`, not `$DSH_HOME`). Overlay Bearer in `$DSH_HOME/profiles/<profile>/cordis.patch.yml` after `/connect?device=` — **same** `id: mcp-centricmem`, restate the whole `config` (`serverName: centricmem`, `transport`, `url`, `headers`). A typo in `serverName` creates a second namespace. Never commit headers. Tools appear as `mcp__centricmem__cm_*` — call those names, not bare `cm_*`. After overlay: **new chat** (mandatory; this session’s catalog is frozen). DSH does not speak MCP OAuth. `session.v3.jsonl.zstd` is not a keep source — skip `cm_keep`; still file note / decision / done. GitHub topic `dsh-plugin` is discovery.

### 1Password (optional vault, not a connect path)

An optional vault, **not** a connect path. Ask if you need the detail.

## Search and show

Progressive disclosure:

| Layer | Call | What you get |
|-------|------|----------------|
| L0 | `cm_search` | snippet from the Markdown **card** |
| L1 | `cm_show` | the card **body** — agent context (style rules, SOP, literature key points) |
| L1 section | `cm_show` `{file, shelf, heading}` | one `##` section only (same `heading=` as delete/rename). Use this to re-read a single note in `lessons.md` / a session heading without the whole file |
| Original | human Dashboard **Download Original** | attach bytes. Not FTS. Not agent context |

Never ask `cm_show` for originals. Never paste download URLs into the chat.

**List a shelf.** Omit `q` (and omit tags / type filters) **and** pass `shelf=` / `library=` → `cm_search` returns that shelf’s cards (`browse: true`, default cap **50**). Pass `limit=` to raise (max 500). Use this to judge empty vs populated, or inventory. Without `shelf=` / `library=`, omitting `q` is 400 — the error tells you to pass a shelf. Do not invent an empty-shelf conclusion from a failed no-`q` call.

Useful query bits (in `q` / `tags` / `type`): `filter`, `tag`, `type:decision`, `#0016` / `id:0016`. Bare word `decision` is full-text, not a type filter. `all` does not leak other shelves. An extra key’s `all` is only the shelves on that key’s grants. Pass `shelf=` / `library=` / `cwd=` when the Bearer can open more than one shelf. Isolation: **one key = its grants**. The owner's agent Bearer is the **default** key (`*` = every shelf).

**`heading=` on show.** Match is case-insensitive; exact `##` title wins, else the first `##` whose title **contains** the string. Duplicate / ambiguous headings → the **first** match in file order — pass a longer unique fragment if you need another. Wrong / missing heading → `Heading not found` (same as delete); it does **not** return the whole file.

## Which key / grants

`cm_health` returns `grants` (and `mode` on extras). Say that **once** this chat (SKILL.md). Do not dump other keys or secrets. This agent has one `centricmem` MCP slot — connecting another key **overwrites** the Bearer; every chat in this agent shares it. Do not invent a second MCP server name for per-tab switching. Grant changes stay on the dashboard **Keys** page (or HTTP/CLI with the default key) — never `cm_*`, so a new secret never lands in chat. Default cannot change its own grants (`*` is always every shelf). Extra `mode=read` (View only) can search/show/list only — writes return 403.

| Situation | Do |
|-----------|-----|
| Session start / resume | Same as SKILL §2: prefer `cm_ambient` with `shelf=` first (grants/mode/skill_latest already there); `cm_health` only when tools missing, connect, or ambient unhealthy. Never a stale `.ambient.md`. Context compress, checkpoint restore, or new chat on the same task = new session — re-run ambient first. Then refresh Skill if published `version` is newer. **Once**, say which key: `*` = default (this library plus shelves shared with this email), else list grant ids; if `mode=read`, say view-only once. Extra keys do not see `share:` rows. If `library=(none)` / unmatched cwd, pick from `libraries=` or mint — do not use the hub `use` pin. Pass a `share:` id **exactly** as listed; do not mint `share:` |
| This chat is default (`grants=["*"]`) | **once**: every shelf. Another agent/person/machine should only see some shelves → they mint an extra on **Keys**, tick those, connect **that** extra there. Optional View only on Keys. Do not nag otherwise |
| This chat is an extra (listed shelf ids) | **once**: those shelves; if `mode=read`, view-only (no note/keep/done). More/fewer → they tick grants on Keys (login, or connect default first). Need every shelf / mint a shelf / rename label / move cards / delete leftover / rename a card → authenticate **default** |
| 403 view-only / FORBIDDEN on write | this extra is View only (`mode=read`). Keys: clear View only, or connect a write key. Never paste a key |
| 403 `LIBRARY_MISMATCH` / cannot open a shelf | this key’s grants omit it. Keys: tick that shelf, or connect default. Never paste a key |
| They ask which key this chat is | `cm_health` `grants` only. Never list tokens |
| Empty library after Skill install | **once**, offer existing durable memories as cards (this file). Capture stays. They may skip |
| Why we chose X | `cm_search` (decision) |
| What we know | `cm_search` + lessons / `tags` |
| Human wants the file | tell them Dashboard Download Original |
| Durable work / chunk done | SKILL §4 Sweep before you yield (named shelf + one batch) |
| Librarian down / token failed | compose the sweep anyway; this agent’s memory `CentricMem deferred sweep`; connect link once; file the hold when health succeeds |
| Leftover named shelf or leftover Inbox | dest must exist; `cm_copy` `{from,to}` on the librarian, then `cm_delete` `{id}`. Never download originals here. Never `to=unclassified` |
| Selected cards on the wrong named shelf | `cm_search` / `cm_show` then `cm_move` `{from,to,files}` (default key or login). Extra keys cannot. Source cards are removed. Never download originals here. Never `to=unclassified` |
| Structured corpus (`corpus=slug`) | `library=` that slug; `cm_search` then `cm_show` the **card**, not a dump page |

Empty ambient + Work/Ops → do not deep-search; execute, then SKILL §4 before you yield.

## Existing memory → cards (once)

First ambient this chat when granted shelves look empty (`Curate: empty`, `library=(none)`, or `cm_search` with `shelf=` lists only AGENTS.md / active_context.md / empty lessons.md):

Offer **once**, in their language. They keep talking. Skip / later / don't log = stop offering this chat.

1. Capture stays (Cursor memories and other plugins). Do not uninstall. Do not dump every memory or every transcript folder.
2. Ask what they already have that should be **cited later**: facts in agent memory they can name, Markdown/PDF they can open, an exporter JSON.
3. Named shelf: pick from `libraries=` or `cm_library` (omit `id` to list `{id, displayName}`; extra keys list grants only). Mint with `{id, displayName}`. If the id is `share:…`, pass it as `shelf=` — do not mint that string. Extra key cannot mint and cannot see invited shelves — authenticate so they enter the **default** key.
4. Then:
   - Files they open or point at → `cm_keep` (bytes, never `path=`) → **this turn**, while you can still read that file, a card with **summary** + **key points** (`cm_note` `title`/`body`, or `cm_log_decision`). Do not stop at the keep stub (title + Attach). Later chats `cm_show` that note, not the attach.
   - ImportBundle JSON they provide → `cm_import` `{bundle:{version:1,…}, library}` then `cm_index`. Daily cards are `items=` (new `imported/kept/`), **not** for updating `rel_path` corpus cards — see **Import shapes**.
   - A **folder of originals** → bulk package below. Do not loop 200 `cm_note`s in one chat.
5. Do not paste chats, keys, or secrets. Do not write back into the capture store.

Skip this offer if the shelf already has real cards (decisions, lessons with body, sessions).

## Bulk package (cards + attachments, one librarian commit)

Stage on this computer (workspace or temp — **not** git, **not** a hub, **not** `unclassified`). The librarian commit is the ingest. Caps (`cm_health` `package`, same numbers): **50 cards**, **50 attachments**, **32MB zip**, **80MB uncompressed**, **25MB per file**, plus remaining attach quota. Over the cap → split into another commit. 400 `PACKAGE_LIMIT`.

**Agent path (you file).** One or a few originals: `cm_keep` then a card with **summary** + **key points**. A titled keep stub is not a card. A folder: keep-sign, then one import whose items each have title (summary) and body (key points). Do not upload a zip through MCP. Do not paste file bytes into chat.

1. For each original this commit (≤50): `cm_keep` `{filename, content, shelf, card:false}`. MCP signs and PUTs. `card:false` stores bytes only (no keep stub). Hold the returned `attach` pointer.
2. Write the Markdown cards locally (Identity / Details / Tags / Body). Prefer Details `- **Shelf**: <id>`. A Tags token that **equals the shelf id** (or its unique display name) also routes — still store about-tags. Mixed shelves in one commit are fine if this key can open each.
3. One `cm_import` `{ items: [{ title, body, tags, shelf, attach, external_id }] }` (or `{ package: { items } }`). A `bundle` that is `{items:[...]}` with no `version` is the same ingest. `attach` is the `imported/attach/…` pointer from step 1. `dryRun: true` previews the same disk paths apply will write (`files[].file`, not the title). Colliding titles become `slug-2.md`. `skipExisting: true` skips a dest slug (or mapped `external_id`) instead of allocating `-2`. Reused attach pointers count as attachments on dryRun and apply.
4. If more files remain, another commit. Tell the human the count left.

**Human path (zip, optional).** Only if they already packed a zip or you cannot read the files. You still file one-or-few with keep+note, and a folder with `{card:false}` then import. When they use the zip: Archive → **Upload zip**. Layout: `cards/*.md` + `attach/*` (optional `manifest.json` with `items[].card` / `attach` / `shelf`). Each card names its shelf (`- **Shelf**: id` or a Tags token that is the shelf id). They do not have to pick the shelf in the form — the card already knows. Mixed shelves in one zip are fine. Invited shelves use the listed `share:` id, not the owner’s slug. You do not fetch the zip.

Text-only exporter JSON still uses ImportBundle (`cm_import` `{bundle}`) — not this package. Example:

```json
{ "version": 1, "lessons": [{ "title": "Summary", "body": "Key points." }] }
```

Not `{items:[...]}` (that is daily cards). Not a dump of the Zod schema. Other keys: `imported`, `decisions`, `sessions`, `research`.

### Import shapes (do not mix)

Two different contracts on the same tool — picking the wrong one creates **new** cards instead of updating corpus paths.

| Goal | Call | Where it lands |
|------|------|----------------|
| **New daily cards** (keep stubs → notes) | `cm_import` `{ items: [{ title, body, tags, shelf, attach, external_id }] }` | `imported/kept/<slug>.md` (title collision → `slug-2.md`) |
| **Upsert existing paths** (corpus / recipes / prior ImportBundle) | `cm_import` `{ bundle: { version: 1, imported: [{ title, body, rel_path, external_id?, agent?, … }] } }` (+ `shelf=` / `library=`) | Exact `rel_path` under `imported/` (e.g. `academic/corpus/recipes/bam7/BAM7-4-01.md`) — updates in place |

Hard rules:

- Top-level `items=` (or `package.items`, or a `bundle` that is **only** `{items:[…]}` with **no** `version`) is **always** the daily-card path. Putting `rel_path` on an `items[]` row does **not** retarget corpus files — you still get `imported/kept/…`.
- To refresh a card that already lives at `imported/academic/…` or any known relative path: use **`bundle.version: 1`** + **`imported[]`** with that **`rel_path`** (and stable `external_id` when you have one). Prefer `dryRun: true` first.
- **`bundle` string = JSON text**, not a filesystem path. Large bundles: the client reads the file and passes the object/string (no host `bundleFile` / `path=`).
- **Counts:** `imported` = newly created under `imported/`; `updated` = same path or known `external_id` whose **content changed**; `unchanged` = same path rewritten with identical body (timestamp-only stamp differences do not count as updated). `files[]` lists `{file, action: created|updated|unchanged|skipped}`. Do not treat `imported:N` alone as “N duplicate cards.”
- **`rel_path` vs `file=`:** import `rel_path` is under `imported/` (omit the `imported/` prefix). `cm_show` / delete / rename `file=` is shelf-root relative — prefer `imported/…`. If you pass the bare `rel_path` and only `imported/<rel_path>` exists, show remaps automatically. Both forms work for show.
- **`agent` on `imported[]`:** optional writer stamp (`logged_by`). When omitted, host import uses the request writer (`X-CentricMem-Writer` / MCP writer, typically `mcp`), not a blank stamp. Local CLI import without a writer still defaults to `migration`. Avoids FTS `agent=unknown`.
- After host `cm_import`, FTS is updated automatically. Call **`cm_index`** (or guest CLI `centricmem index` with the same Bearer as import) when the index may be dirty, after bulk rebuild, or after local-junction sync stories — not every apply.
- If you already created stray `imported/kept/` duplicates by mistake: `cm_delete` those paths; do not “fix” them into the corpus path with another `items=` call.

### Search fields

- **`q` (not `query`):** `cm_search` takes **`q`**. Passing `query=` returns `Provide q, tags, or a type:/#id prefix.`
- **`workSiblings`:** when results share a bibliographic `work` id, search keeps the best hit and sets `workSiblings` to how many **other** cards with that work appeared in **this** result set (before collapse). It is `0` when only one card for that work matched. It is **not** the total card count for the work on the shelf, and it **changes with `limit` / query** because only cards that made it into the ranked window are counted.

### Direct HTTP `/mcp`

MCP is the interface. Use the MCP tools rather than hand-rolling HTTP.

### Hosted shelf ≠ local disk

A hosted library is not a directory on this machine. Ask if you need the detail.

## Skill refresh (once per chat)

1. Compare the version of the copy **this host loads** with `skill_latest` (from `cm_ambient` or `cm_health`).
2. If it is older, refresh the way **this host** was installed, then tell the human to restart the host or open a new chat so the new copy loads.
3. After a disk refresh, re-read this file and SKILL.md before the next write - installing newer is not the same as acting on it.

Host-specific install, refresh and failure detail is **not** shipped in this public copy. Read `cm_ops` when a host detail actually blocks you (librarian >=1.0.6 - it is served on request); ask zeyu@poppyg.com if that does not answer it.

## Writes (card shapes; trigger is SKILL §4)

Hold half-finished thoughts. **chunk** / **yield** / the numbered sweep batch and gate live in SKILL.md §3–§4 — file **before you yield**. Closing the agent does not run this Skill.

**What the API writes — `items=` and `bundle` are different contracts.** Both live on `cm_import`; picking the wrong one is the single most common source of "I filed it" when nothing was written.

| You want to write | Call | Lands in |
| --- | --- | --- |
| A note / lesson | `cm_note` | `lessons.md` |
| A decision | `cm_log_decision` | `decisions/NNNN-*.md` |
| A session unit | `cm_done` | `sessions/<stamp>-<writer>-<id>.md` |
| New cards (daily, bulk) | `cm_import` `{items: […]}` | `imported/kept/<slug>.md` — **cards only** |
| Corpus / known path upsert | `cm_import` `{bundle: {version: 1, imported: [{title, body, rel_path, external_id?}]}}` | that `rel_path` under `imported/` |
| **The shelf's current focus** | `cm_import` `{bundle: {version: 1, context: {body}}}` | **`active_context.md`** — overwrites, stamps `updated_by` / `updated_at` |
| **Global rules** | `cm_import` `{bundle: {version: 1, rules: [{body}]}}` | appended under **`AGENTS.md` → Global Rules** |
| Bulk decisions / lessons / sessions / research | `cm_import` `{bundle: {version: 1, decisions: […], lessons: […], sessions: […], research: […]}}` | `decisions/`, `lessons.md`, `sessions/`, `imported/` |
| An original file | `cm_keep` | R2; a keep stub is **not** a card — follow with a note |

- **A key that can open a shelf can write its library files.** `active_context.md` and `AGENTS.md` are not host-only: the `bundle` shape writes them over MCP, and a guest CLI can send the same bundle over HTTP. What is **not** writable through MCP: `config.json`, and *edits* to an existing card (use `cm_delete` + rewrite).
- `context.body` is the whole body. The writer prepends `# Active Context` and appends `<!-- centricmem:meta updated_at=… updated_by=… -->`; the doctor reads `updated_at` from there, so a hand-edit without that stamp reads as stale.
- **Unknown top-level slot → `400 BAD_IMPORT_BUNDLE`** naming the offending slot(s) and the allowed list (`version, project, source, decisions, lessons, rules, context, imported, sessions, research`). This used to be dropped silently. Nested row fields are still permissive.
- Reaching the shelf: MCP `cm_import` uses the client Bearer. Guest CLI `centricmem import` POSTs the same bundle to the librarian when `CENTRICMEM_TOKEN` is set.
**Who may write (guest vs host).** A CLI that holds a librarian key from *outside* the librarian host is a **guest**: it can write only through `import` / `index` (guest `index` refuses `--embed`). Commands that need a local hub refuse with `Operators write on the librarian host` — `init`, `setup`, `libraries --create/--use`, `migrate`, `serve`, `account bootstrap`, and every other command that needs a local hub. So file cards and decisions with the host MCP tools — `cm_import`, `cm_note`, `cm_log_decision`, `cm_done` — which carry the client Bearer and do not need leftover-hub writes. A guest CLI can still write over HTTP if `CENTRICMEM_TOKEN` is set (or after `connect --claim`), but the hub-write commands stay refused either way. Source: src/guest.ts, src/cli.ts:134.

| Type | When | MCP |
|------|------|------|
| Transcript | Each Non-Micro sweep | Shell-read jsonl → `cm_keep` filename + bytes (MCP does sign+PUT) |
| Session | Same sweep | `cm_done` with `attach`; `summary=` is the key points of this unit |
| Knowledge | durable model / fact | `cm_note` — `title` = summary, `body` = key points. Same title in `lessons.md` is an error (409); pick a new title, or `cm_delete` `{file:"lessons.md", shelf, heading}` then rewrite |
| Decision | architecture or durable host fact | `cm_log_decision` — `title` = summary; `decision` / `context` / `consequences` = key points. `refs` is a string: `1`, `0001`, `#0001`, or a comma list. Junk is 400. When an older decision is replaced, pass `supersedes=<n>` (integer); the old card becomes `status: superseded` / `supersededBy` — keep history, do not delete it |
| Edit a card | title or body of an existing card is wrong | **No in-place edit.** Title only → `cm_rename` `{file, shelf, title}` (optional `heading=`). Body / key points → `cm_delete` `{file, shelf, heading?}` then rewrite the card (or that `##` section). Prefer `dryRun` first. Wrong `heading` returns `Heading not found` and does **not** delete the whole file |
| Original | a file worth keeping | `cm_keep` as above, then a note/decision whose body is the key points. Never `path=`. Never stop at the stub. Same-title stubs 另存 (`slug-2.md`) |
| Bulk originals | many files to card | `cm_keep` `{card:false}` then one `cm_import` `{items}` (≤50). Archive zip only if they already packed one. Never zip via MCP |
| Shelf | none of the named shelves fit | omit `cm_library` `id` to list; then `{id}` to mint (default key). Extra: list grants only; authenticate so they enter the **default** key to mint. Connect does not mint a shelf |
| Shelf label | you learn a better **human** name than the current display name (rebrand, leftover folder slug, they say “that’s X”) | default key: `cm_library` `{id, displayName}` **this turn** — do not wait to be asked. Id / folder / grants stay. Writes still `shelf=<id>`. Use the name they use or the public product name; do not invent a prettier one. Skip if the label already matches. Extra key cannot: authenticate for the default key (step 0.2) and say the intended label once. Humans can also rename on the Library desk |
| Copy shelf | leftover named shelf (or leftover Inbox) should live on another | `cm_copy` `{from,to}`. Dest must exist. Extra keys need both grants. Never download originals here. Never `to=unclassified` |
| Move cards | a subset of Markdown cards should live on another named shelf | `cm_move` `{from,to,files}` (default key or login). `files=` whole Markdown card paths only — not `lessons.md`, not `file#heading`. Companion `imported/kept` stubs that cite the same Attach move with the card. `- **Shelf**:` is rewritten to dest. Extra keys cannot. Source files are deleted. Decision numbers stay if free on dest. Never download originals here. Never `to=unclassified` |
| Delete leftover shelf | leftover is empty or already copied | `cm_delete` `{id}` (default key or login). Extra keys cannot. Leftover Inbox may be the source. This is delete, not archive |
| Delete a card | one Markdown card should go | `cm_delete` `{file, shelf}` (library= also works). Optional `heading=` deletes one `##` section (`lessons.md` notes). Omitting it deletes the whole file. Do not pass `file#heading`. Always pass the shelf. Default key or login. Extra keys cannot. Shared shelves cannot. R2 attach is removed with the card (or that section). `dryRun` previews |
| Rename a card | the displayed title is wrong | `cm_rename` `{file, shelf, title}` (optional `heading=` when the file has several `##` sections). File path stays. Decision numbers stay. Default key or login. Extra keys cannot. Shared shelves cannot. Humans can also rename on the Library desk. `dryRun` previews |
| Bundle | capture / corpus upsert | ImportBundle `{bundle:{version:1, imported:[{rel_path,agent?,…}]}}` — **not** top-level `items=` (that creates `imported/kept/`). Host import indexes; `cm_index` only if FTS looks stale |
| Index | dirty index / bulk rebuild / junction sync | `cm_index`. `scanned` = candidates, `indexed` = rehashed this pass, `skipped` = walked but not FTS (`imported/kept/from-*` copy asides). `cm_show` by path still works |

Later sweeps in the same chat are OK for **new** facts. Do not re-file the same decision.

Do not send `path=` for the librarian to open a server file. Mention `#NNNN` in a decision body when linking units.

Cursor already writes `~/.cursor/projects/<workspace>/agent-transcripts/<uuid>/<uuid>.jsonl`. Shell-read it; never paste jsonl; never delete that local file.

Claude Code, Codex, Hermes, Pi, OpenClaw, Kiro, Kilo, Copilot, and other Agent Skills clients: only keep a transcript if that runtime actually wrote a local **plaintext** file for **this** chat. If there is no file, say so; do not invent a dump. Never paste the bytes into chat. DSH stores `session.v3.jsonl.zstd` (compressed) — that is not a keep source; skip `cm_keep` and still file note / decision / done.

## Optional host hooks

**Where the close half works, and where it does not.** The SessionEnd hook calls
`centricmem log-session --auto`, which is a **host-side** command: on a guest it stops with "this command cannot
write the leftover hub" and points at import or the MCP tools instead. So on a machine that talks to a hosted
librarian the hook is silent, and the card is filed by the **agent**, which is what the Skill already requires
anyway. The hook was left alone rather than making it post a card itself: a hook cannot read the session, and
this project's own rule is that a card's summary states the key points, not a placeholder. Cursor's installed
hooks have the same shape and the same boundary - they file on a librarian host and fall silent elsewhere.

Per-host extras live in folders named after the host. Check yours before assuming there is nothing here:

| Folder | Who it is for | What is in it |
|---|---|---|
| `hooks/` | Claude Code, Codex | `hooks.json`: a SessionStart hook that puts this shelf's context in front of the model, and a SessionEnd hook that files the unit when the session ends |
| `.zcode-plugin/` or the Claude Code marketplace | ZCode | its CLI is `zcode plugins marketplace add …` + `zcode plugins install …`; MCP is Settings → MCP Servers (stdio, HTTP, SSE - pick HTTP, since this service offers no stdio) |
| `dsh/` | DeepSeek Harness | skills come from `~/.agents/skills`; its Claude Code hooks bridge runs `hooks/hooks.json` with `pluginRoot` |
| `qwen/` | Qwen Code | hooks in `.qwen/settings.json`; `SessionStart` adds context via `hookSpecificOutput.additionalContext` |
| `goose/` | goose | recipes for a preflight and a close, plus a MOIM refresher that writes the file goose injects each turn |
| `openclaw/` | OpenClaw | a hook pack (`HOOK.md` + handler) that contributes the same context |
| `hermes/` | Hermes | a shell hook that injects the shelf's context on `pre_llm_call` and files the unit on `on_session_end`. It carries its own copy of the fetch: Hermes runs it from `<HERMES_HOME>/agent-hooks`, outside this package |
| `tools/ambient.mjs` | anything with Node | the one implementation every wrapper calls for the credential and for composing the ambient text. `hermes/` is the exception on the HTTP call itself, and says why |

Hosts not named here need nothing extra: the Skill plus the host MCP tools is the whole integration. Cursor is
in that position with a twist - `centricmem setup --install-hooks` writes the equivalent pair into a code
repository, so a Cursor session refreshes itself and files its own card.

Lifecycle hooks are **optional**. The baseline is this Skill plus the MCP tools: an agent with no hooks still files normally. Ask if you need the hook design.

## Do not

- Curl librarian HTTP (or CLI `note` / `keep` / `done`) when MCP is the Skill path
- Wait for 收尾 / close / wrap up / "log this" before filing a finished chunk (sweep before you yield — SKILL §4)
- `setup --bootstrap` on a guest machine
- Uninstall the agent’s own memories or write back into them
- Put secrets in cards
- Ask the human to paste a key, token, or transcript jsonl. If they leaked a key, they sign in and rotate it on Keys.
- Load attach originals into the chat
- Stop after a titled keep stub or a title-only card — every card needs a summary and key points in the body
- Treat this git checkout as the memory disk
- Write `unclassified` — pick or create a named shelf. Writes without one are 400 `LIBRARY_REQUIRED`.

## Host-side checklist (hand this to the host, not to us)

A host that reports a broken MCP connection usually has one of these, and none of them are fixable from the librarian:

- **"Connected" must mean "callable".** Discovery and invocation have to share one handshake; when they disagree the state should read *degraded* with a one-click restart, not *connected*.
- **A secret written by the host must reach the process that uses it.** After a key is stored, the current session and its MCP child processes need the new value (or the host must say "restart MCP"). A stale environment is indistinguishable from a user pasting the old key.
- **Print three fingerprints on demand** - stored secret, process env, and which credential type the MCP call actually used (Bearer or OAuth) - prefix plus fingerprint only, never the secret.
- **Keep `mcp-remote: Unauthorized` and "the key is wrong" apart.** The first is usually a stale local bridge token: re-authorize, clear `.mcp-auth`, or switch to HTTP.
- **Per-session MCP bridges need to be resettable.** When an old long-running session stops answering but a fresh probe reaches the server, the fix is "reset this chat's MCP", not a machine update.

What we can report is now in `cm_health` and `cm_doctor`: `auth=oauth|bearer|missing` and `keyFp` (12 hex, the same value the new-network notices show), so a host's fingerprints can be compared with ours instead of guessed. The librarian cannot report a *transport*, because there is only one: the hosted service answers on **streamable HTTP** and offers no stdio transport to select. A client configured for stdio cannot reach it at all - that is not a misconfiguration to diagnose, it is a host declaring a server that does not exist.

## One core, one source

A machine with several agents ends up with this Skill more than once: the open skills CLI always writes a canonical copy into the shared hub (`~/.agents/skills`), while a host that installs the package as a plugin keeps its own copy. Nothing is broken by that, but a host can then show two `centricmem-agent` entries and load the stale one - ZCode did exactly that, and Codex, Hermes and a private desktop agent of ours have all been seen holding a copy of their own.

So: **keep the newest copy and remove the older ones** - a plugin copy that your host actually loads is the one to refresh when it lags, and the hub copy is the fallback for hosts that cannot take a plugin. What matters is that one of them is current, and that a host is not left choosing between two. `cm_doctor` now reports every copy it can see (`skill_copies`), and `node tools/prune-duplicate-skill.mjs` prints the plan - it only ever removes centricmem copies, keeps the newest, and does nothing without `--apply`.
