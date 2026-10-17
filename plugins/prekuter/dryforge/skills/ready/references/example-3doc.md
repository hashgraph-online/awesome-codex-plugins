# example-3doc.md — one complete, illustrative 3-doc

A worked example so the shape of a real `handoff` + `spec` + `plan` is concrete, not just
described. **It is illustrative, not a template to copy literally.** The role names below
("submission endpoint", "request store", "dedup worker") are generic on purpose — a real 3-doc is
**stack-agnostic**, written against whatever the project actually uses, discovered at runtime. The
**domain is incidental too**: this happens to be an application feature, but the *identical* 3-doc
shape (spec = behavior, plan = tasks + Execution Graph, a deferred wiring step) applies to any
deliverable — an infrastructure change, a documentation set, a data pipeline, a one-off script —
only the *content* of the behavioral contracts changes, never the structure. Copy the *structure and
altitude*, not the words or the domain. (Only the Execution Graph is a rigid schema; the prose
layout is the author's to design — see `output-format.md`.) The example is **delta-shaped**: its
handoff carries no Project Foundation section — in a first cycle the handoff additionally carries
the Foundation (`output-format.md`), so do not anchor on this example for that section's absence.

The example feature: **idempotent task submission** — clients may retry a submit; the same logical
request must never be processed twice.

---

## handoff.md (governing doc)

**Document roles.** `spec.md` = behavior (ground truth; on conflict, spec wins; spec errors fixed
only with user approval). `plan.md` = task order + file targets (provisional; revise freely).
Existing code = HOW reference, never the authority for WHAT.

**File locations** (project-root-relative): `.dryforge/spec.md`, `.dryforge/plan.md`,
`.dryforge/handoff.md`.

**Execution shape.** One feature; 4 tasks; 2 waves. Wave 1: store + dedup key (parallel). Wave 2:
endpoint + worker (parallel), then a single wiring step registers both.

**Hard gates** (not derivable from code alone):
- A retried submission with the same client-supplied idempotency key MUST return the original
  result, not create a second record.
- Verify gate per task: the project's verify commands (exact commands discovered
  while reading the project) must exit 0.

**Intent captured live (not in spec/plan).** The designer chose key-based dedup over content-hash
dedup because clients already send a stable request id; a content hash would mis-merge two
legitimately-distinct requests that happen to share a body. (Recorded so a downstream agent doesn't
"improve" it back to hashing.)

---

## spec.md (what to build — ground truth)

**Objective.** Make task submission safe to retry: identical re-submits are de-duplicated.

**Behavior**
- A submission carries a client-supplied **idempotency key** (opaque string).
- First submission with a key K: create one request record, process it, store the result against K.
- Any later submission with the same K: return the **stored** result; do not create or process a
  second record — regardless of whether the first is still in flight or already done.

**Invariants (load-bearing)**
- At most one processed record exists per idempotency key. (The dedup contract.)
- A key in flight blocks a duplicate from starting (no double-processing window).

**Edge cases as rules**
- Missing/empty key → reject the submission (do not silently process; that would be undedupable).
- Same key, *different* payload → reject as a conflict (the key is the identity; a changed body is a
  client error, not a new request).

**Assumptions / decisions + rationale**
- Key-based dedup, not content-hash — *rationale in handoff* (stable client request id exists).
- Result storage is durable for at least the retry window; exact backing store discovered from the
  project (not assumed here).

**Required verification.** A retry test: submit K twice (concurrently and sequentially); assert one
record, one processing, identical returned result.

---

## plan.md (what to do — tasks + the machine graph)

**T1 — request store.** Behavioral contract: persist a request keyed by idempotency key, with a
status (in-flight / done) and a result slot; expose "get-or-create by key" with atomic
first-writer-wins semantics. File targets: the project's data/store layer. Verify: store unit tests
green. *Do not* touch the shared registration file.

**T2 — dedup key validation.** Behavioral contract: validate the idempotency key (present,
non-empty) and the same-key/different-payload conflict rule. File targets: the request-validation
layer. Verify: validation unit tests green. *Do not* touch the shared registration file.

**T3 — submission endpoint.** Behavioral contract: accept a submission, run validation (T2), then
get-or-create in the store (T1); on an existing done record return the stored result, on in-flight
return the agreed in-flight response. File targets: the endpoint/handler layer. Verify: endpoint
tests green. *Do not* register the route — the wiring step does.

**T4 — dedup worker.** Behavioral contract: process an in-flight request exactly once and write its
result + flip status to done, so a concurrent duplicate observes done. File targets: the
worker/processing layer. Verify: worker tests green incl. the "second submit sees done" case. *Do
not* touch the shared registration file.

**Wiring (single deferred writer — NOT a graph task).** Register the endpoint route and the worker
in the shared registration file(s), idempotently (check-before-append). This runs at the end of
wave 2 as the **orchestrator's** per-wave wiring step, so it is deliberately **absent from the
Execution Graph below** — shared-write wiring is a prose step, never a `depends`-bearing node (see
`dependency-calc.md`, "shared-write (prose hint, not graph)"). Encoding it as a task would make `go`
dispatch it as an implementer and spec-review it like feature code.

**Phase narrative (for humans).** Store and validation are independent foundations (wave 1). The
endpoint consumes both; the worker consumes the store. They run in parallel (wave 2), then one
wiring step wires them in.

```yaml
tasks:
  - id: T1
    depends: []
    risk: RISKY        # optional; atomic first-writer-wins is a state-coordination invariant
  - id: T2
    depends: []
    risk: RISKY        # optional; the same-key/different-payload conflict is an explicit edge rule
  - id: T3
    depends: [T1, T2]
  - id: T4
    depends: [T1]
regen_barriers: []
```

(Four graph tasks → two waves: `{T1, T2}` then `{T3, T4}`. The wiring step is **not** here — it is
the orchestrator's per-wave deferred-writer, run after the wave's tasks merge, as noted above.)

(The `risk:` atoms above are **optional** — `RISKY | MECHANICAL | NONE`. They size the implementer's
per-task test ceremony and, for a single-task wave, go's execution mode. Omitting one leaves the
task unclassified: go leans toward stronger verification, and the implementer still judges test
ceremony at build time. Here T1/T2 carry named invariants/edge rules, so they read RISKY; T3/T4 are
left unmarked.)

(No `regen_barriers` here — nothing regenerates from another task's output. If, say, T1 changed a
schema that a client/types step regenerates from, you'd add
`{ after: [T1], run: "<the project's regen command>" }`.)

(**Ordering-only edge — illustration.** Every `depends` above is an *artifact-consumption* edge: T3
consumes T1's store and T2's validation. Some edges are **ordering-only** — task B must run after
task A purely for runtime sequence or external-state init, with **no produced artifact consumed**.
Example: a task that stands up a shared runtime resource (a queue, a connection pool, a migration
slot) and a later task that initializes against it. You'd still write `depends: [T_setup]`, but with
a one-line note that the edge is ordering-only (no file/artifact produced) so a reader doesn't hunt
for a consumed output that isn't there.)
