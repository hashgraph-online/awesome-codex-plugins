---
name: agy-headless-evidence
description: Run AGY headlessly via scheduled ticks or
---
# agy-headless-evidence

Run **Antigravity (AGY)** headlessly — a one-shot `agy -p` or a scheduled tick driven through the
**agentapi sidecar** — and leave a **JSONL proof surface** a validator can read back after the
session ends: the event stream, the final message, the exit code, and the exact command. Scope in,
evidence out.

## Overview / When to Use

The factory dispatches AGY workers non-interactively. A worker that only prints prose to a terminal
leaves nothing a validator can verify later (per the cross-agent rule: you read a worker's
*published compression*, never its live session). This skill makes every headless AGY run produce a
durable, inspectable artifact.

AGY's headless surface (distinct from gemini-cli — there is no `gemini -p`, no `gemini mcp`):

- **One-shot:** `agy -p "<prompt>"` / `agy --print` runs the prompt, prints, and exits
  (`--print-timeout` default 5m). `-c`/`--continue` resumes the latest conversation;
  `--conversation <id>` resumes by id.
- **Sidecar:** the **agentapi sidecar** is AGY's long-lived headless server. A scheduled tick (or an
  external timer) drives runs through the sidecar instead of cold-starting `agy` each time — useful
  for recurring loops where you want a persistent brain and warm conversation state.
- **Scope:** `--add-dir <dir>` (repeatable) bounds which repos a run can touch; pair with a scoped
  git worktree so concurrent roles never share a working tree.
- **Brain:** durable memory + userFacing artifacts under `~/.gemini/antigravity-cli/{brain,knowledge}/`
  — the canonical place to mirror a run's verdict so a different context can consume it.

Use it whenever a headless AGY run is part of an automated loop and someone (or something) downstream
must trust the result.

## ⚠️ Critical Constraints

- **Rule 1 — Capture the exit code immediately.** `echo "$?" > exit-code` on the line right after
  `agy -p` returns. **Why:** a plausible final answer with a non-zero exit is still a failed run;
  validators must key off process reality, not self-report (evidence over comfort).
- **Rule 2 — One run, one timestamped directory.** Never append unrelated runs into the same
  evidence files. **Why:** a verdict must bind to exactly one event stream and one command; runs
  otherwise clobber each other.
- **Rule 3 — Pick the role's posture before launching.** A read-mostly validator gets no
  `--dangerously-skip-permissions`; a scoped author gets `--add-dir` to exactly its worktree.
  **Why:** the permission + scope flags are the runtime boundary, not a convenience.
- **Rule 4 — `dcg` guard stays on.** `~/.gemini/settings.json` wires a `BeforeTool` hook on
  `run_shell_command` to `dcg`; keep it even under `--dangerously-skip-permissions`. **Why:** the
  auto-approve flag would otherwise let a destructive command through — `dcg` is the floor.
- **Rule 5 — JSONL is the source of truth over the pretty stream.** **Why:** the human-readable
  output is for eyeballing; the validator parses the captured stream — what isn't captured didn't
  happen as far as the proof surface is concerned.
- **Rule 6 — Record the exact command.** Store argv, cwd, model, scopes (`--add-dir`), and whether
  it ran one-shot or via the sidecar. **Why:** a run that cannot be reproduced is weak evidence.
- **Rule 7 — This is the AGY lane only (LAW 0).** Never reach for `claude -p` / `claude --print` to
  "do the same for Claude." **Why:** `claude -p` bills the API per-token, not the Max sub, and is
  banned for worker dispatch; Claude workers go through NTM panes / spawned subagents. AGY runtime is
  `agy` / `agy -p`.

## Workflow / Methodology

### Phase 1: Declare the role and posture
Decide whether the run is an author, validator, researcher, or tie-breaker, and pick the scope +
permission posture from that role before launching.

| Role | Scope | Permission posture |
|---|---|---|
| Author (edits) | `--add-dir` to one worktree | `--dangerously-skip-permissions` (dcg still on) |
| Validator (read-mostly) | `--add-dir` to the repo, no writes | no skip-permissions; edits forbidden |
| Researcher | `--add-dir` read context | no skip-permissions |
| Externally-sandboxed batch worker | scoped worktree | skip-permissions only by explicit policy |

**Checkpoint:** confirm the role, its `--add-dir` scope, and that you are NOT granting an author's
posture to a validator before launching.

### Phase 2: Build the evidence directory + command record
```bash
RUN_DIR="$(pwd)/.agy-evidence/$(date -u +%Y%m%dT%H%M%SZ)-${ROLE:-run}"
mkdir -p "$RUN_DIR"
{
  printf 'cwd=%s\n' "$PWD"
  printf 'mode=%s\n' "${AGY_MODE:-oneshot}"   # oneshot | sidecar
  printf 'scopes=%s\n' "$REPO"
  printf 'cmd=%s\n' 'agy -p <prompt> --add-dir <repo> --print-timeout 600'
} > "$RUN_DIR/command.txt"
```
Add `model.txt` if a non-default `--model` is used; add `scope.txt` for edit runs.

**Checkpoint:** `command.txt` exists and records cwd, mode (oneshot vs sidecar), and scope.

### Phase 3: Run AGY headless, capture everything

One-shot author run (scoped worktree, dcg on):
```bash
agy -p "Claim one ready bead via br. Implement only it in this worktree. \
  Commit scoped. Write evidence to brain as userFacing. Do NOT close it — a judge will." \
  --add-dir "$REPO" --dangerously-skip-permissions --print-timeout 600 \
  > "$RUN_DIR/events.jsonl" 2> "$RUN_DIR/stderr.log"
echo "$?" > "$RUN_DIR/exit-code"
```

