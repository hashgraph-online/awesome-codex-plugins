---
name: writing-modpack-devlog
description: "Use when starting or appending to a modpack project dev-log. Creates <project>/docs/dev-log.md if absent; appends a dated entry on subsequent calls. Triggers - 'log this', 'add to dev log', 'record what I did', 'note this change', 'devlog'."
---

## Overview

The modpack dev-log is the durable record of what the curator did to the modpack, in chronological order, with enough context for a future maintainer to understand why a change happened. This skill replaces the deleted `templates/modpack/dev-log.md` template by creating `<project>/docs/dev-log.md` at runtime, then appending entries as the modpack evolves.

## When to Use

| Use this skill when... | Result |
| --- | --- |
| The user says "log this", "add to dev log", "record what I did", or "note this change" | Append a dated entry to the project dev-log. |
| A mod was added, removed, replaced, upgraded, downgraded, patched, or moved in load order | Record what changed and why. |
| A conflict-audit session finished | Summarize the finding and link evidence from `xedit-conflict-audit` or `xedit-automation` output. |
| A CTD, freeze, missing asset, bad facegen, navmesh issue, or broken quest was investigated | Preserve the investigation result, even if the fix is not final. |
| A modpack release was cut | Add the curator-facing note and cross-link to `writing-modpack-changelog`. |
| The user made a manual decision that future agents must not re-litigate | Record the decision, context, and evidence. |

## When NOT to Use

| Do not use this skill when... | Use instead |
| --- | --- |
| The user is preparing public release notes for players | `writing-modpack-changelog` |
| The user asks for a one-off explanation without wanting a project record | Answer directly. |
| The project root is unknown and the user refuses to identify it | Stop after explaining what is missing. |
| The entry would expose private notes, credentials, or personal information | Ask for a sanitized version first. |
| The request is to inspect or edit plugin records | `xedit-automation` or `xedit-conflict-audit` first, then log the result. |

## Rules

<EXTREMELY-IMPORTANT>
This skill creates or appends documentation inside the user's modpack project. It does not edit game plugins, install mods, change load order, or write into game installation folders. If the user asks for those actions, route to the appropriate modding or xEdit skill before writing the dev-log entry.
</EXTREMELY-IMPORTANT>

1. Detect the modpack project root before writing.
   - If the user provides `<modpack_project_root>`, use it.
   - If the current working directory looks like a modpack directory because it already has `Data/`, `profiles/`, or `docs/`, default to `pwd` and tell the user what default you used.
   - Otherwise ask once: "Which modpack project root should I use? I can default to the current directory if this is the project root."
2. Locate `<project>/docs/dev-log.md`.
   - If `<project>/docs/` does not exist, create it.
   - If `dev-log.md` is missing, create it before appending.
3. On first creation, use this header shape:
   - `# <Project Name> Dev Log`
   - `Started: <local ISO-8601 timestamp with offset>`
   - A short note that entries are newest-first.
   - `## Entries`
4. Use local time with UTC offset for every entry timestamp, and keep that choice consistent throughout the file.
   - Example: `2026-06-01T14:30:00-04:00`.
   - Do not mix local dates, UTC dates, and vague dates such as "today".
5. Each entry must include these parts:
   - ISO-8601 timestamp with offset.
   - Short title.
   - Body paragraph or paragraphs explaining what changed and why.
   - Optional `Mods touched` subsection when specific mods, plugins, patches, or tools were involved.
   - Optional `Refs` subsection linking evidence, logs, issue threads, release pages, or xEdit captures.
6. Append entries newest-first under the `## Entries` section.
   - Insert the new entry immediately below `## Entries`.
   - Do not append new entries at the bottom unless the file already uses oldest-first and the user explicitly wants to keep it that way.
7. Do not duplicate the most recent entry.
   - Read the newest entry timestamp and title.
   - If the new title and body would be identical or effectively identical within 10 minutes of the newest entry, surface: "This looks like a duplicate of `<existing title>` from `<timestamp>`. Append anyway? (y/N)"
   - Default to no if the user does not confirm.
8. Preserve evidence when the user references it.
   - If the user points at a captured xEdit conflict, crash log, plugin diff, screenshot, text log, or other local evidence file, copy it into `<project>/docs/dev-log-artifacts/<entry-slug>/`.
   - Link the copied artifact from the entry body or `Refs` subsection.
   - Prefer copying over linking to a fragile temporary path.
