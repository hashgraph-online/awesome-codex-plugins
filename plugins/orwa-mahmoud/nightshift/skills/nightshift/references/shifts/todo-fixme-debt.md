# TODO and FIXME debt — finite — actionable code comments resolved without inventing product decisions

Tracked TODO, FIXME, HACK, and XXX comments in repository-owned source. The shift separates work
that the current code and tests define from comments that require an owner's product decision.

Supported on repositories where these markers live in tracked, human-authored source or tests.
Generated files, vendored code, dependencies, build output, and archived receipts are excluded.
Never select this entry in artifact mode. Do not `git init` a notes folder to make markers commitable.

```text
- [ ] **TODO and FIXME debt — resolve actionable comments and stage ambiguous decisions.**
  - Discovery: search tracked, human-authored source and tests for TODO, FIXME, HACK, and XXX
    markers. Exclude generated, vendored, dependency, build, and archive paths. Dedupe against
    snag-log.md (ALL seen — fixed and rejected), then inventory the marker, path, and nearby
    contract for each finding.
  - Never select this entry when work mode is artifact.
  - Classify each finding before editing. Actionable means existing behaviour, tests, issue links,
    or an explicit comment defines the required result. Ambiguous means product intent, UX,
    compatibility, or scope still needs an owner decision.
  - Resolve one actionable cluster at a time, including the underlying work—not only the comment.
    Run the item gate, commit. Remove or update the marker only when its underlying debt is gone.
  - Stage ambiguous findings in drafting-table.md with the decision needed, evidence, source path,
    and next action. Do not put them in the live punch list and do not guess the answer.
  - Never invent a feature, requirement, or compatibility policy from a vague comment.
  - Never delete or reword a marker merely to make the inventory smaller.
  - Ends when every discovered marker is either resolved with verified underlying work or staged
    in drafting-table.md with a concrete owner decision and source reference.
  - Verify: the item gate is green at every commit; a final scoped search finds no unresolved
    actionable markers and every remaining ambiguous marker has a drafting-table entry.
```
