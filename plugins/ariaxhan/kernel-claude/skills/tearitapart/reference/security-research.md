# Security Reference: Research & Best Practices

Reference for secure coding, vulnerability prevention, and AI-specific security risks.
Read on demand. Not auto-loaded.

## Sources

OWASP Top 10 2025, OWASP Top 10 for LLM Applications 2025, OWASP Top 10 for
Agentic Applications 2026 (NEW), Veracode State of Software Security 2026
(Feb 26, 2026), IBM X-Force Threat Index 2026 (Feb 25, 2026), Black Duck OSSRA
2026 (Feb 25, 2026), Snyk AI Security Fabric (Feb 3, 2026), Anthropic Opus 4.6
System Card (Feb 5, 2026), NIST SP 800-218r1 (SSDF 1.2), Check Point MCP research.

---

## AI Code Security: The Numbers (Updated Feb 2026)

Veracode 2026: Security debt affects **82%** of organizations (up from 74%).
High-risk vulnerabilities now at **11.3%** (up from 8.3%).
Veracode: 45% of AI-generated code contains known security flaws.
Opsera 2026: AI code has **15-18% more vulnerabilities** than human code.
CodeRabbit: AI PRs have 1.57x more security findings than human PRs.

IBM X-Force 2026: 44% surge in app exploitation, 4x supply chain attacks since 2020.
Black Duck 2026: Open source vulnerabilities doubled; only 24% do comprehensive
AI code evaluation.

Critical: More vulnerabilities are now created than fixed. AI accelerates
code creation but security review can't keep pace.

---

## OWASP Top 10 (2025) - Most Relevant to AI-Generated Code

A01: Broken Access Control. AI generates endpoints without auth checks.
Always verify: is this endpoint protected? Who can access it?

A03: Software Supply Chain Failures (NEW position). AI adds dependencies
without auditing. Each dependency is a trust decision.
Always: npm audit / pip-audit / cargo audit after adding dependencies.

A05: Injection. AI generates string concatenation for SQL, shell commands,
HTML output. Parameterize everything.

A08: Server-Side Request Forgery. AI generates HTTP clients that don't
validate URLs. Always validate and restrict outbound requests.

A10: Mishandling of Exceptional Conditions (NEW). AI swallows errors or
exposes stack traces. Handle errors explicitly with actionable messages.

---

## OWASP Top 10 for LLM Applications (2025)

LLM01: Prompt Injection. Crafted inputs manipulate LLM behavior.
LLM02: Sensitive Information Disclosure. LLMs leak PII or credentials.
LLM03: Supply Chain. Compromised models, poisoned training data.
LLM04: Data and Model Poisoning. Tampered training degrades security.
LLM05: Improper Output Handling. LLM output used without validation.
LLM06: Excessive Agency. LLMs granted unchecked autonomy.
LLM07: System Prompt Leakage. System instructions exposed to users.
LLM08: Vector and Embedding Weaknesses. RAG pipeline vulnerabilities.
LLM09: Misinformation. LLMs generate false but plausible content.
LLM10: Unbounded Consumption. Resource exhaustion via LLM abuse.

---

## OWASP Top 10 for Agentic Applications (2026) — NEW

Distinct from LLM Top 10. Key distinction: "A standard LLM generates content.
An agentic AI takes action. It uses tools, makes decisions, and performs
multi-step tasks autonomously."

ASI01: Agent Behavior Hijacking. Total compromise where agent becomes weaponized.
ASI02: Prompt Injection. Crafted inputs manipulate agent behavior.
ASI03: Tool Misuse. Exploiting agent's tool access for unauthorized actions.

---

## MCP Security (Critical Gap — Feb 2026)

Model Context Protocol vulnerabilities dominate 2026 security research:

Attack vectors:
- Tool Poisoning: Malicious instructions hidden in tool descriptions.
- Rug Pull Attacks: Tool definitions change post-approval (Day 1: safe, Day 7: malicious).
- Session Hijacking: Session IDs in URLs expose credentials in logs.
- Cross-service exploitation: Single compromised MCP server accesses multiple tools.

Critical CVEs:
- CVE-2025-6514 (CVSS 9.6): mcp-remote project
- CVE-2025-68143/68144/68145: Anthropic Git MCP server RCE
- CVE-2026-21852 (CVSS 5.3): Claude Code API key exfiltration
- CVE-2025-59536 (CVSS 8.7): Claude Code user consent bypass for MCP servers
- CVE-2026-22708: Cursor IDE RCE via indirect prompt injection

Mitigations: Sandbox MCP servers, pin tool versions, review tool descriptions,
restrict network access, use capability-based security.

---

## Prompt Injection Quantified (Anthropic Feb 2026)

First quantified metrics from Anthropic's Opus 4.6 System Card (212 pages):

| Surface | Single Attempt | 200 Attempts | With Safeguards |
|---------|---------------|--------------|-----------------|
| GUI-based agent | 17.8% success | 78.6% success | 1.4% success |
| Constrained coding | 0% success | 0% success | N/A |

