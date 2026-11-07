---
name: setup
description: Set up Bifrost SDK - install CLI, authenticate, configure MCP server. Use when user needs to get started with Bifrost or has incomplete setup.
---

# Bifrost Setup

## Introduction

Before running any commands, introduce the setup process to the user:

> **Bifrost SDK Setup**
>
> I'll help you set up the Bifrost SDK. This involves three steps:
> 1. **Install the CLI** - A command-line tool for developing and testing workflows
> 2. **Authenticate** - Log in to your Bifrost instance
> 3. **Configure MCP** - Connect Claude Code to Bifrost's tools
>
> Let me check your current setup status...

## Connection model

Bifrost stores credentials separately for each instance URL, so several
connections can coexist on one computer. Only `.env` in the exact invocation
directory selects a URL; ancestor dotenv files are never discovered
implicitly. Credentials remain in the global store keyed by URL and are never
loaded from `.env`. Without that local selector, the CLI uses the user's saved
default transparently.

`bifrost auth default` only reports these values; it changes nothing. Only
`bifrost auth use <url>` changes the saved default, so never run it unless the
user explicitly asks to change their default connection.

## Check Current State

Run this command to check environment (set by SessionStart hook):

```bash
echo "SDK: $BIFROST_SDK_INSTALLED | Login: $BIFROST_LOGGED_IN | MCP: $BIFROST_MCP_CONFIGURED"
echo "Python: $BIFROST_PYTHON_CMD ($BIFROST_PYTHON_VERSION) | Pip: $BIFROST_PIP_CMD | OS: $BIFROST_OS"
command -v bifrost >/dev/null && bifrost auth default
```

The environment flags are hints. When the CLI is installed, the read-only
`bifrost auth default` output is the source of truth for the current folder.
If a Codex sandbox reports no credentials, rerun that command with host access
from the exact intended workspace before entering the Login flow. Sandboxing
can hide the OS keyring; a successful host probe means the user is already
logged in and the existing connection must be reused.

## Resume Logic

Based on the environment state:

1. **All true and current connection is intended** -> Setup complete! Inform user they're ready to use `/bifrost:build`
2. **SDK installed + logged in, MCP not configured** -> SDK-first development is ready! MCP is optional — the CLI (`bifrost api`, `bifrost watch`) handles most operations. MCP is only needed for creating forms/apps/agents and knowledge search. Ask if they want to configure it.
3. **SDK not installed** -> Go to SDK Installation
4. **SDK installed but not logged in** -> Go to Login
5. **Logged in but MCP not configured** -> Go to MCP Configuration (optional)

## Windows 11 First

If `BIFROST_OS=windows` or the shell appears to be native PowerShell/CMD:

1. Ask which of three things the user wants: **deploy/run Bifrost** on this
   Windows box, **develop the platform** (contribute to the Bifrost repo), or
   **CLI-only use** against an existing instance.
2. For **deploying/running** Bifrost on Windows, use native PowerShell — no WSL
   or Bash needed. From the repo root run `.\Initialize-Bifrost.ps1` (the
   PowerShell counterpart to `setup.sh`): it generates `.env`, runs
   `docker compose up -d`, and prints the access URL. Docker Desktop must be
   installed with the **WSL2 backend** enabled. (`-Domain`, `-Force`, and
   `-NoStart` switches are available; `-Force` regenerates secrets.)
3. For **platform development** (running `./debug.sh` / `./test.sh` against the
   source), the recommended environment is Linux or macOS. On Windows these
   Bash scripts work through **Git Bash** (e.g.
   `& 'C:\Program Files\Git\bin\bash.exe' -lc './debug.sh up'`) or Ubuntu on
   WSL2 with Docker Desktop WSL integration — but native PowerShell does not run
   them. There is intentionally no PowerShell port of `debug.sh`/`test.sh`.
