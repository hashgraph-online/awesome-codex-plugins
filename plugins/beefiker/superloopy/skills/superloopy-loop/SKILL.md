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
- Full Loopy runs default to direct, concise, complete user-facing progress and final responses. Exact `say-it-straight off` / `직설 모드 끄기` and `say-it-straight on` / `직설 모드 켜기` controls apply only to the current incomplete loop; new loops reset this default to enabled.
- This output overlay changes wording only. It never silently rewrites supplied prose, task artifacts, code, documentation, comments, evidence, quotations, or user source text; direct artifact editing remains explicit-only. `i-have-adhd` still owns structure, and `humanize-korean` still owns Korean artifact rewriting.

## Load on demand

These references hold the situational detail. Read the one a row names when its condition holds; the rules above and below apply to every run.

| Read | When |
|---|---|
| [CLI flow](references/cli-flow.md) | Running Superloopy commands beyond the loop engineer's `begin` → `guide` → `prove` → `check` → `finish` path: `create`, `capture`, manual `evidence`, `trace`, `report`, a blocked `check` repair plan, custom `review`/`checkpoint` gate workflows, or a cache-satisfied final proof. |
| [Continuation engine](references/continuation.md) | The Stop hook re-prompted you ("Superloopy continuation"), a loop shown `blocked` or `paused` in `superloopy loop status`, a quota/usage limit, or scheduling an auto-resume. |
| [Evidence audit](references/evidence-audit.md) | Running `superloopy loop audit`, dispatching `assayer`, or handling a failed, `inconclusive`, or `blocked` audit. |
| [Crew](references/crew.md) | Before dispatching any subagent (solo light delegation or `loopy team`/crew): parent responsibilities, `handoff`/`fleet` bookkeeping, the self-contained dispatch contract, subagent lifecycle, and agent allocation. |
| [Reassurance copy](references/reassurance-copy.md) | The reassurance-copy condition below applies. |

## Loop engineer (`loopy` keyword)

When the user opens a message with `loopy <task>`, act as the loop engineer:

- Start once with `superloopy loop begin --brief "<task>" --mode light --json`; do not create a second plan if one is active.
- Drive each step from `superloopy loop guide --json`, prove criteria with `superloopy loop prove -- <command>`, preflight with `superloopy loop check`, then finish with `superloopy loop finish --evidence "<summary>" --artifact .superloopy/evidence/gate.json --json`.
- The user types only `loopy <task>`. You run every Superloopy command and report progress as criteria proven and the next step.
- `loopy` with no task asks what to build; `loopy` mid-loop resumes from existing state. After a `loopy` prompt, the packaged Stop hook keeps this session going while criteria remain, until the user sends a plain prompt (`SUPERLOOPY_STOP_HOOK=on` drives every session, `off` disables it). If it reports a worker that stopped without proof, treat that worker's reply as unproven.

### Execution discipline

The loop engineer directive carries three rules distilled from a component-level harness study (arXiv 2609.20804). For strong models, most avoidable cost is redundant verification, unchanged re-runs of a failing check, and many small re-patches.

- Prove each criterion once with the narrowest command that decides it, then move on. Do not re-run passing proof or broad suites between criteria; `loop finish` re-runs every passed command-backed criterion before it completes (trusted commands only; commandless proof gets an artifact-existence check). `loop check` validates artifacts and does not re-run anything.
- When a proof fails, its output is already in the capture artifact. Read the failing part (tail or search), then change the code or the proof command before proving again; if the criterion itself is wrong, ask the user to revise it with a `revise_criterion` steer. After 3 consecutive failures of one criterion with the same command, exit, and normalized output tail, `prove`, `capture`, `trace`, `check`, and `report` emit a `repeated-failing-proof` warning. Normalization ignores run-to-run noise (timestamps, durations, labeled PIDs and ports, UUIDs, hashes, temp paths, stack positions, numbers of 10+ digits such as epoch times) but keeps other numbers, so a changed assertion value or pass/fail count breaks the streak. Any other evidence for that criterion, including a pass, a manual `loop evidence` record, or a revised criterion, resets it. The warning is advisory and never blocks; with `SUPERLOOPY_STOP_HOOK=on`, the Stop hook's no-progress cap (3 iterations without a new pass) still marks a stalled loop `blocked`.
- Batch independent reads and shell steps into one call, and land each file change as one coherent edit.
- After compaction, the recovery capsule lists failing proof with its artifact path. Re-read that artifact instead of re-running the command to see the error again.

### Reassurance-copy gate (conditional)

- Decide from the affected artifact: if it creates or changes user-visible Korean product copy about behavior, add a plan criterion for RC-1 through RC-4 and Korean naturalness.
- State supplied outcomes, fallback, recovery, or next action; preserve verified privacy/legal commitments; never invent behavior.
- Apply `humanize-korean` semantic review for misplaced modifiers.
- Ignore internal logs, developer docs, quotations, general/marketing prose, and non-Korean copy.