Sidecar / scheduled-tick run (persistent server; resume warm state by id):
```bash
agy -p "Validate bead <id> against its evidence artifact ONLY. You did not author it. \
  Emit VERDICT: PASS|WARN|FAIL to brain as a userFacing verdict. Do not edit code." \
  --conversation "$CONV_ID" --add-dir "$REPO" --print-timeout 600 \
  > "$RUN_DIR/events.jsonl" 2> "$RUN_DIR/stderr.log"
echo "$?" > "$RUN_DIR/exit-code"
```
Do not broaden `--add-dir` without recording why in `scope.txt`.

**Checkpoint:** `exit-code` is written and `events.jsonl` is non-empty before declaring the run done.

### Phase 4: Mirror the verdict to the brain + validate the evidence
Persist a userFacing artifact so a *different* context can consume it (per agy-native author!=judge):
- Verdict/evidence: `~/.gemini/antigravity-cli/brain/<conversation-id>/<name>_verification.md`
  (+ `.metadata.json`, `userFacing:true`).

Then check the evidence holds:
```bash
test -s "$RUN_DIR/exit-code"
test "$(cat "$RUN_DIR/exit-code")" = 0
test -s "$RUN_DIR/events.jsonl"
test -s "$RUN_DIR/command.txt"
```
If any check fails, the downstream verdict is FAIL or NEEDS-EVIDENCE.

**Checkpoint:** the run-dir path (and brain artifact) is referenced in the bead / Agent Mail
compression so the evidence is discoverable downstream.

## Output Specification

**Format:** a per-run directory of plain files (JSONL + text + exit code), mirrored to a brain artifact.
**Filename / path:** `<workdir>/.agy-evidence/<UTC-timestamp>-<role>/`
**Structure:**
- `events.jsonl` — the captured headless event stream (REQUIRED proof surface)
- `last-message.txt` or `last-message.json` — the final agent message (REQUIRED)
- `exit-code` — captured `$?` (REQUIRED)
- `command.txt` — argv, cwd, mode (oneshot|sidecar), model, `--add-dir` scopes (REQUIRED)
- `stderr.log` — captured stderr (recommended)
- optional `changed-files.txt`, `scope.txt`, `model.txt`, `verdict.md`
- brain mirror: `~/.gemini/antigravity-cli/brain/<conversation-id>/<name>_verification.md` (`userFacing:true`)

## Quality Rubric

- [ ] Exit code captured to `exit-code` immediately after the run and used in the verdict (Rule 1)
- [ ] Run dir is fresh + timestamped — no overwrite of a prior `events.jsonl` (Rule 2)
- [ ] Role posture matched the run: validator had no author scope/skip-permissions (Rule 3)
- [ ] `dcg` BeforeTool hook present in `~/.gemini/settings.json` (Rule 4)
- [ ] `events.jsonl` captured and treated as source of truth over the pretty stream (Rule 5)
- [ ] `command.txt` records argv/cwd/mode/model/scopes — reproducible (Rule 6)
- [ ] No `claude -p` / `claude --print` anywhere; runtime is `agy -p` (Rule 7 / LAW 0)
- [ ] Verdict mirrored to a userFacing brain artifact and the run-dir referenced in the work artifact

## Examples

- **Read-only validator, sidecar tick:** `agy -p "Validate bead AG-123 read-only. VERDICT: PASS|FAIL." --conversation "$CONV_ID" --add-dir "$REPO" > run/events.jsonl 2> run/stderr.log; echo $? > run/exit-code`
- **One-shot author, scoped worktree:** `agy -p "Implement AG-123 in this worktree; commit scoped; evidence to brain; do not close." --add-dir "$WT" --dangerously-skip-permissions > run/events.jsonl; echo $? > run/exit-code`
- **Cross-vendor author!=judge:** author `agy -p --model "Gemini 3.5 Flash (High)"`, judge `agy -p --model "Claude Opus 4.6 (Thinking)"` — two contexts, one loop, no shared session.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `events.jsonl` but pretty output appeared | stdout not redirected to the file | redirect `agy -p` stdout to `events.jsonl` |
| Headless run exits empty | `--print-timeout` hit or no model reachable | raise `--print-timeout`; confirm `agy models` lists a model; check OAuth in `~/.gemini/settings.json` |
| Validator made edits | author posture given to a validator | rerun without `--dangerously-skip-permissions`; enforce read-mostly scope |
| Run "succeeded" but downstream is wrong | exit code ignored | always `echo $? > exit-code`; key the verdict off it |
| Worker tried a destructive command | auto-approve under `--dangerously-skip-permissions` | the `dcg` BeforeTool hook should block it — confirm it's wired in `~/.gemini/settings.json` |
| Judge agreed with author too easily | warm context reused (`-c`/`--continue`) | start a fresh conversation (no `--continue`); read-mostly scope |
| Cannot resume the tick's state | no conversation id captured | record `--conversation <id>` in `command.txt`; reuse it for the sidecar tick |

## See Also / References

- [agy-native](../agy-native/SKILL.md) — the AGY image + headless primitives this skill `consumes`.
- `dcg` — destructive-command guard; the BeforeTool floor this skill keeps on.
- `agentops:validate` — produces the PASS/WARN/FAIL verdict over this proof surface.
- Cross-agent rule: consume a worker's published compression (artifact/mail/bead), never its live session.
- [`$dual-pane-atm`](../dual-pane-atm/SKILL.md) — tri-vendor **interactive pane-3 AGY TUI** (§ Tri-vendor); **not** `agy -p` / headless `--print` — use this skill for evidence-sidecar work instead.
- Migration contract: `~/dev/control-plane/migrations/gemini-to-agy.md` (AGY ≠ gemini-cli; LAW 0).
