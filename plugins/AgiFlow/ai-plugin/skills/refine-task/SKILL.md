---
name: refine-task
description: "Refine a task into a complete, autonomous-ready spec with SMART acceptance criteria, technical context, and AI-readiness checks. Use when a task is vague or keeps getting rejected. Invoked as /agiflow:refine-task <task>. Uses get_task, update_task, list_tasks, create_task_comment, list_artifacts."
tags:
  - agiflow
  - mcp
  - refinement
  - acceptance-criteria
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/refineTask.md
---

> Invoked as `/agiflow:refine-task`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:refine-task <task-slug-or-id>` - Refine specific task
- `/agiflow:refine-task` - List and select from available tasks to refine

**Examples**:

- `/agiflow:refine-task DXX-2` (using slug)
- `/agiflow:refine-task 01K8FABMNEJG1XTA9JGHSNFV40` (using ID)
- `/agiflow:refine-task` (interactive selection)

---

**Purpose**
Refine task descriptions to provide sufficient context for AI agents to work autonomously. Well-refined tasks enable agents to understand scope, constraints, and expected outcomes without requiring human clarification.

**Guardrails**

- Refine only the task scope - do not expand or reduce the original intent.
- Ensure all required context is explicitly documented, not implied.
- Acceptance criteria must be concrete, measurable, and verifiable by an agent.
- Identify and resolve ambiguities before marking task as refined.

If a task slug/id is provided, load it with `get_task`; otherwise list available tasks with `list_tasks` for selection.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**
Track these steps as TODOs and complete them one by one.

## 1. Task Selection & Loading

**If task slug/id NOT provided:**

1. Use `list_tasks` MCP tool to show tasks needing refinement:
   - Filter by `status: "Planning"` or `status: "Todo"` for tasks not yet started
   - Look for tasks with minimal descriptions or vague acceptance criteria
   - Display: slug, title, priority, acceptance criteria count
2. Ask user to select which task to refine.
3. Once user selects, proceed with the selected task slug/id.

**If task slug/id IS provided:** 4. Use `get_task` MCP tool with the provided slug/id to retrieve:

- Task: title, description, priority, status, acceptance criteria
- Comments: Any clarifications or discussions
- Work unit context: If part of a work unit, understand the broader scope

5. Review the task to identify refinement needs:
   - Is the description clear and complete?
   - Are acceptance criteria specific and measurable?
   - Are dependencies and constraints documented?
   - Can an AI agent work on this without asking questions?

## 2. Analyze Context Requirements

6. Determine what context an AI agent would need:

   **Technical Context:**
   - Which files/modules are affected?
   - What existing patterns should be followed?
   - Are there related implementations to reference?

   **Business Context:**
   - What problem does this solve?
   - Who is the end user or beneficiary?
   - What are the success metrics?

   **Constraints:**
   - Performance requirements?
   - Security considerations?
   - Compatibility requirements?
   - Dependencies on other tasks?

7. Use codebase exploration to gather missing context:
   - Search for related files and patterns
   - Identify existing conventions
   - Find relevant documentation

## 3. Refine Task Description

8. Update task description via `update_task` to include:

   **Structure:**

   ```markdown
   ## Overview

   [1-2 sentences explaining the goal and why it matters]

   ## Skills

   [List skill names the executing agent should load before working on this task.
   Match skills to the task domain: e.g. `backend-development` for API work,
   `web-app-development` for frontend features, `react-native-development` for native UI,
   `unit-testing` / `integration-testing` / `e2e-testing` for test tasks,
   `frontend-design` for visual polish, `drizzle-migration` for schema changes, etc.
   Only include skills that are directly relevant to the implementation.]

   ## Technical Context

   - Related files: `path/to/file.ts`, `path/to/other.ts`
   - Pattern to follow: [reference existing implementation if applicable]
   - Dependencies: [list any prerequisite tasks or external dependencies]

   ## Implementation Notes

   [Specific guidance for implementation approach]

   ## Out of Scope

   [Explicitly list what should NOT be done to prevent scope creep]
   ```

9. Update description via `update_task`:
   ```typescript
   {
     description: 'Refined description following the structure above';
   }
   ```

## 4. Refine Acceptance Criteria

10. Evaluate each acceptance criterion using the SMART framework:
    - **Specific**: Clearly states what must be done
    - **Measurable**: Can be verified programmatically or by inspection
    - **Achievable**: Within scope of a single task
    - **Relevant**: Directly contributes to task goal
    - **Testable**: An agent can verify completion

11. Rewrite vague criteria to be specific:

    **Before (Vague):**
    - "Handle errors properly"
    - "Make it performant"
    - "Add tests"

    **After (Specific):**
    - "Return HTTP 400 with error message for invalid input; return HTTP 500 for server errors with logged stack trace"
    - "API response time < 200ms for p95 under 100 concurrent requests"
    - "Add unit tests covering: happy path, validation errors, edge cases (empty input, max length); maintain 80% coverage"

    **Deriving test cases from criteria:**
    For each acceptance criterion, ask:
    - What must be true for this to pass? (happy path test)
    - What could go wrong? (error path test)
    - What are the boundary conditions? (edge case test)
    - What test type fits? (Unit for validation logic, Integration for API/DB, E2E for user flows)

12. Update acceptance criteria via `update_task`:
    ```typescript
    {
      acceptanceCriteria: [
        { description: 'Specific criterion 1', checked: false },
        { description: 'Specific criterion 2', checked: false },
        // ... more criteria
      ];
    }
    ```

## 5. Add Implementation Hints (devInfo)

13. Document implementation hints via `update_task` devInfo:
    ```typescript
    {
      devInfo: {
        suggestedApproach: "Brief description of recommended approach",
        referenceImplementations: ["path/to/similar/file.ts:42"],
        potentialChallenges: ["List any known gotchas or tricky areas"],
        testingStrategy: "How to verify this works correctly",
        testCases: [
          "Happy path: valid input produces expected output",
          "Error path: invalid input returns clear error message",
          "Edge case: empty input, max length, special characters"
        ],
        testTypes: "Unit for validation, Integration for API calls, E2E for user flows"
      }
    }
    ```

## 6. Collect & Attach Artifacts

14. Ask the user if they have any supporting artifacts to attach:
    - Screenshots (UI bugs, current state, expected state)
    - Design mockups / wireframes (screen layouts, page flows)
    - Documentation (API specs, requirements docs, diagrams)
    - Reference images (competitor examples, inspiration)

15. If the user provides artifacts, determine the appropriate scope:

    **Project-level artifacts** (shared across tasks — upload to project):
    - Screen/page mockups and wireframes
    - Design system references
    - Architecture diagrams
    - Shared documentation (API specs, PRDs)

    Use `get_artifact_signed_url` with `action: "upload"` and the project's ID:

    ```
    → get_artifact_signed_url({ action: "upload", filename: "mockup-login-page.png", contentType: "image/png" })
    → User uploads file to the returned URL
    → update_artifact({ key: "<returned-key>", status: "uploaded" })
    ```

    **Task-level artifacts** (specific to this task — link to task):
    - Bug screenshots
    - Task-specific reference images
    - Reproduction steps recordings

    Use `get_artifact_signed_url` then link to the task:

    ```
    → get_artifact_signed_url({ action: "upload", filename: "bug-screenshot.png", contentType: "image/png" })
    → User uploads file to the returned URL
    → update_artifact({ key: "<returned-key>", status: "uploaded", taskId: "<task-id>" })
    ```

16. Reference attached artifacts in the task description or devInfo so agents know to check them.

## 7. AI-Readiness Validation

Before completing refinement, run this type-aware readiness check. Infer the task type from tags and title.

17. **Check artifacts are referenced, not just uploaded:**
    - Use `list_artifacts` to find artifacts linked to the task or its project
    - For EACH artifact: verify it is explicitly mentioned in the task description or devInfo
    - An uploaded but unreferenced artifact is invisible to the executing agent — add a reference or flag it

18. **Type-specific readiness checklist:**

    **For UI/Frontend tasks** (tags: `feat:ui`, `feat:frontend`, or title indicates UI work):

    | Item                                                                           | Verdict               | Notes |
    | ------------------------------------------------------------------------------ | --------------------- | ----- |
    | Visual spec exists (mockup, wireframe, or detailed text description of layout) | PASS / FAIL / WARNING |       |
    | Component states defined (default, loading, error, empty, disabled)            | PASS / FAIL           |       |
    | Data shape specified (what props/API data does the component consume?)         | PASS / FAIL           |       |
    | Interaction behavior described (click, hover, form submission, navigation)     | PASS / WARNING        |       |

    **For API/Backend tasks** (tags: `feat:api`, `feat:backend`, or title indicates API work):

    | Item                                              | Verdict        | Notes |
    | ------------------------------------------------- | -------------- | ----- |
    | Endpoint path and HTTP method defined             | PASS / FAIL    |       |
    | Request payload shape specified (or "no payload") | PASS / FAIL    |       |
    | Success response shape specified                  | PASS / FAIL    |       |
    | Error response codes and shapes specified         | PASS / WARNING |       |
    | Auth/permission requirements noted                | PASS / WARNING |       |

    **For Data/Schema tasks** (tags: `feat:db`, `chore:migration`, or title indicates schema work):

    | Item                                            | Verdict        | Notes |
    | ----------------------------------------------- | -------------- | ----- |
    | Table/column changes described                  | PASS / FAIL    |       |
    | Data types and constraints specified            | PASS / FAIL    |       |
    | Relationships and foreign keys documented       | PASS / WARNING |       |
    | Migration strategy noted (additive vs breaking) | PASS / WARNING |       |

    **For all tasks:**

    | Item                                                      | Verdict        | Notes |
    | --------------------------------------------------------- | -------------- | ----- |
    | Acceptance criteria are SMART (not vague)                 | PASS / FAIL    |       |
    | File paths or patterns to follow are specified            | PASS / WARNING |       |
    | Out-of-scope boundaries are explicit                      | PASS / WARNING |       |
    | Dependencies on other tasks are documented                | PASS / WARNING |       |
    | Required skills listed in description (## Skills section) | PASS / WARNING |       |

19. **Determine readiness verdict:**
    - **Ready**: All PASS, no FAIL items — task can be promoted
    - **Needs-More-Info**: Has WARNING items but no FAIL — task can proceed with caveats noted for the agent
    - **Not-Ready**: Has any FAIL item — flag what's missing and ask the user to provide it before promotion

20. If verdict is **Not-Ready**, document the specific gaps in a task comment and do NOT mark the task as refined. The user must address the FAIL items first.

## 8. Verify Refinement Quality

21. Review the refined task by asking:
    - [ ] Can an agent understand the goal without clarification?
    - [ ] Are all file paths and references explicit?
    - [ ] Is the scope clearly bounded (what's in vs. out)?
    - [ ] Can each acceptance criterion be verified objectively?
    - [ ] Are dependencies and blockers identified?
    - [ ] Are relevant artifacts attached AND referenced in description/devInfo?
    - [ ] Does the AI-readiness check pass for this task type?

22. If any answer is "no", iterate on that section.

## 9. Document Refinement

23. Use `create_task_comment` to add refinement summary:

    ```
    **Task Refined**

    Changes made:
    - [List what was clarified or added]

    Key context added:
    - [Important context that was missing]

    Artifacts attached:
    - [List any artifacts uploaded, with scope: project-level or task-level]

    AI-Readiness: [Ready / Needs-More-Info / Not-Ready]
    [If Needs-More-Info or Not-Ready, list specific gaps]
    ```

24. If task is now ready for agent execution, no status change needed (remains "Todo").
    If further human input is required, document what's needed in the comment.

---

**Refinement Quality Checklist**

Before completing refinement, verify:

| Criterion                                                | Status |
| -------------------------------------------------------- | ------ |
| Clear goal statement                                     |        |
| Technical context (files, patterns)                      |        |
| Explicit scope boundaries                                |        |
| SMART acceptance criteria                                |        |
| Test cases for critical criteria (happy + error paths)   |        |
| Dependencies documented                                  |        |
| Implementation hints provided                            |        |
| Required skills listed in ## Skills section              |        |
| Artifacts attached AND referenced in description/devInfo |        |
| Type-specific readiness checklist passes (no FAIL items) |        |
| No ambiguous language                                    |        |

---

**Common Refinement Patterns**

### API Endpoint Task

```markdown
## Overview

