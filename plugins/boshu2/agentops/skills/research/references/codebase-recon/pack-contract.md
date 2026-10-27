# Codebase-recon pack contract

Applies only when a durable `codebase-recon.v1` pack is selected. An inline
investigation may use dirty working-tree evidence with explicit limits; this
commit-bound pack may not. `<skill-dir>` is defined in [SKILL.md](../../SKILL.md).

- Save `codebase-recon.json` and a cited `codebase-recon.md` companion by
  Research's [save rule](../../SKILL.md#output-and-boundaries), outside the
  target repository or under its `.agents/` (a new file elsewhere in it is
  dirty source; `.agents/scratch/` is disposable). Keep mental model, bounded audit,
  pattern evidence and synthesis distinct.
- Bind the exact current full commit OID, at least one complete baseline flow,
  claims with kind, confidence and evidence, and inspected/uninspected scope.
  Fact and inference citations resolve to repository-relative regular files at
  that commit; the companion report includes line references. Unknowns remain
  explicit.
- The manifest `report` names the companion and its lowercase SHA-256. The
  companion has one `<!-- codebase-recon-report.v1 -->` marker and
  `manifest_commit`, `manifest_mode`, `flows_sha256`, `claims_sha256`, and
  `coverage_sha256` markers; section digests hash the `jq -cS` output for each
  section, including its trailing newline.
- Discover validated priors with
  `bash "<skill-dir>/scripts/codebase-recon/validate-output.sh" --repo-root <target> --discover-priors`;
  it scans only `.agents/recon/` and `.agents/scratch/codebase-recon/`, so cite
  a prior saved elsewhere by its path in `prior_recon`.
  Prefer a verified delta when it answers the request. Delta evidence needs a
  valid ancestor chain, `baseline_verified: true` and the exact changed paths
  between the prior and current commits; do not relabel a directory scan as delta.
- Run `bash "<skill-dir>/scripts/codebase-recon/validate-output.sh" --repo-root
  <target> <recon.json>` before handoff. It checks both artifacts and rechecks
  their identities, HEAD and source state; dirty source outside `.agents/` cannot
  satisfy this commit-bound pack. Return a validation failure without disguising
  it as a completed recon pack.

Preserve earlier packs and their exact cited identities; never move or delete
old proof to match a new layout. See the [recon scenarios](codebase-recon.feature).
