---
name: council
description: "4-voice parallel deliberation (Architect · Skeptic · Pragmatist · Critic) for architecture, tech selection, or design decisions with no clear answer. Anti-anchoring: each voice gets independent context. Records decision in harness-mem."
---

# Council — Structured Multi-Voice Decision Making

## Iron Law
NO MAJOR DECISION WITHOUT AT LEAST TWO OPPOSING VIEWPOINTS.

## When to Trigger
- Architecture choices (monolith vs microservice, SQL vs NoSQL)
- Technology selection (framework, library, language)
- Design decisions with no clear right answer
- Trade-offs between competing requirements (speed vs quality, security vs usability)
- User explicitly requests deliberation

## Process

### 1. Identify the Decision
State the decision in one clear question. Example: "Should we use WebSockets or SSE for real-time updates?"

### 2. Summon 4 Voices (Parallel)

Launch 4 independent subagents using the Agent tool, each with ONLY the question and relevant context (NOT the full conversation history — this prevents anchoring bias):

| Voice | Role | Focus |
|-------|------|-------|
| **Architect** | Long-term correctness | Maintainability, extensibility, architectural alignment |
| **Skeptic** | Challenge assumptions | Simpler alternatives, hidden costs, "what if we don't?" |
| **Pragmatist** | Ship it now | Timeline, user impact, operational complexity, team skills |
| **Critic** | Find the cracks | Edge cases, failure modes, migration risks, rollback difficulty |

**Anti-Anchoring Rule**: Each voice receives only:
- The decision question
- Relevant codebase context (file paths, current architecture)
- Their role and focus area
They do NOT receive: the full conversation, other voices' opinions, or the user's leaning.

### 3. Synthesize

After all 4 voices report back:
1. List areas of **agreement** (strong signal)
2. List areas of **disagreement** (where trade-offs live)
3. Present the user with:
   - **Recommended option** (based on agreement weight)
   - **Key trade-off** (the real decision to make)
   - **Reversibility** (how hard to undo each option)

### 4. Record Decision

Save the decision to memory:
```bash
epic-harness mem add \
  --title "Decision: {question}" \
  --type decision \
  --importance 0.9 \
  --body "Context: ...\nOptions: ...\nChosen: ...\nRationale: ...\nTrade-off accepted: ..."
```

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "I already know the answer" | Your gut feeling is not analysis. Council surfaces blind spots. | Run Council anyway — you'll learn something. |
| "This is too slow for a simple decision" | 5 minutes of council prevents weeks of regret. | Set a 5-minute timer and run the full process. |
| "The team already agreed" | Groupthink is not consensus. Diverse perspectives prevent disasters. | Summon all 4 voices — especially the Skeptic and Critic. |
| "I don't need 4 voices for this" | Even simple decisions benefit from the Skeptic and Critic. | Run all 4 voices. Skipping voices skips insight. |

## Evidence Required

- [ ] All 4 voices were summoned and reported back
- [ ] Areas of agreement and disagreement are listed
- [ ] A recommended option with key trade-off is presented
- [ ] Decision recorded in memory with rationale
- [ ] No voice received the full conversation history

## Red Flags
- Skipping the Council for "obvious" decisions
- Only summoning voices that agree with you
- Reading the full conversation to all voices (anchoring)
- Not recording the decision and rationale
