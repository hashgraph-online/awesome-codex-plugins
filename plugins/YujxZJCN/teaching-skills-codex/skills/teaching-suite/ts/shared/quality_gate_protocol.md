# Quality & Integrity Gate Protocol (Gate 3.5)

The second blocking gate in the teaching pipeline. Runs after Stage 3 (ASSESS), once
materials and assessments exist, and before Stage 4 (DELIVER). Where the Alignment Gate
checks the *design's structure*, this gate checks the *artifacts' quality*: integrity
resilience, accessibility, transparency, and inclusion.

Deterministic checklist over produced artifacts + Course Passport, then professor
acknowledgment. **Not skippable** inside the pipeline.

## Checks

### Q. AI-era integrity (see `ts/shared/ai_era_integrity.md`)

| # | Check | Severity |
|---|-------|----------|
| Q1 | `policies.ai_use_policy` is non-empty and states per-assignment-category rules (permitted / disclosed / prohibited, with reasons) | BLOCK |
| Q2 | Every assessment in the plan has `ai_resilience` set to `reviewed` or `redesigned` (the integrity audit actually ran) | BLOCK |
| Q3 | Assessments worth ≥20% rely on at least one structurally AI-resilient component (in-class, oral, process evidence, personalized data, or staged drafts) OR carry an explicit professor-accepted-risk note | WARN |
| Q4 | No assessment depends on AI-detection tools as its integrity mechanism | WARN |

### T. Transparency (Pedagogy Foundations §6)

| # | Check | Severity |
|---|-------|----------|
| T1 | Every project/paper brief has Purpose / Task / Criteria sections | BLOCK |
| T2 | Every assessment ≥10% weight has a rubric or explicit grading scheme artifact | WARN |
| T3 | Syllabus states grading scheme, late policy, and how to get help | WARN |
| T4 | No artifact bound for students carries an unresolved `[NEEDS PROFESSOR INPUT]` or `[VERIFY]` marker — run `scripts/check_content_markers.py <passport> --strict`. Drafts may carry markers; student-facing finalization may not | WARN (BLOCK at Stage 5 finalize) |

### U. Accessibility & UDL (Pedagogy Foundations §7)

| # | Check | Severity |
|---|-------|----------|
| U1 | Materials checklist run: heading structure, alt-text notes for figures, captions noted for video, colorblind-safe palettes in graphics specs | WARN |
| U2 | At least one alternative route exists for participation-dependent grades (e.g., discussion-board equivalent to cold-calling) | WARN |
| U3 | Exam logistics include an accommodations plan note (extra-time version exists or is trivially derivable) | WARN |

### I. Inclusion & tone

| # | Check | Severity |
|---|-------|----------|
| I1 | Examples/case studies scanned for unnecessarily culture-bound or exclusionary framing (flag, never rewrite silently) | WARN |
| I2 | Syllabus policies use support-oriented rather than adversarial language where equivalent (flag only; tone is the professor's call) | WARN |

### W. Workload re-audit

| # | Check | Severity |
|---|-------|----------|
| W1 | Re-run Alignment Gate D1–D3 against *actual built artifacts* (built problem sets are often longer than planned) | WARN |

## Gate behavior

Identical mechanics to the Alignment Gate: findings written to
`gates.quality_gate.findings[]`; BLOCK → `fail` → return to the producing stage (max 3
rounds); WARN dismissible with logged reason; professor acknowledgment closes the gate.

## Honesty rules

- Q2 verifies the audit *ran*, not that every assessment is AI-proof — no assessment is.
  The gate's job is to ensure the professor made informed, recorded decisions.
- U and I checks are advisory by design: they flag with file/line specificity and a
  suggested alternative, and they never block, because accessibility and tone decisions
  belong to the professor and the institution's actual policies.
- A finding the professor dismissed in a previous run is not re-raised.
