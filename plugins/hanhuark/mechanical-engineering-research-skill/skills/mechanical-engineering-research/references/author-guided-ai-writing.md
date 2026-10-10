# Author-Guided AI Writing

Use this workflow when an author wants AI assistance for a manuscript, proposal, report, review, or response without surrendering the scientific narrative to generic drafting. It standardizes the author decisions that matter most before and after AI generation. It is appropriate for authors who know their work well but have limited formal writing training.

This is a writing-quality workflow, not an AI-authorship detector. It does not prove that a text was written by a person or a model, and it does not replace source checking, scientific judgment, or author responsibility.

## Core principle

The purpose of technical writing is to make people understand. Correctness, completeness, and defensibility matter, but they do not justify prose that obscures the point.

Keep the author responsible for **what the document argues** and use AI to help express, organize, inspect, and revise that argument. A useful loop is:

```text
author story brief -> evidence map -> AI structural draft -> author decision review -> AI revision -> technical and reader audit
```

Do not ask AI to infer the paper's contribution, mechanism, or claim boundary from a folder of sources without an author decision point. That shortcut often produces fluent prose with generic importance statements, modifier-heavy labels, and conclusions that do not follow cleanly from the evidence.

Before retaining a sentence, ask whether it helps the reader understand something necessary at that point in the argument. Remove or relocate detail that only repeats, defensively qualifies, or advertises the work. Put methodological detail in methods, limits beside the claim they bound, and secondary robustness checks in an appropriate figure, table, appendix, or supplement. Do not compress several ideas into a single modifier-heavy sentence merely to make the writing look complete.

Apply a sentence-weight check: the main clause should carry most of the sentence's value. A long trailing list of attributes, inputs, or caveats must change the reader's interpretation enough to justify its space. If the first half already conveys the point and the second half only makes it sound more complete, cut the tail or move the necessary detail to a later sentence.

## 1. Build a short author story brief

Before drafting a substantial section, record the following in plain technical language. The author may answer in bullets. Unknown items stay marked as unknown rather than being filled with plausible AI text.

| Field | Author decision |
| --- | --- |
| Reader and decision | Who needs this document and what should they understand, decide, or do after reading it? |
| Technical problem | What system, phenomenon, or decision is difficult, and why does it matter? |
| Specific gap | What is not measured, explained, predicted, compared, or designed adequately? |
| Why the gap persists | What coupled physics, missing measurement, incompatible data, cost, scale mismatch, or modeling limitation causes it? |
| Present response | What is measured, modeled, developed, or analyzed here? |
| Main evidence | Which figures, datasets, equations, calculations, and sources carry the main claims? |
| Claim ceiling | What can the work establish, and what remains screening-level, inferred, unmeasured, or outside scope? |
| Reader takeaway | State the one-sentence conclusion that the evidence should allow a reader to retain. |

For a review, replace the present response with the organizing comparison and the new synthesis or outlook. For a proposal, replace the main conclusion with the hypothesis, evidence plan, and decision rule.

The brief should fit on one page. A long brief is often a sign that the document contains more than one story and should be divided.

## 2. Convert the brief into an evidence-backed narrative map

Before prose, make a section map that gives every section one reader question, one evidence basis, and one takeaway. For a paper, an introduction normally moves through importance, state of the art, remaining issue, why it persists, present response, and bounded significance. A results section should move through physical questions and figures, not the order in which files were produced.

For each headline claim, record:

- the claim and evidence class: measured, reported, simulated, derived, assumed, inferred, proposed, or validated;
- the figure, table, equation, dataset, calculation, or source that supports it;
- the regime, assumptions, uncertainty, and alternative explanation that bound it; and
- the section where the reader needs it.

Pause for the author to approve the map before full drafting when the document contains a new contribution, consequential conclusion, or contested interpretation. Approval means the author agrees with the scientific story, not that the prose has been polished.

## 3. Give AI a bounded drafting job

Supply the story brief, narrative map, source list, and target section. Ask AI to draft only from those inputs and to preserve explicit evidence labels and claim limits.

Useful drafting instructions include:

- Start each paragraph with its central technical purpose, then develop it with evidence, mechanism, comparison, limitation, or implication.
- Explain an equation by its governing balance or process, not by listing its variables.
- Organize literature by mechanism, method, evidence type, or unresolved issue. Use `FirstAuthor et al.` for narrative citations unless the venue requires another style.
- Name unknown information and missing evidence rather than inventing a citation, result, explanation, or qualified-sounding conclusion.
- Use ordinary technical language before introducing a specialized term. Keep a modifier only when it changes the regime, evidence, mechanism, or system.
- Draft from figures and evidence outward. Do not make a method, dataset, or AI model the contribution by itself.

Request a compact companion audit with the draft: unresolved evidence, claims that need author confirmation, and places where the draft could not explain the physical mechanism from the supplied material.

## 4. Use an author decision review before line editing

The author does not need to rewrite every sentence. Instead, first inspect the draft at the argument level using the following reader-recovery questions:

1. Can I identify the technical problem, specific gap, and present response after reading the title, abstract, introduction, and conclusion?
2. Does every major conclusion point to a measurement, calculation, figure, equation, or source that actually supports it?
3. Does the text explain the governing physics, or does it merely name variables, methods, and model components?
4. Are the assumptions and scope limits placed beside the claims they bound?
5. Does each literature group lead to a limitation, contradiction, or need that motivates the next part of the story?
6. Would a knowledgeable colleague understand the main point without unpacking a dense title, coined label, or chain of modifiers?

Mark each item as **accept**, **revise**, or **evidence needed**. Comments should identify the scientific issue and desired reader takeaway, rather than prescribing a replacement sentence when the structure is the problem.

## 5. Revise in the right order

Resolve `evidence needed` items first. Then revise argument order, paragraph purpose, and technical explanations. Only afterward run the sentence-level clarity and anti-formulaic pass.

Use the following hierarchy:

1. scientific validity and claim support;
2. narrative logic and reader recovery;
3. mechanism, equation, figure, and literature explanation;
4. citation, terminology, and scope integrity;
5. economy, style, and formatting.

Do not make prose sound cautious merely because evidence is incomplete. State the bounded conclusion directly and name the exact missing measurement, validation, or analysis.

## 6. Choose the appropriate depth

### Short section or response

Use a three-item brief: reader takeaway, evidence source, and claim ceiling. Draft, run the six reader-recovery questions, and revise only the flagged items.

### Full manuscript, review, or proposal

Use the complete brief and narrative map. Keep a claim-evidence ledger and conduct at least one separate author decision review before final line editing. Use `research-workflow-and-revision.md` for the broader research workflow and `technical-argument-audit.md` for equations, figures, and claims.

## Completion record

When handing off a draft, retain a short record containing:

- author-approved story brief and narrative map;
- sources, figures, data, and equations used for each main claim;
- accepted, revised, and evidence-needed review items;
- remaining evidence needs and unresolved author decisions; and
- the version of the skill or workflow used.

This record makes AI assistance auditable without treating the text as a model-authorship problem.
