---
name: discovery
user-invocable: false
tags: [quality, discovery, probes, issues]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when running systematic quality discovery and issue detection. Runs modular probes
  adapted to the project's tech stack, presents findings interactively
  for user triage, and creates VCS issues for confirmed problems.
  Invoked standalone via /discovery or embedded in session-end.
---

# Discovery Skill

## Invocation Modes

Two modes of operation:

- **Standalone** (`/discovery [scope]`): Full 6-phase flow with interactive triage (Phases 0-6)
- **Embedded** (from session-end when `discovery-on-close: true`): Phases 0-4 only, returns structured findings to session-end

<!-- scope-enum SSOT (#762): this line is the canonical token list; the wiring test derives SCOPE_TOKENS from it. Add/remove tokens HERE first, the test guards the other surfaces. -->
The `scope` argument accepts: `all` (default), `code`, `infra`, `ui`, `arch`, `session`, `audit`, `vault`, `feature`, or comma-separated like `code,session`.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## Phase 1: Read Session Config

Read and parse Session Config per `skills/_shared/config-reading.md`. Store result as `$CONFIG`.

Discovery-relevant fields (parse these specifically):
- `discovery-on-close`, `discovery-probes`, `discovery-exclude-paths`, `discovery-severity-threshold`, `discovery-confidence-threshold`, `discovery-parallelism`
- `test-command`, `typecheck-command`, `lint-command`
- `pencil`, `vcs`, `cross-repos`, `stale-issue-days`

## Phase 2: Stack Detection & Probe Activation

Detect the project's tech stack via marker file checks. Use Glob and run checks in parallel:

| Marker File(s)                        | Activates               |
|---------------------------------------|-------------------------|
| `package.json`                        | JS/TS probes            |
| `tsconfig.json`                       | TypeScript probes       |
| `requirements.txt` / `pyproject.toml` | Python probes           |
| `Dockerfile` / `docker-compose.yml`   | Container probes        |
| `vercel.json` / `.vercel/`            | Vercel probes           |
| `.github/workflows/`                  | GitHub CI probes        |
| `.gitlab-ci.yml`                      | GitLab CI probes        |
| `supabase/`                           | Supabase probes         |
| `next.config.*` / `nuxt.config.*`     | SSR probes              |
| `tailwind.config.*`                   | Tailwind probes         |
| Pencil in Session Config              | design-drift probe      |
| `.orchestrator/bootstrap.lock`        | harness-audit probe     |
| `.vault.yaml` OR Session Config `vault-integration.enabled: true` | vault probes      |
| `package.json` / `requirements.txt` / `Cargo.toml` **AND** Session Config `slopcheck.enabled: true` AND `slopcheck.sources` includes `"discovery"` | supply-chain probe (`skills/discovery/probes-supply-chain.md`) |
| `docs/` directory present **AND** Session Config `docs-staleness.enabled: true` | docs-staleness probe (`skills/discovery/probes-docs.md`) |
| `CLAUDE.md` (or `AGENTS.md` on Codex CLI) or `README.md` present in repo root | ssot-code-diff probe (`skills/discovery/probes-docs.md`) — always active within the docs category, no Session Config gate |

### Build Activation Set

1. Start with all probes whose marker files are present
2. If `discovery-probes` is set in config, intersect with that list
3. If a `scope` argument was passed, restrict to that category
4. Remove probes whose activation conditions are not met

The audit probe activates when `bootstrap.lock` is present OR when `discovery-probes` config explicitly lists `audit`.

The vault probe activates when `.vault.yaml` is present in the repo root OR when `vault-integration.enabled: true` in Session Config OR when `discovery-probes` config explicitly lists `vault`.

The feature probe activates ONLY when the scope argument includes `feature` OR when `discovery-probes` config explicitly lists `feature`. It never activates under bare `all` — feature discovery is an explicitly requested scan, and its interactive router (below) cannot run in embedded mode.

### Exclude Paths

Default exclude paths (always apply):
- `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `coverage/`

Add any paths from `discovery-exclude-paths` in Session Config.

### VCS Detection

> **VCS Reference:** Detect the VCS platform per the "VCS Auto-Detection" section of the gitlab-ops skill.

### Status Report

Report: "Discovery: [N] probes active across [categories]. Stack: [detected]. Threshold: [severity]."

### Feature-Scope Router (standalone only)

Fires ONLY when the active scope set includes `feature` AND the skill is running standalone (coordinator context). In embedded mode (session-end dispatches discovery as an Explore subagent — AskUserQuestion is unavailable in subagents per `.claude/rules/ask-via-tool.md` AUQ-004), the router MUST NOT fire; proceed directly with the grounded scan as the non-interactive default.

Judgment-based PM work (opportunity framing, personas, market-sizing) deliberately stays OUT of the verified-findings pipeline (Epic #750) — this router is the fork point that keeps grounded, evidence-anchored discovery separate from open-ended product judgment.

When the gate above is satisfied, present exactly this AskUserQuestion (AUQ-003 shape) before proceeding to Phase 3:

```
AskUserQuestion({
  questions: [{
    question: "Scope `feature` was requested. How should this run handle feature discovery?",
    header: "Feature Scope",
    options: [
      { label: "Grounded scan (Recommended)", description: "Run the evidence-anchored feature probes (intent-drift, stubbed-dead-feature) on the probe→verify→triage rails." },
      { label: "Also judgment topics", description: "Grounded scan PLUS collect judgment-based product questions (opportunity framing, personas). A follow-up prompt after Phase 5 offers inline synthesis or hand-off to /brainstorm or /plan feature — judgment items never enter the verified-findings pipeline." },
      { label: "Route out", description: "No scan; hand off to /brainstorm (product ideation) or /grill (assumption stress-test) instead." },
      { label: "Skip", description: "Drop `feature` from this run's scope set." }
    ],
    multiSelect: false
  }]
})
```

**On user selection (every branch is explicit — do not fall through):**

- **"Grounded scan"** → keep `feature` in the active scope set and continue to Phase 3 unchanged.
- **"Also judgment topics"** → keep `feature` in the active scope set and continue to Phase 3 unchanged for the grounded probes. Collect any judgment-based product questions (opportunity framing, personas, market-sizing) encountered during the scan as plain notes — do not route them through Phase 4 (Verification) or Phase 6 (Issue-Creation) at any point. AFTER Phase 5 triage completes, present a SECOND AskUserQuestion that forks how the collected topics are handled:

```
AskUserQuestion({
  questions: [{
    question: "Judgment topics were collected alongside the grounded scan. How should they be handled?",
    header: "Judgment Topics",
    options: [
      { label: "Inline synthesis (Recommended)", description: "Sketch a lightweight OST/persona pass directly in the report's `### Judgment Topics (non-verified)` appendix — explicitly marked non-verified, no separate skill invocation needed." },
      { label: "Route to /brainstorm", description: "Hand the collected topics off as pre-filled context to /brainstorm for a full Socratic ideation dialogue." },
      { label: "Route to /plan feature", description: "Hand the collected topics off as pre-filled context to /plan feature for feature-PRD scoping." }
    ],
    multiSelect: false
  }]
})
```

  - **"Inline synthesis"** → append a `### Judgment Topics (non-verified)` section to the discovery report. For each collected topic, write a brief candidate outcome/opportunity sketch (Teresa Torres OST framing) and, where a persona angle is evident, a one-line persona note — every line explicitly labeled `(non-verified sketch)`. This is prose synthesis, never a probe finding.
  - **"Route to /brainstorm"** → append the same `### Judgment Topics (non-verified)` section, but render each topic as a one-line pointer plus the recommendation to invoke `/brainstorm` with the collected topic context pre-filled as its initial prompt. Do not auto-invoke `/brainstorm` — surface the recommendation and let the operator trigger it.
  - **"Route to /plan feature"** → same rendering as the `/brainstorm` branch above, pointing at `/plan feature` with the collected topic context pre-filled instead.

  **Invariant (PRD §4 Non-Goals) — holds across all three sub-branches above:** judgment items are report-appendix ONLY — they MUST NOT become findings, MUST NOT pass through Phase 4 verification, and MUST NOT produce issues in Phase 6.
- **"Route out"** → remove `feature` from the active scope set. Do NOT run the feature probes. Recommend the operator invoke `/brainstorm` or `/grill` after this run (name whichever fits the operator's question), then continue to Phase 3 with the remaining scopes — or, if `feature` was the ONLY requested scope, stop after reporting: "Feature scope routed out — no probes to run. Invoke /brainstorm or /grill directly."
- **"Skip"** → remove `feature` from the active scope set before Phase 3. If `feature` was the only requested scope, stop with: "Feature scope skipped — nothing to run."

## Phase 3: Probe Execution

### --since Filtering (when `since_ref` is provided)

When `since_ref` is set (passed from the `/discovery --since <git-ref>` invocation):

1. Call `changedFilesSince(since_ref)` from `scripts/lib/discovery/helpers.mjs`.
2. If the helper throws (ref unresolvable), surface the error to the user and halt.
3. If the result is `[]` (no files changed since the ref), emit:
   ```
   No files changed since <since_ref>. Skipping discovery.
   ```
   and exit with status 0. Do NOT fall back to a full-repo scan.
4. If the result is a non-empty array, pass it as `changedFiles` context to each probe agent below.

**Probe exemptions:** The vault-staleness probe and the harness-audit probe are EXEMPT from `--since` filtering — they always scan the full repository because their analysis targets metadata (vault narrative staleness, bootstrap lock state) that is not file-diff-gated. This exemption is advisory: no code enforcement is applied in this wave. The probe agents will naturally read whole-repo state; the `changedFiles` context they receive from `--since` is informational and does not restrict their glob/grep scope.

Dispatch probe agents IN PARALLEL using the Agent tool. Group by category (max `$CONFIG['discovery-parallelism']` agents, default 5):

> **Cursor IDE:** No Agent() tool available. Run probes sequentially within the current session — one category at a time. Complete each category's analysis before moving to the next.

- **Code probes agent**: Runs all activated code probes (hardcoded-values, orphaned-annotations, dead-code, ai-slop, type-safety-gaps, test-coverage-gaps, test-anti-patterns, security-basics)
- **Infra probes agent**: Runs all activated infra probes
- **UI probes agent**: Runs all activated UI probes
- **Arch probes agent**: Runs all activated arch probes
- **Session probes agent**: Runs all activated session probes
- **Audit probes agent**: Runs harness-audit probe
- **Vault probes** (`skills/discovery/probes-vault.md`): invokes `skills/discovery/probes/vault-staleness.mjs` and `skills/discovery/probes/vault-narrative-staleness.mjs` directly via `node`. Each probe returns `{findings, metrics, duration_ms}`. The runner reports `FINDING:` blocks per finding and appends summary records to `.orchestrator/metrics/vault-staleness.jsonl` and `vault-narrative-staleness.jsonl`.
- **Supply-chain probe** (`skills/discovery/probes-supply-chain.md`): invokes `skills/discovery/probes/supply-chain-slopcheck.mjs` directly via `node`. **Gated:** only activates when `slopcheck.enabled: true` AND `"discovery"` is in `slopcheck.sources` (Session Config). The probe returns `{findings, summary}`. SLOP findings surface as `critical`, ASSUMED as `medium`, LEGITIMATE packages generate no finding. See `probes-supply-chain.md` for invocation details and classification reference.
- **Docs probe** (`skills/discovery/probes-docs.md`): invokes `skills/discovery/probes/docs-staleness.mjs` AND `skills/discovery/probes/ssot-code-diff.mjs` directly via `node`. `docs-staleness.mjs` is **gated:** only activates when a `docs/` directory exists AND `docs-staleness.enabled: true` (Session Config); it scans `docs/*.md` (root level) and `docs/examples/*.md` for filesystem-mtime staleness against the `docs-staleness.thresholds.living` threshold (default 90d) — `docs/adr/` and `docs/prd/` are deliberately excluded. `ssot-code-diff.mjs` is **ungated** (no Session Config key) — it always runs when `CLAUDE.md` or `README.md` is present, diffing hardcoded doc "count" claims (e.g. "(13 rules)") against the live code/filesystem value they describe. Both probes return `{findings, metrics, duration_ms}`. See `probes-docs.md` for invocation details and severity escalation.
- **Feature probes agent** (`skills/discovery/probes-feature.md`): intent-drift + stubbed-dead-feature + feature-request-cluster probes. The first two MUST carry file_path:line_number anchors that survive the Phase 4.2 re-read (±3 lines); feature-request-cluster instead anchors on a VCS issue-ID set and MUST carry `verification_method: vcs-issue` — see Phase 4.2's dual verification path below.

Each agent receives:
- The probe definitions from `probes-intro.md` (confidence scoring reference) AND the category-specific `probes-<category>.md` file for this agent's category (include the actual grep commands/patterns in the prompt)
- The exclude paths list
- The project root path
- When `since_ref` was provided and `changedFiles` is non-empty: the `changedFiles` array (informational context for per-probe filtering — per-probe filtering enforcement is deferred to W3)
- Tools: Read, Grep, Glob, Bash (read-only -- no Edit/Write)
- Instruction: "Run each probe. For each finding, output EXACTLY this format:"

```
FINDING:
  probe: <probe_name>
  category: <category>
  severity: <critical|high|medium|low>
  file_path: <absolute path>
  line_number: <number>
  matched_text: <exact text from tool output>
  title: <short title for the finding>
  description: <1-2 sentence description>
  recommended_fix: <concrete fix suggestion>
```

"If a probe's activation condition is not met, skip it with: SKIPPED: <probe_name> -- <reason>"
"If a probe command fails, skip it with: FAILED: <probe_name> -- <error>"
"Do NOT fabricate findings. Only report what tool output confirms."

CRITICAL: `run_in_background: false` for all agents.

Skip categories with no activated probes (don't dispatch empty agents).

## Phase 4: Verification & Scoring

After all probe agents complete:

### 4.1 Parse Findings

Collect all `FINDING:` blocks from agent outputs into a unified findings list.

### 4.2 Verification Pass

For EACH finding, use the verification path matching how the finding is anchored:

**Default path — file-anchored findings (no `verification_method` field, or `verification_method: file-line`):**
1. Read the file at `file_path:line_number` using the Read tool
2. Confirm `matched_text` appears at or near that line (+/-3 lines tolerance)
3. If NOT confirmed, discard with note "false positive -- text not found at reported location"

**VCS-issue-anchored findings (`verification_method: vcs-issue`)** — e.g. `feature-request-cluster`, whose findings anchor on a set of issue IDs rather than a file location:
1. For each issue ID in the finding's `Location` set, verify it via the VCS CLI — syntax reference: `skills/gitlab-ops/SKILL.md` § "Common CLI Commands" (`glab issue view <IID>` / `gh issue view <NUMBER>`); do not duplicate the CLI syntax here
2. Confirm the issue exists and is still open (`state` != closed)
3. If an issue ID no longer resolves or was closed since detection, drop it from the `Location` set; if EVERY issue in the set is gone/closed, discard the finding entirely with note "false positive -- all referenced issues closed/removed since detection"

4. Report: "Verification: N confirmed, M discarded as false positives"

### 4.2a Confidence Scoring

For each verified finding, assign a confidence score (0-100) based on three factors:

| Factor | Low (+0) | Medium (+10) | High (+20) |
|--------|----------|-------------|------------|
| Pattern specificity | Generic match (URL, TODO) | Moderate (orphaned annotation, magic number) | Specific (API key regex, eval(), SQL injection) |
| File context | Test fixture, example, seed data, docs | Utility, config, scripts | Production source, API handler, middleware |
| Historical signal | Previously dismissed as false positive | No prior data (first occurrence) | Recurring issue (confirmed in learnings.jsonl) |

**Scoring rules:**
1. Start at 40 (baseline)
2. Add each factor's score (+0/+10/+20)
3. Clamp to 0-100 range
4. **Critical severity override:** findings with severity `critical` get a minimum confidence of 70 — they are NEVER auto-deferred

**Threshold:** Read `discovery-confidence-threshold` from Session Config (default: 60). If not configured, use 60.

Annotate each finding with its confidence score for Phase 5 presentation.

### 4.3 Deduplication

Two findings are duplicates if:
- Same `file_path` AND
- Overlapping line range (+/-5 lines) AND
- Different probes

Keep the higher severity finding. Merge descriptions.

### 4.4 Apply Thresholds

1. **Severity filter:** Remove findings below `discovery-severity-threshold` from Session Config.
2. **Confidence filter:** Remove findings with confidence score below `discovery-confidence-threshold` (default: 60). Log filtered-out findings: "Auto-dismissed N low-confidence findings (below threshold [T]). Use `discovery-confidence-threshold: 0` to see all."

### 4.5 Group by Category

Group remaining findings by category for Phase 5 presentation.

### 4.6 Embedded Mode Exit

If in embedded mode (called from session-end): STOP HERE. Return structured findings to the caller using this schema:

**Embedded mode return schema:**
```json
{
  "findings": [
    {"probe": "string", "category": "string", "severity": "critical|high|medium|low", "confidence": 0-100, "file": "string", "line": number, "description": "string", "recommendation": "string"}
  ],
  "stats": {
    "probes_run": number,
    "findings_raw": number,
    "findings_verified": number,
    "false_positives": number,
    "user_dismissed": 0,
    "issues_created": 0,
    "by_category": {"<category>": {"findings": number, "actioned": 0}}
  }
}
```

Present both as structured data in your final output. Do not proceed to Phase 5.

## Phase 5: Interactive Triage (Standalone Mode Only)

### 5.0 Load Triage State & Partition Findings

Before auto-defer and before presenting any findings for triage, load the persistent discovery triage state and filter findings through it:

1. Call `loadTriageState()` from `scripts/lib/discovery/triage-state.mjs` (uses default path `.orchestrator/metrics/discovery-triage.jsonl`). Returns an empty Map if the file does not exist — no error.
2. Call `filterFindings({ findings: verifiedFindings, stateMap })` to partition findings into three buckets:
   - `toShow` — state is `open`, `reopened`, or **no prior state entry** (new findings — present for user triage)
   - `suppressed` — state is `dismissed` or `accepted-as-known` (skip silently)
   - `tracked` — state is `promoted-to-#NNN` (issue already filed; show as informational)

3. Emit a one-line state banner before the summary table:
   ```
   Triage state: [N suppressed] suppressed (dismissed/accepted-as-known), [N tracked] tracked in existing issues. Presenting [N toShow] findings.
   ```
   Omit the banner entirely if all three counts are zero (first run).

4. Render `tracked` findings as informational lines in the summary — NOT as interactive triage items:
   ```
   [INFO] Finding "<title>" (<file_path>) is tracked in #<issue_id> — not re-triaged.
   ```

5. Continue Phase 5 triage using only `toShow` findings. The `suppressed` bucket requires no user interaction.

6. After the user completes triage (Steps 1-4 below), append state changes to `.orchestrator/metrics/discovery-triage.jsonl` via `appendTriageEntry()` from `triage-state.mjs`:
   - User selects "Create issue" → append `{ fingerprint, state: 'promoted-to-#<issue_id>', issue_id: <N>, timestamp, session_id }`
   - User selects "Dismiss -- intentional" or "Dismiss -- false positive" → append `{ fingerprint, state: 'dismissed', user_decision: '<reason>', timestamp, session_id }`
   - User selects "Accept all" for batch → append one `{ fingerprint, state: 'open', ... }` entry per finding (so they re-appear next run if not yet promoted)

### 5.1 Auto-Defer Low-Confidence Findings

Before presenting findings for triage, separate by confidence threshold:

1. Findings with confidence >= threshold → present for interactive triage (below)
2. Findings with confidence < threshold → auto-defer with summary:
   "Auto-deferred [N] low-confidence findings (score < [threshold]). Review with `/discovery --include-deferred`."
3. List auto-deferred findings in a collapsed section (not interactive — informational only)

### 5.1 Present High-Confidence Findings

Present findings using AskUserQuestion -- NEVER plain text options. On Codex CLI where AskUserQuestion is unavailable, present as numbered Markdown lists.

Include confidence scores in the presentation:
```
[CRITICAL] (confidence: 85) hardcoded-values: API key found in src/config.ts:42
[HIGH] (confidence: 72) security-basics: eval() usage in src/utils/parser.ts:18
[MEDIUM] (confidence: 61) orphaned-annotations: TODO without issue in src/lib/auth.ts:55
```

### Step 1: Summary

Present a findings overview table:

```
## Discovery Results

Probes run: [N] | Findings verified: [N] | False positives discarded: [N]

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Code     | ...      | ...  | ...    | ... | ...   |
| Infra    | ...      | ...  | ...    | ... | ...   |
| UI       | ...      | ...  | ...    | ... | ...   |
| Arch     | ...      | ...  | ...    | ... | ...   |
| Session  | ...      | ...  | ...    | ... | ...   |
| Audit    | ...      | ...  | ...    | ... | ...   |
| Vault    | ...      | ...  | ...    | ... | ...   |
| Feature  | ...      | ...  | ...    | ... | ...   |
```

### Step 2: Critical + High Findings -- Review Individually

For each Critical or High finding, use AskUserQuestion (on Codex CLI where AskUserQuestion is unavailable, present as numbered Markdown lists):

```
AskUserQuestion({
  questions: [{
    question: "<finding title>\n\n<file_path>:<line_number>\n```\n<matched_text with +/-3 lines context>\n```\n\n<description>\n\nRecommended fix: <recommended_fix>",
    header: "<severity>",
    options: [
      { label: "Create issue (<severity>)", description: "Create a priority:<severity> issue for this finding" },
      { label: "Adjust priority", description: "Create issue with different priority" },
      { label: "Dismiss -- intentional", description: "This is by design, skip" },
      { label: "Dismiss -- false positive", description: "Detection was wrong, skip" }
    ]
  }]
})
```

If user selects "Adjust priority", ask which priority with another AskUserQuestion. On Codex CLI where AskUserQuestion is unavailable, present as numbered Markdown lists.

### Step 3: Medium + Low Findings -- Review Batched

Group remaining findings by category. For each category with medium/low findings (on Codex CLI where AskUserQuestion is unavailable, present as numbered Markdown lists):

```
AskUserQuestion({
  questions: [{
    question: "[N] medium/low findings in [category]:\n\n1. [title] -- [file_path]:[line] ([severity])\n2. [title] -- [file_path]:[line] ([severity])\n...",
    header: "[Category]",
    options: [
      { label: "Accept all (Recommended)", description: "Create issues for all [N] findings" },
      { label: "Review individually", description: "Walk through each finding one by one" },
      { label: "Dismiss all", description: "Skip all medium/low findings in this category" }
    ]
  }]
})
```

If "Review individually" selected, walk through each like Step 2.

### Step 4: Batch Confirmation

Before creating any issues (on Codex CLI where AskUserQuestion is unavailable, present as numbered Markdown lists):

```
AskUserQuestion({
  questions: [{
    question: "Ready to create [N] issues?\n\n- [X] critical\n- [Y] high\n- [Z] medium\n- [W] low",
    header: "Confirm",
    options: [
      { label: "Create all [N] issues", description: "Proceed with issue creation" },
      { label: "Review list first", description: "Show full list before creating" },
      { label: "Cancel", description: "Do not create any issues" }
    ]
  }]
})
```

## Phase 6: Issue Creation & Report

### 6.1 Issue Creation

> **VCS Reference:** Detect the VCS platform per the "VCS Auto-Detection" section of the gitlab-ops skill.
> Use CLI commands per the "Common CLI Commands" section.

For each approved finding:

1. Format using the Discovery Finding Issue Template from `issue-templates.md`
2. Determine labels: `type:discovery` + `priority:<level>` + `area:<inferred from category/filepath>` + `status:ready`
3. Create issue via VCS CLI:
   - **GitLab**: `glab issue create --title "[Discovery] <title>" --label "type:discovery,priority:<level>,area:<area>,status:ready" --description "<body>"`
   - **GitHub**: `gh issue create --title "[Discovery] <title>" --label "type:discovery,priority:<level>,area:<area>,status:ready" --body "<body>"`
4. Brief pause (1s) between creations for rate limiting

### 6.2 Final Report

When the active scope included `feature` AND at least one verified feature finding was approved into an issue, insert an **Opportunity Solution Tree (OST) section** between `### Created Issues` and `### Dismissed Findings` (shown below). This section is feature-scope-only — every other category keeps the flat `### Created Issues` table as its sole findings view, unchanged.

```
## Discovery Report

### Summary
- Probes run: [N] across [categories]
- Raw findings: [N]
- Verified: [N] (false positives discarded: [M])
- User approved: [N]
- Issues created: [N]

### Created Issues
| # | Title | Priority | Area | Probe |
|---|-------|----------|------|-------|
| <IID> | <title> | <priority> | <area> | <probe> |

### Opportunity Solution Tree (feature scope only)
> Present ONLY when the active scope included `feature` and at least one verified feature finding was approved. Group the approved feature findings under a Teresa Torres OST hierarchy: **outcome** (the user/business result the product is steering toward) -> **opportunity** (the observed gap or unmet need the finding surfaces) -> **solution** (the finding itself — the created issue). Infer outcome/opportunity from the finding's probe + description; never fabricate a hierarchy level with no evidentiary basis — when the outcome is genuinely unclear, write "Outcome: (unclassified)" rather than guessing.

Example:
Outcome: Reduce time-to-first-value for new users
  Opportunity: Onboarding drops users before they reach the "aha" moment (intent-drift: docs claim auto-provisioning, code path is manual)
    Solution: #182 -- Implement auto-provisioning of default workspace
  Opportunity: Users repeatedly request the same missing capability without a tracked epic
    Solution: #191, #204, #211 -- feature-request-cluster: "CSV export" cluster (3 issues, no epic)

### Dismissed Findings
- [N] dismissed as intentional
- [M] dismissed as false positive

### Recommendations
- [suggestions based on finding patterns]
```

## Critical Rules

- **NEVER** fabricate findings -- every finding must come from tool output with verifiable evidence
- **NEVER** create issues without user approval (standalone mode)
- **ALWAYS** verify findings by re-reading the file at the reported line (Phase 4)
- **ALWAYS** use AskUserQuestion for triage decisions -- never plain text options (On Codex CLI, use numbered lists as AskUserQuestion is not available)
- **ALWAYS** reference gitlab-ops for VCS operations -- never duplicate CLI logic inline
- If a probe command fails or tool is unavailable, skip gracefully, continue with others
- If in embedded mode, stop after Phase 4, return findings as structured data
- Respect `discovery-severity-threshold` -- filter before presenting to user
- Default exclude paths always apply: `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `coverage/`

## Phase 7: Capture Discovery Stats (Standalone Mode Only)

> This phase runs only in standalone mode. Embedded mode returns findings to the caller.

After Phase 6 (Issue Creation) completes, prepare discovery statistics for session metrics:

1. Count totals from the triage results:
   - `probes_run`: number of probes that were activated and executed
   - `findings_raw`: total findings before verification
   - `findings_verified`: findings that passed Phase 4.2 verification
   - `false_positives`: findings discarded during verification
   - `user_dismissed`: findings the user declined during Phase 5 triage
   - `issues_created`: issues created in Phase 6
   - `by_category`: per-category breakdown of findings and actioned items

2. Report stats summary:
   ```
   Discovery stats: [probes_run] probes, [findings_raw] raw → [findings_verified] verified ([false_positives] false positives). User dismissed [user_dismissed]. Created [issues_created] issues.
   ```

3. These stats are available for session-end to include in `sessions.jsonl` under the `discovery_stats` field. The discovery skill does NOT write to `sessions.jsonl` directly — session-end handles that.

## Discovery Triage State (#419)

Persistent triage state prevents re-presenting the same finding on every `/discovery` run. State is stored in an append-only JSONL file and keyed by a stable fingerprint.

### State File

**Location:** `.orchestrator/metrics/discovery-triage.jsonl` (gitignored via `.orchestrator/metrics/*.jsonl` pattern — machine-local, never committed)

**Format:** One JSON object per line:
```json
{"fingerprint":"aabb1122ccdd3344","state":"dismissed","user_decision":"intentional — debug log","timestamp":"2026-05-17T10:00:00.000Z","session_id":"deep-2"}
{"fingerprint":"eeff5566aabb7788","state":"promoted-to-#119","issue_id":119,"timestamp":"2026-05-17T10:01:00.000Z","session_id":"deep-2"}
```

### Fingerprint

`computeFingerprint({probe, file, severity, ruleId})` → 16-char hex (sha256 prefix).

`line_number` is **intentionally excluded** — it drifts on refactoring without the underlying issue changing. A finding is considered "the same" as long as the probe, file path, severity, and ruleId match.

### State Enum

| State | Meaning |
|---|---|
| `open` | Actively needs triage or was explicitly marked for re-review |
| `dismissed` | User dismissed as intentional or false positive — suppressed on future runs |
| `accepted-as-known` | Known issue, accepted without creating a VCS issue — suppressed on future runs |
| `reopened` | Previously suppressed but re-surfaced by user decision — shown again |
| `promoted-to-#NNN` | VCS issue created; shown informational ("tracked in #NNN") on future runs |

### Re-run Semantics

On each `/discovery` run, Phase 5 loads the state file and partitions findings before presenting them:

- **New findings** (no fingerprint entry) → always shown
- **`open` or `reopened`** → shown for triage
- **`dismissed` or `accepted-as-known`** → suppressed (silent — no user interaction needed)
- **`promoted-to-#NNN`** → informational line only ("tracked in #NNN")

A suppressed finding re-appears only if its fingerprint changes — i.e., the probe, file path, severity, or ruleId changes. No TTL on dismissed state.

### Module

`scripts/lib/discovery/triage-state.mjs` — pure ESM, Node stdlib only. Exports:
- `computeFingerprint({probe, file, severity, ruleId}): string`
- `loadTriageState(stateFilePath?): Promise<Map<fingerprint, entry>>`
- `appendTriageEntry(stateFilePath, entry): Promise<void>`
- `filterFindings({findings, stateMap}): {toShow, suppressed, tracked}`

## Anti-Patterns

- **DO NOT** report findings without verifying them first — false positives erode user trust faster than missed issues
- **DO NOT** skip the interactive triage phase — auto-creating issues for unconfirmed findings creates noise
- **DO NOT** run probes outside the configured scope — if the user asked for `code` scope, don't scan infrastructure
- **DO NOT** present findings without evidence (file path, line number, actual content) — assertions without proof are useless
- **DO NOT** write to `sessions.jsonl` directly — session-end handles metrics persistence
