---
name: beta-reader-feedback
description: Plan beta reading rounds for practical nonfiction and turn reader comments, abandonment, confusion, skepticism, and negative feedback into manuscript revisions. Use when recruiting beta readers, preparing reader instructions, synthesizing feedback, deciding whether a book is ready, or improving a draft from real reader data.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Beta Reader Feedback
  category: Writing
  tags: writing,books,nonfiction,beta-readers,feedback
---

# Beta Reader Feedback

## Core Lens

Beta reading is product testing for a useful nonfiction manuscript. The goal is not praise, proofreading, or opinion collection. The goal is to discover whether readers want the promise, receive the value, stay engaged, and know what to do next.

Use this skill to:

- Plan beta reader rounds.
- Recruit the right readers.
- Write reader instructions.
- Classify and synthesize comments.
- Detect hidden boredom from abandonment.
- Decide what to revise next.
- Decide when the manuscript is ready for polishing.

## Reference Routing

| Need | Read |
|------|------|
| Core beta-reading model and terminology | `references/core/knowledge.md` |
| Operating rules and decision criteria | `references/core/rules.md` |
| Example instructions, feedback classes, and synthesis patterns | `references/core/examples.md` |
| Quick checklist for setup and review | `references/core/checklist.md` |
| Run a beta iteration | `workflows/run-beta-iteration.md` |
| Synthesize comments into revision decisions | `workflows/synthesize-feedback.md` |

## Workflow

### 1. Confirm Beta-Readiness

Start beta reading after the draft is coherent enough for motivated readers, but before it has been polished so heavily that major changes feel costly.

If the draft is still a vague TOC, use `book-toc-lab`. If it needs structural pacing work first, use `reader-experience-edit`.

### 2. Choose The Reader Batch

For each iteration, define:

- Target reader profile.
- Desired number of deeply engaged readers.
- Invitation list, usually larger than the desired reader count.
- Any influential readers to save for a later, stronger draft.

### 3. Prepare The Feedback Surface

Use a tool that supports live comments and engagement visibility.

- Prefer cloud-hosted commenting.
- Do not email PDFs around as the main workflow.
- Tell readers what feedback matters now.
- Ask for confusion, skepticism, missing information, boredom, value, and applicability.

### 4. Classify Feedback

Group feedback by signal:

- Evidence of value.
- Confusion or missing information.
- Skepticism or weak proof.
- Factual issues, overgeneralization, or oversimplification.
- Unnecessary drama or distracting sentences.
- Boredom, abandonment, or comment drop-off.
- Application problems after reading.

### 5. Revise By Signal Strength

Prioritize changes that unblock more readers.

- Treat abandonment as data.
- Treat negative feedback as a lens, not a command.
- Do not argue with readers in the document.
- Follow up when the book is supposed to change behavior after reading.

## Output Format

When helping with beta feedback, return:

1. Beta-readiness or setup diagnosis.
2. Reader recruitment and instruction plan.
3. Feedback taxonomy or synthesis table.
4. Ordered revision priorities.
5. Finish criteria: what evidence would make the manuscript ready for polish.

## Quality Bar

Separate reader signals from author defensiveness. Do not merely summarize comments. Convert them into revision decisions, open questions, and next beta-round tests.
