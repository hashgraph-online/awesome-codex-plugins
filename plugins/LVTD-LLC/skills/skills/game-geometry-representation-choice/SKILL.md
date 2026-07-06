---
name: game-geometry-representation-choice
description: Choose the right geometric representation for game systems before implementing rendering, collision, procedural generation, editing, or conversion code. Use when deciding between meshes, SDFs, voxels, splines, parametric surfaces, fields, or hybrid geometry workflows for games.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Geometry Representation Choice
  category: Game Development
  tags: game-dev,game-geometry,geometry,representation,procedural-generation
---

# Game Geometry Representation Choice

Use this skill before writing geometry-heavy game code. Pick the representation
that makes the important operation simple, robust, and fast enough, then plan
conversion boundaries deliberately.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapters 2 and 10-12.

## Core Workflow

1. Name the operation first: render, collide, pick, offset, deform, Boolean,
   smooth motion, destruct terrain, generate props, edit geometry, or convert.
2. List the data the game already has and the data the game ultimately needs.
   Include textures, normals, animation bindings, gameplay tags, and LODs.
3. Pick the working representation where the core operation is cheapest and
   least fragile. Do not default to meshes just because rendering ends there.
4. Define conversion boundaries: input representation, working representation,
   output representation, resolution, tolerated error, and attribute transfer.
5. Add invariants and tests for the representation, not just the final visual.
6. Revisit the choice when the operation mix changes. A good rendering
   representation may be a poor editing or collision representation.

## Representation Guide

- Use triangle meshes for rendering, GPU pipelines, LODs, static level geometry,
  and approximating smooth surfaces when attribute data matters.
- Use SDFs or implicit fields for Boolean composition, offsets, hollowing,
  organic procedural forms, cheap inside/outside tests, and robust repair steps.
- Use voxels or image masks for destructible terrain, coarse occupancy,
  erosion/dilation, denoising, flood fill, gap checks, and reliable Boolean-like
  operations on a shared grid.
- Use splines or Bezier curves for player paths, camera rails, projectile trails,
  roads, rivers, UI curves, and animation controls where continuity matters.
- Use parametric surfaces when procedural objects come from a small number of
  parameters, such as surfaces of revolution, terrain patches, tubes, or rails.
- Use vector fields or deformation fields for smooth warps, influence maps,
  wind/current effects, procedural variation, and nonrigid deformation.
- Use hybrids when one representation owns interaction and another owns
  rendering, such as voxel sculpting with mesh LOD output.

## Decision Rules

- If the operation is Boolean or offset-like, prefer SDFs or voxels over triangle
  meshes unless exact mesh topology is required.
- If the operation needs exact texture, normal, skinning, or authoring data,
  preserve mesh attributes or plan how to regenerate them after conversion.
- If the system needs smooth paths, start with curves and parameterization, not
  with sampled points.
- If the game needs thousands of repeated spatial tests, choose a representation
  that supports indexing, locality, or precomputed coefficients.
- If memory dominates, prefer boundary data such as meshes or splines over full
  voxel volumes.
- If robustness dominates, prefer grid, SDF, or redundant fallback workflows over
  a single brittle mesh algorithm.

## Output Checklist

Return a short representation brief:

- Chosen working representation:
- Existing input representation:
- Required output representation:
- Operations made simpler:
- Operations made harder:
- Conversion steps:
- Error/resolution budget:
- Attribute preservation plan:
- Degenerate or failure cases:
- Minimal tests or debug views:

## Common Mistakes

- Rendering from meshes, then forcing every gameplay operation to run on the
  same mesh.
- Applying offsets or Booleans to arbitrary triangle meshes before considering
  SDF or voxel workflows.
- Converting representations without a plan for normals, UVs, materials,
  gameplay labels, collision layers, or LODs.
- Treating a sign-only implicit function as a true distance field after operations
  that destroyed distance meaning.
- Choosing a high-resolution grid without proving the memory and streaming
  model.
- Optimizing the algorithm implementation before choosing the representation
  that makes the algorithm unnecessary.
