# Rekall

[![CI](https://github.com/DitriXNew/rekall/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/DitriXNew/rekall/actions/workflows/ci.yml?query=branch%3Amaster)
[![HOL Plugin Scanner](https://github.com/DitriXNew/rekall/actions/workflows/hol-plugin-scanner.yml/badge.svg?branch=master)](https://github.com/DitriXNew/rekall/actions/workflows/hol-plugin-scanner.yml?query=branch%3Amaster)
[![Cisco Skill Scan](https://img.shields.io/github/actions/workflow/status/DitriXNew/rekall/hol-plugin-scanner.yml?branch=master&event=push&label=Cisco%20Skill%20Scan)](https://github.com/DitriXNew/rekall/actions/workflows/hol-plugin-scanner.yml?query=branch%3Amaster)

Long Codex tasks accumulate logs, research, and intermediate decisions. Rekall lets the agent clear that accumulated context at a useful checkpoint while keeping a written handoff of the task, constraints, and next step.

The agent saves the handoff, finishes its turn, and asks the Codex VS Code extension to compact the conversation. Rekall can then resume the authorized work once, carrying the verified handoff into the next turn.

**Works with the Codex extension in VS Code on Windows, macOS, and Linux. Standalone Codex CLI sessions are not supported:** Rekall depends on the extension's IPC owner and conversation lifecycle, which its current adapter cannot access for a standalone CLI session.

## Install

Requires Windows, macOS, or Linux, Node.js 20 or newer on PATH, the Codex VS Code extension, and a Codex CLI with the `plugin` commands. The plugin installation commands below work in PowerShell, zsh, and bash.

```powershell
codex plugin marketplace add DitriXNew/rekall
codex plugin add rekall@rekall
```

This installs the MCP server and the bundled skill together. Start a new chat in the Codex VS Code extension, then ask:

> Compact this thread with a handoff, then continue the remaining work once.

To check access without compacting, ask Codex to run `probe_compaction` for the current thread. The repository includes its [marketplace entry](.agents/plugins/marketplace.json), plugin manifest, and MCP declaration; Codex resolves `${PLUGIN_ROOT}` to the installed plugin directory.

<details>
<summary>Or install manually</summary>

Clone the repository and register the MCP server with an absolute path:

```powershell
git clone https://github.com/DitriXNew/rekall.git
Set-Location rekall
npm ci
codex mcp add rekall -- node "$PWD/bridge.mjs" mcp
```

Manual MCP registration installs only the server. Copy `skills/rekall` into `$CODEX_HOME/skills/rekall` (default: `~/.codex/skills/rekall`) to install the skill, then start a new extension chat.

On macOS or Linux, use `cd rekall` instead of `Set-Location rekall`; the other manual installation commands work in zsh or bash.

If migrating an existing manual installation to the plugin, remove the old manual MCP registration and the manually copied skill to avoid duplicate tool/skill discovery. The retired server name was `context-compact`; current manual installations use `rekall`. Keep the job directory so existing jobs and locks remain available.

</details>

## Measured results

**Observed context-token reductions: 78–90%, with automatic continuation about one second after compaction.**

| Run | Context tokens before → after | Reduction | Compaction | Continuation delay |
| --- | ---: | ---: | ---: | ---: |
| Release verification | 102,826 → 10,537 | 89.8% | 87.5 s | 0.908 s |
| Installed-package verification | 55,856 → 12,128 | 78.3% | 88.5 s | 1.065 s |
| macOS ARM verification | 80,137 → 9,216 | 88.5% | 98.4 s | 0.812 s |
| Earlier user-reported run | 91,384 → 10,798 | 88.2% | ~2 min | ~0.9 s |

The resumed agent read the saved handoff in all three measured verification runs. The macOS run also verified its SHA-256 and exact thread/job binding. Linux operation was additionally reported as tested by the maintainer; no Linux token or timing measurements were supplied. See the [sanitized verification record](live-verification.json). Measurement limits and compatibility details are below.

## Scope

Rekall operates on chats owned by the **Codex VS Code extension on Windows, macOS, or Linux**. Standalone Codex CLI sessions, the Codex desktop app, and Claude Code are not supported. The CLI commands below are another way to address an extension-owned chat; they do not add support for standalone CLI conversations. Node.js is required; there is no standalone executable.

Windows uses the extension's named pipe. macOS and Linux use `$CODEX_HOME/ipc/ipc.sock`, defaulting to `~/.codex/ipc/ipc.sock`. Before connecting, Rekall requires the IPC directory and socket to belong to the current user and have no group/other permissions; symlinks at those two paths are rejected. Rekall does not create or change the socket or its permissions, and does not fall back to a shared temporary socket.

## MCP tools

| Tool | Purpose |
| --- | --- |
| `probe_compaction(threadId)` | Read-only compatibility, owner, and thread-state check. |
| `schedule_compaction(threadId, handoff?)` | Queue one compaction after the current response becomes idle. |
| `compaction_status(threadId)` | Read the current job and recorded metrics. |
| `cancel_compaction(threadId, jobId)` | Cancel a dispatch that has not already been sent. |

Read `compaction_status` and `probe_compaction` before scheduling. Use only the exact current `CODEX_THREAD_ID`, and do not queue a second unfinished job. Rekall does not impose a context-use threshold on a user-requested compaction.

## CLI reference

Run these commands from the repository or installed package directory:

| Command | Purpose |
| --- | --- |
| `node ./bridge.mjs probe [threadId]` | Check the current owner, state, and compatibility. |
| `node ./bridge.mjs status [threadId]` | Read the current job's status. |
| `node ./bridge.mjs schedule [threadId]` | Compact without automatic continuation. |
| `node ./bridge.mjs schedule-with-handoff <absolute-handoff-json-path> [threadId]` | Compact with the saved handoff and its explicit resume setting. |
| `node ./bridge.mjs cancel <threadId> <jobId>` | Cancel pending dispatches for the exact job. |
| `node ./bridge.mjs mcp` | Run the MCP stdio server. |

Square brackets denote an optional argument, not literal command text. Commands with an optional `threadId` use `CODEX_THREAD_ID` when it is omitted. `cancel` requires both IDs explicitly; copy `jobId` from status. Outside the extension session, pass its exact known thread ID. Rekall never guesses a thread or chooses the most recently updated conversation. `worker` is an internal subprocess entry point, not a command to launch manually.

Write handoff JSON as UTF-8 **outside the repository** and quote its absolute path. Its format is described next.

## Handoffs and continuation

An optional handoff has this shape:

```json
{
  "summary": "The refactor is complete and its tests pass; release review remains.",
  "preserve": ["User constraints", "Changed files and test results"],
  "discard": ["Repeated command output", "Superseded investigation notes"],
  "nextStep": "Review the package contents, report the result, and stop.",
  "resume": true
}
```

The complete handoff is limited to 32,000 UTF-8 bytes and each list to 40 entries. `discard` identifies conversation history that may be summarized; it never authorizes file deletion. The handoff is stored separately, bound to the thread and job, and checked by SHA-256 before continuation.

Set `resume` explicitly. When it is `true`, `nextStep` must identify concrete work the user has already authorized and include a stopping condition. When the task is finished, the user asked to stop, or further work needs an answer, set `resume` to `false`. An automatic continuation does not authorize another compaction.

After scheduling, finish the current response: the worker waits for idle. Do not wait for compaction within that same active turn. On continuation, read the saved handoff, verify the exact job and its result, and perform only the authorized next step.

Automatic continuation requires fresh telemetry showing reduced context tokens and no more than 60% of the context window in use. Otherwise, including when telemetry is missing or stale, Rekall preserves the compaction result and skips continuation with `resumeSkipped: "insufficient_headroom"`. It rechecks this immediately before resuming. This guard limits automatic continuation; it never blocks compaction itself.

Scheduling does not mean compaction completed. `scheduled`, `waiting_for_idle`, `requesting`, and `accepted` are intermediate states. `completed` requires a newly observed completed compaction record. `resumed` means the owner returned a follow-up turn ID; it does not mean that turn's work succeeded. Rekall records the compaction ID, completion time, resume turn ID, and up to 20 per-thread measurements, including job number, compaction duration, resume delay, reclaimed tokens, and reclaimed fraction.

Before dispatch, Rekall requires stable idle state, no pending permission request, and no unconfirmed submission. New user input or a stopped or failed turn cancels a pending dispatch. A request already sent cannot be recalled. The worker deadline is 15 minutes from worker start, including idle waiting. Timeouts and unknown outcomes are terminal and are never retried automatically.

## Compatibility and extension updates

The full live compaction/continuation cycle has been verified with `openai.chatgpt-26.901.22334-win32-x64` and, on macOS 26.6.2 with Node.js 26.5.0, `openai.chatgpt-26.901.22334-darwin-arm64`. The macOS run passed IPC, exact-thread ownership, runtime layout, and public-schema checks without an override, observed completed compaction, and resumed with a verified saved handoff. The maintainer also reports successful Linux testing; its distribution, architecture, extension version, and measurements have not been recorded here. Intel Mac live verification is still outstanding. Platform paths are covered by isolated tests. Rekall uses an internal extension IPC protocol, which is not a stable public API. Run `probe_compaction` after extension updates.

Rekall accepts any extension version number and checks compatibility through extension identity, public schema, runtime layout, owner/thread binding, and the IPC protocol. A version update alone does not block compaction. Protocol changes can still require an adapter update; accepting a version number does not mean every past or future protocol is supported.

`probe_compaction` reports `compatibility.extensionVersion` for diagnostics. The former `REKALL_ALLOW_UNVERIFIED` setting is no longer needed and has no effect.

Reloaded public history may omit the private `completed` field. Rekall accepts those historical records but does not count them as completion signals. Automatic continuation still requires a newly observed item with `completed: true`. A read-only probe also passed on Windows with extension `26.903.61454`; this is not a live compaction/continuation measurement.

Report update-related failures through the [compatibility issue template](https://github.com/DitriXNew/rekall/issues/new?template=new-extension-version.yml), including the extension version and **redacted** probe output or error. You do not need to attempt compaction to report a failed probe.

Compatibility checks compare the public App Server schema with the internal completion signal Rekall observes. Before a thread exposes a compaction item, the probe reports `layout_compatible`: the public lifecycle and state layout are compatible, while the private completion field has not yet been observed. Rekall locates a unique extension-bundled executable from the extension's PATH entries: `codex.exe` on Windows or `codex` on macOS or Linux. When that is not possible, set `REKALL_CODEX_BINARY` to its absolute path. Schema generation exports files and exits; it does not start another App Server. Test transports using `REKALL_PIPE` deliberately skip the schema subprocess and production endpoint discovery/validation; do not use this test override for a live socket.

## Security

Rekall is designed for a **single-user workstation**. Any local process able to connect to the extension's pipe or socket can interact with its IPC protocol, subject to the extension's own checks. Rekall does not add a separate authentication boundary. Owner/thread checks prevent accidental misrouting; they do not protect against an untrusted process with access to the same account and IPC endpoint.

Linux uses the same private per-user socket location and ownership/permission checks as macOS. Rekall does not authenticate the peer process separately. Globally shared temporary sockets are not supported. See the historical [upstream socket-isolation report #8965](https://github.com/openai/codex/issues/8965). Linux CI uses isolated test sockets and does not establish live extension compatibility.

Read [SECURITY.md](SECURITY.md) for the trust model, handoff-integrity limits, and private vulnerability reporting.

## Data and privacy

Rekall does not export the transcript. It keeps the active thread snapshot in memory while processing state updates. Local `jobs/` files contain thread and job identifiers, timestamps, state, errors, token counts, paths, checksums, and the handoff text the user explicitly asked it to preserve. These files are excluded from Git and npm packages. Do not publish them or include them in bug reports.

Jobs default to `$CODEX_HOME/tools/rekall/jobs`, or `~/.codex/tools/rekall/jobs` when `CODEX_HOME` is unset. Current environment variables use the `REKALL_` prefix. Legacy `CONTEXT_COMPACT_*` names remain aliases, and an existing `$CODEX_HOME/tools/context-compact/jobs` directory is reused so active locks and history are not lost during migration. `REKALL_JOBS_DIR` can select a different local journal directory for isolated use.

## Verification and limits

The measured 78–90% reduction describes context tokens reclaimed in four individual runs, including one earlier user-reported run. It is not a percentage of the full model window, a latency distribution, or a guarantee for another task. The 15-minute deadline has not been validated against a representative workload distribution or very large threads.

The extension's compaction request does not accept custom instructions. `preserve` and `discard` guide the resumed model; they do not override the native compaction prompt or guarantee selective retention. Rekall does not change global Codex permissions or configuration.

## Development

```powershell
npm ci
npm test
npm pack --dry-run
```

[GitHub Actions](https://github.com/DitriXNew/rekall/actions/workflows/ci.yml?query=branch%3Amaster) runs the suite on Windows, macOS, and Linux with Node.js 20 and 22, plus package validation. Tests use dedicated pipes/sockets, temporary job directories, and child processes. They must never target a live conversation. Passing isolated tests does not establish live extension IPC support. A sandbox that prohibits Unix-socket listeners can cause `listen EPERM`; run the isolated suite in an environment that permits local test sockets.

The npm package uses an explicit file allowlist. Inspect `npm pack --dry-run` before publishing. Plugin and marketplace manifests live in `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`; the MCP declaration is `.mcp.json`. The marketplace points to the plugin at the repository root.

The HOL scanner workflow uses a SHA-pinned action with reviewed scanner version `3.0.103`, requires a score of at least 80 and no critical/high findings, and uploads SARIF to GitHub code scanning. It installs Cisco's skill analyzer and requires that analysis to complete. The Cisco Skill Scan badge reflects this combined workflow, including its mandatory Cisco analysis; it is not a separate workflow. Network analyzers and automatic catalog submissions are disabled. For the same local gate in an isolated scanner installation, run:

```text
pipx install "plugin-scanner[cisco]==3.0.103"
plugin-scanner scan . --format text --cisco-skill-scan on --min-score 80 --fail-on-severity high
```

Scanner findings and optional analyzer availability are separate signals; a passing score does not establish runtime safety. Dependency updates are tracked by Dependabot, and `.codexignore` excludes local runtime and build artifacts without excluding source code from review.

Each successful scanner run publishes a JSON report and skill evidence artifact bound to its Git commit and the SHA-256 of `skills/rekall/SKILL.md`. The skill's `metadata.commit` identifies an immutable revision containing the same instruction body; metadata-only changes may differ. CI compares that body before recording a match. Skill tags and language use Codex's supported `metadata` field. Rekall does not add unsupported top-level fields or a self-declared `verified` flag to increase its separate Skill Trust score. Read the report's analyzer status and findings alongside any numeric rating.

This project is licensed under the [MIT License](LICENSE).

## Releases

Pushing a new version tag such as `v0.3.2` triggers the [Release workflow](https://github.com/DitriXNew/rekall/actions/workflows/release.yml). The tag must match the versions in `package.json`, `package-lock.json`, the plugin manifest, and the skill metadata. The packaged MCP must report that same version.

The workflow runs the shared Windows/macOS/Linux CI matrix and the HOL scanner, then builds the npm archive. It checks the package allowlist, verifies a fresh installation and MCP startup, and generates `SHA256SUMS.txt`. GitHub Release publication happens only after those checks pass. Prerelease versions produce prereleases. npm registry publication is separate and is not enabled by this workflow.

After updating and committing all version fields, validate the intended tag and push it:

```text
npm run release:check -- v0.3.2
git tag v0.3.2
git push origin v0.3.2
```

Replace `v0.3.2` with the new package version. Never move a published tag. The workflow must exist in the tagged commit, so it does not retroactively build older tags such as `v0.3.1`.

Use **Run workflow** on the Release workflow for a build-only check without creating a tag or publishing anything. Download its `rekall-release-<version>` artifact to inspect the archive, checksum, release notes, and source manifest. For a local build from a clean committed checkout, run `npm run release:build`; files are written to the ignored `dist/` directory.

On a repeated tag run, matching published assets are left unchanged. Missing or mismatched published assets cause a failure instead of replacement. An interrupted draft can resume its missing uploads; the release becomes public only after both expected assets have been verified.

## Uninstall

Remove a plugin installation with `codex plugin remove rekall@rekall`. For a manual installation, run `codex mcp remove rekall` and remove the manually copied `skills/rekall` directory from your Codex home.

A worker that has already started continues until it records a result or reaches its deadline. Inspect its journal before handling a stale lock; never remove a lock while its recorded process is still running.

## References

- [Codex plugin marketplaces](https://learn.chatgpt.com/docs/enterprise/plugin-management#supported-formats)
- [Codex App Server: trigger thread compaction](https://learn.chatgpt.com/docs/app-server#trigger-thread-compaction)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Issue #33398](https://github.com/openai/codex/issues/33398)
- [Issue #25074](https://github.com/openai/codex/issues/25074)
