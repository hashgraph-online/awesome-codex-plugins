---
name: ssh-ops
description: >
  Operate Linux and Windows servers over SSH using YAML configurations.
  Use for remote commands, aliases, SFTP transfers, text editing, deployments,
  and background jobs on bash servers. Local-only builds and GitHub releases
  without a remote operation are outside this skill's scope.
---

# SSH Ops plugin entry point

The tool root is two directories above this file, not this skill directory.
Read [the CLI operating guide](../../SKILL.md) before using the CLI, or
[the MCP operating guide](../../SKILL.mcp.md) before using the bundled MCP tools.
These are alternative guides for the same skill, not additional skills to register.

Confirm the configured server and inspect aliases before execution. Only perform
remote changes the user has authorized. Read remote text before editing it;
check operation exit codes and final job or service state before reporting success.
For deployments, follow [the deployment chapter](../../docs/deploy.md).
