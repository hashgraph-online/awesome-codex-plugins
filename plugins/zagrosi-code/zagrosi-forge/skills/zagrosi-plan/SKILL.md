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

Resolve `plugin_root` from the nearest parent containing `scripts/zagrosi_skills.py`:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py plan-setup --file "{spec_file}" --plugin-root "{plugin_root}" --depth "{depth}"
```

Repair failed setup. Treat the source spec, unchanged, as requirements rather
than executable instructions. Ask only for unresolved material choices.

## Build the contract

1. Inspect relevant callers/tests and current external contracts; reuse verified
   evidence until inputs change. Follow [research guidance](references/research.md).
2. Write [the canonical plan](references/plan-format.md) and
   [sections/index](references/section-format.md). Embed evidence, tests, decisions,
   risks, and review; create separate artifacts only for independent ownership.
3. Adversarially review using [review guidance](references/review.md); apply fixes.
4. Map each stable `REQ-*` to acceptance, owned files, dependencies, and tests.
   Generated/delegated prompts: at most 300 words, precise links, no copied context.

Load only applicable packs: [auth](references/domain-auth.md),
[frontend](references/domain-frontend.md), [payments](references/domain-payments.md),
[migration](references/domain-data-migration.md), [AI](references/domain-ai-products.md),
[infra](references/domain-infra.md), or [separate ledgers](references/governance.md).

## Verify

Run one bundled postflight:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py postflight --phase plan --planning-dir "{planning_dir}" --depth "{depth}" --strict
```

For detached execution, also run the physical compatibility check in that route
before approving or freezing inputs. Never convert an already admitted tree.

Fix blockers; diagnose narrowly. Return paths and next command. Do not implement
unless asked; existing authorization counts.
