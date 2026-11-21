---
name: staff-review
description: "Use when the user asks for a review of a branch, diff, repository, directory, or file, or when the development loop requires an independent review of finished work."
user-invocable: true
effort: high
---

# Staff review

Resolve the scope. Without one, review the current branch changes; when there are none, ask what to review.

Dispatch a separate `development-skills:staff-reviewer` subagent in a new context window with no parent conversation history.
Give it the change as an artifact (a diff file, a commit range, or `git diff` output), the user's request verbatim, the plan and chronicle if present, the project standards, the verification output, and the user's language for the report.
Do not narrate how the change was built, your conclusions, or claims such as "safe" or "fully tested": the author's framing hides defects from a reviewer.
On Codex, state in the task that the reviewer is read-only, because a custom agent inherits the parent's live sandbox and approval state.
For a re-review, also give it the prior findings and the fix diff.

The reviewer sketches its own design from the request before it reads the diff. The design verdict runs on every review, and no findings is a valid result.

Relay its report unchanged, including what it did not check: it is already written for a reader who knows nothing about the task. Dispatching needs no permission from the user.
A design finding that challenges the request or a plan decision belongs to the user: present it with its alternative and change nothing until the user answers.
