# Drift detection — code/cascade/temporal staleness

Detection protocol for `/archcore:audit --drift`. Cross-references code changes, the relation graph, and document statuses. Produces an actionable report and offers assisted fixes.

## Step 1: Gather data

Call in parallel:
- `mcp__archcore__list_documents` (apply filter from `$ARGUMENTS` if provided: tag, category, or type)
- `mcp__archcore__list_relations`

Then use `Bash` to gather git context:
- `git log -1 --format=%H -- .archcore/` — last doc commit
- `git log --oneline -20` — recent code activity
- `git diff --stat <last_doc_commit>..HEAD -- ':(exclude).archcore/'` — changed files since last doc update

If git is unavailable, skip code-drift analysis and proceed with cascade + temporal only.

## Step 2: Analyze — Code→Doc Drift

For each document in scope:

1. Read document content via `mcp__archcore__get_document`
2. Extract file and directory references from the content (paths like `src/`, `lib/`, function names, module names)
3. Cross-reference with git changes: check if referenced paths appear in `git diff --name-only` since the document was last modified
4. If referenced paths changed → flag as **critical** with the specific changed files

Score: **Critical** — code changed but document still describes the old behavior.

## Step 3: Analyze — Doc→Doc Cascade

For each document in scope:

1. From the relation graph, find documents where this document is the **target** of `implements`, `depends_on`, or `extends`
2. For each such source document: compare git modification dates
   - `git log -1 --format=%aI -- .archcore/<source>` vs `git log -1 --format=%aI -- .archcore/<target>`
3. If the target (this doc) was modified **after** the source → the source may be stale (it implements/depends-on something that changed after it was last updated)

Score: **Cascade** — relation graph indicates the document's upstream changed.

## Step 4: Analyze — Temporal Staleness

Check for:
- Documents in `draft` status where `git log` shows last modification > 30 days ago
- Documents in `accepted` status with TODO, FIXME, or TBD markers in content
- Plans with phase descriptions referencing past dates
- Documents with `rejected` status that are still **targets** of active `implements` or `depends_on` relations

Score: **Temporal** — age or status anomaly.

## Step 5: Report

Present findings grouped by severity:

```
## Drift Report

### Critical (code drift with evidence)
- {doc-path}: references {src/path} — {N} files changed since doc was last updated
  Changed: {file1}, {file2}, ...

### Cascade (relation graph indicates staleness)
- {doc-path}: implements "{target-title}" which was updated on {date}
  Last modified: {date} — {N} days before upstream changed

### Temporal
- {doc-path}: draft for {N} days — consider accepting or removing
- {doc-path}: accepted but contains {N} TODO markers

### Summary
{N} documents analyzed, {M} findings ({X} critical, {Y} cascade, {Z} temporal)
```

If no findings: "All documents appear current. No staleness detected."

## Step 6: Assisted fix (interactive)

After presenting the report, offer to fix findings one at a time:

For **critical** (code drift):
- "Want me to read the current code and update this document to match?"
- Use `mcp__archcore__get_document` to read, then `mcp__archcore__update_document` with revised content

For **cascade**:
- "Want me to review {source} against the updated {target} and reconcile?"
- Read both documents, identify discrepancies, propose update

For **temporal**:
- "Change status from draft to accepted?" or "Remove TODO markers?"
- Use `mcp__archcore__update_document` for status or content changes

Always confirm each fix with the user before applying. One document at a time.
