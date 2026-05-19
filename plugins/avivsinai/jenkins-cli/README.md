# jk

<p align="center"><em>GitHub CLI–style workflows for Jenkins controllers</em></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="go.mod"><img src="https://img.shields.io/badge/Go-1.25+-00ADD8.svg" alt="Go Version"></a>
  <a href="https://github.com/avivsinai/jenkins-cli/actions/workflows/ci.yml"><img src="https://github.com/avivsinai/jenkins-cli/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/avivsinai/jenkins-cli/actions/workflows/gitleaks.yml"><img src="https://github.com/avivsinai/jenkins-cli/actions/workflows/gitleaks.yml/badge.svg" alt="Security"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/avivsinai/jenkins-cli"><img src="https://api.scorecard.dev/projects/github.com/avivsinai/jenkins-cli/badge" alt="OpenSSF Scorecard"></a>
</p>

`jk` gives developers and operators a modern, scriptable interface to Jenkins: inspect runs, stream logs, manage credentials, and administer controllers from a single cross-platform binary.

## Features

- **Context-aware auth** – store multiple controllers, switch with `jk context use`, or pin a context via `JK_CONTEXT`.
- **Friendly pipelines** – trigger, rerun, follow, and summarize jobs with human or JSON/YAML output.
- **Job provisioning & config** – create Bitbucket-backed Multibranch Pipeline jobs, inspect raw `config.xml`, patch Jenkinsfile paths, and rescan multibranch jobs.
- **Scriptable output** – `--format json|yaml`, `--jq`, and `--template` for machine-friendly pipelines; `--quiet` for scripting.
- **Discovery-first runs** – filter with `--filter`, bound history with `--since`, group by parameters, and attach machine-readable metadata for agents.
- **Artifacts & tests** – browse artifacts, download filtered sets, and surface aggregated test reports.
- **Platform operations** – cordon nodes, manage credentials, inspect queues, and view installed plugins.
- **GitHub CLI parity** – command structure and UX mirror `gh`, easing adoption in developer toolchains.

## Installation

### Homebrew (macOS/Linux)

```bash
brew install avivsinai/tap/jk
```

### Scoop (Windows)

```powershell
scoop bucket add avivsinai https://github.com/avivsinai/scoop-bucket
scoop install jk
```

### Go Install

```bash
# Install latest version
go install github.com/avivsinai/jenkins-cli/cmd/jk@latest

# Or install specific version
go install github.com/avivsinai/jenkins-cli/cmd/jk@v0.0.29
```

Binary will be installed to `$GOPATH/bin` (or `$HOME/go/bin` by default).

### Binary Downloads

