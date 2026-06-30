---
name: superloopy-loop
description: Use Superloopy's lightweight strict-evidence loop for Codex tasks that need durable progress, criteria, and artifact-backed completion.
metadata:
  short-description: Lightweight strict-evidence loop harness
---

# superloopy-loop

Use this skill when the user asks for Superloopy, loopywork, lpy, a loop harness, durable criteria, evidence-backed completion, strict-but-light task flow, or guided next actions.

## Contract

- State lives in `.superloopy/`, or `.superloopy/sessions/<id>/` when `--session-id` is used.
- Do not hand-edit `.superloopy/goals.json`; use the CLI.
- A criterion can pass only after a real artifact exists under the active evidence root.
- User steering must use `SUPERLOOPY_STEER` JSON; do not hand-edit `.superloopy/goals.json`.
- Executor receipts should end with `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.
- Legacy `EVIDENCE_RECORDED` receipts remain accepted for compatibility.
- Tests are useful evidence, but completion requires the Superloopy evidence artifact.
- Use `superloopy loop prove` when an active goal needs command-backed evidence for its next unresolved criterion.
- Keep the workflow lightweight unless the task genuinely needs heavier review.
- A leading `loopy` keyword wakes the loop engineer: take the rest of the prompt as the brief, run the loop yourself, and report progress instead of asking the user to type Superloopy commands.
- `loopywork`, `$lpy`, and `lpy` are lighter prompt triggers; they inject guidance but never mutate `.superloopy/` state by themselves.

## Loop engineer (`loopy` keyword)

When the user opens a message with `loopy <task>`, act as the loop engineer:

- Start once with `superloopy loop begin --brief "<task>" --mode light --json`; do not create a second plan if one is active.
- Drive each step from `superloopy loop guide --json`, prove criteria with `superloopy loop prove -- <command>`, preflight with `superloopy loop check`, then finish with `superloopy loop finish --evidence "<summary>" --artifact .superloopy/evidence/gate.json --json`.
- The user types only `loopy <task>`. You run every Superloopy command and report progress as criteria proven and the next step.
- `loopy` with no task asks what to build; `loopy` mid-loop resumes from existing state. The Stop hook is packaged with the plugin but stays inert until `SUPERLOOPY_STOP_HOOK=on`; when enabled, it blocks completion until evidence exists.

### Two tiers: solo and crew (`loopy team`)

The loop engineer directive is injected for every `loopy` prompt, and it scales to the work:

- **Solo (default).** A plain `loopy <task>` drives one agent through the loop. The directive still permits light delegation: if the work splits into 2+ genuinely independent slices, you may fan them out in parallel with the host's native `multi_agent_v1.spawn_agent` (self-contained `message`, `fork_context: false`); for a single cohesive change, stay solo.
- **Crew (`loopy team <task>` / `loopy crew <task>`, the connected one-word `loopycrew <task>`, or the standalone `ultrawork <task>`).** The same engineer escalates into full fan-out: dispatch the crew across independent lanes, collect them with `multi_agent_v1.wait_agent`, and record only artifact-backed proof. The escalation keyword is stripped from the brief that seeds the loop. This is the active counterpart to "Optional Subagent-Driven Mode" below — same dispatch contract, receipt gate, and mandatory `handoff`/`fleet` tracking.

Each crew dispatch sets `agent_type` to the role so the host can load that role's TOML instructions and advisory model policy: `agent_type: "franky"` to build, `"zoro"` to review, `"usopp"` to test, `"jinbe"` to gate, `"robin"` to audit, `"nami"` to navigate. Because role routing and model defaults are best-effort across hosts, the `message` also stays self-contained (`TASK: act as <role> ...`) so the worker behaves correctly even if the host ignores `agent_type`.

Both tiers are steering, not enforcement: the directive instructs the main agent, and actual spawning depends on the host's native multi-agent tool being available. Superloopy never spawns; it gates the evidence workers deliver. See "Optional Subagent-Driven Mode" for the full dispatch contract and crew roles.

## Continuation Engine

The optional `Stop` hook is a bounded, progress-gated engine, not a one-shot nudge. With `SUPERLOOPY_STOP_HOOK=on`, while work remains it keeps driving you toward evidence-backed completion, counting iterations in `.superloopy/loop-control.json`.

- Progress is measured by recorded proof (passed criteria and completed goals) against a high-water mark; only new proof resets the no-progress counter.
- It never completes anything. Completion stays the plan's authority via `superloopy loop check` + `superloopy loop finish` with real artifacts.
- A cap or no-progress stall marks the loop `blocked` (visible in `superloopy loop status`) and asks for a human — it never fabricates a done.
- Quota/usage limits are distinct from `blocked`: when the host transcript shows a usage/rate/quota-limit marker, the loop is marked `paused` (reason `quota`) in `.superloopy/loop-control.json` — a *resumable* state. It does **not** burn the no-progress counter and is never mistaken for completion; a `loop_paused`/`loop_resumed` pair is written to the ledger. Superloopy is hook-driven and cannot self-wake, so it only pauses cleanly and stays resumable — see "Auto-resume after a quota reset" below.
- Knobs: `SUPERLOOPY_MAX_ITERATIONS` (default 50, `0` = unlimited; the no-progress guard stays active), `SUPERLOOPY_MAX_STALLED` (default 3), `SUPERLOOPY_CONTINUATION=off` (legacy single continuation), `SUPERLOOPY_QUOTA_MARKERS` (comma/newline list of extra host-specific limit phrases — the built-in set is conservative, so set this to your host's exact banner text).

### Auto-resume after a quota reset

Superloopy detects the limit and pauses; *waking* when quota resets is an external job (Superloopy has no daemon). Run an idempotent scheduler that resumes the loop and stops once it is done:

- Read `superloopy loop status --json`: if `summary.aggregateComplete` is false, resume by re-running the loop (`loopy <continue>`, or `superloopy loop guide --json` then the next command); if complete, no-op.
- Schedule it on a cadence that outlasts the limit window — a host cron / cloud routine every 20–30 min, or aligned to a known weekly reset. The first run after the reset succeeds; earlier runs simply no-op while still limited.
- Keep it idempotent and self-terminating, exactly like Superloopy's own gates. Superloopy supplies the resumable state; the scheduler supplies the wake.

## Evidence Audit

`superloopy loop audit` independently re-checks recorded proof. Superloopy itself re-runs each command-backed passed criterion (the deterministic source of truth) and records the result in `.superloopy/audit-state.json`; a re-run that does not reproduce is marked `inconclusive`, never a silent fail.

- For independent judgment, dispatch a read-only `robin` subagent: it judges the re-run against the scenario and ends with `SUPERLOOPY_AUDIT: <verdict-path>`. When the receipt arrives, Superloopy **re-derives that criterion's floor in-process** (it does not trust the recorded `.superloopy/audit-state.json`, which the worker can write) and accepts the verdict only if it is hash-bound to that fresh re-run. Floor dominance is symmetric: the verdict may act only when the re-run reproduces — it can neither upgrade nor flip a non-reproducing (`inconclusive`) re-run.
- At completion the deterministic spine actually gates the result: `superloopy loop review`/`checkpoint` re-derive **every passed criterion** (not just the cited ones) and hash-verify every cited audit verdict, so a regressed command criterion can't be skipped and a structurally valid audit section pointing at hand-written verdict files cannot authorize completion.
- Command-backed vs manual proof: the deterministic guarantee is strongest for **command-backed** criteria — Superloopy re-runs the command and reads the live exit code. A **manual (commandless)** criterion can only be re-validated for artifact existence; its correctness is not command-reproducible and rests on the auditor's (autonomous LLM) judgment and human review, not on the deterministic floor. **Prefer command-backed proof** (`superloopy loop prove -- <command>`) wherever the work allows — the autonomous loop engineer does this by default, so most criteria get the strong guarantee automatically.
- A failed audit (deterministic floor fail or a `verdict: fail`) flips the criterion off pass with the gap recorded in its notes, so the continuation engine re-drives exactly that criterion to be fixed and re-audited. A non-reproducing command re-run is `inconclusive` and never auto-flips (flaky-test safety).
- After `SUPERLOOPY_AUDIT_MAX_FAILS` (default 3) audit failures on the same criterion, it is marked `blocked` for a human instead of looping. Accepted audits are counted monotonically so honest fix → re-audit cycles register as progress.
- Honest limit: Superloopy cannot verify the auditor subagent was spawned isolated/read-only — it trusts the host's agent frame for that. It does NOT, however, trust its own recorded state: `.superloopy/audit-state.json` and `.superloopy/loop-control.json` are worker-writable, so the deterministic floor is re-derived in-process at both verdict acceptance and the completion gate — a forged state file cannot manufacture an accepted pass. The continuation counters (`auditsAccepted`, stall/high-water) are runaway backstops, not a security boundary; completion authority stays the plan's, and the engine never force-completes.

## Optional Subagent-Driven Mode

Use project custom agents from `.codex/agents/` only when the user asks for subagents or the work has independent implementation, review, and QA lanes. The normal single-agent Superloopy flow remains the default for small changes.

Superloopy provisions and tracks these agents; the host (Codex) spawns them. Superloopy never spawns. The host spawn surface cannot reliably select a bundled TOML role, model, or reasoning effort by name, so every dispatch must be self-contained and judged by delivered evidence — never by the role label requested. See `docs/superloopy-host-contract.md`.

Plugin installs bootstrap the `superloopy` command wrapper and bundled custom agents on the first approved `SessionStart` hook. If the host does not run that hook, run `node src/cli.js install --json` from the Superloopy checkout or installed plugin root. `superloopy agents install` remains available to copy only the bundled custom agents into the personal Codex agents directory (`$CODEX_HOME/agents` when set, otherwise `~/.codex/agents`). Restart Codex after installation.

Parent agent responsibilities:

- Keep the Superloopy plan and criteria as the source of truth.
- If the requested repository path differs from `cwd`, verify and state the exact target path before editing or dispatching workers.
- Allocate one bounded handoff card per worker: goal, criterion or slice, allowed files, active evidence root, report artifact target, validation command, non-goals, and expected status values.
- Avoid parallel executors on overlapping files. Parallelize read-heavy review, QA, and summarization lanes first.
- In full crew mode, the implementation worker must own a real bounded implementation slice before the parent edits or completes that slice. If there is no safe independent implementation slice, stay solo or use a smaller read-only crew instead of pretending an implementer lane ran.
- Wait for worker summaries, then record only artifact-backed proof with `superloopy loop prove`, `superloopy loop evidence`, `superloopy loop review`, or `superloopy loop checkpoint`.
- Summarize worker output by status, claim, changed files, commands, artifacts, risks, and next action. Do not paste raw transcripts into the main thread unless they are the evidence.
- After each worker finishes, show the user a concise role completion line with the role, normalized verdict, artifact path, and next action before closing or respawning that lane.
- For full crew, record each dispatch with `superloopy loop handoff --agent <name> --assignment <text> [--verdict <v>] [--artifact <path>]` and run `superloopy loop fleet --json` before the final gate. The fleet output normalizes the workers' APPROVE/PASS/REJECT-style verdicts into one accept/reject/needs-context enum and lists outstanding workers. An accepted verdict requires a valid artifact under the active evidence root. A lifecycle verdict (`working`/`in_progress`/`running`) stays outstanding; an unresolved verdict (`inconclusive`/`timeout`/`ack_only`) normalizes to needs-context and is NEVER counted as accept. Rejected and needs-context lanes appear in `attention`. Known crew lanes may print one original completion line for terminal verdicts, choosing the user's language from the assignment or scoped brief when it matches the supported catalog (`en`, `ko`, `ja`, `zh`, `es`, `fr`, `de`, `it`, `pt`, `id`, `hi`, `tr`, `vi`, `ru`, `ar`, `th`), but the line is presentation only; artifacts, normalized verdicts, `attention`, and `outstanding` remain authoritative. Use `--language <tag>` or `SUPERLOOPY_CREW_LANGUAGE=<tag>` only when the prompt language cannot be inferred. Set `SUPERLOOPY_MAX_PARALLEL` for a soft over-dispatch warning. Handoffs are parent-side bookkeeping only — they never spawn or complete.
- Before the final summary, run untracked-aware status commands such as `git status --short --untracked-files=all` and `git ls-files --others --exclude-standard` so new evidence, scripts, and reports are not omitted from the diff review.

### Dispatch contract (self-contained)

Because role-by-name routing is unverified, each spawn message must stand alone — paste the role's requirements into it rather than relying on the agent name. Lead with an imperative `TASK:` and name the rest:

- `TASK:` the one bounded assignment (one criterion or one non-overlapping slice).
- `DELIVERABLE:` the report artifact path under the active evidence root, and the required receipt (`SUPERLOOPY_EVIDENCE` for workers; `SUPERLOOPY_AUDIT` for `robin`; `nami` writes none).
- `SCOPE:` allowed files, the active evidence root, the validation command, and explicit non-goals.
- `VERIFY:` the binary check that decides PASS/FAIL.

State that it is an executable assignment, not a context handoff. Prefer a fresh, minimal context over a full-history fork so the child works the delegated task instead of continuing old parent state.

### Subagent lifecycle

- Treat a running child as alive, not as a timeout counter. For a long pass, have it emit `WORKING: <task> - <phase>`; reserve `BLOCKED: <reason>` for genuine stalls.
- Do not record a criterion pass, mark a dependent step done, or finish the loop while a live child still owns that step's evidence.
- A silent or ack-only child after follow-up is **inconclusive — never an approval or a pass**. Close the lane, record it as inconclusive, and respawn a smaller self-contained task with only the missing deliverable.

Agent allocation:

- `franky`: edits one criterion or independent slice, writes a report, and ends with `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.
- `zoro`: reviews diff, scope, and evidence; writes a report under the active evidence root; does not edit product files.
- `usopp`: exercises happy-path, regression, and risk scenarios; writes artifact-backed QA evidence; does not edit product files.
- `jinbe`: integrates implementation, review, QA, audit, and criteria coverage; writes a final gate report such as `.superloopy/evidence/jinbe-final-gate-report.md`; the parent still runs Superloopy completion commands.
- `robin`: read-only, skeptical evidence auditor; judges Superloopy's deterministic re-run against the scenario and ends with `SUPERLOOPY_AUDIT: <verdict-path>`. Installed by `superloopy agents install` alongside the workers.
- `nami`: read-only codebase navigator; locates files and code and returns absolute paths with a direct answer. Writes no evidence and edits nothing — dispatch it first to scope a slice before assigning an executor. Parallelize it with review/QA lanes.

