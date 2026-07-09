# NTM Command Patterns

Use this file when the main `ntm` skill body is not enough and you need the denser
operator command patterns that make NTM powerful in practice.

## Contents

- [Session Lifecycle](#session-lifecycle) — quick, spawn, scale, rebalance, adopt
  - [Agent Count Heuristics](#agent-count-heuristics)
- [High-Leverage Send Patterns](#high-leverage-send-patterns) — targeting, file-backed, smart routing, distribute
- [Monitoring and Output](#monitoring-and-output) — capture, activity, health, diff
  - [Human-Only Surfaces](#human-only-surfaces) — dashboard, palette, bind
- [Work Intelligence](#work-intelligence) — triage, alerts, impact, assign
- [Coordination, Recovery, and Durable State](#coordination-recovery-and-durable-state) — mail, locks, checkpoint, timeline, resume, handoff
  - [Controller Agents](#controller-agents)
- [Reusable Assets](#reusable-assets) — recipes, workflows, templates

---

## Session Lifecycle

```bash
ntm quick myproject --template=go       # template = go | python | node | rust
ntm quick myproject --label frontend

ntm spawn myproject --cc=3 --cod=2 --gmi=1
ntm spawn myproject --label frontend --cc=3
ntm spawn myproject --label backend --cc=2 --worktrees
ntm spawn myproject --no-user --cc=5 --cod=5
ntm spawn myproject --stagger-mode=smart   # smart | fixed | none
ntm add myproject --cc=2
ntm add myproject --label frontend --cc=1

ntm list
ntm status myproject
ntm attach myproject
ntm zoom myproject 1
ntm kill myproject
ntm kill --project myproject

# Adjust a running swarm without re-spawning
ntm scale myproject --cc=4
ntm rebalance myproject
ntm respawn myproject           # revive dead panes in place
ntm swarm plan                  # dry-run spawn
ntm swarm status
ntm swarm stop <pattern>

# Adopt an existing external tmux session into ntm
ntm adopt <session>
```

> `ntm view` is a human-operator command that retiles the tmux layout. Do not call it from agent code — use `--robot-tail`, `--robot-snapshot`, or `--robot-inspect-pane` instead.

### Agent Count Heuristics

- `--cc=3 --cod=2 --gmi=1`: good default mixed swarm
- `--cc=5`: architecture-heavy, lower coordination load
- `--cc=2 --cod=3`: straightforward implementation volume
- `--cc=5 --cod=5`: larger swarm only when the operator loop is already healthy

## High-Leverage Send Patterns

```bash
# Basic targeting
ntm send myproject --cc "Review the API design"
ntm send myproject --cod --gmi "Run tests and summarize failures"
ntm send myproject --all "Checkpoint and summarize current state"
ntm send myproject --pane=2 "You own the auth migration."
ntm send myproject --panes=2,3 "Pair on the broken build."

# Broadcast across labeled sessions for one base project
ntm send --project myproject "Sync to main and report blockers."

# File-backed prompts, stdin, and reusable wrappers
ntm send myproject --file prompts/review.md
git diff | ntm send myproject --all --prefix "Review these changes:"
ntm send myproject --base-prompt-file ./common-instructions.txt --file ./task.txt

# File context and templates
ntm send myproject -c internal/auth/service.go "Refactor this safely"
ntm send myproject -c a.go -c b.go "Compare these implementations"
ntm send myproject -t fix --var issue="nil pointer" --file internal/auth/service.go

# Smart routing and automated distribution
ntm send myproject --smart "Take the next auth follow-up"
ntm send myproject --smart --route=affinity "Continue the migration work"
ntm send myproject --distribute --dist-strategy=dependency
ntm send myproject --distribute --dist-auto --dist-strategy=balanced

# Batch / randomized sends
ntm send myproject --batch prompts.txt --delay=5s
ntm send myproject --batch prompts.txt --broadcast
ntm send myproject --all --randomize
```

## Monitoring and Output

```bash
# Output capture
ntm copy myproject:1
ntm copy myproject --all
ntm copy myproject --cc
ntm copy myproject --code
ntm save myproject

# Activity and stream monitoring
ntm activity myproject --watch
ntm health myproject
ntm watch myproject --cc
ntm logs myproject --panes=1,2

# Compare / inspect
ntm extract myproject --lines=200
ntm diff myproject cc_1 cod_1
ntm grep "timeout" myproject -C 3
```

### Human-Only Surfaces

These are excellent for operators, but not for agents driving automation:

```bash
ntm dashboard myproject
ntm palette myproject
ntm bind
ntm tutorial
```

## Work Intelligence

```bash
ntm work triage
ntm work triage --by-label
ntm work triage --by-track
ntm work triage --format=markdown --compact
ntm work alerts
ntm work search "JWT authentication"
ntm work impact internal/api/auth.go
ntm work next
ntm work history
ntm work forecast br-123
ntm work graph
ntm work label-health
ntm work label-flow
```

Use `ntm assign` when you want NTM to help push work onto panes instead of just
observing the graph:

```bash
ntm assign myproject --auto --strategy=dependency
ntm assign myproject --beads=br-123,br-124 --agent=codex
```

## Coordination, Recovery, and Durable State

```bash
ntm mail send myproject --all "Report blockers and current file focus."
ntm mail inbox myproject                        # or: ntm mail inbox myproject --json
ntm locks list myproject --all-agents
ntm locks renew myproject --extend 30           # minutes
ntm locks force-release myproject 42 --note "agent inactive"
ntm coordinator status myproject                # alias: ntm coord status
ntm coordinator digest myproject
ntm coordinator conflicts myproject
ntm coordinator enable auto-assign              # background automation
ntm coordinator enable digest --interval=30m

ntm checkpoint save myproject -m "before risky refactor"
ntm checkpoint list myproject
ntm checkpoint restore myproject                # optional <id> positional
ntm checkpoint export myproject <id>            # portable archive
ntm checkpoint import <archive>
ntm checkpoint verify myproject
ntm checkpoint show myproject <id>

ntm timeline list
ntm timeline show <session-id>
ntm timeline stats
ntm history search "authentication error"
ntm audit show myproject
ntm audit search "<pattern>"

# changes vs conflicts are TWO separate top-level commands (not a nested form):
ntm changes myproject                           # recent attributable file changes
ntm conflicts myproject --since 6h --limit 10   # files touched by multiple agents

ntm resume myproject

# Cross-session handoff bundles
ntm handoff create myproject
ntm handoff list
ntm handoff show <path>
ntm handoff ledger
```

### Controller Agents

```bash
ntm controller myproject                        # coord agent in pane 1 (default cc)
ntm controller myproject --agent-type=cod       # cc|cod|gmi|cursor|windsurf|ws|aider|ollama
ntm controller myproject --prompt=ctrl.txt      # template vars: {{.Session}} {{.AgentList}} {{.ProjectDir}}
ntm controller myproject --no-prompt            # launch agent but send no initial prompt
```

Worktree-specific commands when repo policy allows them:

```bash
ntm worktrees list
ntm worktrees merge claude_1
ntm worktrees clean --session myproject
```

## Reusable Assets

```bash
ntm recipes list
ntm recipes show full-stack
ntm workflows list
ntm workflows show red-green
ntm template list
ntm template show fix-bug
ntm session-templates list
ntm session-templates show refactor
```

Use these when you want repeatable swarm composition rather than bespoke commands every time.
