# Goal Generation Heuristics

## Goal Quality Criteria

A good goal:

1. **Mechanically verifiable** — `check` is a shell command that exits 0 (pass) or non-zero (fail). No human judgment required.
2. **Descriptive** — `description` says what it measures, not how. "Go CLI compiles without errors" not "run go build".
3. **Weighted by impact** — 5 = build/test integrity, 3-4 = feature fitness, 1-2 = hygiene.
4. **Pillar-mapped** — Maps to one of: knowledge-compounding, validated-acceleration, goal-driven-automation, zero-friction-workflow. Infrastructure goals omit `pillar`.
5. **Not trivially true** — Check can actually fail in a realistic scenario. `test -f README.md` is trivially true.
6. **Not duplicative** — No two goals test the same thing. Check existing IDs before proposing.

## Scan Sources

| Source | What to look for | Goal type |
|--------|-----------------|-----------|
| `PRODUCT.md` | Value props, design principles, theoretical pillars without goals | Pillar |
| `README.md` | Claims, badges, features without verification | Pillar |
| `skills/*/SKILL.md` | Skills with no goal referencing them | Pillar or Infra |
| `tests/`, `hooks/` | Scripts not covered by goals | Infrastructure |
| `docs/` | Doc files referenced but not covered | Infrastructure |
| Existing goals | Checks referencing deleted paths | Prune candidates |

## Theoretical Pillar Coverage

Generate mode should check that all 4 theoretical pillars have goals:

### 1. Systems Theory (Meadows)

Targets leverage points #3-#6 (information flows, rules, self-organization, goals). Goals should verify that the system operates at these leverage points rather than lower ones (parameters, buffers).

### 2. DevOps (Three Ways)

- **Flow** maps to `zero-friction-workflow` and `goal-driven-automation`
- **Feedback** maps to `validated-acceleration`
- **Continual Learning** maps to `knowledge-compounding`

Goals should cover all three ways.

### 3. Brownian Ratchet

The pattern: chaos + filter + ratchet = directional progress from undirected energy. Goals should verify:
- Chaos source exists (agent sessions generate varied outputs)
- Filter exists (council validates, vibe checks)
- Ratchet exists (knowledge flywheel captures and persists gains)

### 4. Knowledge Flywheel

Escape velocity condition: `signal_rate x retrieval_rate > decay_rate` (informally: you learn faster than you forget). Goals should verify:
- Signal generation (extract, forge, retro produce learnings)
- Retrieval (inject loads learnings into sessions)
- Decay resistance (learnings are persisted, not just in-memory)

## Weight Guidelines

| Weight | Category | Examples |
|--------|----------|----------|
| 5 | **Critical** | Build passes, tests pass, manifests valid |
| 4 | **Important** | Full test suite, hook safety, mission alignment |
| 3 | **Feature fitness** | Skill behaviors, positioning, documentation |
| 2 | **Hygiene** | Lint, coverage floors, doc counts |
| 1 | **Nice to have** | Stubs, aspirational checks |

## ID Conventions

- Use kebab-case: `go-cli-builds`, `readme-compounding-hero`
- Prefix with domain: `readme-`, `go-`, `skill-`, `hook-`
- Keep under 40 characters
- Must be unique across all goals

## Directive Quality Criteria

When generating or evaluating directives for GOALS.md:

1. **Actionable** — Describes work that can be decomposed into issues. "Expand test coverage" not "Be better at testing."
2. **Steerable** — Has a clear direction (increase/decrease/hold/explore). If you can't assign a steer, it's too vague.
3. **Measurable progress** — You can tell whether work addressed it (even if not fully completed).
4. **Not a gate** — Directives describe intent, not pass/fail thresholds. "Reduce complexity" is a directive; "complexity < 15" is a gate.
5. **Prioritized** — Lower number = higher priority. Directive 1 is worked before directive 2.
6. **Evidence-grounded** — Every directive SHOULD cite a specific metric or finding that motivated it. Vague directives ("improve testing") are a smell. Good: "Close the multi-runtime promise gap — runtime-specific tests are quarantined (8 dirs in `tests/_quarantine/`)". Bad: "Ship more tests."
7. **Balanced across dimensions** — A healthy directive set includes both engineering directives (test, build, refactor) and product/growth directives (onboarding, adoption, user outcomes). If all directives are engineering-flavored, the goals file is incomplete.

### Steer Values

| Steer | Meaning | Example |
|-------|---------|---------|
| `increase` | Do more of this | "Expand test coverage" |
| `decrease` | Reduce this | "Reduce complexity budget" |
| `hold` | Maintain current level | "Keep API compatibility" |
| `explore` | Investigate options | "Evaluate new CI provider" |

### Directive-Gate Relationship

Directives generate gates over time:
- Directive "Expand test coverage" → Gate `test-coverage-floor` (check: coverage > 80%)
- Directive "Reduce complexity" → Gate `complexity-budget` (check: gocyclo -over 15 = 0 findings)

