# Evidence publication

Load this reference when the change is finished and a receipt must be published — inside an active
Superloopy loop always, and standalone when the project keeps a `.superloopy/evidence` root. It carries
the mechanics of publication; the obligation to publish, and the receipt line, live in `SKILL.md`.

Evidence publication coordinates cooperating workers and fails closed on path, identity, durability, and permission races. It is not an operating-system sandbox against a hostile process running as the same user: such a process can retain writable descriptors or change owner permissions, so run mutually untrusted workers under separate OS identities or sandbox boundaries.

## Where the evidence root comes from

Resolve `BACKEND_EVIDENCE_REPORT` at run time. Obtain the active evidence root from the loop's status or guide when a global or scoped Superloopy loop is active; never guess or reuse another session. Outside an active loop, use the project-local global `.superloopy/evidence` root. Use the project root established during discovery as an explicit absolute `<project-root>` so a first standalone run from a non-Git subdirectory cannot create nested state or be promoted to an unrelated enclosing checkout. Choose a portable qualified report id that uniquely names this invocation, such as `goal-<goal-id>-criterion-<criterion-id>-worker-<agent>`; canonical loop ids such as `G001` and `C001` are accepted and normalized to lowercase, and a standalone run uses its timestamped run id. A report id names one attempt: when the same criterion is re-attempted, mint a new id with an attempt suffix such as `-attempt-2` instead of reusing the earlier id, so superseded evidence can never satisfy the new attempt.

## How to publish, and why not to write the path yourself

Pass the completed report on standard input to `node "$BACKEND_SKILL_DIR/scripts/write-evidence-report.mjs" write "<project-root>" "<active-evidence-root>" "<qualified-report-id>"`. The helper stages the report inside a private sibling directory, exclusively opens its staging file without following the output leaf, verifies the opened inode remains confined beneath that project and evidence root, writes and syncs through the verified descriptor, then commits by renaming the complete directory (atomic on POSIX; a fail-closed remove-and-rename pair on Windows) to `.superloopy[/sessions/<session-id>]/evidence/superloopy-backend/<qualified-report-id>/` and prints the published report path. Do not write the target directly or reuse a report id; an existing report fails closed instead of being replaced, while published report files stay read-only inside ordinary writable directories so deliberate cleanup of `.superloopy` keeps working. If the helper cannot run — a copied skill folder without the superloopy core beside it — or fails closed mid-publication — for example a Windows volume without hard-link support — report the missing publication as a blocker or evidence gap; never write the target path directly.

## Recovering a lost receipt

If publication may have succeeded but the receipt was lost, reconcile the same invocation with `node "$BACKEND_SKILL_DIR/scripts/write-evidence-report.mjs" recover "<project-root>" "<active-evidence-root>" "<qualified-report-id>"`; accept its path only after the helper validates the existing confined, non-empty report, and use `recover` only for the invocation whose receipt was lost — a re-attempt publishes under its new attempt id instead.

## Keep the evidence root out of the diff

The evidence root is the loop's state, not part of the work: it must never appear in the change under review. Before handing over, check it against the project's own ignore rules — a repository that does not ignore the evidence root will otherwise carry the report, its local absolute paths and its process commentary into the diff, where it reads as unrelated noise a reviewer will bounce. Keep it out of what you stage rather than deleting the published report. Announce the printed path and end with this exact receipt after replacing the placeholder:

`SUPERLOOPY_EVIDENCE: <BACKEND_EVIDENCE_REPORT>`
