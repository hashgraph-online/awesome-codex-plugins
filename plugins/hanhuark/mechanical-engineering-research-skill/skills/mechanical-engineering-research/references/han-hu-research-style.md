# Han Hu Research-Writing Style

Use this reference for manuscripts authored or supervised by Han Hu and when the user explicitly asks to match Han Hu's established research-writing style. Apply these preferences after the domain and integrity checks in the main skill. When a private style-calibration corpus is available, also use [han-hu-style-calibration-protocol.md](han-hu-style-calibration-protocol.md); its evidence labels control which exemplars may be treated as accepted-author text.

## Concise Section Revisions

Use the description-observation-explanation-conclusion sequence in [technical-writing-analysis.md](technical-writing-analysis.md). Combine related plots when they explain one consistent story, and add a short purpose statement when needed to connect a subsection. Prefer essential table notes in the main text over an explanatory paragraph below the table; preserve venue-required footnotes. Apply the same concision to conclusions while retaining the principal finding and its evidence boundary.

## Stable Style Primitives

- Start from the mechanical or thermal-fluid problem, coupled physics, and multiscale difficulty before introducing AI, software, or data infrastructure.
- Treat AI/ML as a means to measure, interpret, reconstruct, predict, or organize physical behavior rather than the final scientific point.
- Frame laboratory resources as case studies or seed efforts within a balanced field-wide ecosystem.
- Write connected technical paragraphs with one central purpose. Avoid choppy sentence strings, rhetorical self-questioning, excessive colon clauses, and editorial or promotional commentary.
- State the technical finding, mechanism, limitation, or need directly. Use `indicates` for supported interpretation, `suggests` for weaker inference, and `demonstrates` only for direct evidence.
- Make figures, tables, and equations carry the argument. Give related figures distinct roles in the prose.
- Prefer concise final communication, but do not reduce scientific depth for a high-risk audit, review, or revision.
- Use professional publication language without casual expressions, reader guidance, prompt-like statements, or meta-commentary about wording. State the technical meaning directly.
- Avoid excessive colons and semicolons. Use complete sentences or an explicit causal or contrast relationship instead of punctuation as a shortcut. Retain colons and semicolons only when they are required in equations, labels, tables, citations, or metadata.
- Avoid one-sentence paragraphs and strings of very short paragraphs. Each paragraph should develop one central topic through evidence, interpretation, and implication.
- Use short noun phrases for section titles. Do not place conclusions in headings.
- Refer to subfigures as `Fig. 6a`, `Fig. 6b`, and so forth. Do not use "panel" in manuscript text or captions.

## Sentence Construction And Emphasis

A technical sentence should carry one dominant message. Parallel construction distributes weight evenly across its members, which feels complete but leaves the reader without a signal about which claim matters. This differs from legal drafting, where enumerated parallel clauses exist to close loopholes. In research prose the purpose is to convey a message, so the distinctive claim belongs in the main clause and the supporting requirements belong in subordinate or participial constructions.

