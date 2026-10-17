---
name: peer-review-loop
description: >
  Peer Review Ralph Loop — combines Cavekit kits with a Ralph Loop and true cross-model peer review
  using Codex (OpenAI). Claude builds from specs; Codex reviews adversarially.
  Primary path: Codex CLI delegation via codex-review.sh (fast, no MCP overhead).
  Legacy fallback: Codex as MCP server when CLI delegation is unavailable.
  Covers setup, iteration patterns, convergence detection, and completion criteria.
  Triggers: "peer review loop", "ralph loop with codex", "cavekit ralph", "peer review build loop",
  "cross-model loop", "codex peer reviewer", "cavekit to ralph loop"
---

# Peer Review Loop — Cavekit + Ralph Loop + Codex Peer reviewer

Run a Cavekit cavekit through a Ralph Loop where Claude builds and Codex adversarially reviews.
This is the most rigorous automated quality process available: every few iterations, a completely
different model (different training data, different biases, different blind spots) challenges
your implementation.

---

## Why This Works

| Factor | Single-Model Loop | Peer Review Loop |
|--------|-------------------|------------------|
| Blind spots | Same model, same blind spots every iteration | Two models catch different classes of issues |
| Cavekit drift | Builder may silently deviate from cavekit | Peer reviewer checks cavekit compliance explicitly |
| Quality floor | Converges to "good enough for one model" | Converges to "survives cross-examination" |
| Dead ends | May retry failed approaches | Peer reviewer flags repeated patterns |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Ralph Loop                         │
│  (Stop hook feeds same prompt each iteration)        │
│                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  Claude   │───▶│ Build from   │───▶│  Commit    │ │
│  │  (Build)  │    │ cavekit +  │    │  changes   │ │
│  └──────────┘    └──────────────┘    └──────┬─────┘ │
│       ▲                                      │       │
│       │                                      ▼       │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  Fix      │◀──│ Parse        │◀──│  Codex CLI │ │
│  │  findings │    │ findings     │    │  (Review)  │ │
│  └──────────┘    └──────────────┘    └────────────┘ │
│                                                      │
│  Completion: all cavekit requirements met +         │
│              no CRITICAL/HIGH findings               │
└─────────────────────────────────────────────────────┘
```

### Review Invocation: Codex CLI (primary) vs MCP (legacy)

The peer review loop supports two invocation paths:

1. **Codex CLI delegation (primary)** — Uses `scripts/codex-review.sh` which
   calls `codex` directly in `--approval-mode full-auto` with a structured
   review prompt. Faster, no MCP server overhead, findings are parsed and
   appended to `context/impl/impl-review-findings.md` automatically.

2. **MCP server (legacy fallback)** — Configures Codex as an MCP server in
   `.mcp.json`. Claude calls the MCP tool on review iterations. Used only when
   Codex CLI delegation is unavailable (e.g., older Codex versions).

The build script (`setup-build.sh`) auto-detects which path to use: if
`codex-review.sh` is present and `codex` CLI is available, it uses CLI
delegation. Otherwise it falls back to MCP configuration.

---

## Quick Start

```bash
# Basic: implement a cavekit with peer review
/ck:peer-review-loop context/kits/cavekit-auth.md

# With options
/ck:peer-review-loop context/kits/cavekit-api.md --max-iterations 20 --codex-model gpt-5.4-mini

# Review-only mode (review existing code, don't build new)
/ck:peer-review-loop context/kits/cavekit-api.md --review-only

