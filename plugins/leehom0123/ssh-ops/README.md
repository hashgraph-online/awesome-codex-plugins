# ssh-ops

[中文](zh-CN/README.md)

SSH operations through a CLI or MCP server, using YAML server configurations and reusable command aliases.

## What it provides

- Commands, scripts, SFTP transfers, and remote text editing through the same Python core.
- A CLI for terminal use and agents; an MCP server with stdio and HTTP transports.
- YAML aliases exposed as callable MCP tools.
- Remote background jobs for long operations, and byte-paged reads for logs.
- Host-key checks, command filters, path allow-lists, and sudo support with explicit limitations documented in the reference.

The `shell` setting selects helper-command templates for `bash`, `cmd`, or `powershell`. It does not translate arbitrary commands between shells. Connections are reused within a process, not shared between separate CLI and MCP processes.

## Quick start

```bash
git clone https://github.com/leehom0123/ssh-ops.git
cd ssh-ops
python -m pip install -r requirements.txt
python cli.py list-servers
```

Add a server using the [configuration reference](docs/reference.md#configuration), then run:

```bash
python cli.py my-server run "uptime"
```

For an agent, follow the [installation guide](docs/install.md) to load the CLI skill or register MCP. No server is contacted by `list-servers`.

## Typical uses

- **Investigate an incident:** list servers and aliases, collect service logs and system metrics, then inspect the evidence. The tool runs commands; it does not diagnose a cause automatically.
- **Update a configuration:** read the current text, write the reviewed change, and run the application's own validation command before restarting it.
- **Run a long build or migration:** start a background job and poll its status instead of holding one MCP request open.
- **Deploy a release:** use the [scripted deployment workflow](docs/deploy.md), with a project-specific restart command and health check.

## Documentation

| Document | Purpose |
|---|---|
| [CLI skill](SKILL.md) | Agent workflow and command quick reference |
| [SKILL.mcp.md](SKILL.mcp.md) | MCP registration, 22 static tools, and dynamic alias tools |
| [CLI reference](docs/cli.md) | Exact CLI syntax, options, defaults, and output |
| [Runtime reference](docs/reference.md) | YAML fields, security, transfer/job semantics, and HTTP protocol |
| [Installation](docs/install.md) | Agent installation and verification |
| [Deployment](docs/deploy.md) | Workflow, template contract, mirrors, and troubleshooting |

Implementation: [CLI](cli.py), [MCP server](mcp_server.py), and the domain modules under [ssh_client/](ssh_client/). Python imports retain the historical `ssh_client` name.
