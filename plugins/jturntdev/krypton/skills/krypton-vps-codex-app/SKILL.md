---
name: krypton-vps-codex-app
description: Set up, harden, audit, or explain a Linux VPS as a Codex App SSH host for Krypton-style agent workflows. Use when the user wants to move Codex or Claude Code work from a local Mac to a VPS, connect Codex App to an SSH host, configure Ubuntu 24.04/devbox tools, clone a repo remotely, run Codex/Claude/tmux/cmux on the VPS, forward ports for localhost testing, or create repeatable founder/builder setup instructions with proof checks.
---

# Krypton VPS Codex App

## Overview

Turn a Linux VPS into the machine that does the work while the operator's Mac
only displays and controls it. The target result is a working Codex App SSH
project where commands, edits, builds, tests, tmux/cmux sessions, dev servers,
and agent runs happen on the VPS.

Do not describe this as installing Codex App on the VPS. Codex App stays on the
operator's Mac or Windows machine; the VPS needs the Codex CLI and repo
toolchain so the app can start the remote Codex app server through SSH.

Use the current OpenAI Codex docs for Codex App specifics when facts may have
changed. The durable setup facts this skill relies on are:

- Codex App can add projects from an SSH host.
- Codex reads concrete SSH aliases from `~/.ssh/config`.
- Remote project threads run commands and edit files on the remote host.
- The remote host provides the repo files, credentials, tools, skills, MCP
  setup, browser/computer-use setup, and sandbox/approval behavior.
- The remote `codex` command must be available on the remote user's login-shell
  `PATH`.

## Responsibility Split

Codex can prepare commands, inspect SSH config, audit the VPS, bootstrap tools
over SSH when it has access, clone the repo, run checks, and explain failures.

The operator must provide or complete these human steps:

- Buy or provision the VPS if it does not exist yet.
- Create or choose the SSH key pair used for the VPS.
- Add an SSH public key in the VPS provider UI or otherwise grant SSH access.
- Approve any edit to `~/.ssh/config`, or add the SSH alias manually.
- Choose how the VPS may access their GitHub repo.
- Decide whether local-only config files should be recreated, copied, or skipped.
- Keep private keys, provider passwords, API keys, and Codex auth files secret.
- Complete Codex App Settings > Connections and choose the remote project folder.
- Complete browser/device authentication when the flow requires user login.

## First Response

Start by repeating the setup goal in plain English:

```text
You want the VPS to be the actual development machine. Codex App on the Mac
connects to it over SSH, and the repo, tools, agent sessions, builds, tests,
and dev servers run there.
```

Then ask this setup-state question first:

```text
Do you already have a VPS with SSH access, or are we starting before the VPS is
created?
```

If the VPS does not exist yet, give a short purchase/bootstrap checklist:
Ubuntu 24.04 LTS unless the repo needs something else, enough CPU/RAM/swap for
builds and agent runs, SSH-key access, a non-root daily user, no public dev
ports, and GitHub as source of truth. Then ask for the VPS IP, initial username,
and public-key path once the VPS is ready.

If the VPS exists, ask for only the missing inputs needed for the next step:

- SSH alias or VPS IP.
- Remote username.
- Repo URL and desired remote path.
- Whether the repo is public or private.
- Which GitHub access path they want: GitHub CLI login, SSH key on their GitHub
  account, read-only deploy key, or no GitHub setup yet.
- Whether they have local-only config files such as `.env`, ignored config,
  MCP files, package registry auth, or provider credentials that the VPS needs.
- Stack commands if they are not obvious from the repo.
- Whether Codex should only audit or may bootstrap missing tools over SSH.
- Whether the operator wants setup, audit, troubleshooting, or public post-ready
  instructions.

If the user already gave enough, proceed without more questions.

## Setup Workflow

### 1. Host And Security Preflight

Treat this as a development host, not production.

- Use a non-root Linux user for daily work.
- If the first login is `root`, use it only for bootstrap and move the Codex
  SSH alias to a non-root user before day-to-day work.
- Use SSH keys, not passwords.
- Keep GitHub as source of truth for code.
- Keep production deploy targets separate and protected.
- Do not expose dev servers, Codex app-server, Docker sockets, databases, or
  private dashboards to the public internet.
