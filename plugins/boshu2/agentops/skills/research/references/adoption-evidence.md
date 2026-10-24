# Adoption evidence

Applies to an [adoption question](../SKILL.md#adoption-questions). These are the
facts that most often block or reverse an adoption after it looked settled.
Cover one where it could change the answer, cite it under Research's evidence
rules, and list the ones left unchecked in the answer's unchecked scope.

## Ours

- **Fit.** The runtime, language and peer-dependency versions the candidate
  needs, checked against what this repository actually resolves: lockfile,
  manifests and toolchain.
- **License.** The candidate's license against this project's license and the
  licenses of the dependencies it would sit beside.
- **Cost of staying.** Open issues, workarounds and TODO or FIXME notes at the
  incumbent, each cited where it occurs. This is the evidence for or against
  keeping the current tool.
- **Changes in flight.** An open change, branch or issue that already moves
  the decision. Report it in the answer; it may decide the question.

## Theirs

- **Maintenance.** Release recency and whether maintenance is active, slowing
  or stopped for the version under consideration.
- **Field reports.** Failure and migration reports from projects like this
  one, read against the vendor's own claims. A vendor page speaks for its own
  product; it is not independent support for a decisive claim.
