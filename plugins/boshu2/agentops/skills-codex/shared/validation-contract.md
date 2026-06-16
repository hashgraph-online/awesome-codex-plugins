# Validation Contract

> **The Trust Problem**: Agent completion claims cannot be trusted. Verify then trust.

## Overview

This document specifies how validation requirements are defined, executed, and enforced in the swarm/crank architecture.

```
BROKEN (old):
                        ^ TRUST (no verification)

CORRECT (new):
<task-notification> --> RUN VALIDATION --> IF PASS --> complete
                                       --> IF FAIL --> retry/escalate
                        ^ VERIFY then trust
```

---

## Completion-Claim Kernel

Apply this kernel whenever an artifact says a bead, task, epic, gate, or phase is
`DONE`, `closed`, `complete`, `green`, or ready to ship:

1. Treat status fields and agent summaries as claims until fresh evidence proves
   the contract is satisfied.
2. Rerun the narrowest checks that prove the acceptance criteria now, and keep
   command, exit code, and relevant output in the verdict or linked evidence.
3. Separate test existence, command success, and non-trivial assertions against
   production paths. Flag skipped tests, `assert true`, hardcoded success paths,
   disabled code, and mocks where the spec required real integration.
4. Map each claimed acceptance criterion to file:line evidence, named tests, raw
   logs, or explicit no-file evidence.
5. Check parent/child reconciliation, dependency graph health, orphaned
   acceptance criteria, and cross-bead contract drift.
6. Label deterministic suspicion as `flagged-for-review` until rerun evidence
   proves a true failure.

The evidence minimum for a completion claim is: claimed scope, acceptance
criterion, proof artifact, rerun command when applicable, and parent/dependency
reconciliation outcome.

---

## Specifying Validation Requirements


Validation requirements are specified with `metadata.issue_type` plus the `metadata.validation` field when creating tasks:

```
  subject="Implement feature X",
  description="...",
  metadata={
    "issue_type": "feature",
    "validation": {
      "files_exist": ["path/to/file1", "path/to/file2"],
      "command": "npm test",
      "content_check": {"file": "path/to/file", "pattern": "expected_pattern"},
      "tests": "pytest tests/test_feature.py",
      "lint": "eslint src/"
    }
  }
)
```

### Required Validation by Issue Type

| Issue Type | Requirement |
|------------|-------------|
| `feature`, `bug`, `task` | `metadata.validation.tests` is required, plus at least one structural check: `files_exist` and/or `content_check` |
| `docs`, `chore`, `ci` | Explicit exemption from required `tests`; use structural and/or command/lint checks as applicable |

If a `feature`/`bug`/`task` task packet is missing required test or structural checks, do not dispatch the task.
If a task packet is missing `metadata.issue_type`, do not dispatch it once active constraints are in play; task validation cannot apply issue-scoped prevention safely without it.
Treat this as part of the closed flywheel, not extra metadata ceremony: a finding only shifts left into deterministic validation when applicability can be resolved without guessing.

### Active Compiled Constraint Runtime

Active compiled constraints execute through `hooks/task-validation-gate.sh`. The hook reads `.agents/constraints/index.json` as the only executable surface; `.agents/constraints/<id>.sh` files are human-reviewable companion artifacts and must not be executed directly.

Plans that add or depend on active constraints must name these detector kinds explicitly:

- `content_pattern` - literal must-contain or must-not-contain checks over normalized target files.
- `paired_files` - companion-file checks derived from normalized changed files.
- `restricted_command` - bare-name commands that pass `validate_restricted_cmd` before execution.

Applicability is resolved from concrete task and repository inputs:

- `metadata.issue_type`, matched against `applies_to.issue_types`.
- `metadata.files`.
- `metadata.validation.files_exist`.
- `metadata.validation.content_check[].file`.
- staged, unstaged, and untracked git changed files.
- `applies_to.path_globs` and `applies_to.languages`, applied to the normalized target-file set.

If any active constraint declares issue-type applicability, the task payload must include `metadata.issue_type`; do not infer it from prose.

### Validation Types

| Type | Schema | Description |
|------|--------|-------------|
| `files_exist` | `string[]` | List of file paths that must exist after task completion |
| `command` | `string` | Shell command that must exit with code 0 |
| `content_check` | `{file: string, pattern: string}` | File must contain pattern (regex supported) |
| `tests` | `string` | Test command that must pass |
| `lint` | `string` | Lint command that must pass |
| `custom` | `{name: string, command: string}` | Named custom check |
| `cross_cutting` | `{name, type, ...}[]` | Epic-level constraints from "Always" boundaries, applied to every task |

### Multiple Checks

