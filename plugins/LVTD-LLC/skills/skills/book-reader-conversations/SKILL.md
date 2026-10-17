---
name: book-reader-conversations
description: Plan and synthesize pre-draft reader conversations for useful nonfiction books, including listening interviews, teaching calls, reader-language capture, promise validation, scope refinement, and TOC testing. Use when validating a practical book idea, finding target readers, preparing interview prompts, testing a table of contents, or turning reader conversations into book decisions.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Book Reader Conversations
  category: Writing
  tags: writing,books,nonfiction,reader-research,interviews
---

# Book Reader Conversations

## Core Lens

Reader conversations are product discovery for useful nonfiction. The goal is not to ask whether people like a book idea. The goal is to understand the reader's real situation, language, failed attempts, urgency, objections, and ability to receive the value the book intends to deliver.

Use this skill before or during drafting to:

- Validate a book promise before writing too much prose.
- Escape the author's curse of knowledge.
- Find the strongest reader profile and use case.
- Test a takeaway-first TOC by teaching from it.
- Turn conversations into scope, structure, examples, and beta-reader leads.

## Reference Routing

| Need | Read |
|------|------|
| Core model and terminology | `references/core/knowledge.md` |
| Interview and synthesis rules | `references/core/rules.md` |
| Example prompts and synthesis patterns | `references/core/examples.md` |
| Fast setup and review checklist | `references/core/checklist.md` |
| Run a conversation round | `workflows/run-reader-conversations.md` |

## Workflow

### 1. Define The Learning Goal

Choose one primary question for this round:

- Is the reader problem real and urgent?
- Which reader profile cares most?
- What does the reader already know or believe?
- Which promise is easiest to understand and recommend?
- Does the TOC sequence help the reader receive value?

Do not mix early listening with pitching unless the user is explicitly running a teaching conversation.

### 2. Recruit Readers Who Match The Hypothesis

Start with friendly first contacts, existing readers, community members, customers, students, or people already trying to solve the problem.

Avoid cold outreach unless no warm path exists. If nobody relevant will talk, treat that as a scope or access problem rather than a scheduling problem.

### 3. Run The Right Conversation Type

Use two modes:

- **Listening conversation**: explore lived experience, language, urgency, alternatives, and obstacles.
- **Teaching conversation**: help the reader through one slice of the TOC and watch where they get value, confusion, skepticism, or missing steps.

### 4. Synthesize Into Book Decisions

After each batch, update:

- Reader profile and exclusions.
- Promise wording and reader language.
- TOC order, section titles, and missing steps.
- Proof, examples, objections, and caveats.
- Potential beta readers, testimonials, or launch allies.

### 5. Decide The Next Test

Recommend one of:

- More listening with a sharper reader segment.
- Teaching a high-value chapter or section.
- Revising the TOC with `book-toc-lab`.
- Drafting enough for `reader-experience-edit` or `beta-reader-feedback`.

## Output Format

When helping with reader conversations, return:

1. Learning goal and target reader hypothesis.
2. Recruiting list or outreach plan.
3. Conversation guide with prompts.
4. Note-taking schema.
5. Synthesis table: signal, evidence, implication, book decision.
6. Next test or manuscript action.

## Quality Bar

Keep the conversation about the reader's life before the author's idea. Prefer observed behavior, concrete stories, and exact reader language over opinions, compliments, or predictions.
