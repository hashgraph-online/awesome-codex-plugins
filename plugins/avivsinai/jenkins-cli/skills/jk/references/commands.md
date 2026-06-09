# Jenkins CLI Command Reference

Complete command reference for `jk`. Run `jk <command> --help` for details.

## Authentication

### Login

```bash
# Login with credentials
jk auth login https://jenkins.example.com --username alice --token <API_TOKEN>

# Login to a Jenkins controller that uses Google/OIDC/SSO in the browser
jk auth login https://jenkins.example.com --username alice@example.com --token <JENKINS_API_TOKEN>

# With context name
jk auth login https://jenkins.example.com --name prod --username alice --token <TOKEN>

# TLS options
jk auth login https://jenkins.example.com --username alice --token <TOKEN> --insecure
jk auth login https://jenkins.example.com --username alice --token <TOKEN> --ca-file /path/to/ca.pem

# With proxy
jk auth login https://jenkins.example.com --username alice --token <TOKEN> --proxy http://proxy:8080

# Allow insecure storage (when keychain unavailable)
jk auth login https://jenkins.example.com --username alice --token <TOKEN> --allow-insecure-store
```

Options:
- `--name` — Context name (defaults to hostname)
- `--username` — Jenkins user ID (Google/SSO users: usually your email)
- `--token` — Jenkins API token
- `--insecure` — Skip TLS verification
- `--proxy` — Proxy URL
- `--ca-file` — Custom CA bundle path
- `--set-active` — Set as active context (default: true)
- `--allow-insecure-store` — Allow encrypted file fallback

For Google OAuth, OpenID Connect, Okta, Azure AD, or other browser SSO security realms, first sign in to Jenkins in the browser and create a Jenkins API token from `/me/configure`. Use that Jenkins API token with `--token`; do not use a Google/OIDC access token.

### Status and Logout

```bash
jk auth status                           # Show active context info
jk auth logout                           # Logout from active context
jk auth logout prod                      # Logout from specific context
jk auth logout --context prod            # Alternative syntax
```

## Context Management

```bash
# List contexts (* = active)
jk context ls

# Switch active context
jk context use prod-jenkins

# Delete context
jk context rm staging
```

Environment: `JK_CONTEXT` overrides active context.

## Search Commands

Cross-job discovery across folders:

```bash
# Search by job name pattern
jk search --job-glob '*deploy*'

# Search in specific folder
jk search --folder team/services --job-glob '*api*'

# Limit results
jk search --job-glob '*' --limit 20

# Filter by run attributes
jk search --job-glob '*' --filter result=SUCCESS --since 7d

# Filter by parameter values
jk search --job-glob '*/deploy-*' --filter param.ENVIRONMENT=production

# Control scan depth
jk search --job-glob '*' --max-scan 100

# Select additional fields
jk search --job-glob '*' --select parameters --limit 5
```

Options:
- `--folder` — Anchor search in folder
- `--job-glob` — Job name pattern (doublestar supported)
- `--filter key[op]value` — Filter runs (repeatable)
- `--since <duration>` — Time bound (e.g., `72h`, `7d`)
- `--limit <n>` — Max results (default: 10)
- `--max-scan <n>` — Max runs to inspect per job (default: 500)
- `--select field1,field2` — Project additional fields
- `--regex` — Enable regex matching for filters

## Job Commands

### List

```bash
jk job ls                                # List jobs at root
jk job ls team/app                       # List jobs in folder (positional)
jk job ls --folder team/app              # List jobs in folder (flag)
```

### View

```bash
jk job view team/app/pipeline            # View job details
```

### Create

```bash
jk job create auth-relay \
  --folder platform/services \
  --repo-owner playg \
  --repository taboola-sales-skills \
  --script-path services/auth-relay/Jenkinsfile \
  --credentials bitbucket-ro

# Optional discovery behavior
jk job create auth-relay \
  --repo-owner playg \
  --repository taboola-sales-skills \
  --branch-strategy only-prs \
  --discover-origin-prs \
  --discover-fork-prs
```

Options:
- `--folder` — Folder path where the job should be created
- `--description` — Job description
- `--repo-owner` — Bitbucket repository owner/workspace
- `--repository` — Bitbucket repository name
- `--script-path` — Jenkinsfile path inside the repository (default: `Jenkinsfile`)
- `--credentials` — Jenkins credentials ID for the Bitbucket source
- `--bitbucket-url` — Bitbucket server URL (default: `https://bitbucket.org`)
- `--branch-strategy all|exclude-prs|only-prs` — Branch discovery mode
- `--discover-origin-prs` — Discover PRs from the origin repository
- `--discover-fork-prs` — Discover PRs from forks using `TrustTeamForks`

### Config

```bash
# Fetch raw config.xml to stdout
jk job config platform/services/auth-relay

# Save config.xml for review or editing
jk job config platform/services/auth-relay > auth-relay.config.xml
```

