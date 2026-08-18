# Krypton VPS Codex App Setup Runbook

Use this when the operator wants complete setup instructions, a post-ready
checklist, or troubleshooting steps. Keep secret values out of prompts,
terminal output, docs, and screenshots.

## Target Shape

The Mac runs Codex App and controls the workflow. The VPS owns the repo checkout,
shell, tools, builds, tests, agent sessions, tmux/cmux state, and dev servers.
GitHub remains the code source of truth. Production stays separate.

Do not install or describe the desktop Codex App as running on the VPS. The VPS
needs the Codex CLI and repo toolchain; the desktop app connects over SSH and
starts the remote Codex app server through the remote login shell.

```text
Mac -> Codex App -> SSH alias -> VPS
VPS -> repo, Codex CLI, Claude Code, tmux/cmux, builds, tests, dev servers
GitHub -> source of truth
Production -> separate protected deploy target
```

## VPS Baseline

Start by asking:

```text
Do you already have a VPS with SSH access, or are we starting before the VPS is
created?
```

If there is no VPS yet, the operator must provision one first. Recommend the
baseline below, then wait for the VPS IP, initial username, SSH key choice, and
public-key path.

Recommended starting point:

- Ubuntu 24.04 LTS.
- Non-root `dev` user with sudo.
- SSH key auth.
- Password SSH disabled after key auth is confirmed.
- Firewall only allowing required inbound ports. For most setups this is SSH
  only.
- Adequate swap for builds and parallel agents.

Example baseline commands after connecting as an admin user:

```bash
sudo apt-get update
sudo apt-get install -y \
  ca-certificates \
  curl \
  git \
  gnupg \
  jq \
  build-essential \
  tmux \
  unzip
```

Install Node, pnpm, Docker, GitHub CLI, cmux, Codex CLI, and Claude Code using
the current official path for each tool and the repo's documented version
requirements. Do not pin commands from memory if the repo or tool docs specify a
different path.

If the provider gives you `root`, use it for bootstrap only. Create or select a
non-root daily user, add the SSH key there, and point the Codex App SSH alias at
that user before starting normal work.

## SSH Alias

On the Mac that runs Codex App:

Show this snippet before editing `~/.ssh/config`. Only write it for the user
when they ask Codex to make the local edit or the current task explicitly
includes local setup.

