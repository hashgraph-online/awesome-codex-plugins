# Flaky Triage

Read this when the failure does not reproduce on every run: "fails sometimes", "a different test each time", "passes alone", "only fails in CI". Intermittence is itself evidence. Classify before forming hypotheses, because the classification usually removes most of the search space in one step.

## 1. Capture The Signature

Run a fixed, small set of diagnostic reruns. Each answers one question; journal each run. These are diagnosis runs, not repeated attempts to get a green result.

| Rerun | Question it answers |
|---|---|
| The exact command that just failed, again | Does the same test fail again, or a different one? |
| The failing test alone, filtered to that one test | Does it pass in isolation? |
| The full scope on a quiet machine, with this run's other processes stopped | Does the whole suite go green when nothing else runs? |
| The full scope with a shuffled order or an explicit seed | Does a particular order reproduce it? Record the seed. |

Do not stop the user's concurrent work to make a run quiet. Isolate what this run owns, and record what could not be isolated.

## 2. Classify

| Signature | Classification | Next move |
|---|---|---|
| The same test fails intermittently everywhere, including alone | Real race in the code under test, or an async test bug: a fixed sleep, an unawaited promise, a poll loop | §4 real race; reproduce deterministically by subscribing to the completion event or injecting a clock |
| A different test or file fails each run, each passes alone, and a quiet machine is green | Contention between concurrent runs | §3 checklist, then fix the test infrastructure |
| The same test, only in the full suite, green in isolation | Order dependence or a leaked fixture | §4 order dependence; bisect with the recorded seed |
| Fails only on CI, never locally | Resource ceiling (slower disk or CPU reaching a timeout), different parallelism defaults, container clock, missing service | Reproduce locally under the same constraint; raise the signal, not the sleep |
| Green on a plain rerun of the same commit | Still a flake. Classify it before ignoring it; an unclassified flake is a hidden bug report | Capture a bounded discriminating reproduction |

Write the classification in the journal with the rerun that produced it. If the signature does not match any row, say so and treat it as an open real-race hypothesis rather than forcing a category.

## 3. Contention Checklist

Concurrent runs of the same repository, or one checkout plus a background agent, sharing a global mutable resource is the most common modern cause. Check each item while the failure window is still open:

- **Shared temporary roots** — a cache or sandbox directory derived from a fixed path instead of a per-run unique directory. Both runs read and write the same tree.
- **Fixed ports** — a hardcoded listen port. Two suites race to bind it; the loser gets a connection error in whichever file happened to be running.
- **Global environment or config mutation** — a test writing a dotfile, a shared config, or process-external state that the other run reads.
- **Shared containers or databases** — same container name, same schema, same volume.
- **Caches and locks** — package manager caches, lockfiles, index contention.

Evidence to capture while it is live: the listener on the port, a listing of the shared temporary path, a process list showing the concurrent runners.

## 4. Fix Policy By Classification

- **Contention** → fix the test infrastructure, not the individual test. Namespace every suite-global resource per run: a unique temporary directory, an ephemeral port, a unique container name. The bar is that two checkouts of this repository running the suite at the same time do not interfere.
- **Order dependence** → find the leaking fixture using the recorded seed, reset it at teardown, verify the recorded failing order deterministically, then keep shuffle coverage in the final checks.
- **Real race** → return to the normal hypothesis loop. The fix ships with a failing-first test that reproduces the race deterministically, using an event subscription or an injected clock instead of a longer wait.

## 5. Forbidden Fixes

These four are forbidden as the remedy for a flaky failure, regardless of the classification. Each one hides a bug report instead of answering it.

1. **Retry wrappers** — a decorator, a loop, or a runner-level retry that re-runs the test until it passes.
2. **Longer sleeps** — increasing a fixed wait, adding a delay, or raising a timeout to make the flake less frequent.
3. **Quarantine** — moving the test to a skipped or "known flaky" set, or excluding it from the gate.
4. **Test deletion** — removing the test, or weakening its assertion until it cannot fail.

A flake that was classified but not fixed is a finding to report, not something to hide. Journal the signature, the evidence, the classification, and the reason it was left open, and say it in the closing report.

## 6. Cleanup

Remove the extra rerun artifacts, temporary seeds, and any probe this triage added. Restore the runner configuration if it was changed for a diagnostic run.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Contention versus order dependence versus real race, and the signature table | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/03-flaky-triage.md` (mechanism reference, re-authored) |
| The contention checklist and per-run resource namespacing | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/03-flaky-triage.md` (mechanism reference, re-authored) |
| Retry wrappers, longer sleeps, quarantine, and test deletion as forbidden fixes | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/03-flaky-triage.md` (mechanism reference, re-authored) |
| A classified but unfixed flake is reported, not hidden | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/03-flaky-triage.md` (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` - the rerun set and the cleanup step are this package's design. The mechanism rows are re-authored from a repository with no license; no text or code is copied. The four forbidden fixes are kept as a hard list because each one converts a visible bug into an invisible one.
