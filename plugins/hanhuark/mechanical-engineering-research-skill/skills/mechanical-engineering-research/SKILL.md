---
name: mechanical-engineering-research
description: Apply source-aware mechanical-engineering judgment to research, analysis, coding, writing, teaching, research identity, and release work. Use for thermal-fluid systems, heat transfer, fluid mechanics, thermodynamics, HVAC, energy systems, turbomachinery, piping, multiphase flow, experiments, correlations, CFD, reduced-order models, AI/ML, uncertainty, engineering datasets, literature reviews, citations, manuscripts, reviewer revisions, Overleaf packages, figures, proposals, research software, reproducibility, public releases, engineering teaching materials, or a research-project logo and visual identity.
---

# Mechanical Engineering Research

## Core Workflow

1. Define the engineering decision or research question.
   - Identify the system, geometry, materials or fluid, operating regime, boundary and initial conditions, outputs, constraints, and intended user.
   - Ask only for missing information that materially changes scientific validity or the work path. Otherwise state bounded assumptions and proceed.

2. Classify the evidence before interpreting it.
   - Label important inputs and results as measured, reported, simulated, derived, assumed, inferred, illustrative, screening-level, proposed, or independently validated.
   - Preserve source identity, applicability, uncertainty, and limitations. Treat search results and AI summaries as discovery aids, not evidence.

3. Establish the technical invariants.
   - Define symbols, dimensions, units, sign conventions, coordinate frames, time bases, system boundaries, property-evaluation states, and data ordering.
   - Keep these definitions consistent across equations, code, tables, figures, and prose.

4. Select the simplest credible method.
   - Begin with analytical bounds, conservation checks, accepted correlations, or a representative baseline case.
   - Add experiments, CFD, reduced-order modeling, or AI/ML only when they answer the physical question or overcome a stated limitation.

5. Verify in proportion to claim strength and consequence.
   - Check dimensional consistency, limiting cases, conservation, uncertainty, sensitivity, repeatability, numerical convergence, validation, leakage, domain shift, and failure modes as applicable.
   - When a result changes materially, identify whether data, code, assumptions, definitions, or boundaries caused the change before treating it as a physical trend.

6. Produce and verify the actual deliverable.
   - Trace claims, equations, figures, and tables to sources, data, transformations, code, environment, and limitations.
   - Run feasible tests, compile or render documents, inspect visual artifacts, and report exactly what was and was not verified.

## Integrity Gates

- Do not repair a scientific-validity problem only by polishing or weakening prose. Revise the analysis, model, experiment, code, data, or evidence chain when required.
- Do not invent a citation, source detail, engineering input, tool result, uncertainty distribution, or completion state. Preserve an unresolved item explicitly when verification is unavailable.
- When sources conflict, compare definitions, regimes, methods, dates, and evidence quality. Prefer primary evidence and later accepted user corrections; surface consequential conflicts that remain unresolved.
- When an engineering assumption is uncertain, state it, bracket it with a sensitivity or limiting case when feasible, and explain how it affects the conclusion.
- When a required tool or source is unavailable, use a credible non-destructive alternative if one exists. Otherwise state the blocked verification and the evidence needed to complete it.
- Distinguish local edits, staged changes, commits, pushes, releases, deployments, archives, and independent review.

## Task Router

Read only the references needed for the task.

| Task | Read |
| --- | --- |
| Research brief or trade study | [brief-template.md](references/brief-template.md) |
| Technical analysis, DOE, plotting, or results discussion | [technical-writing-analysis.md](references/technical-writing-analysis.md) |
| Paper drafting or structural revision | [paper-writing-style.md](references/paper-writing-style.md) |
| Review article drafting, revision, or evidence-mapped narrative/scoping review | [review-article-workflow.md](references/review-article-workflow.md) |
| Reviewer response, highlighted manuscript, Overleaf package, or submission audit | [manuscript-revision-submission.md](references/manuscript-revision-submission.md) |
| Literature review or research-gap synthesis | [literature-review.md](references/literature-review.md) |
| Citation repair, bibliography audit, or claim verification | [citation-integrity.md](references/citation-integrity.md) |
| Dataset, software, benchmark, or repository-centered review | [dataset-software-review.md](references/dataset-software-review.md) |
| Experiment planning or uncertainty analysis | [experimental-design-and-uncertainty.md](references/experimental-design-and-uncertainty.md) |
| CFD, ROM, surrogate, or ML credibility | [model-verification-and-ml-credibility.md](references/model-verification-and-ml-credibility.md) |
| Material result change or construct redefinition | [result-change-and-construct-audit.md](references/result-change-and-construct-audit.md) |
| Data provenance, benchmark design, research package, or public release | [data-provenance-and-release.md](references/data-provenance-and-release.md) |
| Figure, table, Word, PDF, spreadsheet, or slide QA | [scientific-figure-and-artifact-qa.md](references/scientific-figure-and-artifact-qa.md) |
| Thermal-fluid AI/ML workflow | [ai-tools-thermal-fluids.md](references/ai-tools-thermal-fluids.md) |
| Research code, pipeline, notebook, or package | [research-coding.md](references/research-coding.md) |
| Overleaf, VS Code, GitHub, git, or archival toolchain | [research-toolchain.md](references/research-toolchain.md) |
| Federal proposal or technical narrative | [proposal-development.md](references/proposal-development.md) |
| Research presentation or poster | [presentation-slides.md](references/presentation-slides.md) |
| Mechanical-engineering teaching material | [teaching-mechanical-engineering.md](references/teaching-mechanical-engineering.md) |
| Invention disclosure or commercialization support | [innovation-commercialization.md](references/innovation-commercialization.md) |
| Research-project logo, laboratory or software identity, icon, wordmark, or brand asset pack | [research-logo-and-identity.md](references/research-logo-and-identity.md) |
| Explicit request to match Han Hu's established research-writing style | [han-hu-research-style.md](references/han-hu-research-style.md) |
| Calibrated Han Hu manuscript drafting or revision with a private corpus | [han-hu-style-calibration-protocol.md](references/han-hu-style-calibration-protocol.md) |

For document, PDF, spreadsheet, or presentation files, also use any available format-specific skill for file manipulation and rendering. Keep this skill responsible for engineering validity and scientific interpretation.

For a manuscript authored or supervised by Han Hu, read [han-hu-research-style.md](references/han-hu-research-style.md) together with the task-specific paper and figure references even when the request does not explicitly ask for style matching. When the user provides or configures a private style-calibration corpus, also read [han-hu-style-calibration-protocol.md](references/han-hu-style-calibration-protocol.md), retrieve only genre-matched evidence, and report the evidence status of the exemplars used.

For iterative peer-review work, use `reviewer-author-loop` as the process scaffold when available. Apply this skill to physics, equations, instrumentation, uncertainty, data reduction, figures, modeling assumptions, and claim support.

## Output Contract

- Lead with the engineering answer, finding, or decision.
- State material assumptions, definitions, units, validity ranges, and evidence class.
- Explain the governing mechanism and compare credible alternatives or bounds.
- Report uncertainty, validation, failure modes, and residual risk at the level needed by the claim.
- Provide traceable artifacts and exact verification results when files or code are involved.
- End with the smallest useful next calculation, experiment, simulation, source check, or author decision.