```sshconfig
Host krypton-vps
  HostName 203.0.113.10
  User dev
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

Prove the alias:

```bash
ssh krypton-vps 'hostname; whoami; pwd'
```

Codex App discovers concrete SSH aliases from `~/.ssh/config`; avoid pattern-only
hosts for the project connection.

## Codex On The VPS

The Codex App remote connection starts the remote Codex app server through SSH
using the remote user's login shell. This means the remote login shell must find
the `codex` command.

Check:

```bash
ssh krypton-vps '$SHELL -lc "command -v codex && codex --version"'
```

Authenticate on the VPS:

```bash
ssh krypton-vps
codex login --device-auth
```

If device auth is unavailable, use the official fallback: complete login where a
browser works and copy `~/.codex/auth.json` to the VPS over SSH. Treat that file
like a password.

For setup failures, run `codex doctor` on the VPS. Do not expose
`codex app-server` manually for normal Codex App SSH projects.

## Repo Setup

Ask before copying code:

```text
Do you want GitHub to be the source of truth for this VPS checkout? That is the
recommended path. It keeps code transfer clean, repeatable, and reviewable.
```

Then ask which GitHub access path the operator wants:

- GitHub CLI login on the VPS: best for normal development, private repo
  access, issues, PRs, and pushes.
- SSH key on the user's GitHub account: good for a personal dev VPS, but it can
  access every repo the account can access.
- Read-only deploy key: best for one private repo with least privilege, but it
  cannot push branches unless write access is explicitly enabled.
- Public HTTPS clone: fine for public repos.
- `rsync` or archive from the Mac: fallback when the code is not in GitHub.

Do not ask the user to paste GitHub tokens into chat. Do not put tokens in Git
remote URLs.

GitHub CLI path:

```bash
ssh krypton-vps
gh auth login
gh auth status
mkdir -p ~/src
gh repo clone ORG/REPO ~/src/REPO
cd ~/src/REPO
```

SSH key path:

```bash
ssh krypton-vps
ssh-keygen -t ed25519 -C "krypton-vps" -f ~/.ssh/github-krypton-vps
cat ~/.ssh/github-krypton-vps.pub
```

The operator adds that public key to GitHub, either as an account SSH key or as
a repo deploy key. Then:

```bash
ssh -T git@github.com
mkdir -p ~/src
git clone git@github.com:ORG/REPO.git ~/src/REPO
cd ~/src/REPO
```

For a private repo where the VPS only needs clone/pull, prefer a deploy key with
write access disabled. For a dev VPS where Codex should push PR branches, use
GitHub CLI login or a normal account SSH key instead.

Basic clone shape:

```bash
ssh krypton-vps
mkdir -p ~/src
git clone git@github.com:ORG/REPO.git ~/src/REPO
cd ~/src/REPO
```

Then read the repo:

```bash
ls
test -f AGENTS.md && sed -n '1,160p' AGENTS.md
test -f README.md && sed -n '1,220p' README.md
```

Install dependencies using the repo's commands. For pnpm repos, use the repo's
declared package manager or Corepack version.

## Local Config And Secrets

Ask before touching ignored or local-only files:

```text
Do you want to recreate local config on the VPS from examples, copy selected
ignored files from this machine, or skip local config for now?
```

Use this order:

1. Recreate from checked-in examples such as `.env.example`, README setup, or
   project docs.
2. Copy selected ignored files only when the operator names or approves them.
3. Skip secrets until the app tells you what is missing.

Safe selected-file copy:

```bash
rsync -av --chmod=F600,D700 .env.local krypton-vps:~/src/REPO/.env.local
```

Do not bulk-copy the home directory, `.ssh`, `.codex`, browser profiles,
node_modules, build outputs, caches, private keys, or random dotfiles. Do not
commit copied local config.

Optional CLI smoke before opening the app UI:

```bash
ssh krypton-vps 'cd ~/src/REPO && codex exec --ephemeral --sandbox read-only -C "$PWD" "Run pwd, hostname, whoami, command -v codex, codex --version, git status --short, and do not modify files."'
```

This proves the remote Codex CLI can authenticate and complete a read-only turn.
It is not a substitute for the final Codex App remote project proof.

## Codex App Connection

On the Mac:

1. Open Codex App.
2. Open Settings > Connections.
3. Add or enable the SSH alias.
4. Choose the remote project folder, such as `~/src/REPO`.
5. Start a thread in that remote project.

This is a user-operated app step unless the current Codex session has explicit
desktop/app-control tools and the operator asks to use them. SSH setup alone
does not add the project inside Codex App.

First proof prompt:

```text
Run pwd, hostname, whoami, command -v codex, codex --version, git status --short,
and do not modify files.
```

Expected proof:

- `hostname` is the VPS.
- `pwd` is the remote repo.
- `codex` resolves on PATH.
- Git status is clean or the dirty files are understood.

## Local Environment Actions

Codex App local environments can define setup scripts and actions for worktrees
and common commands. Configure them through Codex App settings first, then check
in the generated `.codex` project config only when it is meant to be shared.

Good actions:

- Install dependencies.
- Run focused tests.
- Start the dev server.
- Run typecheck or lint.

Avoid putting secrets, personal paths, or production commands in shared project
actions.

## Port Forwarding

Forward local browser ports from Mac to VPS:

```bash
ssh -L 3000:127.0.0.1:3000 krypton-vps
```

On the VPS, run the app's dev server. On the Mac, open:

```text
http://127.0.0.1:3000
```

If it fails:

1. On the VPS, prove the server is listening.
2. On the Mac, prove the SSH tunnel is still open.
3. Confirm local and remote ports match.
4. Avoid binding private dev servers to a public interface unless the operator
   explicitly accepts that risk and adds authentication.

On a headless Linux VPS, prefer this tunnel-to-local-browser pattern. Do not
promise Browser or Computer Use unless a supported browser/desktop stack is
installed and verified on the host.

## tmux And cmux

Use tmux to keep sessions alive across Mac sleep/disconnects:

```bash
tmux new -s krypton
tmux attach -t krypton
```

Use cmux when the workflow needs several visible agent sessions. Keep names
boring and traceable, for example:

```text
krypton-main
krypton-review
krypton-test
krypton-ui
```

## Read-Only Audit

From the repo root on the Mac:

```bash
.codex/skills/krypton/krypton-vps-codex-app/scripts/audit-vps-codex-app.sh \
  --host krypton-vps \
  --repo-url git@github.com:ORG/REPO.git \
  --repo-path ~/src/REPO
```

Passing the audit does not prove the Codex App UI connection by itself. It proves
the SSH host is reachable and has the remote prerequisites that Codex App needs.
Finish with a real Codex App remote thread proof.

## Public Post Checklist

Use this short version when creating founder-facing setup content:

1. Buy or rent a Linux VPS with enough CPU and memory for agents and builds.
2. Use Ubuntu 24.04 unless the repo needs something else.
3. Add SSH key access and create a concrete SSH alias on the Mac.
4. Install the repo toolchain, Codex CLI, tmux, cmux, Docker if needed, and
   package managers.
5. Choose a GitHub access path: GitHub CLI login, account SSH key, deploy key,
   or public HTTPS clone.
6. Clone the repo on the VPS from GitHub.
7. Recreate or copy only the local config files the operator approves.
8. Authenticate Codex on the VPS.
9. Connect Codex App to the SSH host and choose the remote repo folder.
10. Start agent sessions on the VPS.
11. Forward ports for local browser testing.
12. Keep GitHub as source of truth and production separate.

## Failure Modes

- SSH alias missing or pattern-only: Codex App cannot discover the host.
- `codex` installed only for an interactive shell: remote app server cannot
  start it. Fix login-shell `PATH`.
- CLI smoke passes but app connection fails: inspect Codex App Settings >
  Connections, then run `codex doctor` on the VPS.
- Local credentials assumed to exist remotely: GitHub, Codex, package registry,
  deploy, and MCP auth must be installed or authenticated on the VPS.
- GitHub clone fails: choose one access method with the operator instead of
  silently switching between GitHub CLI, account SSH keys, deploy keys, and
  HTTPS.
- Local config missing: recreate from examples first, then ask before copying
  ignored files from the Mac.
- Dev server exposed publicly: use SSH forwarding instead.
- Production and dev on the same user/session: split them.
- Worktree setup missing dependencies: configure Codex App local environment
  setup scripts or repo bootstrap commands.
