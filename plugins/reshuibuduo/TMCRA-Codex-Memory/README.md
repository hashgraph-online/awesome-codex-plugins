# TMCRA Local Memory for Codex

![TMCRA Local Memory: cross-tool memory, continuous work](assets/overview.png)

TMCRA Local Memory lets Codex continue project work across sessions and supported agent tools. It connects Codex lifecycle hooks to the owner-local [TMCRA Agent Memory](https://github.com/reshuibuduo/TMCRA-Agent-Memory) runtime. The plugin sends memory traffic only to the loopback TMCRA API; local-model or BYOK provider traffic follows the runtime configuration chosen by the user.

[中文说明](README.zh-CN.md)

## What it does

- **Continue across Codex sessions.** Each prompt recalls relevant owner-global and current-project evidence before Codex answers.
- **Share project memory across tools.** Compatible adapters resolve the same project through `.tmcra/project.json`, Git origin, Git root, or a canonical directory path.
- **Preserve who said what.** User messages and Codex answers are written as separate, source-attributed records.
- **Keep sessions inside projects.** A session remains provenance and grouping metadata under its project; it is not treated as an independent recall scope.
- **Retry local writes safely.** Temporary runtime failures enter an owner-only local outbox and retry on the next lifecycle event.
- **Protect the host workflow.** Hook failures are fail-open, recalled memory is marked as untrusted data, and common credential formats are redacted before recall or storage.

## Lifecycle

```text
Current prompt
  -> recall owner-global + current-project memory
  -> inject bounded, source-labelled evidence into Codex
  -> Codex answers
  -> store USER and CODEX records separately
```

The plugin uses four Codex hooks:

| Hook | Purpose |
| --- | --- |
| `SessionStart` | Checks the loopback TMCRA runtime and retries queued writes. |
| `UserPromptSubmit` | Recalls relevant memory, injects evidence, and stores the redacted user prompt. |
| `Stop` | Stores the visible Codex answer as a separate assistant record. |
| `StopFailure` | Closes pending turn state without inventing an assistant answer. |

## Requirements

- Node.js 18 or newer.
- A Codex build with plugin marketplaces and Hooks support.
- The [TMCRA owner-local runtime](https://github.com/reshuibuduo/TMCRA-Agent-Memory) installed and listening on an exact loopback address.

The plugin contains the Codex bridge. The memory engine, local API, model selection, storage, and provider configuration live in the TMCRA runtime repository.

## Included Codex Skill

The plugin now ships the real `manage-tmcra-memory` Skill. Codex can activate it when a user explicitly asks to recall prior project context, remember a decision, inspect an asynchronous write, or reconcile a pending write. Normal per-turn recall and capture remain the responsibility of the four lifecycle Hooks, so the Skill does not create duplicate records.

When the standalone [TMCRA MCP Server](https://github.com/reshuibuduo/TMCRA-MCP-Server) is connected, the Skill uses its published recall, ingest, lifecycle, reconciliation, and job-status tools. It preserves project scope, session provenance, message role, and Agent attribution, and it reports pending or failed writes without claiming they succeeded.

## Install from Awesome Codex Plugins

```bash
codex plugin marketplace add \
  'https://github.com/hashgraph-online/awesome-codex-plugins.git' \
  --ref 'main' \
  --sparse '.agents/plugins' \
  --sparse 'plugins'
codex plugin install tmcra-local-memory --source awesome-codex-plugins
```

The registry mirrors this repository as the installable plugin bundle. Source contributors can run the validation commands below without registering a second persistent marketplace.

## Configure the local runtime bridge

Install and start TMCRA first. Then let the TMCRA source checkout write the integration configuration without installing its bundled development copy of the plugin.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-local.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\install-codex-local.ps1 -SkipPluginInstall
```

macOS or Linux:

```bash
./scripts/install-local.sh
TMCRA_SKIP_CODEX_PLUGIN_INSTALL=1 ./scripts/install-codex-local.sh
```

Restart Codex, open `/hooks`, review the four **TMCRA Local Memory** hooks, and trust them. Codex keeps this explicit trust step under user control.

Advanced users can configure a non-default TMCRA runtime directly from this repository:

```bash
node scripts/configure.mjs \
  --runtime-config /absolute/path/to/local-runtime.json \
  --base-url http://127.0.0.1:2009
```

The generated integration config stores only the absolute token-file path. It never copies or prints the bearer token.

## Security boundary

- API destinations are limited to `localhost`, `127.0.0.1`, or `::1`.
- The local bearer token is read from its owner-only file for every request.
- Prompts and responses are bounded and scrubbed for common secret formats before leaving the hook process.
- Retrieved memory is wrapped as untrusted evidence, never executable instructions.
- Diagnostic logs contain a bounded error name and message. They do not contain prompts or answers.
- This repository contains no TMCRA production service code or production credentials.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Development

```bash
npm ci
npm run verify
```

The test suite runs a real loopback HTTP fixture and verifies cross-tool project identity, per-session separation, role provenance, redaction, recall injection, and user/assistant writeback.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
