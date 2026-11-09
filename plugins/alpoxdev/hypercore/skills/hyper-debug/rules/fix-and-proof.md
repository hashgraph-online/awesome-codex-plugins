# Fix And Proof

Read this before calling any cause confirmed, and before editing anything in minimal-fix mode. It owns the toggle proof, the red-to-green order, the observability gap, and instrumentation removal.

## 1. Confirmed Means Toggle-Provable

A cause is confirmed only when all three hold, and the third one is the toggle proof: no toggle, no confirmation.

1. **The captured value matches the prediction exactly.** Not "consistent with" — the observation is the value the hypothesis said it would be, read at the moment the failure happens.
2. **The reproduction is stable.** Running it a second time gives the same observation. A case that only sometimes shows the symptom has isolated a symptom, not the cause; go back to the hypothesis loop.
3. **Toggling the cause toggles the failure.** With the cause changed, the failure is gone; with the change reverted, the failure reproduces again. Both directions must be observed. This is the proof that separates a mechanism from a correlation.

Every other level of evidence is correlation. A correlation-driven fix ships bugs.

| Suspected cause | Valid toggle |
|---|---|
| An environment variable overrides a library default, and the override is wrong | Unset it → the failure goes away; restore it → the failure returns |
| A task is not awaited | Add the await → passes; remove it → fails again |
| A client uses a hardcoded URL | Point it at the configured URL → passes; revert → fails again |
| A shared-state race | Serialize the access → passes under load; remove the guard → fails under load |
| A value is read before it is set | Move the read after the write → passes; move it back → fails |

If no toggle can be constructed, the cause is not confirmed. Run another round rather than writing the fix.

## 2. Record The Confirmation

```markdown
## Root cause (confirmed <ISO timestamp>)
- Mechanism: <the causal chain from cause to observable symptom, one paragraph>
- Evidence: <file:line of the captured value | path to the saved reproduction | command and output>
- Toggle proof: "With <change X>, the repro produces <good>. Reverting <change X>, the repro produces <bad>."
- Fix scope: <files and approximate size>
```

The mechanism paragraph is the acid test. If the chain from cause to symptom cannot be written as one causal paragraph, the bug is not understood well enough to fix.

A cause that did not reach toggle proof is reported with `Assumption:` and the exact check that would confirm it, and the run ends `unconfirmed`. It is never edited as though it were confirmed.

## 3. Red To Green

In minimal-fix mode, in this order:

1. **Find the owning test.** Search for the test that already covers this contract at the strongest boundary, and run it on the unfixed code.
   - It already fails for this bug → it is the red proof. Record it.
   - It passes but covers the path → extend it with the failing case rather than adding a parallel test.
   - No owner exists → add a narrow reproduction only where the repository keeps tests for this behavior; otherwise keep the captured executable reproduction as the proof.
2. **Red.** Capture the failing run and paste its output into the journal. The test name should read like a bug report, and the failure output alone should explain what is broken.
3. **Green.** Make the smallest change that fully removes the observed mechanism. Signs of over-fixing: "just in case" null checks, refactoring adjacent functions, new configuration options the bug did not require, a new abstraction to make the code cleaner.
4. **Refactor only after green.** Cleanup that is directly part of the fix is allowed. Everything else is a journal follow-up, not this change.
5. **Area checks.** Run the checks the repository requires for the touched area. A new failure means the "fix" changed something load-bearing; return to §1 with the new failure as evidence.

A test written after the fix can still pass with the fix reverted. Verify the test fails without the fix and passes with it, and keep both outputs in the journal.

## 4. Close The Observability Gap

If diagnosis burned extra rounds because the state was invisible — no log line said which branch ran, what the value was, or whether a fallback engaged — that invisibility is a defect next to the bug. This is the one moment where adding a log line is not "just in case": this run is the evidence that the line earns its place.

- Write it through the project's designated logger, at the level the consumer needs, at the decision point, with data in fields rather than interpolated text.
- Name the ongoing consumer of the line. A line that only served this session is instrumentation, and §5 removes it.
- If the project deliberately does not log, respect that and skip this step; note it in the journal.

## 5. Remove Every Instrumentation Hunk

- Remove every `console.log`, `print`, `dbg!`, `fmt.Println`, temporary flag, disabled assertion, sleep, debug port, and local patch this run added.
- Tick each row of the journal's Instrumentation table, and each row of the Resources table for anything still running.
- Check the diff holds only the intended change: `git diff` (or the repository's equivalent) showing no probe left behind. Do not commit.
- If a probe must stay because it is now part of the fix, it moved into §4 and is named there.

## 6. Handoff Shape

When the confirmed cause needs changes in several files, a new module boundary, or a schema change, the output is a fix brief inside the journal instead of an edit. The journal's `Result:` line is `handoff`.

```markdown
## Fix brief

- 원인: <the confirmed mechanism, one paragraph>
- 증거: `path:line` | `<command and output>`, toggle proof: "<change X → good; revert → bad>"
- 재현: `<exact command>` in `<working directory>` — <expected failure>
- 수정 범위 초안: <the surfaces that must change, with the known location of each>
- 순서: <which file or migration must land first, and why>
- 검증 계획: <the red run, the green run, and the area checks a worker must produce>
- 가정·미확인: <open points>
```

The brief must be executable without re-reading this run's investigation. It is a plan-shaped output, not a plan for a new feature: the cause, the reproduction, and the proof already exist.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| A cause is confirmed only by a toggle that reproduces and removes the failure | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| The three confirmation conditions and the toggle examples | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| Red before green, the owning test first, the smallest change, and refactor only after green | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| Closing the observability gap and removing every temporary instrumentation hunk | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| The `handoff` terminal and the plan-shaped fix brief | integrator contract, 2026-11-09 |

### Evidence grade

`LOCAL` - the fix-brief fields and the ordering of §3 are this package's design. The mechanism rows are re-authored from a repository with no license; no text or code is copied. The toggle proof requirement is kept hard because correlation-driven fixes are the failure mode this package exists to prevent.
