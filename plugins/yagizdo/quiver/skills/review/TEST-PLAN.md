# Test Plan -- /quiver:review

**Trigger:** `/quiver:review` (with optional flags: PR URL, `--base <branch>`, `--deep`, `--plan <path>`, `--output <path>`, `--set-output <path>`, `--terminal`, `--comment-pr`, `--with-codex`); `/quiver:review` should also work.

**Setup:**
- Current directory is a git repo with at least one diff source (PR URL, branch ahead of base, or uncommitted changes).
- `agents/review/*.md` and `agents/research/*.md` are present and registered in `.claude-plugin/plugin.json`.
- `gh` and/or `glab` CLI installed if testing PR Mode 1 path.

**Expected behavior:**
1. Skill picks the first matching review mode (PR/MR URL, branch diff, uncommitted) and announces it.
2. Skill builds the Diff Manifest (Step 1.5) classifying every changed file (`PROMPT`, `SCRIPT`, `CONFIG-APP`, `CONFIG-MANIFEST`, `CODE`, `DOCS`).
3. Skill runs navigation detection (Step 1.75) and dispatches all qualifying agents in a single response (parallel) with the agent context including Diff Manifest, scope reminders, `codegraph_available`, and `lsp_available`.
4. Skill detects existing review reports for the same branch and switches to re-review mode with delta-only scope when a previous report is found.
5. Skill synthesizes findings (deduplicate, subsumption, severity normalization, false-positive filters, proportional floor) and writes `review-<timestamp>.md` to the configured output directory; with `--terminal`, prints inline instead.
6. Skill optionally posts the report as a PR comment when `--comment-pr` is set or the user opts in interactively.
7. All chat-stream output passes the Status-Messages plain-language gate (no rule codes, hashes, or invariant names in user-facing text).
8. Fast mode (default) dispatches exactly 5 agents, runs simplified synthesis, skips Steps 3.5 and 3.75.
9. Deep mode (`--deep`) dispatches all qualifying agents and runs full synthesis pipeline including report-checker and senior-reviewer.
10. `--with-codex` without `--deep` prints a guidance note and continues fast review without Codex.
11. Skill discovers the plan whose `## Global Constraints` section binds the review (Step 1.8), passes the block to every dispatched agent as context item 10, and names the source plan in the report's `Global Constraints` field. With no block found, the run is silent about it and the field reads `N/A`.
12. Every non-filtered finding carries a `Disposition:` line (Before merge | Follow-up | Defer) in both modes, and `## Recommended Fix Order` lists every Before-merge and Follow-up finding at any severity -- the section is never omitted, and deferred findings are named in its `**Deferred:**` line instead.
13. Deep mode dispatches `fix-reviewer` at Step 3.9, after senior-reviewer, when at least one finding carries a fix proposal. Its actions change only the fix block inside a finding; no finding is removed, re-severed, or re-dispositioned at that step.

