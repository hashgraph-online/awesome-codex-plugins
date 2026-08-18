---
name: using-bgs-archive
description: Use when the user wants to inspect, list, extract, unpack, or repack Bethesda BA2/BSA archives; determine archive format/version/compression; or build archive assets for an MO2 overlay. Triggers - "unpack BA2", "extract BSA", "pack archive", "inspect archive", "bgs-archive".
---

# Using bgs-archive

`bgs-archive` is the agent-native CLI for Bethesda BA2/BSA archives. It detects archive family/version, lists entries, extracts assets, and packs supported BSA/BA2 outputs for MO2 overlay workflows.

Use this skill for:

- unpacking or extracting BA2/BSA assets;
- repacking supported BA2/BSA archives;
- inspecting archive contents, format, version, compression, or entry counts;
- preparing packed assets for a mod overlay.

Do not use it for plugin records (`.esp/.esm/.esl`) or load-order edits. Route those through xEdit / load-order skills.

## Prerequisites — capability discovery first

Always query the live binary before choosing a game, format, or packing path:

```powershell
bgs-archive --json capabilities
# Alias:
bgs-archive --json caps
```

Read the JSON envelope and branch on `data.write_support` and `data.read_support`. Do not assume DX10 or GNMF packing exists just because DX10/GNMF extraction works.

If `bgs-archive` is not on PATH, locate the GitHub Release-installed binary under:

```text
~/.bgs-modding-superpowers/tools/bgs-archive/<version>/
```

or build from the source tree:

```powershell
cd D:\awesome-bgs-mod-master\tools\bgs-archive
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
cargo build --release
target\release\bgs-archive.exe --json capabilities
```

## Hard rules

- Never write a packed archive into the game's `Data` folder or any Stock-Game tree.
- Pack output belongs in an MO2 mod overlay: `<MO2_Root>/mods/<mod-name>/Data/...`.
- Extract and inspect archives freely, but keep extraction outputs in a workspace or overlay staging folder, not in game `Data`.
- DX10/GNMF pack is unsupported in this version. Extract works; packing returns `unsupported`.
- Use `--json` for agent workflows and branch on the envelope, not human text.

## 资产优先级判断 / Asset precedence judgment

Asset precedence is the runtime question "which asset bytes does the game actually read for this virtual path?" It is related to load order, but it is not the same layer as plugin-record conflict resolution.

Core rules:

