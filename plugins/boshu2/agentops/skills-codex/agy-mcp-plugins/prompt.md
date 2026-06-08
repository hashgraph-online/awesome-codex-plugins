# Codex Execution Profile — agy-mcp-plugins

Read the base skill `../../skills/agy-mcp-plugins/SKILL.md` first (overview, the
seven constraints, output spec, rubric, troubleshooting). It is the source of truth;
this is the step-ordered path.

## Steps

1. **Verify the live surface** — `agy plugin help` (+ `agy plugin <sub> --help`); never act on a remembered shape.
2. **Inventory** — `agy plugin list` (BEFORE); note declared servers in `~/.gemini/settings.json`. Confirm the target name is absent.
3. **Wire a server** — author a plugin tree whose `plugin.json` declares an `mcpServers` entry (stdio `command`/`args`/`env`, or remote `url`+`*_ENV_VAR` token ref — never a literal). Then `agy plugin validate` → `install` → `enable` → `list` (AFTER).
4. **Ship a bundle** — `agy plugin import claude|gemini` to pull an existing tree, then `agy plugin validate` → `install <tree|name@marketplace>` → `enable`. A bare `SKILL.md` under `~/.gemini/skills/` needs no plugin.json.
5. **Smoke-test** — a read-only `agy -p --add-dir "$REPO"` worker that lists its MCP tools and calls one safe read tool. Not "wired" until a worker uses it.
6. **Capture** — before/after `agy plugin list`, smoke-test exit code, rollback commands into the handoff.

## Guardrails

- List before/after every mutation; declare only scoped servers; `disable` before `uninstall` when uncertain.
- Never inline secrets — tokens by env-var reference in `plugin.json`/`~/.gemini/settings.json`.
- Keep the `BeforeTool` → `dcg` hook wired; nothing under `~/dev/agentops`; no agentops push (invoke-never-rebuild).
- **AGY ≠ gemini-cli** — never use `gemini mcp`/`gemini extensions`/`gemini -p`; runtime is `agy`/`agy -p`, unit is the plugin.
- Backstage only — never surface these commands or framing in client-facing AI Partner content.
