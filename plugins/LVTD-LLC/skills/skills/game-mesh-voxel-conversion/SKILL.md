---
name: game-mesh-voxel-conversion
description: Plan and implement conversions between game meshes, SDFs, voxels, images, contours, and smooth curves while preserving enough gameplay and rendering data. Use when repairing meshes, extracting meshes from fields, voxelizing geometry, contouring, denoising voxel data, generating LODs, or moving geometry between representations.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Mesh Voxel Conversion
  category: Game Development
  tags: game-dev,game-geometry,meshes,voxels,conversion
---

# Game Mesh Voxel Conversion

Use this skill when the game should do an operation in one representation and
ship or render the result in another. Make conversion an explicit workflow with
resolution, error, and attribute rules.

Primary source: Geometry for Programmers by Oleksandr Kaleniuk
(https://www.manning.com/books/geometry-for-programmers), transformed and
paraphrased, especially chapters 10-12. Additional sources: "Marching Cubes"
by Lorensen and Cline (https://dl.acm.org/doi/10.1145/37402.37422), and
"Dual Contouring of Hermite Data" by Ju, Losasso, Schaefer, and Warren
(https://dl.acm.org/doi/10.1145/566654.566586).

## Core Workflow

1. State the source representation and target representation.
2. State why conversion is needed: repair, render, collide, edit, Boolean,
   offset, destruct, simplify, smooth, or export.
3. Choose the working grid or sampling resolution from visible error, gameplay
   tolerance, memory, and streaming constraints.
4. Preserve or regenerate attributes deliberately: normals, UVs, materials,
   skinning, collision layers, gameplay tags, and LOD metadata.
5. Pick the extraction algorithm based on shape needs: marching cubes/squares
   for smooth organic fields, dual contouring for sharper features, or custom
   contouring when curve output matters.
6. Validate geometry and gameplay behavior after conversion.

## Conversion Patterns

### Mesh To SDF To Mesh

Use when mesh operations are brittle but approximate output is acceptable:

- Fix holes, cracks, folds, or inverted triangles.
- Hollow or offset a model approximately.
- Merge or subtract complex shapes.
- Generate clean collision or render meshes from an implicit design step.

Expect loss of exact topology and possible loss of original UVs/materials.

### Field To Mesh

Use marching cubes/squares when:

- The field is smooth and organic.
- Corners do not need to be preserved exactly.
- Linear interpolation on grid edges is good enough.

Use dual contouring when:

- Sharp features matter.
- Hermite data, gradients, or normals are available.
- One vertex per active cell is a useful output shape.

### Voxel Operations

Use voxels or image masks when robustness matters more than exact surface detail:

- Dilation grows filled regions.
- Erosion removes boundary material.
- Erode then dilate to remove small noise.
- Dilate then erode to close thin cracks.
- Boolean union, intersection, and subtraction are simple on aligned grids.
- Connected-component labeling counts separate pieces.

## Resolution And Error Rules

- Every grid conversion has an error budget. Name it before implementation.
- More resolution improves visual detail but increases memory and processing
  cost quickly, especially in 3D.
- Anisotropic voxels or nonuniform world scale must be accounted for in
  distance and neighbor rules.
- Store grid origin, cell size, axis order, and sign convention with the data.
- Use multiresolution or chunking when worlds are large.

## Attribute Preservation Checklist

- Normals: recompute, transfer, or preserve?
- UVs: project, bake, discard, or regenerate?
- Materials: transfer by nearest surface, volume labels, or procedural rules?
- Gameplay tags: transfer by source primitive, volume region, or query?
- LODs: generate now or later?
- Collision: same mesh as rendering, simplified mesh, SDF, or voxel proxy?

## Common Mistakes

- Converting only positions and discovering later that materials or gameplay
  labels were the real asset.
- Using marching cubes for shapes whose main value is sharp edges.
- Treating a voxel grid as exact geometry instead of sampled occupancy.
- Running a mesh repair workflow with no before/after validity tests.
- Picking resolution from screenshots rather than gameplay tolerance and memory.
