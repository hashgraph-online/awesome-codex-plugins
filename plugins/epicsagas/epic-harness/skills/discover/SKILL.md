---
name: discover
description: "Trigger: vague/unfocused request or solution-without-problem. Also invoked via /discover command. Reframes goal before acting."
modes:
  - auto   # auto-triggered on vague/unfocused requests
  - /discover  # explicit invocation
---

# Discover — Problem Discovery

You are starting the **Discover** phase. Your job is to help the user articulate what problem they are actually trying to solve, before jumping to solutions or specs.

**CRITICAL**: Run `HARNESS_DIR=$(epic-harness path)` first. NEVER use `.harness/` in the project directory.

## Iron Law

NO SPEC WITHOUT A PROBLEM STATEMENT. Building the wrong thing well is worse than building the right thing poorly.

## Process

### Step 0: Prerequisites

- Resolve harness directory: `HARNESS_DIR=$(epic-harness path)`
- Read any existing context (CLAUDE.md, README, codebase structure)
- Check for existing problem statements in `$HARNESS_DIR/specs/PROBLEM-*.md`
- Call `mem_recall` with a hint describing the current topic area
- Check for past `decision` or `pattern` nodes related to this domain
- If prior problem exploration exists, reference it: "We discussed something similar before..."
- If existing PROBLEM files are found, review them — the user may be continuing prior work

**Why**: Past context prevents re-exploring ground already covered. The knowledge graph connects today's vague request to yesterday's decisions.

### Step 1: Listen

Read the user's request carefully. Repeat it back in your own words and ask:
- "Is that the core of it, or is there more?"

Categorize the request:

| Category | Signal | Example |
|----------|--------|---------|
| Solution without problem | User names a technology or approach | "Add Redis caching" |
| Feature without context | User describes output, not why | "Build a dashboard" |
| Systemic complaint | Broad negative without specifics | "Everything is slow" |
| Vague ambition | Goal with no boundaries | "Make it better" |
| Clear problem | Observable gap stated | "Login fails for 5% of users" |

**Why**: Categorization determines the probing technique. Misreading the category leads to wrong questions.

### Step 2: Probe

Select the technique based on the category identified in Step 1. Ask **max 3 questions per round**, run **max 3 rounds**. If the user can't answer or says "I'm not sure", proceed to Frame with what you have.

#### Technique Selection

| User signal | Technique | Core question |
|---|---|---|
| Names a solution ("Add Redis") | **5 Whys** | "What's happening that makes you need this?" → repeat |
| Describes a feature without why | **JTBD** | "What situation makes you need this? What would 'done' look like?" |
| "Everything is broken" | **Fishbone** | "Which area: People / Process / Technology / Data / Environment?" |
| Vague or contradictory | **Socratic** | "What specifically do you mean by 'X'?" |
| Has a vision but no path | **Done looks like** | "When this works perfectly, what do you see?" |
| Uncertain assumptions | **Assumption map** | "What must be true for this to work?" |

#### Detailed Technique Reference

**5 Whys** — when the user presents a solution without a problem:
```
User: "Add Redis caching to the API."
→ "What's happening that makes you want caching?"
→ "Why is that slow?"
→ "Why does that query take long?"
```
Stop when you reach an actionable root cause. Max 5 levels.

**JTBD (Jobs To Be Done)** — when the user describes a feature without context:
```
User: "Build a dashboard."
→ "What situation makes you need this?"
→ "What would you do with the information right now?"
→ "What would have to be true for you to say 'this solved it'?"
```
Extract job stories: "When [situation], I want [motivation], so I can [outcome]."

**Fishbone** — when the user has a systemic complaint:
```
User: "Everything is broken."
→ Walk through categories: People, Process, Technology, Data, Environment
→ "Which of these areas is the biggest contributor?"
→ "Is this on all branches or specific ones?"
```
Map causes across categories, then narrow to the top 1-2.

**Socratic Questioning** — when the request is vague or contradictory:
```
User: "Make it more secure." / "I want it to be faster."
→ Clarification: "What specifically do you mean by 'secure' / 'fast'?"
→ Probing assumptions: "What makes you believe this is the issue?"
→ Implications: "If we change X, what happens to Y?"
→ Alternatives: "What other approaches did you consider?"
```

**"What Does Done Look Like?"** — when the user has a vision but no path:
```
→ "When this is shipped and working perfectly, what specifically do you see?"
→ "What would I click, what output would appear, what would the logs show?"
```
Work backwards from the concrete end state.

