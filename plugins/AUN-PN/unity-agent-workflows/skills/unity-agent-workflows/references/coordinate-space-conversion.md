# Coordinate Space Conversion

Read only when a Unity task moves or compares positions across world, local, screen, viewport, canvas, camera, safe-area, or RenderTexture spaces.

## First Identify The Spaces

Before patching position, size, bounds, raycast, tooltip, marker, camera, or UI-follow behavior, answer:

1. What value is being read?
2. What space is it in: world, local, screen pixels, viewport, canvas local, anchored UI, normalized, texture UV, or physics units?
3. What object/root/camera writes or displays the result?
4. Which camera and canvas render mode are involved?
5. Which runtime writer can move either side later: layout, safe area, animation, tween, pooling, camera follow, physics, or scale?

If either source space or destination space is unknown, do not copy coordinates.

## Common Unity Spaces

- `Transform.position`: world units.
- `Transform.localPosition`: parent-local units.
- `Renderer.bounds`: world-space bounds.
- `Collider.bounds`: world-space bounds.
- `RectTransform.anchoredPosition`: parent `RectTransform` anchor space.
- `RectTransform.GetWorldCorners(...)`: world-space corners.
- `Input.mousePosition` / touch position: screen pixels.
- `Camera.WorldToScreenPoint(...)`: world to screen pixels.
- `Camera.ScreenToWorldPoint(...)`: screen pixels to world.
- `Camera.WorldToViewportPoint(...)`: normalized viewport.
- `RectTransformUtility.ScreenPointToLocalPointInRectangle(...)`: screen pixels to UI local space.
- `Screen.safeArea`: screen pixels.
- RenderTexture UV: normalized texture space, not screen or canvas space.

## Conversion Rules

1. Convert through an explicit API path; do not paste numbers between spaces.
2. Use `null` camera only for `ScreenSpaceOverlay`.
3. Use the canvas `worldCamera` for `ScreenSpaceCamera` or `WorldSpace`.
4. Convert after layout/safe-area/camera/tween writers have run, or re-convert on the next layout tick.
5. Keep all related output in one destination space: marker, label, hit area, outline, tooltip, or debug gizmo.
6. Validate by reporting source space, destination space, API path, camera, canvas/root, and runtime proof.

## Coordinate Patch Hard Stop

For output crossing spaces/roots, do not edit coordinates, scale, anchors, offsets, padding, conversion code, fallback rectangles, or layout timing until conversion proof is complete.

Static source inspection is not coordinate proof. Sub-agent reasoning is not coordinate proof. Compile success is not visual proof. Screenshot estimation is not coordinate proof. Checker confidence is not coordinate proof unless it cites concrete runtime values.

Required runtime numeric proof:

```text
source object:
source parent chain:
source RectTransform worldCorners or world bounds:
source canvas/root:
source canvas renderMode:
source canvas scaleFactor:
source camera:
destination object/root:
destination canvas/root:
destination canvas renderMode:
destination canvas scaleFactor:
destination camera:
conversion API path:
converted min/max:
converted center/size:
final output object:
final output anchoredPosition/world position:
final output sizeDelta/bounds:
runtime writer checked:
validation:
```

- Every required field must contain concrete runtime values from Play Mode, Unity MCP/runtime hierarchy query, Device Simulator, Game view inspection, or temporary runtime logs.
- Values such as `expected`, `likely`, `same helper`, `known from source`, `compile passed`, or `checker thinks OK` are not proof.
- Missing `source bounds`, `converted min/max`, or `final output position/size` is a FAIL.
- For cross-canvas or cross-root focus/highlight/spotlight/hole output, missing source canvas/root/camera/scaleFactor, destination canvas/root/camera/scaleFactor, converted min/max, or final drawn rect is a FAIL.
- On FAIL, stay read-only and add a runtime probe plan only.
- Do not patch from inference.

## Cross-Canvas/Root Focus And Spotlight

Use when focus, highlight, spotlight, hole, dim, mask, or blocker output is drawn in a different canvas/root than the selected runtime target.

```text
source target:
source selected bounds:
source canvas/root:
source camera:
source scaleFactor:
destination overlay/root:
destination camera:
destination scaleFactor:
conversion API path:
converted min/max:
converted center/size:
final drawn rect:
runtime writer checked:
validation:
```

Overlay, dim, mask, blocker, scrim, spotlight, and hole objects are destination/output surfaces. Do not use their full-screen rect, generated mask geometry, or blocker rect as source target bounds unless an explicit marker inside that surface names the intended source target.

## UI Between Different Roots

Use when a UI element in one canvas/root drives a marker, tooltip, selection outline, blocker, or debug rectangle in another root.

```csharp
sourceRect.GetWorldCorners(worldCorners);
for (int i = 0; i < 4; i++)
{
    Vector2 screenPoint = RectTransformUtility.WorldToScreenPoint(sourceCamera, worldCorners[i]);
    RectTransformUtility.ScreenPointToLocalPointInRectangle(
        destinationRoot,
        screenPoint,
        destinationCamera,
        out destinationLocalCorners[i]);
}
```

Build destination rect from min/max of `destinationLocalCorners`, then assign it under `destinationRoot`.

## World Object To UI

Use when UI follows a world object, spawn marker, unit, prop, collider, VFX anchor, interactable, or camera/world marker.

1. Resolve the exact active `GameObject`.
2. Choose a bounds source: explicit marker transform, `Renderer.bounds`, or `Collider.bounds`.
3. Convert world center/corners through the active camera.
4. Convert screen pixels into the destination canvas/root.
5. Validate camera, canvas, scale, pooling, clone, animation, and camera-follow writers before editing offsets.

## Safe Area And Screen Edges

`Screen.safeArea` is screen pixels. Convert it into the destination canvas/root before using it as UI local bounds.

Do not treat these as interchangeable:

- `Screen.width` / `Screen.height`
- safe-area pixels
- canvas reference resolution
- `RectTransform.sizeDelta`
- viewport `0..1`
- world camera units

## RenderTexture Or World-Space Canvas

If input, UI, or marker positions pass through a RenderTexture or world-space Canvas:

1. Identify texture pixel size and displayed rect.
2. Convert screen point to the displayed rect local space.
3. Convert local point to UV.
4. Convert UV to RenderTexture pixels or camera viewport.
5. Then convert to the target world/UI space.

Do not use main screen pixels directly as RenderTexture pixels.

## Proof Format

```text
source object:
source value:
source space:
source camera/root:
destination object:
destination space:
destination camera/root:
conversion API path:
runtime writer checked:
validation:
```
