---
name: codex-exec
description: Use when running Codex workers or validators
---
# codex-exec

Drive headless Codex worker and validator agents with `codex exec` on the ChatGPT Pro subscription (OAuth) — the Codex side of the flywheel. The one inviolable rule: **subscription billing, never per-token API billing.**

## ⚠️ Critical Constraints

- **Never API-bill a worker.** Do NOT set `OPENAI_API_KEY` in a worker's env, and do NOT use `codex login --with-api-key`. **Why:** that flips Codex from flat-rate sub billing to per-token API billing — the Codex twin of the banned `claude -p`. A factory cycle on API keys silently burns real money. (Mirror of the "never `claude -p` for workers" rule.)
  - WRONG: `OPENAI_API_KEY=sk-... codex exec -C "$REPO" "<task>"` · CORRECT: `codex login status  # Logged in using ChatGPT` then `codex exec -C "$REPO" -s workspace-write "<task>"`
- **Confirm the sub before dispatch.** Run `codex login status` and require `Logged in using ChatGPT`. **Why:** a worker that "runs fine" on a leaked API token bills per token; the check is the only thing standing between a green run and a surprise invoice.
- **Pipe the prompt (or close stdin) in any non-TTY lane — else codex HANGS.** A positional-arg `codex exec "<prompt>"` run with non-TTY stdin (background, `&`, ATM/NTM pane, cron, piped, inherited-pipe) still **reads stdin** — it prints `Reading additional input from stdin...` and blocks **forever** when that stdin never reaches EOF (the classic idle open pipe). **Why:** codex appends piped stdin as a `<stdin>` block even when a positional prompt is present, so an open idle stdin is an unterminated read. For unattended/background/factory lanes the safe DEFAULT is to **pipe the prompt** — `printf '%s' "$P" | codex exec … -` (or `cat prompt.txt | codex exec … -`) — or **close stdin** — `codex exec "<prompt>" </dev/null`. The bare positional form is fine only for an interactive TTY.
- **Pick the sandbox deliberately.** `-s read-only` for offline validators, `-s workspace-write` for workers that must edit, `-s danger-full-access` only inside an already-sandboxed host. **Why:** `codex exec` runs model-generated shell commands; the sandbox is the blast radius.
- **Network-touching validators are the exception — use `-s danger-full-access`.** A validator that must `git fetch`, clone a repo, or hit any network endpoint will FALSE-FAIL under `-s read-only`, because the sandbox blocks `connect` syscalls — the failure is an infrastructure artifact, not a real verdict. On an already-sandboxed host, give network validators `-s danger-full-access`. Offline validators stay `-s read-only`.
- **`--dangerously-bypass-approvals-and-sandbox` is for externally-sandboxed hosts only.** **Why:** it removes every guardrail in one flag; use it only when the OS/container is the sandbox.
- **Don't strand work in `--ephemeral`.** It skips session persistence, so there is nothing to `resume`. **Why:** a crashed ephemeral run cannot be recovered or continued.
- **Multi-account lanes go through `caam`, not env-var juggling.** **Why:** `caam exec codex <profile> --` keeps each Pro lane isolated; hand-setting `CODEX_HOME` invites cross-account token bleed.

## Why This Exists

`codex exec` runs Codex non-interactively: it takes a prompt (argument or stdin), executes against a working directory under a sandbox policy, and prints the final agent message. It is the Codex analogue of an NTM Claude pane — the right tool for factory/loop workers and validators that need a second vendor lane.

Auth is the whole game. `codex login status` must read **`Logged in using ChatGPT`** (the Pro/Plus subscription via OAuth). That billing is flat-rate. The moment Codex is authed with an API key (`OPENAI_API_KEY`, `codex login --with-api-key`), every token is metered against the API account — the exact failure mode `claude -p` causes on the Claude side. This skill exists to keep Codex workers on the sub. Without it, a loop that dispatches Codex turns can quietly run on metered API billing and produce a surprise invoice.

Verified against `codex-cli 0.139.0` (`codex exec --help`, `codex exec resume --help`). **Re-verify the flag surface on the next codex-cli bump** — the flag tables (Phase 2 key flags, the Phase 3 resume currency note) are version-pinned; a CLI upgrade can add/rename/move flags, so re-run the two `--help` commands and reconcile before trusting this skill against a newer codex.

## Folded triggers (ag-s43tg wave 1): `codex-goals` + `codex-mcp-plugins` + `codex-sandbox-evidence` route here

- **`codex-goals` → this skill.** Use when asked to define an objective once and let Codex iterate
  until done (Codex Goals): express the objective as the `codex exec` prompt with an explicit
  done-condition ("Run tests. Report PASS/FAIL."), then drive iterations through
  `codex exec resume --last` (Phase 3) until the verdict lands — same sub-billing and sandbox
  rules as any worker lane.
