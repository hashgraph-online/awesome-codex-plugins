# Test Plan -- /report-check

**Trigger:** `/report-check <path>` (and `/quiver:report-check` should also work)

**Setup:**
- A review report file exists at the given path (e.g., `.claude/reports/review-*.md`).
- Optionally, the branch referenced in the report still exists locally.

**Expected behavior:**
1. No-arg invocation prints usage message and stops.
2. Invalid file path prints error and stops.
3. Valid path reads the report, optionally reconstructs the diff, and spawns the report-checker agent.
4. Agent findings are presented with action buttons (Apply / Show details / Skip).
5. Apply fixes modifies the report file and verifies the result.

**Verification checklist:**
- [ ] Slash menu shows `/report-check`.
- [ ] No arguments prints usage and stops.
- [ ] Non-existent file path prints error and stops.
- [ ] Valid report path spawns agent and displays findings.
- [ ] "Apply fixes" modifies the file and recalculates counts/verdict.
- [ ] "Skip" leaves the report unchanged.
- [ ] No `{placeholder}` text remains after applying fixes.

**Known gotchas:**
- The diff reconstruction depends on the branch still existing locally. If the branch was deleted after the review, the agent runs without diff (Phase 2 accuracy checks are limited).
- The report format parsed here matches the structure produced by `skills/review/SKILL.md` Step 3. If the report format changes, update the parsing in Step 4.
