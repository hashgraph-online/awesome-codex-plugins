# Outside-In TDD Patterns

## Double-Loop TDD

Use a slow outer loop to express user value and a fast inner loop to build the pieces.

1. Outer red: a functional or acceptance test describes a thin user journey.
2. Inner red: a focused test proves the next missing component.
3. Inner green: write the least code that moves the component forward.
4. Inner refactor: clean code and tests while everything is green.
5. Return outward: run the functional test to discover the next missing component.

The outer test should not become a complete specification. It anchors the journey; faster tests carry the detailed cases.

## Scratchpad Discipline

Keep a short scratchpad for tempting future work:

- URLs or model fields that may be needed later.
- Edge cases discovered while implementing the current slice.
- Refactors that are only safe after another test exists.

Only promote a scratchpad item when a failing test or current design pressure requires it.

## Triangulation

When the first implementation is suspiciously hardcoded, add a second example before generalizing. This is useful for validation branches, redirect targets, template context, and model relationships.

Avoid triangulation when the correct general solution is already simpler than the hardcoded version.

## Working State To Working State

For structural changes:

1. Ensure the suite is green.
2. Add or identify a regression test for the behavior that must survive.
3. Take one reversible step.
4. Get back to green quickly.
5. Delete redundant code and tests only after replacement behavior is covered.

This pattern is safer than rewriting a Django view, URL scheme, model relationship, and template at once.

## Outside-In Layer Walk

| Layer | Useful Test Boundary | Avoid |
| --- | --- | --- |
| Browser | Selenium or framework functional test | Exhaustively checking every branch |
| URL/View | Django client response, redirect, template, context | Mocking the view internals |
| Form | Instantiate form and inspect errors or cleaned data | Only checking rendered strings |
| Model | Constraints, relationships, methods, validation | Assuming `save()` runs validation |
| Domain helper | Plain unit test | Pulling Django in when not needed |

## Refactoring Tests

Refactor tests when they obscure intent:

- Extract behavior-named helpers for repeated user actions.
- Keep helper names at the user's level, not Selenium's method names.
- Collapse multiple assertions when they describe one effect of one action.
- Split tests when one failure would hide a different behavior.
