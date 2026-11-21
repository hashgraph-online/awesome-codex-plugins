# Git Worktree Source Survey

Read this only when the rationale, upstream behavior, or a source comparison needs support. The survey captures patterns distilled from public Git worktree documentation, tools, editor integrations, and AI-agent workflows; operational rules stay in `rules/worktree-lifecycle.md`.

## Sources

> Links checked 2026-09-21. Each of the 17 numbered entries below answered HTTP 200 on that date.

1. **Official Git `git-worktree` documentation** — authoritative command behavior for `add`, `list`, `remove`, `prune`, `lock`, `unlock`, `repair`, `--porcelain`, and annotations.  
   URL: https://git-scm.com/docs/git-worktree.html
2. **Anthropic Claude Code best practices** — recommends parallel sessions and isolated worktrees for scaling coding agents.  
   URL: https://code.claude.com/docs/en/best-practices
3. **incident.io: Shipping faster with Claude Code and Git Worktrees** — practical team workflow around multiple agents, helper functions, completion, and branch/path conventions.  
   URL: https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees
4. **Worktrunk** — branch-addressed CLI with computed paths, core commands, hooks, agent integration, merge/remove flow, CI/PR links.  
   URL: https://github.com/max-sixty/worktrunk
5. **ccswitch** — worktree session tool emphasizing quick session creation, interactive session list, shell integration, smart cleanup, and bulk cleanup.  
   URL: https://ccswitch.dev/
6. **Etz** — multi-repository worktree manager with parallel execution, safe operations, interactive mode, and CLI/desktop split.  
   URL: https://www.etz.dev/
7. **Cline worktrees** — VS Code/Cline workflow with create-and-open windows, full worktree view, merge button, current/main/locked display, and deletion warnings.  
   URL: https://docs.cline.bot/features/worktrees
8. **VS Code Git Branches and Worktrees docs** — editor-native branch/worktree flows and issue-to-branch integration patterns.  
   URL: https://code.visualstudio.com/docs/sourcecontrol/branches-worktrees
9. **VS Code Git Worktrees extension** — command-palette operations, configurable worktree directory, open-new-window default, auto-push/pull, and copy-include patterns.  
   URL: https://marketplace.visualstudio.com/items?itemName=GitWorktrees.git-worktrees
10. **gwq** — fuzzy-finder CLI with global worktree management, status dashboard, tmux integration, and shell completion.  
    URL: https://github.com/d-kuro/gwq
11. **ThePrimeagen/git-worktree.nvim** — editor plugin pattern; highlights bare-repo friendliness and editor-local logs/debuggability.  
    URL: https://github.com/ThePrimeagen/git-worktree.nvim
12. **worktree.io** — issue-to-workspace pattern through GitHub Actions, URL handler, local daemon, and editor launch.  
    URL: https://worktree.io/
13. **IntelliJ IDEA worktree docs** — IDE-native worktree tab, AI/hotfix/review/long-running use cases, warning against nesting inside the current project, and commit-before-delete guidance.  
    URL: https://www.jetbrains.com/help/idea/use-git-worktrees.html
14. **LazyWorktree** — keyboard-first TUI with worktree lifecycle, PR/CI awareness, tmux/zellij sessions, hooks, notes, and taskboard.  
    URL: https://chmouel.github.io/lazyworktree/
15. **Par** — parallel worktree/session manager for AI coding assistants with tmux sessions, global labels, remote command execution, control center, and multi-repo workspaces.  
    URL: https://github.com/coplane/par
16. **git-worktree-cli** — lightweight CLI with automatic path generation, IDE/terminal/Claude launch flags, simple add/list/remove commands, and branch handling.  
    URL: https://pypi.org/project/git-worktree-cli/
17. **GitExtensions worktree docs** — GUI support and WSL/native-path warning.  
    URL: https://git-extensions-documentation.readthedocs.io/en/release-4.2/worktrees.html

## Advantages distilled into this skill

- **Native Git first**: Use official `git worktree` behavior as the stable base; wrap it with disciplined checks rather than depending on a new package.
- **One task equals one worktree**: Popular AI-agent workflows converge on one branch, one folder, one terminal/editor/agent session per task.
- **Predictable path convention**: Tools reduce friction by computing paths. This skill standardizes on `.hyper/worktree/<folder_name>`.
- **Branch and folder are separate concepts**: Keep Git branch names meaningful while sanitizing folder labels for safe local paths.
- **Interactive/list visibility matters**: Good tools expose list/status dashboards. This skill requires `git worktree list --porcelain` plus per-path `git status` when listing.
- **Safe cleanup is a first-class operation**: Tools and IDEs warn before deletion; this skill requires status inspection before `remove` and dry run before `prune`.
- **Editor/session handoff reduces context switching**: Common integrations open VS Code/Cursor/IDE/tmux directly in the worktree. This skill reports handoff commands and runs them only when requested.
- **Hooks and setup are useful but optional**: Worktrunk, LazyWorktree, and Par show value in setup hooks; this skill leaves hook automation to projects unless requested.
- **Parallel agents need more than file isolation**: Worktrees prevent file conflicts, but ports, databases, dependency caches, and env files may still collide.
- **Issue/PR-driven creation is high leverage**: worktree.io, LazyWorktree, and VS Code patterns show that PR/issue/task labels are natural folder and branch seeds.
- **Global labels help humans navigate many contexts**: Par/gwq/ccswitch show that short labels and dashboards are critical when many worktrees exist.
- **Repair/lock/prune are real lifecycle states**: Official Git and IDE tools surface locked/prunable states; the skill keeps them in the operator workflow.
- **Nested worktrees are controversial**: The user-requested `.hyper/worktree/` convention is convenient for project locality, but IDE docs warn against nesting under the current project. This skill mitigates noise with local excludes and calls out IDE/runtime risks.
- **Cross-platform paths can bite**: GitExtensions notes Windows/WSL native path issues; avoid assuming worktrees created by one Git executable are portable to another.

## Forward-test prompts

Use these prompts to evaluate whether the skill triggers and behaves correctly:

1. "Create a worktree for `fix/api-timeout` under `.hyper/worktree` and open Cursor there."
2. "List all worktrees and tell me which ones are dirty."
3. "Remove the stale worktree for `experiment-cache`, but don't delete the branch."
4. "Spin up Codex and Claude in two separate branches without conflicts."
5. "Checkout PR 123 for review in a temporary worktree."
6. "Prune stale worktree metadata safely."
7. "I moved a worktree folder manually and Git is confused; repair it."
8. "Create a Docker compose environment per branch." Should route away unless Git worktree setup is only one part of the request.
