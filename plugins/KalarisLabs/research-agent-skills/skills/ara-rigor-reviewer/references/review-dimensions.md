# Level 2 Review Dimensions — Scoring Anchors and Check Inventory

Six dimensions of epistemic quality. All checks are semantic: they require reading
comprehension and reasoning over the ARA's content. Structural validation (reference
resolution, field presence, YAML parsing) is handled entirely by Level 1.

---

## D1. Evidence Relevance

**Question**: Does the cited evidence actually support each claim in substance, not just by reference?

### Checks

| Check | What to verify | Finding severity |
|-------|---------------|-----------------|
| Relevance | Experiment's Setup/Procedure addresses what the claim actually asserts | major |
| Type-aware entailment | Experiment design matches claim type (causal→ablation, generalization→heterogeneous, improvement→baseline, descriptive→sampling, scoping→bounds) | major |
| Evidence sufficiency | Is a single experiment enough to support this claim, or are multiple needed? | suggestion |

### Scoring Anchors

| Score | Description |
|-------|-------------|
| 5 | Type-appropriate, relevant evidence for every claim; multi-experiment support where needed |
| 4 | Evidence relevant for all claims, minor type mismatches |
| 3 | Most claim-experiment pairs relevant, 1-2 weak matches |
| 2 | Multiple claims where cited experiments don't substantively address the claim |
| 1 | Majority of claims cite experiments irrelevant to their statements |

---

## D2. Falsifiability Quality

**Question**: Are claims genuinely falsifiable with meaningful, actionable criteria?

### Checks

| Check | What to verify | Finding severity |
|-------|---------------|-----------------|
| Actionability | Could an independent researcher execute this? Specifies what to measure, failure threshold, and conditions? | major |
| Non-triviality | Is the criterion more than a tautology? ("If the method doesn't work" = trivial) | major |
| Scope match | Does the criterion address the same scope as the Statement? | major |
| Independence | Could it be tested without proprietary data or systems? | minor |

### Scoring Anchors

| Score | Description |
|-------|-------------|
| 5 | Every claim has specific, actionable, independently testable criteria matching claim scope |
| 4 | Most criteria are strong, 1-2 vague or hard to operationalize |
| 3 | Mixed; some actionable, some trivial or scope-mismatched |
| 2 | Most criteria trivial, tautological, or scope-mismatched |
| 1 | Criteria meaningless across claims |

---

## D3. Scope Calibration

**Question**: Do claims assert exactly what their evidence supports — no more, no less?

### Checks

| Check | What to verify | Finding severity |
|-------|---------------|-----------------|
| Over-claiming | Statement uses universal scope while evidence covers narrow conditions | critical if extreme, major if moderate |
| Under-claiming | Evidence files or experiment results not captured by any claim | minor |
| Assumption explicitness | Key assumptions stated in problem.md or constraints.md | major if unstated assumptions affect validity |
| Generalization boundaries | Artifact states what claims do NOT apply to | minor |
| Qualifier consistency | Hedging language matches evidence strength | minor |

### Scoring Anchors

| Score | Description |
|-------|-------------|
| 5 | All claims precisely match evidence scope, assumptions explicit, limits stated |
| 4 | Well-scoped with minor gaps in assumption documentation |
| 3 | Some claims slightly over/under-reach, assumptions partially stated |
| 2 | Multiple over-claims or significant undocumented assumptions |
| 1 | Pervasive scope mismatch between claims and evidence |

---

## D4. Argument Coherence

**Question**: Does the argument follow a coherent path from problem to solution to evidence?

### Checks

| Check | What to verify | Finding severity |
|-------|---------------|-----------------|
| Observation → Gap derivation | Gaps follow logically from observations | major |
| Gap → Insight connection | Key insight addresses the identified gaps | major |
| Insight → Solution alignment | Solution architecture implements the key insight | major |
| Solution → Claims coverage | Claims cover the solution's main contributions | minor |
| Cross-layer consistency | Claims, tree, and evidence tell the same story | major |
| Narrative completeness | Motivating questions are answered or explicitly deferred | minor |
| Gap coverage | Every gap is substantively addressed by at least one claim | major |

