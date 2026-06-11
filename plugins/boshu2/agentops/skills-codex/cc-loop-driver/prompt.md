# Codex Execution Profile — cc-loop-driver

Read the sibling base skill `../SKILL.md` (full overview, the six critical
constraints, the six-phase workflow, output spec, quality rubric, examples, and
troubleshooting) before acting. That base file is the source of truth; this
profile is the Codex-native, step-ordered execution path. The Claude-native base
uses the Task tool for worker/validator fan-out; on Codex you fan out with
`codex exec` subprocesses (separate session contexts). Two rules are inviolable:
**subscription billing, never per-token API billing** (the Codex twin of the
banned `claude -p`), and **single-writer close** — only the orchestrator
(this session) ever runs `claim`, `close`, and `git commit`.

## Steps

1. **Preflight (base Phase 0).** Confirm the tracker binary (`bd` or `br` — use
   what `AGENTS.md` declares). Confirm `git status` is clean enough that a scoped
   commit won't sweep unrelated work. `mkdir -p evidence/`. Run `codex exec --help`
   and `codex exec resume --help` — never act on a remembered flag shape.
2. **Verify the lane is on the subscription.** `codex login status` MUST read
   `Logged in using ChatGPT`, and `OPENAI_API_KEY` MUST be empty. If either
   fails, STOP and fix auth before dispatching any worker — this is the only
   thing between a green overnight run and a surprise invoice.
3. **Pull + claim (base Phase 1, orchestrator only).**
   `id=$(bd ready --json | jq -r '.[0].id // empty')`; if empty, emit `NO_READY`
   and stop the tick. Else `bd update "$id" --claim` and `bd show "$id"` to
   capture the acceptance text verbatim. ONLY this session claims.
4. **Dispatch the WORKER (base Phase 2) via `codex exec`.** Fresh context, not
   this orchestrator. Pipe the worker prompt from `references/dispatch-templates.md`
   via stdin with a trailing `-`; set the root with `-C/--cd <DIR>`;
   `-s workspace-write` (it edits); capture deterministically with
   `-o/--output-last-message evidence/<id>.worker.txt`. The worker writes
   `evidence/<id>.md` (WHAT / PROOF / ACCEPTANCE MAP) and NEVER closes the bead.
5. **Dispatch the VALIDATOR (base Phase 3) via a SEPARATE `codex exec`.** Author
   != judge — a different subprocess context, never the worker's resume. Use
   `-s read-only`; for a machine-checkable verdict pass `--output-schema FILE`
   (VERDICT + COMMANDS RUN + REASONS) or `-o evidence/<id>.v1.txt`. The validator
   re-runs the cited commands and judges strictly, fail-closed on uncertainty. A
   verdict with an empty `COMMANDS RUN` is unverified — reject it and dispatch a
   fresh tie-break validator.
6. **Close + commit + publish (base Phase 4, orchestrator only, on verified PASS).**
   Use the `tick.sh close` helper from `references/tick-helper.md`: it verifies the
   evidence ref resolves, runs `bd close`, confirms the ledger shows closed,
   commits ONLY scoped paths (ledger + `evidence/<id>.md` + the bead's named
   files — never `git add -A`/`-u`), then confirms HEAD advanced or rolls the
   close back. On verified FAIL: reopen with the validator's reasons injected
   (retry budget 2, then escalate to a human). After a PASS commit lands, publish
   one compression (committed `.agents/` note or bead comment).
7. **Branch on exit code, not scraped text.** For every `codex exec`, exit `0` =
   completed (parse the `-o FILE` / `--output-schema` result); non-zero = a Codex
   error (auth, sandbox denial, bad flag) — NOT a verdict. Re-check auth/sandbox/
   flags, then retry or escalate.
8. **Loop (base Phase 5).** Repeat steps 3–7 until `bd ready` is empty. Emit
   `NO_READY` (work blocked/in-progress) or `CONVERGED` (no open or in-progress
   beads). For unattended re-drive, schedule the tick via the harness scheduler,
   not a shell `&` background loop.

## Guardrails

- **Never API-bill a worker or validator.** Do NOT set `OPENAI_API_KEY`, do NOT
  use `codex login --with-api-key`. That flips Codex to per-token API billing —
  the Codex twin of the banned `claude -p`. A factory cycle on API keys silently
  burns real money. Confirm the sub before dispatch (step 2).
- **Single writer.** Only this orchestrator session runs `claim`, `close`, and
  `git commit`. Workers and validators NEVER close or touch the bead verdict —
  this seam is the whole point of the loop.
- **Author != judge.** The worker `codex exec` and the validator `codex exec` MUST
  be separate subprocess invocations (separate contexts). Never resume the worker
  session to validate its own work — that is self-grade.
- **Evidence-gated close.** Close ONLY on `VERDICT: PASS` whose `COMMANDS RUN`
  cites real commands. No cited commands = unverified = rejected and re-routed.
- **The close cannot lie.** After `bd close`, confirm HEAD advanced AND the ledger
  shows the bead closed, else roll the close back. A closed-but-unpersisted bead
  is worse than an open one. Use `tick.sh close`, never a bare `bd close`.
- **Stage only scoped paths.** Never `git add -A`/`-u` in the close step — a
  blanket add sweeps unrelated in-flight edits into the bead's commit.
- **Sandbox is the blast radius.** `-s read-only` for validators,
  `-s workspace-write` for editing workers;
  `--dangerously-bypass-approvals-and-sandbox` only on an already-sandboxed host.
- **Verify before acting.** No remembered flag shapes — `codex exec --help` first
  (step 1).
- **Multi-account lanes go through `caam`, not env-var juggling.**
  `caam exec codex <profile> --` keeps each Pro lane isolated; hand-setting
  `CODEX_HOME` invites cross-account token bleed.
- **Backstage only.** Never surface these commands or framing in client-facing
  AI Partner content.
