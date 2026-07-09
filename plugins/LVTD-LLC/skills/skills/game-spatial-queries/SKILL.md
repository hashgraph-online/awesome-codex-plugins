---
name: game-spatial-queries
description: Design and review game spatial query code for raycasts, picking, collision predicates, containment tests, orientation tests, and point/line/plane distances. Use when implementing or debugging ray-triangle hits, point-in-triangle checks, barycentric constraints, signed distance tests, or geometry predicates.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Spatial Queries
  category: Game Development
  tags: game-dev,game-geometry,collision,raycasting,spatial-queries
---

# Game Spatial Queries

Use this skill to turn game picking, collision, containment, and distance
questions into small geometric systems with explicit constraints and failure
cases.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapters 3, 4, and 9. Additional source: "Fast,
Minimum Storage Ray-Triangle Intersection" by Tomas Moller and Ben Trumbore
(https://dl.acm.org/doi/10.1145/1198555.1198746).

## Core Workflow

1. State the query as a predicate or measured value: hit/miss, inside/outside,
   closest distance, signed side, intersection point, or parameter value.
2. Move into the simplest local basis when possible. Triangle, segment, plane,
   and object-local bases often reduce the query to bounds checks.
3. Derive parameters first, then apply constraints. Keep constraints visible in
   code instead of burying them in one large expression.
4. Identify denominator, orientation, or length values that signal degeneracy.
5. Choose a numeric policy: exact integer predicate, scale-aware epsilon,
   inclusive boundary, exclusive boundary, or conservative fallback.
6. Test hit, miss, boundary, parallel, degenerate, and near-degenerate cases.
7. Add a debug visualization when the query affects gameplay feel.

## Query Patterns

### Ray Against Triangle

Model the ray as `R = P + t*d` with `t >= 0`. Model triangle points as
`S = A + u*AB + v*AC` with `u >= 0`, `v >= 0`, and `u + v <= 1`.

Solve `R = S`, then:

- Reject when the shared denominator is zero or too small for the numeric policy.
- Reject when `t < 0`.
- Reject when `u < 0`, `v < 0`, or `u + v > 1`.
- Return hit distance `t`, barycentric-like parameters `u` and `v`, and the hit
  point when needed.

### Point In Triangle

Prefer one of these approaches:

- Transform the triangle to its local basis and check `0 <= u`, `0 <= v`,
  `u + v <= 1`.
- Use consistent edge orientation signs from 2D cross products.
- Use barycentric coordinates when the caller needs interpolation weights too.

Decide whether points on edges count as inside. Tests must cover both the chosen
edge policy and reversed triangle winding.

### Signed Point To Plane

Build a plane normal from two nonparallel edges. Dot the normalized normal with
the vector from any plane point to the query point. Keep the sign when side
matters; take absolute value only for unsigned distance.

### Segment And Closest-Point Queries

Project onto the segment direction, clamp the parameter to `[0, 1]`, then measure
distance to the clamped point. Reject or special-case zero-length segments before
normalization.

## Degenerate Geometry Policy

- Zero-length vectors must not be normalized.
- Degenerate triangles must not create unstable bases or normals.
- Parallel ray/plane cases need a deliberate answer: no hit, coplanar handling,
  or fallback query.
- Very small denominators need a scale-aware policy. A fixed epsilon is often
  wrong across different world scales.
- Boundary inclusion must match gameplay: selection tools often want inclusive
  checks; collision separation often wants conservative checks.

## Implementation Checklist

- Function name states geometry and boundary policy.
- Inputs document coordinate space and units.
- Winding assumptions are explicit.
- Denominator and zero-length cases are handled before division.
- Return type exposes enough detail for the caller: bool, distance, hit point,
  normal, barycentric weights, or rejection reason.
- Tests include normal case, miss case, edge/vertex case, reversed winding,
  parallel case, degenerate case, and large/small scale case.

## Common Mistakes

- Computing a global-space query when object-local coordinates make it trivial.
- Returning only `bool` from a query that later needs hit distance or normal.
- Comparing floats to zero with no policy.
- Forgetting that normals and barycentric coordinates depend on winding.
- Treating "not hit" and "invalid input geometry" as the same debugging signal.