- Prefer SSH port forwarding for local browser testing.
- On headless Linux VPS hosts, do not promise Browser or Computer Use unless a
  supported browser/desktop stack is explicitly installed and verified. Prefer
  running the server on the VPS and inspecting it through a local SSH tunnel.
- Never print, paste, or commit `~/.codex/auth.json`, API keys, deploy keys,
  SSH private keys, or provider tokens.

### 2. Mac SSH Config

Create or provide a concrete SSH alias on the Mac that runs Codex App. Do not
edit `~/.ssh/config` silently; show the snippet and ask before writing unless
the user already asked Codex to make the edit.

```sshconfig
Host krypton-vps
  HostName 203.0.113.10
  User dev
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

Verify from the Mac:

```bash
ssh krypton-vps
```

### 3. VPS Tooling

On the VPS, install the repo's real toolchain. For a typical Ubuntu 24.04 agent
box this means:

- `git`
- `gh`
- `curl`
- `jq`
- `python3`
- `ripgrep` (`rg`)
- `build-essential`
- `tmux`
- `unzip`
- `cmux` when the workflow uses it
- `node`
- `corepack`
- `pnpm`
- Docker and Compose when the repo needs containers
- Codex CLI, installed through the current official path
- Claude Code only if the operator uses it and has its auth flow ready

Do not guess a repo's install commands. Read `README.md`, package manager files,
and repo docs first.

### 4. Codex On The VPS

The remote shell must find `codex`:

```bash
command -v codex
codex --version
```

For headless login, prefer:

```bash
codex login --device-auth
```

If device auth is unavailable, use the official fallback options. If copying
`~/.codex/auth.json`, treat it like a password and never expose its contents.

For troubleshooting, use `codex doctor` on the VPS. Do not manually expose
`codex app-server` for a normal Codex App SSH project; the app starts the remote
app server over SSH.

### 5. Repo And Project

Before copying code, ask:

```text
Do you want GitHub to be the source of truth for this VPS checkout? That is the
recommended path. It keeps code transfer clean, repeatable, and reviewable.
```

If yes, ask which GitHub access method the operator wants:

- GitHub CLI login on the VPS: best when the user wants normal development,
  private repo access, issues, PRs, and pushes from the VPS.
- SSH key on the user's GitHub account: good when the VPS should behave like one
  of the user's dev machines. This key can access every repo that account can
  access, so do not use it casually on shared hosts.
- Read-only deploy key: best for cloning one private repo with least privilege.
  It is not enough if Codex needs to push branches back to GitHub.
- Public HTTPS clone: fine for public repos or read-only public examples.
- `rsync`/archive from the Mac: fallback for code not in GitHub; do not present
  this as the default for active codebases.

Never ask the user to paste a GitHub token into the chat or put a token in a Git
remote URL. If token auth is unavoidable, use the official GitHub CLI or
provider flow and avoid printing the token.

For private repos with GitHub CLI:

```bash
ssh krypton-vps
gh auth login
gh auth status
gh repo clone ORG/REPO ~/src/REPO
```

For SSH Git access:

```bash
ssh krypton-vps
ssh-keygen -t ed25519 -C "krypton-vps" -f ~/.ssh/github-krypton-vps
cat ~/.ssh/github-krypton-vps.pub
```

The operator adds the printed public key to GitHub. Then verify and clone:

```bash
ssh -T git@github.com
mkdir -p ~/src
git clone git@github.com:ORG/REPO.git ~/src/REPO
cd ~/src/REPO
```

For a read-only deploy key, add the public key under the single GitHub repo's
Deploy keys with write access disabled. Use this only when the VPS needs to
clone or pull, not push.

After clone, set the normal project path:

```bash
mkdir -p ~/src
git clone git@github.com:ORG/REPO.git ~/src/REPO
cd ~/src/REPO
```

Install dependencies using the repo's own commands. If the repo uses checked-in
skills, hooks, MCP config, or local environment actions, keep them in the repo
so Codex App sees the same project guidance remotely.

### 6. Local Config And Secrets

Treat code and local configuration as separate moves.

Ask before touching local config:

```text
Do you want to recreate local config on the VPS from examples, copy selected
ignored files from this machine, or skip local config for now?
```

Recommended order:

1. Recreate from checked-in examples such as `.env.example`, README setup, or
   project docs.
2. Copy selected ignored files only when the operator confirms the exact files.
3. Skip secrets until the repo can boot far enough to show what is missing.

Safe copy pattern for selected local files:

```bash
rsync -av --chmod=F600,D700 .env.local krypton-vps:~/src/REPO/.env.local
```

Do not bulk-copy the whole home directory, `.ssh`, `.codex`, browser profiles,
node_modules, build outputs, caches, or private key files. Do not commit copied
local config. After copying, verify permissions and keep secrets out of terminal
summaries.

Optional stronger CLI proof before the app UI:

```bash
ssh krypton-vps 'cd ~/src/REPO && codex exec --ephemeral --sandbox read-only -C "$PWD" "Run pwd, hostname, whoami, command -v codex, codex --version, git status --short, and do not modify files."'
```

This proves the remote Codex CLI can complete a read-only turn. It does not
replace the final Codex App remote-thread proof.

### 7. Codex App Connection

In Codex App on the Mac:

1. Open Settings.
2. Open Connections.
3. Add or enable the SSH host alias.
4. Choose the remote project folder, for example `~/src/REPO`.
5. Start a remote project thread.

This is a user-operated app step unless the current Codex session has explicit
desktop/app-control tools and the operator asks to use them. Do not pretend SSH
alone completes the Codex App connection.

Proof prompt for the first remote thread:

```text
Run pwd, hostname, command -v codex, codex --version, git status --short, and
do not modify files.
```

The result should show the VPS hostname, the remote repo path, a working Codex
binary, and a clean or understood Git state.

### 8. Port Forwarding

Use SSH forwarding for local browser proof:

```bash
ssh -L 3000:127.0.0.1:3000 krypton-vps
```

Run the dev server on the VPS bound to localhost or the documented dev-host
address. Browse from the Mac at `http://127.0.0.1:3000`.

