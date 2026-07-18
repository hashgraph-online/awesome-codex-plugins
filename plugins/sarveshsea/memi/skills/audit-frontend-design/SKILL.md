---
name: audit-frontend-design
description: Use when reviewing or changing a React, Next.js, Tailwind, or shadcn interface and you need evidence-backed findings for accessibility, hierarchy, tokens, states, and responsive design before editing code.
---

# Audit Frontend Design

Audit the real source tree before proposing UI changes. Memi's checks are deterministic and file-anchored; no Figma connection or background process is required.

## Run The Audit

From the repository root:

```bash
npx -y @memi-design/cli@2.6.2 diagnose . --json --no-write --fail-on none
```

For UX behavior and visual craft detail, run only the relevant follow-up:

```bash
npx -y @memi-design/cli@2.6.2 ux audit . --json --no-write
npx -y @memi-design/cli@2.6.2 craft audit . --json --no-write
```

Use `--screenshot <path>` with `craft audit` when the user provides a rendered screen.

## Workflow

1. Read repository instructions and identify the requested route or component.
2. Run `diagnose` before broad UI edits.
3. Group findings by user impact, not by checker name.
4. Verify each proposed fix against the cited file and local design tokens.
5. Implement only fixes relevant to the user's request.
6. Re-run the same command and report the score and remaining findings.

## Output

Lead with actionable findings:

| Priority | Evidence | Change |
| --- | --- | --- |
| High | `path/to/file.tsx:line` and rule id | Specific code-level fix |

Include the command run, before/after score, files changed, and unresolved risks. Never replace source evidence with generic taste advice.