Add GET /api/users/:id endpoint to retrieve user profile.

## Technical Context

- Route file: `src/routes/users.ts`
- Pattern: Follow existing `GET /api/organizations/:id` in `src/routes/organizations.ts:45`
- Schema: Use existing `UserSchema` from `src/schemas/user.ts`

## Implementation Notes

- Use existing `UserRepository.findById()` method
- Return 404 if user not found

## Out of Scope

- User creation (separate task)
- Authentication changes
```

### UI Component Task

```markdown
## Overview

Create UserAvatar component displaying user profile picture with fallback initials.

## Technical Context

- Component path: `src/components/UserAvatar/index.tsx`
- Pattern: Follow `src/components/OrganizationLogo/index.tsx`
- Design system: Use `@agimonai/frontend-web-ui` Avatar primitive

## Implementation Notes

- Accept size prop: 'sm' | 'md' | 'lg'
- Fallback to initials when no image URL
- Use semantic colors from design system

## Out of Scope

- Image upload functionality
- Edit mode
```

---

**Common Mistakes to Avoid**

- Leaving implicit assumptions undocumented
- Using vague terms like "properly", "correctly", "efficiently"
- Acceptance criteria that require subjective judgment
- Missing file paths or references
- Not specifying what's out of scope
- Expanding task scope during refinement
- Adding acceptance criteria that belong to different tasks
- Not verifying the task can be completed autonomously
