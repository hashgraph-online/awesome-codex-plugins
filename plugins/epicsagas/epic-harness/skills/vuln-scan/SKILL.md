---
name: vuln-scan
description: "Systematic vulnerability scan across injection, auth, data exposure, and dependencies — traced by reading code, not grepping for keywords. Use when scanning for vulnerabilities, reviewing security, or validating threat models."
---

# Vuln Scan — Systematic Vulnerability Scanner

## Iron Law

Code you haven't traced from input to sink has vulnerabilities you haven't found. A grep hit is a lead, not a finding.

## Process

### Step 0: Load Engagement Context

Check for `.harness/engagement.md`. If present, load scope constraints — only scan in-scope paths and respect exclusions.

Check for `THREAT_MODEL.md` from a previous `/threat-model` run. If present, use its threat scenarios as scan targets. If absent, run full-surface scan.

### Step 1: Map Entry Points to Trust Boundaries

Enumerate every place untrusted data enters the system, by reading the code:

- **External → app**: HTTP handlers/routers, GraphQL resolvers, webhooks, file uploads, form fields, query params, headers
- **Process boundary**: CLI args, environment variables, IPC, deserialization of stored data (cache, DB rows written earlier, config files)
- **Client-supplied state**: cookies, JWT claims, API keys, referer/origin

For each entry point, note: what validation exists (yes/no/partial), and where the data flows next. This list is the scan's backbone — a scan that cannot name its entry points has not started.

### Step 2: Trace Data Flow to Sinks

From each entry point, follow the data by reading code until it reaches a dangerous operation, or dies (validated, parameterized, dropped). Dangerous sink classes:

| Sink class | Examples (non-exhaustive) |
|-----------|--------------------------|
| Command/code execution | shell invocation, `eval`-family, template engines with code modes, deserialization to live objects |
| Query construction | string-built SQL, raw-query escapes in any ORM (Knex `raw`, Prisma `$queryRaw`, SQLAlchemy `text()`, Sequelize `literal`, Django `extra`/`raw`, Rails `where("...")` with interpolation) |
| Filesystem | path joins with user input, upload destinations, archive extraction (zip-slip), file reads driven by request params |
| Web output | template rendering with non-auto-escaping engines, `innerHTML`-family, redirect targets, header values (CRLF) |
| Auth decisions | IDOR — object lookups keyed only on user-supplied ids without ownership checks; role checks done client-side or per-endpoint instead of per-object |

Read the surrounding code for every candidate sink. A sink that only receives validated/parameterized data is not a finding; a sink reachable from an entry point with no validation is.

### Step 3: Reason About Encoding and Context at Each Sink

For each reachable sink, ask what context the data lands in and whether the encoding matches:

- Interpolated into a SQL string? → parameterize, don't escape
- Interpolated into a shell string? → arg-array execution, don't quote
- Rendered into HTML/JS/CSS/URL? → each needs context-specific output encoding; auto-escaping templates cover HTML only when actually enabled for that template
- Joined into a path? → canonicalize, then verify containment inside the intended root
- Deserialized? → prefer format + type that cannot instantiate attacker-chosen types

### Step 4: Auth & Data-Exposure Pass

- **Default-deny**: routes/actions missing an auth middleware or check entirely — enumerate handlers and look for the gaps, not the checks
- **Object-level authorization**: for each handler that reads/writes a user-owned object, is ownership verified on THIS request?
- **Secrets**: hardcoded credentials vs. config/env references; secrets in logs, error messages, client bundles, API responses
- **Error leakage**: verbose errors/stack traces/config in production paths; error messages that distinguish "no such user" from "wrong password"

### Step 5: Dependency Pass

```bash
cargo audit 2>/dev/null || echo "cargo-audit not installed"   # Rust
npm audit 2>/dev/null || echo "npm audit not available"       # Node.js
```

For each advisory: is a fix available, and is the vulnerable code path actually reachable from this codebase's usage? Unreachable advisories are LOW/INFO, not silent drops. Also flag actively-used dependencies that are unmaintained (no release in ~2+ years, archived repo) even without a CVE.

### Grep as Accelerator, Not Oracle

Grep is fine for *candidate* sink locations (`raw(`, `exec`, `innerHTML`, `eval`, secret-ish identifiers) — use it to shortlist where to read. It misses framework-specific sinks, aliases, and data built across files. Never report a finding from a grep hit alone; never conclude "clean" because grep found nothing.

### Step 6: Produce Output

Write `VULN-FINDINGS.json`:

```json
{
  "scan_date": "ISO-8601",
  "scope": "full | incremental",
  "threat_model_ref": "THREAT_MODEL.md | null",
  "entry_points_traced": ["list every entry point examined — required for clean scans"],
  "findings": [
    {
      "id": "V1",
      "dimension": "injection | auth | exposure | dependency",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW | INFO",
      "file": "path/to/file",
      "line": 42,
      "source": "untrusted-input origin (entry point)",
      "sink_chain": ["entry function", "...", "sink function"],
      "description": "what was found",
      "validated": true,
      "false_positive": false,
      "reachable": true,
      "mitigated": false,
      "threat_scenario": "T1 | null",
      "remediation": "one-line fix hint"
    }
  ],
  "summary": {
    "total": 10,
    "critical": 1,
    "high": 3,
    "medium": 4,
    "low": 2,
    "false_positives": 0
  }
}
```

### Step 7: Feed into Triage

After producing findings, suggest:
**"Run `/triage` to validate findings with adversarial review."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "It's an internal tool / not user-facing" | Internal boundaries are attack surfaces — lateral movement starts inside. | Trace internal entry points with the same rigor. |
| "The framework sanitizes automatically" | Auto-escaping and parameterization have opt-outs, raw escapes, and edges; business logic is framework-agnostic. | Find the raw/dangerous escapes and read them. |
| "We'll add validation later" | Later never arrives for paths that already work. | Finding = now; remediation line goes in the output. |
| "Grep found nothing, so we're clean" | Grep misses aliased and framework-specific sinks by construction. | A clean claim requires traced entry points, not an empty grep. |
| "Dependencies are vetted" | Transitive dependencies aren't. | Run the dependency pass every time the lockfile changes. |

## Evidence Required

- [ ] Every finding cites file:line + the untrusted-input origin + the sink call chain
- [ ] Each finding validated: reachable, not mitigated, severity confirmed
- [ ] A clean (or low-finding) scan lists `entry_points_traced` — absence of evidence is not evidence of absence
- [ ] All 4 dimensions completed (injection, auth, exposure, dependency)
- [ ] VULN-FINDINGS.json written with summary
- [ ] If THREAT_MODEL.md exists: each threat scenario mapped to findings
- [ ] No CRITICAL/HIGH finding dismissed without explicit justification

## Red Flags

- Reporting grep hits without reading the surrounding code
- Skipping framework-specific sink types (ORM raw escapes, non-auto-escaping templates)
- Claiming clean without naming which entry points were traced
- Scanning only changed files when full-surface scan was requested
- Marking findings as false positives without a traced reason
- VULN-FINDINGS.json with zero findings on a non-trivial codebase — the scan was likely incomplete, not the codebase clean
