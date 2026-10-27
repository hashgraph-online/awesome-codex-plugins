# Security Class Checklist

> Code-level review classes drawn from the OWASP Top 10 plus SSRF, deserialization,
> command injection, cryptography and prompt injection. Load it during a `/security`
> review pass to walk each class and record a per-class result. It is not exhaustive:
> add any class the surface needs (a race, business logic) to the ledger rather than
> calling it clean. It ranks findings by severity; it does not gate merges or
> releases — those are caller decisions.

## Checklist

### 1. Secrets Management
- [ ] No hardcoded API keys, passwords, or tokens in source
- [ ] All secrets loaded from environment variables or secret stores
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in log output, error messages, or terminal echo while a person types one in
- [ ] CI/CD secrets use platform-native secret management, and each job receives only the secrets its workflow references
- [ ] When one operation issues several credentials, routine calls use the least-privileged one and the elevated one is kept only for the operations that need it

**Detection:**
```bash
grep -rn 'password\s*=\s*"[^"]\+"\|api_key\s*=\s*"[^"]\+"\|secret\s*=\s*"[^"]\+"\|token\s*=\s*"[^"]\+' --include='*.go' --include='*.py' --include='*.ts' --include='*.js' . | grep -v _test | grep -v test_ | grep -v vendor/
```

### 2. Input Validation
- [ ] All user input validated with schema (Zod, JSON Schema, struct tags)
- [ ] Input length limits enforced
- [ ] Content-type validation on file uploads
- [ ] No `eval()`, `exec()`, or dynamic code execution with user input
- [ ] Path traversal prevention (no `../` in user-supplied paths)
- [ ] Secret files and scratch in a shared temp directory are owner-only from the moment they exist (restrictive umask before creation, not chmod after the write); scratch takes a fresh `mktemp` path, and code that reuses a fixed, guessable name refuses it when it is a symlink or another user's entry at the open itself (exclusive no-follow create: `O_EXCL|O_NOFOLLOW`, or `set -C` in shell), not by a test before the write, since any local user can create or redirect that name first

### 3. SQL Injection
- [ ] All database queries use parameterized statements
- [ ] No string concatenation in SQL
- [ ] ORM usage follows safe query patterns
- [ ] Raw queries (if any) are reviewed and justified

### 4. XSS (Cross-Site Scripting)
- [ ] User-generated HTML sanitized before rendering
- [ ] CSP (Content-Security-Policy) headers configured
- [ ] Template engines auto-escape by default
- [ ] No `innerHTML` or `dangerouslySetInnerHTML` with user input

### 5. CSRF (Cross-Site Request Forgery)
- [ ] Anti-CSRF tokens on state-changing requests
- [ ] `SameSite=Strict` or `SameSite=Lax` on cookies
- [ ] Origin/Referer header validation

### 6. Authentication
- [ ] Tokens in httpOnly cookies (not localStorage)
- [ ] Session expiry configured
- [ ] Password hashing uses bcrypt/argon2 (not MD5/SHA1)
- [ ] Rate limiting on auth endpoints
- [ ] Account lockout after failed attempts

### 7. Authorization
- [ ] Role-based access control (RBAC) enforced
- [ ] Authorization checks on every endpoint (not just frontend)
- [ ] No direct object reference without ownership check
- [ ] Admin endpoints require elevated permissions

### 8. Rate Limiting
- [ ] Rate limits on all public endpoints
- [ ] Stricter limits on auth/payment endpoints
- [ ] Rate limit headers returned (X-RateLimit-*)
- [ ] Distributed rate limiting if multi-instance

### 9. Sensitive Data Exposure
- [ ] No passwords, tokens, or PII in log output
- [ ] Error messages are generic (no stack traces in production)
- [ ] HTTPS enforced (no mixed content)
- [ ] Sensitive fields excluded from API responses
- [ ] Database encryption at rest for PII

### 10. Dependencies
- [ ] No known vulnerable dependencies (`npm audit`, `pip audit`, `govulncheck`)
- [ ] Dependencies pinned to specific versions
- [ ] Lock files committed
- [ ] Regular dependency update process (Renovate/Dependabot)

### 11. CI and Automation Definitions
- [ ] Triggers that run contributor-controlled code (forked pull requests, comment commands) get no write token or secrets
- [ ] Attacker-controlled fields (PR title, branch name, issue body) never expand directly into shell or script steps. The same holds wherever a script or agent instruction writes a command around text it did not author (a branch name from PR data, a model id or effort level from config): admit the value only if it matches a narrow character allowlist, or keep it out of the command text by passing it through a variable, file or stdin, and refuse a failing value rather than quoting it harder. `$(...)` still runs inside double quotes, and git accepts it in branch names
- [ ] Third-party actions, images and scripts are pinned to an immutable commit or digest, not a moving tag
- [ ] Each job's token permissions are the minimum it needs; default write access is off
- [ ] Every job has an execution time limit

### 12. Server-Side Request Forgery (SSRF)
- [ ] A server-side fetch of a caller-supplied URL or host is limited to an allowlist; redirects and resolved addresses are rechecked, and loopback, private and cloud-metadata addresses are refused

### 13. Deserialization
- [ ] Untrusted bytes are never loaded with a format that can build arbitrary objects (`pickle`, `yaml.load` without a safe loader, Java native serialization, `Marshal`); use a data-only format and validate it

### 14. OS Command Injection
- [ ] Application code never builds a shell command from untrusted input: pass an argument list (no `shell=True`, `os.system`, or `sh -c` around interpolated text) and allowlist any value that becomes an argument; class 11 covers scripts and agent instructions

### 15. Cryptography
- [ ] Standard libraries and current algorithms only (no ECB mode, no MD5 or SHA-1 for integrity, no home-made scheme); keys and IVs are never hardcoded or reused; tokens come from a CSPRNG (`secrets`, `crypto/rand`), not `random`; TLS certificate verification is never disabled

### 16. Prompt Injection and Model Output
- [ ] Untrusted text that reaches a model (retrieved documents, issues, web pages, tool output) cannot widen what it may do: tool access, secrets and write actions are bounded by the caller's authority, not by the prompt
- [ ] Model output is untrusted input before it reaches a shell, query, file path, HTML or another tool

## Severity Classification

Severity ranks findings so a reviewer can order them; it carries no merge, release,
or remediation-timing authority. Whether and when to fix, and whether to block any
delivery, are caller decisions this checklist does not make.

| Finding | Severity |
|---------|----------|
| Hardcoded secret in source | CRITICAL |
| SQL injection possible | CRITICAL |
| OS command injection or unsafe deserialization of untrusted input | CRITICAL |
| SSRF reaching internal or metadata addresses | HIGH |
| Missing input validation on public endpoint | HIGH |
| Dependency with known CVE (CVSS > 7) | HIGH |
| Missing rate limiting | MEDIUM |
| Missing CSP headers | MEDIUM |
| Debug logging in production code | LOW |

## Integration

### With /security (suite primitives)
The offline redteam scan (`prompt_redteam.py scan`) checks repo-owned prompt and control surfaces against the attack pack. It does not review application code, so every item in this checklist still needs a code-level result: finding, clean, or not assessed.

### With CI
```bash
# Minimum: secrets + dependencies
grep -rn 'password\|secret\|api_key' --include='*.go' --include='*.py' . | grep -v test
govulncheck ./...  # or npm audit / pip audit
```
