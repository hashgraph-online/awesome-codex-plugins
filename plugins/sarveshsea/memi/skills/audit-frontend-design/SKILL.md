---
name: audit-frontend-design
description: Use when reviewing or changing a React, Next.js, Tailwind, or shadcn interface and you need evidence-backed findings for accessibility, hierarchy, tokens, states, and responsive design before editing code.
---

# Audit Frontend Design

Audit the real source tree before proposing UI changes. Memi's checks are deterministic and file-anchored; no Figma connection or background process is required.

This workflow targets published beta **2.8.0-beta.2**. Use `npx -y @memi-design/cli@2.8.0-beta.2 --version` to verify the exact package; a local `memi` must report that same version before these recipes run. The independent stable compatibility baseline is **2.7.9**. See [current release state](https://github.com/memi-design/memi/blob/main/docs/CURRENT_RELEASE.md) and [known limitations](https://github.com/memi-design/memi/blob/main/docs/trust/KNOWN_LIMITATIONS.md). npm availability alone does not establish native-binary success.

## Run The Audit

From the repository root:

```bash
memi diagnose . --json --no-write --fail-on none
```

For UX behavior and visual craft detail, run only the relevant follow-up:

```bash
memi ux audit . --json --no-write
memi craft audit . --json --no-write
```

A supplied screenshot is context, not proof that Memi performed pixel analysis. Use the harness browser or image tools for actual rendered checks. Use `memi diagnose . --receipt-only --fail-on none` when the output must exclude source content.

## Workflow

1. Read repository instructions and identify the requested route or component.
2. Run `diagnose` before broad UI edits.
3. Group findings by user impact, not by checker name.
4. Verify each proposed fix against the cited file and local design tokens.
5. Implement only fixes relevant to the user's request.
6. Re-run the same command and report assessed quality, category coverage, scan omissions, and remaining findings.

## Output

Lead with actionable findings:

| Priority | Evidence | Change |
| --- | --- | --- |
| High | `path/to/file.tsx:line` and rule id | Specific code-level fix |

Include the command run, before/after score, files changed, and unresolved risks. Never replace source evidence with generic taste advice.
