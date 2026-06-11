# Codex Execution Profile — agy-headless-evidence

Read the base skill `../../skills/agy-headless-evidence/SKILL.md` (overview, the
seven critical constraints, the four-phase workflow, output spec, rubric)
before acting. The base is the source of truth; this is the step-ordered Codex
path. One inviolable rule: **scope in, evidence out — and never `claude -p`
(LAW 0); the AGY runtime is `agy -p`.**

## Codex tool mapping

- **Read** → shell reads (`cat`/`sed -n`) or `rg`.
- **Write** → `apply_patch` or shell redirection.
- **Bash** → `shell_command` (your native shell tool).
- **author != judge** → two SEPARATE invocations (distinct processes = distinct
  contexts): a one-shot `agy -p` author, then a fresh `agy -p` judge. Never reuse
  one warm conversation (`-c`/`--continue`) for both.
- **Scheduling the tick** → a bushido timer / cron calling `agy -p` against the
  agentapi sidecar, never an in-session loop that reuses context.

## Steps

1. **Confirm the live surface.** `which agy && agy models | head`; confirm
   `~/.gemini/antigravity-cli/{brain,knowledge}` exists. Stop if `agy` does not
   resolve or no model lists. AGY ≠ gemini-cli — there is no `gemini -p`.
2. **Declare the role + posture.** Author = `--add-dir` to one worktree +
   `--dangerously-skip-permissions` (dcg still on). Validator = read-mostly
   `--add-dir`, NO skip-permissions, edits forbidden.
3. **Fresh run dir + command record.**
   `RUN_DIR="$(pwd)/.agy-evidence/$(date -u +%Y%m%dT%H%M%SZ)-${ROLE:-run}"; mkdir -p "$RUN_DIR"`;
   write `command.txt` (cwd, mode oneshot|sidecar, scopes, argv). One run, one dir.
4. **Run headless, capture everything.** Redirect stdout to `events.jsonl`,
   stderr to `stderr.log`, then `echo "$?" > "$RUN_DIR/exit-code"` on the next
   line — never let another command clobber `$?`. Use `--print-timeout 600`;
   `--conversation <id>` for a warm sidecar tick.
5. **Branch on the exit code, not scraped text.** `0` = parse `events.jsonl` /
   the final message; non-zero with a plausible last message is a silent failure.
6. **Mirror the verdict to the brain.** Write a `userFacing` artifact under
   `~/.gemini/antigravity-cli/brain/<conversation-id>/` so a DIFFERENT context
   can consume it; reference `$RUN_DIR` in the bead / Agent Mail / commit note.
7. **Run the quality rubric** from the base skill before declaring the run green.

## Guardrails

- **AGY lane only — never `claude -p` / `claude --print` (LAW 0).** `claude -p`
  bills the API, not the Max sub, and is banned for worker dispatch. Drive AGY
  with `agy -p`; Claude work goes through NTM panes / subagents.
- **Exit code is the verdict, not self-report.** Capture `$?` immediately.
- **One run, one timestamped dir.** Never overwrite a prior `events.jsonl`.
- **author != judge.** Two separate invocations; no `--continue` reuse.
- **`dcg` guard stays on** in `~/.gemini/settings.json` even under
  `--dangerously-skip-permissions`.
- **JSONL is the source of truth** over the pretty stream.
- **Multi-account lanes go through `caam`** (`caam exec agy <profile> --`).
- **Backstage only.** Never surface this content in client-facing material.