## Basic Flow

```sh
superloopy loop begin --brief "<task>" --mode light --json
superloopy loop create --brief "<task>" --mode light --json
superloopy loop create --brief "<task>" --session-id "<id>" --mode strict --json
superloopy loop create --brief $'@goal: Build\n<story one>\n@goal: Verify\n<story two>' --json
superloopy loop guide --json
superloopy loop trace
superloopy loop report
superloopy loop check
superloopy doctor --comparison-path /path/to/comparison --json
```

`status` is the fastest reorientation command; it returns current counts and the immediate guide.

`create` returns the immediate guide too; follow it with `next` unless you used `begin`.

`begin` already starts the first goal and returns the immediate guide, including the next proof command.

The guide shows the next command, proof target, recorded evidence, proof plan, capture template, and evidence template. It also shows recorded evidence for already-passed criteria with each captured timestamp, a flow checklist for start or resume, record artifact-backed proof, check evidence, and finish with quality gate, unresolved criteria with suggested proof paths, manual evidence templates, plus the trace, report, and check commands for evidence inspection. Capture, evidence, and repair templates include `--notes "<summary>"` so proof rows stay self-documenting.

For the active goal's next unresolved criterion, prove command-backed evidence directly:

```sh
superloopy loop prove -- npm test
```

For explicit criterion targeting, write artifacts under `.superloopy/evidence/` or capture a command transcript:

