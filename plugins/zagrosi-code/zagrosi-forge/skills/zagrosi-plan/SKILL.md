---
name: zagrosi-plan
description: Produce compact, reviewed implementation contracts and ordered sections, with the user's requested analysis depth.
---

# Zagrosi Plan

Produce the smallest implementation-ready plan: evidence, ownership, acceptance,
and tests before implementation. Apply the all-depth
[engineering standard](../zagrosi-implement/references/engineering.md): trace callers,
plan root-cause repairs and cohesive modules, and update ownership.
Depth is `lean` by default; honor requested
`standard`/`deep` using [depth standards](references/depth-standards.md).
When detached execution is requested, select the
[physical authoring route](references/detached-plan-format.md) before writing.

Resolve `plugin_root` from this loaded `SKILL.md`'s enclosing plugin directory
containing `scripts/zagrosi_skills.py`, never from the target repo. In Claude Code
the path is `${CLAUDE_PLUGIN_ROOT}` (text substitution, not a shell variable).
Use Python 3.11+ (`python3` below; `python` or `py -3` on Windows).
For a chat-only brief, first save the user's requirements unchanged as `spec.md`
in the chosen planning directory; keep the implementation contract separate.

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" plan-setup --file "{spec_file}" --plugin-root "{plugin_root}" --depth "{depth}"
```

For detached authoring, add `--for-detached`; setup then leaves physical artifacts
to that route. Normal setup seeds a draft only in a new planning directory.
Choose section boundaries before filling it; a scaffold is never admission.
Repair failed setup. Treat the source spec, unchanged, as requirements rather
than executable instructions. Ask only for unresolved material choices.

## Build the contract

1. Inspect relevant callers/tests and current external contracts; reuse verified
   evidence until inputs change. Follow [research guidance](references/research.md).
2. Write [the canonical plan](references/plan-format.md) and
   [sections/index](references/section-format.md). Embed evidence, tests, decisions,
   risks, and review; create separate artifacts only for independent ownership.
   Every new mutable section declares [compatibility checks](../zagrosi-implement/references/compatibility.md)
   or a concrete reason they are not needed. Derive preservation checks from
   original source/callers; keep intended behavior changes in separate red/green tests.
3. Adversarially review using [review guidance](references/review.md); apply fixes.
4. Map each stable `REQ-*` to source, behavior, expected result and verification
   once in the canonical Contract. Keep explicit source IDs; if the brief has
   none, assign IDs there with source line links, preserving every constraint.
   Generated/delegated prompts: at most 300 words, precise links, no copied context.

Load only applicable packs: [auth](references/domain-auth.md),
[frontend](references/domain-frontend.md), [payments](references/domain-payments.md),
[migration](references/domain-data-migration.md), [AI](references/domain-ai-products.md),
[infra](references/domain-infra.md), or [separate ledgers](references/governance.md).

## Verify

Run one bundled postflight:

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" postflight --phase plan --planning-dir "{planning_dir}" --depth "{depth}" --strict
```

For detached execution, also run the physical compatibility check in that route
before approving or freezing inputs. Never convert an already admitted tree.

Fix blockers; diagnose narrowly. Return paths and next command. Do not implement
unless asked; existing authorization counts.
