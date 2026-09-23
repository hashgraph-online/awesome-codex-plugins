---
name: review
description: Run a multi-agent code review. Default fast mode (5 agents); pass --deep for full pipeline (all agents + quality check + senior review). Pass --with-codex for cross-model coverage.
argument-hint: "[PR/MR URL | --base <branch>] [--deep] [--plan <path>] [--output <path>] [--set-output <path>] [--terminal] [--comment-pr] [--with-codex]"
disable-model-invocation: true
when-to-use: "user wants a multi-agent code review of a PR or diff -- '/review', 'review my changes', 'review this PR', 'code review', 'audit the diff' (not: 'senior review')"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --sort=-committerdate 2>/dev/null || echo "NO_GIT"`
```

---

# Instructions

You are a review orchestrator. Your job is to determine the correct diff source, announce the review mode, dispatch multiple review agents in parallel, then synthesize their findings into a single unified report.

## Step 0 -- Git Availability

If any gather-context block above returned `NO_GIT`, this directory is not a git repository.
Print: `> No git repository detected. /quiver:review requires a git repo.`
**Stop here.**

## Step 0.5 -- Detect Review Depth

Parse `$ARGUMENTS` for the `--deep` and `--plan` flags:

1. If `$ARGUMENTS` contains `--deep`, set `review_mode = deep`. Strip `--deep` from `$ARGUMENTS` before passing to subsequent steps.
2. Otherwise, set `review_mode = fast`.
3. If `$ARGUMENTS` contains `--plan <path>`, set `constraints_plan_path` to the path token that follows the flag, and strip both `--plan` and that path from `$ARGUMENTS` before passing to subsequent steps. Otherwise leave `constraints_plan_path` unset.

`--deep` affects Steps 2 (agent dispatch), 3 (synthesis), 3.5, 3.75, and 3.9 only. `--plan` affects Step 1.8 only -- it names the plan whose Global Constraints bind this review, and never changes which diff is reviewed. All other steps (diff source detection, manifest building, LSP detection, report saving, PR posting) are identical in both modes.

Announce the mode:
- Fast: `Running review (5 core agents)...`
- Deep: `Running deep review (full agent pipeline)...`

## Step 1 -- Determine Review Mode

Silently evaluate the conditions below in order. Use the **first** mode that matches.

### Mode 1 -- PR/MR Link Provided

If `$ARGUMENTS` contains a pull request or merge request URL from any Git platform (GitHub, GitLab, Bitbucket, Azure DevOps, etc.):

1. Detect the platform from the URL pattern. For GitHub, pass the full URL directly to `gh pr diff`. For GitLab, extract the merge request number and validate it is numeric.
   - **GitHub:** `github.com/{owner}/{repo}/pull/{number}` -- use `gh pr diff <full-URL>`
   - **GitLab:** `gitlab.com/{group}/{project}/-/merge_requests/{number}` -- extract `{number}` (must be numeric) and use `glab mr diff {number}`
   - **Bitbucket:** `bitbucket.org/{workspace}/{repo}/pull-requests/{number}` -- Bitbucket CLI lacks a direct diff command. Fall back to Mode 2 (branch diff).
   - **Other platforms:** Fall back to Mode 2 with a note:
     > Platform not recognized for direct diff fetching. Falling back to branch diff.
2. Before running a platform CLI command (`gh`, `glab`), check if the CLI is available. If not, fall back to Mode 2 with a note:
   > `{cli}` CLI not found. Falling back to branch diff.
3. Announce: `Reviewing PR/MR from provided link...`
4. If fetching fails (permissions, invalid URL), print a warning:
   > Could not fetch diff from the provided link. Falling back to branch diff.
   Then continue to Mode 2.
5. If fetching succeeds, pass the diff to the agent in Step 2.

### Mode 2 -- Branch Diff

If no PR link was provided (or Mode 1 fell back), and **any** of the following are true: (a) `$ARGUMENTS` contains `--base <branch>`, or (b) the current branch is **not** `main` or `master`:

1. **Determine the base branch** using one of these methods (in order):
   - **`--base` flag:** If `$ARGUMENTS` contains `--base <branch>`, use that branch directly. Skip the prompt.
   - **Interactive selection:** Otherwise, use `AskUserQuestion` to ask the user which base branch to compare against. Use the gathered branch list output to build action buttons for candidate branches. Include an **"Other (I'll type it)"** button as the last option. Phrasing:
     > You're on `{current_branch}`. Which branch should I compare against for the review?
   - If the user picks "Other (I'll type it)", ask them to type the branch name.
1b. **Validate the base branch:** Run `git rev-parse --verify {base_branch}` to confirm the ref exists.
    If it fails: > Branch `{base_branch}` not found. Please check the name and try again.
    **Stop here.**
2. Announce: `Reviewing branch {current_branch} against {base_branch}...`
3. Get the diff:
   ```
   git diff {base_branch}...HEAD
   ```
4. If the diff is empty, announce:
   > Branch diff against `{base_branch}` is empty. Checking for local uncommitted changes...
   Then continue to Mode 3.
5. Otherwise, pass the diff to the agent in Step 2.

### Mode 3 -- Uncommitted/Staged Changes

If the current branch is `main`/`master`, or the branch diff was empty:

1. Check for unstaged changes:
   ```
   git diff
   ```
2. If empty, check for staged changes:
   ```
   git diff --cached
   ```
3. If both are empty:
   > No changes to review. Commit some changes or switch to a feature branch and try again.
   **Stop here.**
4. Announce: `Reviewing local uncommitted changes...`
5. Pass the diff to the agent in Step 2.

### Re-review detection (all modes)

After obtaining the diff, check if a previous review report exists for this branch:

1. Scan the report directory (`.claude/reports/` or saved preference path) for `review-*.md` files.
2. **Filter by branch.** For each report found, read its `## Review Context` section and check the `Branch` field. Only consider reports that match the current branch. Discard reports for other branches.
3. If one or more matching reports exist, read the most recent one and extract its findings and metadata.
4. **Calculate iteration number**: Read the previous report's `## Review Context` section. Extract the `Iteration` value and increment by 1. If the previous report has no `Iteration` field, this is iteration 2.
5. **Extract previous HEAD commit**: Read the `HEAD at review` field from the previous report's `## Review Context`. Use this SHA to compute the delta diff: `git diff {previous_head_sha}...HEAD`. If the field is missing, fall back to using the report's filename timestamp to estimate the commit range via `git log --after="{timestamp}" --format=%H`.
6. This is a **re-review**. Apply these constraints:
   - **Scope lock**: Only flag findings that are (a) NEW issues introduced by commits made AFTER the previous review's timestamp, or (b) regressions where a previously-addressed finding has reappeared.
   - **No scope expansion**: Do NOT flag pre-existing patterns, stylistic preferences, or aspirational improvements that were not in the original review. The original review had the chance to flag these -- if it didn't, they are accepted.
   - **Idempotency check**: If the diff between the previous review and now contains NO functional code changes (only whitespace, comments, or formatting), the verdict MUST be "Approve" with zero findings.
   - When populating the report template's `## Review Context` section, set `Iteration` to {N}, `Previous report` to the path of the matched report, `Scope` to "Delta-only (changes since previous review)", and add a `Delta` line with `{commit_count} commits, {files_changed} files`.
7. Pass the re-review context and scope constraints to all agents in Step 2.

---

## Step 1.5 -- Build Diff Manifest

After obtaining the diff, analyze the list of changed files and classify each one. Build a text manifest using the taxonomy below:

