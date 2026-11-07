# Worktree Lifecycle 규칙

`hyper-git`의 worktree 모드가 활성화되었을 때 이 규칙을 사용한다.

## 1. 저장소 discovery

대상 저장소의 어떤 descendant에서도 실행한다.

```bash
git rev-parse --show-toplevel
git rev-parse --git-common-dir
git worktree list --porcelain
```

Git repository 내부가 아니면 operation을 중단하고 repository path가 필요하다고 보고한다.

## 2. 작업 의도, naming, path

기본 root:

```text
<repo-root>/.hyper/worktree/<folder_name>
```

Direct argument fast path:

- invocation이 `hyper-git worktree <ARGUMENT>`이면 `<ARGUMENT>`를 create target으로 취급하고 어떤 worktree를 만들지 묻지 않는다.
- PR, issue, ref, explicit path를 명확히 나타내지 않는 한 argument를 branch/task label로 해석한다.
- Git operation에는 branch/ref text를 보존하고 `.hyper/worktree/<folder_name>`의 folder label만 sanitize한다.
- unsafe, reserved, conflicting, unmappable argument에 대해서만 계속 질문한다.

Interaction language:

- Clarification question은 사용자 요청과 같은 언어로 묻는다.
- 한국어 사용자에게는 한국어로만 묻는다. English fallback text나 generic English operation menu를 보여주지 않는다.
- 묻기 전에 사용자 wording에서 operation을 추론한다. 추론이 실패하면 "어떤 worktree 작업을 원하시나요? 생성, 목록, 열기/이동, 삭제, 정리, 복구, 잠금 중에서 알려주세요."처럼 localized question 하나를 묻는다.
- 새 worktree의 work intent만 빠졌다면 operation이 아니라 work intent를 묻는다.

Worktree를 만들기 전에 거기서 무엇을 할지 확정한다.

- direct `hyper-git worktree <ARGUMENT>` argument가 있으면 그것이 work intent다. work-intent question을 건너뛴다.
- 사용자가 이미 branch, PR, issue, task, concrete work item을 명명했다면 그 context를 사용한다.
- 사용자가 worktree 생성만 말했고 task가 불명확하면 생성 전에 정확히 하나의 concise localized question을 묻는다. 한국어 사용자에게는 "이 worktree에서 어떤 작업을 할 예정인가요?"라고 묻는다.
- 답변에서 `<folder_name>`을 도출한다. 사용자가 명시적으로 원하지 않는 한 random timestamp나 generic `worktree-1`을 사용하지 않는다.

Naming rules:

- 짧은 task label을 선호한다: `feature-auth`, `fix-login`, `review-pr-42`, `agent-docs-pass`.
- 실제 branch name은 folder name과 별도로 보존한다.
- explicit slug algorithm으로 folder name을 sanitize한다. task label을 lowercase로 만들고 `/`, whitespace, shell-sensitive character를 `-`로 바꾸며, 반복 separator를 collapse하고 leading/trailing separator를 trim한 뒤 `.`, `..`, `.git`, `main`, empty slug 같은 reserved label을 reject한다.
- sanitized slug가 너무 generic하면(`worktree`, `task`, `new-worktree`) folder 생성 전에 사용자 stated intent에서 concrete noun 하나를 추가한다.
- 너무 긴 label은 읽을 수 있는 길이로 제한하고 target path가 이미 있으면 numeric suffix를 추가한다.
- 사용자가 명시적으로 요청하지 않은 경우에만 repository 밖 path를 거부한다.
- 사용자가 명시적으로 요청하고 nesting risk를 이해하지 않는 한 existing linked worktree 안에 worktree를 만들지 않는다.

이 project의 요청 convention은 repository 아래에 worktree를 nest하므로 항상 root가 local에서 ignored되도록 보장한다.

```bash
exclude_file="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$exclude_file")"
grep -qxF ".hyper/worktree/" "$exclude_file" 2>/dev/null || printf '\n.hyper/worktree/\n' >> "$exclude_file"
```

사용자가 convention을 commit하라고 요청하지 않는 한 `.gitignore` 편집보다 local exclude를 선호한다.

## 3. Worktree 생성

### 현재 `HEAD`에서 새 branch

```bash
git worktree add -b <branch> <path> HEAD
```

### base branch에서 새 branch

```bash
git fetch --all --prune
git worktree add -b <branch> <path> <base-ref>
```

### 기존 local branch

```bash
git worktree add <path> <branch>
```

Git이 branch가 이미 다른 곳에서 checked out되었다고 보고하면 duplicate checkout을 force하지 말고 기존 worktree를 list하고 open한다.

