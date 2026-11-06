# Canvas validation

Run from the plugin root:

```sh
python3 -B -m unittest discover -s skills/obsidian-canvas-authoring/tests
```

The [fixtures](../assets/fixtures/) cover all three layouts and all four node types. Tests check stable IDs, duplicate keys and IDs, invalid dimensions and colors, dangling edges, lexical file and subpath validation, Unicode and literal text transport, likely clipping, and exact preservation of unrelated records during a scoped edit. The missing-source fixture requires a live vault check because the helper has no filesystem access.

## Disposable-vault procedure

1. Seed a disposable vault with the exact paths and headings used in the fixture, or adapt the input to the disposable notes. Resolve the vault name and canonical root. Snapshot the fixture notes and check each file and heading through the CLI.
2. Run the helper on each request and preview the approved target and relationship evidence. Check that the target remains absent and the source notes retain their original bytes. Run the missing-source case and verify that it stops before any write.
3. With an approved create, recheck the vault and absence, apply through the official CLI, and compare the full file to the candidate bytes. Repeat the state check against the same candidate and classify it as already applied.
4. Open each exact Canvas. After cards finish rendering, review all three layouts at fit-to-view, including the text, source sections, arrow directions and documented/inferred labels. Record any remote card whose preview fails to load.
5. Preview a group label edit against the existing Canvas fixture. Introduce a controlled change to its extension field and confirm the stale preview is blocked. Refresh the preview, apply the scoped edit, and compare every byte outside the changed label. Confirm the fixture notes remain unchanged.

## Observed on macOS

Obsidian desktop and installer 1.15.0 opened the project, research and process fixtures. Exact CLI create and overwrite bytes matched before opening. Obsidian later reserialized the three new maps. Their parsed content, IDs, geometry and edges still matched the approved candidates.

- The Atlas project map showed the approved sign-in decision, the rollout blocker and the proposed review in one view. The two file cards rendered their exact headings. The first draft clipped edge labels. Wider spacing resolved that at fit-to-view.
- The research map rendered the Unicode file card and separated staging evidence from the open approval question. The selected public JSON Canvas link card loaded in the representative research review.
- The process map rendered three ordered cards with rightward arrows and readable inferred relationship labels.
- The missing source blocked apply. Exact-state checks recognized repeat creates and blocked a stale update. A refreshed group-label update preserved unrelated bytes, including the intervening extension change. The source notes retained their original bytes.

The disposable-vault run covered macOS. Other platforms and Obsidian builds need their own transport and rendering checks.
