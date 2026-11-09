# Working Loop

Read this before the first reproduction attempt. It owns the setup, the reproduction, and the journal.

## 1. Fix The Four Facts Before Anything Else

Write these in the journal before running a probe. A wrong value here wastes every later round.

| Fact | How to get it | Why it decides the rest |
|---|---|---|
| Launcher | The exact command a user or CI runs, from `package.json` scripts, `Makefile`, `justfile`, `pyproject.toml`, `Cargo.toml`, `go.mod`, a workflow file, or the report itself | A reproduction that starts the program a different way can pass while the real path fails |
| Runtime identity | Version and the actual binary on `PATH` (`node -v`, `python3 -V`, `rustc -V`, `go version`, `file <binary>`) | A failure in one version is not a failure in another, and a stale global install is a classic false lead |
| Inputs | The exact file, request body, row, fixture, environment variables, and seed that produced the report | An approximate input produces an approximate symptom |
| Expected behavior | What should have happened, taken from a spec, a test, a doc, or the user's words | Without it, "wrong output" has no definition and the fix cannot be verified |

If one of the four is missing and the report does not supply it, ask for that one thing and mark the run `awaiting_input`; do not invent it.

## 2. Reproduce First

- Run the reported path unchanged before changing anything. Record the command, the working directory, and the output verbatim.
- If it reproduces: shrink it. Remove inputs, flags, layers, and dependencies one at a time, re-running after each removal, until the failure disappears; keep the last setup that still fails. That setup is the reproduction.
- If it does not reproduce: check the four facts against the report before concluding anything. A different version, a different working directory, a warm cache, or a different environment variable is a different program.
- Reproduce the reported failure, not a nearby one. A reproduction of a different symptom proves nothing about this report.

## 3. Smallest Safe Setup

- Prefer a disposable target: a temp directory, a local file copy, a scratch database, a local server on an ephemeral port. Never point a reproduction at a shared, staging, or production system.
- Copy the minimum data needed to show the symptom. Redact secrets from anything pasted into the journal; record the shape of the value, not the value.
- Write down every resource the setup creates — files, directories, processes, ports, containers, environment overrides — in the journal's Resources table before creating it, so cleanup is a checklist rather than a memory test.
- Stop any process this run started before the run ends. Leave processes that belong to the user alone, and say so when one blocks the reproduction.
- A reproduction that needs credentials, a paid service, a device, or a network the session does not have is `awaiting_input` with one specific question, not a guess.

## 4. Read Before Instrumenting

- Read the failing code, its callers, and the tests that already cover it before adding a single probe.
- Reuse an existing test or fixture as the reproduction when one already covers the path; extending it is cheaper and leaves the repository with a real regression case.
- Prefer an observation the runtime already gives: an exit code, stderr, a stack trace, a log line, a request and response pair, a returned value.
- Add instrumentation only when no existing signal answers the hypothesis. Record each hunk in the journal's Instrumentation table with the file, the line, and the question it answers.

## 5. Journal

Write to `.hyper/debug/<slug>.md`. `<slug>` is a short kebab-case name of the symptom, not of the guessed cause. Create the directory if it does not exist.

````markdown
# <symptom in one line>

- 모드: findings-only | minimal-fix
- 런처: `<command>`
- 런타임: `<name and version>`
- 입력: `<the exact inputs>`
- 기대 동작: <what should happen>
- 보고: "<the user's report, quoted>"

## Resources

| Kind | Path / port / pid | Created by this run | Cleanup |
|---|---|---|---|
| temp dir | `/tmp/debug-<slug>` | yes | removed |

## Reproduction

- Command: `<exact command>`
- Working directory: `<path>`
- Output:
```text
<verbatim>
```
- Shrink steps: <what was removed, and what still failed>

## Hypotheses

| # | Axis | Claim | Distinguishing observation | If true, the fix is |
|---|---|---|---|---|
| H1 | ... | ... | ... | ... |
| H2 | ... | ... | ... | ... |

## Evidence

### <timestamp> — <what was observed>
- Source: `path:line` | `<command>` | `<log source>`
- Value: `<verbatim>`
- Interpretation: <one line>
- Confirms / refutes: H<n>

## Instrumentation

| File:line | Added | Question it answered | Removed |
|---|---|---|---|
| `path:line` | `console.log(...)` | which branch ran | yes |

## Root cause

- Mechanism: <the causal chain in one paragraph>
- Toggle proof: "With <change>, the repro produces <good>; reverting it produces <bad>."
- Fix scope: <files and approximate size>

## Verification

- Red: `<command>` → <verbatim failure>
- Green: `<command>` → <verbatim pass>
- Area checks: `<command>` → <result>

Result: <terminal>
````

Rules for the journal:

- Quote values verbatim. `items.length=0` is evidence; "the list looked empty" is a memory of an observation.
- One evidence entry per observation, with the source and the hypothesis it touches.
- Update the journal as the run goes, not at the end. A journal written afterwards records the story, not the evidence.
- The last line is exactly `Result: <terminal>` with one value from the terminal table in the core.

## 6. Cleanup

- Remove every temporary file, directory, process, port, container, and environment override this run created; tick each row of the Resources table.
- Remove every instrumentation hunk this run added; tick each row of the Instrumentation table. `rules/fix-and-proof.md` §4 owns the one exception — a log line that earns a permanent place.
- A run that leaves a debug port, a background server, or a stray temp directory has not finished.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Reproduce first, shrink to the smallest failing setup, and keep a resource and instrumentation journal | `dbc-hbin/omp-ulw@74df40f debugging/SKILL.md` (mechanism reference, re-authored) |
| Reading existing tests and logs before adding instrumentation | `dbc-hbin/omp-ulw@74df40f debugging/SKILL.md` (mechanism reference, re-authored) |
| Verbatim values as the only acceptable evidence | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/02-investigate.md` (mechanism reference, re-authored) |
| The `Result:` line and the six terminals | integrator contract, 2026-11-09 |

### Evidence grade

`LOCAL` - the four facts, the journal fields, and the cleanup checklists are this package's design. The mechanism rows are re-authored from a repository with no license; no text or code is copied.
