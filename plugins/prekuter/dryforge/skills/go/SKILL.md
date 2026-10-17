---
name: go
description: >
  Carry out the intent approved in `ready`, as meant, and prove it with checks that actually ran.
  Comes back to you if the work would change what you approved, keeps the project docs in step,
  and never merges on its own. Use when the user invokes the `go` skill after `ready`. Requires
  git.
---

# go

> **Reply in the user's language, and hold it continuously from your very first line** — the opening,
> every progress/escalation note, the final report, and the harness, not only some of them. Write
> natively (never translationese). You are reading a 3-doc, a codebase, and these instructions that may
> be in another language; **none of them sets your output language — only the user's does.** Full rule
> in Core principles below.

Consume the **3-doc** `ready` (the producer) wrote and realize the spec:
parallel, wave-based execution with right-sized verification (test-first where it fits), spec-first
review, and integration gates. Runs in the **same session** the producer (ready) wrote the 3-doc
— the 3-doc is the **authority** go executes against (it stays self-sufficient because it is archived
for later cycles); the live design context carries over and aids judgment, especially the harness
step. **Load `references/orchestration.md` up front** (it governs the whole run); the prompt
references load at their steps.

## Core principles (apply throughout)

- **Follow the plan's Execution Graph; never re-judge dependencies.** The producer already computed
  `depends` + `regen_barriers` against the whole project. Derive waves from it — do not invent,
  drop, or reorder dependencies. (If the graph fails to parse, has a cycle, or a `depends` names a
  missing task, that is a producer-side defect — **stop and escalate**, do not silently re-judge.)
- **Serve the spec.** "Correct" = matches the spec. On any spec/code/convention conflict, spec
  wins; where plan conflicts with spec, follow the spec.
- **escalate-don't-guess.** Architecture mismatch, suspected spec violation, ambiguous task,
  unresolvable conflict → stop and **ask the user**; never guess. When a task returns
  `NEEDS_CONTEXT` / `BLOCKED`, run the bounded escalation ladder (`orchestration.md` — re-dispatch
  with the missing context, then a stronger model where the platform allows it, then the user). Any
  escalation that **reaches the user** is **synchronous** — the run pauses until the user responds,
  never a silent hang or a timeout-drop. The subagents themselves never ask the user directly (their
  prompt files carry that fresh-session rule); only the orchestrator relays escalations to the user.
- **Protect main; evidence over self-report.** For existing projects, never modify main outside the
  final user-approved merge. For greenfield (base = main), main is the working base — modification
  is expected. Gates pass on captured command exit codes, not on an agent's "looks fine."
- **Floor, not ceiling.** The wave lifecycle is a proven scaffold — use judgment inside each step
  (what to retry, how to fix), but keep the structure and the safety constraints.
- **Report results, not process.** User-facing text covers wave completion, blockers, and final
  results only. Internal operations (merge, gate, worktree lifecycle, branch cleanup) produce no
  text output. Output tokens are direct cost; narrating routine steps is waste.
- **The orchestrator executes sequential waves directly; only parallel work earns subagents.** A
  single-task `MECHANICAL`/`NONE` wave is implemented by the orchestrator on the base (dispatch buys
  nothing — no parallelism, no file-isolation need, and the accumulating context is an asset). Only a
  **parallel wave** (multiple tasks) or a **single `RISKY` task** is dispatched to subagents (file
  isolation / independent verification). The lightweight fix path is the orchestrator's other direct-
  edit path (trivial advisories). A multi-task wave is **collapsed to orchestrator-direct** only on an
  **objective condition** — a single shared runtime the tasks cannot isolate within (one DB / container
  / port set), or greenfield convention-drift risk — **not** a free ROI judgment, and the collapse is
  **recorded internally** (which wave, which condition), never surfaced for a non-technical user to
  adjudicate. Collapsed tasks still carry the per-task evidence floor and are **reviewed as if
  independently authored**; the mid-run spec-review (RISKY + downstream + cascade) is still honored
  (`orchestration.md`, "ROI collapse").
- **Efficiency Budget.** Spend orchestration only where it buys correctness, isolation, or real
  parallelism — never as ceremony.