### Scoring Anchors

| Score | Description |
|-------|-------------|
| 5 | Clear arc from observations → gaps → insight → solution → claims → evidence, all gaps addressed |
| 4 | Strong flow with minor gaps or one unaddressed gap |
| 3 | General flow present but disconnects between layers |
| 2 | Significant misalignment between problem and claims, or contradictions |
| 1 | No coherent logical flow; layers tell different stories |

---

## D5. Exploration Integrity

**Question**: Does the exploration tree faithfully document the research journey?

### Checks

| Check | What to verify | Finding severity |
|-------|---------------|-----------------|
| Dead-end specificity | failure_mode is concrete, lesson is transferable | major |
| Decision rationale quality | Rationale explains why chosen path preferred over real alternatives | major |
| Rebutted-branch consistency | No claim advocates a dead_end or pivot approach | critical |
| Exploration breadth | Main design choices have ≥2 documented alternatives | minor |
| Honesty signal | Tree documents genuine negatives, not post-hoc justification | suggestion |

### Scoring Anchors

| Score | Description |
|-------|-------------|
| 5 | Rich tree, specific failure modes, actionable lessons, thorough rationale, genuine negatives |
| 4 | Good tree with minor gaps in dead-end or decision documentation |
| 3 | Tree present but dead-ends lack specificity or decisions lack alternatives |
| 2 | Boilerplate documentation; dead-ends and decisions read as formulaic |
| 1 | Tree contradicts claims or reads entirely as post-hoc justification |

---

## D6. Methodological Rigor

**Question**: Are experiments well-designed with adequate baselines and reporting?

### Checks

| Check | What to verify | Finding severity |
|-------|---------------|-----------------|
| Baseline adequacy | Right things compared? Baselines recent and relevant? | major |
| Ablation coverage | Multi-component claims have experiments isolating individual contributions | major |
| Statistical reporting | Variance, CI, number of runs, or tests mentioned | major for quantitative claims |
| Metric-claim alignment | Metric measures what claim asserts | major |
| Reproducibility signals | Setup specific enough for replication (model, dataset, hardware, hyperparameters) | minor |

### Scoring Anchors

| Score | Description |
|-------|-------------|
| 5 | Comprehensive baselines, proper ablations, statistical rigor, precise metric-claim alignment |
| 4 | Strong methodology with minor gaps |
| 3 | Adequate but missing some baselines or statistical details |
| 2 | Significant gaps; missing baselines for comparative claims or no ablations |
| 1 | No baselines, no ablations, metrics don't match claims |

---

## Overall Grade Mapping

| Grade | Condition |
|-------|-----------|
| **Strong Accept** | mean ≥ 4.5 AND no dimension < 3 |
| **Accept** | mean ≥ 3.8 AND no dimension < 2 |
| **Weak Accept** | mean ≥ 3.0 AND no dimension < 2 |
| **Weak Reject** | mean ≥ 2.0 AND (mean < 3.0 OR any dimension < 2) |
| **Reject** | mean < 2.0 OR any dimension = 1 |

## Finding Severity Definitions

| Severity | Meaning | Example |
|----------|---------|---------|
| `critical` | Fundamental epistemic flaw; the claim or argument cannot stand as written | Causal claim supported only by correlation; claim advocates a dead-end approach |
| `major` | Significant weakness that undermines a claim or dimension | Comparative claim with no baseline; trivial falsification criteria; metric doesn't match claim |
| `minor` | Noticeable issue that doesn't invalidate the work | Missing generalization boundaries; hedging inconsistent with evidence |
| `suggestion` | Constructive improvement, not a flaw | Adding a retrieval baseline for context; documenting exploration breadth |
