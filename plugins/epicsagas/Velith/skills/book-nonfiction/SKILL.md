---
name: book-nonfiction
description: "Nonfiction craft reference: argument architecture, evidence discipline, narrative in nonfiction, chapter design, the nonfiction-specific AI tells. Read by all agents on nonfiction, memoir, business, self-help, essay, and narrative nonfiction projects."
---

# Nonfiction

The reader of nonfiction wants one of three things: to understand something they did not, to be able to do something they could not, or to have lived through something they never will. Decide which this book delivers (or which mix) in `PRD.md`, and let that decide the structure. A how-to book with the structure of a memoir fails both.

## Structure options

- **Problem → Principles → Practice → Advanced** — the default for practical nonfiction. Reader arrives with a pain, leaves with a method.
- **Narrative spine with argument chapters** — a story runs through the book (a case, a person, a year) and argument chapters hang off it. Best for big-idea books.
- **Question-driven** — each chapter is a question the previous chapter raised. Best for explanatory nonfiction.
- **Chronological** — history, memoir, biography. Risk: "and then" pacing; fix by organizing around turning points, not dates.
- **Thematic essays** — a collection unified by voice and subject. Each essay stands alone; the order builds.
- **Framework** — one model, one chapter per component. Risk: framework inflation; only if the framework is genuinely the book's contribution.

Whatever the shape: the introduction earns the reader's next hour by naming the pain and the promise; chapter 1 delivers something usable; the middle escalates from simple to hard, not from topic to topic; the ending returns to the promise and shows it kept.

## Argument

Every chapter has one claim the reader could disagree with. If they cannot disagree, it is not a claim, it is a topic.

- **Claim → evidence → warrant → objection → answer.** The objection is the strongest one a smart skeptic would raise, not a straw one.
- **Confidence signaling.** Mark what is settled, what is contested, and what is the author's speculation. Uniform confidence is a tell and a liability.
- **One recurring example** carried across chapters beats a new example every paragraph. The reader builds a mental model of it.
- **Abstraction ladder.** Every abstract paragraph is followed by a concrete one. Never two abstractions in a row.
- **Cut the preview and the recap.** Chapter titles and transitions do that work.

## Evidence discipline

This is where AI nonfiction fails and where reputations end.

- **Every number, study, quote, and named person traces to `sources/INDEX.md` or a URL the fact-checker verified.** No source, no claim. "Studies show" without a study is deleted, not softened.
- **Hierarchy**: primary data and the author's own experience > peer-reviewed research > reputable reporting > expert opinion > anecdote. Core claims need the top two. Anecdote illustrates; it never proves.
- **Quotes are exact or paraphrased.** A fabricated quote is a Critical defect even if it is plausible.
- **Dates, names, titles, affiliations** are checked. Getting a person's job title wrong costs the reader's trust for the rest of the book.
- **Case studies**: minimum three, with names or explicit anonymization, with what did not work as well as what did.
- **Counter-evidence** is presented, not hidden.

The fact-checker builds a claim ledger from the draft. Write so the ledger is easy to build: cite inline with source IDs during drafting (`[S03]`); the copy edit converts to the house citation style.

## Narrative in nonfiction

Story is the delivery mechanism, not decoration.

- Open chapters in a scene or with a specific person in a specific moment when possible. Not a rhetorical question, not a definition, not a statistic.
- Real people get the same treatment as fiction characters: they want things, they are wrong about themselves, they speak in their own register. If the author interviewed them, use the transcript's actual phrasing.
- Memoir: the narrator then vs. the narrator now. The gap between them is the book. Reflection belongs to the narrator-now and is rationed.
- The reader's own story: second person ("you") is powerful in practical nonfiction and grating in explanatory nonfiction. Follow the voice fingerprint.

## Chapter design

- **Hook** (scene, specific case, or a claim that sounds wrong)
- **Stakes** — why this matters to this reader, concretely
- **Body** — the claim, its evidence, its objection, the recurring example advanced
- **Application** — what the reader does with it (practical) or what it changes in their understanding (explanatory)
- **Exit** — a line that opens the next chapter's question. Not a summary.

Callouts, sidebars, and exercises: at most two per chapter, and only if the voice fingerprint allows them. Bullet lists only for genuinely parallel, scannable items. Most lists should be prose.

## Nonfiction-specific tells

- Chapter opens with a definition or a dictionary quote.
- "In this chapter" / "as we saw in chapter 3."
- A named framework with an acronym per chapter.
- Every example is a famous company or a famous person.
- "Research shows," "experts agree," "studies have found" without a citation.
- Every paragraph ends on a lesson.
- Uniform confident register from first page to last.
- Three-item lists everywhere.
- Action steps that restate the chapter as imperatives.
- A conclusion chapter that summarizes each chapter.

## Length and format notes

- English: 50-75K words trade nonfiction; 30-45K business/short-form; memoir 70-90K.
- Korean: 실용서 80,000-120,000자; 에세이 60,000-90,000자 (공백 제외). 각주는 출판 단계에서 미주 또는 각주로 변환; 초안은 인라인 `[S03]`.
- Endnotes vs. footnotes vs. inline is decided in `STYLE.md`; drafts use source IDs regardless.

## Validation (architect scoring for nonfiction)

Reader promise stated and each chapter's purpose maps to it; one claim per chapter; evidence map covers every core claim with primary or research-grade sources; difficulty escalates; recurring example threads through; no two chapters with the same purpose; introduction under 8% of the book; conclusion under 5%.

## Visuals

Figures are part of the argument. Plan them in the outline: each figure has a purpose sentence and a data source. Charts read data files in `sources/`, never hand-typed numbers; axis labels carry units; no 3D, no pie beyond two categories; direct labels; grayscale-safe. Concept diagrams ≤ 9 elements with one consistent grammar across the book (the art bible's figure system). Photos: author's own or licensed, recorded with license and attribution; no generated "photos" of real events or people. One recurring visual model that develops across chapters beats a new diagram per chapter. All through `/book-visuals`; `figure-engineer` renders, `fact-checker` verifies labels and data.
