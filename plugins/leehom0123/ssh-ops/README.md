# ssh-ops

[中文](zh-CN/README.md)

Operate remote SSH servers from the CLI or over MCP: one Python core behind both entry points, servers defined in YAML files, and repeatable commands registered as aliases.

## Highlights

- **One core, two entry points.** Commands, scripts, SFTP transfers, remote text editing, and background jobs are implemented once in the Python core; the CLI and the MCP server (stdio and HTTP transports) differ only in how you reach them. An operation you verified in the terminal can be handed to an agent over MCP as it is.
- **Manage a fleet by name.** Each server is a YAML entry with its own host, authentication, shell, script directory, aliases, and security filters. Agents discover the set with `list-servers` and target any machine by name, operating Linux and Windows boxes through one interface. Connections may route through a SOCKS5 proxy with automatic fallback to direct, and are reused within one process, not shared between the CLI and MCP processes.
- **Aliases are ready-made tools.** Register a command or script in a server YAML as an alias, with its own timeout and sudo setting. The MCP server generates a zero-argument tool for each alias (for example `ssh_alias.my-server.health`), so the agent calls the registered operation without rebuilding the command line or deciding on privileges:

  ```yaml
  # servers/my-server.yml
  aliases:
    - name: health
      inline: "df -h /"
      desc: Check disk usage
  ```

- **Background jobs and paged reads.** Start long builds or migrations as background jobs and poll by job ID instead of holding one MCP request open; job state lives in marker files on the remote server and stays queryable after the local process or the MCP server restarts. Logs and text are read in byte-sized pages, so a large file never arrives whole in the agent's context. Background jobs require a bash server.
- **Security limits.** The host key is probed before authentication (trust-on-first-use by default, `tofu`), so a man-in-the-middle cannot capture the login password. Commands pass blacklist/whitelist filtering, transfers check local and remote path allow-lists, and the sudo password lives in the YAML, not in the command line. Regex filtering is a guardrail, not a sandbox; each limit is documented in the [runtime reference](docs/reference.md).
- **Any client OS, any server shell.** ssh-ops ships paramiko, a pure-Python SSH implementation, so the machine running it needs no system ssh client; Windows, Linux, and macOS all work. On the server side, `shell` covers bash (Linux, macOS servers) and cmd or powershell (Windows servers running the OpenSSH service); the setting picks the templates for the tool's own helper commands and does not translate user commands.

## Quick start

```bash
git clone https://github.com/leehom0123/ssh-ops.git
cd ssh-ops
python -m pip install -r requirements.txt
python cli.py list-servers
```

Add a server: write the connection fields per the [configuration reference](docs/reference.md#configuration), then install them with `python cli.py create-server my-server my-server.yml` or the MCP `ssh_create_server` tool. Then run:

```bash
python cli.py my-server run "uptime"
```

For an agent, follow the [installation guide](docs/install.md) to load the CLI skill or register MCP. Server entries are created and changed through the CLI commands or MCP tools, not by reading or editing the YAML files directly; when a user-named server is missing from `list-servers`, offer the closest names as candidates or ask for host, user, and authentication before creating it. No server is contacted by `list-servers`.

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
