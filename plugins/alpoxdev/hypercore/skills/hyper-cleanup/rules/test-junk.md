# Test Junk

Read this when the file set contains a test, or when a cleanup needs a test to prove a cut. It owns the marks, the junk classes, the proof each class needs, and how to run the two bundled scripts.

## 1. Marks

Every test declaration in scope gets one mark. The mark decides whether the declaration stays, changes, merges, or goes.

| Mark | Meaning | The ledger line names |
|---|---|---|
| `R` retain | guards a contract | the contract, and the regression it would catch |
| `F` fix | a real contract with a weak assertion | the repaired assertion |
| `C` consolidate | the assertion moves into a keeper; the declaration disappears | the keeper |
| `D` delete | no contract, or another test already owns it | the owning test, or why no contract exists, plus the proof |

`F` is not a softer `D`. A weak assertion that guards a real contract is repaired in place; deleting it loses the contract.

## 2. Junk Classes

A declaration in one of these classes is a candidate for `D` or `C`, and never for automatic deletion. The KEEP list in §3 outranks the class.

| Class | What it looks like | Proof it is junk |
|---|---|---|
| Cannot fail | no assertion, or an assertion that compares a value with itself, or an expected value computed by the code under test | a mutation of the production owner that the test survives |
| Change certificate | pins the diff: a constant, a string, a call, or the shape of the edit | revert the change; the test fails for the diff and not for a regression |
| Mock echo | the mock returns exactly what the test then asserts | mutate the owner; the test stays green |
| Implementation mirror | asserts call order, call count, private arguments, or internal state shape | a keeper at the real boundary catches the behavioral mutation |
| Prose pin | asserts wording, headings, order, snapshots, or lengths of a document | no behavior to mutate; cite the repository's own prose-test rule |
| Copied inventory | a hard-coded list of exports, files, tools, or keys that mirrors the source | a generator, freshness check, or real consumer already owns the list |
| Source grep | reads a source file and greps for a string or an import | an identifier-only rename turns it red while behavior is unchanged |
| Duplicate contract | the same input and output asserted at two layers with no distinct transport or lifecycle risk | the mutation is caught by both; keep the stronger boundary |
| Layer replay | a shared helper retested through every wrapper that calls it | one helper owner test plus one wiring test per real wrapper |
| Fabricated postcondition | the fixture supplies the state the owner should produce, and the test asserts a store nothing writes | mutate the writer; the test stays green |
| Capability restatement | asserts a flag is `true` instead of the delivery the flag promises | a delivery test owns it, or none exists |
| Input transcript | asserts the argv, URL, or request handed to a child process rather than the state it resolved | mutate the child's handling of that input; the test stays green |
| Near duplicate | N declarations differing only in input literals | consolidate into one table; every old assertion stays a row |

Two more outcomes belong here rather than in the table. A **misnamed** test is marked by what it actually checks, not by its name. A test that is **red on the unchanged base** is a product bug and leaves the ledger for the report in [behavior-lock.md](behavior-lock.md) §2.

## 3. Retention Bar

These stay `R` even when they match a class above. Name the row that keeps the test in the ledger.

- A public API, SDK, RPC, or protocol contract
- A configuration schema or a default value
- A migration, a storage format, or a compatibility suite
- A security boundary or a permission check
- A platform behavior, including a shipped artifact run under the real runtime
- Shipped-copy equality between two real artifacts
- A machine-consumed token: a parsed field, a sentinel a runtime greps, a schema key, or a routing-bearing fragment of parsed frontmatter
- An issue regression, until another test is shown to fail on that exact regression

Static or slow is never a reason to delete. A prose file has no behavioral seam: do not add a phrase, word-count, or heading pin for it, and cover only a value a machine actually parses.

## 4. Proof For `D` and `C`

Break the production owner, then run the candidate and its named keeper on the unmodified test tree.

| Candidate | Keeper | Verdict |
|---|---|---|
| green | red | the candidate cannot catch this → `D` proven |
| red | red | the behavior is already covered → `D` or `C` proven |
| red | green | the candidate is the only proof → `R`, or fold it into the keeper and rerun |
| green | green | the mutation missed the behavior → confirm the edit landed and pick another mutation |