### 기존 remote branch

```bash
git fetch --all --prune
git worktree add --track -b <branch> <path> origin/<branch>
```

현재 worktree를 바꾸지 않고 새 worktree 안에 local tracking branch를 만든다. 여기서 `git switch --track`은 사용자의 현재 worktree를 바꾸므로 쓰지 않는다.

### Detached review

```bash
git worktree add --detach <path> <commit-or-tag>
```

Detached worktree는 read-only inspection, bisect-like diagnostics, 또는 explicit throwaway review에만 사용한다.

생성 후 worktree가 존재하는지 검증하고 follow-up work의 active context로 만든다. "enter", "open", "switch", "go into it", "들어가", "이동", "전환" 또는 같은 의미의 한국어 표현이 있는 create request는 새 path에서 follow-up command가 실행될 때까지 완료되지 않는다.

```bash
git -C <path> status --short --branch
# In a normal interactive shell:
cd <path> && pwd

# In persistent agent shells/sessions, actually run cd <path> there.
# In tool-only environments, run the next command with workdir=<path>, or use git -C <path>.
```

Persistent shell, tmux pane, CLI session에서 "worktree로 이동"은 active session에서 실제로 `cd <path>`를 실행하고 `pwd`로 검증한다는 뜻이다. subprocess의 `cd`가 지속되지 않는 agent environment에서는 이 task의 다음 및 이후 tool call에 `workdir=<path>`를 설정하거나 equivalent tool working-directory field를 사용한다. `cd <path>`를 출력만 했다면 active context가 이동했다고 주장하지 않는다. 사용한 move mechanism을 보고한다: persistent-session `cd <path>` 또는 tool `workdir=<path>`.

## 4. 이동, 열기, handoff

생성 후 active agent context를 folder로 전환한 다음 사용 가능한 handoff command를 하나 이상 제공한다.

```bash
cd <path>
pwd
code <path>
cursor <path>
tmux new-session -A -s <folder_name> -c <path>
```

AI-agent workflow에서는 task와 boundary를 명시적으로 hand off한다.

- branch name
- worktree path
- target files 또는 ownership boundary
- verification command
- merge/cleanup expectation

사용자가 요청했거나 현재 skill invocation이 그 action을 명확히 포함하지 않는 한 external editor 또는 agent command를 시작하지 않는다. Active agent command context를 새 worktree로 이동하는 것은 creation의 일부이며 추가 confirmation이 필요 없다.

## 5. 목록과 상태 dashboard

Git registry와 per-worktree status를 모두 사용한다.

```bash
git worktree list --porcelain
git worktree list --verbose
git worktree list --porcelain | awk '/^worktree / {print substr($0, 10)}' | while IFS= read -r p; do
  printf '\n== %s ==\n' "$p"
  git -C "$p" status --short --branch || printf 'missing path (check the prunable annotation)\n'
done
```

다음을 보고한다.

- path
- branch 또는 detached commit
- clean/dirty state
- locked/prunable annotation
- recommended next action

## 6. 안전한 removal

제거 전에:

```bash
git -C <path> status --short --branch
git -C <path> log --oneline --decorate -5
```

사용자가 이미 linked worktree 안에 있으면서 path 없이 worktree delete/remove를 요청하면 current linked worktree를 target으로 추론한다. 밖으로 이동하기 전에 target path를 저장하고, main worktree는 거부한 뒤, 다른 safe worktree에서 remove한다.

```bash
target_path="$(git rev-parse --show-toplevel)"
git_dir="$(git rev-parse --git-dir)"
common_dir="$(git rev-parse --git-common-dir)"
main_path="$(git worktree list --porcelain | awk 'NR==1 && /^worktree / {print substr($0, 10)}')"

# If git-dir and common-dir resolve to the same directory, this is the main worktree; do not remove it.
# Also stop when Git cannot provide a distinct safe worktree to run removal from.
if [ "$(cd "$git_dir" && pwd -P)" = "$(cd "$common_dir" && pwd -P)" ] || [ -z "$main_path" ] || [ "$main_path" = "$target_path" ]; then
  echo "Refusing to remove this path as a linked worktree: $target_path" >&2
  git worktree list --porcelain >&2
  exit 1
fi

git -C "$target_path" status --short --branch
git -C "$target_path" log --oneline --decorate -5
cd "$main_path"
git worktree remove "$target_path"
```

Target worktree 안에서 `git worktree remove .` 또는 `rm -rf .`를 실행하지 않는다. `main_path`를 resolve할 수 없으면 추측하지 말고 target path와 `git worktree list --porcelain` output을 보고한 뒤 중단한다.

Safe removal path:

