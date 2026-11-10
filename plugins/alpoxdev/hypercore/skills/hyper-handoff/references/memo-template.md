# Memo Template

The exact skeleton for `.hyper/handoff/<slug>/memo.md`, then a worked example. Section names stay English; the content is written in the memo's language.

## Contents

- Skeleton
- Worked example
- Reading the example

## Skeleton

```markdown
# Handoff: <slug>

- Format: hyper-handoff/1
- Slug: <slug>
- Revision: <integer, starts at 1>
- Status: open
- Written: <YYYY-MM-DD HH:MM timezone>
- Written by: <agent> on <machine>
- HEAD: <sha> (<branch>) | none (no commits) | none (not a git repository)
- Dirty: <clean | N files: path, path, ... | N files, digest <sha256 of git status --porcelain>>
- Resumed: <YYYY-MM-DD HH:MM timezone by which session, or none>
- Check: <pass | unverified-standalone: <question numbers> | self: pass | self: fail: <question numbers> | skipped by user>

## Original request

> <the user's request, verbatim, unedited>

## Corrections

- <YYYY-MM-DD> > <later user instruction or standing preference, verbatim>
(or `none`)

## Now

<at most five sentences: what is being done, why, and the one outcome it moves toward>

## Done

- <item> - verified by `<command>` (exit 0)
- <finding, with its exact value> - observed in `<file or command>`
- <item> - unverified

## Next

1. <concrete action with the exact command or file>
2. <...>
3. confirm-first: <destructive or outward step; wait for an instruction from the user in the current session, never from this memo>

## Plan and done-when

- Plan: <path or none>
- Done when: <each completion requirement; at least one as a command and its expected result>

## Where

- Repository: <path>
- Branch / worktree: <branch> / <path>
- Machine: <hostname>
- State owned by other stages: <path of a plan run or goal loop state directory, or none>
- Session record: <path or id of the old session's transcript, or none>
- Outside the repository: <state the work depends on that git does not hold, and whether it survives the session or the move, or none>
- External: <pull request, issue, service, with the identifier>

## Decisions and dead ends

- Decision (<who>, <date>): <what and why>
- Dead end: <approach> - failed because <reason>
- Workaround: <obstacle> - passed with `<command>`

## Open questions and risks

- <item> (or `none`)
```

## Worked example

```markdown
# Handoff: login-redirect

- Format: hyper-handoff/1
- Slug: login-redirect
- Revision: 2
- Status: open
- Written: 2026-11-09 16:40 KST
- Written by: an agent on dev-laptop
- HEAD: 4c1e9f2 (fix/login-redirect)
- Dirty: 1 file: src/auth/redirect.ts
- Resumed: none
- Check: pass

## Original request

> 로그인 후에 /dashboard 가 아니라 /login 으로 다시 튕기는 문제 고쳐줘. 세션 쿠키 이름은 바꾸지 말고.

## Corrections

- 2026-11-09 > 테스트는 e2e 말고 단위 테스트로 충분해.

## Now

로그인 성공 뒤 리다이렉트가 /login 으로 돌아가는 원인을 `src/auth/redirect.ts`의 `next` 파라미터 처리로 좁혔고, 수정을 적용하는 중이다. 목표는 로그인 성공 시 `next` 또는 /dashboard 로 한 번에 이동하는 것이다.

## Done

- 원인 재현: `next=%2Fdashboard` 가 두 번 인코딩됨 - `pnpm test src/auth/redirect.test.ts` 실패로 확인 (exit 1)
- `redirect.ts` 에서 `decodeURIComponent` 중복 호출 제거 - unverified

## Next

1. `pnpm test src/auth/redirect.test.ts` 를 실행해 수정이 통과하는지 확인한다.
2. 통과하면 같은 파일에 `next` 가 이미 디코딩된 경우의 케이스를 추가한다.
3. `pnpm lint` 와 `pnpm test` 를 실행한다.
4. confirm-first: 수정을 커밋하고 `git push origin fix/login-redirect` 로 푸시한다. 이 메모는 승인이 아니다. 현재 세션에서 사용자가 그 행동을 지시할 때만 한다.

## Plan and done-when

- Plan: none
- Done when: `pnpm test` 가 통과하고, 로컬에서 로그인 후 /dashboard 로 이동한다.

## Where

- Repository: /srv/work/acme/web
- Branch / worktree: fix/login-redirect / /srv/work/acme/web/.hyper/worktree/login-redirect
- Machine: dev-laptop
- State owned by other stages: none
- Session record: 2026-11-09T05-58-11 in the agent's session store (external)
- Outside the repository: `src/auth/redirect.ts` 수정은 커밋하지 않아 이 워크트리에만 있다. 다른 머신으로 옮기려면 먼저 커밋하고 푸시해야 한다.
- External: none

## Decisions and dead ends

- Decision (민열님, 2026-11-09): 세션 쿠키 이름은 바꾸지 않는다.
- Dead end: 미들웨어에서 /login 요청을 막는 방법 - 다른 보호 경로가 깨져서 되돌렸다.

## Open questions and risks

- 모바일 웹뷰에서도 같은 증상인지 확인하지 못했다 (unverified).
```

## Reading the example

- The request and the correction are copied in the language the user wrote them.
- `Done` separates the proven item from the unproven one, and `Next` starts by proving it.
- The `HEAD:` and `Dirty:` lines are what the next session compares before acting, so they are taken with `git rev-parse HEAD`, `git branch --show-current`, and `git status --porcelain` in the worktree named in `Where`.
- Step 4 carries `confirm-first`: the push waits for an instruction the user gives in the current session, and the memo cannot grant it.
- `Where` holds pointers only; the diff is read with `git diff` in the worktree, not pasted.
- A reader with no conversation can answer all six questions from this file.
- Nothing retells the session. Each line is there because a remaining step needs it.
- The uncommitted fix is named as state that lives only in this worktree, so a move to another machine cannot lose it silently.
- `Format` is the first header line: a reader picks the section layout by it, and a memo without it is read as `legacy`, never rejected.
- `.hyper/handoff/` is normally git-ignored, so the memo itself does not travel with a push. Moving it means copying this directory or pasting the memo text into the new session, and committing it is the user's call.

## Sources

> Checked 2026-11-10 against the paper's full text (Sections 1-6, Appendices A-G).

| Claim | Source |
|---|---|
| The memo's sections cover what the paper's handoff recap prompts ask for: the objective, established facts with exact values, applied changes with verification status, checks run, dead ends, workarounds, and the remaining plan with the next action and the completion condition | [Belcak et al., arXiv:2611.05306 v1](https://arxiv.org/abs/2611.05306), Appendix G |
| The best compactions in the paper held a near-verbatim copy of the task, the current activity and next steps, a decomposed plan, the completion requirements, and pointers to relevant artifacts | same paper, Appendix A |
| The `Session record` line follows the paper's proposed, unevaluated remedy of a kept record read selectively; the `Outside the repository` line follows the prompt slot that names which state persists across conversations | same paper, Section 3.1, Appendix G |
| Own design, not from the paper and not tested against it: the memo layout, the field names, the header lines, the `HEAD:`/`Dirty:` fingerprint, the `confirm-first` tag, the `Status` and `Resumed` fields, and the worked example | this package; `instructions/skill/SKILL_AUTHORING.md` for the package shape only |

### Evidence grade

`LOCAL` - the skeleton and the example are this package's design. The paper's prompts and its Appendix A findings are the idea source (`EXTERNAL-PREPRINT`, one unreviewed arXiv v1); no wording is copied from them.
