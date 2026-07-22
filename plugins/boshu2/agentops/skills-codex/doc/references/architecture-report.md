
<!-- TOC: Core | Prompt | Quick Start | Modes | Anti-Patterns | Subagent | References -->

# Codebase Report

> **Core Insight:** Understanding is ephemeral. Documents survive context compaction.

## The Problem

You explore a codebase, build a mental model, then context compacts. This skill produces **reusable artifacts** that survive.

**Differs from codebase-archaeology:** Archaeology = understanding. This = producing a document.

---

## THE EXACT PROMPT

```
Produce a Comprehensive Technical Architecture Report for this codebase:

1. Executive summary (what is it, key stats)
2. Entry points (main, routes, handlers)
3. Key types (3-5 core domain objects)
4. Data flow (input → processing → output)
5. External dependencies (DBs, APIs, critical libs)
6. Configuration (env, files, CLI, precedence)
7. Test infrastructure

Include file:line references. Output as markdown I can reference later.
```

---

## Quick Start

No scaffold script ships with this skill — explore manually, then fill the
template from the structure below:

```bash
cat README.md AGENTS.md 2>/dev/null | head -200
ls src/ lib/ cmd/ pkg/ 2>/dev/null
rg "fn main|func main|if __name__" --type-add 'all:*.*' -l | head -5
```

---

## Report Modes

| Mode | Time | Depth | Use When |
|------|------|-------|----------|
| **Quick Scan** | 10 min | Entry + types + flow | Orientation, PR context |
| **Standard** | 30 min | Full template | Onboarding, docs |
| **Deep Dive** | 1+ hr | + diagrams, all paths | Audits, major decisions |

### Quick Scan (Minimal)

```
Quick architecture overview:
- What is it? (1 sentence)
- Entry points (list)
- 3 key types
- Main data flow (1 diagram)
Keep under 150 lines.
```

---

## Output Structure

```markdown
# [Project] - Technical Architecture Report

## Executive Summary
[What + stats in 3 lines]

## Entry Points
| Entry | Location | Purpose |
|-------|----------|---------|

## Key Types
| Type | Location | Purpose |
|------|----------|---------|

## Data Flow
[ASCII diagram + 2-sentence description]

## External Dependencies
| Dependency | Purpose | Critical? |
|------------|---------|-----------|

## Configuration
| Source | Priority | Example |
|--------|----------|---------|

## Test Infrastructure
| Type | Location | Count |
|------|----------|-------|
```


---

## Delegation Pattern

For large codebases, delegate exploration:

```
Use the codebase-explorer subagent to explore this codebase.
Return structured findings, then I'll compile the final report.
```

The subagent explores in read-only mode and returns findings in report-ready format.

---

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Stop at understanding | Always produce artifact |
| Vague descriptions | Include `file:line` refs |
| Skip data flow | Trace end-to-end |
| One giant report | Match depth to purpose |
| Assume knowledge persists | Write it down now |

---

## Integration

### With New Projects

On a fresh clone, start the report by hand: copy the section structure from
this reference into `ARCHITECTURE.md`, then fill it from manual exploration
(Quick Start above). There is no auto-scaffold script.

### With Other Skills

| After using... | Consider... |
|----------------|-------------|
| codebase-archaeology | Producing this report to persist findings |
| multi-pass-bug-hunting | Adding "Known Issues" section |
| cross-project-pattern-extraction | Noting patterns in "Notes & Gotchas" |

---

## References

| Topic | File |
|-------|------|

## Scripts

Shipped with the doc skill (`skills/doc/scripts/`):

| Script | Purpose |
|--------|---------|
| `scripts/audit-oss-docs.sh` | Audit OSS documentation coverage by tier |
| `scripts/validate.sh` | Self-check the doc skill package structure |

## Subagents

| Subagent | Purpose |
|----------|---------|
| `subagents/explorer.md` | Parallel exploration for large codebases |
# Example Architecture Reports

## Example 1: beads_rust (CLI Tool)

Real report from a local-first issue tracker:

