# Source-linked Canvas maps

Select **Obsidian Canvas Authoring** or run `workflow_id=canvas.map mode=preview` through Obsidian CLI Workflows. For example, ask for an Atlas project map at `Maps/Atlas.canvas` linking the approved decision, the rollout dependency, and next actions.

## Evidence and layout

Resolve the vault through workspace/navigation. Verify the target and sources within the canonical root, rejecting escaping symlinks and aliases that change identity. Resolve a file card with exact-path CLI inspection. Verify a heading against the exact note outline and a block against the exact note text. Require a unique verified target. If a subpath is unavailable, preview the proposed whole-note fallback or leave the card blocked. A structurally valid reference can still fail in Obsidian.

Reuse session-only source records from cited retrieval. Select the smallest useful set of sources and relationships. Keep external URL cards explicit and disclose that Obsidian may load remote pages or resources when rendering a card. Existing source notes may also render their own embeds. For text cards, prefer a concise explanation, decision, or next action. The renderer escapes supplied text as literal Markdown rather than activating pasted embeds or instructions.

| Layout | Order and limits |
| --- | --- |
| `research` | Sources, Synthesis, Open questions. Up to three cards per lane and nine total. |
| `project` | Decisions, Dependencies and risks, Next actions. Up to three cards per lane and nine total. |
| `process` | Up to five cards in explicit left-to-right order. |

Research and project layouts add group backgrounds behind their cards. Supply at most 12 relationships between adjacent columns or process steps. Use short directional labels of at most 20 characters and mark each `documented` or `inferred`. Documented edges need a verified supporting passage or link in the preview. Separate unrelated rows when edge lines cross. Group containment is spatial. The renderer keeps group nodes beneath their contents and uses stable IDs derived from card keys and edge endpoints.

## Render or edit a candidate

Run [canvas_definition.py](../scripts/canvas_definition.py) from the installed skill with Python 3.9+ and a literal UTF-8 JSON object on stdin. The renderer uses the standard library and performs no vault access. Input is capped at 64 KiB and definitions at 12 KiB. [Example requests](../assets/fixtures/) cover all three layouts.

- Creation takes `layout`, `cards` and optional `relationships`. Cards require stable `key`, `lane` for research/project, and exactly one of `file`, `text`, or `url`. A file can take `subpath` such as `#Decision`. Relationships take `from` and `to` card keys, `label`, and `evidence`.
- Validation takes only `canvas`, the parsed JSON Canvas object. It returns lexical references, layout warnings, and whether the document has extension fields. Verify reported paths, subpaths and source evidence independently. Geometry, endpoint integrity, color, grouping, likely card text and horizontal edge label clipping, dense connections and approximate crossings are checked. App rendering may differ.
- Editing takes literal `before` text and any of `update` (object mapping exact IDs to supported fields), `remove` (explicit IDs), or `add` (complete new records under `nodes` or `edges`). Assign explicit stable IDs for additions and retain all existing IDs. Remove any affected edges explicitly. New groups go behind existing nodes. The patcher changes selected JSON spans and preserves unrelated record bytes, order, and extension values. It blocks newly introduced layout warnings and reports pre-existing warnings. The first release bounds existing Canvas documents to 32 nodes and 40 edges.

Obsidian CLI 1.15.0 decodes literal newline and tab escapes in content. The renderer emits equivalent JSON Unicode escapes for those tokens and for escaped backslashes immediately before `n` or `t`. It compares parsed values before and after and reports the substitutions in the exact preview diff. This can change the spelling of an escape in an otherwise untouched record while preserving its JSON value. Other unsafe transport, including CRLF, blocks rather than normalizing the document.

## Apply and inspect

Probe installed `version`, `help create`, and `help open` when opening is requested. The bundled launcher verified exact suffix and bytes for both `create path=...` and approved `overwrite` on Obsidian desktop and installer 1.15.0. For other builds require equivalent capability evidence before writing. Do not substitute a developer command or filesystem write. Use the shared exact state check before apply and disclose whole-file transport for scoped edits. A recheck leaves an optimistic concurrency window. Verify exact path and bytes after applying and before opening. Before an overwrite, check the installed `tabs` output in the pinned vault and require the target Canvas to be closed. If tab titles cannot disambiguate the target, resolve the state before writing.

Obsidian can reserialize a Canvas during visual inspection. Compare the post-open JSON values with the approved candidate and report format-only changes or substantive differences separately. If the helper reports `extension_fields: true`, skip opening the original unless the installed build has established preservation for those extensions. Record the visual check as deferred or inspect a separately authorized disposable copy.

Review the map at fit-to-view and inspect dense lanes or labels at readable zoom. Confirm source cards show the intended note or section, connector direction matches the evidence, and a reader can find the decision, dependencies and next steps. Record any clipping, rendering differences or unverified interactions separately from structural validity.

[JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/) · [Obsidian Canvas](https://obsidian.md/help/plugins/canvas) · [Obsidian CLI](https://obsidian.md/help/cli)