### 9. cmux And tmux

Use tmux for persistence and cmux for managing multiple agent sessions when the
operator wants that workflow:

```bash
tmux new -s krypton
```

Keep the rule simple: Mac displays, VPS works, GitHub stores source, production
stays separate.

## Audit Script

When an SSH alias exists, run:

```bash
.codex/skills/krypton/krypton-vps-codex-app/scripts/audit-vps-codex-app.sh \
  --host krypton-vps \
  --repo-url git@github.com:ORG/REPO.git \
  --repo-path ~/src/REPO
```

The script is read-only. It checks SSH reachability, Linux/Ubuntu details,
required command availability, whether `codex` is on the login-shell `PATH`,
basic auth-cache presence without printing secrets, GitHub repo reachability
when `--repo-url` is supplied, Git repo state, root-user risk, and common
agent-workflow tools. It does not prove the Codex App UI connection by itself;
finish with a real remote project thread.

## Troubleshooting Rules

- If Codex App cannot find the host, inspect `~/.ssh/config` on the Mac and
  confirm `ssh <alias>` works outside the app.
- If Codex App connects but remote threads fail immediately, check that `codex`
  is installed and visible in the remote login shell.
- If the CLI smoke passes but the app fails, inspect Codex App Settings >
  Connections and run `codex doctor` on the VPS.
- If browser login fails on the headless VPS, use device auth or an SSH
  localhost callback tunnel.
- If private GitHub clone fails, decide whether the user wants `gh auth login`,
  a GitHub account SSH key, or a single-repo deploy key. Do not switch methods
  without asking.
- If the repo boots but config is missing, recreate from examples first, then
  ask before copying any ignored local files.
- If dev server preview fails, first prove the server is listening on the VPS,
  then prove the SSH tunnel maps the right remote port to the right local port.
- If tests are slow or memory-heavy, confirm the VPS size and swap before
  blaming Codex.
- If credentials are missing, install or authenticate them on the VPS. The Mac's
  local credentials do not automatically become remote credentials.

## Reference

Read `references/setup-runbook.md` when the user needs complete copy/paste setup
steps, a public-post checklist, or deeper troubleshooting.
