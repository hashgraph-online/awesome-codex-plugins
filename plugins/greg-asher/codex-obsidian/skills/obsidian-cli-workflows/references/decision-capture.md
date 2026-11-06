# Project decision capture

Use the bundled `decision` recipe through `workflow_id=inbox.capture recipe=decision` or an explicit request to capture a project decision after selecting the workflow skill. This recipe creates one note with create-only behavior. The workflow skill owns input resolution and the preview. Navigation owns vault discovery. Core authoring owns the CLI call, verification, and recovery.

## Inputs and rendered note

| Input | Requirement |
| --- | --- |
| `vault` | Resolve and pin the vault selector and canonical root through navigation. A missing selector can resolve to one unambiguous vault. |
| `project_path` | An existing, exact vault-relative Markdown project note. A project name may be resolved by scoped read-only discovery. Ask for a selection when ambiguous. |
| `folder` | The requested existing destination folder inside that vault. Ask when unknown. |
| `title` | One filename stem, without an extension. Preserve the user's wording. Ask for a safe alternative when invalid. |
| `decision` | The decision to record. Use supplied or explicitly selected text. |
| `rationale` | Optional supplied rationale. Omit the section when absent. |

The destination is `<folder>/<title>.md`. Use a stable title for repeats. No timestamps or random suffixes are added. The fixed template has two frontmatter text values, `type: "decision"` and `project: "[[<project_path>]]"`, plus a Decision section and optional Rationale. Preserve the decision and rationale as literal text blocks so pasted links, embeds, and markup cannot become active content. Only the resolved project link is generated as a wikilink. If existing vault property types conflict with the recipe, explain the conflict before any write.

Use [decision_capture.py](../scripts/decision_capture.py), Python 3.9+ standard library, to render the candidate. Resolve the script from the loaded workflow skill. Pass a UTF-8 JSON object via stdin with `title`, `decision`, `project_path`, `folder`, and optional `rationale`. Use a JSON serializer and literal arguments. The helper returns `path`, `properties`, and exact Markdown `content`. It only validates lexical input and renders. The agent still verifies canonical containment, actual filenames and normalization aliases, project identity, property types, and permissions.

## Preview, apply, and repeat

1. Resolve all required inputs. Use the pinned vault to verify the project note exists and the destination folder is contained and already exists. Check the resolved target and any path alias. Stop if the project link would resolve ambiguously, the destination aliases the project note, or the folder/path cannot be verified.
2. Render the draft. Use the [core authoring procedure](../../obsidian-official-cli/references/authoring-and-revision.md) to retain the target, exact expected bytes, and before-state. Check the core launcher's literal-content constraints before offering apply. Preview the project link, properties, exact Markdown, destination, and create-only policy. Preview never writes, even when `output=note`. Inline/JSON controls the report format. A plan-only request may stop before rendering.
3. If the destination already contains the exact rendered bytes, report `already-present` and skip the write. This describes the observed content without attributing it to a prior run. If different or unreadable, report the collision or blocker. A new title or folder is a new preview. An apply request without a matching approved preview produces the preview and waits for approval.
4. With matching approval, revalidate the vault mapping, contained paths, project reference, destination state, and supported `create` options. Delegate a single `create path=...` with the exact approved Markdown as literal content and no overwrite, navigation, or additional property writes. Apply only if the destination remains absent. The same-content check also applies here if another run has created the note in the meantime.
5. Read the exact destination through the pinned CLI and verify complete expected bytes, typed properties, and the intended project reference through the shared authoring contract. Report verified success, already present, conflict, or uncertain completion. After uncertainty, inspect the actual state and use the core retry rules. An absent note alone cannot establish that the original write cannot still happen. Concurrent app writes retain the documented recheck-to-write race.

If the user asks for alternative collision behavior, use the existing ordinary authoring workflow with its own preview. This is the undated form for one direct decision. For an explicitly dated decision, a batch, a web source, or the other recipes, use the [dated capture recipe contract](capture-recipes.md).
