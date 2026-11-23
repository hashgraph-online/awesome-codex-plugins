# Recommended Codex setup

These optional user-level instructions and configuration defaults complement the marketplace plugins across all projects. Review and adapt them to your own security requirements, tools, and working style.

For a new empty or essentially empty repository, follow the [New repository setup recipe](new_repo_recipe.md). With Toolkit installed and enabled, start it in a Plan-mode chat with `$toolkit:perform setup-new-repo`.

## Computer administration workspace

For software installation, configuration, networking, and other machine maintenance, follow the [Computer administration workspace recipe](computer_setup_recipe.md) and its [workspace templates](templates/computer_workspace.md). It establishes `~/Agents` as the normal entry point, with a concise `AGENTS.md`, current machine/software records, confirmed preferences, pending tasks, ignored local resources, and an automation inventory for maintained scripts, desktop launchers, and service/timer definitions. User helpers can use stable links; privileged automation uses reviewed deployed copies, with activation and source changes explicitly approved. Each computer has its own private Git repository. This optional documentation workflow requires no plugin action or development-project scaffolding.

## User-level instructions

This repository includes a recommended [user-level AGENTS.md file](../AGENTS_user.md) with global Codex instructions that complement the plugins. Review and adapt it as desired, or directly copy it into your Codex home directory:

```bash
cp AGENTS_user.md ~/.codex/AGENTS.md  # <-- CAUTION: Check first whether you have an existing AGENTS.md that might get clobbered!
```

Codex applies `~/.codex/AGENTS.md` as user-level guidance across all your projects. If that file already exists, merge the recommendations into it instead of overwriting your existing instructions.

## User-level configuration

The following generic defaults are a practical starting point for `~/.codex/config.toml`:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
model_reasoning_effort = "medium"
plan_mode_reasoning_effort = "high"

[history]
persistence = "save-all"
max_bytes = 52428800
```

You can additionally opt in to live web search and outbound network access for sandboxed commands. Merge these entries into the appropriate locations rather than duplicating TOML tables; `web_search` is a top-level setting.

```toml
web_search = "live"

[sandbox_workspace_write]
network_access = true
```

Command network access allows package managers such as `pip`, `uv`, `npm`, and `cargo` to query registries and download dependencies. Live web search and command network access both increase exposure to untrusted external content, so enable them deliberately.

Use `/model` within Codex to choose a model available to your signed-in account and set its reasoning effort. To pin a preferred model across sessions, save the selection when offered or add a top-level `model` setting using the exact available identifier. Revisit `/model` when switching to a newer model rather than copying an aging model name from a setup example. Keep default-mode reasoning at `medium` and Plan-mode reasoning at `high` as shown above.

For projects using pre-commit, include its normal cache root. For Python development, add these writable roots to the same `[sandbox_workspace_write]` table to let `pip` and `uv` reuse their caches and let `uv` manage downloaded tools and Python installations:

```toml
writable_roots = [
    "~/.cache/gh",
    "~/.cache/pip",
    "~/.cache/pre-commit",
    "~/.cache/uv",
    "~/.local/share/uv",
]
```

The following is one possible TUI setup for a detailed status line and informative terminal title:

```toml
[tui]
status_line = ["project-name", "git-branch", "model-with-reasoning", "run-state", "task-progress", "context-used", "total-input-tokens", "total-output-tokens", "five-hour-limit", "weekly-limit", "thread-title", "session-id"]
terminal_title = ["activity", "project-name"]
theme = "catppuccin-mocha"
show_tooltips = false
copy_on_select = "auto"
right_click_paste = "off"
```

These are optional personal preferences. Use `/theme` to preview and save another theme; `show_tooltips = false` hides welcome-screen onboarding tips. `copy_on_select = "auto"` copies mouse selections on release where Codex's terminal detection enables it. `right_click_paste = "off"` disables Codex's fullscreen right-click paste fallback, while the terminal's own paste binding remains available. Both mouse settings are current settings defined in [Codex's TUI configuration](https://github.com/openai/codex/blob/main/codex-rs/config/src/types.rs). Newer optional TUI settings may require a CLI newer than the marketplace's minimum supported version; update the CLI or omit an unsupported preference. See [CLI customization](https://learn.chatgpt.com/docs/cli-customization).

See [Marketplace plugin installation](installation.md) if the `la-review` and `toolkit` plugins are not installed yet. After completing the user-level setup, continue with [Language-agnostic project setup](project_setup_agnostic.md) for each repository and then [Python project setup](project_setup_python.md) when applicable.

## Optional apps and memories

For a local coding setup, consider keeping app connectors and cross-chat memories off until you need them. Merge this table into `~/.codex/config.toml`, preserving unrelated feature settings:

```toml
[features]
apps = false
memories = false
```

`apps = false` disables app/connector integrations and avoids their associated tools and context when unnecessary. Codex then cannot use those connected services; opt in with `apps = true` when you need them. The amount of context avoided depends on the enabled integrations and CLI version. This flag does not disable all plugins, independently configured MCP servers, or web search. See the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

`memories = false` disables the local memory feature, including using learned context from earlier chats and generating new memories. You lose automatic cross-chat recall, but can still keep durable guidance in `AGENTS.md`. Opt in with `memories = true` if you want that recall. Disabling the feature does not delete stored memories or conversation history. Local Codex memory is separate from ChatGPT web memory. See [Memories](https://learn.chatgpt.com/docs/customization/memories).

### Inspect existing memories

Resolve the Codex home used by the client, then list generated memory files without printing their contents:

```bash
codex_setup_home="${CODEX_HOME:-$HOME/.codex}"
printf 'Codex home: %s\n' "$codex_setup_home"
for codex_memory_dir in "$codex_setup_home/memories" "$codex_setup_home/memories_v2" "$codex_setup_home/memories_extensions"; do
    if [ -d "$codex_memory_dir" ]; then
        find "$codex_memory_dir" -type f -print
    fi
