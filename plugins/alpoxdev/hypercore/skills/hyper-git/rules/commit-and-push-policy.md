# Commit And Push Policy

Use this rule when the commit mode of `hyper-git` is active and you need the durable commit/push contract after the fast inspection pass.

## Argument Modes

| Input | Action |
|------|------|
| no argument | Same as `current`: select only changes attributable to the current session, verify against Git state, group into logical commits, then push. Do not fall back to unrelated remaining changes. |
| `current` or `CURRENT` | Explicit current-session mode. Use the session's edit/tool record plus diff evidence to select only files or hunks this session created. If attribution is ambiguous, exclude the change and report it rather than absorbing user or other-agent work. |
| `ALL` or `all` | Include every uncommitted file, group into logical commits, and leave no file behind. |
| `--force` | Remove `--force` from commit arguments and pass it only to the push phase, which must use `--force-with-lease` and still block `main`/`master`. |
| `&& <branch>` | End commit arguments and append one propagation target. Multiple targets run left-to-right after the source branch is committed and pushed. Scope keywords are case-insensitive. |
| other argument | Treat it as a filter for repo discovery, file selection, staging, and message generation. Stop if it does not match actual git state. |

## Current-Session Attribution

- Prefer exact files and hunks written through the current session's tools and verified in the live diff.
- A file touched by this session is not wholly owned by it: split-stage only attributable hunks when pre-existing or concurrent edits share the file.
- Never infer ownership merely because a change is unstaged, recent, or the only remaining dirty change.
- If exact hunk separation cannot be performed safely, leave the ambiguous file uncommitted and report it. `ALL` is the explicit opt-in for absorbing every uncommitted change.

## Commit Rules

| Category | Rule |
|------|------|
| Inspect first | Run a status/preflight command before staging or committing. |
| Diff source | If staged changes exist, treat staged files as the default candidate and inspect staged diff. If nothing is staged, inspect unstaged/untracked changes. |
| Repository boundary | Multiple repositories must be committed independently. Never stage or commit from a non-repository parent as if nested repos were one repo. In linked Git worktrees, use the checkout root from `git rev-parse --show-toplevel` as the boundary; do not collapse it to the shared `git-common-dir`. |
| Logical scope | Each commit covers exactly one logical change. Commit multiple groups sequentially. |
| Staging discipline | Stage only files required for the selected group. Do not use blanket staging unless `ALL` mode truly includes every uncommitted file and grouping still happens per logical unit. |
| Type selection | Choose the Conventional Commit type from the actual dominant change. |
| Scope selection | Use scope only when one module/package/feature clearly owns the change. |
| Language | Write the subject, body, and footers in English. If the repository documents its own commit convention (a contributing guide or a commitlint config), follow that convention instead. |
| Subject line | `<type>(<scope>): <summary>` in the imperative mood ("add", "fix", "remove"), lowercase first word after the colon, no trailing period; aim for 50 characters and never exceed 72. |
| Body/footer | Separate the body from the subject with one blank line and wrap it at 72 characters. Add a body only when the why, risk, or follow-up is not obvious from the subject; explain what changed and why, not how. Add footers only for `BREAKING CHANGE:`, verified issue references, or explicitly requested metadata. |
| Attribution | Add `Signed-off-by`, `Co-authored-by`, or other sign-off or AI attribution trailers only when the user or the repository requires them; a sign-off certifies a human's authority, which an agent cannot give. Never invent issue numbers, reviewers, or co-authors. |
| Safety | Never commit secrets, generated credentials, or unrelated user changes. Never use `--no-verify`, rebase, reset, amend, or destructive history operations unless explicitly requested. |
| Hook failures | Inspect the error. Fix and retry only if the current change caused it and the fix is safe; otherwise stop and report the blocker. |

## Commit Message Format

Write the subject as the change the commit applies, completing the sentence "If applied, this commit will ...".

| Use | Avoid | Why |
|------|------|------|
| `fix(auth): handle expired refresh tokens` | `fix(auth): Fixed expired refresh tokens.` | Past tense, capitalized first word, and trailing period. |
| `feat(cli): add --json output to status` | `feat(cli): this commit adds JSON output` | Describes the commit instead of stating the change. |
| `refactor(api): split request validation from handlers` | `refactor: misc cleanup` | Too vague to review or search later. |
| `build(deps): pin toolchain to stable versions` | `build(deps): 안정 버전 도구 체인으로 고정` | Commit messages are English. |

Example with a body and footer:

```text
fix(sync): retry uploads after transient network errors

Uploads failed permanently on the first timeout, which left local
changes unsynced until the next manual run. Retry up to three times
with exponential backoff before reporting the failure.

Refs: #142
```

