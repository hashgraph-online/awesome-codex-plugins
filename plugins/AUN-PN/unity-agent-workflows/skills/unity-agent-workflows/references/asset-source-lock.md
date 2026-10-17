# Asset Source Lock

Use before changing directional sprites, model poses, animation frames, sprite/model selectors, visual factories, fallback visuals, generator IDs, source asset IDs, or exact asset/surface locks.

## Asset Variant Availability Gate

Before editing, prove:

```text
requested visual state:
expected variants:
actual asset paths/names found:
factory/selector lookup path:
active runtime asset/sprite/model name:
fallback when variant missing:
callers using the selector/factory:
surface-local fallback possible: yes/no
```

If variants are missing, do not assume a code patch will make a visible change. Add a surface-local fallback only after caller blast-radius proof, generate/obtain the missing asset through the approved asset workflow, or stop and ask.

## Source Asset / ID Lock

When the user names a generator ID, asset ID, sprite sheet, prefab, scene, screen, runtime object, or exact surface, that value is a hard scope lock.

- Do not replace it with a nearby asset/source.
- Do not generate from another source ID.
- Do not apply the new asset path to global gameplay/runtime factories unless the requested surface is proven as the only caller.
- If the source is missing, inaccessible, or incompatible, stop and ask before substituting.
- Closeout must include the exact source ID/path/name used and where it is called at runtime.
