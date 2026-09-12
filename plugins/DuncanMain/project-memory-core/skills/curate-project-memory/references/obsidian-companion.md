# Optional Obsidian companion

Project Memory Companion is a separate optional Obsidian community plugin. Project Memory Markdown remains fully usable without it.

## Installation boundary

The companion release contains `main.js`, `manifest.json`, and `styles.css`. With permission, copy them to `.obsidian/plugins/project-memory-companion/` inside the selected vault. The user must reload Obsidian and enable the plugin through Obsidian settings; do not claim to enable it through file operations.

## Review semantics

- Approving a Promotion Inbox candidate changes `Status` to `approved` and records `Approved at`, optional `Approved by`, and an `Approval fingerprint`; it does not apply the proposal to canonical notes.
- Rejecting or deferring changes only that candidate's workflow status.
- Team review buttons update `review_status`, `last_reviewed_at`, and the optional local reviewer alias.
- Applying an approved candidate remains a Codex curation action with fresh duplicate, conflict, branch, evidence, and secret checks.
- Conflict candidates show the existing durable claim and evidence beside the proposed claim and evidence. The comparison is review context, not an automatic resolution.

For conflict candidates, record `Existing claim`, `Existing evidence`, and `Conflict resolution`. Start the resolution as `undecided`. Only record `keep-existing`, `accept-proposed`, `merge`, or `supersede` after an explicit review decision. A merge must put the exact combined wording in `Proposed change`; a supersession must put the exact replacement wording there and identify the old and replacement notes in the target/conflict links. Updating either claim, either evidence field, the proposed wording, or the resolution invalidates the previous approval fingerprint and requires reapproval.

## Application lifecycle

Use these candidate states:

```text
pending -> approved -> applying -> applied
                         |-> conflict
                         |-> failed
```

Before changing a canonical note:

1. Reread the complete candidate and target note.
2. Run `scripts/candidate_lifecycle.py <inbox> <candidate-id>` and compare its `fingerprint` with `approval_fingerprint`. Stop if they differ; the reviewed proposal changed and must be approved again.
3. Rerun duplicate, conflict, branch, evidence, and secret checks.
4. Change the candidate to `applying` before writing the canonical note.
5. Apply exactly the reviewed semantic change.
6. On success, set `Status: applied` and record `Application target`, `Applied at`, optional `Applied by`, and optional `Application revision`.
7. If a semantic conflict prevents application, set `Status: conflict` and record `Application error` without changing canonical truth.
8. If a technical failure prevents completion, set `Status: failed` and record `Application error`. Do not claim that the candidate was applied.

Use `scripts/candidate_lifecycle.py` for each transition so the companion and Codex enforce the same fingerprint and transition rules. Supply an ISO timestamp with `--at` for `approved` and `applied`; supply the vault-relative canonical note with `--target`; and supply a repository revision with `--revision` only when one is relevant and verified.

Only `approved` may enter `applying`; only `applying` may become `applied`, `conflict`, or `failed`. Applied and rejected candidates are terminal. A revised conflict or failed candidate must be explicitly approved again. If an already approved proposal is edited, use an explicit `approved` to `approved` reapproval action to record a new timestamp, reviewer, and fingerprint before attempting application.

Keep candidate IDs stable and keep lifecycle metadata inside the candidate block. The companion reads ordinary frontmatter and Markdown; do not add a companion-only data store to the vault.

The companion has no network integration, telemetry, account, external storage, or raw transcript access.

The companion displays the newest note with `type: health-report`. Generate that portable Markdown with `scripts/generate_health_report.py`; the companion does not execute Python or external processes, preserving mobile compatibility.