```markdown
# beads_rust - Technical Architecture Report

## Executive Summary

**beads_rust** is a local-first issue tracker CLI optimized for AI coding agents. Built with Rust 1.85, Edition 2024.

**Key Statistics:**
- ~3,500 lines of code across 12 modules
- Language: Rust 1.85 (Edition 2024)
- Key dependencies: clap, rusqlite, serde, chrono, anyhow

---

## Entry Points

| Entry | Location | Purpose |
|-------|----------|---------|
| CLI main | `src/main.rs:1` | Parses args via clap, dispatches to commands |
| Commands | `src/commands/*.rs` | Individual command implementations |

---

## Key Types

| Type | Location | Purpose |
|------|----------|---------|
| `Issue` | `src/model.rs:15` | Core domain object - the issue/bead |
| `Storage` | `src/storage.rs:1` | SQLite persistence layer |
| `Cli` | `src/main.rs:20` | clap-derived CLI structure |
| `Config` | `src/config.rs:1` | Runtime configuration |

---

## Data Flow

```
CLI Input (br create "title")
     │
     ▼
Clap Parser ─── validates args
     │
     ▼
Command Handler ─── orchestrates
     │
     ▼
Storage Layer ─── SQLite + JSONL sync
     │
     ▼
Output (JSON/table/confirmation)
```

**Happy Path:** User runs `br create "Fix bug"` → clap parses → CreateCommand runs → Storage inserts to SQLite → JSONL sync triggered → ID printed.

---

## External Dependencies

| Dependency | Purpose | Critical? |
|------------|---------|-----------|
| rusqlite (bundled SQLite) | Local persistence | Yes |
| serde/serde_json | Serialization | Yes |
| clap | CLI parsing | Yes |
| chrono | Timestamps | Yes |
| rich_rust | Terminal formatting | No |

---

## Configuration

| Source | Example | Priority |
|--------|---------|----------|
| Env var | `BR_DB_PATH=/path/to/db` | Highest |
| Config file | `.beads/config.yaml` | Medium |
| Default | `.beads/beads.db` | Lowest |

---

## Test Infrastructure

| Type | Location | Count |
|------|----------|-------|
| Unit tests | `src/*.rs` (inline) | ~40 |
| Integration | `tests/` | ~15 |
| Benchmarks | `benches/storage_perf.rs` | 1 suite |

**Running Tests:**
```bash
cargo test              # All tests
cargo test --lib        # Unit only
cargo bench             # Performance benchmarks
```

---

## Notes & Gotchas

- JSONL sync is one-way (SQLite → JSONL) for git compatibility
- Issue IDs are base36 encoded for compactness
- `--robot` flag outputs JSON for agent consumption
```

---

## Example 2: Web Service (Express/TypeScript)

```markdown
# api-gateway - Technical Architecture Report

## Executive Summary

**api-gateway** is an Express.js API gateway handling auth, rate limiting, and request routing. Built with TypeScript 5.3.

**Key Statistics:**
- ~2,100 lines across 8 modules
- Language: TypeScript 5.3
- Key dependencies: express, passport, redis, zod, pino

---

## Entry Points

| Entry | Location | Purpose |
|-------|----------|---------|
| Server boot | `src/index.ts:1` | Express app initialization |
| Router setup | `src/routes/index.ts:1` | Route registration |
| Middleware chain | `src/middleware/index.ts:1` | Auth, rate limit, logging |

---

## Key Types

| Type | Location | Purpose |
|------|----------|---------|
| `User` | `src/types/user.ts:5` | Authenticated user shape |
| `ApiRequest` | `src/types/request.ts:1` | Extended Express Request |
| `RateLimitConfig` | `src/config/limits.ts:10` | Per-route rate limits |

---

## Data Flow

```
HTTP Request
     │
     ▼
Express Router ─── path matching
     │
     ▼
Middleware Stack ─── auth, rate limit, validation
     │
     ▼
Route Handler ─── business logic
     │
     ▼
Upstream Service ─── proxy to microservices
     │
     ▼
Response Transform ─── standardize format
     │
     ▼
HTTP Response
```

---

## External Dependencies

| Dependency | Purpose | Critical? |
|------------|---------|-----------|
| Redis | Rate limiting, sessions | Yes |
| PostgreSQL | User data | Yes |
| Upstream APIs | Backend services | Yes |
| Sentry | Error tracking | No |

---

## Configuration

| Source | Example | Priority |
|--------|---------|----------|
| Env var | `DATABASE_URL`, `REDIS_URL` | Highest |
| Config file | `config/production.json` | Medium |
| Default | `config/default.json` | Lowest |

Uses `node-config` for layered configuration.
```

---

## Quick vs Deep Reports

| Report Type | Time | Depth | Use When |
|-------------|------|-------|----------|
| **Quick Scan** | 10 min | Entry points + key types | Orientation, PR review |
| **Standard** | 30 min | Full template | Onboarding, documentation |
| **Deep Dive** | 1+ hr | + sequence diagrams, all flows | Architecture review, audits |

### Quick Scan Prompt

```
Give me a quick architecture overview of this codebase:
- What is it?
- Entry points (main, routes, handlers)
- 3 key types
- Main data flow

Keep it under 200 lines.
```

### Deep Dive Additions

For deep reports, also include:
- Sequence diagrams for critical flows
- All error handling paths
- Performance characteristics
- Security considerations
- Technical debt inventory
# Comprehensive Technical Architecture Report Template

Copy this template and fill in the sections.

---

# [Project Name] - Technical Architecture Report

## Executive Summary

**[Project]** is a [CLI tool / web service / library] that [main purpose]. Built with [language] [version].

**Key Statistics:**
- ~X,XXX lines of code across Y modules
- Language: [Rust 1.XX / TypeScript 5.X / Python 3.XX]
- Key dependencies: [dep1], [dep2], [dep3], [dep4], [dep5]

---

## Entry Points

| Entry | Location | Purpose |
|-------|----------|---------|
| CLI main | `src/main.rs:15` | Parses args via clap, dispatches commands |
| HTTP router | `src/routes/mod.rs:1` | Sets up axum/express routes |
| [Add more] | `path:line` | Description |

---

## Key Types

| Type | Location | Purpose |
|------|----------|---------|
| `TypeName` | `src/model.rs:10` | Core domain object representing X |
| `Config` | `src/config.rs:5` | Runtime configuration loaded from file/env |
| `Storage` | `src/storage.rs:1` | Persistence layer abstraction |
| [Add more] | `path:line` | Description |

---

## Data Flow

```
[Input Source]
     │
     ▼
[Entry Point] ─── parses/validates
     │
     ▼
[Handler/Controller] ─── orchestrates
     │
     ▼
[Core Domain Logic] ─── business rules
     │
     ▼
[Storage/External] ─── persists/calls
     │
     ▼
[Output/Response]
```

**Happy Path Description:**
1. User invokes [command/endpoint]
2. [Entry] parses input and creates [Type]
3. [Handler] calls [Core] which processes...
4. Result is [stored/returned/displayed]

---

## External Dependencies

| Dependency | Purpose | Critical? |
|------------|---------|-----------|
| SQLite (rusqlite) | Local persistence | Yes |
| reqwest | HTTP client for external APIs | No |
| tokio | Async runtime | Yes |
| serde | Serialization | Yes |
| [Add more] | Purpose | Yes/No |

---

## Configuration

| Source | Location/Example | Priority |
|--------|------------------|----------|
| Environment var | `APP_CONFIG=/path/to/config.toml` | 1 (highest) |
| Config file | `~/.config/app/config.toml` | 2 |
| CLI flag | `--config /path` | 3 |
| Default | Hardcoded in `src/config.rs:50` | 4 (lowest) |

**Key Config Options:**
- `option_name`: Description, default value
- `another_option`: Description, default value

---

## Module Structure

```
src/
├── main.rs          # Entry point, CLI setup
├── config.rs        # Configuration loading
├── model/           # Core domain types
│   ├── mod.rs
│   └── types.rs
├── handlers/        # Request/command handlers
│   └── mod.rs
├── storage/         # Persistence layer
│   ├── mod.rs
│   └── sqlite.rs
└── utils/           # Shared utilities
    └── mod.rs
```

---

## Test Infrastructure

| Type | Location | Count |
|------|----------|-------|
| Unit tests | `src/**/*.rs` (inline) | ~XXX |
| Integration | `tests/integration/` | ~XX |
| E2E | `tests/e2e/` | ~X |

**Running Tests:**
```bash
cargo test              # All tests
cargo test --lib        # Unit only
cargo test --test e2e   # E2E only
```

---

## Error Handling

- Error type: `src/error.rs` - uses thiserror/anyhow
- Propagation: `?` operator, Result<T, Error>
- User-facing: Formatted messages in CLI/API responses

---

## Logging

- Framework: tracing / log / env_logger
- Levels: Configurable via `RUST_LOG` or `--verbose`
- Output: stderr (CLI), structured JSON (service)

---

## Notes & Gotchas

- [Any non-obvious behavior]
- [Known limitations]
- [Areas needing improvement]

---

*Generated: [Date]*
*By: [Agent/Human]*