4. For CLI-only use, continue with native Windows setup below.
5. Check for a coding tool before MCP setup:
   - `claude --version` for Claude Code
   - `codex --version` for Codex
   - `code --version` for VS Code
   If none are installed, tell the user to install at least one before MCP or
   source-development setup. CLI-only usage can proceed without a coding tool.
6. If the repo was cloned natively on Windows, inspect `skills/setup`. If it is
   a plain file containing `../.claude/skills/bifrost-setup` instead of a
   directory/symlink, tell the user this is a Git symlink checkout issue:
   enable Developer Mode, set `git config --global core.symlinks true`, reclone,
   or run `bifrost skill update` after CLI installation.

## SDK Installation

### Prerequisites Check

**If BIFROST_PYTHON_CMD is empty:**
Python 3.11+ is required. Install based on OS:
- **ubuntu/debian**: `sudo apt install python3.11`
- **macos**: `brew install python@3.11`
- **windows native PowerShell**: Prefer
  `winget install --id Python.Python.3.11 -e`. If winget fails with
  `0x8a15000f`, run `Set-WinHomeLocation -GeoId 244`, `winget source reset
  --force`, and `winget source update`, then retry. If winget is still broken,
  install Python directly from python.org. Reopen PowerShell and verify with
  `py -3.11 --version`.

**If BIFROST_PIP_CMD is empty:**
Need pipx (recommended for CLI tools on modern systems):
- **ubuntu/debian**: `sudo apt install pipx && pipx ensurepath`
- **macos**: `brew install pipx && pipx ensurepath`
- **windows native PowerShell**: `py -3.11 -m pip install --user pipx`
  then `py -3.11 -m pipx ensurepath` and reopen PowerShell

If Windows only reports `python.exe` from `Microsoft\WindowsApps`, that is the
Microsoft Store launcher alias, not an installed Python. Install Python with
winget or python.org, then use `py -3.11` explicitly. Do not use plain
`python` until `Get-Command python` no longer points at `WindowsApps`.

### Get Bifrost URL

If `bifrost auth default` already shows the intended current connection, reuse
that URL and do not log in again.

**Otherwise:** Ask the user: "What is your Bifrost instance URL? (e.g., https://yourcompany.gobifrost.com)"

Do NOT suggest placeholder URLs - every Bifrost instance has a unique URL provided by the user's organization.

`BIFROST_DEV_URL` is an optional override for preview and platform links. Do
not use it as evidence of the authenticated CLI connection; when it is absent,
the authenticated current connection is the default link base.

### Install SDK

**Use the detected pip command** (from `$BIFROST_PIP_CMD`):

```bash
$BIFROST_PIP_CMD {url}/api/cli/download/bifrost-cli.tar.gz
```

On native Windows, prefer:

```powershell
py -3.11 -m pipx install --force {url}/api/cli/download/bifrost-cli.tar.gz
```

Verify with:
```powershell
bifrost help
```

If `bifrost` is not on PATH yet, open a new PowerShell window or run it from
`%USERPROFILE%\.local\bin\bifrost.exe`.

## Update an Existing Installation

Treat these as three independent update planes. Updating one does not update
the others; update the CLI first because it supplies the SDK-update command.

1. **CLI from the intended Bifrost instance:**
   ```bash
   pipx install --force {url}/api/cli/download/bifrost-cli.tar.gz
   bifrost --version
   ```
   On native Windows, use
   `py -3.11 -m pipx install --force {url}/api/cli/download/bifrost-cli.tar.gz`.
2. **Vendored web SDK in each Solution workspace:**
   ```bash
   cd /path/to/solution
   bifrost solution sdk update
   ```
   Review and commit the changed vendored SDK files, then rerun
   `bifrost solution start` and confirm any stale-SDK warning is gone.
