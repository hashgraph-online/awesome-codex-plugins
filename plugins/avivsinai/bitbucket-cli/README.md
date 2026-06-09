# bkt – Bitbucket CLI

<p align="center"><em>Bitbucket Cloud & Data Center workflows for developers, coding agents, and automation-first teams.</em></p>

[![CI](https://github.com/avivsinai/bitbucket-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/avivsinai/bitbucket-cli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/avivsinai/bitbucket-cli/graph/badge.svg)](https://codecov.io/gh/avivsinai/bitbucket-cli)
[![Release](https://img.shields.io/github/v/release/avivsinai/bitbucket-cli?cache=none)](https://github.com/avivsinai/bitbucket-cli/releases)
[![Go Report Card](https://goreportcard.com/badge/github.com/avivsinai/bitbucket-cli?cache=none)](https://goreportcard.com/report/github.com/avivsinai/bitbucket-cli)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/avivsinai/bitbucket-cli/badge)](https://scorecard.dev/viewer/?uri=github.com/avivsinai/bitbucket-cli)
[![Go Reference](https://pkg.go.dev/badge/github.com/avivsinai/bitbucket-cli.svg)](https://pkg.go.dev/github.com/avivsinai/bitbucket-cli)
[![License](https://img.shields.io/github/license/avivsinai/bitbucket-cli?cache=none)](LICENSE)

`bkt` is a stand-alone Bitbucket command-line interface that targets Bitbucket Data Center **and** Bitbucket Cloud. It mirrors the ergonomics of `gh` and delivers a consistent JSON/YAML contract for automation.

**Built for AI & automation:** Drop `bkt` into Claude Code, Codex and other coding agents, or shell scripts and they inherit structured output, predictable flags, and safe defaults—no glue code required.

## Installation

### Homebrew (macOS/Linux)

```bash
brew install avivsinai/tap/bitbucket-cli
```

### Scoop (Windows)

```powershell
scoop bucket add avivsinai https://github.com/avivsinai/scoop-bucket
scoop install bitbucket-cli
```

### Go Install

```bash
go install github.com/avivsinai/bitbucket-cli/cmd/bkt@latest
```

This installs `bkt` to `$GOPATH/bin` (or `$HOME/go/bin` by default). Ensure the directory is in your `$PATH`.

### Nix (NixOS / nix-darwin / Linux / macOS)

Run the latest `master` without installing:

```bash
nix run github:avivsinai/bitbucket-cli -- --version
```

Install into your user profile:

```bash
nix profile install github:avivsinai/bitbucket-cli
```

Pin to a specific tag or commit by appending a ref (e.g. `github:avivsinai/bitbucket-cli/v1.2.3`).

Don't have Nix yet? See [nixos.asia/en/install](https://nixos.asia/en/install) for a quick setup guide (installs Nix with flakes enabled out of the box).

### Binary Downloads

Download pre-built binaries for your platform from the [releases page](https://github.com/avivsinai/bitbucket-cli/releases/latest).
The `.tar.gz` and `.zip` release archives also include `skills/bkt/`, so the CLI and canonical skill files stay in sync when you install from a release artifact.

Official binaries support Bitbucket Cloud OAuth (`bkt auth login --kind cloud --web`) out of the box. Source and Nix builds can use the same flow by setting `BKT_OAUTH_CLIENT_ID` and `BKT_OAUTH_CLIENT_SECRET` in the environment. API-token login via `--web-token` works without that extra setup.

### Bitbucket Pipelines

`bkt` supports fully config-free headless use via environment variables. Set `BKT_TOKEN` and `BKT_HOST` as secured [repository variables](https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/) — no prior `bkt auth login` or `bkt context create` step required.

```yaml
pipelines:
  default:
    - step:
        name: Open PR
        script:
          - export BKT_VERSION="0.26.0"  # pin to a released version
          - curl -sL "https://github.com/avivsinai/bitbucket-cli/releases/download/v${BKT_VERSION}/bkt_${BKT_VERSION}_linux_x86_64.tar.gz" | tar xz -C /tmp && install /tmp/bkt /usr/local/bin/
          - bkt pr create --title "Auto PR" --source "$BITBUCKET_BRANCH"
```

### Environment Variables

All `bkt` behaviour can be configured via environment variables, which is especially useful in containers and CI/CD pipelines.

| Variable | Description |
|---|---|
| `BKT_TOKEN` | Authentication token. Bypasses keyring storage entirely. |
| `BKT_HOST` | Bitbucket server base URL (e.g. `https://bitbucket.example.com`). Required alongside `BKT_TOKEN` for config-free use. `bitbucket.org` is auto-detected as Cloud. |
| `BKT_USERNAME` | Username for basic authentication in headless mode. |
| `BKT_AUTH_METHOD` | Authentication method: `basic` or `bearer`. DC defaults to `bearer` when `BKT_USERNAME` is absent; Cloud always uses `basic`. |
| `BKT_PROJECT` | Default Data Center project key (headless mode). |
| `BKT_WORKSPACE` | Default Bitbucket Cloud workspace (headless mode). |
| `BKT_REPO` | Default repository slug (headless mode). |
| `BKT_CONFIG_DIR` | Override the config file directory (default: `$XDG_CONFIG_HOME/bkt`). |
| `BKT_HTTP_DEBUG` | Set to `1` to log HTTP request URLs and response status codes. |
| `BKT_ALLOW_INSECURE_STORE` | Set to `1` to use encrypted file fallback when no OS keychain is available. |

**Minimal headless example (Data Center):**

```bash
export BKT_HOST=https://bitbucket.example.com
export BKT_TOKEN=my-personal-access-token
export BKT_PROJECT=MYPROJ
export BKT_REPO=my-service

bkt pr list
bkt pr create --title "Automated PR" --source feature/my-branch
```

**Minimal headless example (Bitbucket Cloud):**

```bash
export BKT_HOST=https://bitbucket.org
export BKT_TOKEN=my-api-token
export BKT_USERNAME=me@example.com
export BKT_WORKSPACE=my-workspace
export BKT_REPO=my-repo

bkt pr list
```

### From Source

```bash
git clone https://github.com/avivsinai/bitbucket-cli.git
cd bitbucket-cli
make build   # produces ./bin/bkt
./bin/bkt --help
```

### Claude Code / Codex Skill

Install the `bkt` skill to give Claude Code or Codex CLI native Bitbucket knowledge:

<details open>
<summary><b>Via skills (Recommended)</b></summary>

Using [Vercel's skills CLI](https://github.com/vercel-labs/add-skill):

```bash
npx skills add avivsinai/bitbucket-cli -g -y
```

</details>

<details>
<summary><b>Via skild registry</b></summary>

```bash
npx skild install @avivsinai/bkt -t claude -y
```

</details>

<details>
<summary><b>Via Skills Marketplace</b></summary>

> **Known Issue**: Claude Code uses SSH to clone marketplace repos, which fails without SSH keys configured. See [issue #14485](https://github.com/anthropics/claude-code/issues/14485). Use the skills or skild methods instead.

```bash
/plugin marketplace add avivsinai/skills-marketplace
/plugin install bkt@avivsinai-marketplace
```

</details>

<details>
<summary><b>Manual install</b></summary>

```bash
git clone https://github.com/avivsinai/bitbucket-cli.git
cp -r bitbucket-cli/.claude/skills/bkt ~/.claude/skills/
```

</details>

## Getting started

After installation, verify it works:

```bash
bkt --help
```

### 1. Authenticate against Bitbucket Data Center or Cloud

#### Bitbucket Data Center

```bash
# Guided flow: opens browser to create a Personal Access Token
bkt auth login https://bitbucket.mycorp.example --web-token

# Or provide credentials directly
bkt auth login https://bitbucket.mycorp.example --username alice --token <PAT>
```

Create a **Personal Access Token (PAT)** in Bitbucket Data Center:
1. Go to **Profile picture → Manage account → Personal access tokens**
2. Click **Create a token**
3. Grant permissions: **Repository Read**, **Repository Write**, **Project Read**
4. Copy the token (you won't see it again)

#### Bitbucket Cloud

```bash
# Browser OAuth flow for Bitbucket Cloud
bkt auth login https://bitbucket.org --kind cloud --web

# Or provide credentials directly
bkt auth login https://bitbucket.org --kind cloud --username <email> --token <api-token>
```

Create an **API token with scopes** for Bitbucket Cloud:
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create and manage API tokens** → **Create API token with scopes**
3. Name your token and set an expiry date
4. **Select "Bitbucket" as the application** (required!)
5. Grant scopes:
   - **Account: Read (`read:user:bitbucket`)** — Required for authentication
   - **Repositories: Read, Write** — For repo commands
   - **Pull requests: Read, Write** — For PR commands
   - **Issues: Read, Write** — For issue commands (optional)
6. Click **Create** and copy the token immediately

> **Warning:** General Atlassian API tokens won't work. You must select "Bitbucket" as the application when creating the token.

> **Note:** Use your **Atlassian account email** as the username (not your Bitbucket username).

<details>
<summary>Legacy: App passwords (deprecated)</summary>

App passwords are deprecated. New app passwords cannot be created since September 2025, and existing ones will stop working June 2026. If you have an existing app password:

```bash
bkt auth login https://bitbucket.org --kind cloud --username <bitbucket-username> --token <app-password>
```

Note: For app passwords, use your **Bitbucket username** (not email).

</details>

#### Credential storage

Access tokens are stored in your OS keychain (Keychain Access on macOS, Windows Credential Manager, or
Secret Service/KWallet on Linux) while host metadata lives in
`$XDG_CONFIG_HOME/bkt/config.yml`. Pass `--allow-insecure-store` (or set
`BKT_ALLOW_INSECURE_STORE=1`) to permit the encrypted file backend on systems
without a native keychain.

If your keyring requires an interactive unlock prompt, you can increase the keyring timeout via
`BKT_KEYRING_TIMEOUT` (for example `BKT_KEYRING_TIMEOUT=2m`).

##### macOS note: Keychain prompts after `brew upgrade`

On macOS, every `brew upgrade bkt` may trigger one Keychain prompt because the
stored item's ACL is tied to the installed binary. Re-run `bkt auth login` once
after the upgrade to refresh the ACL, then subsequent invocations should not
prompt. Releases pin the Designated Requirement to the bundle identifier, so
the refresh is only needed once. Run `bkt auth doctor` to diagnose prompts
that persist beyond that; it never reads the stored secret.

### 2. Create and activate a context

#### Bitbucket Data Center

```bash
bkt context create dc-prod --host bitbucket.mycorp.example --project ABC --set-active
bkt context list
```

#### Bitbucket Cloud

```bash
bkt context create cloud-prod --host api.bitbucket.org --workspace myteam --set-active
bkt context list
```

> **Tip:** Run `bkt auth status` to see configured hosts and the exact host value to use with `--host`.

Contexts capture the host mapping, default project/workspace, and optional default repository for commands.

### 3. Work with repositories

```bash
bkt repo list --limit 20
bkt repo list --workspace myteam --limit 10   # Cloud workspace override
bkt repo view platform-api
bkt repo create data-pipeline --description "Data ingestion" --project DATA
bkt repo create frontend-app --workspace myteam --cloud-project WEB
bkt repo browse --project DATA --repo platform-api
bkt repo clone platform-api --project DATA --ssh
```

`repo list`/`repo view` automatically target the right REST API for your active context: Data Center uses `/rest/api/1.0/projects/{projectKey}/repos`, while Cloud uses `/2.0/repositories/{workspace}`.
For `repo create`, `--project`, `--forkable`, `--default-branch`, and `--scm` are Data Center flags; `--workspace` and `--cloud-project` are Cloud flags. Host-specific create flags are rejected when they would otherwise be ignored.

### 4. Pull request workflows

```bash
bkt pr list --state OPEN --limit 10
bkt pr create --title "feat: cache" --source feature/cache --target main --reviewer alice
bkt pr merge 42 --message "merge: feature/cache"
bkt pr checks 42                              # Show build/CI status
bkt pr checks 42 --wait                       # Wait for builds to complete
bkt pr checks 42 --wait --timeout 5m          # Wait with timeout
bkt pr checks 42 --wait --max-interval 1m     # Custom backoff cap
bkt pr comments 42 --details                  # Review PR comments and thread IDs
bkt pr comments resolve 42 1001               # Resolve a top-level comment thread
bkt pr comments reopen 42 1001                # Reopen a resolved comment thread
bkt pr comments delete 42 1001                # Delete a PR comment
```

The CLI wraps Bitbucket pull-request endpoints for creation, listing, review, and merge operations. The `checks` command displays build status with color-coded output (green for success, red for failure, yellow for in-progress) and supports polling until all builds complete. Polling uses exponential backoff with jitter to avoid overwhelming the API during long builds.
For comment thread state changes, pass the top-level thread comment ID; replies
cannot be resolved or reopened directly.

### 5. Issue tracking (Bitbucket Cloud only)

```bash
bkt issue list --state open --kind bug           # List open bugs
bkt issue view 42 --comments                     # View issue with comments
bkt issue create -t "Login broken" -k bug -p major
bkt issue edit 42 --assignee "{abc-123}" --priority critical
bkt issue close 42                               # Close an issue
bkt issue reopen 42                              # Reopen a closed issue
bkt issue comment 42 -b "Fixed in v1.2.0"        # Add a comment
bkt issue status                                 # Show your assigned/created issues

# Attachments
bkt issue attachment list 42                     # List attachments
bkt issue attachment upload 42 screenshot.png    # Upload file(s)
bkt issue attachment download 42 --all           # Download all attachments
bkt issue attachment delete 42 old-file.txt      # Delete an attachment
```

Note: The issue tracker is only available for Bitbucket Cloud. Bitbucket Data Center uses Jira for issue tracking.

### 6. Branch, permission, webhook, pipeline, and extension management

```bash
bkt branch list --workspace myteam           # Cloud branch listing
bkt branch create release/1.9 --from main    # Data Center branch utils
bkt perms repo list --project DATA --repo platform-api
bkt webhook create --name "CI" --url https://ci.example.com/hook --event repo:refs_changed
bkt pipeline run --workspace myteam --repo api --ref main --var ENV=staging
bkt extension install https://github.com/example/bkt-hello.git
bkt extension exec hello -- --flag=1
bkt status pipeline {pipeline-uuid}
bkt status rate-limit
```

Branch utilities use Bitbucket's Branch Utils REST API for listing, creation, deletion, and default updates. Permission and webhook commands map to their respective REST endpoints for consistent automation.

Extensions are cloned into `$XDG_CONFIG_HOME/bkt/extensions` (or the directory configured via `BKT_CONFIG_DIR`) and executed in-place. Binaries should follow the `bkt-<name>` naming convention so the CLI can discover them automatically.

### Structured output & raw API access

Every command supports the global `--json` and `--yaml` flags for automation-ready output.

For endpoints that are not yet wrapped, reach directly for the API escape hatch:

```bash
bkt api /rest/api/1.0/projects --param limit=100 --json
bkt api /repositories --param workspace=myteam --field pagelen=50
```

## Security

This project uses automated secret scanning ([gitleaks](https://github.com/gitleaks/gitleaks)), dependency updates ([Dependabot](https://github.com/dependabot)), and security posture tracking ([OSSF Scorecard](https://github.com/ossf/scorecard)).

Found a security issue? See our [security policy](SECURITY.md) for responsible disclosure.

## Development

### Project Layout

```
cmd/bkt/             # CLI entry point
internal/bktcmd/     # Main() wiring (factory + root command)
internal/build/      # Version metadata (overridden via ldflags)
internal/config/     # Context and host configuration
internal/remote/     # Git remote parsing utilities
pkg/cmd/             # Cobra command implementations (auth, repo, pr, ...)
pkg/cmdutil/         # Shared command helpers and factory wiring
pkg/iostreams/       # IO stream abstractions
pkg/bbdc/            # Bitbucket Data Center client implementation
pkg/bbcloud/         # Bitbucket Cloud client implementation
pkg/format/          # Output rendering helpers
pkg/httpx/           # Shared HTTP client and retry logic
```

### Building & Testing

```bash
make build      # Build the binary to ./bin/bkt
make test       # Run unit tests
make fmt        # Format code
make lint       # Run linters
make tidy       # Tidy go modules
```

`go test ./...` runs fast smoke coverage that wires the CLI against an in-memory Bitbucket mock (see `pkg/cmd/smoke/cli_smoke_test.go`).

## Troubleshooting

### Debug HTTP Requests

To see API request URLs and response status codes, set the `BKT_HTTP_DEBUG` environment variable:

```bash
BKT_HTTP_DEBUG=1 bkt pipeline view 10
```

This outputs request method/URL and response status, useful for diagnosing API errors.

## Support

- **Questions / Ideas**: File an [issue](https://github.com/avivsinai/bitbucket-cli/issues/new?template=feature_request.md)
- **Bug Reports**: File an [issue](https://github.com/avivsinai/bitbucket-cli/issues/new?template=bug_report.md)

## License

`bkt` is available under the [MIT License](LICENSE).
