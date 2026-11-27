# Engineering Standard — All Depths

Start at a real caller and follow a representative input to its result and side
effects. Use the repository's domain names and conventions. Include units or
state in names when callers could confuse them. Keep the normal path easy to
trace. A guard clause can make the order of validation, work and cleanup
visible. Explain an invariant or a surprising trade-off where it matters.

Before extracting shared code, compare what its callers accept, return, mutate
and raise. Put a shared rule with the code that owns it. Keep similar-looking
operations separate when their ordering, failure behavior or reasons to change
differ. Use existing code, native or standard-library facilities, then installed
dependencies. Introduce an interface when a concrete caller needs the boundary.

## Dependency versions

Start with the latest stable release of each direct dependency the change adds,
updates or builds on, including development tools and compilers. Check the
project's configured package registry or upstream release metadata when making
the choice. Record the source, version and date checked in the existing plan or
review. Read the upstream migration notes for breaking changes between the
installed and proposed versions. A documented minimum is a compatibility floor.
Keep it if the public API still supports it, and test that floor when affected.

Check runtime support, peer ranges and the APIs used by callers. Prefer the
newest compatible stable version. If a supported runtime, peer, reproducible bug
or explicit pin excludes a newer release, name the constraint, the chosen
version and what would allow the upgrade. Use a prerelease only by explicit
opt-in. When upstream is unavailable, identify the cached evidence and mark
current freshness unverified.

Use the repository's package manager, manifest conventions and lockfile policy.
Resolve the scoped change, review the lockfile diff, and verify the actual
installed version with the affected build or tests. Keep unrelated updates out
of the diff. A floating tag or a successful install alone cannot establish which
API the code exercised.

For example, suppose a build uses `example-linter`. In this fixture, the
registry lists 3.2.0 as stable, requiring Node 22, and 4.0.0-rc.1 as a preview.
The project's supported Node 20 runtime makes 2.9.1 its newest compatible stable
release. If the project's minimum rises to Node 22, evaluate the 3.x migration
and run the lint fixtures with 3.2.0. For an npm v3 lockfile, run this read-only
Node probe at the project root to compare the declared range, locked selection
and installed copy.

```javascript
const name = 'example-linter';
const declared = require('./package.json').devDependencies[name];
const locked = require('./package-lock.json').packages[`node_modules/${name}`].version;
const installed = require(`./node_modules/${name}/package.json`).version;
console.log(JSON.stringify({declared, locked, installed}));
```

Seeing `^2.3.0`, `2.9.1` and `2.5.0` means a passing local lint run exercised
2.5.0. Restore the locked install and rerun the build before reporting 2.9.1.

## Behavior and compatibility

Address encountered bad code, mixed responsibilities, and oversized modules in
the task's execution path. Fix shared causes once. Plan substantive cleanup with
the feature; implement it without extra permission when already authorized. If
additional files are needed, update ownership/contracts and serialize overlapping
work before editing. Do not hide necessary repairs behind an obsolete file fence
or refactor unrelated systems. Planning-only requests still stop before coding.
If extending encountered duplication, characterize uncertain behavior first,
then repair the shared cause. Weak coverage calls for characterization, not
another copy. Defer only for a concrete scope or compatibility constraint,
explained in the existing review. Cache removal is housekeeping, not code cleanup.

Preserve observable behavior and safety invariants. Identify the affected caller
observation, its original result and the intended difference. Derive preservation
checks from unchanged source and callers; keep intentional changes in separate
red/green tests. Reuse adequate coverage. When it cannot distinguish a plausible
broken implementation, add a focused characterization test. For an uncertain,
high-risk check, demonstrate that it rejects the suspected mistake in an isolated
scratch copy; never mutate user work or weaken checks to manufacture evidence.

Choose only probes needed for changed or uncertain contracts:
- **Resources:** in an isolated fixture, fail an operation after allocation and
  before handoff; verify cleanup, complete relevant state and the original error.
  Replacing an entire helper can miss failures inside it.
- **Calls:** observe callback receiver/arguments, call order and input consumption;
  a test double must expose the behavior being preserved.
- **Boundaries:** compare full relevant metadata and inputs accepted by the
  original. Reusing the implementation's mask or conversion in an assertion can
  conceal the same bug.

For meaningful mutable refactors, use the shared [compatibility checks](compatibility.md)
to capture a passing baseline and replay unchanged checks; record provenance
honestly. When full public compatibility is promised, enumerate names/signatures,
including re-exported types/dependencies, and keep baseline assertions passing
through the move. A plan, facade or `__all__` cannot narrow that promise; internal
non-use does not prove external non-use. Prefer public outcomes to private
structure or cosmetic choices. Run targeted checks before/after meaningful changes
and one full suite at final integration; record deviations and actual results.

## Performance where it matters

When cost could affect a caller, identify the workload and limiting resource.
Follow the data through loops and across file, database and network boundaries.
Check for repeated reads, round trips, unnecessary copies and unbounded retained
state. Choose an algorithm and data structure that suit expected input size,
ordering and memory use. Bound the lifetime of a cache by the validity of its
inputs. Consider cancellation, duplicate work and stale results where callers
can overlap or retry.

For an optimization, compare the same representative input and conditions before
and after. Count operations when the claim is fewer reads or calls. Measure
elapsed time for a latency claim and peak memory for a memory claim. Keep the
caller-level check alongside that measurement. If execution is unavailable,
describe the expected complexity and the measurement still needed. Routine
changes can use their existing correctness checks.

The [worked lookup example](lookup-example.md) pairs a read count with checks
for output order, empty values, the first failure and cache lifetime.

Before PR delivery, use the existing review to inspect the diff and relevant
callers for introduced or encountered clutter. Fix justified local problems and
refresh affected checks before the final integration result. Record unrelated
debt without expanding the PR indefinitely. An explicitly requested repository
cleanup uses [Cleanup](../../zagrosi-cleanup/SKILL.md).

## Useful simplification

- **Earn a helper.** Replace an internal `_label(prefix, name)` used once only to
  return `f"{prefix}: {name}"` with that expression. Extract repeated amount
  parsing into `parse_amount` when it owns a shared validation rule. Preserve
  public entrypoints, conversion/error order, and single-use iterators.
- **Split responsibilities.** For an import godfile that parses CSV, validates
  amounts, calculates totals, and writes reports, keep the public entrypoint as
  a short composition of parsing, calculation, and output. Reuse existing module
  boundaries; move cohesive behavior with its tests. Renaming a 300-line method
  or distributing arbitrary chunks among new classes does not simplify it.
- **Keep dependencies direct.** Let stateful workflows call pure calculation;
  don't make a calculation construct the workflow to call back into itself.
  Remove such reverse dependencies instead of hiding cycles with delayed imports.

During the existing review, identify the concrete gain: less repeated policy,
fewer concepts to follow, clearer responsibilities, or easier changes. Reject
code golf and unnecessary layers even when line counts improve. Use before/after
regressions for public results, errors, ordering, side effects, and callers that
the cleanup could affect; avoid a new review artifact just to state this.
