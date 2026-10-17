---
name: setup-project
description: Use to generate HOTL adapter files for the current project — creates AGENTS.md, .clinerules, cursor rules, or copilot instructions depending on tools the team uses.
---

# Setup Project for HOTL

## Overview

Generate the right config files so every code assistant on your team follows HOTL principles.

**Announce:** "Running HOTL project setup. Let me check what tools your team uses."

## Process

1. Ask: "Which code assistants does your team use?" (select all that apply)
   - Claude Code
   - Codex (OpenAI)
   - Cline (VS Code extension)
   - Cursor
   - GitHub Copilot

2. Ask: "Will this project run multi-phase initiatives?" **Default: no.** Only answer yes for multi-phase work like major migrations, v1/v2 rewrites, platform rebuilds, or any effort that will span multiple phases with separate phase design docs and workflows. For a single feature, bug fix, or refactor, answer no — the standard HOTL flow handles those just fine.

   **If yes**, ask the follow-up: "What's the initiative slug? (kebab-case, e.g. `ai-assurance`, `v2-migration`)". Validate the answer matches `[a-z0-9][a-z0-9-]*`.

   **If no** (or if the user declines to opt in), skip step 5 entirely and proceed with tool-adapter generation only.

3. For each selected tool, generate the appropriate file:

| Tool | File Generated | Location |
|---|---|---|
| Claude Code | `CLAUDE.md` | Project root |
| Codex | `AGENTS.md`; optional `.codex/agents/*.toml` | Project root |
| Cline | `.clinerules` | Project root |
| Cursor | `.cursor/rules/hotl.md` | Project root |
| GitHub Copilot | `.github/copilot-instructions.md` | Project root |

4. Each generated file contains:
   - HOTL operating principles (intent/verification/governance contracts)
   - Brainstorming guidance that produces design docs in `docs/designs/`
   - Link to `docs/plans/YYYY-MM-DD-<slug>-workflow.md` format
   - Risk level guidelines
   - What always requires human review

5. **If Codex was selected**, ask whether to install HOTL Codex custom agent templates. Default: yes. These templates make the bundled reviewer, architect, researcher, QA, dev, and PM roles available to the target project as Codex project-scoped custom agents.

   Resolve `hotl-install-codex-agents.sh` using the same six-location install-path order as the initiative scaffolder below:

   1. If you are working in the `hotl-plugin` repo itself, use `scripts/hotl-install-codex-agents.sh`
   2. Codex native-skills install: `~/.codex/hotl/scripts/hotl-install-codex-agents.sh`
   3. Codex plugin install: `~/.codex/plugins/hotl-source/scripts/hotl-install-codex-agents.sh`
   4. Codex plugin cache fallback: `~/.codex/plugins/cache/codex-plugins/hotl/*/scripts/hotl-install-codex-agents.sh`
   5. Cline install fallback: `~/.cline/hotl/scripts/hotl-install-codex-agents.sh`
   6. Claude Code plugin fallback: `~/.claude/plugins/hotl/scripts/hotl-install-codex-agents.sh`

   **Invoke the installer from the project root:**

   ```bash
   bash <resolved-hotl-install-codex-agents.sh>
   ```

   The installer creates `.codex/agents/` and copies the tracked HOTL templates from `adapters/codex-agents/` into it. Existing agent files are preserved by default and emitted as `SKIP:` lines. Only use `--force` when the user explicitly approves overwriting existing project agent files.

6. **If the user opted in to initiative support in step 2**, invoke the scaffolder to create `.hotl/config.yml`, the six `docs/<tier>/` directories, and the four initiative-tier templates under `docs/prompts/`. The scaffolder should configure `docs/designs/` as the canonical design-doc home and `docs/plans/` as the canonical workflow home.

   **Resolve `hotl-init-initiative.sh`** using the same six-location order as `document-lint.sh` and `hotl-config.sh` (see `skills/document-review/SKILL.md`):

   1. If you are working in the `hotl-plugin` repo itself, use `scripts/hotl-init-initiative.sh`
   2. Codex native-skills install: `~/.codex/hotl/scripts/hotl-init-initiative.sh`
   3. Codex plugin install: `~/.codex/plugins/hotl-source/scripts/hotl-init-initiative.sh`
   4. Codex plugin cache fallback: `~/.codex/plugins/cache/codex-plugins/hotl/*/scripts/hotl-init-initiative.sh`
   5. Cline install fallback: `~/.cline/hotl/scripts/hotl-init-initiative.sh`
   6. Claude Code plugin fallback: `~/.claude/plugins/hotl/scripts/hotl-init-initiative.sh`

   **Invoke the scaffolder with the slug collected in step 2:**

   ```bash
   bash <resolved-hotl-init-initiative.sh> --name <slug>
   ```

   The scaffolder refuses cleanly when `.hotl/config.yml` already exists — that is the intended behavior and should not be worked around. If any of the four target outputs under `docs/prompts/` already exists, it is preserved byte-for-byte and a `SKIP:` line is emitted.

   **Only invoke the scaffolder when the user answered yes in step 2.** If the user answered no (the default), skip this step entirely.

7. Commit all generated files:

```bash
git add AGENTS.md .clinerules .cursor/ .github/ CLAUDE.md
# If Codex custom agents were installed, also add:
#   .codex/agents/
# If initiative support was scaffolded in step 6, also add:
#   .hotl/config.yml docs/
git commit -m "chore: add HOTL adapter files for [tool list]"
```

## AGENTS.md Template Content

```markdown
# AGENTS.md — HOTL Operating Model

This project follows the Human-on-the-Loop (HOTL) development model.

## How to Work

1. Before feature work: brainstorm with intent/verification/governance contracts
2. Brainstorm into a design doc in `docs/designs/`, then create a dated workflow file at `docs/plans/YYYY-MM-DD-<slug>-workflow.md`
3. Execute steps autonomously within guardrails
4. Pause at `gate: human` for high-risk steps

## Risk Levels

- **low/medium + auto_approve: true:** Execute autonomously, auto-approve gates
- **high:** Always pause for human review at gates

## Always Requires Human Review

- Auth/authz changes
- Encryption or key management
- Privacy-critical logic (PII, consent, deletion)
- Billing or financial logic
- Broad access control changes

## Workflow Format

See `docs/plans/YYYY-MM-DD-<slug>-workflow.md` for canonical workflow instances or `workflows/` in the plugin for templates.
```
