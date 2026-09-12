# Plan review

Find material failures: missed/conflicting requirements; unclear file, data, or
test ownership; unsafe security, migration, compatibility, concurrency, retry,
or rollback; untestable behavior; cycles, collisions, invalid parallelism; and
release/recovery gaps.

Write one `reviews/codex.md` with findings (`severity: problem -> fix`), applied
plan edits, and residual risk with owner or accepted boundary. `Verdict: pass.`
is enough. Apply accepted fixes to the plan. Merge optional external or
delegated review here unless the user requests separate records.
