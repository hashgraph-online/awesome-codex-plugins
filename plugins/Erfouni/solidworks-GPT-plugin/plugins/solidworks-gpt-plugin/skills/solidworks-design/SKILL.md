---
name: solidworks-design
description: Plan, create, modify, inspect, repair, validate, save, and export SolidWorks parts, assemblies, and drawings. Use for any request involving SolidWorks CAD geometry, engineering drawings or reference images, materials, fits, tolerances, fasteners, mates, mass properties, or STEP/IGES/STL/PDF deliverables. Orchestrates the mandatory knowledge-base pre-start, catalog lookup, deterministic validation, and consent-based session reporting workflow.
---

# SolidWorks Design

Treat this skill as the entry point for every SolidWorks task. Use the available
SolidWorks automation surface for CAD operations; this plugin supplies the
engineering and knowledge workflow rather than a SolidWorks installation.

## Start the task

1. On the first SolidWorks request in the current Codex task, resolve the
   plugin root from this file and run:

   ```text
   python <plugin-root>/scripts/sw_session.py start
   ```

   Echo the returned UUID as `SESSION_ID` in working context. Run this command
   only once per Codex task and never replace the ID mid-task.
2. Establish the design goal, units, geometry-driving dimensions, material,
   tolerances or fits, manufacturing process, and deliverables.
3. Ask one concise question when missing data changes geometry, safety, fit, or
   the requested output. Do not guess engineering values. If the user
   explicitly delegates a non-geometry default, apply the active KB convention
   and disclose it.
4. Invoke `$sw-pre-start`, then `$sw-kb-api`, in that exact order before
   opening SolidWorks, generating CAD code, or calling a SolidWorks API.

## Plan before editing

Write a compact implementation plan that identifies:

- files and document types to create;
- datums, origins, coordinate systems, and reference geometry;
- ordered sketches and features with named driving dimensions;
- sketch relations and the fully-defined condition;
- material, tolerance, fit, fastener, clearance, and manufacturing decisions;
- assembly mates and intended remaining degrees of freedom;
- measurable acceptance criteria and required exports.

Query the KB standards tables when each material, fit, tolerance, fastener, or
clearance decision is made. Never substitute remembered nominal values when a
standards lookup is available.

## Build and verify parts

Create each part separately. For every part:

1. Use metric model units unless the user explicitly overrides them.
2. Build parametric, fully-defined sketches with stable references and named
   dimensions.
3. Rebuild after meaningful feature groups and inspect returned API values.
4. Before each SolidWorks API method, check the part-specific and global known
   errors loaded by `$sw-kb-api`; apply a resolved prevention first.
5. Assign the verified material and record its source and units.
6. Inspect rebuild status, document errors, feature tree, mass properties,
   bounding box, and a representative image.
7. Use deterministic document validation as pass/fail. Treat screenshots as
   visual evidence only.
8. Save the native part, export requested formats, then close it before
   starting an assembly.

Do not report success when rebuild or document validation has not passed.

## Build and verify assemblies

Create an assembly only after all component parts are saved and closed.
Insert components from explicit saved paths, add mates in a stable order, and
verify mate status, interference or clearance requirements, component count,
and remaining degrees of freedom. Rebuild and run deterministic document
validation before saving or exporting.

## Drawings and exports

Create requested drawings from the validated final model. Include specified
views, dimensions, tolerances, fits, GD&T, material notes, and title-block
metadata. Export only after final design-rule validation passes.

Prefer project folders named `work/` for native working files and `exports/`
for deliverables unless the user explicitly chooses other paths.

## Finish the task

1. Invoke `$sw-pre-start` Phase 6 with final parameters and resolve every
   `fail`. Record advisories.
2. Report native files and exports, explicit units, measured mass and bounding
   box, validation result, errors, and limitations.
3. Track the corrected feature sequence, every final code artifact, repeatable
   failures and resolutions, and non-obvious lessons.
4. After delivering the CAD result, invoke `$sw-session-reporter`. Do not skip
   reporting merely because the KB was offline during the build.