| Type | Matched by | Security relevance |
|------|-----------|-------------------|
| `PROMPT` | `commands/*.md`, `agents/**/*.md`, `skills/**/*.md` with YAML frontmatter | Low -- instructions to LLM |
| `SCRIPT` | `*.sh` (anywhere, not just hooks/), `Makefile`, `Dockerfile`, `*.py`/`*.rb` (executable), CI workflow files (`.github/workflows/*.yml`, `.gitlab-ci.yml`) | High |
| `CONFIG-APP` | App configuration: auth, database, CI/CD environment, secrets files (`*.json`, `*.yaml`, `*.toml` containing app settings, credentials, or infrastructure) | High |
| `CONFIG-MANIFEST` | Package/plugin registries: `plugin.json`, `package.json`, lockfiles, `tsconfig.json`, `*.toml` build configs, `.gitignore`, `.editorconfig`, `.dockerignore` -- structural metadata only | Low |
| `CODE` | Application source (JS, TS, Go, Dart, etc.) | High |
| `DOCS` | `*.md` outside command/agent/skill dirs, `README*`, `CHANGELOG*` | Low |

Format the manifest as a simple list:

```
Diff Manifest:
- skills/review/SKILL.md → PROMPT (low security relevance)
- hooks/scripts/pre-compact-handover.sh → SCRIPT (high security relevance)
- plugin.json → CONFIG-MANIFEST (low security relevance)
- .env.example → CONFIG-APP (high security relevance)
```

Include risk signals if present: new dependencies, auth changes, secrets handling, new endpoints.

---

## Step 1.75 -- Navigation Detection

Before dispatching agents, detect navigation capabilities once.

**CodeGraph:** Check if `.codegraph/` exists at project root. Set `codegraph_available` to `true` or `false`. No user prompt.

**LSP:** Run the LSP detection flow in `skills/code-navigation/SKILL.md` (cached preference, one probe, no prompt); it yields `lsp_available`.

Pass both `codegraph_available` and `lsp_available` to agents that search the broader codebase (waste-detector, architecture-strategist, stress-tester, and project-context-analyst) in Step 2.

---

## Step 1.8 -- Global Constraints Discovery

Find the plan whose Global Constraints bind this review and extract that block verbatim. This step is a read-only lookup. It never edits, extends, paraphrases, or renumbers the block, and it never writes a plan file -- `/plan` is the only skill that decides constraint content.

1. **Explicit plan.** If Step 0.5 set `constraints_plan_path` from `--plan <path>`, use that file. If the path does not exist or cannot be read, set the block to empty and continue with no note.
2. **PR/MR mode.** Otherwise, if Step 1 resolved to Mode 1 (PR/MR link provided) and did not fall back to Mode 2 or Mode 3, skip discovery entirely and set the block to empty. A PR diff can come from a branch whose plan never existed on this machine, so the newest local plan is more likely wrong than right, and a wrong constraint removes real findings in the suppression direction. A user who knows a local plan applies to a PR passes `--plan <path>`.
3. **Newest local plan.** Otherwise, list the plans directory with the Bash tool (`ls -1t .claude/plans/*.md 2>/dev/null`) and take the first path it prints -- the newest `.md` file by modification time. Empty output means there is no plans directory and no plan file; go to rule 5.
4. **Extract the block.** Read the chosen file and take the `## Global Constraints` section: every line after that heading up to the next `## ` heading, with leading and trailing blank lines trimmed. Set `constraints_plan_path` to the chosen file's path -- Step 3's report template prints it in `## Review Context`.
5. **Degrade cleanly.** If there is no `.claude/plans/` directory, no `.md` file in it, or no `## Global Constraints` heading in the chosen file, set the block to empty and continue with no note, no warning, and no error. An empty block means Step 2 skips per-agent context item 10 entirely, the Step 3 `constraint-blocked` filter never fires, and the report's `Global Constraints` field reads `N/A`. This path must behave exactly as a review did before this step existed.

Do the listing and the read with the Bash and Read tools at this point in the run, not with a `!` block at the top of this file: the lookup is conditional on the review mode resolved in Step 1, and `!` blocks run before any step logic.

Say nothing about this step in the chat stream. The report's `Global Constraints` field and the `constraint-blocked` entries in `## Filtered Findings` are where the block becomes visible.

---

## Step 2 -- Parallel Agent Dispatch

### 2a -- Discover available agents

Discover agents using a two-tier registry:

**Tier 1 — Review agents (dynamic):** Scan `agents/review/*.md`. For each `.md` file, read its YAML frontmatter to extract `name` and `description`.

**Tier 2 — External specialists (explicit):** Also include these agents from outside the review directory:
- `agents/research/best-practices-researcher.md`
- `agents/research/project-context-analyst.md`

For Tier 2 agents, read the frontmatter the same way. If a Tier 2 file is missing or unreadable, skip it silently — do not fail the review.

**Agent type identifiers** use the format `quiver:{name}` where `{name}` is the frontmatter `name` field. The category subdirectory is organizational only -- it is NOT part of the identifier. Examples:
- `agents/review/waste-detector.md` → `quiver:waste-detector`
- `agents/research/best-practices-researcher.md` → `quiver:best-practices-researcher`

### 2b -- Conditional Dispatch

Apply dispatch rules based on the Diff Manifest from Step 1.5.

The canonical gate for every agent is the `## Dispatch Gates` table in `.claude/rules/review-agent-rules.md`. The per-agent rules restated below are a copy of it for the orchestrator's use, and `tests/skills/test-review-dispatch-contract.sh` is the binding that fails when the copies diverge. When a gate changes, change the table first.

### Review depth dispatch

**If `review_mode = fast`:** Dispatch only these 5 agents:
- **`waste-detector`**: Always dispatched (same as deep mode).
- **`security-audit`**: Only when diff contains `SCRIPT`, `CODE`, or `CONFIG-APP` files (same gate as deep mode). In fast mode, receives additional context: "FAST MODE CHECK: For state management and interactive flows, verify every user-initiated process has a guaranteed termination path (timeout, cancel handler, forced cleanup). Missing exit conditions on partial user actions create livelock -- flag as High."
- **`logic-reviewer`**: Only when diff contains `SCRIPT` or `CODE` files (same gate as deep mode).
- **`best-practices-researcher`**: Only when diff contains `SCRIPT` or `CODE` files (same gate as deep mode). Include changed file list with detected languages/frameworks in the prompt.
- **`project-context-analyst`**: Always dispatched (same as deep mode). No scope restriction in fast mode -- the agent uses its full methodology to search git history and codebase for constraints that affect the diff. Scoping this agent reduces its effectiveness because it misses constraint forms not explicitly listed in the prompt.

All other agents are skipped in fast mode. Do not print skip notes for agents excluded by mode -- only print skip notes for agents excluded by their file-type gate within the active set (e.g., if fast mode is active and the diff has no CODE files, print the security-audit skip note).

**`--with-codex` in fast mode:** `codex-code-reviewer` is a deep-mode-only agent. If `--with-codex` is passed with fast mode, print:
> `--with-codex` requires `--deep` mode. Run `/quiver:review --deep --with-codex` for Codex coverage.
Then continue the fast review without Codex.

**If `review_mode = deep`:** Use the existing dispatch rules below (unchanged).

### Deep mode dispatch rules

- **`waste-detector`**: Always dispatched. Evaluates every changed file for unnecessary additions, redundancy with existing codebase, dead paths, and over-engineering.
- **`project-context-analyst`**: Always dispatched. Searches git history, project memory, and docs for institutional knowledge relevant to the changed files. Provides context that informs other agents' findings.
- **`security-audit`**: Only dispatched when the diff contains at least one `SCRIPT`, `CODE`, or `CONFIG-APP` file. Skip when all files are `PROMPT`, `DOCS`, or `CONFIG-MANIFEST`:
  > Skipping security-audit: no application code, scripts, or security-relevant configuration changed.
