# Ensemble Mode Reference

Multi-agent reasoning swarm: each pane runs a distinct reasoning mode against the same
question, outputs are synthesized. Catalog is large (80 modes, 9 presets, 10 synthesis
strategies) — this is the lookup.

**Availability gate:** live NTM exposes ensemble catalog/status/suggest robot surfaces in normal builds, but ensemble spawning is experimental. If `--robot-ensemble-spawn` returns `NOT_IMPLEMENTED`, rebuild NTM with `-tags ensemble_experimental` or choose a normal `ntm spawn` / pipeline flow instead. Do not treat an experimental-spawn refusal as a broken swarm.

## Contents

- [What is Ensemble Mode](#what-is-ensemble-mode)
- [Subcommand list](#subcommand-list)
- [Reasoning modes catalog](#reasoning-modes-catalog) — 80 modes across 12 categories
  - [A: Formal & Mathematical](#category-a-formal--mathematical-reasoning-a1-a8)
  - [B: Ampliative](#category-b-ampliative-reasoning-b1-b11)
  - [C: Uncertainty](#category-c-reasoning-under-uncertainty-c1-c5)
  - [D: Vagueness](#category-d-reasoning-under-vagueness-d1-d5)
  - [E: Change & Defaults](#category-e-reasoning-with-change--defaults-e1-e7)
  - [F: Causal & Dynamic](#category-f-causal--dynamic-reasoning-f1-f7)
  - [G: Practical](#category-g-practical-reasoning-g1-g11)
  - [H: Strategic & Social](#category-h-strategic--social-reasoning-h1-h4)
  - [I: Dialectical & Interpretive](#category-i-dialectical--interpretive-reasoning-i1-i5)
  - [J: Modal / Temporal / Spatial / Normative](#category-j-modal-temporal-spatial-normative-j1-j4)
  - [K: Domain-Specific](#category-k-domain-specific-reasoning-k1-k7)
  - [L: Meta & Reflective](#category-l-meta-level--reflective-l1-l6)
- [Presets catalog](#presets-catalog) — 9 presets
- [Synthesis strategies](#synthesis-strategies) — 10 strategies
- [Robot-mode equivalents](#robot-mode-equivalents)
- [Example invocations](#example-invocations)
- [Gotchas](#gotchas)

---

## What is Ensemble Mode

Ensemble mode spawns multiple agents in parallel in one tmux session, each reasoning
about the same question using a different *reasoning mode*. The outputs are then
synthesized into a unified analysis. Benefits:

- Mitigates single-agent blind spots
- Surfaces hidden assumptions
- Provides confidence scoring via mode agreement/disagreement
- Produces more robust and creative solutions

**Workflow**:

1. Load or define a preset (bundle of modes + synthesis strategy + budgets).
2. Spawn agents in a tmux session, one pane per mode.
3. Inject prompts guiding each agent toward its assigned mode.
4. Collect outputs as agents complete.
5. Synthesize using the specified strategy (e.g., adversarial, consensus, creative).
6. Merge findings and emit a final report.

Source: `/dp/ntm/internal/cli/ensemble.go:96-164` (newEnsembleCmd).

## Subcommand list

### `ntm ensemble [preset-name] "<question>"`

Shorthand — spawn an ensemble with a preset and question.

```bash
ntm ensemble project-diagnosis "What are the main security issues in this codebase?"
```

Source: `/dp/ntm/internal/cli/ensemble.go:102-141`.

### `ntm ensemble spawn <session>`

Explicit create. Flags:

| Flag | Purpose |
|------|---------|
| `--preset=<name>` | Use preset (mutually exclusive with `--modes`) |
| `--modes=<id1>,<id2>,...` | Explicit mode IDs |
| `--question="..."` | Required |
| `--allow-advanced` | Allow advanced/experimental tier modes |
| `--agent-mix=cc=3,cod=2,gmi=1` | Agent distribution |
| `--assignment=round-robin|affinity|category|explicit` | Pane assignment strategy |
| `--synthesis=<strategy>` | Synthesis strategy override |
| `--budget-total=<n>` / `--budget-per-agent=<n>` | Token budget caps |
| `--no-cache` | Skip context pack cache |
| `--no-inject` | Create session without injecting prompts |
| `--project=<dir>` | Project directory (default: cwd) |
| `--dry-run [--show-preambles]` | Preview spawn plan |

Source: `/dp/ntm/internal/cli/ensemble_spawn.go:61-84`.

### `ntm ensemble presets` (alias `list`)

List presets. Flags: `--format=table|json|yaml`, `--verbose`, `--imported`,
`--tag=<tag>`. Source: `/dp/ntm/internal/cli/ensemble_presets.go:105-150`.

### `ntm ensemble suggest "<question>"`

Recommend the best preset for a question.

```bash
ntm ensemble suggest "What features should we add next?" --id-only
# → idea-forge
```

Source: `/dp/ntm/internal/cli/ensemble_suggest.go:33-66`.

### `ntm ensemble status [session]`

Show current state, assignments, synthesis readiness.
Flags: `--format=table|json|yaml`, `--show-contributions`.
Source: `/dp/ntm/internal/cli/ensemble.go:171-208`.

### `ntm ensemble stop [session]`

Stop all agents, save partial state. Flags: `--force`, `--no-collect`, `--quiet`,
`--yes`. Source: `/dp/ntm/internal/cli/ensemble.go:230-282`.

### `ntm ensemble synthesize [session]`

Trigger synthesis of completed outputs. Flags:

| Flag | Purpose |
|------|---------|
| `--strategy=<name>` | Override synthesis strategy |
| `--format=markdown|json|yaml` | Output format |
| `--output=<file>` | Write to file |
| `--stream [--resume --run-id=<id>]` | Incremental streaming + resume |
| `--force` | Synthesize even if agents incomplete |
| `--explain` / `--verbose` | Include reasoning detail |
| `--use-cache` / `--no-cache` | Cache control |

Source: `/dp/ntm/internal/cli/ensemble.go:885-950`.

### Additional subcommands

- `export <preset>` — Export preset to TOML.
- `import <file-or-url>` — Import preset from TOML.
- `estimate [session]` — Token budget estimate.
- `compare <session>` — Compare outputs across modes.
- `cache` — Manage context pack cache.
- `export-findings [session]` — Export findings file.
- `provenance [session]` — Evidence chain for findings.
- `resume [session]` — Resume paused ensemble.
- `rerun-mode [session] <mode>` — Rerun a single mode.
- `clean-checkpoints [session]` — Prune checkpoint files.

## Reasoning modes catalog

80 modes across 12 categories. Each mode has: id, category code (A1–L6), tier
(Core / Advanced / Experimental), outputs, best-for, failure-modes, differentiator.
Source: `/dp/ntm/internal/ensemble/modes.go:12-1100` (`EmbeddedModes`).

### Category A: Formal & Mathematical Reasoning (A1-A8)

| Code | ID | Name | Tier |
|------|-----|------|------|
| A1 | deductive | Deductive Inference | Core |
| A2 | mathematical-proof | Mathematical Proof | Core |
| A3 | formal-verification | Formal Verification | Core |
| A4 | equational | Equational Reasoning | Advanced |
| A5 | model-theoretic | Model-Theoretic Reasoning | Advanced |
| A6 | constraint-sat | Constraint Satisfaction | Advanced |
| A7 | type-theoretic | Type-Theoretic Reasoning | Core |
| A8 | edge-case | Edge Case Reasoning | Core |

### Category B: Ampliative Reasoning (B1-B11)

| Code | ID | Name | Tier |
|------|-----|------|------|
| B1 | inductive | Inductive Generalization | Core |
| B2 | statistical | Statistical Reasoning | Advanced |
| B3 | bayesian | Bayesian Reasoning | Advanced |
| B4 | likelihood | Likelihood Reasoning | Advanced |
| B5 | option-generation | Option Generation (abductive) | Core |
| B6 | analogical | Analogical Transfer | Core |
| B7 | case-based | Case-Based Reasoning | Advanced |
| B8 | conceptual-blending | Conceptual Blending | Core |
| B9 | simplicity | Simplicity / Occam | Advanced |
| B10 | reference-class | Reference-Class Reasoning | Advanced |
| B11 | fermi | Fermi Estimation | Advanced |

### Category C: Reasoning Under Uncertainty (C1-C5)

| Code | ID | Name | Tier |
|------|-----|------|------|
| C1 | probabilistic-logic | Probabilistic Logic | Advanced |
| C2 | imprecise-probability | Imprecise Probability | Advanced |
| C3 | evidential | Evidential (Dempster-Shafer) | Advanced |
| C4 | maximum-entropy | Maximum-Entropy | Advanced |
| C5 | qualitative-probability | Qualitative Probability | Advanced |

### Category D: Reasoning Under Vagueness (D1-D5)

| Code | ID | Name | Tier |
|------|-----|------|------|
| D1 | fuzzy | Fuzzy Reasoning | Advanced |
| D2 | ambiguity-detection | Ambiguity Detection | Core |
| D3 | rough-set | Rough Set Reasoning | Advanced |
| D4 | prototype-reasoning | Prototype Reasoning | Core |
| D5 | qualitative | Qualitative Reasoning | Advanced |

### Category E: Reasoning with Change & Defaults (E1-E7)

| Code | ID | Name | Tier |
|------|-----|------|------|
| E1 | non-monotonic | Non-Monotonic | Advanced |
| E2 | default-typicality | Default Reasoning | Advanced |
| E3 | defeasible | Defeasible Reasoning | Advanced |
| E4 | belief-revision | Belief Revision (AGM) | Advanced |
| E5 | paraconsistent | Paraconsistent Reasoning | Advanced |
| E6 | argument-mapping | Argument Mapping | Core |
| E7 | assurance-case | Assurance Case | Advanced |

### Category F: Causal & Dynamic Reasoning (F1-F7)

| Code | ID | Name | Tier |
|------|-----|------|------|
| F1 | causal-inference | Causal Inference | Advanced |
| F2 | dependency-mapping | Dependency Mapping | Core |
| F3 | counterfactual | Counterfactual | Advanced |
| F4 | failure-mode | Failure Mode Analysis | Core |
| F5 | root-cause | Root Cause Analysis | Core |
| F6 | second-order-effects | Second-Order Effects | Core |
| F7 | systems-thinking | Systems Thinking | Core |

### Category G: Practical Reasoning (G1-G11)

| Code | ID | Name | Tier |
|------|-----|------|------|
| G1 | means-end | Means-End | Advanced |
| G2 | decision-under-uncertainty | Decision Under Uncertainty | Core |
| G3 | prioritization | Prioritization | Core |
| G4 | strategic-planning | Strategic Planning | Core |
| G5 | resource-allocation | Resource Allocation | Core |
| G6 | worst-case | Worst-Case Analysis | Core |
| G7 | minimax-regret | Minimax Regret | Advanced |
| G8 | satisficing | Satisficing | Advanced |
| G9 | value-of-information | Value-of-Information | Advanced |
| G10 | heuristic | Heuristic Reasoning | Advanced |
| G11 | search-based | Search-Based Reasoning | Advanced |

### Category H: Strategic & Social Reasoning (H1-H4)

| Code | ID | Name | Tier |
|------|-----|------|------|
| H1 | game-theoretic | Game-Theoretic | Advanced |
| H2 | perspective-taking | Perspective Taking | Core |
| H3 | negotiation | Negotiation | Advanced |
| H4 | mechanism-design | Mechanism Design | Advanced |

### Category I: Dialectical & Interpretive Reasoning (I1-I5)

| Code | ID | Name | Tier |
|------|-----|------|------|
| I1 | dialectical | Dialectical | Advanced |
| I2 | rhetorical | Rhetorical | Advanced |
| I3 | hermeneutic | Hermeneutic | Advanced |
| I4 | narrative | Narrative | Advanced |
| I5 | sensemaking | Sensemaking | Advanced |

### Category J: Modal, Temporal, Spatial, Normative (J1-J4)

| Code | ID | Name | Tier |
|------|-----|------|------|
| J1 | modal | Modal Reasoning | Advanced |
| J2 | deontic | Deontic Reasoning | Advanced |
| J3 | temporal | Temporal Reasoning | Advanced |
| J4 | spatial | Spatial Reasoning | Advanced |

### Category K: Domain-Specific Reasoning (K1-K7)

| Code | ID | Name | Tier |
|------|-----|------|------|
| K1 | scientific | Scientific Reasoning | Advanced |
| K2 | test-plan | Test Plan Mode | Core |
| K3 | engineering-design | Engineering Design | Core |
| K4 | compliance | Compliance Lens | Core |
| K5 | moral-ethical | Moral-Ethical | Advanced |
| K6 | historical-investigative | Historical-Investigative | Advanced |
| K7 | clinical-operational | Clinical-Operational | Advanced |

### Category L: Meta-Level & Reflective (L1-L6)

| Code | ID | Name | Tier |
|------|-----|------|------|
| L1 | meta-cognitive | Meta-Cognitive Monitoring | Core |
| L2 | calibration | Calibration Reasoning | Advanced |
| L3 | reflective-equilibrium | Reflective Equilibrium | Advanced |
| L4 | transcendental | Transcendental Reasoning | Advanced |
| L5 | adversarial-review | Adversarial Review | Core |
| L6 | debiasing | Debiasing Reasoning | Advanced |

## Presets catalog

9 embedded presets. Source: `/dp/ntm/internal/ensemble/ensembles.go:7-228`
(`EmbeddedEnsembles`).

| Name | Modes | Synthesis | Budget | Advanced? | Best for |
|------|-------|-----------|--------|-----------|----------|
| project-diagnosis | systems-thinking, worst-case, dependency-mapping, failure-mode, perspective-taking | adversarial | 30k | No | Holistic health check |
| idea-forge | conceptual-blending, analogical, option-generation, second-order-effects, prototype-reasoning | creative | 30k | No | Feature brainstorming, innovation |
| spec-critique | deductive, ambiguity-detection, edge-case, test-plan, perspective-taking | consensus | 25k | No | Requirements review, API contracts |
| safety-risk | worst-case, adversarial-review, compliance, failure-mode, root-cause | adversarial | 30k | No | Security audit, threat modeling |
| architecture-review | argument-mapping, root-cause, systems-thinking, perspective-taking, strategic-planning | deliberative | 30k | No | Design review |
| tech-debt-triage | dependency-mapping, failure-mode, resource-allocation, prioritization | prioritized | 20k | No | Debt prioritization |
| bug-hunt | clinical-operational, inductive, adversarial-review, deductive, causal-inference, type-theoretic | analytical | 28k | **Yes** | Multi-angle debugging |
| root-cause-analysis | clinical-operational, causal-inference, counterfactual, inductive, debiasing | deliberative | 28k | **Yes** | Postmortems, incident investigation |
| strategic-planning | strategic-planning, systems-thinking, decision-under-uncertainty, second-order-effects, resource-allocation, prioritization, perspective-taking | deliberative | 32k | No | Roadmap / policy design |

## Synthesis strategies

10 strategies. Source: `/dp/ntm/internal/ensemble/strategy.go:30-128`
(`strategyRegistry`).

| Strategy | Requires Agent | Synthesizer Mode | Output Focus | Best for |
|----------|:-:|---|---|---|
| manual | No | — | concatenated findings | Simple aggregation, debugging |
| adversarial | Yes | adversarial-review | vulnerabilities, counterarguments | Security, risk, stress-test |
| consensus | Yes | meta-evaluation | agreement areas, confidence-weighted | Multi-perspective validation |
| creative | Yes | conceptual-blending | novel combinations, emergent patterns | Innovation, cross-domain |
| analytical | Yes | systems-thinking | structured comparison, gap analysis | Architecture, comprehensive analysis |
| deliberative | Yes | decision-analysis | tradeoff analysis, weighted recommendations | Decision making, policy |
| prioritized | Yes | meta-evaluation | ranked findings, quality scores | Triage, best-of selection |
| dialectical | Yes | dialectical | thesis/antithesis pairs, resolved tensions | Controversial topics |
| meta-reasoning | Yes | meta-evaluation | reasoning quality, epistemic status | High-stakes decisions |
| voting | No | — | vote tallies, score distributions | Democratic aggregation |
| argumentation | Yes | argumentation | support/attack edges, grounded claims | Debate, legal reasoning |

**Deprecated → current mapping** (auto-migrated with warning, `strategy.go:164-178`):

- `debate` → `dialectical`
- `weighted` → `prioritized`
- `sequential` → `manual`
- `best-of` → `prioritized`

## Robot-mode equivalents

All registered in `/dp/ntm/internal/cli/root.go:3195-3213`.

| Flag | Purpose | Args |
|------|---------|------|
| `--robot-ensemble-modes` | List reasoning modes | `--tier=core|advanced|all`, `--category=A-L`, `--limit`, `--offset` |
| `--robot-ensemble-presets` | List presets | — |
| `--robot-ensemble=SESSION` | Show ensemble status | `SESSION` |
| `--robot-ensemble-spawn=SESSION` | Spawn ensemble | `--preset`, `--modes`, `--question`, `--allow-advanced`, `--agents` |
| `--robot-ensemble-suggest=QUESTION` | Suggest preset | `--suggest-id-only` |
| `--robot-ensemble-stop=SESSION` | Stop | `--stop-force`, `--stop-no-collect` |

Implementation: `/dp/ntm/internal/robot/ensemble_presets.go:44-125`,
`/dp/ntm/internal/robot/ensemble_modes.go:65-185`.

## Example invocations

### 1. Security audit

```bash
ntm ensemble safety-risk "Identify vulnerabilities in our authentication system"
ntm ensemble status
# wait for status.Done > 0, status.Pending == 0
ntm ensemble synthesize --strategy adversarial --format=json
```

### 2. Architecture decision with deliberation

```bash
ntm ensemble spawn arch-review-2024 \
  --preset=architecture-review \
  --question="Microservices or monolith?" \
  --agent-mix="cc=4,cod=2" \
  --budget-total=50000

ntm ensemble status arch-review-2024

ntm ensemble synthesize arch-review-2024 \
  --strategy deliberative --explain \
  --format=markdown --output=architecture-decision.md
```

### 3. Dry-run before expensive spawn

```bash
ntm ensemble spawn trial-session \
  --preset=bug-hunt \
  --question="Why is payment processing failing intermittently?" \
  --allow-advanced \
  --dry-run --show-preambles \
  --format=json > dry-run-report.json

jq '.assignments, .budget, .validation' dry-run-report.json

# Looks good — spawn for real
ntm ensemble spawn bug-hunt-session \
  --preset=bug-hunt \
  --question="Why is payment processing failing intermittently?" \
  --allow-advanced
```

### 4. Robot mode for agent integration

```bash
ntm --robot-ensemble-presets | jq '.presets[].name'

ntm --robot-ensemble-suggest="What features should we add?" --suggest-id-only
# → idea-forge

ntm --robot-ensemble-spawn=myproject \
  --preset=project-diagnosis \
  --question="Main technical issues?" \
  --robot-format=json

ntm --robot-ensemble=myproject | jq '.status_counts'

ntm --robot-ensemble-stop=myproject
```

## Gotchas

### Session state & pane names

- Ensemble creates a new tmux session with unique panes per mode.
- Session must not already exist; use `ntm ensemble spawn <unique-name>`.
- Pane names follow `<session>:<pane-index>`.
- If the tmux session dies, partial outputs may be lost unless the context-pack cache
  retains them (`--no-cache=false` is the default).

Source: `/dp/ntm/internal/cli/ensemble_spawn.go:215-224`.

### Advanced modes & `--allow-advanced`

- 28 core modes always available; 52 advanced/experimental require `--allow-advanced`.
- Presets `bug-hunt` and `root-cause-analysis` require `--allow-advanced` explicitly
  even if you only touch them through the preset.
- Without the flag, advanced modes are silently filtered out.

Source: `/dp/ntm/internal/ensemble/ensembles.go:174-200`.

### Budget & token limits

- `--budget-per-agent` overrides `MaxTokensPerMode` for every mode.
- `--budget-total` caps absolute across all modes.
- Estimates are rough; agents can be force-killed if they exceed budget mid-response.

Source: `/dp/ntm/internal/ensemble/budget.go`, `ensemble_spawn.go:306-311`.

### Synthesis timing

- Synthesis waits for all agents to complete (or `--force` synthesizes partial).
- Synthesizer agent itself consumes budget tokens.
- `--stream --resume --run-id=<id>` supports resume but checkpoints are **not durable
  across CLI invocations**.

Source: `/dp/ntm/internal/cli/ensemble.go:910-990`.

### Assignment strategies

- `round-robin` — assign modes to panes in order.
- `affinity` — cluster similar-category modes together.
- `category` — one mode per category.
- `explicit` — requires `--modes` with `mode:agent-type` specs.

Source: `/dp/ntm/internal/cli/ensemble_spawn.go:239-248`.

### Contribution scoring

`ntm ensemble status --show-contributions` reports per-mode contribution scores
(overlap, unique insights, citations, rank) *after* synthesis completes.

Source: `/dp/ntm/internal/cli/ensemble.go:657-689`.
