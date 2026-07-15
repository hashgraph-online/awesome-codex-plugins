# OWASP Top 10 Security Checklist

> Pre-deployment security audit checklist. Use as gate in `/validate --preset=security-audit` or `/postmortem --scope security`.

## Checklist

### 1. Secrets Management
- [ ] No hardcoded API keys, passwords, or tokens in source
- [ ] All secrets loaded from environment variables or secret stores
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in log output or error messages
- [ ] CI/CD secrets use platform-native secret management

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

## Severity Classification

| Finding | Severity | SLA |
|---------|----------|-----|
| Hardcoded secret in source | CRITICAL | Block merge |
| SQL injection possible | CRITICAL | Block merge |
| Missing input validation on public endpoint | HIGH | Fix before release |
| Missing rate limiting | MEDIUM | Fix within sprint |
| Dependency with known CVE (CVSS > 7) | HIGH | Fix before release |
| Missing CSP headers | MEDIUM | Fix within sprint |
| Debug logging in production code | LOW | Fix in next cleanup |

## Integration

### With /validate
```bash
/validate --preset=security-audit src/
```
Loads this checklist as judge context. Each judge evaluates against relevant checklist items.

### With /postmortem
```bash
/postmortem --scope security
```
Run the full checklist as factual security evidence for the exact candidate.

### With /security (suite primitives)
The redteam primitive (`collect-redteam`) covers items 1-4 automatically. This checklist covers the remaining items that require code-level review.

### With CI
```bash
# Minimum: secrets + dependencies
grep -rn 'password\|secret\|api_key' --include='*.go' --include='*.py' . | grep -v test
govulncheck ./...  # or npm audit / pip audit
```
