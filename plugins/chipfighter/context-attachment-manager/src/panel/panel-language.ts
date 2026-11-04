// Panel-only language selection. Claude Desktop persists its app language in userData/config.json's locale;
// read that setting without writing it or sharing Codex's remembered model language. Paths are best-effort:
// Claude has used both standard Electron folders and a per-package Claude-Data folder on Windows.
import { readFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export type PanelLang = "en" | "zh" | "ja";
type Options = { settingsFiles?: readonly string[]; env?: NodeJS.ProcessEnv; platform?: NodeJS.Platform; home?: string };

function panelLangOf(tag: unknown): PanelLang | null {
  if (typeof tag !== "string" || !tag.trim()) return null;
  const value = tag.trim().toLowerCase();
  if (value === "c" || value === "posix" || value.startsWith("c.")) return null;
  return value.startsWith("zh") ? "zh" : value.startsWith("ja") ? "ja" : "en";
}

function settingsFiles(env: NodeJS.ProcessEnv, platform: NodeJS.Platform, home: string): string[] {
  if (platform === "darwin") return [join(home, "Library", "Application Support", "Claude", "config.json")];
  if (platform !== "win32") return [join(env.XDG_CONFIG_HOME || join(home, ".config"), "Claude", "config.json")];
  const local = env.LOCALAPPDATA || join(home, "AppData", "Local");
  const roaming = env.APPDATA || join(home, "AppData", "Roaming");
  const native = join(local, "Claude-Data");
  let packages: string[] = [];
  try { packages = readdirSync(native, { withFileTypes: true }).filter(entry => entry.isDirectory() && /^claude_/i.test(entry.name)).map(entry => entry.name).sort(); } catch {}
  return [
    ...packages.map(name => join(native, name, "config.json")),
    join(native, "config.json"), join(local, "Claude", "config.json"), join(roaming, "Claude", "config.json"),
  ];
}

export function claudePanelLanguage(options: Options = {}): PanelLang {
  const env = options.env ?? process.env;
  const system = () => {
    for (const name of ["LC_ALL", "LC_MESSAGES", "LANG"]) { const lang = panelLangOf(env[name]); if (lang) return lang; }
    return panelLangOf(Intl.DateTimeFormat().resolvedOptions().locale) ?? "en";
  };
  for (const file of options.settingsFiles ?? settingsFiles(env, options.platform ?? process.platform, options.home ?? homedir())) {
    try {
      const settings = JSON.parse(readFileSync(file, "utf8").replace(/^\uFEFF/, ""));
      return panelLangOf(settings?.locale) ?? system();
    } catch {}
  }
  return system();
}