- **`best-practices-researcher`**: Only dispatched when the diff contains at least one `SCRIPT` or `CODE` file. Configuration files (both `CONFIG-APP` and `CONFIG-MANIFEST`) do not trigger this agent since they lack framework/library code to research. If dispatched, its prompt must include the list of changed files with their detected languages/frameworks so it can target its context7 lookups. Skip with a note otherwise:
  > Skipping best-practices-researcher: no application code or scripts changed.
- **`architecture-strategist`**: Only dispatched when the diff contains at least one `SCRIPT`, `CODE`, or `CONFIG-APP` file. If dispatched, its prompt must include the project's root file listing (`ls` of the project root) so it can map conventions in Phase 1. Skip when all files are `PROMPT`, `DOCS`, or `CONFIG-MANIFEST`:
  > Skipping architecture-strategist: no application code, scripts, or structural configuration changed.
- **`developer-experience-auditor`**: Only dispatched when the diff contains at least one `SCRIPT` or `CODE` file. Evaluates discoverability, error message quality, debugging experience, and automation-readiness. Skip when no code/scripts changed:
  > Skipping developer-experience-auditor: no application code or scripts changed.
- **`logic-reviewer`**: Only dispatched when the diff contains at least one `SCRIPT` or `CODE` file. Traces each changed function's inputs through branches to verify logical correctness. Skip when all files are `PROMPT`, `DOCS`, or `CONFIG-MANIFEST`:
  > Skipping logic-reviewer: no application code or scripts changed.
- **`test-reviewer`**: Only dispatched when the diff contains at least one `SCRIPT` or `CODE` file. Evaluates test assertion strength, regression detection power, and risk-based coverage gaps. Skip when all files are `PROMPT`, `DOCS`, or `CONFIG-MANIFEST`:
  > Skipping test-reviewer: no application code or scripts changed.
- **`stress-tester`**: Only dispatched when the diff contains at least one `SCRIPT` or `CODE` file. Constructs failure scenarios via assumption stress, composition fracture, and cascade chains. Receives depth calibration context: diff manifest file types + detected risk signals. Skip when all files are `PROMPT`, `DOCS`, or `CONFIG-MANIFEST`:
  > Skipping stress-tester: no application code or scripts changed.
- **`codex-code-reviewer`**: Only dispatched when ALL three conditions are met: (1) `$ARGUMENTS` contains `--with-codex`, (2) the `codex` CLI is detected on PATH, and (3) the diff is 2000 lines or fewer. This agent is a transport adapter that delegates the review to OpenAI Codex via the `codex` CLI; the actual reviewing is performed by Codex, not Claude. The Codex agent runs in parallel with all qualifying Claude review agents, providing cross-model "third eye" coverage. The CLI presence check is a Bash tool call the orchestrator performs at dispatch time (`command -v codex >/dev/null 2>&1 && echo PRESENT || echo MISSING`); do not place this check inside a `!` block in this command file (R3 forbids logic-bearing pipes in shell blocks). The diff line count is already available from the diff captured in Step 1 (`wc -l` on the diff output). Skip with notes otherwise:
  > Skipping codex-code-reviewer: --with-codex flag not provided.
  > Skipping codex-code-reviewer: codex CLI not found on PATH. Install with `npm install -g @openai/codex` (>= 0.123.0) or run `/codex:setup` from the openai/codex-plugin-cc plugin.
  > Skipping codex-code-reviewer: diff exceeds 2000 lines ({actual_count} lines). Codex review is skipped for large diffs to avoid excessive token consumption and timeouts.
- **`report-checker`**: Never dispatched in Step 2. This agent is a post-synthesis quality gate, dispatched only in Step 3.5 after the report is assembled. Skip silently during agent discovery.
- **`senior-reviewer`**: Never dispatched in Step 2. This agent is a post-quality-check senior review, dispatched only in Step 3.75 after report-checker completes. Skip silently during agent discovery.
- **`fix-reviewer`**: Never dispatched in Step 2. This agent is a post-senior-review fix-proposal check, dispatched only in Step 3.9 after senior-reviewer completes. It lives under `agents/debug/`, so Step 2a's discovery never sees it. Skip silently during agent discovery.
- **Future agents**: Add a row to the `## Dispatch Gates` table in `.claude/rules/review-agent-rules.md` before the agent's first review run, then restate that row here. The table row is the gate. Until a row exists, the agent is dispatched on every diff regardless of what changed, and `tests/skills/test-review-dispatch-contract.sh` fails until one is added -- dispatching too much is recoverable, silently reviewing nothing is not.

Spawn qualifying agents simultaneously using multiple Agent tool calls in a single response. Use the `quiver:{name}` identifier format described above as the `subagent_type`.

Each agent receives (in this order):
1. The **Diff Manifest** from Step 1.5.
2. A **scope reminder**: "Your findings MUST be scoped to code CHANGED in this diff. Respect file classifications in the Diff Manifest."
3. **Review context**: mode used, branches, PR URL (if applicable).
4. **Re-review context** (if applicable): "This is re-review iteration {N}. ONLY flag issues that are NEW in the delta since the previous review or regressions of previously-fixed findings. Do NOT flag pre-existing patterns, stylistic preferences, or aspirational improvements. If the delta contains no functional changes, return zero findings."
5. The **full diff** from Step 1. For re-reviews, also include the delta diff (`git diff {previous_head_sha}...HEAD`).
6. **File scope reminder**: "Review ALL file types in the diff regardless of language or type -- shell scripts, config files, CI configs, and build scripts deserve the same scrutiny as application source code."
7. **Citation accuracy**: "Every file:line reference in your findings must be verified by reading the file. Do not cite line numbers from memory or inference -- use the Read tool to confirm the content at the cited line before including it in a finding."
8. **Navigation availability** (for waste-detector, architecture-strategist, stress-tester, and project-context-analyst): `codegraph_available: {true|false}` and `lsp_available: {true|false}` from Step 1.75. These agents search the broader codebase and benefit from CodeGraph/LSP-first navigation. Other agents are diff-scoped and do not need these flags.
9. **Scope discipline**: Aspirational improvements, stylistic preferences, "could be better" suggestions, and theoretical hardening are out of scope. Flag only concrete demonstrable problems with code that is wrong, unsafe, or broken as written. If the code works correctly as written and you would not fix it yourself, do not flag it. Zero findings is a correct and expected result on clean code. (This clause applies on every review. Re-review mode adds additional delta-specific scope on top of this general lock.)
10. **Global Constraints** (only when Step 1.8 produced a non-empty block). Skip this item entirely when the block is empty -- do not emit the heading, an empty list, or a "no constraints" line. When the block is non-empty, append it exactly as written below, substituting the discovered plan path and the block text with no edits of your own:

    ```
    ## Global Constraints (from {plan path})

    These bind the change under review. They cut both ways:
    - A change in the diff that violates one of these is a finding, at whatever
      severity the violation earns.
    - A finding whose recommendation would require violating one of these is not a
      finding. Discard it and emit a one-line SUPPRESSED entry naming the constraint
      that ruled it out.

    {verbatim block}
    ```

    Pass the block through unchanged. Do not renumber it, summarize it, split it per agent, or add constraints of your own -- every agent receives the same text, and Step 3 relies on the agents' `SUPPRESSED` entries naming constraints the block actually contains.

### Adding future agents

- **Review-scoped agents:** Create under `agents/review/` and register in `plugin.json`'s `agents` array. The orchestrator discovers them automatically via Tier 1.
- **Cross-category agents:** Create under `agents/<category>/`, register in `plugin.json`, and add the path to the Tier 2 list in Step 2a. Add a dispatch rule in Step 2b.

