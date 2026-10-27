# PR titles and descriptions for slices

If the repo has a PR template or a required description layout, use it. Put the stacked-PR notes below inside its sections instead of adding new top-level sections.

## Title

`<type>(<area>): <ID> [k/N] <what this slice does>`, adapted to the repo's title style.

For example: `feat(cart): ABC-12 [4/7] add the cart integration layer, not yet wired`.

If N changes, update every title (with approval). When the stack changes shape, `changes.md` lists the lines that go stale.

## What every slice description says

1. **Position:** "Part k of N of splitting #<ref>", with a link to the reference PR.
2. **What changes, in plain words,** and whether behavior changes.
3. **Stacked-PR note** (for any slice that doesn't target the base): what it targets, what that target contains, that it will be retargeted to the base once those merge, and "Don't merge it before them."
4. **Bulleted changes,** with code identifiers.
5. **Not in this PR:** what a reviewer might look for but will find in a later slice ("Wiring: call sites → PR 5").
6. **Tests:** new and moved tests.
7. **What to test:** CI expectations first, then manual checks.
8. **Local checks:** what was actually run ("No local build was run; CI is the compile gate."). Never claim a build that didn't run.

## Extra notes by slice type

**First slice:** add **Why this is safe to merge** (evidence such as "no callers of the changed APIs on the base"), the **Slice plan** as a numbered list with "This PR" in bold, and "#<ref> stays open, unchanged, as the reference branch."

**Cutover built from the fork point:** add **How this branch is built (read first)**:
- It's based on the fork point (`<sha>`), not on the current base, and carries PRs 1–k as their own commits.
- Link or summarize the copied-dependency map: starting base, source tips, original-to-copy SHAs, and the boundary before the cutover's own edits. Publishing the full local record requires authorization.
- **Identify the cutover's own commits:** initially `<after-copies>..<initial-cutover-tip>`. After base merges, that range to the current tip also includes upstream commits: identify cutover/port commits explicitly and review the full current target diff with the porting log. Merging the landed base can reduce duplicate content, but later fixes and ports require reconciliation; do not promise that copied changes simply disappear.
- Content equals the reference's except <planned differences and reconciled upstream changes>.

Then list **Behavior changes**, **Expected conflicts with <base>** (the file list from splitting step 2, plus the base's new files that use removed code), **Decision pending**, and **Open questions**. Mark What to test "(after conflicts are resolved)".

Before landing, draft a **Reconciliation** summary from `reconciliation.md`: checked source/base/cutover SHAs, map/log location or an authorized summary, relevant change outcomes, removed-API reference checks, and unresolved items or skipped validation. Refresh it when those tips move. A clean merge alone is not evidence that upstream changes were preserved.

**Review follow-up slice:** "the follow-up to <reviewer>'s review of #<pr>", then **Cause**, **Fix**, an optional "What stays the same", and **Tests**.

## Writing rules

- Keep the opening paragraph plain; put code identifiers in the bullets.
- Link every PR you mention.
- Never mention AI tools, and never add generated-by footers or co-author trailers.