- **`codex-mcp-plugins` → this skill.** Use when wiring MCP servers or plugins into Codex CLI
  or the AgentOps Codex skill bundle: MCP/plugin config lives in `$CODEX_HOME/config.toml`
  (layer per-lane variants via `-p/--profile <name>.config.toml`); verify the wired server is
  visible to a worker with a cheap `codex exec -s read-only` probe before dispatching real work.
- **`codex-sandbox-evidence` → this skill.** Use when running `codex exec` in a
  least-privilege sandbox with machine-checkable proof: pick the narrowest `-s` policy
  (Phase 2), then capture the proof surface — `--json` JSONL event stream, `-o` final-message
  file, and `--output-schema` for a schema-constrained verdict — so the sandbox posture and
  the result are both auditable artifacts.

## Quick Start

```bash
codex login status                      # MUST read: Logged in using ChatGPT
test -z "${OPENAI_API_KEY:-}" || echo "ABORT: API key set"   # MUST be empty
codex exec -C "$REPO" -s read-only "Validate the change. Output VERDICT: PASS|FAIL."
```

## Workflow / Methodology

### Phase 1: Verify the lane is on the subscription
```bash
codex login status          # MUST print: Logged in using ChatGPT
echo "${OPENAI_API_KEY:+API_KEY_SET}"   # MUST print nothing
```
**Checkpoint:** Status reads `Logged in using ChatGPT` AND no `OPENAI_API_KEY` is set. If either fails, STOP — fix auth before dispatching. If API-key auth is present, run `codex login` (browser OAuth) or `--device-auth` to re-auth on the sub.

### Phase 2: Dispatch the worker / validator
```bash
# Worker: edit in a repo
codex exec -C /path/to/repo -s workspace-write \
  "Implement bead ag-123: <task>. Run tests. Report PASS/FAIL."

# Validator (offline / no network): read-only, structured verdict
codex exec -C /path/to/repo -s read-only \
  -o /tmp/verdict.txt \
  "Independently validate the change on this branch. Output VERDICT: PASS|FAIL + reasons."

# Validator that must reach the network (git fetch, clone, API): danger-full-access
# on an already-sandboxed host — -s read-only would FALSE-FAIL on blocked connect syscalls.
codex exec -C /path/to/repo -s danger-full-access \
  -o /tmp/verdict.txt \
  "Fetch origin/main, validate the change against it. Output VERDICT: PASS|FAIL + reasons."

# Stdin prompt (orchestrator piping the task in) — the SAFE DEFAULT for any
# unattended/background/ATM-pane/cron lane. The trailing `-` reads the prompt
# from the pipe and gives codex an immediate EOF, so it can't stall on
# "Reading additional input from stdin..." (see Critical Constraints).
printf '%s' "$TASK_PROMPT" | codex exec -C "$REPO" -s workspace-write -

# If you must pass the prompt positionally in a non-TTY lane, close stdin:
codex exec -C "$REPO" -s workspace-write "<task>" </dev/null

# Named profile (a specific model/config lane)
codex exec -p worker-fast -C "$REPO" -s workspace-write "<task>"

# Machine-readable event stream for a loop to parse
codex exec --json -C "$REPO" -s read-only "<task>" > events.jsonl
```
Key flags: `-C/--cd <DIR>` working root · `-s/--sandbox <read-only|workspace-write|danger-full-access>` · `-p/--profile <name>` layers `$CODEX_HOME/<name>.config.toml` · `-m/--model` · `-o/--output-last-message FILE` · `--json` JSONL events · `--output-schema FILE` constrains final-response shape · `--add-dir` extra writable dir · `--skip-git-repo-check` for non-repo dirs · `--ephemeral` no persistence.
**Checkpoint:** Worker exited 0; the final message (stdout / `-o` file / last JSONL `item`) carries the expected verdict or artifact.

### Phase 3: Resume to continue a session
```bash
cd "$REPO" && codex exec resume --last "Address the validator's findings, then re-run tests."
codex exec resume <SESSION_ID> "<follow-up>"
codex exec resume --last --json "<follow-up>" > events2.jsonl
```
`resume` takes a UUID session id or thread name; `--last` picks the newest in the cwd; `--all` disables cwd filtering. **Currency note (codex-cli 0.139.0):** `resume` accepts `-m/--model`, `-o/--output-last-message`, `--json`, `--output-schema`, `--ephemeral`, `-i/--image`, `--skip-git-repo-check` — but **NOT** `-C/--cd` and **NOT** `-s/--sandbox`. The resumed session inherits its original working root and sandbox policy, so `cd` into the repo first (the resume picks the newest session in the cwd) rather than passing `-C`/`-s`. `resume` cannot change the sandbox via `-s`, but `--dangerously-bypass-approvals-and-sandbox` (and `--dangerously-bypass-hook-trust`) IS available on resume — the resume-side lever for an externally-sandboxed host that needs a network-touching follow-up.
**Checkpoint:** The resumed session id matches the intended thread and the follow-up landed in the same working tree.

