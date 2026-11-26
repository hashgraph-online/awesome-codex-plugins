# Author Interview Question Bank

Use this bank with the interview protocol in `author-guided-ai-writing.md`. It is a starting set, not a script. Reword each question around the actual document and quote the sentence or name the figure that prompted it. Skip a factual question when the supplied material already answers it; always ask the story questions, because their answers are author decisions rather than facts.

## Completeness test

A complete answer is specific, comparative, bounded, and traceable:

- **specific:** it names a quantity, system, and regime;
- **comparative:** it states the comparison (baseline, prior method, other condition, or theory);
- **bounded:** it uses a claim verb that matches the evidence (`demonstrates`, `indicates`, `is consistent with`) and says what the work does not establish;
- **traceable:** it points to a figure, table, equation, dataset, or source.

A follow-up asks only for the missing element. Allow at most two follow-ups per question; then record the question as an open decision.

| Author answer | Missing element | Follow-up |
| --- | --- | --- |
| "To better understand boiling." | specific, comparative | Which quantity, on which surface and fluid, compared with what? |
| "A more in-depth and quantitative analysis of X." | specific | The answer names the activity, not the finding. What did the analysis show about X, and in which direction? |
| "H decreases with temperature," when lower H means stronger hysteresis | specific | Which way does the effect run? A metric whose direction reads backwards is an editorial question: recommend a definition that rises with the effect. |
| "The coating improves heat transfer." | bounded, traceable | Improves which coefficient, by how much, in which heat-flux range, and in which figure? |
| "Fig. 4 shows the mechanism." | bounded | What does Fig. 4 show directly, and which part of the mechanism is inferred? |
| "The model is accurate." | comparative, traceable | Accurate against which data, by which error metric, and on data held out from training? |

## Round 1: Story

Ask these first, with no suggested answer. Later rounds depend on them.

1. After reading this paper, what will a reader know that they could not know before? Answer in one sentence.
2. Who is the reader, and what will they do differently after reading it?
3. What exactly is missing (a measurement, an explanation, a prediction, a design rule), and what barrier kept it missing: coupled physics, measurement access, timescale, scale, or cost?
4. What is the strongest claim your evidence supports, and what does it not establish?
5. Which figure, and which subfigure, carries that claim?

Reconcile the answers with the current title, abstract, and conclusion. Point out any mismatch, for example an abstract that claims a mechanism when the answer to question 4 claims an association. When an earlier version the author approved exists, quote its key message in question 1 and ask what the new paper adds; the answer often reveals a reframing or a competing explanation, such as a mechanism the earlier version proposed that the new evidence places downstream of another variable.

For a fitted constant that carries the main claim, also ask whether the author wants a physical meaning for it. If so, propose candidates from the literature, verify each source, test each candidate with the constant fixed, and report the fit of each, including the candidates that fail.

## Round 2: Title, abstract, keywords

- **Title:** Which term for the phenomenon must appear? Which modifiers can go? Does the title promise more than the answer to question 4?
- **Abstract:** For each current sentence, what is its job: problem, gap, approach, finding, or limit? Which one or two numbers must a reader retain?
- **Limiting sentence:** What does the work not establish? Ask the author to draft this sentence first; it constrains every sentence before it.
- **Keywords (editorial):** Recommend terms a researcher in the field would search for that are not already in the title, and let the author accept or change them.

## Introduction

Work in rounds of 3 to 5 paragraphs.

- What single sentence must the reader take away from this paragraph?
- Which citations support that sentence, and which of their limitations leads into the next paragraph?
- What physical limit motivates the work? Use the answer to open on the phenomenon rather than on the application market.
- Why has the gap persisted? Ask only if round 1 did not settle it.

## Methods

- Which variables are controlled, and which instruments set or measure them? Everything else is a candidate for compression.
- What are the uncertainty and the sampling or acquisition rate of the measurement behind the main claim?
- Which records are missing (timestamps, raw traces, calibration files), and which reported quantities does each gap degrade?
- Was the series replicated? If not, say so where the result is reported.

## Each figure

Use one round per figure, with its discussion paragraph.

- What question does this figure answer?
- What is the observation, in one sentence that includes the number that matters?
- What explains it? What alternative explanation exists, and is the alternative excluded or only made less likely?
- What does this figure not show?
- For a model-derived figure: what are the model's failure modes, are the displayed confidence values model scores or measurement uncertainties, and is there a held-out set?

## Limitations and conclusion

- Which limitation most changes how the main result should be read? Quantify it.
- What measurement or analysis would remove it?
- What are the two or three conclusions, and which claim verb does each carry? Reconcile them with round 1.

## Other document types

- **Proposal:** replace round 1 with the hypothesis, the preliminary evidence and its evidence class, the decision rule that would confirm or reject the hypothesis, and the main risk with its fallback.
- **Review article:** replace round 1 with the organizing comparison, the maturity of each body of evidence (established, emerging, proposed), and the synthesis the review adds beyond the sources.
- **Response to reviewers:** for each comment, ask what the reviewer needs to see changed, whether the change is to the analysis or only to the wording, and what new evidence, if any, the response can cite.