done
```

Open selected files locally in your editor to review summaries and supporting evidence before sharing them. Older homes can use `memories/`, newer homes can use `memories_v2/`, and migration or extensions can leave multiple stores. Treat these files as generated state rather than hand-editing them as the primary control. When memories are enabled, `/memories` controls whether the current chat uses existing memories or contributes to future generation; it is not a memory-delete command.

### Clear local memories

In the ChatGPT desktop app, use **Settings > Personalization > Delete Codex memories** and confirm the selected machine. Where Computer History is available, this also clears it. This does not manage ChatGPT web memory, which has separate controls.

For a terminal-only reset, Codex CLI `0.170.0` also has the hidden internal command below. It is version-dependent, not part of this marketplace's minimum CLI guarantee. First check availability without deleting anything:

```bash
codex debug clear-memories --help
```

Before actually resetting, stop affected Codex sessions and background clients, preserve any memory artifacts you want to keep, and confirm the Codex home displayed above is the intended one. Keep `features.memories = false` if you want memory use and generation to remain off. Run the reset from outside a repository with project-specific Codex settings, retaining the same `CODEX_HOME`, `CODEX_SQLITE_HOME`, or `sqlite_home` configuration as the client whose memories you intend to clear:

```bash
codex debug clear-memories
```

This clears generated memory directories and persisted memory-generation state, rather than deleting your conversations. OpenAI's [reset tests](https://github.com/openai/codex/blob/main/codex-rs/cli/tests/debug_clear_memories.rs) cover directory cleanup and persisted state. Deleting only one memory directory is incomplete because database state and other memory stores can remain. If the command is unavailable, use the desktop reset or update the CLI; do not delete whole Codex databases as a workaround.

Check that the command exits successfully and reports the expected storage paths. Repeat the file listing to confirm generated artifacts are gone, then restart the client. Existing chats may already contain injected memory context, so use a new chat when checking the result. If memory generation is re-enabled later, eligible retained chats can contribute to new memories again.

## Local storage

The `[history]` example above retains prompt history with a 50 MiB (`52428800` byte) cap on the history file, dropping older entries as needed. It does not cap the entire Codex home or all conversation storage. Sessions, thread-history databases, SQLite companion files, logs, and generated memories have separate storage lifecycles. Disabling history persistence or clearing memories does not imply that all those files have been deleted.

Inspect disk usage without modifying stored data:

```bash
codex_setup_home="${CODEX_HOME:-$HOME/.codex}"
du -sh "$codex_setup_home"
du -sh "$codex_setup_home"/*
```

The second command omits hidden entries. If you configured `CODEX_SQLITE_HOME` or `sqlite_home`, inspect that directory separately too. Use supported conversation and memory deletion controls for the data you intend to remove; do not remove active databases or their journal/WAL files merely to satisfy the history cap. See [history persistence](https://learn.chatgpt.com/docs/config-file/config-advanced#history-persistence) and [config and state locations](https://learn.chatgpt.com/docs/config-file/config-advanced#config-and-state-locations).

### Measure and clean up stored sessions

To measure saved session files and session-related databases, including archived conversations, run:

```bash
codex_setup_home="${CODEX_HOME:-$HOME/.codex}"
codex_session_db_home="${CODEX_SQLITE_HOME:-$codex_setup_home}"
for codex_session_path in "$codex_setup_home/sessions" "$codex_setup_home/archived_sessions" "$codex_session_db_home"/state_*.sqlite* "$codex_session_db_home"/thread_history_*.sqlite*; do
    if [ -e "$codex_session_path" ]; then
        du -sh "$codex_session_path"
    fi
done
```

If `sqlite_home` is configured in TOML instead of the environment, set `codex_session_db_home` to that directory. The state database also contains metadata beyond transcripts; these figures identify the main storage locations rather than an exact per-session accounting. Modern Codex can store history in databases, so measuring or deleting only `sessions/**/*.jsonl` is insufficient.

Use Codex's built-in deletion controls rather than selecting sessions through an internal SQLite schema. In CLI `0.170.0`, `codex delete` accepts a session UUID or name, but has no delete-all or older-than option:

```bash
codex delete SESSION_UUID
```

Review the confirmation before deleting. Inside a session, `/delete` deletes the current chat. Deletion also removes delegated descendant sessions. Archiving only hides a session from active lists; it does not delete its stored history. See [Codex deletion commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-delete).

For a built-in bulk option, use the ChatGPT desktop app's Codex chat history. Archive the chats you want to remove, then open **Settings > Archived chats > Delete all** and review the confirmation. This removes all archived chats in that scope, including project chats; chats still unarchived remain. Confirm that the app shows the intended machine/account's sessions before deleting: a separate app installation or Codex home may show different history. See OpenAI's [archiving and deletion guide](https://help.openai.com/en/articles/20001333-archiving-and-deleting-codex-chats-in-the-chatgpt-app). If the app does not expose your CLI sessions, use per-session CLI deletion; there is no equivalent supported bulk CLI command in the checked version.

After deletion, stop affected Codex clients and background servers, then remove empty leftover directories below both session roots. The bottom-up traversal removes newly empty parents too, preserves the roots themselves, and does not follow symlinks:

```bash
for codex_session_dir in "$codex_setup_home/sessions" "$codex_setup_home/archived_sessions"; do
    if [ -d "$codex_session_dir" ] && [ ! -L "$codex_session_dir" ]; then
        find "$codex_session_dir" -depth -mindepth 1 -type d -empty -delete
    fi