- **Subordinate to emphasize.** When three clause-level actions appear in series, identify the one that is novel and promote it. "The system must read signals the record never held, act within the time the physics allows, and learn from the result" distributes weight across three equal members. "The system must recover signals the written record never contained, acting within the time the physics allows and improving from each outcome" places the novel claim in the main clause and demotes the two ordinary requirements.
- **Distinguish enumeration from rhetorical parallelism.** A list that names a complete set of real items is legitimate and should be kept, as in "optical, acoustic, electrical, and thermal signatures" or "fabricated, packaged, operated, and driven to failure." The pattern to revise is the series of parallel clauses, each asserting a separate claim.
- **Give short sentences specific content.** A brief sentence is acceptable when it carries a number, a mechanism, or a named object. A brief sentence that only generalizes, such as "The platform acts on the process," should be absorbed into the sentence that supplies the detail.
- **Name the object directly.** Replace generic interrogative clauses such as “determine how,” “identify which,” “test whether,” and “state what” with the substantive quantity, method, requirement, decision, or evidence object when that construction is clearer. For example, write “quantify the price,” “identify the required documentation,” “evaluate assignment adequacy,” or “specify the decision criteria.” Retain a question form only when the question itself is the scientific object.
- **Use evidence-specific vocabulary.** Use `record` only for an actual database entry, archival record, or formal official record. Otherwise name the relevant evidence directly, such as a measurement, observation, dataset, metadata field, permit, contract, plan, drawing, procedure, log, interconnection agreement, or supporting documentation.
- **Avoid definitional asides.** Constructions such as "X here means," "what this means is," and "in other words" read as spoken instruction. State the definition directly, as in "Embodiment in this platform refers to direct coupling with the process through sensors and actuators."
- **Lead with the subject.** A pseudo-cleft opener such as "What the random split rewards is the capacity to store the training windows" withholds the subject until the verb has already passed, and it does so in the sentence that usually carries the paragraph's conclusion. Write "The random split rewards the capacity to store the training windows."
- **Keep the subject short enough to hold.** When three long noun phrases precede the verb, the reader carries all three without yet knowing what is being said about them. "Independent boiling tests, propagation of the label uncertainty through the evaluation, and comparison of the learned representation against bubble-resolved measurements are required before the approach qualifies as a validated measurement technique" reaches its verb at word twenty-five. "Validating the approach as a measurement technique would require independent boiling tests, propagation of the label uncertainty through the evaluation, and comparison of the learned representation against bubble-resolved measurements" reaches it at word seven and is no longer.
- **Use the author's own test for a convoluted sentence.** The reader understands every word and is still confused by the sentence. The usual causes are a predicate that does not fit its subject, as in "the places where Fig. 4b departs from the ordering of Fig. 4a are the families for which that trade occurs", where places are equated with families; a supporting fact appended with `given that` after the claim; and a clause-level `and` joining two sentences that should be separate.
- **Diagnose a short sentence by what it omits.** "Table 3 and Fig. 8a report the estimates" is weak because it names two floats without saying what they hold, not because it is seven words. A short sentence that carries a number, a mechanism, or a named object is correct as written.
- **Prefer formal causal connectives.** Use `since`, `thus`, `therefore`, `as a result`, and `whereas` in place of `because` and `so`. Reserve `because` for a causal claim that carries genuine weight, and avoid `so` as a sentence connective in manuscript prose.
- **Do not define the subject by what it is not.** Avoid the contrast frames `X is A rather than B`, `X is A, not B`, and `not B but A` as a way to introduce an idea. Each one sets up an alternative that the reader never proposed and then rejects it, and the abstract subject and verb they usually carry, such as "availability is organized as," hide who does what. State the actor, the action, and the object in ordinary language, and let a figure or a later sentence carry the concept. Keep a contrast only when the alternative is a real competing option under discussion, such as a rival hypothesis, an existing method, or a design choice the reader would otherwise assume. A bullet heading, a diagnostic label, or a definition that exists to separate two things a reader confuses is doing contrastive work and is exempt. The rule governs the body prose of a manuscript, a proposal, or a response.

  | Avoid | Prefer |
  |---|---|
  | Availability in the hub is organized as a lifecycle rather than a download portal (Fig. 4). | The hub makes datasets available through four linked activities that repeat throughout the project (Fig. 4). |

  A contrast that names a real competing explanation stays. "The model depends on interfacial motion rather than static scene content" is correct as written, since static appearance is the explanation a reader would otherwise assume and the sentence exists to rule it out. The revision above names the actor and the action, uses the phrasing a colleague would use aloud, and removes a straw-man alternative. The cycle itself is shown in the figure and listed in the next sentence, so the opening sentence does not need the abstract label `lifecycle`.

- **Prefer common phrasing over abstract nominal constructions.** When an abstract noun is the subject of an abstract verb, as in "availability is organized as" or "engagement is structured around," rewrite with the actor as the subject and a concrete verb. The plain version is usually shorter and is understood on the first reading.

**Diagnostic pass.** Before final submission, count `rather than`, `, not`, `not … but`, `instead of`, `because`, `so`, and `which is` across the document, and flag any clause-level series of three. Of these, only `rather than` carries a usable rate. The other frames appear in ordinary appositives and in legitimate contrasts, so read each one and rewrite only those that reject an alternative no reader proposed. A rate above roughly one `rather than` per 300 words, or any paragraph containing two clause-level triads, indicates that emphasis has been distributed instead of placed. Use [anti-formulaic-writing.md](anti-formulaic-writing.md) for the surface-prose patterns that accompany these constructions.

## Paragraph Openers And The Skeleton Test

The first sentence of a paragraph delivers that paragraph's central idea, and the last delivers its message or its handoff to the next. Read the openers and closers in sequence with nothing between them. The argument should survive that reduction, and each opener should connect to the preceding closer. Put the paragraphs in random order and a reader should be able to restore the original one.

Failures the test catches:

