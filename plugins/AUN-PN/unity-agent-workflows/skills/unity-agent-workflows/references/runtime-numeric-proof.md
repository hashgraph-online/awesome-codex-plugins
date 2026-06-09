# Runtime Numeric Proof

Use after any visible-output patch fails, appears unchanged, lands in the wrong place, or is challenged with a screenshot. After a visible patch is challenged, static source reasoning is not enough.

Static source inspection is not runtime proof. Sub-agent reasoning is not runtime proof. Compile success is not visual proof. Screenshot estimation is not coordinate proof. Checker confidence is not proof without values.

## Runtime Numeric Proof Gate

Before another coordinate, focus, layout, marker, camera, safe-area, or fallback patch, collect concrete runtime values from Play Mode, Unity MCP/runtime hierarchy query, Device Simulator, Game view inspection, or temporary runtime logs:

```text
source object:
source parent chain:
source bounds: markerRect / visualRect / interactiveRect / logicRect
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
converted rect min/max:
converted center/size:
final drawn object:
final drawn position:
final drawn size/bounds:
active caller:
active runtime caller:
active asset/sprite/model name:
selector/factory result:
fallback path/value used:
runtime writer checked:
validation:
```

Missing source bounds, converted rect, final drawn rect, active caller, or active asset/sprite/model name is a FAIL when those values are relevant to the challenged visible behavior. On FAIL, stay read-only and return a runtime probe plan only.

## Repeated-Fix Flow

When the user says the result is still wrong:

1. Stop tuning constants.
2. Re-read the screenshot/target wording.
3. Re-run the Runtime Visible Output Hard Stop proof chain.
4. Run the Runtime Numeric Proof Gate before another patch.
5. Check duplicate names, inactive scene objects, cloned runtime objects, and parent-chain ambiguity.
6. Search runtime writers and refresh paths.
7. Check whether the edited script is in the compiled assembly.
8. Check whether scene/prefab overrides also need updating.
9. Patch only after numeric proof explains the mismatch.
10. Validate with Game view/device/screenshot proof when possible.
