---
name: simplify-stuff
description: Deep simplification pass over a target's files. Use when the user invokes /simplify-stuff or asks to simplify files, docs, skills, or plugins (simplify, semplifica).
argument-hint: [files, directories, or plugin to simplify]
disable-model-invocation: true
---

# simplify-stuff

The argument is the target scope. Run a deep pass that applies the [writing contract](../../shared/writing.md) to existing files:

1. Read every file in the scope, plus the files each one references or shares content with — judge a file inside its ecosystem, never alone. Check what points at the scope from outside before restructuring, so no link or section reference breaks.
2. Rewrite each file to the contract, deduplicating across the whole scope: each fact lands in its one right home and the other files link to it.
3. Verify before finishing: grep that load-bearing specific tokens (names, paths, commands, conventions) survived; confirm nothing active links to removed content; and check the result is both shorter and clearer — when a cut would lose real capability, relocate the content instead of deleting it.

Record what was removed and why in the project's usual decision record, so cuts stay recoverable.
