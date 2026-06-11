# Codex Execution Profile — codex-sandbox-evidence

Read the sibling base skill `../SKILL.md` (full overview, critical constraints,
four-phase workflow, output spec, quality rubric, examples, troubleshooting)
before acting. This profile is the Codex-native, step-ordered execution path; the
base SKILL.md is the source of truth. The one inviolable rule: **least privilege
in, evidence out — never a `--dangerously-bypass-*` flag inside the loop.**

## Steps

1. **Confirm the live surface.** Run `codex exec --help` and
   `codex sandbox --help`. Flag shape changes between releases (base verified
   2026-06-06) — never act on a remembered shape. Confirm `--json`,
   `-o/--output-last-message`, `--output-schema`, and `-s/--sandbox` exist.
2. **Pick the floor sandbox for the task.** Start at `-s read-only` (the default
   and the floor). Escalate to `-s workspace-write` ONLY when the task edits
   files in the working root; add `--add-dir <DIR>` for specific extra writable
   paths. Reserve `-s danger-full-access` for already-sandboxed hosts only.
   Confirm you are NOT passing `--dangerously-bypass-approvals-and-sandbox`,
   `--dangerously-bypass-hook-trust`, or `--ignore-rules`.
3. **Make a fresh, timestamped run directory.**
   `RUN_DIR="$(pwd)/.codex-evidence/$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$RUN_DIR"`.
   One run, one dir — never overwrite a prior event stream.
4. **Wire the three evidence flags.** Always `--json` (redirect stdout to
   `events.jsonl`); always `-o "$RUN_DIR/last-message.{txt,json}"` for the final
   message; add `--output-schema "$RUN_DIR/schema.json"` when the validator needs
   structured fields instead of prose. Set the working root explicitly with
   `-C/--cd <DIR>`; add `--skip-git-repo-check` outside a git repo.
5. **Run least-privilege and capture everything.** Redirect stdout to
   `events.jsonl` and stderr to `stderr.log`, then capture the exit status
   immediately: `echo "$?" > "$RUN_DIR/exit-code"`. Do this on the same line /
   next line — never let another command clobber `$?`.
6. **Branch on the exit code, not scraped text.** Read `exit-code`: `0` = run
   completed, parse the structured result (`events.jsonl` / the `-o` file /
   schema-shaped last message). Non-zero with a plausible last message is the
   silent-failure case — treat it as a failure, not a verdict.
7. **Hand the proof surface to the validator.** The validator reads `$RUN_DIR`,
   never the live session. Record the run-dir path in the bead / Agent Mail
   compression / commit note so the evidence is discoverable downstream.

## Guardrails

- **Never `--dangerously-bypass-approvals-and-sandbox` / `--dangerously-bypass-hook-trust`
  inside the loop.** They disable the sandbox AND the safety hooks — defeating
  the entire point of an evidence-producing, contained worker. Don't pass
  `--ignore-rules` either; keep `.rules` execpolicy active.
- **Start at `read-only`, escalate deliberately.** The sandbox is the blast
  radius. Widen to `workspace-write` only for tasks that edit files; a worker
  that can write or reach beyond its task is exactly what dcg exists to contain.
- **Exit code is the verdict, not self-report.** Capture `$?` to `exit-code`
  immediately after the run; key the validator off the real status. Evidence over
  comfort — a plausible last message with a non-zero exit is a silent failure.
- **JSONL is the source of truth.** The validator parses `events.jsonl`; what is
  not in the JSONL did not happen as far as the proof surface is concerned. The
  pretty stream is for eyeballing only.
- **Verify before acting.** No remembered flag shapes — `--help` first (step 1).
- **One run, one timestamped dir.** Never overwrite a prior `events.jsonl`; the
  validator binds a verdict to exactly one event stream.
- **Codex lane only.** Don't reach for `claude -p` to "do the same for Claude" —
  it bills per-token against the API, not the Max sub, and is banned for worker
  dispatch. Claude workers go through NTM panes / spawned subagents.
- **Multi-account lanes go through `caam`.** `caam exec codex <profile> --` keeps
  each Pro lane isolated; hand-juggling env vars invites cross-account bleed.
- **Backstage only.** Never surface these commands or framing in client-facing
  AI Partner content.
