---
name: documentation-inversion
description: >
  Inverts the traditional documentation flow from code-to-wiki-for-humans (which rots) into
  code-to-CLAUDE.md-to-skills-for-agents (which stays current). Each module gets a machine-readable
  CLAUDE.md, navigation skills teach agents how to explore libraries, and plugins package skills for
  on-demand loading. Documentation structured for machine consumption -- hierarchical, cross-referenced,
  with clear entry points -- rather than narrative human reading. This is a fundamental shift: build
  documentation for agents, not people.
  Triggers: "documentation inversion", "skills as docs", "living documentation",
  "docs for agents", "machine-readable docs", "agent-first documentation".
---

# Documentation Inversion

Traditional documentation drifts out of sync because it lives separately from the code. Documentation inversion places guidance directly in the codebase, structured for agent consumption, so that AI can explore the source and find current information on demand.

## Core Principle

> **Structure documentation for programmatic navigation -- hierarchical, cross-referenced, with
> explicit entry points -- so that AI agents can find what they need without human guidance.**

Traditional documentation assumes a human reader who will browse, search, and interpret context.
Agent-first documentation assumes a machine reader that needs: explicit entry points, structured
hierarchies, cross-references it can follow programmatically, and guidance on what to explore next.

---

## The Problem: Traditional Documentation Rots

### Traditional Flow

```
Developer ships a feature → Writes a wiki article explaining it
                                      ↓
                               Weeks or months elapse
                                      ↓
                               Another developer refactors the feature
                                      ↓
                               The wiki article is never revised
                                      ↓
                               A third developer (or an agent) follows the stale article
                                      ↓
                               Incorrect assumptions, wasted effort, subtle bugs
```

**Why it rots:**
- Documentation is a second-class artifact -- the incentive is to ship code, not update docs
- The audience (humans) may not notice staleness until they hit a problem
- There is no automated validation that docs match code
- Docs live in a separate system (wiki, Notion) disconnected from the codebase
- Nobody owns documentation maintenance as a primary responsibility

### The Cost of Rot

- New team members learn wrong patterns from stale docs
- AI agents given stale docs produce code based on outdated assumptions
- Time spent debugging issues caused by following outdated guidance
- Tribal knowledge accumulates in chat, not in any durable format

---

## The Solution: Inverted Documentation Flow

### Inverted Flow

```
Developer modifies a module → Updates the co-located CLAUDE.md in the same PR
                                       ↓
                                Navigation skill describes HOW to explore, not WHAT exists
                                       ↓
                                Plugin bundles skills so agents can load them on demand
                                       ↓
                                Agent enters the module → loads skill → reads live source code
                                       ↓
                                Guidance stays accurate because the source itself is the authority
```

**Why it stays current:**
- CLAUDE.md files live *in the codebase*, next to the code they describe
- They are loaded automatically by AI agents when entering a directory
- Skills teach agents *how to explore*, not *what the code currently does* -- so they stay
  accurate even as implementation details change
- The agent reads current source code, guided by the skill -- the source is the documentation
- Code review can enforce CLAUDE.md updates alongside code changes

---

## Implementation Pattern

### Step 1: Each Module Gets a CLAUDE.md

Place a `CLAUDE.md` file at the root of each significant module, library, or directory.

**What goes in a CLAUDE.md:**

```markdown
# {Module Name}

## Purpose
{One paragraph: what this module does and why it exists}

## Entry Points
- `src/index.ts` -- Public API surface. Start here for understanding exports.
- `src/core/engine.ts` -- Core logic. Start here for understanding internals.

## Architecture
{Brief description of how the module is structured internally}

### Key Files
| File | Responsibility |
|------|---------------|
| `src/index.ts` | Public API, re-exports |
| `src/core/engine.ts` | Core processing engine |
| `src/core/types.ts` | Shared type definitions |
| `src/utils/helpers.ts` | Utility functions |

## Conventions
- {Naming conventions specific to this module}
- {Error handling patterns}
- {Testing patterns}

## Dependencies
- `{dependency-a}` -- Used for {purpose}
- `{dependency-b}` -- Used for {purpose}

## Cross-References
- See `../shared/CLAUDE.md` for shared utilities
- See `../api/CLAUDE.md` for the API layer that consumes this module
```

