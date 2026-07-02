---
name: setting-up-bgs-modding-environment
description: "Use on first install of this plugin, when MO2 or xEdit is not yet detected, when starting a new modpack project, or when the user says 'set up', 'install', 'bootstrap', 'configure', or 'initialize' the BGS modding environment. Orchestrates: MO2 detection and control-plane install, MO2 visible launch, optional xEdit download from BB-84C/TES5Edit, optional bgs-translator/xtl PyPI install, dev-log and release-changelog initialization, and end-to-end semantic smoke verification."
---

# Setting Up the BGS Modding Environment

This is the first-run bootstrap. Use it when:

- The user installed `bgs-modding-superpowers` and this is the first conversation
  in their project directory.
- A new modpack project is being set up from scratch.
- MO2 path is not yet known to the agent.
- The user explicitly asks to "set up", "install", "bootstrap", "configure", or
  "initialize" the BGS modding environment.
- A subsequent skill (e.g., `xedit-automation`) finds the environment incomplete
  and routes back here.

## Hard guardrails

- **Do NOT install MO2 yourself by default.** The default path is to detect MO2
  and, if absent, guide the human user to install it themselves. Agent-driven
  install requires explicit user consent ("yes, install MO2 for me").
- **Never write into the user's vanilla game install** (e.g.,
  `<Steam>/steamapps/common/<Game>/Data/`). All overlays go through MO2.
- **Treat the user's existing MO2 profile as canonical.** Do not silently mutate
  `profiles/<Profile>/plugins.txt`, `modlist.txt`, INIs, or load order.
- **Pause and surface state before each install action.** The user should always
  know which MO2 root, which profile, and which file is about to be touched
  before it happens.
- **MO2 must run visibly.** Never start MO2 in any background / hidden mode.
  The human owner needs to see and interact with the MO2 GUI. The launch helper
  `scripts/start-mo2.ps1` enforces this and surfaces "zombie" MO2 processes
  (running but no window) so they can be cleaned up before a fresh start.

## What the control plane actually is

The "MO2 control plane" we deploy in step 4 is a **Python MO2 plugin** plus a
**PowerShell broker**:

- `tools/mo2-control-plane/live-bridge/mo2_agent_control.py` — the actual MO2
  plugin. When MO2 loads it, the plugin opens a named pipe and starts publishing
  bootstrap runtime files. This is what the agent harness talks to.
- `tools/mo2-control-plane/broker/` — PowerShell IPC client used by
  `xedit-client.ps1`. Runs from the plugin checkout; no install step.

There is **no C++ DLL to build or deploy** at v0.1. A C++ kernel skeleton lives
under `docs/internal/future-c-kernel/` as a design note for later perf-critical
paths; it is intentionally unbuilt. If a previous agent told you to "build
Mo2AgentControl.dll first" — that was wrong. The Python plugin is the
integration.

## Workflow

### Step 1 - Detect MO2 install

Search for `ModOrganizer.exe` in common locations:

- `$env:LOCALAPPDATA\ModOrganizer*\ModOrganizer.exe`
- `D:\ModOrganizer*\ModOrganizer.exe`, `E:\ModOrganizer*\ModOrganizer.exe`,
  `C:\ModOrganizer*\ModOrganizer.exe`
- The user's Documents folder.
- The user's Desktop / common steam-library siblings.

If exactly one MO2 install is found, propose it to the user for confirmation.
If multiple, list them with paths and ask which is the target. If none, go to
step 2.

Persist the confirmed install root in conversation context as `MO2_Root`. All
subsequent steps reference this variable.

**Also surface the `BGS_MO2_ROOT` env-var requirement.** The `xedit` MCP server
needs to know `MO2_Root` so it can resolve `<MO2_Root>/tools/xEdit/xEdit.exe`
and `<MO2_Root>/profiles/<profile>/plugins.txt`. Without it, the MCP either
falls back to a stale dev-sandbox path (silent wrong-answer on dev clones) or
errors with a "MO2 sandbox root is not configured" message (on end-user
installs). Tell the user where to set it for their harness:

- **OpenCode**: add to the `xedit` MCP entry's env block in `opencode.json`:
  ```json
  { "mcp": { "xedit": { "env": { "BGS_MO2_ROOT": "<MO2_Root>" } } } }
  ```
- **Codex**: append to `~/.codex/config.toml`:
  ```toml
  [mcp_servers.xedit.env]
  BGS_MO2_ROOT = "<MO2_Root>"
  ```
