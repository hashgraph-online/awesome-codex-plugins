# /plan-external-review arm procedure

Manual arm detail, script commands, and "what Claude should produce" for `.cursor/commands/plan-external-review.md` (kept out of the command to fit its size budget; Goal, Preconditions, the exit-3 honesty clause, and References stay in the command itself).

## Manual arm

### Chat vs CI (do not confuse)

| Path | What to run | Where |
|------|-------------|--------|
| Chat when `mode: "autonomous"` (or `--autonomous`) | `--force --autonomous --wait-monitor` | Spawns interactive Claude in an **inspectable background PTY** (tmux/screen preferred; macOS Terminal without `activate`; emulator last resort), then waits for a **fresh** `plan-monitor-<slug>.md`. Spawn-only without wait is not review done. |
| Chat paste fallback / legacy | `--force --paste-only` then operator pastes `--force --interactive` | User's Cursor Terminal; session still waits for a fresh monitor after Claude runs |
| Mid-batch / queue-end (`--batch`) | `--force --autonomous --wait-monitor --batch p1.plan.md p2.plan.md` (or one arm+wait per plan) | Background/inspectable spawn + wait_all; no paste Ask; no N-session fan-out without wait |
| Headless `agent-kit run-plan` | `--print` (CLI always passes it) | CI / cron agent shell (`claude -p`) |

**Agents in chat MUST NOT** exec headless `--print` / `--force` alone and claim the audit is running. That agent shell is not an inspectable audit PTY; Claude HITL can block invisibly; no monitor file appears. Prefer `--autonomous` (background PTY). Use `--paste-only` only when background spawn is unavailable or the operator opts out. Background PTY ≠ banned invisible agent-shell `-p` (ADR `2026-07-28_audits-headless-terminal-honesty.md`).

### What "operator-visible" means (smoke notes)

- **Autonomous success:** chat arm **must** use `--force --autonomous --wait-monitor`. The launcher prefers a background/inspectable PTY (no OS Terminal focus by default; `--focus-terminal` / `AGENT_KIT_AUDIT_FOCUS_TERMINAL=1` restores activate), then polls until a **fresh** monitor exists (`mtime >= arm epoch` or the HTML comment sentinel `<!-- audits-wait-fresh: created|updated -->` written into the monitor).
  Chat AwaitShell uses `waitSliceSeconds` (default 90); total budget is `waitTimeoutSeconds` (default 900) persisted in `.cursor/context/audit-wait/<slug>.json`. A new session resumes remaining budget and does not restart 900s. Early-ready still exits `0` at first freshness. Exit `0` = fresh ready; `3` = timeout (slice or total; not review done); `4` = soft-fail while waiting. Spawn-only exit 0 without wait is **not** review done.
  **Chat continuation:** AwaitShell until `0|3|4`; on `0` run `/plan-review-triage` Ask in the same session. Do **not** stop at Final HANDOFF "after monitor lands" or require typing `done`. ADRs: `decisions/2026-07-27_audits-wait-freshness-enforce.md`, `decisions/2026-08-13_audits-atomic-wait-reviewer-fallback.md`.
- **Autonomous soft-fail:** missing `claude` → tip + exit `4` when `--wait-monitor` was requested (Field Report owed). Background spawn unavailable → falls back to `--paste-only` UX with an honest "NOT running yet" banner. A **silent PTY** (spawn succeeded, no scrollback within the progress-gate grace window) is reported as a failed launch: the launcher disposes the session it just spawned, prints the paste fallback, and soft-fails instead of burning the wait budget. A **session-cap refusal** (detached `agent-kit-audit-*` sessions at the cap) never spawns at all. Soft-fail does **not** invent a monitor or run triage as if review completed.
- **Exit 3 is timeout-only:** it means the freshness gate was not satisfied inside the budget, never that the review finished. A monitor that appears later, including one written by a different or later arm, does **not** convert a `3` into success. Leave the target Field Report **owed** and re-arm. ADR: `decisions/2026-07-30_audits-pty-progress-gate-zombie-policy.md`.
- **Paste-only:** clipboard + printed interactive one-liner; review starts only after the operator pastes into their Cursor Terminal. After paste (Claude running), the session still waits for the monitor file then continues into triage Ask when possible.
- **`--dry-run`:** resolves mode/plan and prints `background-cmd` / `paste-cmd` / `focus-terminal` / `reviewer-backend` / `same-model-refuse` without spawning a reviewer (useful for smoke).
- **Reviewer cascade:** `--backend auto|claude|cursor|cloud` (or config). `cloud` is an opt-in pin (Cursor Cloud Agents over REST) that `auto` never reaches. Claude spawn passes `--model` from `roles.reviewer.model`, then `reviewerModel`. Cursor fallback cannot honor a Claude-family name. The identical implementer and reviewer model is refused (Auto/Auto included); a different model of the same family runs with one warning (`same-family-warn` in `--dry-run`). Findings-only until `/plan-review-triage`. Never `/git-prod`.
- **Reviewer role (`roles.reviewer`, read before `externalPlanReview`):** `enabled: false` or `scope: "off"` = no review: skip the exhaustion Ask and the arm. `scope: "tick"` = the headless runner reviews after each tick and no exhaustion audit arms (chat included). `scope: "plan"` (default) = this page. `enabled` absent follows `externalPlanReview.enabled`. A one-shot `--force` still arms. Naming a reviewer model different from the tick model lifts the unsatisfiable-config check. ADR `decisions/2026-11-16_reviewer-same-family-rule.md`.

