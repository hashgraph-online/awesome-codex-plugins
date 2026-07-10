---
name: language-config
description: "Configure language settings. Use when: setting primary languages, do-not-translate terms, or locale formatting."
---

# /digital-marketing-pro:language-config

## Purpose

Configure and manage multilingual settings for the active brand. This command controls the language infrastructure that powers all translation, localization, and multilingual audit commands in the plugin. It sets the primary content language (the source language for all translations), secondary and target languages (which markets and languages the brand operates in), do-not-translate terms (brand names, product names, trademarked phrases, and technical terms that must appear identically in every language), preferred translation service per language (routing to the optimal MCP for each language pair), and locale-specific formatting rules (date, number, currency, measurement formats per market).

This configuration persists in the brand profile and is referenced by every multilingual command — translate, transcreate, multilingual-score, language-audit, hreflang-check, and any content creation targeting non-primary languages. Getting this configuration right upfront prevents repeated corrections downstream and ensures consistent multilingual output across all workflows.

## Input Required

The user must provide (or will be prompted for):

- **Configuration action**: What to do — `view` (display all current language settings), `set-primary` (change the primary/source language), `add-language` (add a secondary/target language), `remove-language` (remove a secondary language), `add-dnt` (add a do-not-translate term), `remove-dnt` (remove a do-not-translate term), `set-translation-pref` (set preferred translation service for a language), `set-locale-format` (set locale-specific formatting for a language-region), or `reset` (restore language config to defaults)
- **Language code** (for language actions): ISO 639-1 language code with optional ISO 3166-1 region (e.g., `en`, `en-US`, `de-DE`, `hi-IN`, `ja-JP`, `pt-BR`). Required for set-primary, add-language, remove-language, set-translation-pref, and set-locale-format actions
- **Term** (for DNT actions): The exact term to add or remove from the do-not-translate list. Required for add-dnt and remove-dnt. Can be a single term or a comma-separated list of terms to add/remove in batch
- **Translation service** (for set-translation-pref): The preferred translation MCP for the specified language — one of `deepl` (best for European languages), `sarvam-ai` (best for Indic languages), `google-cloud-translation` (broadest language coverage), or `lara-translate` (best for marketing/creative context preservation). Required for set-translation-pref action
- **Formatting preferences** (for set-locale-format): Locale-specific format settings — `date_format` (e.g., DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD), `number_format` (decimal and thousands separators, e.g., "1,234.56" or "1.234,56"), `currency_format` (symbol position and spacing, e.g., "$1,234" or "1.234 EUR"), `measurement` (metric or imperial). Any subset can be provided; omitted fields retain current values

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Read current language configuration**: Extract the `language` object from `profile.json` containing `primary_language`, `secondary_languages`, `content_languages`, `do_not_translate`, `translation_preferences`, and `locale_formatting`. If the language object does not exist yet (new brand or pre-multilingual setup), initialize it with sensible defaults: primary_language set to "en", empty arrays for secondary_languages and do_not_translate, and empty objects for translation_preferences and locale_formatting.
3. **For view action**: Display all current language settings in a clear, structured format — primary language with full name (e.g., "en-US: English (United States)"), all secondary languages with full names, the complete do-not-translate term list, translation service preferences per language (showing which MCP handles each), locale formatting rules per language-region, and a summary of which translation services are configured versus using auto-routing defaults.
4. **For set-primary action**: Validate the provided language code against ISO 639-1 (and ISO 3166-1 if region included). Check that the language is supported by at least one configured translation MCP via `language-router.py --action supported-languages`. Update `profile.json` field `language.primary_language` to the new value. If the old primary language is not already in secondary_languages and the user has content in it, suggest adding it as a secondary language to maintain existing translations.
5. **For add-language / remove-language actions**: Validate the language code. For add: append to both `language.secondary_languages` and `language.content_languages` arrays (avoiding duplicates). Recommend a translation service for the new language based on language-router.py routing logic (DeepL for European, Sarvam AI for Indic, Google Cloud for others) and prompt the user to confirm or override. Provide default locale formatting for the language-region. For remove: remove from both arrays, warn if content exists in this language (it will no longer be targeted by multilingual commands), and ask for confirmation before removing.
6. **For add-dnt / remove-dnt actions**: Validate that terms are non-empty strings. For add: append each term to `language.do_not_translate` array, avoiding duplicates, and confirm each term added. For remove: remove matching terms (case-sensitive match), warn if a term is not found in the list. Display the updated do-not-translate list after changes. For batch operations (comma-separated input), process all terms and report results for each.
7. **For set-translation-pref action**: Validate that the specified service is one of the supported translation MCPs: `deepl`, `sarvam-ai`, `google-cloud-translation`, `lara-translate`. Validate that the language code is in the brand's configured languages (primary or secondary). Set `language.translation_preferences[language_code]` to the specified service name. Note: this overrides the automatic routing in language-router.py for this specific language — the user's explicit preference takes priority over default routing logic.
8. **For set-locale-format action**: Validate the language-region code. Set fields under `language.locale_formatting[language_region]` for the provided preferences (date_format, number_format, currency_format, measurement). If not all fields are provided, retain existing values for omitted fields. Provide format previews showing how dates, numbers, currency, and measurements will render with the configured format (e.g., "Date preview: 13/02/2026", "Currency preview: EUR 1.234,56").
9. **Save updated profile.json**: Write the modified language configuration back to the brand profile. Validate JSON integrity before saving.
10. **Confirm changes with before/after comparison**: Display a clear diff showing exactly what changed — old value versus new value for each modified field. For array changes (languages, DNT terms), show items added or removed. Provide a summary of the current complete language configuration after all changes.

## Output

A structured language configuration result containing:

- **Current language configuration display**: Complete view of all language settings after changes — primary language, secondary languages list with full names, content languages, do-not-translate terms, translation preferences per language, and locale formatting per language-region
- **Changes made**: Before/after comparison for every modified field, clearly showing what was added, removed, or updated
- **Supported languages reference**: Output from `language-router.py --action supported-languages` showing which languages are available and which translation service handles each, so the user can make informed decisions about adding languages
- **Translation service recommendation**: For each configured language, the recommended translation MCP based on language-router.py routing logic, with the user's override noted where applicable — helping the user understand which service will handle their translations and why
- **Locale formatting defaults**: For each configured language-region, the default date, number, currency, and measurement formats with preview examples — making it easy to verify formatting is correct before it affects content output

## Agents Used

- **localization-specialist** — Validates language codes against ISO standards, recommends optimal translation service routing per language based on quality benchmarks and language family expertise (DeepL for European, Sarvam AI for Indic, Google Cloud Translation for broad coverage, Lara Translate for marketing context), provides locale formatting defaults and previews per language-region, and ensures the language configuration is complete and consistent for downstream multilingual workflows
