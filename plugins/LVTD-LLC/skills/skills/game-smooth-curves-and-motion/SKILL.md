---
name: game-smooth-curves-and-motion
description: Design smooth game motion with splines, Bezier curves, interpolation, derivative continuity, path parameterization, and speed control. Use when implementing camera rails, waypoint paths, vehicle routes, projectile trails, animation curves, roads, rivers, or any motion/path system that must feel smooth.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Smooth Curves And Motion
  category: Game Development
  tags: game-dev,game-geometry,splines,bezier,motion
---

# Game Smooth Curves And Motion

Use this skill to design path and curve systems where continuity, control, and
game feel matter more than exact mathematical purity.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapters 5-7. Additional source: A Primer on Bezier
Curves by Pomax (https://pomax.github.io/bezierinfo/).

## Core Workflow

1. Identify what must be smooth: position, tangent direction, speed, curvature,
   camera orientation, banking, or animation value.
2. Choose the curve family that gives the needed controls with the least state:
   linear segments, cubic Hermite, Catmull-Rom, Bezier, B-spline, NURBS, or a
   custom polynomial piece.
3. Define continuity targets:
   - C0: pieces meet at positions.
   - C1: tangents match for visually smooth direction.
   - C2: curvature changes smoothly.
4. Decide parameterization: uniform `t`, chord length, centripetal, explicit
   timing, or arc-length lookup.
5. Separate authoring controls from runtime samples. Designers may edit points
   and handles; the game may use baked lookup tables.
6. Test extreme control points, sharp turns, closed loops, repeated points, and
   speed variation.

## Curve Selection

- Use linear segments for grid motion, debug paths, and intentionally sharp
  routes.
- Use cubic Hermite when you know endpoint positions and tangent vectors.
- Use Bezier curves when control handles are the natural authoring interface.
- Use Catmull-Rom-style splines when paths should pass through waypoints with
  minimal handle authoring.
- Use B-splines or NURBS when many control points, high continuity, or exact
  conic sections matter.
- Avoid one high-degree global polynomial through many points. Split into
  pieces to avoid oscillation and poor local control.

## Motion Rules

- Smooth position does not imply smooth speed. Check derivative length along
  the path.
- Constant `t` increments rarely produce constant world-space speed.
- For nearly constant speed, precompute an arc-length table and map distance
  traveled back to curve parameter.
- Tangent length affects both speed and curve shape in Hermite-like systems.
- Normalize tangent direction only when speed should be controlled separately.
- Keep gameplay collision separate from visual smoothing when curves are only
  a presentation layer.

## Implementation Checklist

- Curve type and continuity target are documented.
- Parameter range and units are explicit.
- Closed paths handle first/last continuity deliberately.
- Runtime evaluation is bounded and allocation-free in hot paths.
- Baked samples include position, tangent, optional normal/binormal, and
  cumulative distance when needed.
- Debug view shows control points, handles, samples, tangents, and speed heat.

## Common Mistakes

- Using interpolation that passes through every point when approximation would
  be smoother and more stable.
- Assuming Bezier handles are points on the curve.
- Letting repeated or near-repeated points create undefined tangents.
- Moving a camera at constant parameter speed and calling the result constant
  motion.
- Adding more control points to fix a curve that needs a different
  parameterization or continuity target.
