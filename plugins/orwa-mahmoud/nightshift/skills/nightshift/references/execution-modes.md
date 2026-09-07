# Selection and launch modes

Hunt and Quality use two independent choices. Never infer one from the other.

## Selection

- **Guided** — the owner chooses one or more catalog entries, then may add scope or approach.
- **Automatic** — the owner supplies a time budget; inspect the work target and choose the
  applicable catalog entries that offer the strongest evidenced user value in that time.

Automatic selection is not a generic brainstorm. Read every entry in `shifts/`, then inspect the
work target. In repository mode that is tooling, tests, documentation, issue references available
in the workspace, and recent git history. In artifact mode that is the persistent folder's files
and any existing source manifests or reports; do not require a git history that cannot exist.
Refuse to compose, cut, or arm when `$NS/receipts` exists but is not a usable directory.
If `$NS/work-mode` is missing and Setup would propose artifact, refuse to compose, cut, or arm and send the owner to Setup; do not `git init` a notes folder.
Refuse to compose, cut, or arm when work-mode is malformed.
Refuse to compose, cut, or arm when the work target cannot be resolved.
An entry is applicable only when the work target can supply its discovery surface. Skip coverage,
CI, dependency, and similar quality-debt entries when the folder has no tests, tooling, or
manifests to inspect. Skip the GitHub issue hunt when work mode is artifact or no proposed
imports exist. Skip the defect hunt when work mode is artifact.
Skip documentation drift when work mode is artifact.
Skip TODO and FIXME debt when work mode is artifact.
Skip coverage hunt when work mode is artifact.
Skip tooling quality-debt entries when work mode is artifact.
Do not `git init` a notes folder to make them applicable.
For each applicable entry record one sentence of evidence. Rank by:

1. user or production impact;
2. strength of work-target evidence;
3. ability to finish and verify inside the remaining time;
4. risk and reversibility.

Remove overlaps: one finding belongs to one entry. Run finite entries first. If useful time remains,
choose at most one open-ended entry to use it.
One deadline governs the whole automatic shift, and automatic mode always requires hours.

## Launch

- **Review first** — discovery is read-only. Show the evidence, selected entries, order, scope,
  endings, and hours. Write and arm nothing until the owner approves. The clock starts only after
  that approval.
- **Run directly** — the owner's choice is explicit authority to discover, select, implement, and
  verify within the stated scope and time. Start the clock immediately, assemble and cut one work
  order, arm one shift, and continue selecting applicable work until quitting time.

Guided + run directly still performs the selected entry's discovery, but it does not pause after
showing the findings. Guided + review first does pause. Choosing a category is not by itself approval
to implement; the launch choice decides that.

## Direct-mode decisions

Run directly means make progress, not avoid judgment:

- choose the strongest production-quality default;
- make reasonable, reversible decisions on the isolated branch or inside the artifact work target;
- preserve compatibility or include migration and rollback where a breaking change is justified;
- implement and verify the decision;
- record every significant choice, evidence, alternatives, shipped result, and rollback in
  `parking-lot.md`; then continue.

Stop for the owner only when the action is outside the granted coding-work boundary: publishing,
merging, deploying, deleting production data, exposing secrets, spending money, or changing legal or licensing policy.
A difficult or potentially breaking code change is not automatically outside the
boundary when it is isolated, tested, reviewable, and reversible.

## One shift contract

Any combination becomes one ordered work order, one punch list, one branch or artifact work target, one deadline where
required, and one set of receipts. In repository mode those receipts are work-target commits. In artifact mode they are files under `.nightshift/receipts/`. Never arm a separate shift per entry. The catalog entry remains
the definition of done; selection and launch modes decide who chooses it and whether discovery
pauses for approval.

A GitHub issue hunt cannot grow past the imported `Status: proposed` set the owner already
staged. Direct mode may rank inside that set; it must not search GitHub or add issues that were
not imported.
