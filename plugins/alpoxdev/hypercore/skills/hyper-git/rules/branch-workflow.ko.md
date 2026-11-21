# 브랜치 워크플로

`hyper-git`의 workflow 모드가 활성화되었을 때 이 규칙을 사용한다. 브랜치 모델을 고르거나 문서로 남기고, 작업 브랜치를 만들거나 동기화하고, 풀 리퀘스트를 열고, 병합하고, 한 브랜치를 다른 브랜치에 병합해 푸시하고, 병합 뒤 정리하는 경우다.

## 1. 저장소를 먼저 읽는다

저장소 자체 설정이 워크플로를 정하며, 이 규칙은 어떤 모델도 강요하지 않는다. 행동 전에 다음을 읽는다.

```bash
git rev-parse --show-toplevel
git status --short --branch
git remote -v
git branch -a
git symbolic-ref --short refs/remotes/origin/HEAD   # default branch
gh repo view --json defaultBranchRef,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge
```

기여 가이드, `AGENTS.md`, 브랜치 관련 메모가 있으면 함께 읽는다. `gh`나 원격이 없으면 워크플로는 로컬 전용이며, 풀 리퀘스트와 원격 설정을 읽지 못했다고 보고한다.

브랜치 보호와 필수 검사는 풀 리퀘스트를 통해 읽는다(`gh pr checks`, `gh pr view --json mergeStateStatus,reviewDecision`). 거부된 푸시는 보호가 걸려 있다는 근거이며, 더 약한 형태로 재시도하지 않는다.

## 2. 브랜치 모델

사용자가 어떤 모델을 쓸지 물으면 선호가 아니라 저장소 근거로 추천한다.

| 모델 | 맞는 경우 | 형태 |
|---|---|---|
| GitHub flow | 배포 가능한 줄기가 하나이고 지속적 배포와 풀 리퀘스트 리뷰를 할 때 | 기본 브랜치에서 짧은 브랜치 생성 -> 풀 리퀘스트 -> 검사와 리뷰 -> 병합 -> 브랜치 삭제 |
| 트렁크 기반 | 팀이 작거나 CI가 강하고 최소 하루 한 번 통합할 때 | 아주 짧은 브랜치 또는 트렁크에 직접 커밋. 릴리스 브랜치는 필요할 때 그때 만듦 |
| 통합 브랜치(`dev`)와 배포 브랜치 | 저장소에 이미 `dev`, `deploy/*`, `release/*` 브랜치가 있을 때 | `dev`에서 작업 브랜치 생성 -> `dev`에 병합 -> 요청 시 배포 브랜치나 기본 브랜치로 승격 |
| Git Flow | 여러 릴리스 버전을 동시에 지원해야 하는 명시적 버전 소프트웨어 | `develop`, `feature/*`, `release/*`, `hotfix/*`, `main` |

고른 모델, 그것을 뒷받침하는 브랜치, 사용자가 다른 모델을 골랐을 때 달라질 점을 보고한다. 선택을 기여 문서에 적는 일은 별도의 명시적 요청이다.

## 3. 작업 브랜치

- 기준: 사용자가 댄 브랜치, 없으면 통합 브랜치(`dev`가 있으면 `dev`), 그것도 없으면 기본 브랜치.
- 이름: Conventional Commit 타입을 쓴 `<type>/<short-slug>`(`feat/`, `fix/`, `refactor/`, `docs/`, `chore/`), 이슈 작업은 `<type>/<issue-number>-<slug>`. 저장소가 다른 관례를 문서로 두지 않았을 때다. `git check-ref-format --branch <name>`으로 검증한다.
- 깨끗하지 않은 체크아웃을 건드리지 않고 만들기: 깨끗한 체크아웃에서만 `git switch -c <name> <base>`를 쓴다. 아니면 워크트리 모드로 워크트리를 만든다.
- 동기화: `git fetch origin <base>` 후 공유 브랜치에서는 `git merge origin/<base>`, 아무도 당겨 가지 않은 브랜치에서 사용자나 저장소가 선형 이력을 선호할 때만 `git rebase origin/<base>`를 쓴다. 푸시한 브랜치를 rebase한 뒤에는 맨 `--force`가 아니라 `--force-with-lease`로 푸시하며, `main`·`master`·기본 브랜치에서는 절대 하지 않는다.

## 4. 풀 리퀘스트

```bash
git push -u origin <branch>
gh pr create --base <base> --head <branch> --title "<conventional subject>" --body-file <file>
gh pr view <n> --json state,mergeStateStatus,reviewDecision,statusCheckRollup
gh pr checks <n> --watch
```