**No fallback polling.** After dispatching agents, wait for the harness's completion notification before moving to Step 3 -- never call `ScheduleWakeup` as a hedge against a missed notification. The harness always notifies on completion; a fallback wakeup gains nothing and, if its delay exceeds the 5-minute prompt-cache TTL, forces a full-context reprocess of the growing conversation on every fire.

## Step 3 -- Synthesize Findings

After **all** agents return, merge their outputs into a single unified report.

### Synthesis mode

**If `review_mode = fast`:** Use the simplified synthesis rules below. **If `review_mode = deep`:** Use the full synthesis rules (items 0-9 with subsumption and proportional floor).

### Fast mode synthesis

With 5 agents, the finding volume is low enough to skip the heavy-duty noise reduction designed for 10+ agent output.

0. **Filter on substance, not citation form.** Same as deep mode item 0 -- correct citations rather than discard findings.
1. **Deduplicate.** If 2+ agents flag the same issue, keep the more detailed finding and note both agents. No consensus tracking (5 agents rarely produce 3+ consensus).
2. **Unified severity.** Same scale and definitions as deep mode (Critical/High/Medium/Low).
3. **Tag source.** Same format: `[ID] [SEVERITY] (agent-name) file:line -- title`.
4. **Filter false positives.** Apply 5 filters only:
   - Prompt-vs-code confusion (agent treats prompt text as executable code)
   - Out-of-scope findings (references code not changed in diff)
   - Phantom citations (graduated check with recovery -- same as deep mode item 4 sub-items a/b/c)
   - Severity inflation (hypothetical scenario -> downgrade to Low)
   - Constraint-blocked (finding carries a `SUPPRESSED` entry, or its recommendation cannot be acted on without violating a Global Constraint) -> DISCARD, recorded as filtered with classification `constraint-blocked` and the constraint named. Same rule as deep mode item 4, so both modes behave identically; never fires when Step 1.8 produced no block.
5. **Unified verdict.** Same rules as deep mode.
6. **Identify strengths.** Same rules as deep mode.
7. **Assign a disposition to every finding.** Same rules as deep mode item 7, including the rule that a finding whose own body argues against acting now cannot be **Before merge**.
8. **Compute fix order.** Same rules as deep mode item 8.
9. **Populate findings overview.** Same format as deep mode.

**Skipped in fast mode:**
- Subsumption (parent-child merging) -- finding volume too low to need it
- Proportional severity floor (Profile A/B/C) -- designed for 10-agent output volumes
- Consensus tracking with severity upgrade -- 5 agents rarely produce 3+ consensus given non-overlapping scopes
- Contradictions filter -- rare with 5 non-overlapping agents
- Aspirational refactoring filter -- agents' discipline rules already suppress this
- Subjective style filter -- same
- Misapplied doc lookups filter -- best-practices-researcher already handles this internally

### Deep mode synthesis

Follow these rules:

**0. Filter on substance, not citation form.** When a finding's underlying observation is verifiable in the codebase but its citation is malformed (wrong line number, off-by-N, points to a blank line or unrelated content), **correct the citation rather than discard the finding**. Use grep or file search to locate the described content; if found, update the `file:line` reference and keep the finding. Only discard as a phantom citation when the described content does not appear anywhere in the cited file (true fabrication). Do not use citation-format filters to drop findings whose underlying defects you have verified to exist. The phantom-citation filter (item 4 below) exists to suppress hallucinations, not to dismiss substantive observations on a technicality. This rule applies to every agent's output but is most relevant for external transport adapters like `codex-code-reviewer`, where line-number drift between diff hunk position and absolute file line is a common LLM error.

