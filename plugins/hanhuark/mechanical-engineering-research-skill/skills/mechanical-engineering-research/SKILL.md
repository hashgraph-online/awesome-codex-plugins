---
name: mechanical-engineering-research
description: Research, write, code, analyze, present, and develop proposals for thermal-fluid mechanical engineering work with source-aware rigor. Use for heat transfer, fluid mechanics, thermodynamics, HVAC, energy systems, turbomachinery, pumps, piping, CFD review, experiment planning, correlation validity checks, dimensionless groups, uncertainty analysis, standards, datasheets, papers, patents, AI/ML tools, computer vision, sequence regression, surrogate modeling, research coding, Overleaf, VS Code, GitHub, git, federal grant proposals, DOE/NSF/NASA-style narratives, invention disclosure, provisional patent support, commercialization, and trade studies. Produces technical briefs, critical literature reviews, proposal narratives, review-criteria responses, manuscript sections, methods, results discussions, data-analysis plans, plots, presentations, design comparisons, calculation plans, reproducible code, repository workflows, disclosure drafts, patent-support packets, and research roadmaps.
---

# Mechanical Engineering Research

## Overview

Use this skill to research thermal-fluid systems with engineering rigor: define the question, collect reliable sources, preserve assumptions and validity ranges, and separate verified evidence from inference.

## Workflow Coordination

For full paper, proposal, review-article, thesis chapter, or major manuscript workflows, use an academic-research workflow as the scaffold when one is available, and use this skill as the thermal-fluid/mechanical-engineering judgment layer.

Treat the roles as:

- **Academic research workflow**: organize the process, checkpoints, outline, drafting sequence, review/revision loop, citation/claim checks, and finalization.
- **Mechanical engineering research skill**: enforce domain logic, physical reasoning, literature synthesis standards, methodology detail, assumptions, data-analysis rigor, figure discussion, plotting, presentation quality, AI/ML interpretation, reproducible coding, and proposal-specific technical judgment.

When both are available, do not let a generic academic workflow overwrite domain judgment. Apply this skill whenever deciding whether the research question, gap, method, DOE, model assumptions, interpretation, figure narrative, or proposal significance is mechanically and thermally sound.

## Research Workflow

1. Clarify the engineering objective.
   - Identify the system, working fluid, operating regime, geometry, boundary conditions, performance metric, and constraints.
   - Ask for missing high-impact values only when they determine the research path; otherwise state assumptions and proceed.

2. Build a source hierarchy.
   - Prefer standards, textbooks/handbooks, peer-reviewed papers, manufacturer datasheets, government or lab reports, and primary patents.
   - Use web search for current papers, standards status, products, prices, regulations, or citations. Cite sources with links whenever browsing is used.
   - Treat blogs, marketing pages, forum posts, and uncited summaries as orientation only unless the user explicitly asks for informal context.

3. Extract engineering substance.
   - Capture equations, correlations, dimensionless groups, material limits, empirical constants, and uncertainty.
   - Record applicability limits: Reynolds/Rayleigh/Nusselt ranges, Prandtl range, Mach/compressibility assumptions, phase-change regime, geometry, roughness, orientation, temperature/pressure range, and fluid property source.
   - Note what was measured, simulated, or assumed.

4. Compare alternatives by mechanism.
   - Explain why each design or model performs differently, not only which is "best."
   - Consider pressure drop, heat-transfer coefficient, pumping power, fouling, manufacturability, instrumentation, maintenance, safety, cost, and scaling behavior.

5. Produce a decision-ready output.
   - Lead with the answer or recommendation.
   - Include assumptions, key evidence, equations/correlations, source quality, uncertainty, and next verification steps.
   - Mark engineering inference explicitly when sources do not directly prove a claim.
   - Use a clear paragraph logic flow: each paragraph starts with a central topic sentence, and each following sentence develops, supports, qualifies, or transitions from that topic.

## Output Patterns

For a research brief, use:

- **Question**: One sentence defining the engineering problem.
- **Bottom Line**: Concise answer, recommendation, or state of evidence.
- **Assumptions**: Operating conditions, geometry, fluid, and scope.
- **Evidence**: Source-backed findings with citations.
- **Models/Correlations**: Equations, variables, units, and validity limits.
- **Tradeoffs**: Performance, cost, safety, reliability, manufacturability, and uncertainty.
- **Gaps**: What remains unverified or standards-dependent.
- **Next Steps**: Calculations, experiments, simulations, or standards lookups.

For a literature review, read `references/literature-review.md`. Group sources by mechanism, method, design family, or unresolved question rather than listing papers chronologically.

For federal research proposals, DOE EPSCoR/National Laboratory partnership proposals, full narrative expansions, review-criteria responses, proposal figure planning, preliminary-results integration, or ready-to-submit proposal polishing, read `references/proposal-development.md`.

For a design comparison, include a compact decision matrix and explain the dominant physics behind each score.

For manuscript-style technical writing, read `references/technical-writing-analysis.md` before drafting or revising introductions, methods, modeling sections, results/discussion, data analysis, or plot narratives.

