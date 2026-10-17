# Target Bounds Catalog

Read this only when choosing bounds for a specific visible object type.

## UI Button / Tab / Menu Item

Use:
1. `markerRect`: child marker named `* Focus Target`, `* Highlight Target`, `* Visual Target`
2. `visualRect`: visible graphic cluster from active `Image`, `RawImage`, `Text`, `TMP_Text`, icon, label, card/frame children
3. `interactiveRect`: `Button` / `Selectable` root rect only as fallback

Reject:
- full-size invisible hitbox
- transparent background image
- layout-only parent
- mask/clip root unless it is the visible frame

Report `interactiveRect`, `visualRect`, `markerRect`, selected rect, and root-button fallback status.

## UI Card / Panel / Modal

Use:
1. `markerRect`: explicit marker rect
2. `visualRect`: visible panel/frame image rect
3. content group rect if the card has padding or transparent margins

Reject parent section root, full-screen container, and scroll viewport unless it is the target.

## Icon / Badge / Currency / Resource Counter

Use:
1. icon image rect + value text rect combined
2. icon rect only if the user points to the icon
3. text rect only if the user points to the number/label

Do not use the whole HUD bar unless the request names the whole bar.

## Scroll/List Row

Use active row visible frame, row content cluster, then row button/hitbox fallback.

Before converting:
- ensure row is active after layout/rebuild
- ensure scroll content has completed positioning
- reject pooled inactive row templates

## Tooltip / Coach Bubble / Tutorial Panel

Use panel visible rect, arrow tip/pointer marker when aligning to target, and text bounds only when requested.

## World Unit / Character / Vehicle / Prop

Use:
1. explicit marker transform: `FocusPoint`, `AimPoint`, `Core`, `Center`, `Head`, `Socket`
2. `Renderer.bounds` combined across visible renderers
3. `Collider.bounds` only for hitbox/debug or when requested
4. root transform position fallback

Reject pooled inactive prefabs, parent container bounds that include offscreen helpers, and weapon/projectile children unless requested.

## Projectile / Bullet / Missile / Beam

Use active renderer bounds, collider bounds for hitbox debug, and trail/line renderer bounds only if visual trail is the target. For fast-moving objects, sample after movement update or in `LateUpdate`.

## VFX / Particle / Explosion / Area Effect

Use explicit center marker, `ParticleSystemRenderer.bounds`, then authored radius or gameplay area config. Do not use particle system root if renderer bounds or radius exists.

## 2D World Object / Sprite / Prop

Use explicit marker transform, `SpriteRenderer.bounds` or combined `Renderer.bounds`, then `Collider2D.bounds` if collision/hitbox target.

## Spawn Point / Path / Invisible Trigger

Use marker transform/shape gizmo if visible target is a marker, collider/trigger bounds for gameplay debug, and never invisible trigger bounds for a visual focus unless requested.

## Safe Area / Screen Edge / Camera View

Use `Screen.safeArea` converted into destination canvas/root, or camera viewport corners converted through the active camera. Do not use raw `Screen.width` / `Screen.height` as overlay-local coordinates.

## Text / TMP Label

Use text rect after layout rebuild, preferred values only for sizing decisions, and outline/shadow padding if the focus ring must visually surround text. Reject parent row/card unless requested.
