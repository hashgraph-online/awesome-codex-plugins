# Swarm Mode: Agent Teams

Enable external agents (Codex, etc.) to participate in Claude Code Agent Teams by reading/writing the shared task list.

## Commands

```bash
amq swarm list                                    # Discover teams
amq swarm join --team my-team --me codex          # Join team
amq swarm tasks --team my-team                    # View tasks
amq swarm claim --team my-team --task t1 --me codex  # Claim work
amq swarm complete --team my-team --task t1 --me codex  # Mark completed work done
amq swarm fail --team my-team --task t1 --me codex --reason "tests red"  # Mark failed
amq swarm block --team my-team --task t1 --me codex --reason "waiting on API"  # Mark blocked
amq swarm bridge --team my-team --me codex        # Run task notification bridge
```

## Communication

These examples use team `my-team`, task `t1`, and handle `codex`; replace them
with the assigned values. If you add `--evidence`, include only results you
observed. Follow the task owner's rules for who may mark work complete.

Communication is asymmetric — bridge delivers task lifecycle notifications only:

- **Claude Code teammate → external agent**: works directly via `amq send`
- **External agent → Claude Code teammate**: relay through the team leader's AMQ inbox

```bash
# External agent sends to leader, noting the intended teammate
amq send --to claude --thread swarm/my-team --labels swarm \
  --subject "To: builder - question about task t1" --body "..."
```

The leader drains and forwards via Claude Code internal messaging.

## Bridge

`amq swarm bridge` watches the shared task list and delivers AMQ messages labeled `swarm` into the agent's inbox. Standard `amq wake` detects these automatically.

```bash
amq swarm bridge --team my-team --me codex --poll --poll-interval 5s &
```

## Task Workflow

1. `amq swarm list` — discover available teams
2. `amq swarm join --team <name> --me <agent>` — join a team
3. `amq swarm tasks --team <name>` — view available tasks
4. `amq swarm claim --team <name> --task <id> --me <agent>` — claim a task
5. Do the work
6. `amq swarm complete --team <name> --task <id> --me <agent> [--evidence <json>]` — mark done
7. `amq swarm fail --team <name> --task <id> --me <agent> [--reason <str>]` — mark failed
8. `amq swarm block --team <name> --task <id> --me <agent> [--reason <str>]` — mark blocked