For full technical papers, journal manuscripts, or paper-style section drafting, also read `references/paper-writing-style.md` to match the preferred section logic, abstract style, figure-led results, and conclusion patterns.

For experiments, simulations, or parameter studies, use `references/technical-writing-analysis.md` to plan a detailed baseline case and hypothesis-driven DOE before proposing broad sweeps or large case matrices.

For research presentations or slide decks, read `references/presentation-slides.md` before creating slide outlines, slide content, speaker notes, or visual-story plans.

For AI/ML-assisted thermal-fluid research, read `references/ai-tools-thermal-fluids.md` before recommending computer vision, sequence regression, surrogate modeling, sensor fusion, dimensionality reduction, or data-driven control workflows.

For research code, scripts, notebooks, data pipelines, plotting code, CFD automation, or ML implementation, read `references/research-coding.md` before writing or reviewing code.

For research tool workflows involving Overleaf, VS Code, GitHub, or git, read `references/research-toolchain.md` before advising on manuscript collaboration, code/debugging workflow, repository updates, archival releases, branches, commits, tags, or reproducibility hygiene.

For innovation, invention disclosure, provisional patent support, utility patent technical content, or technology commercialization, read `references/innovation-commercialization.md` before drafting disclosure answers, non-confidential summaries, technical descriptions, figure lists, prior-art comparisons, market/use-case notes, inventor response emails, or commercialization briefs. Support the technical and strategic content, but do not provide legal advice; defer claim scope, filing strategy, assignments, declarations, and prosecution decisions to Technology Ventures and patent counsel.

## Thermal-Fluid Checks

Before finalizing, check whether the answer should account for:

- Laminar, transitional, turbulent, natural, forced, or mixed convection.
- Internal, external, developing, fully developed, compressible, multiphase, or non-Newtonian flow.
- Radiation, conduction contact resistance, fins, heat pipes, boiling, condensation, or evaporative cooling.
- Pump/fan curves, NPSH, cavitation, choking, surge, fouling, erosion, corrosion, thermal stress, or fatigue.
- Property variation with temperature and pressure.
- Similarity/scaling limits between benchtop tests, CFD, and full-scale systems.
- Applicable ASME, ASTM, ISO, API, ASHRAE, NFPA, or local code requirements.

## CFD And Experiments

When discussing CFD:

- Identify turbulence model, wall treatment, mesh independence, boundary conditions, property models, convergence criteria, and validation data.
- Do not present CFD as evidence unless the setup and validation are known.
- Suggest simpler analytical or empirical checks as sanity bounds when available.

When discussing experiments:

- Identify sensors, calibration, uncertainty, repeatability, heat loss correction, flow development, and property measurement.
- Prefer outputs that can be independently reproduced from stated dimensions and conditions.

## Reference Files

Read `references/brief-template.md` when the user asks for a reusable research brief format, report outline, or deliverable template.

Read `references/technical-writing-analysis.md` when the user asks for technical writing, manuscript sections, data analysis, figures, plots, or results discussion.

Read `references/paper-writing-style.md` when the user asks to write, revise, outline, or polish a journal paper, conference paper, manuscript, abstract, introduction, methods, results/discussion, conclusion, or paper-style technical narrative.

Read `references/literature-review.md` when the user asks for a literature review, related-work section, research background, citation map, state-of-the-art comparison, review figure/table, future-work analysis, or paper discovery strategy.

Read `references/proposal-development.md` when the user asks for grant/proposal development, solicitation alignment, pre-application expansion, DOE EPSCoR or National Lab partnership narratives, collaborator document planning, review-criteria mapping, milestones, preliminary-results integration, proposal figures, reviewer-friction diagnosis, references, or ready-to-submit polish.

Read `references/presentation-slides.md` when the user asks for presentation slides, a research talk, conference talk, group-meeting slides, slide-by-slide narrative, speaker notes, animation/video suggestions, or figure-focused storytelling.

Read `references/ai-tools-thermal-fluids.md` when the user asks about AI tools, machine learning, computer vision, BubbleID, SeqReg, CFDTwin, DataDroid-LAM, MEEG-54403, sensor fusion, surrogate modeling, dimensionality reduction, thermal-fluid datasets, or ML-enhanced data analysis.

Read `references/research-coding.md` when the user asks for coding help, research scripts, notebooks, data processing, plotting, reproducibility, simulation automation, CFD post-processing, ML implementation, repository organization, or code review.

Read `references/research-toolchain.md` when the user asks about Overleaf writing/editing, VS Code coding/debugging, GitHub repo updating or archiving, git branches/commits/tags/releases, repository hygiene, manuscript-code-data synchronization, or reproducible project handoff.

Read `references/innovation-commercialization.md` when the user asks for invention disclosure, Technology Ventures, Sophia disclosure, provisional patent, utility patent application support, patent counsel feedback, USPTO filing support, notice of allowance/grant tracking, licensing, startup/commercialization strategy, non-confidential summaries, or translating research results into protectable/commercializable technology.
