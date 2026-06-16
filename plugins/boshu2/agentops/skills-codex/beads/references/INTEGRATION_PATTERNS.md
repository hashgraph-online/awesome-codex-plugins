# Integration Patterns with Other Skills


## Contents

- [Task Tools Integration](#task-tools-integration) - Temporal layering pattern
- [writing-plans Integration](#writing-plans-integration) - Detailed implementation plans
- [Cross-Skill Workflows](#cross-skill-workflows) - Using multiple skills together
- [Decision Framework](#decision-framework) - When to use which tool

---

## Task Tools Integration

**Both tools complement each other at different timescales:**

### Temporal Layering Pattern

**Task tools** (short-term working memory - this hour):
- Tactical execution: "Review Section 3", "Expand Q&A answers"
- Present/future tense ("Review", "Expand", "Create")
- Ephemeral: Task list resets when session ends

**Beads** (long-term episodic memory - this week/month):
- Strategic objectives: "Continue work on strategic planning document"
- Key decisions and outcomes in notes field
- Past tense in notes ("COMPLETED", "Discovered", "Blocked by")
- Persistent: Survives compaction and session boundaries

**Key insight**: Task tools = working copy for the current hour. Beads = project journal for the current month.

### The Handoff Pattern

3. **Reach milestone**: Update bead notes with outcomes + context
4. **Session end**: Task list resets, bead survives with enriched notes

**After compaction**: Task list is gone, but bead notes reconstruct what happened.

### Example: Task tools track execution, Beads capture meaning

**Task tools (ephemeral execution view):**
```
Create session tasks:
```

**Corresponding bead notes (persistent context):**
```bash
bd update issue-123 --notes "COMPLETED: Login endpoint with bcrypt password
hashing (12 rounds). KEY DECISION: Using JWT tokens (not sessions) for stateless
auth - simplifies horizontal scaling. IN PROGRESS: Session middleware implementation.
NEXT: Need user input on token expiry time (1hr vs 24hr trade-off)."
```

**What's different**:
- Task tools: Task names (what to do)
- Beads: Outcomes and decisions (what was learned, why it matters)

**Don't duplicate**: Task tools track execution, Beads captures meaning and context.

### When to Update Each Tool

**Update Task tools** (frequently):

**Update Beads** (at milestones):
- Completed a significant piece of work
- Made a key decision that needs documentation
- Hit a blocker that pauses progress
- About to ask user for input
- Session token usage > 70%
- End of session

**Pattern**: Task tools change every few minutes. Beads updates every hour or at natural breakpoints.

### Full Workflow Example

**Scenario**: Implement OAuth authentication (multi-session work)

**Session 1 - Planning**:
```bash
# Create bd issue
br create "Implement OAuth authentication" -t feature -p 0 --design "
JWT tokens with refresh rotation.
See BOUNDARIES.md for bd vs Task tools decision.
"

# Mark in_progress
bd update oauth-1 --status in_progress

# Create session tasks for today's work
Create session tasks:
```

**End of Session 1**:
```bash
# Update bd with outcomes
bd update oauth-1 --notes "COMPLETED: Researched OAuth2 refresh flow. Decided on 7-day refresh tokens.
KEY DECISION: RS256 over HS256 (enables key rotation per security review).
IN PROGRESS: Need to set up test OAuth provider.
NEXT: Configure test provider, then implement token endpoint."

# Task list resets when session ends
```

**Session 2 - Implementation** (after compaction):
```bash
# Read bd to reconstruct context
bd show oauth-1
# See: COMPLETED research, NEXT is configure test provider

# Create fresh session tasks from NEXT
Create session tasks:

# Work proceeds...

# Update bd at milestone
bd update oauth-1 --notes "COMPLETED: Test provider configured, token endpoint implemented.
TESTS: 5 passing (token generation, validation, expiry).
IN PROGRESS: Adding refresh token rotation.
NEXT: Implement rotation, add rate limiting, security review."
```

**For complete decision criteria and boundaries, see:** [BOUNDARIES.md](BOUNDARIES.md)

---

## writing-plans Integration

**For complex multi-step features**, the design field in bd issues can link to detailed implementation plans that break work into bite-sized RED-GREEN-REFACTOR steps.

### When to Create Detailed Plans

**Use detailed plans for:**
- Complex features with multiple components
- Multi-session work requiring systematic breakdown
- Features where TDD discipline adds value (core logic, critical paths)
- Work that benefits from explicit task sequencing

**Skip detailed plans for:**
- Simple features (single function, straightforward logic)
- Exploratory work (API testing, pattern discovery)
- Infrastructure setup (configuration, wiring)

**The test:** If you can implement it in one session without a checklist, skip the detailed plan.

### Using the writing-plans Skill

When design field needs detailed breakdown, reference the **writing-plans** skill:

**Pattern:**
```bash
# Create issue with high-level design
br create "Implement OAuth token refresh" --design "
Add JWT refresh token flow with rotation.
See docs/plans/2025-10-23-oauth-refresh-design.md for detailed plan.
"

# Then use writing-plans skill to create detailed plan
# The skill creates: docs/plans/YYYY-MM-DD-<feature-name>.md
```

**Detailed plan structure** (from writing-plans):
- Bite-sized tasks (2-5 minutes each)
- Explicit RED-GREEN-REFACTOR steps per task
- Exact file paths and complete code
- Verification commands with expected output
- Frequent commit points

**Example task from detailed plan:**
```markdown
### Task 1: Token Refresh Endpoint

**Files:**
- Create: `src/auth/refresh.py`
- Test: `tests/auth/test_refresh.py`

**Step 1: Write failing test**
```python
def test_refresh_token_returns_new_access_token():
    refresh_token = create_valid_refresh_token()
    response = refresh_endpoint(refresh_token)
    assert response.status == 200
    assert response.access_token is not None
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/auth/test_refresh.py::test_refresh_token_returns_new_access_token -v`
Expected: FAIL with "refresh_endpoint not defined"

**Step 3: Implement minimal code**
[... exact implementation ...]

**Step 4: Verify test passes**
[... verification ...]

**Step 5: Commit**
```bash
git add tests/auth/test_refresh.py src/auth/refresh.py
git commit -m "feat: add token refresh endpoint"
```
```

### Integration with bd Workflow

**Three-layer structure**:
1. **bd issue**: Strategic objective + high-level design
2. **Detailed plan** (writing-plans): Step-by-step execution guide
3. **Task tools**: Current task within the plan

**During planning phase:**
1. Create bd issue with high-level design
2. If complex: Use writing-plans skill to create detailed plan
3. Link plan in design field: `See docs/plans/YYYY-MM-DD-<topic>.md`

**During execution phase:**
1. Open detailed plan (if exists)
2. Use Task tools to track current task within plan
3. Update bd notes at milestones, not per-task
4. Close bd issue when all plan tasks complete

**Don't duplicate:** Detailed plan = execution steps. BD notes = outcomes and decisions.

**Example bd notes after using detailed plan:**
```bash
bd update oauth-5 --notes "COMPLETED: Token refresh endpoint (5 tasks from plan: endpoint + rotation + tests)
KEY DECISION: 7-day refresh tokens (vs 30-day) - reduces risk of token theft
TESTS: All 12 tests passing (auth, rotation, expiry, error handling)"
```

### When NOT to Use Detailed Plans

**Red flags:**
- Feature is simple enough to implement in one pass
- Work is exploratory (discovering patterns, testing APIs)
- Infrastructure work (OAuth setup, MCP configuration)
- Would spend more time planning than implementing

**Rule of thumb:** Use detailed plans when systematic breakdown prevents mistakes, not for ceremony.

**Pattern summary**:
- **Simple feature**: bd issue only
- **Complex feature**: bd issue + Task tools
- **Very complex feature**: bd issue + writing-plans + Task tools

---

## Cross-Skill Workflows

### Pattern: Research Document with Strategic Planning

**Scenario**: User asks "Help me write a strategic planning document for Q4"

**Tools used**: bd-issue-tracking + developing-strategic-documents skill

**Workflow**:
1. Create bd issue for tracking:
   ```bash
   br create "Q4 strategic planning document" -t task -p 0
   bd update strat-1 --status in_progress
   ```

2. Use developing-strategic-documents skill for research and writing

3. Update bd notes at milestones:
   ```bash
   bd update strat-1 --notes "COMPLETED: Research phase (reviewed 5 competitor docs, 3 internal reports)
   KEY DECISION: Focus on market expansion over cost optimization per exec input
   IN PROGRESS: Drafting recommendations section
   NEXT: Get exec review of draft recommendations before finalizing"
   ```

4. Task tools track immediate writing tasks:
   ```
   Create session tasks:
   ```

**Why this works**: bd preserves context across sessions (document might take days), skill provides writing framework, Task tools track current work.

### Pattern: Multi-File Refactoring

**Scenario**: Refactor authentication system across 8 files

**Tools used**: bd-issue-tracking + systematic-debugging (if issues found)

**Workflow**:
1. Create epic and subtasks:
   ```bash
   br create "Refactor auth system to use JWT" -t epic -p 0
   br create "Update login endpoint" -t task
   br create "Update token validation" -t task
   br create "Update middleware" -t task
   br create "Update tests" -t task

   # Link hierarchy
   br dep add auth-epic login-1 --type parent-child
   br dep add auth-epic validation-2 --type parent-child
   br dep add auth-epic middleware-3 --type parent-child
   br dep add auth-epic tests-4 --type parent-child

   # Add ordering
   br dep add validation-2 login-1  # validation depends on login
   br dep add middleware-3 validation-2  # middleware depends on validation
   br dep add tests-4 middleware-3  # tests depend on middleware
   ```

2. Work through subtasks in order, using Task tools for each:
   ```
   Current: login-1
   Create session tasks:
   ```

3. Update bd notes as each completes:
   ```bash
   bd close login-1 --reason "Updated to JWT. Tests passing. Backward compatible with session auth."
   ```

4. If issues discovered, use systematic-debugging skill + create blocker issues

**Why this works**: bd tracks dependencies and progress across files, Task tools focus on current file, skills provide specialized frameworks when needed.

---

## Decision Framework

### Which Tool for Which Purpose?

| Need | Tool | Why |
|------|------|-----|
| Track today's execution | Task tools | Lightweight, shows current progress |
| Preserve context across sessions | bd | Survives compaction, persistent memory |
| Detailed implementation steps | writing-plans | RED-GREEN-REFACTOR breakdown |
| Research document structure | developing-strategic-documents | Domain-specific framework |
| Debug complex issue | systematic-debugging | Structured debugging protocol |

### Decision Tree

```
Is this work done in this session?
├─ Yes → Use Task tools only
└─ No → Use bd
    ├─ Simple feature → bd issue + Task tools
    └─ Complex feature → bd issue + writing-plans + Task tools

Will conversation history get compacted?
├─ Likely → Use bd (context survives)
└─ Unlikely → Task tools are sufficient

Does work have dependencies or blockers?
├─ Yes → Use bd (tracks relationships)
└─ No → Task tools are sufficient

Is this specialized domain work?
├─ Research/writing → developing-strategic-documents
├─ Complex debugging → systematic-debugging
├─ Detailed implementation → writing-plans
└─ General tracking → bd + Task tools
```

### Integration Anti-Patterns

**Don't**:
- Duplicate session tasks into bd notes (different purposes)
- Create bd issues for single-session linear work (use Task tools)
- Put detailed implementation steps in bd notes (use writing-plans)
- Update bd after every task completion (update at milestones)
- Use writing-plans for exploratory work (defeats the purpose)

**Do**:
- Update bd when changing tools or reaching milestones
- Use Task tools as "working copy" of bd's NEXT section
- Link between tools (bd design field → writing-plans file path)
- Choose the right level of formality for the work complexity

---

## Summary

**Key principle**: Each tool operates at a different timescale and level of detail.

- **Task tools**: Minutes to hours (current execution)
- **bd**: Hours to weeks (persistent context)
- **writing-plans**: Days to weeks (detailed breakdown)
- **Other skills**: As needed (domain frameworks)

**Integration pattern**: Use the lightest tool sufficient for the task, add heavier tools only when complexity demands it.

**For complete boundaries and decision criteria, see:** [BOUNDARIES.md](BOUNDARIES.md)
