# Suede AI Ship Copy Skills: Worked Handoff

## Inputs

Request: “Research and draft this launch page.” Required `piece` preserves that
brief verbatim; `surface` is `landing page`. Supply product source paths, live
URL if one exists, audience, protected product-name strings, word budget, and
facts explicitly supplied by the requester in `given`. Choose a draft-only
`outDir`, such as `.suede-copy/launch/`. Obtain the documented agent-budget
choice before launching; do not interpret this exercise as a funded run.

## Expected output

Read `claim-origin-policy.md` and `phase-and-threshold-reference.md`, then invoke
the bundled workflow through an available compatible host. The returned handoff
leads with `copyVerdict` and deliverable path, then stalled sections, open author
placeholders, dropped/narrowed agent claims, given claims, out-of-scope findings,
confirmed findings, mechanical checks, cleanup score, and unread evidence.
Requester-supplied facts stay intact. A research agent's unsupported “twice as
fast” claim is removed; a missing source becomes `[AUTHOR: supply X]`, not a
plausible substitute. Preserve every protected string exactly.

## Failure case

`outDir` points to the published README: report the path hazard and offer a draft
location. A section-map collision requires replanning rather than repeating the
same launch. A host without `Workflow`, phase support, or subagents cannot run
this graph: return an explicit orchestration blocker and a handoff to a supported
host; never claim the workflow completed or silently substitute a single pass.

## Validation

Check actual output files and returned evidence before describing a completed
run. Confirm placeholders and stalled sections are reported, the claimant origin
policy was applied at every phase, and no draft is called published, sent, or
live. Compare the runtime's reported counts and verdict with the retained output;
do not copy the illustrative agent counts as a claim about an unexecuted run.
