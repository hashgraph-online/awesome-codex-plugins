# codex-obsidian

`codex-obsidian` is a Codex plugin for local Obsidian workflows through the official desktop `obsidian` CLI.

It currently ships seven focused skills:

- `obsidian-official-cli` for core note and metadata workflows.
- `obsidian-cli-bases-and-bookmarks` for Bases discovery/query and bookmark workflows.
- `obsidian-cli-runtime-admin` for plugin/theme/snippet and command/hotkey runtime administration.
- `obsidian-cli-devtools` for runtime diagnostics and developer-command workflows.
- `obsidian-cli-sync-and-publish` for Sync workflows and capability-gated Publish workflows with explicit side-effect guardrails.
- `obsidian-cli-workspace-and-navigation` for vault/workspace/tab/navigation and utility workflows.
- `obsidian-cli-workflows` for named one-command orchestration across the six domain skills with preview-first execution.

## What This Plugin Does

- Reads and inspects local Obsidian vault content through the official desktop CLI.
- Handles note, link, task, property, template, history, Bases, Bookmarks, Sync, developer-command, and workspace/navigation workflows that the documented CLI supports, with Publish handled only when detected as available in the local CLI.
- Exposes named one-command workflow IDs (for example `tasks.rollup`, `daily.bootstrap`, `workspace.focus_mode`) with preview/apply controls.
- Handles runtime administration for plugins, themes, snippets, and command/hotkey surfaces through documented CLI commands.
- Uses minimal local filesystem support only when that is needed to safely support an official CLI workflow.

## Skill Routing Quick Guide

- Use `obsidian-official-cli` for note content and knowledge workflows.
- Use `obsidian-cli-bases-and-bookmarks` for Bases and bookmark query/creation workflows.
- Use `obsidian-cli-runtime-admin` for runtime configuration and command registry workflows.
- Use `obsidian-cli-devtools` for runtime diagnostics, screenshots, and explicit eval/CDP workflows.
- Use `obsidian-cli-sync-and-publish` for Sync state and remote-side-effect operations, and for Publish only when publish commands are available.
- Use `obsidian-cli-workspace-and-navigation` for vault/workspace/tab/navigation operations and utility commands.
- Use `obsidian-cli-workflows` for named orchestration workflows that chain the domain skills in preview/apply mode.

See the detailed matrix and chaining recipes in:

- `skills/obsidian-official-cli/references/obsidian-cli-skill-routing-matrix-2026-04-21.md`

## One-Command Workflow Entry Point

Use explicit workflow command IDs through `obsidian-cli-workflows`:

- `workflow_id=tasks.rollup mode=preview output=json`
- `workflow_id=daily.bootstrap mode=preview vault=Work`
- `workflow_id=workspace.focus_mode mode=preview`
- `workflow_id=workspace.focus_mode mode=apply` (run only after preview + explicit confirmation)

## What This Plugin Does Not Do

- It does not target community Obsidian CLIs or plugin-specific APIs.
- It does not cover `obsidian://` launcher automation or Headless Sync workflows.
- It does not bundle MCP servers or connector apps in this version.

## Repository Layout

This repository is the plugin root.

```text
.
├── .codex-plugin/plugin.json
├── .agents/plugins/marketplace.json
├── assets/
└── skills/
```

The source of truth is the unpacked plugin content in this repository. There is no separate packaged copy.

## Local Install And Test Flow

1. Clone this repository locally.
2. Review `.agents/plugins/marketplace.json`. It exposes this repo as a local marketplace entry with `source.path` set to `./`.
3. Restart Codex so it reloads the repo marketplace metadata.
4. Open the plugin directory in Codex, choose `LumiCorp's Marketplace`, and install `codex-obsidian`.
5. Invoke one skill explicitly and run a small read-only task first to confirm install and routing boundaries.

Codex installs local plugins from a cached copy. After you change the plugin, restart Codex and reinstall or refresh from the repo marketplace flow so the installed copy picks up the new files.

## Publish Status

This repository is prepared to be shared on GitHub as a single public plugin repo.

OpenAI's current Codex plugin docs still describe official public plugin publishing as "coming soon," so this repo is structured for:

- GitHub distribution
- local marketplace installs
- future official directory publication when self-serve publishing is available

## Suggested GitHub Metadata

- Description: `Codex plugin for local Obsidian workflows through the official desktop CLI.`
- Topics: `codex-plugin`, `obsidian`, `obsidian-cli`, `agent-skill`, `openai-codex`

## Notes For Future Publish Prep

- GitHub repo: `https://github.com/greg-asher/codex-obsidian`
- Add an install-surface screenshot under `assets/` after the plugin has been verified through the local marketplace flow.