1. **Deduplicate with consensus tracking.** If two or more agents flag the same issue (e.g., waste-detector's Redundancy Scan and architecture-strategist both flag unnecessary duplication, or security-audit and best-practices-researcher both flag an unsafe dependency pattern), keep the more detailed finding and discard the other. Prefer the specialist agent's version when depth is comparable. **Record which agents flagged it** -- when 2+ agents independently flag the same issue, add a `Flagged by:` annotation listing all agents. Multi-agent consensus increases confidence; when 3+ agents flag the same issue, consider upgrading its severity by one tier (e.g., Medium -> High) unless it is already Critical.

   **Subsumption rule.** After deduplication, check for parent-child relationships between remaining findings. If a narrow finding is a direct symptom, consequence, or subset of a broader finding, **absorb** the narrow finding into the broader one instead of listing it separately. **Parent selection:** Choose the finding that better explains the root cause or connects to project conventions/architecture as the parent -- not necessarily the one with higher severity. A LOW finding that explains "this breaks the project's convention X" is a better parent than a HIGH finding that only says "unused import." After absorption, re-evaluate the parent's severity considering the absorbed findings' consensus signals. Add an `Also noted:` line under the parent finding listing the absorbed item(s) and which agents flagged them. Do not count absorbed findings as separate entries in severity tallies or the fix order table. **Guard:** Only absorb when the narrow finding would be **automatically resolved** by fixing the parent finding. If fixing the parent would NOT eliminate the narrow finding, they are independent -- list both separately. Example:
   Example: A diff replaces library A with library B. The architecture-strategist flags the migration as a HIGH architectural concern. The waste-detector separately flags a leftover import from library A as LOW. Since removing library A automatically eliminates the stale import, the LOW finding is absorbed:
   ```
   [HIGH] (architecture-strategist) models/foo.dart -- Library A replaced with Library B, breaking codebase convention
   Flagged by: architecture-strategist, project-context-analyst
   Also noted: Stale library-A import left behind (flagged by 5 agents) -- automatically resolved by completing the migration.
   ```
2. **Unified severity.** Reclassify all findings into a single scale:
   - **Critical** -- Must fix before merge. Actively exploitable vulnerabilities, data-loss bugs, auth bypass. CI secret exposure (logs, artifacts) qualifies.
   - **High** -- Strongly recommended. Performance regressions, authorization gaps, unsafe patterns. CI issues that silently produce wrong results or deploy wrong artifacts qualify.
   - **Medium** -- Should fix. Best-practice violations, maintainability concerns, defensive gaps. CI configuration failures that cause visible build errors (missing dependencies, wrong paths) are capped here -- a failing CI pipeline is a guardrail working as intended.
   - **Low** -- Optional. Style nits, hardening opportunities, future considerations.

   **CI severity cap:** Configuration issues that cause CI to fail visibly (build errors, missing tools, wrong paths) are capped at Medium. Reserve High for CI issues that silently produce wrong results or expose secrets. Rationale: a failing CI pipeline blocks bad code from merging -- it is self-evident on first run and easily fixed.
3. **Tag the source.** Prefix each finding with the agent that produced it for traceability. When 2+ agents flagged the same issue, include the `Flagged by:` annotation:
   ```
   [ID] [SEVERITY] (waste-detector) file_path:line_number -- Short title
   Flagged by: waste-detector, architecture-strategist
   ```
   The `Flagged by:` line only appears when 2+ agents independently flagged the same issue.
4. **Filter false positives.** Before finalizing, apply these noise filters:
   - **Prompt-vs-code confusion**: If an agent flagged a security or code quality issue in a `PROMPT` file and treats the prompt text as executable code (e.g., "shell injection" in a `!backtick` block, "missing input validation" on a CLI instruction) → DISCARD. Record as filtered false positive.
   - **Misapplied doc lookups on prompts**: If an agent used context7 doc lookups to flag CLI tool usage, shell syntax, or framework mentions in a `PROMPT` file as "best practice violations" (e.g., "deprecated CLI flag", "missing error handling in shell example") → DISCARD. Only keep doc-sourced findings on prompt files if they identify a genuinely broken or deprecated API reference.
   - **Contradictions**: If two agents produce contradictory findings (one says "add X", another says "remove X") → keep the one aligned with existing codebase conventions, discard the other. If neither aligns, discard both. Record as filtered contradiction.
   - **Out-of-scope findings**: If a finding references code NOT changed in the diff and does not argue that the diff worsened it → DISCARD. Record as filtered out-of-scope.
   - **Severity inflation**: If a finding's severity relies on a hypothetical scenario ("an attacker could...", "in the future this might...") rather than a concrete, demonstrable consequence → DOWNGRADE to Low. If it was already Low, keep it.
   - **Aspirational refactoring**: If a finding suggests restructuring working code for theoretical cleanliness, extensibility, or "better design" without identifying a concrete problem → DISCARD. Record as filtered aspirational.
   - **Constraint-blocked**: If a finding carries a `SUPPRESSED` entry from its agent, or its recommendation cannot be acted on without violating one of the Global Constraints passed as per-agent context item 10, it is not a finding -> DISCARD. Record as filtered with classification `constraint-blocked` and name the constraint that ruled it out, so the developer can see what the plan committed to rather than re-litigating it. This filter never fires when Step 1.8 produced no block. It does not run in the other direction: a change in the diff that violates a constraint stays a finding at whatever severity it earned.
   - **Subjective style opinions**: If a finding flags naming, formatting, or structural preferences where reasonable developers would disagree → DISCARD. Record as filtered stylistic.
   - **Phantom citations**: For each finding with a `file_path:line_number` reference, verify the citation. Apply this graduated check (per Step 3 item 0, do NOT default to DISCARD on the first mismatch):
     - **(a) `file_path` must exist in the repository.** If not → DISCARD as filtered phantom citation. (True fabrication: cited file does not exist.)
     - **(b) `line_number` must fall within the file's actual line count.** If not → DISCARD as filtered phantom citation. (True fabrication: cited line is past EOF.)
     - **(c) If the finding describes specific content at that line and the cited line's actual content does NOT match**, do not discard immediately. **Recovery procedure:** Search the file for the described content (grep distinctive snippets, key tokens, or quoted phrases from the finding body). Three outcomes:
       1. **Found at a different line:** correct the citation to the new line and keep the finding. Add a brief `Citation corrected: original line N -> actual line M` note in the finding body for transparency.
       2. **Found but ambiguous (multiple plausible matches):** keep the finding with the original citation and add `Citation note: line uncertain, content present in file at lines [list]`. Do not discard.
       3. **Not found anywhere in the cited file:** this is the true fabrication case → DISCARD as filtered phantom citation.
     - This filter catches agent hallucinations where findings cite non-existent code or fabricated content. It does NOT catch findings whose underlying observation is real but whose line citation drifted; those are corrected per the recovery procedure above. Self-protective filtering — using citation drift as a pretext to drop substantive findings, especially against one's own earlier work — is the failure mode this rule prevents.

**4a. Proportional severity floor.** After applying the 9 false-positive filters above, apply a diff-shape filter to Low findings only. Medium, High, and Critical findings are never affected by this rule.

Compute the diff profile from the Diff Manifest (Step 1.5) and the diff line count:

- **Profile A** (strict floor): zero `CODE`/`SCRIPT`/`CONFIG-APP` files, OR diff has `CODE`/`SCRIPT` but is under ~100 changed lines AND contains no risk signals (auth, payments, secrets, CI workflow changes). **Rule:** drop all Low findings. Record each drop in Filtered Findings with reason "Proportional floor (strict)".
- **Profile B** (consensus floor): diff is 100-250 changed lines, no high-risk signals. **Rule:** keep Low findings only when 2+ agents flagged the same issue (use the `Flagged by:` consensus annotation from Step 3.1). Drop single-agent Lows. Record each drop in Filtered Findings with reason "Proportional floor (consensus)".
- **Profile C** (no floor): any high-risk signal is present (auth, payments, secrets, CI workflow changes), OR diff is over 250 changed lines. **Rule:** no filter applied. Current behavior preserved.

Risk signals are detected from the Diff Manifest: any `CONFIG-APP` file touching auth or secrets, any file under a `payments/` or `auth/` path, any CI workflow file (`.github/workflows/*.yml`, `.gitlab-ci.yml`), any file matching `secrets|credentials|keys|tokens` in its name.

The proportional floor runs AFTER subsumption (Step 3.1) and the 9 filters (Step 3.4) so that dropped findings have already been deduplicated. Dropped findings still appear in the Filtered Findings section with their drop reason, preserving transparency.

**No promotion to escape the floor.** Severity is assigned based on concrete consequence, not on whether a finding will survive the proportional floor. Do NOT reclassify a finding from Low to Medium solely because the current profile would drop Lows. If a finding is genuinely Low under the severity rubric, drop it (record in Filtered Findings) -- do not launder it into Medium to preserve it in the report. The floor is a synthesis-stage noise filter, not an incentive to inflate severity. Violating this rule reintroduces the exact noise pattern the floor exists to suppress. When in doubt, ask: "Would I assign this severity if no filter existed?" If the honest answer is Low, keep it Low.

5. **Unified verdict.** Apply the strictest verdict across all agents (using only non-filtered findings):
   - If **any** agent produces a Critical or High finding --> **Request changes**
   - If the worst finding is Medium --> **Approve with suggestions**
   - If only Low or no findings --> **Approve**
6. **Identify strengths.** From agent outputs and diff analysis, identify 2-5 positive aspects of the changes. Look for:
   - Net negative LOC (code removal is good)
   - Correct use of established project patterns
   - Good test coverage additions
   - Proper error handling
   - Clean abstractions or well-chosen framework conventions
   If the diff has no notable strengths, omit the "What's Working Well" section rather than fabricating praise.
7. **Assign a disposition to every finding.** Every finding that survives filtering carries exactly one disposition, Low findings included. Severity says how big the consequence is; disposition says what the reader does about it, and a report that states only the first leaves every Low finding unowned:
   - **Before merge** -- the change is not safe to ship without this. Critical and High start here.
   - **Follow-up** -- real, worth an issue, not worth holding the merge.
   - **Defer** -- correct as an observation, but the cost or the blast radius is wrong for now.

   Severity does not decide the disposition on its own. A High whose fix is a one-word doc correction is still **Before merge**; a Medium that needs a shipped file touched can be **Follow-up**. State the reason in the disposition line when it is not the default for that severity.

   **A finding cannot be assigned Before merge when its own body argues against acting now.** Read the finding's text for a concession -- "eventually rather than now", "not now", "worth doing when", "either answer is defensible", "when the team wants it". A finding carrying one is **Defer**, and it keeps its place in `## Findings` with its severity intact. The reader is told what to skip; the finding is not deleted to achieve that. This check reads the finding's own words, so it does not depend on re-judging the defect.

   Write the disposition on its own line directly under the finding's ID block:
   ```
   Disposition: Before merge | Follow-up | Defer -- {reason, only when it is not the default for this severity}
   ```
8. **Compute fix order.** Rank every finding whose disposition is **Before merge**, then every finding whose disposition is **Follow-up**, into the `## Recommended Fix Order` table. Within one disposition:
   1. Severity (Critical first)
   2. Dependency (if fix A must happen before fix B, A goes first)
   3. Effort (quick wins before large refactors within same severity)
   **Defer** findings do not enter the table -- their disposition line is the whole instruction. Never omit the table: when no finding is Before merge or Follow-up (every finding deferred, or no findings at all), the table still prints, carrying the single row `| -- | -- | Nothing blocks the merge | -- | -- | -- |`, so a reader learns that from the report rather than from its absence.
9. **Populate findings overview.** After all filtering, deduplication, and severity assignment, count findings per severity tier. Write the totals into the `Findings overview` line in `## Review Context`. Use the format: `X Critical, Y High, Z Medium, W Low (N filtered)`. Omit tiers with zero findings (e.g., `2 High, 1 Medium (3 filtered)` instead of `0 Critical, 2 High, 1 Medium, 0 Low`).

### Synthesized report structure

```markdown
# Code Review Report

## Review Context
- **Branch**: {current branch name}
- **Mode**: {branch diff | PR | uncommitted} ({fast | deep})
- **Iteration**: {1 if first review, N if re-review}
- **Previous report**: {path or "N/A"}
- **Scope**: {Full diff | Delta-only (changes since previous review)}
- **Delta**: {commit_count} commits, {files_changed} files since previous review (omit for first review)
- **HEAD at review**: {output of `git rev-parse --short HEAD`}
- **Global Constraints**: {plan path the block came from, or "N/A"}
- **Findings overview**: {X Critical, Y High, Z Medium, W Low} ({N filtered})
- **Dispositions**: {X before merge, Y follow-up, Z deferred}

## Summary
One paragraph: what the PR does, overall risk, top-line recommendation.

## Agents Dispatched
{list each dispatched agent and its verdict}
{In fast mode: note that this was a fast review with 5 core agents. Do NOT list every skipped deep-mode agent -- only note agents skipped within the active set due to file-type gates.}
{In deep mode: list all discovered agents including those skipped with reasons, same as current behavior.}

## What's Working Well
{2-5 bullet points highlighting positive aspects of the changes. Each item is one sentence, no severity ratings. Omit this section entirely if the diff has no notable strengths -- do not fabricate praise.}

## Architectural Assessment
{If architecture-strategist ran: include its Architecture Context (3-5 bullets) and Structural Summary here. If it did not run or returned empty, omit this section entirely.}

## Findings

Each finding gets a short ID: severity initial + sequence number (C1, C2... for Critical; H1, H2... for High; M1, M2... for Medium; L1, L2... for Low). These IDs are stable within a report and can be used to reference findings concisely (e.g., "except L1", "fix H2 first").

Every finding carries a `Disposition:` line directly under its ID block, from Step 3 item 7. It is not optional and it has no default -- a finding with no disposition line is a finding whose reader has to guess.

### Critical
[C1, C2, ... merged critical findings]

### High
[H1, H2, ... merged high findings]

### Medium
[M1, M2, ... merged medium findings]

### Low
[L1, L2, ... merged low findings]

{For findings flagged by 2+ agents, include the annotation: "Flagged by: agent1, agent2"}

## Senior Assessment
{If senior-reviewer ran: team lead's overall assessment, meta-review observations, and any finding modifications with justification. Omit this section entirely if senior-reviewer did not run or returned no assessment.}

## Recommended Fix Order
{Every finding whose disposition is Before merge, then every finding whose disposition is Follow-up, at any severity. Deferred findings are listed in the Deferred block below instead. This section is never omitted.}

| Priority | ID | Finding | Severity | Disposition | Effort |
|----------|----|---------|----------|-------------|--------|
| 1 | C1 | [Short title with file:line] | Critical | Before merge | ~X min |
| 2 | H1 | [Short title with file:line] | High | Before merge | ~X min |
| 3 | L2 | [Short title with file:line] | Low | Follow-up | ~X min |
| ... | ... | ... | ... | ... | ... |

**Deferred:** {comma-separated finding IDs with a half-line reason each, e.g. "L3 -- extracting the helpers means touching a shipped file in this PR". Write "None." when nothing was deferred.}

## Filtered Findings

**{N} findings reported, {M} filtered** ({classification breakdown, e.g., "3 out-of-scope, 2 aspirational, 1 constraint-blocked, 1 subjective style"})

- [brief reason for each, e.g., "~~[M3] [Medium] (waste-detector) config/routes.rb:15 -- Consider extracting nested routes~~ -- Aspirational: working code, no concrete problem"]
- [constraint-blocked entries name the constraint, e.g., "~~[M4] [Medium] (logic-reviewer) skills/plan/SKILL.md:212 -- Compute the newest plan inline in the shell block~~ -- Constraint-blocked: Global Constraint 2 (no new shell logic in `!` blocks)"]

(Omit this section entirely if no findings were filtered.)

## Verdict
[Unified verdict] -- [severity counts] -- [one-line justification]
```

<!-- SYNC: This report format is parsed by skills/work/SKILL.md, section `#### 4c -- Review finding verification (review-fix plans only)`. If you change the report structure (section headings, finding format), update the verification parsing logic there. New sections (What's Working Well, Recommended Fix Order, Senior Assessment) are additive and do not affect Phase 4c parsing. Step 3.5 and Step 3.75 below may modify findings (remove, downgrade, rewrite, promote, add) before Step 4 saves the report; Step 3.9 modifies only the fix block inside a finding and never the finding itself. -->

## Step 3.5 -- Report Quality Check

**If `review_mode = fast`:** Skip this step entirely. The report-checker is designed to catch noise from 10+ agents; with 5 focused agents and simplified synthesis, the noise level does not justify an additional agent spawn. Proceed directly to Step 3.75.

After synthesis, dispatch the `report-checker` agent for an independent quality audit. This step catches noise, false positives, and proportionality issues that survive the Step 3 filters.

1. **Dispatch.** Spawn `quiver:report-checker` with:
   - The full synthesized report (the markdown string from Step 3)
   - The original diff (same diff passed to agents in Step 2)
   - Do NOT pass individual agent outputs -- the checker evaluates the report as a reader would.

2. **Handle results:**
   - **Zero issues:** Print `Quality check passed -- report is ready.` Proceed to Step 4.
   <!-- SYNC: The apply-fixes procedure below (REMOVE/DOWNGRADE/REWRITE actions + recalculation steps) is duplicated in skills/report-check/SKILL.md Step 4 "Apply fixes" block. Keep both in sync. -->
   - **Issues found:** Apply the recommended actions:
     - REMOVE: Delete the finding from the report.
     - DOWNGRADE: Change the finding's severity and move it to the correct section.
     - REWRITE: Replace the finding's recommendation text with the corrected version.
   - After applying fixes, recalculate:
     - Findings overview counts in `## Review Context`
     - Disposition counts in `## Review Context`, and the `**Deferred:**` line under the fix order table
     - Severity section contents (move downgraded findings, remove deleted ones)
     - Recommended Fix Order table (remove entries for deleted/downgraded findings)
     - Verdict line (recompute based on remaining finding severities)
   - Print: `Quality check: {N} issues found and fixed.`

3. **Retry (max 1).** Re-dispatch `report-checker` with the corrected report.
   - **Zero issues on retry:** Proceed to Step 4.
   - **Issues remain on retry:** Proceed to Step 4 anyway. Do NOT retry again. Append a `## Quality Check Notes` section to the end of the report (before Verdict) listing the unresolved items with their QA IDs and descriptions.
   - Print: `Quality check: {N} items remain after correction. Proceeding with the report.`

4. The max iteration count (1 retry after initial check) is a hard limit. This prevents infinite correction loops. The same discipline that applies to the report-checker agent applies here: if the report is good enough after one correction pass, stop.

**Status messages (plain language, no rule codes):**
- Before dispatch: `Running quality check on the review report...`
- These messages are user-facing and are fully covered by the plain-language scan in Step 4b.

## Step 3.75 -- Senior Review

**If `review_mode = fast`:** Skip this step entirely. The senior meta-review adds most value when synthesizing findings from many agents. With a 5-agent fast review, the orchestrator's synthesis is sufficient. Proceed directly to Step 4.

After the quality check, dispatch the `senior-reviewer` agent for a pragmatic senior developer assessment. This step provides the "team lead final verdict" -- evaluating both the code and the other agents' findings through a senior developer lens.

1. **Dispatch.** Spawn `quiver:senior-reviewer` with:
   - The full synthesized report (post-quality-check -- with report-checker fixes applied)
   - The original diff (same diff passed to agents in Step 2)
   - The Diff Manifest from Step 1.5
   - Pipeline mode context: "You are running inside the /quiver:review pipeline. Run Phase 0-4 (your own independent code review) on the diff first, then run Phase 5 (Meta-Review) on the synthesized report. The report has already been quality-checked by report-checker -- findings that were removed are out of scope. Do not attempt to recover or reference them."
   - Language context: detected languages from the Diff Manifest file extensions
   - Do NOT pass --quick flag in pipeline mode. Always run full analysis (Phase 0-4 + Phase 5).

2. **Handle results:**
   - **Zero modifications, zero new findings:** Print `Senior review passed -- no changes to report.` Proceed to Step 3.9.
   <!-- SYNC: The apply-fixes procedure below (REMOVE/DOWNGRADE/REWRITE/PROMOTE/ADD actions + recalculation steps) is a superset of the procedure in Step 3.5 and skills/report-check/SKILL.md Step 4. PROMOTE and ADD are unique to Step 3.75. Keep the shared actions (REMOVE/DOWNGRADE/REWRITE) and recalculation steps in sync across all three locations. -->
   - **Modifications or new findings:** Apply the recommended actions:
     - REMOVE: Delete the finding from the report.
     - DOWNGRADE: Change the finding's severity and move it to the correct section.
     - REWRITE: Replace the finding's recommendation text with the corrected version.
     - PROMOTE: Upgrade the finding's severity and move it to the correct section. The senior-reviewer must provide justification for promotion.
     - ADD: Insert a new finding into the appropriate severity section, with a `Disposition:` line assigned by the Step 3 item 7 rules. New findings from senior-reviewer use the prefix SR (SR1, SR2, etc.) to distinguish them from original agent findings. The senior-reviewer must cite the file and line for each added finding.
   - After applying fixes, recalculate:
     - Findings overview counts in `## Review Context`
     - Disposition counts in `## Review Context`, and the `**Deferred:**` line under the fix order table
     - Severity section contents (move promoted/downgraded findings, remove deleted ones, insert added ones)
     - Recommended Fix Order table (update entries for promoted/downgraded findings, add entries for new findings, remove deleted ones)
     - Verdict line (recompute based on remaining finding severities)
   - Print: `Senior review: {N} modifications, {M} new findings.`

3. **Senior Assessment section.** If the senior-reviewer produced an overall assessment, insert a `## Senior Assessment` section in the report after `## Findings` and before `## Recommended Fix Order`. This section contains the team lead's summary and any meta-review observations. Omit this section if the senior-reviewer returned no assessment text.

4. **No retry.** Unlike report-checker, the senior-reviewer does NOT get a retry. One pass only. Proceed to Step 3.9.

**Status messages (plain language, no rule codes):**
- Before dispatch: `Running senior developer review (independent code review + meta-review of findings)...`
- After completion: `Senior review complete.` or `Senior review: {N} modifications, {M} new findings.`

## Step 3.9 -- Fix Proposal Check

**If `review_mode = fast`:** Skip this step entirely. Proceed to Step 4.

Every step up to here verifies that a finding describes a real defect. Nothing has yet verified the fix printed under it. A wrong snippet in a High finding is worse than no snippet -- it is the version the reader pastes, and it arrives carrying the authority of a report that was right about the defect.

Run this step only when at least one finding carries a fix: a fenced code block, a patch, or a concrete "replace X with Y" instruction. When no finding carries one, print `No fix proposals to check.` and proceed to Step 4.

1. **Dispatch.** Spawn `quiver:fix-reviewer` with:
   - Every finding that carries a fix, as a numbered proposal list. Give each one the finding ID, its severity, its `file:line`, the defect description as the root cause, and the fix verbatim.
   - The original diff from Step 1 and the Diff Manifest from Step 1.5.
   - This scope context, verbatim:

     ```
     These are fix proposals from a code review report, not applied changes. Review the
     fixes only. Do not re-litigate whether the defect is real, do not propose fixes for
     defects no proposal targets, and do not change any finding's severity.

     Read the file each proposal edits before flagging a convention violation or a side
     effect. Add one check to your Phase 3: a proposal whose comment, doc comment, or
     surrounding prose states a behaviour its own code does not produce is a FLAG under
     CONVENTION_VIOLATION -- quote both halves and say which one is wrong.

     A proposal that cannot be implemented on this project's platform or language as
     written -- a subclass of a type the platform forbids subclassing, an override on a
     method the class does not expose, an API unavailable at the declared minimum version
     -- is a REJECT, naming the specific restriction.
     ```

2. **Handle results.** Every action lands on the fix, never on the finding:
   - **APPROVE:** leave the finding untouched.
   - **FLAG:** replace the fix block with the corrected version, and add a one-line `Fix corrected:` note under it naming what was wrong with the original.
   - **REJECT:** delete the fix block and put `No verified fix -- {one line naming why the proposed one does not work}` in its place.

   Do not remove a finding, change a severity, or change a disposition at this step. A fix that does not work is not evidence that the defect is not there, and Steps 3.5 and 3.75 have already had their pass at the findings themselves.

3. **Recalculate.** Only the `Effort` column of the Recommended Fix Order table changes, and only for a finding whose fix was corrected or rejected; a rejected fix's effort reads `unknown`. Findings overview counts, dispositions and the verdict are unchanged by this step.

4. **No retry.** One pass only. Proceed to Step 4.

**Status messages (plain language, no rule codes):**
- Before dispatch: `Checking the fixes the report recommends...`
- After completion: `Fix check: {N} proposals reviewed, {M} corrected, {K} left without a verified fix.`

## Step 4 -- Save Review Report

### 4a -- Determine output destination

Evaluate in order:
1. **`--terminal` flag:** If `$ARGUMENTS` contains `--terminal`, print the full report in the terminal. Do not write a file. Skip to the terminal summary.
2. **`--set-output` flag:** If `$ARGUMENTS` contains `--set-output <path>`, use that path as the save directory **and** save it as the default for future reviews. **Path validation:** Before saving, verify the path matches the allowlist pattern `[a-zA-Z0-9_./ -]+` (letters, digits, dots, underscores, slashes, hyphens, spaces). Additionally, reject any path that starts with `/` (absolute paths) or where any path segment (split by `/`) equals `..` to prevent directory traversal outside the project root. Reject anything else. If invalid, warn the user and do not write the preference. Write (or update) a `review-preferences.md` file in your auto-memory directory:
   ```markdown
   # Review Preferences
   - report_path: <path>
   ```
   Confirm: > Default report path set to `<path>`. Future reviews will save here automatically.
3. **`--output` flag:** If `$ARGUMENTS` contains `--output <path>`, use that path as the save directory (one-time, not saved). Apply the same path validation as `--set-output` (allowlist pattern, reject absolute paths and `..` path segments).
4. **Saved preference:** Check auto-memory for a `review-preferences` file with a `report_path` field. If found, use that path.
5. **Default:** Use `{project_root}/.claude/reports/`.

### 4b -- Write and summarize

1. Create the chosen directory if it does not exist.
2. Write the full synthesized report as `review-{timestamp}.md` (use `date '+%Y-%m-%d_%H-%M-%S'`).
3. Draft a short terminal summary with these elements:
   - One-line verdict
   - Counts per severity
   - Which agents ran and their individual verdicts
   - If any agents were skipped for a non-trivial reason (diff too large for Codex, CLI not found, etc.), include a one-line note per skipped agent explaining why. Do NOT list agents skipped because their file-type gate did not match (those are routine and expected). Only mention skips that reduced coverage the user explicitly requested (e.g., `--with-codex` was passed but Codex was skipped).
   - Path to the saved report file
   - **Fast mode coverage advisory** (only when `review_mode = fast`): If the Diff Manifest shows 3+ `CODE`/`SCRIPT` files changed, OR the diff adds new enum cases/tiers/configuration levels, OR the diff contains UI state management code, append: `Fast review (5 agents). For full coverage including failure scenario analysis and cross-agent validation, run with --deep.` Omit the advisory on small/isolated diffs where fast mode coverage is sufficient.
4. **Pre-print scan (mandatory gate).** Before printing the drafted summary, run the scan defined in the "Status Messages: Plain Language Required" section against the draft. The summary is a live chat-stream message and is fully covered by the plain-language rule -- it is not exempt because it appears at the end of the run. If the draft contains any rule code, hash prefix, bare commit SHA, or internal invariant name, rewrite it using the plain-English replacement named in that category's own bullet, then re-scan. Only print the summary after the scan passes.
5. Do **not** print the full review in the terminal unless `--terminal` was used.

---

## Step 5 -- Post to PR (Optional)

This step enables posting the review report as a PR comment. It is **strictly opt-in** and never runs automatically.

### 5a -- Determine if PR commenting applies

Evaluate in order:

1. **`--comment-pr` flag:** If `$ARGUMENTS` contains `--comment-pr`, skip the prompt and proceed directly to 5b.
2. **PR context available:** If Mode 1 was used (a PR/MR URL was provided), ask the user:
   > Review saved. Would you like to post this report as a comment on the PR?
   Use `AskUserQuestion` with action buttons: **"Yes, post to PR"** and **"No thanks"**.
   - If the user selects "No thanks" or dismisses, **stop here**. Do not post.
3. **No PR context:** If Mode 2 or Mode 3 was used and no PR URL was provided, attempt to detect an active PR for the current branch:
   - **GitHub:** `gh pr view --json url,number --jq '.url' 2>/dev/null`
   - **GitLab:** `glab mr view --output json 2>/dev/null`
   - If detection succeeds and `--comment-pr` was passed, proceed to 5b using the detected PR.
   - If detection succeeds but `--comment-pr` was NOT passed, do not prompt -- skip silently. The user must explicitly opt in via the flag when no PR URL was provided.
   - If detection fails, skip silently. Do not warn or error.

### 5b -- Post the comment

1. **Read the saved report** from the path determined in Step 4b.
2. **Post using the platform CLI:**
   - **GitHub:** `gh pr comment {pr_number_or_url} --body-file {report_path}`
   - **GitLab:** `glab mr comment {mr_number} --message "$(cat {report_path})"`
   - For other platforms: print a note and skip:
     > PR commenting is not supported for this platform. You can manually paste the report from: `{report_path}`
3. **Confirm success:**
   > Review posted as a comment on {pr_url}.
4. **Handle failure gracefully:** If the CLI command fails (permissions, network, etc.):
   > Could not post the review to the PR. The report is saved at: `{report_path}`
   Do not retry. Do not error out.

---

## Status Messages: Plain Language Required

Every character the user sees in the terminal is read by someone who has not memorized this file. This covers mid-run status lines, `AskUserQuestion` prompt bodies and button labels, the Step 4b terminal summary, the final verdict line, and every warning, confirmation, and error message. State what you are checking in plain English with a short clause on why it matters -- the problem the check prevents, not the rule that demands it.

**Pre-print scan (mandatory gate, not a suggestion).** Before any chat-stream text leaves you -- the Step 4b summary and the verdict line included, they are not exempt for coming after the last tool call -- scan the draft for the categories below. On a match, rewrite and re-scan; text that has not passed the scan must not be printed. If you need a concept on this list and cannot find a plain-English version, omit the detail rather than leaking the jargon -- a correct but shorter status line beats a complete but cryptic one.

- **Rule codes** -- `RA`/`LA`/`R`/`L` followed by a digit, "rule N", "lesson N". Say what the rule requires: "the exact wording every review agent must carry".
- **Hash material** -- any unbroken run of 8 or more hexadecimal characters, full SHAs and `5fc168ad...` truncations alike. Omit it; hashes are never user-facing.
- **Bare commit SHAs** -- `[0-9a-f]{7,}` with no plain-language label. Name the commit by what it did: "the commit that added the status-message section".
- **Internal invariant names** -- "canonical text", "byte-identical", "drift check", "exemption variant", "subsumption rule", "proportional severity floor", "Profile A/B/C", "diff manifest", "discipline section", "stability test". Say what the thing does: "the classified list of changed files", "a filter that drops low-severity findings on small diffs", "the 'would I still flag this cold tomorrow' check".
- **Section references into the rule files** -- "Step 2 item 9", "sub-item 4a", "hard rule N". Name the check, not its address.

**What stays technical:** file paths, agent names (`waste-detector`, `project-context-analyst`), line and file counts, severities (Critical/High/Medium/Low), commit counts in a delta. Users expect these. The ban covers only terms that need the Quiver rule files to parse, and the saved report file on disk is the one place they are allowed.

---

## Anti-Patterns

- **Don't** prompt the user for input **between base branch confirmation and report save** -- the review itself runs end-to-end without interaction until the save-location prompt in Step 4.
- **Don't** silently assume `main` or `master` as the base branch in Mode 2 -- always confirm with the user or require `--base`.
- **Don't** dump the full review into the terminal -- write it to the report file and show only the summary (unless the user chose "Show in terminal").
- **Don't** save review reports to system temp directories (`/tmp/`) -- always save inside the project or show in terminal, per the user's choice.
- **Don't** skip the mode announcement -- the user must know which diff source is being reviewed.
- **Don't** use two-dot `git diff <base>..<head>` for branch diffs -- two-dot diffs include unrelated upstream changes. Bare `git diff` (no arguments) is correct for Mode 3 uncommitted changes.
- **Don't** run agents sequentially -- always dispatch all agents in parallel (multiple Agent tool calls in one response).
- **Don't** present raw agent outputs side-by-side -- always synthesize into a single merged report with deduplication.
- **Don't** let duplicate findings from different agents inflate severity counts -- deduplicate before counting.
- **Don't** ignore saved review preferences -- always check auto-memory for a `review-preferences` file before defaulting in Step 4.
- **Don't** ignore the `--output` flag when provided.
- **Don't** post a PR comment without explicit user consent -- `--comment-pr` flag or interactive confirmation are the only valid triggers.
- **Don't** prompt to post a PR comment when no PR context exists (Mode 2/3 without `--comment-pr`) -- skip silently.
- **Don't** hardcode platform tokens, repository URLs, or API endpoints -- rely on `gh`/`glab` CLIs which manage their own authentication.
- **Don't** retry or error out if PR comment posting fails -- warn and move on.
- **Don't** narrate your work to the user using internal rule codes, SHA hashes, or invariant names -- every chat-stream status line must follow the "Status Messages: Plain Language Required" section above. The saved report body is the only place rule codes belong.
- **Don't** dispatch deep-mode-only agents in fast mode -- the mode gate in Step 2b is the source of truth for which agents run.
- **Don't** promote `--with-codex` usage when in fast mode -- print the "requires --deep" note and continue.
