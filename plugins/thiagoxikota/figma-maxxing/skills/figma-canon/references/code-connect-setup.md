# Code Connect setup

Load when mapping Figma components to React code. Code Connect quickstart for a React + TypeScript + Tailwind app: `figma.config.json` template, `.figma.tsx` example, property mapping helpers, publish workflow, and when NOT to use it.

## What it is

Code Connect creates a bidirectional link between a Figma component and a production code component. Dev Mode then shows the actual React import path + props mapping instead of generic React+Tailwind.

Two flavors:

- **CLI (recommended for repos with code):** runs locally, framework-specific (React/Vue/SwiftUI/Compose), precise prop mapping
- **UI:** runs in Figma, GitHub-backed, language-agnostic, less precise

Use the **CLI** for a React + TypeScript + Tailwind app. The examples below assume one.

## When to use

- Use: an app repo that has React + TypeScript + Tailwind component code, for example under `src/components/`.
- Do not use: a project with no code yet. Defer until the repo exists.
- Do not use: a repo with no UI components.

## Installation

```bash
cd <path-to-your-app-repo>   # wherever the repo lives
npm install --save-dev @figma/code-connect
```

## figma.config.json template

At the root of the app repo:

```json
{
  "codeConnect": {
    "parser": "react",
    "include": ["src/components/**/*.figma.tsx"],
    "exclude": ["test/**", "docs/**", "build/**", "dist/**"],
    "label": "React",
    "language": "tsx",
    "importPaths": {
      "src/components/ui/*": "@/components/ui",
      "src/components/forms/*": "@/components/forms"
    },
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

## `.figma.tsx` example (a HeroBanner component)

`src/components/ui/HeroBanner.figma.tsx`:

```tsx
import figma from '@figma/code-connect/react'
import { HeroBanner } from './HeroBanner'

figma.connect(HeroBanner, 'https://www.figma.com/design/<fileKey>/?node-id=<nodeId>', {
  props: {
    eyebrow: figma.string('Eyebrow'),
    title:   figma.string('Title'),
    body:    figma.string('Body'),
    variant: figma.enum('Variant', {
      Default: 'default',
      Dark: 'dark',
      Brand: 'brand',
    }),
    showCta: figma.boolean('Show CTA'),
    cta:     figma.instance('CTA Slot'),
  },
  example: ({ eyebrow, title, body, variant, showCta, cta }) => (
    <HeroBanner
      eyebrow={eyebrow}
      title={title}
      body={body}
      variant={variant}
    >
      {showCta ? cta : null}
    </HeroBanner>
  ),
})
```

## Property mapping helpers

| Figma type | Helper | Returns |
| --- | --- | --- |
| Text content | `figma.string('PropName')` | string |
| Boolean property | `figma.boolean('PropName')` | boolean |
| Variant property | `figma.enum('PropName', { VariantName: 'codeValue' })` | string (mapped) |
| Instance swap | `figma.instance('SlotName')` | React node |
| Children content | `figma.children('SlotName')` | React node |
| Nested instance | `figma.nestedProps('NestedName', { ... })` | object |

## Advanced patterns

### Compound components with slots (`<Card.Header/>`)

For Figma components built with named slot frames (for example `Header`, `Body`, `Footer`):

```tsx
figma.connect(Card, '<URL>', {
  props: {
    header: figma.children('Header'),
    content: figma.children('Body'),
    footer: figma.children('Footer'),
  },
  example: ({ header, content, footer }) => (
    <Card>
      <Card.Header>{header}</Card.Header>
      <Card.Body>{content}</Card.Body>
      <Card.Footer>{footer}</Card.Footer>
    </Card>
  ),
})
```

Figma-side requirement: the slot frames are named exactly as the prop expects them (case-sensitive). A missing or misnamed slot leads to an instance duplication failure: the agent draws raw frames instead of using the compound component.

### Polymorphic components (`as="button" | "a" | "div"`)

Use a variant property named for example `Element Type` and map it via `figma.enum`:

```tsx
figma.connect(Button, '<URL>', {
  props: {
    as: figma.enum('Element Type', { Button: 'button', Link: 'a', Div: 'div' }),
    label: figma.string('label'),
  },
  example: ({ as, label }) => <Button as={as}>{label}</Button>,
})
```

This forces the agent to make a semantic-HTML decision instead of defaulting to `<div>` for all interactive elements.

### Nested component delegation (complex tables, multi-axis sets)

For components composed of named sub-instances (for example `Table` contains a `TableHeader`), delegate the prop mapping to the nested layer to keep the top-level mapping flat:

```tsx
figma.connect(Table, '<URL>', {
  props: {
    headerProps: figma.nestedProps('TableHeader', {
      title: figma.string('title'),
      isSortable: figma.boolean('Sortable'),
    }),
    rows: figma.children('Rows'),
  },
  example: ({ headerProps, rows }) => (
    <Table>
      <TableHeader {...headerProps} />
      {rows}
    </Table>
  ),
})
```

Use this when a component set would otherwise need 6+ axes at the top level: nesting collapses the variant explosion. Failure mode if skipped: the agent hits the 20KB output limit reading a flat prop list and returns a truncated payload.

## Publish workflow

Publishing is a high-risk action: it changes what Dev Mode shows for every mapped component. Ask the user before running `figma connect publish` (see "Never automate without explicit user approval" in `references/security-canon.md`).

The token is the personal access token in the `FIGMA_ACCESS_TOKEN` environment variable, the same variable the figma-console MCP server reads. Never print it, never write it to a file.

```bash
# Get a PAT from Figma > Settings > Security > Personal access tokens
# Scopes required: "Code Connect: Write" + "File content: Read"
export FIGMA_ACCESS_TOKEN="figd_..."

