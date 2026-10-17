
<skill id="security">

<purpose>
Security is not a feature. It's a constraint on all features.
Never trust user input. Never hardcode secrets. Defense in depth.
45% of AI-generated code contains known security flaws - verify everything.
</purpose>

<prerequisite>
Check for existing security patterns in codebase. Follow them.
Never bypass security checks "for now" or "temporarily."
</prerequisite>

<reference>
Skill-specific: skills/tearitapart/reference/security-research.md
</reference>

<core_principles>
1. NO HARDCODED SECRETS: Environment variables or secure vaults only.
2. INPUT VALIDATION: Validate at system boundaries. Reject invalid, don't sanitize.
3. LEAST PRIVILEGE: Minimum access needed. No admin-by-default.
4. DEFENSE IN DEPTH: Multiple layers. Don't rely on single control.
5. FAIL SECURE: Errors should deny access, not grant it.
6. NORMALIZE BEFORE ALLOWLISTS: reject lexical `.` / `..` path segments and
   resolve the candidate into the intended root before prefix or regex checks.
   An allowlisted prefix is not containment when traversal is still present.
</core_principles>

<flow>

  1. **Secrets check**: grep for hardcoded keys/passwords/tokens before any commit.
     (gate: `git grep -E "(api_key|apiKey|password|secret|token)\s*=\s*['\"][^'\"]{8,}"` returns empty)

  2. **Input validation**: all user input validated at API boundary with schema (Zod/Pydantic).
     (gate: every public endpoint parses input through schema before use; see code patterns in reference)

  3. **SQL injection**: all queries parameterized; no string concatenation with user data.
     (gate: grep for template literal SQL with user variables returns empty)

  4. **XSS prevention**: user-provided HTML sanitized (DOMPurify); CSP headers configured.
     (gate: `dangerouslySetInnerHTML` only appears with DOMPurify wrapping)

  5. **Authentication**: tokens in httpOnly cookies, not localStorage; auth checked per-request.
     (gate: no `localStorage.setItem('token'`; every protected route has auth check)

  6. **Authorization**: role/ownership check before every sensitive operation.
     (gate: no delete/update/admin endpoint without requester role verification)

  7. **CSRF protection**: tokens on state-changing requests; SameSite=Strict on session cookies.
     (gate: POST/PUT/DELETE endpoints verify X-CSRF-Token or use SameSite cookie)

  8. **Rate limiting**: enabled on all public endpoints; stricter on expensive ops.
     (gate: every `/api/` route has rate limit middleware)

  9. **Error handling**: generic messages in responses; stack traces only in server logs.
     (gate: no `error.stack` or internal paths in HTTP response bodies)

  10. **Dependency audit**: `npm audit` / `pip-audit` clean; lockfile committed.
      (gate: audit exits 0 or all findings are acknowledged with justification)

  11. **Supply chain**: verify package existence + download counts before installing AI-suggested packages.
      (gate: no packages added without explicit npm/pypi verification; see supply chain patterns in reference)

  12. **Prompt injection** (AI-integrated features): user text never interpolated into system prompts; LLM output validated before use.
      (gate: no f-string/template system prompt with raw user input; see prompt injection patterns in reference)

  13. **Agent permissions**: every spawned agent has explicit tool allowlist + file scope; no admin-by-default.
      (gate: spawn contract lists allowed tools ≤5; sensitive scopes named explicitly)

  14. **Risk-based review priority**: when doing a full security review pass, prioritize in order: logic changes → deleted validations → auth flows → query changes → areas with prior security incidents. Start where impact is highest. Highest-risk categories (auth, cryptography, payment flows, secrets/credential handling) require human sign-off regardless of AI review confidence; never delegate final approval to automation alone. <!-- Updated 2026-06-11: https://blog.exceeds.ai/ai-code-review-best-practices/ -->

  15. **Automated coverage baseline**: automated checks (ESLint + AI linters + security scanners) catch 70–80% of common issues. Wire Snyk MCP into the dev loop to let Claude scan for vulnerabilities and dependency CVEs inline, without a separate review step. <!-- Updated 2026-06-09: https://sourcegraph.com/blog/ai-code-review https://code.claude.com/docs/en/best-practices -->

  16. **Deny-first permissions**: configure deny rules for sensitive directories (`migrations/`, `secrets/`, `.env*`) BEFORE allow/ask rules in `.claude/settings.json`. Files invisible via deny can't be accessed even if Claude generates a path to them; this is stronger than a hook because it acts at the permissions layer, not the script layer. <!-- Updated 2026-06-14: https://smartscope.blog/en/generative-ai/claude/claude-code-best-practices-advanced-2026/ -->

  17. **AI-generated code defect rate**: AI-generated PRs contain 1.7× more defects than human-only PRs. Apply proportionally stricter review to AI-generated changes: security linter + human sign-off on auth/payment/secrets paths, regardless of AI review confidence. "45% of AI-generated code contains security vulnerabilities" compounds this; never waive the security checklist for AI-authored code. <!-- Updated 2026-06-18: https://blog.exceeds.ai/ai-code-review-best-practices/ https://www.verdent.ai/guides/best-ai-for-code-review-2026 -->

  18. **Difference-aware PR scanning**: scan against the PR diff, not the full codebase. Scoping to changed lines produces focused, change-contextual findings rather than codebase-wide noise that reviewers learn to ignore. Pair with two-stage refutation: first pass generates candidate findings; second pass asks Claude to refute each one ("what evidence would disprove this vulnerability?"), filtering false positives before surfacing to human reviewers. <!-- Updated 2026-06-21: https://www.anthropic.com/news/claude-code-security -->

  19. **NIST SP 800-218A for AI-assisted development**: the three essential security frameworks in 2026 are OWASP Top 10 (traditional app vulnerabilities), OWASP Top 10 for LLM Applications (prompt injection, insecure output handling, training data poisoning), and NIST SP 800-218A (extends the NIST SSDF to the AI code generation pipeline). SP 800-218A requirements: document AI tool usage in the SBOM, apply the same secure coding standards to AI-generated code as hand-written code, and require human sign-off on AI-authored components touching safety-critical paths. Treat the AI generation pipeline as part of the supply chain, not a trusted internal tool. <!-- Updated 2026-06-22: https://www.metacto.com/blogs/establishing-code-review-standards-for-ai-generated-code -->

  20. **Track AI security findings for codebase patterns**: record which vulnerability classes AI review catches most frequently in your repo. High-frequency findings reveal systemic weaknesses (e.g., consistently missing auth checks on a specific route pattern, XSS in a template helper). Use the pattern map to add targeted custom rules and prioritize higher-scrutiny review at known weak spots. <!-- Updated 2026-06-30: https://www.codeant.ai/blogs/code-review-best-practices -->

