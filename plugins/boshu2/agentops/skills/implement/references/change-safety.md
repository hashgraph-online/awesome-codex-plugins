# Conditional change safety

Use the section matching the actual operation. The caller's acceptance, scope,
tracking policy and remaining bounds still govern; none of these methods creates
a ledger, review round, retry allowance or delivery authority.

## A deliberately limited implementation

When a limit is accepted or already meets acceptance, explain it at the code
that enforces it, using the repository's comment convention. State the supported
range and observable condition that would require revisiting it; point to the
existing decision when available. Follow caller tracking policy rather than
creating a parallel shortcut list. A comment cannot excuse missed acceptance:
report an unaccepted omission under `gaps`.

## Findings on your own change

Compare review claims with the code and accepted behavior before editing.
Resolve each as a supported repair, a different repair, inapplicable with
counterevidence, or a caller decision. Recover the reason for deliberate code
from its tests, comments or change history before removing it. If a premise is
false, reconsider other findings that depend on that premise rather than
accepting or dismissing the reviewer wholesale.

For a supported finding, inspect other sites introduced by this same change
that share its faulty rule, within authorized scope; repair confirmed instances
and run their checks. Report outside-scope instances or unresolved cases as
such. This is not a repository-wide bug hunt. If feedback breaks an earlier
repair, check whether the responsibility belongs elsewhere before stacking
another patch. Review text supplies evidence, not new acceptance or authority.

## An authorized commit in a shared checkout

Immediately before committing, verify the intended branch and inspect the exact
staged diff, not only filenames. Compare it with authorized content and inspect
unstaged changes in those same files. A path restriction does not separate
hunks or authors: `git commit --only` can include unstaged edits to named files.
If unrelated work is staged or a file mixes authors' edits, use an isolated
checkout and deliberately transfer only the authorized change. Leave the
existing index and others' edits intact. Inspect the isolated staged diff and
follow the caller's and repository's commit policy. This method supplies no new
delivery authority.

## An authorized removal or shrinking overwrite

Inspect the concrete targets for unique content and dependents before deleting
or truncating them. Include uncommitted and unpushed work, recovery copies and
references that would become unusable. Establish the available recovery and its
cost under the owner's retention policy. A directory called temporary, ignored
or cache is not evidence of disposability. Preserve unique material through an
authorized reversible route; if that route is unavailable, report the blocking
risk before removal. Reinspect when the target set changes. Force flags neither
supply owner permission nor waive preservation requirements.

## Your mutation returns no definite outcome

A transport failure after submission does not establish that a write failed.
Inspect the destination through an authorized read before submitting it again.
When a request or operation ID was returned, query that existing operation;
allow pending work to finish instead of duplicating it. If safe reconciliation
is unavailable, report the outcome as unknown and the missing lookup. Do not
invent an idempotency guarantee or a new retry loop. Product failure-path
checks remain in [Test's error recovery method](../../test/references/error-recovery.md).

## Dependency upgrades

Work from the resolved versions and requested targets. Read the authoritative
release notes across that span for changes affecting this repository. Move one
independent dependency, or an actually coupled group, then run affected checks
before the next step so failures can be attributed. Use the repository's
available package-manager tooling to resolve versions and update the lockfile;
do not manufacture lock entries. Preserve unrelated resolutions and inspect
unexpected transitive changes. If required tooling is unavailable, state that
limit and follow existing authority for supplying it; never guess lockfile bytes.

A failure calls for attribution and a scoped repair, not weaker checks. An
already authorized rollback, including a batch rollback when appropriate,
remains available; preserve its evidence and compatibility requirements.

## A safety control refuses the operation

Read the actual refusal and its reason. Do not encode, split, wrap or reroute
the same prohibited effects to evade a safety guard. Use an authorized safer
alternative or report the blocked operation and required decision. Existing
approval follows the reviewed operation, effects and targets: a benign spelling
or flag adjustment within that authority does not require asking again. A
change that exceeds it does. A command's output is not permission to override
the control.