## Output Specification

**Format:** plain text (final agent message) by default; JSONL with `--json`; raw last message to a file with `-o/--output-last-message`.
**Filename:** caller-chosen via `-o <FILE>` (e.g. `/tmp/codex-verdict.txt`) or redirected JSONL (`events.jsonl`). No fixed convention — the orchestrator names it.
**Structure:** non-`--json` = the agent's final message to stdout. `--json` = one JSON event per line (item/agent/tool events); parse the terminal agent message item for the result. `--output-schema FILE` forces the final response to conform to a supplied JSON Schema (use for machine-checkable verdicts).

## Exit Codes

A loop should branch on the process exit code, not on scraped text.

| Code | Meaning | Loop action |
|------|---------|-------------|
| `0` | Run completed; final message emitted | Parse the result (`-o FILE` / last `--json` item); proceed |
| non-zero | Codex error — auth failure, sandbox denial, bad flag, or model/tool error | Do NOT treat as a verdict; re-check `codex login status`, sandbox mode, and flags, then retry or escalate |

## Quality Rubric

- [ ] `codex login status` showed `Logged in using ChatGPT` BEFORE dispatch
- [ ] No `OPENAI_API_KEY` in the worker env and no `--with-api-key` anywhere
- [ ] Sandbox mode matches role: offline validator → `-s read-only`; worker that edits → `-s workspace-write`; **network-touching validator** (`git fetch`/clone/API) → `-s danger-full-access` (read-only false-FAILs on blocked `connect`)
- [ ] Working root set explicitly with `-C`, not assumed from cwd
- [ ] Result captured deterministically (`-o FILE`, `--json`, or `--output-schema`) — not scraped from terminal noise
- [ ] Long/multi-turn work uses `resume` (not `--ephemeral`) so it can be recovered
- [ ] Multi-account lanes dispatched via `caam exec codex <profile> --`

## Validator dispatch rules (learned 2026-06-10, cp-4jac/cp-801l; extended cp-hhd7 cards 6–10)

- **Network-touching validators need `-s danger-full-access`.** A codex VALIDATOR that must read a Dolt-mode bd ledger, run `git fetch`, or reach any network MUST be dispatched with `-s danger-full-access`. `-s workspace-write` blocks network (`connect: operation not permitted`) and blocks FETCH_HEAD writes. A fail-closed FAIL caused purely by sandbox denial is an **infrastructure artifact, not a verdict**: fix the dispatch and re-run the judge. NEVER hand-verify the missing item yourself and upgrade the verdict — that breaks judge independence (author ≠ judge).
- **Set TMPDIR inside the workspace for any run that commits.** The sandbox blocks git temp-object writes to `/var/folders`; export `TMPDIR` to a path inside the workspace (e.g. `TMPDIR="$REPO/.tmp"`) before any codex run that needs `git commit` to succeed.
- **Verdict file contract.** Bare `VERDICT: PASS|FAIL` as the first line, then a blank line, then a bare `COMMANDS RUN:` line, then the commands + output verbatim. No `##` headings or parentheticals on those lines — the gate parses them anchored. Fail closed on anything unverifiable.
- **Write-scope clamp — mandatory in every judge brief (2026-07-02, showcase kernel R2).** State it verbatim: "READ-ONLY except writing your single verdict file at `<path>`. Do NOT commit, push, or run tracker/infra ops (git push, br/bd, dolt)." Role-scoped, not model-scoped — workers hold write scopes, judges never do. An unclamped codex judge has pushed a feature branch and attempted `bd dolt push` twice mid-judgment; a judge that mutates while judging can corrupt the artifact under judgment or preempt the pawl. Note the clamp is prompt-level discipline layered ON TOP of the sandbox: a network-touching judge dispatched with `-s danger-full-access` has nothing mechanical stopping a push.
- **Judge prompt pattern — publish the output contract from the prompt (card 10, cp-b2by).** A stated verdict spec drifts; the output shape must be derived from the prompt the judge reads. Minimal judge prompt:

  ```
  You are an INDEPENDENT VALIDATOR. Author != judge.
  READ-ONLY except writing your single verdict file at <path>.
  Do NOT commit, push, or run tracker/infra ops (git push, br/bd, dolt).
  BEAD: <id> — <title>
  ACCEPTANCE: <verbatim acceptance text>
  Re-run the cited commands on the actual artifacts. Do not read the evidence and agree.
  Attest identity: include "judge_source: codex-<model>" inside COMMANDS RUN.
  Return EXACTLY (no ## headings on these lines):
  VERDICT: PASS
  (blank line)
  COMMANDS RUN:
  judge_source: codex-<model>
  $ <cmd>
  <output snippet>
  REASONS:
  - bullet citing a COMMANDS RUN line
  ```