Key insight: "Defenses degrade under sustained attack." Promptfoo red team found
jailbreak success climbs from 4.3% baseline to 78.5% in multi-turn scenarios.

---

## Security Checklist for Every Feature

### Input Layer
- All user input validated at API boundary (type, length, format)
- All user input sanitized for context (HTML, SQL, shell, path)
- File uploads: validate type, size, scan for malware
- Rate limiting on all public endpoints

### Data Layer
- All queries parameterized (no string concatenation)
- Sensitive data encrypted at rest and in transit
- PII handling: minimal collection, access logging, deletion capability
- No secrets in source code (grep for key=, token=, password=, secret=)

### Auth Layer
- Authentication on every endpoint that needs it
- Authorization checked per-request (not cached)
- Session management: secure cookies, expiry, rotation
- No sensitive data in URLs or query parameters

### Output Layer
- Error messages: no stack traces, no internal details in production
- Response headers: CORS configured, security headers set
- No internal IDs, file paths, or infrastructure details exposed

### Dependency Layer
- npm audit / pip-audit / cargo audit before committing
- Lockfile committed (ensures reproducible builds)
- No dependencies added for trivial functionality (<10 lines)
- Check last update date, open security issues, maintainer status
- **NEW 2026**: Dependency cooldown (7-14 days for new packages)
- **NEW 2026**: 230+ malicious packages confirmed in Feb 2026 alone

### MCP/Agent Layer (NEW 2026)
- Sandbox all MCP servers (container isolation or capability-based)
- Review tool descriptions for hidden instructions
- Pin tool versions; verify no post-approval changes
- Tier agents by risk level; higher tiers need more verification
- Scoped and short-lived credentials for agent tool access

---

## KERNEL Integration

- Adversary agent: security testing is phase 5 (after edge cases, before
  contract verification). Check input validation, auth, data exposure, injection.
- Validator agent: secrets scan is phase 1 (first thing checked, blocks commit).
- Invariants in kernel.md: no hardcoded secrets, no irreversible operations
  without confirmation.
- tearitapart: security review is a dedicated phase in architecture assessment.

---

## Code Patterns: Secrets Management

```typescript
// BAD: Hardcoded secrets
const apiKey = "sk-proj-xxxxx"  // NEVER

// GOOD: Environment variables
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) throw new Error('OPENAI_API_KEY not configured')
```

Checklist before commit:
- [ ] No API keys in code
- [ ] No passwords in code
- [ ] No connection strings with credentials
- [ ] .env files in .gitignore
- [ ] Secrets in environment variables or vault

---

## Code Patterns: Input Validation

```typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150)
})

export async function createUser(input: unknown) {
  const validated = CreateUserSchema.parse(input)
  return await db.users.create(validated)
}
```

```typescript
// File upload validation
function validateFileUpload(file: File) {
  const maxSize = 5 * 1024 * 1024  // 5MB
  if (file.size > maxSize) throw new Error('File too large')

  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(file.type)) throw new Error('Invalid file type')

  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif']
  const ext = file.name.toLowerCase().match(/\.[^.]+$/)?.[0]
  if (!ext || !allowedExtensions.includes(ext)) throw new Error('Invalid extension')
}
```

---

## Code Patterns: SQL Injection

```typescript
// BAD: String concatenation
const query = `SELECT * FROM users WHERE email = '${userEmail}'`  // NEVER

// GOOD: Parameterized queries
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', userEmail)

// Or with raw SQL
await db.query('SELECT * FROM users WHERE email = $1', [userEmail])
```

---

## Code Patterns: XSS Prevention

```typescript
import DOMPurify from 'isomorphic-dompurify'

// ALWAYS sanitize user-provided HTML
function renderUserContent(html: string) {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p'],
    ALLOWED_ATTR: []
  })
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

```typescript
// Content Security Policy
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      connect-src 'self' https://api.example.com;
    `.replace(/\s{2,}/g, ' ').trim()
  }
]
```

---

## Code Patterns: Authentication

```typescript
// BAD: localStorage (vulnerable to XSS)
localStorage.setItem('token', token)  // NEVER

// GOOD: httpOnly cookies
res.setHeader('Set-Cookie',
  `token=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`)
```

```typescript
// Authorization check
export async function deleteUser(userId: string, requesterId: string) {
  const requester = await db.users.findUnique({ where: { id: requesterId } })

  if (requester.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })
  }

  await db.users.delete({ where: { id: userId } })
}
```

```sql
-- Row Level Security (Supabase)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own data"
  ON users FOR SELECT
  USING (auth.uid() = id);
```

---

## Code Patterns: CSRF Protection

```typescript
import { csrf } from '@/lib/csrf'

export async function POST(request: Request) {
  const token = request.headers.get('X-CSRF-Token')

  if (!csrf.verify(token)) {
    return NextResponse.json({ error: 'Invalid CSRF token' }, { status: 403 })
  }

  // Process request
}
```

```typescript
// SameSite cookies prevent CSRF
res.setHeader('Set-Cookie',
  `session=${sessionId}; HttpOnly; Secure; SameSite=Strict`)
```

