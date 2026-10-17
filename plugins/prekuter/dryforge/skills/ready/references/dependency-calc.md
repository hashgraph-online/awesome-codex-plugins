# dependency-calc.md — the Execution Graph

The **last** step of PLAN: after the spec is frozen and the plan prose is written, compute the
machine-readable scheduling skeleton. The schema is in `output-format.md`; this file is *how*
to fill it. Compute it once here — go follows it and never re-judges dependencies.

## Scaffold is not a task

Project initialization (manifests, dependencies, directory layout, build config, entry points) is
**not a plan task**. `go` performs scaffold inline before dispatching implementers. Do not create a
scaffold task in the Execution Graph. Exception: if scaffold itself is large enough to warrant a
dedicated agent (complex infra, containers, CI pipelines — work that requires investigation or
trial-and-error), it may appear as a task, but this is rare.

## Encode two things; leave the rest

The graph encodes only:

- **`depends`** — per task, the task ids that must finish first. The only encoded judgment.
- **`regen_barriers`** — cross-cutting steps between waves (`after: [ids]`, `run: "<cmd>"`).

Do **not** encode produces / consumes / shared_write / waves:
- produces/consumes are the *reasoning you use to derive `depends`*, not graph fields.
- **waves** are derived by go (topological sort of `depends`, then ≤8-concurrent batches).
- **shared_write** is a prose hint (below), with a runtime safety net.

## Deriving `depends`

For each task ask: does it **consume** something another task **produces** — a file, an
exported symbol, a type, a schema, a migration? If so, it depends on that task.

- **Complete *and* minimal** — go topologically sorts `depends` into waves, so
  accuracy cuts both ways:
  - **Miss a real edge** → a consumer runs before its producer exists → it breaks at
    integration (the classic "merge, then a wall of type errors").
  - **Add a spurious edge** → work that could run in parallel gets serialized → lost parallelism.
- Encode every genuine producer→consumer need and nothing else. Tasks with no real edge share a
  wave (run in parallel).

**Beyond artifact consumption.** Are any tasks ordered by runtime **sequence**, environment setup,
or external-state initialization rather than artifact consumption? If so, declare an explicit
`depends` even with no file consumed. And for **external shared state** — tasks writing a DB, a
registry, a queue, or remote config with no local file collision — declare a serialization point (a
writer task the others `depends` on) when the parallel writes are **not** idempotent/commutative;
otherwise record the safe-parallel assumption in the handoff. ORIENT surfaces these project-specific
constraints.

## Task risk tier (optional)

Per task, optionally classify the behavioral risk. It sizes the implementer's **per-task test
ceremony** and, for a single-task wave, go's execution mode; it does not set review topology. The
field shape is `risk: RISKY | MECHANICAL | NONE`. It is **optional**. If omitted, the task is
unclassified: go leans toward stronger verification, and the implementer still judges test ceremony
at build time (no break). When present it is visible in the 3-doc the user reviews before go runs.

Derivation heuristic (a **floor, not a checklist** — judged per task):

- **RISKY** if the behavioral contract names an explicit edge case, invariant, state-coordination,
  or validation rule.
- **NONE** if the target is config / schema / docs / pure scaffold with no behavioral surface.
- **MECHANICAL** otherwise.

This sizes the implementer's per-task test ceremony — it never changes whether code is
verified or reviewed, and never touches gate topology. (go may also read the tier to choose a
single-task wave's execution mode — a consumer-side use; the producer only derives and emits it.)

## regen barriers

A step that must run **between** waves because one task changes an input others regenerate
from: schema → client/type generation, contract → codegen, message-catalog rebuilds, etc.
Encode `{ after: [ids], run: "<command>" }`. **The command is discovered while reading the
project** — never hardcode a stack's regen command. Note for the executor: if the regen *output* is
consumed by a later task, it must be **committed** to the base (and not gitignored), or it
won't reach the fresh worktree of a downstream wave — same propagation rule as the deferred-wiring
commit.

## shared-write (prose hint, not graph)

When several tasks would write the **same** file (an aggregator/index file, a module registry/list,
a routes table, any registration point), prevent collision with a **single deferred writer**:

- In the plan prose, tell each feature task *not* to touch the shared file, and add one wiring
  step at the **end of the wave** that appends all registrations.
- This is best-effort. go still backstops it at runtime (changed-file overlap
  detection + merge-conflict). A missed hint becomes a *handled conflict*, not corruption.
- **Package/namespace markers count too.** In a *new* package or namespace, a marker file the
  ecosystem requires every module to sit under — a package/module declaration file, or an
  aggregator/index created from scratch — is needed by **every** parallel task, so it is an implicit
  shared-write: if each task creates it, they collide. Assign it to the **scaffold step** (go's
  inline setup, so it exists before the parallel wave) — don't leave each feature task to create it. (Identical empty
  markers happen to merge cleanly, but differing ones conflict — don't rely on the accident. What
  the marker is and whether the stack needs one is discovered from the project, never assumed.)

## When uncertain, escalate

If you can't confidently determine a dependency, a regen command, or whether a file is
shared-written, **ask the user — don't guess.** A wrong edge breaks waves or kills parallelism;
a guessed regen command breaks the build. (escalate-don't-guess.)

## Method fixed, specifics discovered

The *method* (produces/consumes → `depends`; mark regen points; defer shared writes) is
stack-agnostic and fixed. *What* is a regen barrier or a shared/registration file is
discovered per project while reading the code — never assumed.
