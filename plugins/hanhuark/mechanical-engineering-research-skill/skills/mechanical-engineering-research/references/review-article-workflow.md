# Review Article Workflow

Use this reference when drafting, substantially revising, or auditing a narrative, scoping, taxonomy-driven, or systematic review article in mechanical engineering. For a narrower related-work section, use [literature-review.md](literature-review.md). For citation mechanics, use [citation-integrity.md](citation-integrity.md).

## 1. Declare The Review Contract

Before searching or drafting, state what the review is and is not:

- review type: narrative, scoping, taxonomy-driven, systematic, or mixed;
- engineering question and intended decision or community need;
- organizing logic: mechanism, scale, diagnostic, data modality, model task, design family, or performance metric;
- corpus boundary, time window, and source families;
- contribution beyond collection: critical synthesis, taxonomy, definition table, comparison, benchmark framework, or evidence-backed roadmap.

Do not claim systematic or PRISMA-level completeness without a documented protocol. For a narrative review, describe the search and screening method plainly enough that readers can understand its coverage and limits.

## 2. Build The Corpus Across Release Channels

Use complementary discovery routes because engineering knowledge can appear first as a journal article, preprint, dataset, code repository, conference benchmark, laboratory release, standard, or archival record.

1. Start from seminal theories, representative experiments, established correlations, and major diagnostic or model families.
2. Use backward and forward citation tracing around the central sources.
3. Search domain terms together with method, data, and infrastructure terms. Include synonyms that authors outside the core discipline may use.
4. Search primary publishing records and relevant code, data, and benchmark archives directly when software or datasets are in scope.
5. Diagnose discovery blind spots. Check title changes, repository-first releases, preprint-to-journal transitions, author or laboratory variants, and adjacent AI/scientific-computing venues.
6. Record search date, channels, representative queries, inclusion criteria, exclusion criteria, and resource-screening criteria at a level appropriate for the review type.

Treat repositories and web records as evidence of availability, version, and documentation. Use primary papers, data records, standards, or official technical documentation for scientific claims.

## 3. Extract Evidence Before Writing Synthesis

For each central source, capture only fields needed for comparison:

- physical system, geometry, material or fluid, operating regime, and applicability boundary;
- measurements, simulation assumptions, data representation, labels, preprocessing, and uncertainty;
- model task, baseline, split logic, metrics, validation, and failure cases;
- publication state, stable identifier, archive/version, license, software maintenance, and reuse constraints.

For definitions, equations, and dimensionless quantities, preserve the reference state, averaging convention, geometry scale, property source, and validity range. Do not merge values that use incompatible definitions or boundaries.

Use a claim-evidence ledger for consequential statements. Mark a resource as reported, archival, maintained, proposed, illustrative, or unverifiable based on what was actually checked.

## 4. Build A Physics-First Review Story

Use the engineering problem to organize the narrative. A common structure is:

1. Application need and governing transport phenomena.
2. Coupled mechanisms, multiscale effects, or measurement limitations that make prediction or design difficult.
3. What current diagnostics, datasets, models, or methods reveal and where they remain insufficient.
4. The review taxonomy or comparison framework.
5. Evidence organized by the framework, including limitations and conditions of transfer.
6. A bounded roadmap, research gap, or design implication.

Introduce data-driven or AI/ML methods after the physical need and evidence gap are clear. Present them as tools for measurement, reconstruction, prediction, interpretation, or design, not as replacements for governing physics.

Give closely related figures distinct jobs. For example, one may establish coupled mechanisms and another may establish scale coupling or modeling limits. Cite each figure where its specific role advances the argument.

## 5. Use Tables And Figures As Critical Analysis

Every review table or figure should answer a comparison question. Include only columns, axes, and visual encodings that affect interpretation.

- A definition table should state common meaning, ambiguity, and metadata needed for reuse.
- A dataset or software table should separate modality, task, physical scope, access state, evidence level, and reuse requirements.
- A benchmark table or figure should state the split unit, target, metric, baseline, uncertainty treatment, and generalization boundary.
- A literature comparison plot should retain source identity, units, data-extraction status, definition differences, and uncertainty.

If heterogeneous resources appear in one table, label their status instead of implying equivalence. A qualitative maturity rubric may use terms such as `unclear`, `emerging`, `partial`, and `mature` only when the criteria are defined and the figure/table states that it assesses infrastructure readiness, not scientific merit or laboratory quality.

## 6. Keep Roadmaps And Community Infrastructure Honest

For benchmarks, databanks, curation workflows, tool libraries, or other infrastructure, separate:

- **existing:** publicly accessible, citable, and verifiable components;
- **under development:** documented work with incomplete implementation or validation;
- **proposed:** recommended architecture, governance, metadata, or future evaluation.

State this status in nearby prose and in the caption of a conceptual figure. Do not present a seed benchmark, initial repository, or conceptual workflow as a completed field standard.

Describe generalization in engineering terms. Distinguish random records from held-out operating conditions, geometries, materials, fluids, facilities, time histories, or laboratories. Do not compare headline accuracy across unrelated datasets as though it establishes model superiority.

## 7. Balance Scope And Tone

- Organize research by mechanism, method, evidence, or unresolved gap rather than author chronology.
- Use `FirstAuthor et al.` when naming a study. Do not use long author-chain labels in the main text.
- Treat author-group datasets, packages, and prototypes as case studies or seed efforts within the field-wide evidence base.
- Use direct, evidence-calibrated wording. State limitations, incomplete coverage, and uncertainty explicitly.
- Prefer developed topic-centered paragraphs over lists of studies, promotional language, or generic claims about impact.

Use [paper-writing-style.md](paper-writing-style.md) for paragraph construction, figure discussion, and sentence-level style.

## 8. Review-Article Completion Audit

Before finalizing, verify:

1. The stated review type matches the actual search and screening evidence.
2. The introduction moves from the physical problem to the evidence gap and review contribution.
3. Every major figure and table is cited, interpreted, and assigned a distinct role.
4. Definitions, units, equations, reference states, and applicability limits are consistent across text, tables, and figures.
5. Tables distinguish publication state, evidence, and reuse maturity where resource types differ.
6. Proposed infrastructure, standards, and roadmaps are explicitly labeled as proposed or under development.
7. Claims about data, software, benchmarks, access, versions, and licenses are checked against the appropriate primary record.
8. Numeric citations, bibliography order, figure permissions, data/software availability, and cross-references have been audited after structural edits.
9. The conclusion states what the review clarifies, what remains unresolved, and what evidence or community work is needed next.

For a revised manuscript, also read [manuscript-revision-submission.md](manuscript-revision-submission.md). For dataset/software-centered reviews, also read [dataset-software-review.md](dataset-software-review.md).
