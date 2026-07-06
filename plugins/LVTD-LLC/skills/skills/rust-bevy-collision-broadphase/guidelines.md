# Rust Bevy Collision Broadphase Guidelines

Use this router to load the smallest useful file set.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Replacing nested collision loops | `references/broadphase-patterns.md`, `workflows/optimize-collision.md` |
| Designing new collider components | `references/broadphase-patterns.md` |
| Reviewing collision events and response | `references/broadphase-patterns.md` |
| Benchmarking a collision bottleneck | `workflows/optimize-collision.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Frame time grows with every obstacle or projectile | `workflows/optimize-collision.md` |
| Collision response depends on query order | `references/broadphase-patterns.md` |
| Despawned entities appear in collision output | `references/broadphase-patterns.md` |
| Fast entities pass through thin obstacles | `references/broadphase-patterns.md` |

## Decision Tree

```text
Need collision work?
|
+-- Tiny entity count and not hot? -> keep brute force, add tests
+-- Uniform grid or tile world? -> consider spatial hash
+-- Clustered or uneven object distribution? -> consider quad tree
+-- Fast movers? -> add swept bounds or substeps before tuning indexes
+-- Response is tangled with detection? -> emit events and split systems
```

## File Index

| File | Purpose |
|------|---------|
| `references/broadphase-patterns.md` | Concepts, rules, patterns, and examples |
| `workflows/optimize-collision.md` | Step-by-step optimization process |
