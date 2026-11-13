# Other CI providers and code hosts

fix-ci's loop doesn't depend on the provider; only the commands change. These notes are starting points, not tested
adapters: write the commands into the `## Agent workflow settings` section of your root `AGENTS.md` and check each one
on a real pipeline before relying on it. A waiter you write should keep `scripts/wait_for_ci`'s exit statuses (0 every
watched run passed, 1 failed, 2 API error, 3 no pipeline yet, 124 deadline passed first, never success) so the loop in
SKILL.md reads it the same way, and SKILL.md's check of the required checks still follows an exit 0.

## CircleCI

There's no official "watch" command. Write a small waiter over the API v2: find the pipeline for the branch and
commit, poll its workflows until all of them finish (not only until the first failure), and exit 0 only when every
workflow succeeded. Report an approval job on hold as pending, not as passed. Read the API token from an environment
variable or a secret manager's CLI that doesn't print it. With dynamic config (a setup workflow that continues into
the real one), list the pipeline's workflows again on every poll, since the real workflow appears after the setup one
finishes. Failed jobs' logs are in the API's job details and the web UI.

## GitLab CI and merge requests

`glab ci status --live` follows the pipeline for the current branch, `glab ci view` shows its jobs, and
`glab ci trace <job-id>` prints a job's log. Merge request threads are discussions:
`glab api projects/:id/merge_requests/<iid>/discussions` lists them, a `POST` to
`.../discussions/<discussion-id>/notes` replies, and a `PUT` to `.../discussions/<discussion-id>?resolved=true`
resolves one.

## Other code hosts

The review-comment steps need three commands: list unresolved threads with their IDs, reply to a thread, and resolve
a thread. Put them in the settings. Without them, handle CI only and list the review comments for the user.
