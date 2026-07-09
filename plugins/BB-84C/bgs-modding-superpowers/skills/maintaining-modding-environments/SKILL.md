---
name: maintaining-modding-environments
description: "Use after first-run for ongoing modpack maintenance: update/install KB packs, author or register custom/mod KB packs, maintain localization glossary KBs for translator use, prune KB cache, health-check the environment, version-pin KB/tooling, or handle recurring BGS modding environment care."
---

# Maintaining Modding Environments

## When to use

- The environment is already set up and the user asks to maintain, refresh, update, or health-check it.
- The user says "register custom pack", "install my KB pack", "set `BGS_KB_USER_PACKS`", or asks how to author a local KB pack.
- The user asks how to maintain a mod knowledge base, a translator glossary KB, or a third-party localization KB for Skyrim/Fallout/Starfield.
- The user asks to install, upgrade, repair, or verify the standalone
  `xtl`/`bgs-translator` CLI after first-run.
- The user asks to check or apply knowledge-base updates after first-run.
- The user asks to prune the KB cache or clean old pack versions.
- The user asks whether to pin a KB pack version, follow latest, or handle a `minPluginVersion` warning.

## What this skill replaces

Use `setting-up-bgs-modding-environment` for first-run: MO2 detection, control-plane install, visible MO2 launch, first xEdit acquisition, first KB pack acquisition, and first semantic smoke.

This skill owns ongoing care after that first-run boundary: KB updates, cache hygiene, custom-pack authoring and registration, translator CLI maintenance, recurring environment health checks, and version-pinning advice.

## Translator CLI maintenance

`xtl` is the standalone AI translation CLI/Web GUI launcher. It is published on
PyPI as `bgs-translator`; the portable plugin may include translator-facing
skills, but a fresh user machine still needs the Python package installed before
high-speed agents can call `xtl`.

Start every maintenance pass with an explicit readback:

```powershell
# Check whether xtl is installed and can report its version/capabilities.
xtl version

# Inspect top-level commands before choosing a workflow.
xtl --help
```

If `xtl` is missing or too old, prefer an isolated user-level CLI install:

```powershell
# Install the current release-candidate build as an isolated command-line tool.
pipx install bgs-translator==0.9.0rc1

# Upgrade an existing pipx-managed xtl install when a newer stable build exists.
pipx upgrade bgs-translator
```

If `pipx` is unavailable, or the user explicitly wants `xtl` inside a project
virtual environment, use Python's package installer from that environment:

```powershell
# Install or upgrade xtl inside the selected Python environment.
py -3.12 -m pip install --upgrade bgs-translator==0.9.0rc1
```

For a future stable release, use the unpinned package name for normal installs:
`pipx install bgs-translator`, `pipx upgrade bgs-translator`, or
`py -3.12 -m pip install --upgrade bgs-translator`. Do **not** use broad
`--pre` during routine maintenance; it can allow prerelease dependency versions
that were not part of the tested translator build. Pin an exact prerelease only
when the user intentionally wants that version.

After any install or upgrade, inspect subcommand help instead of assuming
specific option values:

```powershell
# Verify provider-profile setup options, including all supported SDK kinds.
xtl profile add --help

# Verify web GUI launch options and ports.
xtl gui --help

# Verify batch controls before telling an agent to submit or resume work.
xtl batch --help
```

If a GUI or background translator service gets into an inconsistent state,
restart it with the repo's reusable helper instead of inventing process-kill
steps:

```powershell
# Restart the translator GUI/service stack using the project helper.
pwsh tools\bgs-translator\scripts\restart-web-gui.ps1 -Port 7847
```

If that helper is absent in an older checkout, fall back to the current
`using-bgs-translator` instructions for launching `xtl gui`, then file a note in
the environment maintenance log that the helper should be added or backported.

## Check + apply KB updates

1. Start with `bgs_kb_status({})` to see loaded packs, versions, cache root, user roots, and warnings.
2. If `bgs_kb_check_updates` exists, call it for the installed pack IDs. Surface available updates, `breakingChange`, and release URLs before taking action.
3. If `bgs_kb_check_updates` is not present yet (pre-KB-6), check GitHub Releases for `bgs-modding-superpowers` KB pack artifacts and `manifest-index.json`. Do not invent release names.
4. Before installing or replacing a pack, get user consent for the download / cache mutation.
5. If `bgs_kb_install_pack` exists, use it with an exact `{ packId, version }`. Prefer `dryRun: true` before live install when the tool supports it.
6. If the install tool is not present yet, download the Release asset manually only after consent, verify the published sha256, extract into the cache layout below, then restart or reconnect the MCP so discovery runs again.
7. After any update, run the health checks below.

## Cache hygiene

Cache root (all platforms — unified with `xtl` / `bgs-translator`):

```text
~/.bgs-modding-superpowers/kb/packs/<packId>/<version>/
```

The legacy Windows-only cache at `%LOCALAPPDATA%/bgs-modding-superpowers/kb/packs/`
is **no longer used**. If `bgs_kb_status` surfaces packs that are not visible to
`xtl batch plan`, suspect a legacy cache and either:

- move the directory tree from `%LOCALAPPDATA%/bgs-modding-superpowers/kb/` to
  `~/.bgs-modding-superpowers/kb/`, or
- export the legacy root via `$env:BGS_KB_USER_PACKS` so the MCP keeps reading
  it as an additional read-only root while the user finishes migrating.

Each version directory contains `manifest.json`, `records/`, and `kb.sqlite`. Current policy: retain the current version and the immediately previous version as rollback/fallback. Prune versions older than that only after confirming the pack is not pinned by the user or referenced by a current modpack workflow.

Use the KB MCP CLI for routine pruning:

```powershell
# Preview which cached pack versions would be removed.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js prune-cache --dry-run

# Apply the prune after the user accepts the preview.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js prune-cache
```

The dry run should be surfaced before deletion when the user has not already approved cache mutation. The command keeps the highest version and the immediately previous version per pack, then removes older cached versions.

Do not delete `incoming/` while an install is running. If an install failed earlier and no installer is active, stale `incoming/` contents can be removed after surfacing the path to the user.

## Custom pack authoring + registration

Author records as:

