> [!IMPORTANT]
> **[`opencode-dejavu`](https://github.com/WhiteBite/opencode-dejavu) has been RENAMED to [`dejavu-gates`](https://github.com/WhiteBite/dejavu-gates) — you are on the new home.**
> The old URL [github.com/WhiteBite/opencode-dejavu](https://github.com/WhiteBite/opencode-dejavu) redirects here permanently.
> - **OpenCode config:** `{ "plugin": ["opencode-dejavu"] }` → `{ "plugin": ["dejavu-gates"] }`
> - **git remote:** `git remote set-url origin https://github.com/WhiteBite/dejavu-gates.git`
> - **npm:** the old package [`opencode-dejavu`](https://www.npmjs.com/package/opencode-dejavu) is deprecated and frozen at 2.27.0; all releases from 2.39.0 are [`dejavu-gates`](https://www.npmjs.com/package/dejavu-gates)

<p align="center">
  <img src="logo/icon.svg" width="96" height="96" alt="dejavu logo — a lowercase d with two amber echo strokes">
</p>

<h1 align="center">dejavu — error gates for AI coding agents</h1>

<p align="center"><b>English</b> | <a href="README.ru.md">Русский</a></p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/harnesses-10-green.svg" alt="OpenCode, Claude Code, Codex, Gemini CLI, Cursor, Copilot CLI, Crush, Devin CLI, Kiro, Cline">
  <img src="https://img.shields.io/badge/TypeScript-Bun-black.svg" alt="TypeScript + Bun">
  <img src="https://github.com/WhiteBite/dejavu-gates/actions/workflows/ci.yml/badge.svg" alt="CI">
</p>

Cross-session **memory prosthesis with teeth** for AI coding agents. Agents repeat the same mistakes because they forget between sessions — and markdown rules don't fix that. dejavu mechanically detects recurring tool-call failures (bash, read, edit, write, glob, grep) and promotes them into enforced gates: a reminder on the next attempt, a hard block on same-session repeat offense. One engine, many hosts: OpenCode (plugin), Claude Code, Codex CLI, Gemini CLI, Cursor, Copilot CLI, Crush, Devin CLI, Kiro (hook-handler CLI), Cline (in-package plugin). TypeScript + Bun, ships as source, no build step.

## Quickstart

```bash
npm install dejavu-gates
dejavu report
```

Tests: `npm run test`

## Supported harnesses

| Harness | Install | Block (pre) | Remind NOTE (post) | Notes |
|---|---|---|---|---|
| **OpenCode** | npm plugin / source | ✅ | ✅ | full integration: all channels, repeat guard, compaction context |
| **Claude Code** | `install-hooks.ts` | ✅ | ✅ | `additionalContext` annotations; `SessionStart` hook injects a gate digest (top enforced gates) at session start; hooks carry no exit codes → text detection |
| **Codex CLI** | `install-hooks.ts` | ✅ | ✅ | hooks are stable and on by default; Pre/PostToolUse fire for every tool (matcher covers `Bash` + `apply_patch`); a first-run trust prompt may still apply to project hooks |
| **Gemini CLI** | `install-hooks.ts` | ✅ | ✅ | BeforeTool/AfterTool |
| **Cursor** | `install-hooks.ts` | ✅ | ✅ | shell events + CC-compatible events |
| **Copilot CLI** | `install-hooks.ts` | ✅ | ✅ | camelCase + PascalCase payload families |
| **Crush** | `install-hooks.ts` | ✅ | ❌ degraded | upstream has PreToolUse only — enforcement + shared store still protect; no post annotations |
| **Devin CLI** | `install-hooks.ts` | ✅ | ✅ | `.devin/hooks.v1.json` root-event merge; Claude-format hooks also auto-import from `.claude/settings.json` |
| **Kiro** | `install-hooks.ts` | ✅ | ✅ | `.kiro/hooks/dejavu-gates.json`; the NOTE rides raw hook stdout (Kiro's context channel); project scope only |
| **Cline** | `cline plugin install --npm dejavu-gates` | ✅ | ✅ | in-package plugin host (`src/cline-plugin.ts`); SDK/CLI/Kanban only — the VS Code and JetBrains extensions have no plugin system; no exit codes → text detection |
| Zed, Aider | — | ❌ | ❌ | no hook API to intercept tool calls — not portable |
| Windsurf, Amp | — | (planned) | ❌ | block-only / fire-and-forget surfaces; deferred until context injection exists |

**Unified store — gates travel across harnesses.** Every host reads/writes the same store (`<repo>/.opencode/dejavu/` + `~/.config/opencode/dejavu/`, `DEJAVU_HOME` overrides). Call signatures are harness-neutral (tool names and arg fields are normalized before signing), so a gate learned in Claude Code fires in OpenCode, Cursor, or anywhere else — and vice versa.

## How it works

```
tool call fails  →  signature normalized (paths/numbers/hashes stripped)
                 →  pattern-key counted, sessions tracked
                 →  3 failures across 2 distinct sessions  →  gate promoted
 next attempt     →  [dejavu] REMINDER (call aborted, agent sees the correction)
 retry fails again →  same-session repeat offense → hard BLOCK on further attempts
 diagnostic cmd   →  gate stays remind-only: the call RUNS and the reminder rides
                     on the failing output as a [dejavu] NOTE (once per session)
```

Design decisions (post-mortem of existing approaches):

- **Remind first, block on repeat.** Pure blocking starts an arms race — the agent routes around gates (`npm` blocked → uses `pnpm`). A reminder with the correction teaches; the block is reserved for ignored reminders.
- **Gate messages are teachers.** Every message carries `CORRECTION:` (what to do instead) and `EVIDENCE:` (N failures across M sessions), not just a prohibition.
- **Mechanical pattern-keys only.** No LLM-based error classification in the hot path — the unreliable component doesn't do reliability work.
- **Two scopes.** Repo-specific gotchas live in `<repo>/.opencode/dejavu/` (committable); patterns seen in 2+ project dirs are agent-level habits and move to `~/.config/opencode/dejavu/`. No single store can see all projects, so a global pattern index (`index.json`) counts distinct project dirs per key and drives the escalation.
- **Gates rot — so they expire.** 60 days without recurrence and a gate is dropped. A gate blocked 10+ times without the error going away gets `review: true` for manual inspection.
- **The metric is recurrence-after-gate.** Tracked per gate as `recurredAfterGate` — if gates don't reduce recurrence, the whole approach is wrong and you'll see it in the data.
- **Enforcement has negative feedback.** The metric acts: a gate that keeps failing after promotion (3+ recurrences across 2+ sessions that reoffended after a reminder) or keeps getting explicitly bypassed (blocking: 3+ `dejavu:proceed` overrides across 2+ distinct sessions; reminding: 5 distinct bypassing sessions, no raw-count bar — bypassing a gate that never interrupts is weaker friction; a single stubborn/injected session cannot disarm a gate) is friction, not teaching — it demotes itself to `watching` and never re-promotes mechanically (`feedbackDemoted`). A human can re-enforce by setting `status` back and clearing `feedbackDemoted` in `gates.json`; the gate then gets a fresh grace window.
- **No identity, no teeth.** A signature whose substance was entirely parameterized away (`cmd <path> <str>`, `node <str>`) matches a whole command family and can never enforce — it may only watch. Over-generic shapes degrade to evidence instead of punishing unrelated calls.
- **Fail-open, always.** The hook CLI never wedges a host: malformed payloads, a broken store, or an internal dejavu bug produce `{}` + exit 0. stdout carries only the decision JSON; everything else goes to stderr.

## Install

Prerequisite for every path: [Bun](https://bun.sh) on PATH (hook handlers run raw TypeScript; no build step).

### One command, any harness (recommended)

```bash
npx -y dejavu-gates install            # auto-detects installed harnesses, installs project-scope
npx -y dejavu-gates install --user     # user-scope (~/.claude, ~/.codex, ...)
npx -y dejavu-gates install --harness claude,cursor --yes
npx -y dejavu-gates uninstall          # removes only dejavu-managed entries, keeps your other hooks
npx -y dejavu-gates hooks --check      # drift report: ok / stale (moved clone) / missing / broken
```

The installer merges idempotently into each harness's config (foreign hooks and fields survive), backs the file up to `<config>.dejavu-bak` before mutating, refuses to touch unparseable configs, and writes hook commands that call the installed package's CLI directly (never `npx` in the hot path — hooks fire on every tool call). Or install the package once (`npm i -g dejavu-gates` or `npm i -D dejavu-gates`) and use the `dejavu` / `dejavu-gates` command instead of `npx -y`.

### Native plugin channels (no npx, auto-updating)

| Harness | Command |
|---|---|
| Claude Code | `claude plugin marketplace add WhiteBite/dejavu-gates` then `claude plugin install dejavu-gates@dejavu-marketplace` |
| Codex CLI | `codex plugin add WhiteBite/dejavu-gates` (hooks are enabled by default; approve the first-run trust prompt if it appears) |
| Copilot CLI | `copilot plugin install WhiteBite/dejavu-gates` |
| Cursor | IDE: `/add-plugin` → browse marketplace → dejavu-gates (or copy the repo to `~/.cursor/plugins/local/dejavu-gates`) |
| Gemini CLI | `gemini extensions install https://github.com/WhiteBite/dejavu-gates` |
| Crush | no plugin system — use the installer above or edit `crush.json` by hand |
| Devin CLI | no plugin marketplace — the installer writes `.devin/hooks.v1.json`; Devin also auto-imports Claude-format hooks from `.claude/settings.json` |
| Kiro | no plugin marketplace — the installer writes `.kiro/hooks/dejavu-gates.json` (project scope; Kiro documents no user-level hooks path) |
| Cline | `cline plugin install --npm dejavu-gates` (or drop `src/cline-plugin.ts` into `.cline/plugins/`); SDK/CLI/Kanban hosts only |

The companion reaction protocol (`skills/dejavu/`) ships inside the plugin bundle and is auto-discovered by the Claude Code, Cursor, and Gemini CLI plugin formats.

### GitHub Packages (authenticated mirror)

Every release is also published to GitHub Packages as `@whitebite/dejavu-gates`. GitHub Packages requires a token even for public packages, so npmjs.com above stays the recommended channel:

```ini
# .npmrc
@whitebite:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=<PAT with read:packages>
```

```bash
npm i -D @whitebite/dejavu-gates
```

### OpenCode

**npm (recommended)** — OpenCode installs it automatically at startup. OpenCode V1 uses the `"plugin"` key; V2 renamed it to `"plugins"`:

```jsonc
// ~/.config/opencode/opencode.json (global) or opencode.json (project)
// OpenCode V1 (@opencode-ai/plugin)
{ "plugin": ["dejavu-gates"] }
```

```jsonc
// OpenCode V2 (@opencode/cli) — or run `opencode plugin add dejavu-gates`
{ "plugins": ["dejavu-gates"] }
```

**From source:**

```bash
git clone https://github.com/WhiteBite/dejavu-gates ~/.config/opencode/vendor/dejavu
cd ~/.config/opencode/vendor/dejavu && bun install
```

```ts
// ~/.config/opencode/plugins/dejavu.ts
export { Dejavu } from "../vendor/dejavu/index.ts"
```

Companion skill (agent behavior protocol): copy `skills/dejavu/` to `~/.config/opencode/skills/dejavu/`.
Status command: copy `commands/dejavu.md` to `~/.config/opencode/command/dejavu.md` (Claude Code, Cursor, and Gemini CLI pick the same command up from the plugin bundle automatically: `commands/dejavu.md` for the first two, `commands/dejavu.toml` for Gemini).

Restart OpenCode. Gates appear automatically as failures recur — nothing to configure.

### Manual / from a clone (all harnesses)

```bash
git clone https://github.com/WhiteBite/dejavu-gates && cd dejavu-gates && bun install
bun scripts/install-hooks.ts --harness claude            # project scope (cwd)
bun scripts/install-hooks.ts --harness claude --user     # user scope (~/.claude/...)
bun scripts/install-hooks.ts --harness codex --dry-run   # preview without writing
```

The generator merges hook entries into the harness's config (`.claude/settings.json`, `.codex/hooks.json`, `.gemini/settings.json`, `.cursor/hooks.json`, `.github/hooks/dejavu.json`, `.crush/crush.json`, `.devin/hooks.v1.json`, `.kiro/hooks/dejavu-gates.json`) pointing at `bun "<clone>/src/cli.ts" <pre|post> --harness <name>`. It is idempotent, preserves other hooks/fields, and refuses to touch an unparseable config.

Harness specifics:

- **Codex**: hooks are a stable feature enabled by default; Pre/PostToolUse fire for every function tool with canonical hook names (`Bash` for shell, `apply_patch` for edits with `Write`/`Edit` matcher aliases, `spawn_agent`, MCP tools under flat names). dejavu's matcher covers `Bash` and `apply_patch`; a first-run trust prompt may still apply to project hooks.
- **Crush**: PreToolUse only (no AfterTool upstream) — dejavu runs degraded: blocking works, reminders can't annotate; the shared store still teaches Crush from gates learned elsewhere.
- **Devin CLI**: hooks live in `.devin/hooks.v1.json` where the file root IS the event map — the installer merges dejavu entries into it and strips them on uninstall, foreign events survive. Devin also auto-imports Claude-format hooks from `.claude/settings.json` (`read_config_from.claude`, on by default), so a Claude install already gates Devin sessions. No user-level hooks file is documented — project scope only.
- **Kiro**: hooks are standalone files under `.kiro/hooks/`; dejavu owns `dejavu-gates.json` there. Kiro blocks on any non-zero hook exit and injects a successful hook's stdout into agent context, so the reminding NOTE rides raw on stdout and an allow writes nothing. Kiro documents no user-level hooks path — project scope only.
- **Claude Code**: `PostToolUseFailure` is wired to the same post handler; payloads carry no exit codes, so failure detection runs on output text (the engine's text channel). The `SessionStart` hook injects a digest of the project's top enforced gates (blocking first, then reminding) as `additionalContext`, so the agent knows the gated calls before losing a first one to a reminder.

Manual invocation (any harness with command hooks):

```bash
echo '{"hook_event_name":"PreToolUse","session_id":"s","tool_name":"Bash","tool_input":{"command":"deploy.sh"},"cwd":"/repo"}' \
  | bun src/cli.ts pre --harness claude --store /repo
# exit 0 + {} = allow; exit 2 + stderr = blocked with a [dejavu] message
```

## Robustness & safety

- **Blocking policy** — only `bash` commands that are NOT diagnostics may ever become blocking gates. Diagnostics and iteration commands (tsc/eslint/mypy/pytest/phpunit/rspec/rubocop/gradle-test/`mvn test`/`dotnet test`/flutter/curl/grep, `dart run`, `go run|build|test|vet`, `cargo run|build|test|clippy`, `swift build|test`...) promote to `reminding` — they annotate the failing output with a `[dejavu] NOTE` (once per session) and never block or interrupt the run, so iterating on tests/builds is never punished. File probes (read/edit/write/glob/grep) stay `watching`: measured, visible in reports, never interrupting. Event-channel `tool-error` signatures (argless calls whose error text is the only identity) promote to `reminding` once their literal head carries enough identity — never `blocking`. `canBlock()`/`canRemind()` in `src/patterns.ts` are the single source of truth. Signatures without residual identity (see above) enforce at no tier.
- **One-liner identity** — for `python -c` / `node -e` / `bun -e` / `php -r` / `ruby -e` / `perl -e` / `julia -e` / `lua -e` / `Rscript -e` and PowerShell `-Command` the code payload IS the call, so it is fingerprinted (`<code:hash>`) instead of flattened to `<str>`: different scripts never share a gate, the same script failing repeatedly still converges. `-r` fingerprints only for php (node/ruby/perl `-r` is a preload flag). PowerShell shapes are covered — quoted exe paths (`& "C:\...\python.exe" -c ...`), here-string payloads, env-prefixed invocations (`PYTHONPATH=x python -c ...`). Legacy bare `-c <str>` shapes never enforce at any tier (residual-identity guard).
- **Wrapper unwrapping** — `cmd /c|/k "..."` normalizes to the INNER command: the gate key, identity and diagnostic tier all see the real call instead of a `cmd <path> <str>` shape matching every cmd invocation.
- **Clean persistence** — terminal control characters (PowerShell VT colors, NULs) are stripped before anything touches disk; signatures, snippets and corrections never carry ANSI escapes. Harness payloads are external untrusted input and cross the same `sanitizeForStore()` boundary before anything is persisted.
- **Secret scrubbing** — every signature and snippet passes `scrubSecrets()` (OpenAI/Anthropic/AWS/GitHub/Slack/Stripe/JWT/bearer/DB-conn-string/PEM patterns + `root@host`) before touching disk. Historical data is cleaned by `migrate()` at init or via `bun scripts/migrate.ts <dirs...>` (also scrubs logs).
- **Intended non-zero exits** — exit 1 from diagnostics is NOT a failure (that is their normal "found nothing / found issues" outcome). Exit ≥ 2 always counts.
- **Aborted ≠ failed** — cancelled/aborted tool executions ("Tool execution aborted") are infrastructure noise and are never counted as failures.
- **Long-running guard** — a FOREGROUND dev-server/watcher start (`npm run dev`, `next dev`, `vite`, `flask run`, `uvicorn`, `python -m http.server`, `mvn spring-boot:run`, `gradle bootRun`, …) would block the bash call until its timeout and strand an orphan process. dejavu interrupts it in the before-hook with a "run detached" reminder (tmux / `nohup … &` / `Start-Process` / a startup script that spawns detached). Detached forms (trailing `&`, `nohup`, `tmux`, `Start-Process`) and one-shots/builds (`vite build`, `npm run build`) pass silently; `# dejavu:proceed` allows a deliberate foreground run. The starter list is deliberately conservative (ambiguous `node <file>`, `go run`, `dotnet run` are not flagged).
- **Suppressed-spawn guard** — compensating measure for [anomalyco/opencode#29831](https://github.com/anomalyco/opencode) (remove when the upstream fix ships): a call that spawns a DETACHED daemon while piping/redirecting stdout (`… start | Out-Null`, `… start > $null`) hangs forever — opencode ends a bash call only on stdio EOF, and the living daemon keeps the pipe open. A static bounded list (`DETACHED_SPAWNERS`) is interrupted in the before-hook with the correction "run the spawn bare (1-3 lines of output) and poll status in a separate call". Bare spawns, non-spawn verbs, and stderr-only redirects (`2>`, `2>&1`) pass; `# dejavu:proceed` bypasses (logged as a warning).
- **Inherited-spawn guard** — the second leak path of the same EOF semantics, empirically verified: `Start-Process -RedirectStandard*`/`-Wait` turns ON handle inheritance, so the spawned process receives the call's stdio pipes and holds them until it exits — a daemon that outlives the call (`-WindowStyle Hidden|Minimized`, or a known server starter as the spawned command) hangs the call forever, and redirecting all three streams does NOT help (a bare `Start-Process` leaks nothing). The before-hook interrupts that shape and teaches bare spawns (daemon writes its own logs) or a two-stage spawn (outer bare `Start-Process` of a pwsh one-liner that redirects inside); `# dejavu:proceed` bypasses (logged).
- **Orphan-job guard** — `Start-Job` without an in-call wait runs inside the call's PowerShell and is killed silently when the call ends: "background" work that never survives, with no error anywhere. The before-hook interrupts it and teaches the detached bare-Start-Process pattern (or `Wait-Job`/`Receive-Job -Wait` for in-call results); `# dejavu:proceed` bypasses (logged).
- **Snowball guard** — an agent re-issuing its own previous bash command verbatim as a strict prefix with a new section appended (command accretion) re-executes every already-answered query and floods the context with duplicate output (the incident: a research subagent issued 30+ growing calls, 46 minutes, no deliverable). The before-hook denies the third consecutive growth call and teaches: issue only the NEW query as a fresh command — the cd/setup prefix belongs in the bash tool's workdir parameter, independent questions are parallel tool calls. Identical re-sends stay the repeat channel's business; `# dejavu:proceed` bypasses (logged).
- **File content is not command output** — in OpenCode, text failure signatures are scanned for `bash` only; `read`/`edit`/`write` failures come exclusively from the event channel (a file containing "TypeError" is not a failure). External harnesses deliver file-tool failures through their post hooks, where the tool's own error text (not file content) is the payload.
- **Concurrency** — gates.json mutations run under an exclusive lockfile; log appends and rotation take their own lock; writes are tmp+rename with EPERM/EACCES/EBUSY retry (Windows AV/indexer). NT long paths get the `\\?\` prefix. Parallel tool calls in the SAME process serialize on an in-process queue before ever touching the file lock. Across processes (several OpenCode windows, or parallel hook-CLI invocations from one harness), if a lock cannot be acquired within 3s the critical section degrades to unlocked (the tool pipeline must never hang) and emits a `degraded` log event. A transiently-unreadable store (AV lock, `EISDIR`) throws instead of parsing as empty, so a failed read can never let the next save clobber real gates.
- **Multi-process safe** — the remind→block escalation chain is persisted on the gate itself (`remindedSessions`/`failedSessions`), not in process memory: several windows, several harnesses, and short-lived hook-CLI processes on one store all see the same chain. Enforcement always reads fresh gate state under the store lock.
- **Near-duplicate consolidation** — new failures merge into existing patterns via normalized Levenshtein ≤ 0.3 with an absolute floor of 3 edits (replaces token Jaccard, which collapsed all `<str>` placeholders; the floor stops `git push` vs `git pull`-style merges).
- **Bounded memory** — per-session maps are capped (50 entries per gate) and freed on session end; handled part IDs evict FIFO; TTL expiry and log rotation re-run every 6 h in long-lived processes (the CLI runs its idempotent init passes per invocation and flushes deferred log events before exit).
- **Migration** — gates outside the blocking policy are re-tiered automatically (diagnostics land in `reminding`, everything else in `watching`); already-proven recurring diagnostics start reminding immediately; project copies of already-global gates are merged into the global gate (evidence is consolidated, never deleted).
- **Self-healing** — every init reconciles the stores: an unparseable `gates.json` is quarantined (bytes preserved as `gates.json.corrupt-<ts>`), gate records are strictly parsed and mechanically repaired (inverted dates swapped, duplicate keys merged, secrets/control-chars re-sanitized, stale blocking demoted), unparseable log lines are excised to `log.jsonl.corrupt`, and the cross-project index is reconciled. Every repair is logged as a `repaired`/`quarantined` event.
- **Gates heal, not just accumulate** — dejavu sees successes too: a SUCCESS matching an enforced gate grows `succeededAfterGate`, and after 3 in a row the gate retires to `watching` (logged `healed`), so a command you fixed stops triggering reminders. A failure resets the streak. The negative twin: a gate the agent keeps fighting (recurrences or explicit overrides) demotes itself (logged `demoted`) — enforcement listens to behavior in both directions. Third path: a gate reminded 5+ times with zero reoffense has TAUGHT its lesson — it retires softly (logged `retired-taught`), re-promotion on new failures stays possible. Fourth path: reminders reaching 10 with 1–2 reoffenses (too ignored for taught, not ignored enough for anti-nag) retire as chronic (logged `retired-chronic`). A gate promoted and retired three times each never re-promotes mechanically — the promote→retire oscillation is terminal (logged `demoted`). Heal-aware: a blocking gate with a live heal streak does not interrupt the first run — it lets a likely-fixed command run and blocks only a repeat failure.
- **Auto-corrections, no manual work** — a promoted gate always ships with a mechanical, overridable default correction chosen by command family (stale `--check` artifacts, failing tests, type errors, network, installs, go/cargo/maven/dotnet/rspec/phpunit/make builds) or from the captured error line, so a gate never sits "NOT TEACHING" awaiting a human. `migrate()` backfills existing gates.
- **Repeat channel (OpenCode only)** — DashScope/Qwen hard-rejects a request whose history carries the same tool call (name + args byte-identical) in consecutive rounds (HTTP 400), and one rejection poisons the session forever. The transform hook scans every outgoing payload statelessly: occurrences past the first of an identical-consecutive series get a `_dejavu_repeat` marker (payload-only, never persisted), a series reaching the tail gets a `[dejavu] REPETITION` note on its last tool result, and a third identical call is hard-blocked in the before-hook. Windowed near-repeats (cosmetic churn — trailing comments, paging offsets, temp scratch paths like `%TEMP%\…\head_cr.md` vs `head_cs.md`, which collapse to one shape) earn a `[dejavu] SHAPE LOOP` note instead. Bypass: `_dejavu_proceed: true` in args (logged as override). No gates, no persistence, no promotion — pure payload hygiene.
- **Loop break (OpenCode only)** — a model that keeps re-issuing the call past the REPEAT STOP message gets an automated user-role message appended to the outgoing payload (payload-only, marked `synthetic`). Blocked tool errors are an in-loop stimulus that weak models read as "retry"; a user-role turn is the one stimulus that reliably forces a text reply and ends the loop. The injection fires only while the same series owns the tail — a real user message or a text reply ends it — and logs `loop-break` once per series.

## Observability (debugging aids)

- Every `log.jsonl` gets an `init` event with `PLUGIN_VERSION`; `detected` events carry `channel` (`exit`/`text`/`event`) and the raw exit code; `reminded`/`blocked` carry `via` (`exact`/`fuzzy`/`segment`). Stale plugin sessions are therefore visible in the data. A long-lived host that finds a store last written by a newer plugin self-surfaces the drift at boot — a warn line plus a `version-drift` log event — instead of waiting for a doctor run.
- `bun scripts/doctor.ts [--repair] [projectDirs...]` — one-command report over every invariant the data model implies: gate shape, duplicate keys, temporal order, nested-token corruption, blocking without evidence, policy violations, index↔gates consistency, stale project copies, missed escalation, log integrity, secrets, version drift. `--repair` heals first (idempotent), then reports. `dejavu report [dirs...]` (the npm bin) runs the same report for any harness, no OpenCode needed.
- `bun scripts/analyze.ts [projectDirs...]` — store summary: statuses, tools, top patterns.
- `dejavu lesson list` / `dejavu lesson set <key> "<one-line fix>"` — review gates whose `correction` is still the machine default and write a human correction onto an existing gate (cannot create gates; promotion stays mechanical). `lesson list --all` includes watching gates; `lesson set --author owner|agent` records who wrote the correction; `lesson retire-when <key> <spec>` declares an external invalidation (`dep:<name>@>=<min>`, `path-present/absent:<p>`, `tag:<name>`) that `doctor` evaluates.
- `/dejavu` command (OpenCode, installed globally) runs doctor first, then reports.
- Hook CLI diagnostics: set `DEJAVU_DEBUG=1` to see engine log lines on stderr (stdout always stays pure JSON).

## Detection coverage

| Channel | Catches |
|---|---|
| exit code + output text (OpenCode `tool.execute.after`) | bash failures (non-zero exit, TS errors, test failures, stack traces) |
| output text only (external harness post hooks — no exit codes exist there) | failure-shaped output: `error TS…`, `FAIL`, `panic:`, `[ERROR]`, PHPUnit/`FAILURES!`, `Fatal error:`, TAP `not ok`, … |
| `message.part.updated` event scan (OpenCode) | tool-level failures (read of missing file, rejected edits) that never reach the after-hook; error text is Sentry-style parameterized |
| chain-segment matching | gates fire even when the gated command hides inside `x && gated-cmd` chains, `cmd /c "..."` wrappers, or `$(...)` / backtick substitutions |
| `experimental.chat.messages.transform` (OpenCode) | repeat channel: consecutive identical tool calls sanitized in the outgoing payload (DashScope 400 prevention) + NOTE at 2nd round, hard block at 3rd |
| companion skill | agent behavior protocol (how to react, when to annotate) |
| `/dejavu` command | status report: active gates, recurrence metric, review flags |

Language ecosystems covered by failure detection: JS/TS, Python, Go, Rust, Java/Kotlin/Scala (Maven/Gradle/sbt), .NET, Ruby, PHP (PHPUnit), Dart/Flutter, C/C++, Elixir; shells: bash, PowerShell, cmd. Not covered (by design): semantically-equivalent-but-syntactically-different failures beyond fuzzy (Levenshtein ≤ 0.3, ≥ 3 edits) matching.

## Data files

| File | Contents |
|---|---|
| `~/.config/opencode/dejavu/gates.json` | global gates (agent habits) |
| `~/.config/opencode/dejavu/index.json` | cross-project pattern index: which project dirs each failure key was seen in (escalation evidence) |
| `<repo>/.opencode/dejavu/gates.json` | project gates (repo gotchas) |
| `*/dejavu/log.jsonl` | every event: detected, promoted, reminded, retry-allowed, blocked, override, expired, recurred-after-gate, demoted, healed, retired-healed, retired-taught, repaired, quarantined, degraded, init |
| `*/dejavu/*.corrupt*` | quarantined corruption (unparseable gates.json, excised log lines) — bytes preserved for forensics; safe to delete after inspection |

The store paths are historical (`.opencode/`) but the store is harness-neutral — ALL harnesses share it. Both files are human-editable. Removing a gate object disables it. Editing `correction` improves what the agent is told. Clearing `feedbackDemoted` (and setting `status` back to `blocking`/`reminding`) re-enforces a gate the agent's behavior retired — it gets a fresh grace window via `feedbackBaseline`.

Project stores keep themselves out of `git status`: init writes a self-ignoring `.opencode/dejavu/.gitignore` — `gates.json` is designed to be committable (shared repo gotchas; it carries repo-relative project paths and session ids, no absolute machine paths), runtime files (log, index, locks, tmp) are ignored — and `doctor --repair` sweeps orphaned `*.tmp` files and stale `*.lock` files (`--prune-corrupt=<days>` opts into deleting quarantine artifacts past the age; default 30 days). A root-level `.gitignore` rule for `.opencode/` overrides the nested re-include — repos that ignore `.opencode/` at the root must adjust their ignore rules to actually commit `gates.json`.

### Environment overrides

`DEJAVU_HOME` moves both store dirs; `DEJAVU_DEBUG=1` prints hook-CLI diagnostics to stderr. The enforcement tunables below can be overridden per process without editing source — each is read once at startup and falls back to its default when the value is not an integer within bounds:

| Variable | Default | Bounds | Effect |
|---|---|---|---|
| `DEJAVU_TTL_DAYS` | 60 | 1–3650 | days without recurrence before a gate expires |
| `DEJAVU_NOISE_TTL_DAYS` | 7 | 1–365 | TTL for one-off patterns (`watching`, count ≤ 1) |
| `DEJAVU_PROMOTE_COUNT` | 3 | 1–100 | failures before a bash pattern becomes a gate |
| `DEJAVU_PROMOTE_COUNT_PROBE` | 5 | 1–100 | failures before a probe tool becomes a gate |
| `DEJAVU_PROMOTE_SESSIONS` | 2 | 1–100 | distinct sessions required to promote |
| `DEJAVU_HEAL_SUCCESSES` | 3 | 1–100 | consecutive successes that retire a gate |
| `DEJAVU_DEMOTE_RECURRENCES` | 3 | 1–100 | post-gate recurrences that demote a gate |
| `DEJAVU_DEMOTE_OVERRIDES` | 3 | 1–100 | explicit bypasses that demote a blocking gate |
| `DEJAVU_TAUGHT_REMINDERS` | 5 | 1–100 | reminders with zero reoffense that retire a gate as taught |
| `DEJAVU_SNOWBALL_CHAIN_MIN` | 3 | 1–100 | consecutive prefix-growth bash calls before the snowball guard interrupts |

## Development

```bash
bun install
bun run typecheck          # tsc --noEmit (index.ts, src/**, scripts/**, test/**)
bun test/smoke.ts          # OpenCode plugin behavioral suite (drives index.ts hooks)
bun test/enforce.ts        # engine characterization (harness-agnostic core)
bun test/adapters.ts       # adapter mapping + decision dialects
bun test/cli.ts            # CLI end-to-end (spawn, promotion, block/annotate, fail-open)
bun test/language-gaps.ts  # language-ecosystem coverage of patterns.ts
bun test/guards.ts         # proactive guards characterization (fire shapes, precedence, bypass)
bun test/messages.ts       # teaching-text framing (tier-truthful, data-label, correction bound)
bun test/property.ts       # seeded generator: normalization/fuzzy invariants
bun test/fuzz.ts           # mutation fuzz: no crash, no invariant break
bun test/env.ts            # DEJAVU_* env overrides: resolved tunables + promotion effect
bun run lint:ast           # ast-grep structural gates (needs ast-grep on PATH)
```

Architecture: `src/patterns.ts` + `src/store.ts` + `src/validate.ts` (pure engine + persistence), `src/enforce.ts` + siblings (harness-agnostic enforcement: `enforceBefore`/`enforceAfter`/`recordEventFailure`/`cleanupSession` over `EnforceContext`), `src/adapters/` (payload ↔ contract mapping per harness), `src/cli.ts` (hook-handler entry for external harnesses), `index.ts` (OpenCode plugin host). Tunables are named constants at the top of their modules (`src/store.ts`, `src/context.ts`, `src/before.ts`, `src/repeat.ts`, `index.ts`).

Structural gates live in `.ast-grep/rules/` (run by `bun run lint:ast` and CI): `no-load-force-flag` forbids `load(true)`/`loadIndex(true)`; `no-raw-gates-splice` forbids raw splices on gate arrays.

## Comparison with analogs

Landscape survey (Sep 2026, ~60 OSS projects + native features checked). The space splits into two camps that never intersect: **guardrail/hook engines** intercept and block tool calls, but only evaluate human-authored static policies per call — no failure memory, nothing learned; **memory/learning plugins** persist and extract across sessions, but only inject context into the prompt — none ever blocks a tool call. dejavu is currently the only shipped project closing the loop mechanically: observe failures → count recurrence (3× across 2 sessions) → promote an enforceable gate → remind/block → heal/demote from behavior.

The three axes that separate every product in the space:

| Product | Learns rules from observed failures | Enforces / blocks tool calls | Mechanical hot path (no LLM) |
|---|---|---|---|
| **dejavu** | ✅ mechanical promotion | ✅ remind→block escalation | ✅ |
| Cupcake · agentjail · cc-safety-net · probity · guardrails packs | ❌ human-authored policy | ✅ deny | ◐ |
| claude-mem · claude-smart · supermemory · opencode-mem · harness-memory | ◐ LLM-extracted, injected only | ❌ | ❌ |
| sinapsis (archived) · harness-forge · projectmem · open-bias | ◐ counted or classified | ❌ advisory only | ◐ |
| NeMo Guardrails · Guardrails AI · LLM gateways | ❌ | ❌ proxy-level | ❌ |
| Claude Code native permissions | ❌ static allow/deny | ◐ | ✅ |

### What nobody else has

- **Learning + enforcement in one loop.** Policy engines block but never learn; memory tools learn but never block. The closest mechanisms died on the way: sinapsis (occurrence counting, multi-session promotion, downvote demotion, TTL — advisory-only, archived Aug 2026), harness-forge (failure ledger with lesson weights, but LLM-classified), projectmem (warns before repeating a failed approach, no teeth).
- **Rules with negative feedback.** A gate the agent keeps fighting (recurrences or explicit overrides) demotes itself; a command that starts succeeding heals to retirement. No analog's policy system adapts to being ignored.
- **Harness-neutral identity.** Signatures are normalized before hashing, so one store shared across OpenCode/Claude/Codex/Gemini/Cursor/Copilot/Crush/Devin/Kiro/Cline means a gate learned anywhere fires everywhere. Analog configs are per-harness by construction.
- **Operational hardening.** Self-healing/quarantining store, doctor report, secret scrubbing before persistence, proactive hang/orphan guards — nothing in the surveyed set ships this surface.

### Where dejavu is worse (honest gaps)

- **Semantic identity.** Two syntactically different calls solving the same broken thing (`pnpm tsc --noEmit` vs `npm run typecheck`) land on different keys; fuzzy merge is Levenshtein ≤ 0.3 with a ≥ 3-edit floor by design. LLM-driven memory tools collapse such variants at extraction cost — dejavu pays precision for determinism.
- **Rule expressiveness.** Gates key on tool-call signatures only. Human-authored policy engines (Rego in Cupcake/agentjail, rulebooks in cc-safety-net, `probity.config.ts`) can express arbitrary conditions — file paths, tenant isolation, PII, "never touch prod" — that dejavu cannot represent. dejavu deliberately does not try to be a security sandbox; those tools are complementary, not competitors.
- **Conversational memory.** claude-mem/claude-smart/supermemory recall decisions, preferences, and project history; dejavu remembers exactly one thing: failing calls. Composable — they occupy orthogonal storage.
- **Traction.** claude-mem (~95k★), claude-smart (~800★), abide (~400★) vs a young repo here.

### Adjacent-by-name, not competitors

- **ast-grep / sloppy / Semgrep-style linters** — check code content statically; dejavu consumes ast-grep for its own repo gates but enforces at runtime on tool calls.
- **NeMo Guardrails / Guardrails AI / LLM gateways (LiteLLM, Portkey, Plano)** — police prompts and responses at the proxy; they never see or intercept the agent's tool pipeline.
- **Reflexion (research)** — verbal self-reflection in an episodic buffer per run; never shipped as a coding-agent plugin, nothing enforced.
- **post_compact_reminder** — a static "re-read AGENTS.md" hook after compaction; dejavu's compaction hooks carry real gate state instead.
- **Hook SDKs (cchooks, cc-hooks-ts, claude_hooks, beyondcode SDK)** — authoring frameworks for writing your own hooks; dejavu is a shipped policy, and its CLI speaks the dialects they target.
- **Native platform features** — Claude Code permissions/checkpoints and OpenCode plugins cover the static halves; neither has cross-session failure learning or recurrence-driven enforcement (the anthropics/claude-code#34556 persistent-memory request was closed unimplemented). If a platform ships this natively, it absorbs the niche — watch, don't assume.

## Stats

The honest answer: dejavu does not ship benchmark numbers, and this section will not invent any. What exists is your own store — every host writes `log.jsonl`, so the evidence is local, per-agent, and auditable.

All-time contents of one developer's global store (`~/.config/opencode/dejavu/log.jsonl`) as of Sep 29, 2026 — 6574 events on 40 active days (Aug 21 – Sep 29), across 11 project dirs and every harness sharing that store:

| Event | Count |
|---|---|
| `detected` failures | 3931 (2431 distinct pattern keys) |
| gates `promoted` | 237 events, 211 distinct keys |
| `recurred-after-gate` | 163 events, 76 distinct keys |
| `blocked` | 56 |
| `override` (`dejavu:proceed`) | 383 |
| healed / retired-taught / demoted | 11 / 46 / 30 |

Reading it carefully: 62 of the 211 promoted keys recurred after their gate existed. That is not a reduction rate — recurrence-after-gate is the per-gate health signal (`recurredAfterGate`), and demotions (30) plus heal/teach retirements (57) are the loop closing in both directions. One person's agent habits over six weeks is a sample size of one; treat it as an example of what the data looks like, not as proof.

**Measure it yourself.** After N sessions of real use:

```bash
dejavu report            # doctor over project + global stores
bun scripts/analyze.ts   # statuses, tools, top patterns
```

or run `/dejavu` inside OpenCode. The metrics that matter are in `gates.json` and `log.jsonl`: `recurredAfterGate` per gate (did the error survive the reminder?), and the `healed` / `retired-taught` / `demoted` events (did the gate retire because you fixed the command, or because it was fighting you?). If your numbers say the approach is wrong, the data will show it — that is the point of the metric.

## Roadmap

- Windsurf / Amp adapters — blocked on usable context-injection surfaces (block-only today); the adapter slots exist
- recurrence-after-gate reporting command; `tool.execute.error` (opencode issue #27900) closed upstream as not planned — event-channel detection remains the supported path
- auto-proposal of ast-grep rules for statically detectable patterns (repo-level CI gates)
- embedding-assisted candidate merging for semantic near-duplicates (advisory only — the enforcement decision stays mechanical; addresses the semantic-identity gap above)
- `dejavu share` — export/merge portable gate bundles between machines and teams (opt-in; gates are already harness-neutral JSON, the command makes moving them explicit)
- docs-as-code — generate the gate/correction reference from the store schema instead of hand-maintaining prose that drifts from `validate.ts`
- env-var overrides — expose the enforcement tunables (promotion thresholds, TTLs, caps) via `DEJAVU_*` env vars alongside the named constants, without a config file
- semantic mapping table — a maintained synonym table (`pnpm tsc` ↔ `npm run typecheck`) feeding the existing mechanical fuzzy merge; advisory only, same as embeddings

## Disclaimer

dejavu is a community project. It is not built by, and not affiliated with, the OpenCode, Anthropic, OpenAI, Google, Anysphere (Cursor), GitHub, or Charm teams.

## License

MIT

## Who is it for

Developers who run AI coding agents daily and watch the same failures recur in every new session — the stale flag, the missing path, the command that only fails on this machine. Three profiles:

- **Solo agent-heavy developers** — gates accumulate from your own `log.jsonl` evidence, so enforcement matches your actual failure history, not a generic rulebook.
- **Multi-harness users** — one store shared across all supported hosts: a gate learned in Claude Code fires in OpenCode, Cursor, or any other harness reading the same store.
- **Teams that want enforcement without hand-written policy** — gates promote mechanically from recurrence (3 failures across 2 sessions) and demote themselves when the agent stops fighting them; humans only edit corrections.

## Use cases

- **A command that keeps failing across sessions.** After 3 failures across 2 distinct sessions a gate promotes; the next attempt is aborted with a `CORRECTION:` reminder, and a same-session retry after a failed reminder blocks.
- **Failing diagnostics that must keep running.** `tsc`, `pytest`, `cargo test` and other diagnostics promote to `reminding` — the call runs, a `[dejavu] NOTE` rides the failing output once per session, nothing is interrupted.
- **Repeated file-probe failures.** Reads of missing files and rejected edits land in `watching` gates — measured and reportable, never interrupting.
- **Foreground servers that strand orphans.** `npm run dev`, `uvicorn`, `next dev` starts are interrupted in the before-hook with a run-detached correction (tmux / `nohup … &`).
- **One habit, every harness.** Signatures normalize before hashing, so the same failing call is gated in whichever host shares the store.
- **Curating what the agent is told.** `dejavu lesson list` surfaces gates still on machine-default corrections; `lesson set` replaces them with a human fix.

## Why choose this

- **Learning and enforcement in one loop.** A Sep 2026 survey of ~60 OSS projects found no shipped tool that both learns rules from observed failures and blocks tool calls — policy engines never learn, memory plugins never block.
- **A mechanical hot path.** Pattern-key counting and Levenshtein ≤ 0.3 fuzzy merging decide every promotion — no LLM in the failure path.
- **Gates answer to behavior.** 3 post-gate recurrences or 3 explicit overrides demote a gate; 3 consecutive successes heal it; 60 days without recurrence expires it.
- **One store, 10 harnesses.** OpenCode, Claude Code, Codex CLI, Gemini CLI, Cursor, Copilot CLI, Crush, Devin CLI, Kiro, and Cline read and write the same gates.

## Examples

Install into specific harnesses and verify the hook wiring:

```bash
npx -y dejavu-gates install --harness claude,cursor --yes
dejavu hooks --check
```

Check gate health — doctor invariants over every discovered store, then per-gate recurrence verdicts:

```bash
dejavu report
dejavu report --recurrence
```

Replace a gate's machine-default correction with a human one (keys come from `lesson list`):

```bash
dejavu lesson list
dejavu lesson set <key> "run pnpm install before building"
```
