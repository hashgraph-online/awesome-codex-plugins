# Evidence Binding

Use this rule before the first capture and whenever a proof is reported pass, stale, missing, or failing. It defines what a proof is bound to and when that binding expires.

## 1. What the Fingerprint Covers

A proof is meaningful only for the exact content it checked. This package binds a proof to two values and one command:

| Value | How it is produced | Why it is there |
|---|---|---|
| `tree` | `git rev-parse 'HEAD^{tree}'` | A commit that changes only messages or identities does not invalidate a proof, because the content is the same |
| `diff_sha256` | SHA-256 of `git diff --binary HEAD` followed by one `<sha256>\t<path>` line per sorted untracked file | Uncommitted edits and new files are part of the proof, so an uncommitted change cannot be hidden behind an unchanged `HEAD` |
| `command` | The exact command line the capture ran | A later reader can re-run it, and a reader who cannot re-run it knows the proof is weaker than it looks |

Ignored files are excluded, so build output, dependency folders, and caches do not churn the digest. The loop directory itself is excluded, because appending to `ledger.jsonl` would otherwise invalidate every earlier proof; that exclusion is the whole reason the loop directory sits inside the worktree without breaking its own ledger.

The bundled verifier computes this value; do not compute it by hand:

```bash
bash <skill-dir>/scripts/verify-loop-state.sh snapshot --dir .hyper/loop/<slug>
```

It prints `tree`, `diff_sha256`, the untracked entries, and the excluded path. [references/state-schemas.md](../references/state-schemas.md) holds the exact field list.

## 2. The Ledger Row

One criterion proof is one JSON object appended to `ledger.jsonl`:

```json
{"event":"evidence","goal_id":"G1","criterion_id":"C2","verdict":"pass",
 "tree":"<tree>","diff_sha256":"<digest>","command":"<the command that was run>",
 "evidence":"<what the capture showed>","artifacts":["<path>"],"rationale":"<why this proof answers the criterion>"}
```

Rules for the row:

- Append, never edit. A wrong row is superseded by a newer row for the same criterion; the older row stays as history.
- `verdict` is `pass`, `fail`, or `blocked`. A `blocked` row means the scenario could not run, which is not a pass.
- `command` is the command that actually produced the evidence, not the command that should have produced it.
- `evidence` describes what was observed, in concrete terms: the exit code, the output line, the measured value.
- `artifacts` names files the capture wrote, relative to the repository root or absolute. At least one artifact or the `expected_evidence` file must carry the observation.

A checkpoint row uses `event: "checkpoint"` and names the goal, the tree, the digest, and the criteria that passed. Steering uses `event: "steering"` with the verb and its rationale. Failure bounds use `event: "failure"` with the signature.

## 3. Fresh, Stale, Missing, Failing

The verifier compares the last evidence row for a criterion with a fingerprint computed now.

| State | Meaning |
|---|---|
| `pass` | The row's `verdict` is `pass`, its tree and digest equal the current ones, and the `expected_evidence` file exists and is non-empty |
| `stale` | The row passed, but the tree or the digest differs from the current worktree; the content moved after the capture |
| `failing` | The last row's verdict is `fail` or `blocked` |
| `missing` | No evidence row exists for the criterion |
| `missing-evidence-file` | The row is fresh but the file at `expected_evidence` is absent or empty |

Only `pass` counts as proof. `stale` is the state this whole mechanism exists for: the code changed, so the old output no longer describes the current behavior, even if nothing about the change looked related.

## 4. Re-capture, Never Re-label

When a criterion is `stale`, the answer is a new capture:

1. Re-run the scenario exactly as the criterion's `scenario` states.
2. Write the new observation to the same `expected_evidence` path, replacing the old content.
3. Append a new evidence row with the current tree and digest.
4. Run `--goal <id>` again and read the new states.

Never do these:

- Update the row's `tree` and `diff_sha256` while keeping the old output.
- Attach an old log to a new fingerprint because the change "cannot have affected it".
- Mark the criterion `pass` in `goals.json` without a row.

If a change genuinely cannot affect a criterion, re-running its scenario is cheap and settles the question; the run will re-run it rather than argue.

## 5. Evidence Files

- One file per criterion is enough; the path in `expected_evidence` is the address the verifier checks.
- The file holds the observation, not a summary written afterwards: command output, a transcript, a diff, a measurement, or a screenshot path for a visual surface.
- Keep files small and text-like where possible. A screenshot is fine for a visual surface; a multi-megabyte dump is not, because nobody re-reads it at the gate.
- Cleanup receipts go in the criterion's `cleanup` note and, when they matter, in the row's `rationale`: which processes were stopped, which temporary directories were removed, which resources were never created.
- Deleting an evidence file turns its criterion into `missing-evidence-file`, which is why evidence lives inside the run directory rather than in a temporary path.

## 6. What the Fingerprint Does Not Prove

- It does not prove the scenario was a good test; a weak criterion passes weakly.
- It does not cover files outside the repository, remote services, or state that changes without touching a file.
- It cannot tell two machines apart when they share content; a proof from a machine with a different toolchain may have run different commands against identical bytes.

State these limits when a proof rests on them, and prefer a scenario that observes the product surface over one that observes an internal value.

## Sources

> Checked 2026-11-09.

Source paths below are given from the source repository's skill root (its `skills` directory).

| Claim | Source |
|---|---|
| Binding a proof to the git tree, a worktree diff digest, and the capture inputs, and invalidating it when the captured content changes | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/omp-ledger.md` (mechanism reference, re-authored) |
| Excluding workflow bookkeeping from the fingerprint so the ledger does not invalidate itself | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/omp-ledger.md` (mechanism reference, re-authored) |
| `git rev-parse HEAD^{tree}` yielding the tree object of the current commit | <https://git-scm.com/docs/git-rev-parse> |
| `git diff --binary` emitting a binary-safe patch | <https://git-scm.com/docs/git-diff> |
| Excluding ignored files from untracked enumeration with `--exclude-standard` | <https://git-scm.com/docs/git-ls-files> |

### Evidence grade

`LOCAL` - the exact concatenation order of the digest and the exclusion rule are this package's design, implemented in `scripts/verify-loop-state.sh` and proven by its `--self-test`. The git commands are `PRIMARY` - each is documented by git.