```text
<pack-root>/records/<domain>/<id>.md
```

Record frontmatter uses the same schema as official packs under `knowledge/bgs-kb/schema/record.schema.json`: stable `id`, `title`, `domains`, `appliesTo`, `canonical`, `sources`, `lastReviewed`, and `schemaVersion` are the important fields to check first.

Every pack needs a `bgs-kb-meta.yml` at the pack root. Minimum fields:

```yaml
packId: user-my-pack
displayName: My Modpack Knowledge
version: 2026.06.02
schemaVersion: 1
minPluginVersion: 0.2.0
```

Reserved official pack IDs: `bgs-kb-core`, `bgs-kb-skyrim`, `bgs-kb-fallout4`, `bgs-kb-fallout3-fnv`, `bgs-kb-starfield`. End-user packs must not use the `bgs-kb-*` namespace; recommend a `user-*` prefix.

Build the pack:

```powershell
# Build kb.sqlite and manifest.json from the pack's records/ tree.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js build <pack-root>
```

This produces `kb.sqlite` and `manifest.json` next to `records/`.

Validate and inspect:

```powershell
# Validate every Markdown record against the official KB schema.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js validate <pack-root>

# Inspect pack metadata, counts, games, and domains.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js info <pack-root>
```

Important `BGS_KB_USER_PACKS` semantics: each entry is a directory that contains one or more pack directories, not a pack directory itself. Multiple roots are separated by `;` on Windows.

Worked example:

```text
C:\my-kb-roots\
  my-custom-pack\
    bgs-kb-meta.yml
    manifest.json
    kb.sqlite
    records\
      load-order\
        my-local-rule.v1.md
```

Set:

```powershell
# Point discovery at the directory that contains one or more pack folders.
$env:BGS_KB_USER_PACKS = "C:\my-kb-roots"
```

Do not set it to `C:\my-kb-roots\my-custom-pack`; that points at the pack itself and discovery will look one level too deep.

After registration, restart/reconnect the MCP so pack discovery runs, then call `bgs_kb_status({})` and verify the custom pack appears with the intended `packId`.

## Pack discovery + collision recovery

`bgs_kb_status({})` may report two warning codes when discovery sees the same `packId` at multiple roots:

| Code | Meaning |
|---|---|
| `pack_id_overridden` (MEDIUM, informational) | Multiple sources for the same `packId`; precedence picked a winner automatically and listed the loser(s). All packs still load. |
| `pack_id_collision` (HIGH, fail-closed fallback) | Precedence could not choose a winner — should be rare; all colliding copies are refused. |

**Discovery precedence (apply in order):**
1. Sort candidates with the same `packId` by `builtAt` timestamp DESC — newest manifest wins.
2. Tie-break by root class: `bundled > cache > user`.

**Common cause: `install-pack` over an already-bundled `packId`.** Plugin distributions ship per-game packs (e.g. `bgs-kb-fallout4`) in the bundled tree. If a user runs `bgs_kb_install_pack({ packId: "bgs-kb-fallout4", ... })` to fetch a Release-channel update, the new version lands in the cache root `~/.bgs-modding-superpowers/kb/packs/bgs-kb-fallout4/<version>/`. On the next MCP restart:

- If the cache copy has a newer `builtAt` (the normal update case) → cache wins, bundled loser warning. No action needed.
- If the bundled copy is somehow newer (e.g. you pulled a plugin update that shipped a newer KB) → bundled wins, cache becomes the loser. To make the cache copy authoritative, install a newer Release or remove the stale cache copy.

**Other causes:**

- Two `$BGS_KB_USER_PACKS` parent directories contain pack folders with the same `packId` → warning per loser.
- Manual file copy of a pack between roots without removing the original.

**Preview before restarting MCP:** the bgs-kb-mcp CLI exposes a read-only `dev-status` subcommand that shows the same discovery decision the MCP would make, without requiring a server restart:

```powershell
# Preview every discovered packId, every candidate source, and which one would win.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js dev-status

# Filter to one pack id (useful before install-pack or before editing user packs).
node <plugin>\tools\bgs-kb-mcp\dist\cli.js dev-status --pack bgs-kb-fallout4

# Machine-readable output for scripting.
node <plugin>\tools\bgs-kb-mcp\dist\cli.js dev-status --json
```

**Recovery patterns:**

- **Want the cache copy to win**: ensure its `builtAt` is newer than the bundled copy's (run `bgs_kb_install_pack` for a fresh Release version), restart MCP, verify.
- **Want the bundled copy to win**: remove or rename the cache pack directory, restart MCP.
- **Two user roots collide**: drop one parent from `$BGS_KB_USER_PACKS`, or rename the colliding pack folder to a unique `packId` (after also updating its `bgs-kb-meta.yml`), restart MCP.
- **Pre-flight before authoring or installing**: always run `dev-status --pack <packId>` first — it surfaces collisions before the next MCP restart turns them into status warnings.

Do not delete cache copies aggressively as a first-line fix; the precedence rule selects automatically, so warnings are usually informational, not blocking.

## Localization and translator KBs

Localization glossary packs are KB packs whose SQLite store includes
`glossary_entries` and `glossary_aliases`. They feed `bgs-translator` RAG so an
LLM receives canonical terms such as places, factions, item names, UI concepts,
and do-not-translate entries. Put this guidance here, not in
`using-bgs-translator`, because the same maintenance rules apply to official,
mod-specific, and third-party glossary packs.

Official bundled policy:

- `bgs-l10n-starfield-zhhans` is the only official zh-Hans glossary pack we
  ship from vanilla game data because Starfield is the only supported BGS game
  with official Simplified Chinese localization.
- Do not fabricate official Skyrim/Fallout4 Chinese packs. If the user wants
  them, create third-party/user packs with explicit source, license, scope, and
  review notes.
- The Starfield official pack is large and should be distributed through KB
  Release artifacts, not copied into the portable plugin tree.

For a mod-specific translator KB, prefer a user namespace such as
`user-l10n-<game>-<mod>-zhcn`. Include only the mod's accepted terminology,
character/place names, recurring UI labels, and do-not-translate terms. Do not
dump every translated sentence into a term KB unless the user explicitly wants a
translation-memory style pack and accepts the recall/noise tradeoff.

