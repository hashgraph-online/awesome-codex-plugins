# Memo Template

`.hyper/handoff/<slug>/memo.md`의 정확한 골격이다. 그다음 사례 예가 이어진다. 절 이름은 영어 그대로 두고 내용은 메모의 언어로 쓴다.

## Contents

- Skeleton
- Worked example
- Reading the example

## Skeleton

```markdown
# Handoff: <slug>

- Slug: <slug>
- Revision: <integer, starts at 1>
- Written: <YYYY-MM-DD HH:MM timezone>
- Written by: <agent> on <machine>
- Check: <pass | unverified-standalone: <question numbers> | self | skipped by user>

## Original request

> <the user's request, verbatim, unedited>

## Corrections

- <YYYY-MM-DD> > <later user instruction, verbatim>
(or `none`)

## Now

<at most five sentences: what is being done, why, and the one outcome it moves toward>

## Done

- <item> - verified by `<command>` (exit 0)
- <item> - unverified

## Next

1. <concrete action with the exact command or file>
2. <...>

## Plan and done-when

- Plan: <path or none>
- Done when: <observable condition, ideally a command and its expected result>

## Where

- Repository: <path>
- Branch / worktree: <branch> / <path>
- Machine: <hostname>
- State owned by other stages: <path of a plan run or goal loop state directory, or none>
- External: <pull request, issue, service, with the identifier>

## Decisions and dead ends

- Decision (<who>, <date>): <what and why>
- Dead end: <approach> - failed because <reason>

## Open questions and risks

- <item> (or `none`)
```

## Worked example

```markdown
# Handoff: login-redirect

- Slug: login-redirect
- Revision: 2
- Written: 2026-11-09 16:40 KST
- Written by: omp on alpoxs-macbook
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

## Plan and done-when

- Plan: none
- Done when: `pnpm test` 가 통과하고, 로컬에서 로그인 후 /dashboard 로 이동한다.

## Where

- Repository: /Users/alpox/dev/acme/web
- Branch / worktree: fix/login-redirect / /Users/alpox/dev/acme/web/.hyper/worktree/login-redirect
- Machine: alpoxs-macbook
- State owned by other stages: none
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
- `Where`는 위치 표시만 담는다. diff는 붙여 넣지 않고 워크트리에서 `git diff`로 읽는다.
- 대화가 없는 읽는 쪽도 이 파일만으로 여섯 질문에 모두 답할 수 있다.

## Sources

> 확인 2026-11-09.

| Claim | Source |
|---|---|
| 메모 절은 인수인계 요약 프롬프트의 모양을 따른다. 목표, 확립된 사실, 검증 상태가 붙은 적용 변경, 막다른 길, 다음 명령과 완료 조건이 붙은 남은 계획이다 | [Belcak et al., arXiv:2611.05306](https://arxiv.org/abs/2611.05306), Appendix G |
| 메모 배치, 필드 이름, 작업 예는 이 패키지의 설계다 | 패키지 형태만 `instructions/skill/SKILL_AUTHORING.md` |

### 근거 등급

`LOCAL` - 골격과 예는 이 패키지의 설계다. 논문의 프롬프트는 아이디어 출처이며 문구를 복사하지 않았다.
