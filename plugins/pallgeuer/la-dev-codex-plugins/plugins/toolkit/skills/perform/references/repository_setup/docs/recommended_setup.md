# Recommended Codex setup

These optional user-level instructions and configuration defaults complement the marketplace plugins across all projects. Review and adapt them to your own security requirements, tools, and working style.

For a new empty or essentially empty repository, follow the [New repository setup recipe](new_repo_recipe.md). With Toolkit installed and enabled, start it in a Plan-mode chat with `$toolkit:perform setup-new-repo`.

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

You can also opt in to pinning a preferred model with the following top-level setting:

```toml
model = "gpt-5.6-sol"
```

Use `/model` within Codex to select an available model and add or update this setting automatically, especially when switching to a newer model.

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
```

See [Marketplace plugin installation](installation.md) if the `la-review` and `toolkit` plugins are not installed yet. After completing the user-level setup, continue with [Language-agnostic project setup](project_setup_agnostic.md) for each repository and then [Python project setup](project_setup_python.md) when applicable.

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
