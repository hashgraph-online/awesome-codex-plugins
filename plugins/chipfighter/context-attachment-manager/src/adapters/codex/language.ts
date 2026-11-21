// Purpose: v0.1-20 — Codex's own language setting (user 2026-09-26), so the tab's title is right before any panel is
// opened, and after the user changes Codex's language: the desktop app writes the interface language it uses for its
// Computer Use helper to <CODEX_HOME>/computer-use/config.json. The language as Codex shows it is the core's choice
// (core/language.ts) with that setting (v0.11: split from language.ts, docs/v0.11/plan.md).
// Input: Codex's computer-use/config.json (read only). Output: "zh" | "en".

import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Lang } from "../../core/lang.ts";
import { currentLang as langWith, languageFileOf, rememberLang as rememberWith, type LangSource } from "../../core/language.ts";
import { codexHome } from "./codexconfig.ts";

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

export const rememberLang = (lang: Lang, source: LangSource, file = languageFileOf(), setting = codexUiFileOf()): void => rememberWith(lang, source, file, codexUiLocale(setting));
export const currentLang = (file = languageFileOf(), setting = codexUiFileOf()): Lang => langWith(file, codexUiLocale(setting));