- **Claude Code**: set the env var in the shell that launches Claude Code, or
  edit `<plugin-root>/.mcp.json` to add an `env` block on the `xedit` entry.

After the user sets it, the user must restart their harness session so the
MCP server picks up the new env. Confirm by calling `xedit_status({})` and
checking that the returned hint no longer mentions BGS_MO2_ROOT.

Per-call override is also available: `xedit_start({ moRoot: "<MO2_Root>", ... })`.
Useful for one-off testing, but the env-var path is what makes restarts and
subsequent sessions work without re-passing it.

### Step 2 - If MO2 absent: branch the user

Surface a `[BLOCKED]` notice and offer THREE paths, in order of preference:

**(a) Default - human install.** Provide the official MO2 release URL:
https://github.com/ModOrganizer2/modorganizer/releases/latest. Give the user
a brief setup outline (download installer, pick an install root outside Program
Files, launch once to initialize). Wait for the user to install and come back
with the path.

**(b) Agent-handled install (explicit user consent required).** Only if the
user says something like "yes, install MO2 for me, go ahead": download the
official MO2 installer to a temp location, run it (silent install where
supported), register the resulting path as `MO2_Root`. Surface every step
("downloading from ...", "installing to ...", "MO2 ready at ..."). Never
proceed without the explicit verbal consent.

**(c) No-MO2 mode.** If the user says "I do not need MO2 for this project"
(e.g., they are writing modpack docs / planning without a runtime), record
`MO2_Root = none`, continue through step 3 for KB target selection, then skip to
step 9 (dev-log / changelog init). Mark that any MO2-bound or xEdit-bound work
will be unavailable until they revisit this skill.

### Step 3 - First-run KB target selection and pack acquisition

Ask which target games the modpack should support. Use the exact game codes
when talking to KB tools where possible: `SkyrimLE`, `SkyrimSE`, `SkyrimAE`,
`SkyrimVR`, `Fallout4`, `Fallout4VR`, `Fallout3`, `FalloutNV`, `Starfield`.

The bundled `bgs-kb-core` pack is materialized inside the plugin tree at
`plugins/bgs-modding-superpowers/knowledge/bgs-kb/packs/core/`. No action is
needed for it; it appears in `bgs_kb_status` even before MO2 or xEdit are
configured.

Per-game packs (`bgs-kb-skyrim`, `bgs-kb-fallout4`, `bgs-kb-fallout3-fnv`,
`bgs-kb-starfield`) are published as GitHub Release artifacts on the
`BB-84C/bgs-modding-superpowers` repo. The KB MCP wraps the entire fetch +
sha256 verify + cache install in two tools — do **not** download zips by hand:

1. Map the chosen games to pack IDs:
   - `SkyrimLE` / `SkyrimSE` / `SkyrimAE` / `SkyrimVR` -> `bgs-kb-skyrim`
   - `Fallout4` / `Fallout4VR` -> `bgs-kb-fallout4`
   - `Fallout3` / `FalloutNV` -> `bgs-kb-fallout3-fnv`
   - `Starfield` -> `bgs-kb-starfield`

   Additionally, if the user has indicated a translation/localization workflow
   for any of these games (intent to run `xtl batch` against the game), add the
   corresponding localization pack. Today's released localization packs:
   - `Starfield` + Simplified Chinese -> `bgs-l10n-starfield-zhhans`
     (151k Bethesda-official terminology entries; RAG retrieval inside `xtl`
     depends on this pack — see `using-bgs-translator`.)

   These follow the same install path (`bgs_kb_check_updates` ->
   `bgs_kb_install_pack`) and the same on-disk cache layout as the per-game
   packs. Do not assume a localization pack is present just because the
   per-game pack is installed; check `bgs_kb_status` after install.

2. List what is available from the live release manifest:
   ```
   bgs_kb_check_updates({})
   ```
   This reads the published `manifest-index.json` and returns the latest
   `{ packId, version, sha256, url, breakingChange }` for every official pack.
   Surface the per-game-pack rows that match the chosen games before doing
   anything else.

