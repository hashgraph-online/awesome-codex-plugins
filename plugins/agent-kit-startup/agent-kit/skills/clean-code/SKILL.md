---
name: clean-code
description: Remove AI code slop (redundant comments, noisy try/catch, any casts, deep nesting), alias code-deslop. Use after AI sessions or before review.
version: 0.1.0
category: quality
---

# Clean Code (code-deslop)

Obvious comments, excessive defense, `any` to silence the type checker, deep nesting - patterns that read like machine code.

## When to use

- After AI session, before commit
- PR review with generated code
- Explicit request: deslop / clean AI code
- Before code review

Diff or specific file: this skill. Large refactoring: `cleancode-refactor` subagent.

## Process

1. `git diff` against base (e.g., `main`)
2. Scan the areas below
3. Minimal change; same behavior except for clear bugs
4. Lint and typecheck
5. Summary in 1-3 sentences

## Focus Areas (slop patterns)

### 1. Redundant comments

Repeat the obvious instead of explaining the why.

```typescript
// BAD - slop
const total = items.length; // Get the total number of items
return total; // Return the total

// GOOD - no comment needed, code is self-explanatory
const total = items.length;
return total;
```

### 2. Too much defense

Try/catch or null check in internal path where caller already guarantees valid data.

```typescript
// BAD - slop (internal helper, caller always passes valid data)
function formatName(user: User): string {
  try {
    if (!user) throw new Error('User is required');
    if (!user.name) throw new Error('Name is required');
    return user.name.trim();
  } catch (error) {
    console.error('Error formatting name:', error);
    throw error;
  }
}

// GOOD
function formatName(user: User): string {
  return user.name.trim();
}
```

### 3. `any` to escape typing

Cast just to silence the checker instead of modeling the correct type.

```typescript
// BAD - slop
const result = (response as any).data;

// GOOD - use the actual type
const result = (response as ApiResponse).data;
```

### 4. Deep nesting

Stacked if/else or try/catch; prefer early return or guard clauses.

```typescript
// BAD - slop
function process(input: string | null) {
  if (input) {
    if (input.length > 0) {
      if (isValid(input)) {
        return transform(input);
      }
    }
  }
  return null;
}

// GOOD - early returns
function process(input: string | null) {
  if (!input || input.length === 0 || !isValid(input)) return null;
  return transform(input);
}
```

### 5. Style inconsistent with file

Names, imports, error handling or formatting different from the rest of the file.

### 6. Em dash ("—") in text

The em dash "—" is one of the strongest marks of AI-generated text. In comments, commit messages, docs, README, HANDOFF and memory, it's slop: replace with hyphen, colon, comma, parentheses or period.

```text
BAD  (AI slop, with em dash)
feat: new cache — reduces latency and simplifies flow
the CLI parses — then validates — then saves

GOOD
feat: new cache reduces latency and simplifies flow
the CLI parses, validates and saves
the CLI parses; then validates; then saves
```

Rule: **completely eliminate** "—" from commits, text and docs. Only use when mandatory for a concrete reason (e.g., literally quoting external text, data or an API that already contains the character). In these cases, preserve the original.

Note: this applies to the repository and to chat. It's textual slop, not just code; see rules `agent-output-hygiene`, `docs-professional-standard` and `ux-tone`.

## Conventions

- Same observable behavior, except for clear bug fixes
- Small edits; align to local style
- Comment that explains *why*: keep it
- Run linter/typecheck after

## Checklist

- [ ] Obvious comments removed
- [ ] Unnecessary try/catch and checks removed where flow is reliable
- [ ] `any` replaced with appropriate type or removed
- [ ] Nesting flattened (early return / guards)
- [ ] Em dash "—" eliminated from comments, commits and touched docs (only keep if mandatory literal quote)
- [ ] Style aligned to file
- [ ] No meta-language / gossip / chat reasoning in comments, commits or touched docs (rule `agent-output-hygiene`)
- [ ] Lint/typecheck ok; short summary