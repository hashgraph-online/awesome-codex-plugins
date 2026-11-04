# jk

<p align="center"><em>GitHub CLI–style workflows for Jenkins controllers</em></p>

<p align="center">
  <a href="https://github.com/avivsinai/jenkins-cli/releases/latest"><img src="https://img.shields.io/github/v/release/avivsinai/jenkins-cli" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="go.mod"><img src="https://img.shields.io/badge/Go-1.26+-00ADD8.svg" alt="Go Version"></a>
  <a href="https://github.com/avivsinai/jenkins-cli/actions/workflows/ci.yml"><img src="https://github.com/avivsinai/jenkins-cli/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/avivsinai/jenkins-cli/actions/workflows/gitleaks.yml"><img src="https://github.com/avivsinai/jenkins-cli/actions/workflows/gitleaks.yml/badge.svg" alt="Security"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/avivsinai/jenkins-cli"><img src="https://api.scorecard.dev/projects/github.com/avivsinai/jenkins-cli/badge" alt="OpenSSF Scorecard"></a>
</p>

`jk` is a single Go binary for Jenkins operators. Search jobs across folders, trigger and follow runs, stream logs, download artifacts, and manage credentials, nodes, queues, and plugins. Output is human, JSON, or YAML.

This is not the official Jenkins CLI (`jenkins-cli.jar`; [jenkins.io](https://www.jenkins.io/doc/book/managing/cli/)).

**Status ([v0.0.36](https://github.com/avivsinai/jenkins-cli/releases/tag/v0.0.36), 11 Aug 2026):** released and tested against stock Jenkins LTS REST APIs. Auth, contexts, search, jobs, runs, logs, artifacts, tests, credentials, nodes, queue, and plugins ship today. Companion plugin, JCasC, events, and metrics are not in this binary. The version stays 0.x for that reason.

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

Install the `jk` binary from the paths below. Homebrew uses [`avivsinai/tap`](https://github.com/avivsinai/homebrew-tap) (`jk`); Scoop uses [`avivsinai/scoop-bucket`](https://github.com/avivsinai/scoop-bucket). There is no Nix package and no PyPI project for this CLI.

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
go install github.com/avivsinai/jenkins-cli/cmd/jk@v0.0.36
```

Binary will be installed to `$GOPATH/bin` (or `$HOME/go/bin` by default).

### Binary Downloads

Download prebuilt binaries (macOS, Linux, Windows) or `.deb` packages from [GitHub Releases](https://github.com/avivsinai/jenkins-cli/releases).

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
cp -r jenkins-cli/skills/jk ~/.claude/skills/
```

</details>

## Quickstart

Find jobs fast with `jk search` (alias for `jk run search`) before drilling into specific pipelines.

```bash
jk auth login https://jenkins.company.example      # authenticate and create a context
jk context ls                                      # list available contexts
jk search --job-glob '*deploy-*' --limit 5 --json               # discover job paths across folders
jk job create auth-relay --folder platform/services --repo-owner playg --repository my-service-repo --script-path services/auth-relay/Jenkinsfile --credentials bitbucket-ro
jk job config platform/services/auth-relay | rg scriptPath
jk job configure platform/services/auth-relay --script-path services/auth-relay/Jenkinsfile
jk job config platform/services/auth-relay | jk job configure platform/services/auth-relay --stdin
jk job scan platform/services/auth-relay
jk run ls team/app/pipeline --filter result=SUCCESS --since 7d --limit 5 --json --with-meta
jk run ls team/app/pipeline --include-queued   # include queued builds (shown as qN)
jk run params team/app/pipeline                    # inspect inferred parameter metadata
jk log team/app/pipeline 128 --follow              # stream logs until completion
jk log team/app/pipeline 128 --tail 40 --plain      # last 40 lines of a completed console
jk log team/app/pipeline 128 --grep '(?i)error|fail' --tail 20 --json # last 20 matching lines
jk artifact download team/app/pipeline 128 -p "**/*.xml" -o out/
```

### Source revisions in run output

`run ls`, `run view`, and `search` prefer the job's `SCMRevisionAction`
revision over shared-library checkouts. For GitHub pull requests built with a
merge strategy, `commit` is the PR head, not Jenkins' synthetic merge commit.
Branch and repository metadata are omitted when no current checkout can be
matched to that revision; a matching branch name or historical checkout alone
is insufficient. Controllers whose SCM revision exposes neither `hash` nor
`pullHash` (including some Bitbucket/GitLab PR revisions) retain legacy checkout
selection. A failed source-revision lookup is reported as an error.

### Watch a commit's build

```bash
jk run watch team/app/main --commit <full-source-sha> --exit-status --timeout 20m
jk run watch team/app/main --commit <full-source-sha> --json --timeout 20m
```

`run watch` scans retained build history in newest-first pages for an exact full
40- or 64-character hexadecimal source SHA. If no build exists yet, it polls and
shows queue reasons for the job without claiming that those queue entries belong
to the commit. Once it finds a build, it pins that build number even if another
build of the same commit starts later. Executor waits are correlated by the
queue task's build URL, not by its display name.

Progress goes to stderr and is printed only when the state changes; ETA-only
changes are suppressed. JSON/YAML stdout contains one final result, including on
timeout or cancellation. `--interval` defaults to `2s`; `--timeout 0` waits without
a deadline. A timeout covers discovery and execution and exits 124; cancellation
exits 130. With `--exit-status`, build results use the same codes as `run view`
(SUCCESS 0, UNSTABLE 10, FAILURE 11, ABORTED 12, NOT_BUILT 13); an unknown terminal
result exits 1. See the [watch output contract](docs/api.md#29-commit-watch-jk-run-watch---json).

Log filters use Go regular expressions and apply `--grep` before `--tail`. They scan the complete console of a **completed** build; running builds and `--follow` cannot use these filters. Selected output is limited to 2 MiB: if the requested result does not fit, JSON/YAML reports `truncated: true` and `complete: false`. A line larger than 1 MiB fails explicitly. `--plain` keeps output free of headings and notices; use structured output when completeness matters.

### Jenkins SSO / Google OAuth

`jk` uses Jenkins API tokens for scripted clients. If your controller uses Google OAuth, OpenID Connect, Okta, Azure AD, or another browser-based SSO realm, sign in to Jenkins in the browser first, open `/me/configure`, create a Jenkins API token, then run:

```bash
jk auth login https://jenkins.company.example --username <jenkins-user-id> --with-token < jenkins-token.txt
```

`--with-token` reads the token from standard input, so it never shows in the process list. `--token <JENKINS_API_TOKEN>` also works, but `ps` shows it.

Use your Jenkins user ID for `--username`. For many Google/OIDC setups that is your email address, but some SSO realms use an opaque provider ID instead. If you are unsure, sign in to Jenkins in the browser and open `<jenkins-url>/whoAmI/api/json`; use the returned `name` value. If it reports `anonymous`, sign in first. Do not paste a Google OAuth access token into `--token` — Jenkins REST calls expect a Jenkins API token.

This works because Jenkins validates API tokens before consulting the security realm, so SSO realms such as the `google-login` plugin do not block token-based CLI access (covered by an end-to-end test against a google-login controller).

`jk auth login` verifies the credentials against the controller before finishing:

- On success it reports the authenticated user (`Logged in to <url> as <user>`).
- If Jenkins rejects the credentials (or treats them as anonymous), the login fails and the previous context, token, and active-context selection are restored — a typo can't clobber a working login. The error explains the API-token workflow and points to the browser `whoAmI` check above.
- If the request is redirected to a sign-in page (Jenkins form login, `securityRealm/commenceLogin`, or an external identity provider), `jk` reports that the request never authenticated instead of failing on an HTML response. The same detection applies to every `jk` command, so an expired token against an SSO-fronted controller produces an actionable error.
- If the controller cannot be reached, the credentials are saved unverified with a warning. Use `--no-verify` to skip the check entirely (for example when bootstrapping configuration before the controller is up).

Service accounts cannot authenticate through a browser-based SSO realm like `google-login` — they never become Jenkins users, so they cannot hold API tokens. Jenkins itself still needs a Jenkins API token; a front door in front of Jenkins can admit the service account (see below).

### Front door (WAF, SSO proxy, Google IAP)

Some controllers sit behind a front door that needs its own credential before a request reaches Jenkins (the controller answers by IP, but not through its DNS name). Add a `front_door` block to the context in `config.yaml`. `jk` keeps Jenkins Basic auth unchanged and also sends `<header>: Bearer <token>`, where the token is the output of `token_command`:

```yaml
contexts:
  prod:
    url: https://jenkins.example.com
    username: alice@example.com
    front_door:
      mode: proxy-bearer-command
      header: Proxy-Authorization
      token_command: [gcloud, auth, print-identity-token, --audiences=<IAP_CLIENT_ID>]
```

- `token_command` is an argv list. `jk` runs it without a shell before the first request, trims the output, and runs it again when the token is older than 30 minutes. For a service account, add `--impersonate-service-account=<sa-email>` to the gcloud command.
- The header goes on every request to the context's host, including login verification and CSRF crumb requests. Redirects to other hosts (for example artifact downloads from object storage) do not get it.
- `header` cannot be `Authorization`, because `jk` sends the Jenkins API token there. Google IAP accepts `Proxy-Authorization`.
- If the command fails, the error names the context and the command. `jk` never prints the token.
- If a first `jk auth login` is rejected with a 401, 403, or 407 that has no `X-Jenkins` header, the response came from the front door and the login error adds a hint pointing here.
- Configure `front_door` in `config.yaml` first, then run `jk auth login <url> --name prod ...`. Login keeps the existing `front_door` block and verifies through the front door.

### Secret Storage

By default, `jk` stores API tokens in the OS keychain. `--allow-insecure-store` or `JK_ALLOW_INSECURE_STORE=1` selects the encrypted file backend instead of trying native keyring backends. `KEYRING_BACKEND` remains an explicit backend override for advanced use.

For noninteractive file-backend use, set `JK_KEYRING_PASSPHRASE` before running `jk`; compatible fallback variables are `KEYRING_FILE_PASSWORD` and `KEYRING_PASSWORD`.

### Headless authentication

Set `JK_TOKEN` to supply the API token for the selected context without opening
the keyring or storing the token. Context selection stays `--context` >
`JK_CONTEXT` > active context. Empty environment variables are treated as unset.

With no selected context, provide `JK_URL`, `JK_USER` (the Jenkins user ID) and
`JK_TOKEN` together to use an ephemeral connection. For example, after your
secrets manager supplies `JK_TOKEN`:

```bash
export JK_URL=https://jenkins.example.com
export JK_USER=automation
jk run ls team/app/main --json
jk auth status
```

Nothing is written to config or the keyring. `auth status` reports
`Credential source: environment` and never prints the token.

`JK_URL` and `JK_USER` require the complete three-variable tuple. When a stored
context is selected, those values must match its URL and user; they cannot
silently redirect its credential to another controller. An explicitly selected
missing context is an error. `JK_TOKEN` alone requires an existing selected
context. Unset all three variables before `auth login` or `auth logout` to manage
stored credentials; these commands do not persist or remove environment tokens.

Structured `jk search` output already includes lightweight search metadata; `--with-meta` is only needed for `jk run ls` (`jk search` accepts it as a no-op for flag parity).

Add `--json`, `--yaml`, or `--format json|yaml` to supported commands for machine-readable output. Use `--jq` or `--template` to select or reshape JSON results.

```bash
# Extract a single field with jq
jk run view team/app/pipeline 128 --format json --jq '.result'

# Custom formatting with Go templates
jk run view team/app/pipeline 128 --format json --template 'Result={{.result}}'
```

## Pipeline Stage and Step Logs

With the optional [Pipeline Graph View plugin](https://plugins.jenkins.io/pipeline-graph-view/), inspect native Pipeline stages and labelled steps without parsing the combined console:

```bash
jk run steps team/app/main 128
jk run steps team/app/main 128 --json
jk log team/app/main 128 --step 23 --plain
```

Use the returned node IDs, since parallel branches and repeated labels can have the same name. `--step` accepts a stage or step ID and reads only that node's log, capped at 2 MiB. JSON/YAML includes `stepId`, `truncated` and `complete`; `complete` is false for an unfinished build or capped response. Step logs cannot currently be combined with `--follow`, `--tail` or `--grep`. An absent plugin or unsupported run produces an explicit capability error; ordinary console logs keep working without the plugin. These endpoints require only read access to the run.

## Job Commands

Job provisioning and config management:

```bash
# Create a Bitbucket-backed Multibranch Pipeline job
jk job create auth-relay \
  --folder platform/services \
  --repo-owner playg \
  --repository my-service-repo \
  --script-path services/auth-relay/Jenkinsfile \
  --credentials bitbucket-ro \
  --branch-strategy all

# Create a job of any type (Pipeline, Freestyle, Folder, ...) from a full config.xml
jk job config platform/services/auth-relay > auth-relay.config.xml
jk job create auth-relay-copy --folder platform/services --file auth-relay.config.xml

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

## Test reports

Inspect JUnit results with `jk test report <job> <build>` or show only failing
cases with `jk test report <job> <build> --failed`. The filter includes both
`FAILED` and `REGRESSION` cases and keeps aggregate counts for the whole report.
Human case names and error details are single lines with control characters
removed, capped at 160 and 1,024 Unicode characters respectively (plus an ellipsis).
Add `--json` or `--yaml` for case failure details, full stack traces, `age` and
`failedSince` when Jenkins supplies them.

`jk run view <job> <build> --summary` includes at most five failed cases with
their failure history and a short error detail. Names and details are bounded to
160 and 240 Unicode characters respectively (plus an ellipsis when truncated);
stack traces remain available through `test report --failed --json`. When
Jenkins omits `totalCount`, totals are derived from pass, fail and skip counts.

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
