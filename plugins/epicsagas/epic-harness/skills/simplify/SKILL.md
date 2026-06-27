---
name: simplify
dimension: context_assembly
description: "Code simplification for high-complexity files. Targets deep nesting, copy-paste patterns, god functions, and files over 200 lines."
---

# Simplify — Code Simplification

## When to Trigger
- File exceeds 200 lines
- Function exceeds 40 lines
- Deeply nested code (3+ levels)
- Copy-pasted blocks detected
- "This is getting hard to follow" feeling

## Process

### 1. Measure
- Line count, function count, nesting depth
- Identify the longest/most complex function

**Why**: You cannot improve what you cannot quantify. Baseline metrics prove simplification actually happened and prevent subjective "it feels cleaner" claims.

### 2. Extract
- **Extract function**: Turn a code block into a named function
- **Extract constant**: Replace magic numbers/strings
- **Extract module**: Split large files by responsibility

**Why**: Named abstractions replace "what does this block do?" with "what does this function promise?" — reducing cognitive load per reading unit.

### 3. Rename
- Variables: describe what it holds, not how it's computed
- Functions: describe what it does, not how
- Files: match the primary export/class

**Why**: Precise names eliminate the need for comments and make wrong code look wrong. A reader should understand intent from names alone.

### 4. Reduce
- Remove dead code (unused imports, unreachable branches)
- Replace imperative loops with declarative (map, filter, reduce)
- Merge duplicate logic into shared utility

**Why**: Every line of code is a line someone must read, understand, and maintain. Fewer lines with the same behavior means lower lifetime cost.

### 5. Verify
- All tests still pass after simplification
- No behavior changes — only structural improvements

**Why**: Simplification that breaks behavior is not simplification — it is a regression. Tests are the safety net that makes structural changes safe.

## Constraints
- One simplification at a time — verify between each
- Never simplify and add features in the same change

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "We might need this later" | YAGNI. Code you don't need is code you maintain for free. Add it when you need it. | Delete it. When the need arises, write it with current context — not stale assumptions. |
| "This abstraction makes it more flexible" | Flexibility without a concrete use case is complexity. Simple code is flexible code. | Abstract only after you see the second use case. Two concrete examples beat one imagined future. |
| "It's already working, don't touch it" | Chesterton's Fence: understand why it exists first. But if it's needlessly complex, simplify it. | Understand it, write tests for it, then simplify it. Working code that nobody can read is a ticking bomb. |

## Evidence Required

Before claiming simplification is done, show ALL of these:

- [ ] Before/after metrics: line count, function count, or nesting depth reduced
- [ ] All tests pass after change (show output)
- [ ] No behavior change: same inputs produce same outputs
- [ ] Each extraction is independently justified (not "because it felt cleaner")

**"I cleaned it up" without metrics = opinion, not simplification.**

## Red Flags
- Simplifying code you don't understand
- Over-abstracting (3 files for a 10-line utility)
- Mixing simplification with feature additions
