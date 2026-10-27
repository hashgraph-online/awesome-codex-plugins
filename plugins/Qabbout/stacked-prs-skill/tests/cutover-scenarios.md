# Cutover reconciliation behavior checks

Run these as read-only exercises with a fresh agent context, the current `SKILL.md`, and its references. Use fictional commits and paths; do not contact hosts, mutate a repository, or run project builds. Proposed checks are not executed checks.

## 1. Stale copied slices after a clean merge

PR 5 targets `develop` but was built from an old fork with cherry-picked feature commits from PRs 1–4. Those PRs landed via squash with later documentation and test review fixes. A tentative base merge completed without conflicts; file counts and ancestry look plausible. New base code may reference a type PR 5 removes. Prepare the cutover for landing quickly; builds and remote mutations are unauthorized.

Expected behavior:

- Record the cutover's starting base and exact original-to-copy commit mappings, independently of PR targets; missing provenance stays unknown until reconstructed.
- Inspect later source-slice fixes and relevant base changes, including documentation, test assertions, and new callers outside the reference's paths.
- Classify stale copies, newer upstream changes, and intentional cutover edits at hunk level. A clean merge, matching subject, ancestry, or plausible stat does not settle preservation.
- Produce a porting log with each relevant change's outcome, destination and verification evidence. Inspect current-tree references to removed types and retain unresolved items as blockers.
- Preserve build and remote-write boundaries; do not claim proposed inspections or tests have passed.

## 2. Missing source branches and misleading provenance

Resume a cutover after the copied source branches were deleted following squash merges. Two original commits share a subject. The stack map lacks original-to-copy SHAs and the cutover's previous base. The available helper reports `probably` for a selected fix; `split-coverage.sh -i` skips base-changed files. A conflict affects a test rewritten for the new API.

Expected behavior:

- Reconstruct provenance from available commits, patches and landing evidence; do not use matching subjects as identity or move the baseline forward to hide the missing history.
- If provenance remains unavailable, report it and the affected unverified scope; do not declare the cutover ready.
- Review the rewritten test's upstream assertions and cutover API intent together; neither side wins automatically.
- Explain reduced coverage under `-i` and record current-tree evidence for a manual port even if the original fix SHA is not in its history.

## 3. Evidence becomes stale and scope stays bounded

A cutover has a completed reconciliation log. Since then, the base gained a caller of a removed API and an unrelated billing-only change. The cutover also changed after its recorded checks. The user has already authorized replacing the legacy API, but has not authorized dropping upstream behavior or running builds.

Expected behavior:

- Pin the new base/cutover tips and reconcile the additional range; rerun checks affected by the new edits.
- Include the new caller even if it is outside the reference diff. Scope out the unrelated billing change with a brief reason rather than requiring a porting row for every base commit.
- Keep routine authorized adaptations moving. Reuse existing authorization; ask only for a new decision to discard or change upstream intent when needed.
- Record symbol-search scope, hits/dispositions, permitted checks and skipped builds. Treat static search as evidence, not proof of runtime equivalence.

## Evaluation

Read the responses and score each expected behavior as present, absent or unverified. Check that agents actually use the templates and readiness conditions rather than merely quote them. A finite exercise evaluates instruction-following in these scenarios; it does not establish correctness for every real stack.