For a third-party game localization KB, require:

- source language, target language, game, source project/version, and license;
- provenance in `bgs-kb-meta.yml` and in generated notes;
- a stable pack id outside reserved `bgs-kb-*` official namespaces;
- a small sample query after registration to verify the pack is discoverable.

If the input is an xTranslator SST dictionary, the translator tool has a
one-shot builder that creates the glossary SQLite shape directly:

```powershell
# Build a user-maintained glossary pack from an SST dictionary.
py -3.12 tools\bgs-translator\bgs_translator\tools\xtranslator_sst_to_kb_pack.py `
  --input "D:\path\to\source_english_chinese.sst" `
  --output-dir "C:\my-kb-roots\user-l10n-skyrim-thirdparty-zhcn" `
  --pack-id user-l10n-skyrim-thirdparty-zhcn `
  --display-name "User Skyrim zh-CN Localization Glossary" `
  --game SkyrimSE `
  --source-lang en `
  --target-lang zh-cn
```

Then set `BGS_KB_USER_PACKS` to the parent root, restart/reconnect the MCP, and
query a known term. For translator-only packs, use `xtl`/translator glossary
smokes as the stronger check because `bgs_kb_query` only searches Markdown-style
records unless the MCP has been upgraded for glossary-table queries.

## Official KB release maintenance

For project maintainers cutting a KB Release, use the release staging script:

```powershell
# Rebuild source-record packs, verify prebuilt glossary packs, zip all packs,
# and write dist/kb-release/manifest-index.json.
pwsh scripts/build-kb-release.ps1 -Force
```

The script includes the generated Starfield zh-Hans glossary pack in the release
index but does not rebuild it from Markdown records. If `kb.sqlite` hash
verification fails, regenerate that pack from its approved source SST before
publishing. The script prints the exact `gh release create ...` command; review
the staged `manifest-index.json` before running that network-side publish.

## Version-pinning advice

Follow latest when the user wants current general guidance and accepts normal KB refresh cadence.

Pin a specific pack version when a modpack release, guide, benchmark, or reproducibility note depends on exact advice staying stable. Record the pin in the modpack dev-log or release docs.

If a new pack's `minPluginVersion` exceeds the installed plugin version, warn and stop. Do not auto-upgrade the plugin. Offer choices: update the plugin with user consent, keep the older pack version, or pin the previous version until the plugin can be upgraded.

KB cadence is independent of plugin cadence. A new KB pack can be consumed when `schemaVersion` and `minPluginVersion` are compatible; it does not automatically imply an xEdit or MO2 change.

## Health checks

Quick KB smoke after maintenance:

```text
bgs_kb_status({})
bgs_kb_query({ query: "plugins", maxResults: 3 })
```

Expected: at least one loaded pack, no unexpected collision / integrity warnings, and at least one query hit. If the target game is known, include the game filter, for example:

```text
bgs_kb_query({ query: "plugins", games: ["Fallout4"], maxResults: 3 })
```

For custom packs, query a term from one of the custom records and verify hits are tagged with the custom `packId`.

If maintenance touched MO2 or xEdit runtime state, also use the appropriate setup / xEdit skill checks. Do not treat KB health as proof of live load-order or plugin state.

## Anti-patterns + warnings

- Never write directly into Stock Game / vanilla game `Data`. Any game-local change goes through an MO2 mod overlay or overwrite surface.
- KB records are advisory. xEdit MCP readback remains authoritative for actual plugin, record, conflict, and load-order state.
- Do not use `BGS_KB_USER_PACKS` to point at a single pack directory; point it at a root containing pack directories.
- Do not use reserved `bgs-kb-*` pack IDs for local packs.
- Do not install or upgrade KB packs with a `minPluginVersion` the current plugin does not satisfy.
- Do not delete all old cache versions; keep current + previous unless the user explicitly chooses otherwise.

## Refreshing Nexus update state without opening MO2 (Option B)

Use this when the user wants fresh `newestVersion`, `nexusFileStatus`,
`lastNexusQuery`, and `lastNexusUpdate` metadata without opening MO2 and running
`Tools -> Check All for Updates`.

Why this exists: mobase's Python API does not expose the GUI update-check
trigger, and three of the four timestamp fields are not on the abstract
`IModInterface`. See KB record
`install-planning.nexus-direct-api-update-check.v1`. The direct Nexus API read
path works for both Free and Premium accounts; these read endpoints are not
Premium-gated.

Prerequisite: the user must already have Nexus auth configured in MO2. That same
MO2 credential store is the API-key source for the agent; see the next section.

Endpoints used:

```text
GET https://api.nexusmods.com/v1/games/{game_domain}/mods/updated.json?period=1m
GET https://api.nexusmods.com/v1/games/{game_domain}/mods/{id}.json
```

The first endpoint is one bulk call to discover recently updated mods. The
second endpoint is one per-mod call for fresh metadata. Nexus' rate budget is
20,000 calls/day; a full 300-mod refresh is about 301 calls and is comfortable.

Per-mod `meta.ini` update shape:

```powershell
$statusMap = @{ "published"=1; "hidden"=9; "removed"=6; "wastebinned"=6; "under_moderation"=9 }
$mod = Invoke-RestMethod -Uri "https://api.nexusmods.com/v1/games/starfield/mods/$modid.json" -Headers $headers
$statusInt = if ($statusMap.ContainsKey($mod.status)) { $statusMap[$mod.status] } else { 1 }
$nowIso = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$updatedIso = [DateTimeOffset]::FromUnixTimeSeconds($mod.updated_timestamp).ToString("yyyy-MM-ddTHH:mm:ssZ")
$content = [IO.File]::ReadAllText($metaPath, [Text.UTF8Encoding]::new($false))
$content = $content -replace '(?m)^newestVersion=.*$', "newestVersion=$($mod.version)"
$content = $content -replace '(?m)^nexusFileStatus=.*$', "nexusFileStatus=$statusInt"
$content = $content -replace '(?m)^lastNexusQuery=.*$', "lastNexusQuery=$nowIso"
$content = $content -replace '(?m)^lastNexusUpdate=.*$', "lastNexusUpdate=$updatedIso"
[IO.File]::WriteAllText($metaPath, $content, [Text.UTF8Encoding]::new($false))
```

For production-grade automation, prefer the helper script:

```powershell
pwsh scripts\refresh-nexus-update-state.ps1 -MO2Root <path> -Game starfield
```

Caveat: direct `meta.ini` writes do not refresh MO2's in-memory
`ModInfoRegular` until the next `organizer.refresh()` or MO2 restart.

## Reading Nexus credentials from MO2's Windows Credential Manager store

MO2 stores Nexus credentials globally for the current Windows user, not per MO2
instance. All portable MO2 instances under the same Windows account share them.
MO2 uses `getWindowsCredential` / `setWindowsCredential` in `settings.cpp`.

Credential Manager targets:

| Target | Meaning |
|---|---|
| `ModOrganizer2_APIKEY` | Legacy 162-character personal API key. |
| `ModOrganizer2_NEXUS_OAUTH_TOKENS` | Compact JSON `{access_token, refresh_token, expires_at, scope, token_type}` from the modern OAuth flow. |

Read pattern:

```powershell
$signature = @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class CredMan {
  [DllImport("advapi32.dll", SetLastError=true, EntryPoint="CredReadW", CharSet=CharSet.Unicode)]
  static extern bool CredRead(string target, uint type, uint flag, out IntPtr cred);
  [DllImport("advapi32.dll")] static extern void CredFree(IntPtr p);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct CREDENTIAL { public uint Flags,Type; public IntPtr TargetName,Comment; public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten; public uint CredentialBlobSize; public IntPtr CredentialBlob; public uint Persist,AttributeCount; public IntPtr Attributes,TargetAlias,UserName; }
  public static string Read(string t) { IntPtr p; if (!CredRead(t,1,0,out p)) return null; try { var c=(CREDENTIAL)Marshal.PtrToStructure(p,typeof(CREDENTIAL)); byte[] b=new byte[c.CredentialBlobSize]; Marshal.Copy(c.CredentialBlob,b,0,(int)c.CredentialBlobSize); int nz=0; for(int i=1;i<b.Length;i+=2)if(b[i]==0)nz++; return nz>(b.Length/4)?Encoding.Unicode.GetString(b):Encoding.UTF8.GetString(b); } finally { CredFree(p); } }
}
'@
Add-Type -TypeDefinition $signature -Language CSharp
$apiKey = [CredMan]::Read("ModOrganizer2_APIKEY")
$oauthJson = [CredMan]::Read("ModOrganizer2_NEXUS_OAUTH_TOKENS")
```

Verification call:

```powershell
Invoke-RestMethod -Uri "https://api.nexusmods.com/v1/users/validate.json" -Headers @{ APIKEY = $apiKey }
```

Expected fields include `user_id`, `name`, `is_premium`, and `is_supporter`.

[WARNING]
Reading user credentials requires explicit user consent. Mask the key in any
logged output, for example `d0Ra...72d4 (len=162)`. Recommend key rotation after
the session if there is any leak risk.

Failure modes:

- `cmdkey /list | findstr nexus` returns nothing because the target name has no
  `nexus` string. Use `cmdkey /list | findstr ModOrganizer2` instead.
- HKCU registry entries such as `HideCreateInstanceIntro` are cosmetic flags,
  not credentials.
- `ModOrganizer.ini` `[Settings]` has no auth fields.
- If `CredRead` returns null, Nexus auth is not set up in MO2 yet. Direct the
  user to `Settings -> Nexus -> Connect to Nexus`.

See KB record `install-planning.mo2-windows-credential-mining.v1`.

## Script Extender (xSE) update workflow — game-root drop, runtime-pinned

Use this when Steam updates the game runtime and the existing xSE DLL no longer
matches it. The signal is a launch refusal through the xSE loader because the
DLL runtime tag does not match the current `<game>.exe` `FileVersion`.

Detection:

```powershell
# Current xSE version (filename pattern)
Get-ChildItem "$gameRoot\sfse_*.dll" | Select Name  # e.g. sfse_1_15_222.dll = SFSE for runtime 1.15.222

