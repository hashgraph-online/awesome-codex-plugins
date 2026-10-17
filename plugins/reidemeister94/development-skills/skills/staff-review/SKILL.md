---
name: staff-review
description: "Review a local branch, diff, repository, directory, or file for supported specification and quality findings."
user-invocable: true
effort: xhigh
---

# Staff review

Resolve the requested scope. With no explicit scope, review the current branch changes; if none exist, ask what to review.

Dispatch a separate `development-skills:staff-reviewer` subagent in a new context window with no parent conversation history.
Never fork or continue the implementation context.
Give it the change as an artifact, plus the requirement or plan, related chronicle, project standards, and verification evidence.
Do not narrate how the change was built, what you concluded, or what you suspect.
On Codex, state that the reviewer is read-only because a custom agent inherits the parent's live sandbox and approval state.
Wait for its verdict.

The reviewer must inspect the diff before those materials and return separate specification and quality verdicts.
No findings is a valid result.
For re-review, give it the prior findings and fix diff. It checks those findings and new breakage without reopening untouched code.

Relay its factual verdict unchanged, including what it did not check.
Do not ask the user for permission to dispatch. Research only when it can settle a material doubt.
