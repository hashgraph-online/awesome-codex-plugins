# 에이전트 병렬 처리

`hyper-git`의 commit 모드가 활성화되어 있고 더러운 작업 트리가 복잡해 Claude Code 또는 Codex 하위 에이전트가 Git 상태를 건드리지 않고 분석 시간을 줄일 수 있을 때 이 규칙을 사용한다.

## 위임 시점

다음 조건 중 하나 이상이 참일 때만 읽기 전용 에이전트를 병렬로 실행한다.

- 여러 저장소가 범위에 있다
- 여러 논리적 커밋 그룹이 예상된다
- diff가 커서 그룹화, 안전 검토, 메시지 초안을 독립적으로 실행할 수 있다
- 사용자가 명시적으로 병렬 에이전트 사용을 요청한다

단일 파일 또는 단일 그룹이 명확한 커밋에는 에이전트를 실행하지 않는다. 조율 비용이 직접 실행보다 느린 경우가 많다.

## 안전한 에이전트 레인

| 레인 | 책임 | 입력 | 출력 | 편집/스테이징/커밋? |
|------|------|------|------|------|
| Repo Mapper | 저장소/worktree 루트, staged/unstaged/untracked 파일, 소유 경계를 매핑한다 | `git-fast.sh inspect` 출력, `git diff --name-only` | 저장소/파일 맵, linked-worktree 맥락, 모호성 목록 | 아니오 |
| Grouping Critic | 논리적 커밋 그룹을 제안하고 무관한 파일이나 비밀을 표시한다 | status, 파일 목록, diff 요약 | 신뢰도와 제외 항목을 포함한 그룹 계획 | 아니오 |
| Message Drafter | 영어 Conventional Commit 제목/본문을 작성한다 | 그룹 계획과 diff 요약 | 근거가 있는 메시지 후보 | 아니오 |
| Safety Verifier | 비밀, 파괴적 작업, 보호 브랜치, detached HEAD, upstream/push 위험을 확인한다 | status, branch/upstream 출력, 스크립트 diff | 통과/차단 보고서 | 아니오 |
| Main Integrator | 레인 간 충돌을 해결하고 stage, commit, push, report를 수행한다 | 모든 레인 출력 | 실제 커밋과 push 요약 | 예 |

## 엄격한 경계

- 하위 에이전트는 파일을 검사하고 읽기 전용 명령을 실행하며 결정을 제안할 수 있다.
- 하위 에이전트는 `git add`, `git commit`, `git push`, `git reset`, `git rebase`, `git clean`, `git restore`를 실행하면 안 된다.
- 같은 저장소의 staging과 commit은 Git index와 staged set을 공유하므로 단일 소유자로 유지해야 한다.
- push는 모든 의도한 커밋 그룹이 성공할 때까지 기다린다.
- 최종 그룹화, 메시지 선택, staging, commit 실행, push는 main integrator가 소유한다.

## 런타임 참고

- Claude Code: 독립 레인에는 작업별 하위 에이전트를 사용하고 lead agent가 결과를 조율한다.
- Codex: 사용 가능하면 bounded read-only 레인에 native/project-local 하위 에이전트를 사용한다.
- 프로젝트 로컬 에이전트 정의는 나중에 `.claude/agents/` 또는 `.codex/agents/` 아래에 추가할 수 있지만, 이 스킬은 home/global 에이전트 디렉터리에 의존하면 안 된다.
- 런타임이 하위 에이전트를 실행할 수 없으면 main context에서 같은 레인 체크리스트를 수동으로 사용한다.

## 위임 프롬프트 템플릿

다음 템플릿은 바로 복사해 사용할 수 있다. 대괄호 필드는 현재 inspect 출력이나 파일 목록으로 바꾼다. 모든 레인은 읽기 전용이다.

### Repo Mapper

```text
Read-only hyper-git commit-mode repo mapping. Do not edit, stage, commit, push, or restore files.
Input: [paste git-fast inspect output and optional git diff --name-only].
Return: repositories/worktree roots in scope, staged/unstaged/untracked files by repo, linked-worktree context if present, ownership boundaries, and ambiguity list.
```

### Grouping Critic

```text
Read-only hyper-git commit-mode grouping review. Do not edit, stage, commit, push, or restore files.
Input: [paste status, file list, and focused diff summaries].
Return: proposed logical commit groups, files included in each group, exclusions, confidence, and any secret/unrelated-change concerns.
```

### Message Drafter

```text
Read-only hyper-git commit-mode commit message drafting. Do not edit, stage, commit, push, or restore files.
Input: [paste final or candidate group plan and diff summary].
Return: English Conventional Commit subject/body candidates for each group, with rationale: imperative subjects, lowercase after the colon, no trailing period, at most 72 characters, no fabricated issue footers, and no sign-off or attribution trailers unless requested.
```

### Safety Verifier

```text
Read-only hyper-git commit-mode safety verification. Do not edit, stage, commit, push, or restore files.
Input: [paste branch/upstream/status output, changed file list, and changed hyper-git script diff if this run modifies scripts].
Return: pass/block verdict for secrets, destructive git operations, protected branch force-push risk, detached HEAD, upstream risk, and missing validation.
```

## 충돌 해결

| 충돌 | 해결 |
|------|------|
| Grouping Critic과 Message Drafter가 불일치 | 그룹화 근거를 우선하고 최종 그룹 선택 후 메시지를 다시 작성한다 |
| Safety Verifier가 blocker를 보고 | mutation을 중단하고 blocker를 보고한다 |
| Repo Mapper가 repo boundary mismatch를 발견 | staging 전에 focused inspect를 다시 실행한다 |
| 편집/hooks 이후 에이전트 출력이 오래됨 | push 전에 status를 갱신하고 다시 검증한다 |

## Sources

> 외부 출처 없음. 내용 확인 2026-09-22.

이 규칙은 이 패키지의 저장소 작업 경험에서 작성했다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