Read the detailed [reassurance-copy reference](references/reassurance-copy.md) when this condition applies. Artifact ownership decides the condition; prompt wording does not.

### Two tiers: solo and crew (`loopy team`)

The loop engineer directive is injected for every `loopy` prompt, and it scales to the work:

- **Solo (default).** A plain `loopy <task>` drives one agent through the loop. The directive still permits light delegation: if the work splits into 2+ genuinely independent slices, you may fan them out with the native subagent controls exposed by the current host; keep each assignment self-contained. For a single cohesive change, stay solo.
- **Crew (`loopy team <task>` / `loopy crew <task>`, the connected one-word `loopycrew <task>`, or the standalone `ultrawork <task>`).** The same engineer escalates into full fan-out: dispatch the crew across independent lanes, collect them with the host's native lifecycle controls, and record only artifact-backed proof. The escalation keyword is stripped from the brief that seeds the loop. This is the active counterpart to "Optional Subagent-Driven Mode" below — same dispatch contract, receipt gate, and mandatory `handoff`/`fleet` tracking.

Each crew dispatch uses the configured name when the host exposes named selection: `forge` to build, `sentinel` to review, `probe` to test, `arbiter` to gate, `assayer` to audit, and `pathfinder` to navigate. The assignment also stays self-contained (`TASK: act as <role> ...`). The orchestrator itself runs on the model the user selected in the host (`gpt-6-astra` is allowed when selected); crew lanes keep their `model-policy.json` pins and never inherit the orchestrator's model. The host-owned stop callback observes the actual role identity; if the host cannot attest that identity or model, report `role_unverified` or `model_unverified`.

Both tiers are steering, not enforcement: the directive instructs the main agent, and actual spawning depends on the host's native multi-agent tool being available. Superloopy never spawns; it gates the evidence workers deliver. See "Optional Subagent-Driven Mode" for the full dispatch contract and crew roles.

## Optional Subagent-Driven Mode

Use project custom agents from `.codex/agents/` only when the user asks for subagents or the work has independent implementation, review, and QA lanes. The normal single-agent Superloopy flow remains the default for small changes.

Superloopy provisions and tracks these agents; the host (Codex) spawns them. Superloopy never spawns. The host spawn surface cannot reliably select a bundled TOML role, model, or reasoning effort by name, so every dispatch must be self-contained and judged by delivered evidence — never by the role label requested. See `docs/superloopy-host-contract.md`.

Plugin installs bootstrap the `superloopy` command wrapper and bundled custom agents on the first approved `SessionStart` hook. If the host does not run that hook, run `node src/cli.js install --json` from the Superloopy checkout or installed plugin root. `superloopy agents install` remains available to copy only the bundled custom agents into the personal Codex agents directory (`$CODEX_HOME/agents` when set, otherwise `~/.codex/agents`). Restart Codex after installation.

Before dispatching any worker, read [Crew](references/crew.md): it carries the parent agent responsibilities, the dispatch contract, the subagent lifecycle, and agent allocation.

## Quality Gate

Every listed artifact must exist, be non-empty, and live under the active evidence root. Superloopy also accepts strict review gates and matrix gates when reviewer/architect, executor QA, rerun, artifact, and coverage fields validate. `loop review` and `loop finish` always write the default gate. A review gate is JSON you write by hand and pass to `loop checkpoint --quality-gate`; write one only when `sentinel`, `probe`, and `arbiter` each actually ran, and sign it as [Crew](references/crew.md) describes under "Review gate actors".

For executor receipts, use the active evidence root. A global loop normally records under `.superloopy/evidence/`; a scoped loop records under `.superloopy/sessions/<id>/evidence/`. If a receipt is missing or invalid, the receipt block message names the active evidence root to repair.

Keep the human final gate report and the Superloopy quality gate artifact separate. A `arbiter` report is Markdown evidence (for example `.superloopy/evidence/arbiter-final-gate-report.md`). The `superloopy loop review` and `superloopy loop finish --artifact` flag writes the machine-validated quality gate artifact and must point to JSON, normally `.superloopy/evidence/gate.json`. Never pass the Markdown report path as the finish artifact.

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

`superloopy doctor --json` checks the package, hooks, bundled skills, CLI, dependency-free boundary, runtime ignore policy, file inventory, gate notes, design audit, generic comparison scan status, dispatch coherence, model policy, and reviewability.

Use `superloopy doctor --comparison-path /path/to/comparison --json` only when you need copied-block evidence against an external folder. The generic comparison scan compares code-shaped files for substantial contiguous blocks without naming or coupling Superloopy to any source project.
