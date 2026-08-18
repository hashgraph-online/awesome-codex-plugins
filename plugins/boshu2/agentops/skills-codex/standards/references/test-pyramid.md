# Risk-Based Test Portfolio

Choose the smallest test surface that can disprove the behavior claim. Test
levels are tools, not mandatory ceremony: the right mix follows risk,
boundaries, and failure modes.

## Levels

| Level | Scope | Best for |
|---|---|---|
| L0 contract | schemas, registrations, imports, generated parity | structural promises and compatibility |
| L1 unit | one function or module | dense logic, edge cases, fast regression guards |
| L2 integration | collaborating modules or an I/O boundary | interface mismatches and adapter behavior |
| L3 component/E2E | a user-visible path through a subsystem | workflows and high-blast-radius behavior |
| smoke/production | a deployed critical path | environment, packaging, and rollout facts |

Higher is not automatically better. A pure parser fix may need one table-driven
unit test. A CLI command crossing config, filesystem, and formatting boundaries
may need an integration test. A deployment claim cannot be proven by a local
unit test.

## Selection questions

Start from the acceptance behavior and ask:

1. What is the narrowest observable that fails when the behavior is wrong?
2. Which boundary is most likely to hide a defect?
3. Which regression would be expensive or dangerous?
4. Can the check run quickly and deterministically during implementation?
5. What remains impossible to check in this environment?

Add test levels only when each one covers a distinct risk. Do not require L2 by
default, duplicate the same assertion at every level, or treat test count as
evidence quality.

## Operating-loop use

- **Plan** names the active behavior, edge scenario, required evidence, and
  first acceptance check.
- **Implement** records the first check failing for the right reason, makes the
  smallest change that turns it green, and refactors without changing the
  behavior.
- **Validate** examines the exact candidate, judges whether the evidence is
  sufficient for each acceptance criterion, and records checked and unchecked
  scope.

Premortem, Council, Postmortem, and test specialists are optional strategies.
They do not add lifecycle phases or authorize continuation.

## Regression design

When fixing a bug, preserve a test that:

- reproduces the observed failure before the fix;
- asserts the externally relevant result, not incidental implementation;
- includes the edge that made the defect reachable;
- fails if the old behavior returns.

Prefer realistic fixtures at the boundary under test. Mocks are useful for
specific failure injection, but a mock that reimplements the expected behavior
can make the test prove itself instead of the system.

Use property, fuzz, mutation, golden, chaos, performance, or compatibility
tests when the risk calls for them:

- property or fuzz tests for parsers and broad input spaces;
- mutation testing for critical logic whose coverage may be shallow;
- golden tests for stable generated or formatted output;
- fault injection for timeout, permission, corruption, and dependency errors;
- performance tests for a named latency or throughput contract;
- compatibility fixtures for public data or command formats.

These are targeted tools, not a required checklist for every change.

## Throughput

Keep feedback proportional to the current surface:

1. Run the first acceptance check while shaping the change.
2. Run focused package or adapter checks after the bounded implementation.
3. Run the full deterministic repository suite once on the frozen complete
   candidate.

Use one machine-readable invocation when it provides both timing and failure
details. Before repairing a newly observed failure, establish whether it is
introduced by the candidate; pre-existing failures belong in unchecked or
residual evidence unless the caller expands scope.

Parallelize read-only tests only when they do not contend for shared state.
Isolate tests that touch tmux, ports, environment variables, global config, or
the filesystem so they cannot damage a parent session.

## Evidence quality

Good test evidence records:

- exact command or artifact path;
- subject identity or changed surface;
- exit status and relevant result;
- environment assumptions that affect reproducibility;
- what the check did not cover.

Green tests are factual evidence, not a semantic verdict. Validate supplies the
independent judgment against the exact candidate.