All specified checks must pass. Order of execution:

1. `files_exist` - fastest, fail-fast
2. `content_check` - fast pattern matching
3. `lint` - catch style issues before tests
4. `tests` - comprehensive verification
5. `command` - custom commands last
6. `custom` - any additional custom checks
7. `cross_cutting` - epic-level constraints last

---

## Validation Check Details

### files_exist

Verifies that specified files exist after task completion.

**Schema:**
```json
{
  "files_exist": ["src/auth.py", "tests/test_auth.py"]
}
```

**Execution:**
```bash
for file in files_exist:
    if not os.path.exists(file):
        FAIL("File not found: " + file)
PASS
```

**Use when:** Task creates new files.

### command

Runs arbitrary shell command, checks exit code.

**Schema:**
```json
{
  "command": "make build"
}
```

**Execution:**
```bash
result = subprocess.run(command, shell=True)
if result.returncode != 0:
    FAIL("Command failed with exit code: " + result.returncode)
PASS
```

**Use when:** Need custom build/validate step.

### content_check

Verifies file contains expected content.

**Schema:**
```json
{
  "content_check": {
    "file": "src/config.py",
    "pattern": "API_VERSION = \"2.0\""
  }
}
```

**Multiple patterns:**
```json
{
  "content_check": [
    {"file": "src/auth.py", "pattern": "def authenticate"},
    {"file": "src/auth.py", "pattern": "def authorize"}
  ]
}
```

**Execution:**
```bash
content="$(cat "$file")"
if ! printf '%s' "$content" | grep -Eq "$pattern"; then
    echo "Pattern not found in $file: $pattern" >&2
    exit 1
fi
```

**Use when:** Task must implement specific functions/patterns.

### tests

Runs test suite, checks for passing tests.

**Schema:**
```json
{
  "tests": "pytest tests/test_feature.py -v"
}
```

**Execution:**
```bash
result = subprocess.run(tests, shell=True)
if result.returncode != 0:
    FAIL("Tests failed")
PASS
```

**Use when:** Task has associated tests.

### lint

Runs linter, checks for clean output.

**Schema:**
```json
{
  "lint": "ruff check src/"
}
```

**Execution:**
```bash
result = subprocess.run(lint, shell=True)
if result.returncode != 0:
    FAIL("Lint errors found")
PASS
```

**Use when:** Code quality must be maintained.

### custom

Named custom check for documentation.

**Schema:**
```json
{
  "custom": {
    "name": "Database migration",
    "command": "python manage.py migrate --check"
  }
}
```

**Use when:** Domain-specific validation needed.

### cross_cutting

Epic-level constraints applied to EVERY task. Derived from "Always" boundaries in the plan.

**Schema:**
```json
{
  "cross_cutting": [
    {"name": "auth-required", "type": "content_check", "file": "src/middleware.go", "pattern": "AuthMiddleware"},
    {"name": "tests-pass", "type": "tests", "tests": "go test ./..."},
    {"name": "builds-clean", "type": "command", "command": "go build ./..."}
  ]
}
```

Each entry is a **flat object** with:
- `name` (string): Human-readable label for the constraint
- `type` (string): One of `files_exist`, `content_check`, `command`, `tests`, `lint`
- Remaining fields: Same as the corresponding validation type above

**Execution:**
```bash
# Run AFTER all per-task checks pass
for check in cross_cutting:
    run_check(check.type, check)  # Same execution logic as per-task checks
    if FAIL:
        FAIL(f"Cross-cutting constraint '{check.name}' failed")
PASS
```

**Use when:** Plan defines "Always" boundaries that apply to every issue in the epic. $crank reads these from the epic description and injects into every worker task.

**Source:** Cross-cutting constraints flow from plan boundaries:
```
```

---

## Failure Handling

### Retry Strategy

| Failure Type | Retry Action | Max Retries |
|--------------|--------------|-------------|
| `files_exist` | Re-spawn agent with explicit file list | 2 |
| `command` | Re-spawn with command output as context | 3 |
| `content_check` | Re-spawn with exact pattern required | 2 |
| `tests` | Re-spawn with test failure details | 3 |
| `lint` | Re-spawn with lint errors | 2 |

### Retry Context

When retrying, include failure context in the agent's prompt:

```
RETRY task #<id>: Previous attempt failed validation.

## Original Task
<original description>

## Validation Failure
Type: <check_type>
Details: <failure_output>

## Required Fix
<specific guidance based on failure>

Complete the task and ensure validation passes."
)
```

### Escalation

After MAX_RETRIES failures:

1. Mark task as blocked:
   ```
   ```

