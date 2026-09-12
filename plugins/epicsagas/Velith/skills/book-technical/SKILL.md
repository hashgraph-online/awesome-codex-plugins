---
name: book-technical
description: "Technical book craft reference: concept gradient, running project, failure-first teaching, code standards, diagrams, exercises, version handling, the technical-book AI tells. Read by all agents on programming, engineering, and data science books."
---

# Technical

The reader of a technical book is trying to become someone who can do the thing. Every chapter must move them closer to doing it themselves, and the surest sign of a book that fails is a reader who can follow along but cannot deviate.

## Structure

Default: **Intro (10-15%) → Foundations (25%) → Practice (30%) → Advanced (20%) → Reference (10%)**. Within that:

- **Running project.** The reader builds one thing across the book. Each chapter adds a capability. By the end they have something that works and that they understand every line of. Books without a running project produce readers who have read about the thing.
- **Concept gradient**: each concept is introduced once, at the first chapter that needs it, with the minimum needed then, and deepened later where it becomes necessary. The outline's dependency DAG enforces this; the architect verifies there are no forward references.
- **Difficulty is monotonic non-decreasing** within a part; the first chapter of a part can step back slightly.
- **Reference material** (API tables, option lists) goes to the back or an appendix, never inside a teaching chapter.

## Failure-first teaching

The single largest gap between AI technical writing and good human technical writing: humans show the thing going wrong.

- Show the naive version first. Run it. Show the actual error message or wrong output.
- Explain why it fails in terms of the mental model, not just the fix.
- Then the correct version. Then what else would have broken it.
- Debugging is a chapter topic, not an afterthought. How would the reader know something is wrong? What would they look at first?
- Performance, security, and edge cases appear where the reader would first hit them, not in a separate "advanced considerations" chapter.

## Code standards

- Every code block has a language tag and, when it is a file, a filename comment on line 1.
- Runnable, or explicitly labeled `# pseudocode`. Imports included. Expected output shown after.
- Lengths: 10-30 lines when introducing; 30-80 when building; 80+ only for a complete listing, and then with the key section explained separately.
- Version pinned in `PRD.md` and stated once in the introduction; not repeated per chapter. Breaking changes and security-relevant versions are called out inline.
- Prefer "save the file" to "click File → Save"; UI paths change, concepts do not.
- The fact-checker runs code blocks where the environment allows. Write code that can be run.
- Diagrams: Mermaid for flow/sequence, ASCII fallback for EPUB readers that do not render Mermaid, tables for comparisons. At most three per chapter.

## Chapter design

- **Hook**: a concrete task or a concrete failure the reader recognizes
- **Concept**: minimum needed now, linked to what they already know from earlier chapters
- **Build**: add to the running project; show the code, run it, show the output
- **Break**: what goes wrong when the reader deviates; show it
- **Explain**: the model behind the fix
- **Exercise**: one thing the reader does without the book's hand (three levels: guided, hinted, goal-only)
- **Exit**: what the next capability is and why the current build needs it. Not a summary.

## Technical-book tells

- Every chapter starts with "In this chapter, you will learn."
- Code that always works on the first try.
- Explanations that restate the code line by line without adding a model.
- "It is important to note that" before every caveat.
- Bullet lists of "best practices" with no reasoning.
- Diagrams of boxes and arrows that add nothing to the prose.
- Exercises that repeat the chapter's example with a variable renamed.
- A "conclusion" section per chapter.
- Uniform confidence about tradeoffs that are genuinely contested.
- Analogies for concepts that are simpler than the analogy.

## Language notes

- Korean technical books: 개발자 독자는 영문 용어 병기를 기대한다 (예: 컨텍스트 윈도(context window)). 첫 등장 시 병기, 이후 한글 또는 원어 중 STYLE.md에서 정한 쪽. 코드 주석은 영문 또는 한글 중 하나로 통일. 경어체(합니다체) 또는 평서체(한다체) 하나로 고정.
- English: second person, present tense, active voice. "You" is the reader; "we" only if the fingerprint allows.
- Japanese: です・ます体 for tutorials; だ・である体 for reference sections; do not mix within a chapter.

## Validation (architect scoring for technical)

DAG has no cycles and no forward references; running project defined and advanced in every practice chapter; failure shown in every build chapter; difficulty monotonic within parts; exercise per chapter with three levels; versions pinned; reference material segregated; diagrams ≤ 3/chapter and each does work the prose cannot.

## Visuals

Diagrams are code (Mermaid, D2, Graphviz, SVG), versioned in `visuals/figures/src/`, rendered to SVG for EPUB and PNG for print, with a single theme file for fonts and color roles. Architecture, sequence, state, and data-flow diagrams use the same node and edge grammar throughout (art bible figure system). Screenshots are real and cropped to the relevant region, annotated in SVG overlays, and dated in the caption if the UI may change. Terminal output is a code block, never an image. Charts from measured data with units. ≤ 3 figures per chapter; each does work the prose cannot. `figure-engineer` produces; `fact-checker` verifies every label against the text and the running project's actual state.
