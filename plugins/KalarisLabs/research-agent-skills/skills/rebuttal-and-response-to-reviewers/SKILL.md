---
name: rebuttal-and-response-to-reviewers
description: Plan and write responses to peer review, including journal "response to reviewers" letters for revise-and-resubmit, conference rebuttals under strict length limits (OpenReview/ICLR, NeurIPS, ICML, ACL ARR, CVPR), author responses to meta-reviews, and appeals. Use when a user receives reviews, must triage reviewer comments, draft point-by-point replies, decide what new experiments to run, disagree respectfully with a reviewer, or track manuscript changes for a revision. For authors answering reviews of their own manuscript; to write a review of someone else's paper, use peer-review instead.
license: MIT
compatibility: No runtime dependencies.
metadata:
  version: "1.0"
  category: research-writing
  maintainer: Kalaris Labs
  author: Kalaris Labs (Sayan Chowdhury)
  tags: peer review, rebuttal, response to reviewers, revise and resubmit, OpenReview, author response
---

# Responding to Reviewers

The audience of a response is the **editor or area chair**, who must decide
quickly whether concerns were addressed. Make every reply easy to verify:
quote the concern, answer it directly, show the change with a location.

## Step 1: Triage (before writing anything)

Split every review into atomic comments and classify each in a table:

| ID | Reviewer | Comment (short) | Type | Effort | Plan |
|---|---|---|---|---|---|
| R1.1 | 1 | Missing baseline X | Experiment | High | Run X on 2 datasets |
| R2.3 | 2 | Claim in §4 overstated | Wording | Low | Soften + add limitation |

Types: *misunderstanding* (the text was unclear), *missing analysis/experiment*,
*wording/presentation*, *disagreement on substance*, *out of scope*, *factual error by reviewer*.

Then:
- Identify the **2-3 concerns that drive the scores** (often shared across reviewers). These get
  the most effort and appear first in a conference rebuttal.
- Decide what is feasible in the revision window. Never promise experiments you will not run.
- Note conflicts between reviewers so the editor can adjudicate.

## Step 2: Do the work, then write

Run the experiments and edit the manuscript **before** drafting replies, so every reply can
point to a concrete change. Keep a change log with section/page/line numbers.

## Step 3: Reply patterns

**Journal response letter** (no strict length):

```text
Reviewer 1, Comment 1: "<quote or faithful summary of the concern>"

Response: We thank the reviewer for ... [direct answer in the first sentence].
We have [action]. The new results (Table 3, p. 7, lines 210-224) show ...

Change in manuscript: "<quoted new/revised text>" (Section 4.2, p. 7)
```

Best practices:
- Answer in the first sentence ("Yes, we have added...", "We agree and have...", "We respectfully disagree because...").
- Thanks once per reviewer, not before every comment.
- Quote revised text so the reviewer need not hunt for it. Provide a tracked-changes/diff version if the journal allows.
- Number comments (R1.1, R1.2 ...) and cross-reference instead of repeating ("see our response to R2.1").

**Disagreeing** (it is allowed and expected when justified):
1. Acknowledge the underlying concern ("We understand the concern that ...").
2. Give evidence: data, citations, a small additional analysis, or a precise explanation.
3. Make a concession where honest: a clarification in the text or a stated limitation.
Never be sarcastic, never say the reviewer "failed to understand". Rewrite the text so the next reader won't.

**Conference rebuttal** (hard limits: characters/words per reviewer or one page; check the venue):
- Lead with a short **general response** covering shared concerns and new results.
- Then per reviewer, only the comments that affect the decision, 2-5 sentences each.
- Put new numbers in compact tables. State exactly what will change in the camera-ready.
- Correct factual misreadings politely with pointers ("Section 3.2, Eq. 4 defines ...").
- Respect the venue's rules on new experiments, links and supplementary material.
  Many prohibit external links or new PDFs during rebuttal.
- On OpenReview discussions: reply promptly and concisely, and summarize the resolved points for the AC near the end.

## Step 4: Cover note to the editor (journals)

Summarize the main changes in 3-6 bullets, flag any reviewer disagreements you could not
resolve and why, and confirm all co-authors approved the revision.

## Quality checklist

- Every comment has a response. Count them against the triage table.
- Every "we have added/changed" is actually in the manuscript at the cited location.
- New numbers match between response, manuscript, tables and abstract.
- Tone: professional, specific, never defensive. Read it as the reviewer would.
- No new claims beyond what the revised evidence supports.
- Length within the venue limit (count it).

## Related skills

`peer-review` (reviewing others' work: useful to anticipate criticism), `scientific-writing`,
`ml-paper-writing`, `scientific-critical-thinking`, `statistical-analysis`.
