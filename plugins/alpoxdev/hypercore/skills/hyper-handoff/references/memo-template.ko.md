# Memo Template

`.hyper/handoff/<slug>/memo.md`의 정확한 골격이다. 그다음 사례 예가 이어진다. 절 이름은 영어 그대로 두고 내용은 메모의 언어로 쓴다.

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

- 요청과 정정은 사용자가 쓴 언어 그대로 복사한다.
- `Done`은 증명된 항목과 증명되지 않은 항목을 나누고, `Next`는 그것을 증명하는 일로 시작한다.
- `HEAD:`와 `Dirty:` 줄은 다음 세션이 움직이기 전에 대조하는 값이며, `Where`가 밝힌 워크트리에서 `git rev-parse HEAD`, `git branch --show-current`, `git status --porcelain`으로 잰다.
- 4번 단계에 `confirm-first`가 붙는다. 푸시는 현재 세션에서 사용자가 주는 지시를 기다리며, 메모는 그것을 허가하지 못한다.
- `Where`는 위치 표시만 담는다. diff는 붙여 넣지 않고 워크트리에서 `git diff`로 읽는다.
- 대화가 없는 읽는 쪽도 이 파일만으로 여섯 질문에 모두 답할 수 있다.
- 세션을 되짚어 이야기하는 줄이 없다. 모든 줄은 남은 단계에 필요해서 있다.
- 커밋하지 않은 수정을 이 워크트리에만 있는 상태로 적어, 다른 머신으로 옮길 때 모르는 사이에 잃지 않게 한다.
- `Format`은 헤더의 첫 줄이다. 읽는 쪽은 이 줄로 절 배치를 고르고, 이 줄이 없는 메모는 `legacy`로 읽되 거부하지 않는다.
- `.hyper/handoff/`는 보통 git 무시 대상이라 메모 자체는 푸시를 따라가지 않는다. 옮기려면 이 디렉터리를 복사하거나 메모 본문을 새 세션에 붙여 넣고, 커밋 여부는 사용자가 정한다.

## Sources

> 확인 2026-11-10. 논문 전문(Section 1-6, Appendix A-G)과 대조했다.

| Claim | Source |
|---|---|
| 메모 절은 논문의 인수인계 재요약 프롬프트가 요구하는 것을 다룬다. 목표, 정확한 값이 붙은 확인된 사실, 검증 상태가 붙은 적용 변경, 돌린 검사, 막다른 길, 우회 방법, 다음 행동과 완료 조건이 붙은 남은 계획이다 | [Belcak et al., arXiv:2611.05306 v1](https://arxiv.org/abs/2611.05306), Appendix G |
| 논문에서 가장 좋았던 압축에는 작업의 원문에 가까운 사본, 현재 하는 일과 다음 단계, 나눈 계획, 완료 요건, 관련 산출물로 가는 위치 표시가 들어 있었다 | 같은 논문, Appendix A |
| `Session record` 줄은 기록을 남겨 두고 골라 읽는다는 논문의 제안(평가하지 않은 해법)을 따른다. `Outside the repository` 줄은 대화가 바뀌어도 남는 상태를 밝히는 프롬프트 슬롯을 따른다 | 같은 논문, Section 3.1, Appendix G |
| 자체 설계이며 논문에서 가져오지 않았고 논문으로 시험하지 않은 것: 메모 배치, 필드 이름, 헤더 줄, `HEAD:`/`Dirty:` 지문, `confirm-first` 표기, `Status`와 `Resumed` 필드, 작업 예 | 이 패키지. 패키지 형태만 `instructions/skill/SKILL_AUTHORING.md` |

### 근거 등급

`LOCAL` - 골격과 예는 이 패키지의 설계다. 논문의 프롬프트와 Appendix A의 발견은 아이디어 출처이며(`EXTERNAL-PREPRINT`, 검토하지 않은 arXiv v1 하나) 문구를 복사하지 않았다.
