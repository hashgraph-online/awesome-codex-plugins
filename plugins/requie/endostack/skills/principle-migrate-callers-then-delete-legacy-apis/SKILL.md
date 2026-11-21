---
name: principle-migrate-callers-then-delete-legacy-apis
description: Use when a replacement internal API exists but code still calls the old one. Move all callers over and remove the old API in that same wave, without a compatibility layer, as long as no external user relies on it.
disable-model-invocation: true
---

# Migrate callers, then delete legacy APIs

Replacing an internal API means moving every caller to the replacement and removing the original within one change set or wave, with no shim left over.

## When it applies

A new internal API exists and callers of the old one remain. All three preconditions must hold:

- Nothing outside the project relies on the old API staying compatible.
- The project can take one coordinated breaking change.
- The replacement comes out of a simplification or refactor.

If any one fails, a deprecation period may be justified. Say which precondition failed and why.

## What to do

1. Enumerate the callers with a script or codemod, per [principle-build-the-lever](../principle-build-the-lever/SKILL.md), so the list is complete and reproducible. A text search misses dynamic dispatch and re-exports; a type-aware search or the compiler's own errors after deleting the old symbol are more reliable.
2. Migrate every caller.
3. Remove the old API in that same change set.
4. Rewrite the tests so they check the new contract, and drop any test whose only job was pinning the old internals ([principle-test-behavior-not-implementation](../principle-test-behavior-not-implementation/SKILL.md)).

Legacy APIs are a common home for weaker security. If the old `verify_token(token)` skipped audience checks and the new `verify_token(token, audience)` enforces them, every caller left on the old path is still exploitable. Deleting the old function is what closes the hole.

## The failure it prevents

Two APIs that live forever, and shims that become permanent debt every new contributor must learn.

## Done when

The old API has zero callers and has been removed.

Related: [principle-outcome-oriented-execution](../principle-outcome-oriented-execution/SKILL.md), [principle-test-behavior-not-implementation](../principle-test-behavior-not-implementation/SKILL.md), [principle-build-the-lever](../principle-build-the-lever/SKILL.md).
