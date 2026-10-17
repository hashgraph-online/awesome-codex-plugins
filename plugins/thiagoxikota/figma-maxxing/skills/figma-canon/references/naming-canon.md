# Naming canon

Load before creating or renaming any layer, frame, component or section. Semantic naming for Figma: components in PascalCase with slash hierarchy, layers in kebab-case with a middle-dot state suffix, frames as `NN-name[/state]`, the atomic rule for variant axis renames, human-authorship rules for team-visible names, and the audit-before-rename rule. Project-specific canon defers to the project map.

## Components: PascalCase + slash hierarchy

```
Button/Primary/Default
Button/Primary/Hover
Button/Secondary/Default
Card/Elevated/Light
Card/Elevated/Dark
Input/Text/Default
Input/Text/Focus
Input/Text/Error
Icon/Alert
Icon/Profile
Icon/Close
```

- Slash creates folder hierarchy in Figma's component panel.
- PascalCase identifies a component (not a layer).
- All variants in a set must have the same number of slashes.

## Variant axes: Title Case property names + values

When using Figma's Variants feature:

- Property names: `Type`, `Size`, `State`, `Variant`, `Theme`, `Direction` (Title Case)
- Property values: `Small`, `Medium`, `Large`, `Default`, `Hover`, `Disabled`, `Light`, `Dark` (Title Case)
- Booleans: property name `hasIcon`, `isDisabled`, `showLabel`; values `True` / `False`

Common axis order: `Type > State > Size > Boolean`.

WRONG: `state=hover` (lowercase name + lowercase value).
RIGHT: `State=Hover`.

### When to split a component set

Signals that a component set has outgrown a single component and should be fragmented into sub-components:

- **5+ variant axes** OR **>32 total variants**: Figma's UI starts degrading and Dev Mode codegen becomes ambiguous.
- **Semantic divergence**: axes that do not combine logically (e.g., a `Loading` state on a `Card/Type=Promo` does not mean the same as `Loading` on `Card/Type=Empty`).
- **Code Connect mapping ambiguity**: when a single Figma variant could map to two different React components (e.g., `Button + IconButton` if `hasIcon=true` triggers a different layout component in code).
- **Layout-logic divergence**: padding, alignment, or internal constraints change with a variant: that variant should be a separate component, not an axis.

Default heuristic for the canonical `Button + Icon` case: stay as ONE component with a `hasIcon` boolean UNLESS adding the icon changes the padding/alignment math; only then split into `Button` + `IconButton`.

## Layers: kebab-case + middle-dot for state suffix

```
button-label
button-icon
button-label · hover
button-label · disabled
card-header
card-body
card-footer
input-placeholder
input-helper-text
```

- Kebab-case identifies an element/layer (not a component).
- ` · ` (space + middle-dot U+00B7 + space) for the state suffix on layer names.
- This layer convention comes from one production project. Other projects may use a different convention: check the project map first (see "Project-specific canon defers to project map" below).

## Frames: `NN-name[/state]` prefix

```
01-home
02-detail/empty
02-detail/loading
02-detail/error
02-detail/default
03-settings/default
03-settings/edit-profile
```

- `NN` = two-digit display order (01, 02, 03 ...)
- `name` = semantic kebab-case
- `/state` = optional state suffix for variant frames

### Screen-frame sweep heuristic (Figma device-frame defaults)