Notes:
- Output is always raw XML.
- `--json`, `--yaml`, and `--format json|yaml` are rejected for this command.

### Configure

```bash
# Replace config.xml from a file
jk job configure platform/services/auth-relay --file auth-relay.config.xml

# Replace config.xml from stdin
cat auth-relay.config.xml | jk job configure platform/services/auth-relay --stdin

# Patch only the Jenkinsfile path for a multibranch job
jk job configure platform/services/auth-relay --script-path services/auth-relay/Jenkinsfile
```

Options:
- `--file <path>` — Read a full `config.xml` replacement from a file
- `--stdin` — Read a full `config.xml` replacement from standard input
- `--script-path <path>` — Patch the Multibranch Pipeline Jenkinsfile path

### Scan

```bash
# Trigger a multibranch rescan
jk job scan platform/services/auth-relay
```

Notes:
- `jk job scan` is only valid for Multibranch Pipeline jobs.
- The command validates the target job type before triggering the Jenkins `/build?delay=0` endpoint.

## Run Commands

### List

```bash
jk run ls team/app/pipeline              # List recent runs
jk run ls team/app/pipeline --limit 50   # Limit results

# Filtering
jk run ls team/app/pipeline --filter result=SUCCESS
jk run ls team/app/pipeline --filter result=FAILURE
jk run ls team/app/pipeline --filter param.ENV=staging
jk run ls team/app/pipeline --since 7d

# Grouping and aggregation
jk run ls team/app/pipeline --group-by result --agg count
jk run ls team/app/pipeline --group-by param.ENV --agg last

# Include queued builds
jk run ls team/app/pipeline --include-queued

# With metadata for agents
jk run ls team/app/pipeline --json --with-meta

# Pagination
jk run ls team/app/pipeline --cursor <cursor>
```

Options:
- `--limit <n>` — Max results (default: 20)
- `--cursor <string>` — Pagination cursor
- `--filter key[op]value` — Filter runs (repeatable)
- `--since <duration>` — Time bound
- `--select field1,field2` — Project additional fields
- `--group-by <field>` — Group results
- `--agg count|first|last` — Aggregation for groups
- `--include-queued` — Include queued builds
- `--with-meta` — Include metadata in JSON output
- `--regex` — Enable regex matching for filters

### Search

```bash
jk run search --job-glob '*deploy*'      # Same as `jk search`
```

### View Parameters

```bash
jk run params team/app/pipeline          # Show job's parameter definitions
```

### Start

```bash
jk run start team/app/pipeline           # Trigger a run
jk run start team/app/pipeline -p BRANCH=main -p ENV=staging

# Follow logs until completion
jk run start team/app/pipeline --follow
jk run start team/app/pipeline --follow --follow-interval 500ms

# Wait for completion (no log streaming)
jk run start team/app/pipeline --wait
jk run start team/app/pipeline --wait --interval 2s --timeout 10m

# Get only the result
jk run start team/app/pipeline --follow --result

# Fuzzy job matching
jk run start deploy --fuzzy
jk run start deploy --fuzzy --non-interactive

# Quiet mode (outputs only build number)
jk run start team/app/pipeline --quiet
```

Options:
- `-p, --param key=value` — Build parameter (repeatable)
- `--follow` — Follow logs until completion
- `--follow-interval <duration>` — Poll interval for logs (default: 500ms)
- `--fuzzy` — Enable fuzzy job name matching
- `--non-interactive` — Fail on ambiguous matches
- `--result` — Output only final result (requires --follow)
- `--wait` — Wait for completion without streaming logs
- `--interval <duration>` — Wait poll interval (default: 2s)
- `--timeout <duration>` — Max wait time (0 = no timeout)

### View

```bash
jk run view team/app/pipeline 128        # View run details

# Get only result
jk run view team/app/pipeline 128 --result

# Exit with build result code
jk run view team/app/pipeline 128 --exit-status

# Wait for completion
jk run view team/app/pipeline 128 --wait
jk run view team/app/pipeline 128 --wait --interval 2s --timeout 5m

# Show human-readable summary
jk run view team/app/pipeline 128 --summary
```

Options:
- `--result` — Output only build result
- `--exit-status` — Exit with code based on build result
- `--wait` — Wait for build to complete
- `--interval <duration>` — Wait poll interval (default: 2s)
- `--timeout <duration>` — Max wait time (0 = no timeout)
- `--summary` — Show human-readable summary

### Cancel

```bash
jk run cancel team/app/pipeline 128      # Cancel running build
jk run cancel team/app/pipeline 128 --mode stop   # Default
jk run cancel team/app/pipeline 128 --mode term   # Terminate
jk run cancel team/app/pipeline 128 --mode kill   # Force kill
```

