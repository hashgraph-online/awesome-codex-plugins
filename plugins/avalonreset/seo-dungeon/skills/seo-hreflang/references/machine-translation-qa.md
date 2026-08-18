# Machine-translation QA flag (Jan 2025 QRG)

Google's January 23, 2025 Quality Rater Guidelines update added
explicit language about **machine-translated content with no human
review** as a form of scaled content abuse (§4.6.5).

> "Using automated tools (generative AI or otherwise) as a low-effort
> way to produce many pages that add little-to-no value."

Machine-translated content is fine **when reviewed by a human
speaker and corrected**. Untranslated MT — or "lightly post-edited"
output that still contains hallucinated terms, wrong gender/number
agreement, or untranslated proper nouns — is treated as scaled
content abuse.

## Signals the seo-hreflang audit should surface

| Signal | Severity | Notes |
|---|---|---|
| Multiple `hreflang` alternates point to URLs whose content is identical except for header chrome | Critical | Indicates the body wasn't translated; just template wrapped. |
| `lang="xx"` attribute on `<html>` doesn't match the body language | High | Translation pipeline output without a final QA step. |
| Auto-translated `<meta name="description">` longer than 160 chars (untrimmed) | Medium | The translator overran the snippet limit — no human reviewer caught it. |
| `lang` attribute is `auto` or missing entirely | Medium | Pages that don't declare their language confuse hreflang + AI crawlers. |
| Untranslated proper nouns or product names sprinkled in body | Low (heuristic) | Common MT failure mode; hard to detect automatically. |
| Schema.org `inLanguage` field absent or wrong | Medium | Multi-language audits should cross-check `inLanguage` vs. body. |

## What the audit should NOT flag

- Sites that have a few MT pages clearly labelled as MT (a
  human-translation-fallback pattern). Google's QRG explicitly
  permits MT *when honestly labelled and clearly scoped*.
- Machine-translated UI strings — those are i18n, not "content".
- Content with `lang="auto"` if the audit can't fetch a fallback
  signal (be conservative; don't claim what we can't verify).

## Cross-skill delegation

- For per-page hreflang validation, stay inside `seo-hreflang`.
- For broader scaled-content scoring (entropy of translated pages,
  AI-pattern detection in body), defer to `seo-content` via
  `python3 scripts/content_quality.py`.
- For "is this translated by Google's own auto-translate widget"
  detection, look for the `.goog-te-banner-frame` iframe; auto-
  translate widgets are explicitly exempted from MT-scaled-content
  abuse but produce poor passage-citability anyway.

## Primary sources

- Jan 2025 QRG §4.6.5: https://services.google.com/fh/files/misc/hsw-sqrg.pdf
- John Mueller on MT (multiple SOTR episodes, 2024-2025): MT is OK
  when reviewed by a human; bulk MT without review is abuse.

Last verified: 2026-05-17.