3. Get **explicit** user consent before installing each pack ("yes, install
   `bgs-kb-skyrim`"). Pack install mutates `~/.bgs-modding-superpowers/kb/packs/<packId>/<version>/`
   (legacy `%LOCALAPPDATA%/bgs-modding-superpowers/kb/packs` is no longer used; the cache
   root is unified with `xtl`).

4. For each consented pack:
   ```
   bgs_kb_install_pack({ packId: "bgs-kb-skyrim", version: "<from check_updates>", dryRun: true })
   ```
   Verify the dry-run reports the expected version + sha256, then re-run
   without `dryRun` to actually install. The MCP downloads from the official
   release URL, verifies sha256, and lays the pack out in the versioned cache.

5. If `bgs_kb_check_updates` returns an empty or partial list for a game the
   user wanted (network failure, release not yet published), say so and
   continue with the bundled core pack. Do not improvise a download URL or
   `iwr` into the cache by hand.

Smoke test after selection / install:

```text
bgs_kb_status({})
bgs_kb_query({ query: "plugins", games: ["<chosen-game>"], maxResults: 3 })
```

Success criterion: `bgs_kb_status` lists every pack that was just installed
plus `bgs-kb-core`, and `bgs_kb_query` returns at least one hit. If only the
core pack is available, a core-pack hit is enough for first-run.

For routine update / prune / version-pinning work after first-run, route to
`maintaining-modding-environments` — it documents the full ongoing-care flow
on top of the same two MCP tools.

### Step 3A - Install or verify `xtl` for AI translation workflows

If the user plans to translate mods, or a downstream workflow routes into
`using-bgs-translator`, make sure the standalone translator CLI is available.
`xtl` is distributed on PyPI as the `bgs-translator` package; do not assume it
is present in a fresh machine just because this plugin is installed.

Start with a readback:

```powershell
# Check whether the translator CLI is already installed and can report capabilities.
xtl version
```

If `xtl` is missing, choose one install path:

```powershell
# Preferred user-level CLI install when pipx is available.
pipx install bgs-translator==0.9.0rc1

# Fallback when pipx is unavailable, or when the user wants xtl inside the active Python environment.
py -3.12 -m pip install bgs-translator==0.9.0rc1
```

For a future stable release, the same commands can omit the exact prerelease
pin, for example `pipx install bgs-translator` or
`py -3.12 -m pip install bgs-translator`. Do **not** use broad
`pip install --pre bgs-translator` as routine setup; it can opt unrelated
dependencies into prerelease builds. Pin an exact release candidate only when
that exact version is the intended runtime.

Verify after install:

```powershell
# Confirm xtl is on PATH and exposes the expected command surface.
xtl version

# Inspect the top-level help before choosing subcommands or options.
xtl --help

# Inspect provider-profile options instead of assuming a single SDK kind.
xtl profile add --help

# Inspect GUI launch options if the user wants the web translator.
xtl gui --help
```

If `xtl version` fails after a pipx install, surface the pipx PATH warning and
ask the user to reopen the shell/session, then retry. Once it passes, route
actual translation work to `using-bgs-translator`; this setup skill only
installs and smoke-checks the CLI.

### Step 4 - Install the MO2 control plane (Python + broker)

Once `MO2_Root` is known (path a or b), deploy the Python plugin:

```powershell
& "<plugin-root>/scripts/install-mo2-control-plane.ps1" -MO2Root "<MO2_Root>"
```

This deploys:

- `tools/mo2-control-plane/live-bridge/mo2_agent_control.py` -> `<MO2_Root>/plugins/`
- The `Mo2AgentControl/` support tree -> `<MO2_Root>/plugins/`
- `ModOrganizer.ini lock_gui=false` normalization.

After the script returns, list `<MO2_Root>/plugins/` and confirm
`mo2_agent_control.py` is present. The script will NOT install a `.dll` — that
is intentional (see "What the control plane actually is" above). If the script
errors, stop and surface it; do not continue.

### Step 5 - Start MO2 visibly

```powershell
& "<plugin-root>/scripts/start-mo2.ps1" -MO2Root "<MO2_Root>" -Profile "<Profile>"
```

The launcher script:

- Refuses to start if a visible MO2 is already running (use that one).
- If a zombie MO2 (running but no window) is detected, surfaces it and asks
  before killing — use `-KillStale` to skip the prompt.
- Starts MO2 with `-WindowStyle Normal` so the GUI is visible.
- Waits up to 30s for the main window to appear and reports its title.

Verify after launch: the user should see the MO2 GUI on their desktop. The
plugin's bootstrap runtime files should appear at
`<MO2_Root>/plugins/Mo2AgentControl/bootstrap/runtime/` within a few seconds:

- `status.json` -> `{ schemaVersion, state: "ok", mo2Pid }`
- `endpoint.json` -> `{ transport: "named-pipe", endpoint: "mo2-control-plane-<pid>" }`
- `capabilities.json` -> lists `launch.*`, `system.*` methods.

If those don't appear, the Python plugin didn't load. Check MO2's plugin
settings to confirm `mo2_agent_control` is enabled.

### Step 6 - Ask the user whether they want xEdit

xEdit is optional but high-value. Describe what it does so the user can make
an informed choice:

> "xEdit is the canonical editor for Bethesda plugin files (.esp / .esm / .esl).
> Modpack curators use it to resolve conflicts between mods, generate
> compatibility patches, flag plugins as ESL (light) to free up load-order
> slots, clean stray edits (ITM / UDR), and run Pascal-based bulk edits.
> With this plugin's bundled `xedit` MCP, your agent can drive xEdit
> programmatically - no GUI clicks required."

Then ask: "Would you like me to install xEdit?" - explicit consent gate.

If the user declines, skip to step 9.

### Step 7 - If yes: fetch xEdit from BB-84C/TES5Edit

The forked, agent-friendly xEdit lives at https://github.com/BB-84C/TES5Edit.
Fetch its latest release into the MO2 tools tree:

```powershell
& "<plugin-root>/scripts/fetch-xedit-release.ps1" -MO2Root "<MO2_Root>"
```

This downloads the latest release zip, extracts into
`<MO2_Root>/tools/xEdit/`, and verifies `xEdit.exe` exists post-extract. For
ongoing version pinning after first install, route to
`maintaining-modding-environments`.

### Step 8 - Deploy the xEdit hook bridge

`xEditHookBridge.dll` ships with THIS plugin (it is OWNED by
`bgs-modding-superpowers`, NOT by the xEdit fork). Co-locate it with
`xEdit.exe`:

```powershell
& "<plugin-root>/scripts/install-xedit-hook-bridge.ps1" -MO2Root "<MO2_Root>"
```

This copies `tools/xedit-hook-bridge/dist/xEditHookBridge.dll` into
`<MO2_Root>/tools/xEdit/`. The xEdit daemon will find it there at runtime.

### Step 9 - Initialize dev-log and release-changelog

Ask the user for their **modpack project root**. This is usually one of:

- `<MO2_Root>/profiles/<ProfileName>/` (if the profile is the unit of work).
- A separate Git-tracked source directory the user maintains (more common for
  released modpacks).

Once `<project_root>` is known, route to:

- `writing-modpack-devlog` skill - creates `<project_root>/docs/dev-log.md` with
  the project name and start date as the first entry.
- `writing-modpack-changelog` skill - creates
  `<project_root>/docs/release-changelog.md` skeleton.

From here on, those two skills maintain the files at runtime; do not template
or pre-fill them in this skill.

### Step 10 - Verify with a semantic smoke test (NON-BLOCKING)

The xEdit MCP is fully non-blocking. Do NOT call a single blocking tool and
wait — that will time out. Instead:

**0. Read MO2's managed gamePath before launching xEdit.** xEdit's default
   game discovery uses the Windows registry, which points at the Steam install
   — NOT MO2's Stock Game. To force xEdit to see MO2's projected game tree,
   read `<MO2_Root>\ModOrganizer.ini` and extract the `gamePath` value:

   ```
   gameName=<Target Game>
   gamePath=@ByteArray(<MO2 managed game root>)
   ```

   Strip the `@ByteArray(...)` wrapper; the Data dir is `<gamePath>\Data`.
   Pass this to `xedit_start` as `dataPath` in the next step. See
   `writing-bgs-load-order` for the full reasoning + alternative load-order
   workflows.

1. **Kick off the daemon launch.**
   ```
   xedit_start({
     dataPath: "<gamePath>\\Data",   // from step 0 above
   })
   ```
   Without an explicit `dataPath`, xEdit will discover the game via registry
   and may open the wrong Data directory.

   Expect `{ ok: true, data: { status: "starting" } }` (or `"ready"` if it was
   already up). If you want to use a custom subset of plugins (load-order
   experimentation), also pass `pluginsFile`:
   ```
   xedit_start({
     dataPath: "<gamePath>\\Data",
     pluginsFile: "<agent-owned-artifacts-path>/plugins.txt",
   })
   ```
   The `writing-bgs-load-order` skill explains how to author the file.

2. **Poll `xedit_status` until ready.** The first launch takes 60-240s because
   xEdit must parse the active load order. Sleep 5-15s between polls.
   ```
   xedit_status({})  -> { status: "starting", elapsedSeconds: N }
   xedit_status({})  -> { status: "starting", elapsedSeconds: N+5 }
   ...
   xedit_status({})  -> { status: "ready", pid: N, readySince: timestamp }
   ```

   If `status: "failed"`, surface `data.error` exactly and STOP. Do not declare
   success. Common reasons: MO2 not running, MO2 not loading the Python plugin,
   xEdit binary missing, xEdit's automation-serve mode tripping on the active
   load order.

3. **Confirm with `xedit_health`** — sends a real `system.ping` to the daemon
   to catch zombies. Expect `{ status: "ready", responsive: true }`.

4. **Confirm domain tools work.**
   ```
   xedit_list_capabilities({})  -> ~49 commands, empty drift.onlyInDigest
   xedit_session({})            -> { gameMode: "Fallout4", loadOrderSize: N, daemonPid: N }
   ```

If all four pass: surface `[OK] BGS modding environment ready` with the recorded
`MO2_Root`, xEdit path (if installed), and project root.

## Acceptance (semantic, not surface)

The setup is complete only when ALL of the following hold. Do not declare
success otherwise:

- `<MO2_Root>` is known and `<MO2_Root>/ModOrganizer.exe` exists.
- Target games are recorded; `bgs_kb_status` sees the bundled core pack; and at
  least one `bgs_kb_query` smoke for the chosen game returns a hit.
- If AI translation workflows were requested: `xtl version` succeeds from the
  user's shell, and `xtl --help` lists the translator command surface.
- `<MO2_Root>/plugins/mo2_agent_control.py` exists (skipped only in no-MO2 mode).
- MO2 is visibly running (process has `MainWindowHandle != 0`) and
  `<MO2_Root>/plugins/Mo2AgentControl/bootstrap/runtime/status.json` reports
  `state: "ok"` with a current `mo2Pid` (skipped only in no-MO2 mode).
- If xEdit was chosen: `<MO2_Root>/tools/xEdit/xEdit.exe` AND
  `<MO2_Root>/tools/xEdit/xEditHookBridge.dll` both exist.
- `<project_root>/docs/dev-log.md` and
  `<project_root>/docs/release-changelog.md` both exist (or user explicitly
  declined - record the decline in conversation context).
- `xedit_status` eventually reports `status: "ready"`, and
  `xedit_health.data.responsive` is `true`, and
  `xedit_list_capabilities` returns a non-empty digest. (Skipped only if xEdit
  was declined or no-MO2 mode.)

In no-MO2 mode, only the KB target selection / smoke and the dev-log / changelog
steps need to pass.

## Common mistakes

- Skipping the consent gate on step 2(b) or step 6. Both REQUIRE explicit user
  agreement; silent install or silent install-decision is forbidden.
- Silently choosing one MO2 install when multiple are detected. Always ask.
- **Trying to build `Mo2AgentControl.dll` from `docs/internal/future-c-kernel/`.**
  That is a skeleton, not a real MO2 plugin. The Python plugin IS the
  integration. Build the C++ kernel only if you are deliberately moving
  perf-critical paths out of Python in a future release.
- **Calling `xedit_session` or any domain tool and blocking on the response.**
  Every tool returns immediately. If you see `status: "starting"`, poll
  `xedit_status`; do not call the same tool again in a tight loop.
- **Using `/mcp reconnect` as the normal way to relaunch xEdit.**
  Prefer `xedit_dirty`, `xedit_stop`, and `xedit_restart` so the agent can
  decide whether to save or abandon unsaved edits before clearing state.
- **Starting MO2 with `Start-Process -WindowStyle Hidden`** (or any other
  invisible/background mode). Always use the `start-mo2.ps1` helper, which
  forces a visible window.
- Writing into the user's vanilla game install directly instead of via MO2
  overlay. NEVER do this. See `using-bgs-modding-superpowers` rule 1.
- Declaring success on a green script return without the semantic readback
  (the file existence checks and the four MCP smoke calls).
- Using broad `pip install --pre bgs-translator` during setup. Prefer an exact
  package version such as `bgs-translator==0.9.0rc1`, or use the stable package
  name once a stable release is published.

## See also

For ongoing care after first-run, see `maintaining-modding-environments`.

- `using-bgs-modding-superpowers` - the per-session bootstrap; lists the full
  skill inventory and hard rules.
- `xedit-automation` - hub skill for all xEdit work; load after this skill
  succeeds.
- `writing-modpack-devlog`, `writing-modpack-changelog` - runtime asset skills
  invoked from step 9.
- The installer scripts under `scripts/`: `install-mo2-control-plane.ps1`,
  `start-mo2.ps1`, `fetch-xedit-release.ps1`, `install-xedit-hook-bridge.ps1`.