2. Record failure history:
   ```

   ## ESCALATED - Validation Failures
   Attempt 1: <failure>
   Attempt 2: <failure>
   Attempt 3: <failure>

   Requires human review.")
   ```

3. Continue with other tasks (don't block entire swarm)

---

## Default Validation

When no explicit validation is specified (docs/chore/ci exemption path or legacy tasks), apply minimal checks:

```python
def default_validation(task_id, worker_artifacts):
    # Check agent didn't end with errors

    # Check worker reported artifacts exist
    # The team lead validates artifacts exist before committing.
    for artifact in worker_artifacts:
        if not os.path.exists(artifact):
            return FAIL(f"Reported artifact not found: {artifact}")

    # Check for modified files (workers write in main tree or isolated worktrees)
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True)
    if not result.stdout.strip():
        return WARN("No file changes detected — worker may not have written anything")

    return PASS
```

> **Note:** Workers MUST NOT commit. The team lead is the sole committer.
> Validation checks for file existence and content, not commit history.
> The lead commits all validated changes after the wave completes.
> See `skills/swarm/SKILL.md` "Git Commit Policy" for details.

---

## Integration with Crank

When crank invokes swarm, it can specify validation at the epic level:

```python
# Crank creates tasks from beads issues
for issue in ready_issues:
        subject=f"{issue.id}: {issue.title}",
        description=issue.description,
        metadata={
            "beads_id": issue.id,
            "validation": build_validation_from_issue(issue)
        }
    )
```

### Building Validation from Issue

```python
def build_validation_from_issue(issue):
    issue_type = (issue.type or "").lower()
    validation = {}
    files_mentioned = extract_file_paths(issue.description)
    patterns = extract_code_patterns(issue.description)

    if issue_type in {"feature", "bug", "task"}:
        test_cmd = detect_test_command(issue)
        if not test_cmd:
            raise ValueError("feature|bug|task require metadata.validation.tests")
        validation["tests"] = test_cmd

        if files_mentioned:
            validation["files_exist"] = files_mentioned
        if patterns:
            validation["content_check"] = patterns
        if "files_exist" not in validation and "content_check" not in validation:
            raise ValueError("feature|bug|task require files_exist or content_check")
        return validation

    if issue_type in {"docs", "chore", "ci"}:
        # Explicit test exemption path for non-implementation work.
        if files_mentioned:
            validation["files_exist"] = files_mentioned
        if patterns:
            validation["content_check"] = patterns
        return validation

    # Unknown type: best-effort inference with structural checks only.
    if files_mentioned:
        validation["files_exist"] = files_mentioned
    if patterns:
        validation["content_check"] = patterns
    return validation
```

---

## Examples

### Example 1: New Feature with Tests

```
  subject="Add user authentication",
  description="Implement JWT-based authentication...",
  metadata={
    "validation": {
      "files_exist": [
        "src/auth/jwt.py",
        "src/auth/__init__.py",
        "tests/test_auth.py"
      ],
      "content_check": [
        {"file": "src/auth/jwt.py", "pattern": "def create_token"},
        {"file": "src/auth/jwt.py", "pattern": "def verify_token"}
      ],
      "tests": "pytest tests/test_auth.py -v",
      "lint": "ruff check src/auth/"
    }
  }
)
```

### Example 2: Bug Fix

```
  subject="Fix null pointer in user lookup",
  description="Handle case where user not found...",
  metadata={
    "validation": {
      "content_check": {
        "file": "src/users/lookup.py",
        "pattern": "if user is None"
      },
      "tests": "pytest tests/test_users.py::test_user_not_found -v"
    }
  }
)
```

### Example 3: Documentation Update

```
  subject="Update API docs for v2",
  description="Update README with new endpoints...",
  metadata={
    "validation": {
      "files_exist": ["docs/api/v2.md"],
      "content_check": {
        "file": "docs/api/v2.md",
        "pattern": "## Authentication"
      }
    }
  }
)
```

### Example 4: Infrastructure Change

```
  subject="Add Redis caching layer",
  description="Configure Redis for session caching...",
  metadata={
    "validation": {
      "files_exist": ["docker-compose.yml", "src/cache/redis.py"],
      "command": "docker-compose config --quiet",
      "content_check": {
        "file": "docker-compose.yml",
        "pattern": "redis:"
      }
    }
  }
)
```

---

## See Also

- `skills/swarm/SKILL.md` - Main swarm skill with validation integration
- `skills/crank/SKILL.md` - Crank orchestration with validation loop
- `skills/crank/failure-taxonomy.md` - Comprehensive failure handling
- `skills/validate/SKILL.md` - Comprehensive validation skill