9. Make the entry useful to a future curator.
   - Include the decision, cause, tradeoff, or unresolved question.
   - Avoid entries that only say "fixed stuff" or "updated mods".
10. Keep private working noise out of the dev-log.
    - Do not paste entire terminal transcripts unless they are the evidence.
    - Summarize the result, then link artifacts.
11. If the user gave rough notes, preserve meaning rather than polishing away operational details.
    - Keep mod names, plugin names, load-order context, symptoms, and reproduction facts.
    - Clean up grammar only enough to make the entry readable.
12. After writing, report the file path, entry title, timestamp, and any artifacts copied.

## Quick Reference

| Field | Canonical shape | Example |
| --- | --- | --- |
| File | `<project>/docs/dev-log.md` | `docs/dev-log.md` |
| Entry heading | `### <timestamp> - <short title>` | `### 2026-06-01T14:30:00-04:00 - Rebuilt settlement patch after lighting update` |
| Body | One or more paragraphs explaining what changed and why | `Updated the settlement compatibility patch after the lighting mod changed precombines in the affected cells.` |
| Mods touched | Optional bullet list | `- Example Lighting Overhaul` |
| Refs | Optional bullet list of copied artifacts or external references | `- dev-log-artifacts/rebuilt-settlement-patch/xedit-conflict-summary.md` |

Canonical entry shape:

```markdown
### 2026-06-01T14:30:00-04:00 - Rebuilt settlement patch after lighting update

Updated the settlement compatibility patch after the lighting mod changed records in the affected cells. The new patch keeps the visual change while preserving the workshop keyword edits from the settlement overhaul.

#### Mods touched

- Example Lighting Overhaul
- Example Settlement Overhaul
- Example Modpack Patch

#### Refs

- dev-log-artifacts/rebuilt-settlement-patch/xedit-conflict-summary.md
```

## Examples

### Bad

```markdown
Fixed the lighting thing.
```

This entry has no date, no mod names, no context, no evidence, and no explanation of what was fixed.

### Good

```markdown
### 2026-06-01T14:30:00-04:00 - Resolved lighting and workshop keyword conflict

Kept the lighting overhaul's cell image-space change, but restored the settlement overhaul's workshop keyword edits in the patch. This should preserve the intended visual pass without breaking workshop placement in the affected settlement.

#### Mods touched

- Example Lighting Overhaul
- Example Settlement Overhaul
- Example Modpack Patch

#### Refs

- dev-log-artifacts/lighting-workshop-keyword-conflict/xedit-conflict-summary.md
```

This entry tells a future curator what changed, why it changed, which mods were involved, and where the evidence lives.

## Common Mistakes

- Writing a loose note without a timestamp.
- Logging only the action and omitting the reason.
- Using the dev-log as public release notes instead of curator history.
- Duplicating the same entry because the user repeated "log this" after a tool run.
- Linking to temporary evidence paths that will disappear.
- Copying huge raw logs into the main entry instead of summarizing and linking artifacts.
- Recording "updated mods" without naming the mods.
- Turning rough curator notes into generic prose that loses load-order context.
- Asking multiple root-location questions instead of one question with a default.
- Creating the file somewhere outside the actual modpack project root.

## Rationalizations

| Excuse | Reality |
| --- | --- |
| "This is just a tiny note; it does not need structure." | Tiny notes become the only record future agents can trust. Date, title, context, and refs are the minimum useful shape. |
| "The release changelog will cover it." | The changelog is for players. The dev-log is for curators and future agents. They answer different questions. |
| "The evidence is in my terminal scrollback." | Scrollback is not durable. Copy evidence into `docs/dev-log-artifacts/<entry-slug>/` and link it. |
| "I can append at the bottom; it is easier." | Newest-first keeps the current state visible. Insert below `## Entries` unless the user explicitly chose oldest-first. |
| "The user knows what they meant by 'lighting thing'." | Future maintainers will not. Name the symptom, mod, plugin, cell, record, or decision. |
| "I should ask several questions to make sure the entry is perfect." | Ask once for the project root if needed. Otherwise write the best entry from available context and flag uncertainties inline. |
| "The artifact path is already linked in the conversation." | Conversation links are not project records. Copy or preserve the artifact in the project docs tree. |
| "I should make this sound polished." | Accuracy beats polish. Keep the operational facts and make the wording readable. |

## See also

- `writing-modpack-changelog` - use for player-facing release notes and version sections.
- `setting-up-bgs-modding-environment` - use when the modpack project structure itself is being created or located.
