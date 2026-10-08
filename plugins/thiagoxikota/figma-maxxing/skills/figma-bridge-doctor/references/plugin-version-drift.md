# Plugin version drift

Loaded from the `figma-bridge-doctor` SKILL.md when the plugin panel shows `Plugin update available`, or when `figma-status.sh` prints `plugin_drift=true`. Paths written `scripts/...` are in this skill's `scripts/` directory; run the commands from this skill's directory (the folder that holds SKILL.md).

Copying files into `~/.figma-console-mcp/plugin/` (rule 3 and the recipe) changes what Figma loads on the next plugin run. Back up first, as the recipe does, and tell the user before you do it.

## Plugin version: THREE layers, and the banner does not say the direction

Field note, 2026-09. The plugin panel shows the status `Connected`, the line `Connected to N AI apps`, a Pause button, and sometimes a `Plugin update available` notice asking you to re-import through `Plugins > Development > Import from manifest`. Before obeying that notice, understand that there are THREE distinct versions, and they diverge on their own:

| Layer | Where it lives | How to read it |
|---|---|---|
| Package | `$(npm config get cache)/_npx/<hash>/node_modules/figma-console-mcp/package.json` | `plugin_pkg_newest` in `figma-status.sh` |
| Plugin bundle | `figma-desktop-bridge/code.js` INSIDE the package, and the copy in `~/.figma-console-mcp/plugin/` | `plugin_bundle_newest` and `plugin_disk_version` |
| Plugin RUNNING | process inside Figma, per open file | `figma_get_status` -> `connectedFiles[].pluginVersion` + `pluginUpdateAvailable` |

`N AI apps` counts **live servers in the 9223-9232 range**, not files: the plugin opens one WebSocket per server. 6 open Claude Code sessions = "6 AI apps". It is not a sign of a problem.

**The trap (paid for in 2026-09, a self-inflicted regression):** every server, on boot, rewrites `~/.figma-console-mcp/plugin/` with ITS OWN bundle. A server from an old npx cache **downgrades the plugin on disk**. It happened because an earlier version of the fallback's `daemon.mjs` resolved the cache with `ls -t` (newest mtime), and the cache with the newest mtime was **1.35.0**, not 1.40.0. The 1.35.0 server overwrote the disk, and the next plugin trigger loaded 1.35.0 inside Figma. The banner appeared saying only "update available", without saying that the correct move was BACKWARDS. Following the banner and re-importing would have installed the downgrade for good.

**Rules that stay:**

1. **Never re-import because of the banner without measuring first.** Run `figma-status.sh` and read `plugin_drift`. `true` = the disk is NOT the newest bundle; fix the DISK first.
2. **Updating the plugin is almost never "Import from manifest".** Figma reads `code.js` from disk on every Run. A correct disk + re-running the plugin (Step T of SKILL.md) already solves it. Import from manifest only when `manifest.json` really changed (compare its md5 with the package's) or when the entry disappeared from the `Plugins > Development` menu.
3. **Fixing the disk** = copy `code.js`, `ui.html`, `manifest.json` from the package with the HIGHEST VERSION (not the one with the newest mtime) to `~/.figma-console-mcp/plugin/`, and write the package version into `.version`. Back up the dir first (`plugin.bak-<version>-<date>`).
4. **`pluginVersion` is per FILE.** After re-running, one file can be on 1.39.0 and another still on 1.35.0: each one only switches when the plugin runs in that file. Check the whole `connectedFiles[]`, not only the active one.
5. **An old npx cache is dangerous garbage**: move it to `<hash>.stale-<version>` as soon as you identify it. While it exists, any resolution by mtime can resurrect the downgrade.

Full fix recipe:

```bash
bash scripts/figma-status.sh | grep plugin_        # measure: drift? which version?
# if plugin_drift=true:
NPX="$(npm config get cache)/_npx"
PKG=$(for d in "$NPX"/*/node_modules/figma-console-mcp; do \
  [ -f "$d/package.json" ] && echo "$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$d/package.json") $d"; \
done | sort -V | tail -1 | cut -d' ' -f2-)
cp -R ~/.figma-console-mcp/plugin ~/.figma-console-mcp/plugin.bak-$(date +%Y%m%d-%H%M%S)
cp "$PKG"/figma-desktop-bridge/{code.js,ui.html,manifest.json} ~/.figma-console-mcp/plugin/
python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'],end='')" "$PKG/package.json" > ~/.figma-console-mcp/plugin/.version
# then Step T of SKILL.md (re-run the plugin) and check pluginVersion in figma_get_status
```
