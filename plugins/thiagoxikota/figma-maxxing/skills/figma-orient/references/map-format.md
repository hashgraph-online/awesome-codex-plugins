# map format

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Canonical screens vs scratchpad

Device-sized frames on canonical pages are real screens. A page is not canonical when its name contains "WIP", "Archive" or "Sandbox" (match case-insensitive: real page names often carry a prefix or a year), or when the map's `Project canon` marks it as non-canonical. The device sizes:

| Device | Frame sizes |
| --- | --- |
| Mobile | 375x667, 390x844, 393x852 |
| Tablet | 768x1024, 820x1180 |
| Desktop | 1440x900, 1920x1080 |

Frame dimensions are heuristics, not proof of draft status. Use project docs, page purpose and live context; record uncertainty rather than downgrading every off-size canonical frame.

## Persistence (the reason this skill exists)

Write the map to a `figma-map.md` file kept in the project. The default path is `docs/figma-map.md`. The map holds the file key and node ids, so check first whether the repository is public: if it is and the Figma file is not, add the map to `.gitignore` or keep it in the agent's memory system. A runtime memory location is optional only when that runtime’s contract and owner authorization permit it. Never inherit a Claude/Codex memory path from this skill. Private maps can use an authorized task-local ignored location without creating runtime memory.

The body of the map holds: the file type, the pages with their purpose, the canonical screens with their node ids, the design system source, the WIP zones and the date.

If the map ALREADY exists, CONSOLIDATE it. Never duplicate it: update the section of the file you just oriented on, or add a section for a file that is not in the map yet. One map per project, one section per Figma file.

Future session: start from the saved map (summarize the file from it instead of walking it again), then run `figma_get_design_changes` to pick up only the delta. An empty result is not proof that the file is unchanged since `Last oriented`: read the tool's own description for what it captures and since when, and confirm that a node id taken from the map still resolves before acting on it. When the delta cannot be trusted, walk again only the pages you are about to act on.

The other skills in this set refer to the same map, and project-specific rules (layer naming, required states, locale, anti-patterns, Code Connect status) are recorded in it. Leave the sections you did not touch as they are.

### Map template

Replace every placeholder. Drop a row or a section that does not apply instead of leaving it empty. Record only what you actually read. Fill `Project canon` only from the project's own docs or from what the user states; never infer it from the canvas, and drop the section when neither source exists.

```markdown
# Figma map

One section per Figma file. Written and consolidated by the figma-orient skill.

## <file name>

- File key: `<fileKey>` (branch: none | `<branchKey>`)
- File type: Design | FigJam | Slides | Make
- Last oriented: YYYY-MM-DD
- Scope walked: whole file | page "<page name>" only (read truncated)

### Pages

| Page | Node id | Purpose | Status |
| --- | --- | --- | --- |
| <page name> | 0:1 | <what lives on this page> | canonical |
| <page name> | 12:34 | <what lives on this page> | WIP |
| <page name> | 56:78 | <what lives on this page> | archive |

### Canonical screens

| Screen | Node id | Page | Size |
| --- | --- | --- | --- |
| <screen name> | 123:456 | <page name> | 390x844 |
| <screen name> | 123:789 | <page name> | 1440x900 |

### Design system source

- Components: local to this file | library "<library name>"
- Variables: <collections and modes>
- Styles: <text and color styles, if any>

### WIP zones

- <page or section name> (`234:567`): <why it is not canonical>

### Flags

- <view-only file, truncated read, off-size frames treated as drafts, anything a later write must know>

### Project canon

- <project-specific rules that override the universal rules of the `figma-canon` skill: layer naming, required states, locale, anti-patterns, Code Connect status. Source: the project's docs or the user, never the canvas.>
```
