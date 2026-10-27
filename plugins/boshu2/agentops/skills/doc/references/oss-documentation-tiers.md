# Documentation Tiers

> Prioritized documentation requirements for OSS projects.
> Based on analysis of successful open source projects.

## Overview

Not all documentation is created equal. This tiered approach ensures
critical files are prioritized while allowing progressive enhancement.

The [OSS pack](oss-pack.md#audit-and-project-type) audit script checks Tiers 1-3
by file presence. For Tier 3 it counts `docs/QUICKSTART.md`,
`docs/ARCHITECTURE.md`, `docs/CLI_REFERENCE.md` (or `docs/CRD_REFERENCE.md`),
`docs/CONFIG.md`, `docs/TROUBLESHOOTING.md` and an `examples/` directory; it
does not check `docs/FAQ.md`.

---

## Tier 1: Required (Legal + Essential)

**Must have for any public repository.**

| File | Purpose | Template |
|------|---------|----------|
| `LICENSE` | Legal terms for usage | Apache 2.0, MIT, etc. |
| `README.md` | First impression, quick start | Project-type specific |
| `CONTRIBUTING.md` | How to contribute | Fork/PR workflow |
| `CODE_OF_CONDUCT.md` | Community standards | Contributor Covenant |

### Why These Are Required

- **LICENSE**: Without a license, code is "all rights reserved" by default
- **README.md**: First file GitHub displays, defines project identity
- **CONTRIBUTING.md**: Reduces friction for new contributors
- **CODE_OF_CONDUCT.md**: Sets expectations, required by many organizations

---

## Tier 2: Standard (Professional Quality)

**Expected for production-quality projects.**

| File | Purpose | When Critical |
|------|---------|---------------|
| `SECURITY.md` | Vulnerability reporting | Always |
| `CHANGELOG.md` | Version history | Versioned releases |
| `AGENTS.md` | AI assistant context | AI-assisted development |
| `.github/ISSUE_TEMPLATE/` | Structured issue reports | Public issue tracker |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist | Active contributions |

### Why These Matter

- **SECURITY.md**: Private vulnerability disclosure channel
- **CHANGELOG.md**: Users need to know what changed between versions
- **AGENTS.md**: AI assistants (Claude, Copilot) work better with context
- **Issue Templates**: Reduce noise, get structured reports
- **PR Template**: Ensure consistency, remind of checklist items

---

## Tier 3: Enhanced (Comprehensive)

**For mature projects with complex functionality.**

| File | Purpose | Recommended When |
|------|---------|------------------|
| `docs/QUICKSTART.md` | Detailed getting started | Complex setup |
| `docs/ARCHITECTURE.md` | System design | Non-trivial codebase |
| `docs/CLI_REFERENCE.md` | Command documentation | CLI tools |
| `docs/CONFIG.md` | Configuration options | Configurable software |
| `docs/TROUBLESHOOTING.md` | Common issues | Production software |
| `docs/FAQ.md` | Frequently asked questions | Recurring questions |
| `examples/README.md` | Example index | Multiple examples |

### Recommendation Matrix

| Project Characteristic | Recommended Docs |
|------------------------|------------------|
| CLI tool | CLI_REFERENCE.md, QUICKSTART.md |
| Kubernetes operator | ARCHITECTURE.md, CONFIG.md |
| Library | API.md, examples/ |
| Complex config | CONFIG.md, TROUBLESHOOTING.md |
| Large codebase | ARCHITECTURE.md, INTERNALS.md |

---

## Tier 4: Specialized

**Domain-specific documentation.**

| Category | Files |
|----------|-------|
| **API** | `docs/API.md`, OpenAPI spec |
| **Helm** | `docs/VALUES.md`, upgrade guides |
| **Operator** | CRD references, RBAC docs |
| **Protocol** | Wire format, versioning |
| **MCP** | Server setup, tool documentation |

---

## Scoring Guide

| Score Range | Status | Action |
|-------------|--------|--------|
| Tier 1 < 4 | Incomplete | Add missing required files |
| Tier 1 = 4, Tier 2 < 3 | Basic | Add standard files |
| Tier 1 = 4, Tier 2 >= 3 | Standard | Consider Tier 3 |
| All tiers complete | Comprehensive | Maintain and update |

---

## Progressive Enhancement Strategy

### Phase 1: Go Public (Tier 1)

Before making a repo public:
1. Add LICENSE (choose appropriate license)
2. Write README.md with basic info
3. Add CONTRIBUTING.md (fork/PR workflow)
4. Add CODE_OF_CONDUCT.md (Contributor Covenant)

### Phase 2: Attract Contributors (Tier 2)

After initial public release:
1. Add SECURITY.md for vulnerability reports
2. Start CHANGELOG.md for version tracking
3. Add issue/PR templates
4. Create AGENTS.md for AI assistants

### Phase 3: Scale (Tier 3)

As project grows:
1. Split README content into docs/
2. Add troubleshooting for common issues
3. Document architecture for contributors
4. Create comprehensive examples
