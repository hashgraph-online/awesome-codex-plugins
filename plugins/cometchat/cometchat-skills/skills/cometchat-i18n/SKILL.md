---
name: cometchat-i18n
description: "Localize a CometChat integration — set the UI Kit language, register custom/overridden translations, handle RTL, and never leak a raw localization key into the UI. Cross-family: the mechanism is CometChatLocalize on React, Angular, iOS and Android, while React Native uses CometChatI18nProvider (there is no CometChatLocalize in the RN kit); the exact signature is fetched from each family's localize doc. Triggers: 'translate cometchat', 'change chat language', 'localization', 'i18n', 'RTL / Arabic / Hebrew chat', 'my UI shows group_info instead of a label', 'add a language to cometchat', 'custom translations'."
license: "MIT"
compatibility: "CometChatLocalize on React v7 · Angular v5 · iOS v5 · Android v6. React Native v5 uses CometChatI18nProvider + the useCometChatTranslation hook (no CometChatLocalize in the RN kit). Flutter v6 is moving to CometChatLocalize but the shipping 6.1.0 kit uses Translations (staged). Exact API per family+major from that family's localize docs."
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat i18n localization localize rtl language translations cometchatlocalize"
---

> **Ground truth:** localization is the **`CometChatLocalize`** class on **React, Angular, iOS and Android**. Two exceptions: **React Native** uses **`CometChatI18nProvider`** + the **`useCometChatTranslation`** hook (there is no `CometChatLocalize` in the RN kit — catalog-confirmed), and **Flutter** is moving to `CometChatLocalize` but the shipping **6.1.0** kit still exposes **`Translations`** (see `cometchat-flutter-v6-customization` → Localization — **STAGED** pending the kit). Exact methods and built-in string keys differ by family and major — **FETCH the signature from the resolved family's localize doc** via `cometchat-<family>-core/references/docs-map.md` (intent: localization / localize). Do not carry an API across families or majors (v6 React, for one, renamed language codes and keys). Never assert a key set from memory — look it up in the kit's `resources/<lang>/translation.json` / the localize page.

## Use this skill when
Making the chat speak another language, shipping to a multi-locale or RTL market, adding/overriding wording, or fixing a UI that shows a raw key (e.g. `group_info`) instead of text.

## The mechanism (per family, one shape)
Most UI Kits localize through `CometChatLocalize` (React Native is the exception — it uses `CometChatI18nProvider` + the `useCometChatTranslation` hook): it can **detect** the user's browser/device language and **set** the active locale, and it exposes the current locale to components (which read their strings from it). The three things you do:
1. **Set the locale** — let it auto-detect, or set it explicitly to match your app's language switcher. Do this **before** the surface renders (alongside init), so components mount already localized. (React v7: pass the `locale` prop on `CometChatProvider` — `<CometChatProvider locale="fr">` — applied on mount/change.)
2. **Register custom / overridden translations** — add your own strings or override the kit defaults per locale (e.g. React v7: `CometChatLocalize.getSharedInstance()?.addTranslation({ "en-us": { key: "value" } })` — an **INSTANCE** method taking a **nested per-language** map; reach the live instance via `getSharedInstance()`, never `new CometChatLocalize()`; other families have the equivalent — **React Native** instead uses the `CometChatI18nProvider` **`translations`** prop, keyed on the **active** language code: under the default auto-detect that's the 2-letter device code, so use `translations={{ "en": { KEY: "value" } }}` — a regional key like `en-US` is ignored unless you also pass `selectedLanguage="en-US"`, and codes must match the kit's keys **exactly (case-sensitive)** — e.g. `zh-tw` is lowercase but `en-US`/`en-GB` are uppercase-region; not `addTranslation`. Provider props: `selectedLanguage` · `autoDetectLanguage` · `translations` · `fallbackLanguage` — `{DOCS_BASE}/ui-kit/react-native/localize`). Fetch the exact call for your family.
3. **Read a string yourself** where you render kit text in your own markup — use the family's localized-string accessor (React v7: `useLocale().getLocalizedString(key)`), never a hardcoded English literal.

The exact class methods, the supported language list, and the key namespace are per family+major — **fetch them**; this file is the discipline, the docs are the signatures.

## Never render a raw key
A snake_case token in the UI (`group_info`, `add_members`, `sample_*`) means a **missing or wrong key** — the localizer returns the key on a miss. Causes and fixes:
- The component isn't inside the kit provider/localization context → wrap it (the provider auto-wires localization).
- The key changed across majors (v5→v6/v7 moved keys, some under `sample_*`) → look up the CURRENT key in the kit's `resources/<lang>/translation.json` or the localize doc; don't guess.
- You hardcoded a raw key as a label → use the component or the localized-string accessor.

## RTL (Arabic, Hebrew, Farsi, Urdu)
- Set the document/layout direction to RTL for RTL locales (web: `dir="rtl"` on the app root or the locale-driven wrapper; native: the platform's RTL layout support). The kit follows the surrounding direction; your host must set it.
- **React Native exception:** the RN kit ships **no RTL locale** — its built-in languages (≈18, plus English regional aliases; `{DOCS_BASE}/ui-kit/react-native/localize` → Supported Languages) are all LTR (no Arabic/Hebrew/Farsi/Urdu). An RTL language is only possible as a custom `translations` entry + a matching `selectedLanguage`, with the host handling layout direction — re-check that page before promising RTL chat on React Native.
- Don't hard-code left/right margins/paddings on the kit's ancestors — use logical properties (`margin-inline-start`, etc.) so your chrome mirrors correctly.
- Verify icons/affordances that imply direction (back, send) read correctly mirrored.

## Also
- **Dates/times/numbers** localize with the locale; confirm the family's date-format option (v6+ added date-format controls) matches the user's region.
- **User-generated content is not translated** by localization — that's the `message-translation` feature (per-message, `cometchat-<family>-features`), a different thing from UI-Kit localization.
- **Keep host i18n and kit i18n in sync** — when your app switches language, also switch the kit's language so the chat doesn't stay in the old one: set `CometChatLocalize` (React · Angular · iOS · Android), or change the `selectedLanguage` prop on `CometChatI18nProvider` (**React Native** — there is no `CometChatLocalize` setter there).

## Common pitfalls
1. **Raw keys in the UI** — missing/renamed key or missing provider; look up the current key, don't guess.
2. **Carrying an API across families/majors** — v6 React changed codes/keys; fetch per family.
3. **Locale set after render** — set it before/with init so the surface mounts localized.
4. **RTL not applied by the host** — the kit mirrors within the direction you set; set `dir`/layout direction yourself.
5. **Confusing UI localization with message translation** — different features.

## Verify it works
Switching the app language re-renders the chat in that language · no snake_case keys appear in the UI · custom/overridden strings show · an RTL locale mirrors layout and direction-sensitive icons · dates/times read in the locale · your language switcher and the kit's language (`CometChatLocalize`, or React Native's `selectedLanguage` prop) stay in sync.
