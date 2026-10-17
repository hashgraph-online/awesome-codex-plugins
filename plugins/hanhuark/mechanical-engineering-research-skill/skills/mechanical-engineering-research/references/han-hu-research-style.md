# Han Hu Research-Writing Style

Use this reference for manuscripts authored or supervised by Han Hu and when the user explicitly asks to match Han Hu's established research-writing style. Apply these preferences after the domain and integrity checks in the main skill. When a private style-calibration corpus is available, also use [han-hu-style-calibration-protocol.md](han-hu-style-calibration-protocol.md); its evidence labels control which exemplars may be treated as accepted-author text.

## Stable Style Primitives

- Start from the mechanical or thermal-fluid problem, coupled physics, and multiscale difficulty before introducing AI, software, or data infrastructure.
- Treat AI/ML as a means to measure, interpret, reconstruct, predict, or organize physical behavior rather than the final scientific point.
- Frame laboratory resources as case studies or seed efforts within a balanced field-wide ecosystem.
- Write connected technical paragraphs with one central purpose. Avoid choppy sentence strings, rhetorical self-questioning, excessive colon clauses, and editorial or promotional commentary.
- State the technical finding, mechanism, limitation, or need directly. Use `indicates` for supported interpretation, `suggests` for weaker inference, and `demonstrates` only for direct evidence.
- Make figures, tables, and equations carry the argument. Give related figures distinct roles in the prose.
- Prefer concise final communication, but do not reduce scientific depth for a high-risk audit, review, or revision.
- Use professional publication language without casual expressions, reader guidance, prompt-like statements, or meta-commentary about wording. State the technical meaning directly.
- Avoid excessive colons and semicolons. Prefer connected complete sentences, using i), ii), and iii) for compact enumerations when needed.
- Avoid one-sentence paragraphs and strings of very short paragraphs. Each paragraph should develop one central topic through evidence, interpretation, and implication.
- Use short noun phrases for section titles. Do not place conclusions in headings.
- Refer to subfigures as `Fig. 6a`, `Fig. 6b`, and so forth. Do not use "panel" in manuscript text or captions.

## Reader-First Narrative

For an abstract, introduction, conclusion, or other high-level passage, make the main story understandable before introducing a dense list of inputs, metrics, or acronyms. An informed reader outside the immediate specialty should be able to identify i) the problem, ii) what the work does, iii) what the main result is, and iv) why the result matters.

- State what is developed, measured, modeled, or analyzed in direct language before listing the data sources, variables, or implementation details.
- Do not treat combining datasets, building a map, or running a model as the innovation by itself. State what that integration is used to estimate, compare, test, reveal, or support.
- Keep the narrative chain explicit: existing work and its remaining gap; the consequence of that gap; the present response; the principal result; and the bounded practical implication.
- Do not make a known limitation the paper's main conclusion. Show what the present work quantifies, distinguishes, tests, or makes possible because it addresses that limitation.
- State the consequence of a methodological gap when evidence supports it. For example, an unsupported national estimate may be mistaken for a local effect, or scarce validation effort may be directed to the wrong cases.
- Prefer two connected sentences over one sentence that combines a long list of inputs, methods, findings, and implications. Remove repeated restatements of the same purpose or limitation.
- Use plain terms for the function of a method before introducing specialized terminology. Retain technical precision, but define non-obvious abbreviations and avoid an array of terms that a reader does not need to understand the central message.

For conclusions, state what the study did, what was learned, and how the finding should be used. Keep numerical detail to the one or two findings that carry the take-home message. Do not cite figures in the conclusion unless the citation is necessary to resolve genuine ambiguity. Do not repeat the detailed methods, a catalog of assumptions, or the figure-by-figure results discussion.

## Reader-Side Interrogation

Before accepting a title, abstract, introduction, conclusion, or other high-level passage, temporarily read it as an informed reader who has not followed the project. Treat the following questions as a required clarity gate rather than an optional copy-editing exercise:

- **Title:** What is the research object, what was actually done, and what will the reader reasonably expect to find? Does the title imply a direct measurement, prediction, validation, or causal finding that the evidence does not support? Remove geographic, methodological, or descriptive words that merely repeat information already conveyed elsewhere in the title.
- **Method labels:** What does each central label such as `screening`, `assessment`, `framework`, `scenario`, `priority`, or `validation` mean in this particular study? If an informed reader cannot answer from the first one or two sentences, use a more ordinary term or define the label by its inputs, calculation, and decision purpose.
- **Specialized terms:** Is the term established in the target field and necessary for the argument? If it is a convenient internal phrase, replace it with the physical quantity, analysis, decision, or uncertainty it denotes. Do not retain a coined label merely because it is grammatically compact.
- **Scope:** Does the passage distinguish estimated, modeled, screening-level, and measured quantities? If the title is intentionally concise, state the decisive scope limitation and the missing evidence in the abstract and conclusion rather than forcing every qualification into the title.
- **Usefulness:** Does each sentence tell the reader what the analysis was used to determine, compare, or support? A list of datasets or a statement that information was combined is not a contribution without the resulting analytical purpose.

