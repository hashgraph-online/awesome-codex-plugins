---
name: game-vector-math-primitives
description: Apply vector math primitives for game rendering, collision, orientation, lighting, steering, and geometry predicates. Use when working with dot products, cross products, triple products, normals, projections, signed areas, signed volumes, facing checks, or vector normalization.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Vector Math Primitives
  category: Game Development
  tags: game-dev,game-geometry,vectors,rendering,collision
---

# Game Vector Math Primitives

Use this skill when game code depends on vector operations whose geometric
meaning matters. Prefer clear primitives and named intent over opaque formula
paste.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapters 2 and 9.

## Core Workflow

1. Identify the geometric question: angle, projection, side, area, normal,
   volume, distance, facing, or interpolation.
2. Choose the primitive that answers that question directly.
3. Check the input assumptions: dimensionality, coordinate space, units,
   handedness, normalization, and zero-length vectors.
4. Preserve sign when orientation or sidedness matters. Discard sign only when
   the caller truly needs magnitude.
5. Name intermediate values by meaning: `normal`, `signed_area2`,
   `light_factor`, `plane_distance`, `facing`, `projection_t`.
6. Add tests that exercise orientation, reversed winding, orthogonal vectors,
   parallel vectors, and zero-length inputs.

## Primitive Guide

### Dot Product

Use dot products for:

- Projection onto a direction.
- Angle/facing tests.
- Lambert-style lighting coefficients.
- Distance along a ray or segment.
- Checking orthogonality: dot equals zero under the numeric policy.

If both vectors are normalized, the dot product is the cosine of the angle
between them. Clamp before inverse cosine if a display angle is needed.

### Cross Product And 2D Cross Scalar

Use cross products for:

- Surface normals from two triangle edges.
- Signed 2D orientation tests.
- Twice the signed area of a 2D triangle.
- Detecting parallel vectors through near-zero magnitude.
- Building tangent frames with a known handedness.

For 2D, use the scalar `a.x * b.y - a.y * b.x` instead of constructing fake 3D
vectors unless the codebase already uses a 3D type.

### Triple Product

Use the scalar triple product for:

- Signed volume.
- Point side relative to an oriented plane.
- Point-to-plane distance when divided by the plane normal length.
- Tetrahedron orientation and containment-style predicates.

Keep the sign when side matters. Take absolute value only for unsigned volume or
distance.

## Guardrails

- Never normalize before checking vector length.
- Distinguish a direction vector from a point vector in naming and APIs.
- Keep normals in the same space as the vectors they are compared with.
- Recompute or transform normals correctly after nonuniform scale.
- Decide whether clockwise or counterclockwise winding is canonical.
- Use squared length when comparing distances and no square root is needed.
- Avoid inverse trigonometric functions in hot paths unless a real angle is
  required. Dot thresholds are usually cheaper.

## Common Mistakes

- Treating every vector as normalized because examples used unit vectors.
- Losing useful sign information by taking absolute values too early.
- Mixing coordinate spaces in one dot or cross operation.
- Using angle calculations where a dot-product threshold would be simpler.
- Flipping triangle winding without updating normals, culling, or orientation
  predicates.
