---
name: review-a-pr
description: Have a Rush cloud agent review a GitHub pull request and report what it would change. Use when someone asks for a code review, a second opinion on a PR, or a check of a PR before merging.
---

# Review a pull request with Rush

1. **Find the pull request.** Get its URL. If the person names only a
   repository, ask which PR. If `list_repositories` does not list the
   repository, say the Rush GitHub App does not reach it yet
   (https://cloud.getrush.ai/console/settings/?section=connections) and stop.
2. **Start the review.** Call `create_session` with the PR URL as `repo`, a
   fresh UUID you write yourself as `request_id`, and a `task` like: "Review
   this pull request. Read the diff and the code it touches, run the tests and
   linters the repo has, and list each problem with its file and line, why it
   matters and the change you would make, most serious first. Say plainly if
   you find nothing. Do not push commits or post comments." Add anything the
   person asked to focus on, such as security or performance. To review several
   PRs, start one session each.
3. **Wait.** A review takes a few minutes: call `wait_for_sessions` with
   `timeout_seconds: 50` until it settles.
4. **Report.** From `get_session`: the findings, most serious first, each with
   its file and line, and which tests ran. Do not add findings of your own to
   Rush's list. On `needs_review` or `failed`, say so with the reason.
5. **Offer the next step.** Ask follow-up questions with
   `send_session_message` in the same session; its task told it not to
   push. To make the fixes, start a new session with the
   findings in its `task` and the PR's branch (`/tree/<branch>`) as `repo`
   for a branch in the same repository; for a PR from a fork, the new session
   opens its own pull request. Start it only when the person asks.
