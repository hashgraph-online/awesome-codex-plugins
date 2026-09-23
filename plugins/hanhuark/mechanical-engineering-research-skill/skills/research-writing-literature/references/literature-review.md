# Critical Literature Review

Use this reference when producing literature reviews, related-work sections, citation maps, research-background sections, review figures/tables, or paper discovery strategies.

## Core Principle

Treat literature review as research analysis, not paper collection.

Reading papers and writing one or two sentences about each paper is only preliminary data collection. A good review adds the author's own analysis: patterns, limitations, challenges, mechanisms, disagreements, opportunities, and synthesis across papers.

Effective review work should integrate:

- Reading and writing: find, understand, summarize, compare, and synthesize sources.
- Doing: build CAD models, write analysis code, digitize plots, run calculations, simulate cases, or perform preliminary tests when needed to understand a paper.
- Communicating: talk to experts, manufacturers, collaborators, or authors when papers do not contain enough practical detail.

Assume that some papers cannot be fully understood from reading alone. When needed, reproduce a calculation, implement a model, inspect geometry, digitize a figure, or run a small baseline case to understand the method and limitations.

## Review As A Story

Write the review as the user's own story, not as a concatenated list of paper summaries.

The review should answer:

- Why does this field or problem matter?
- What are the main approaches, theories, methods, materials, designs, diagnostics, or manufacturing routes?
- What has each approach clarified or enabled?
- What limitations, contradictions, or unresolved challenges remain?
- Why do these challenges persist?
- What opportunities, future work, or research directions follow from the synthesis?
- How does the user's current or proposed work fit into this landscape?

If a review only teaches the writer what others have done, it is preliminary. A mature review contributes something new through critical analysis, outlook, synthesized trends, mechanism maps, taxonomies, benchmark plots, summary tables, or a clarified research framework.

## Literature Review Workflow

1. Start from the research question and target decision.
   - Define what the review must enable: choosing a manufacturing method, selecting a model, designing a diagnostic, interpreting data, or framing a manuscript.

2. Identify seminal work.
   - Start with papers that introduced major theories, methods, benchmark datasets, structures, models, or experimental approaches.
   - Do not start only from the newest papers; understand the origin of the ideas.

3. Trace the past and future of key references.
   - For each key reference, read its introduction and bibliography carefully. This is the past of the work.
   - Search for papers that cited the key reference. This is the future of the work.
   - Use citation tracing to identify main players, competing schools of thought, and how the field evolved.

4. Search selectively and balance coverage.
   - Avoid overciting one research group, one theory, or one method when multiple major approaches exist.
   - For mature fields, cite representative and high-impact papers rather than every available paper.
   - Ensure coverage includes major theories, major experimental methods, key materials/geometries, and important contradictory results.

5. Extract comparable information.
   - Capture geometry, material, working fluid, operating conditions, manufacturing method, diagnostics, performance metrics, correlations, assumptions, and uncertainty.
   - Convert symbols and definitions into a unified notation when comparing equations.
   - Digitize figures when needed and allowed by the task; clearly mark digitized values and likely uncertainty.

6. Synthesize rather than list.
   - Group papers by mechanism, theory, design family, method, metric, material, operating regime, or unresolved challenge.
   - Identify trends, scaling behavior, agreement, disagreement, limitations, and missing diagnostics.

7. Connect review to doing and communicating.
   - Use the review to decide what calculation, CAD model, code, experiment, manufacturer question, or expert conversation should happen next.
   - Use results from doing and communicating to refine the literature search.

## Critical Review Expectations

A critical review should include more than summary.

It should identify:

- Limitations of existing studies.
- Challenges that explain why issues remain unsolved.
- Conflicting conclusions and possible causes of disagreement.
- Missing diagnostics, missing operating regimes, or missing practical constraints.
- Trends and patterns visible only after comparing multiple papers.
- Main directions and future work.
- Opportunities created by new measurement methods, models, fabrication methods, or datasets.

Avoid writing "to the best of our knowledge, no literature has been published on this topic" as the main novelty claim. Instead, ask:

- Is the topic important? If not, why study it?
- If it is important, why has it not been solved?
- Is the barrier measurement difficulty, fabrication difficulty, coupled physics, lack of theory, cost, throughput, scale-up, or missing diagnostics?
- How does the proposed work overcome that barrier?

## Citation And Synthesis Style

Use professional manuscript citation style.

- Refer to papers by the first author's last name followed by "et al." when the sentence names the authors, such as "Rahman et al. demonstrated..." Do not write long author lists such as "Author 1, Author 2, Author 3, and Author 4..." in the prose.
- Avoid vague phrasing such as "Author and collaborators" unless the exact paper or group relationship matters.
- Use citation placeholders or the user's citation format consistently, such as `Rahman et al. [12]` or `Rahman et al. (2014)`, depending on the manuscript style.
- Check that the named first author matches the actual first author of the cited paper.

Write compact synthesis instead of redundant two-sentence summaries.