# Current Steam runtime
(Get-Item "$gameRoot\Starfield.exe").VersionInfo.FileVersion  # e.g. 1.16.244.0

# If they do not match, update is needed.
```

Latest-version sources: silverlock.org points to Nexus mod `#106` for SFSE,
`#100216` for SKSE64, and `#42147` for F4SE.

Update workflow:

1. Get the latest `file_id` from
   `/v1/games/{game}/mods/{xse_mod_id}/files.json`; use the file with
   `category_name=MAIN`.
2. Premium: call
   `POST /v1/games/{game}/mods/{xse_mod_id}/files/{file_id}/download_link.json`.
   The response is an array of seven CDN mirrors (Chicago, Amsterdam, Prague,
   LA, Miami, Dallas, plus Nexus CDN). Pick the first URL.
3. Free: open the Nexus page in a browser, click manual download, and save the
   `.7z` to a known location.
4. Extract the `.7z`. Gotcha: the archive expands to an `<xse>_<version>/`
   subdirectory, such as `sfse_0_2_21/`, not a flat folder. Glob-find files:
   `Get-ChildItem -Recurse -Filter "sfse_*.dll" | Select-Object -First 1`.
5. Backup current game-root xSE files to
   `<MO2_Root>\.backups\sfse-<oldver>_pre-<newver>-update_<timestamp>\`.
6. Copy the new DLL, readme, and whatsnew files to the game root. Skip files
   with unchanged sha256; the `<xse>_loader.exe` often does not change between
   minor versions.
7. Delete the old runtime DLL. This is optional but recommended for cleanliness;
   the loader auto-picks by runtime match and does not need the old DLL.
8. Verify sha256 for all four game-root files against staging.

### After SFSE: the cascade is the principle

A game runtime bump is a dependency cascade, not a single-file event. xSE is
only the first layer. Address Library and every runtime-bound DLL plugin also
bind to runtime-specific addresses, so a correct maintenance pass follows the
chain until the launch dialog stops reporting downstream leaks.

Read the chain this way:

1. **xSE binary** is the game-root layer and must match `<game>.exe`.
2. **Address Library** (Nexus mod #3256 for Starfield, #32444 for SkyrimSE,
   #47327 for Fallout4) is a normal MO2 mod projected into
   `Data\SFSE\Plugins\`. It supplies `versionlib-<runtime>.bin` for the
   current runtime.
3. **SFSE/SKSE/F4SE plugin mods** each ship their own DLL and may need an
   author-side rebuild.

The SFSE Plugin Loader dialog is the cascade readback surface:

- `address library needs to be updated` means the plugin could not find the new
  versionlib file; update Address Library first.
- `incompatible with current version of the game` means the plugin DLL itself
  is behind the game runtime; investigate whether the author has released a
  compatible build.

For the actual update of each SFSE plugin mod, the mechanical pattern remains:
- Premium API: `POST /v1/games/{game}/mods/{id}/files/{file_id}/download_link.json`
- Extract to staging (remember the 7z subdirectory gotcha noted above)
- Backup current MO2 mod folder contents
- Replace files in mod folder
- Update meta.ini's `version`, `newestVersion`, `installationFile`, `lastNexusUpdate`
- If folder name encodes a version (for example `<modname> - AddLib 18` or
  `<modname> - Game version 1.15.222`), rename folder and update `modlist.txt`
  to match.

If Nexus reports `status=not_published` or `status=hidden`, treat it as a
continuity investigation signal, not an instant disable verdict. Check whether
the same author republished or moved the release before proposing replacement.

### Intent-aware mutation methodology

A mod update is complete only when the observed post-state satisfies the intent
that motivated the update. Replacing files proves one effect; it does not prove
runtime compatibility, curator-visible classification, metadata consistency, or
enablement.

After acting, ask: **did this satisfy the intent across all dependent MO2 state
dimensions, or only the dimension I directly touched?** The dependent dimensions
usually include:

- files in the mod folder;
- `meta.ini` version/source/status fields and visible annotations;
- folder name when it encodes version or runtime support;
- `modlist.txt` line text after any rename;
- separator ownership, especially for mods previously parked in
  `版本已过期`, `等待作者更新`, or `[弃用]`;
- enable flag when the original disable reason has been resolved;
- for DLL plugins, the author's claimed runtime support versus the local game
  runtime.

This is a ReAct-style observation rule at the level of intent, not a rote
checklist. If observation shows that only files changed while the mod remains in
a waiting separator, still disabled, or still behind the current runtime, report
the intent gap and propose the next reconciliation step before declaring done.
Do not trust an action return value or a delegated fixer's summary as proof;
read `modlist.txt`, read affected `meta.ini` files, and use launch readback when
runtime compatibility is load-bearing.

Cross-link: KB record `install-planning.mod-update-post-state-discipline.v1` for the full discipline.

### Placeholder dummy mod for xSE binary tracking (curator convention, optional)

BB84's personal pattern: keep an empty MOD folder under `<MO2Root>/mods/<XSE
Name> <runtime-tag>/` (e.g. `Starfield Script Extender 1-15-222/`) with a
single `sfse_<binary-ver>/` empty subdir + a complete `meta.ini` carrying
the real `modid=106` + `version=` + `installationFile=` + nexus-side
metadata. Effect: the MO2 mod list visibly tracks the current SFSE binary
version even though the actual SFSE binaries live in game root and are
otherwise invisible to MO2's update-tracking. On each xSE update, rename
both the outer folder and the inner marker dir, and update the meta.ini.
This is a curator preference, not a required workflow.

[WARNING]
This writes to the real game install, for example
`D:\SteamLibrary\steamapps\common\<game>\`. It requires explicit per-session
user confirmation. xSE has no MO2 VFS overlay path: the loader must spawn
`<game>.exe`, so it has to live next to it.

For production-grade automation:

```powershell
pwsh scripts\install-xse-update.ps1 -GameRoot <path> -XseMod sfse|skse|f4se|nvse
```

See KB record `engine.xse-update-workflow.v1`.

## xEdit binary upgrade workflow — sister of xSE upgrade, but tools-tree-local

Use this when the user wants to verify or upgrade the xEdit installation
without launching the MO2 GUI by hand. Sister flow to xSE upgrade but with
different mechanics: xEdit lives in `<MO2_Root>/tools/xEdit/` (NOT game root,
NOT under STOCK001 protection), and its runtime carries a versioned binary
cache that must be invalidated on every binary swap or the daemon launches
against a stale cache and either crashes or returns wrong data.

### When to check

- The user explicitly asks to verify / upgrade xEdit.
- A scheduled environment health pass is running.
- The xEdit MCP daemon fails to launch, crashes mid-session, or returns
  unexpected protocol errors against a load order that worked before.
- New automation features are needed (multi-pattern filters, reverse
  navigation, WRLD parent coords, etc. — anything past the contract version
  the deployed binary supports).

### Stale detection — SHA-256 hash comparison

`Get-Item.VersionInfo.FileVersion` is unreliable for xEdit because the
contrib fork ships multiple builds under the same `4.1.5.0` / `4.1.6` label.
Use SHA-256 against the reference source:

```powershell
$mo2Bin     = "$MO2_Root\tools\xEdit\SF1Edit64.exe"
$refSource  = "D:\TES5Edit-contrib\Build\xEdit64.exe"   # OR the path returned by fetch-xedit-release.ps1
$mo2Hash    = (Get-FileHash -LiteralPath $mo2Bin -Algorithm SHA256).Hash
$refHash    = (Get-FileHash -LiteralPath $refSource -Algorithm SHA256).Hash
if ($mo2Hash -ne $refHash) {
  Write-Warning "xEdit stale: MO2 has $($mo2Hash.Substring(0,16))... reference has $($refHash.Substring(0,16))..."
}
```

Also surface mtimes for human readability — a 10-day gap with non-matching
hashes is a real version drift, not a build metadata glitch.

For the `xEditHookBridge.dll`: compare against the plugin-tree source
`<plugin>\tools\xedit-hook-bridge\dist\xEditHookBridge.dll`. If hashes match,
no swap needed. The HookBridge is owned by THIS plugin and follows the
plugin's release cadence, not the xEdit binary's.

### Reference source — contrib build vs release channel

Two reference sources exist:

1. **Local dev build at `D:\TES5Edit-contrib\Build\`** — the contrib fork's
   continuously-rebuilt artifacts. Captures unreleased features (contract
   0.18 → 0.19 → 0.20 additions, WRLD parent, reverse navigation, etc.) and
   bug fixes. Use this when the user is developing against the latest
   automation surface or needs features not yet in a tagged release.

2. **GitHub release artifacts via `fetch-xedit-release.ps1`** — the
   `BB-84C/TES5Edit` tagged-release stream. Stable, reproducible, ships
   with a manifest. Use this for end-user installs, reproducible modpack
   build chains, or any scenario where the user is not the binary's author.

For BB84's developer workstation: contrib build is canonical because BB84
authors the contrib fork. For end-user installs: release channel is
canonical. The skill should ask which source the user wants when ambiguous.

### Upgrade workflow

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'

# 1. Backup current tools/xEdit/ (full mirror, mtimes preserved)
robocopy "$MO2_Root\tools\xEdit" "$MO2_Root\tools\xEdit.backup-$ts" /MIR /NFL /NDL /NJH /NJS

# 2. Swap binaries (rename to game-specific filename so xEdit auto-detects mode)
Copy-Item "$refSource\xEdit64.exe" "$MO2_Root\tools\xEdit\SF1Edit64.exe" -Force  # Starfield
Copy-Item "$refSource\xEdit64.exe" "$MO2_Root\tools\xEdit\xEdit64.exe"   -Force
Copy-Item "$refSource\xEdit.exe"   "$MO2_Root\tools\xEdit\xEdit.exe"     -Force

# (For other games: FO4Edit64.exe, SSEEdit64.exe, etc. — the xEdit binary
#  detects game mode from its filename when launched directly.)

# 3. (Optional) Swap HookBridge.dll if hash differs from plugin-tree source
& "<plugin>\scripts\install-xedit-hook-bridge.ps1" -MO2Root "$MO2_Root"

# 4. INVALIDATE CACHE — mandatory after any binary swap
$cacheDir = "$MO2_Root\overwrite\<Game>Edit Cache"  # e.g. SF1Edit Cache
Move-Item -LiteralPath $cacheDir "$MO2_Root\overwrite\<Game>Edit Cache.stale-$ts" -ErrorAction SilentlyContinue
```

