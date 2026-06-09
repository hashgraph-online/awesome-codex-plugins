---
name: java-dev
description: "Java development. Use for Java, Spring Boot, Maven, Gradle, JPA, Hibernate."
user-invocable: true
allowed-tools: Glob, Read, Grep, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# Java Development

**Announce:** "I'm using the java-dev skill. Following the 4-phase workflow."

## MANDATORY: Read and Follow the Shared Workflow

**You MUST read [workflow.md](../../shared/workflow.md) NOW** and follow ALL 4 phases defined there. The sections below provide Java-specific inputs for each phase.

Read [patterns.md](patterns.md) during Phase 1.

**If you lost workflow.md from context:** Re-read `../../shared/workflow.md` NOW before continuing.

---

## Java-Specific Configuration

### Verification Commands (Phase 1 plan + Phase 3 verify)

WORKFLOW STATE Verification line: `mvn test / gradle test, mvn compile / gradle build`

**Phase 3 Tier A commands:**
- `mvn test` or `gradle test` — run tests
- `mvn compile` or `gradle build` — compilation check
- Check for compiler warnings

**Phase 3 Tier B additional MCP verifications:**
- PostgreSQL MCP → Query DB state before/after
- Legacy DB MCP → Query legacy databases for data verification

### Implementation Rules (Phase 3)

- **Data carrier structure** — Records with CRUD variants per entity (CreateRequest/UpdateRequest/Response), domain-driven packages, composition over deep inheritance
- **Minimize complexity** — efficient streams, HashMap lookups over list scans
- **Preserve compatibility** — Overloaded methods for new params, @JsonProperty for renamed fields, @Deprecated before removal

### Staff Review Configuration (Phase 4)

- **Patterns file path:** Path to this skill's `patterns.md`

---

## Java-Specific Rules

- The compiler catches type errors, not logic bugs or concurrency issues — verification is still mandatory
- Understand Spring Boot auto-configuration before relying on it
- No positive claim without running `mvn test` or `gradle test`

---

## Quality Checklist (Java-Specific)

Add these to the shared workflow's verification checklist:

- [ ] Using Java 21+ features (var, records, switch expressions, pattern matching)
- [ ] Records used for immutable data carriers
- [ ] Constructor injection for all dependencies
- [ ] No raw types — generics used properly
- [ ] Build succeeds without warnings
- [ ] `mvn test` or `gradle test` passes
- [ ] No compiler warnings
