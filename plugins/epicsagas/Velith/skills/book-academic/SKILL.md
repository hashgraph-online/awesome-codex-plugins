---
name: book-academic
description: "Academic writing craft reference: IMRAD and discipline structures, literature review, argument chains, citation integrity, academic register in en/ko/ja, and academic-writing AI tells. Read by all agents on theses, dissertations, monographs, and research reports."
---

# Academic

The reader is a peer or an examiner. They will check the citations, and they will notice when the literature review summarizes instead of argues. Academic AI text fails by being fluent about things it has not read.

## Structure by discipline

- **Sciences**: IMRAD (Introduction → Methods → Results → Discussion), plus Abstract, References, Appendices.
- **Social sciences**: Introduction → Literature review → Theoretical framework → Methods → Findings → Discussion → Conclusion.
- **Humanities**: Thesis → evidence chapters (each an argument, not a topic) → synthesis → conclusion.
- **Thesis/dissertation**: as above with committee and program requirements from `PRD.md` overriding defaults (chapter count, word limits, citation style, formatting).
- **Monograph**: like humanities but with a stronger narrative spine and less methodological apparatus.

## Literature review

Organize by theme and argument, never chronologically and never author-by-author. Establish the field → identify the gap → position this work. For each source: claim, method, limitation, relevance to this work. Build a synthesis matrix (themes × sources) in `sources/INDEX.md` before drafting. The review argues that the gap exists; it does not list what people have said.

## Argument

Toulmin: claim → evidence → warrant → backing → qualifier → rebuttal. Every chapter thesis supports the central thesis, and the chapter's opening states its claim, position, and scope. Paragraph: topic sentence (claim) → evidence and analysis → link. Hedging is calibrated, not stacked: "may suggest" is fine; "it could perhaps be argued that it may" is not.

## Citation integrity

- Every citation refers to a real work the author has (or the fact-checker has verified exists) with the correct authors, year, title, venue, and page range. **A fabricated or misattributed citation is a Critical defect; the fact-checker removes it.**
- Drafts cite inline with source IDs (`[S12, p. 45]`); copy edit converts to the house style (APA 7, MLA 9, Chicago 17, IEEE, or the program's own).
- Direct quotes ≤ 40 words inline, longer as block quotes, always with page numbers.
- Paraphrase must change structure, not only vocabulary.
- Citation density: heavy in the review, light in methods and results, moderate in discussion.
- Self-citation disclosed; retracted works not cited; preprints marked.

## Register

- English: third person or disciplinary convention; present tense for established knowledge and for discussing texts, past tense for what was done; defined terms used consistently; no rhetorical questions; no contractions.
- Korean (학술 문체): 한다체 fixed; 본고/본 연구 for self-reference; 무생물 주어 restrained (연구 결과 ~로 나타났다 rather than 결과는 보여준다); 한자어 register consistent with the field; 각주 vs 미주 per program; 인용 표기 (저자, 연도) or 각주 per style.
- Japanese: だ・である体; 本稿/本研究; 引用 per discipline.

## Figures, tables, cross-references

Numbered per chapter (Figure 3.1). Captions below figures, above tables. Every figure and table referenced in the text before it appears. Self-contained. Cross-references by section number (Section 4.2), never "above" or "below."

## Academic-writing tells

- A literature review that lists studies in order.
- "Scholars have long debated" without naming any.
- Citations clustered at the end of a paragraph supporting a claim none of them makes.
- Perfectly balanced discussion sections that find every finding "interesting."
- Limitations section that lists generic limitations.
- Abstract that describes the paper instead of stating its findings.
- Hedging on findings and confidence on speculation.
- Keyword-stuffed sentences that restate the title.

## Abstract formula

Context (1-2 sentences) → gap (1) → purpose (1) → method (1-2) → key finding with a number (1-2) → significance (1). 150-300 words. Written last.

## Validation (architect scoring for academic)

Central thesis stated; each chapter's thesis supports it; review organized by theme with a stated gap; methods sufficient to replicate; every core claim in the results has evidence in the results; discussion addresses the strongest alternative explanation; synthesis matrix exists; citation style declared; program constraints in `PRD.md` satisfied.

## Visuals

Figures and tables follow the discipline's conventions and the program's format. Every figure is code-rendered from data in `sources/` with the exact numbers in the results; captions are self-contained; numbering per chapter; referenced in the text before they appear. No decorative images. Conceptual frameworks as diagrams ≤ 9 elements with a consistent grammar. `figure-engineer` produces; `fact-checker` reconciles every plotted value with the data file.
