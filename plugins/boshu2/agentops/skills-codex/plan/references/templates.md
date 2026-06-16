# Formula Templates Reference

Detailed templates for formula files and plan summaries.

---

## Formula File Template (.formula.toml)

**Location:** `.agents/formulas/{topic-slug}.formula.toml`

### Structure Overview

| Section | Purpose |
|---------|---------|
| Top-level fields | Formula metadata (`formula`, `description`, `version`, `type`) |
| `[vars]` | Simple key-value pairs for parameterization |
| `[[steps]]` | Array of implementation steps with dependencies |

### Full Template

```toml
# Formula: {Goal Name}
# Reusable pattern for creating {description}
# Created: YYYY-MM-DD

# REQUIRED: Top-level fields (NOT in a [formula] table!)
formula = "{topic-slug}"
description = "{Detailed description of what this formula produces}"
version = 2
type = "workflow"  # MUST be: workflow | expansion | aspect

# OPTIONAL: Variables for parameterization
# Use {{var_name}} syntax in step descriptions
[vars]
service_name = "default-service"
base_path = "services/"

# Steps define the work items - each becomes a child issue when poured
# Order doesn't matter - dependencies define execution order via `needs`

[[steps]]
id = "core"
title = "Add {{service_name}} core implementation"
description = """
Implement the core {{service_name}} functionality:
- Add main module at {{base_path}}{{service_name}}/core.py
- Include error handling and logging
- Follow existing patterns in the codebase

Files affected:
- {{base_path}}{{service_name}}/core.py
- {{base_path}}{{service_name}}/__init__.py

Acceptance criteria:
- Module is importable
- Passes unit tests
- Handles edge cases gracefully
"""
needs = []  # Wave 1 - no dependencies

[[steps]]
id = "config"
title = "Add {{service_name}} configuration"
description = """
Add configuration for {{service_name}}:
- Update charts/ai-platform/values.yaml with new config section
- Add environment variable mappings
- Document configuration options in values.yaml comments

Files affected:
- charts/ai-platform/values.yaml
- charts/ai-platform/templates/configmap.yaml

Acceptance criteria:
- Config values documented
- Defaults are sensible
- Works in dev and prod environments
"""
needs = []  # Wave 1 - can run parallel with core

[[steps]]
id = "tests"
title = "{{service_name}} integration tests"
description = """
Add comprehensive tests for {{service_name}}:
- Unit tests for core functionality
- Integration tests for API endpoints
- Ensure >80% coverage

Files affected:
- tests/unit/test_{{service_name}}.py
- tests/integration/test_{{service_name}}_e2e.py

Acceptance criteria:
- Happy path covered
- Error cases handled
- CI passes
"""
needs = ["core"]  # Wave 2 - depends on core implementation

[[steps]]
id = "docs"
title = "{{service_name}} documentation"
description = """
Document {{service_name}}:
- API reference in docs/api/
- Update README with usage examples
- Add architecture decision record if needed

Files affected:
- docs/api/{{service_name}}.md
- README.md

Acceptance criteria:
- Usage examples work
- API fully documented
"""
needs = ["core", "config"]  # Wave 2 - depends on both core and config
```

### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `formula` | Yes | string | Unique identifier (slug) at TOP LEVEL |
| `description` | Yes | string | What the formula creates |
| `version` | Yes | integer | Use `2` |
| `type` | Yes | string | `workflow`, `expansion`, or `aspect` |
| `[vars]` | No | table | Simple `key = "value"` pairs |
| `[[steps]]` | Yes | array | Step definitions |
| `steps.id` | Yes | string | Unique step identifier |
| `steps.title` | Yes | string | Short step title (can use {{vars}}) |
| `steps.description` | Yes | string | Detailed implementation guidance |
| `steps.needs` | Yes | array | Step IDs this depends on (empty = Wave 1) |

### WRONG Format (Do NOT Use)

