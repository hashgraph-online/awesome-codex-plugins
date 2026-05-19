# AI Workflows

## Purpose

Use this when a Unity task needs a repeatable process before and after edits. The goal is to stop new work from piling into the nearest controller, manager, partial class, or scene YAML value.

## Universal Workflow

1. Load live repo context.
   - Read repo instructions and architecture docs.
   - Check dirty files.
   - Derive the user's actual project structure before routing.
   - Load only the relevant detailed reference.

2. Read graph and architecture context.
   - Prefer a current graph report when available.
   - If the graph is missing, continue with direct source inspection.
   - Do not copy static graph counts into permanent rules.

3. Prove the owner chain.
   - UI/visible bugs: visible object -> scene/prefab/reference -> script/component -> mutating method -> serialized/runtime override.
   - Screenshot/visible text bugs: visible text -> exact string/localization key/text setter -> UI text object -> creator method -> refresh/update writer -> owner.
   - Multi-surface visible behavior: prove each requested surface separately before editing any one surface.
   - Sprite/model/animation state bugs: prove active asset/sprite/model name, selector/factory result, and fallback path.
   - Gameplay bugs: entrypoint -> orchestrator -> collaborator -> data/config -> contracts/events.
   - Compile bugs: exact error -> file -> assembly -> dependency edge -> smallest fix.

4. Classify placement before editing.
   - Use `references/project-structure-discovery.md` to map the repo's real folders, namespaces, assemblies, scenes, prefabs, and content paths.
   - Feature/module behavior -> the existing repo-local owner for that feature/module.
   - Reusable runtime service -> the existing repo-local service/system/runtime owner path.
   - Cross-module API/event/interface -> the repo's existing contract/event/gateway boundary.
   - Project primitive -> the repo's existing primitive/shared foundation path.
   - Content/tuning/unlock/balance data -> ScriptableObjects, content definitions, config, or serialized fields.
   - Source visual asset -> asset generation/replacement workflow before integration code.

5. Apply stop gates.
   - No fixed sample layout unless the repo already uses it or the user requests migration.
   - No new scripts in broad folders when a more specific live owner exists.
   - No direct sibling feature imports.
   - No system-to-feature dependency.
   - No hub growth when a collaborator can own the work.
   - No shared factory/helper/style/global method patch for a scoped visible target until caller search proves all runtime callers and non-target surfaces stay unchanged.
   - No asset/source substitution when the user provided an exact ID/path/name/surface.
   - No preview-only or transition-only patch when the user also requested gameplay/runtime behavior.
   - No directional sprite/model/animation patch until variant availability and fallback behavior are proven.

6. Edit the smallest safe file set.
   - Preserve Unity serialized field names where possible.
   - Use `FormerlySerializedAs` when renaming serialized fields.
   - Keep unrelated scene, prefab, cache, and generated output out of the patch.

7. Validate.
   - Docs: `git diff --check`.
   - JSON/asmdef: parse and compare actual files.
   - C#: compile-oriented check.
   - UI/visible: screenshot, hierarchy, or runtime-owner proof.

8. Close with proof.
   - Changed files.
   - Validation result.
   - Runtime-owner or structural proof.
   - Non-requested systems touched.
   - Visual asset tool status.

## Workflow Recipes

Load `references/workflow-recipes.md` only when the task needs a named recipe (`WF-0` through `WF-12`) or when the universal workflow above is not specific enough.

## Sub-Agent Decision And Permission Gate

Default: use one main agent only.

Consider sub-agents only when at least one is true:

- The task has 2+ independent proof tracks that can run read-only in parallel.
- Runtime-visible owner is ambiguous across multiple surfaces, scenes, prefabs, factories, feature names, or source assets.
- The user-visible target and semantic feature name disagree.
- A large repo-wide audit, security scan, checker pass, or changed-plus-related-files review needs independent verification.
- The user explicitly asks for sub-agent, multiple agents, parallel agents, checker, or independent review.

Do not use sub-agents when:

- The owner file and runtime writer are already proven.
- The task is a simple one-file edit, command, explanation, or narrow validation.
- The main agent has not read live project instructions.
- The user says `อย่าพึ่งแก้`, unless the sub-agent plan is only being proposed or the user explicitly approves read-only discovery. Edit permission remains forbidden.
- The sub-agent would edit files before the main agent locks scope.

Before spawning any sub-agent, ask the user first.

The approval request must include:

```text
why sub-agent is needed:
sub-agent count:
each sub-agent task:
read-only or edit permission:
files/surfaces allowed:
files/surfaces forbidden:
checker needed: yes/no
```

Do not spawn until the user explicitly approves in the same turn, except when the user already explicitly requested sub-agents in that turn.

## Main-Agent Scope Lock Before Worker Patch

Use this before sub-agents patch screenshot, visible UI, runtime text, state-step, or runtime-visible output tasks.

Main agent must record:

```text
visible target:
exact text/key searched:
exact object/surface/source ID:
owner file:
creator method:
refresh/update writer:
allowed runtime caller(s):
forbidden callers/surfaces:
shared helper/factory/global method candidates:
allowed files:
explicitly not touched:
nearby candidates rejected:
```

Workers must stop when they only find a candidate, helper, factory, style utility, localization provider, global method, registry, bridge, or shared primitive. They must ask for scope revision if the proven owner differs from the scope lock, requires a file outside `allowed files`, touches a forbidden caller/surface, or changes existing behavior for callers outside the allowed runtime caller list.

Checker must return FAIL when the patch lacks the visible target -> owner -> writer chain, when a shared helper/global method is edited without caller blast-radius proof, when an exact asset/source ID was substituted, or when rejected nearby candidates are not explained for screenshot/visible text fixes.

Checker must also return FAIL when a requested multi-surface behavior proves only one surface, when a preview/transition patch is presented as gameplay proof, or when a directional sprite/model/animation change lacks active asset/factory/fallback proof.
