# Tree Ring Memory Codex Plugin

Tree Ring Memory is a local-first memory lifecycle practice for Codex agents.

This plugin packages one Codex skill that teaches agents when to recall, write,
audit, consolidate, and forget project memory using the open-source
[Tree Ring Memory](https://github.com/TerminallyLazy/Tree-Ring-Memory) CLI.

Plugin `0.3.6` requires Tree Ring Memory CLI **>= 0.15.0**. The minimum adds
verified project-local bootstrap and scope-preserving CLI updates on top of the
receipt-backed harness, schema-v3, coordinated-write, and idempotency contracts
used by this guidance.

The repository plugin includes native lifecycle hooks and requires CLI `0.15.6`
or newer for automatic recall. Build the separate public-directory ZIP with
`python3 packaging/build-codex-skills-only.py tree-ring-memory-codex-skills-only.zip`.
That generated ZIP includes skills and native Codex lifecycle hooks. The portal
calls the route "Skills only" because this plugin has no MCP server. The upload
preserves executable hook scripts and excludes Claude metadata and commands.
Hooks require Codex or ChatGPT Work, an available CLI, and host trust; ordinary
Chat remains guidance-only. See [OpenAI's current compatibility guidance](https://developers.openai.com/plugins/guides/submit-claude-plugin).

It does not run a background service, scrape chats, or capture transcripts.
The active agent chooses when a memory action is useful, source-linked, and
privacy-safe.

## What It Adds

- Recall before context-dependent project work.
- Concise memory writes for validated decisions, lessons, warnings, and user
  preferences.
- Evidence-backed outcomes through `tree-ring evidence`.
- Same-host worker identity, scoped fan-out/fan-in, and idempotent retries.
- Optional coordinator-authorized shared publication and protected lifecycle
  writes.
- Receipt-backed harness readiness that distinguishes configured bridges from
  observed use in a fresh agent session.
- Explicit forgetting, redaction, and supersession guidance.
- DOX and Revolve adapter usage with dry-run-first guardrails.
- Verified project-local CLI bootstrap and scope-preserving update guidance.

## Install Tree Ring Memory

From the actual project root, after the user has authorized Tree Ring setup:

Download the official version-pinned `v0.15.0/install.sh` to a temporary file,
verify its SHA-256 is
`ef0d5eb8f09cbe2e4c3abe80ee9a98a56759c89ad4ddd103d6c68314cd653ade`, inspect
it, then run these commands from the project root:

```bash
sh <verified-installer-path> --project --init --release latest --no-animation
.tree-ring/bin/tree-ring --root .tree-ring integrations status --verbose
```

Do not pipe a network response directly to a shell.

The verified prebuilt installer supports macOS ARM64 and Linux x86_64. Homebrew
remains available on macOS with `brew install tree-ring`. The agent may proceed
when the user's request already authorizes setup; otherwise it obtains
permission before the download or software installation.

Verify the installed core before using this wrapper:

```bash
tree-ring --version
```

The result must be `tree-ring 0.15.0` or newer.

Use `tree-ring update --check` for a read-only release check. With update
authorization, `tree-ring update` verifies official assets and preserves the
active project-local, direct-prefix, or Homebrew scope. The plugin does not edit
shell configuration, change global installation scope, or claim a memory action
ran without the required authorization and observed command output. For other
install paths, use the canonical project README:
<https://github.com/TerminallyLazy/Tree-Ring-Memory#install>.

## Use

After installing this plugin in Codex, ask:

```text
Use Tree Ring Memory to recall durable project context before editing.
Use Tree Ring Memory to capture this validated lesson without storing a transcript.
Use Tree Ring Memory to audit stale or sensitive memory before closeout.
Use Tree Ring Memory to preview DOX contract summaries before syncing them.
```

The skill will look for project-local `.tree-ring/SKILL.md` and
`.tree-ring/CLI.md` files first. If they are absent, it falls back to the public
CLI commands documented in the main framework repository.

For DOX projects, it reads the applicable `AGENTS.md` chain before edits and
keeps the live contracts authoritative. DOX sync is dry-run-first, persists only
concise source-linked summaries, and never rewrites the source contracts.

For installed-runtime evidence, use `tree-ring integrations certify` or
`tree-ring recall-quality`. The full `scripts/certify-tree-ring.sh` release suite
requires a complete Tree Ring framework source checkout and is intentionally not
bundled in this plugin.

On a host without local shell and project-file access, the skill remains useful
as memory-lifecycle guidance but cannot perform Tree Ring recall, capture,
audit, activation, or forgetting.

## Receipt-Backed Harness Readiness

For a new project, start with:

```bash
tree-ring init
tree-ring integrations status
```

Configuration is not activation proof. A harness is `active` only after a
fresh, matching receipt shows scoped recall and safe context injection from a
new session. States such as `configured-awaiting-proof`, `needs-trust`,
`needs-plugin`, `needs-project-mount`, `needs-user-review`, and `unsupported`
remain explicitly non-active. Use `tree-ring integrations status --verbose`
for diagnosis; do not manufacture bridge files or receipts.

## Same-Host Multi-Agent Contract

Tree Ring supports concurrent workers sharing one root only when they run on
the same host and use a local filesystem. It is not a distributed lock service
and does not claim safe cross-host, NFS, or network-filesystem database sharing.
Use separate per-host roots and an explicit evidence-preserving fan-in when
work spans hosts.

Give every worker a unique agent profile and operation ID, while sharing the
workflow and session for one fan-out attempt:

```bash
tree-ring --root .tree-ring remember "Storage worker validated WAL behavior." \
  --event-type lesson \
  --scope agent \
  --project example-service \
  --agent-profile worker-storage \
  --workflow-id release-readiness \
  --session-id attempt-1 \
  --operation-id validate-storage-v1 \
  --source-ref runs/release-readiness/worker-storage.json
```

An exact retry reuses the original session and operation IDs and the same
payload. Reusing the operation key with changed metadata or content fails
closed. At fan-in, the coordinator recalls the shared workflow/session without
an agent-profile filter, inspects source references, and writes an explicit
source-linked summary.

## Coordinated Write Policy

Stores start in Open mode. Enable Coordinated mode when ordinary workers should
write only non-heartwood memories to their own agent partition and a designated
coordinator should own shared publication:

```bash
tree-ring --root .tree-ring policy enable --coordinator release-coordinator
# Set and export TREE_RING_COORDINATOR_TOKEN with a history-safe, no-echo prompt
# supported by your shell, or inject it through an approved secret manager.
tree-ring --root .tree-ring policy status
tree-ring --root .tree-ring policy audit --limit 100
```

The capability is printed once. Put it only in
`TREE_RING_COORDINATOR_TOKEN`; never pass it as a CLI flag or retain it in
memory, logs, source refs, transcripts, scripts, or committed files. Do not
paste it into an `export` command; use a history-safe, no-echo prompt supported
by the current shell or approved secret-manager injection. Inject it only into
coordinator processes and launch ordinary workers with the variable unset.

In Coordinated mode, the coordinator capability is required for shared or
non-agent writes, heartwood creation/promotion, import, persisted DOX/Revolve
sync, persisted consolidation, ring changes, supersede/delete/redact, and
maintenance with apply or repair flags. Recall, export, policy status/audit,
adapter and consolidation dry-runs, and report-only maintenance remain
read-only.

## Schema-v3 Upgrade Fence

Before opening a pre-v0.13 store with a current release:

1. Stop every Tree Ring CLI, TUI, plugin, and bundled worker using the root.
2. Checkpoint SQLite WAL state and make a verified backup.
3. Upgrade every CLI, plugin, and bundled worker.
4. Reopen with the current release to migrate the store to schema v3.

Do not reopen the upgraded root with v0.12. Schema v3 fences old memory
inserts, updates, and deletes, and all mixed-version operation is unsupported.
Rollback requires stopping every process and restoring the complete pre-upgrade
backup.

## Canonical Project

- Framework repo: <https://github.com/TerminallyLazy/Tree-Ring-Memory>
- Canonical v0.15 skill: <https://github.com/TerminallyLazy/Tree-Ring-Memory/blob/v0.15.1/skills/tree-ring-memory/SKILL.md>
- v0.15 release: <https://github.com/TerminallyLazy/Tree-Ring-Memory/releases/tag/v0.15.1>
- Launch page: <https://terminallylazy.github.io/Tree-Ring-Memory/>
- Homebrew tap: <https://github.com/TerminallyLazy/homebrew-tree-ring>

## Security

This plugin ships instructions only. It does not include remote MCP servers,
webhooks, analytics, credentials, or networked runtime code.

See [PRIVACY.md](PRIVACY.md), [TERMS.md](TERMS.md), and
[SECURITY.md](SECURITY.md) for data handling, use terms, and disclosures.

## Install The Hook-Capable Plugin

```bash
codex plugin marketplace add TerminallyLazy/tree-ring-memory-codex-plugin
codex plugin add tree-ring-memory@tree-ring-memory
```

Review and trust the Tree Ring hook definitions in Codex, then start a new session.


## Automatic Lifecycle Hooks

The repository plugin registers exactly `SessionStart`, `SubagentStart`,
`Stop`, and `SubagentStop`. Each hook forwards its event JSON directly to the
local CLI and waits synchronously for at most 10 seconds. It does not register
prompt, tool, compaction, or `SessionEnd` hooks; run a background service;
scrape chats; or ship an MCP server.

Session start covers startup, resume, and compaction rehydration when the host
reports those sources. Subagent start gives each worker an independent,
receipt-backed preflight. Codex requires review and trust of the installed hook
definition before it runs. Claude Code loads the hook with the enabled plugin.

Startup recall loads a bounded brief of shared project guidance and this
agent's durable memories, including captures from earlier sessions. Workflow
and session memories remain limited to their matching scope. It does not
depend on memories containing special startup keywords. Use targeted recall
when the task changes; the startup brief is not an exhaustive search.

Stop and subagent-stop enforce one agent-mediated memory checkpoint. The
lifecycle parser uses only stable harness identity and project fields; it never
inspects or persists `transcript_path`, `last_assistant_message`, prompts, or
transcript content. The checkpoint asks the active agent to evaluate its
already-grounded work. If and only if that evaluation yields a concise,
durable, normal-sensitivity candidate, the agent automatically runs the exact
strict `tree-ring capture` command template returned by the lifecycle handler.
Strict capture fixes agent scope, requires identity and provenance, adds an
automatic-capture tag, and rejects sensitive candidates. No candidate means no
memory write. This is one bounded checkpoint, not a recorder or automatic
summary of every turn.

The hook wrapper resolves the Git project root when available, prefers that
project's `.tree-ring/bin/tree-ring`, and otherwise uses `tree-ring` from
`PATH`. It then invokes the shared lifecycle entry point with the project-local
`.tree-ring` root. An unavailable or incompatible CLI is not active-harness
proof and cannot be reported as a successful checkpoint or capture.

When project activation has already installed the managed lifecycle definition
in `.codex/hooks.json` or `.claude/settings.json`, that project definition owns
recall and stop checkpoints. The marketplace wrapper detects the exact managed
marker and exits without invoking the CLI, preventing duplicate context,
receipts, checkpoint continuations, or capture attempts when the host merges
project and plugin hooks.

`integrations status --verbose` reports the last validated recall's result
count and query class. A zero-result receipt proves the check ran; it does not
prove that useful context was found. Older skills-only packages omitted
automatic lifecycle hooks. Current Git and public upload packages include them. A newly configured Codex hook still needs
the host's trust flow and a new session before automatic execution can be
verified.

Installer onboarding requires CLI 0.15.7 or newer to create the activation
manifest and native project hooks in the same install action. On earlier 0.15
CLIs, run `tree-ring init` explicitly after the installer. Onboarding readiness
is configuration; a fresh host receipt is required to prove automatic recall.
