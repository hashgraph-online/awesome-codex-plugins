# Python Standards Catalog - Vibe Canonical Reference

**Version:** 1.0.0
**Last Updated:** 2026-01-21
**Purpose:** Canonical Python standards for vibe skill validation

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Package Management](#package-management)
3. [Code Formatting](#code-formatting)
4. [Reducing Complexity](#reducing-complexity)
5. [Type Hints](#type-hints)
6. [Docstrings](#docstrings)
7. [Error Handling](#error-handling)
8. [Logging](#logging)
9. [Testing](#testing)
10. [CLI Script Template](#cli-script-template)
11. [Code Quality Metrics](#code-quality-metrics)
12. [Security Practices](#security-practices)
13. [Anti-Patterns Avoided](#anti-patterns-avoided)
14. [Compliance Assessment](#compliance-assessment)

---

## Project Structure

### Standard Layout

```text
project/
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Lock file (commit this!)
├── src/
│   └── mypackage/           # Source code
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── scripts/                 # CLI tools
│   └── my_script.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_core.py
│   └── e2e/                 # End-to-end tests
│       ├── conftest.py      # Testcontainers fixtures
│       └── test_integration.py
└── docs/                    # Documentation
```

**Key Principles:**
- Use `src/` layout for packages (prevents import issues)
- CLI scripts are standalone files in `scripts/`
- Tests mirror source structure
- Always commit `uv.lock` for reproducibility

---

## Package Management

### uv - Project Dependencies

Use `uv` for all project-level Python dependencies. It's 10-100x faster than pip and creates deterministic builds.

```bash
# Initialize a new project
uv init my-project
cd my-project

# Add dependencies
uv add requests pyyaml        # Runtime deps
uv add --dev pytest ruff      # Dev deps

# Install from existing pyproject.toml
uv sync                       # Creates/updates uv.lock

# Run a script with project deps
uv run python my_script.py
```

### pipx - Global CLI Tools

Use `pipx` for Python CLI tools you want available everywhere.

```bash
# Install CLI tools globally
pipx install ruff             # Linter/formatter
pipx install radon            # Complexity analysis
pipx install xenon            # Complexity enforcement
pipx install pre-commit       # Git hooks

# Upgrade all
pipx upgrade-all

# Run without installing
pipx run cowsay "hello"
```

### When to Use What

| Need | Tool | Command |
|------|------|---------|
| Install project deps | uv | `uv sync` |
| Add library to project | uv | `uv add requests` |
| Install CLI globally | pipx | `pipx install ruff` |
| Install system tool | brew | `brew install shellcheck` |
| Quick script run | uv | `uv run script.py` |

### What NOT to Do

```python
# DON'T use pip globally
pip install requests          # Pollutes system Python
sudo pip install anything     # Even worse

# DON'T mix package managers
pip install requests          # Now you have pip AND uv deps
uv add pyyaml                 # Conflicts likely

# DON'T commit venv/
git add .venv/                # Use .gitignore
```

---

## Code Formatting

### ruff Configuration

**Full recommended configuration:**

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
    "S",   # flake8-bandit (security)
    "A",   # flake8-builtins
    "PT",  # flake8-pytest-style
]
ignore = [
    "E501",  # line-too-long (handled by formatter)
    "S101",  # assert (OK in tests)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101"]  # Allow assert in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Usage

```bash
# Check linting
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/

# Check formatting only
ruff format --check src/
```

---

## Reducing Complexity

**Target:** Maximum cyclomatic complexity of 10 (Grade B) per function

### Why Complexity Matters

- CC = number of independent paths through code
- CC > 10 means exponentially more test cases for coverage
- High complexity correlates with defect density
- Humans (and LLMs) struggle with deeply nested logic

### Pattern 1: Dispatch Pattern (Handler Registry)

**When to use:** Functions with if/elif chains that dispatch based on mode or type.

```python
# Bad - if/elif chain (CC=18+)
def main():
    if args.patch:
        # 90 lines of patch logic
    elif args.read:
        # 20 lines of read logic
    else:
        # 100 lines of write logic

# Good - Dispatch pattern (CC=6)
def _handle_patch_mode(args: Args, client: Client) -> None:
    """Handle --patch mode."""
    # Focused patch logic

def _handle_read_mode(args: Args, client: Client) -> None:
    """Handle --read mode."""
    # Focused read logic

def main() -> int:
    args = parse_args()
    client = build_client()

    handlers = {
        "patch": _handle_patch_mode,
        "read": _handle_read_mode,
        "write": _handle_write_mode,
    }

    handler = handlers.get(args.mode, _handle_write_mode)
    handler(args, client)
    return 0
```

### Pattern 2: Early Returns (Guard Clauses)

```python
# Bad - Deep nesting (CC=8)
def validate_document(doc: Document) -> bool:
    if doc:
        if doc.content:
            if len(doc.content) > 0:
                if doc.tenant:
                    return True
    return False

# Good - Guard clauses (CC=4)
def validate_document(doc: Document | None) -> bool:
    if not doc:
        return False
    if not doc.content:
        return False
    if len(doc.content) == 0:
        return False
    if not doc.tenant:
        return False
    return True
```

### Pattern 3: Lookup Tables

```python
# Bad - Each 'or' adds +1 CC
def normalize_field(key: str, value: str) -> str:
    if key == "tls.crt" or key == "tls.key" or key == "ca":
        return normalize_cert_field(value)
    elif key == "config.json":
        return normalize_pull_secret_json(value)
    else:
        return value

# Good - O(1) lookup
NORMALIZERS: dict[str, Callable[[str], str]] = {
    "tls.crt": normalize_cert_field,
    "tls.key": normalize_cert_field,
    "ca": normalize_cert_field,
    "config.json": normalize_pull_secret_json,
}

def normalize_field(key: str, value: str) -> str:
    normalizer = NORMALIZERS.get(key)
    return normalizer(value) if normalizer else value
```

### Pattern 4: Strategy Pattern (Class-Based)

```python
# Bad - Type checking with isinstance
def process(item: Item) -> Result:
    if isinstance(item, TypeA):
        # TypeA logic
    elif isinstance(item, TypeB):
        # TypeB logic
    elif isinstance(item, TypeC):
        # TypeC logic
    # ... many more types

# Good - Strategy pattern
from abc import ABC, abstractmethod

class ItemProcessor(ABC):
    @abstractmethod
    def process(self, item: Item) -> Result:
        pass

class TypeAProcessor(ItemProcessor):
    def process(self, item: Item) -> Result:
        # TypeA logic

class TypeBProcessor(ItemProcessor):
    def process(self, item: Item) -> Result:
        # TypeB logic

# Registry
PROCESSORS: dict[type, ItemProcessor] = {
    TypeA: TypeAProcessor(),
    TypeB: TypeBProcessor(),
}

def process(item: Item) -> Result:
    processor = PROCESSORS.get(type(item))
    if not processor:
        raise ValueError(f"No processor for {type(item)}")
    return processor.process(item)
```

### Helper Naming Convention

| Prefix | Meaning | Example |
|--------|---------|---------|
| `_handle_` | Mode/dispatch handler | `_handle_patch_mode()` |
| `_process_` | Processing helper | `_process_secret()` |
| `_validate_` | Validation helper | `_validate_cert()` |
| `_setup_` | Initialization helper | `_setup_mount_point()` |
| `_normalize_` | Data normalization | `_normalize_cert_field()` |
| `_build_` | Construction | `_build_audit_metadata()` |

### Measuring Complexity

```bash
# Check specific file
radon cc scripts/my_script.py -s -a

# Fail if any function exceeds Grade B (CC > 10)
xenon scripts/ --max-absolute B

# Show only Grade C or worse
radon cc scripts/ -s -n C
```

---

## Type Hints

### Modern Syntax (Python 3.12+)

```python
from __future__ import annotations
from typing import Any, Callable, TypeVar

# Basic types - use lowercase
items: list[str] = []
mapping: dict[str, int] = {}
coords: tuple[int, int, int] = (0, 0, 0)

# Union with pipe operator
value: str | int = "hello"
optional: str | None = None

# Function signatures
def process(
    items: list[str],
    config: dict[str, Any] | None = None,
    callback: Callable[[str], bool] | None = None,
) -> list[str]:
    """Process items with optional config."""
    ...

# Generics
T = TypeVar("T")

def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

### Type Hint Anti-Patterns

| Anti-Pattern | Problem | Better |
|--------------|---------|--------|
| `Any` everywhere | Defeats type checking | Use generics or specific types |
| `# type: ignore` without comment | Hides real issues | Add explanation |
| Old syntax `List[str]` | Deprecated | Use `list[str]` |
| Missing return type | Incomplete signature | Always add return type |

---

## Docstrings

### Google Style (Required)

```python
def verify_secret_after_write(
    client: hvac.Client,
    mount_point: str,
    name: str,
    expected_payload: dict[str, Any],
) -> bool:
    """Verify secret was written correctly.

    Args:
        client: Vault client connection.
        mount_point: KV v2 mount point path.
        name: Secret name/key.
        expected_payload: Expected secret data to verify against.

    Returns:
        True if verification passed, False if any check failed.

    Raises:
        hvac.exceptions.InvalidPath: If secret path is invalid.
        ConnectionError: If Vault connection fails.

    Example:
        >>> client = hvac.Client(url="http://localhost:8200")
        >>> verify_secret_after_write(client, "secret", "mykey", {"foo": "bar"})
        True
    """
    pass
```

### When to Include Each Section

| Section | When to Include |
|---------|-----------------|
| **Args** | Always if function has parameters |
| **Returns** | Always if function returns non-None |
| **Raises** | If function can raise exceptions |
| **Example** | For complex or non-obvious usage |
| **Note** | For important caveats or warnings |

---

## Error Handling

### Good Patterns

```python
# Good - Specific exception, logged
try:
    cert_info = validate_certificate(payload["tls.crt"])
except subprocess.CalledProcessError as exc:
    logging.warning("Certificate validation failed: %s", exc)

# Good - Multiple specific types for format detection
try:
    decoded = base64.b64decode(data)
except (UnicodeDecodeError, base64.binascii.Error, ValueError) as exc:
    logging.debug("Not base64, assuming PEM format: %s", exc)
    decoded = data

# Good - Re-raise with context
try:
    result = subprocess.run(cmd, check=True, capture_output=True)
except subprocess.CalledProcessError as exc:
    raise RuntimeError(f"Command failed: {cmd}") from exc

# Good - Custom exception with context
class ConfigError(Exception):
    """Configuration validation error."""
    def __init__(self, key: str, message: str):
        self.key = key
        super().__init__(f"Config '{key}': {message}")
```

### Bad Patterns

```python
# Bad - Bare exception, swallowed
try:
    validate_something()
except Exception:
    pass  # Silent failure!

# Bad - Catching Exception without re-raising
try:
    process_data()
except Exception as e:
    logging.error("Error: %s", e)
    return None  # Hides the problem

# Bad - Too broad, catches KeyboardInterrupt
try:
    long_running_task()
except:  # noqa: E722
    pass
```

### Exception Hierarchy for Custom Errors

```python
class MyAppError(Exception):
    """Base exception for application errors."""

class ValidationError(MyAppError):
    """Input validation failed."""

class ConnectionError(MyAppError):
    """External service connection failed."""

class ConfigError(MyAppError):
    """Configuration error."""
```

---

## Logging

### Standard Setup

```python
import logging

# Basic setup for scripts
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)

# Module logger for libraries
log = logging.getLogger(__name__)
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed diagnostic (development only) |
| `INFO` | Key events, progress |
| `WARNING` | Recoverable issues |
| `ERROR` | Operation failed |
| `CRITICAL` | Application cannot continue |

### Good Patterns

```python
# Good - Use % formatting (lazy evaluation)
logging.info("Processing secret: %s", secret_name)
logging.warning("Retry %d of %d: %s", attempt, max_retries, error)

# Good - Include context
logging.info("Prepared %s: %s", secret_name, preview)
logging.warning("Security policy check failed for %s: %s", key, exc)

# Good - Structured for parsing
logging.info("event=secret_prepared name=%s preview=%s", secret_name, preview)
```

### Bad Patterns

```python
# Bad - f-string (evaluated even if level disabled)
logging.info(f"Processing {expensive_to_compute()}")

# Bad - No context
logging.info("Processing...")
logging.error(str(e))

# Bad - print() instead of logging
print("DEBUG: value is", value)
```

---

## Testing

### Pytest Structure

```text
tests/
├── conftest.py           # Shared fixtures
├── test_core.py          # Unit tests for core module
├── test_utils.py         # Unit tests for utils
└── e2e/                  # End-to-end tests
    ├── conftest.py       # Testcontainers fixtures
    └── test_integration.py
```

### Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "e2e: marks tests as end-to-end (require Docker)",
    "slow: marks tests as slow",
]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Testcontainers for E2E Tests

Use testcontainers for tests that need real infrastructure.

```python
# tests/e2e/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Spin up PostgreSQL for E2E tests."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres
    # Container automatically cleaned up

@pytest.fixture
def db_connection(postgres_container):
    """Get connection to test database."""
    import psycopg
    conn_str = postgres_container.get_connection_url()
    with psycopg.connect(conn_str) as conn:
        yield conn
```

### Test Patterns

```python
# Table-driven tests
import pytest

@pytest.mark.parametrize("input,expected", [
    ("valid@example.com", True),
    ("invalid", False),
    ("", False),
    ("@nodomain", False),
])
def test_validate_email(input: str, expected: bool):
    assert validate_email(input) == expected

# Fixtures for setup/teardown
@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: value")
    return config_file

def test_load_config(temp_config):
    config = load_config(temp_config)
    assert config["key"] == "value"

# Mock external services
from unittest.mock import patch, MagicMock

def test_api_call():
    with patch("mymodule.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"data": "test"})
        result = my_api_function()
        assert result == {"data": "test"}
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run only E2E tests
pytest -m e2e

# Run excluding slow tests
pytest -m "not slow"
```

---

## CLI Script Template

```python
#!/usr/bin/env python3
"""One-line description of what this script does.

Usage:
    python3 script_name.py --config config.yaml --apply

Exit Codes:
    0 - Success
    1 - Argument/configuration error
    2 - Runtime error
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)


def die(message: str) -> None:
    """Print error message and exit with code 1."""
    logging.error(message)
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        type=Path,
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default: dry-run)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.apply:
        logging.info("Dry-run mode (use --apply to make changes)")

    # Validate config exists
    if not args.config.exists():
        die(f"Config file not found: {args.config}")

    # Main logic here
    try:
        # ... implementation
        logging.info("Processing complete")
        return 0
    except Exception as exc:
        logging.error("Failed: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

---

## Code Quality Metrics

> See `common-standards.md` for universal coverage targets and testing principles.

### Complexity Thresholds

| Grade | CC Range | Action |
|-------|----------|--------|
| A | 1-5 | Ideal - simple, low risk |
| B | 6-10 | Acceptable - moderate complexity |
| C | 11-20 | Refactor when touching |
| D | 21-30 | Must refactor before merge |
| F | 31+ | Block merge |

### Validation Commands

```bash
# Code quality + style
ruff check src/ --statistics
# Output: "10 errors, 5 warnings" → Count these

# Complexity analysis
radon cc src/ -s -a
# Output includes per-function CC and average → Report both

# Enforce complexity limit
xenon src/ --max-absolute B
# Fails if any function exceeds CC=10

# Test coverage
pytest --cov=src --cov-report=term-missing
# Output: "87% line, 71% branch" → Report both

# Docstring coverage
interrogate src/
# Output: "85% (45/53 functions)" → Report fraction + %
```

---

## Security Practices

### eval/exec Avoidance

Never use `eval()` or `exec()` on user-controlled input:

```python
# DANGEROUS - Remote code execution
user_expr = request.args["expr"]
result = eval(user_expr)  # Attacker sends: __import__('os').system('rm -rf /')

# SAFE - Use ast.literal_eval for data literals
import ast
result = ast.literal_eval(user_input)  # Only parses strings, numbers, tuples, lists, dicts

# SAFE - Use a mapping for dynamic dispatch
OPERATIONS = {"add": operator.add, "mul": operator.mul}
func = OPERATIONS.get(user_input)
if func:
    result = func(a, b)
```

**Validation:** Prescan pattern P16 detects `eval(` and `exec(` calls

### Pickle Safety

Never unpickle untrusted data — `pickle.loads()` executes arbitrary code:

```python
# DANGEROUS - Arbitrary code execution on load
import pickle
data = pickle.loads(untrusted_bytes)  # Attacker crafts payload to run code

# SAFE - Use JSON for data interchange
import json
data = json.loads(untrusted_bytes)

# SAFE - Use msgpack for binary efficiency
import msgpack
data = msgpack.unpackb(untrusted_bytes, raw=False)
```

If pickle is unavoidable (e.g., ML model loading), load only from trusted, integrity-verified sources.

### YAML Deserialization

`yaml.load()` with the default loader executes arbitrary Python objects:

```python
# DANGEROUS - Arbitrary code execution
import yaml
data = yaml.load(untrusted_string)  # Can execute __reduce__, !!python/object, etc.

# SAFE - Use safe_load (only basic YAML types)
data = yaml.safe_load(untrusted_string)

# SAFE - Explicit SafeLoader
data = yaml.load(untrusted_string, Loader=yaml.SafeLoader)
```

**Rule:** Always use `yaml.safe_load()` or `yaml.safe_load_all()`. Never use `yaml.load()` without `Loader=yaml.SafeLoader`.

### SQL Injection Prevention

Always use parameterized queries:

```python
# DANGEROUS - SQL injection
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# SAFE - Parameterized query
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))

# SAFE - SQLAlchemy ORM
user = session.query(User).filter(User.name == user_input).first()

# SAFE - SQLAlchemy text with bind params
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE name = :name")
result = conn.execute(stmt, {"name": user_input})
```

### SSRF Prevention

Validate URLs before making outbound requests:

```python
# DANGEROUS - Server-Side Request Forgery
url = request.args["url"]
resp = requests.get(url)  # Attacker sends: http://169.254.169.254/metadata

# SAFE - URL allowlist validation
from urllib.parse import urlparse

ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.hostname not in ALLOWED_HOSTS:
        return False
    return True

if validate_url(url):
    resp = requests.get(url, timeout=10)
```

### Path Traversal Prevention

User-controlled path components can escape intended directories:

```python
# DANGEROUS - Path traversal
user_file = request.args["filename"]
path = os.path.join("/data/uploads", user_file)  # "../../../etc/passwd" escapes!
content = open(path).read()

# SAFE - Resolve and check prefix
from pathlib import Path

UPLOAD_DIR = Path("/data/uploads").resolve()

def safe_read(filename: str) -> str:
    target = (UPLOAD_DIR / filename).resolve()
    if not target.is_relative_to(UPLOAD_DIR):
        raise ValueError(f"Path traversal blocked: {filename!r}")
    return target.read_text()

# SAFE - Strip directory components entirely
from pathlib import PurePosixPath

def sanitize_filename(filename: str) -> str:
    """Extract only the final filename component."""
    return PurePosixPath(filename).name
```

**Key pitfalls:**
- `os.path.join("/base", "/etc/passwd")` returns `/etc/passwd` (absolute path overrides base)
- Symlinks can bypass prefix checks — use `.resolve()` before comparison
- Always use `pathlib.Path.is_relative_to()` (Python 3.9+) for containment checks
- Never construct file paths from user input without validation

### Input Validation

Validate all external input at system boundaries:

```python
# Pydantic (recommended for structured data)
from pydantic import BaseModel, Field, field_validator

class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    age: int = Field(ge=0, le=150)

    @field_validator("name")
    @classmethod
    def no_script_tags(cls, v: str) -> str:
        if "<script" in v.lower():
            raise ValueError("HTML not allowed in name")
        return v.strip()

# Manual validation for simple cases
def validate_port(port: str) -> int:
    try:
        p = int(port)
    except ValueError:
        raise ValueError(f"Invalid port: {port!r}")
    if not (1 <= p <= 65535):
        raise ValueError(f"Port out of range: {p}")
    return p
```

### Secrets Management

Never hardcode secrets in source code:

```python
# DANGEROUS - Hardcoded secrets
API_KEY = "REDACTED"  # Leaked in git history forever
db_url = "postgresql://user:REDACTED@prod-db:5432/app"

# SAFE - Environment variables
import os
API_KEY = os.environ["API_KEY"]  # Fails loudly if missing

# SAFE - With default for optional config
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# SAFE - Vault/secrets manager for production
from hvac import Client
vault = Client(url=os.environ["VAULT_ADDR"])
secret = vault.secrets.kv.v2.read_secret_version(path="myapp/creds")
```

**Validation:** Prescan pattern P17 detects common secret patterns (API keys, passwords in strings)

### Subprocess Safety

Avoid `shell=True` — it enables command injection:

```python
# DANGEROUS - Shell injection
filename = request.args["file"]
subprocess.run(f"cat {filename}", shell=True)  # Attacker sends: "; rm -rf /"

# SAFE - List arguments, no shell
subprocess.run(["cat", filename], check=True, capture_output=True)

# SAFE - For complex pipelines, use Python instead of shell
from pathlib import Path
content = Path(filename).read_text()

# If shell=True is truly needed, validate input strictly
import shlex
safe_arg = shlex.quote(user_input)
```

### ALWAYS / NEVER Rules

| Rule | Category | Detail |
|------|----------|--------|
| **ALWAYS** use parameterized queries | SQL | Never interpolate user input into SQL strings |
| **ALWAYS** validate URLs before fetch | SSRF | Check scheme, hostname against allowlist |
| **ALWAYS** resolve and check path prefix | Path Traversal | Use `pathlib.resolve()` + `is_relative_to()` |
| **ALWAYS** use `secrets` module for tokens | Crypto | `secrets.token_urlsafe()`, not `random` |
| **ALWAYS** set request timeouts | Network | `requests.get(url, timeout=10)` |
| **NEVER** use `eval()`/`exec()` on user input | Injection | Use `ast.literal_eval` or dispatch maps |
| **NEVER** unpickle untrusted data | Deserialization | Use JSON or msgpack instead |
| **NEVER** use `shell=True` with user input | Command injection | Use list args with `subprocess.run` |
| **NEVER** hardcode secrets | Secrets | Use env vars or vault |
| **NEVER** disable TLS verification | TLS | No `verify=False` in production |
| **NEVER** log secrets or tokens | Logging | Redact sensitive fields before logging |

---

## Anti-Patterns Avoided

> See `common-standards.md` for universal anti-patterns across all languages.

### No God Functions

```python
# Bad - Single function doing everything
def process_all(data):
    # 200+ lines of validation, transformation, saving, logging...
    pass

# Good - Separated concerns
def validate(data: Data) -> ValidationResult:
    ...

def transform(data: Data) -> TransformedData:
    ...

def save(data: TransformedData) -> None:
    ...
```

### No Bare Except

```python
# Bad
try:
    risky_operation()
except:
    pass

# Good
try:
    risky_operation()
except SpecificError as e:
    logging.warning("Operation failed: %s", e)
```

### No Global Mutable State

```python
# Bad
config = {}  # Module-level mutable

def load_config(path):
    global config
    config = load_yaml(path)

# Good
@dataclass
class Config:
    setting_a: str
    setting_b: int

def load_config(path: Path) -> Config:
    data = load_yaml(path)
    return Config(**data)
```

### No Magic Strings

```python
# Bad
if status == "pending":
    ...
elif status == "complete":
    ...

# Good
class Status(str, Enum):
    PENDING = "pending"
    COMPLETE = "complete"

if status == Status.PENDING:
    ...
```

---

## Compliance Assessment

**Use letter grades + evidence, NOT numeric scores.**

### Assessment Categories

| Category | Evidence Required |
|----------|------------------|
| **Code Quality** | ruff violations count, auto-fixable count |
| **Complexity** | radon cc output, functions >CC10 count |
| **Type Safety** | % public functions with hints, missing count |
| **Error Handling** | Bare except count, specific exception count |
| **Testing** | pytest coverage (line/branch %), test count |
| **Documentation** | Docstring coverage %, missing count |

### Grading Scale

| Grade | Criteria |
|-------|----------|
| A+ | 0 ruff violations, 0 functions >CC10, 95%+ hints, 90%+ coverage |
| A | <5 ruff violations, <3 functions >CC10, 85%+ hints, 80%+ coverage |
| A- | <15 ruff violations, <8 functions >CC10, 75%+ hints, 70%+ coverage |
| B+ | <30 ruff violations, <15 functions >CC10, 60%+ hints, 60%+ coverage |
| B | <50 ruff violations, <25 functions >CC10, 50%+ hints, 50%+ coverage |
| C | Significant issues, major refactoring needed |
| D | Not production-ready |
| F | Critical issues |

### Example Assessment

```markdown
## Python Standards Compliance

**Target:** src/
**Date:** 2026-01-21

| Category | Grade | Evidence |
|----------|-------|----------|
| Code Quality | A- | 8 ruff violations (6 fixable), 0 security |
| Complexity | B+ | 12 functions >CC10, avg CC=6.8 (radon) |
| Type Safety | A | 47/52 public functions typed (90%) |
| Error Handling | A- | 0 bare except, 2 broad catches |
| Testing | B | 73% line, 58% branch (pytest) |
| Documentation | A | 48/52 documented (92%, interrogate) |
| **OVERALL** | **A-** | **8 HIGH, 15 MEDIUM findings** |

### High Priority Findings

- **CMPLX-001** - `processor.py:89` CC=15 - Refactor dispatch
- **TYPE-001** - `utils.py` - 5 functions missing hints
```

---

## Vibe Integration

### Prescan Patterns

| Pattern | Severity | Detection |
|---------|----------|-----------|
| P04: Bare Except | HIGH | `except:` or `except Exception:` without re-raise |
| P08: print() Debug | MEDIUM | `print(` in non-CLI modules |
| P15: f-string Logging | LOW | `logging.*\(f"` pattern |

### JIT Loading

**Tier 1 (Fast):** Load `~/.agents/skills/standards/references/python.md` (5KB)
**Tier 2 (Deep):** Load this document (20KB) for comprehensive audit

---

## Additional Resources

- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [radon Complexity](https://radon.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [testcontainers-python](https://testcontainers-python.readthedocs.io/)

---

**Related:** `python-patterns.md` for quick reference examples (if needed)