### Cache lifecycle — REQUIRED reading before launch

xEdit's binary cache lives at `<MO2_Root>/overwrite/<Game>Edit Cache/`
(e.g. `SF1Edit Cache/`, `FO4Edit Cache/`, `SSEEdit Cache/`). Files are
named `<load-order-hash>_<plugin>_<plugin-hash>_g<cp>_t<cp>_l<cp>_<lang>.refcache`.

**The cache is binary-version-bound.** A binary upgrade invalidates every
cache file because:

- xEdit's internal record-parsing logic may have changed (new contract
  features, fixes to malformed-data tolerance, etc.).
- The cache format itself may have evolved.
- Stale caches produce subtle wrong-answer bugs that look like xEdit
  protocol errors but are actually parser drift.

ALWAYS move the cache dir aside (don't delete — it's the safety net) before
the first launch after a binary swap. Pattern:
`overwrite/<Game>Edit Cache.stale-<timestamp>/`.

The cache will be rebuilt automatically on first launch. Once stable and
verified, the `.stale-*` backup can be removed in a future cleanup pass.

### First-launch timing (cold cache)

Cache-cold launch on a 175-plugin Starfield profile takes **9-10 minutes**.
This is real-time wall clock for xEdit to:

1. Parse every plugin in the load order.
2. Hash each plugin's records.
3. Write the per-plugin `.refcache` file.

