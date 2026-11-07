# Git Worktree 소스 조사

근거, upstream 동작, 출처 비교에 지원이 필요할 때만 읽는다. 이 조사는 공개 Git worktree 문서, 도구, editor integration, AI-agent workflow에서 추출한 패턴을 기록하며, operational rule은 `rules/worktree-lifecycle.md`에 유지한다.

## Sources

> 링크 확인 2026-09-21. 아래 17개 항목의 URL은 같은 날짜에 요청해 모두 HTTP 200을 받았습니다.

1. **공식 Git `git-worktree` 문서** — `add`, `list`, `remove`, `prune`, `lock`, `unlock`, `repair`, `--porcelain`, annotation의 authoritative command behavior.  
   URL: https://git-scm.com/docs/git-worktree.html
2. **Anthropic Claude Code best practices** — coding agent를 확장하기 위해 parallel session과 isolated worktree를 권장한다.  
   URL: https://code.claude.com/docs/en/best-practices
3. **incident.io: Shipping faster with Claude Code and Git Worktrees** — multiple agent, helper function, completion, branch/path convention을 둘러싼 실무 team workflow.  
   URL: https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees
4. **Worktrunk** — computed path, core command, hook, agent integration, merge/remove flow, CI/PR link를 갖춘 branch-addressed CLI.  
   URL: https://github.com/max-sixty/worktrunk
5. **ccswitch** — 빠른 session creation, interactive session list, shell integration, smart cleanup, bulk cleanup을 강조하는 worktree session tool.  
   URL: https://ccswitch.dev/
6. **Etz** — parallel execution, safe operation, interactive mode, CLI/desktop split을 갖춘 multi-repository worktree manager.  
   URL: https://www.etz.dev/
7. **Cline worktrees** — create-and-open window, full worktree view, merge button, current/main/locked display, deletion warning을 갖춘 VS Code/Cline workflow.  
   URL: https://docs.cline.bot/features/worktrees
8. **VS Code Git Branches and Worktrees docs** — editor-native branch/worktree flow와 issue-to-branch integration pattern.  
   URL: https://code.visualstudio.com/docs/sourcecontrol/branches-worktrees
9. **VS Code Git Worktrees extension** — command-palette operation, configurable worktree directory, open-new-window default, auto-push/pull, copy-include pattern.  
   URL: https://marketplace.visualstudio.com/items?itemName=GitWorktrees.git-worktrees
10. **gwq** — global worktree management, status dashboard, tmux integration, shell completion을 갖춘 fuzzy-finder CLI.  
    URL: https://github.com/d-kuro/gwq
11. **ThePrimeagen/git-worktree.nvim** — editor plugin pattern. bare-repo friendliness와 editor-local logs/debuggability를 강조한다.  
    URL: https://github.com/ThePrimeagen/git-worktree.nvim
12. **worktree.io** — GitHub Actions, URL handler, local daemon, editor launch를 통한 issue-to-workspace pattern.  
    URL: https://worktree.io/
13. **IntelliJ IDEA worktree docs** — IDE-native worktree tab, AI/hotfix/review/long-running use case, current project 내부 nesting 경고, delete 전 commit guidance.  
    URL: https://www.jetbrains.com/help/idea/use-git-worktrees.html
14. **LazyWorktree** — worktree lifecycle, PR/CI awareness, tmux/zellij session, hook, note, taskboard를 갖춘 keyboard-first TUI.  
    URL: https://chmouel.github.io/lazyworktree/
15. **Par** — tmux session, global label, remote command execution, control center, multi-repo workspace를 갖춘 AI coding assistant용 parallel worktree/session manager.  
    URL: https://github.com/coplane/par
16. **git-worktree-cli** — automatic path generation, IDE/terminal/Claude launch flag, simple add/list/remove command, branch handling을 갖춘 lightweight CLI.  
    URL: https://pypi.org/project/git-worktree-cli/
17. **GitExtensions worktree docs** — GUI support와 WSL/native-path warning.  
    URL: https://git-extensions-documentation.readthedocs.io/en/release-4.2/worktrees.html

## 이 스킬에 반영한 장점

- **Native Git first**: 공식 `git worktree` 동작을 안정적인 기반으로 사용한다. 새 package에 의존하기보다 disciplined check로 감싼다.
- **하나의 task는 하나의 worktree**: 인기 있는 AI-agent workflow는 task마다 하나의 branch, folder, terminal/editor/agent session으로 수렴한다.
- **예측 가능한 path convention**: 도구들은 path를 계산해 friction을 줄인다. 이 skill은 `.hyper/worktree/<folder_name>`을 표준화한다.
- **Branch와 folder는 별개 개념**: Git branch name은 의미 있게 유지하고 folder label만 safe local path로 sanitize한다.
- **Interactive/list visibility가 중요하다**: 좋은 도구는 list/status dashboard를 노출한다. 이 skill은 list 시 `git worktree list --porcelain`과 per-path `git status`를 요구한다.
- **Safe cleanup은 일급 operation이다**: 도구와 IDE는 삭제 전 경고한다. 이 skill은 `remove` 전 status inspection과 `prune` 전 dry run을 요구한다.
- **Editor/session handoff가 context switching을 줄인다**: 일반 integration은 VS Code/Cursor/IDE/tmux를 worktree에서 직접 연다. 이 skill은 handoff command를 보고하고 요청된 경우에만 실행한다.
- **Hook과 setup은 유용하지만 선택 사항이다**: Worktrunk, LazyWorktree, Par는 setup hook의 가치를 보여준다. 이 skill은 요청되지 않는 한 hook automation을 project에 맡긴다.
- **Parallel agent에는 file isolation 이상의 것이 필요하다**: Worktree는 file conflict를 막지만 port, database, dependency cache, env file은 여전히 충돌할 수 있다.
- **Issue/PR-driven creation은 leverage가 높다**: worktree.io, LazyWorktree, VS Code pattern은 PR/issue/task label이 자연스러운 folder와 branch seed임을 보여준다.
- **Global label은 많은 context를 탐색하는 사람에게 도움이 된다**: Par/gwq/ccswitch는 많은 worktree가 있을 때 short label과 dashboard가 중요함을 보여준다.
- **Repair/lock/prune은 실제 lifecycle state다**: 공식 Git과 IDE tool은 locked/prunable state를 노출한다. 이 skill은 이를 operator workflow에 유지한다.
- **Nested worktree는 논쟁적이다**: 사용자가 요청한 `.hyper/worktree/` convention은 project locality에 편리하지만, IDE 문서는 current project 아래 nesting을 경고한다. 이 skill은 local exclude로 noise를 줄이고 IDE/runtime risk를 명시한다.
- **Cross-platform path가 문제를 일으킬 수 있다**: GitExtensions는 Windows/WSL native path issue를 언급한다. 한 Git executable이 만든 worktree가 다른 executable에서도 portable하다고 가정하지 않는다.

## Forward-test 프롬프트

다음 프롬프트로 skill이 올바르게 trigger되고 동작하는지 평가한다.

1. "Create a worktree for `fix/api-timeout` under `.hyper/worktree` and open Cursor there."
2. "List all worktrees and tell me which ones are dirty."
3. "Remove the stale worktree for `experiment-cache`, but don't delete the branch."
4. "Spin up Codex and Claude in two separate branches without conflicts."
5. "Checkout PR 123 for review in a temporary worktree."
6. "Prune stale worktree metadata safely."
7. "I moved a worktree folder manually and Git is confused; repair it."
8. "Create a Docker compose environment per branch." Git worktree setup이 request의 일부일 뿐인 경우가 아니면 route away해야 한다.
