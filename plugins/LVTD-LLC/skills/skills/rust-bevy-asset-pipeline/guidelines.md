# Rust Bevy Asset Pipeline Guidelines

Use this router before loading reference files.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Creating an asset catalog | `references/asset-pipeline-patterns.md` |
| Adding loading states | `references/asset-pipeline-patterns.md`, `workflows/build-asset-pipeline.md` |
| Replacing hard-coded paths | `workflows/build-asset-pipeline.md` |
| Preparing packaged builds | `references/asset-pipeline-patterns.md`, `workflows/build-asset-pipeline.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Gameplay system calls `asset_server.load` repeatedly | `references/asset-pipeline-patterns.md` |
| Asset path typo appears only at runtime | `workflows/build-asset-pipeline.md` |
| Loading screen advances before handles are ready | `references/asset-pipeline-patterns.md` |
| Release build cannot find resources | `workflows/build-asset-pipeline.md` |

## Decision Tree

```text
Need asset work?
|
+-- Paths scattered in systems? -> create typed catalog
+-- Loading race? -> add loading state and readiness gate
+-- Sprite animations? -> catalog atlas handles and frame metadata
+-- Audio handles cloned everywhere? -> store in resource and clone handles
+-- Packaged build fails? -> verify runtime asset layout
```

## File Index

| File | Purpose |
|------|---------|
| `references/asset-pipeline-patterns.md` | Catalog, loading, and packaging patterns |
| `workflows/build-asset-pipeline.md` | Step-by-step asset pipeline process |
