# Mode: `/plan feature` — Feature PRD

> Reference file for the plan skill. Read by SKILL.md when mode is `feature`.
> Covers: feature discovery (1-2 waves) → compact PRD → issue creation.
> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md).

---

## Phase 1: Feature Discovery (1-2 waves)

### Wave 1 — Feature Core (6 questions)

Before asking questions, dispatch 3 Explore agents in parallel:

```
Agent({ subagent_type: "Explore", description: "Analyze codebase for related patterns",
  prompt: "Use Glob and Grep to find existing implementations related to [feature topic].
  Search relevant directories for similar patterns, naming conventions, and architecture.
  Report: affected files, current patterns, reuse opportunities." })

Agent({ subagent_type: "Explore", description: "Check VCS for related issues",
  prompt: "Use Bash to run VCS CLI (glab/gh, auto-detect per gitlab-ops skill).
  List open issues mentioning [feature topic] or related keywords.
  Check recent merged MRs/PRs for related work. Report: open issues, recent changes, blockers." })

Agent({ subagent_type: "Explore", description: "Research best practices",
  prompt: "Use WebSearch to find best practices for [feature type].
  Look for common pitfalls, recommended patterns, and prior art.
  Report: top 3 approaches with pros/cons." })
```

Synthesize agent findings into 2 AskUserQuestion calls (3+3 split):

**Questions:**

1. **What to build** — Open-ended. Analyze the answer and suggest structure (e.g., break into sub-features, identify components). Use codebase agent findings to ground suggestions.
   - *Multiple candidate subfeatures surfaced?* Rank them by Opportunity Score (see `SKILL.md` § "Opportunity Score (Ranking Candidate Subfeatures)") and present the top-ranked candidate as the `(Recommended)` Option 1.
2. **Why now** — Business driver, user feedback, or technical necessity? Present agent-found context (related issues, recent changes) as options.
3. **Who uses it** — Existing personas or new audience? Reference existing user research if available in the repo.
4. **User-Story-Schicht** — "User-Story-Schicht für dieses Feature erzeugen?" Immer fragen (kein Audience-Heuristik-Gate). Drei Antwortoptionen: **Ja (Als/möchte/damit)** — klassische Persona-Story-Form; **Ja (job-story)** — job-story-Form ("When [situation], I want [motivation], so I can [outcome]"); **Nein** — byte-identisches Status-quo-Verhalten. Bei einer der beiden "Ja"-Optionen emittiert die PRD eine optionale ## User Stories Sektion (je Story ein ↳ AC-Pointer) in der gewählten Form; bei "Nein" wird die Sektion vollständig weggelassen.
5. **Scope** — MVP appetite (Shape Up: 1w/2w/6w) + explicit exclusions. Push hard for "what is NOT in this feature." First option is always the recommended appetite based on complexity.
6. **Dependencies** — On existing issues, features, or other repos. Pre-populate from VCS agent findings. Flag blockers.

### Wave 2 — Technical Deep Dive (conditional, 5 questions)

> Trigger Wave 2 only if Wave 1 answers reveal: multiple subsystems affected, unclear
> integration points, significant architectural decisions needed, or user explicitly
> requests deeper analysis. Skip otherwise — proceed to Phase 2.

Before asking, dispatch 3 Explore agents:

```
Agent({ subagent_type: "Explore", description: "Deep-read affected source files",
  prompt: "Read the specific files identified in Wave 1 findings.
  Trace call paths from entry points to data layer.
  Report: file list, function signatures, data flow, coupling points." })

Agent({ subagent_type: "Explore", description: "Check test patterns for affected area",
  prompt: "Use Glob to find test files for the affected modules.
  Read test structure and coverage patterns.
  Report: existing test approach, gaps, suggested test strategy." })

Agent({ subagent_type: "Explore", description: "Research technical approach",
  prompt: "Use WebSearch and WebFetch for the specific technical challenge identified.
  Look for library options, performance benchmarks, migration guides.
  Report: recommended approach with evidence." })
```

**Questions:**

1. **Architecture decisions** — Based on codebase patterns found by agents. Present 2-3 approaches with trade-offs. First option is the recommendation.
2. **Integration points** — API changes, new endpoints, event hooks. Pre-populated from deep-read agent findings.
3. **Data model changes** — DB migrations, schema changes, new tables. Show current schema context.
4. **Edge cases** — Error handling, concurrent access, backwards compatibility. Agent findings inform likely failure modes.
5. **Performance impact** — Query complexity, caching needs, load implications. Ground in current performance patterns.

---

## Phase 2: Feature PRD Generation

1. Read `prd-feature-template.md` from this skill directory.
2. Fill all 5 sections:

