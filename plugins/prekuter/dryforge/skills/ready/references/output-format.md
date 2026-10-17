# output-format.md — the 3-doc contract

Defines what **`ready`** (the producer) outputs and **`go` consumes**. This is the contract between
`ready` and `go`.

**Core principle:** exactly ONE part is a rigid, machine-parsed schema — the
Execution Graph. The three documents' bodies are *content requirements*: the agent
designs the structure per project (intent fixed, structure flexible). All content is
stack-agnostic — project specifics are discovered while reading the project, never hardcoded.

## The three documents (handoff governs)

### handoff — governing doc + intent injection
Must convey (structure is the agent's to design — 3 hard gates or 30):
- **Document Roles** table + conflict resolution: spec defines *behavior*; plan defines
  *order and work targets*.
- File locations (as project-root-relative paths, e.g. `.dryforge/spec.md` — never
  machine-absolute, so the 3-doc stays portable and survives archiving) + the big
  picture (execution shape).
- **Hard gates**: non-negotiable constraints the executing agent cannot derive from code alone.
- Intent decided while authoring but not captured in spec/plan.
- **First cycle only (no project harness yet):** the handoff **carries** a **Project Foundation**
  section — the project-wide foundation (full domain model, technical decisions, future scope) that
  seeds the harness `go` creates at the end. `ready` produces it through its first-cycle ELICIT loop
  and writes it at the SPEC step (`foundation-format.md`). It is **required** in a first cycle — there
  is no degrade path; `go` treats a missing Foundation in a first cycle as a precondition violation and
  stops (`foundation-format.md`, "First-cycle precondition"). Omit it in later cycles (the harness has
  taken over the project-context role).

### spec — what to build (ground truth)
Must convey: objective + motivation; product behavior; key design rationale / thinking-base
(decision + why, where not code-derivable — see below); domain decisions/invariants; scope
boundaries; API surface; edge cases as explicit rules; required verification.
spec is ground truth — on conflict spec wins; spec errors are fixed only with user
approval.

**The spec transcribes the settled decision surface — it does not make or defer decisions.** ELICIT
already settled every load-bearing decision, *including the contract* (`elicitation.md`'s CONTRACT
lens: data-model fields and their constraints, the exact status/enum value **sets**, uniqueness/
identity rules, output keys, whether two conceptually distinct fields were collapsed into one). Pin
each of those **here, the first time — as precisely as if no downstream gate existed.** Do **not** ship
a half-pinned contract for the 3-doc-gate to tighten over rounds: a gate catching a precision gap is an
*upstream failure*, not the gate's job, and leaning on it is the reward-hack
`elicitation.md` forbids. (A genuine tuning default with no user preference is *pinned* as a default
**marked tunable** — which is settling it, not deferring it.)

**The spec is pure content — no provenance/attribution tags.** Every load-bearing decision appears as
a settled rule, written from understanding the user's intent (`elicitation.md`). Do **not** annotate
decisions with who-decided markers (`[user-decided]` / `[agent-default]`) or target/context labels —
those are internal tokens, they clutter the user-facing document, and the artifact does not need them.
That a decision is the user's intent (not an agent guess) is ensured *upstream* — by ELICIT's
"no-guess-survives" exit and the independent intent-completeness check (`intent-completeness.md`) — not
by a tag in the doc. The only annotation a decision carries is its **reason in the thinking-base** when
non-derivable (below), written in the user's terms as prose.

### plan — what to do (tasks + the machine graph)
Must convey: per-task **behavioral contract** (goal, **work targets** — files |
state | external resource — and verification gate); **thinking-base** (decision +
reason where not code-derivable); shared-write guidance (prose, below); a phase
narrative for humans; and the **Execution Graph** (below). The verification gate
matches the deliverable type: a file diff for code, captured external evidence for
state/operational work. Target shape and gate are discovered from the project, not
assumed.

## The Execution Graph — the only rigid part

A fenced `yaml` block inside the plan. go parses it for scheduling:

```yaml
tasks:
  - id: T5
    depends: [T2, T3]      # task ids that must finish first
    risk: RISKY            # OPTIONAL: RISKY | MECHANICAL | NONE
regen_barriers:
  - { after: [T3], run: "<regen step — discovered while reading the project>" }
```

- `depends` is the **only encoded judgment** (which task needs which). the producer
  computes it; go follows.
- `risk: RISKY | MECHANICAL | NONE` is an **optional** per-task atom alongside `depends`.
  It sizes the implementer's per-task test ceremony — it never changes whether code is
  verified or reviewed, and never touches gate topology. (go may also read it to choose a single-task
  wave's execution mode, but that is a consumer-side use; the producer just derives the tier.) Derive
  it per task (see
  `references/dependency-calc.md`): RISKY if the behavioral contract names an explicit edge case,
  invariant, state-coordination, or validation rule; NONE if the target is config / schema / docs /
  pure scaffold with no behavioral surface; otherwise MECHANICAL. This is a derivation heuristic
  judged per task, not a fixed checklist. If a producer omits it, the task is unclassified: go leans
  toward stronger verification, and the implementer still judges test ceremony at build time — no
  break.
- go derives waves by topological sort of `depends`, then dispatches in
  batches of **≤8 concurrent**.
- `regen_barriers` = cross-cutting steps between waves (timing: after task X). The
  command is discovered per project while reading the code, not hardcoded.
- Do **not** encode produces / consumes / shared_write / waves here — they are prose,
  runtime-derived (git diff), or computed.
- `id`s match the prose plan; the graph is the scheduling skeleton only.

## Shared-write handling — two layers (hint + safety net)

Parallel tasks must not collide on shared/registration files (an aggregator/index file, a module
list, a routes table, ...). Two layers, not a strict prediction:

1. **Hint** (prose in plan, best-effort, may be incomplete): per task, e.g. *"Do not
   write the shared registration files; a single wiring step adds all registrations at
   the end of the wave."* Proactively avoids known collisions. Not authoritative.
2. **Guarantee** (runtime, go): before merging a wave, detect changed-file
   overlaps across task branches (`git diff`). Declared-shared files are already
   deferred; an **undeclared** overlap degrades safely (serialize / ad-hoc defer /
   escalate); a git merge conflict is the final backstop. A missed hint becomes a
   *handled conflict*, never silent corruption.

## Authoring rules (for the prose bodies)
- **Match the user's language (language-agnostic)**: author the three docs in the language the user
  communicates in, natively — discovered at runtime, never assumed, exactly like stack specifics. Not
  translationese; the language this contract is written in does not constrain the 3-doc.
- Replace premature implementation code with **behavioral contracts** (goal,
  invariants, what-to-test — not how).
- **Stack-agnostic**: no project-specific assumption as a rule; specifics (build
  targets, regen commands, conventions) are discovered from the project.
- The three docs' section layout is the agent's to design; only the content above is
  required.

## thinking-base (decision + reason) — the derivability test

Record a reason only where a fresh agent, reading the project code, could **not** reach the
designer's decision on its own. Test in order:

1. **Derivable from code?** → **Yes**: no reason needed (the code says it).
2. **Unsure if it's derivable?** → include it (gray-zone default: an over-included reason is cheap; a
   missing one derails the executing agent).
3. **Not derivable (a reason is needed)** → is it **actually on the record** — settled in the
   dialogue / material?
   - **Yes** → record *decision + reason*.
   - **No — you'd have to invent it** → **do NOT write a reason. Ask the user.** A fabricated reason is
     worse than none: it sends the executing agent confidently the wrong way. (Never attribute a
     reason to something that was not actually decided.)

**Tuning values are recorded as defaults, not grounded decisions.** A configurable value within an
already-settled mechanism that is a *conventional default* or is *tuned later by feel* — one the user
has no preference on — is a tuning value, *not* a user-grounded decision (`elicitation.md`, "exit bar
item 2"). Record a sensible default and **mark it tunable**, so the executor knows it is adjustable,
not a hard requirement. This is **not** a thinking-base reason (it is derivable / a default), and it
must **not** be forced through the user — that is over-asking. The *mechanism* it sits in is
the load-bearing decision; the *value* is the tunable. (Mechanism vs tuning value is judged per
project, never a fixed list.)

Frequent categories (accelerators for spotting candidates, **not** an exhaustive list): trade-off /
external constraint / scope boundary / convention exception / domain invariant / non-functional (a
chosen quality attribute: security posture, consistency level, perf budget) / rejected alternative (an
option the designer considered and discarded — record it, and why, so a downstream agent doesn't
"improve" the design back into the rejected choice).

## A complete worked example

See `references/example-3doc.md` for one full `handoff` + `spec` + `plan` (an idempotent-submission
feature) — read it once to anchor the shape and altitude. It is **illustrative, not a template**:
its role names are deliberately generic because a real 3-doc is stack-agnostic and written against
the project discovered at runtime. Copy the structure, not the words.