**Key properties of a good CLAUDE.md:**
- **Hierarchical:** Organized as a tree the agent can navigate level by level
- **Cross-referenced:** Links to related CLAUDE.md files in other modules
- **Entry-point focused:** Tells the agent *where to start*, not *everything that exists*
- **Convention-documenting:** Captures patterns the agent should follow when modifying code
- **Brief:** Under 100 lines. Details live in the code itself.

### Step 2: Create Navigation Skills

A navigation skill teaches the agent *how to explore* a library or module. It does not
describe the library's current state -- it describes the *process* for understanding it.

**Navigation Skill Template:**

```markdown
---
name: {library-name}-navigation
description: >
  Teaches the agent how to navigate and understand the {library-name} library.
  Triggers: "{library-name}", "how does {library-name} work",
  "understand {library-name}".
---

# Navigating {Library Name}

## Quick Orientation
1. Read `{root}/CLAUDE.md` for purpose and entry points
2. Read `{root}/src/index.ts` for the public API surface
3. Read `{root}/src/core/types.ts` for core type definitions

## Understanding the Architecture
1. Start with the entry point identified in CLAUDE.md
2. Trace the main flow: {describe the primary call path}
3. Key abstractions: {list the 3-5 most important interfaces/classes}

## Common Tasks

### Adding a New Feature
1. Define types in `src/core/types.ts`
2. Implement core logic in `src/core/`
3. Export from `src/index.ts`
4. Add tests in `tests/`

### Fixing a Bug
1. Identify the failing test or behavior
2. Trace from the public API inward
3. Core logic is in `src/core/engine.ts`
4. Edge cases are typically in `src/utils/helpers.ts`

### Understanding a Specific Feature
1. Search for the feature name in `src/core/`
2. Read the test file for that feature -- tests document behavior
3. Check CLAUDE.md for any conventions specific to that area

## Anti-Patterns to Avoid
- {Pattern to avoid and why}
- {Pattern to avoid and why}
```

**Why skills work better than static docs:**
- The skill tells the agent *what to do*, not what the code is
- The agent then reads the *current* source code to understand what the code is
- The process described in the skill remains valid even as the code changes
- It is a recipe, not a snapshot

### Step 3: Package as a Plugin

Bundle related navigation skills into a Claude Code plugin:

```
{library-name}-docs/
├── plugin.json
└── skills/
    ├── navigation/
    │   └── SKILL.md          # How to navigate the library
    ├── contributing/
    │   └── SKILL.md          # How to contribute to the library
    └── troubleshooting/
        └── SKILL.md          # How to debug common issues
```

**plugin.json:**
```json
{
  "name": "{library-name}-docs",
  "description": "Agent-first documentation for {library-name}",
  "version": "1.0.0"
}
```

### Step 4: Agent Loads On Demand

When an agent encounters the library:
1. The plugin's skills appear in the agent's available skill set
2. Agent loads the navigation skill when it needs to work with the library
3. Skill guides the agent to read CLAUDE.md files and explore current source
4. Agent builds understanding from current code, not stale documentation

---

## The Hierarchy: Three Levels of Agent Documentation

```
Level 1: CLAUDE.md files (per-directory, auto-loaded)
    ↓
Level 2: Navigation skills (per-library, loaded on demand)
    ↓
Level 3: Plugin packages (distributable, installable)
```

### Level 1: CLAUDE.md Files

- **Scope:** One directory or module
- **Loaded:** Automatically when the agent enters the directory
- **Content:** Purpose, entry points, conventions, cross-references
- **Maintained by:** The team that owns the module
- **Update trigger:** Code review -- CLAUDE.md changes alongside code changes

### Level 2: Navigation Skills

- **Scope:** One library or subsystem (may span multiple directories)
- **Loaded:** On demand when the agent needs to work with the library
- **Content:** Exploration process, common tasks, anti-patterns
- **Maintained by:** The team or developer who created the skill
- **Update trigger:** When the library's architecture changes (not every code change)

