# UI And Visual Assets

## UI Routing

Use this when the task touches HUD, menus, overlays, mobile layout, safe areas, text readability, screenshot alignment, or visual source assets.

- Layout/anchors/safe area -> inspect hierarchy, `RectTransform`, `CanvasScaler`, parent groups, masks, and runtime builders.
- Readability/polish -> inspect typography, contrast, density, touch targets, icon/value alignment, localized text growth.
- Focus/highlight/spotlight/modal dimming for any visible UI target -> resolve the real runtime target first, then draw from converted runtime bounds, not hardcoded layout.
- New/replaced UI art, icon art, panel art, sprite, model, VFX source -> run visual asset workflow before code integration.
- Same sprite/model/animation behavior across preview, transition, menu, and gameplay -> prove every requested surface owner plus active asset/factory/fallback path before editing.

## Mobile UI Rules

- Preserve the primary scene/viewport visibility.
- Put primary actions in reachable thumb zones.
- Respect notches and safe areas.
- Keep tappable targets near 44x44 points / 48dp equivalent or larger.
- Keep text away from decorative strokes, scanlines, and corner brackets.
- Plan for localized strings to grow.
- For Thai or other complex scripts, reserve extra line height and vertical padding.
- Use stable dimensions for rails, grids, buttons, counters, and HUD slots so hover/state/text changes do not shift layout.

## Screenshot Fix Rules

1. Identify the exact visible target.
2. Prove runtime owner chain.
3. Change only the marked layer and direct dependencies.
4. If placement is wrong, check parent layout before child offsets.
5. If text/color/visibility reverts, patch both creation and refresh/update paths.
6. If the user asks for object truth, do not use screenshot pixels as the source of truth.
7. Do not use hardcoded focus anchors, sizes, or expected menu positions as the primary target path.
8. Validate with screenshot, hierarchy, or runtime proof.
9. If a visible patch already failed or the user says it is still wrong, stop editing and collect runtime numeric proof before another patch.
10. If the visible change depends on sprite/model/animation state, also capture the active asset/sprite/model name, active caller, selector/factory result, and fallback path.

## Spotlight And Modal Highlight

Use this when a tutorial, onboarding, tooltip, modal, focus ring, dim scrim, or spotlight needs to point at a visible UI target such as a button, icon, card, chip, panel, HUD slot, meter, label, list row, marker, or modal control.

- The highlighted target must stay bright and unobstructed unless the user asks otherwise.
- Dim or block only the background/outside area requested.
- Use the same coordinate space for target bounds, focus ring, spotlight hole, scrim, and input blocker.
- Do not create a new button, icon, panel, card, marker, duplicate object, or replacement action unless the user explicitly asks.
- If background input must be blocked, keep only the allowed modal/action target interactive.
- Check `Canvas.renderMode`, `CanvasScaler`, safe area, sorting order, parent scale, masks, layout groups, and runtime-created roots before editing offsets.
- For cross-canvas focus/spotlight, convert target `GetWorldCorners()` through `RectTransformUtility.WorldToScreenPoint(...)` and `RectTransformUtility.ScreenPointToLocalPointInRectangle(overlayRoot, ...)`; do not use `Screen.width` / `Screen.height` normalized values as overlay-local coordinates.
- Resolve duplicate names before choosing a target. Parent chain and active/interactable state must disambiguate the real runtime object.
- If the visible target is interactive, still compare `markerRect`, `visualRect`, and `interactiveRect` before choosing; use hardcoded fallback only after target lookup fails and report it.
- If no marker exists and the visible center differs from the interactive/root center, recommend adding a marker before changing coordinates.
- After a failed focus/highlight/spotlight/modal patch, require runtime numeric values for target bounds, converted rect, and final drawn ring/hole/blocker rect before changing offsets, anchors, scale, timing, or fallback constants again.

## Designer Focus Marker

When the desired focus point is a designer-chosen position, not the object center, require an explicit marker.

Recommended UI marker:

- child `RectTransform`
- name: `<Target Name> Focus Target`
- no visual graphic required
- placed in the same hierarchy as the visible target
- size matches the intended spotlight/focus bounds

The marker is the source of truth for tutorial focus.

## Visual Asset Gate

Use this gate for source asset creation/replacement/material redesign:

- model, sprite, character, unit, vehicle, prop, environment piece
- UI/HUD/panel/button/frame/icon art
- animation source or sprite sheet
- VFX source texture/frame
- procedural shipped art

Do not use the gate for:

- code-only bug fixes
- tuning/balance
- localization text
- layout around existing assets
- Inspector reference wiring
- shader/material parameter tuning when the source asset stays unchanged
- validation only

## Visual Asset Workflow

1. Define exact asset type and purpose.
2. Generate/obtain the source asset with the approved project tool.
3. If the user provides a generator ID, source asset ID, sprite sheet, prefab, scene, or runtime object name, treat it as a hard source lock. Do not substitute another ID/source or apply it to global factories without caller blast-radius proof.
4. For UI assets, require no baked text unless explicitly requested.
5. For resizable UI, require 9-slice-friendly corners, straight edges, and quiet center.
6. For pixel art, check grid intent, crisp silhouette, palette, transparent background, and import settings.
7. Integrate actual source output, not a mood-board reference.
8. Before wiring the asset into code, prove the requested surface callsite and avoid changing shared selectors/factories used by non-target surfaces.
9. Pause before broader C# integration and rerun architecture routing.

## Sprite/Model Variant Availability

Before code edits that should change direction, pose, animation frame, or visible model state:

- List expected variant paths/names.
- Prove which variants exist in `Assets/`, `Resources`, Addressables, or the repo's asset catalog.
- Prove the selector/factory lookup path and all runtime callers.
- Prove the fallback sprite/model/pose used when variants are missing.
- If the fallback is visually indistinguishable, report that before patching more code.

Missing variants require either source asset generation/replacement, a proven surface-local fallback, or user approval to broaden scope.

## Diegetic Screen Pattern

For in-world consoles, radar panels, terminals, or screen-in-screen UI:

- Make the panel feel like game-world hardware first.
- Use clear state rails, telemetry cells, and readable action zones.
- Keep primary actions thumb-safe.
- Prefer Canvas-to-RenderTexture or world-space Canvas when the screen must exist in the game world.
- Keep CRT/bloom/noise effects subtle and localized.