```toml
# WRONG - Do not use this format!
[formula]                              # WRONG: formula is a top-level string, not a table
name = "topic-slug"                    # WRONG: use `formula = "..."` at top level
version = "1.0.0"                      # WRONG: use integer `version = 2`

[variables]                            # WRONG: use [vars] with simple values
component = { type = "string" }        # WRONG: complex type definitions not supported

[[tasks]]                              # WRONG: use [[steps]]
title = "..."
type = "feature"                       # WRONG: no type field in steps
priority = "P1"                        # WRONG: no priority field in steps
wave = 1                               # WRONG: no wave field (computed from needs)
depends_on = ["..."]                   # WRONG: use needs = [...]
files = ["..."]                        # WRONG: no files field

[waves]                                # WRONG: waves are computed, not declared
1 = ["step1", "step2"]
```

### Wave Computation

Waves are computed from the `needs` field:

| Wave | Rule | Example |
|------|------|---------|
| Wave 1 | `needs = []` | core, config |
| Wave 2 | All `needs` are Wave 1 | tests (needs core), docs (needs core, config) |
| Wave N | All `needs` are Wave N-1 or earlier | - |

### Variable Substitution

Variables defined in `[vars]` can be used in step descriptions with `{{var}}` syntax:

```toml
[vars]
service_name = "rate-limiter"
requests_per_minute = "100"

[[steps]]
id = "impl"
title = "Implement {{service_name}}"
description = "Configure {{requests_per_minute}} requests per minute"
needs = []
```

### Using bd cook

> **Note:** `bd cook` is a planned feature, not yet implemented.

```bash
# Preview what would be created
bd cook .agents/formulas/{topic-slug}.formula.toml --dry-run

# Cook and save proto to database
bd cook .agents/formulas/{topic-slug}.formula.toml --persist

# Cook with variable overrides
bd cook .agents/formulas/{topic-slug}.formula.toml --persist \
  --var service_name=auth-middleware

# Then pour to create actual issues
# FUTURE: bd mol not yet implemented. See skills/beads/references/MOLECULES.md for design spec.
bd mol pour {topic-slug}
```

---

## Companion Plan Document Template

**Location:** `.agents/formulas/{topic-slug}.md`

### Tag Vocabulary (REQUIRED)

Document type tag: `formula` (required first)

**Examples:**
- `[formula, agents, kagent]` - KAgent implementation formula
- `[formula, data, neo4j]` - GraphRAG implementation formula
- `[formula, auth, security]` - OAuth2 implementation formula
- `[formula, ci-cd, tekton]` - Tekton pipeline formula

### Full Template

```markdown
---
date: YYYY-MM-DD
type: Formula
goal: "[Goal description]"
tags: [formula, domain-tag, optional-tech-tag]
formula: "{topic-slug}.formula.toml"
epic: "[beads epic ID, if instantiated]"
status: TEMPLATE | INSTANTIATED
---

# Formula: [Goal]

## Overview
[2-3 sentence summary of what this formula creates and when to use it]

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| service_name | default-service | Name of the service |
| base_path | services/ | Base path for source files |

## Steps (Dependency Order)

| ID | Title | Needs | Wave |
|----|-------|-------|------|
| core | Add core implementation | - | 1 |
| config | Add configuration | - | 1 |
| tests | Integration tests | core | 2 |
| docs | Documentation | core, config | 2 |

## Dependency Graph

```
Wave 1 (No Dependencies):
  core: Add core implementation
  config: Add configuration
       |
       v unblocks
Wave 2 (Depends on Wave 1):
  tests: Integration tests (needs: core)
  docs: Documentation (needs: core, config)
