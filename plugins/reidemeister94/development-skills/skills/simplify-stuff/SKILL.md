---
name: simplify-stuff
description: Remove unnecessary content and simplify files while preserving useful behavior and project knowledge.
argument-hint: [files, directories, or plugin to simplify]
disable-model-invocation: true
---

# Simplify stuff

Use the argument or request as the scope. Apply the [writing contract](../../shared/writing.md).
Inspect the target, relevant references, and inbound callers before deleting or moving content.

Delete what carries no useful behavior, fact, constraint, or decision.
Merge repeated information into its owner, then simplify what remains.
Keep project conventions and non-obvious operational knowledge. A shorter file that loses these facts is a regression.

Check names, paths, commands, conventions, links, and relevant behavior after the change.
Record material removals and their reasons in an existing decision record when useful.
Do not create a new process or file merely to document a routine wording edit.
