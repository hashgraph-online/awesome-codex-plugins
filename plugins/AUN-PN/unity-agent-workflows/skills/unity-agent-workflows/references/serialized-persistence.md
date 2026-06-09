# Serialized Persistence

Use when the fix touches serialized scene objects, prefab assets, prefab instances, variants, component fields, object references, or editor tooling.

## Serialized Scene And Prefab Persistence

Before closeout, prove:

```text
intended target
-> scene instance / prefab asset / prefab instance / prefab variant
-> serialized field or component changed
-> dirty state or override recorded
-> saved asset or scene file updated
-> runtime path still reads that serialized value
```

- Distinguish scene instance, prefab asset, prefab instance override, nested prefab, prefab variant, and Prefab Mode before editing.
- Use the project's existing editor tooling when it exists; otherwise prefer Unity editor APIs such as `SerializedObject`, `Undo.RecordObject`, `PrefabUtility`, `EditorUtility.SetDirty`, and `EditorSceneManager.MarkSceneDirty`.
- For prefab instances, record the intended override with `PrefabUtility.RecordPrefabInstancePropertyModifications(...)` when editor code changes serialized properties.
- For scene edits, confirm the correct scene is dirty and saved. Multi-scene setups must identify which loaded scene owns the object.
- For prefab asset edits, confirm whether the change belongs on the source prefab, a variant, or a specific scene instance override.
- Preserve `.meta` GUIDs during moves or asset replacement unless the user explicitly approves reference-breaking regeneration.
- After saving, re-open or re-query the object when possible and confirm the serialized value did not revert through import, `OnValidate`, setup scripts, or Play Mode initialization.
- Serialized persistence is not runtime proof. If a runtime builder, presenter, animation, or service rewrites the value, patch that runtime owner too.
