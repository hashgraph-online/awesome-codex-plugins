# Runtime Visible Output

Use for runtime-visible output drawn, positioned, blocked, aimed, anchored, masked, followed, measured, or converted from a live Unity target. Broader than tutorial focus UI.

Examples include UI overlays, selection outlines, input blockers, drag targets, HUD markers, objective arrows, world-to-UI labels, damage numbers, nameplates, health bars, safe-area-dependent UI, camera targets, RenderTexture-driven UI, world-space canvases, and hardcoded layout used as a substitute for a live target.

For extracted UI items, textless UI sprites, generated slices, or design manifests, the visible source can be the extracted item bounds rather than a live scene object. In that case, load `references/ui-and-visual-assets.md` and use the Extracted UI Item Assembly Gate before overlay text/button placement.

## Runtime Visible Output Hard Stop

Do not edit coordinates, anchors, offsets, padding, scale, layout timing, camera conversion, or fallback constants until this proof exists:

```text
user-visible output
-> active source object
-> selected source bounds: markerRect / visualRect / interactiveRect / logicRect
-> source parent chain
-> source owner script/component
-> runtime writer after creation/layout
-> source space and camera/canvas
-> destination root/canvas/space
-> conversion API path
-> converted output rect/position
-> validation method
```

If any link is unknown, stay read-only or inspect deeper. Do not patch from semantic similarity, object center, first-name lookup, screenshot proximity, or a previously edited constant.

## Hardcoded Layout Guard

```text
visible target -> runtime object -> runtime bounds -> converted coordinate space -> overlay
```

Hardcoded layout is not runtime object proof. Use hardcoded values only as a named fallback after runtime target resolution fails, and report residual risk.