The current xedit-mcp `xedit-client.ps1` has a **240-second timeout** for
daemon readiness. **First-launch on a real-world load order will exceed
this timeout and fail.**

Workaround options:

1. **Build cache via manual GUI launch first** (preferred for current
   tooling): run xEdit through MO2's normal launch path (either via
   `Mo2Mo2RunTool_tool` with the configured customExecutable, or have the
   user click the MO2 button). Wait until xEdit's window finishes loading
   (status bar shows "Background Loader: finished" or similar). Close
   xEdit. Then `xedit_start` will launch in <3 min wall-clock against the
   warm cache.
2. **Bump the timeout in xedit-client.ps1** if scripting around step 1 is
   undesirable. The relevant constant is documented in the xedit-mcp
   broker source.

### Polling discipline during cold-cache launch

`xedit_status({})` sends a lightweight read against the daemon's state file,
but the daemon's response handler is on the same Pascal thread that's
parsing the load order. **Aggressive polling during the cold-cache build
can stall or crash xEdit's parser.** Empirically observed on a 175-plugin
Starfield profile on 2026-06-27: 30-second poll cadence during cold-cache
build correlated with a parse hang requiring manual kill.

Polling discipline:

- During cold-cache build (first launch after binary swap): wait at least
  60 seconds between polls. Better: don't poll at all until 8+ minutes have
  elapsed, then check once.
- During cache-warm launch (subsequent launches): 30-60 second poll cadence
  is fine. Total launch time ~3 minutes.
- After `status: "ready"`: domain tools (`xedit_session`, `xedit_health`,
  `xedit_call`) can be called freely.

### Verification after launch

```text
xedit_health({})       -> { responsive: true, pingEnvelope: { ok: true } }
xedit_session({})      -> { gameMode: "Starfield", contractVersion: "0.20",
                            loadOrderSize: N, consentEnabled: false (read-only)
                                                or true (mutations allowed) }
xedit_dirty({})        -> { dirty: false, unsavedChangeCount: 0 }
```

Check `contractVersion` against the contract level the new binary should
have shipped. If contractVersion is lower than expected, the binary didn't
swap correctly OR the daemon picked up the wrong binary path.

### Clean shutdown — cache preserved

`xedit_stop({})` on a clean dirty state preserves the cache for the next
launch. Subsequent `xedit_start({})` will hit the warm cache and complete
in ~3 minutes. Do not delete the cache dir between sessions unless a
binary upgrade is happening.

### See also

- KB record `engine.xedit-binary-cache-lifecycle.v1` for the full
  binary-cache binding mechanism.