</flow>

<pre_deployment_checklist>
Before ANY production deployment:
- [ ] **Secrets**: No hardcoded secrets, all in env vars
- [ ] **Input Validation**: All user inputs validated with Zod/Pydantic
- [ ] **SQL Injection**: All queries parameterized
- [ ] **XSS**: User content sanitized, CSP configured
- [ ] **CSRF**: Protection on state-changing operations
- [ ] **Authentication**: Tokens in httpOnly cookies, not localStorage
- [ ] **Authorization**: Role checks before sensitive operations
- [ ] **Rate Limiting**: Enabled on all endpoints
- [ ] **HTTPS**: Enforced in production
- [ ] **Error Handling**: No sensitive data in responses
- [ ] **Logging**: No passwords, tokens, or PII in logs
- [ ] **Dependencies**: npm audit clean, no known vulnerabilities
- [ ] **RLS**: Row Level Security enabled (Supabase)
- [ ] **File Uploads**: Validated (size, type, extension)
</pre_deployment_checklist>

<anti_patterns>
- "We'll add security later" (you won't)
- Disabling security for development (gets shipped)
- Rolling your own crypto (use established libraries)
- Security through obscurity (it's not security)
- Trusting client-side validation alone
- Logging sensitive data
- Installing AI-suggested packages without verifying they exist and are legitimate
- Giving agents more tools or file access than their task requires
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"security","vectors_checked":["injection","xss","authz","secrets"],"findings":N}'
</on_complete>

</skill>
