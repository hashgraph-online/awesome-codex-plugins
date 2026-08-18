---
name: codebase-recon
description: 'Reconstruct a repository as cited Triggers: "codebase recon", "trace this codebase", "repository audit", "refresh the prior recon".'
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
   precedence. Search for validated prior manifests before starting with
   `skills/codebase-recon/scripts/validate-output.sh --repo-root <target> --discover-priors`.
   Successful empty output means no prior pack exists at either documented
   default.
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
uncited at its original confidence. The manifest validator checks citations
against the exact Git commit declared by that manifest. They must be safe
repository-relative regular-file paths; artifact-local and external paths are
rejected because this schema has no digest field for those bytes. A supplied
line number must exist in the committed blob. The validator also resolves each
representative flow path at that commit. It does not require every citation to
carry a line number; hold the companion report to the stricter floor: a path
without a line is a pointer to homework, not a citation, and counts as a
coverage gap in the report's own terms.

When reconstructing a repository other than the one that ships this skill, pass
`--repo-root <target>` to the validator so evidence resolves against the target
tree rather than the skill's own checkout.

## Output Specification

- **Artifact directory:** the caller-selected output path, defaulting to `.agents/scratch/codebase-recon/<run-id>/`
- **Filename convention:** `codebase-recon.json` with companion report
  `codebase-recon.md` in the same directory.
- **Format:** `codebase-recon.v1` JSON manifest plus an evidence-cited Markdown
  report covering the same commit, mode, flows, claims, and scope boundaries.
  The manifest's `report` object names `codebase-recon.md` and binds its
  lowercase SHA-256. The report carries one
  `<!-- codebase-recon-report.v1 -->` marker plus `manifest_commit`,
  `manifest_mode`, `flows_sha256`, `claims_sha256`, and `coverage_sha256`
  markers computed from canonical compact sorted JSON for those sections.
- **Validation command:** `skills/codebase-recon/scripts/validate-output.sh <codebase-recon.json>`
  snapshots and validates both artifacts, then rechecks their identities and
  the repository HEAD/index/worktree before returning.
- **Downstream handoff:** pass both validated artifact paths to the requesting
  research, planning, review, or documentation workflow; the consumer owns any
  decision or code-change plan.

### Earlier default compatibility

Packs already stored under `.agents/recon/<run-id>/` remain in place. The
validator's `--discover-priors` mode enumerates validated
`codebase-recon.json` manifests under both that legacy root and the current
scratch root. Record the selected manifest's exact path in `prior_recon`; delta
validation re-validates the cited manifest and its prior chain instead of
accepting a path merely because it exists. New packs use the current default
unless the caller supplies a different path. Never move, copy, or delete an
earlier pack merely to make its directory match the new state tier, because
that would obscure the identity a delta cites. Downstream consumers use the
exact returned artifact paths rather than scanning only one default root. An
earlier pack without a digest-bound companion report remains untouched but is
not returned as validated prior evidence under the current contract.

Baseline manifests carry at least one complete entry-to-test flow. A manifest
being handed off must name the target repository's current `HEAD` by its full
object-format OID; abbreviations and hex-looking refs are rejected. Historical
manifests cited as priors must likewise carry full immutable commit OIDs that
resolve in that repository.
Delta manifests name an existing prior recon, set `baseline_verified: true`,
and list exactly the paths in Git's prior-commit-to-current-commit diff. The
validator derives those facts rather than trusting the boolean or path list.
It also refuses dirty tracked, staged, or untracked source state outside
`.agents/`, because those bytes are not bound by the declared commit. Every
manifest lists both inspected and uninspected scope. Manifests and companions
must be real regular files, are read from one snapshot, and are rechecked along
with HEAD and source status after validation so a mid-run swap cannot earn a
green result for different bytes.

The validator is the machine boundary:

```bash
skills/codebase-recon/scripts/validate-output.sh <recon.json>
```

Evidence entries are repository-relative files at the manifest's commit,
optionally followed by a line number.
Delta manifests require a valid prior `codebase-recon.json` chain, an ancestor
commit, `baseline_verified: true`, and an exact changed-path match to the Git
diff ending at current `HEAD`. Enumerate validated manifests at both documented
defaults with:

```bash
skills/codebase-recon/scripts/validate-output.sh --repo-root <target> --discover-priors
```

Executable behavior:
[references/codebase-recon.feature](references/codebase-recon.feature).

## Quality

- Every fact and inference resolves to evidence in the manifest's exact commit;
  unknowns remain visibly typed and never masquerade as established behavior.
- Representative flows reach entry, domain, integration, and test surfaces,
  while inspected and uninspected scope stay explicit.
- The named validator passes before the JSON manifest and companion report are
  handed to a downstream consumer.

## Do not

- Regenerate a full replacement report when a verified delta is possible.
- Present an inference as fact or omit uninspected scope.
- Turn the recon artifact into a completion verdict or a code-change plan.
