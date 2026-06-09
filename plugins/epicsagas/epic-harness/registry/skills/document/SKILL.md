---
name: document
description: "Trigger: public API, function, or module added or changed — exports, signatures, new modules."
---

# Document — Auto-Documentation

## When to Trigger
- New public function, class, or API endpoint
- Function signature changed (params added/removed)
- Module purpose unclear from code alone
- User explicitly asks for documentation

## Process

### 1. Detect what changed
- New exports? → Add JSDoc/docstring
- Changed params? → Update existing docs
- New file? → Add module-level doc comment

**Why:** Undocumented changes are the most common source of onboarding friction. Catching every diff ensures no public surface is left without context.

### 2. Write docs
Follow the project's existing doc style. If none exists:

**TypeScript/JavaScript:**
```typescript
/**
 * Brief description of what this does.
 *
 * @param name - Description of parameter
 * @returns Description of return value
 * @throws ErrorType - When this happens
 *
 * @example
 * const result = myFunction("input");
 */
```

**Python:**
```python
def my_function(name: str) -> str:
    """Brief description.

    Args:
        name: Description of parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When this happens.
    """
```

**Why:** Consistent doc style across the project reduces cognitive load for every reader. Inlining examples prevents the "how do I call this?" round-trip.

### 3. Don't over-document
- Skip obvious getters/setters
- Skip internal/private helpers unless complex
- Code should be self-documenting first, comments second

**Why:** Noise docs train readers to ignore all comments. Document only where the code cannot speak for itself.

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "The code is self-documenting" | Good naming helps readers, but doesn't explain intent, constraints, or edge cases. | Document the why, the constraints, and the non-obvious. |
| "I'll document it later" | Later never comes. If it's worth exporting, it's worth documenting now. | Document as you write. Updating is cheaper than reconstructing intent. |
| "Docs go stale anyway" | Stale docs are better than no docs. They at least signal intent. Keep them in sync with code changes. | Put docs near code (JSDoc/docstring). They update with the code. |

## Evidence Required

Before claiming documentation is done, show ALL applicable:

- [ ] Every new public function/class has a doc comment (show one example)
- [ ] Changed signatures have updated docs (show the diff)
- [ ] `@param` / `@returns` / `@throws` present for non-trivial functions
- [ ] At least one `@example` for complex APIs

**"I added docs" without showing them = not documented.**

## Red Flags
- Comments that restate the code: `// increment i` → `i++`
- Outdated comments that contradict the code
- Missing docs on public API that others will call
