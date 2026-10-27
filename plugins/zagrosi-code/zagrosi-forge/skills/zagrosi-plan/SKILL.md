---
name: zagrosi-plan
description: Produce compact, reviewed implementation contracts and ordered sections, with the user's requested analysis depth.
allowed-tools:
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" team status *)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" status *)
  - Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" next-section *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" team status *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" status *)
  - Bash(python "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" next-section *)
  - Bash(py -3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" team status *)
  - Bash(py -3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" status *)
  - Bash(py -3 "${CLAUDE_PLUGIN_ROOT}/scripts/zagrosi_skills.py" next-section *)
---

# Zagrosi Plan

For a Git target, check `team status --target-dir "{target_dir}"` with Forge’s
helper before work or resume.
Follow [team coordination](../zagrosi-forge/references/collaboration.md) when configured or unavailable;
reuse the same task across phases and delegated agents.

Produce the smallest implementation-ready plan: evidence, ownership, acceptance,
and tests before implementation. Apply the all-depth
[engineering standard](../zagrosi-implement/references/engineering.md): trace callers,
plan root-cause repairs and cohesive modules, and update ownership.
Depth is `lean` by default; honor requested
`standard`/`deep` using [depth standards](references/depth-standards.md).
When detached execution is requested, select the
[physical authoring route](references/detached-plan-format.md) before writing.
Only when the user asks for state-first lean, or the planning directory has
`status.json`, follow [state-first](../zagrosi-implement/references/state-first.md)
instead: write `plan.md`, run setup with `--state-first`, and skip the contract and
postflight below.

Resolve absolute `plugin_root`: the plugin directory two levels above this skill's
folder, containing `scripts/zagrosi_skills.py`; never the target repo. Claude Code
substitutes it when loading this skill: `${CLAUDE_PLUGIN_ROOT}`. Literal text there
means the file was read directly: derive the path; no such shell variable exists.
Run every helper command, including returned argv arrays, with the exact prefix
`python3 "{plugin_root}/scripts/zagrosi_skills.py"` (Python 3.11+; `python` or
`py -3` on Windows); host pre-approvals match that text.
Resolve `target_dir` separately to the absolute project root and run these
helpers from that directory. Use absolute `spec_file` and `planning_dir` paths.
For a chat-only brief, first save the user's requirements unchanged as `spec.md`
in the chosen planning directory; keep the implementation contract separate.

```bash
python3 "{plugin_root}/scripts/zagrosi_skills.py" plan-setup --file "{spec_file}" --plugin-root "{plugin_root}" --target-dir "{target_dir}" --depth "{depth}"
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
python3 "{plugin_root}/scripts/zagrosi_skills.py" postflight --phase plan --planning-dir "{planning_dir}" --target-dir "{target_dir}" --depth "{depth}" --strict
```

For detached execution, also run the physical compatibility check in that route
before approving or freezing inputs. Never convert an already admitted tree.

Fix blockers; diagnose narrowly. Return paths and next command. Do not implement
unless asked; existing authorization counts.
