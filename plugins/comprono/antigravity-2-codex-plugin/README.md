# Google Antigravity Codex Plugin

Created by [comprono](https://github.com/comprono).

This Google Antigravity Codex Plugin is a community local Windows bridge for Codex and Google Antigravity. It helps OpenAI Codex Antigravity workflows connect to the Antigravity 2.0 desktop app using a Codex MCP plugin, DevTools MCP Antigravity controls, and local helper commands.

This is a local Codex plugin that helps Codex connect to the Antigravity 2.0 desktop app on Windows. It can open Antigravity, inspect whether it is running, discover the Chromium DevTools endpoint exposed by the Electron app, read model quota state from the local language server, inspect visible projects and chats, verify the visible model, and hand off prompts into Antigravity conversations.

After setup, you can start from the ChatGPT mobile app, open Codex, and use this local plugin as the bridge into your Windows Antigravity desktop session.

## Google Antigravity Codex Plugin

This is a community Codex plugin for Google Antigravity / Antigravity 2.0. It lets OpenAI Codex connect to a local Antigravity desktop app on Windows using MCP tools, Chromium DevTools, and local PowerShell helper commands. It provides an Antigravity 2.0 Codex bridge for people who want Codex, including Codex sessions started from ChatGPT on mobile, to hand off work into a locally running Antigravity desktop environment.

Keywords: Google Antigravity Codex plugin, OpenAI Codex Antigravity, Antigravity 2.0 Codex bridge, Codex MCP plugin, DevTools MCP Antigravity.

## What It Does

- Launches the local Antigravity desktop app.
- Reports install path, user data path, running process IDs, setup readiness, and DevTools port.
- Reports Antigravity model quota state from the local language server.
- Connects to Antigravity's bundled `chrome-devtools-mcp` server when available.
- Exposes local setup/model/status commands as MCP tools, so Codex can use them even when skill files are unavailable.
- Helps Codex inspect live project/chat context from the UI.
- Supports safe handoff to continue an existing chat, start a new chat in an existing project, or start a new project.
- Provides a local privacy scan for sensitive data before publishing changes.

## Requirements

- Windows.
- Antigravity installed at `%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe`.
- Codex plugins loaded from `%USERPROFILE%\plugins`.
- Node.js available on `PATH` for the DevTools MCP bridge.

## Install

Clone this repository into your Codex plugins directory:

```powershell
git clone https://github.com/comprono/antigravity-2-codex-plugin.git "$env:USERPROFILE\plugins\antigravity-2"
```

Then install or refresh the plugin from your Codex personal marketplace.

For a setup check after cloning:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" setup
```

The setup report tells Codex whether Antigravity is installed, whether Node.js is available, whether the bundled DevTools MCP package exists, whether the DevTools endpoint is reachable, and whether the local language-server model-limit API is ready.

## MCP Tools

The plugin registers two MCP servers:

- `antigravity-local`: direct local tools for `quick`, `setup`, `doctor`, `status`, `open`, `repair-live`, `inspect`, `live`, `devtools-health`, `submission-guide`, `prepare-offload`, `submit-offload`, `limits-summary`, `limits`, `models`, `offload-advice`, `handoff-template`, and `privacy`.
- `antigravity-devtools`: Chromium DevTools controls for inspecting and driving the Antigravity UI.

Codex should call `antigravity-local.submit-offload` first when the correct Antigravity project/chat is already selected and the goal is to hand work to Antigravity with minimum friction. It prepares the compact handoff, fills the active composer, and submits with a direct CDP Enter keypress, avoiding repeated `list_pages`, snapshots, fill, key, and evaluate calls. If the MCP tool list is stale and does not show `submit-offload`, use the PowerShell helper `antigravity.ps1 submit-offload` before falling back to DevTools choreography. Use `antigravity-local.prepare-offload` when Codex should show the plan first or when the selected chat is uncertain. For nontrivial workspace, repo, browser, UI, research, planning, debugging, review, implementation, and job-application work, the intended cost split is: Antigravity explores and works locally; Codex plans, gates safety, reviews final changes, and summarizes. Use `antigravity-local.quick` for general setup checks. If `ReadyForLiveUiInspection` is false, call `antigravity-local.repair-live` once before using DevTools. If repair restarts Antigravity, an already-started DevTools MCP connection may need to reconnect to the new port. If `antigravity-devtools` fails with `Transport closed`, call `antigravity-local.devtools-health`; do not keep retrying `list_pages` in the same broken transport. Use `limits-summary` for normal quota checks and full `limits` only when the complete per-model JSON is needed.

## Usage

Check status:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" status
```

Fast combined readiness and quota summary:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" quick
```

Open Antigravity:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" open
```

Repair live DevTools inspection if Antigravity is running but exposes zero pages:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" repair-live
```

Inspect integration details:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" inspect
```

Inspect live UI connection:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" live
```

After a DevTools MCP `Transport closed` error, use the local fallback:

```text
Call antigravity-local.devtools-health.
```

If it reports pages are ready, restart Codex to recreate the DevTools MCP transport or use `antigravity-local.handoff-template` for a manual paste into Antigravity for the current turn.

Report model quota state:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" limits-summary
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" models
```

The `limits-summary` command gives a compact availability summary. The `models` and `limits` commands call Antigravity's local language server over its gRPC-web API (`LanguageServerService/GetAvailableModels` and `GetLoadCodeAssist`) and return the fuller per-model data. This is the same source the Antigravity Models tab uses. It returns per-model quota metadata such as remaining fraction and reset time when available. It does not expose a raw all-model token ledger if Antigravity itself does not publish one.

Run a local repository privacy scan:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" privacy
```

## Codex Operating Model

This plugin intentionally combines two local surfaces:

- Stable status and model-limit checks use local helper commands and Antigravity's local language server.
- Project/chat actions use the live Antigravity UI through the `antigravity-devtools` MCP bridge, because the UI is the source of truth for selected projects, selected conversations, composer state, and model selection.

For chat actions, Codex should verify the target project, conversation, and selected model before sending anything. For new projects or new chats, Codex should use the visible Antigravity controls through DevTools automation and report whether Antigravity accepted the action or showed an error/quota state.

For nontrivial work, Codex should act as the orchestrator, not the main worker. Codex gives Antigravity compact tasks, waits, reads only status artifacts or targeted diffs, reviews the result, and sends the next improvement task back to Antigravity. Codex should avoid duplicating Antigravity's broad file reading, browser operation, and long reasoning unless Antigravity is blocked or final verification requires it.

For prompt submission, Codex should call `antigravity-local.submission-guide` or follow the same rule: fill/type the prompt without a `submitKey`, then click the visible Send/arrow button. If a keyboard submit is required, use a separate key call with a simple accepted key such as `Enter`. Do not use `Control+Enter`, `Ctrl+Enter`, or chord strings unless the active tool schema explicitly lists that exact value; some DevTools tools reject those strings with `Unknown key`.

## Token-Saving Offload Pattern

Use this plugin to make Codex the router and verifier while Antigravity does the long work. Codex should avoid reading huge files, full logs, or full Antigravity chat transcripts. Instead, Codex sends Antigravity a compact handoff, lets Antigravity inspect the workspace locally, and reads back only a small artifact or status checkpoint.

Token savings are not automatic. First decide whether the task is worth offloading:

- Keep Codex direct only for arithmetic, short factual answers, tiny shell checks, small summaries, and prompts that do not need workspace context.
- Use Antigravity by default for project work, implementation, debugging, reviews, planning, research, UI operation, job-search/application workflows, and analysis where Antigravity can inspect local files and write a compact result.
- In existing project chats, assume Antigravity may inspect attached folders before answering. That is useful for real project work and wasteful for tiny tests.
- If Antigravity starts broad folder exploration for a small task, cancel it and answer directly in Codex.

Recommended flow:

1. If the correct Antigravity project/chat is already selected, run `antigravity-local.submit-offload` with `submit=true`, plus `expectedProject` and `expectedChat` when known.
2. If the selected chat is uncertain, run `antigravity-local.prepare-offload`, then use DevTools only to select the project/chat/model.
3. If it returns `codex-direct`, do not open or drive Antigravity.
4. Ask Antigravity to write progress to a small artifact such as `notes/antigravity-status.md`, `plans/antigravity-next.md`, or `reports/antigravity-result.json`.
5. Codex reads only that artifact, a targeted diff, or a compact visible UI status.
6. If the result is incomplete, Codex sends a short follow-up task back to Antigravity with the exact gap instead of pulling broad context into Codex.
7. Codex summarizes for the user after Antigravity has produced a useful result or is clearly blocked.

If a Codex session cannot see MCP tools and can only run shell commands, use the equivalent PowerShell helper:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" prepare-offload -Goal "<goal>" -Workspace "<path>" -StatusFile "notes/antigravity-status.md" -NextStep "<next step>"
```

For selected-chat direct submission through the PowerShell helper:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\plugins\antigravity-2\scripts\antigravity.ps1" submit-offload -Goal "<goal>" -Workspace "<path>" -StatusFile "notes/antigravity-status.md" -NextStep "<next step>" -ExpectedProject "<project text>" -ExpectedChat "<chat text>" -Submit true
```

Use `-Submit false` for verify-only; it should not fill the composer. Use `-FillOnly true` only when the user wants to manually review the handoff before sending.

If UI submission is blocked by a stale DevTools port, use `antigravity-local.handoff-template` to generate the compact prompt and avoid repeated CDP probing. Restart Codex or paste the generated handoff manually so the next session attaches to the current Antigravity port.

Compact handoff template:

```text
Goal: <goal>
Workspace: <path>
Constraints: inspect files locally; do not paste full files, full logs, or full source; use search before reading whole files.
Token rule: work token-efficiently; write progress to <small-status-file>; output max 10 bullets plus changed file list.
Next step: <specific next action>
If blocked: ask one concise question; otherwise continue autonomously.
```

## Safety

This plugin operates only on the local machine and local Antigravity profile. It does not patch Antigravity internals, commit runtime tokens, or call Antigravity cloud APIs directly. Treat Antigravity user data, settings, chats, and workspace files as user-owned state.

Before publishing changes, run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\antigravity.ps1" privacy
```

## License

MIT
