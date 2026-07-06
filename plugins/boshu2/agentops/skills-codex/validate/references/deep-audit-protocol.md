# Deep Audit Protocol

> Used by `/vibe --deep`, `/vibe --sweep`, and `/post-mortem` (unless `--skip-sweep`).

Two-phase architecture: cheap per-file explorer sweep (discovery) followed by council judges (adjudication). All reporting caps removed.

```
Files -> chunk into batches of 3-5
  -> [up to 8 Explore agents in parallel, 8-category checklist per file] -> raw findings
  -> sweep manifest (ALL findings merged)
  -> [council judges] adjudicate + add cross-cutting findings -> ALL findings reported
```

---

## Phase 1: Explorer Sweep

### File Chunking Rules

Sort target files by line count (largest first), then chunk:

| File Size | Batch Size | Rationale |
|-----------|-----------|-----------|
| <= 100 lines | 5 per batch | Small files — explorers can handle many |
| 101–300 lines | 3 per batch | Medium files — moderate depth needed |
| > 300 lines | 1 per batch (solo) | Large files — full attention required |

**Max 8 batches.** If chunking produces more than 8 batches, merge the smallest batches until you have 8. If fewer than 8 batches, use fewer explorers.

### Explorer Prompt Template

Each explorer receives this prompt with its assigned file batch:

```
You are a Deep Audit Explorer. Your job is DISCOVERY — find every concrete issue in
the assigned files. You are NOT a judge; you do not decide severity thresholds or
ship-readiness. Find problems. Be thorough. Be specific.

## Assigned Files

{FILE_LIST}

## Mandatory 8-Category Checklist

For EACH file, you MUST check all 8 categories. Do not skip any category for any file.

1. **Resource Leaks** — Unclosed files/connections/handles, missing defer/finally/cleanup,
   goroutine leaks, listener leaks, temp file accumulation
2. **String Safety** — Unsanitized user input, format string injection, path traversal,
   SQL/command injection, XSS vectors, unsafe interpolation.
   **Boundary with Cat 8:** String Safety covers injection at the data layer (SQL, command, format string).
   HTTP-layer concerns (XSS in HTML output, CORS headers, CSRF tokens) belong to Cat 8.
   Path traversal appears in both: Cat 2 when sanitizing input strings, Cat 8 when serving HTTP file requests.
3. **Dead Code** — Unreachable branches, unused imports/variables/functions, commented-out
   code left behind, feature flags that are always on/off
4. **Hardcoded Values** — Magic numbers, hardcoded paths/URLs/credentials, environment-
   specific values not in config, hardcoded timeouts/limits
5. **Edge Cases** — Nil/null/zero handling, empty collections, boundary values, integer
   overflow, off-by-one, Unicode edge cases, concurrent access
6. **Concurrency** — Data races, missing locks, lock ordering issues, channel misuse,
   deadlock potential, shared state without synchronization
7. **Error Handling** — Swallowed errors, generic catch-all, missing error propagation,
   panic/crash on recoverable errors, unclear error messages
8. **HTTP/Web Security** — XSS vectors (innerHTML, document.write, dangerouslySetInnerHTML),
   path traversal (../ sequences, directory escape), CORS misconfiguration, CSRF tokens missing,
   HTTP response splitting, Content-Type mismatches, missing rate limiting, open redirects,
   SSRF (outbound URL/IP validation), missing security headers (Strict-Transport-Security,
   X-Frame-Options, Content-Security-Policy), credential/token exposure in logs

## Per-File Coverage Certification

For each file, you MUST either:
- Report at least 1 finding, OR
- Explicitly certify all 8 categories clean with a brief reason per category

Do NOT skip a file. Do NOT say "looks fine" without checking each category.

## Output Format

For each file, produce:
1. A category coverage checklist (checked = issue found, certified = explicitly clean)
2. A findings table

### Category Coverage

```
File: {filename}
[x] Resource Leaks — found: unclosed DB connection at line 45
[ ] String Safety — CLEAN: all inputs validated via sanitize() helper
[x] Dead Code — found: unused import "fmt" at line 3
[ ] Hardcoded Values — CLEAN: all values from config package
[x] Edge Cases — found: nil map access at line 78
[ ] Concurrency — CLEAN: single-goroutine function, no shared state
[ ] Error Handling — CLEAN: all errors returned with context wrapping
[ ] HTTP/Web Security — CLEAN: no HTTP handlers, outbound requests, or log statements with credentials in this file
```

### Findings Table

| File | Line | Category | Severity | Description | Evidence |
|------|------|----------|----------|-------------|----------|
| auth.go | 45 | Resource Leaks | high | DB connection opened but never closed in error path | `db.Open()` at L45, return at L52 skips `defer db.Close()` |
| auth.go | 3 | Dead Code | low | Unused import "fmt" | No fmt.* calls in file |
| auth.go | 78 | Edge Cases | high | Nil map access when config missing | `config["key"]` without nil check, panics if config unset |

Severity levels:
- **critical** — Security vulnerability, data loss, crash in production
- **high** — Bug that will manifest under normal usage
- **medium** — Code smell, maintainability issue, minor bug in edge case
- **low** — Style issue, minor dead code, documentation gap

## Rules

- Read each file completely. Do not skim.
- Every finding MUST have a specific line number and evidence quote.
- Do not invent findings. If a category is clean, certify it clean.
- Prefer false negatives over false positives — only report what you can evidence.
- Do NOT assess overall quality or make ship/no-ship recommendations.
```

