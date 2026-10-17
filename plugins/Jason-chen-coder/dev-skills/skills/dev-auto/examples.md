# Dev Auto Examples

These examples illustrate decisions, not a required response format.

## Clear scope, no artifacts

User: "用 dev-auto 看下一步。我已经说清楚只改导出按钮的文案。"

Recommend the scoped implementation step and proportional verification. Do not require a spec, slug confirmation, design-context file, or full planning chain merely because artifacts are absent.

## One feature, two files

`designs/user-export.md` is `ALIGNED`; `plans/user-export.md` is `APPROVED`.

Treat these as one work item. Inspect current evidence to determine whether implementation or verification is next; two artifact files do not imply two competing features. Approval of the plan is not evidence of implemented code.

## Draft with an unresolved permission decision

`designs/user-export.md` exists with `DRAFT`; its open question asks whether administrators may export other users' private records.

Recommend resolving that decision before dependent implementation. Do not infer readiness from file existence. A `--next` answer can be one command such as `dev-grill-docs --spec-only user-export`, with the reason that export authorization is unresolved.

## Same slug in different namespaces

`designs/session.md` and `fixes/session.md` coexist. The user asks about the session-expiry bug.

Use the fix record and its source links. No rename is required just because a feature shares the slug.

## Transient verification failure

Verification failed because the local test database was unavailable, and fresh evidence shows it is healthy again.

Recommend rerunning the affected command. A retry after an identified environment recovery is useful; a blind repeat without new evidence is not.

## Direct action request

User: "修复 session 过期后页面不跳转。"

Do not invoke `dev-auto` automatically. The request belongs to the bug workflow and authorizes investigation and repair.