When a section contains many screen-level frames named `iPhone 14 & 15 Pro Max - NNN` (Figma's default for device-frame templates), use this deterministic rename pattern:

```
<section-slug>/<NNN>
```

Where:

- `<section-slug>` = slugified `parent.SECTION.name` (lowercase, alphanumeric, `-` separator, max 40 chars)
- `<NNN>` = the trailing number from the original default name (preserves the designer's ordering)

Example: `iPhone 14 & 15 Pro Max - 212` inside a section named `Profile - Likes & Comments` becomes `profile-likes-comments/212`. A status emoji at the start of the section name drops out of the slug, because only alphanumerics survive.

Proven on 800 frames across 2 files with zero errors (field note, 2026-05). The original `NNN` is preserved so the designer's mental ordering survives. The section prefix makes Dev Mode codegen produce locally scoped names.

Walk pseudocode:

```js
// \u2013 is the en dash: the default name may use a hyphen or an en dash before the number
const IPHONE_RE = /^iPhone\s+\d+(\s*&\s*\d+)?(\s+(?:Pro\s+Max|Plus|Pro|Mini|Max))?\s*[-\u2013]\s*(\d+)$/i;
function findSectionAncestor(n) {
  let cur = n.parent;
  while (cur) { if (cur.type === 'SECTION') return cur; cur = cur.parent; }
  return null;
}
// walk; for each match: NN = regex group, sec = findSectionAncestor(node), newName = `${slugify(sec.name)}/${NN}`
```

Notes on the pseudocode: the trailing number (`NN` in the comment, `<NNN>` above) is capture group 3 of `IPHONE_RE`. `slugify` is not defined here: implement the rule above (lowercase, alphanumerics, `-` separator, max 40 chars). `findSectionAncestor` returns `null` for a frame outside any section: skip those frames.

## Variant axis renames: atomic rule

Renaming variant property names (e.g. `Propriedade 1=`, a default property name as it appears in a Portuguese-language Figma UI, to `State=`, or `state=` lowercase to `State=` Title Case):

**Rename ALL variants of a set in ONE `figma_execute` call.** A partial rename fragments the property axis: Figma creates a second property (`state` + `State`) instead of replacing the original. An atomic rename triggers Figma's variant-name re-parser to update `componentPropertyDefinitions` in one go.

Pseudocode:

```js
// SAFE: all variants of one set renamed in one execute
const renames = [['state=hover','State=Hover'],['state=default','State=Default'],...];
for (const [_, newName] of renames) {
  const variant = setNode.children.find(c => c.name === _);
  variant.name = newName;
}
// After loop completes, setNode.componentPropertyDefinitions.State exists.
```

Verification: after the loop, `setNode.componentPropertyDefinitions` should contain ONLY the new property key. If the old key still appears alongside the new one, the property was fragmented: fix it by completing the rename of the missed variants.

Resolve every variant before renaming any. In the loop above, a name that `find` does not match leaves `variant` undefined, so the assignment throws partway, and the renames already applied stay on the canvas (a throw does not roll back, see `references/figma-execute-atomicity.md`). That leaves exactly the fragmented axis this rule prevents. Look up all the variants first, stop if one is missing, and only then rename.

A naming sweep must change zero paint. After the sweep, verify paint integrity on a sample of node ids (the production-tested protocol checked 26 ids).

## Human authorship: sections, pages, and canvas docs

Field note, 2026-07. Delivered Figma files are read by teammates. Names and canvas notes must read like a designer typed them: short and plain, with no status emoji, invented codenames or packed metadata. Treat this as a hard rule, not a preference.

Section/page names: short and plain, like a designer typed them in passing.

- WRONG: `[test-tube emoji] V2 · Checkout form + Order summary · OPTIONS (24/07)`
- WRONG: `[check-mark emoji] V1 · Final card · approved format (stakeholder name, 24/07)`
- RIGHT: `Final card`, `checkout form`, `order summary options`

Banned in section/page names: status emoji (test tube, check mark, warning sign), invented codenames (`V1`, `A2`, `BATCH`), packed metadata (dates, "approved by <name>", process state). If something truly needs a marker, one plain word (`old`, `approved`) is the ceiling.

Canvas docs / annotations / dev notes: short running prose (2-6 sentences), like a spoken comment. No ALL-CAPS headers, no nested taxonomic bullets, no meta-words ("verbatim", "blueprint", "grouping rule"), no bold on every line. Sibling names should NOT follow a visibly repeated template: perfect consistency is itself an AI tell.

Scope: a note card built from the `HandoffNote` spec in `references/handoff-format.md` keeps that spec (its short all-caps step label and the `Why:` / `Edge:` prefixes); its sentences still follow this rule. Free-form doc frames, dev notes and comments follow this paragraph in full.

This overrides the structured conventions above wherever the surface is visible to the team (sections, pages, doc frames, comments). Layer/component naming for Dev Mode codegen (kebab-case, PascalCase slash hierarchy) still applies, since that reads as normal professional practice, not as AI.

## What's BANNED (auto-fail in delivered work)

- `Frame 1`, `Frame 47` (Figma defaults)
- `Group 5`, `Group 12` (Figma defaults)
- `Rectangle 1`, `Rectangle 8` (Figma defaults)
- `Ellipse 3`, `Vector 12` (Figma defaults)
- `Text 4`, `Text 9` (Figma defaults)
- Generic colors as names: `BlueButton`, `GrayCard` (describes color, not function)
- Single letters: `A`, `B`, `C` (not semantic)
- Compound names without separator: `ButtonPrimaryDefault` (use slash hierarchy)

The `figma-slop-check` skill auto-fails on the Figma default names above, and its `names` check also flags a component name with no `/`. It has no check for color names or single letters: check those by reading the layer list.

## Audit-before-rename rule

Before introducing new terminology in a Figma file:

1. Run a `grep`-equivalent search of the existing canon (`figma-orient` output, project map, similar components).
2. Build a glossary table: old terminology vs proposed new vs project canon.
3. Net-new names ONLY when no existing word covers the concept.
4. If the new term clashes with existing usage: pick the existing one, deprecate the proposed one.

Pattern: when mapping a competitor's architecture into the project, search the existing canon FIRST. Many "new" concepts already have a project name.

## Project-specific canon defers to project map

The universal canon above applies to all projects. Project-specific layer canon (e.g., one project's `/` for components and ` · ` for layer state) lives in the project map: a `figma-map.md` file kept in the project (default `docs/figma-map.md`), or the agent's own memory system if it has one.

On conflict: the project map wins for that project. The universal canon stays the fallback.

## Property naming for components

- Text properties: `label`, `title`, `body`, `helperText`, `placeholder`
- Boolean: `hasIcon`, `isDisabled`, `showLabel`
- Instance swap: `iconLeft`, `iconRight`, `slot`

## Why semantic naming matters

- Figma's Dev Mode generates code from layer names: semantic names produce readable code
- Code Connect maps component names to React component imports
- Audit tools (`figma-slop-check`) flag default names automatically
- Future-you (and other designers) navigates by name; cryptic names slow everyone down

## Pre-write checklist

Before creating any new layer:

- [ ] Does a named element already exist for this purpose? If yes: instance/extend, do not recreate.
- [ ] Is the proposed name semantic (describes purpose, not appearance)?
- [ ] Does the name follow the project convention (component vs layer vs frame)?
- [ ] No Figma defaults?
- [ ] If state-bearing: state suffix applied (` · hover`, `/error`)?
