# bkt – Bitbucket CLI

<p align="center"><em>Bitbucket Cloud & Data Center workflows for developers, coding agents, and automation-first teams.</em></p>

[![CI](https://github.com/avivsinai/bitbucket-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/avivsinai/bitbucket-cli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/avivsinai/bitbucket-cli/graph/badge.svg)](https://codecov.io/gh/avivsinai/bitbucket-cli)
[![Release](https://img.shields.io/github/v/release/avivsinai/bitbucket-cli?cache=none)](https://github.com/avivsinai/bitbucket-cli/releases)
[![Homebrew](https://img.shields.io/homebrew/v/bitbucket-cli)](https://formulae.brew.sh/formula/bitbucket-cli)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/avivsinai/bitbucket-cli/badge)](https://scorecard.dev/viewer/?uri=github.com/avivsinai/bitbucket-cli)
[![Go Reference](https://pkg.go.dev/badge/github.com/avivsinai/bitbucket-cli.svg)](https://pkg.go.dev/github.com/avivsinai/bitbucket-cli)
[![License](https://img.shields.io/github/license/avivsinai/bitbucket-cli?cache=none)](LICENSE)

`bkt` is one command-line interface for Bitbucket Cloud **and** Bitbucket Data Center. It follows the ergonomics of `gh`, gives every command a stable JSON/YAML output contract, and ships an agent skill and an MCP server so coding agents can work with Bitbucket too.

This project (`github.com/avivsinai/bitbucket-cli`, binary `bkt`) is unrelated to the Rust [`bkt`](https://github.com/dimo414/bkt) subprocess-caching tool, the [Bitbucket Enterprise CLI](https://github.com/swisscom/bitbucket-cli), and other packages named `bitbucket-cli`.

<p align="center">
  <img src="docs/demo.gif" alt="Recorded terminal: brew install avivsinai/tap/bitbucket-cli, then bkt --help" width="860">
</p>

## Quick start

```bash
brew install bitbucket-cli

# Bitbucket Cloud: log in through your browser
bkt auth login https://bitbucket.org --kind cloud --web
bkt context create cloud --host api.bitbucket.org --workspace myteam --set-active

# Bitbucket Data Center: paste a Personal Access Token
bkt auth login https://bitbucket.example.com --web-token
bkt context create dc --host bitbucket.example.com --project ABC --set-active

bkt pr list --mine
bkt pr create --title "feat: cache" --source feature/cache --target main
```

Inside a clone, `bkt` takes the workspace or project and the repository from the git remote when the remote points at the active context's host.

## Install

| Platform | Command |
|---|---|
| macOS / Linux ([Homebrew core](https://formulae.brew.sh/formula/bitbucket-cli)) | `brew install bitbucket-cli` |
| Windows ([WinGet](https://github.com/microsoft/winget-pkgs)) | `winget install AvivSinai.Bitbucket-CLI` |
| Windows ([Scoop](https://github.com/avivsinai/scoop-bucket)) | `scoop bucket add avivsinai https://github.com/avivsinai/scoop-bucket`<br>`scoop install bitbucket-cli` |
| Go 1.26+ | `go install github.com/avivsinai/bitbucket-cli/cmd/bkt@latest` |
| Nix (flakes) | `nix profile install github:avivsinai/bitbucket-cli` |
| Debian / Ubuntu | `.deb` from the [latest release](https://github.com/avivsinai/bitbucket-cli/releases/latest) |
| Any | Archive from the [latest release](https://github.com/avivsinai/bitbucket-cli/releases/latest) |

Every install method supports Bitbucket Cloud browser login with no extra setup.

- **Homebrew tap.** `brew install avivsinai/tap/bitbucket-cli` installs the prebuilt release binary, signed with a Developer ID and notarized, instead of Homebrew's source build. Both provide the same `bkt` command, so install only one.
- **Nix.** `nix run github:avivsinai/bitbucket-cli -- --version` runs `master` without installing. Append a ref, such as `github:avivsinai/bitbucket-cli/v0.36.0`, to pin a release.
- **Release archives** also contain `skills/bkt/`, so the CLI and its agent skill stay on one version.
- **Verify a download.** Each release publishes `checksums.txt`, a CycloneDX SBOM, and GitHub build provenance: `gh attestation verify <archive> --repo avivsinai/bitbucket-cli`.
- **From source.** `git clone https://github.com/avivsinai/bitbucket-cli && cd bitbucket-cli && make build` produces `./bin/bkt`.

## Authenticate

`bkt auth login` checks a credential against the host before it stores it. `bkt auth status` lists your hosts and when OAuth tokens expire.

### Bitbucket Cloud

**Browser OAuth (recommended).** `bkt` opens Bitbucket in your browser. After you approve access, `bkt` stores a short-lived access token and refreshes it automatically:

```bash
bkt auth login https://bitbucket.org --kind cloud --web
```

To use your own OAuth consumer instead of bkt's, set both `BKT_OAUTH_CLIENT_ID` and `BKT_OAUTH_CLIENT_SECRET` before you log in.

**API token.** `--web-token` opens Atlassian's token page, then prompts for the token:

```bash
bkt auth login https://bitbucket.org --kind cloud --web-token
# or non-interactively
bkt auth login https://bitbucket.org --kind cloud --username <atlassian-email> --with-token < token.txt
```

Create the token under [Atlassian account → Security → API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) with **Create API token with scopes**. Choose **Bitbucket** as the app (general Atlassian tokens do not work) and grant:

- **Account: Read** (`read:user:bitbucket`), required
- **Repositories: Read, Write**, plus **Admin** for `bkt repo create`
- **Pull requests: Read, Write**
- **Pipelines** and **Webhooks**, if you use `bkt pipeline`, `bkt variable`, or `bkt webhook`

Log in with your Atlassian account **email**, not your Bitbucket username. Atlassian has removed app passwords; replace any you still use with an API token.

### Bitbucket Data Center

```bash
bkt auth login https://bitbucket.example.com --web-token
# or non-interactively
bkt auth login https://bitbucket.example.com --username alice --with-token < pat.txt
```

Create the Personal Access Token under **Profile picture → Manage account → Personal access tokens** with **Repository Read/Write** and **Project Read**.

### Credential storage

Tokens live in the OS keychain: macOS Keychain, Windows Credential Manager, or Secret Service/KWallet on Linux. Host metadata lives in `$XDG_CONFIG_HOME/bkt/config.yml` and never contains a token.

- **No keychain** (containers, minimal Linux): pass `--allow-insecure-store` or set `BKT_ALLOW_INSECURE_STORE=1` to use an encrypted file instead.
- **Slow unlock prompts:** raise `BKT_KEYRING_TIMEOUT`, for example `BKT_KEYRING_TIMEOUT=2m`.
- **A passphrase prompt on every run (Linux):** some Secret Service providers, such as KWallet, create a separate wallet for bkt's `bkt` collection. Set `BKT_KEYRING_COLLECTION` to your provider's default collection (for example `kdewallet`) to share the wallet you already unlocked. Add credentials stored under the old collection again. Distributors can set the default at build time with `-ldflags -X github.com/avivsinai/bitbucket-cli/internal/secret.defaultKeyringCollection=<collection>`; the environment variable still wins.
- **macOS Keychain prompts:** release binaries are signed with one Developer ID, so after you choose **Always Allow** once, upgrades keep access. `bkt auth doctor` explains prompts that persist; it never reads the stored secret.

### CI and containers

Set `BKT_TOKEN` and `BKT_HOST`, and `bkt` needs no login and no config file:

```bash
# Data Center
export BKT_HOST=https://bitbucket.example.com BKT_TOKEN=<pat> BKT_PROJECT=MYPROJ BKT_REPO=my-service

# Cloud, user API token (basic auth)
export BKT_HOST=https://bitbucket.org BKT_TOKEN=<api-token> BKT_USERNAME=me@example.com \
       BKT_WORKSPACE=my-workspace BKT_REPO=my-repo

# Cloud, repository / project / workspace access token (bearer auth)
export BKT_HOST=https://bitbucket.org BKT_TOKEN=<access-token> BKT_AUTH_METHOD=bearer

bkt pr list
```

Resource access tokens belong to no user. Commands that need a user identity, such as `bkt pr list --mine` across repositories, still need a user API token or OAuth.

In Bitbucket Pipelines, store `BKT_TOKEN` and `BKT_HOST` as secured [repository variables](https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/) and install a pinned release:

```yaml
pipelines:
  default:
    - step:
        name: Open PR
        script:
          - export BKT_VERSION=0.36.0  # pin the release you have tested
          - curl -fsSL "https://github.com/avivsinai/bitbucket-cli/releases/download/v${BKT_VERSION}/bkt_${BKT_VERSION}_linux_x86_64.tar.gz" | tar xz -C /tmp && install /tmp/bkt /usr/local/bin/
          - bkt pr create --title "Auto PR" --source "$BITBUCKET_BRANCH"
```

| Variable | Purpose |
|---|---|
| `BKT_TOKEN` | Token for every request; bypasses the keychain. |
| `BKT_HOST` | Base URL, for example `https://bitbucket.example.com`. `bitbucket.org` selects Cloud. |
| `BKT_USERNAME` | Username for basic auth. Required for Cloud user API tokens. |
| `BKT_AUTH_METHOD` | `basic` or `bearer`. Data Center defaults to `bearer` without `BKT_USERNAME`; Cloud defaults to `basic`. |
| `BKT_PROJECT` / `BKT_WORKSPACE` / `BKT_REPO` | Default Data Center project, Cloud workspace, and repository. |
| `BKT_CONFIG_DIR` | Config directory (default `$XDG_CONFIG_HOME/bkt`). |
| `BKT_OAUTH_CLIENT_ID` / `BKT_OAUTH_CLIENT_SECRET` | Your own Bitbucket Cloud OAuth consumer for `--web`; set both. |
| `BKT_ALLOW_INSECURE_STORE` | `1` allows the encrypted file store when no keychain exists. |
| `BKT_KEYRING_TIMEOUT` | Keychain operation timeout, for example `2m`. |
| `BKT_KEYRING_COLLECTION` | Secret Service collection (Linux). |
| `BKT_HTTP_DEBUG` | `1` logs each request URL and response status. |

## Use it

A context binds a host to a default workspace or project, and optionally a repository. `bkt auth status` prints the host value to pass to `--host`.

```bash
bkt context create cloud --host api.bitbucket.org --workspace myteam --set-active
bkt context list
```

**Repositories**

```bash
bkt repo list --limit 20
bkt repo view platform-api
bkt repo create data-pipeline --description "Data ingestion" --project DATA   # Data Center
bkt repo create frontend-app --workspace myteam --cloud-project WEB          # Cloud
bkt repo clone platform-api --project DATA --ssh
bkt repo browse --project DATA --repo platform-api
bkt repo downloads upload before.png after.png   # Cloud: host images for PR descriptions
```

**Pull requests**

```bash
bkt pr list --state OPEN --limit 10
bkt pr create --title "feat: cache" --source feature/cache --target main --reviewer alice
bkt pr checks 42 --wait --timeout 5m             # wait for builds, with backoff
bkt pr comments 42 --details                     # threads with file/line anchors
bkt pr comments resolve 42 1001
bkt pr merge 42 --message "merge: feature/cache"
```

**Issues.** Atlassian removed Bitbucket Cloud Issues in August 2026, and Data Center never had them; track issues in Jira.

**Pipelines, branches, permissions, webhooks**

```bash
bkt pipeline run --workspace myteam --repo api --ref main --var ENV=staging
bkt pipeline run --ref master --selector-type custom --selector-pattern deploy-to-production
bkt status pipeline {pipeline-uuid}
bkt branch create release/1.9 --from main
bkt perms repo list --project DATA --repo platform-api
bkt webhook create --name "CI" --url https://ci.example.com/hook --event repo:refs_changed
bkt status rate-limit
```

**Anything else.** `bkt api` calls any REST endpoint with your stored credentials:

```bash
bkt api /rest/api/1.0/projects --param limit=100 --json           # Data Center
bkt api /repositories --param workspace=myteam --field pagelen=50  # Cloud
```

**Output for scripts.** Commands accept `--json`, `--yaml`, `--jq <expr>`, and `--template <go-template>`.

**Extensions.** `bkt extension install <git-url>` adds a `bkt-<name>` command; `bkt extension exec <name>` runs it.

**Shell completion.** `bkt completion bash|zsh|fish|powershell`. The Homebrew core formula installs completions for you.

The full command reference, generated from `bkt --help`, is in [`skills/bkt/rules/`](skills/bkt/rules/).

## Coding agents

**Agent skill.** The `bkt` skill teaches Claude Code, Codex, and other agents to use `bkt`:

```bash
npx skills add avivsinai/bitbucket-cli -g -y
```

Alternatives: `npx skild install @avivsinai/bkt -t claude -y`; the Claude Code marketplace (`/plugin marketplace add avivsinai/skills-marketplace`, then `/plugin install bkt@avivsinai-marketplace`); or copy [`skills/bkt`](skills/bkt) into `~/.claude/skills/`.

**MCP server.** `bkt mcp serve` exposes read-only Bitbucket tools over MCP stdio for one pinned context:

```bash
claude mcp add bitbucket -- bkt mcp serve
```

**Skills hosted on Bitbucket.** `bkt skill` installs [Agent Skills](https://agentskills.io/specification) from Bitbucket repositories, mirroring [`gh skill`](https://github.com/cli/cli#agent-skills):

```bash
bkt skill install myteam/agent-skills                  # list what a repository publishes
bkt skill install myteam/agent-skills code-review@v1.2.0 --agent claude-code --scope user
bkt skill list
bkt skill update --all
bkt skill publish --tag v1.2.0                         # validate and tag your own skills
```

`--agent` selects the target agent (Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and more; see `bkt skill install --help`). The default, `universal`, writes to the shared `.agents/skills` directory. Installed skills record their source in `SKILL.md` frontmatter, and `bkt skill update` compares it with the repository; `@version` or `--pin` pins a skill until `--unpin`. `bkt skill search` uses the Bitbucket Cloud code-search API, which Atlassian has [announced for deprecation](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-other-operations/#api-workspaces-workspace-search-code-get); Data Center has no equivalent API.

## Troubleshooting

- `BKT_HTTP_DEBUG=1 bkt <command>` prints each request URL and response status.
- `bkt auth status` shows each host, its auth method, and OAuth expiry.
- `bkt auth doctor` diagnoses keychain prompts and timeouts.

## Project

- [Contributing](CONTRIBUTING.md): build, test, and pull request workflow
- [Security policy](SECURITY.md) and [security operations](docs/SECURITY.md)
- [Changelog](CHANGELOG.md) · [Versioning](docs/VERSIONING.md) · [Privacy](docs/PRIVACY.md)
- Questions and bugs: [GitHub issues](https://github.com/avivsinai/bitbucket-cli/issues)

`bkt` is available under the [MIT License](LICENSE).
