# 속도와 자동화

`hyper-git`의 commit 모드가 느리게 느껴지거나 사용자가 더 빠른 commit-and-push 경로를 명시적으로 요청할 때 이 규칙을 사용한다.

## 빠른 경로

verbose manual workflow보다 이 경로를 먼저 선호한다.

```bash
scripts/git-fast.sh inspect . --jobs 4
```

그런 다음 기존 commit helper로 각 논리 그룹을 commit한다.

```bash
scripts/git-commit.sh "<type>(<scope>): <imperative summary>" path/to/file1 path/to/file2
scripts/git-commit.sh --repo path/to/repo "<type>(<scope>): <imperative summary>" path/to/file1
```

모든 commit이 성공하면 다시 discovery하지 말고 inspected repo list를 재사용한다.

```bash
scripts/git-fast.sh push /absolute/repo/path
scripts/git-fast.sh push --force /absolute/repo/path
```

fast helper가 실패하거나 필요한 detail을 빠뜨리면 `repo-discover.sh`, `repo-status.sh`, `git-commit.sh`, `git-push.sh`로 fallback한다.

## Fast Helper가 자동화하는 것

| 단계 | 자동화 |
|------|------|
| repository discovery | current repo/worktree short-circuit; descendant discovery는 무거운 generated directory를 prune하고 linked worktree `.git` file을 인식한다 |
| multi-repo inspection | `--jobs` / `HYPER_GIT_JOBS`를 통한 parallel per-repo status block |
| file inventory | repository마다 porcelain status snapshot 하나를 수집하고, 세 번의 중복 file scan 대신 여기서 staged, unstaged, untracked list를 도출한다 |
| legacy helper | `repo-discover.sh`는 generated tree를 prune하고, `repo-status.sh`는 수집한 status/stat 출력을 재사용하며, `git-push.sh`는 동일한 safe-push policy를 독립적으로 보존한다 |
| worktree context | operator가 checkout root를 common git dir와 분리해 유지하도록 `worktree|primary` 또는 `worktree|linked`와 git dir metadata를 출력한다 |
| push | explicit repo path를 받고 `GIT_TERMINAL_PROMPT=0`을 사용하며 detached HEAD를 건너뛰고 protected force push를 차단한다 |

## 병렬화 규칙

- repository 간 read-only inspection을 병렬화한다.
- 같은 repository 안의 commit은 병렬화하지 않는다. staging/index state를 공유한다.
- file group과 repo boundary가 이미 명확할 때만 repository를 독립적으로 commit할 수 있다.
- 모든 의도한 commit이 성공한 뒤에만 push한다.

## 느린 경로 트리거

다음 경우에는 더 느린 full workflow를 사용한다.

- partial hunk에 `git add -p`가 필요하다
- staged와 unstaged 변경사항이 의도적으로 섞여 있다
- hook이 실패해 diagnosis가 필요하다
- filter argument가 file에 명확히 매핑되지 않는다
- push 실패에 remote/auth investigation이 필요하다

## 시간 기대치

helper는 피할 수 있는 overhead를 제거하기 위한 것이지 safety를 우회하기 위한 것이 아니다. 다음을 빠르게 한다.

- commit과 push 사이의 중복 repository discovery
- common generated folder를 prune해 큰 descendant tree scan 단축
- `.git`이 directory라고 가정하지 않고 checkout root를 resolve하는 linked worktree run
- read-only work를 병렬화하는 multiple-repository status check
- raw status와 grouped file inventory에 하나의 status snapshot을 재사용하는 single-repository inspection
- `grep` process를 만들지 않는 Bash 내부 commit-message 검증

diff inspection, logical change grouping, 올바른 commit message 작성, hook failure 처리가 필요 없어진 것은 아니다.

## Sources

> 외부 출처 없음. 내용 확인 2026-09-22.

이 규칙은 이 패키지의 저장소 작업 경험에서 작성했다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
