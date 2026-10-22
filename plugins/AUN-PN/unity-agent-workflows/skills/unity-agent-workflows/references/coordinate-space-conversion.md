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

## Projective Geometry & Near-Clip Plane Singularity (w <= 0)

When converting world points to screen or UI overlay space:
$$\mathbf{p}_{\text{clip}} = \mathbf{M}_{\text{proj}} \cdot \mathbf{M}_{\text{view}} \cdot \mathbf{p}_{\text{world}}$$

In perspective cameras, screen coordinates are computed via perspective divide by $w_{\text{clip}} = z_{\text{view}}$:
$$\mathbf{p}_{\text{ndc}} = \frac{\mathbf{p}_{\text{clip}}}{w_{\text{clip}}}$$

**The Singularity Failure**: If a world object is behind the camera or closer than the camera's near clip plane ($z_{\text{view}} \le z_{\text{near}}$), $w_{\text{clip}} \le 0$. Standard `Camera.WorldToScreenPoint` divides by a negative number, inverting screen coordinates $(x, y) \to (-x, -y)$, which flips offscreen pointers/HUD arrows 180 degrees backwards!

**Closed-Form Screen-Edge Border Clamping**:
For offscreen target indicators (HUD arrows, radar markers):
1. Compute view-space position $\mathbf{p}_v = \mathbf{V} \cdot \mathbf{p}_w$.
2. If $z_v \le 0$ (behind camera), invert the screen-direction ray:
   $$\mathbf{d} = -(\mathbf{p}_{\text{screen}} - \mathbf{C}_{\text{screen}})$$
   else:
   $$\mathbf{d} = \mathbf{p}_{\text{screen}} - \mathbf{C}_{\text{screen}}$$
3. **Optical Axis Degeneracy Guard**: If $\|\mathbf{d}\|_2 < 10^{-6}$ (target lies directly on the optical axis behind the camera, $x_v \approx 0, y_v \approx 0$), the direction vector is degenerate. Guard against $\text{NaN}$ by assigning the canonical camera up direction:
   $$\mathbf{d} = (0, 1)^T$$
4. Intersect ray $\mathbf{C} + t \mathbf{d}$ with screen boundary rectangle $[x_{\min}, x_{\max}] \times [y_{\min}, y_{\max}]$ with padding margin $m$:
   $$t_x = \frac{W/2 - m}{|d_x| + 10^{-9}}, \quad t_y = \frac{H/2 - m}{|d_y| + 10^{-9}}$$
   $$t^* = \min(t_x, t_y)$$
   $$\mathbf{P}_{\text{clamped}} = \mathbf{C}_{\text{screen}} + t^* \mathbf{d}$$
5. Marker rotation angle: $\theta = \text{atan2}(d_y, d_x)$.

## Frustum Near-Plane 3D Bounding Box Parametric Clipping

When projecting a 3D bounding volume (`Renderer.bounds`, OBB, or AABB) with vertices $\mathbf{V}_k$ to screen space:
If any vertex penetrates the camera near plane ($z_{\text{view}} \le z_{\text{near}}$), naively projecting all 8 corners causes perspective divide by negative/zero values, flipping those corners across the screen center and expanding the bounding box to the entire screen.

**Parametric Near-Plane Edge Clipping Algorithm** (Blinn & Newell, ACM SIGGRAPH; Sutherland-Hodgman):
1. Transform bounding box vertices to camera view space: $\mathbf{v}_i = \mathbf{V}_{\text{view}} \cdot \mathbf{V}_i$.
2. For each of the 12 bounding box edges $(A, B)$:
   - If both $A_z \ge z_{\text{near}}$ and $B_z \ge z_{\text{near}}$: Retain both vertices.
   - If both $A_z < z_{\text{near}}$ and $B_z < z_{\text{near}}$: Discard edge.
   - If edge crosses the near plane ($A_z < z_{\text{near}} \le B_z$ or vice versa): Compute parametric intersection:
     $$t_{\text{clip}} = \frac{z_{\text{near}} - A_z}{B_z - A_z} \in [0, 1]$$
     $$\mathbf{P}_{\text{clipped}} = A + t_{\text{clip}} (B - A)$$
     Retain the valid vertex ($z \ge z_{\text{near}}$) and $\mathbf{P}_{\text{clipped}}$.
3. Project only the retained/clipped 3D vertices to screen space via `Camera.WorldToScreenPoint`.
4. The true tight 2D screen bounding rect is $[\min(x_s), \min(y_s), \max(x_s), \max(y_s)]$.


## CanvasScaler Logarithmic Match Formula

Unity's `CanvasScaler` in `ScaleWithScreenSize` mode with `ScreenMatchMode.MatchWidthOrHeight` scales using a **logarithmic geometric mean**, NOT linear interpolation:

$$\text{scaleFactor} = \left(\frac{W_{\text{actual}}}{W_{\text{ref}}}\right)^{1 - m} \times \left(\frac{H_{\text{actual}}}{H_{\text{ref}}}\right)^m = 2^{(1 - m) \log_2(W_{\text{actual}} / W_{\text{ref}}) + m \log_2(H_{\text{actual}} / H_{\text{ref}})}$$

