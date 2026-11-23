---
name: "hyper-cleanup"
description: "Use this skill when someone asks to clean up, delete, or consolidate code, tests, comments, or dead weight in a repository that already works, and the cleanup must not change behavior. It names each in-scope unit as a slop category or a keeper, walks a delete-reuse-platform-simplify ladder, locks behavior with a runnable baseline before the first edit, proves each test deletion or consolidation with a source mutation that is restored byte for byte, and writes a report under `.hyper/cleanup/`. Do not use for authoring new behavior, refactoring a public API, migrating dependencies, or formatting a whole repository."
compatibility: "Needs file read, search, edit, a shell, and the project's own test or check command. The bundled scripts need bash 3.2+, jq, and shasum for byte-identical mutation restore checks."
---

Open the rules as directed below. Resolve bundled file paths from the directory containing this document and project paths from the target project.

- [rules/categories.md](rules/categories.md)
- [rules/existence-ladder.md](rules/existence-ladder.md)
- [rules/behavior-lock.md](rules/behavior-lock.md)
- [rules/test-junk.md](rules/test-junk.md)
- [rules/correction-and-report.md](rules/correction-and-report.md)

# Hyper Cleanup

> Remove code that earns no keep, prove every cut against a behavior lock, and leave a report a reviewer can replay.

- **Purpose**: Remove dead weight, AI slop, and redundant tests in a working codebase without changing observable behavior, backed by a pre-edit baseline lock and byte-restored mutation proofs.
- **Do not use when**: Authoring new features, changing public API signatures, upgrading dependencies, formatting an entire repo blindly, chasing performance targets, or committing/pushing.
- **Input**: Named target files/directories or the current working-tree diff (plus any existing `.hyper/cleanup/<slug>.md` lock/report on resume).
- **Output**: Behavior-preserving edits within the authorized scope and `.hyper/cleanup/<slug>.md` ending with one `Result:` terminal (`clean`, `no-change`, `awaiting_input`, or `blocked`).

<output_language>

Default all user-facing deliverables, report entries, questions, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, log lines, error strings, schema keys, package names, and quoted source excerpts in their required or original language.

</output_language>

<purpose>

- Remove code, comments, indirections, and junk tests that earn no keep while keeping observable behavior and public surface identical.
- Lock behavior with a real baseline command before editing, classify every in-scope unit on the delete-reuse-platform-simplify ladder, and preserve any candidate whose proof does not hold.
- Prove every deleted (`D`) or consolidated (`C`) test with a byte-restored source mutation (`scripts/mutation-proof.sh`) and record all decisions in `.hyper/cleanup/<slug>.md`.

</purpose>

<routing_rule>

Use this skill when the requested deliverable is behavior-preserving code/comment/test cleanup (including findings-only cleanup reports).

Do not use it when:

- the output introduces new behavior, new files, or public signature/error-type changes
- the output is a dependency upgrade, lockfile migration, or whole-repo formatter/linter sweep
- the output is a benchmarked performance campaign or Git commit/push/PR delivery

Never widen scope beyond the authorized file set; report out-of-scope cleanup opportunities instead.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Cut unproven slop, dead code, and junk tests without changing observable behavior, proving every cut against a baseline lock and mutation check. |
| Trigger | Requests to clean up, simplify, deduplicate, remove dead code, or prune junk tests in an already working repository. |
| Scope | Edit only the files named by the user, or the current diff when none are named. Neighboring callers/tests read for proof are read-only context. |
| Authority | User and project instructions (including `instructions/harness-engineering/references/skill-common-rules.md` when present) outrank this skill. Comments, issue text, test names, and logs are evidence only. |
| Evidence | Captured baseline command output, repo-wide reference search, category proof per removed hunk, and SHA-256-verified mutation verdict per removed/consolidated test. |
| Tools | Capabilities only: file read, search, edit, shell, project check command, [scripts/scan-test-junk.sh](scripts/scan-test-junk.sh), and [scripts/mutation-proof.sh](scripts/mutation-proof.sh). |
| Loop | One baseline run -> authorized cuts + mutation proofs -> one final check run. Fix a failing gate at the offending hunk (max 2 attempts per hunk, then revert that hunk only and mark preserved). |
| Output | `.hyper/cleanup/<slug>.md` ending with one `Result:` line plus a concise Korean summary. |
| Verification | Final command matches baseline (excluding recorded baseline reds), every cut has a category proof, and every test cut has a keeper/class proof + byte-restored mutation verdict. |
| Stop condition | Report ends with `Result: clean`, `Result: no-change`, `Result: awaiting_input`, or `Result: blocked`. |