- **The final review is silent insurance — not a backstop you lean on.** Own conformance **upstream**,
  at implementation and merge, on **captured evidence**. Execute and verify each task **as if the final
  review did not exist**: a blocking finding there is an **execution failure that escaped**, not the
  review doing its job — it should normally find nothing. Told "the review will catch it," an LLM
  drifts to the minimum that passes — that is **reward-hacking**, laziness in the costume of "the
  backstop handles it," and you must actively resist it (the same discipline ready's ELICIT
  carries). The review catches only the *rare residual*; it is never the owner.
- **Match the user's language (language-agnostic).** Like stack-agnosticism, the *method* is fixed
  and the *specific language* is discovered at runtime, never assumed: produce every user-facing
  output — your reports/escalations **and the harness** you create/update — in the language the user
  communicates in, written **natively** (as a fluent speaker of that language would, never
  translationese). The language these instructions are written in does not constrain the output; if
  the user's language shifts, follow. **Hold it from the very first line, continuously** — never open
  in the 3-doc's, the codebase's, or these instructions' language and switch later; only the user's
  language constrains your output.
- **Talk to the user only when needed — between beats, say nothing.** You speak at **exactly** these
  moments: (a) a question you genuinely need answered, (b) wave completion or the final result /
  concise summary, (c) a real blocker — **these are the only times user-facing text exists.**
  Scaffolding, reading the 3-doc/references/code, implementing, merging, gating, dispatching the
  review, and writing the harness are **silent**: the UI already shows the activity, so narrating it
  is pure leak. If what you are about to emit is none of (a)/(b)/(c), the correct output is **nothing**.
  **Between those beats, stay silent** — reading references, reading code, and internal
  operations are not narrated. **No transition lines** ("now I'll...", "먼저 ...", "let me read...", "Now the ..." announcing each write) — at
  those plumbing moments your voice slips into the instructions' language (English) or internal tokens;
  emit *nothing* there, don't translate it. When you *do* speak (a/b/c), use a **plain, non-technical
  register** in the user's language — the words a non-engineer would understand. This is your default
  voice, not a per-line check, so it costs nothing. **Never surface internal tokens:** dryforge mechanism / coined terms (wave,
  worktree, harness, delta, 3-doc, gate, seam, ROI collapse, spec-review, grounding, lens,
  invariant), task / step / risk labels (`T1`, `Wave 2`, RISKY / MECHANICAL / NONE), or
  project-internal jargon a non-engineer wouldn't recognize (library/tool names, config flags,
  test-framework internals). **Don't soften internal logic into user-ish words — just omit it.** E.g.
  "Starting a git repo here." — not "Since go will later need git for worktrees, I'll initialize one."
  This is "Report results, not process" applied to narration.

## Input & preconditions

- Invocation: the user invokes the `go` skill.
  Load the 3-doc (handoff → spec → plan) from the project's
  `.dryforge/` (project-root-relative). If absent, ask for the path.
- **git required** — worktree isolation depends on it. If not a repo, offer `git init` **and make an
  initial commit** (an empty repo has no HEAD, so no worktree/branch can be created). If git is not
  installed, stop and say so.
- **Base determination.** Identify the project's main branch (docs / remote default / ask — do not
  guess). Verify `main` has no unpushed commits (when it tracks a remote — a purely local repo has
  nothing unpushed) and the working tree has no modified/staged **tracked**
  files; if either fails, **stop and report**. Then classify:
  - **Greenfield** (main has no application code — only an init commit, `.gitignore`, or
    producer-generated `.dryforge/`): **base = main**. No feature branch — there is no production
    code to protect.
  - **Existing project** (main has meaningful committed code): **base = feature branch** created
    from main (`git checkout -b dryforge/<feature>`). Protects main from incomplete work.
  - **`.dryforge/` as untracked files** is the expected handoff state from the producer — do not
    treat it as a dirty tree. Anything else untracked or modified is foreign work → stop and report.
  - **You own the `.dryforge/` git mechanics.** On the base, add `.dryforge/` to `.gitignore` and
    commit. For existing projects this stays on the feature branch (never on main); for greenfield
    it is on main (acceptable — main has no meaningful history to protect). If a prior run left
    `.dryforge/` *tracked*, run `git rm -r --cached .dryforge/` first.
