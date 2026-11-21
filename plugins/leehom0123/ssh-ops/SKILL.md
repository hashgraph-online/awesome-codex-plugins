---
name: ssh-ops
description: >
  Operate remote SSH servers through the bundled CLI and YAML server configurations.
  Use for remote commands, service restarts, log inspection, file transfer, text edits,
  deployments, background jobs, and aliases on bash/cmd/powershell servers, even when
  the user does not explicitly mention SSH. Local-only builds and GitHub releases
  without a remote server operation are outside this skill's scope.
  Trigger keywords: deploy, release, ship, server health, SSH, run on server,
  upload script, download file, server alias, 部署, 上线, 发布, 重启, 查看日志, 服务器健康检查.
---

# ssh-ops CLI skill

[中文参考](zh-CN/SKILL.md)

## Locate the tool and target

Use the directory containing this skill file as the tool root to locate `cli.py`. Use a Python interpreter with the project's dependencies installed. Do not assume the user's project contains `cli.py`, and do not change the user's project working directory just to run this tool. The `python cli.py` examples below are shorthand: invoke the confirmed interpreter and CLI by absolute path. Local file paths resolve against the current working directory.

Reuse an interpreter already confirmed for this installation; otherwise check the checkout's virtual environment or the configured interpreter before installing anything. For example, after replacing the paths with the actual installation:

```bash
/absolute/path/to/python /absolute/path/ssh-ops/cli.py my-server run "uptime"
```

Use `list-servers` to confirm server names. Do not guess names or substitute listing indexes for names. Before reusing an operation, use `list-aliases` to inspect its command, sudo setting, and timeout. Do not repeat discovery already completed for the same task. Read the [installation guide](docs/install.md) only when dependencies or configuration are missing.

## Choose the operation

- Prefer a suitable existing alias after checking that its content, target, and privileges match the task.
- Use `run` for ad hoc checks. For complex quoting, `$`, or multiline commands, use `run -` with a quoted heredoc to avoid local shell expansion.
- Use text I/O for small configurations and log excerpts. Transfer binary files, large files, or text that must be preserved exactly; do not concatenate paged text as a lossless copy.
- Use background jobs for operations likely to exceed one request's wait time. Save the returned job ID and query its status. Background jobs require a bash server.
- For deployment, read the [deployment chapter](docs/deploy.md) before generating and executing project scripts. Do not improvise a sequence of release commands.

## Command quick reference

Server operations in the table are prefixed with `python cli.py <server>`. Full options and defaults are maintained only in the [CLI reference](docs/cli.md).

| Purpose | Command |
|---|---|
| Discover servers | `python cli.py list-servers` |
| Inspect and run aliases | `list-aliases`, `alias <name>` |
| Execute commands | `run '<command>'`; use `run -` to read complex commands from stdin |
| Upload and run scripts | `upload <local>`, `run-script <name>`, `upload-all`, `list-scripts` |
| Transfer files | `upload-file <local> <remote>`, `download-file <remote> <local>` |
| Download directories and scripts | `download <remote> <local>`, `download-script <name> <local>` |
| Read and write text | `read-file <remote>`, `write-file <remote> < input.txt` |
| Long-running work | `job-start '<command>'` → `job-status <id>`; use `job-kill <id>` when termination is needed |
| List jobs | `job-list` |

For creating, updating, copying, or deleting local server configurations, choose the specific command from the [CLI reference](docs/cli.md). Do not modify local configuration files through remote operations.

## Important rules

- Put options after positional arguments. There is no `--overwrite`: transfers overwrite by default, and selected transfer commands accept `--no-overwrite`.
- Use CLI `-s` for sudo; never embed passwords in commands. Aliases use YAML privilege and timeout settings, not CLI `-s/-t` overrides.
- Read a remote configuration before modifying it and retain a recoverable copy. Validate with the application's own checks before restarting.
- Act when the user has clearly authorized the operation and the target and scope are clear. Ask when the target, deletion scope, or required privileges are unclear; do not ask again for authorization already given.
- Use CLI `run`, `run-script`, or `alias` for live output; MCP does not stream execution progress.
- Text paging, sudo staging, command filtering, and path restrictions have limits documented in the [runtime reference](docs/reference.md). Regex filtering is not a sandbox.

## Deployment

Follow the [deployment chapter](docs/deploy.md): confirm the server, region, mode, directory, ports, and health endpoint, then generate project-specific local and server scripts. The [deploy/scripts/](deploy/scripts/) templates require customization; they are not ready-to-run universal release tools. Route all remote interaction through this CLI. The deployment chapter is the authority for package-source and health-check rules.

## Verify and report

Successful startup is not task completion. Inspect operation exit codes and actual output. For background jobs, check the final state and job exit code; for releases and restarts, also check application health. A successful local CLI exit alone is insufficient.

A normal command timeout does not guarantee that its remote process stopped. After a timeout or disconnect, inspect remote jobs, processes, and service state before deciding whether to retry. Avoid duplicate deployments or migrations.

Report the target server, operations actually performed, and verification results. State what remains incomplete or unverified. If work is still running, include the job ID rather than claiming completion.

For the MCP interface, see [SKILL.mcp.md](SKILL.mcp.md).