- **An opener that points backward at something buried in the previous paragraph.** "The distinction is consequential here" names a distinction the skeleton cannot supply, so the transition is broken even though the sentence is grammatical.
- **An opener that announces that a comparison is possible.** "Figure 9e separates which quantity each feature follows" describes the act of looking. State the finding and let the figure pointer follow it in the next sentence.
- **An opener carrying a leftover number.** A paragraph opening "Pooling the cases weakens every correlation, to 0.55" starts on the residue of the previous analysis. Its central idea is the scope of the result, which an opener such as "These correlations hold within a case and do not transfer across operating condition" states directly.
- **An opener that forward-references what the paragraph never introduces.** Rewriting an opener creates this failure routinely: one new opening sentence referred to a maximum that the paragraph itself established three sentences later. Re-read the whole paragraph after every opener change.
- **A closer that delivers a requirement, a list, or a disclaimer.** A closing sentence must deliver a message.

Open with a purpose statement when a paragraph begins a new analysis, as in "To examine how vapor content and the operating threshold influence segmentation accuracy, Fig. 4 plots ...". One sentence then carries the transition and the description step together.

## Defensive Qualification

State the problem, what was done, and what was found. A manuscript is not a comprehensive book, and a catalog of what the work does not support belongs in neither the results nor the conclusions.

Keep a statement when it changes what a result means and is made once. Cut it when it denies a claim no reader made, or restates a limit the manuscript already states elsewhere. Evidence-class verbs stay on real claims. The trailing "although X does not isolate Y" clause bolted onto "is consistent with" duplicates the verb and goes.

Nearly always cuttable:

- "This result does not imply that ..." and other denials of a claim nobody made.
- A list of what a quantity is not.
- The same limitation stated in the methods, again in the results, and again in the conclusions.
- A result stated negatively. "does not demonstrate incremental information" becomes "adds no predictive accuracy for wall temperature beyond heat flux, mass flux, and inlet subcooling".

A regular-expression pass over `does not`, `do not`, `cannot`, `is not`, `precludes`, and `unvalidated` collects the candidates, and each one is then judged against the rule rather than deleted wholesale. On one manuscript this reduced 23 flagged sentences to 5 and removed 235 words, and the 5 that survived were load-bearing.

Defensive phrasing also generates reviewer confusion instead of preventing it. Two of four review comments on that manuscript landed on this register: "I do not understand this statement" against a compressed limitation clause, and "We can provide this" against a sentence listing what was unavailable.

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
- Confine the caption to description. Move results, interpretation, and the justification for a plotting choice into the section that uses them, and do not restate values already printed on the figure. Keep the protocol, calibration, or scope statement that bounds what the figure supports.
- Discuss figures with enough detail to identify both axes, the experimental or modeled conditions, the principal observation, and the physical interpretation.
- Use publication-facing operating conditions rather than internal case IDs. Use author-year labels for individual literature datasets.
- Keep the key that makes the figure readable when shortening a caption. Confining a caption to description does not license removing the definition of a symbol printed on the figure, the mapping from subfigure to model or condition, the identity of each series and marker, or the meaning of a reference line drawn across the axes. These are the first items lost when a caption is trimmed, and the loss is silent. Re-read every shortened caption against the rendered figure before accepting it.
- Do not use a generic corner uncertainty marker unless it is explicitly requested and its meaning is unambiguous.


## One Name Per Thing

A revision that renames a model, a dataset, a metric, or a protocol must propagate the new name through the manuscript, the supplement, the figure captions, the figure scripts, and the reviewer response. Reviewers read these side by side, so a residual variant reads as a second entity.

- Choose one term for each concept and sweep the variants after every structural edit. A single object acquiring three names across a package is the normal failure, not an unusual one: `final-frame CNN` against `residual CNN`, `random split` against `random division`, `predict` against `estimate`, `N_seq` against `L`.
- Never let one word carry two technical senses in one paper. A ConvLSTM whose head applies global pooling, discussed a few pages from a statement that two run series "are not pooled", gives `pooled` an architectural and a statistical meaning at once. The same trap appears with `residual` for a skip connection and for a recurrent correction term, and with a metric name reused for a proportion. Resolve it by renaming one sense to a term the paper already uses rather than by defining both.
- Prefer the name the figure, the table, and the methods section already print. A term that exists only in one paragraph of the results is a coined term, whether or not it was intended as one.
- State an abbreviation at first use in the body, and check that the first use is the earliest one after restructuring moves paragraphs.

## Terms The Reader Cannot Look Up

A manuscript accumulates terms that no one decided to introduce. Sweep for them once the structure is final and classify each one before rewriting, since the right repair differs by class.

