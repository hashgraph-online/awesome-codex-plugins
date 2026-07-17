---
name: codebase-recon
description: Reconstruct a repository as cited
---
# Codebase Recon

Build a reusable, falsifiable model of a repository. This skill reports what
the tree and executable probes support; it does not edit code or issue a final
PASS/WARN/FAIL verdict.

## Constraints

- To prevent a floating recon, record the exact repository commit and local
  source-of-truth precedence.
- Because confidence is not evidence, type every material claim and cite each
  fact and inference.
- To preserve traceability, prefer a verified delta when a prior pack exists
  instead of rewriting unchanged evidence as fresh discovery.

## Modes, views, and lenses

One skill replaces a cluster of loose recon skills. Steer it with mode, view
emphasis, lens, and depth — do not invent a second skill for each shape.

| Control | Values | Use when |
|---|---|---|
| **Mode** | `baseline` \| `delta` | First pack vs refresh after a prior recon |
| **View emphasis** | mental model · bounded audit · pattern evidence · synthesis | Archaeology-style map, audit-style findings, pattern harvest, or executive synthesis |
| **Lens** | persistence · auth · CLI · build · test (one per pass) | Domain-deep cut instead of a shallow whole-tree sweep |
| **Depth** | quick · standard · deep | Orientation vs onboarding vs decision-grade evidence |

Ask for the shape explicitly, for example:

```text
codebase-recon --mode=delta --view=audit --lens=cli --depth=standard
codebase-recon baseline, mental-model view, persistence lens, deep
```

Natural-language equivalents count. The durable pack still carries all four
views; emphasis changes what you spend tokens on and what the companion report
leads with. Pattern packaging beyond evidence pointers belongs in
[`pattern-mining`](../pattern-mining/SKILL.md). Binding PASS/FAIL stays with
[`validate`](../validate/SKILL.md).

## Workflow

1. Record the current commit and the repository's local source-of-truth
   precedence. Search for a prior recon pack before starting.
2. If no prior pack exists, use `baseline` mode. If one exists, verify its
   still-valid claims against the current commit and use `delta` mode. Preserve
   valid evidence by reference and describe only changed paths and synthesis.
3. Trace representative paths from entry point to domain logic, integration
   boundary, and test. Prefer a few complete flows over a broad file inventory.
4. Keep four views distinct in the report: mental model, bounded audit, pattern
   evidence, and synthesis. Label each claim `fact`, `inference`, or `unknown`,
   assign confidence, and cite evidence for facts and inferences.
5. List inspected and uninspected scope. Write the JSON manifest and companion
   report, then run the validator. Missing evidence and hidden coverage gaps are
   contract failures, not prose caveats.

## Docs-first entry-point tracing

Enter through what the repository declares about itself — README, architecture
docs, build manifests, CLI help — and only then verify those declarations
against the tree. Before the first broad search, list the declared entry points
and trace at least one of them to code. The named failure mode is grep-first
drift: opening with keyword sweeps builds a model of whatever happened to
match, and the recon inherits the search terms' blind spots instead of the
repository's actual shape. When declaration and code disagree, that is a
finding, not noise: record the doc's claim as `inference`, the traced behavior
as `fact`, and cite both.

## One-domain-deep lens per pass

Each pass adopts exactly one lens — persistence, auth, CLI surface, build
system, test harness — and follows it from entry point through domain logic to
its tests before switching lenses. A pass ends in exactly one of two states:
the lens has one complete entry-to-test flow, or the report names the file and
line where the trace was cut and why. The named failure mode is the shallow
sweep: touching every directory at depth one produces a file inventory that
reads like a model but supports no claim, because no path was followed far
enough to falsify anything.

## Citation floor: file:line or downgrade

The durable output doc earns its keep only if a future reader can re-verify a
claim without redoing the recon. Every `fact` cites file:line; every
`inference` cites the file:line facts it rests on. A claim that cannot be
cited is downgraded to `unknown` before the report ships — never shipped
uncited at its original confidence. The manifest validator accepts a bare path,
but hold the companion report to the stricter floor: a path without a line is
a pointer to homework, not a citation, and counts as a coverage gap in the
report's own terms.

## Output Specification

- **Artifact directory:** `.agents/recon/<run-id>/`
- **Filename convention:** `codebase-recon.json` with companion report
  `codebase-recon.md` in the same directory.
- **Format:** `codebase-recon.v1` JSON manifest plus an evidence-cited Markdown
  report covering the same commit, mode, flows, claims, and scope boundaries.
- **Validation command:** `skills/codebase-recon/scripts/validate-output.sh <codebase-recon.json>`
  validates the machine-readable manifest; the cited Markdown report remains
  its human-readable companion.
- **Downstream handoff:** pass both validated artifact paths to the requesting
  research, planning, review, or documentation workflow; the consumer owns any
  decision or code-change plan.

Baseline manifests carry at least one complete entry-to-test flow. Delta
manifests name an existing prior recon, prove `baseline_verified: true`, and
describe at least one changed path. Every manifest lists both inspected and
uninspected scope.

The validator is the machine boundary:

```bash
skills/codebase-recon/scripts/validate-output.sh <recon.json>
```

Evidence entries are existing file paths, optionally followed by a line number.
Delta manifests require an existing prior pack, `baseline_verified: true`, and
at least one described change.

Executable behavior:
[references/codebase-recon.feature](references/codebase-recon.feature).

## Quality

- Every fact and inference resolves to existing evidence; unknowns remain
  visibly typed and never masquerade as established behavior.
- Representative flows reach entry, domain, integration, and test surfaces,
  while inspected and uninspected scope stay explicit.
- The named validator passes before the JSON manifest and companion report are
  handed to a downstream consumer.

## Do not

- Regenerate a full replacement report when a verified delta is possible.
- Present an inference as fact or omit uninspected scope.
- Turn the recon artifact into a completion verdict or a code-change plan.
