# Preserve existing behavior

For ordinary mutable workflows in either host, at every depth. The pinned
detached protocol is unchanged. Depth changes investigated risks, not whether
promised behavior receives real checks.

## Declare once

Read the original request, source, callers and tests. In the existing section
Contract, separate behavior to preserve from intended changes. Use `required`
for meaningful refactors or changes to existing interfaces, errors, ordering,
state and side effects. Reuse adequate tests; add characterization only for gaps.
For full compatibility, cover public names/signatures and re-exports as well as
results, errors and caller behavior. Tests must exercise contracts, not private
structure or the planned replacement.

Each new mutable section includes this heading and one fenced JSON object:

## Compatibility

```json
{
  "version": 1,
  "mode": "required",
  "source_paths": ["src/labels.py"],
  "check_paths": ["tests/test_labels_compatibility.py"],
  "check_provenance": {"source": "existing", "author": "Repository maintainers"}
}
```

Paths are target-relative. Select affected source/caller dependencies and all
check helpers/fixtures needed to protect the stated behavior. Keep source and
check roots disjoint, including aliases and hard links. Regular files and
directories are supported; selected symlinks and special files are rejected.
Source paths must exist at activation; checks may be added afterward, before
baseline capture. Explicit ignored check directories are supported. Replace the
example with inspected facts.
Recursive scans omit known generated/dependency directories (`.git`, `.venv`,
`venv`, `node_modules`, `__pycache__` and tool caches); explicitly selected regular
inputs remain bound. Environment and dependencies beyond declared inputs are not pinned.

Docs, formatting and isolated new behavior without an existing contract to
preserve can use `{"version": 1, "mode": "not_required", "reason": "Only corrects README links; no executable behavior changes."}`
in the same fenced block. Give the actual reason; this is not captured compatibility.
Ordinary verification still applies. Existing undeclared plans remain legacy and
cannot claim a captured before/after pair.

## Derive checks honestly

When delegation is available, have another agent derive missing preservation
checks from original source/callers before seeing replacement code. Record the
actual author and `check_provenance.source`: `existing`, `independent`, `writer`
or `external`. Use `independent` only for separately derived checks; reviewing
writer-authored checks or switching providers does not make them independent.
If delegation is unavailable, derive the checks yourself and say `writer`.
External reviews remain optional under existing authorization. Never add a
provider requirement, routine interview or reviewer quorum.

Authorship is an attestation. Capture binds the executed command, its outcome and
declared inputs. Review must establish that the command exercises those checks;
capture cannot prove independence, sufficient coverage or complete correctness.
Receipts are editable local records, not an authenticated or undeletable history.

## Capture and replay

Before source edits, activate the ready section with the usual `implement-setup`
arguments plus `--section "{section}"`. Without a selector, setup activates the
next section. Activation records original source once, including current user
changes. `status` and `next-section` only return actions; they do not activate it.

Capture passing preservation checks before refactoring:

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" implement-verify --planning-dir "{planning_dir}" --target-dir "{target_dir}" --section "{section}" --stage baseline -- <command argv>
```

After the change, run the same command and unchanged checks with `--stage candidate`.
Keep checks, helpers, fixtures and their command unchanged across the pair; compare
asserted behavior, not incidental stdout or timing. The candidate source may change.
Select preservation tests explicitly; keep new feature tests separate so discovery
does not silently expand the replayed suite.
Required pairs are enforced at completion; a baseline alone cannot close work.
Capture ordinary feature checks and final integration using `implement-verify`
without `--stage`, as described in [Implement](../SKILL.md).

Repair failed preservation checks before completion. A bug fix has separate
red/green tests for intended changes; do not preserve the bug merely to match a
baseline. Retain pre-existing failures separately. If checks need correction,
establish a fresh baseline against the unchanged original source before retrying
the candidate. Never reset user work or rebaseline changed code to manufacture a
pass. Origin does not refresh automatically. If the original source is unavailable,
report the missing evidence; do not claim compatibility or substitute an attestation.
Retain original receipts and failed attempts; never delete or rewrite state to
clear a mismatch.

Use the existing section evidence, verification receipts and review. Summarize
protected contracts, actual outcomes and remaining gaps; add no parallel ledger.