- **Terms the whole paper runs on but never defines.** The most frequent words are the most exposed, since familiarity inside the project hides them. One manuscript indexed every result by `case` and `state`, 29 and 36 uses, and defined neither; the reader had to infer both from context, and the paper never explained why the optical count was 37 while the matched count was 36. Define such terms once where the objects are introduced, and let the definition resolve the arithmetic a reader would otherwise stumble over.
- **One word carrying two unrelated technical senses.** `coverage` meant an area fraction in two sections and the fraction of a signal file that a window spans in a third, and neither sense was defined. Removing all eleven uses was shorter than defining two senses, and every replacement was a term the figures already printed.
- **A term defined and then never used again.** It exists only to be defined. Delete the definition and name the quantity at its single point of use; one such term introduced in an instrumentation section became `a standard deviation`.
- **Labels invented to carry a term that is leaving.** Group names such as `the low-area-fraction group` survive only to hold a departing word. Replace them with the grouping rule, as in `the nine images at vapor area fraction below 0.05`.
- **Compressed nominal coinages.** `split audit`, `convention-limited values`, `experiment-held-out annotations`, `sequence-grouped images`, `onset state`, and `degradation range` each compress a procedure into a noun phrase that appears nowhere in the field's literature. Expand to the procedure itself, as in `the training and holdout images are also checked for shared source frames, by parsing the frame index in each filename`.
- **Abbreviations expanded only in the nomenclature.** A reader meets the body out of order, so expand each one at its first appearance in the body as well. Check the entire list rather than the entries that look unfamiliar, since the omission is usually the one that felt too standard to verify; `RMSE` was expanded nowhere in one manuscript, the nomenclature included. Retire an abbreviation that is used once, since `critical heat flux` is barely longer than `CHF`.
- **A named but unstated value.** `within the prescribed electrical-input tolerance` is a definition gap, not a style choice. Recover the value from the released reduction code, the instrument log, or the data-reduction script, confirm that nothing overrides it, state it in the manuscript, and tell the author which source supplied it. Do not invent the number and do not leave the phrase standing.

Run the sweep as a scripted pass with one assertion per replacement, so that a phrase already altered by an earlier pass fails loudly instead of being skipped in silence, and end the pass with a count of each retired term to confirm that none survived.

## Edits That Move Text

Consolidating limitations, reordering sections, or merging paragraphs breaks references that no spell checker reports.

- Re-resolve every demonstrative after a move. A sentence reading "propagation of that label uncertainty" is correct beside the sentence that introduced the uncertainty and meaningless once that sentence has moved to another section.
- Re-resolve every `Section N`, `Figure N`, and `Table N` after renumbering, in the manuscript, the supplement, and the response. Renumbering is silent: `Section 3.5` continues to resolve to a heading that now covers a different subject.
- Check that removing a section did not remove content a reviewer was promised. After each revision round, confirm that every passage quoted in the response still exists in the manuscript, verbatim.
- Keep a machine check on the package: every figure, table, section, and supplementary item cited must exist, and every cited number must match its source.

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

## Measured Prose Targets

The author's own edit of an AI-drafted manuscript is the calibration, and the measurements below are the check, in place of a judgment about whether a draft reads naturally. That edit cut the body by 24 percent, from 11,619 to 8,811 words, without removing a finding.

| Quantity | Target, measured from the edited draft |
|---|---|
| Mean sentence length | 15.2 words |
| Median sentence length | 15 words |
| 90th-percentile sentence length | 32 words |
| `which` and `that`, per 10,000 words | 75 |
| `rather than`, per 10,000 words | 8 |
| `because`, per 10,000 words | 0 |
| `therefore`, per 10,000 words | 11 |
| Semicolons, per 10,000 words | 1 |
| Inline figure pointers such as `(Fig. 4a)`, per 10,000 words | 12 |
| `respectively`, per 10,000 words | 9 |

The draft rejected as convoluted ran a mean of 17.3 words per sentence, so a draft above roughly 18 is worse than the text already sent back. Measure before and after a style pass, and watch for trading one tic for another: a first pass that fixed sentence length pushed `therefore` from 17.8 to 26.6 per 10,000 words.

**The six moves the edit makes, in order of payoff.**

1. Collapse parallel measurements into one comparative sentence. Four sentences each carrying one number become one sentence carrying all four.
2. Delete the justification sentence that opens a results paragraph, and open on the figure instead.
3. Halve the relative clauses. A `, which ...` that explains becomes its own short sentence.
4. Delete apparatus: sentences defending the experimental design instead of reporting a result, and digressions about which version of an analysis produced a number.
5. Reduce captions to a subject noun phrase, `showing`, and the bare subfigure list.
6. Lead the abstract with the contribution, and state each result as a finding instead of hanging it on `but`, `although`, or `while`.

The edit cuts none of the findings, negative ones included. A data-leakage result, an accuracy collapse, and a failed transfer across surfaces all survive it. `rather than` survives wherever it marks a real technical contrast; its rate fell with the surrounding meta-commentary, and the construction itself was never hunted.

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
