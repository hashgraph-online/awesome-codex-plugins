# Multi-Surface Visible Behavior

Use when the same visible behavior must work across multiple scenes, UI previews, transitions, gameplay runtime, prefabs, or surfaces.

Trigger examples:

- "also make it happen after the scene transition"
- "menu and gameplay should both show the same pose"
- "preview works but runtime does not"
- "same model/animation/sprite behavior across menu and runtime"

## Multi-Surface Visible Behavior Lock

Before editing any surface, prove all requested surfaces:

```text
requested visible behavior:
surface list:
surface:
visible object:
runtime GameObject/component:
owner controller/presenter:
active caller:
writer/update method:
asset/sprite/model/factory dependency:
active asset/sprite/model name:
variant paths/names checked:
fallback behavior if variant missing:
validation method:
```

Do not patch only the first proven surface when another requested surface remains unproven. If one surface is only a preview/transition and another is gameplay/runtime, prove both or return the missing proof plan.