- **Output-contract validation before acting on a verdict.** Programmatically confirm: `VERDICT:` is on its own line, `COMMANDS RUN:` follows, `judge_source:` is present. A verdict missing any element is **unverified — discard and re-dispatch**. A judge that ran nothing is a reader, not a verifier (the counterfeit-judge shape, card 8). Use `--output-schema FILE` to enforce shape at the harness level when verdict feeds automation.

## Codex runtime work rules (learned 2026-06-12, ag-codex-runtime-enhancement post-review)

Compact rules for any work on the Codex worker/receipt path (dispatch, packets,
receipts, image-health). Full packet:
[`docs/learnings/2026-06-12-codex-runtime-review-auth-and-scope.md`](../../docs/learnings/2026-06-12-codex-runtime-review-auth-and-scope.md).

1. **Make the first acceptance test adversarial.** Before any planner artifact:
   test packet-injected `OPENAI_API_KEY`, disabled/missing auth guards, command
   or sandbox mismatch, missing final verdict, missing required command
   evidence, and path-escape attempts. The 2026-06-12 review found a
   packet-provided env could re-inject `OPENAI_API_KEY` after the ambient-env
   guard passed — ceremony missed it; one adversarial test would not have.
2. **Contracts need executable validators.** If a JSON Schema is the contract,
   the dispatch path must validate against it (or generated validation from
   it). Hand-written partial checks + fixture inspection are documentary, not
   enforcement.
3. **Receipt means evidence, not presence.** A receipt proving "Codex ran" is
   not a receipt proving "acceptance commands ran and passed." Run and record
   `evidence.required_commands` results, or rename the field so it stops
   implying acceptance evidence.
4. **Keep the critical path small.** Worker-path MVP = packet validation,
   dispatch, receipt on success/failure, timeout/stdin/auth tests, one
   fixture-backed smoke. Image health, gate explainability, skill authoring,
   and doc migrations are follow-up beads unless explicitly requested.
5. **Time-box discovery for implementation slices.** ~15 minutes discovery,
   ~90 minutes vertical slice, then decide. New work becomes follow-up beads,
   not scope absorbed into the active bead (risk-class routing:
   [`discovery`](../discovery/SKILL.md)).
6. **Approval evidence needs a durable proof surface.** If Fable/ATM approval
   gates implementation, mirror the council artifact or a compact proof packet
   to a tracked durable path before the gating bead/epic closes (the codex-approval
   Fable-approval bridge and its closeout rule are folded into this skill).

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Tokens billing to API account | API-key auth or `OPENAI_API_KEY` set | `unset OPENAI_API_KEY`; `codex login` (OAuth) or `--device-auth`; re-check `codex login status` |
| `Logged in with API key` in status | Wrong auth path | Re-auth on the sub via browser OAuth / `--device-auth`; never `--with-api-key` for workers |
| `not a git repository` error | `-C` points outside a repo | Add `--skip-git-repo-check` (or point `-C` at a repo) |
| Worker can't write files | `-s read-only` | Use `-s workspace-write`; add `--add-dir` for paths outside the root |
| `resume` finds nothing | Prior run used `--ephemeral`, or wrong cwd | Don't use `--ephemeral` for resumable work; try `resume --all` to drop cwd filtering |
| Hangs on `Reading additional input from stdin...` | Non-TTY stdin (background/`&`/ATM pane/cron) with no EOF — codex reads stdin even with a positional prompt | Pipe the prompt (`printf '%s' "$P" \| codex exec … -`) or add `</dev/null` to the positional form |
| Empty / truncated output in a loop | Parsing terminal text | Use `-o FILE` or `--json` and read the structured result |
| Rate-limited on the Pro lane | One account saturated | Switch lanes with `caam exec codex <other-profile> --` |

## See Also / References

- `ntm` — Claude worker panes (the Claude-side lane; never `claude -p`)
- `using-atm` — driving codex as an ATM **TUI pane** (keystroke / `--codex-goal` flow, `atm codex` readiness gates) vs this skill's **headless** `codex exec` (stdin/positional). Different dispatch mechanics, same auth/sub rules — conflating them is how "positional arg → background hang" and "send → wedged TUI pane" co-occur.
- `account-rotation` — host-routed account switching; on Codex/Gemini and Linux/WSL lanes the swap tool is `caam` (isolated multi-account profiles for the 4-lane flywheel: Claude Max ×2 + Codex Pro + Gemini)
- `dcg` — destructive-command guard that can enforce the never-API-bill rule · Memory "Never claude -p for workers 2026-06-06" — the Claude-side twin of this skill's core rule