```sh
superloopy loop capture --goal-id G001 --criterion-id C001 -- npm test
superloopy loop evidence --goal-id G001 --criterion-id C001 --status pass --artifact .superloopy/evidence/<artifact>.txt --notes "<summary>" --json
```

Inspect the evidence trail when reporting progress or looking for missing proof:

```sh
superloopy loop trace
superloopy loop report
```

`trace` and `report` both return the next guide action after showing or writing evidence context, including evidence summary counts and a timestamped timeline from the ledger. Their artifact rows include capture times for already-recorded proof, and timeline rows include manual evidence notes when provided. The report artifact also includes recorded evidence with captured timestamp, an Evidence Summary section, the current next action, proof plan, and suggested artifact paths for criteria still missing proof.

Run the lightweight preflight before finishing:

```sh
superloopy loop check
```

`check` prints an evidence summary with artifact-backed criteria, unresolved, and invalid counts. If it is blocked, use the numbered repair plan: each step names the target artifact, capture command, and manual evidence alternative.

`trace`, `check`, and `report` also surface warnings for commandless manual proof and exhausted worker/auditor attempts. Warnings do not fail a preflight by themselves, but they are a prompt to prefer command-backed proof or close an inconclusive lane.

Finish in one command after all criteria pass:

```sh
superloopy loop finish --evidence "<summary>" --artifact .superloopy/evidence/gate.json --json
```

