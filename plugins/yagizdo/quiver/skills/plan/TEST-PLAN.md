# Test Plan -- /plan

**Trigger:** `/plan <task description>` (and `/quiver:plan` should also work)

**Setup:**
- Project root with optional `.claude/plans/` directory.
- For review-fix path: a `.claude/reports/review-*.md` file exists and is passed as the argument.

**Expected behavior:**
1. Skill gathers git context; on a non-git directory it continues with empty git fields and a warning line.
2. Skill restates the task and assesses complexity (Light / Standard / Deep) silently, dispatching the matched agents in parallel.
3. Skill detects review-fix context when the argument matches `.claude/reports/review-*.md` and adds `review_source` + `review_iteration` to the plan frontmatter.
4. Skill presents the synthesized plan and uses `AskUserQuestion` for the Step 7 review gate (`Approve` / `Modify` / `Reject`).
5. On `Approve`, skill saves the plan to `.claude/plans/YYYY-MM-DD-<name>-plan.md`, reads it back to verify, then invokes `AskUserQuestion` again for the Step 8 next-step gate.

**Verification checklist:**
- [ ] Slash menu shows `/plan`.
- [ ] Plan file is written under `.claude/plans/` with the date-prefixed filename.
- [ ] Multiple agents are dispatched in a single response when complexity is Standard or Deep (parallel execution).
- [ ] Review-fix detection produces frontmatter with `review_source` and `review_iteration`.
- [ ] No raw `{placeholder}` strings remain in the saved plan.
- [ ] A plan whose Step 4.5 gate had at least one candidate selected carries a `## Global Constraints` section holding exactly the selected entries and no others.
- [ ] A plan whose Step 4.5 gate had zero candidates selected carries no Global Constraints heading and no empty section.
- [ ] A task that contradicts one of the plan's own Global Constraints is caught by Step 6 Check 7 and resolved as FIX -- the task is rewritten, or the constraint is dropped -- before the plan reaches the user.
- [ ] A plan whose Task A creates a symbol Task B names by exact identifier carries a `**Provides:**` line on Task A, and a plan where no symbol crosses tasks carries no `**Provides:**` line anywhere.
- [ ] A plan where Task A creates a symbol Task B names but Task A carries no `**Provides:**` entry is corrected by Step 6 Check 8 as ADD before the plan reaches the user.
- [ ] The Step 7 and Step 8 user gates appear as `AskUserQuestion` calls, not plain-text prompts.
- [ ] Agent dispatch and Plan Guard checks execute correctly for Standard/Deep plans.
- [ ] Step 6.5 agent dispatch follows skip conditions (Light and review-fix plans skip).
- [ ] Plan Guard Notes subsection appears in the plan's Context section only when NOTE findings exist.
- [ ] `codegraph_available` flag detected and passed to agents when `.codegraph/` exists.
- [ ] In a project with a test framework, every task that produces testable behavior lists its test step before its implementation step, and the plan names `skills/tdd/SKILL.md` for the cycle rather than restating it.

**Known gotchas:**
- The code-navigator agent (`agents/research/code-navigator.md`) owns the Code Navigation Strategy. When updating the strategy in `skills/code-navigation/SKILL.md`, update the agent file too.
- `review_iteration` is determined by counting prior plans with the same `review_source` field; if naming conventions drift, the iteration count can desync.
