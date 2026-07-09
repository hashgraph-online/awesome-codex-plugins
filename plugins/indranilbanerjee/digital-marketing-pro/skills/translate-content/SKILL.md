---
name: translate-content
description: "Translate marketing content. Use when: localizing with brand voice preservation, quality scoring, or transcreation."
argument-hint: "[target-language]"
---

# /digital-marketing-pro:translate-content

## Purpose

Translate marketing content with intelligent service routing and quality assurance. This command automatically selects the best translation service based on the target language — Sarvam AI for Indic languages (Hindi, Tamil, Bengali, etc.), DeepL for European languages (German, French, Spanish, etc.), Google Cloud Translation for broad coverage, and Lara Translate for specialized needs — preserving brand voice, formatting, and key terminology throughout.

Beyond literal translation, this command analyzes content for elements that require transcreation rather than translation: idioms, wordplay, humor, emotional calls-to-action, and cultural references. When these are detected (or when the user explicitly requests transcreation), it produces multiple creative options with intent-preservation scoring, ensuring the emotional impact and marketing effectiveness carry across languages. Every translation is quality-scored and brand-voice-checked before delivery.

## Input Required

The user must provide (or will be prompted for):

- **Content to translate**: Text inline, file path, or pasted content block. Can be a single piece (headline, email, ad copy) or a structured document (landing page, email template with sections)
- **Target language(s)**: One or more target languages — accepts language codes (hi, de, ja, fr-CA, pt-BR) or plain names (Hindi, German, Japanese, Canadian French, Brazilian Portuguese). Multiple targets can be specified for batch translation
- **Source language**: Optional — the language of the original content. Auto-detected via language-router.py if omitted
- **Transcreation flag**: Optional — set to `true` to force transcreation approach on all content, regardless of content analysis. Useful when the user knows the content is highly creative or culturally sensitive
- **Do-not-translate terms**: Optional — specific terms, product names, or brand elements that must remain in the source language. Overrides any do-not-translate list already defined in the brand profile
- **Formality level**: Optional — `formal` or `informal`. Supported by DeepL for languages with formal/informal registers (German Sie/du, French vous/tu, etc.). If omitted, defaults to brand profile preference or formal
- **Glossary entries**: Optional — term pairs (source: target) to enforce specific translations for key terminology. Supplements any brand-level glossary

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract language configuration — `do_not_translate` term list, `translation_preferences` (preferred services per language pair, formality defaults, glossary), and `locale_formatting` rules (date formats, number separators, currency symbols). Load compliance rules for target markets from `skills/context-engine/compliance-rules.md`. Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load voice-and-tone rules (these inform brand voice scoring of the translation). Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Detect source language**: If the source language was not specified, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/language-router.py" --action detect --text "{content_or_path}"` to identify the source language with confidence score. Report the detected language to the user for confirmation if confidence is below 95%.
3. **Route to optimal translation service**: For each target language, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/language-router.py" --action route --source "{source_lang}" --target "{target_lang}"` to select the best translation service. The router considers language pair quality, service specialization (Sarvam AI for Indic languages, DeepL for European languages with formality support, Google Cloud for broad coverage), and any brand-level service preferences. Report the selected service to the user.
4. **Analyze content for transcreation needs**: Scan the source content for elements that resist literal translation — idioms and colloquialisms, wordplay or puns, humor and sarcasm, emotional CTAs and slogans, cultural references and analogies, rhyme or rhythm patterns, double meanings. If the transcreation flag is set or the content contains significant transcreation-requiring elements, prepare a transcreation brief using the methodology defined in `skills/context-engine/transcreation-framework.md`. For each flagged element, document the original intent, emotional tone, and desired audience response to guide creative adaptation.
5. **Execute translation**: Call the routed translation MCP server for each target language:
   - For DeepL: Use the `deepl` MCP server with formality parameter, glossary entries, and tag handling for HTML/XML preservation
   - For Sarvam AI: Use the `sarvam-ai` MCP server with script and dialect preferences for Indic languages
   - For Google Cloud: Use the `google-cloud-translation` MCP server with model selection (NMT) and glossary
   - For Lara Translate: Use the `lara-translate` MCP server with domain-specific model selection
   - Pass do-not-translate terms (merged from brand profile and user-provided list), formality settings, glossary entries, and any formatting preservation flags (HTML tags, placeholders like {{first_name}}, Markdown syntax)
6. **Score translation quality**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/language-router.py" --action score --source "{source}" --target "{target}" --original "{source_content}" --translated "{translated_content}"` to assess quality across dimensions:
   - Length ratio (translated vs. source — flags unusual expansion or compression)
   - Formatting preservation (HTML tags, Markdown, placeholders intact)
   - Key term consistency (do-not-translate terms respected, glossary terms applied correctly)
   - Placeholder integrity (all dynamic variables like {{name}}, {price} preserved)
   - Completeness (no missing sentences or paragraphs)
7. **Handle quality issues**: If the translation quality score is below 85, identify specific issues from the scoring breakdown. Attempt targeted corrections — re-translate problematic segments, fix formatting breaks, restore missing placeholders. Re-score after corrections. If quality remains below 85, flag the specific issues for human review.
8. **Execute transcreation** (if applicable): For content flagged for transcreation or when the transcreation flag is set, produce 2-3 creative adaptation options per flagged element. Each option includes:
   - The creative adaptation in the target language
   - Back-translation to English for review
   - Intent-preservation score (how well the original marketing intent carries through)
   - Cultural fit notes (why this adaptation works for the target market)
   - Tone alignment assessment (formal/playful/urgent matches the original tone)
9. **Run brand voice check**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/brand-voice-scorer.py" --brand {slug} --text "{translated_content}"` to assess whether the translated content maintains brand voice characteristics. Flag any voice drift with specific examples and suggestions.
10. **Present translated content with quality metrics**: Deliver the final translated content alongside all quality data, formatted for easy review and approval.

## Output

A structured translation delivery containing:

- **Translated content**: The final translated text for each target language, preserving original formatting (HTML, Markdown, placeholders)
- **Translation quality score**: Overall score (0-100) with per-dimension breakdown — length ratio, formatting preservation, key term consistency, placeholder integrity, completeness
- **Service used**: Which translation service handled this language pair and why it was selected
- **Source language**: Detected or confirmed source language with confidence level
- **Do-not-translate compliance**: Confirmation that all protected terms were preserved in the source language, or flags for any violations
- **Brand voice score**: How well the translated content maintains brand voice characteristics, with specific observations on voice drift if detected
- **Transcreation options** (if applicable): 2-3 creative adaptation options per flagged element, each with back-translation, intent-preservation score, cultural fit notes, and tone alignment assessment
- **Formatting preservation report**: Confirmation that HTML tags, Markdown syntax, placeholders, and structural elements survived translation intact
- **Quality flags**: Any issues that scored below threshold with specific descriptions and severity (critical: missing content or broken placeholders; warning: slight formatting drift or unusual length ratio; info: minor style observations)
- **Recommendations**: Suggestions for improving the translation — human review priorities, terms to add to the glossary for future translations, and any locale-specific adjustments needed (e.g., date format, currency symbol, measurement units)

## Agents Used

- **localization-specialist** -- Manages the end-to-end translation workflow including service routing, transcreation analysis, quality scoring, cultural adaptation assessment, brand voice preservation in the target language, and quality issue resolution