| Section | Source |
|---------|--------|
| 1. Problem & Motivation | Wave 1 Q1 (what) + Q2 (why). Concise, 2-3 paragraphs. |
| 2. Solution & Scope | Wave 1 Q5 (scope). Explicit In-Scope and Out-of-Scope lists. |
| ## User Stories (conditional) | Emit only when the User-Story-Schicht toggle ≠ "Nein"; one story per persona-goal, each linking ≥1 §3/§3.A acceptance criterion. Toggle = "Ja (Als/möchte/damit)" → emit the classic Als/möchte/damit form. Toggle = "Ja (job-story)" → emit the job-story form ("When [situation], I want [motivation], so I can [outcome]"). Omit the section entirely when toggle = "Nein" (byte-for-byte status quo). |
| 3. Acceptance Criteria | Derive Given/When/Then scenarios from Wave 1 answers. Each sub-feature produces 1-3 Gherkin scenarios. |
| 3.A Acceptance Criteria (EARS) | OPTIONAL — emit EARS clauses (Ubiquitous/State-driven/Event-driven/Optional feature/Unwanted behaviour) for the same Feature Areas. Used by `/write-executable-plan` for 1:1 vitest stub generation. Leave blank if Section 3 narrative suffices. |
| 4. Technical Notes | Wave 2 findings if it ran (architecture, affected files, data model). If Wave 2 was skipped, populate from Wave 1 Explore agent findings. |
| 5. Risks & Dependencies | Wave 1 Q6 (dependencies) + Wave 2 Q4-Q5 (edge cases, performance) if available. |

3. Save to `{plan-prd-location}/YYYY-MM-DD-{feature-slug}.md`. Read `plan-prd-location` from Session Config in CLAUDE.md (or AGENTS.md on Codex CLI) (default: `docs/prd/`).
4. Dispatch PRD reviewer subagent per `prd-reviewer-prompt.md`. Max 3 iterations. Surface unresolved issues to user.
5. **Package Legitimacy Audit (Slopcheck — #520):** if Session Config has `slopcheck.enabled: true` and `slopcheck.sources` includes `plan`, run the Phase 3.5 audit defined in `SKILL.md` against the generated PRD body (scan `## Affected Files`, `## Dependencies`, and code-fenced `pnpm add` / `npm install` / `pip install` / `cargo add` blocks for npm/pip/cargo package mentions, then call `classifyPackages()` from `scripts/lib/slopcheck.mjs`). Fail-soft on registry errors. See `SKILL.md` § "Phase 3.5: Package Legitimacy Audit" for the full handling matrix.
6. **PRD Commit Gate:** before proceeding to Phase 3 (Issue Creation), satisfy the PRD Commit Gate — see `SKILL.md` § Phase 5.5 (HARD-GATE). Do not create issues referencing an uncommitted PRD.

---

## Phase 3: Issue Creation

### Derive Epic + Sub-Issues

Source: PRD Section 3 (Acceptance Criteria).

- **Epic title:** feature name + one-line purpose.
- **Sub-issues:** one per acceptance criterion group. Group related Given/When/Then scenarios — do not create one issue per individual scenario.

### Auto-Prioritize

Apply this scoring:

1. **Technical dependencies** — Issues that block other issues get `priority:critical` or `priority:high`. DB before API, API before UI, shared before consumers.
2. **Core acceptance criteria** — Issues covering primary happy-path scenarios get `priority:high`.
3. **Edge cases / nice-to-haves** — Defensive scenarios, error handling, optional behaviors get `priority:medium` or `priority:low`.
4. **Risk factor — Impact × Risk 2×2 triage:** Classify by Impact (high/low) × Risk (high/low): **High-Impact + Low-Risk → Implement** (bump priority up one level); **High-Impact + High-Risk → Experiment** (smallest spike first); **Low-Impact + Low-Risk → Defer** (backlog, no issue in this set); **Low-Impact + High-Risk → Reject** (no issue — note rationale in § Risks & Dependencies). Full quadrant definitions: `SKILL.md` § 6.2 Auto-Prioritize.

### Labels

Apply per gitlab-ops skill label taxonomy:

- **Type:** `type:feature` for new capabilities, `type:enhancement` for extensions of existing features.
- **Priority:** `priority:critical` / `priority:high` / `priority:medium` / `priority:low` from auto-prioritize above.
- **Area:** Infer from affected code paths (e.g., `area:api`, `area:frontend`, `area:infra`).
- **Appetite:** Map from Wave 1 Q5 scope answer (`appetite:1w`, `appetite:2w`, `appetite:6w`).

### User Review Gate

Present the full issue structure via AskUserQuestion before creation:

- Epic title and description
- Each sub-issue: title, priority, labels, dependency links
- User confirms, adjusts priorities, or removes issues

### Create Issues

1. Create via VCS CLI (auto-detect per gitlab-ops skill: `glab` or `gh`).
2. Set `blocks` / `is-blocked-by` dependency links between issues. On HTTP 403 (non-Premium/Ultimate): `relates_to` + body-ordering-note fallback — see gitlab-ops SKILL.md § "Issue Linking (`blocks` / `is_blocked_by`)".
3. Report created issue URLs to user.
4. **Epic Backlink Commit:** once the Epic issue's IID is known, follow `SKILL.md` § 6.6 to add an `**Epic:** #<IID>` line to the PRD and commit it as a separate follow-up commit.
