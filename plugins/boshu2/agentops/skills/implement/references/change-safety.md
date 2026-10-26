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

Compare review claims with the code and accepted behavior before editing. If
the code moved since the review, locate the concern again in the current code
rather than acting at the old line or quote. Resolve each as a supported
repair, a different repair (sometimes removing the mechanism the finding is
about), inapplicable with counterevidence, unverified when you cannot confirm
its premise, or a caller decision. Recover the reason for deliberate code
from its tests, comments or change history before removing it. If a premise is
false, reconsider other findings that depend on that premise rather than
accepting or dismissing the reviewer wholesale. A binding finding you dispute
stays visible to its judge with your evidence.

For a supported finding, or a defect of this change you found yourself, inspect
other sites this same change introduced or touched that share its faulty rule,
within authorized scope. Repair those that take the same fix without
site-specific judgment and check the rule at each one; report sites whose
correct treatment differs, outside-scope instances or unresolved cases as such.
This is not a repository-wide bug hunt, though a targeted search for the same
root-cause pattern is in bounds: repair matches inside accepted scope that take
the same fix without site-specific judgment, checking each; report the rest
like an uncovered consumer. Where the pattern recurs, propose removing
the way to write it (one helper that does the step correctly, a type that
cannot hold the bad state, or a check that fails if it returns) as a separate
change after the minimal repair passes, limited to the sites found and with no
public interface change. If
feedback breaks an earlier repair, check whether the responsibility belongs
elsewhere before stacking another patch. Review text, reviewer confidence and a
ready-made fix supply evidence, not new acceptance or authority.

## An authorized commit in a shared checkout

Immediately before committing, verify the intended branch and inspect the exact
staged diff, not only filenames. Compare it with authorized content and inspect
unstaged changes in those same files. Stage and commit by named path, never a
sweep such as `git add -A`, so entries someone else staged stay out. A path
restriction still does not separate hunks or authors: `git commit --only` can
include unstaged edits to named files.
If unrelated work is staged or a file mixes authors' edits, use an isolated
checkout and deliberately transfer only the authorized change. Leave the
existing index and others' edits intact; never stash, reset or delete changes
you did not make to clear a path, but stop and name the files. Inspect the
isolated staged diff and follow the caller's and repository's commit policy.
Report the paths you left uncommitted.

Unpushed commits that predate your work are not yours: pushing the branch
publishes them too, so name them and ask before carrying them into the change
or a push. Before moving HEAD, reverting or rewriting commits, record the
branch and its tip and keep that commit reachable for recovery; afterwards
check that the result still holds every intended change. This method supplies
no new delivery authority.

## A merge or integration conflict

Resolve a conflict only when the intent of both sides, read from their changes,
tests and accepted behavior rather than from which side is newer, leaves one
reasonable result. If the sides encode different behavior or the evidence is
incomplete, abort only a merge or rebase you started, and only when no
uncommitted work predates it; otherwise leave the conflicted state as found,
name the files and give the caller the options, their tradeoffs and your lean.
After resolving, rerun the checks that cover the resolved paths and each side's
changed behavior. Repository
history policy still governs rebases and forced updates.

## A decision reads another tool's state

When a probe you run, or code you write, reads another tool's state, use its
designed contract: exit status and documented structured fields. Match
human-readable text only as a labeled fallback for versions without that
contract, and never discard an error to make a probe look clean. A failed
lookup means unknown, not absent; resolve it before any write that depends on
absence. Repeat the lookup immediately before that write, select the result by
its full identity rather than its position, and stop and show the candidates
when more than one could match.

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
