---
name: translate-content
description: "Translate marketing content with automatic service routing per language pair, quality scoring across five dimensions (length ratio, formatting, key terms, placeholders, completeness), and a brand-voice check on the result; flags idioms, wordplay, and emotional CTAs for transcreation with 2-3 scored creative options plus back-translations. Triggers on \"/digital-marketing-pro:translate-content\", \"translate this landing page into German\", \"localize this email for India\", \"transcreate our slogan\", \"does the translated version keep our brand voice\". Reads the brand profile's do-not-translate terms, glossary, and formality preferences; executes via connected translation MCP servers."
argument-hint: "[target-language]"
---

# /digital-marketing-pro:translate-content

## Purpose

Translate marketing content with capability-first service routing and quality assurance. For each target language the router names what the language family needs from a translation service (native script-aware models for Indic targets, formality registers for European, segmentation and script mixing for CJK) and resolves a concrete service at run time — from the brand's recorded preference or from translation MCP servers the user has already connected. When nothing resolves, translation proceeds through the harness's own multilingual capability with mandatory quality scoring — no product is ever named from memory, and none is required. Brand voice, formatting, and key terminology are preserved throughout.

Beyond literal translation, this command analyzes content for elements that require transcreation rather than translation: idioms, wordplay, humor, emotional calls-to-action, and cultural references. When these are detected (or when the user explicitly requests transcreation), it produces multiple creative options with intent-preservation scoring, ensuring the emotional impact and marketing effectiveness carry across languages. Every translation is quality-scored and brand-voice-checked before delivery.

## Input Required

The user must provide (or will be prompted for):

- **Content to translate**: Text inline, file path, or pasted content block. Can be a single piece (headline, email, ad copy) or a structured document (landing page, email template with sections)
- **Target language(s)**: One or more target languages — accepts language codes (hi, de, ja, fr-CA, pt-BR) or plain names (Hindi, German, Japanese, Canadian French, Brazilian Portuguese). Multiple targets can be specified for batch translation
- **Source language**: Optional — the language of the original content. Auto-detected via language-router.py if omitted
- **Transcreation flag**: Optional — set to `true` to force transcreation approach on all content, regardless of content analysis. Useful when the user knows the content is highly creative or culturally sensitive
- **Do-not-translate terms**: Optional — specific terms, product names, or brand elements that must remain in the source language. Overrides any do-not-translate list already defined in the brand profile
- **Formality level**: Optional — `formal` or `informal`, for languages with formal/informal registers (German Sie/du, French vous/tu, etc.). Passed to the resolved translation service when it supports register control; otherwise enforced in the translation instructions and verified in review. If omitted, defaults to brand profile preference or formal
- **Glossary entries**: Optional — term pairs (source: target) to enforce specific translations for key terminology. Supplements any brand-level glossary

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract language configuration — `do_not_translate` term list, `translation_preferences` (preferred services per language pair, formality defaults, glossary), and `locale_formatting` rules (date formats, number separators, currency symbols). Load compliance rules for target markets from `skills/context-engine/compliance-rules.md`. Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load voice-and-tone rules (these inform brand voice scoring of the translation). Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Detect source language**: If the source language was not specified, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/language-router.py" --action detect --text "{content_or_path}"` to identify the source language with confidence score. Report the detected language to the user for confirmation if confidence is below 95%.
3. **Route to a translation capability**: For each target language, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/language-router.py" --action route --source "{source_lang}" --target "{target_lang}" --brand {slug}`. The result names the `capability_kind` and `service_criteria` for the language family and resolves a concrete service ONLY from the brand's recorded preference (`basis: brand-preference`) or the user's connected translation MCP servers (`basis: connected-servers`; with multiple candidates, pick the one best matching the criteria and offer to record the choice via /digital-marketing-pro:language-config). Report the resolved service and its basis to the user. If `basis: unresolved`, say so plainly and follow the payload's resolution ladder — never name a service from memory and never instruct installing one.
4. **Analyze content for transcreation needs**: Scan the source content for elements that resist literal translation — idioms and colloquialisms, wordplay or puns, humor and sarcasm, emotional CTAs and slogans, cultural references and analogies, rhyme or rhythm patterns, double meanings. If the transcreation flag is set or the content contains significant transcreation-requiring elements, prepare a transcreation brief using the methodology defined in `skills/context-engine/transcreation-framework.md`. For each flagged element, document the original intent, emotional tone, and desired audience response to guide creative adaptation.
5. **Execute translation** through whatever the route resolved:
   - **Resolved MCP server** (`basis: brand-preference` or `connected-servers`): call that server. Use its capabilities where they exist — formality/register parameters, glossary or do-not-translate enforcement, tag handling for HTML/XML preservation, script or dialect preferences for Indic targets, variant selection for Chinese. Where the server lacks a capability the criteria call for, enforce it in the instructions you send and verify it in the scoring step.
   - **Unresolved** (`basis: unresolved`): translate with the harness's own multilingual capability, applying the route result's `service_criteria` yourself (register, script fidelity, variant). This path is legitimate, not a degraded fallback — but the step-6 quality score and step 7's below-85 human-review flag are non-negotiable for it.
   - In every path: pass or enforce do-not-translate terms (merged from brand profile and user-provided list), formality settings, glossary entries, and formatting preservation (HTML tags, placeholders like {{first_name}}, Markdown syntax)
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
