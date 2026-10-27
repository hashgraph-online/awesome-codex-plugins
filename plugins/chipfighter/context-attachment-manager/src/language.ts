// Purpose: v0.1-14 — which language the plugin speaks: Simplified Chinese or English (user 2026-09-25: these two for
// v0.1; Chinese of any region gets Simplified Chinese, every other language gets English). The panel learns Codex's
// interface language and reports it with its calls; it is kept in the data directory, where the engine (the text for
// the model) and the plugin service (the tab's title) read it. The command line always follows the system language.
// CAM_LANG=zh|en (tests, development) fixes the language.
// v0.1-20 (user 2026-09-26) — Codex's own language setting counts too, so the tab's title is right before any panel is
// opened, and after the user changes Codex's language: the desktop app writes the interface language it uses for its
// Computer Use helper to <CODEX_HOME>/computer-use/config.json. Order: a panel's report while that setting is the one
// it was seen with, else the setting, else the last report, else the system language.
// Input: language tags (BCP 47 or POSIX, e.g. "zh-CN", "zh_TW.UTF-8", "en-US"), the environment, the data directory,
// Codex's computer-use/config.json (read only). Output: "zh" | "en";
// <data dir>/language.json = { "lang": "zh", "source": "codex" | "system", "at": "…", "codexLocale": "zh-CN" | null }.

import { mkdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { codexHome } from "./codexconfig.ts";
import { dataDir } from "./paths.ts";

export type Lang = "zh" | "en";
// codex: the panel got Codex's interface language; system: it only had the system's.
export type LangSource = "codex" | "system";
// codexLocale: Codex's language setting when the panel reported (absent in records from before v0.1-20).
type Stored = { lang: Lang; source: LangSource; at: string; codexLocale?: string | null };

export function langOf(tag: unknown): Lang | null {
  if (typeof tag !== "string") return null;
  const value = tag.trim().toLowerCase();
  if (!value || value === "c" || value === "posix" || value.startsWith("c.")) return null;
  return value.startsWith("zh") ? "zh" : "en";
}

// POSIX locale variables when set (macOS, Linux, some Windows shells), else what the runtime reports (Windows).
export function systemLang(env: NodeJS.ProcessEnv = process.env): Lang {
  if (env.CAM_LANG === "zh" || env.CAM_LANG === "en") return env.CAM_LANG;
  for (const name of ["LC_ALL", "LC_MESSAGES", "LANG"]) {
    const lang = langOf(env[name]);
    if (lang) return lang;
  }
  return langOf(Intl.DateTimeFormat().resolvedOptions().locale) ?? "en";
}

export const languageFileOf = (root = dataDir()) => join(root, "language.json");
let cache: { file: string; mtimeMs: number; value: Stored | null } | null = null;

// Codex's language setting as the desktop app writes it for its Computer Use helper ({ "locale": "en-US", … }): the
// language chosen in Codex's settings, else the app's own locale. Desktop 26.924 rewrites it when the user changes the
// language or the theme, and whenever it builds a task's tool configuration. Not a documented interface, so it is only
// read, and anything missing or unexpected (other platforms, other versions) counts as no setting.
export const codexUiFileOf = (home = codexHome()) => join(home, "computer-use", "config.json");

export function codexUiLocale(file = codexUiFileOf()): string | null {
  try {
    const locale = JSON.parse(readFileSync(file, "utf8"))?.locale;
    return typeof locale === "string" && locale.trim() ? locale.trim() : null;
  } catch {
    return null;
  }
}

export function storedLang(file = languageFileOf()): Stored | null {
  try {
    const { mtimeMs } = statSync(file);
    if (cache?.file === file && cache.mtimeMs === mtimeMs) return cache.value;
    const raw = JSON.parse(readFileSync(file, "utf8"));
    const lang = raw?.lang === "zh" || raw?.lang === "en" ? (raw.lang as Lang) : null;
    const value: Stored | null = lang ? { lang, source: raw.source === "codex" ? "codex" : "system", at: String(raw.at ?? ""), ...("codexLocale" in raw ? { codexLocale: typeof raw.codexLocale === "string" ? raw.codexLocale : null } : {}) } : null;
    cache = { file, mtimeMs, value };
    return value;
  } catch {
    return null;
  }
}

// Written only when it changes, whole file then renamed, so readers never see half of it.
export function rememberLang(lang: Lang, source: LangSource, file = languageFileOf(), setting = codexUiFileOf()): void {
  const codexLocale = codexUiLocale(setting);
  const known = storedLang(file);
  if (known?.lang === lang && known.source === source && known.codexLocale === codexLocale) return;
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(`${file}.tmp`, JSON.stringify({ lang, source, at: new Date().toISOString(), codexLocale }));
  renameSync(`${file}.tmp`, file);
  cache = null;
}

export function currentLang(file = languageFileOf(), setting = codexUiFileOf()): Lang {
  const fixed = process.env.CAM_LANG;
  if (fixed === "zh" || fixed === "en") return fixed;
  const codexLocale = codexUiLocale(setting);
  const stored = storedLang(file);
  // A panel saw the interface itself, which can differ from the app's locale; that holds while the setting is unchanged.
  if (stored?.source === "codex" && stored.codexLocale === codexLocale) return stored.lang;
  // Otherwise the setting: no panel has reported yet, or the user has changed Codex's language since.
  return langOf(codexLocale) ?? stored?.lang ?? systemLang();
}
