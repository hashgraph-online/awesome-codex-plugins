// Purpose: v0.1-14 — which language the plugin speaks: Simplified Chinese or English (user 2026-09-25: these two for
// v0.1; Chinese of any region gets Simplified Chinese, every other language gets English). A panel learns the host's
// interface language and reports it with its calls; it is kept in the data directory, where the engine (the text for
// the model) and the plugin service (the tab's title) read it. The command line always follows the system language.
// CAM_LANG=zh|en (tests, development) fixes the language.
// v0.1-20 (user 2026-09-26) — the host's own language setting counts too (Codex: adapters/codex/language.ts). Order: a
// panel's report while that setting is the one it was seen with, else the setting, else the last report, else the
// system language.
// v0.11: split from language.ts (docs/v0.11/plan.md); the host's setting comes in as `uiLocale`.
// Input: language tags (BCP 47 or POSIX, e.g. "zh-CN", "zh_TW.UTF-8", "en-US"), the environment, the data directory.
// Output: "zh" | "en"; <data dir>/language.json = { "lang": "zh", "source": "codex" | "system", "at": "…", "codexLocale": "zh-CN" | null }.

import { mkdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import type { Lang } from "./lang.ts";
import { dataDir } from "./paths.ts";

// codex: the panel got the host's interface language; system: it only had the system's.
export type LangSource = "codex" | "system";
// codexLocale: the host's language setting when the panel reported (absent in records from before v0.1-20).
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
export function rememberLang(lang: Lang, source: LangSource, file = languageFileOf(), uiLocale: string | null = null): void {
  const codexLocale = uiLocale;
  const known = storedLang(file);
  if (known?.lang === lang && known.source === source && known.codexLocale === codexLocale) return;
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(`${file}.tmp`, JSON.stringify({ lang, source, at: new Date().toISOString(), codexLocale }));
  renameSync(`${file}.tmp`, file);
  cache = null;
}

export function currentLang(file = languageFileOf(), uiLocale: string | null = null): Lang {
  const fixed = process.env.CAM_LANG;
  if (fixed === "zh" || fixed === "en") return fixed;
  const codexLocale = uiLocale;
  const stored = storedLang(file);
  // A panel saw the interface itself, which can differ from the app's locale; that holds while the setting is unchanged.
  if (stored?.source === "codex" && stored.codexLocale === codexLocale) return stored.lang;
  // Otherwise the setting: no panel has reported yet, or the user has changed the host's language since.
  return langOf(codexLocale) ?? stored?.lang ?? systemLang();
}
