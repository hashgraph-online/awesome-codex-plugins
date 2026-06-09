# agy-rules-workflows — Codex Execution Profile

Runtime adapter for Codex CLI. The doctrine, the five invariant **laws**, the
five-phase Workflow, and the output spec are defined in the Codex wrapper
[`SKILL.md`](./SKILL.md) and the source skill
[`../../skills/agy-rules-workflows/SKILL.md`](../../skills/agy-rules-workflows/SKILL.md). **Read the base skill
first**; this file only maps that skill onto Codex-native tooling and restates
the load-bearing guardrails.

This skill *authors AGY surfaces* — it materializes Rules, a Workflow, and hook
stubs into the AGY/`~/.gemini/` tree. Codex is the harness doing the authoring;
the artifacts it writes are AGY-native (they run later on the `agy` brain, not on
Codex). Do not "translate" the produced Rules/Workflow into Codex idioms — they
must stay AGY-native per the base skill.

## Codex tool mapping

- **Read** → shell reads (`cat`/`sed -n`) or `rg`.
- **Write** → create files via `apply_patch` or shell redirection (the
  `.agents/rules/*.md`, `.agents/workflows/agy-loop.md`, and JSON hook stanza).
- **Edit / MultiEdit** → `apply_patch`. When extending `~/.gemini/settings.json`,
  read it first and merge the `hooks` block — never overwrite (preserve `dcg`).
- **Bash** → `shell_command` (your native shell tool).
- **Grep** → `rg` (fallback `grep`).
- **Glob** → `rg --files` or `find`.
- **Subagent / clean-context judge** → Codex runs single-threaded; realize
  author!=judge as **two separate `codex exec` invocations** (distinct processes
  = distinct contexts). Do NOT reuse one Codex session for both author and judge.
  The *produced* AGY Workflow still dispatches an AGY subagent as judge.
- **Scheduling the tick** → prefer AGY's native **`/schedule`** (`agy -p "/schedule
  agy-loop --every 15m"`) with the objective pinned via **`/goal`**; fall back to a
  bushido timer calling `agy -p "/agy-loop …"`. Never an in-session loop that reuses context.

## Steps

1. **Read the base skill.** Open `../../skills/agy-rules-workflows/SKILL.md` and load Overview, the five
   Critical Constraints (the laws), and the five-phase Workflow. Everything below
   assumes it.

2. **Verify the AGY surface (Phase 1).** `command -v agy && agy plugin list`;
   confirm `~/.gemini/settings.json` and `~/.gemini/skills` exist. Stop if `agy`
   does not resolve — the AGY image is not installed and there is nothing to
   enforce against.

3. **Write the invariant Rules (Phase 2).** `apply_patch` the five laws into
   `.agents/rules/flywheel-laws.md` as imperative law (not advice). Confirm AGY
   loads project rules from `.agents/rules/`; if this install uses another path,
   write there and note it.

4. **Write the loop Workflow (Phase 3).** `apply_patch`
   `.agents/workflows/agy-loop.md` expressing claim->work->validate->close->persist
   (paste body from `references/agy-loop-workflow.md`). Re-read it and confirm the
   validate step names a **separate** clean-context AGY subagent — the author
   never appears as the judge.

5. **Wire the mechanical guardrails (Phase 4).** Merge close-guard + scope-guard
   hooks into `~/.gemini/settings.json` `hooks` (extend, do not clobber the
   existing `BeforeTool` `dcg` entry). Wire `scripts/scope-guard.sh` (Rule 4) and
   `scripts/close-guard.sh` (Rules 2/5). `agy plugin validate` (or dry run); the
   `dcg` hook must survive intact.

6. **Package + smoke (Phase 5).** Optionally bundle Rules + Workflow + hooks +
   subagents as an AGY plugin (`plugin.json`) for `agy plugin install`. Smoke one
   bead headless: `agy -p "/agy-loop run one ready bead end-to-end; STOP after
   persist"`. Confirm a *separate* subagent judged it and it closed only with
   evidence. If the author closed its own bead, Rule 1 is not wired — return to
   Phase 2/3.

7. **Run the quality rubric** from `../../skills/agy-rules-workflows/SKILL.md` before declaring done (all five
   laws as always-active Rules, separate clean-context judge, evidence-gated
   close, scoped commits, persist-before-done, `dcg` intact, nothing leaks into
   client-facing surfaces). Return the paths written + rule/workflow IDs + smoke
   verdict.

## Guardrails

- **The five laws are AGY-native, not Codex idioms.** This skill authors AGY
  Rules/Workflow/hooks; do not rewrite them as Codex wrappers. (Base laws 1–5.)
- **author != judge, always two contexts.** When you exercise the loop from
  Codex, the process that closes a bead must not be the one that wrote it — two
  separate `codex exec` / `agy -p` invocations, never `-c`/`--continue` reuse.
  The produced Workflow's validate step dispatches a clean-context AGY subagent.
  (Base Rule 1/3.)
- **Evidence-gated close.** A bead closes only when each Given/When/Then maps to
  a captured proof surface (test output, diff, artifact); no "looks good" path.
  Consume an agent's published compression, never its live session. (Base Rule 2.)
- **Scoped commits.** Each commit touches only the bead's declared write scope;
  the scope guard rejects drive-by edits. (Base Rule 4.)
- **Persist before done.** Write evidence + learning to the bead + `.agents/ratchet/`
  and an AGY artifact before the turn is marked done. (Base Rule 5.)
- **`dcg` guard stays on.** Merge hooks into `~/.gemini/settings.json` without
  clobbering the existing `BeforeTool` `dcg` entry. Under Codex's own
  `danger-full-access` sandbox, still route destructive commands through `dcg`.
- **Never use a different agent CLI as the Codex executor.** Drive AGY work with
  `agy -p`/`agy -i` when the AGY image is the target, and Codex work with
  `codex exec`.
- **Operator-side; AGY-native only.** Never emit this skill's content into
  client-facing material. For Claude use `operating-loop-workflow` / `bead-crank`;
  this is the AGY turnout, authored from Codex but not a Codex port.
