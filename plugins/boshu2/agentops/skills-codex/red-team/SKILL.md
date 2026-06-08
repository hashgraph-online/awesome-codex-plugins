---
name: red-team
description: "Run red team."
---
# $red-team — Persona-Based Adversarial Validation

> **Quick Ref:** Adopt constrained personas. Attempt real tasks. Report what breaks. Unlike `$council` (expert judgment) or `$vibe` (code quality), red-team tests whether things actually WORK when someone TRIES to use them.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Quick Start

```bash
$red-team docs/                                    # probe docs with default personas
$red-team skills/council/                          # probe a skill's SKILL.md
$red-team --surface=docs README.md                 # explicit surface type
$red-team --personas-file=.agents/red-team/p.yaml  # custom personas
$red-team --deep skills/rpi/                       # council consolidation with --deep
```

---

## How It Works

```
Council:    expert judges  →  review artifact  →  debate  →  verdict
Red-team:   constrained agents  →  attempt task  →  collect findings  →  council consolidates
```

Council judges SEE everything and JUDGE quality. Red-team agents have RESTRICTED context and ATTEMPT tasks. Council is reused only for the consolidation/verdict phase.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--surface=<type>` | auto-detect | Force surface type: `docs` or `skills` |
| `--personas-file=<path>` | built-in | Custom persona definitions (YAML) |
| `--scenarios-file=<path>` | auto-generate | Custom scenario definitions (YAML) |
| `--deep` | off | Use full council (not --quick) for consolidation |
| `--persona=<name>` | all | Run only a specific persona |
| `--target=<path>` | `.` | Target path to probe |

---

## Execution Steps

### Step 0: Setup

Detect target surface type and create output directory.

```bash
mkdir -p .agents/red-team
```

**Surface detection:**
- Path contains `skills/` and a `SKILL.md` exists → `skills` surface
- Path contains `docs/` or target is `README.md` → `docs` surface
- Explicit `--surface=<type>` overrides auto-detection

**Validate surface:** v1 supports `docs` and `skills` only. If another surface is detected, output:
```
Surface '<type>' is not supported in v1. Supported: docs, skills.
```

### Step 1: Load Personas

**Priority order:**
1. `--personas-file=<path>` → load custom personas from YAML
2. `.agents/red-team/personas/*.yaml` → load project-specific personas
3. Built-in defaults from council `red-team` preset (see [references/persona-format.md](references/persona-format.md))

**For docs surface:** Default personas: `panicked-sre`, `junior-engineer`, `first-time-consumer`
**For skills surface:** Default persona: `zero-context-agent`

If `--persona=<name>` is set, filter to only that persona.

### Step 2: Build Context-Restricted Prompts

For each persona, construct a context-restricted agent prompt. This is the critical step that differentiates red-team from council — the agent operates under enforced knowledge constraints.

**Prompt template:**

```
You are {PERSONA_NAME}: {ROLE}.

CONTEXT: {CONTEXT_DESCRIPTION}

MANDATORY CONSTRAINTS — you MUST follow these:
- You can ONLY read files in: {ALLOWED_PATHS}
- You do NOT know: {EXCLUDED_KNOWLEDGE}
- You CANNOT: {CANNOT_LIST}
- You MUST navigate from the entry point a real {ROLE} would use
- Do NOT use Grep to search the entire codebase — only read files
  you would naturally discover by following links and references

YOUR TASK: Complete the following scenarios in order.

{SCENARIO_LIST}

For EACH scenario, record:
1. Steps taken (file read, link followed, search attempted)
2. Path taken: entry_point → file1:line → file2:line → ...
3. Verdict: PASS (completed), FAIL (blocked), PARTIAL (completed with friction)
4. Friction points (even on PASS — what slowed you down?)
5. Evidence: exact file:line references
6. Severity: critical (blocks task), significant (impedes task), minor (friction)

Write your complete findings report to: .agents/red-team/probe-{PERSONA_NAME}.md

Use this format for each finding:
## RT-NNN: <title>
- **Scenario:** <which scenario>
- **Verdict:** PASS | FAIL | PARTIAL
- **Severity:** critical | significant | minor
- **Path taken:** <navigation path>
- **Finding:** <what happened>
- **Evidence:** <file:line>
- **Recommendation:** <actionable fix>
```

**Context restriction enforcement:**

The persona's `constraints.allowed_paths` controls which files the agent can read. The `constraints.excluded_knowledge` tells the agent what concepts to treat as unknown. The `constraints.cannot` lists forbidden actions.

These constraints are enforced via the agent prompt — the agent is instructed to behave as if it only has access to the allowed paths and lacks the excluded knowledge. While not technically sandboxed, this produces meaningful usability findings because the agent genuinely navigates from the entry point rather than using expert knowledge to skip ahead.

### Step 3: Load Scenarios

**Priority order:**
1. `--scenarios-file=<path>` → load custom scenarios
2. `.agents/red-team/scenarios/*.yaml` → load project-specific scenarios
3. Auto-generate from target surface

**Auto-generation rules** per surface type — see [references/scenario-format.md](references/scenario-format.md):
- **Docs:** 4-6 scenarios per persona probing discoverability, completeness, copy-paste readiness, jargon
- **Skills:** 3-5 scenarios per persona probing step executability, examples, error handling, flags

### Step 4: Execute Probes

Spawn one agent per persona. Each agent runs all scenarios for their persona sequentially.

```
Agent(
  description="Red-team probe: {persona_name}",
  prompt=<context-restricted prompt from Step 2>,
  subagent_type="general",
  run_in_background=true
)
```

**Spawn all persona agents in parallel** (they work on independent probes).

**Wait for all agents to complete.** Each writes findings to `.agents/red-team/probe-{persona_name}.md`.

### Step 5: Collect and Normalize Findings

Read each probe report from `.agents/red-team/probe-{persona_name}.md`.

Parse findings into canonical `schemas/finding.json` format:

```json
{
  "severity": "critical",
  "category": "red-team/panicked-sre",
  "description": "Runbook for ArgoCD sync failure not reachable from docs entry point",
  "location": "docs/README.md:45",
  "recommendation": "Add incident runbook link to docs/README.md quick-reference section",
  "fix": "Add '## Incident Runbooks' section with links to docs/runbooks/",
  "why": "On-call SRE cannot find recovery procedure under time pressure",
  "ref": "docs/README.md → docs/operations/README.md → dead end (no runbook link)"
}
```

**Field mapping:**
- `category` → `"red-team/<persona-name>"`
- `location` → file:line from evidence
- `ref` → navigation path taken
- `why` → root cause (why this matters for the persona)

### Step 6: Cross-Persona Deduplication

When the same finding appears from multiple personas:
1. Keep the highest-severity instance
2. Note all personas that found it (increases confidence)
3. Add to cross-persona findings table in the report

**Dedup key:** `location` + normalized `description`. Two findings at the same location about the same issue = one finding with multiple persona citations.

### Step 7: Consolidate via Council

Run council with red-team preset to review and consolidate all findings:

```
$council --preset=red-team [--quick] validate .agents/red-team/
```

Use `--quick` by default. Use full council (omit `--quick`) when `--deep` flag is set.

Council judges review the raw findings using red-team perspectives (OnCall, NewHire, Agent, Consumer) and produce a consolidated verdict.

### Step 8: Write Report

Write consolidated report to `.agents/red-team/YYYY-MM-DD-red-team-<target-slug>.md`.

Report includes:
- Overall verdict (PASS/WARN/FAIL)
- Per-persona results table
- Detailed findings with evidence
- Cross-persona findings (higher confidence)
- Council consolidation verdict

See [references/report-format.md](references/report-format.md) for the full template.

### Step 9: Feed Flywheel

**Do NOT emit raw findings directly to `.agents/findings/registry.jsonl`.** The registry is for reusable normalized patterns, not one-off target defects.

Instead:
- If verdict is WARN or FAIL, suggest running `$post-mortem --quick` to capture reusable lessons
- If called from `$post-mortem`, findings flow through the standard normalization pipeline
- Log: `"Red-team complete. Run '$post-mortem --quick' to capture reusable findings."`

---

## Persona Defaults by Surface

| Surface | Default Personas | Rationale |
|---------|-----------------|-----------|
| docs | panicked-sre, junior-engineer, first-time-consumer | Tests time-pressure, onboarding, and zero-knowledge paths |
| skills | zero-context-agent | Tests whether an agent can execute from SKILL.md alone |

---

## Output Directory

```
.agents/red-team/
├── probe-panicked-sre.md         # Raw probe output
├── probe-junior-engineer.md      # Raw probe output
├── probe-first-time-consumer.md  # Raw probe output
├── probe-zero-context-agent.md   # Raw probe output
├── YYYY-MM-DD-red-team-<target>.md  # Consolidated report
├── personas/                     # Custom persona definitions
│   └── *.yaml
└── scenarios/                    # Custom scenario definitions
    └── *.yaml
```

---

## Examples

### Probe Documentation

**User says:** `$red-team docs/`

**What happens:**
1. Detects `docs` surface
2. Loads 3 default personas (panicked-sre, junior-engineer, first-time-consumer)
3. Auto-generates 4-6 scenarios per persona (discoverability, completeness, copy-paste, jargon)
4. Spawns 3 agents in parallel, each constrained to docs/ and README.md
5. Collects findings, deduplicates cross-persona
6. Runs `$council --preset=red-team --quick` for consolidation
7. Writes report to `.agents/red-team/`

**Result:** Structured usability findings from 3 constrained perspectives.

### Probe a Skill

**User says:** `$red-team skills/evolve/`

**What happens:**
1. Detects `skills` surface (SKILL.md exists)
2. Loads zero-context-agent persona
3. Auto-generates 3-5 scenarios (step executability, examples, error handling, flags)
4. Spawns 1 agent restricted to `skills/evolve/SKILL.md` and `skills/evolve/references/`
5. Agent attempts to follow the SKILL.md workflow step-by-step
6. Collects findings on ambiguities, missing steps, undefined terms
7. Writes report

**Result:** Actionable feedback on SKILL.md clarity from a zero-context perspective.

### Custom Personas

**User says:** `$red-team --personas-file=.agents/red-team/personas/platform-ops.yaml docs/`

**What happens:** Uses project-specific personas instead of built-in defaults.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Agent reads files outside allowed_paths | Prompt constraint not followed | Re-run with stricter prompt; check agent output for constraint violations |
| Too many findings (noise) | Broad target scope | Narrow target (e.g., `docs/getting-started/` instead of `docs/`) |
| All scenarios PASS | Target is well-documented or personas too permissive | Try custom personas with tighter constraints or broader scenario scope |
| Council consolidation misses findings | Raw findings not in standard format | Check probe files match the expected format |
| Surface auto-detection wrong | Ambiguous target path | Use explicit `--surface=docs` or `--surface=skills` |

---

## See Also

- [skills/council/SKILL.md](../council/SKILL.md) — Multi-model consensus (used for consolidation)
- [skills/vibe/SKILL.md](../vibe/SKILL.md) — Code quality validation (complementary)
- [skills/doc/SKILL.md](../doc/SKILL.md) — Doc generation/validation (complementary)
- [skills/bug-hunt/SKILL.md](../bug-hunt/SKILL.md) — Systematic audit (closest cousin)

## Reference Documents

- [references/persona-format.md](references/persona-format.md) — Persona YAML schema with context restriction fields
- [references/scenario-format.md](references/scenario-format.md) — Scenario YAML schema with pass/fail criteria
- [references/surface-types.md](references/surface-types.md) — Supported surfaces and probing dimensions
- [references/report-format.md](references/report-format.md) — Report template and verdict rules
