# Python Standards (Tier 1)

## Required
- `ruff check` passes (or `flake8`)
- `ruff format` (or `black`) for formatting
- Type hints on public functions
- Docstrings on public classes/functions

## Error Handling
- Never bare `except:` - always specify exception type
- Use `raise ... from e` to preserve stack traces
- Log before raising in library code

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| `except Exception:` | Too broad | Catch specific exceptions |
| `# type: ignore` | Hiding problems | Fix the type error |
| `eval()` / `exec()` | Security risk | Use safer alternatives |
| Mutable default args | Shared state bugs | Use `None` + conditional |

## Security
- Never use `eval()`, `exec()`, or `__import__()` with untrusted input
- Use `secrets` module for tokens, not `random`
- Validate and sanitize all external input (user data, file paths, URLs)
- Use parameterized queries for SQL — never string formatting

## Dataclass & Model Contract Completeness

When adding fields to a dataclass, Pydantic model, or TypedDict, every code path that creates an instance **must** populate them.

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| New field with `default=None`, some constructors never set it | Consumers see `None` for some paths, real value for others | Grep all `ClassName(` calls; verify each sets the new field |
| Synthesized instances (e.g., summary dicts, fallback objects) skip fields | Downstream code assumes all instances have the same shape | Store provenance metadata alongside state; populate synthesized instances from it |
| Index fields after sort | `event_index` points to sorted position, not caller's original position | Zip with `enumerate()` before sorting; emit original index |
| `__init__` sets fields conditionally | Some branches leave fields unset | Use `field(default_factory=...)` or set in all branches |

**Checklist for adding fields:**
1. Grep `ClassName(` across the package — every constructor call must set the new field
2. Check factory functions (`from_dict`, `from_json`, `create_*`)
3. Check synthesized/summary instances created outside the main loop
4. Add a structural assertion test (see below)

## Wire Input Validation

When parsing external JSON/YAML into models with enum-like fields, **validate against known values** before trusting.

```python
# BAD: trust whatever the wire sends
if event.error_class:
    # use as-is — "bogus" passes through

# GOOD: validate against known values
VALID_ERROR_CLASSES = {"timeout", "rate_limit", "auth_failure", ...}
if event.error_class and event.error_class not in VALID_ERROR_CLASSES:
    event.error_class = classify_error(event)  # reclassify from content
```

For Pydantic models, use `Literal` types or `@field_validator` to reject invalid values at parse time:

```python
from typing import Literal

class StreamEvent(BaseModel):
    error_class: Literal["timeout", "rate_limit", "auth_failure", ""] = ""
```

Also normalize impossible states: if `is_error=False` but `error_class="timeout"`, use a `@model_validator` to clear it.

## Classification & Pattern Matching

When classifying inputs by string patterns (error types, log levels, status codes):

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| `"429" in msg` | Matches port numbers, line numbers | Use regex with context: `r'\b(status|http|error|code)\s*:?\s*429\b'` |
| Bare keyword match (`"sandbox" in msg`) | "sandbox startup failed" misclassifies as sandbox violation | Require compound match: keyword + policy phrase (`denied`, `violation`) |
| Meaningless default case | `return "unknown"` for both truly-unknown and simply-unrecognized | Make default semantic: `"execution_error"` for non-empty, `"unknown"` for empty |
| No false-positive test coverage | Tests only check happy paths | Generate 5+ realistic false-positive inputs per pattern |

## Testing

### Exact Assertion Rule

**Always assert the exact expected value, never just "not the wrong one."**

```python
# BAD: passes even if classification drifts to a different wrong class
assert classify(msg) != "rate_limit"

# GOOD: pins the exact expected behavior
assert classify(msg) == "execution_error"
```

This applies to all classifier/enum tests. `!= X` assertions silently pass when the result drifts to a third, equally wrong value.

### Structural Invariant Tests

For dataclasses/models with required fields, add a sweep test that asserts ALL output instances populate them:

```python
def test_all_violations_have_structured_fields(violations):
    """Every violation must populate team_name, timestamp, and event_index."""
    for v in violations:
        assert v.team_name, f"violation {v} missing team_name"
        assert v.timestamp is not None, f"violation {v} missing timestamp"
```

### Property-Based Tests (BF1)

Use Hypothesis to randomize inputs to data transformations:

```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.dictionaries(
    keys=st.from_regex(r'[A-Z_]+', fullmatch=True),
    values=st.text(min_size=0, max_size=200),
    min_size=1,
))
def test_parse_reader_never_crashes(env_vars):
    """Any valid config must parse without crashing."""
    stream = io.StringIO("\n".join(f"{k}={v}" for k, v in env_vars.items()))
    ctx = parse_reader(stream)
    assert isinstance(ctx, SiteContext)
```

Target: every parser, serializer, and data transformer. If it accepts external input, fuzz it.

### Backward Compatibility Tests (BF8)

Maintain a corpus of real inputs from prior versions as fixtures:

```python
from glob import glob

@pytest.mark.parametrize("fixture", sorted(glob("tests/fixtures/compat/*.env")))
def test_legacy_config_parses(fixture):
    """Every historical config format must still parse."""
    ctx = parse_config_env(fixture)
    assert ctx.site_name  # at least one required field populated
```

**Rule:** When changing input formats, add the OLD format as a fixture BEFORE making the change.

### Performance/Benchmark Tests (BF7)

Use `pytest-benchmark` for hot-path functions:

```python
def test_parse_config_performance(benchmark):
    """Parser must handle large configs without regression."""
    large_config = "\n".join(f"KEY_{i}=value_{i}" for i in range(1000))
    result = benchmark(parse_reader, io.StringIO(large_config))
    assert isinstance(result, SiteContext)
```

Install: `pip install pytest-benchmark`. Run: `pytest --benchmark-only`.

### Regression Tests (BF6)

Every bug fix gets a reproducing test named after the bug ID:

```python
def test_bug_ag_m0r_empty_value_crashes():
    """Regression: parse_reader crashed on config lines with empty values (ag-m0r)."""
    stream = io.StringIO("SITE_NAME=\nDB_HOST=prod-db")
    ctx = parse_reader(stream)
    assert ctx.site_name == ""
    assert ctx.db_host == "prod-db"
```

### Security Tests (BF9)

Test secrets redaction and input sanitization:

```python
def test_render_export_redacts_secrets():
    """render_export must never emit raw secret values."""
    ctx = SiteContext(site_name="test", db_password="s3cr3t!", api_key="ak-12345")
    output = render_export(ctx)
    assert "s3cr3t!" not in output, "raw password leaked"
    assert "ak-12345" not in output, "raw API key leaked"

def test_rejects_path_traversal():
    """Config paths must reject traversal attempts."""
    for payload in ["../../../etc/passwd", "..\\windows", "foo/../bar"]:
        with pytest.raises(ValueError):
            load_config(payload)
```

### Test Conventions

- **pytest** preferred; `conftest.py` for shared fixtures.
- **Mock external services, not internal code.**
- **ruff** linter: `ruff check` must pass.
- **mypy** for type checking.
- **Black** formatter with 100-character line length. Config in `pyproject.toml`.
- **Type hints** on all public functions.
- **Docstrings** on all public classes and functions.

Security and error-handling rules are not repeated here; see `## Security` and
`## Error Handling` above.