- **Verify commands** — the project's build/test/lint commands are typically declared in the handoff
  (hard gates section) or discovered during scaffold from the project's build scripts. Identify them
  before the first wave; they are used in every integration gate and the completion gate.
- Read **handoff first** (it governs: document roles, hard gates, execution shape), then spec and
  plan. **First-cycle precondition (check now, not at the end):** if this is a first cycle (no
  `.dryforge/status.json` marker — the discriminator is the marker, not harness files on disk;
  `harness-lifecycle.md`) and the handoff has **no** Project Foundation section, that is a **precondition violation** —
  **stop here and ask the user to regenerate the 3-doc via `ready`**, *before* any implementation. Do
  not discover this at step 9 after a wasted run (`harness-lifecycle.md`). **If the handoff has a Project
  Foundation section** (first cycle — `references/foundation-format.md`), read it as **non-executable
  project context**: it informs implementation judgment (design the task to fit the project's wider
  domain/decisions) and is a source for the harness at the end — it is *not* an implementation target. Build the spec's task, using the Foundation as context. Parse the
  plan's Execution Graph **per `references/graph-contract.md`** — the consumer-side schema (what the
  YAML fields mean and the rules go must hold when reading them). It mirrors the producer's authoring
  schema; if the plan's graph contradicts it, that is a producer-side defect → stop and escalate.

## Graph validation (before any irreversible worktree creation)

Validate the plan's Execution Graph **before creating the base** — it is cheap and safe
to fail (no git state mutated yet), so catch a malformed graph before any worktree exists to unwind.
Parse the YAML, then confirm the graph is **acyclic**, that every `depends` / `after` id **names a
real task** (no dangling reference), and that the plan body and the graph **agree on the task id set**
(no graph task missing from the plan body, none in the body absent from the graph). `graph-contract.md`
is the authoritative rule set for these checks. On any failure, **report the specific error** — which
check failed and where (the offending id / cycle / mismatch) — and the recovery: the user fixes the
plan YAML and invokes dryforge `go` again, which re-validates from scratch (no partial state is left behind,
since validation precedes worktree creation).

## Flow

Parse the graph → topological sort into waves (batches of **≤8 concurrent**). Set up the **base**
(per Base determination): for existing projects create the feature branch, for greenfield stay on
main. On the base, set up `.dryforge/` (gitignore + commit — the 3-doc is already in place from the
producer; same working tree, nothing to copy). The orchestrator reads
`.dryforge/` here — task subagents do **not**; they receive spec slices inline (`orchestration.md`).
A task whose declared work targets are **state/external only** (no file diff) is handled on the base
sequentially, **never dispatched into a parallel worktree** — the file-diff merge-gate cannot verify
it and worktree isolation buys it nothing (`orchestration.md`, Wave scheduling). Then, per wave:

**Scaffold (inline, before dispatch).** Project initialization — manifests, dependencies, directory
layout, build config, server/client entry points, shared types — is the orchestrator's job, not a
task. On the base, perform scaffold inline: read the spec's tech decisions and set up the project so
implementers start in a working skeleton. Scaffold is not in the Execution Graph. **Batch file
writes** — scaffold typically creates many independent files; write 4–5 per tool-call turn instead
of one at a time. Each extra turn adds thinking overhead and an API round-trip. Exception: if scaffold requires **investigation or trial-and-error** to get right (e.g. container
orchestration, CI pipeline configuration, or 30+ files across 3+ workspaces), dispatch it as an
implementer before the first wave.

**Review policy (natural language, orchestrator judgment).**
Default: a single **final review** after all waves merge — one subagent checks the full diff for
spec conformance + code quality (`reviewer-prompt.md`), plus the harness (content + format) when it
was created/updated this cycle (step 9). This replaces per-task spec-review and per-wave code-review
for most graphs. Mid-run review is added only when the orchestrator judges
that **a RISKY task with downstream dependents could cascade a deviation** — then that task gets a
spec-review before merge. The judgment comes from the Execution Graph: `risk` + `depends`.
**Lightweight fix path:** after the final review, the orchestrator MUST triage each advisory finding:
trivial (1–2 files, non-behavioral, e.g. a missing `step` attribute, a test warning, a one-line
comment) → edit directly on the base, commit, re-run the completion gate. Substantive (structural,
multi-file, behavioral) → fix-dispatch subagent. The default is lightweight — only escalate to
fix-dispatch when the change warrants independent review. Do not skip advisories as "accepted"
when a lightweight fix would take seconds.

