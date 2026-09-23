# Detached Frozen Planning — Operations

Use only with `--implementation-root`. This mode preserves an admitted planning
tree and records implementation evidence externally. Mutable-mode shortcuts do
not apply. Let Forge enforce schemas, hashes, identity checks, locks, and recovery;
never repair its state by hand.

## Authority and setup

Require operator-approved admission/source hashes, not hashes invented to bypass
a mismatch. Planning, target, and implementation roots must be pairwise disjoint,
including ancestor, case, and mount aliases. The admission pinner is a pre-existing
external canonical JSON regular single-link file, mode `0600`. The implementation
root is user-owned `0700`; Forge creates only its fixed directories/config/state.

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-setup \
  --sections-dir "{sections_dir}" --target-dir "{target_dir}" \
  --implementation-root "{implementation_root}" \
  --admission-pinner "{admission_pinner}" \
  --expected-admission-pinner-sha256 "{approved_admission_hash}" \
  --expected-implement-tool-sha256 "{approved_tool_hash}" \
  --expected-implement-skill-sha256 "{approved_skill_hash}" \
  --expected-implement-test-sha256 "{approved_test_hash}"
```

The source hashes bind complete `scripts/zagrosi_skills.py`,
`skills/zagrosi-implement/SKILL.md`, and `tests/test_zagrosi_skills.py` bytes.
The tool also authenticates this operational reference. Setup authenticates the
admission pinner and complete planning tree before creating state; it writes
neither planning nor target roots. Require successful preflight; resolve target
branch/dirty-work conflicts before implementation.

Existing roots cannot be silently upgraded after source, admission, or target
changes. Use a newly admitted setup with reviewed hashes. A completed config is
immutable; replay requires identical authorities and config bytes.

## Non-negotiable boundaries

- Keep the admitted planning tree unchanged: no packets, skeletons, reviews,
  evidence, usage, traceability, or section edits there. Generated outputs use
  fixed external directories only. Detached packet/skeleton commands require an
  explicit `--output-dir` beneath `{implementation_root}/code_review/`.
- Forge owns exactly `code_review/`, `evidence/`, `pinners/`,
  `zagrosi_implement_config.json`, `zagrosi_implement_state.json`, and
  `forge-progress.json`. Unknown members fail closed; do not delete them to force
  admission. JSON/evidence/pinners are canonical, `0600`, regular, and single-link;
  paths must not contain symlinks.
- Forge reopens authorities before/after mutations and holds the fixed `/` and
  implementation-root locks throughout recovery and completion. Unsupported
  locks, contention, drift, or ambiguous recovery fail closed. Never bypass locks,
  edit journals/pinners, rewrite state, or manually clear pending transactions.
- Successful records report `committed-clean` or `committed-cleanup-pending`.
  Let the next supported command recover pending cleanup; preserve ambiguous
  evidence. Do not infer rollback from leftover files after a committed result.
- The protocol's privileged closure is Darwin/APFS on one shared host/mount
  namespace. Do not substitute executables, platforms, or weaker verification.

## Ready-section loop

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py next-section --planning-dir "{planning_dir}" --implementation-root "{implementation_root}"
```

Implement only returned dependency-ready sections. Use targeted TDD, focused
review, and disjoint ownership for parallel work; serialize recording. Scope or
contract changes require a newly admitted plan, not an edit to frozen inputs.
Never re-record a predecessor pinned by completed dependants; new final hashes
require a new root/state and dependency-ordered replay.

Write both external records even for a clean review:

```text
code_review/{section}-review.md
code_review/{section}-decisions.md
```

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-record-section \
  --sections-dir "{sections_dir}" --implementation-root "{implementation_root}" \
  --section "{section}" --commit "{hash_or_none}" \
  --file "{changed_file}" --test-file "{test_file}" \
  --review-artifact "code_review/{section}-review.md" \
  --review-artifact "code_review/{section}-decisions.md" \
  --verification "{targeted_test_or_gate_command}"
```

Repeat file/review/verification flags as applicable. Nonreserved evidence uses
`--evidence-row "{name}=evidence/{result}.json"`; each unique lower-snake-case name
binds canonical file bytes. The section-owned verifier must validate their meaning.
Never supply reserved S26/S28 rows; Forge derives them.

## Privileged S26/S28 handoff

Only this public command obtains reserved evidence:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-evidence-handoff --implementation-root "{implementation_root}" --section S26
```

Use exact `S26` or `S28`; aliases, extra arguments, missing selectors, and
`--pretty` silently exit 2. Require a non-root Darwin arm64 caller and a ready
section. Forge uses fixed trusted runners, pinned dependencies, clean protected
source, bounded process groups, and signature verification. Never copy/chown raw
root results, invoke repository code as root, replace runners, or retry a failed
privileged child. Exit 3 means unavailable; exit 5 means refused/invalid/conflicting
authority or evidence. Diagnose the closed error without weakening checks.

Success is create-once `created`/`reopened`; an authorized rerun accepts only
identical evidence. Handoff alone does not record section completion.

## Completion and protocol diagnosis

Run the full configured test command once, then `next-section` with
`--implementation-root`. Require no remaining/next section, unchanged
planning/admission/source identities, and successful reopening of every pinner.
Do not run planning-local writers.

Only when diagnosing or extending protocol mechanics, read
[the complete protocol](detached-protocol.md). Before reading, require a no-follow
regular single-link file with complete-file SHA-256
`63fab2d082629bce818e96ab43b7c2b60cd23c670c2e1f41979308786e87ecf8`.
It preserves exact schemas, digest domains, transaction states, publication/
rollback ordering, host checks, and closed errors; those invariants still apply.