- Loose files win over archive contents at the same virtual path. If a loose `textures/...` or `meshes/...` file is active, it can mask every packed copy of that path.
- Archive-to-archive order follows the plugin/load-order surface (`plugins.txt` / the game's active plugin order), not MO2 left-pane mod order. Moving a mod in the left pane may change loose-file winners, but it does not by itself prove a packed archive entry will win.
- Before extracting, identify the layer: asset path conflict, archive count/format issue, or plugin record conflict. Do not solve the wrong problem with the wrong tool.
- For current-game engine caveats or archive-count/packaging diagnostics, query the KB instead of inlining rules here:

```text
bgs_kb_query({ query: "asset precedence engine caveat", games: ["<current game>"], domains: ["engine", "archive-precedence"] })
bgs_kb_query({ query: "archive count or packaging CTD", games: ["<current game>"], domains: ["archive-precedence", "debugging"] })
```

Red flags:

| Thought | Reality |
|---|---|
| "The wrong texture/model loaded, so I should reorder plugins first." | First inspect the final asset provider chain. Wrong bytes are usually an asset-precedence question before they are a record-order question. |
| "MO2 left-pane priority controls packed assets too." | Left-pane priority controls loose-file winners. Packed archive winners are tied to the plugin/load-order surface. |
| "I'll extract every archive loose so conflicts are obvious." | Bulk extraction creates duplicate active surfaces and can make the final tree harder to reason about. Extract only a bounded diagnostic set or a deliberate overlay. |
| "A current game's engine-specific archive/precompute problem belongs in this archive skill." | That is game-specific engine knowledge. Query the relevant KB record and keep this skill game-agnostic. |
| "The archive command succeeded, so the runtime winner changed." | Run `info`/`list` and inspect the MO2 final virtual path/provider chain before claiming the game will read the new asset. |

Rationalizations:

| Excuse | Reality |
|---|---|
| "Plugin order changed, so asset order must be fixed." | Only plugin-associated archives follow that surface; loose files can still override the packed winner. |
| "It's just a texture, not a real conflict." | Asset conflicts are real runtime behavior. A single winning mesh, texture, interface file, or script can be the visible bug. |
| "Unpacking is reversible, so I'll do it broadly." | Reversible clutter is still clutter. Keep extraction bounded and staged outside game `Data`. |
| "The FO4 recipe is known, so paste it here." | Game facts belong in KB. The archive skill teaches the judgment frame and asks KB for game-specific facts. |
| "If the file is in a BA2/BSA, MO2 mod priority is irrelevant." | It is different, not irrelevant: archives route through active plugins/load order. |

After asset precedence is understood, route record-level conflicts to `xedit-conflict-audit`. Archives decide files; xEdit decides plugin records.

## JSON envelope contract

Every `--json` command returns one stdout object:

```json
{
  "ok": true,
  "tool": "bgs-archive",
  "command": "capabilities",
  "data": {},
  "error": null
}
```

On classified failures:

```json
{
  "ok": false,
  "tool": "bgs-archive",
  "command": "pack",
  "data": null,
  "error": { "code": "unsupported", "message": "dx10_pack not yet supported (Task A-DX10)" }
}
```

## Commands

Check `bgs-archive --help` and `<subcommand> --help` for the current option surface. The examples below are templates.

### `capabilities`

Use first to discover supported games, subcommands, read support, and write support.

```powershell
bgs-archive --json capabilities
```

Expected machine output includes:

```json
{"ok":true,"tool":"bgs-archive","command":"capabilities","data":{"games":["morrowind","oblivion","fallout3","falloutnv","skyrimle","skyrimse","fallout4","fallout4ng","fallout76","starfield"],"write_support":{"tes3":true,"tes4":true,"fo4_gnrl":true,"dx10":false,"gnmf":false},"read_support":{"all_families":true}},"error":null}
```

### `info`

Detect archive family, version, BA2 format, compression, and entry count.

```powershell
bgs-archive --json info "D:\path\to\Archive.ba2"
```

Expected machine output shape:

```json
{"ok":true,"tool":"bgs-archive","command":"info","data":{"path":"D:\\path\\to\\Archive.ba2","family":"fo4","version":1,"format":"GNRL","compression":"Zip","entry_count":42},"error":null}
```

### `list`

List archive entries, optionally with a glob filter and long metadata.

```powershell
bgs-archive --json list "D:\path\to\Archive.ba2" --filter "textures/**/*.dds" --long
```

Expected machine output shape:

```json
{"ok":true,"tool":"bgs-archive","command":"list","data":[{"path":"textures/example/diffuse.dds","size":4096,"compressed":true}],"error":null}
```

### `extract`

Extract to a chosen directory. Use filters to keep agent runs bounded.

```powershell
bgs-archive --json extract "D:\path\to\Archive.ba2" --out "D:\work\archive-extract" --filter "meshes/**/*.nif"
```

Expected machine output shape:

```json
{"ok":true,"tool":"bgs-archive","command":"extract","data":{"output_dir":"D:\\work\\archive-extract","extracted_count":1,"paths":["meshes/example/static.nif"]},"error":null}
```

### `pack`

Pack a directory into a supported output. The output path must be inside an MO2 mod overlay when the result is game-local content.

```powershell
$overlay = "D:\ModOrganizer\mods\My Packed Assets"
bgs-archive --json pack "$overlay\source-assets" "$overlay\Data\MyPackedAssets - Main.ba2" --game fallout4 --format gnrl --compress zip
```

Expected machine output shape:

```json
{"ok":true,"tool":"bgs-archive","command":"pack","data":{"out_archive":"D:\\ModOrganizer\\mods\\My Packed Assets\\Data\\MyPackedAssets - Main.ba2","family":"fo4","version":1,"entry_count":12},"error":null}
```

Unsupported DX10/GNMF pack example:

```powershell
bgs-archive --json pack "$overlay\source-assets" "$overlay\Data\Textures.ba2" --game fallout4 --format dx10
```

Expected result:

```json
{"ok":false,"tool":"bgs-archive","command":"pack","data":null,"error":{"code":"unsupported","message":"dx10_pack not yet supported (Task A-DX10)"}}
```

## Coverage notes

- Read/extract: Oblivion BSA v103, Fallout 3/New Vegas/Skyrim LE BSA v104, Skyrim SE/AE BSA v105, Fallout 4 BA2 v1, Fallout 4 NG BA2 v7/v8, Fallout 76 BA2 v1, Starfield BA2 v2 GNRL/v3 DX10.
- Pack/write: TES3, TES4-family BSA versions, and FO4-family GNRL BA2 v1/v2/v7/v8.
- DX10 and GNMF packing are not supported. Extracting those formats is supported.

## Safe workflow pattern

1. Run `bgs-archive --json capabilities`.
2. Run `info` on the source archive.
3. Run `list --filter ...` to bound the exact asset set.
4. Extract into a workspace or overlay staging folder.
5. If packing, write only to `<MO2_Root>/mods/<mod-name>/Data/...`.
6. Run `info` and `list` on the packed archive as readback before reporting success.

Remember: game `Data` and Stock-Game trees are read-only real state. MO2 overlays are the correct Vault-Tec-approved safety containment chamber.
