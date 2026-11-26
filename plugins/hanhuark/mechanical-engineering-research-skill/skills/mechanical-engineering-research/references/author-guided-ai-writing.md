# Author-Guided AI Writing

Use this workflow when an author wants AI assistance for a manuscript, proposal, report, review, or response without surrendering the scientific narrative to generic drafting. It standardizes the author decisions that matter most before and after AI generation. It is appropriate for authors who know their work well but have limited formal writing training.

The workflow starts with an author interview. The quality of the result therefore depends on the author's understanding of the work: an author who can state the key message, the claim ceiling, and what each figure establishes gets a draft built on those decisions, and an author who cannot sees exactly which decisions are still open instead of receiving fluent prose that hides them.

This is a writing-quality workflow, not an AI-authorship detector. It does not prove that a text was written by a person or a model, and it does not replace source checking, scientific judgment, or author responsibility.

## Core principle

The purpose of technical writing is to make people understand. Correctness, completeness, and defensibility matter, but they do not justify prose that obscures the point.

Keep the author responsible for **what the document argues** and use AI to help express, organize, inspect, and revise that argument. A useful loop is:

```text
author interview -> decision record and evidence map -> AI drafting one unit at a time -> author decision review -> AI revision -> consistency and reader audit
```

Do not ask AI to infer the paper's contribution, mechanism, or claim boundary from a folder of sources without an author decision point. That shortcut often produces fluent prose with generic importance statements, modifier-heavy labels, and conclusions that do not follow cleanly from the evidence.

Before retaining a sentence, ask whether it helps the reader understand something necessary at that point in the argument. Remove or relocate detail that only repeats, defensively qualifies, or advertises the work. Put methodological detail in methods, limits beside the claim they bound, and secondary robustness checks in an appropriate figure, table, appendix, or supplement. Do not compress several ideas into a single modifier-heavy sentence merely to make the writing look complete.

Apply a sentence-weight check: the main clause should carry most of the sentence's value. A long trailing list of attributes, inputs, or caveats must change the reader's interpretation enough to justify its space. If the first half already conveys the point and the second half only makes it sound more complete, cut the tail or move the necessary detail to a later sentence.

Apply a parallel-detail check: when a sentence lists more than three items, identify the shared technical concept before retaining the inventory. Prefer the one or two concepts that explain the mechanism, deficiency, or decision. Keep the individual items only when they lead to different interpretation, reproduction, boundary assessment, or action. A compressed abstraction must remain specific enough to preserve the scientific point; replacing a list with a vague word such as `context` or `factors` is not an improvement unless the surrounding sentence identifies the relevant kind of context or factor.

## 1. Interview the author

Interview the author before drafting or structurally revising a section, abstract, introduction, results discussion, or full document. Do not construct the author's answers. Use [author-interview-question-bank.md](author-interview-question-bank.md) for the questions and [author-decision-record.md](../assets/templates/author-decision-record.md) for the record.

1. **Intake.** When the user sends the manuscript, figures, notes, and comments in one long message, read all of it as reference and do not draft. Facts are the AI's job; decisions are the author's. Extract the facts the material contains: measured quantities, instruments, sampling rates, sample sizes, what each figure plots, and terms already defined. Ask the author only for decisions and for facts the material does not contain, such as whether a series was replicated. When an earlier version the author approved exists, such as a conference paper or an accepted draft, read it as calibration and quote it in round 1. Asking how the story changed since that version surfaces reframings and competing explanations that the current draft hides.
2. **Rounds.** Ask numbered rounds of 3 to 5 questions, top-down: story; title, abstract, and keywords; introduction paragraphs; methods; each figure with its discussion; limitations and conclusion. A round contains only questions whose prerequisites are already answered. Wait for the author's answers before the next round.
3. **Author first, then challenge.** Story-level questions carry no suggested answer: the key message, the reader, the gap and why it persists, the claim ceiling, and what each figure establishes. After the author answers, compare the answer with the current manuscript. Ask a follow-up for a vague answer, asking only for the missing element (which quantity, compared with what, in which regime), and point out any mismatch with the text. Allow at most two follow-ups per question. Editorial questions, such as keywords, term choice, or section order, carry a recommended answer the author can accept or change.
4. **Question quality.** Each question must require understanding of the work to answer, and its answer must change the text. Quote the sentence or name the figure that prompted it. Do not ask navigation or approval questions such as "Shall we move to Section 2?", "Do you accept these changes?", or "Anything else?"; state the next step in one line at the end of a round.
5. **Weak answers.** When the author answers "I don't know" or remains vague after two follow-ups, record an open decision. The affected text keeps a visible placeholder such as `[OPEN D3: what Fig. 5 establishes]` or a narrower claim. Never fill the answer with plausible AI text. The end-of-interview report lists each open decision with what would resolve it: a reading, an analysis, a measurement, or a discussion with a co-author.
6. **Short form and skip.** A single-paragraph edit receives 2 to 3 questions: the paragraph's takeaway, its evidence, and its claim ceiling, minus any the decision record already answers. Skip the interview when the user says "no interview" or when the record already covers the section.
7. **Analysis requests between rounds.** An answer often reveals that a stated motivation or claim was never analyzed, or the author asks for an analysis, a literature check, or a physically derived value in place of a fitted one. Fix the analysis instead of the wording. Run the analysis between rounds when the data are available, save the script and figure beside the manuscript, and record the result in the fact sheet with its file path. The next round then asks the decisions the result enables. Verify every reference against the source before relying on it, and label any value or formula recalled from memory as unverified until checked.
8. **Wording proposed during the interview.** Load the author's style references before proposing any wording, including agreed wording for the record and draft sentences offered for confirmation. A record entry drafted in a style the author rejects costs a round and erodes trust in the drafts that follow.
9. **Completion.** The interview ends when every question at every level is answered or recorded as open. An answered round confirms the record entries it touched. Ask for explicit confirmation only of entries the AI filled that the author has not yet seen. Start drafting only then.