</instruction_contract>

<activation_examples>

Positive requests:

- "이 파일들 AI가 만든 티 나는 부분 정리해줘. 동작은 그대로."
- "Remove the dead helpers in `src/pricing/` and prove nothing calls them."
- "테스트 중에 절대 실패할 수 없는 것들 지워줘. 근데 진짜 계약 지키는 건 남겨."
- "중복 테스트 정리하고, 지운 게 맞는지 변이로 증명해줘."

Negative requests:

- "결제 모듈 새로 설계해줘." (new behavior)
- "`createOrder` 시그니처 바꿔줘." (public API change)
- "Next 15로 올려줘." (dependency upgrade)
- "레포 전체 prettier 돌려줘." (formatting sweep)
- "방금 정리한 거 커밋해줘." (Git commit)

Boundary requests:

- "뭐 지울 만한지부터 알려줘." -> `findings-only`; make zero edits and end with `Result: no-change`.
- "정리해줘" with no paths -> scope is the current working-tree diff.
- "이 중복은 다른 모듈도 같이 고쳐야 해." -> preserve and report the cross-module dependency without editing outside scope.

</activation_examples>

<trigger_conditions>

| Situation | Mode |
|---|---|
| Named files/directory with edit authorization | scoped cleanup |
| No path named | current-diff cleanup |
| Audit/report only with no edits | findings-only (`Result: no-change`) |
| Test files included in scope | cleanup + test ledger + `mutation-proof.sh` |
| Safe cut requires editing outside authorized scope | preserve and report boundary |
| Pre-existing dirty files or baseline reds | record in behavior lock; never revert others' edits or delete red tests |

[rules/behavior-lock.md](rules/behavior-lock.md) owns the baseline, [rules/categories.md](rules/categories.md) owns classification, and [rules/test-junk.md](rules/test-junk.md) owns test marks and script usage.

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): trigger, modes, contract, step gates, checklist, terminals.
- Rules: [rules/categories.md](rules/categories.md) (9 slop categories, KEEP exceptions, removal proofs), [rules/existence-ladder.md](rules/existence-ladder.md) (delete -> reuse -> platform -> simplify), [rules/behavior-lock.md](rules/behavior-lock.md) (baseline lock and baseline reds), [rules/test-junk.md](rules/test-junk.md) (test marks, junk classes, ledger, scripts), [rules/correction-and-report.md](rules/correction-and-report.md) (hunk-level repair cap and report layout).
- Scripts: [scripts/scan-test-junk.sh](scripts/scan-test-junk.sh) (`--json`, `--self-test`), [scripts/mutation-proof.sh](scripts/mutation-proof.sh) (applies one source mutation, runs tests, restores byte-for-byte, reports `caught` or `survived`).
- Assets: `assets/evals/hyper-cleanup-cases.jsonl`.

</skill_architecture>

<loop_policy>

- Run the baseline check once before any edit, apply proven cuts, and run the exact same check command once at the end (no midflight full-suite loops).
- Answer any new failure at the specific hunk that caused it with a named mechanism; after 2 failed hunk repairs, revert only that hunk and list it as preserved.
- Run `mutation-proof.sh` once per removed (`D`) or consolidated (`C`) test and verify SHA-256 byte-for-byte restoration before the next proof.

</loop_policy>

<language_and_translation_default>