where $m \in [0, 1]$ is `matchWidthOrHeight`.
- $m = 0$ (Match Width): $S = W_{\text{actual}} / W_{\text{ref}}$
- $m = 1$ (Match Height): $S = H_{\text{actual}} / H_{\text{ref}}$
- $m = 0.5$: $S = \sqrt{\frac{W_{\text{actual}} H_{\text{actual}}}{W_{\text{ref}} H_{\text{ref}}}}$

**Screen to Canvas Coordinate Transform**:
$$\mathbf{P}_{\text{canvas}} = \frac{\mathbf{P}_{\text{screen}} - \mathbf{Origin}_{\text{canvas}}}{S}$$
Never assume linear scaling or raw screen-to-reference ratios on non-matching aspect ratios.

## RectTransform Invariant Equations

A `RectTransform` element is governed by exact geometric invariants:
- Parent Size: $\mathbf{S}_p = (W_p, H_p)$
- Anchor Min / Max: $\mathbf{a}_{\min} = (x_{\min}, y_{\min})$, $\mathbf{a}_{\max} = (x_{\max}, y_{\max}) \in [0, 1]^2$
- Anchor Span: $\mathbf{Span}_{\text{anchor}} = (\mathbf{a}_{\max} - \mathbf{a}_{\min}) \odot \mathbf{S}_p$
- Rendered Rect Size:
  $$\mathbf{Size}_{\text{rect}} = \mathbf{Span}_{\text{anchor}} + \mathbf{sizeDelta}$$

**Rules for Setting Dimensions**:
1. **Point Anchors** ($\mathbf{a}_{\min} = \mathbf{a}_{\max}$): $\mathbf{Span}_{\text{anchor}} = \mathbf{0} \implies \mathbf{sizeDelta} = \mathbf{Size}_{\text{target}}$.
2. **Stretched Anchors** ($\mathbf{a}_{\min} \neq \mathbf{a}_{\max}$): $\mathbf{sizeDelta} = \mathbf{Size}_{\text{target}} - \mathbf{Span}_{\text{anchor}}$.
   *Assigning `sizeDelta = targetSize` on stretched anchors expands the element by parent span, causing blown-up layout.*
3. **Local Position from Pivot $\mathbf{p} \in [0, 1]^2$**:
   $$\mathbf{P}_{\text{local}} = \mathbf{a}_{\min} \odot \mathbf{S}_p + \mathbf{anchoredPosition} + (\mathbf{p} - 0.5) \odot \mathbf{Size}_{\text{rect}} - 0.5 \mathbf{S}_p$$

## Unity 2D RectTransform in Canvas: Screen Space - Overlay vs World Space Invariants

When anchoring UI elements (overhead health bars, damage numbers, interaction reticles, speech bubbles) to 2D sprites or Rigidbody2D entities:

### 1. Screen Space - Overlay Canvas (`camera = null` Invariant)
In Overlay mode, UI is rendered in screen space directly over the viewport. The rendering camera is completely decoupled from UI layout.
When converting a 2D world entity $(x_w, y_w)$ to an Overlay Canvas RectTransform:
1. `Vector2 screenPos = Camera.main.WorldToScreenPoint(worldPos);`
2. **The Overlay Camera Invariant**: `RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRect, screenPos, null, out Vector2 localPoint);`
   **Never pass `Camera.main` to `ScreenPointToLocalPointInRectangle` when Canvas is in Overlay mode.** Passing a non-null camera causes Unity to perform unintended projection matrix inversions on screen coordinates that are already in raw pixels, resulting in massive positional offsets or editor warnings.
3. Closed-Form Local Coordinates on Canvas with scale factor $S$ and canvas dimensions $(W_c, H_c)$:
   $$\mathbf{P}_{\text{canvas}} = \frac{\mathbf{P}_{\text{screen}}}{S}$$
   $$\mathbf{P}_{\text{local}} = \mathbf{P}_{\text{canvas}} - \mathbf{Pivot}_{\text{canvas}} \odot (W_c, H_c)$$

### 2. World Space Canvas in 2D Games ($1/\text{PPU}$ Scale Invariant)
When UI elements live directly in the 2D world hierarchy (e.g. attached as a child of a 2D player/enemy character):
1. **The PPU Scale Invariant**: A Canvas in World Space defines dimensions in UI pixel units (e.g. `sizeDelta = (100, 20)` for a health bar).
   To match the sprite asset's Pixels Per Unit ($\text{PPU}$, e.g. 100 px/unit), the Canvas transform `localScale` **must be set to the inverse of PPU**:
   $$\text{localScale} = \left(\frac{1}{\text{PPU}}, \; \frac{1}{\text{PPU}}, \; 1\right)$$
   For $\text{PPU} = 100$: $\text{localScale} = (0.01, 0.01, 1)$.
