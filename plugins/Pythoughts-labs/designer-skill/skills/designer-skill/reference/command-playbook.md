# Command Playbook

The canonical vocabulary is `scripts/command-metadata.json`. Each entry owns its description, argument hint, aliases, cues and reference reads. Do not maintain a second dispatch table in prose or source code.

Use `list_commands` to discover supported verbs. `get_command` validates a verb and returns help plus reference names; it does not eagerly load their contents. Use `get_reference` for only the relevant documents.

Explicit canonical commands and aliases take precedence over natural-language scoring. Unknown explicit commands fail rather than silently falling back to an implementation workflow. Natural-language results are suggestions, not authorization to edit. A low-confidence request should retain the user's scope, not expand it.

`check` and `review` are read-only. `plan` produces a plan. `setup` is optional and requires authorization to write project context. Missing PRODUCT.md is not a reason to discard DESIGN.md or interrupt a small repair. `css` is a supported canonical command across discovery, help and dispatch.

Start with at most four references. The dispatcher lists additional candidates in `deferredReads`; load them only with a task-specific reason. Some repairs need only one reference. Do not add an aesthetic checklist to unrelated backend or database work.

After implementing, collect relevant evidence. `review_and_gate` is a static check with explicit coverage, not a full UI readiness certificate. Audits can finish with defects reported; implementation cannot claim checks that were never run.

When adding a verb, update its registry entry and add positive, alias, negative-trigger and discovery-parity tests. Validate every referenced document exists in the shipped package.