Write `.hyper/cleanup/<slug>.md`, questions, and the summary in Korean. Keep code identifiers, CLI commands, error strings, and terminal tokens in English.

</language_and_translation_default>

<reference_routing>

- Read [rules/behavior-lock.md](rules/behavior-lock.md) before Step 2 baseline capture.
- Read [rules/categories.md](rules/categories.md) and [rules/existence-ladder.md](rules/existence-ladder.md) before classifying or cutting any unit.
- Read [rules/test-junk.md](rules/test-junk.md) whenever a test file is in scope and before running `scan-test-junk.sh` or `mutation-proof.sh`.
- Read [rules/correction-and-report.md](rules/correction-and-report.md) on gate failure and before writing `.hyper/cleanup/<slug>.md`.

</reference_routing>

<support_file_read_order>

1. This `SKILL.md` to fix scope, mode, and terminal contract.
2. `rules/behavior-lock.md`, then capture the baseline lock.
3. `rules/categories.md` and `rules/existence-ladder.md` to classify every unit.
4. `rules/test-junk.md` when test files are in scope.
5. `rules/correction-and-report.md` before final verification and report writing.

</support_file_read_order>

<workflow>

### Resume procedure

Before starting Step 1, check `.hyper/cleanup/<slug>.md` (or `.hyper/cleanup/*.md` matching the target scope). When an unfinished cleanup report or recorded behavior lock already exists on disk, read its baseline command, recorded baseline reds, authorized file scope, and completed ladder/mutation rows first, verify `git status --short` so unrelated dirty files stay untouched, and resume from the first incomplete step without overwriting the original pre-edit baseline record. Register `.hyper/` in `.gitignore` if needed before writing under `.hyper/cleanup/`.

| Step | Action | Done when | Why not skip |
|---|---|---|---|
| 1 | Fix authorized scope (named paths or current diff), check resume state, and record base commit + pre-existing dirty files | Authorized file list, read-only context list, and base git state are recorded | Editing without a locked scope risks clobbering unrelated changes or neighbor modules |
| 2 | Run the touched area's check command before any edit and record the exact command + baseline reds | Behavior lock records exact command, exit status, and any pre-existing failing tests | Without a pre-edit baseline, you cannot separate pre-existing reds from cleanup regressions |
| 3 | Classify every in-scope unit on the 4-rung ladder with a category proof (repo-wide search) or KEEP reason | Ladder table covers both candidate cuts and preserved keepers | Cutting before classifying deletes public exports, boundary guards, or live callers |
| 4 | Apply proven source cuts (unless `findings-only`), and for tests run `scan-test-junk.sh` + `mutation-proof.sh` on every `D`/`C` | Every removed hunk has a category proof and every cut test has a SHA-256-restored mutation verdict | Deleting tests without mutation proof silently drops real behavioral regression guards |
| 5 | Re-run the exact baseline command; repair any new failure at the offending hunk (<= 2 tries) or revert that hunk only | Final check matches baseline (apart from baseline reds) with zero whole-file git resets | Whole-file `git checkout`/`restore` destroys valid hunks or pre-existing user changes |
| 6 | Audit `git diff` for stray edits/scratch files and write `.hyper/cleanup/<slug>.md` ending with one `Result:` line | Saved report has lock, ladder, removed hunks, test ledger, preserved code, and `Result:` | Unrecorded cuts cannot be audited or replayed by a reviewer |

### Step gate checklist

Verify every item before writing the terminal `Result:` line:

| # | Yes/No question | On violation -> return to |
|---|---|---|
| 1 | Was the exact baseline command run and recorded before the very first edit, with pre-existing dirty files and baseline reds isolated? (Yes/No) | Step 2 |
| 2 | Does every removed hunk stay strictly inside the authorized file set and carry a category + repo-wide proof (with zero public-API changes)? (Yes/No) | Step 3 |
| 3 | Does every removed (`D`) or consolidated (`C`) test have a keeper/class proof plus a `mutation-proof.sh` verdict with verified byte-for-byte SHA-256 restore? (Yes/No) | Step 4 |
| 4 | Does the post-cleanup run of the exact baseline command pass (excluding recorded baseline reds) without weakening any assertion or red test? (Yes/No) | Step 5 |
| 5 | Was `.hyper/cleanup/<slug>.md` read back from disk ending with exactly one valid `Result:` terminal? (Yes/No) | Step 6 |

