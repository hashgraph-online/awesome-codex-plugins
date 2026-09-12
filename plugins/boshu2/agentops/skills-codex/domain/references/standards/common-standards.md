# Common Standards Catalog - Cross-Language Patterns

**Version:** 1.0.0
**Last Updated:** 2026-03-03
**Purpose:** Universal coding standards shared across all languages. Language-specific files reference this document for philosophical and cross-cutting patterns, keeping language-specific implementation details in their own catalogs.

---

## Table of Contents

1. [Error Handling Philosophy](#error-handling-philosophy)
2. [Testing Best Practices](#testing-best-practices)
3. [Security Principles](#security-principles)
4. [Documentation Standards](#documentation-standards)
5. [Code Organization Principles](#code-organization-principles)
6. [Canonical Language Owners](#canonical-language-owners)

---

## Error Handling Philosophy

Errors are first-class citizens. Every language has different mechanisms (Result types, exceptions, error returns), but the underlying principles are universal.

### Core Rules

| Rule | ALWAYS | NEVER |
|------|--------|-------|
| Visibility | Log or propagate every error | Suppress errors silently |
| Specificity | Use specific error types/exceptions | Catch-all without re-raising |
| Context | Add context when propagating | Lose the original error chain |
| Recovery | Distinguish recoverable vs fatal | Treat all errors the same |
| Documentation | Document error behavior in public APIs | Assume callers know failure modes |
| Libraries | Log before raising in library boundaries | Swallow errors inside libraries |

### Error Chain Preservation

Every language provides a mechanism for preserving error chains. Use it.

| Language | Mechanism | Example |
|----------|-----------|---------|
| Go | `fmt.Errorf("context: %w", err)` | Preserves `errors.Is()` / `errors.As()` |
| Python | `raise NewError("context") from exc` | Preserves `__cause__` chain |
| Rust | `?` with `.context()` / `#[source]` | Preserves `Error::source()` chain |
| TypeScript | `new AppError("context", { cause: err })` | Preserves `Error.cause` chain |
| Shell | `err "context: $cmd failed"; return $exit_code` | Preserves exit code semantics |

### Intentional Error Ignores

When errors are intentionally ignored (e.g., best-effort cleanup), document the reason:

| Language | Pattern |
|----------|---------|
| Go | `_ = conn.Close() // nolint:errcheck - best effort cleanup` |
| Python | `except SpecificError: pass  # best effort cleanup` with comment |
| Rust | `let _ = conn.close(); // Intentional ignore: best effort cleanup` |
| TypeScript | `void promise.catch(() => {}); // fire-and-forget, logged elsewhere` |
| Shell | `rm -rf "$TMPDIR" 2>/dev/null \|\| true` |

### Error Aggregation

When multiple operations can fail independently (parallel execution, multi-step cleanup), use the language's error aggregation mechanism rather than discarding all but the first error.

| Language | Mechanism |
|----------|-----------|
| Go | `errors.Join(err1, err2)` (1.20+) |
| Python | `ExceptionGroup` (3.11+) |
| Rust | Custom `Vec<Error>` or `anyhow` context chain |
| TypeScript | `AggregateError` |

### Custom Error Hierarchies

Define a base error type per project/crate/package. Subtypes encode categories.

**Principles:**
- Base type enables catch-all at API boundaries
- Subtypes enable programmatic handling by callers
- Machine-readable codes (where applicable) enable telemetry
- Human-readable messages enable debugging

### Severity Classification

| Level | Definition | Action |
|-------|-----------|--------|
| Fatal | Process cannot continue | Log, clean up, exit non-zero |
| Recoverable | Operation failed, process continues | Log, retry or degrade gracefully |
| Warning | Non-ideal but not broken | Log at warning level, continue |
| Informational | Expected alternative path | Log at debug level |

### Anti-Patterns (Universal)

| Anti-Pattern | Why It's Bad | Instead |
|--------------|-------------|---------|
| Silent suppression (`catch {}`, `except: pass`, `_ =` without comment) | Hides bugs, makes debugging impossible | Log, propagate, or document the ignore |
| String-only errors | Not matchable, no programmatic handling | Use typed/structured errors |
| Catching too broadly | Masks unrelated failures | Catch the most specific type possible |
| Logging AND re-raising the same error | Duplicate log entries at every layer | Log at the boundary, propagate elsewhere |
| Panic/throw in library code for expected failures | Crashes callers unexpectedly | Return error types; reserve panic for invariant violations |

---

## Testing Best Practices

### Test Organization

| Layer | Scope | Speed | When to Run |
|-------|-------|-------|-------------|
| Unit | Single function/method | < 100ms | Every commit |
| Integration | Multiple components, real I/O | < 30s | Every PR |
| End-to-end | Full system with real deps | < 5min | Pre-release |
| Property-based | Invariant fuzzing | Varies | CI nightly or on critical paths |

### Table-Driven / Parameterized Tests

The table-driven pattern is universal. Define inputs and expected outputs in a data structure, then iterate.

| Language | Mechanism |
|----------|-----------|
| Go | `[]struct{ name, input, want }` + `t.Run()` |
| Python | `@pytest.mark.parametrize("input,expected", [...])` |
| Rust | `#[test]` with loop or `proptest!` macro |
| TypeScript | `test.each([...])` or `describe.each([...])` |
| Shell | BATS `@test` with parameterized fixtures |

**Benefits:**
- Easy to add new cases (one line per case)
- Clear test naming
- DRY -- assertion logic written once

### Fixtures and Mocking Philosophy

| Principle | ALWAYS | NEVER |
|-----------|--------|-------|
| External boundaries | Mock external services, APIs, databases | Let tests hit real external services in unit tests |
| Internal code | Test real internal implementations | Mock internal functions (couples tests to implementation) |
| Test isolation | Each test sets up its own state | Share mutable state between tests |
| Cleanup | Clean up resources (files, containers, connections) | Leave test artifacts behind |

### Test Double Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| Stub | Returns canned data | Simple happy/sad path |
| Mock | Verifies interactions were called | Behavior verification |
| Fake | Working lightweight implementation | Integration-like tests without real infra |
| Spy | Records calls for later assertion | Interaction counting/ordering |

### Coverage Targets

| Metric | Minimum | Target | Critical Paths |
|--------|---------|--------|----------------|
| Line coverage | 60% | 80% | 90%+ |
| Branch coverage | 50% | 70% | 85%+ |

**Coverage philosophy:**
- Coverage is a floor, not a ceiling -- low coverage signals under-testing, high coverage does not guarantee quality
- Prioritize critical paths (error handling, security, data integrity) over boilerplate
- Measure branch coverage, not just line coverage -- untested branches hide bugs

### Property-Based Testing

Test invariants that must hold for ALL inputs, not just hand-picked examples.

**When to use:**
- Serialization roundtrips (encode then decode = original)
- Mathematical properties (commutativity, associativity)
- Parser contracts (valid input always parses, invalid always fails)
- Boundary conditions (output never exceeds input, no negative values)

### Doc Tests / Example Tests

Code examples in documentation should be executable tests. Guarantees documentation accuracy.

| Language | Mechanism |
|----------|-----------|
| Go | `func Example*` in `_test.go` files |
| Python | Doctest in docstrings, or `>>> ` examples |
| Rust | Code blocks in `///` doc comments |
| TypeScript | JSDoc `@example` blocks (manual verification) |

---

## Security Principles

### No Hardcoded Secrets

| ALWAYS | NEVER |
|--------|-------|
| Load secrets from environment variables or secret stores | Hardcode API keys, tokens, passwords in source |
| Use `.env` files locally (gitignored) | Commit `.env` or credential files |
| Rotate secrets on exposure | Assume secrets are safe in private repos |
| Audit git history for leaked secrets | Rely on `.gitignore` alone for protection |

**Detection:** Prescan pattern P2 flags hardcoded secrets in all languages.

### Input Validation

Validate at system boundaries (user input, external APIs, file reads). Trust internal code within the same trust boundary.

| Rule | Description |
|------|-------------|
| Validate early | Check inputs at the entry point, not deep in business logic |
| Fail fast | Reject invalid input immediately with clear error messages |
| Allowlist over denylist | Define what IS valid, not what ISN'T |
| Type-safe parsing | Parse into typed structures, not raw strings |

### Injection Prevention

| Attack Vector | Prevention |
|---------------|-----------|
| SQL injection | Parameterized queries / prepared statements. NEVER string interpolation. |
| Command injection | Use array-based exec (no shell). Avoid `eval()`, `exec()`, `system()`. |
| Template injection | Use auto-escaping template engines. Escape user input in templates. |
| Path traversal | Resolve to absolute path, verify within allowed directory. Block `..` sequences. |
| JSON/YAML injection | Use proper serialization libraries (e.g., `jq` in shell). NEVER string interpolation for structured formats. |

### Cryptographic Best Practices

| ALWAYS | NEVER |
|--------|-------|
| Use timing-safe comparison for secrets | Use `==` for secret/token comparison |
| Use established crypto libraries | Roll your own cryptography |
| Use strong hash functions (SHA-256+, bcrypt, argon2) | Use MD5 or SHA-1 for security |
| Enforce TLS 1.2+ (prefer 1.3) | Disable certificate verification in production |
| Generate random values with crypto-grade RNG | Use math/random for security-sensitive values |

### Dependency Auditing

| Practice | Frequency |
|----------|-----------|
| Run `audit` command (`npm audit`, `cargo audit`, `pip-audit`, `govulncheck`) | Every CI build |
| Pin dependency versions with lock files | Always committed for applications |
| Review new dependencies before adding | Before merge |
| Monitor for CVEs in transitive dependencies | Automated via Dependabot/Renovate |

### eval/exec/system Avoidance

| Rule | Description |
|------|-------------|
| Avoid `eval()` in all languages | Executes arbitrary code; use structured dispatch instead |
| Avoid shell execution from application code | Use library APIs instead of shelling out |
| If shell execution is unavoidable | Use array-based exec with no interpolation |
| Shell scripts | Avoid `eval` for user-provided data; use functions for dispatch |

### OWASP Top 10 Mapping

| # | OWASP Category | Prevention Pattern | Detection |
|---|----------------|-------------------|-----------|
| A01 | Broken Access Control | Deny by default; enforce server-side auth on every endpoint | Prescan P3: missing auth middleware |
| A02 | Cryptographic Failures | TLS 1.2+, strong hashing (bcrypt/argon2), no plaintext secrets | Prescan P2: hardcoded secrets |
| A03 | Injection | Parameterized queries, array-based exec, template auto-escaping | Prescan P1: string interpolation in queries/commands |
| A04 | Insecure Design | Threat modeling, abuse case testing, rate limiting | Architecture review |
| A05 | Security Misconfiguration | Minimal permissions, disable defaults, harden headers | Config audit |
| A06 | Vulnerable Components | `govulncheck`, `npm audit`, `pip-audit`, `cargo audit` | CI dependency scan |
| A07 | Auth Failures | MFA, strong passwords, session timeout, credential rotation | Auth integration tests |
| A08 | Data Integrity Failures | Signed updates, verified CI/CD pipeline, SBOM | Supply chain review |
| A09 | Logging Failures | Log auth events, access control failures, input validation | Log coverage audit |
| A10 | SSRF | Allowlist outbound hosts, block internal IPs, validate URLs | Prescan P4: unvalidated URL construction |

### HTTP Handler Security Patterns

| Pattern | ALWAYS | NEVER |
|---------|--------|-------|
| Request validation | Validate Content-Type, Content-Length, and body schema before processing | Process requests without type checking |
| Response escaping | Use framework auto-escaping; set explicit Content-Type headers | Return user data in responses without escaping |
| Content-Type | Set `Content-Type` and `X-Content-Type-Options: nosniff` on every response | Rely on browser MIME-sniffing |
| CORS | Restrict `Access-Control-Allow-Origin` to known domains | Use wildcard (`*`) origin with credentials |
| CSRF | Use anti-CSRF tokens for state-changing operations | Rely solely on cookies for authentication |
| Rate limiting | Apply rate limits to authentication, API, and upload endpoints | Allow unlimited requests to sensitive endpoints |
| Headers | Set `Strict-Transport-Security`, `X-Frame-Options`, `Content-Security-Policy` | Omit security headers from responses |

### Path Traversal Prevention

Resolve user-supplied paths to absolute form, then verify the result stays within the allowed directory.

| Language | Pattern |
|----------|---------|
| Go | `cleaned := filepath.Clean(userPath); if !strings.HasPrefix(filepath.Join(baseDir, cleaned), baseDir) { reject }` |
| Python | `resolved = (base_dir / user_path).resolve(); if not str(resolved).startswith(str(base_dir.resolve())): raise` |
| Node | `const resolved = path.resolve(baseDir, userPath); if (!resolved.startsWith(baseDir)) throw` |
| Shell | `realpath "$user_path" | grep -q "^$base_dir" || exit 1` |

**Key rules:**
- Always resolve BEFORE checking — `../` sequences bypass naive prefix checks
- Block null bytes (`\0`) in file paths — some runtimes truncate at null
- Reject absolute paths in user input when relative paths are expected

### Logging Security

| Rule | Description |
|------|-------------|
| Never log passwords | Hash or mask credentials before any log statement |
| Never log tokens | API keys, JWTs, session tokens — redact to first/last 4 chars max |
| Never log PII | Email, SSN, phone numbers — mask or omit in logs |
| Structured logging | Use structured fields (JSON) to prevent log injection via newlines |
| Log levels for security events | Auth failures = WARN, access control violations = ERROR, suspected attacks = CRITICAL |
| Retention | Define log retention policy; purge logs containing sensitive data on schedule |

### Rate Limiting Guidance

| Endpoint Type | Recommended Limit | Strategy |
|---------------|-------------------|----------|
| Authentication (login, register) | 5-10 req/min per IP | Token bucket with exponential backoff |
| API (authenticated) | 100-1000 req/min per user | Sliding window counter |
| File upload | 5-10 req/hour per user | Fixed window with size limits |
| Password reset | 3-5 req/hour per email | Fixed window, no enumeration leak |
| Public (unauthenticated) | 30-60 req/min per IP | Sliding window with CAPTCHA fallback |

**Implementation notes:**
- Apply rate limits at the reverse proxy / API gateway level when possible
- Return `429 Too Many Requests` with `Retry-After` header
- Log rate limit hits for abuse detection
- Consider separate limits for read vs write operations

---

## Documentation Standards

### What to Document

| Document | Why |
|----------|-----|
| Public API signatures | Callers need to know parameters, return types, error behavior |
| Non-obvious logic | Future readers (including yourself) need to understand WHY, not WHAT |
| Error behavior | Callers must know what can fail and how |
| Security-sensitive decisions | Reviewers need to verify threat model compliance |
| Configuration options | Users need to know defaults, valid ranges, and effects |
| Architecture decisions | Teams need to understand trade-offs and constraints |

### What NOT to Document

| Skip | Why |
|------|-----|
| Obvious code (`i++`, `return nil`) | Comments add noise, not signal |
| Implementation details of private functions | Changes frequently; comments go stale |
| Type information already in signatures | Redundant with the type system |
| "What" the code does (when code is clear) | The code itself is the documentation |

### Examples in Documentation

- Include usage examples for public APIs
- Examples should be runnable (doc tests where supported)
- Show the common case first, edge cases second
- Include error handling in examples

### Keeping Documentation in Sync

| Practice | Description |
|----------|-------------|
| Doc tests | Executable examples catch staleness automatically |
| Review docs with code changes | PR reviews should include doc updates |
| Delete docs for deleted features | Stale docs are worse than no docs |
| Version documentation | Match docs to release versions |

### Cross-Reference Patterns

- Link to related concepts rather than duplicating content
- Use relative paths within a project
- Reference external standards by URL (e.g., RFC numbers, OWASP guides)

---

## Code Organization Principles

### Module/Package Naming

| Convention | Description |
|------------|-------------|
| Short, descriptive names | `config`, `handlers`, `models` -- not `configurationManager` |
| Lowercase with language-appropriate separators | `snake_case` (Python/Rust/Go), `kebab-case` (npm/crate names), `camelCase` (TS) |
| No stuttering | `config.Config` is fine; `config.ConfigConfig` is not |
| Domain-driven grouping | Group by feature/domain, not by technical layer |

### Public vs Private Visibility

| Rule | Description |
|------|-------------|
| Minimize public API surface | Export only what callers need |
| Default to private | Make things public only when required |
| Use explicit re-exports | Control the public API from a single entry point |
| Hide implementation details | Internal helpers, data structures, and algorithms stay private |

### Circular Dependency Avoidance

| Strategy | Description |
|----------|-------------|
| Dependency inversion | Depend on abstractions (interfaces/traits), not implementations |
| Extract shared types | Move shared types to a separate, leaf-level module |
| Event-based decoupling | Use events/callbacks instead of direct cross-module calls |
| Layer discipline | Higher layers depend on lower layers, never the reverse |

### File Size Heuristics

| Size | Status | Action |
|------|--------|--------|
| < 300 lines | Excellent | Maintain |
| 300-500 lines | Acceptable | Monitor |
| 500-800 lines | Warning | Consider splitting |
| 800+ lines | Critical | Split into submodules |

### Version-Aware Development

Language-specific standards SHOULD declare the target language/runtime version and organize modern features by version availability. This prevents using features unavailable in the target version and ensures developers adopt modern alternatives when available.

| Language | Version Source | Example Modern Features |
|----------|---------------|------------------------|
| Go | `go.mod` `go` directive | `slices` (1.21+), `range n` (1.22+), `t.Context()` (1.24+) |
| Python | `pyproject.toml` `requires-python` | `match` (3.10+), `tomllib` (3.11+), exception groups (3.11+) |
| Rust | `Cargo.toml` `edition` | `let-else` (2021+), `async fn in trait` (2024+) |
| TypeScript | `tsconfig.json` `target` | `satisfies` (4.9+), `using` (5.2+) |

### Import Ordering

All languages follow the same conceptual grouping:

1. **Standard library** imports
2. **External/third-party** imports
3. **Internal/project** imports

Separated by blank lines. Alphabetical within each group.

---

## Canonical Language Owners

Language-specific guidance lives beside this document in one concise canonical
file per language:

| Language | Canonical file |
|----------|----------------|
| Go | `go.md` |
| Python | `python.md` |
| Rust | `rust.md` |
| TypeScript | `typescript.md` |
| JavaScript | `javascript.md` |
| Shell | `shell.md` |
| JSON/JSONL | `json.md` |
| YAML | `yaml.md` |
| Markdown | `markdown.md` |

Validate consumes these standards as criteria; it does not own duplicate
language catalogs. Universal error-handling, testing, security, documentation,
and organization rules remain here, while language files carry only the
syntax, tooling, and runtime details needed to apply them.

---

**Related:** Language-specific standards in `go.md`, `python.md`, `rust.md`, `typescript.md`, `shell.md`