# Review every iteration instead of every 2nd
/ck:peer-review-loop context/kits/cavekit-auth.md --review-interval 1
```

---

## What the Command Does

1. **Validates** the cavekit file exists and Codex CLI is installed
2. **Configures** Codex as an MCP server in `.mcp.json` (if not already configured)
3. **Builds** a Ralph Loop prompt that embeds:
   - The cavekit path and related plan/impl files
   - Instructions to alternate between build and review iterations
   - The peer review prompt template for Codex
   - Completion criteria tied to cavekit acceptance criteria
4. **Starts** the Ralph Loop via the stop hook mechanism

---

## Codex Review Invocation

### Primary: Codex CLI via codex-review.sh

When `codex` CLI is available, the loop delegates review to `scripts/codex-review.sh`
which exposes the `bp_codex_review` function. This runs Codex in `full-auto` mode with
a structured adversarial review prompt, parses findings into a standardized table, and
appends them to `context/impl/impl-review-findings.md`.

```bash
# What the build loop runs on review iterations:
source scripts/codex-review.sh
bp_codex_review --base main
```

The CLI path is faster (no MCP server startup), produces structured findings with
severity levels (P0-P3), and handles fallback gracefully if Codex is unavailable.

### Legacy fallback: Codex MCP Server

When Codex CLI delegation is not available, the command configures Codex as an MCP
server automatically:

```json
{
  "mcpServers": {
    "codex-reviewer": {
      "command": "codex",
      "args": ["mcp-server", "-c", "model=\"gpt-5.4\""]
    }
  }
}
```

Claude calls this MCP server on review iterations to get peer review feedback. The MCP server
exposes Codex as a tool that accepts prompts and returns responses — Claude sends the cavekit +
code diff, Codex returns findings.

### Changing the Codex Model

Use `--codex-model` to specify which OpenAI model Codex should use:

```bash
/ck:peer-review-loop cavekit.md --codex-model gpt-5.4-mini    # faster, cheaper
/ck:peer-review-loop cavekit.md --codex-model gpt-5.4          # default, most capable
```

---

## Iteration Pattern

```
Iteration 1: BUILD  — Read cavekit, implement first requirement
Iteration 2: REVIEW — Call Codex CLI (or MCP fallback), get findings, fix CRITICAL/HIGH
Iteration 3: BUILD  — Continue implementing, address remaining findings
Iteration 4: REVIEW — Call Codex CLI (or MCP fallback) again, new findings on new code
...
Iteration N: BUILD  — All requirements met, all findings fixed
             → outputs <promise>SPEC COMPLETE</promise>
```

The review interval is configurable. Default is every 2nd iteration.
Use `--review-interval 1` for maximum rigor (review every iteration).

---

## Peer Review Findings File

Review findings are tracked in `context/peer-review-findings.md`:

```markdown
# Peer Review Findings

## Latest Review: Iteration 4 — 2026-03-14T10:30:00Z
### Reviewer: Codex (gpt-5.4)

| # | Severity | File | Issue | Status |
|---|----------|------|-------|--------|
| 1 | CRITICAL | src/auth.ts:L42 | Missing input validation on token | FIXED |
| 2 | HIGH | src/auth.ts:L67 | Race condition in session refresh | FIXED |
| 3 | MEDIUM | src/auth.ts:L15 | Unused import | NEW |
| 4 | LOW | src/auth.ts:L3 | Comment typo | WONTFIX |

## History
### Iteration 2
| # | Severity | File | Issue | Status |
|---|----------|------|-------|--------|
| 1 | CRITICAL | src/auth.ts:L20 | SQL injection in login query | FIXED |
```

---

## Completion Criteria

The loop exits when the completion promise is output. The prompt instructs Claude
to ONLY output it when ALL of these are true:

- All cavekit requirements (R-numbers) have been implemented
- All acceptance criteria pass
- No CRITICAL or HIGH peer review findings remain unfixed
- Build passes
- Tests pass
- At least one review iteration completed with no new CRITICAL/HIGH findings

---

## Modes

### Build + Review (default)
Alternates between implementing cavekit requirements and calling Codex for review.
Use for greenfield implementation from a cavekit.

### Review Only (`--review-only`)
Skips building. Each iteration calls Codex to review existing code against the cavekit,
then fixes issues found. Use when code already exists and you want peer review QA.

---

## Prerequisites

1. **Codex CLI installed**: `npm install -g @openai/codex`
2. **OpenAI API key configured**: Codex needs authentication (via `codex login` or env var)
3. **Cavekit context directory**: Cavekit file must exist at the given path
4. **Ralph Loop plugin**: The ralph-loop plugin must be installed (provides the stop hook)

---

## Convergence Signals

The peer review loop has converged when:
- Codex's findings drop to zero or only LOW/MEDIUM severity
- Code diffs between iterations are minimal
- All cavekit requirements confirmed as met by both Claude and Codex

If the loop hits max iterations without converging:
- Check `context/peer-review-findings.md` for persistent issues
- Consider whether the cavekit needs clarification
- Run `/ck:revise` to trace issues back to kits

---

## Cross-References

- **peer-review** — The underlying peer review patterns and prompt templates
- **convergence-monitoring** — How to detect convergence vs ceiling
- **validation-first** — Validation gates that run on every build iteration
- **impl-tracking** — How implementation progress is tracked across iterations
- **Ralph Loop** — The underlying Ralph Loop mechanism
