---
name: game-sdf-and-field-modeling
description: Model game shapes, volumes, influence, procedural objects, and effects with signed distance functions, implicit functions, scalar fields, vector fields, and deformation fields. Use when building SDF primitives, field composition, raymarching inputs, organic procedural shapes, offsets, Booleans, deformation, or field-driven gameplay.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game SDF And Field Modeling
  category: Game Development
  tags: game-dev,game-geometry,sdf,fields,procedural-generation
---

# Game SDF And Field Modeling

Use this skill when a game system is better represented as a function over space
than as explicit triangles. Treat fields as gameplay and content tools, not only
rendering tricks.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapters 2, 8, 10, and 11. Additional sources:
NVIDIA GPU Gems 3 chapter 34, "Signed Distance Fields Using Single-Pass GPU
Scan Conversion of Tetrahedra"
(https://developer.nvidia.com/gpugems/gpugems3/part-v-physics-simulation/chapter-34-signed-distance-fields-using-single-pass-gpu),
and "Designing with Distance Fields" by Perry, Frisken, and Jones
(https://merl.com/publications/TR2006-054).

## Core Workflow

1. Define the field signature: point in which space goes in, what value comes
   out, and what sign convention means.
2. Choose whether the function must be a true distance field or only a sign-like
   implicit function.
3. Build primitive fields first, then compose with transforms, Booleans,
   blends, offsets, or deformation fields.
4. Transform the input point by the inverse object transform. Do not rewrite the
   primitive for every translation, rotation, or scale.
5. Track when operations preserve or destroy true distance meaning.
6. Decide how the field becomes gameplay or renderable data: direct sampling,
   raymarching, mesh extraction, voxelization, particles, decals, or collision
   probes.
7. Add visual debugging: slices, isolines, gradient arrows, sample points, and
   sign colors.

## Field Types

- Scalar field: returns a number at each point. Use for terrain height,
  influence, heat, fog, danger, signed distance, or density.
- SDF: returns negative inside, zero on the boundary, positive outside, and
  magnitude as distance when it remains a true SDF.
- Vector field: returns a vector at each point. Use for wind, currents, steering,
  force fields, deformation, and flow.
- Deformation field: returns displacement vectors in the same space as the
  modeled object.
- Implicit surrogate: returns a sign-like value but not true distance. Useful,
  but unsafe for operations that require distance magnitude.

## SDF Operations

- Union: take the minimum of two fields.
- Intersection: take the maximum of two fields.
- Subtraction: intersect the first field with the negated second field.
- Dilation/erosion on a true SDF: add or subtract a constant according to the
  project's sign convention.
- Hollowing: convert a boundary band into a shell using absolute distance and
  shell width.
- Smooth blends: useful for organic shapes but may destroy exact distance
  semantics.

## Distance Validity Rules

- A true SDF can support reliable offsets and gradient-based movement.
- Boolean composition usually keeps the sign behavior but not exact distance
  everywhere.
- Metaballs, lemniscates, density functions, and many procedural formulas are
  implicit fields, not true SDFs.
- After distance validity is lost, reinitialize or recompute distance before
  algorithms that depend on exact distance.
- Gradients on noisy or sampled fields need filtering or robust finite
  differences.

## Game Use Cases

- Procedural rocks, caves, blobs, shields, zones, decals, and organic props.
- Destructible or editable volumes before conversion to mesh or voxels.
- Influence maps for AI, hazard fields, fog density, wind, water currents, and
  force fields.
- Cheap inside/outside tests for volumes where mesh topology is unreliable.

## Common Mistakes

- Treating every implicit function as a true SDF.
- Applying offsets after Booleans without checking distance validity.
- Recomputing transforms or expensive neighbor searches per sample in a hot
  path.
- Sampling a field at too low a resolution, then blaming the extraction
  algorithm.
- Shipping field logic without a slice or isoline debug view.