- 제목은 변경의 Conventional Commit subject로 쓴다. 본문에는 무엇을 왜 바꿨는지, 어떻게 검증했는지, `gh issue view`에서 읽은 이슈의 `Closes #<n>` 줄을 적는다(닫기 키워드는 기준 브랜치가 기본 브랜치일 때만 동작한다. `rules/issue-workflow.md` 참고).
- 커밋이 하나인 브랜치에는 `--fill`을 써도 된다. 게시 전에 생성된 텍스트를 확인한다.
- 풀 리퀘스트 생성은 협업자에게 게시하는 일이다. 사용자가 풀 리퀘스트를 요청했거나 저장소가 전달을 풀 리퀘스트로 처리할 때만 연다.
- 리뷰어는 사용자가 이름을 댔을 때만 요청한다.

## 5. 병합

저장소가 허용하고 사용자가 요청한 병합 방식을 쓴다. 여러 방식이 허용되고 사용자가 하나도 지정하지 않았으면 저장소가 문서로 둔 관례를 따르고, 그것도 없으면 작업 브랜치를 통합 브랜치에 넣을 때 squash를 우선한다.

| 경로 | 명령 | 쓰는 경우 |
|---|---|---|
| 풀 리퀘스트 병합 | `gh pr merge <n> --squash|--merge|--rebase [--delete-branch]` | 풀 리퀘스트가 있고 검사와 리뷰를 통과했을 때 |
| 자동 병합 | `gh pr merge <n> --auto --squash` | 필수 검사가 통과하면 병합되게 하고 싶을 때 |
| 로컬 병합과 푸시 | `git switch <target> && git pull --ff-only && git merge --no-ff <branch>` 후 `git push origin <target>` | 사용자가 이름을 댄 브랜치에 직접 병합하라고 했고 풀 리퀘스트를 요구하는 규칙이 없을 때 |
| 새 커밋만 전파 | commit 모드의 `&& <branch>` 대상 | 이번 실행이 만든 커밋만 다른 브랜치에 닿아야 할 때 |

모든 병합에 적용하는 규칙:

- `main`, `master`, 기본 브랜치, 배포 브랜치로의 병합은 사용자가 이 대화에서 그 브랜치를 댔을 때만 한다.
- `gh pr merge --admin`을 쓰지 않고, 필수 검사나 리뷰를 건너뛰지 않고, 브랜치 보호와 병합 설정을 바꾸지 않는다. 대신 무엇이 바뀌어야 하는지 보고한다.
- 로컬 병합 전에 대상은 원격에서 fast-forward되어야 한다(`git pull --ff-only`). 갈라진 대상은 병합을 멈추고 그대로 보고한다.
- 충돌은 commit 모드의 의도 보존 충돌 규칙(`rules/commit-and-push-policy.md`)으로 해결하고, 병합 결과에서 저장소 검사를 실행하며, 통과한 뒤에만 푸시한다.
- 대상이 여럿이면("dev, main") 왼쪽부터 병합하고 푸시한다. 하나가 실패하면 뒤 대상은 멈춘다.
- 병합 결과를 force push하지 않는다.

## 6. 병합 뒤

- 원격에서 병합을 확인한다: `git fetch origin <target>` 후 `git branch -r --contains <commit>`, squash 병합이면 `+` 줄이 없는 `git cherry origin/<target> <branch>`, 또는 풀 리퀘스트 상태 `MERGED`.
- 병합이 확인되고 그 브랜치를 쓰는 열린 풀 리퀘스트가 없을 때만 작업 브랜치를 로컬(`git branch -d`, squash 병합이 확인된 뒤에는 `-D`)과 원격(`git push origin --delete <branch>`)에서 삭제한다.
- 워크트리는 워크트리 모드의 삭제 검사를 거쳐 제거한다.
- 병합이 닫지 못한 열린 이슈를 보고한다.

## 7. 보고

한국어로 보고한다. 읽은 모델이나 브랜치, 생성·푸시·병합·삭제한 브랜치와 커밋 SHA, 풀 리퀘스트 URL과 상태, 검사 결과, 게이트가 멈춘 모든 행동.

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| GitHub flow 단계 | <https://docs.github.com/en/get-started/using-github/github-flow> |
| 지속적으로 배포하는 소프트웨어는 더 단순한 흐름을 선호하라는 Git Flow 저자의 2020년 메모 | <https://nvie.com/posts/a-successful-git-branching-model/> |
| 짧은 브랜치와 적시 릴리스 브랜치를 쓰는 트렁크 기반 개발 | <https://trunkbaseddevelopment.com/> |
| GitHub의 병합 커밋, squash, rebase 동작 | <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github> |
| 보호 브랜치는 force push와 삭제를 막고 검사와 리뷰를 요구할 수 있음 | <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches> |
| `gh pr create`의 기준 브랜치 결정과 `--fill` | <https://cli.github.com/manual/gh_pr_create> |
| `gh pr merge`의 병합 방식, `--auto`, `--delete-branch`, `--admin` | <https://cli.github.com/manual/gh_pr_merge> |
| `--force-with-lease`와 `--force`의 차이 | <https://git-scm.com/docs/git-push> |

모델 선택 표, 브랜치 이름 기본값, 작업 브랜치에 대한 squash 기본값은 외부 요구 사항이 아니라 이 패키지의 설계다.
