# Agent Event Policy

Use this policy when the host agent exposes command or tool hooks, and as
router guidance when it does not.

## Events

- `before_commit`: before creating or amending a commit, load
  `agent-pr-review`, stage intended changes separately, review the exact staged
  diff, then record a local receipt for that staged diff. The protected commit
  must not use implicit staging flags or pathspecs. Do not combine staging,
  commit, or push in one shell command.
- `before_release`: before tags, version bumps, hosted release records, package builds,
  artifact publication, or promotion, load `release-build-reproducibility` to
  check pinned inputs, artifact identity, promotion path, and rollback
  traceability, and load `production-readiness-review` to check release
  ownership, rollback, watch, and operator impact.

## Enforcement

Receipts live under the repository's git metadata, not in the working tree. They
bind to the current source revision and staged diff for commit events, so a
receipt cannot be reused after another commit changes the base. Release receipts
bind to the current source revision, staged diff, unstaged diff, and the paths
and content of untracked files so packaging or promotion cannot consume inputs
absent from the reviewed state. If that bound state changes after review, the
agent must rerun the matching event review before retrying the action.

On receipt-enforced hosts, the specialist review, receipt, and protected command
are separate steps and separate shell commands. After a clean commit review,
record the commit receipt as its own shell command before the first commit
attempt. After clean release reviews, record the release receipt as its own
shell command before the first release command; a review message alone does not
satisfy the hook. Do not combine the receipt command with the commit, tag,
release, push, or promotion command. The command hook checks the whole shell
command before any subcommand runs, so a combined `ack && git commit` or
`ack && git tag` command is denied by the host hook before the receipt can
authorize the protected command. The receipt helper itself records receipts and
does not enforce shell composition when a host bypasses command hooks.
Likewise, one receipt never authorizes multiple protected operations composed
in one shell command. Run commits, tag creation, tag pushes, package builds,
hosted release changes, and promotions as individually checked commands.
Do not precede a protected operation with another command in the same shell
invocation because the hook checks the receipt before that earlier command can
change the bound state. A literal directory change to the target checkout may
remain in the protected invocation.
Run protected operations directly rather than hiding them in a nested shell
command string, where the hook cannot resolve and bind the exact operation
state.
Do not use protected Git operations with alternate repository, worktree,
namespace, index, object-storage, or configuration selectors. Enter the target
checkout normally so the reviewed state and receipt refer to the same Git
state.
Reading only router or host bootstrap files does not satisfy a specialist
review; the agent must read the matching specialist files. Do not add AI
assistant co-author or attribution trailers to commit messages.

The review requirement gates agent awareness, not user authority. A clean review
can record a normal receipt. A review with unresolved gaps can still record an
override receipt when the user explicitly accepts the findings and asks to
proceed. Do not offer an override merely because the repo or change appears
personal, small, or low risk.

Hosts without command-interception hooks still follow the same policy through
router and specialist triggers. A commit attempt is a concrete change-set review
request. A release, tag, version, package, artifact, or promotion attempt is a
release-engineering request.
