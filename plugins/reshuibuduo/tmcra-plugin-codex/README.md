# TMCRA Memory for Codex

TMCRA Memory adds automatic long-term memory to Codex through the public TMCRA API. It does not require access to the TMCRA server.

This repository is the standalone distribution mirror of the plugin maintained in the [TMCRA monorepo](https://github.com/reshuibuduo/tmcra/tree/main/07-tmcra-codex-plugins/tmcra-memory). Download the versioned ZIP and its SHA-256 file from [GitHub Releases](https://github.com/reshuibuduo/tmcra-plugin-codex/releases).

## What it does

- Initializes the global/project scope at `SessionStart` without recalling or injecting memory.
- Recalls relevant global and project memory only after `UserPromptSubmit`, using the current prompt as the query.
- Includes both user records (requirements and facts) and assistant records (Codex work progress and results) in recall, while keeping their actor and provenance labels separate.
- Applies authority in this order: current user instruction, historical user requirements/facts, then historical Codex progress/results. Assistant records never become user statements.
- Captures the completed user/assistant turn at `Stop`.
- Records bounded, redacted tool progress locally during long turns with `PostToolUse`.
- Creates an idempotent continuity checkpoint before `PreCompact`, records `PostCompact`, and restores the local checkpoint plus relevant long-term memory from `SessionStart(source=compact)`.
- Keeps stable user facts in a global layer, each project in a separate scope, and each Codex task as a session inside its project.
- Provides explicit MCP tools for inspecting the latest automatic recall, running a fresh recall, ingesting memory, and checking jobs.
- Can import retained Codex history or bootstrap a baseline from the current repository.

## See what was recalled

Automatic recall stays out of the way during normal work. After Codex finishes an answer, ask **"Show the TMCRA memory used for my latest answer"** or **"查看上一轮回答的召回"**. Codex calls `tmcra_last_recall` with its default `latest_answer` view and shows the global/project evidence and counts promoted by that answer's `Stop` Hook. The new inspection prompt cannot overwrite this completed-answer receipt. Use `view=current_prompt` only to inspect the prompt Codex is processing right now. Neither view runs another search, and both omit internal scope identifiers, database paths, tenant data, and retrieval diagnostics.

Codex Hooks do not expose a third-party custom side panel. The explicit inspection tool is therefore the in-Codex audit surface; the TMCRA desktop application can provide a longer activity history separately.

## Windows installation

Download the versioned release ZIP, verify the adjacent SHA-256 file, extract it to a stable local directory, then run:

```powershell
.\Install-TMCRA.ps1
```

The installer registers the bundled marketplace, installs the plugin into the same plugin registry used by Codex Desktop, enables the Codex Hooks feature, and removes obsolete duplicate TMCRA MCP registrations. It then opens the TMCRA verification page and shows a short user code. Sign in and approve this Codex installation in the browser; the installer receives a scoped access token through PKCE and stores it in the protected local TMCRA configuration. It never prints the access token, device code, PKCE verifier, or delivery receipt. The Token remains short-lived until the installer confirms that the protected config write succeeded. If confirmation is interrupted, rerunning the installer resumes that saved confirmation instead of minting another Token.

After installation, restart Codex Desktop and confirm **TMCRA Memory** appears as enabled in the Plugins page. Run `/hooks`, inspect and trust all nine TMCRA lifecycle hooks: `SessionStart`, `SubagentStart`, `UserPromptSubmit`, `PostToolUse`, `PreCompact`, `PostCompact`, `Stop`, `StopFailure`, and `SubagentStop`. Codex intentionally requires this review; the installer cannot silently grant Hook trust. `StopFailure` only checkpoints the user request when an answer fails; it never stores provider error text as assistant memory. Start a new task and complete one turn, then use the desktop application's **Verify real Codex execution** action or call the `tmcra_status` MCP tool. Ready is reported only after SessionStart, recall, and capture events from the current plugin version have all been observed.

## macOS and Linux installation

Download and extract the same versioned release ZIP, then run:

```sh
sh ./install.sh
```

Node.js 18 or newer and the Codex CLI must be available on `PATH`.

The same browser authorization flow is used on every platform. If a browser cannot be opened automatically, copy the displayed verification link into a browser and enter the displayed user code.

## Account and console

Normal users do not need SSH access or a server API key. Browser authorization links the local Codex installation to the signed-in TMCRA account. Use [tmcra.com](https://tmcra.com) to approve or revoke Codex installations, inspect global/project/session boundaries, view the memory graph, and check server-reported usage and remaining quota. Rerun the installer if the local authorization expires or is revoked.

## Project identity

No project setup is required. The adapter uses `.tmcra/project.json` when present, otherwise Git origin/root identity, and finally the absolute project path. To pin a stable identity before moving or cloning a project:

```powershell
node .\plugins\tmcra-memory\scripts\project_init.mjs --path "D:\work\my-project" --name "My project"
```

Do not copy the same `.tmcra/project.json` into unrelated projects.

## Existing Codex history

The TMCRA Memory desktop application always exposes this flow under **History migration**. After the plugin is installed, a project can be previewed locally before sign-in; importing stays disabled until the account is connected. Choose one project for a read-only preview, review the task/message and excluded-credential counts, then confirm the import in the native warning dialog. The application re-runs the preview in its main process before importing and waits for every accepted write to finish.

Preview is read-only and performs no upload:

```powershell
node .\plugins\tmcra-memory\scripts\history_import.mjs preview
```

After reviewing the result, import one project explicitly:

```powershell
node .\plugins\tmcra-memory\scripts\history_import.mjs import --project "D:\work\my-project" --confirm --wait
```

Use `--source` when the historical transcript points at an older location. The importer includes only user and assistant messages; it excludes reasoning, tool logs, developer instructions, private keys, passwords, and credential-like content.

If the old transcript is gone, create a baseline from the current repository and recent Git history:

```powershell
node .\plugins\tmcra-memory\scripts\project_bootstrap.mjs preview --project "D:\work\my-project"
node .\plugins\tmcra-memory\scripts\project_bootstrap.mjs import --project "D:\work\my-project" --confirm
```

This is a repository snapshot, not reconstructed conversation history.

## Configuration

### Local Writer and background organizer

Ask Codex **“Open TMCRA local model settings”** to open the setup page. The MCP response contains no credential value or setup-session token. The page is served from a temporary random-token session bound to `127.0.0.1`, and it supports separate Writer and background-organizer providers or one shared provider.

Provider settings are shared by the Codex and DeepSeek Harness plugins in `~/.config/tmcra/local-providers.json`. API keys stay in that local user file and are sent only to the provider endpoint while testing a connection. A changed Provider or Base URL requires the key to be entered again, preventing a saved key from being forwarded to another endpoint. The file uses mode `0600` on macOS/Linux; on Windows it removes inherited ACLs and grants access only to the current user and SYSTEM. Any process running as that user can potentially read the file, so use this feature only on a trusted local account.

The saved configuration is active while the Codex MCP process is running. Ingest requests route Writer work, including a forced slow stage, to the authenticated local executor. `tmcra_consolidate` routes an explicit background-organizer job the same way. The executor leases only tasks created with the current device credential, calls the configured OpenAI-compatible endpoint, and returns the parsed JSON result, normalized token usage, and provider request ID. Provider keys and raw provider response envelopes stay in the current user's local process.

The default configuration file is `~/.config/tmcra/config.json`. Environment variables override it:

- `TMCRA_ACCESS_TOKEN`
- `TMCRA_API_KEY`
- `TMCRA_BASE_URL`
- `TMCRA_SCOPE_NAMESPACE`
- `TMCRA_GLOBAL_SCOPE`
- `TMCRA_PROJECT_SCOPE_PREFIX`
- `TMCRA_HOOK_REQUEST_TIMEOUT_MS` (automatic Hooks only; defaults to 9000 ms and is capped at 10000 ms)
- `TMCRA_CHECKPOINT_EVENT_THRESHOLD` (significant tool events before a periodic long-task checkpoint; defaults to 24)
- `TMCRA_CHECKPOINT_BYTE_THRESHOLD` (redacted tool-summary characters before a checkpoint; defaults to 48000)
- `TMCRA_CHECKPOINT_AGE_MS` (maximum active time between tool-progress checkpoints; defaults to 600000 ms)

The normal installer uses device authorization; it does not ask the user to paste a credential. `-ApiKey` on Windows and `TMCRA_SETUP_API_KEY` on any platform remain available only for explicit developer, self-hosted and automated test setups:

```powershell
.\Install-TMCRA.ps1 -ApiKey $env:TMCRA_SETUP_API_KEY -BaseUrl "https://api.example.invalid"
```

Never place a TMCRA API key or access token in a prompt, project source file, browser bundle, command example, or shell history.

## Reliability and privacy

Hooks fail open: an unavailable memory service must not block Codex. Automatic Hook calls use a short request timeout independent from longer explicit MCP operations. Writes are asynchronous and idempotent. The access token is stored only in the protected local TMCRA configuration; it is never ingested as memory. The plugin does not store chain-of-thought or developer instructions. During a long turn it keeps bounded tool input/output excerpts for continuity, applies credential redaction before local persistence, and sends only thresholded or pre-compaction checkpoints rather than one API write per tool call. Passwords, access tokens, verification codes, and private keys are excluded from checkpoint content.

Lifecycle Hooks and the bundled MCP server honor `HTTPS_PROXY`, `HTTP_PROXY`, and `ALL_PROXY`. On Windows, when those variables are absent, the runtime launcher also reads the enabled per-user system proxy so Codex works with proxy clients that use a fake-IP DNS range. Loopback TMCRA endpoints bypass the proxy.

## Development verification

```sh
npm ci
npm run verify
npm run build:release
```

The deterministic suite starts isolated mock services and does not read normal Codex history or contact the public TMCRA API. It verifies Codex and Claude Code lifecycle contracts, device authorization, scope isolation, durable writes, credential redaction, MCP tools, history preview/import rules, repository bootstrap, and release packaging on Windows and Linux.