Options:
- `--mode stop|term|kill` — Cancellation mode (default: stop)

### Rerun

```bash
jk run rerun team/app/pipeline 128       # Rerun with same parameters
jk run rerun team/app/pipeline 128 --follow
jk run rerun team/app/pipeline 128 --wait --timeout 10m
jk run rerun team/app/pipeline 128 --follow --result
```

Options:
- `--follow` — Follow logs until completion
- `--follow-interval <duration>` — Poll interval for logs
- `--result` — Output only final result (requires --follow)
- `--wait` — Wait for completion without streaming logs
- `--interval <duration>` — Wait poll interval
- `--timeout <duration>` — Max wait time

## Log Commands

```bash
jk log team/app/pipeline 128             # View console log (snapshot)
jk log team/app/pipeline 128 --follow    # Stream live logs
jk log team/app/pipeline 128 --follow --interval 2s
jk log team/app/pipeline 128 --plain     # No decorations
```

Options:
- `--follow` — Stream live output
- `--interval <duration>` — Poll interval (default: 1s)
- `--plain` — Disable headings and formatting

## Artifact Commands

### List

```bash
jk artifact ls team/app/pipeline 128     # List artifacts
```

### Download

```bash
jk artifact download team/app/pipeline 128
jk artifact download team/app/pipeline 128 --pattern "**/*.jar"
jk artifact download team/app/pipeline 128 -p "reports/**/*.xml"
jk artifact download team/app/pipeline 128 -o ./artifacts/
jk artifact download team/app/pipeline 128 -p "*.log" --allow-empty
```

Options:
- `-p, --pattern <glob>` — Filter pattern (default: `**/*`)
- `-o, --output <dir>` — Output directory (default: `.`)
- `--allow-empty` — Don't error if no artifacts match

## Test Commands

### Report

```bash
jk test report team/app/pipeline 128     # View test report
jk test report team/app/pipeline 128 --json
```

## Credential Commands

### List

```bash
jk cred ls                               # List system credentials
jk cred ls --scope system                # Explicit system scope
jk cred ls --scope folder --folder team/app
```

Options:
- `--scope system|folder` — Credential scope (default: system)
- `--folder <path>` — Folder path (required for folder scope)

### Create Secret

```bash
jk cred create-secret --id my-secret --secret "value"
jk cred create-secret --id my-secret --secret "value" --description "API key"

# From stdin
echo "secret" | jk cred create-secret --id my-secret --from-stdin

# Folder-scoped
jk cred create-secret --id my-secret --secret "value" --scope folder --folder team/app
```

Options:
- `--id <id>` — Credential ID (required)
- `--secret <value>` — Secret value
- `--description <text>` — Description
- `--from-stdin` — Read secret from stdin
- `--scope system|folder` — Scope (default: system)
- `--folder <path>` — Folder path (required for folder scope)

### Delete

```bash
jk cred rm my-secret                     # Delete system credential
```

## Node Commands

### List

```bash
jk node ls                               # List all nodes
```

### Cordon

```bash
jk node cordon agent-01                  # Mark temporarily offline
jk node cordon agent-01 --message "Maintenance"
```

Options:
- `--message <text>` — Offline message

### Uncordon

```bash
jk node uncordon agent-01                # Bring back online
```

### Remove

```bash
jk node rm agent-01                      # Delete node
```

## Queue Commands

### List

```bash
jk queue ls                              # List queued items
```

### Cancel

```bash
jk queue cancel <id>                     # Cancel queued item
```

## Plugin Commands

### List

```bash
jk plugin ls                             # List installed plugins
```

### Install

```bash
jk plugin install docker-workflow        # Install (prompts for confirm)
jk plugin install docker-workflow --yes  # Skip confirmation
jk plugin install docker-workflow@1.26   # Specific version
jk plugin install plugin1 plugin2        # Multiple plugins
```

Options:
- `-y, --yes` — Skip confirmation prompt

### Enable/Disable

```bash
jk plugin enable docker-workflow
jk plugin disable docker-workflow
```

## Global Options

All commands support:
- `-c, --context <name>` — Use specific context
- `--json` — JSON output
- `--yaml` — YAML output
- `--format json|yaml` — Output format
- `--jq <expr>` — Filter JSON with jq expression
- `-t, --template <tmpl>` — Format with Go template
- `-q, --quiet` — Suppress non-essential output

## Environment Variables

- `JK_CONTEXT` — Override active context (empty = use config)
- `JK_QUIET` — Equivalent to `--quiet` (any value enables)

## Exit Codes

### General Exit Codes

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

### Build Result Exit Codes (with `--follow` or `--wait`)

| Code | Result |
|------|--------|
| 0 | SUCCESS |
| 10 | UNSTABLE |
| 11 | FAILURE |
| 12 | ABORTED |
| 13 | NOT_BUILT |
| 14 | RUNNING |