2. **The 100x Layout Blowout Trap**: Leaving `localScale = (1, 1, 1)` on a World Space Canvas renders a $120 \times 16$ px health bar at $120 \times 16$ world units (meters), creating a gigantic rectangle 120 meters wide that dwarfs a 1-meter sprite and blankets the orthographic camera.
3. **World-to-Canvas Local Position**:
   $$\mathbf{P}_{\text{canvas\_local}} = (\mathbf{P}_{\text{target\_world}} - \mathbf{P}_{\text{canvas\_world}}) \times \text{PPU}$$

## Unity 2D Orthographic Camera Projection & Viewport Space

In 2D games, Unity cameras are typically set to `CameraClearFlags.SolidColor` or `Depth` with `orthographic = true`.
Unlike perspective cameras, the projection lines are parallel and projective scale $w = 1$. The orthographic frustum dimensions are governed by `orthographicSize`:

- Half-Height: $H_w / 2 = \text{orthographicSize} = S$
- Aspect Ratio: $\alpha = \frac{\text{Screen.width}}{\text{Screen.height}}$
- Half-Width: $W_w / 2 = S \times \alpha$
- World Visible Bounds:
  $$x_w \in [x_{\text{cam}} - S \alpha, \; x_{\text{cam}} + S \alpha]$$
  $$y_w \in [y_{\text{cam}} - S, \; y_{\text{cam}} + S]$$

**Screen Pixel $(s_x, s_y)$ to 2D Orthographic World $(w_x, w_y)$**:
$$w_x = x_{\text{cam}} + \left(\frac{s_x}{\text{Screen.width}} - 0.5\right) \times 2 S \alpha$$
$$w_y = y_{\text{cam}} + \left(\frac{s_y}{\text{Screen.height}} - 0.5\right) \times 2 S$$

Never use perspective field-of-view (FOV) or divide by $z$ in orthographic 2D camera calculations.

## Camera.main.ScreenToWorldPoint 2D z-Distance Plane Invariant

In Unity, `Input.mousePosition` provides a `Vector3` where $z = 0$.
A common AI agent bug is directly invoking:
`Vector3 worldPos = Camera.main.ScreenToWorldPoint(Input.mousePosition);`

**The 2D Plane Trap**: If the camera is at $z_{\text{cam}} = -10$ and $z = 0$ is passed to `ScreenToWorldPoint`, Unity unprojects the point onto the camera's own near plane ($z = -10$). The resulting point lies 10 units behind the 2D gameplay plane ($z = 0$). All subsequent 2D raycasts, triggers, and distance checks to sprites fail or clip through.

**The 2D z-Distance Invariant**:
$$\text{screenPoint.z} = z_{\text{target\_plane}} - z_{\text{camera}}$$
For standard 2D gameplay at $z = 0$ with camera at $z = -10$:
$$\text{screenPoint.z} = 0 - (-10) = 10$$
Always assign `screenPoint.z = -Camera.main.transform.position.z` (or the explicit target plane distance) before calling `ScreenToWorldPoint`.

## 2D Pixel-Perfect PPU Snapping & Texel Alignment

In pixel-art 2D games, rendering at arbitrary sub-pixel floating-point coordinates causes sprite shimmering, edge tearing, and uneven pixel scaling.
Let $\text{PPU}$ be the Pixels Per Unit defined in the sprite asset (e.g. 16, 32, or 64 px/unit).

**Texel Grid Snapping Invariant**:
$$x_{\text{snapped}} = \frac{\text{round}(x \times \text{PPU})}{\text{PPU}}, \quad y_{\text{snapped}} = \frac{\text{round}(y \times \text{PPU})}{\text{PPU}}$$

- Maximum sub-pixel displacement error: $\|\Delta \mathbf{P}\|_\infty \le \frac{1}{2 \times \text{PPU}}$.
- The value $x_{\text{snapped}} \times \text{PPU}$ is guaranteed to be an integer (texel boundary alignment).
- When moving sprites or camera in 2D, accumulate motion in raw floating-point variables, but apply the snapped coordinates to the `Transform.position` or sprite renderer matrix.

## 2D Tilemap Grid-to-World Center Pivot Offset Invariant

Unity `Grid` and `Tilemap` components map continuous world space to discrete integer cell coordinates $(c_x, c_y) \in \mathbb{Z}^2$.
For cell size $\mathbf{S}_{\text{cell}} = (s_x, s_y)$:

1. **World to Cell**:
   $$c_x = \left\lfloor \frac{w_x}{s_x} \right\rfloor, \quad c_y = \left\lfloor \frac{w_y}{s_y} \right\rfloor$$
2. **Cell to Tile World Bounds**:
   $$[c_x s_x, \; (c_x + 1) s_x] \times [c_y s_y, \; (c_y + 1) s_y]$$
3. **Cell to World Tile Center (Half-Tile Pivot Offset)**:
   $$w_{\text{center}, x} = (c_x + 0.5) \times s_x, \quad w_{\text{center}, y} = (c_y + 0.5) \times s_y$$

Omitting the $+0.5$ half-tile offset causes pathfinding, waypoint guidance, and marker placement to target the bottom-left corner of the tile instead of the center, causing 2D agents to get stuck against tile colliders.

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