**Assumption Mapping** — when the request depends on uncertain premises:
```
→ "Let me check what we're assuming must be true for this to work."
→ List 4-5 assumptions, ask which are uncertain.
```
Shaky assumptions become prerequisites.

Each round should narrow the space. If after 2 rounds you have enough to frame, don't force a third.

**Why**: The right technique extracts the real problem in 2-3 rounds instead of 10 random questions. Technique mismatch wastes rounds and frustrates the user.

### Step 3: Frame

Synthesize everything into a structured problem statement:

> **[Who]** experiences **[observable problem]** when **[trigger condition]**, resulting in **[quantified impact]**. The desired state is **[measurable outcome]**.

Capture supporting context:
- **Root cause** (from 5 Whys) or **Job story** (from JTBD)
- **Constraints**: timeline, technology, scale, compatibility
- **Assumptions**: what must be true, which are uncertain
- **Out of scope**: what this problem explicitly does NOT cover

Show the frame to the user and ask: "Does this capture the problem accurately?"

**Why**: A written problem statement is testable. If you can't write one, you haven't discovered the problem yet.

### Step 4: Save

Once confirmed, save the problem statement:

```bash
mkdir -p "$HARNESS_DIR/specs"
```

Write to `$HARNESS_DIR/specs/PROBLEM-{timestamp}.md` (see Output Format below).

If the user realizes there are multiple problems during probing, address them one at a time. Each problem gets its own file.

### Step 5: Transition

Tell the user: **"Problem defined. Run `/spec` to turn this into a buildable specification."**

If the user wants to explore further (e.g., they realize there are actually 3 problems), loop back to Step 2 with the new angle.

**Why**: The transition from problem to spec is natural but explicit. The user owns the decision to move forward.

## When to Trigger

**Auto-trigger** (no command needed):
- User's request lacks a clear problem or goal
- User names a technology/solution without explaining why
- User describes symptoms without identifying the underlying issue
- User says "I don't know where to start" or equivalent
- Request is so broad it could mean 3+ different things

**Explicit invocation** (`/discover`):
- User wants to formally start the discover phase for a new project or feature
- User wants to re-explore a problem before re-specifying
- Continuation from a previous discovery session

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "Let's just start building and figure it out" | Building without a problem is expensive guessing. | Spend 5 minutes framing the problem. It saves hours of rework. |
| "The problem is obvious" | If it were obvious, you'd have a spec, not a vague request. | Write the problem statement. If it's obvious, it takes 30 seconds. |
| "I don't have time for questions" | You don't have time to build the wrong thing. | Run 2 focused rounds, not 10 open-ended ones. |
| "I already told you the problem" | You told me a solution. The problem is why you need that solution. | Ask one "why" question. If the answer reveals the problem, proceed. |
| "Can't you just figure it out from the code?" | Code shows what exists, not what's missing or why it hurts. | Combine code exploration with user context for the full picture. |
| "Let me just show you the bug" | A bug is a symptom, not a problem. Fixing symptoms is whack-a-mole. | Trace the bug to its root cause before jumping to a fix. |

## Evidence Required

Before claiming the problem is defined, show ALL of these:

- [ ] Problem statement written in the structured format (Who / Problem / When / Impact / Desired state)
- [ ] Root cause or job story identified
- [ ] At least one measurable/observable criterion for success
- [ ] User confirmed the frame is accurate
- [ ] Scope boundaries stated (what's in and out)

**"I think I understand" without a written problem statement = guessing.**

## Red Flags

- Jumping to solutions or code during the discovery conversation
- Asking more than 3 questions per round (overwhelming the user)
- Running more than 3 rounds without attempting a frame (analysis paralysis)
- Ignoring when the user says "I'm not sure" — that IS information
- Producing a problem statement the user didn't confirm
- Confusing symptoms with root causes
- Framing the problem so broadly it could mean anything ("improve the system")
- Skipping discovery for non-trivial, ambiguous work

## Output Format

Save to `$HARNESS_DIR/specs/PROBLEM-{timestamp}.md`:

```markdown
---
status: framed
created: {ISO-8601 timestamp}
context: {one-line summary}
---

# Problem: {title}

## Problem Statement
{Who} experiences {observable problem} when {trigger condition}, resulting in {quantified impact}. The desired state is {measurable outcome}.

## Root Cause / Job Story
{5 Whys chain or JTBD job story}

## Constraints
- Timeline: {when is this needed}
- Technology: {stack constraints}
- Scale: {expected load/users}
- Compatibility: {backward-compat requirements}

## Assumptions
- {assumption} — {certain / uncertain}
- {assumption} — {certain / uncertain}

## Out of Scope
- {what this problem explicitly does NOT cover}
```
