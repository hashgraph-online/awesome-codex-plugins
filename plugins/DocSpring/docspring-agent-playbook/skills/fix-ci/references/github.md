# GitHub and GitHub Actions commands

The worked adapter for fix-ci. Every command here uses `gh`, signed in, run from inside the repository.

## Waiting for the pipeline

`scripts/wait_for_ci` (in this skill's folder) watches the GitHub Actions runs on HEAD, including runs that start
later, and exits 0 only when every visible run passed and every `--require` workflow ran and passed. Run it in the
background, naming each required workflow:

```bash
<skill folder>/scripts/wait_for_ci --timeout 1800 --require CI --require Deploy
```

Its exit statuses: 0 every visible run passed, 1 a run failed, 2 `gh` or the API kept failing, 3 no run registered,
124 the deadline passed first (runs pending, a required workflow missing, or not yet settled; the deadline never counts
as success). `--help` lists the options.

It only sees GitHub Actions runs. After exit 0, confirm the branch's required checks, which can include other
services' checks and statuses:

```bash
gh pr checks <pr-number> --required   # exit 0: all required checks passed; 8: some still pending; 1: one failed
```

## Runs, jobs and logs

```bash
# Every workflow run for the commit, with its state
gh run list --commit "$(git rev-parse HEAD)" --json databaseId,workflowName,status,conclusion,attempt

# Failed jobs and their logs
gh run view <run-id> --json jobs -q '.jobs[] | select(.conclusion == "failure") | .name'
gh run view <run-id> --log-failed

# Rerun only the failed jobs (for a flaky failure)
gh run rerun <run-id> --failed

# The checks on the PR (add --required for only the required ones)
gh pr checks <pr-number>
```

`gh pr checks` lists only the checks that have started, so "all checks pass" can mean "everything so far". Compare
against the branch's required checks (the branch protection or ruleset) before you call CI green. Checks reported by
an outside CI service show up as commit statuses: `gh api repos/{owner}/{repo}/commits/$SHA/status`. A deployment
waiting for an environment's approval shows as a run with status `waiting`; a green summary doesn't prove a required
approval happened, so check the run itself.

## Finding the PR

```bash
gh pr view --json number,url
```

## Review comments

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
N=$(gh pr view --json number -q .number)

# Inline review threads, with the thread IDs you need to resolve them and their resolution state
gh api graphql -F owner="$OWNER" -F repo="$REPO" -F n="$N" -f query='
  query($owner:String!, $repo:String!, $n:Int!) {
    repository(owner:$owner, name:$repo) { pullRequest(number:$n) {
      reviewThreads(first:100) { nodes {
        id isResolved isOutdated path line
        comments(first:50) { nodes { databaseId author { login } body url createdAt } }
      } }
    } }
  }'

# Review bodies and conversation comments
gh api --paginate "repos/$OWNER/$REPO/pulls/$N/reviews"
gh api --paginate "repos/$OWNER/$REPO/issues/$N/comments"
```

A PR with more than 100 threads needs the GraphQL query paged (`pageInfo { hasNextPage endCursor }` and `after:`).

Replying and resolving:

```bash
# Reply to an inline comment (use the databaseId of the thread's first comment)
gh api "repos/$OWNER/$REPO/pulls/$N/comments/<comment-id>/replies" -f body='Fixed in abc1234: ...'

# Resolve the thread (use the thread's GraphQL id)
gh api graphql -F id=<thread-id> -f query='
  mutation($id:ID!) { resolveReviewThread(input:{threadId:$id}) { thread { isResolved } } }'

# Answer a conversation comment
gh pr comment "$N" --body-file <file>

# Update the PR description (read the current body first)
gh pr edit "$N" --body-file <file>
```
