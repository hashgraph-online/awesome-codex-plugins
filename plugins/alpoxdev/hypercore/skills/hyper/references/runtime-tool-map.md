# Multi-Agent Runtime Capability and Skill-Loading Map

Single source of truth mapping the capability names used across Hypercore skills to concrete tools, skill installation paths, cross-skill loading rules, and frontmatter rules across **omp**, **Antigravity (`agy`)**, **Claude Code**, and **Codex**. Skill bodies MUST use the neutral capability names in §1 rather than hardcoding product-specific tool names.

## Contents

- 1. Capability-to-Tool Mapping
- 2. Skill Discovery, Installation, and Cross-Skill Loading
- 3. Portable Frontmatter Contract
- 4. Verification Status by Runtime
- Sources

## 1. Capability-to-Tool Mapping

Skills name **capabilities** ("read files", "search text", "run shell commands", "delegate a read-only or scoped subtask", "ask one user question", "load a sibling skill"). Each runtime satisfies those capabilities with its own surface:

| Capability in skill text | omp (`oh-my-pi`) | Antigravity (`agy`) | Claude Code | Codex (`codex` CLI / App) |
|---|---|---|---|---|
| Read file (`파일 읽기`) | `read` | `read_file` | `Read` | Built-in file read / `exec_command` (`sed`, `cat`) |
| Write / edit file (`파일 쓰기·수정`) | `write`, `edit` | `write_file`, `edit_file` | `Write`, `Edit` | `apply_patch` |
| Search files & text (`파일·본문 검색`) | `grep`, `find` | `run_command` (`rg`, `fd`) | `Grep`, `Glob` | `exec_command` (`rg`, `fd`) |
| Run shell command (`셸 명령 실행`) | `bash` | `run_command` (`manage_task` for background jobs) | `Bash` | `exec_command` (`codex exec` in headless CLI) |
| Delegate subtask (`하위 작업 위임`) | `task` (or external `hc` worker when configured) | `invoke_subagent` (`define_subagent`, `send_message`, `run_workflow`) | `Agent` / `Task` tool (`.claude/agents/*.md`, agent teams) [doc] | Native subagents / `spawn_agent`, `send_input`, `wait_agent` (`.codex/agents/*.toml`) [doc] |
| Ask user (`사용자 질문`) | `ask` (or plain-text question) | `ask_question` (multi-choice) or plain-text question | `AskUserQuestion` or plain-text question [doc] | Plain-text turn question (`request_user_input` in plan mode, estimated across modes) |
| Load skill (`스킬 불러오기`) | `skill://<name>` or read `../<name>/SKILL.md` | Activate discovered skill or read `../<name>/SKILL.md` | `/<name>` or `Skill` tool, or read `../<name>/SKILL.md` [doc] | `$<name>` or read `../<name>/SKILL.md` |
| Project instruction surface (`프로젝트 지침`) | `AGENTS.md`, `~/.omp/agent/rules/` | `GEMINI.md`, `AGENTS.md`, `.agents/rules/`, `~/.gemini/config/rules/` | `AGENTS.md` (v2.1.277+, unless suppressed by `CLAUDE.md`), `CLAUDE.md` [doc] | `AGENTS.md`, `AGENTS.override.md`, `~/.codex/config.toml` |

 Fallback rule when a capability is absent:

- **No subagent tool exposed**: run independent read-only checks sequentially in the current session unless a skill's high-accuracy review contract explicitly requires an independent reviewer (in which case follow that skill's documented stop/degrade rule).
- **No structured question tool exposed**: ask one concise plain-text question with a recommended default and wait for the user's reply.

## 2. Skill Discovery, Installation, and Cross-Skill Loading

Different hosts mount skills from different directories, so hardcoded repository paths such as `skills/<name>/SKILL.md` or URI schemes such as `skill://<name>` break outside one host.

| Runtime | Project skill path | User/global skill path | Verified `npx skills` install command |
|---|---|---|---|
| omp | `.agents/skills/<name>/` | `~/.omp/agent/skills/<name>/` | `npx skills add alpoxdev/hypercore -a codex` (project; `-a omp` is rejected by `skills@1.9.0`) |
| Antigravity (`agy`) | `.agents/skills/<name>/` | `~/.gemini/config/skills/<name>/` | `npx skills add alpoxdev/hypercore -a antigravity-cli -g` (or `-a antigravity`; omit `-g` for project) |
| Claude Code | `.claude/skills/<name>/` (or marketplace plugin `skills/`) | `~/.claude/skills/<name>/` | `npx skills add alpoxdev/hypercore -a claude-code -g` (or `claude plugin install hypercore@alpoxdev`) |
| Codex | `.agents/skills/<name>/` | `~/.agents/skills/<name>/` | `npx skills add alpoxdev/hypercore -a codex -g` (`$CODEX_HOME/skills` is legacy, not primary) |