done
```

Repeat the size check afterward. Deletion makes database pages reusable but may not immediately shrink SQLite files on disk. Clearing conversations is separate from clearing learned memories, the prompt-history file, and diagnostic logs. Removing only `sessions/` and `archived_sessions/` does not clear modern database-backed history, while removing the entire Codex home would also discard configuration, authentication, and plugin state. There is no simple supported CLI wipe of only all session history in the checked version; avoid direct database deletion or schema-dependent cleanup recipes.

## Attention sounds

For optional sounds after completed conversation and built-in review turns, and when approvals or structured questions need attention, follow [Codex attention sounds](codex_notifications.md). Its standalone Python 3.6+ helper assigns a stable pitch per chat, detects Linux/macOS audio players, and includes preview and diagnostic commands. Completion sounds use the root `notify` entry; approval/question sounds additionally use optional lifecycle hooks that the user reviews and trusts through `/hooks`.

This is user-level setup once per machine, independent of marketplace plugin installation. Keep the helper outside project repositories, preserve an existing working setup, and use the same explicitly chosen amplitude for completion and attention sounds: 85% (the default) or 100% (full amplitude). The new-repository recipe offers full sounds, completion-only sounds, or skipping setup when no working setup exists; enabling sounds requires an explicit amplitude choice before previews or configuration changes.

## Project trust

Codex loads `.codex/config.toml` only for trusted projects. A user-level trust entry looks like:

```toml
[projects."/ABSOLUTE/PATH/TO/REPOSITORY"]
trust_level = "trusted"
```

A repository's writable_roots list replaces the user/system list; include every cache it needs. Use `/debug-config` to inspect loaded layers and `/status` to check effective settings. See the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
