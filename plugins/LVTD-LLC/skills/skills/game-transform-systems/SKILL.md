---
name: game-transform-systems
description: Design and debug game transform systems, coordinate spaces, local/world/view/projection matrices, homogeneous coordinates, camera constraints, and inverse transforms. Use when implementing object transforms, camera math, parent-child transforms, projection/unprojection, or coordinate-space conversions.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Transform Systems
  category: Game Development
  tags: game-dev,game-geometry,transforms,cameras,coordinate-systems
---

# Game Transform Systems

Use this skill to make transform code explicit, composable, testable, and
consistent across gameplay, rendering, physics, and tools.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapter 4. Additional source: Khronos glTF 2.0
specification transform and coordinate-system conventions
(https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).

## Core Workflow

1. List every coordinate space involved: model, local, parent, world, view,
   clip, screen, texture, grid, or field space.
2. Define conventions once: handedness, up axis, units, row/column vectors,
   matrix memory layout, multiplication order, angle units, and quaternion
   order.
3. Name transforms by direction, such as `local_to_world` and `world_to_view`.
4. Compose transforms in one place and cache composed matrices when reused.
5. Use inverse transforms to move queries into simpler spaces, especially for
   picking, SDFs, fields, and object-local collision.
6. Keep camera construction explicit: position, target or forward vector, up
   vector, field of view, aspect ratio, near/far planes.
7. Verify with round-trip tests and debug axes before tuning gameplay behavior.

## Design Rules

- Treat transforms as first-class data, not hidden side effects in helper
  methods.
- Prefer one canonical transform chain for rendering and gameplay. Add adapters
  at engine or asset boundaries.
- Use homogeneous coordinates when translation, projection, and matrix
  composition must live in one pipeline.
- Use affine transforms for ordinary rotation, translation, scale, and shear.
- Use projective transforms when perspective, projection, or planar warping is
  part of the problem.
- Apply the inverse transform to an SDF or field input instead of rewriting the
  field's formula for every object transform.
- Transform normals with the inverse transpose when nonuniform scale or shear
  is possible.

## Camera And Projection Checks

- A camera needs enough constraints to define orientation. A position and target
  still leave roll ambiguous without an up/right/down vector or equivalent.
- Near and far planes should fit the playable range; sloppy values harm depth
  precision.
- Projection and unprojection should be tested with known points at screen
  center, viewport corners, near plane, and far plane.
- Screen-space y direction and pixel-center conventions must be documented for
  picking and UI/game interaction.

## Transform Debug Checklist

- Draw local axes for selected objects.
- Draw camera frustum and near/far planes.
- Log transform direction in variable names.
- Assert matrices are finite before submitting to rendering or physics.
- Test identity, translation-only, rotation-only, scale-only, parent-child, and
  inverse round trips.
- Test nonuniform scale if normals, collision, or child transforms are affected.

## Common Mistakes

- Mixing row-major memory layout with row-vector math assumptions.
- Multiplying transforms in a plausible but wrong order.
- Recomputing inverse matrices inside tight per-point loops.
- Forgetting that `w = 0` represents a direction in homogeneous coordinates,
  while `w = 1` represents a point.
- Applying object transforms to an SDF output instead of inverse-transforming
  the query point.
- Fixing a camera roll bug by changing asset orientation instead of camera
  constraints.
