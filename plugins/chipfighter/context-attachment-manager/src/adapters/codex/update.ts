// Purpose: v0.13 — keeping the plugin up to date in Codex (core/update.ts), with Codex's own command line, the same
// steps as the one-line install (scripts/install.ps1, install.sh): the marketplace is this repository on GitHub, pinned
// to a release tag (`ref` in config.toml); moving it to the new tag, refreshing Codex's copy of the repository and
// adding the plugin again installs that release into Codex's plugin cache. Codex runs it from its next start.
// Installed another way (a local folder: a developer's checkout, or another repository) it is left alone.
// Input: `codex plugin list / marketplace list / marketplace upgrade / add`, config.toml. Output: config.toml's ref
// for this marketplace (backed up first, put back when the refresh fails), Codex's plugin cache.

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { failure, isOurRepo, jsonOf, runCommand, type Installed, type Platform, type Release } from "../../core/update.ts";
import { findCodexCli } from "./codexcli.ts";
import { codexHome } from "./codexconfig.ts";
import { MARKETPLACE, PLUGIN, PLUGIN_ID } from "./install.ts";
import { preservingPluginCacheAsync } from "./plugin-cache.ts";
import { backupConfig, codexFiles, readConfig, replaceFile } from "./setup.ts";

// The ref of a marketplace's table in config.toml: replaced, added after the table's last line, or (ref null) removed.
// previous: the ref it had (null: none). found: whether the table is there at all.
export function setMarketplaceRef(text: string, name: string, ref: string | null): { text: string; previous: string | null; found: boolean } {
  const newline = text.includes("\r\n") ? "\r\n" : "\n";
  const lines = text.split(/\r?\n/);
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const header = new RegExp(`^\\s*\\[\\s*marketplaces\\s*\\.\\s*(?:"${escaped}"|'${escaped}'|${escaped})\\s*\\]\\s*(?:#.*)?$`);
  const start = lines.findIndex((line) => header.test(line));
  if (start < 0) return { text, previous: null, found: false };
  let end = lines.findIndex((line, index) => index > start && /^\s*\[/.test(line));
  if (end < 0) end = lines.length;
  const at = lines.findIndex((line, index) => index > start && index < end && /^\s*ref\s*=/.test(line));
  const previous = at < 0 ? null : lines[at].replace(/^\s*ref\s*=\s*/, "").replace(/\s+#.*$/, "").trim().replace(/^(["'])(.*)\1$/, "$2");
  if (ref === null) {
    if (at >= 0) lines.splice(at, 1);
  } else if (at >= 0) {
    lines[at] = `ref = ${JSON.stringify(ref)}`;
  } else {
    // After the table's last line that holds something.
    let last = end - 1;
    while (last > start && !lines[last].trim()) last--;
    lines.splice(last + 1, 0, `ref = ${JSON.stringify(ref)}`);
  }
  return { text: lines.join(newline), previous, found: true };
}

export function codexPlatform(options: { env?: NodeJS.ProcessEnv; cli?: string | null; anySource?: boolean } = {}): Platform {
  const env = options.env ?? process.env;
  const cli = () => options.cli ?? findCodexCli(env);
  const codex = async (args: string[], what: string) => {
    const command = cli();
    if (!command) throw new Error("no Codex command line");
    const ran = await runCommand(command, args, { env });
    if (!ran.ok) throw failure(`codex ${what}`, ran);
    return ran;
  };
  // Where Codex keeps its copy of this marketplace, and the plugin version in it.
  const snapshotVersion = async (): Promise<string | null> => {
    const listed = jsonOf((await codex(["plugin", "marketplace", "list", "--json"], "plugin marketplace list")).stdout);
    const root = (listed.marketplaces ?? []).find((entry: any) => entry?.name === MARKETPLACE)?.root;
    if (typeof root !== "string") return null;
    try {
      const marketplace = JSON.parse(readFileSync(join(root, ".agents", "plugins", "marketplace.json"), "utf8"));
      const path = marketplace.plugins?.find((entry: any) => entry?.name === PLUGIN)?.source?.path ?? "./plugin";
      return JSON.parse(readFileSync(join(root, path, ".codex-plugin", "plugin.json"), "utf8")).version ?? null;
    } catch {
      return null;
    }
  };
  const installedEntry = async () => {
    const listed = jsonOf((await codex(["plugin", "list", "--json"], "plugin list")).stdout);
    return (listed.installed ?? []).find((plugin: any) => plugin?.pluginId === PLUGIN_ID) ?? null;
  };
  const installedVersion = async (): Promise<string | null> => {
    const entry = await installedEntry();
    return typeof entry?.version === "string" ? entry.version : null;
  };
  return {
    host: "codex",
    async inspect(): Promise<Installed> {
      if (!cli()) return { eligible: false, reason: "no Codex command line" };
      const entry = await installedEntry();
      if (!entry || typeof entry.version !== "string") return { eligible: false, reason: "not installed in Codex" };
      const source = entry.marketplaceSource ?? {};
      if (!options.anySource && (source.sourceType !== "git" || !isOurRepo(source.source))) return { eligible: false, reason: "installed from a local folder", version: entry.version };
      return { eligible: true, version: entry.version };
    },
    async apply(release: Release): Promise<string> {
      const { configFile } = codexFiles();
      const before = setMarketplaceRef(readConfig(), MARKETPLACE, release.tag);
      if (!before.found) throw new Error("the marketplace is not in config.toml");
      // As the one-line install does: the files of older versions stay, for the plugin services and the engine still
      // running from them (this very service among them). The refresh below already replaces the installed version
      // in the cache (2026-11-23), so it runs inside this too.
      const cacheRoot = join(codexHome(), "plugins", "cache", MARKETPLACE, PLUGIN);
      return preservingPluginCacheAsync(cacheRoot, release.version, async () => {
        backupConfig();
        replaceFile(configFile, before.text);
        try {
          // Codex's refresh has once left its copy at the old tag on the first try (2026-11-23); a second one moved it.
          let version = null;
          for (let attempt = 0; attempt < 2 && version !== release.version; attempt++) {
            await codex(["plugin", "marketplace", "upgrade", MARKETPLACE, "--json"], "plugin marketplace upgrade");
            version = await snapshotVersion();
          }
          if (version !== release.version) throw new Error(`Codex's copy of the marketplace is at ${version ?? "an unknown version"}, not ${release.version}`);
        } catch (error) {
          // The ref back as it was, so the configuration matches what is installed.
          replaceFile(configFile, setMarketplaceRef(readConfig(), MARKETPLACE, before.previous).text);
          throw error;
        }
        // The refresh installs the new version itself. `plugin add` only when it did not: while a plugin service runs
        // from the old version's folder (it always does here: this one), Windows keeps that folder, and `plugin add`
        // fails to set it aside ("failed to back up plugin cache entry", os error 5; 2026-11-23), where the refresh
        // had already put the new version beside it.
        let installed = await installedVersion();
        if (installed !== release.version) {
          const added = jsonOf((await codex(["plugin", "add", "--json", PLUGIN_ID], "plugin add")).stdout);
          installed = typeof added?.version === "string" ? added.version : null;
        }
        if (!installed || !existsSync(join(cacheRoot, installed, "src", "cam.ts"))) throw new Error(`the installed copy of ${installed ?? "the plugin"} is incomplete`);
        return installed;
      });
    },
  };
}