```bash
git worktree remove <path>
```

사용자가 명시적으로 요청했거나 변경사항이 disposable임을 이미 확인했을 때만 force를 사용한다. Dirty current-worktree deletion도 `--force` 전에 같은 explicit force/discard intent가 필요하다.

```bash
git worktree remove --force <path>
```

Branch deletion은 별도이며 explicit해야 한다.

```bash
git branch -d <branch>
# use -D only when explicitly requested and disposable
```

Main worktree는 절대 삭제하지 않는다. Main worktree 안에서 path 없는 "워크트리 삭제" 같은 요청이 오면 repository root를 disposable로 취급하지 말고 linked worktree path/name을 물어본다.

## 7. Prune, lock, unlock, repair

Prune은 dry run 이후에만 한다.

```bash
git worktree prune --dry-run
git worktree prune
```

Long-lived 또는 externally stored worktree는 lock한다.

```bash
git worktree lock --reason "<reason>" <path>
git worktree unlock <path>
```

Path를 수동으로 옮겼다면 recreate하기 전에 repair한다.

```bash
git worktree repair <path>
```

연결된 워크트리는 Git으로 옮겨 레지스트리 항목이 따라오게 한다. 잠긴 워크트리는 먼저 잠금을 해제해야 한다.

```bash
git worktree move <path> <new-path>
```

레지스트리를 해석하는 스크립트는 `git worktree list --porcelain -z`를 쓴다. 경로에 줄바꿈이 들어갈 수 있기 때문이다.

## 8. 이슈 기반 워크트리

워크트리가 GitHub 이슈를 위한 것이고 `gh`가 인증되어 있으면 `gh issue develop <n> --base <base> --name <branch> --worktree <path>`가 연결된 브랜치와 워크트리를 한 단계로 만든다(`rules/issue-workflow.md`). 경로는 여전히 2절을 따르고, 3절의 제외 등록, 검증, 컨텍스트 이동 검사도 그대로 적용한다.

## 9. 병합 복귀 인계

워크트리의 작업이 끝나면:

1. 상태가 깨끗하거나 의도적으로 스테이징·커밋되었는지 검증한다.
2. 그 워크트리에서 프로젝트의 테스트와 빌드를 실행한다.
3. 프로젝트의 워크플로(`rules/branch-workflow.md`)에 따라 병합하고, rebase하거나, PR을 연다.
4. 작업이 병합, 푸시, 또는 의도적으로 버려진 뒤에만 워크트리를 제거한다. squash나 cherry-pick 병합은 `git branch --merged`로 증명되지 않으므로, `+` 줄이 없는 `git cherry <target> <branch>`나 병합된 풀 리퀘스트로 확인한다.
5. 오래된 메타데이터는 먼저 dry run으로 정리한다.

## 10. 흔한 위험

- `.hyper/worktree/` 아래 중첩 워크트리는 로컬에서 무시되어야 한다. 그렇지 않으면 메인 워크트리가 지저분해진다.
- 같은 브랜치는 보통 두 워크트리에서 동시에 체크아웃할 수 없다.
- 연결된 워크트리는 Git 객체 저장소와 설정을 공유하지만 작업 파일은 독립적이다.
- 워크트리별 의존성 폴더, 포트, 데이터베이스, 생성 산출물은 여전히 충돌할 수 있다. 필요하면 별도 env 파일이나 포트를 쓴다.
- 한 Git 실행 파일이 만든 워크트리를 다른 실행 파일이 쓰면 Windows/WSL 경로 이식성이 깨질 수 있다.

## Sources

> 링크 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 이 규칙이 기반으로 삼는 `git worktree add`, `list`, `move`, `remove`, `prune`, `lock`, `unlock`, `repair`, `--porcelain -z`, `--detach`와 이미 체크아웃된 브랜치 오류 | <https://git-scm.com/docs/git-worktree> |
| 이슈 브랜치와 그 워크트리를 함께 만드는 `gh issue develop --worktree` | <https://cli.github.com/manual/gh_issue_develop> |
| 저장소 탐지와 로컬 제외 단계에서 쓰는 `git rev-parse --show-toplevel`, `--git-dir`, `--git-common-dir`, `--git-path info/exclude` | <https://git-scm.com/docs/git-rev-parse> |
| `.hyper/worktree/`를 status 출력에서 제외하는 로컬 제외 파일의 의미 | <https://git-scm.com/docs/gitignore> |
| 이 패키지가 네이티브 Git, 워크트리당 하나의 작업, 삭제 전 확인을 우선하는 이유 | [`../references/worktree-source-survey.ko.md`](../references/worktree-source-survey.ko.md) |