- Avoid this pattern: "Rahman et al. studied X. Their results show Y."
- Prefer a single purposeful sentence when possible: "Rahman et al. used X to demonstrate Y."
- Use two sentences only when the method and conclusion each need emphasis, or when a limitation, contrast, or mechanism must be developed.

For each cited paper or group of papers, decide whether it is:

- A key reference that deserves discussion of method, result, mechanism, and limitation.
- A background reference that only needs acknowledgment within a category.
- A comparison reference used to position the user's data, model, or method.

Do not give every background reference a full sentence. Doing so makes the review read like an annotated bibliography instead of a synthesis.

## Background Reference Grouping

Background references should be acknowledged efficiently and accurately.

When many studies belong to different categories, group citations by category rather than bundling all references at the end of one broad sentence.

Good pattern:

```text
Textured boiling surfaces have been developed in many forms, including micropillar arrays [15-21], re-entrant cavities [1,22,23], ordered porous structures [24-27], disordered microporous coatings [28-31], nanowires [32-36], and hierarchical multiscale structures [20,37-56].
```

This structure is better than either:

- writing one sentence for every background paper, which is too slow and redundant; or
- placing one large citation range at the end of the sentence, which hides the fact that the papers belong to different technical categories.

Use category-level background citations when:

- the purpose is to acknowledge the breadth of prior work;
- the individual papers are not central to the current argument; or
- the review is setting up a transition to the few papers that matter most.

After category-level citations, select only the most relevant papers for deeper discussion.

## Group Review To Gap Transition

After reviewing a group of references, explicitly state the limitation, unresolved issue, or knowledge gap that motivates the present work.

Use this logic:

1. Summarize the research category or theory.
2. Cite representative references in the right categories.
3. State what the group of studies has established.
4. State what remains unclear, limited, contradictory, difficult to measure, or insufficiently modeled.
5. Explain how that limitation motivates the present study.

Example pattern:

```text
Prior studies have shown that structured surfaces can enhance boiling performance through increased nucleation density, capillary liquid supply, and modified liquid-vapor interfacial dynamics [category-specific citations]. However, the relative contribution of these mechanisms remains difficult to isolate because most measurements observe the apparent interface rather than liquid replenishment within the structures. This limitation motivates the present use of multimodal diagnostics to connect surface wickability with boiling behavior.
```

Do not end a paragraph after only summarizing prior work. The paragraph should usually end by pointing to a limitation, gap, challenge, implication, or transition.

## Review Figures, Tables, And Charts

Use figures, charts, and tables as analysis tools.

Valuable review artifacts include:

- Taxonomy figures that classify technologies, mechanisms, theories, structures, diagnostics, or manufacturing approaches.
- Benchmark plots that compare performance metrics across literature and the user's work.
- Summary tables of geometry, material, dimensions, method, operating conditions, and performance.
- Mechanism maps that connect structures or process parameters to physical effects and outcomes.
- Equation comparison tables with a unified symbol system and stated assumptions.
- Timeline or citation-map figures showing how ideas developed from seminal work to current directions.
- Cost, throughput, scalability, and limitation tables for manufacturing or experimental methods.

When making a comparison plot:

- Use color to distinguish source or study group when useful.
- Use marker shape to distinguish material, structure type, fluid, or method.
- Include the user's result only when directly comparable; otherwise explain why the comparison is imperfect.
- Use the plot to draw a conclusion about generalizability, gaps, or positioning, not only to decorate the review.

Even if a review figure contains no new experimental data, it can contribute new knowledge by organizing scattered literature into a clear framework.

## Literature-Grounded Positioning

Compare the user's work against literature honestly.

- If the user's performance is not better than prior work, state that plainly.
- Then identify other contributions: transient versus steady-state behavior, multimodal diagnostics, new measurement access, model validation, manufacturability, cost, throughput, scalability, or mechanism clarification.
- Use literature comparison to decide whether the work should emphasize performance improvement, fundamental understanding, method development, or practical feasibility.

## Manufacturing And Technology Reviews

When reviewing manufacturing options, include more than technical feasibility.

Compare:

- Achievable geometry and material compatibility.
- Process constraints, tolerances, defects, and post-processing.
- Throughput, cost, vendor availability, maturity, and scalability.
- Risks, failure modes, inspection methods, and quality control.
- What must be tested or asked of manufacturers before down-selection.

Use communication with manufacturers or experts as review evidence, but label it clearly as expert/vendor input rather than peer-reviewed literature.

## Quality Check

Before finalizing a literature review, ask:

- What new knowledge does this review contribute?
- Are the contributions critical analysis, outlook, synthesized trends, benchmark comparisons, taxonomy, or unified theory/model comparison?
- Does the review identify main players and seminal work?
- Does it avoid overrepresenting one group, one theory, or one convenient cluster of papers?
- Are the figures, tables, or charts doing analytical work?
- Does the review explain why unresolved problems remain difficult?
- Does the review lead naturally to a research question, DOE, model, experiment, or design decision?
