# Reconcile copied slices and newer upstream changes

Use this before landing a cutover that carries copied lower slices or ports newer base code, and while maintaining its copied dependencies. A clean merge, ancestry, a matching subject, and a small diff stat do not establish that upstream intent survives.

## 1. Pin the comparison and recover provenance

Complete the copied-dependency record in `stack-map.md`: the original reference/fork, the cutover's start, the base observed when copies were made, the tip before its own edits, and each original-to-copy SHA. Keep those historical pins unchanged. Record the current base and cutover SHAs for this reconciliation pass, plus the cutover's pre-merge tip if a base merge is needed.

Reconstruct missing mappings from actual patches, available commit objects and landed PR evidence, including squash/rebase landing SHAs. A subject match or `stack-status.sh -c` result is a lead, not identity or semantic proof. If required history remains unavailable, identify the affected changes as unverified; do not call the cutover ready.

## 2. Inventory relevant upstream changes

- Inspect each copied source slice from its recorded source tip through its latest fixes or landed version. Include fixes carried through other dependent slices. Use the recorded original and landing SHAs when source branches have gone away.
- Inspect base changes from the cutover's original starting commit/fork through the current pinned base. The base observed when copies were made is a checkpoint, not proof those base changes were included in a fork-built cutover. For later completed passes, retain the prior log and review the additional range. Account for relevant merge resolutions as well as individual commits.
- Relevant changes include copied code, documentation corrections, test assertions/coverage, replacement APIs, and callers/configuration affected by removals. Include new or moved base files outside the reference diff; search for uses of removed APIs across the current tree.
- Review the range for relevance before filtering paths. Note unrelated groups with a brief scope reason; a porting row for every unrelated base commit is unnecessary. Record each relevant commit or hunk explicitly, linking duplicate source/landed copies to the same entry.

The immutable reference is the split baseline, not a complete inventory of subsequent review or base changes. `split-coverage.sh` compares snapshots on the reference's paths; `-i` skips base-changed paths. Neither substitutes for this inventory.

## 3. Reconcile by hunk and intent

Compare the copied version, the updated upstream version, and the cutover's own edits. Inspect full patches and use per-hunk `git blame` to trace surviving lines; use parent versions and rename/deletion history for removed code. Classify each difference:

| Kind | Action |
|---|---|
| Stale copied content | Carry the missing correction from the owning slice, or port its intent onto the replacement API |
| Newer upstream change | Preserve its applicable behavior, documentation and test intent; migrate new callers and configuration |
| Intentional cutover change | Retain the intended migration while adapting the upstream correction to it |

Kinds can overlap in one hunk. Neither the child nor the base wins automatically. Review relevant cleanly merged hunks too. Preserve the stronger upstream test assertions on the new API, rather than restoring an obsolete test wholesale. If dropping or changing upstream intent needs a decision outside existing authorization, prepare the alternatives and ask; continue independent authorized work.

## 4. Keep a porting log

Keep the log with the stack map in durable session notes or an authorized local artifact, and include its location in the handoff. Do not commit it or publish it to a PR unless that is authorized. This is an accounting record with evidence, not a proof of behavioral equivalence.

```markdown
Cutover: <branch>; original starting commit/fork: <sha>
Base observed when copies were made: <sha>
Compared through: source slices <slice:sha, …>; base <sha>
Checked cutover tip: <sha>; previous checked tips: <…>
Unrelated scope exclusions: <groups/ranges and reasons, or none>

| Upstream commit / hunk | Intent (including docs/tests) | Outcome | Destination in current tree / port commit | Verification and result |
|------------------------|------------------------------|---------|-------------------------------------------|-------------------------|
| <sha / path / hunk> | <what must survive> | <status> | <path, symbol/test and sha> | <inspection/test evidence, or unverified> |

Removed/replaced APIs: <symbols and replacements, or none>
Reference checks: <checked sha, search scope/command, hits and dispositions>
Unresolved preservation: <entries, or none>
Checks not run: <reason and remaining gate, or none>
```

Outcomes are **already present**, **ported**, **superseded** (with replacement evidence and reason), **intentionally dropped** (with the applicable user decision), or **unresolved**. Every relevant change needs an outcome and evidence. Group changes only when their explicit SHAs/hunks and shared disposition remain traceable. An ancestor commit can have been reverted later; inspect the current tree. A manual port can preserve intent without containing the original SHA.

For example, an upstream retry-test rewrite should map to the replacement test's assertions and actual verification result. A corrected dependency comment should map to the adapted comment, not disappear from the inventory because it does not change runtime behavior.

## 5. Verify the current result and report remaining gates

1. Inspect the full diff against the pinned base, not only its stat. Explain residual copied-slice differences with the log.
2. For removed/replaced APIs, search all relevant tracked source, tests and configuration in the resulting tree, including new base callers outside the original file list. For example, with an actual pinned `CUTOVER_SHA`:

   ```bash
   git grep -n -F -e 'LegacyRetryCoordinator' "$CUTOVER_SHA" --
   ```

   Exit 1 means no matches; distinguish it from a search error. Resolve live references and classify intentional documentation, migration fixtures or compatibility uses explicitly. Check generated or dynamic references separately where applicable. A static search alone does not establish runtime correctness.
3. Run focused behavioral checks, lint, build and CI checks as permitted by the project and user. Record actual results, failures and skipped checks; a proposed test is not a passed test. Preserve existing build/push/host-write boundaries.
4. Before a ready-to-land claim, every relevant change must have a supported outcome, no live reference to a removed API may remain unresolved, and required validation gates must pass. Missing provenance, unresolved preservation, or required checks not run remain explicit blockers.
5. Tie the evidence to the checked base and cutover SHAs. If either moves, reconcile the additional changes and repeat affected checks before reusing the readiness conclusion. Retain the historical log and report its location, checked tips, outcomes and blockers before cleanup.
