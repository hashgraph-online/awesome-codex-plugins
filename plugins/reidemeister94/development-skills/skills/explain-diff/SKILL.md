---
name: explain-diff
description: "Explain a diff, branch, PR, patch, or review packet; use after Full-path verification when the change teaches a useful business or technical concept."
argument-hint: "[--visual] [scope]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Write, AskUserQuestion
---

# Explain diff

Transfer ownership of a change. Manual mode is repository-read-only; `--visual` may write only to the system temp directory.

## Establish the evidence

Parse `--visual`; the rest is a working tree, branch, range, PR, patch, or packet. Default to the current worktree. Use the available request, plan, chronicle, verification, and details about what was not checked. Do not require a standard packet.

In Full, require the request, plan or chronicle, diff, fresh Verify results, and details about what was not checked. Otherwise inspect read-only.

State verification status. With absent or stale evidence, label **Unverified change** and separate code facts from unproved behavior.

For `--visual`, read [visual mode](references/visual-mode.md). At the automatic Full checkpoint, name the dynamic concept a visual would clarify and ask **Continue in chat** or **Create visual**; only the latter activates it.

## Teach the change

Assume no project knowledge. Present only what the change needs:

1. the minimum background and vocabulary needed;
2. the intuition and functional result;
3. concrete examples or sanitized toy data;
4. a guided diff ordered by concept, not file order;
5. decisions, trade-offs, failure modes, and evidence limits;
6. the comprehension dialogue below.

Use a small diagram only when clearer than prose.

## Check understanding

Merge overlapping concepts and omit filler. Zero questions is valid. Cover relevant business rules, invariants, flows, states, edge cases, architecture, lifecycle, concurrency, trade-offs, failure modes, and evidence—not syntax.

Ask one applied free-response question at a time through `AskUserQuestion`. Show the text box with **I don't know — explain** and **Proceed without answering**, translated to the conversation language. Do not offer answer choices. In the question text, invite the user to answer in the free-text box; never name interface internals such as "Other".

If the interface cannot show selectable actions, list those two actions beside the free-response prompt.

- Correct: cite the evidence briefly and continue.
- Incorrect or explain: reteach from first principles, then ask a different applied question.
- Second unsuccessful attempt: expose the gap and offer more dialogue or conscious skip.
- **Proceed without answering:** record a conscious decision in the chronicle as unverified, without raw dialogue; never count it as success.

Set no question quota, score, or pass threshold.

## Resolve divergence without presuming fault

When an answer conflicts with the current explanation:

1. show the answer's implication and what request, plan, code, and evidence support;
2. label the diagnosis as a hypothesis;
3. pause only that question while locating the gap in understanding, explanation, requirements, plan, implementation, or proof;
4. return to an earlier phase only after shared confirmation.

If work is valid, explain the divergence and rephrase. If invalid, end the dialogue and return to the first agreed invalid phase.

## Preserve only durable understanding

Persist a concept only when both parties confirm it, evidence supports it, it resolves a real ambiguity or decision, and it helps maintainers.

When all four hold in the Full path:

1. update the source requirement, plan, acceptance criterion, or implementation first;
2. then add a faithful English paraphrase to `How the understanding evolved`, naming the ambiguity, evidence, and effect.

The chronicle records evolution; it never replaces the source contract. In manual mode, propose edits without writing.

In Full, record verified concepts, conscious skips, unresolved gaps, and resolved divergences, including empty categories and no raw dialogue.

Do not store raw answers, scores, failed attempts, personal judgments, or disputed claims as facts.

## Hand off to review

Summarize what was verified, what the user chose to skip, remaining gaps, known differences from the plan, and what was not checked. A conscious skip continues to Review. Evidence that disproves an earlier decision returns the work to the affected phase.

Give Review the request, plan, diff, standards, and verification—not answers or this skill's interpretation.