For assumption-based analysis, define an `assumption case` or `scenario` at first use as a specified set of input choices. State whether the cases are sensitivity tests, bounds, probabilities, or projections. Do not let an energy-planning term such as `scenario` imply a forecast or likelihood when the work only varies deterministic inputs.

After this interrogation, ask one final question: could a domain colleague explain the paper's purpose, principal result, and appropriate use after reading only the title, abstract, and conclusion? If not, revise the structure and terminology before adding more detail.

Use [paper-writing-style.md](paper-writing-style.md) for paper structure, [literature-review.md](literature-review.md) for synthesis, and [manuscript-revision-submission.md](manuscript-revision-submission.md) for revision/submission details. Do not duplicate their checklists here.

## Figure And Caption Preferences

- Use Arial for all figure text unless the target journal explicitly requires another typeface. Keep font sizes legible and consistent at final publication dimensions.
- Italicize variable symbols. Keep units and subscript or superscript descriptors in roman type unless a mathematical convention or journal rule requires otherwise.
- Place subfigure labels `(a)`, `(b)`, and so forth outside the plotting box near the upper-left corner, aligned just above the y-axis label and level with the top of the axes with a small cushion, when the journal layout permits.
- Give every subplot a unique sequential label. Remove excessive whitespace and prevent labels, legends, annotations, and data from overlapping.
- Write descriptive captions as continuous prose. Identify the quantities, conditions, subfigure mapping, visual encodings, uncertainty treatment, and data-reduction choices without using the word "panel."
- Discuss figures with enough detail to identify both axes, the experimental or modeled conditions, the principal observation, and the physical interpretation.
- Use publication-facing operating conditions rather than internal case IDs. Use author-year labels for individual literature datasets.
- Do not use a generic corner uncertainty marker unless it is explicitly requested and its meaning is unambiguous.

## Manuscript Revision Calibration

When revising a manuscript to match this style, preserve the scientific evidence while strengthening the connection from engineering need to mechanism, method, result, and bounded implication. Revise the section and paragraph structure before making sentence-level edits; generic simplification alone is insufficient.

- Make the abstract evidence-dense. When the data support it, include two to three principal quantitative findings rather than incidental experimental detail, then state the specific capability or implication supported within the tested scope.
- Build the abstract as a compact story: problem, present method, what the method does with the evidence, principal findings, claim boundary, and practical use. Do not make the abstract a method catalog or a compressed results section.
- Synthesize the literature by application, architecture, material, diagnostic method, or modeling approach. Distinguish adjacent approaches from the specific remaining gap; do not claim that no prior work exists when relevant neighboring work exists.
- End an introduction by linking the specific gap and its consequence to the present contribution. Follow with a short road map that tells the reader what the paper examines and why each analysis is needed; do not merely list section contents or variables.
- Define experimental and model boundaries explicitly: system boundary, coordinate convention, imposed and inferred quantities, calibration, uncertainty, and the distinction between a fitted effective property and an intrinsic constituent property.
- Treat every principal result as a figure-led argument: orient the reader, report the quantitative observation, relate it to the physical architecture or mechanism, and give the design implication.
- Place each caveat near the claim it bounds. Identify the relevant unmeasured quantity, uncertain boundary, untested condition, or model-form limitation once, rather than repeating generic defensive qualifications throughout the manuscript.
- Use two to four numbered conclusions for multi-result papers. Each conclusion should state the finding, physical interpretation, and bounded implication, not merely restate a section heading.
- Do not resolve a substantive evidence gap by weakening prose alone. Identify the additional analysis, validation, or measurement required and preserve uncertainty and provenance in the final manuscript.

## Reviews Of Data, Software, And Benchmarks

- Organize by mechanism, modality, dimensionality, task, evidence maturity, and unresolved gap rather than author chronology.
- Use spatial-plus-temporal dimensionality when it helps organize multimodal data; do not force the taxonomy onto unrelated work.
- Connect data classes to plausible analysis or ML tasks and the physical quantities they expose.
- Treat initial benchmark releases as seed benchmarks and collaborative mechanisms unless coverage, governance, baselines, and external validation support a field-standard claim.
- Make physics metadata central: geometry, fluid/material, operating conditions, calibration, synchronization, uncertainty, data reduction, and useful dimensionless groups.
- Separate author-generated availability from third-party resources and avoid one-lab dominance.

Use [dataset-software-review.md](dataset-software-review.md) and [data-provenance-and-release.md](data-provenance-and-release.md) for the detailed workflows.

## Citation And Submission Habits

- Use `FirstAuthor et al.` in prose and avoid long author-chain labels.
- Verify citation intent after structural edits, especially numeric references, permissions, datasets, and software.
- Highlight only changed phrases, clauses, or sentences in marked manuscripts.
- Make reviewer responses complete enough to stand alone and include specific changes and locations.
- Keep one active Overleaf entry point and remove stale alternate source files from production packages.

Use [citation-integrity.md](citation-integrity.md) and [manuscript-revision-submission.md](manuscript-revision-submission.md) for the authoritative procedures.
