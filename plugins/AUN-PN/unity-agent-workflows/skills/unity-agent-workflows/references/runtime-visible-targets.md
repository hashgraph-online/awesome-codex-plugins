# Runtime Visible Targets

Read this only when a task involves focus, highlight, click/tap target, visual target, spotlight, modal dimming, duplicate names, hardcoded layout/position, or "do not guess".

## Runtime Visible Output Scope

Use this for any visible or interactive output whose position, size, mask, blocker, label, camera target, selection, or marker depends on a runtime object. Do not limit this workflow to tutorial overlays.

Common cases:

- UI overlays, markers, highlights, selections, blockers, masks, and dimming holes.
- HUD markers, objective arrows, nameplates, health bars, damage numbers, and world-to-UI labels.
- Click/tap/drag targets, input blockers, tooltip anchors, and selection brackets.
- Safe-area-dependent UI, RenderTexture UI, world-space Canvas, camera/world/screen/canvas conversions.
- Hardcoded anchors or fallback rectangles that stand in for live runtime targets.

Required chain:

```text
visible output -> active runtime target -> selected source bounds -> converted output rect -> runtime writer -> validation
```

If the chain is incomplete, stay read-only or inspect deeper before editing.

## Hardcoded Fallback Contract

Keep hardcoded layout only as a named fallback, never as the primary path, when a live runtime target can be resolved.

Allowed fallback shape:

```text
try runtime target -> try runtime bounds conversion -> if lookup/conversion fails, use named hardcoded fallback -> report residual risk
```

Keep the fallback until runtime lookup and coordinate conversion are validated across scene timing, orientation, safe area, and device layout.

When fallback runs, the closeout or runtime log must include:

- target name or identifier that failed
- expected parent chain or owner
- source canvas and destination overlay root, if known
- failed step: lookup, duplicate ambiguity, inactive target, missing camera, layout not ready, or conversion failure
- fallback anchor/size name used

## UI Target Resolution

For Unity UI targets such as buttons, icons, cards, chips, panels, HUD slots, meters, labels, tooltips, list rows, overlays, and modal controls:

1. Resolve the exact active `RectTransform`.
2. Require an expected parent chain, owner component, or source builder when names are not unique.
3. For interactive targets, require the `Button`, `Toggle`, `Slider`, `Selectable`, `EventTrigger`, raycast target, collider, or input component to be active/enabled/interactable when applicable.
4. Reject ambiguous duplicates. Do not choose the first object returned by `GameObject.Find(name)`.
5. Read bounds with `RectTransform.GetWorldCorners()`.
6. Convert bounds into the same overlay/canvas/root coordinate space used to draw the focus, hole, ring, or blocker.
7. Compute focus/highlight/spotlight from the converted runtime bounds, not guessed constants.
8. Reject hardcoded focus anchors/sizes as the primary path when an active UI target exists.

## Visual Target Selection

A runtime target can have multiple bounds. Pick the one for the requested job, not the first object with the right name. A live object alone is not proof.

Always classify these separately:

- `interactiveRect`: click/tap/hit area such as `Button`, `Selectable`, `Collider`, `EventTrigger`
- `visualRect`: pixels/mesh/sprite/text/card the user sees
- `logicRect`: gameplay area such as attack radius, trigger volume, spawn region, lock-on range
- `markerRect`: author-provided focus/anchor marker such as `Focus Target`, `Highlight Target`, `Visual Target`, `Aim Point`, `Socket`, `Muzzle`, `Pivot`
- `overlayRect`: selected rect after conversion into destination overlay/root space

For focus rings, spotlight holes, tutorial highlights, selection brackets, arrows, tooltip anchors, and visual alignment, prefer:

1. explicit `markerRect`
2. `visualRect`
3. `interactiveRect`
4. named hardcoded fallback

Do not use `interactiveRect` as the primary visual target when visible children or marker transforms exist.

## Overlay/Dim/Mask/Blocker Source Bounds

Overlay, dim, mask, blocker, scrim, spotlight, and hole objects are destination/output surfaces. Do not use their `RectTransform`, full-screen rect, generated mask geometry, or blocker rect as the source bounds for focus, highlight, spotlight, or hole calculation.

These objects can be source bounds only when they contain an explicit `markerRect` or marker child that names the intended target and is not merely the output surface. Otherwise, resolve the active runtime target separately, choose `markerRect`, `visualRect`, `interactiveRect`, or `logicRect`, then convert those selected source bounds into the destination overlay/root.

For focus/highlight/spotlight/hole patches, using an overlay/dim/mask/blocker rect as source bounds is a FAIL unless the report proves the explicit marker and target relationship with runtime values.

If `markerRect` is missing and `visualRect` differs strongly from `interactiveRect`, report ambiguity and recommend adding a marker.

If an object is found but no marker exists:

- Do not claim the target is proven from the object alone.
- Show candidate rects before choosing.
- If the selected rect does not match the user-visible point, recommend adding a marker.
- Do not patch hardcoded coordinates from root/object center by guessing.

## Required Target Report

For every runtime visible output target, closeout or diagnosis must include:

- target name
- parent chain
- owner script/component
- `interactiveRect`
- `visualRect`
- `markerRect`
- selected rect
- source canvas
- destination overlay/root
- conversion method
- whether fallback was used

Patch coordinates only after the selected rect is proven.

## Runtime Numeric Target Report

For repeated visible failures, the report must include concrete runtime values, not only owner names or source-code reasoning:

```text
target name:
parent chain:
owner script/component:
duplicate count:
active/interactable state:
markerRect:
visualRect:
interactiveRect:
logicRect:
selected rect:
source canvas/root:
source renderMode:
source scaleFactor:
source camera:
destination overlay/root:
destination renderMode:
destination scaleFactor:
destination camera:
conversion method:
converted min/max:
converted center/size:
final drawn object:
final drawn position:
final drawn size/bounds:
fallback used:
runtime writer checked:
validation:
```

Values like `expected`, `likely`, `same helper`, `known from source`, `compile passed`, or `checker thinks OK` are not proof.

## Cross-Canvas/Root Focus Proof

For cross-canvas or cross-root focus, highlight, spotlight, hole, dim, mask, or blocker output, the report must prove all of these runtime numeric values:

- source canvas/root
- source camera
- source scaleFactor
- destination canvas/root
- destination camera
- destination scaleFactor
- converted min/max
- final drawn rect

The source rect must be the selected runtime target bounds, not the destination overlay/dim/mask/blocker surface, unless an explicit marker inside that surface is the documented target.

## Repeated Visible Failure Lock

If the user says the result is still wrong, unchanged, in the wrong place, or provides marked visual evidence after a patch:

1. Stop tuning constants.
2. Treat the marked visual target as the current scope.
3. Re-resolve the active runtime target and duplicate names.
4. Re-classify `markerRect`, `visualRect`, `interactiveRect`, `logicRect`, and selected output rect.
5. Re-check source canvas/root, destination canvas/root, camera, scale factor, layout timing, safe area, animation, pooling, and refresh writers.
6. Collect the Runtime Numeric Target Report.
7. Also prove the active runtime caller and active asset/sprite/model name when the patch affects factories, selectors, visual layers, animation frames, generated assets, or shared preview/gameplay paths.
8. Patch only after the converted output rect, final drawn rect, active caller, and active source asset are proven with runtime values where relevant.

Do not infer the fix from the previous patch, nearby object names, compile success, asset file location, or a visually similar control.

Checker rule: return FAIL when runtime numeric proof is absent for a repeated visible-output patch, or when the patch uses overlay/dim/mask/blocker output rects as source bounds without an explicit marker proof.