The owner is restored byte for byte after every row, and no mutation is ever committed. That restore is what `scripts/mutation-proof.sh` does.

```sh
bash scripts/mutation-proof.sh --file src/pricing.ts --find 'if (total > 0)' --replace 'if (total >= 0)' --test 'npm test -- pricing'
bash scripts/mutation-proof.sh --file src/pricing.ts --find 'a' --replace 'b' --test 'npm test -- pricing' --json
```

The script prints one verdict: `caught` when the test failed with the mutation in place, `survived` when it passed. It restores the file and compares the SHA-256 before it reports, so a `survived` verdict still leaves the tree clean. Exit 0 means the proof ran, whether the verdict was caught or survived; exit 2 is a usage or target error; exit 3 means the restore could not be verified and the backup path is printed. `--find` must occur exactly once, which keeps one run to one mutation.

`--test` runs through `sh -c` in the current directory, so it sees the real project and the real runner. A mutation on the same file never runs in parallel with another: the two would restore over each other.

## 5. Find The Candidates

`scripts/scan-test-junk.sh` reports the classes a static read can see. Its findings are candidates for the ledger, never cuts.

```sh
bash scripts/scan-test-junk.sh tests/ src/pricing.test.ts
bash scripts/scan-test-junk.sh tests/ --json
bash scripts/scan-test-junk.sh --self-test
```

| Code | What it flags |
|---|---|
| `FOCUSED_TEST` | `.only`, `fit`, `fdescribe`, `focus: true`, or a focused marker |
| `SKIPPED_TEST` | `.skip`, `xit`, `xdescribe`, `todo`, `#[ignore]`, or a skip marker |
| `FIXED_SLEEP` | a numeric `sleep`, `waitForTimeout`, or a fixed `setTimeout` delay |
| `SELF_COMPARISON` | an assertion that compares a value with itself |
| `WEAK_ASSERTION` | an assertion that proves only length or non-emptiness |
| `SOURCE_TEXT_GREP` | a test that reads a source file and matches its text |

The scan is read-only and never widens past the paths it was given. A directory is searched for the test-file naming conventions of the common runners. Exit 0 means the scan completed, with or without findings; exit 2 is a usage, path, or tool failure.

A code in the output is a reason to read the line, not a reason to cut it. `SELF_COMPARISON` on a comparison of two independently computed values is a false positive, and `WEAK_ASSERTION` on a retention-bar test is a false positive that the ledger records.

## 6. Writing The Ledger

One row per `D`, `C`, or `F`. Rows are the audit trail, so they name paths and cases, not summaries.

```markdown
| Test | Mark | Keeper or reason | Proof |
|---|---|---|---|
| tests/pricing.test.ts:88 `totals` | D | tests/checkout.test.ts:120 owns the contract | mutation `> 0` → `>= 0`; candidate green, keeper red |
| tests/format.test.ts:31 `pads` | F | keeps the contract for zero padding | assertion repaired to compare the padded string |
| tests/api.test.ts:14 `returns list` | R | public API contract | — |
```

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Test junk classified as remove, fix, consolidate, or document, with a proof per class | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| The junk-class table, the retention bar, and the R/F/C/D marks | `dbc-hbin/omp-ulw@74df40f programming/references/testing/junk-classes.md` (mechanism reference, re-authored) |
| The candidate and keeper verdict matrix, and the byte-identical restore after each mutation | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| A static detector's findings are candidates and never automatic cuts | `dbc-hbin/omp-ulw@74df40f remove-ai-slops/SKILL.md` (mechanism reference, re-authored) |
| The two script interfaces, their codes, and their exit meanings | integrator contract, 2026-11-10 (issue #24) |

### Evidence grade

`LOCAL` - the mark set, the static code names, and the ledger row shape are this package's design. The class list and the proof matrix are re-authored from a repository with no license; no text or code is copied.