# Publish all mappings in src/components/**/*.figma.tsx
npx figma connect publish --token=$FIGMA_ACCESS_TOKEN

# Unpublish a single mapping
npx figma connect unpublish --node=<NODE_URL> --label=React
```

## CI integration

Add to the package.json scripts:

```json
{
  "scripts": {
    "figma:publish": "figma connect publish --token=$FIGMA_ACCESS_TOKEN",
    "figma:unpublish-all": "figma connect unpublish --label=React --token=$FIGMA_ACCESS_TOKEN"
  }
}
```

CI workflow (GitHub Actions example):

```yaml
- name: Publish Code Connect mappings
  run: npx figma connect publish --token=${{ secrets.FIGMA_ACCESS_TOKEN }}
```

## PAT scope checklist

- [ ] `Code Connect: Write`
- [ ] `File content: Read`
- [ ] Stored in an env var (NEVER committed)
- [ ] Stored in CI secrets (NEVER in the repo)

## Example component paths

Each `*.figma.tsx` sits next to its component file, inside a folder that the `include` glob of `figma.config.json` matches. For example: `src/components/ui/HeroBanner.tsx` + `src/components/ui/HeroBanner.figma.tsx`.

## Verification

After publishing:

1. Open the mapped Figma component in Dev Mode
2. Verify the code panel shows the React import path + JSX example
3. Verify the props show with the correct values from the Figma instance

## Effect on the agent workflow

When Code Connect is configured:

- `get_code_connect_map` (official Figma MCP server) returns the mapping
- The agent uses the actual component path instead of inventing JSX
- Variant property changes in Figma map to React prop changes
- Turns the AI-slop move "I'll create a new Button" into "I'll instance the existing one"

## Project with no code yet

When a project has no code repo, Code Connect is deferred until the repo exists. When that happens:

1. Bootstrap the repo (with your project's own build skill or workflow, if any)
2. Add `@figma/code-connect`
3. Create `figma.config.json`
4. Map the components per the project's library structure
5. Update the project's `figma-map.md` with the Code Connect status
