# Rust Bevy Procedural World Builder Guidelines

Use this router before changing generated-world code.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Designing generated map data | `references/procedural-world-patterns.md` |
| Adding a level or base generator | `workflows/build-procedural-world.md` |
| Checking reachability or spawn rules | `references/procedural-world-patterns.md` |
| Moving generation to a background task | `references/procedural-world-patterns.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Generated maps can trap the player | `references/procedural-world-patterns.md` |
| Generation stutters gameplay | `workflows/build-procedural-world.md` |
| Bevy world is mutated from background code | `references/procedural-world-patterns.md` |
| Generated entities cannot be reproduced | `references/procedural-world-patterns.md` |

## Decision Tree

```text
Need procedural generation?
|
+-- Need reproducibility? -> seed the generator and log parameters
+-- Need gameplay constraints? -> validate generated data before spawning
+-- Need performance? -> profile data generation vs entity/material spawning
+-- Need background work? -> send data back to main thread, not Commands
+-- Need streaming? -> chunk data and materialize incrementally
```

## File Index

| File | Purpose |
|------|---------|
| `references/procedural-world-patterns.md` | Generation data, validation, and threading rules |
| `workflows/build-procedural-world.md` | Step-by-step generated world process |