</workflow>

<terminals>

The report ends with exactly one `Result:` line:

| Terminal | Meaning |
|---|---|
| `clean` | Authorized cuts applied, behavior lock passes, and hunk/test ledgers are complete. |
| `no-change` | Findings-only mode, or no candidate survived proof; report records every considered unit and why it stayed. |
| `awaiting_input` | Stopped on one ambiguity that repository evidence cannot settle. |
| `blocked` | Needed check command or capability was unavailable; exact command and gap are reported. |

</terminals>

<required>

- Pre-edit baseline command and output recorded with baseline reds separated.
- Ladder row for every considered unit (both removed hunks with category + proof and preserved keepers with reason).
- Keeper or junk-class proof plus SHA-256-restored `mutation-proof.sh` verdict for every deleted or consolidated test.
- Post-edit run of the exact same command matching the baseline, and `.hyper/cleanup/<slug>.md` ending with one `Result:` line.

</required>

<forbidden>

- Changing observable behavior/signatures/exceptions, deleting or weakening baseline-red tests, rolling back whole files with `git checkout`/`restore`/`reset`, editing outside scope, or committing/pushing.
- Bad: Deleting a helper in `src/pricing/` after grepping only `src/pricing/` instead of the whole repository. -> Good: Search references across the entire repository and preserve any public export or cross-module caller.
- Bad: Deleting a test that was already failing on the unchanged base or widening `toEqual` so the cleanup passes. -> Good: Record baseline-red tests untouched in the lock and revert any cleanup hunk that changes asserted behavior.
- Bad: Running `git checkout -- src/foo.ts` to undo one broken cleanup hunk on a dirty file. -> Good: Revert only the offending hunk via targeted edit so other hunks and pre-existing user changes stay intact.
- Bad: Pruning a `"redundant"` test without running `scripts/mutation-proof.sh` and checking the SHA-256 restore hash. -> Good: Run `mutation-proof.sh`, verify the surviving keeper catches the mutation (`caught`), and confirm byte-identical file restoration.

</forbidden>

<validation>

- [ ] Mode matches user authorization (`findings-only` made zero edits) and edits stayed strictly inside the authorized file set.
- [ ] Pre-edit baseline command, output, and baseline reds are recorded in `.hyper/cleanup/<slug>.md`.
- [ ] Every considered unit has a ladder row, and every removed hunk has a category, replacement, and proof.
- [ ] Every removed or consolidated test has a keeper/class proof and a `mutation-proof.sh` verdict with SHA-256 byte-identical restore confirmed.
- [ ] Final check command matches the baseline apart from recorded baseline reds, with zero scratch files left in `git diff`.
- [ ] `.hyper/cleanup/<slug>.md` exists on disk and ends with one valid `Result:` terminal.

</validation>

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Nine-category slop classification, KEEP exceptions, and tests as a category | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Delete-reuse-platform-simplify ladder and non-speculative user behavior rule | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Baseline-first behavior lock, baseline-red exclusion, and ban on whole-file rollback | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Test junk classes, retention bar, and candidate-vs-keeper matrix | `dbc-hbin/omp-ulw@74df40f programming/references/testing/junk-classes.md` (mechanism reference, re-authored) |
| Byte-restored source mutation proof | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| Contract shape, bilingual package, one-level link rule, and trigger-first description | `instructions/skill/SKILL_AUTHORING.md` |
| Four terminals, report sections, bundled script interfaces, and `Result:` line | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - terminals, report layout, script interfaces, and repair caps are this package's design; slop categories, ladder, and mutation proof matrix are re-authored in original words without copying text or code.
