# Shell Script Standards Catalog - Vibe Canonical Reference

**Version:** 1.0.0
**Last Updated:** 2026-01-21
**Purpose:** Canonical shell scripting standards for vibe skill validation

---

## Table of Contents

1. [Required Patterns](#required-patterns)
2. [Shellcheck Integration](#shellcheck-integration)
3. [Error Handling](#error-handling)
4. [Logging Functions](#logging-functions)
5. [Script Organization](#script-organization)
6. [Security](#security)
7. [Common Patterns](#common-patterns)
8. [Testing](#testing)
9. [Documentation Standards](#documentation-standards)
10. [Code Quality Metrics](#code-quality-metrics)
11. [Anti-Patterns Avoided](#anti-patterns-avoided)
12. [Compliance Assessment](#compliance-assessment)

---

## Required Patterns

### Shebang and Flags

Every shell script MUST start with:

```bash
#!/usr/bin/env bash
set -eEuo pipefail
```

**Flag explanation:**

| Flag | Effect | Failure without |
|------|--------|-----------------|
| `-e` | Exit on error | Silent failures, continued execution |
| `-E` | ERR trap inherited | Traps don't fire in functions |
| `-u` | Exit on undefined | Empty variables cause silent bugs |
| `-o pipefail` | Pipe fails propagate | `false \| true` returns 0 |

### Variable Quoting

Always quote variables to prevent word splitting and globbing:

```bash
# GOOD - Quoted variables, safe defaults
namespace="${NAMESPACE:-default}"
kubectl get pods -n "${namespace}"

# GOOD - Array expansion
files=("file with spaces.txt" "another file.txt")
cat "${files[@]}"

# BAD - Unquoted variables (word splitting, globbing risks)
kubectl get pods -n $namespace
cat $files
```

### Safe Defaults

```bash
# Pattern: ${VAR:-default}
namespace="${NAMESPACE:-default}"
timeout="${TIMEOUT:-300}"
log_level="${LOG_LEVEL:-INFO}"

# Pattern: ${VAR:?error message}
api_key="${API_KEY:?API_KEY must be set}"
```

---

## Shellcheck Integration

### Repository Configuration

Create `.shellcheckrc` at repo root:

```ini
# .shellcheckrc
# Shell variant
shell=bash

# Can't follow non-constant source
disable=SC1090
# Not following sourced files
disable=SC1091
# Consider invoking separately (pipefail handles this)
disable=SC2312
```

### Common Shellcheck Fixes

| Code | Issue | Fix |
|------|-------|-----|
| SC2086 | Word splitting | Quote: `"$var"` |
| SC2164 | cd can fail | `cd /path \|\| exit 1` |
| SC2046 | Word splitting in $() | Quote: `"$(command)"` |
| SC2181 | Checking $? | Use `if command; then` |
| SC2155 | declare/local hides exit | Split: `local x; x=$(cmd)` |
| SC2034 | Unused variable | Remove or use |
| SC2206 | Word splitting in array | `read -ra arr <<< "$var"` |

### Disable Rules Sparingly

```bash
# Only disable when truly necessary
# shellcheck disable=SC2086
# Reason: Word splitting is intentional for flag array
$tool_cmd $flags_array "$input_file"
```

---

## Error Handling

### ERR Trap for Debug Context

```bash
#!/usr/bin/env bash
set -eEuo pipefail

on_error() {
    local exit_code=$?
    local line_no=$1
    echo "ERROR: Script failed on line $line_no with exit code $exit_code" >&2
    echo "Command: ${BASH_COMMAND}" >&2
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR
```

### Exit Code Documentation

Document exit codes in script headers:

```bash
#!/usr/bin/env bash
# ===================================================================
# Script: deploy.sh
# Purpose: Deploy application to Kubernetes cluster
# Usage: ./deploy.sh <namespace> [--dry-run]
#
# Exit Codes:
#   0 - Success
#   1 - Argument error
#   2 - Missing dependency
#   3 - Configuration error
#   4 - Validation failed
#   5 - User cancelled
#   6 - Deployment failed
# ===================================================================

set -eEuo pipefail
```

### Cleanup Pattern

```bash
#!/usr/bin/env bash
set -eEuo pipefail

# Create temp directory
TMPDIR=$(mktemp -d)

cleanup() {
    local exit_code=$?
    rm -rf "$TMPDIR" 2>/dev/null || true
    exit "$exit_code"
}
trap cleanup EXIT

# Your code here - cleanup runs on exit or error
```

### Checking Command Success

```bash
# GOOD - Direct conditional
if kubectl get namespace "$ns" &>/dev/null; then
    echo "Namespace exists"
else
    echo "Creating namespace"
    kubectl create namespace "$ns"
fi

# GOOD - Negation
if ! kubectl get namespace "$ns" &>/dev/null; then
    kubectl create namespace "$ns"
fi

# BAD - Capturing exit code (unnecessary)
kubectl get namespace "$ns" &>/dev/null
result=$?
if [[ $result -eq 0 ]]; then
    ...
fi
```

---

## Logging Functions

### Standard Logging

```bash
# Logging functions
log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
warn() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $*" >&2; }
err()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }
die()  { err "$*"; exit 1; }

# Debug logging (controlled by variable)
debug() {
    [[ "${DEBUG:-false}" == "true" ]] && echo "[DEBUG] $*" >&2
}

# Usage
log "Processing namespace: ${NAMESPACE}"
warn "Timeout exceeded, retrying..."
die "Required tool 'kubectl' not found"
debug "Variable state: foo=$foo"
```

### Colored Output (Optional)

```bash
# Color codes (check if terminal supports colors)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'  # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error()   { echo -e "${RED}[ERR]${NC} $*" >&2; }
```

---

## Script Organization

### Full Template

```bash
#!/usr/bin/env bash
# ===================================================================
# Script: <name>.sh
# Purpose: <one-line description>
# Usage: ./<script>.sh [args]
#
# Environment Variables:
#   NAMESPACE - Target namespace (default: default)
#   DRY_RUN   - If "true", don't make changes (default: false)
#
# Exit Codes:
#   0 - Success
#   1 - Argument error
#   2 - Missing dependency
# ===================================================================

set -eEuo pipefail

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

NAMESPACE="${NAMESPACE:-default}"
DRY_RUN="${DRY_RUN:-false}"
TIMEOUT="${TIMEOUT:-300}"

# -------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
warn() { echo "[$(date '+%H:%M:%S')] WARNING: $*" >&2; }
err()  { echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2; }
die()  { err "$*"; exit 1; }

on_error() {
    local exit_code=$?
    err "Script failed on line $1 with exit code $exit_code"
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

cleanup() {
    rm -rf "${TMPDIR:-}" 2>/dev/null || true
}
trap cleanup EXIT

usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [options] <required-arg>

Options:
    -h, --help      Show this help message
    -n, --namespace Kubernetes namespace (default: $NAMESPACE)
    --dry-run       Don't make changes, just show what would happen

Environment:
    NAMESPACE       Same as --namespace
    DRY_RUN         Same as --dry-run (set to "true")
EOF
}

validate_args() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi
}

check_dependencies() {
    local missing=()
    for cmd in kubectl jq; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        die "Missing dependencies: ${missing[*]}"
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

main() {
    local required_arg=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            -*)
                die "Unknown option: $1"
                ;;
            *)
                required_arg="$1"
                shift
                ;;
        esac
    done

    validate_args "${required_arg:-}"
    check_dependencies

    log "Starting with namespace: $NAMESPACE"
    [[ "$DRY_RUN" == "true" ]] && log "DRY RUN MODE - no changes will be made"

    # Main logic here
}

# Setup
TMPDIR=$(mktemp -d)

# Run
main "$@"
```

---

## Security

### Secret Handling

**Never pass secrets as CLI arguments** - they're visible in `ps aux`:

```bash
# BAD - Secrets visible in process list
kubectl create secret generic my-secret --from-literal=token="$TOKEN"

# GOOD - Pass via stdin
kubectl create secret generic my-secret --from-literal=token=- <<< "$TOKEN"

# GOOD - Use file-based approach
echo "$SECRET" > "$TMPDIR/secret"
chmod 600 "$TMPDIR/secret"
kubectl create secret generic my-secret --from-file=token="$TMPDIR/secret"

# GOOD - Environment variable (some tools support this)
export TOKEN
some_tool --token-env=TOKEN
```

### Input Validation

#### Kubernetes Resource Names (RFC 1123)

```bash
validate_namespace() {
    local ns="$1"
    # RFC 1123: lowercase alphanumeric, hyphens, max 63 chars
    if [[ ! "$ns" =~ ^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$ ]] && \
       [[ ! "$ns" =~ ^[a-z0-9]$ ]]; then
        die "Invalid namespace format: $ns (must be RFC 1123 label)"
    fi
}
```

#### Path Traversal Prevention

```bash
validate_path() {
    local path="$1"
    # Block path traversal
    case "$path" in
        *..*)
            die "Path traversal detected: $path"
            ;;
    esac
    # Optionally ensure path is under allowed directory
    local resolved
    resolved=$(realpath -m "$path" 2>/dev/null) || die "Invalid path: $path"
    if [[ "$resolved" != "$ALLOWED_DIR"/* ]]; then
        die "Path outside allowed directory: $path"
    fi
}
```

### Sed Injection Prevention

```bash
# User input in sed can have special meaning
# BAD - Injection possible
NAME="test&id"  # & inserts matched text
sed "s/{{NAME}}/$NAME/g" template.txt  # & causes issues

# GOOD - Escape special characters
escape_sed_replacement() {
    printf '%s' "$1" | sed -e 's/[&/\]/\\&/g'
}

escaped_name=$(escape_sed_replacement "$NAME")
sed "s/{{NAME}}/$escaped_name/g" template.txt
```

### JSON Construction

```bash
# BAD - String interpolation (injection risk, quoting issues)
json="{\"name\": \"$NAME\", \"value\": \"$VALUE\"}"

# GOOD - Use jq for proper escaping
json=$(jq -n --arg name "$NAME" --arg value "$VALUE" \
    '{name: $name, value: $value}')

# GOOD - Building complex JSON
json=$(jq -n \
    --arg name "$NAME" \
    --arg ns "$NAMESPACE" \
    --argjson replicas "$REPLICAS" \
    '{
        metadata: {name: $name, namespace: $ns},
        spec: {replicas: $replicas}
    }')
```

---

## Common Patterns

### Polling with Timeout

> **SECURITY WARNING:** The pattern below uses `eval` which can lead to command injection
> if `condition_cmd` contains unsanitized user input. **Never pass untrusted input to this function.**
> For safer alternatives, use bash functions instead of string evaluation:
> ```bash
> # SAFER: Pass a function name instead of a command string
> wait_for_condition 300 10 check_pod_running
> ```

```bash
wait_for_condition() {
    local timeout=${1:-300}
    local interval=${2:-10}
    local condition_cmd="$3"

    # WARNING: eval is dangerous with untrusted input - see security note above
    local elapsed=0
    while ! eval "$condition_cmd" &>/dev/null; do
        if [[ $elapsed -ge $timeout ]]; then
            err "Timeout waiting for condition after ${timeout}s"
            return 1
        fi
        log "Waiting... (${elapsed}s/${timeout}s)"
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    return 0
}

# Usage
wait_for_condition 300 10 \
    "kubectl get pod my-pod -o jsonpath='{.status.phase}' | grep -q Running"
```

### Parallel Execution

```bash
run_parallel() {
    local pids=()
    local failures=()

    for item in "$@"; do
        process_item "$item" &
        pids+=($!)
    done

    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failures+=("$pid")
        fi
    done

    if [[ ${#failures[@]} -gt 0 ]]; then
        err "Failed jobs: ${#failures[@]}"
        return 1
    fi
}
```

### Kubernetes Resource Checks

```bash
resource_exists() {
    local kind="$1"
    local name="$2"
    local ns="${3:-}"

    local ns_flag=""
    [[ -n "$ns" ]] && ns_flag="-n $ns"

    # shellcheck disable=SC2086
    kubectl get "$kind" "$name" $ns_flag &>/dev/null
}

# Usage
if resource_exists deployment my-app my-namespace; then
    log "Deployment exists"
fi
```

### Retry Pattern

```bash
retry() {
    local max_attempts=${1:-3}
    local delay=${2:-5}
    shift 2
    local cmd=("$@")

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if "${cmd[@]}"; then
            return 0
        fi
        warn "Attempt $attempt/$max_attempts failed, retrying in ${delay}s..."
        sleep "$delay"
        attempt=$((attempt + 1))
    done

    err "All $max_attempts attempts failed"
    return 1
}

# Usage
retry 3 5 kubectl apply -f manifest.yaml
```

---

## Testing

### Manual Testing

```bash
# Test with shellcheck
shellcheck ./script.sh

# Test with bash
bash ./script.sh --help

# Test with debug output
bash -x ./script.sh

# Test with verbose mode
bash -v ./script.sh
```

### BATS Framework

For complex scripts, use [BATS](https://github.com/bats-core/bats-core):

```bash
# test/test_script.bats
#!/usr/bin/env bats

setup() {
    load 'test_helper/bats-support/load'
    load 'test_helper/bats-assert/load'
    SCRIPT="$BATS_TEST_DIRNAME/../script.sh"
}

@test "script requires argument" {
    run bash "$SCRIPT"
    assert_failure 1
    assert_output --partial "Usage:"
}

@test "script validates namespace format" {
    run bash "$SCRIPT" --namespace "INVALID_NS"
    assert_failure
    assert_output --partial "Invalid namespace"
}

@test "script succeeds with valid input" {
    run bash "$SCRIPT" valid-namespace
    assert_success
}
```

---

## Documentation Standards

### Header Comments

Every script MUST have a header block describing purpose, usage, and exit codes:

```bash
#!/usr/bin/env bash
# ===================================================================
# Script: deploy.sh
# Purpose: Deploy application to target Kubernetes cluster
# Usage: ./deploy.sh [options] <namespace>
#
# Options:
#   -h, --help      Show this help message
#   -n, --namespace Target namespace (default: default)
#   --dry-run       Preview changes without applying
#
# Environment Variables:
#   NAMESPACE - Target namespace (default: default)
#   DRY_RUN   - If "true", don't make changes
#
# Exit Codes:
#   0 - Success
#   1 - Argument error
#   2 - Missing dependency
# ===================================================================
```

### Inline Help (--help / -h)

Every user-facing script MUST support `--help` and `-h` flags:

```bash
usage() {
    cat <<EOF
Usage: ${SCRIPT_NAME} [options] <required-arg>

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    --dry-run       Preview mode

Examples:
    ${SCRIPT_NAME} my-namespace
    ${SCRIPT_NAME} --dry-run my-namespace
EOF
}
```

**Requirements:**
- Print to stdout (not stderr) so output is pipeable
- Exit 0 on `--help`, exit 1 on missing/invalid args
- Include at least one usage example

### Function Documentation

Document non-trivial functions with a comment above the declaration:

```bash
# Wait for a Kubernetes resource to reach the desired state.
# Arguments:
#   $1 - Resource kind (e.g., deployment, pod)
#   $2 - Resource name
#   $3 - Desired condition (e.g., Available, Ready)
#   $4 - Timeout in seconds (default: 300)
# Returns: 0 on success, 1 on timeout
wait_for_resource() {
    local kind="$1" name="$2" condition="$3" timeout="${4:-300}"
    # ...
}
```

### ALWAYS / NEVER Rules

| Rule | Rationale |
|------|-----------|
| **ALWAYS** include a header block with Purpose, Usage, Exit Codes | First thing a reader sees — orients them |
| **ALWAYS** support `--help` / `-h` in user-facing scripts | Discoverability — no need to read source |
| **ALWAYS** document functions with 3+ parameters | Prevents misuse of positional args |
| **ALWAYS** document non-obvious exit codes (beyond 0/1) | Callers need to handle specific failures |
| **NEVER** omit the shebang line (`#!/usr/bin/env bash`) | Portability — don't assume `/bin/bash` |
| **NEVER** put usage info only in comments (not in `--help`) | Users shouldn't need to read source |

---

## Code Quality Metrics

> See `common-standards.md` for universal coverage targets and testing principles.

### Validation Commands

```bash
# Shellcheck all scripts
shellcheck scripts/*.sh
# Output: "X issues" → Count by severity

# Check set flags
grep -r "^set -" scripts/ | grep -c "eEuo pipefail"
# Compare to total script count

# Count unquoted variables (SC2086)
shellcheck scripts/*.sh -f json | jq '[.[] | select(.code == 2086)] | length'

# Check ERR trap presence
grep -r "trap.*ERR" scripts/ | wc -l

# Check exit code documentation
grep -r "# Exit Codes:" scripts/ | wc -l

# Security: Check for secrets in args
grep -rE "\-\-(password|token|secret)=" scripts/
# Should return nothing
```

---

## Anti-Patterns Avoided

> See `common-standards.md` for universal anti-patterns across all languages.

### No Parsing ls Output

```bash
# Bad
for f in $(ls); do
    echo "$f"
done

# Good
for f in *; do
    [[ -e "$f" ]] || continue
    echo "$f"
done

# Good - find with null separator
while IFS= read -r -d '' f; do
    echo "$f"
done < <(find . -type f -print0)
```

### No Useless Cat

```bash
# Bad
cat file.txt | grep pattern

# Good
grep pattern file.txt
```

### No Backticks

```bash
# Bad
result=`command`

# Good
result=$(command)

# Good - nested
result=$(echo $(date))
```

---

## Compliance Assessment

**Use letter grades + evidence, NOT numeric scores.**

### Assessment Categories

| Category | Evidence Required |
|----------|------------------|
| **Safety** | set flags count, SC2086 violations |
| **Code Quality** | shellcheck total violations, function count |
| **Security** | Secrets in CLI, input validation |
| **Error Handling** | ERR trap, exit code docs |
| **Logging** | Log function usage |

### Grading Scale

| Grade | Criteria |
|-------|----------|
| A+ | 0 shellcheck errors, set flags, ERR trap, 0 security issues |
| A | <5 shellcheck warnings, set flags, ERR trap, quoted vars |
| A- | <15 shellcheck warnings, set flags, mostly quoted |
| B+ | <30 shellcheck warnings, set flags present |
| B | <50 shellcheck warnings, some flags |
| C | Significant safety issues |
| D | Not production-ready |
| F | Critical issues |

### Example Assessment

```markdown
## Shell Script Standards Compliance

**Target:** scripts/
**Date:** 2026-01-21

| Category | Grade | Evidence |
|----------|-------|----------|
| Safety | A+ | 12/12 have set -eEuo pipefail, 0 SC2086 |
| Code Quality | A- | 8 shellcheck warnings (SC2312), 15 functions |
| Security | A | 0 secrets in CLI, 8/8 inputs validated |
| Error Handling | A | 12/12 ERR trap, 11/12 exit codes |
| **OVERALL** | **A** | **5 MEDIUM findings** |
```

---

## Vibe Integration

### Prescan Patterns

| Pattern | Severity | Detection |
|---------|----------|-----------|
| P05: Missing set flags | HIGH | No `set -eEuo pipefail` |
| P06: Unquoted variables | MEDIUM | SC2086 violations |
| P09: Secrets in CLI | CRITICAL | `--password=` patterns |

### JIT Loading

**Tier 1 (Fast):** Load `~/.agents/skills/standards/references/shell.md` (5KB)
**Tier 2 (Deep):** Load this document (18KB) for comprehensive audit

---

## Additional Resources

- [Bash Manual](https://www.gnu.org/software/bash/manual/)
- [ShellCheck Wiki](https://www.shellcheck.net/wiki/)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [BATS Testing Framework](https://github.com/bats-core/bats-core)

---

**Related:** Quick reference in Tier 1 `shell.md`