When a directive is fully addressed (gate exists and passes), consider removing the directive and keeping the gate.

## Product Directive Patterns

Engineering directives target code quality. Product directives target user outcomes. A complete GOALS.md needs both.

### Product Directive Examples

| Pattern | Example | Steer |
|---------|---------|-------|
| Onboarding friction | "Gate the install path — 3 install scripts have zero automated testing" | increase (install scripts with smoke tests) |
| Adoption barrier | "Restructure quickstart to reach first validated workflow in under 5 min" | decrease (time to first value) |
| Retention signal | "Verify knowledge lifecycle end-to-end — capture through injection to retrieval" | increase (lifecycle stages gated) |
| Growth lever | "Maintain competitive awareness — refresh comparison docs within 45 days" | decrease (stale comparison doc count) |
| User outcome | "Reduce false-positive council verdicts below 5%" | decrease (false positive rate) |

### How to Generate Product Directives

1. **Check PRODUCT.md** — if Known Gaps section exists, each gap is a candidate directive
2. **Check install/onboarding paths** — untested install = highest-risk product gap
3. **Check user-facing promises** — README claims without verification = directive candidates
4. **Check retention infrastructure** — knowledge flywheel, session handoff, learning retrieval
5. **Ask the user** — "What's your biggest product gap?" and "What metric would tell you the product is working?"

### Evidence Sources for Grounding Directives

When writing directives, cite specific data when available:

| Source | What to extract | Example citation |
|--------|----------------|------------------|
| `gh api repos/{owner}/{repo}` | Stars, forks, clones, traffic | "2,317 clones/14d" |
| `.agents/defrag/latest.json` | Flywheel metrics | "σ=0.02 decay, 1.2% promotion rate" |
| `tests/_quarantine/` | Quarantined test count | "8 test dirs disabled" |
| `.agents/retros/` | Failure patterns | "3 of 5 retros cite missing install gates" |
| `ao goals measure --json` | Gate pass rates | "5/7 passing (71%)" |
| Council FAIL verdicts | Root causes | "#1 cause: missing mechanical verification" |

## Anti-Star Generation

Anti-stars define what the project explicitly avoids. The best anti-stars come from proven failure modes, not hypothetical bad practices.

### Auto-Discovery

Scan these sources for failure patterns to convert into anti-stars:

1. **`.agents/retros/`** — recurring themes in retrospectives (e.g., "scope bundling caused 3 failed epics")
2. **Council FAIL verdicts** — root causes from `.agents/council/` or council index (e.g., "missing mechanical verification" → anti-star: "Product promises with no automated verification")
3. **`.agents/learnings/`** — learnings tagged as anti-patterns or mistakes

### Conversion Pattern

| Failure mode | Anti-star |
|-------------|-----------|
| Knowledge stored but never retrieved | "Capture without compounding" |
| Gates pass but product doesn't improve | "Goals that measure code metrics instead of user outcomes" |
| Tests quarantined indefinitely | "Quarantined tests that hide real regression risk" |
| Features built without user demand | "Building features nobody asked for" |

### Fallback

If no `.agents/` data exists, use generic anti-stars:
- "Shipping without validation"
- "Measuring activity instead of outcomes"
- "Optimizing for metrics that don't correlate with user value"

## North Star Quality

North stars should describe outcomes, not features.

| Weaker (feature-focused) | Stronger (outcome-focused) |
|--------------------------|---------------------------|
| "Skills work across 4 runtimes" | "Skills work identically across Claude Code, Codex CLI, Cursor, and OpenCode" |
| "Knowledge flywheel captures learnings" | "Knowledge captured in one session is retrieved and applied in the next" |
| "Fast onboarding" | "A new user goes from install to first validated workflow in under 5 minutes" |

When reviewing north stars, ask: "If this star is achieved, does a user's life actually improve?" If the answer is "only if other things also happen," the star is too narrow.

## Product Gate Patterns

Product gates verify product health alongside code health. Suggest gates based on what infrastructure exists:

| Infrastructure | Gate ID | Check | Weight |
|---------------|---------|-------|--------|
| `.agents/learnings/` + flywheel CLI | `flywheel-compounding` | `ao flywheel status --json \| jq -e '.escape_velocity_compounding == true'` | 8 |
| `skills/status/` | `quickstart-under-5min` | `bash scripts/check-quickstart-timing.sh` | 5 |
| `docs/comparisons/` | `competitive-freshness` | `bash scripts/check-competitive-freshness.sh` | 3 |
| `PRODUCT.md` with Known Gaps | `product-gaps-tracked` | `grep -c '|' PRODUCT.md \| test $(cat) -gt 0` | 3 |
| `ao flywheel status` works | `flywheel-promotion-rate` | `ao flywheel status --json \| jq -e '.promotion_rate > 0.05'` | 4 |

Only suggest product gates for infrastructure that actually exists in the project. Don't create aspirational gates — they'll just fail and get ignored.