- KB record `engine.xedit-stale-detection-via-hash.v1` for the SHA-256
  comparison method against reference sources.
- KB record `tooling.xedit-contrib-build-vs-release-channel.v1` for the
  source-selection strategy.
- KB record `debugging.xedit-cold-cache-launch-timeout-and-polling.v1`
  for the 240s timeout + polling-discipline gotchas.

## meta.ini `comments=` vs `notes=` as visibility design

MO2 has two note-shaped fields because it has two different reading modes:
visibility-at-a-glance and detail-on-demand.

- **`comments=`** serves the at-a-glance mode. It appears in the mod-list
  Comments column, so it is the right place for short summaries, status tags
  (`[UPDATE→vX]`, `[WAITING-FOR-X.Y.Z]`), CC markers (`[CC]`, `[CC·汉化版]`),
  and other information the curator should see without opening a dialog.
- **`notes=`** serves the detail-on-demand mode. It appears only in the mod's
  properties Notes tab, so it is the right place for install procedure memos,
  FOMOD choice records, conflict-resolution notes, and verbose version history.

Choose the field by intended reader behavior. If the curator must see the fact
while scanning the list, use `comments=`. If the fact is reference material for
when the mod is already being inspected, use `notes=`. Automation that
synthesizes 1-2 sentence per-mod summaries from `nexusDescription` therefore
writes to `comments=` by default; putting those summaries in `notes=` makes the
list look empty even though the information exists.

## Post-patch loose-extract hygiene (game-install Data\ stale CK extracts)

After every BGS game patch, a standard maintenance pass should sweep the
game-install `Data\` tree for stale Creation Kit loose extracts. The full
methodology lives in KB record
`archive-precedence.stale-ck-extract-loose-files.v1`; the operational shape
for a maintenance pass is short:

The trap. When the curator installs the Creation Kit alongside the game, the
CK auto-extracts authoring-time loose files from `Tools\ContentResources.zip`
into `Data\` — `Data\Materials\` (`.mat`), `Data\Particles\` (`.psfx`),
`Data\Scripts\Source\` (`.psc`), plus editor metadata. Archive invalidation,
which any modded curator has enabled, makes those loose files override the
compiled BA2 databases at runtime. While the game version matches the CK
extract version this is invisible; the moment the game patches its compiled
material database, particle archive, or compiled scripts, the loose files
become stale references against the new BA2 and the runtime breaks silently
(purple/iridescent terrain, missing meshes, wrong VFX, subtle Papyrus drift).

The cheap diagnostic test. Before bisecting mods on any post-patch visual or
behavioral regression:

```powershell
# Inspect the game-install Data\ for stale CK extracts.
$gd = "<game-install>\Data"
Get-ChildItem -LiteralPath $gd -Directory |
  Where-Object { $_.Name -in @('Materials','Particles','Scripts','Source','Textures','EditorFiles','DataViews') } |
  ForEach-Object {
    $files = Get-ChildItem -LiteralPath $_.FullName -Recurse -File -ErrorAction SilentlyContinue
    $oldest = ($files | Sort-Object LastWriteTime | Select-Object -First 1).LastWriteTime
    "{0,-14}  files: {1,5}  oldest: {2}" -f $_.Name, $files.Count, $oldest
  }
```

Compare oldest mtime to the current patch's BA2 mtime. If older, the extract
is stale. If `Tools\ContentResources.zip` modification time matches the
current patch, the recovery path is intact — deletion is fully reversible.

The fix. Delete the stale extract trees from `Data\`. Runtime falls back to
BA2. For Starfield specifically the priority order is `Data\Materials\` →
`Data\Particles\` → `Data\Textures\` → `Data\Scripts\` (runtime impact),
then `Data\Source\`, `Data\DataViews\`, `Data\EditorFiles\` (CK-editor-only,
harmless to keep, harmless to delete).

[WARNING]
This writes to the real game install, for example
`D:\SteamLibrary\steamapps\common\<game>\Data\`. It requires explicit
per-session user confirmation. The action is reversible by re-extracting
`Tools\ContentResources.zip` into `Data\`, but the deletion itself is
destructive against the loose extracts that are currently there.

A cleaner long-term pattern: extract `ContentResources.zip` into a dedicated
Mod Organizer 2 mod folder (e.g. `mods/CK Resources Vanilla/`) so the CK
loose files can be toggled per-profile and never touch the real game install.

Cross-link: KB record `archive-precedence.stale-ck-extract-loose-files.v1`
for the full mechanism. KB record
`debugging.asymmetric-evidence-self-falsify.v1` for the diagnostic
discipline that prevents the trap from misleading bisection planning.

## meta.ini comment vs note field hygiene (HARD RULE)

Every time an agent touches a mod folder's `meta.ini`, two text fields exist
and they have STRICTLY DIFFERENT purposes. Putting content in the wrong field
breaks the curator's mental model of their own modpack.

**`comments=` = SHORT description of WHAT THE MOD DOES (the mod's CONTENT)**

- 1-2 sentences max
- Language: match the curator (Chinese for BB84-style packs, English otherwise)
- Shown in MO2 GUI mod-list "Comments" column (visible at a glance without clicking)
- Describes the mod's GAMEPLAY/VISUAL/SYSTEM effect, not its install metadata

Example (good): `调整起降过场镜头比例,提供更沉浸的驾驶舱视角与速度选项。`

**`notes=` = TIME-SENSITIVE markers + operational memory (the mod's STATUS)**

- Update history with datestamp + version diff + file_id
- Archive / obsolescence / version-tag-unsync / user-install / local-patch markers
- FOMOD choice records, conflict resolution memos, investigation findings
- Shown in Notes tab (hidden until clicked)
- MOST text per mod ends up here

Marker prefixes that ALWAYS belong in `notes=`, NEVER in `comments=`:

```
[UPDATED YYYY-MM-DD] x.y.z -> a.b.c | file_id N [MAJOR|MINOR|PATCH]
[ARCHIVED YYYY-MM-DD] reason
[OBSOLETE YYYY-MM-DD] reason
[FIXED YYYY-MM-DD] reason
[USER-INSTALLED YYYY-MM-DD] FOMOD picks / manual install footprint
[NEW-INSTALL YYYY-MM-DD] reactivation cluster context
[STALE YYYY-MM-DD] SC translation lags / lifecycle drift
[LOCAL-PATCH] curator's local fixup
[VERSION-TAG-UNSYNC] page-version-vs-file-version mismatch
[INVESTIGATION YYYY-MM-DD] analysis findings + anti-stale-fact note
[UPDATE→x.y.z] BB84's pre-existing update-pending arrow flag (marker is JUST the bracket; description after it belongs in `comments=`)
```

**bash extract-on-top update path MUST preserve existing `comments=`**:

When updating a mod's content (e.g. v1.3.1 → v1.3.2 via extract-on-top),
the helper MUST NOT overwrite `comments=`. Instead, APPEND the update marker
to `notes=` (preserving any pre-existing notes with `\n` separator).

Anti-pattern that destroyed BB84's curator descriptions on 2026-06-25:

```powershell
# WRONG — overwrites comments, destroys description
$content = [Regex]::Replace($content, '(?m)^comments\s*=.*$', "comments=[UPDATED ...] $versionDiff")
```

Correct pattern:

```powershell
# RIGHT — preserve comments, append marker to notes (Qt INI literal \n)
$newMarker = "[UPDATED $date] $oldVersion -> $newVersion | file_id $fileId"
$content = [Regex]::Replace($content, '(?m)^notes[\t ]*=[\t ]*(.*)$', { param($m) 
  $existing = $m.Groups[1].Value
  if ([string]::IsNullOrWhiteSpace($existing)) { "notes=$newMarker" }
  else { "notes=$newMarker\n$existing" }  # \n is literal backslash-n; Qt INI renders as newline
})
```

**Regex bug to avoid**: do NOT use `\s*` in INI line anchoring — it consumes
`\r\n` and captures content from the next line. Use `[\t ]*` for in-line
whitespace only:

```powershell
# WRONG — \s* crosses lines, leaks neighbour key's value into your match
$cmtM = [Regex]::Match($content, '(?m)^comments\s*=\s*(.*)$')