Keep the decision record in the manuscript folder and update it after every round. It contains unpublished results and author decisions and therefore stays with the manuscript. Record the author's story answers verbatim beside the agreed wording. Later drafting then answers to the author's words, not to an AI paraphrase. Record each terminology decision in the terms table as soon as the author makes it.

For a review, the story round covers the organizing comparison, the maturity of each body of evidence, and the synthesis the review adds. For a proposal, it covers the hypothesis, preliminary evidence, decision rule, and main risk.

## 2. Convert the record into an evidence-backed narrative map

Before prose, make a section map from the decision record that gives every section one reader question, one evidence basis, and one takeaway. For a paper, an introduction normally moves through importance, state of the art, remaining issue, why it persists, present response, and bounded significance. A results section should move through physical questions and figures, not the order in which files were produced.

For each headline claim, record:

- the claim and evidence class: measured, reported, simulated, derived, assumed, inferred, proposed, or validated;
- the figure, table, equation, dataset, calculation, or source that supports it;
- the regime, assumptions, uncertainty, and alternative explanation that bound it; and
- the section where the reader needs it.

Pause for the author to approve the map before full drafting when the document contains a new contribution, consequential conclusion, or contested interpretation. Approval means the author agrees with the scientific story, not that the prose has been polished.

## 3. Draft one unit at a time

Draft only from the decision record and the supplied material. Use the whole manuscript as reference and one unit as the task: a paragraph, or a figure with its discussion. The same comments produce a deeper and more concrete revision at that scale, and the whole manuscript as reference keeps terms, numbers, and stated limits consistent.

- A sentence that depends on an open decision carries its placeholder, for example `[OPEN D3: what Fig. 5 establishes]`.
- After each unit, report what changed, which record entries the draft used, and any new open decision.
- When an author comment on a draft changes a recorded decision, such as the claim ceiling or a figure's takeaway, update the record before the text.
- Start a fresh session for a major section from the record and the manuscript; a long session that has been summarized loses detail.

Useful drafting instructions include:

- Start each paragraph with its central technical purpose, then develop it with evidence, mechanism, comparison, limitation, or implication.
- Explain an equation by its governing balance or process, not by listing its variables.
- Organize literature by mechanism, method, evidence type, or unresolved issue. Use `FirstAuthor et al.` for narrative citations unless the venue requires another style.
- Name unknown information and missing evidence rather than inventing a citation, result, explanation, or qualified-sounding conclusion.
- Use ordinary technical language before introducing a specialized term. Keep a modifier only when it changes the regime, evidence, mechanism, or system.
- Draft from figures and evidence outward. Do not make a method, dataset, or AI model the contribution by itself.

State each limitation once, beside the claim it bounds, and name what the evidence does not separate. Check the limitation against the data before writing it; a default hedge can contradict the evidence, as when a sentence denies an effect that a controlled series in the same paper shows. Keep the claim verb alone, as in "is consistent with", without a trailing clause such as "but is not independent proof of". Follow the defensive-qualification rules in `han-hu-research-style.md`.

Run the prose metrics on every unit draft before showing it, with `scripts/audit_technical_writing.py` on the prose exported as plain text. Compare the mean sentence length and the construction rates with the measured prose targets in `han-hu-research-style.md`, revise until they are close, and report the numbers with the draft.

After the last unit, run a separate consistency pass against the record: terms and symbols, repeated numbers, claim verbs, cross-references, and limitations stated twice. This pass checks; it does not redraft.

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

Run the short-form interview: the takeaway, the evidence source, and the claim ceiling, minus any the record already answers. Draft, run the six reader-recovery questions, and revise only the flagged items.

### Full manuscript, review, or proposal

Run the full interview and keep the decision record. Use the claim-evidence ledger for the claims table when the document has many claims, and conduct at least one separate author decision review before final line editing. Use `research-workflow-and-revision.md` for the broader research workflow and `technical-argument-audit.md` for equations, figures, and claims.

## Decision record at handoff

The decision record is the handoff record. When handing off a draft, make sure it contains:

- the author's story answers and the agreed wording;
- the sources, figures, data, and equations used for each main claim;
- accepted, revised, and evidence-needed review items;
- remaining open decisions and what would resolve each; and
- the version of the skill or workflow used.

This record makes AI assistance auditable without treating the text as a model-authorship problem.
