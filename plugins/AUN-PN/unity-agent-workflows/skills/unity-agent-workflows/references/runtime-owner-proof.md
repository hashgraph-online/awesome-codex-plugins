# Runtime Owner Proof

Use when a visible fix may not show in Play mode, a screenshot target is ambiguous, an object may have duplicate names, or a previous change "did nothing".

This file is the core owner-proof router. Load extra gate files only when the matching trigger appears.

## Owner Chain

Visible object proof chain:

Prove this before editing visible/runtime behavior:

```text
visible object
-> scene/prefab/reference
-> script/component
-> mutating method
-> serialized/runtime override
```

If one link is missing, search another direction before stopping.

## Runtime Visible Target Lock

Use when the user asks to move, focus, highlight, click, bind, align, dim around, brighten, select, inspect, or fix any visible UI/gameplay target.

Required proof before editing:

```text
user-visible target
-> runtime object / runtime GameObject
-> runtime RectTransform/Transform
-> scene/prefab/source creator
-> script/component owner
-> runtime layout/movement writer
-> duplicate-name result
-> measurement coordinate space
-> validation method
```

If proof is incomplete, do not patch coordinates. Inspect deeper or ask one concise question if two live owners are equally plausible.

## Load Extra Detail Only When Needed

| Trigger | Read |
|---|---|
| visual/model/sprite/source asset/prefab/animation integration where names or owners disagree | `references/visible-object-identity.md` |
| same visible behavior across menu/gameplay/preview/runtime/transition/scene surfaces | `references/multi-surface-visible.md` |
| directional sprites, model poses, animation frames, selector/factory fallback, generator ID, asset ID, source asset lock | `references/asset-source-lock.md` |
| screenshot text, OCR, visible UI label, HUD text, menu text, tutorial text, localized string, TMP text/styling | `references/screenshot-text-owner.md` |
| shared factory/helper/registry/bridge/global method/style/localization/sprite selector/reusable presenter dependency | `references/shared-caller-blast-radius.md` |
| runtime-visible output, focus ring, tutorial spotlight, modal hole, tap/click target, highlight, marker, visual alignment, input blocker, world-to-UI label, HUD marker, hardcoded layout | `references/runtime-visible-output.md`, `references/runtime-visible-targets.md` |
| visible-output patch failed/unchanged/wrong/challenged, repeated coordinate/layout/fallback/asset visible mismatch | `references/runtime-numeric-proof.md` |
| button/icon/card/HUD row/world unit/projectile/VFX/text bounds, choosing `markerRect` vs `visualRect` vs `interactiveRect` | `references/target-bounds-catalog.md` |
| world/local/screen/viewport/canvas/camera/safe-area/RenderTexture mismatch or world-to-UI conversion | `references/coordinate-space-conversion.md` |
| serialized scene object, prefab asset, prefab instance, prefab variant, component fields, object refs, editor tooling | `references/serialized-persistence.md` |

## Read-Only Target Inspection

When the user says not to edit yet, or asks what the object is:

- Do not edit files.
- List candidate objects with parent chain, scene/prefab source, active state, component type, and owner script when available.
- Count duplicate names and explain which candidates are runtime-active.
- Wait for explicit edit approval before patching.

## Search Directions

- Visible text, object name, sprite name, material name, method name.
- Scene YAML and prefab YAML refs.
- Script GUID from `.meta` files.
- Serialized field names and `FormerlySerializedAs`.
- Runtime builders: `Awake`, `OnEnable`, `Start`, `LateUpdate`, layout builders, factories, presenters.
- Refresh paths that rewrite labels/colors/sizes after creation.
- `GameObject.Find`, `FindObjectOfType`, `Resources.Load`, addressables, service locators.
- Animation, tween, clone, pooling, safe-area, CanvasScaler, or camera scripts that override values.

## Do Not Assume

- Scene transform scale if startup rewrites it.
- Prefab default if scene overrides exist.
- A constant if a presenter/layout helper later clamps it.
- Compile passing as visual proof.
- Static source inspection, sub-agent reasoning, checker confidence, or screenshot estimation as runtime numeric proof.
- A semantically related file as screenshot-target ownership.
- `GameObject.Find(name)` when duplicate/inactive objects may exist.
- Screenshot pixels when the user asks for object, hierarchy, or code-derived position.
- Hardcoded layout/position when a live `RectTransform`, `Transform`, `Renderer`, `Collider`, or marker can be resolved.

## Screenshot Ambiguity

If screenshot and text disagree, ask one concise clarifying question before editing. If the screenshot clearly marks one object, that runtime target wins over semantic guesses; scope to that object and direct dependencies only.