3. **Installed Codex plugin:**
   ```bash
   codex plugin marketplace upgrade bifrost
   codex plugin list
   ```
   If the installed version remains stale, refresh its cached content:
   ```bash
   codex plugin remove bifrost@bifrost
   codex plugin add bifrost@bifrost
   codex plugin list
   ```
   Start a new Codex task (or restart Codex) afterward; the current task keeps
   the skill text it loaded at startup.

## Login

Run login from the project folder the user wants connected:

```bash
bifrost login --url {url}
bifrost auth default
```

This opens a browser for authentication. On Windows, credentials are stored in
Windows Credential Manager when keyring is available, with
`%APPDATA%\Bifrost\credentials.json` as the fallback. On Linux/macOS, keyring is
used when available with `~/.bifrost/credentials.json` as the fallback. Login
also writes the URL to the current folder's `.env`, selecting that connection
for commands run there. Tokens for other instance URLs remain available.

For the repository's local debug stack, use the `bifrost-debug` skill instead;
it knows the default `dev@gobifrost.com` / `password` credentials and creates a
dedicated scratch-folder selector without changing the saved default.

To disconnect a specific instance, use `bifrost logout --url {url}`. It clears
that URL's stored credentials and offers to remove a matching folder selector.

## MCP Configuration

MCP setup is coding-tool specific.

### Claude Code

Check existing configuration:
```bash
claude mcp list
```

**If `bifrost` exists with wrong URL:** Ask user if they want to update it.

**Add/update MCP server:**
```bash
claude mcp remove bifrost 2>/dev/null; claude mcp add --transport http bifrost {url}/mcp
```

### Codex / Other Coding Tools

If the user is using Codex or another agent CLI, do not run `claude mcp`.
Tell them SDK-first development works with `bifrost watch` and `bifrost api`.
Configure that tool's MCP settings only if its MCP command/config format is
available in the current environment.

## Restart Required (MCP only)

If MCP was configured, tell the user:

> Setup complete! Please restart Claude Code for the MCP server to take effect.
>
> After restarting, you can use `/bifrost:build` to create workflows, forms, and apps.

If MCP was skipped (SDK-first only), tell the user:

> Setup complete! You're ready to use `/bifrost:build` for SDK-first development.
>
> Use `bifrost watch` to auto-sync file changes and `bifrost api` for platform operations. MCP can be added later if you need `create_form`, `create_app`, or knowledge search.

## Troubleshooting

### pipx install fails with network error
- Verify URL is accessible: `curl -L {url}/api/cli/download/bifrost-cli.tar.gz -o /dev/null -w "%{http_code}"`

### bifrost login hangs
- Check if URL is accessible in browser
- Try with `--no-browser` flag and copy the URL manually

### MCP not working after restart
- Verify with `claude mcp list`
- Check Claude Code logs for MCP connection errors

### Windows setup stops immediately
- If `git` is missing, install Git in the shell where setup is running.
- If Docker is missing in WSL, enable Docker Desktop WSL integration.
- If `python` opens the Microsoft Store or prints the Store alias message,
  install Python with `winget install --id Python.Python.3.11 -e` or the
  python.org installer, then use `py -3.11`.
- If a `bifrost run ... -p '{"name":"Alice"}' example fails in native
  PowerShell with invalid JSON, escape the quotes:
  `-p '{\"name\":\"Alice\"}'`.
- If `bifrost push workflows/foo.py` fails, push a directory instead:
  `bifrost push workflows` or `bifrost push .`.
- If winget fails with `0x8a15000f`, reset the Windows region and winget
  sources: `Set-WinHomeLocation -GeoId 244`, `winget source reset --force`,
  `winget source update`.
- If `wsl --install` or VirtualMachinePlatform changes make the VM reboot into
  repair, stop platform setup on that VM and continue CLI-only setup natively.
  That host likely needs nested virtualization/WSL support fixed before Docker
  Desktop can work.
- If skills are not discovered after a native Windows clone, check whether
  `skills/setup` is a symlink/directory or a plain text file. Use WSL or run
  `bifrost skill update`.
