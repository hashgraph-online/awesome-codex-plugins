---
name: unslop-reasoning
description: >
  Strip AI-slop patterns from reasoning traces (chain-of-thought, extended
  thinking, agent decomposition) — not final prose. Reasoning text has its
  own slop catalog that regular unslop doesn't target: over-explaining the
  question, over-hedging, over-decomposing trivial problems into 6-bullet
  substeps, infinite-loop rationalization.
  Trigger: /unslop-reasoning, "clean up my reasoning", "fix this chain of
  thought", "this CoT sounds robotic". Applies to reasoning output; does
  not override regular /unslop mode.
---

# unslop-reasoning

## Purpose

The regular unslop skill targets prose. Chain-of-thought output has a
separate failure mode — AI-slop patterns that appear in *reasoning*, not in
the final answer. These patterns have no equivalent in the prose catalog
because nobody hand-edits a thinking trace. The research in docs/research/
calls this gap out explicitly: "no AI-slop reasoning pattern catalog" (Cat
19). This skill fills it.

Apply when the user pastes a reasoning trace — an internal chain of
thought, an agent's decomposition, or extended-thinking output — and asks
for it to read less robotic.

## Signals of reasoning slop

Six canonical patterns, each with an example and a tighter rewrite.

### 1. Restating the question

**AI:**

> The user is asking how to fix the auth middleware bug. They want me to
> identify the root cause and propose a fix.

**Human:**

> Auth middleware bug. Find cause, propose fix.

The model often spends a paragraph paraphrasing the input back to itself.
Humans don't. They read, maybe underline, and move.

### 2. Over-hedging the plan

**AI:**

> There are several factors to consider when approaching this problem.
> First, we should think about the scope. It's also important to consider
> the context. There are many potential approaches.

**Human:**

> Three options: A, B, C. A is fastest. B is safest. Picking A unless
> something looks wrong.

Hedging in reasoning inflates the trace without narrowing the problem.
Real thinking commits to a direction early, then revises.

### 3. Over-decomposing

**AI (for a two-line fix):**

> Step 1: Identify the file.
> Step 2: Find the function.
> Step 3: Read the function.
> Step 4: Identify the bug.
> Step 5: Plan the change.
> Step 6: Write the change.
> Step 7: Verify the change.

**Human:**

> Open auth.py. Token expiry uses `<`, should be `<=`. Fix line 42.

Trivial problems don't need a 7-step decomposition. A flat "here's the
answer" is more honest than a ceremonial march.

### 4. Infinite-loop rationalization

**AI:**

> Option A could work, but it has drawback X. Option B avoids X but has
> drawback Y. Option A's drawback X might be acceptable if we consider
> that Y is also a concern. But B's drawback Y could be addressed by...

**Human:**

> A or B. A has X, B has Y. Picking A because X is reversible and Y is not.

When the same two options keep re-appearing with reshuffled pros and cons,
the reasoning is circling, not progressing. Commit. Name the tiebreaker.

### 5. Performative exhaustiveness

**AI:**

> Let me consider all possibilities. It could be a network issue. It could
> be a DNS issue. It could be a routing issue. It could be a firewall
> issue. It could be a permission issue. It could be...

**Human:**

> Looks like DNS or firewall. Checking DNS first because the logs show
> resolution errors.

Human reasoning filters. It doesn't enumerate. Listing every possibility
without prioritizing reads as AI performing rigor rather than doing it.

### 6. Unmotivated confidence-then-retraction

**AI:**

> I am certain the bug is in the cache layer. Wait, let me reconsider.
> Actually, it might be in the middleware. Although, on reflection, I
> believe I was right the first time. The cache layer is the most likely
> cause.

**Human:**

> Probably the cache. Middleware is also possible — check logs before
> committing to one.

Swinging between "I am certain" and "let me reconsider" three times in
one paragraph is not thinking. It is simulated humility.

## Application

When the user asks you to clean up a reasoning trace:

1. Read the trace once.
2. Mark which of the six patterns appear.
3. Rewrite the trace so each marked section becomes a single sentence that
   commits to a direction. Keep facts, cut ceremony.
4. Preserve every concrete detail — file names, line numbers, error
   strings, specific numbers. Only the meta-reasoning gets trimmed.
5. If the cleaned trace is < 30% of the original, flag it: "This trace
   was mostly hedging. The actual content is X."

## Boundaries

- Do NOT use this on the FINAL answer. Final answers have their own voice
  targets handled by the regular `/unslop` skill. This is for the visible
  thinking that precedes the answer.
- Do NOT remove a correction. If the trace genuinely reconsidered and
  changed its mind based on a concrete finding, preserve that beat — it's
  a real reasoning move, not simulated humility.
- Do NOT over-compress. A 40-line thinking trace compressed to one line
  is as suspicious as the original. Human reasoning has surface area.
  Aim for the shape of human thinking, not for word-count minimalism.
- Code, commands, error messages, file paths, numbers: preserved exactly.

## Research basis

Cat 19 (Agentic Autonomous Thinking) names the missing-catalog gap
directly: "there are well-documented blacklists for AI-slop prose (stock
phrases, sycophancy, hedging stacks — Cat 01, 16). There is no equivalent
list for AI-slop reasoning patterns: over-explaining, over-hedging, over-
decomposing, and the infinite-loop rationalization visible mid-agent-run."
This skill is the first pass at that catalog. It is a starting point, not
a final answer.

Cat 06 (Chain-of-Thought Reasoning) makes the case that visible-reasoning
traces are a feature, not a bug. The goal here is not to hide reasoning
but to make the visible part read like a person thinking, not a model
performing thought.
