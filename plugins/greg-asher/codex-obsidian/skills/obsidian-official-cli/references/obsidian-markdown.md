# Obsidian content conventions

Use only the syntax relevant to the requested note. Preserve the note's existing style; do not add frontmatter, links, or callouts just to demonstrate features. These examples are original fixtures based on official documentation, not copied competitor implementations.

## Resolve links before authoring

Use CLI search/files and exact-path reads to resolve notes in the pinned vault. Prefer a path-qualified wikilink when titles collide: `[[Projects/Atlas|Atlas]]`. Display text after `|` is a link label; frontmatter `aliases` supplies alternate note names. Verify headings with outline/read and block IDs in raw content before generating `[[Projects/Atlas#Risks]]`, `[[Projects/Atlas#^decision-1]]`, or same-note `[[#Risks]]`. Block IDs use Latin letters, digits, and dashes and must be unique within the target note. Preserve existing IDs during revisions.

`![[Projects/Atlas#Risks]]` embeds a section. `![[Attachments/architecture.png|480]]` embeds an image at a width; keep the extension for attachments. Resolve the attachment too. Do not embed a note into itself. In Markdown tables escape the alias separator: `[[Projects/Atlas\|Atlas]]`. Ordinary Markdown links are also supported; percent-encode spaces in their destinations and preserve a user's chosen link style.

If a target/anchor is absent, report it. An explicitly requested future-note link may remain unresolved, with that intent in the preview/result. Do not invent or create a missing note/anchor silently. New links must not accidentally bind to a duplicate title. Avoid filenames containing link delimiters (`#`, `|`, `^`, `[[`, `]]`) rather than promising they work.

## Properties and callouts

Use one YAML frontmatter block at file start. Quote wikilinks and YAML-sensitive scalar values; use lists for `tags`, `aliases`, and `cssclasses`. Avoid duplicate keys; do not coerce existing property types. Follow [metadata revision](authoring-and-revision.md#revise-metadata) to preserve frontmatter and verify typed CLI behavior. Obsidian property types are shared by name across a vault; do not change global type definitions to repair one note. Date/date-time values follow the installed app's supported ISO formats; missing is different from an empty or false value. Nested YAML may be valid YAML without being editable in the Properties UI; do not promise full UI support.

```markdown
---
aliases:
  - Atlas overview
tags:
  - project/atlas
status: "in progress"
owner: "[[People/Sam]]"
---
# Atlas

> [!warning] Delivery risk
> The supplier date is unconfirmed.
> Check [[Projects/Atlas#Risks|current risks]].
```

Every body line of a callout stays inside the blockquote. `> [!note]` is open by default; `[!tip]+` and `[!warning]-` explicitly expand/collapse. Plain paragraphs may define an anchor at their end: `Approved the staged rollout. ^decision-1`. For structured blocks (lists/callouts/tables), place the block ID on its own line separated by blank lines. Do not generate links to unsupported parts of a table/callout.

## Templates

Discover templates with `templates`; inspect a selected template with `template:read` and probe `resolve`/`title=` before use. Official Templates supports title/date/time substitutions and configured date/time formatting. Do not assume Templater, QuickAdd, arbitrary JavaScript, or unknown placeholders execute. Preview known rendered content, property merge effects, and unresolved variables. Recheck template state before applying a preview; a changed template may need a new preview. Do not combine `content` and `template` assuming an undocumented precedence. Creation and active-note insertion are different operations: avoid implicit-active `template:insert`; use exact-path template creation or a reviewed resolved-content insertion when supported. Confirm actual title/date/time and metadata after write.

## Rendering check

Syntax review and fixture checks do not establish live rendering. In a disposable vault check Reading view/Live Preview for links and alias labels, embeds, heading/block navigation, callout body/folding, and typed Properties display. Use workspace/navigation for requested opens and devtools for authorized visual diagnostics; never enable eval/CDP merely to bypass a missing write capability.

Official sources: [internal links](https://obsidian.md/help/links), [embeds](https://obsidian.md/help/embeds), [callouts](https://obsidian.md/help/callouts), [properties](https://obsidian.md/help/properties), [Templates](https://obsidian.md/help/plugins/templates), [CLI](https://obsidian.md/help/cli). Installed help and runtime behavior still gate execution.