### A. Script (preferred)

```bash
# Chat / session when autonomous (mandatory wait + freshness)
.cursor/scripts/plan-external-review.sh --force --autonomous --wait-monitor

# Mid-batch or queue-end batch arm (one wait_all; no paste Ask)
.cursor/scripts/plan-external-review.sh --force --autonomous --wait-monitor --batch plan-a.plan.md plan-b.plan.md

# Legacy paste fallback (clipboard + print; does NOT start Claude)
.cursor/scripts/plan-external-review.sh --force --paste-only

# Then paste this in YOUR Cursor terminal (script prints/copies it):
.cursor/scripts/plan-external-review.sh --force --interactive YOUR-PLAN.plan.md

# Optional rollback: focus OS Terminal window
.cursor/scripts/plan-external-review.sh --force --autonomous --focus-terminal --wait-monitor

# CI / headless one-shot (claude -p; no IDE panel)
.cursor/scripts/plan-external-review.sh --force --print

# Dry-run (resolve + print strategy only)
.cursor/scripts/plan-external-review.sh --force --autonomous --wait-monitor --dry-run YOUR-PLAN.plan.md

# Interactive session already in the Cursor terminal
.cursor/scripts/plan-external-review.sh --interactive

# Explicit plan file (else resolved from .cursor/HANDOFF.md Plan: line)
.cursor/scripts/plan-external-review.sh optional_claude_code_plan_review_2026_07_20.plan.md
```

Compatibility wrapper: `scripts/plan-external-review.sh` forwards to `.cursor/scripts/`.

Script behavior (ADR):

- Disabled / missing config → tip + exit 0 (does not fail the plan run)
- Missing template → tip + exit 0 (suggest `agent-kit update --refresh`)
- `claude` missing → tip + exit 0 for autonomous/print/interactive; `--paste-only` still prints the command
- `mode: "autonomous"` (non-headless) → background/inspectable PTY auto-launch; soft-fallback to paste-only
- Missing `mode` key → paste-compatible default (`--print` when no flag; chat should pass `--paste-only` or set autonomous)
- Interactive and headless launches pass Claude CLI `--permission-mode auto`
- Post-spawn progress gate: samples PTY scrollback before the monitor wait; silent PTY → early abort (`AGENT_KIT_AUDIT_PROGRESS_TIMEOUT`, default 60s, `0` disables); channels without a scrollback API stay advisory
- Session pressure: warns at `AGENT_KIT_AUDIT_SESSION_WARN` detached `agent-kit-audit-*` sessions, refuses to spawn at `AGENT_KIT_AUDIT_SESSION_CAP`; reap is opt-in (`--reap-audit-sessions`), detached-only, past `AGENT_KIT_AUDIT_REAP_MIN_AGE`
- `--paste-only` copies the interactive one-liner via `pbcopy` / `xclip` / `xsel` / `clip.exe` when available
- Never `/git-prod`; never broad `git add`
- Does **not** register a Cursor native `stop` hook

### B. Paste fallback

1. Prefer autonomous first. If spawn fails or operator opts out: `.cursor/scripts/plan-external-review.sh --force --paste-only`.
2. Open a Cursor Terminal in the repo root and paste the printed interactive command.
3. Or open `claude` and paste the optional prompt block the script prints.
4. After the monitor exists: paste the explicit `/plan-review-triage .cursor/memory/plan-monitor-<slug>.md` line printed by the launcher (or Claude closeout). Prefer that over bare `/plan-review-triage`.

## What Claude should produce

Same contract as `.cursor/context/templates/plan-external-review-prompt.md` (Claude's working prompt). Command prose must not lag the template.

- Monitor file: `.cursor/memory/plan-monitor-<plan-slug>.md` (template: `plan-monitor.md`)
- Index row in `.cursor/memory/_index.md` when creating a new monitor (target must be git-tracked; add monitor by name)
- **Delivery truth first:** for each `completed` to-do, was the claimed work actually done? Verify against code, tests, APIs, infra, Git SHAs, and published artifacts. Docs, HANDOFF, and inventories are indicative only (`docs-professional-standard`; ADR `2026-08-01_docs-indicative-delivery-truth`)
- **Finding priority** (highest first): (1) delivery truth, (2) security, (3) logic gaps, (4) bad code/practices with path-level evidence. Rank Still open / residuals by this order
- **Evidence mandate:** every `PASS` / `GAP` / `FAIL` cites at least one path, SHA, command, or artifact check
- **Forbidden filler:** do not ship restated plan text with no verification; ceremony checklists marked Met without path/SHA/command evidence; "looks good" / empty praise with no findings; decorative prose that finds nothing because nothing was checked
- No product commits unless a human asks after triage