```

## Wave Execution Order

| Wave | Steps | Can Parallel | Notes |
|------|-------|--------------|-------|
| 1 | core, config | Yes | No dependencies, different files |
| 2 | tests, docs | Yes | Both depend on Wave 1, different files |

**Wave Computation Rules:**
- **Wave 1:** All steps with `needs = []`
- **Wave N:** Steps where all `needs` are in Wave N-1 or earlier
- **Can Parallel:** "Yes" if steps in same wave affect different files

## Files to Modify

| File | Change |
|------|--------|
| `{{base_path}}{{service_name}}/core.py` | Add core module with main logic |
| `{{base_path}}{{service_name}}/config.py` | **NEW** — configuration handling |
| `tests/unit/test_{{service_name}}.py` | **NEW** — unit tests |

## Implementation

### 1. Core Module

In `{{base_path}}{{service_name}}/core.py`:

- **Create `ServiceHandler` class** with `__init__(self, config: ServiceConfig)` and `process(self, request: Request) -> Response`
- **Key functions to reuse:**
  - `validate_request()` at `{{base_path}}common/validation.py:45`
  - `format_response()` at `{{base_path}}common/response.py:23`

### 2. Configuration

In `{{base_path}}{{service_name}}/config.py`:

- **Add `ServiceConfig` dataclass:**
  ```python
  @dataclass
  class ServiceConfig:
      service_name: str = "{{service_name}}"
      base_path: str = "{{base_path}}"
  ```

## Tests

**`tests/unit/test_{{service_name}}.py`** — **NEW**:
- `test_service_handler_happy_path`: Valid request returns expected response
- `test_service_handler_invalid_input`: Bad request raises ValueError
- `test_config_defaults`: ServiceConfig has correct defaults

## Verification

1. **Unit tests**: `pytest tests/unit/test_{{service_name}}.py -v`
2. **Build check**: `python -c "from {{base_path.replace('/', '.')}}{{service_name}} import core"`
3. **Manual test**:
   ```bash
   python -c "
   from {{base_path.replace('/', '.')}}{{service_name}}.core import ServiceHandler
   handler = ServiceHandler()
   print(handler.process({'data': 'test'}))
   "
   ```

## Implementation Notes
[Key decisions, patterns to follow, risks identified]

## Usage

### Cook and Pour

> **Note:** `bd cook` is a planned feature, not yet implemented.

```bash
# Preview what would be created
bd cook .agents/formulas/{topic-slug}.formula.toml --dry-run

# Cook proto to database
bd cook .agents/formulas/{topic-slug}.formula.toml --persist

# Pour to create actual issues
# FUTURE: bd mol not yet implemented. See skills/beads/references/MOLECULES.md for design spec.
bd mol pour {topic-slug}

# With variable overrides
# FUTURE: bd mol not yet implemented. See skills/beads/references/MOLECULES.md for design spec.
bd mol pour {topic-slug} --var service_name=rate-limiter
```

## Next Steps
Run `$crank <epic-id>` for hands-free execution, or `$implement-wave <epic-id>` for supervised.
```

---

## Formula Summary Template (Crank Handoff)

Output this after cooking/pouring a formula. This is the **handoff to crank**.

```markdown
---

# Formula Instantiated: [Goal Description]

**Formula:** `.agents/formulas/{topic-slug}.formula.toml`
**Epic:** `<rig-prefix>-xxx`
**Plan:** `.agents/formulas/{topic-slug}.md`
**Steps:** N steps across M waves

---

## Wave Execution Order

| Wave | Steps | Can Parallel | Ready Now |
|------|-------|--------------|-----------|
| 1 | xxx.core, xxx.config | Yes | Ready |
| 2 | xxx.tests, xxx.docs | Yes | Blocked by Wave 1 |

## Steps Created

| ID | Step | Needs |
|----|------|-------|
| xxx.core | Add core implementation | - |
| xxx.config | Add configuration | - |
| xxx.tests | Integration tests | core |
| xxx.docs | Documentation | core, config |

## Dependency Graph

```
Wave 1 (needs = []):
  xxx.core: Add core implementation
  xxx.config: Add configuration
       |
       v unblocks
Wave 2 (depends on Wave 1):
  xxx.tests: Integration tests (needs: core)
  xxx.docs: Documentation (needs: core, config)
```

---

## Ready for Execution

### Pre-Flight Checklist

- [x] Formula cooked with `bd cook --persist` <!-- FUTURE: bd cook not yet implemented -->
- [x] Mol poured with `bd mol pour` <!-- FUTURE: bd mol not yet implemented. See skills/beads/references/MOLECULES.md for design spec. -->
- [x] Steps have proper dependencies via `needs`
- [ ] External requirements: [list any, e.g., "API key configured"]

### Execute

**Autonomous (overnight, parallel via polecats):**
```bash
$crank xxx              # Full auto until epic closed
```

**Supervised (sequential, same session):**
```bash
$implement-wave xxx     # One wave at a time
```

### Alternative: Manual Execution

```bash
# Implement one at a time
br ready
$implement xxx.core
```
```