---

## Code Patterns: Rate Limiting

```typescript
import rateLimit from 'express-rate-limit'

// General API rate limit
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 100,                   // 100 requests per window
  message: 'Too many requests'
})

// Stricter limit for expensive operations
const searchLimiter = rateLimit({
  windowMs: 60 * 1000,  // 1 minute
  max: 10,              // 10 requests per minute
})

app.use('/api/', limiter)
app.use('/api/search', searchLimiter)
```

---

## Code Patterns: Error Handling

```typescript
// BAD: Exposing internals
catch (error) {
  return NextResponse.json({
    error: error.message,
    stack: error.stack  // NEVER
  }, { status: 500 })
}

// GOOD: Generic messages
catch (error) {
  console.error('Internal error:', error)  // Log for debugging
  return NextResponse.json({
    error: 'An error occurred. Please try again.'
  }, { status: 500 })
}
```

```typescript
// BAD: Logging sensitive data
console.log('User login:', { email, password })  // NEVER

// GOOD: Redact sensitive fields
console.log('User login:', { email, userId })
```

---

## Supply Chain Security (Updated 2026-03-30)
<!-- Sources: Claude Code best practices, OWASP supply chain guidance -->

AI-generated code introduces supply chain risks beyond traditional OWASP top 10:

- **Hallucinated packages**: AI may reference packages that don't exist or have been
  name-squatted. Always verify package existence and download counts before installing.
- **Version pinning**: Pin exact versions in package.json/requirements.txt for production.
  Floating versions allow silent breaking changes on redeploy.
- **Dependency audit cadence**: Run `npm audit` / `pip audit` / `cargo audit` on every PR,
  not just on release. CI gate should block merge on HIGH/CRITICAL findings.
- **Lockfile integrity**: Commit lockfiles. Verify lockfile wasn't modified unexpectedly
  before merging PRs (lockfile tampering is a supply chain attack vector).

---

## Prompt Injection Patterns (Updated 2026-03-30)
<!-- Sources: Anthropic prompt engineering guide, agentic security research -->

When building AI-integrated features, prevent prompt injection:

- **Untrusted content isolation**: Never interpolate user-provided text directly into
  system prompts. Use structured data formats (JSON tool calls) instead of free-text.
- **Output validation**: Treat LLM output as untrusted input. Validate and sanitize before
  rendering or executing.
- **Capability scoping**: AI agents should have only the permissions needed for their task.
  An agent that reads files shouldn't be able to write to disk unless explicitly required.
- **Indirect injection**: User-provided data can contain injections that activate when
  processed by an AI (e.g., "Ignore previous instructions and..."). Sanitize on ingestion,
  not just on display.

---

## Cautionary Pattern Library (Updated 2026-04-29)
<!-- Sources: https://javaworldmag.com/evolving-code-reviews-with-ai-in-2026/, https://codeintelligently.com/blog/ai-code-quality-guide-2026 -->

AI code reviewers miss security issues that require system context humans possess.
Maintain a living doc at `_meta/security/cautionary-patterns.md` capturing:
- AI hallucinations that produced plausible but insecure code (non-existent APIs called, wrong auth flows)
- Patterns where AI bypassed validation "for simplicity" that later became vulnerabilities
- Successful security prompts that caught real issues (promote to skills)

Review this doc before any security-sensitive implementation. Institutional memory beats repeated audits.

---

## Agentic Security Scanning (Updated 2026-05-12)
<!-- Source: https://www.coderabbit.ai/blog/claude-opus-4-7-for-ai-code-review -->

**In-agent dependency scanning**: Use Snyk MCP (or equivalent) to run vulnerability checks inside the agent rather than as a separate CI step. Agent sees results inline, can fix issues before committing. Install once, invoke via MCP tool calls.

**Tool count limit**: Give each security-review agent ≤5 tools. Each tool adds context overhead; beyond 5, agents lose focus and tool selection degrades. For security review: Read + Grep + Bash (run audit) + one MCP scanner. That's it.

**Agent permission audit**: Before spawning any agent that touches auth, payments, or PII, explicitly list its allowed tools and file scope in the contract. An agent scoped to read `src/api/` should never touch `src/auth/` or `.env`. Least-privilege applies to agents, not just users.

---

## Risk-Based Review Configuration (Updated 2026-05-17)
<!-- Sources: https://brightsec.com/blog/ai-code-review-best-practices-2-0-2026-toolchain/, https://www.kluster.ai/blog/best-code-review-practices -->

Configure AI code review tools with risk-based rules — not blanket "review everything" settings. Default-enable scanning for:
- Deleted input validations (highest risk: silent regression)
- Auth flow changes (any modification to authentication/authorization logic)
- Query changes touching user-scoped data (RLS bypass risk)
- SQLi / XSS / unsafe API patterns
- Functions exceeding complexity threshold (complexity correlates with audit misses)

Turn off style and formatting rules in security scanning — noise drowns signal. Security reviewers should see zero false-positive noise to avoid alert fatigue.