Keep the human final gate report and the Superloopy quality gate artifact separate. A `jinbe` report is Markdown evidence (for example `.superloopy/evidence/jinbe-final-gate-report.md`). The `superloopy loop review` and `superloopy loop finish --artifact` flag writes the machine-validated quality gate artifact and must point to JSON, normally `.superloopy/evidence/gate.json`. Never pass the Markdown report path as the finish artifact.

For custom gate workflows:

```sh
superloopy loop review --status passed --artifact .superloopy/evidence/gate.json --notes "<summary>" --json
superloopy loop checkpoint --goal-id G001 --status complete --evidence "<summary>" --quality-gate .superloopy/evidence/gate.json --json
```

When a final proof command can be satisfied from cache but the task needs fresh evidence, capture a rerun variant in the artifact, for example Gradle `--rerun-tasks` on the focused JVM test. Use this for final evidence capture, not as a default tax on every local check.

## Quality Gate

Every listed artifact must exist, be non-empty, and live under the active evidence root. Superloopy also accepts strict review gates and matrix gates when reviewer/architect, executor QA, rerun, artifact, and coverage fields validate.

For executor receipts, use the active evidence root. A global loop normally records under `.superloopy/evidence/`; a scoped loop records under `.superloopy/sessions/<id>/evidence/`. If a receipt is missing or invalid, the receipt block message names the active evidence root to repair.

## Steering

Accept only structured prompt-level steering:

```text
SUPERLOOPY_STEER: {"kind":"annotate","evidence":"fact","rationale":"why it matters"}
SUPERLOOPY_STEER: {"kind":"add_goal","title":"New slice","objective":"Concrete objective","rationale":"why it changed"}
SUPERLOOPY_STEER: {"kind":"revise_criterion","goalId":"G001","criterionId":"C002","scenario":"New scenario.","rationale":"why it changed"}
SUPERLOOPY_STEER: {"kind":"reorder_pending","goalIds":["G003","G002"],"rationale":"why this order"}
```

After any accepted steering, follow the returned guide; run `superloopy loop status --json` when you need a fresh reorientation.

## Doctor

`superloopy doctor --json` checks the package, hooks, skill, CLI, dependency-free boundary, runtime ignore policy, file inventory, gate notes, design audit, generic comparison scan status, dispatch coherence, model policy, and reviewability.

Use `superloopy doctor --comparison-path /path/to/comparison --json` only when you need copied-block evidence against an external folder. The generic comparison scan compares code-shaped files for substantial contiguous blocks without naming or coupling Superloopy to any source project.
