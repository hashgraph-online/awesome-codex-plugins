---
name: team-assign
description: "Assign tasks to team members. Use when: distributing work by role, expertise, and capacity, or managing workloads."
---

# /digital-marketing-pro:team-assign

## Purpose

Assign marketing tasks to team members with intelligent matching based on role, channel expertise, regional alignment, and current capacity. Supports viewing team workload distributions, managing active assignments, and rebalancing when utilization is uneven. Ensures every task lands with the right person at the right time, preventing overload and skill mismatches across the team.

Handles three core operations: assigning new tasks with smart member matching, listing and filtering current assignments across the team, and generating workload dashboards that surface capacity risks before they become bottlenecks. For agencies managing multiple brands, provides cross-brand visibility into team utilization.

## Input Required

The user must provide (or will be prompted for):

- **Action**: The operation to perform — `assign` (assign a new task to a team member), `get-assignments` (view current assignments filtered by member or status), or `check-workload` (show team utilization dashboard with capacity warnings and rebalancing suggestions)
- **Task description** (for assign): Clear description of the marketing task — e.g., "Write Q2 email nurture sequence", "Audit Google Ads account", "Create social media calendar for April"
- **Channel** (for assign): The marketing channel the task belongs to — email, social, paid, blog, seo, analytics, content, design, pr, influencer, automation, or multi-channel
- **Priority** (for assign): Task priority level — low (no deadline pressure), medium (standard timeline), high (accelerated timeline), or urgent (drop everything, capacity overrides allowed up to 95%)
- **Due date** (for assign): Target completion date for the task — used to evaluate team member availability within the timeframe and detect scheduling conflicts with existing assignments
- **Estimated hours** (optional, for assign): Expected effort in hours — improves capacity matching accuracy. If omitted, estimated from task type and channel complexity using historical averages
- **Brand** (optional, for assign): Which brand the task is for — defaults to active brand. Relevant for agencies managing multiple brands where team members may be assigned across accounts
- **Specific team member** (optional, for assign): If the user has a preferred assignee — the system will verify capacity before confirming, or suggest alternatives if the member is overloaded
- **Dependencies** (optional, for assign): Other task IDs that must be completed before this task can begin — used to sequence work and prevent premature assignment to available members
- **Filter criteria** (for list-assignments): Filter by team member name, status (active, completed, overdue, blocked), channel, priority, brand, or date range
- **Time range** (for check-workload): Period to evaluate — this week, next two weeks, this month, or custom date range
- **Notes** (optional, for assign): Additional context for the assignee — links to briefs, reference materials, client preferences, or special instructions that should accompany the task notification

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load team roster**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/team-manager.py" --action list-team --brand {slug}` to retrieve all team members with their roles, channel specializations, regional assignments, seniority level, and current active/inactive status. If no team roster exists, prompt the user to set one up first.
3. **Route by action type**: Branch based on the requested action — assign (steps 4-10), get-assignments (step 11), or check-workload (steps 12-13).
4. **Check team capacity**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/team-manager.py" --action check-capacity --brand {slug}` to pull current utilization for each team member. Flag anyone above 85% utilization as at-risk for new assignments. Flag anyone above 95% as unavailable unless priority is urgent. Include hours allocated this week and next two weeks for forward-looking availability.
5. **Estimate task effort**: If estimated hours were not provided, infer from task type, channel complexity, and historical averages — e.g., a blog post averages 6-8 hours, a full Google Ads audit averages 12-16 hours, a social media calendar averages 4-6 hours. Display the estimate and let the user confirm or adjust before matching.
6. **Check task dependencies**: If dependencies were specified, verify those tasks are complete or on track. If a dependency is overdue or blocked, warn the user that this task may not be actionable on the requested timeline and suggest adjusting the due date or resolving the blocker first.
7. **Match task to best team member**: Score eligible team members on four weighted factors — role fit (40% weight: does the role align with the task type), channel expertise (30% weight: does the member specialize in the required channel), current utilization (20% weight: prefer members below 70% utilization, allow up to 85%), and region alignment (10% weight: timezone and market overlap with the task's target audience). Rank candidates by composite score.
8. **Check for scheduling conflicts**: Verify the top-ranked candidate does not have conflicting deadlines — multiple high-priority tasks due within the same 48-hour window. If conflicts detected, adjust ranking or flag the conflict for user review with a visualization of the member's upcoming deadline timeline.
9. **Validate specific member request**: If the user requested a specific team member, verify their capacity is below 85% utilization and check for deadline conflicts. If overloaded, present the capacity data and suggest the top-ranked alternative with an explanation of the match rationale. Let the user decide — override is allowed for urgent priority.
10. **Create assignment and notify**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/team-manager.py" --action assign-task --brand {slug} --data '{task_json}'` — the `--data` payload carries the selected member, task description, channel, priority, due date, estimated hours, and dependencies. Record the assignment with a unique task ID and timestamp. If Slack MCP is connected, send an assignment notification to the team member with task details, priority, due date, and any relevant brand context. If email MCP is connected, send a backup notification. If neither is connected, include the notification text in the output for manual forwarding.
11. **List current assignments**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/team-manager.py" --action get-assignments --brand {slug}` with any provided filters (e.g. `--status pending|in-progress|completed`). Format results as a structured table showing task ID, description, assignee, channel, priority, due date, estimated hours, status, dependencies, and days remaining or days overdue. Include summary counts per status and per team member. Highlight overdue tasks and blocked tasks whose dependencies have not been met.
12. **Generate workload dashboard**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/team-manager.py" --action check-capacity --brand {slug}` for the specified time range. Display per-member utilization percentages, available capacity hours, assignment count, upcoming deadlines, overload warnings (above 85%), and underutilization flags (below 40%). Highlight imbalances and produce specific rebalancing recommendations with task-move suggestions.
13. **Detect cross-brand conflicts**: If operating in portfolio mode with multiple brands, check whether team members are assigned conflicting deadlines across different brands. Surface cross-brand overload risks that single-brand views would miss. Show per-brand hour allocation to identify accounts consuming disproportionate team capacity.
14. **Log assignment history**: Append the assignment action to the team assignment log at `~/.claude-marketing/logs/assignments.json` for historical tracking — enables trend analysis on team utilization patterns, average task durations by type, and recurring bottlenecks over time.

## Output

A structured assignment result or workload view containing:

- **Assignment confirmation** (for assign): Assignee name, role, task ID, task description, channel, priority, due date, estimated hours, match score breakdown (role fit, channel expertise, utilization, region), dependency chain status, and notification delivery status
- **Match rationale** (for assign): Plain-language explanation of why this team member was selected — e.g., "Sarah specializes in email marketing (channel fit), is currently at 62% utilization (capacity available), and is assigned to the EMEA region (timezone aligned with this campaign's audience)"
- **Alternative candidates** (for assign, if relevant): Top 2-3 alternative team members with match scores, current utilization, and availability notes — shown when the best match is borderline or when a specific member request was capacity-limited
- **Scheduling conflict warnings** (for assign): Any flagged deadline clusters where the assignee has multiple high-priority tasks due within the same 48-hour window, with suggested timeline adjustments
- **Dependency alerts** (for assign): Status of prerequisite tasks — complete, in progress, or blocked — with projected impact on the new task's start date if dependencies are running late
- **Assignment list** (for get-assignments): Filtered table of all assignments — task ID, description, assignee, channel, priority, due date, estimated hours, status (active/completed/overdue/blocked), dependencies, and days remaining or overdue. Summary row with counts per status category
- **Workload dashboard** (for check-workload): Per-member utilization breakdown showing current capacity percentage, active task count, hours allocated vs. available, upcoming deadline density, overload warnings, underutilization flags, and channel distribution of current assignments
- **Capacity alerts**: Any team members flagged as at-risk (above 85%) or critically overloaded (above 95%) with specific task counts, deadline pressure, and suggested redistributions
- **Rebalancing suggestions**: When significant utilization imbalances exist (variance above 30% between team members), specific recommendations for moving tasks between members to optimize team throughput — including which tasks to move, from whom, to whom, and the projected utilization impact
- **Cross-brand summary** (portfolio mode): If the team works across multiple brands, a unified view showing per-brand task distribution, per-brand hour allocation, cross-brand deadline conflicts, and total utilization across all accounts
- **Historical assignment patterns**: Summary of recent assignment trends — which team members handle which channels most often, average task completion time by type, and any recurring overload patterns that suggest team capacity needs adjustment
- **Overdue task escalation list**: Any tasks past their due date with assignee, days overdue, original priority, and recommended escalation action — reassign, extend deadline, or flag to account lead
- **Team efficiency metrics** (for check-workload): Average task completion rate, on-time delivery percentage, and channel-level throughput — providing a health check on overall team productivity beyond just capacity numbers
- **Upcoming deadline preview**: Timeline view of the next 14 days showing all task due dates across the team, color-coded by priority, highlighting any date clusters where multiple deliverables converge
- **Assignment log entry**: Confirmation that the action was recorded in the assignment history log with timestamp, action type, and details — enabling audit trail and trend analysis over time

## Agents Used

- **agency-operations** — Team roster management, capacity analysis, task-to-member matching, assignment creation, dependency tracking, scheduling conflict detection, workload optimization, and rebalancing recommendations