# RIGHT — [\t ]* stays on one line
$cmtM = [Regex]::Match($content, '(?m)^comments[\t ]*=[\t ]*(.*)$')
```

**Before any batch meta.ini migration**, write a 3-case unit-test fixture:

1. Pure marker only (`[ARCHIVED 2026-06-25] reason`) → expect comments empty, marker stays in notes
2. BB84 arrow style (`[UPDATE→2.0.0.0] 中文描述`) → expect comments has Chinese, notes has `[UPDATE→2.0.0.0]`
3. Mixed (description text first, then marker) → expect comments has description, notes has marker

Then dry-run on 3-5 sample mods spanning all three cases BEFORE batch dispatch.
Skipping this check is what destroyed 49 mods' Chinese descriptions in the
2026-06-25 buggy migration. See `.opencode/memory/45-mo2-mcp-internals.md`
rule 18 for the full incident postmortem.

### Qt QSettings INI quoting (silent display-empty trap)

MO2's backend uses Qt QSettings to parse meta.ini. Qt's INI parser conflates
a value that STARTS with `[` (e.g. `[UPDATED ...]`, `[CC]`, `[UPDATE→x.y.z]`)
with a section-header start (`[Section]`) and silently returns empty for that
key. MO2 GUI's Notes/Comments tab then shows blank, even though a raw text
preview of the same meta.ini clearly displays the value populated.

**Hard rule**: whenever a `comments=` or `notes=` value starts with `[`,
wrap the value in double quotes:

```
# BROKEN — Qt parses as empty, MO2 GUI shows blank
notes=[UPDATED 2026-06-25] 1.1.5.0 -> 1.2.77.0 [MAJOR] | file_id 61879
comments=[CC] Watchtower: Orbital.Strike\Fleet.Command

# CORRECT — Qt strips outer quotes, returns bracketed content; MO2 GUI displays correctly
notes="[UPDATED 2026-06-25] 1.1.5.0 -> 1.2.77.0 [MAJOR] | file_id 61879"
comments="[CC] Watchtower: Orbital.Strike\Fleet.Command"
```

Implementation rules:
1. **WRITE path**: before serializing a `comments=` / `notes=` line, check if
   the value's first non-whitespace char is `[`. If yes, emit double quotes
   around the value. If the value contains internal `"`, escape them as `\"`.
   Internal `\n` (literal backslash-n) IS preserved by Qt as a multi-line
   escape inside quoted strings and renders as a newline in MO2 GUI.
2. **READ path**: after reading a `comments=` / `notes=` line, strip a single
   leading and trailing `"` pair (if present) BEFORE parsing the value
   semantically. Unescape internal `\"` to `"`.
3. **Idempotence**: re-running the quoting step on an already-quoted value
   should be a no-op (`if ($val -match '^".*"$') { skip }`).
4. **Special cases**: values already starting with `@ByteArray(...)`,
   `<HTML>`, or other Qt-supported wrapper forms are left untouched — they
   have their own parsing path.

Reproduction: 2026-06-26 Xeno Master screenshot pair (BB84). 268-char notes
value with `[UPDATED ...]` start displayed empty in MO2 GUI. Adding double
quotes around the value fixed display immediately on MO2 refresh (no
restart). Sweep across BB84 Starfield modpack found 220 affected meta.ini
files; backups preserved at
`D:\Starfield MO2\.backups\meta-qt-quote-fix-20260626-003856\`.

Cross-link: KB record `engine.qt-ini-bracket-quote-requirement.v1` (TBD)
should codify this for end-users authoring their own meta.ini writers.

Cross-link: KB record `install-planning.mod-mutation-cleanliness-discipline.v1`
covers the broader 7-discipline mutation hygiene checklist that this hygiene
rule plugs into.

## See also

- `setting-up-bgs-modding-environment` — first-run MO2 / xEdit / KB acquisition orchestrator.
- `using-bgs-modding-superpowers` — session bootstrap, available tools, and hard BGS modding rules.
- `docs/internal/roadmap.md` — KB track status and phase closeouts.
- Deep reference: `docs/internal/superpowers/specs/2026-06-02-agentic-cross-game-kb-design.md`.