If the natural draft is past tense, descriptive ("this commit ..."), or vague, rewrite it to the imperative change itself.

## Grouping Heuristics

1. Files that implement the same feature or fix belong together.
2. Tests belong with corresponding implementation files.
3. Config/build changes belong with the feature they support.
4. Unrelated standalone changes each form their own group.
5. In `ALL` mode, every uncommitted file must appear in exactly one group.

## Push Rules

| Category | Rule |
|------|------|
| Commit first | All commit groups must succeed before any push. |
| No confirmation | Do not ask whether to push after successful commits; push automatically. |
| Explicit repos | Prefer passing the repo list from `scripts/git-fast.sh inspect` into `scripts/git-fast.sh push` to avoid duplicate discovery. |
| Worktrees | Linked worktrees are valid push targets when on a named branch; pass their checkout root paths, not `.git/worktrees/...` or the common git dir. |
| Upstream | If no upstream exists, push with `-u origin <branch>`. |
| Safety | Never force push to `main` or `master`. Never push from detached HEAD. |
| Failure | If push fails, report failed repos. Commits remain local; do not pretend the operation completed. |

## Multi-Branch Propagation

1. Parse and validate every `&&` target before mutation. Reject empty/duplicate targets, the source branch, detached HEAD, and invalid ref names.
2. Capture the ordered commit list created by this run. Never propagate unrelated earlier commits merely because they are ahead locally.
3. Use a clean existing linked worktree or create a temporary linked worktree per target. Do not switch a dirty source checkout or disturb unrelated worktree state.
4. Fetch and fast-forward the target from its configured remote before applying commits. Do not merge the whole source branch or rewrite target history.
5. Cherry-pick the captured commits in order. This is the application mechanism; conflict resolution may merge the intentional source and target behaviors in the resulting files.
6. Push a target only after its cherry-pick sequence and relevant validation succeed. Then continue to the next target.
7. Remove only temporary worktrees created by this run and only after they are clean. Never remove a user's pre-existing worktree.

## Conflict Resolution And Escalation

On conflict, own the resolution by default:

- inspect all conflict stages (`base`, `ours`, `theirs`), the source commit intent, target-branch evolution, relevant callers, and tests
- preserve non-conflicting target changes and integrate the source behavior rather than choosing a side wholesale
- resolve generated artifacts through their canonical generator when available; do not hand-edit generated output as the primary fix
- run focused type/lint/tests or the affected executable surface before continuing and pushing
- document what was reconciled in the final report

Ask the user one narrow outcome question only if at least one material decision remains: two or more plausible product behaviors, incompatible schema/data migrations, security or deployment policy ambiguity, deletion of intentional target functionality, or a redesign whose scope substantially exceeds the propagated commits. File count alone is not a blocker, but a wide conflict is evidence to reassess scope. If asking, stop before later targets and preserve a recoverable cherry-pick/worktree state with exact commands and paths reported.

## Type Selection

| Observed dominant change | Type |
|------|------|
| user-facing capability added | `feat` |
| incorrect behavior fixed | `fix` |
| docs only | `docs` |
| formatting/style only | `style` |
| internal restructure | `refactor` |
| performance improvement | `perf` |
| tests added/updated | `test` |
| build/dependency/tooling | `build` |
| CI automation | `ci` |
| maintenance/metadata | `chore` |
| revert | `revert` |

## Failure Handling

| Failure case | Response |
|------|------|
| candidate filter does not match git state | stop; do not push |
| no changes to commit | report no commit was created; push only if there are already unpushed commits and user intent still includes push |
| one commit group fails | stop; do not push any later groups |
| push fails | report which repositories failed; local commits remain safe |
| propagation conflict with one coherent intent-preserving result | resolve, validate, continue, and report the reconciliation |
| propagation conflict requires a material behavior/architecture decision | ask one focused question; do not begin later targets |
| network/auth prompt risk | use non-interactive push helper output; report remote/auth blocker if push cannot proceed |

## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| `<type>[optional scope]: <description>`, the blank line before the body, and footer syntax | <https://www.conventionalcommits.org/en/v1.0.0/> |
| A short summary line of about 50 characters, a blank line, then the description | `git-commit(1)` DISCUSSION (git 2.56.0), <https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project> |
| Imperative mood, lowercase after the `area:` prefix, and no full stop | <https://github.com/git/git/blob/master/Documentation/SubmittingPatches> |
| Agents must not add `Signed-off-by`, because only a human can certify it | <https://docs.kernel.org/process/coding-assistants.html> |

The argument modes, attribution, grouping, push, propagation, and conflict rules are authored in this package from repository practice and cite no external source.