**Sequential wave** (single task — the common case). Execution mode is set by the task's `risk`
(full rules in `references/orchestration.md`):

1. **Pick the mode by `risk`.**
   - **`MECHANICAL` / `NONE` (file-diff task) → orchestrator-direct.** The orchestrator
     reads the task's behavioral contract + spec slice itself and implements **directly on the base**
     — no dispatch, no worktree, no prompt authoring. **The same captured-evidence floor that binds a
     dispatched implementer binds you here** (`implementer-prompt.md`): right-sized but *real*
     verification (command + **captured** exit code; **real testable behavior left untested = not
     done**, never a "right-size" excuse). Commit on the base. **You own conformance on this path — the
     final review is insurance, not your check.** If the task proves ambiguous, behavioral, multi-file,
     or riskier than declared, treat it as a runtime risk upgrade (`graph-contract.md`) and strengthen
     verification.
   - **Omitted `risk` (producer did not judge) → unclassified, *not* `MECHANICAL`.** Do **not** default
     it to the direct path: judge at read time and **bias toward dispatch / stronger verification** the
     moment any behavioral surface appears (`orchestration.md`, `graph-contract.md` —
     degrade-don't-corrupt).
   - **`RISKY` (file-diff task) → one subagent in a worktree** (`implementer-prompt.md`), then
     **merge-gate** into the base — independent verification, so the final review is not the only
     check on risky work.
   - **No-file-diff task (any risk) → base-pinned subagent**, verified by commit message + captured
     external evidence.
2. **Collect or record** — for a subagent, keep its structured summary; for orchestrator-direct work,
   record files changed, commands run, and concerns in the same shape.
3. **Spec review** (conditional, `spec-review-prompt.md`, **before merge**) — only when the review
   policy calls for it (RISKY task with downstream dependents): review the task branch's diff before
   the merge-gate, so a deviation never lands on the base.
4. **Land + verify** — confirm the commit on the base (`git log`, diff touches declared targets;
   no-file-diff: commit message + captured external evidence). RISKY worktree: merge-gate into the
   base. Then run **regen barriers** and **deferred wiring** if applicable, committed on the base.
   No integration gate — the self-checks on the cumulative base are sufficient for a single-task
   wave. → next wave.

**Parallel wave** (multiple tasks — worktree isolation required):

0. **Worktree pool** (first parallel wave only) — if the graph has multiple parallel waves,
   pre-create `max(wave sizes)` worktrees once **under `.dryforge/worktrees/`**; recycle between waves
   instead of remove+recreate (see `orchestration.md`). For a single parallel wave, create on demand.
1. **Create task worktrees** — serially (avoid `.git/config.lock` contention), **under
   `.dryforge/worktrees/<task-id>`** (inside the gitignored `.dryforge/`, so they never sprawl into
   the project tree or get tracked), each branched off the base (or reset a pooled worktree to the
   current base tip). **If the project has an installable dependency tree**, install or share it
   (sharing guidance in `orchestration.md`).
2. **Dispatch implementers** — one subagent per task, in parallel, ≤8 at a time
   (`implementer-prompt.md`): right-sized verification, shared-write constraints, pinned worktree
   path. Dispatch every implementer and reviewer as a **general-purpose** subagent (full
   read/edit/run tools — never a plan-only or search-only agent type: an implementer must edit and
   run, a reviewer must read and cross-check).
3. **Collect** — each returns a structured summary.
4. **Spec review** (conditional, **before merge**) — only when the review policy calls for it.
5. **Merge serially** into the base. **Merge-gate per task (objective, not existence-only):** the task
   branch is strictly **ahead** of the base (`git rev-list base..task` non-empty) AND its diff is
   non-empty and touches declared targets — checked with three-dot diff (`git diff base...task`).
   The **merge commit message must satisfy the project's commit-msg hooks**. Then run **regen
   barriers**, then **deferred wiring** (check-before-append, idempotent; conflicts → escalate) and
   **commit wiring on the base**.
6. **Integration gate** — run the project's verify commands on the merged result **after** wiring is
   committed; **green = exit 0, output captured**. This catches cross-task interactions that no single
   implementer could see. Failure → analyze → fix-dispatch or escalate.
7. **Clean up or recycle** task worktrees. If a later parallel wave exists, **recycle** pooled
   worktrees (`git checkout <base-tip> && git reset --hard`) instead of removing. If no later
   parallel wave needs them, **defer cleanup** to after the completion gate — batch-remove all
   worktrees at once. Only remove after asserting each task's commit is an ancestor of the base
   (`git merge-base --is-ancestor`); if not, **do not remove** — escalate. Prefer safe `git worktree
   remove` (no `--force`). Remove dependency-share symlinks first (slash-less `<dir>` pattern).
   Delete merged task branches (`git branch -d`). A failed task's worktree and branch are preserved
   for diagnosis. After the final batch-remove, also delete the now-empty `.dryforge/worktrees/`
   directory and any task temp dirs — `.dryforge/` should hold only the active 3-doc, `NNN/` archives,
   `status.json`, and `backup/` (no litter). → next wave.

**After all waves:**

8. **Completion gate** — the full verify set on the base. **SHA reuse rule:** if the last parallel
   wave's integration gate passed, **ran the full verify set** (not the affected-only subset), AND the
   base tip SHA has not changed since that gate (no lightweight fix, no wiring, no regen committed
   after it), the completion gate is satisfied by the prior gate's captured result — do not re-run.
   If any commit landed after the last gate, **or that gate was affected-only**, re-run the full verify set.

9. **Harness create / update** (`references/harness-lifecycle.md` + `references/harness-format.md`,
   force-load). After the completion gate, before the final review: **re-read the 3-doc** (mandatory —
   the session is now code-biased), then act on the local marker `.dryforge/status.json`:
   - **First cycle** (marker absent): create the whole harness — CLAUDE.md / AGENTS.md + `docs/` +
     module AGENTS.md — from the handoff's Project Foundation + spec + code. The Foundation is a
     **first-cycle invariant** (`ready` always writes it); if a first-cycle handoff has **no
     Foundation section**, do **not** guess one from spec + code — **stop and ask the user to
     regenerate the 3-doc via `ready`** (`harness-lifecycle.md`, fail-fast precondition). Back up +
     critically rework any existing CLAUDE.md / AGENTS.md with user approval.
   - **Delta** (marker present): update only the changed-scope `docs/` (read all current docs first;
     escalate an in-scope conflict; new module → new AGENTS.md + navigation-tree update).
   See `harness-lifecycle.md` for the marker rule and the clobber safety guard.
   **Write every file silently** — do not announce each file or section as you go ("Now the docs...",
   "이제 모듈 노트를...", "Now the module roadmap note in `X`"); the UI already shows each write. This
   multi-file writing sequence is the last place narration leaks — emit nothing between writes.

10. **Final review** — one subagent checks the **full diff on the base** for spec conformance + code
    quality, **and the harness** (when created/updated this cycle) against `references/harness-review.md`
    (`reviewer-prompt.md`, four lenses). **Clear = zero blocking findings, recorded.**

11. **Fix if needed** — lightweight fix path for trivial advisories (MUST triage); fix-dispatch
    substantive findings. Fixes may touch **code or harness**. Re-run per `harness-lifecycle.md`:
    code changed → re-run completion gate; harness changed → re-run harness review; both → both. A
    finding about a doc/code mismatch **outside this cycle's change scope** is not fixed here — record
    it in `docs/tracking/findings.md` and defer (scope-limited delta).

12. **User gate.** Present for approval. **First cycle:** present the code result **and** the harness
    as a reconciliation against the decisions the user took part in — *"the [X] we agreed is
    recorded in the harness as [this]"* — **not** a raw document dump. **Later cycle:** include a
    harness-change summary in the result report.

13. **Archive (move) + mark.** On approval, **move** the active 3-doc into `.dryforge/NNN/` — copy
    `.dryforge/{handoff,spec,plan}.md` into the new highest+1 dir, **then delete them from the
    `.dryforge/` root** (archiving is a move, not a copy — leave no stale active 3-doc at root). Write
    `.dryforge/status.json` (`{ "initialized": true }`) if absent — the local marker that makes the
    next cycle a delta.

**Advancing waves.** Sequential waves advance immediately after commit verification — no gate to
wait for. For parallel waves, the next wave's provisioning SHOULD overlap the current wave's
integration gate (`orchestration.md`, Advancing waves), but dispatch waits for a green gate.
Fall back to fully serial advance if uncertain.

Mechanics, subagent dispatch constraints, status protocol, context budget, and failure handling live in
`references/orchestration.md`.

## Completion gate (avoid self-judgment A=A)

Done only when ALL hold — on **evidence**, not assertion:
- every wave merged; every spec requirement traced to a merged task; zero open
  `BLOCKED` / needs-fix. **"Zero open BLOCKED" is not "counted as done"** — each BLOCKED task must have
  **completed escalation to the user** (the user has been told and has resolved its disposition) with
  its **worktree preserved** for diagnosis; a BLOCKED task may never be silently tallied into "done".
- every `DONE_WITH_CONCERNS` concern **resolved (fix-dispatched) or explicitly accepted and
  recorded** (at code-review or by the user) — a flagged concern is never silently carried into
  "done".
- a **final full check** — **all** of the project's verify commands (whatever the stack actually has
  — e.g. typecheck / lint / test / build, or fewer; including any genuinely expensive end-only step
  deferred from the per-wave gate) on the integrated base **exit 0, with the commands and
  exit codes captured and shown** (not "looks green"). **Why re-run everything when each wave already
  passed:** a per-wave gate proves each wave green *in isolation*, but the integrated result can break
  on **cross-wave interactions** that no single wave's gate could see — so the completion gate re-runs
  the full verify set against the whole base as the final, all-together check. Running the
  full verify set every wave is the **safe baseline**; narrowing to an **affected-only** subset is an
  optional efficiency lever for **intermediate (per-wave) gates only** — never for the completion
  gate. Affected-only is permitted when the project's test runner supports change-based filtering
  (e.g. the test runner's change-based filter — `--changed`, `--since`, `--lf`, or equivalent). When
  using
  affected-only, record what was skipped so the completion gate's full run covers it. The
  **completion gate always runs the full verify set** — it is the cross-wave safety net.
- **runtime smoke** — **in addition to** the verify commands above (which prove the code compiles
  and tests pass): when the spec declares a running server or service, start it, send one
  health-check or minimal request, confirm a 2xx response, then stop. A green build proves the
  code compiles; a runtime smoke proves it boots and responds. Skip only when the project has no
  runnable server component.
- **An unevaluable check is a fail, not a pass.** A verify or smoke command counts as green only when
  its **assertion itself evaluated and reported success** — exit 0 *from the assertion*, or the
  expected output actually observed. If the assertion could not run (the command errored before
  asserting, the server never came up, the matched output was empty, the response couldn't be parsed),
  that is a **failure** — diagnose it, fix the check (or the code), and re-run until the assertion
  genuinely passes. **Never infer a pass from side-effects** ("the server logged the request", "a file
  appeared", "no error printed") when the declared assertion did not itself succeed; a check you can't
  evaluate is not evidence. (This is A=A self-judgment applied to the gate's own evidence — see header.)
- no residual escalation outstanding — every task that returned `NEEDS_CONTEXT` / `BLOCKED` was
  resolved through the bounded escalation ladder, and any escalation that **reached the user** was
  **synchronous** (the orchestrator pauses the run and waits for the user's
  response — never a silent hang or a timeout-drop). Subagents themselves never ask the user directly
  (the prompt files carry that fresh-session rule); only the orchestrator relays escalations to the user.

## Finish

After the harness step, final review, user approval, and 3-doc archiving (steps 9–13 above):

- **Greenfield (base = main) →** work is already on main. Notify the user that the project is
  complete on main. No merge needed.
- **Existing project (base = feature branch) →** ask the user **how to integrate**:
  - **Merge to main →** fetch and confirm main has not moved (if it has, re-integrate / escalate);
    merge the feature branch with **`--no-ff`** **from a checkout on the main branch**. **On
    conflict, abort and escalate.** After confirming the merge, clean up branches.
  - **Open a PR / push →** push the feature branch; leave integration to the project's review flow.
  - **Hand off only →** keep the feature branch intact.
  Never integrate on your own.