**Standard cross-skill reference rule**:

1. Every installation layout above places sibling skills side-by-side under a shared parent directory (`skills/<name>/SKILL.md`).
2. Whenever an orchestrator or handoff rule loads another Hypercore skill, the **canonical portable path** is `../<skill>/SKILL.md` resolved from the active skill's own directory (with the runtime's native skill loader permitted as an equivalent shortcut when exposed).
3. After opening `../<skill>/SKILL.md`, verify that its YAML frontmatter `name` equals `<skill>`, then resolve that skill's `rules/`, `references/`, `scripts/`, and `assets/` relative to `../<skill>/`.

## 3. Portable Frontmatter Contract

- **Required universal keys**: `name` and `description` only. Every agent parser reads these two keys.
- **Optional non-load-bearing keys**: `compatibility`, `license`, `metadata`, `allowed-tools`, and runtime-specific switches (`disable-model-invocation`). Core behavior MUST still hold on runtimes that ignore optional keys; runtime-only switches (`agents/openai.yaml`, `disable-model-invocation`) belong in adapter notes, never as silent prerequisites.
- **Mandatory quoting**: Every scalar string value in `SKILL.md` and `SKILL.ko.md` frontmatter (`name`, `description`, `compatibility`, `license`) MUST be safely quoted (or use a valid YAML block scalar) so `: ` or ` #` never breaks strict parsers (`scripts/check-skill-frontmatter.sh`).

## 4. Verification Status by Runtime

| Runtime | What was verified directly on this host (2026-11-23) | Documented / estimated (`추정`) items |
|---|---|---|
| omp | `omp --help` (`v19.1.0`), `~/.omp/agent/` layout, headless handoff smoke pass (`omp/18.18.6`), `-a codex` project install | Exact internal tool parameter changes in future releases |
| Antigravity (`agy`) | Active session tool declarations (`read_file`, `write_file`, `edit_file`, `run_command`, `invoke_subagent`, `ask_question`, `run_workflow`), `agy-customizations` skill discovery rules, `skills@1.9.0` `-a antigravity` / `-a antigravity-cli` install probe in isolated `/tmp` | UI-only IDE slash-command differences across desktop builds (estimated) |
| Claude Code | `skills@1.9.0` `-a claude-code` isolated `/tmp` install probe (`.claude/skills`), `.claude-plugin/` manifest gate | `claude` binary is not installed on this Mac mini (`not_run` locally); `Read`/`Edit`/`Bash`/`Agent`/`AskUserQuestion` and v2.1.277+ `AGENTS.md` behavior come from official Anthropic docs (`[doc]`, live flag parity estimated on this host) |
| Codex | `codex --help` & `codex exec --help` locally, `skills@1.9.0` `-a codex` isolated `/tmp` install probe (`.agents/skills`) | Internal harness tool names (`apply_patch`, `spawn_agent`, `request_user_input`) are not printed by `codex --help`; sourced from OpenAI Codex docs (`[doc]`, mode-specific exposure estimated) |

## Sources

> Checked 2026-11-23.

| Claim | Source |
|---|---|
| `skills@1.9.0` agent targets (`antigravity`, `antigravity-cli`, `claude-code`, `codex`, `cursor`, `pi`) and project/global destination directories | Local `npx skills --version` (`1.9.0`), `skills/dist/remove.mjs` inspection, and isolated `/tmp` install verification, 2026-11-23 |
| `omp v19.1.0` CLI flags and `.agents/skills` / `~/.omp/agent/skills` loading | Local `omp --help` (`v19.1.0`) on 2026-11-23; <https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/skills.md> (checked 2026-11-10) |
| Antigravity tool declarations and `.agents/` + `~/.gemini/config/` customization precedence | Active Antigravity runtime tool declarations and built-in `agy-customizations` guide, 2026-11-23 |
| Claude Code tools, `.claude/skills`, `CLAUDE.md` / `AGENTS.md` precedence, and frontmatter validation | <https://code.claude.com/docs/en/skills>, <https://code.claude.com/docs/en/sub-agents>, and `instructions/context-engineering/references/runtime-profiles.md` (checked 2026-11-08) |
| Codex CLI commands (`codex exec`, `resume`, `review`, `mcp`) and `.agents/skills` + `agents/openai.yaml` | Local `codex --help` / `codex exec --help` on 2026-11-23; <https://learn.chatgpt.com/docs/build-skills> (checked 2026-11-08) |

### Evidence grade

`LOCAL` for `omp`, `Antigravity`, `codex --help`, and `npx skills@1.9.0` install probes executed on 2026-11-23; `EXTERNAL-VENDOR-DOC` (with host-unverified live details explicitly marked `estimated`) for `Claude Code` CLI internals and `Codex` internal tool schemas.