### Level 3: Plugin Packages

- **Scope:** A distributable collection of skills for a library or framework
- **Loaded:** Installed into a project, then skills load on demand
- **Content:** Multiple skills covering navigation, contributing, troubleshooting
- **Maintained by:** The library maintainers or community
- **Update trigger:** Major version changes or new skill additions

---

## Designing CLAUDE.md for Machine Consumption

### Structure for Machines, Not Narratives

**Bad (human-narrative style):**
```markdown
This module was originally created in 2023 to handle user authentication.
Over time, we've added OAuth support, session management, and rate limiting.
The main file you'll want to look at is auth.ts, which contains most of the
logic. There's also a helpers file with some utility functions.
```

**Good (machine-structured style):**
```markdown
# Auth Module

## Purpose
User authentication: login, logout, session management, OAuth, rate limiting.

## Entry Points
- `src/auth.ts` -- Core auth logic (login, logout, verify)
- `src/oauth.ts` -- OAuth provider integrations
- `src/session.ts` -- Session management
- `src/rate-limit.ts` -- Rate limiting middleware

## Key Types
- `AuthUser` in `src/types.ts` -- Authenticated user object
- `Session` in `src/types.ts` -- Session state
- `OAuthProvider` in `src/oauth.ts` -- Provider interface

## Conventions
- All auth functions return `Result<T, AuthError>` -- never throw
- Sessions are stored in Redis -- see `src/session.ts` for connection setup
- Rate limits are per-IP by default -- see `src/rate-limit.ts` for config
```

### Key Differences

| Dimension | Human-Oriented | Agent-Oriented |
|-----------|----------------|----------------|
| Layout | Flowing paragraphs and narrative arcs | Labeled sections, bullet lists, and tables |
| Starting points | Buried in prose ("you'll want to look at...") | Dedicated "Entry Points" section with exact file paths |
| Type information | Woven into explanatory text | Enumerated with source locations |
| Historical context | Prominent (gives humans background) | Absent (agents only need current state) |
| Coding standards | Scattered across wikis or tribal knowledge | Stated as explicit rules inside the CLAUDE.md |
| Links to related docs | Vague ("check the API docs") | Precise (`../api/CLAUDE.md#authentication`) |

---

## CLAUDE.md Hierarchy and Inheritance

CLAUDE.md files are hierarchical -- an agent entering a directory loads the CLAUDE.md from
that directory AND all parent directories up to the project root.

```
project/
├── CLAUDE.md                    # Project-wide conventions (loaded everywhere)
├── src/
│   ├── CLAUDE.md                # Source code conventions (loaded in src/ and below)
│   ├── auth/
│   │   ├── CLAUDE.md            # Auth module specifics (loaded in auth/ and below)
│   │   └── oauth/
│   │       └── CLAUDE.md        # OAuth specifics (loaded only in oauth/)
│   └── api/
│       └── CLAUDE.md            # API module specifics
└── tests/
    └── CLAUDE.md                # Testing conventions
```

**When an agent works in `src/auth/oauth/`**, it loads:
1. `project/CLAUDE.md` -- project-wide conventions
2. `project/src/CLAUDE.md` -- source code conventions
3. `project/src/auth/CLAUDE.md` -- auth module conventions
4. `project/src/auth/oauth/CLAUDE.md` -- OAuth-specific conventions

**Use this hierarchy intentionally:**
- Project root: language, build commands, Git conventions, overall architecture
- `src/`: coding conventions, import patterns, error handling patterns
- Module level: module-specific entry points, types, dependencies
- Sub-module level: only when there are sub-module-specific conventions

---

## Migration Path: From Wiki to Inverted Docs

### Phase 1: Add CLAUDE.md Files (1-2 days)

1. Identify the 5-10 most important modules in the codebase
2. Create a CLAUDE.md for each with: purpose, entry points, key files, conventions
3. Add a root CLAUDE.md with project-wide conventions
4. **Do not delete the wiki yet** -- CLAUDE.md files supplement it initially

### Phase 2: Create Navigation Skills (1-2 days)