### Dispatching Explorers

Use the Task tool with `subagent_type: "Explore"` for each batch. Launch all batches in parallel (single message, multiple tool calls):

```
Task(
  subagent_type="Explore",
  description="Sweep batch N of M",
  prompt="<explorer prompt with FILE_LIST filled in>"
)
```

Each explorer writes findings to `.agents/council/sweep-batch-{N}.md`.

---

## Phase 2: Sweep Manifest

After all explorers complete, merge their findings into a single sweep manifest:

**Write to:** `.agents/council/sweep-manifest.md`

```markdown
# Sweep Manifest

**Files Scanned:** {total_file_count}
**Batches:** {batch_count}
**Total Findings:** {finding_count}

## All Findings

| # | File | Line | Category | Severity | Description | Evidence |
|---|------|------|----------|----------|-------------|----------|
| 1 | auth.go | 45 | Resource Leaks | high | DB connection unclosed in error path | `db.Open()` at L45... |
| 2 | ... | ... | ... | ... | ... | ... |

## Category Summary

| Category | Findings | Files Affected |
|----------|----------|----------------|
| Resource Leaks | 3 | 2 |
| String Safety | 1 | 1 |
| Dead Code | 5 | 4 |
| Hardcoded Values | 2 | 2 |
| Edge Cases | 4 | 3 |
| Concurrency | 0 | 0 |
| Error Handling | 3 | 2 |
| HTTP/Web Security | 1 | 1 |

## Clean Certifications

| File | Categories Certified Clean |
|------|---------------------------|
| utils.go | All 8 |
| config.go | Resource Leaks, String Safety, Dead Code, Edge Cases, Concurrency |
```

**No caps.** Include ALL findings from ALL explorers. Do not filter, rank, or truncate.

---

## Phase 3: Council Adjudication

When a sweep manifest exists, inject it into the council packet and shift judges from discovery to adjudication mode.

### Council Injection Text

Add this to the council packet's `context.sweep_manifest`:

```json
{
  "sweep_manifest": {
    "source": "deep-audit-protocol explorer sweep",
    "file": ".agents/council/sweep-manifest.md",
    "finding_count": N,
    "summary": "<first 3000 chars of sweep manifest>"
  }
}
```

### Judge Mode Shift

When `sweep_manifest` is present in the council context, judges operate in **adjudication mode** instead of discovery mode. The judge prompt receives an additional section (see `council/references/agent-prompts.md` for the exact injection text).

In adjudication mode, judges:
1. **Confirm or reject** each sweep finding (with brief rationale)
2. **Reclassify severity** where the explorer got it wrong
3. **Add cross-file findings** that individual explorers couldn't see (architectural issues, inconsistent patterns across files, missing integration points)
4. **Assess overall readiness** considering the full sweep manifest

### Reporting

The final report includes ALL findings — both confirmed sweep findings and judge-added cross-cutting findings. No caps on finding count. If more than 20 findings, group by category in the report.

---

## Flag Behavior

| Flag | Sweep? | Judges | Notes |
|------|--------|--------|-------|
| `/vibe` (default) | No | 2 | Unchanged: lightweight bug-hunt + council |
| `/vibe --quick` | No | 1 (inline) | Unchanged: fast inline check |
| `/vibe --deep` | Yes | 3 | Enhanced: sweep + 3 judges in adjudication mode |
| `/vibe --sweep` | Yes | 2 | New: sweep + 2 judges in adjudication mode |
| `/vibe --sweep recent` | Yes | 2 | Same, targeting recent changes |
| `/post-mortem` | Yes | 3 | Enhanced: sweep before retrospective council |
| `/post-mortem --skip-sweep` | No | 3 | Old behavior: 3 judges, no sweep |
| `/post-mortem --quick` | No | 1 (inline) | Unchanged: fast inline check |