Download prebuilt binaries for your platform from [GitHub Releases](https://github.com/avivsinai/jenkins-cli/releases).

### From Source

```bash
git clone https://github.com/avivsinai/jenkins-cli.git
cd jenkins-cli
make build   # produces ./bin/jk
```

### AI Coding Skill

Install the `jk` skill for Claude Code or Codex CLI:

<details open>
<summary><b>Via skills (Recommended)</b></summary>

Using [Vercel's skills CLI](https://github.com/vercel-labs/add-skill):

```bash
npx skills add avivsinai/jenkins-cli -g -y
```

</details>

<details>
<summary><b>Via skild registry</b></summary>

```bash
npx skild install @avivsinai/jk -t claude -y
```

</details>

<details>
<summary><b>Via Skills Marketplace</b></summary>

> **Known Issue**: Claude Code uses SSH to clone marketplace repos, which fails without SSH keys configured. See [issue #14485](https://github.com/anthropics/claude-code/issues/14485). Use the skills or skild methods instead.

```bash
/plugin marketplace add avivsinai/skills-marketplace
/plugin install jk@avivsinai-marketplace
```

</details>

<details>
<summary><b>Manual install</b></summary>

```bash
git clone https://github.com/avivsinai/jenkins-cli.git
cp -r jenkins-cli/.claude/skills/jk ~/.claude/skills/
```

</details>

## Quickstart

Find jobs fast with `jk search` (alias for `jk run search`) before drilling into specific pipelines.

```bash
jk auth login https://jenkins.company.example      # authenticate and create a context
jk context ls                                      # list available contexts
jk search --job-glob '*deploy-*' --limit 5 --json               # discover job paths across folders
jk job create auth-relay --folder platform/services --repo-owner playg --repository taboola-sales-skills --script-path services/auth-relay/Jenkinsfile --credentials bitbucket-ro
jk job config platform/services/auth-relay | rg scriptPath
jk job configure platform/services/auth-relay --script-path services/auth-relay/Jenkinsfile
jk job config platform/services/auth-relay | jk job configure platform/services/auth-relay --stdin
jk job scan platform/services/auth-relay
jk run ls team/app/pipeline --filter result=SUCCESS --since 7d --limit 5 --json --with-meta
jk run ls team/app/pipeline --include-queued   # include queued builds (shown as qN)
jk run params team/app/pipeline                    # inspect inferred parameter metadata
jk run view team/app/pipeline 128 --follow         # stream logs until completion
jk artifact download team/app/pipeline 128 -p "**/*.xml" -o out/
```

### Jenkins SSO / Google OAuth

`jk` uses Jenkins API tokens for scripted clients. If your controller uses Google OAuth, OpenID Connect, Okta, Azure AD, or another browser-based SSO realm, sign in to Jenkins in the browser first, open `/me/configure`, create a Jenkins API token, then run:

```bash
jk auth login https://jenkins.company.example --username you@example.com --token <JENKINS_API_TOKEN>
```

Use your Jenkins user ID for `--username`; for Google/OIDC setups this is usually your email address. Do not paste a Google OAuth access token into `--token` — Jenkins REST calls expect a Jenkins API token.

Structured `jk search` output already includes lightweight search metadata; `--with-meta` is only needed for `jk run ls`.

Add `--json`, `--yaml`, or `--format json|yaml` to supported commands for machine-readable output. Use `--jq` or `--template` to select or reshape JSON results.

```bash
# Extract a single field with jq
jk run view team/app/pipeline 128 --format json --jq '.result'

# Custom formatting with Go templates
jk run view team/app/pipeline 128 --format json --template 'Result={{.result}}'
```

## Job Commands

Current job provisioning and config management is focused on Multibranch Pipeline workflows:

```bash
# Create a Bitbucket-backed Multibranch Pipeline job
jk job create auth-relay \
  --folder platform/services \
  --repo-owner playg \
  --repository taboola-sales-skills \
  --script-path services/auth-relay/Jenkinsfile \
  --credentials bitbucket-ro \
  --branch-strategy all

# Fetch raw config.xml (stdout is always XML)
jk job config platform/services/auth-relay > auth-relay.config.xml

# Replace config.xml from a file or stdin
jk job configure platform/services/auth-relay --file auth-relay.config.xml
cat auth-relay.config.xml | jk job configure platform/services/auth-relay --stdin

# Patch only the Jenkinsfile path inside a Multibranch Pipeline config
jk job configure platform/services/auth-relay --script-path services/auth-relay/Jenkinsfile

# Trigger a multibranch rescan
jk job scan platform/services/auth-relay
```

## Documentation

- [Specification](docs/spec.md) - Architecture and design decisions
- [API Contracts](docs/api.md) - JSON/YAML schemas for structured output
- [Agent Cookbook](docs/agent-cookbook.md) - Automation recipes and examples
- [Changelog](CHANGELOG.md) - Release notes and migration guidance

## Security

This project uses automated secret scanning ([gitleaks](https://github.com/gitleaks/gitleaks)), dependency updates ([Dependabot](https://github.com/dependabot)), and security posture tracking ([OSSF Scorecard](https://github.com/ossf/scorecard)).

Found a security issue? See our [security policy](SECURITY.md) for responsible disclosure.

## Community

- Read the [code of conduct](CODE_OF_CONDUCT.md) and [contributing guide](CONTRIBUTING.md)
- Ask questions or propose ideas via GitHub Discussions (coming soon) or issues
- Follow the [support guidelines](SUPPORT.md) for help

## Development

### Quick Start

```bash
# First-time setup
make pre-commit-install  # Install git hooks (gitleaks, formatting, etc.)

# Standard workflow
make build      # Build the binary
make test       # Run unit tests
make lint       # Run linters
make security   # Run security checks (gitleaks + pre-commit)
```

### Full Test Suite

```bash
make e2e        # End-to-end tests (requires Docker)
make e2e-up     # Launch test Jenkins (port 28080)
make e2e-down   # Tear down test environment
```

**Prerequisites:**
- [golangci-lint](https://golangci-lint.run/) for linting
- [gitleaks](https://github.com/gitleaks/gitleaks) for secret scanning
- [pre-commit](https://pre-commit.com/) for git hooks
- Docker/Colima for e2e tests

**Note:** E2e tests require Docker. On macOS with Colima, use `colima start --network-address`. See [CONTRIBUTING.md](CONTRIBUTING.md#end-to-end-tests) for details. Skip with `JK_E2E_DISABLE=1 make test`.

### Before Submitting PRs

```bash
make security   # Gitleaks + pre-commit checks
make lint       # Run linter
make test       # Run tests
```

## License

`jk` is available under the [MIT License](LICENSE).
