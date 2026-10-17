---
name: review-work
description: "Quality gate: verify each acceptance criterion of a completed task/work unit, run quality checks, and create follow-up tasks for gaps. Use before merging or to audit delivered work. Invoked as /agiflow:review-work <work-unit-or-task>. Uses get_work_unit, get_task, update_task, create_task, create_task_comment."
tags:
  - agiflow
  - mcp
  - review
  - quality-gate
metadata:
  mirrors: backend/apis/agiflow-api .../prompts/reviewWork.md
---

> Invoked as `/agiflow:review-work`. In hosts without slash-prompts, this skill is triggered by matching intent and drives AgiFlow via its MCP tools.

**Usage**:

- `/agiflow:review-work <work-unit-slug-or-id>` - Review a specific work unit
- `/agiflow:review-work <task-slug-or-id>` - Review a specific task
- `/agiflow:review-work` - List completed items for review

**Examples**:

- `/agiflow:review-work DXX-WU-1` (review work unit by slug)
- `/agiflow:review-work DXX-3` (review task by slug)
- `/agiflow:review-work` (interactive selection)

---

**Purpose**
Verify that completed work actually meets its acceptance criteria, catches quality issues, and is ready to ship. AI code has 1.7x more defects than human-written code — review is the last line of defense before shipping.

**Guardrails**

- Review what exists — do not implement fixes during review (create follow-up tasks instead).
- Every acceptance criterion gets a pass/fail verdict with evidence.
- Flag issues by severity: blocker (must fix), warning (should fix), note (nice to fix).
- Be honest — a "pass" with gaps is worse than a clear "needs rework".

If a work unit or task slug/id is provided, load it with `get_work_unit` / `get_task`; otherwise list candidates with `list_work_units` / `list_tasks` for selection.

---

## AgiFlow Project Management Guidelines

Follow the shared AgiFlow project-management guidelines in [`references/agiflow-agents.md`](../../references/agiflow-agents.md) — agent assignment, the task status workflow and transitions, work-unit best practices, and the tags strategy apply to this workflow.


---

**Steps**

## 1. Load the Work for Review

**If work unit slug/id provided:**

1. Use `get_work_unit` MCP tool to load the work unit and its tasks.
2. For each task in the work unit, use `get_task` to load full details (acceptance criteria, devInfo, comments).

**If task slug/id provided:** 3. Use `get_task` MCP tool to load the task with full details.

**If nothing provided:** 4. Use `list_work_units` with `status: "completed"` to show completed work units. 5. Use `list_tasks` with `status: "Review"` or `status: "Done"` to show completed tasks. 6. Ask user to select what to review.

## 2. Acceptance Criteria Audit

7. For each task, evaluate EVERY acceptance criterion:

| Criterion        | Verdict               | Evidence            |
| ---------------- | --------------------- | ------------------- |
| [criterion text] | PASS / FAIL / PARTIAL | [what you observed] |

**Verdict rules:**

- **PASS**: Criterion is fully met with evidence (test results, devInfo notes, implementation confirmed)
- **FAIL**: Criterion is not met or cannot be verified
- **PARTIAL**: Criterion is partially met — document what's missing

8. Check devInfo for implementation evidence:
   - Were files actually changed? (`filesChanged` in devInfo)
   - Did tests pass? (`testResults` in devInfo)
   - Is there a draft PR? (`draftPr` in devInfo)
   - Were acceptance criteria marked as checked?

## 3. Quality Checks

9. Evaluate these quality dimensions:

**Completeness:**

- Are ALL acceptance criteria addressed (not just the easy ones)?
- Are there gaps between what was asked and what was delivered?
- Were test cases included for critical paths?

**Consistency:**

- Do the changes align with the task/work unit description?
- Is the scope appropriate (no gold-plating, no missing pieces)?
- Do devInfo notes match the actual changes?

**Risk Assessment:**

- Are there edge cases that weren't covered?
- Could the changes break existing functionality?
- Are there security implications?
- Are there performance concerns?

## 4. Review Comments

10. For each task reviewed, use `list_task_comments` to check existing progress notes.
11. Use `create_task_comment` to add your review findings:

```
**Review Summary**

Verdict: APPROVED / NEEDS REWORK / APPROVED WITH NOTES

**Acceptance Criteria:**
- [criterion 1]: PASS - [evidence]
- [criterion 2]: FAIL - [what's missing]

**Issues Found:**
- [BLOCKER] [description] — must fix before shipping
- [WARNING] [description] — should fix, creates tech debt
- [NOTE] [description] — minor improvement opportunity

**What's Good:**
- [positive observation]

**Next Steps:**
- [action needed, if any]
```

## 5. Verdict and Actions

12. Based on findings, recommend one of:

**APPROVED** — All criteria pass, no blockers.

- If work unit: use `update_work_unit` to confirm status "completed"
- If task: use `update_task` to confirm status "Done"
- Summarize what shipped and its value

**APPROVED WITH NOTES** — All criteria pass, minor issues.

- Keep current status
- Create follow-up tasks for noted improvements using `batch_create_tasks`
- Document notes in task comment

**NEEDS REWORK** — One or more criteria fail or blockers found.

- If work unit: use `update_work_unit` to set status back to "in_progress"
- If task: use `update_task` to set status back to "In Progress"
- Uncheck failed acceptance criteria
- Document what needs to change in task comment
- Be specific: "criterion X fails because Y, to fix do Z"

## 6. Work Unit Summary (if reviewing a work unit)

13. After reviewing all tasks in the work unit, produce a rollup:

```
**Work Unit Review: [title]**

Tasks: [N passed] / [total] passed
Overall: APPROVED / NEEDS REWORK

| Task | Slug | Verdict | Issues |
|------|------|---------|--------|
| [title] | [slug] | PASS | 0 |
| [title] | [slug] | FAIL | 2 blockers |

[Summary of what the work unit delivers and whether it's ready]
```

---

**Common Mistakes to Avoid**

- Rubber-stamping: marking PASS without checking evidence
- Fixing issues during review instead of documenting them for rework
- Ignoring devInfo (it contains the implementation trail)
- Reviewing only the happy path and missing edge cases
- Not creating follow-up tasks for issues found
- Approving work with unchecked acceptance criteria
