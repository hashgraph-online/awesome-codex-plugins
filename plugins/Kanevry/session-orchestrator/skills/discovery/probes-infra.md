> See probes-intro.md for confidence scoring reference.

## Category: `infra`

### Probe: ci-pipeline-health

**Activation:** CI config exists (`.gitlab-ci.yml`, `.github/workflows/`, `Jenkinsfile`, etc.).

**Detection Method:**

```bash
# GitLab: query recent pipeline status
glab pipeline list -R <OWNER>/<REPO> --per-page 10

# GitHub: query recent workflow runs
gh run list -R <OWNER>/<REPO> --limit 10

# Parse output for:
# - Repeated failures (same pipeline failing 3+ times in a row)
# - Long-running failures (pipeline failed >24h ago with no subsequent success)
# - Currently failing pipelines
```

**Evidence Format:**
```
Pipeline: <pipeline_id or run_id>
Status: failed | success
Duration: <time>
Failed Since: <timestamp>
Consecutive Failures: <count>
```

**Default Severity:** High. Critical if failed >24h with no fix.

---

### Probe: env-config-drift

**Activation:** `.env.example` exists.

**Detection Method:**

```bash
# Extract keys from .env.example
grep -E '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' .env.example | sed 's/=.*//' | sort > /tmp/env_example_keys

# Extract keys from .env (if exists)
grep -E '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' .env 2>/dev/null | sed 's/=.*//' | sort > /tmp/env_keys

# Extract keys from .env.local (if exists)
grep -E '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' .env.local 2>/dev/null | sed 's/=.*//' | sort > /tmp/env_local_keys

# Keys in .env.example but NOT in .env — missing config
comm -23 /tmp/env_example_keys /tmp/env_keys

# Keys in .env but NOT in .env.example — undocumented config
comm -13 /tmp/env_example_keys /tmp/env_keys
```

**Evidence Format:**
```
Key: <ENV_VAR_NAME>
Status: missing-from-env | undocumented | missing-from-env-local
Source: .env.example
```

**Default Severity:** Medium. High if key name contains SECRET, KEY, TOKEN, PASSWORD.

---

### Probe: outdated-dependencies

**Activation:** Package manager detected (`package.json`, `requirements.txt`, `Pipfile`, `Cargo.toml`, `go.mod`).

**Detection Method:**

```bash
# Node.js
npm outdated --json 2>/dev/null
npm audit --json 2>/dev/null

# Python
pip list --outdated --format=json 2>/dev/null
pip-audit --format json 2>/dev/null

# Go
go list -u -m all 2>/dev/null

# Rust
cargo outdated --format json 2>/dev/null
cargo audit --json 2>/dev/null
```

Parse JSON output. Flag:
- Major version bumps (current major != latest major)
- Known CVEs from audit output

**Evidence Format:**
```
Package: <name>
Current: <version>
Latest: <version>
Bump Type: major | minor | patch
CVE: <CVE-ID or NONE>
CVE Severity: <critical|high|medium|low|none>
```

**Default Severity:** Low (outdated minor/patch), Medium (outdated major), Critical (known CVE).

---

### Probe: deployment-health

**Activation:** `health-endpoints` configured in Session Config.

**Detection Method:**

```bash
# For each endpoint in health-endpoints:
curl -s -o /dev/null -w "%{http_code} %{time_total}" <endpoint>

# Flag:
# - Non-200 status codes
# - Response time > 2s
# - Connection timeouts
```

**Evidence Format:**
```
Endpoint: <url>
Status Code: <code>
Response Time: <seconds>s
Healthy: true | false
```

**Default Severity:** High.

---
