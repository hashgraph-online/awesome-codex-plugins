# Visual Confirmation

Use this reference before front-end implementation.

## Required User Gate

Implementation may start only after the user approves exported images.

The image set must include:

- Desktop full-screen view.
- Mobile full-screen view.
- Component detail sheet.
- State matrix for each important component.

After images are exported, run `review_visual_evidence`. A checked box or `visualDesignApproved: true` in `00-stage.json` is not enough by itself.

## Visual Evidence Contract

Each visual handoff must include:

- design tool: Pencil or Figma
- current change id from `00-stage.json.latestChangeId`
- user approval record with approvedBy, approvedAt, and scope
- export category for every image
- component coverage for component-detail boards
- state coverage for state-matrix boards

Required board categories:

- `desktop`
- `mobile`
- `component-detail`
- `state-matrix`

## Required Component States

Show these states when applicable:

- default
- hover
- focus
- disabled
- loading
- empty
- error
- success
- mobile

## Pencil Process

1. Call `get_editor_state(include_schema: true)` before any other Pencil tool.
2. Use `batch_design` to create frames and component/state details.
3. Use `snapshot_layout` to check clipping, overlap, and spacing.
4. Use `export_nodes` or `get_screenshot` to create images for the user.
5. Ask for user approval and wait before coding.

## Figma Process

1. Load `figma-use` before any Figma write operation.
2. Load `figma-create-new-file` before creating a new Figma file.
3. Use `figma-generate-design` only when capturing an existing web page for the first time.
4. Search existing design system assets before recreating components.
5. Export or show the design images and wait for user approval before coding.

## Component Detail Sheet

For each important component, show:

- anatomy and subparts
- sizes
- variants
- icon and label placement
- spacing
- radius
- color roles
- focus ring
- disabled treatment
- loading treatment
- empty/error/success copy placement
