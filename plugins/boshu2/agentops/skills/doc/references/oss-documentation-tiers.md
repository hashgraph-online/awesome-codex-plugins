# Documentation Tiers

> Prioritized documentation requirements for OSS projects.
> Based on analysis of successful open source projects.

## Overview

Not all documentation is created equal. This tiered approach ensures
critical files are prioritized while allowing progressive enhancement.

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

### Audit Check

```bash
TIER1_SCORE=0
[[ -f LICENSE ]] && ((TIER1_SCORE++))
[[ -f README.md ]] && ((TIER1_SCORE++))
[[ -f CONTRIBUTING.md ]] && ((TIER1_SCORE++))
[[ -f CODE_OF_CONDUCT.md ]] && ((TIER1_SCORE++))
echo "Tier 1: $TIER1_SCORE/4"
```

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

### Audit Check

```bash
TIER2_SCORE=0
[[ -f SECURITY.md ]] && ((TIER2_SCORE++))
[[ -f CHANGELOG.md ]] && ((TIER2_SCORE++))
[[ -f AGENTS.md ]] && ((TIER2_SCORE++))
[[ -d .github/ISSUE_TEMPLATE ]] && ((TIER2_SCORE++))
[[ -f .github/PULL_REQUEST_TEMPLATE.md ]] && ((TIER2_SCORE++))
echo "Tier 2: $TIER2_SCORE/5"
```

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

### Audit Check

```bash
TIER3_SCORE=0
[[ -f docs/QUICKSTART.md ]] && ((TIER3_SCORE++))
[[ -f docs/ARCHITECTURE.md ]] && ((TIER3_SCORE++))
[[ -f docs/CLI_REFERENCE.md ]] && ((TIER3_SCORE++))
[[ -f docs/CONFIG.md ]] && ((TIER3_SCORE++))
[[ -f docs/TROUBLESHOOTING.md ]] && ((TIER3_SCORE++))
[[ -d examples ]] && ((TIER3_SCORE++))
echo "Tier 3: $TIER3_SCORE/6"
```

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

---

## Examples from Beads

Beads (chronicle) demonstrates excellent documentation coverage:

**Tier 1 (all present):**
- LICENSE (MIT)
- README.md (comprehensive overview)
- CONTRIBUTING.md (detailed guide)
- CODE_OF_CONDUCT.md (Contributor Covenant)

**Tier 2 (all present):**
- SECURITY.md (vulnerability reporting)
- CHANGELOG.md (Keep a Changelog format)
- AGENTS.md (AI workflow guide)
- Issue templates (bug report, feature request)
- PR template

**Tier 3 (extensive):**
- docs/QUICKSTART.md
- docs/ARCHITECTURE.md
- docs/CLI_REFERENCE.md (~800 lines)
- docs/CONFIG.md (~615 lines)
- docs/TROUBLESHOOTING.md (~845 lines)
- docs/FAQ.md
- docs/GIT_INTEGRATION.md
- docs/WORKTREES.md
- examples/ directory with multiple patterns

**Key Patterns:**
- Clear separation between user docs and developer docs
- Extensive troubleshooting documentation
- Multiple integration guides (MCP, Claude Code, etc.)
- Active CHANGELOG with detailed version notes