1. For each major library or subsystem, create a navigation skill
2. Focus on the exploration process, not the current state
3. Package skills into a plugin
4. Test: give the agent a task in each library area and verify it loads the skill

### Phase 3: Enforce Co-Location (Ongoing)

1. Add to code review checklist: "Does this change need a CLAUDE.md update?"
2. When new modules are created, require a CLAUDE.md as part of the PR
3. When existing docs are found to be stale, update the CLAUDE.md (not the wiki)
4. Gradually, the CLAUDE.md files become the authoritative source

### Phase 4: Deprecate the Wiki (When Ready)

1. Audit: for each wiki page, verify the information exists in CLAUDE.md files or skills
2. Archive the wiki (do not delete -- it may have historical context worth preserving)
3. Redirect documentation questions to: "Read the CLAUDE.md in the relevant directory"

---

## Measuring Documentation Health

### Staleness Indicators

| Signal | Meaning |
|--------|---------|
| CLAUDE.md not updated in 6+ months but code changed significantly | Documentation may be stale |
| Agent frequently ignores CLAUDE.md guidance | Guidance may be outdated or unhelpful |
| Agent asks clarifying questions about a module that has a CLAUDE.md | CLAUDE.md is missing key information |
| New team members still rely on tribal knowledge | CLAUDE.md files are incomplete |

### Health Metrics

- **Coverage:** What percentage of significant modules have a CLAUDE.md?
- **Freshness:** When was each CLAUDE.md last updated relative to its module's last code change?
- **Usefulness:** Do agents produce better output when CLAUDE.md files are present?
- **Completeness:** Does each CLAUDE.md have: purpose, entry points, key files, conventions?

---

## Anti-Patterns

### 1. CLAUDE.md as a Code Dump
**Problem:** CLAUDE.md lists every file and function in the module.
**Fix:** Focus on entry points and navigation, not exhaustive inventory. The agent can
read the directory listing itself.

### 2. Narrative Prose Instead of Structure
**Problem:** CLAUDE.md reads like a blog post about the module's history.
**Fix:** Use tables, lists, and labeled sections. Agents parse structure, not stories.

### 3. Duplicating Code Comments
**Problem:** CLAUDE.md repeats what is already in code comments and docstrings.
**Fix:** CLAUDE.md should describe the *module-level* view -- architecture, conventions,
entry points. Code comments handle the *function-level* view.

### 4. Never Updating CLAUDE.md
**Problem:** CLAUDE.md is written once and never touched again.
**Fix:** Make CLAUDE.md updates part of the code review process. If you changed the
module's architecture, update the CLAUDE.md.

### 5. One Giant CLAUDE.md at the Root
**Problem:** All documentation is in a single root CLAUDE.md file.
**Fix:** Use the hierarchy. Root CLAUDE.md has project-wide conventions; each module
has its own CLAUDE.md with module-specific guidance. This mirrors progressive disclosure.

---

## Integration with SDD

Documentation inversion is a natural extension of SDD's context architecture:

| SDD Concept | Documentation Inversion Counterpart |
|------------|-----------------------------------|
| Context directory structure (specs/, plans/, impl/) | Per-module CLAUDE.md files co-located with source |
| Progressive disclosure (index file points to detail files) | CLAUDE.md hierarchy cascading from project root to leaf modules |
| Specifications as the source of truth | CLAUDE.md as the authoritative guidance artifact for each module |
| Skills encoding reusable procedures | Navigation skills encoding reusable exploration workflows |
| Plugins as a distribution mechanism | Documentation plugins bundling skills for installation into other projects |

The key insight from SDD applies directly: **strong documentation enables agents to orient
themselves in unfamiliar code and contribute meaningfully without step-by-step human direction.**

---

## Cross-References

- **context-architecture** -- The progressive disclosure pattern that CLAUDE.md hierarchy implements
- **methodology** -- How documentation inversion fits into the broader Cavekit lifecycle
- **spec-writing** -- Specs and CLAUDE.md files share the same structural principles
- **brownfield-adoption** -- When adopting SDD on an existing codebase, CLAUDE.md files are step 1
- **impl-tracking** -- Implementation tracking documents are a form of inverted documentation
