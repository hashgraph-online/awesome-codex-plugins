---
name: jk
version: 0.0.34
description: Jenkins CLI for controllers. Use when users need to manage jobs, pipelines, config.xml, runs, logs, artifacts, credentials, nodes, or queues in Jenkins. Triggers include "jenkins", "jk", "pipeline", "build", "job create", "job config", "config.xml", "run logs", "jenkins credentials", "jenkins node".
metadata:
  short-description: Jenkins CLI for jobs, config, pipelines, runs
  compatibility: claude-code, codex-cli
---

# Jenkins CLI (jk)

`jk` is a GitHub CLI–style interface for **Jenkins controllers**. It provides modern, scriptable workflows for developers and operators.

## Dependency Check

**Before executing any `jk` command**, verify the CLI is installed:

```bash
jk --version
```

For `jk job create`, `jk job config`, `jk job configure`, and `jk job scan`, use `jk` `0.0.29` or newer.

If the command fails or `jk` is not found, install it using one of these methods:

| Platform | Command |
|----------|---------|
| macOS/Linux | `brew install avivsinai/tap/jk` |
| Windows | `scoop bucket add avivsinai https://github.com/avivsinai/scoop-bucket && scoop install jk` |
| Go | `go install github.com/avivsinai/jenkins-cli/cmd/jk@latest` |
| Binary | Download from [GitHub Releases](https://github.com/avivsinai/jenkins-cli/releases) |

**Only proceed with `jk` commands after confirming installation succeeds.**

## Authentication

```bash
# Login with credentials
jk auth login https://jenkins.example.com --username alice --token <API_TOKEN>

# Login to a Jenkins controller that uses Google/OIDC/SSO in the browser
jk auth login https://jenkins.example.com --username alice@example.com --token <JENKINS_API_TOKEN>

# Login with custom context name
jk auth login https://jenkins.example.com --name prod --username alice --token <TOKEN>

# Login with TLS options
jk auth login https://jenkins.example.com --username alice --token <TOKEN> --insecure
jk auth login https://jenkins.example.com --username alice --token <TOKEN> --ca-file /path/to/ca.pem

# Check auth status (active context)
jk auth status

# Logout from a context
jk auth logout              # Logout from active context
jk auth logout prod         # Logout from specific context
```

Options for `auth login`:
- `--name` — Context name (defaults to hostname)
- `--username` — Jenkins user ID (Google/SSO users: usually your email)
- `--token` — Jenkins API token
- `--insecure` — Skip TLS verification
- `--proxy` — Proxy URL
- `--ca-file` — Custom CA bundle
- `--set-active` — Set as active context (default: true)
- `--allow-insecure-store` — Allow encrypted file fallback

For Google OAuth, OpenID Connect, Okta, Azure AD, or other browser SSO security realms, first sign in to Jenkins in the browser and create a Jenkins API token from `/me/configure`. Use that Jenkins API token with `--token`; do not use a Google/OIDC access token.

## Contexts

Contexts store controller URLs and credentials for easy switching:

```bash
# List contexts (* = active)
jk context ls

# Switch active context
jk context use prod-jenkins

# Remove a context
jk context rm staging
```

Environment: `JK_CONTEXT` overrides active context.

## Quick Command Reference

| Task | Command |
|------|---------|
| Search jobs | `jk search --job-glob '*deploy*'` |
| List jobs | `jk job ls` |
| View job | `jk job view team/app` |
| Create multibranch job | `jk job create auth-relay --folder platform/services --repo-owner playg --repository repo` |
| Fetch job config | `jk job config platform/services/auth-relay` |
| Patch Jenkinsfile path | `jk job configure platform/services/auth-relay --script-path services/auth-relay/Jenkinsfile` |
| Rescan multibranch job | `jk job scan platform/services/auth-relay` |
| List runs | `jk run ls team/app` |
| Start run | `jk run start team/app -p KEY=value` |
| View run | `jk run view team/app 128` |
| Follow logs | `jk run start team/app --follow` |
| Stream logs | `jk log team/app 128 --follow` |
| Download artifacts | `jk artifact download team/app 128` |
| Test report | `jk test report team/app 128` |
| List credentials | `jk cred ls` |
| List nodes | `jk node ls` |
| View queue | `jk queue ls` |
| List plugins | `jk plugin ls` |

## Job Discovery

```bash
# Search across folders
jk search --job-glob '*deploy*' --limit 10

# Search in specific folder
jk search --folder team/services --job-glob '*api*'

# Filter by run results
jk search --job-glob '*' --filter result=FAILURE --since 7d

# With parameter filters
jk search --job-glob '*/deploy-*' --filter param.ENV=production
```

## Job Operations

```bash
# List jobs in root
jk job ls

# List jobs in folder (positional or flag)
jk job ls team/app
jk job ls --folder team/app

# View job details
jk job view team/app/pipeline

# Create a Bitbucket-backed Multibranch Pipeline job
jk job create auth-relay \
  --folder platform/services \
  --repo-owner playg \
  --repository taboola-sales-skills \
  --script-path services/auth-relay/Jenkinsfile \
  --credentials bitbucket-ro \
  --branch-strategy all

# Fetch raw config.xml for a job
jk job config platform/services/auth-relay

# Replace config.xml from a file or stdin
jk job configure platform/services/auth-relay --file auth-relay.config.xml
cat auth-relay.config.xml | jk job configure platform/services/auth-relay --stdin

# Patch only the Jenkinsfile path in a multibranch config
jk job configure platform/services/auth-relay --script-path services/auth-relay/Jenkinsfile

# Trigger a multibranch rescan
jk job scan platform/services/auth-relay
```

## Run Management

### Listing Runs

```bash
# List recent runs
jk run ls team/app/pipeline

# Limit results
jk run ls team/app/pipeline --limit 50

# Filter runs
jk run ls team/app/pipeline --filter result=SUCCESS
jk run ls team/app/pipeline --filter result=FAILURE --since 7d

# Filter by parameters
jk run ls team/app/pipeline --filter param.ENV=staging

# Include queued builds
jk run ls team/app/pipeline --include-queued

# Group by parameter
jk run ls team/app/pipeline --group-by param.ENV --agg last

# With metadata for agents
jk run ls team/app/pipeline --json --with-meta

# Pagination
jk run ls team/app/pipeline --cursor <cursor-from-previous>
```

### Starting Runs

```bash
# Start a run
jk run start team/app/pipeline

# Start with parameters
jk run start team/app/pipeline -p BRANCH=main -p ENV=staging

# Start and follow logs
jk run start team/app/pipeline --follow

# Start, wait for completion (no log streaming)
jk run start team/app/pipeline --wait --timeout 10m

# Get only the result
jk run start team/app/pipeline --follow --result

# Fuzzy job matching
jk run start deploy --fuzzy
```

### Viewing Runs

```bash
# View run details
jk run view team/app/pipeline 128

# Get only result status
jk run view team/app/pipeline 128 --result

# Exit with build result code
jk run view team/app/pipeline 128 --exit-status

# Wait for completion
jk run view team/app/pipeline 128 --wait --timeout 5m

# Show summary
jk run view team/app/pipeline 128 --summary
```

### Other Run Commands

```bash
# View run parameters
jk run params team/app/pipeline

# Cancel a run
jk run cancel team/app/pipeline 128
jk run cancel team/app/pipeline 128 --mode term
jk run cancel team/app/pipeline 128 --mode kill

# Rerun a build (with same parameters)
jk run rerun team/app/pipeline 128
jk run rerun team/app/pipeline 128 --follow
```

## Logs

```bash
# View console log (snapshot)
jk log team/app/pipeline 128

# Stream live logs
jk log team/app/pipeline 128 --follow

# Custom poll interval
jk log team/app/pipeline 128 --follow --interval 2s

# Plain output (no decorations)
jk log team/app/pipeline 128 --plain
```

## Artifacts

```bash
# List artifacts
jk artifact ls team/app/pipeline 128

# Download all artifacts
jk artifact download team/app/pipeline 128

# Download with pattern filter
jk artifact download team/app/pipeline 128 --pattern "**/*.jar"
jk artifact download team/app/pipeline 128 -p "reports/**/*.xml"

# Output directory
jk artifact download team/app/pipeline 128 -o ./artifacts/

# Allow empty result (no error if no matches)
jk artifact download team/app/pipeline 128 -p "*.log" --allow-empty
```

## Test Results

```bash
# View test report
jk test report team/app/pipeline 128

# JSON output
jk test report team/app/pipeline 128 --json
```

## Credentials

```bash
# List credentials (system scope)
jk cred ls

# List folder-scoped credentials
jk cred ls --scope folder --folder team/app

# Create secret text
jk cred create-secret --id my-secret --secret "value"
jk cred create-secret --id my-secret --secret "value" --description "API key"

# Create from stdin
echo "secret-value" | jk cred create-secret --id my-secret --from-stdin

# Folder-scoped credential
jk cred create-secret --id my-secret --secret "value" --scope folder --folder team/app

# Delete credential (system scope only)
jk cred rm my-secret
```

## Node Management

```bash
# List nodes
jk node ls

# Cordon node (mark temporarily offline)
jk node cordon agent-01
jk node cordon agent-01 --message "Maintenance"

# Uncordon node (bring back online)
jk node uncordon agent-01

# Remove node
jk node rm agent-01
```

## Queue Management

```bash
# List queued items
jk queue ls

# Cancel queued item
jk queue cancel <item-id>
```

## Plugin Management

```bash
# List installed plugins
jk plugin ls

# Install plugin (prompts for confirmation)
jk plugin install docker-workflow

# Install without confirmation
jk plugin install docker-workflow --yes

# Install specific version
jk plugin install docker-workflow@1.26

# Enable/disable plugin
jk plugin enable docker-workflow
jk plugin disable docker-workflow
```

## Output Modes

All commands support structured output:

```bash
# JSON output
jk run ls team/app --json

# YAML output
jk run ls team/app --yaml

# Filter with jq expression
jk run ls team/app --json --jq '.items[0].number'

# Go template
jk run ls team/app --json --template '{{range .items}}{{.number}}{{end}}'

# Quiet mode (minimal output)
jk run start team/app --quiet
```

## Global Options

- `-c, --context <name>` — Use specific context
- `--json` — JSON output
- `--yaml` — YAML output
- `--format json|yaml` — Output format
- `--jq <expr>` — Filter JSON with jq expression
- `-t, --template <tmpl>` — Format with Go template
- `-q, --quiet` — Suppress non-essential output

## Environment Variables

- `JK_CONTEXT` — Override active context
- `JK_QUIET` — Equivalent to `--quiet` (any value enables)

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Validation error |
| 3 | Not found |
| 4 | Authentication failure |
| 5 | Permission denied |
| 6 | Connectivity failure |
| 7 | Timeout |
| 8 | Feature unsupported |

With `--follow` or `--wait`, build results use additional codes:

| Code | Result |
|------|--------|
| 0 | SUCCESS |
| 10 | UNSTABLE |
| 11 | FAILURE |
| 12 | ABORTED |
| 13 | NOT_BUILT |
| 14 | RUNNING |

## References

- **Full command reference**: See [references/commands.md](references/commands.md)

<!-- auto-generated by cmd/docgen — do not edit below this line -->

- [artifact](rules/artifact.md) — Work with run artifacts
- [auth](rules/auth.md) — Authenticate with Jenkins instances
- [context](rules/context.md) — Manage Jenkins contexts
- [cred](rules/cred.md) — Manage Jenkins credentials
- [job](rules/job.md) — Manage Jenkins jobs and pipelines
- [node](rules/node.md) — Inspect and manage Jenkins nodes
- [plugin](rules/plugin.md) — Inspect and manage Jenkins plugins
- [queue](rules/queue.md) — Inspect the build queue
- [run](rules/run.md) — Interact with job runs
- [test](rules/test.md) — Inspect test results
- [other](rules/other.md) — log, search, version

<!-- end auto-generated -->
