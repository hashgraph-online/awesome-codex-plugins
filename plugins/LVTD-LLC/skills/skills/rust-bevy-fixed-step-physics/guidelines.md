# Rust Bevy Fixed Step Physics Guidelines

Use this router before changing simulation or movement code.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Fixing frame-rate-dependent movement | `workflows/stabilize-physics.md` |
| Adding velocity or acceleration components | `references/fixed-step-patterns.md` |
| Handling fast movement through obstacles | `references/fixed-step-patterns.md` |
| Smoothing fixed-step visual motion | `references/fixed-step-patterns.md`, `workflows/stabilize-physics.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Player moves faster on high refresh displays | `workflows/stabilize-physics.md` |
| Fast movers pass through obstacles | `references/fixed-step-patterns.md` |
| Animation code mutates authoritative physics position | `references/fixed-step-patterns.md` |
| Fixed timestep feels visually jittery | `references/fixed-step-patterns.md` |

## Decision Tree

```text
Movement issue?
|
+-- Changes with FPS? -> fixed-step simulation
+-- Misses collisions? -> swept movement or substeps
+-- Looks choppy but sim is stable? -> interpolate/tween visuals
+-- Input feels delayed? -> sample input in Update, consume in FixedUpdate
+-- Animation changes physics transform? -> split visual child from authority
```

## File Index

| File | Purpose |
|------|---------|
| `references/fixed-step-patterns.md` | Simulation, prediction, and smoothing patterns |
| `workflows/stabilize-physics.md` | Step-by-step stabilization process |