**Verification checklist:**
- [ ] Slash menu shows `/quiver:review`.
- [ ] All qualifying agents are spawned in a single response (multiple Agent tool calls in one assistant turn).
- [ ] Re-review mode produces a `Delta` line and `Scope: Delta-only` in the saved report's `## Review Context`.
- [ ] Report path defaults to `.claude/reports/` and respects `--output`/`--set-output`/saved preference, with path validation rejecting absolute paths and `..` segments.
- [ ] `--with-codex` is silently skipped when the `codex` CLI is missing (does not error).
- [ ] `--with-codex` is silently skipped when the diff exceeds 2000 lines (skip note shows actual line count).
- [ ] No internal jargon (rule codes, hashes, invariant names) appears in the terminal summary; report file content may include them.
- [ ] `/quiver:review` (no flags) dispatches at most 5 agents (logic-reviewer, security-audit, waste-detector, best-practices-researcher, project-context-analyst).
- [ ] `/quiver:review --deep` dispatches all qualifying agents (same as pre-optimization behavior).
- [ ] `/quiver:review --with-codex` (without --deep) prints "--with-codex requires --deep" note and proceeds.
- [ ] Fast mode report includes `(fast)` in the Mode line of Review Context.
- [ ] Fast mode report's Agents Dispatched section does not list deep-mode-only agents as skipped.
- [ ] Deep mode report includes `(deep)` in the Mode line of Review Context.
- [ ] Branch-mode review with a plan carrying `## Global Constraints` in `.claude/plans/` names that plan in the report's `Global Constraints` field, and every dispatched agent's prompt carries the block under `## Global Constraints (from {plan path})`.
- [ ] With no `.claude/plans/` directory, no `.md` file in it, or no `## Global Constraints` section in the newest plan, the field reads `N/A`, no note or warning is printed, and no agent prompt carries context item 10.
- [ ] Review of a PR URL without `--plan` reads `N/A` (Step 1.8 does not run in PR mode); the same PR URL with `--plan <path>` names that path in the field.
- [ ] `--plan` and its path are stripped from `$ARGUMENTS` in Step 0.5 and never reach the diff-source logic in Step 1.
- [ ] A finding whose recommendation cannot be acted on without violating a constraint appears in `## Filtered Findings` classified `constraint-blocked` with the constraint named, and is absent from `## Findings`.
- [ ] A change in the diff that violates a constraint is still reported as a finding -- the block cuts both ways.
- [ ] Every finding in `## Findings` has a `Disposition:` line; a Low finding is dispositioned like any other and is not left out of the report's action accounting.
- [ ] A finding whose own body argues against acting now ("worth doing eventually rather than now", "either answer is defensible") is dispositioned `Defer`, keeps its severity, and stays in `## Findings` rather than being deleted.
- [ ] `## Recommended Fix Order` is present even when nothing blocks the merge, and its `Disposition` column matches each finding's own disposition line.
- [ ] Deep review of a report carrying at least one fix snippet prints the fix-check line and dispatches `fix-reviewer` exactly once; a report with no fix snippet prints `No fix proposals to check.` instead.
- [ ] A rejected fix leaves its finding in place with `No verified fix -- {reason}` where the snippet was, at the original severity and disposition.
- [ ] Fast mode skips Step 3.9 along with Steps 3.5 and 3.75.

**Known gotchas:**
- Step 1.8 takes the newest plan in `.claude/plans/` with no matching heuristic, so an unrelated plan can supply constraints in branch mode. The `Global Constraints` field names the plan for exactly this reason; re-run with `--plan <path>` when the named plan is wrong.
- The `## Global Constraints` heading is the whole interface between `/plan`, `/work`, and `/quiver:review`. Renaming it in `skills/plan/SKILL.md` makes extraction here return nothing, silently, on the degrade-cleanly path.
- Bitbucket/Azure DevOps PR URLs fall back to Mode 2 because there is no diff CLI; PR commenting also skips on those platforms with a manual-paste hint.
- Two-dot `git diff <base>..<head>` is wrong for branch diffs; the skill uses three-dot `git diff <base>...HEAD` instead.
- The synthesized report SYNC contract pairs with `skills/work/SKILL.md` Phase 4c parsing; changing section headings or finding-ID format requires updating the work skill verification logic.
- `fix-reviewer` lives under `agents/debug/`, not `agents/review/`, because `/quiver:hypothesis-debugging` dispatches it too. Step 2a's Tier 1 scan never sees it, so its `NEVER` row in `## Dispatch Gates` and its path in the dispatch-scope list of `tests/skills/test-review-dispatch-contract.sh` are what keep it under the contract. Dropping either leaves Step 3.9 dispatching an agent no test covers.
- Step 3.9 runs after Step 3.75 on purpose: senior-reviewer rewrites fix snippets and adds SR findings with fixes of their own, so a fix check placed before it would not see the pipeline's last author.
