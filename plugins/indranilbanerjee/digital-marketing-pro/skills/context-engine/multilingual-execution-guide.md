# Multilingual Marketing Execution Guide

End-to-end reference for planning, executing, and quality-assuring multilingual marketing campaigns. Covers translation service selection, cultural adaptation, RTL implementation, Indic and CJK specifics, SEO, and budget optimization.

---

## 1. End-to-End Multilingual Workflow

Every multilingual campaign follows this eight-step pipeline. Each step maps to a specific command and produces an artifact that feeds the next step.

### Step 1: Language Configuration

**Command:** `/digital-marketing-pro:language-config`

Define the languages your brand operates in, set primary and secondary languages, and configure translation preferences in the brand profile.

```
language:
  primary: en-US
  secondary: [de-DE, fr-FR, es-ES, ja-JP, hi-IN]
  translation_preferences:
    default_service: auto          # let language-router decide
    force_service: null             # override: deepl | sarvam-ai | google-cloud-translation | lara-translate
    formality: formal               # formal | informal | auto
    glossary_enabled: true
    do_not_translate: ["BrandName", "ProductX", "ProSuite"]
  transcreation_triggers: [slogan, cta, headline, tagline, emotional_campaign]
```

Output: Updated brand profile with language block.

### Step 2: Create Source Content

Author content in the primary language following brand voice guidelines. Tag each content piece with its type (technical, marketing, creative, legal) so the pipeline knows which translation approach to use downstream.

### Step 3: Evaluate Source Content

**Command:** `/digital-marketing-pro:eval-content`

Score the source content for clarity, brand voice alignment, and translatability before spending money on translation. Ambiguous source text produces bad translations in every language.

Translatability checklist:
- No idioms that rely on source-language wordplay
- Short, clear sentences (aim for Flesch-Kincaid grade 8-10 for marketing copy)
- Cultural references flagged for adaptation
- Placeholders and variables clearly marked
- Brand terms from the do-not-translate list used consistently

### Step 4: Translate

**Command:** `/digital-marketing-pro:translate-content`

The `language-router.py` script automatically selects the best translation service based on the target language family. Content tagged as requiring transcreation is routed to the transcreation workflow instead (see Section 4 and `transcreation-framework.md`).

### Step 5: Score Translation Quality

**Command:** `/digital-marketing-pro:multilingual-score`

Automated quality scoring across five dimensions: meaning accuracy, fluency, terminology consistency, brand voice, and formatting. Scores below 70 are flagged for human review. Scores below 50 trigger re-translation with a different service.

### Step 6: Localize Campaign Assets

**Command:** `/digital-marketing-pro:localize-campaign`

Beyond text translation, this step adapts:
- Date and time formats
- Currency and number formats
- Images and visual assets (text in images, cultural appropriateness)
- CTAs and conversion flows
- Payment methods and trust signals
- Platform-specific formatting (character limits, hashtags, handles)

### Step 7: Language Audit

**Command:** `/digital-marketing-pro:language-audit`

Final quality gate before publishing. Checks:
- All target languages have complete translations (no missing strings)
- Glossary terms are consistent across all languages
- RTL languages have correct directional formatting
- hreflang tags are properly configured
- No source-language text leaking into translated assets
- Compliance and legal disclaimers present in all required languages

### Step 8: Publish

Deploy localized assets to target platforms. Monitor performance per language/market and feed learnings back into the language configuration for the next cycle.

---

## 2. Translation Service Comparison

| Feature | DeepL | Sarvam AI | Google Cloud Translation | Lara Translate |
|---|---|---|---|---|
| **Languages** | 30+ | 22 Indic | 100+ | 100+ |
| **Primary strength** | European language quality | Indic language specialist | Broadest language coverage | Marketing context preservation |
| **Formality control** | Yes (formal/informal) | No | No | Yes (formal/informal) |
| **Glossary support** | Yes | No | Adaptive NMT | Yes (Translation Memory) |
| **Batch processing** | Yes | Yes | Yes | Yes |
| **Best for** | DE, FR, ES, IT, PT, NL, PL, RU, JA, KO, ZH | HI, TA, TE, BN, MR, GU, KN, ML, PA | Rare languages, AR, TH, VI, ID, SW | Marketing copy, brand voice content |
| **API rate limits** | 500K chars/month (free), unlimited (pro) | Per-request, batch preferred | 6M chars/month default | Project-based quotas |
| **Context window** | Sentence + paragraph | Sentence-level | Sentence-level | Document-level TM |
| **MCP server** | `deepl` | `sarvam-ai` | `google-cloud-translation` | `lara-translate` |

### When to use each service

- **DeepL**: Default for European languages. Superior quality for DE, FR, ES, IT, NL, PL. Also strong for JA, KO, ZH. Use when formality control matters.
- **Sarvam AI**: Mandatory for Indic languages. Purpose-built models for Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and 13 other Indic languages. Handles script-specific nuances that general-purpose engines miss.
- **Google Cloud Translation**: Fallback for languages not well-served by DeepL or Sarvam. Primary choice for Arabic, Thai, Vietnamese, Indonesian, Swahili, and other languages outside European/Indic families.
- **Lara Translate**: Best for marketing content where brand voice preservation is critical. Translation Memory maintains consistency across campaigns. Use for high-visibility marketing copy when budget allows.

---

## 3. Language Routing Decision Tree

The `language-router.py` script automates service selection using this logic:

```
Input text + target language
    |
    v
Detect source language (if not specified)
    |
    v
Check brand profile for force_service override
    |-- If override set --> Use specified service
    |
    v
Determine target language family
    |
    |-- Indic (HI, TA, TE, BN, MR, GU, KN, ML, PA, OR, AS, UR, SD, NE, SI, etc.)
    |       --> Primary: Sarvam AI
    |       --> Fallback: Google Cloud Translation
    |
    |-- European (DE, FR, ES, IT, PT, NL, PL, RU, CS, DA, FI, SV, EL, HU, RO, SK, BG, etc.)
    |       --> Primary: DeepL
    |       --> Fallback: Lara Translate --> Google Cloud Translation
    |
    |-- CJK (JA, KO, ZH-CN, ZH-TW)
    |       --> Primary: DeepL
    |       --> Fallback: Google Cloud Translation
    |
    |-- Semitic (AR, HE)
    |       --> Primary: Google Cloud Translation
    |       --> Fallback: DeepL (limited support)
    |
    |-- Other (TH, VI, ID, MS, SW, TL, etc.)
    |       --> Primary: Google Cloud Translation
    |       --> Fallback: Lara Translate
    |
    v
Check content type
    |-- If transcreation_trigger (slogan, cta, headline, tagline, emotional_campaign)
    |       --> Route to transcreation workflow
    |       --> See transcreation-framework.md
    |
    v
Check glossary/do-not-translate list
    --> Protect brand terms before sending to API
    --> Restore after translation
    |
    v
Execute translation --> Score --> Return result
```

### Overriding the router

Users can force a specific service in the brand profile:

```yaml
translation_preferences:
  force_service: deepl    # bypass routing, always use DeepL
```

Or per-request via the translate command:

```
/digital-marketing-pro:translate-content --service=sarvam-ai --target=hi-IN
```

---

## 4. Transcreation Methodology

Transcreation is creative translation where the output may share no words with the original but achieves the same emotional and commercial goal. See `transcreation-framework.md` for the complete framework.

### When to transcreate (not translate)

- Slogans and taglines
- Headlines and subject lines
- CTAs where emotion or urgency matters
- Humor, wordplay, puns, or double meanings
- Cultural references and idioms
- Emotional campaigns (fear, joy, nostalgia, aspiration)
- Content where rhythm, rhyme, or sound matters

### When standard translation is sufficient

- Product specifications and data sheets
- Legal and compliance text
- FAQ and help center articles
- Internal communications
- Technical documentation

### Quick process

1. Create a transcreation brief (intent, emotion, key message, constraints)
2. Generate 3-5 options in the target language (not translations, but original creations)
3. Score each option against the brief
4. Select and refine the winner
5. Validate with `/digital-marketing-pro:multilingual-score` and `/digital-marketing-pro:prompt-test`

---

## 5. Cultural Dimension Mapping (Hofstede Applied to Marketing)

Geert Hofstede's cultural dimensions provide a practical framework for adapting marketing messages across markets. Below is how each dimension affects marketing execution.

### Individualism vs Collectivism

| High Individualism (US, UK, AU, NL) | High Collectivism (JP, KR, IN, CN, ID) |
|---|---|
| "Your personal success" | "Your team's achievement" |
| Individual testimonials | Group consensus, popularity indicators |
| Personal benefit CTAs | Family/community benefit CTAs |
| Self-expression messaging | Belonging and harmony messaging |
| "Stand out from the crowd" | "Join millions who trust us" |

### Power Distance

| Low Power Distance (DE, NL, DK, SE, NZ) | High Power Distance (IN, MY, PH, MX, SA) |
|---|---|
| Peer-level, conversational tone | Authority-based trust signals |
| "We're partners in this" | "Recommended by industry leaders" |
| User-generated content valued | Expert endorsements valued |
| Informal brand voice acceptable | Respectful, aspirational tone expected |
| Question authority freely | Hierarchy signals credibility |

### Uncertainty Avoidance

| Low Uncertainty Avoidance (US, UK, SG, DK, SE) | High Uncertainty Avoidance (JP, DE, FR, KR, GR) |
|---|---|
| Bold claims, innovation focus | Detailed specifications, certifications |
| "Try it risk-free" | "Tested and certified to ISO 9001" |
| Emphasize novelty and disruption | Emphasize reliability and track record |
| Short-form content, quick decisions | Long-form content, detailed comparisons |
| "Be the first to try" | "Trusted by experts for 20 years" |

### Long-Term Orientation

| Short-Term (US, UK, AU, NG) | Long-Term (JP, KR, CN, DE) |
|---|---|
| Quick results, immediate ROI | Legacy, tradition, long-term value |
| "See results in 30 days" | "Building for the next generation" |
| Quarterly performance focus | Multi-year vision messaging |
| Trend-driven campaigns | Heritage and craftsmanship narratives |

### Indulgence vs Restraint

| High Indulgence (US, UK, AU, MX, CO) | High Restraint (RU, PL, KR, EG, PK) |
|---|---|
| Emotional, fun, aspirational | Factual, restrained, practical |
| Lifestyle imagery | Product-focused imagery |
| "Treat yourself" | "A sensible investment" |
| Humor and entertainment | Information and education |
| Desire-driven messaging | Need-driven messaging |

### Practical application

When adapting a campaign for a new market, cross-reference the target country against these dimensions and adjust:
- **CTAs**: Urgency vs relationship vs authority
- **Testimonials**: Individual vs consensus vs expert
- **Visual elements**: Lifestyle vs product, individual vs group
- **Urgency tactics**: Direct urgency vs seasonal/appropriate timing
- **Trust signals**: Guarantees vs certifications vs social proof

---

## 6. RTL Implementation Checklist

For Arabic (AR), Hebrew (HE), Farsi/Persian (FA), and Urdu (UR).

### Text and Layout

- [ ] Set `dir="rtl"` on the root container element
- [ ] Set `lang` attribute to the correct language code (e.g., `lang="ar"`)
- [ ] Use CSS `direction: rtl` and `text-align: right` (or use logical properties: `text-align: start`)
- [ ] Replace `margin-left`/`padding-right` with logical properties: `margin-inline-start`/`padding-inline-end`
- [ ] Test that text wraps correctly in RTL mode
- [ ] Verify that bidirectional text (RTL with embedded LTR like English brand names) renders correctly using Unicode BiDi algorithm

### Numbers and Data

- [ ] Numbers remain LTR within RTL text (this is automatic in most browsers)
- [ ] Phone numbers display in correct reading order
- [ ] Currency symbols position correctly (e.g., SAR amounts: "100 ر.س" with symbol on the left in RTL)
- [ ] Date formats match locale (Arabic: DD/MM/YYYY, Hebrew: DD.MM.YYYY)
- [ ] Percentage signs position correctly

### Visual Elements

- [ ] Navigation menus flip to right-to-left order
- [ ] Breadcrumbs read right-to-left with reversed separators
- [ ] Progress bars and timelines reverse direction
- [ ] Directional icons (arrows, chevrons) mirror horizontally
- [ ] Non-directional icons (search, settings) do NOT mirror
- [ ] Checkmarks and universal symbols do NOT mirror
- [ ] Image compositions that imply direction (person looking forward, hand pointing) are evaluated for mirroring

### Forms and Inputs

- [ ] Form labels align to the right
- [ ] Input fields align text to the right
- [ ] Validation messages appear on the correct side
- [ ] Submit/action buttons move to the left side (start position in RTL)
- [ ] Dropdown menus open in the correct direction

### Email Templates

- [ ] HTML email uses `dir="rtl"` on the outer table
- [ ] Table-based layouts reverse column order
- [ ] Preheader text reads correctly in RTL email clients
- [ ] Test in Outlook (Windows), Apple Mail, Gmail (web and mobile), Yahoo Mail

### Social Media

- [ ] Twitter/X: Supports RTL natively; test thread readability
- [ ] Facebook/Instagram: RTL text in captions renders correctly; test carousel direction
- [ ] LinkedIn: RTL article content may need manual formatting checks
- [ ] Platform-specific character limits may differ when mixing RTL and LTR scripts

---

## 7. Indic Language Marketing Guide

Covers Hindi (HI), Tamil (TA), Telugu (TE), Bengali (BN), Marathi (MR), Gujarati (GU), Kannada (KN), Malayalam (ML), and Punjabi (PA).

### Script Rendering

Each Indic language uses a distinct script. Ensure:
- Fonts support the target script (Noto Sans is a safe cross-script family)
- Complex conjunct characters (ligatures) render correctly on all devices
- Line-breaking algorithms handle Indic scripts properly (some scripts have different word-boundary rules)
- Font sizes may need to be larger than Latin equivalents for readability (Devanagari, Tamil, and Malayalam typically need 10-15% larger sizes)

### Transliteration Strategy

Use transliteration (writing Indic words in Latin script) for:
- Brand names that should remain recognizable: "BrandName" not "ब्रांडनेम"
- Technical terms without established Indic equivalents
- URLs, email addresses, and code snippets
- Hashtags (Latin script hashtags have broader reach)

Use native script for:
- Body copy and main messaging
- CTAs and buttons (native script builds trust with non-English audiences)
- Legal and compliance text
- Cultural and emotional content

### Code-Switching (Hinglish and Mixed-Language Marketing)

Hindi-English code-switching (Hinglish) is the dominant communication style for urban Indian audiences aged 18-45. For many campaigns targeting Indian metros, Hinglish outperforms both pure Hindi and pure English.

Examples:
- Pure English: "Get 50% off on your first order"
- Pure Hindi: "अपने पहले ऑर्डर पर 50% की छूट पाएं"
- Hinglish: "Apne pehle order pe 50% off pao!" (often most effective for urban audiences)

Guidelines:
- Match code-switching level to audience: Metro urban (heavy Hinglish) vs Tier 2-3 cities (more Hindi) vs rural (pure regional language)
- Keep brand names and technical terms in English
- Use Devanagari script for Hindi-heavy Hinglish, Latin script for English-heavy Hinglish
- Test both approaches with `/digital-marketing-pro:prompt-test`

### Regional Festival Calendar (Campaign Timing)

| Period | Festival | Primary Regions | Marketing Opportunity |
|---|---|---|---|
| Jan 14-15 | Makar Sankranti / Pongal | Pan-India / Tamil Nadu | New beginnings, harvest themes |
| Mar-Apr | Holi | North and West India | Color, joy, playfulness campaigns |
| Apr 14 | Baisakhi / Tamil New Year | Punjab / Tamil Nadu | New year offers, fresh starts |
| Aug-Sep | Onam | Kerala | Harvest, prosperity, homecoming |
| Aug-Sep | Ganesh Chaturthi | Maharashtra, Karnataka | Community, celebration |
| Sep-Oct | Navratri / Durga Puja | Gujarat, West Bengal | Multi-day campaign arcs |
| Oct-Nov | Diwali | Pan-India | Biggest commercial event: gifts, electronics, fashion, home |
| Nov | Chhath Puja | Bihar, Jharkhand, UP | Family, tradition |
| Jan | Pongal (Tamil) / Lohri (Punjabi) | Regional | Harvest, gratitude |

### Sarvam AI Capabilities by Language

Sarvam AI provides purpose-built models for Indic languages with:
- Native text generation (not just translation from English)
- Speech-to-text and text-to-speech for voice campaigns
- Transliteration support
- Cultural context awareness in translations
- Support for all 22 scheduled languages of India

Best results: Hindi, Tamil, Telugu, Bengali, Marathi. Good results: Gujarati, Kannada, Malayalam, Punjabi. Expanding: Odia, Assamese, Urdu.

### Social Media Platform Preferences

| Language/Region | Primary Platforms | Notes |
|---|---|---|
| Hindi (urban) | WhatsApp, Instagram, YouTube | Short-form video dominates |
| Hindi (semi-urban/rural) | WhatsApp, YouTube, ShareChat | ShareChat is Hindi-first |
| Tamil | WhatsApp, YouTube, Instagram | Strong regional content ecosystem |
| Telugu | WhatsApp, YouTube, Instagram | YouTube consumption extremely high |
| Bengali | WhatsApp, Facebook, YouTube | Facebook still strong in Bengal |
| Marathi | WhatsApp, Instagram, ShareChat | Regional pride in Marathi content |

### Payment and E-commerce Localization

- UPI is the dominant digital payment method; display UPI as a primary option
- Cash on Delivery (COD) remains important in Tier 2-3 cities and for first-time online buyers
- Display prices in INR with proper formatting: ₹1,00,000 (Indian numbering: lakhs and crores, not millions)
- EMI (equated monthly installment) options significantly boost conversion for high-value purchases
- Include local payment wallets: Paytm, PhonePe, Google Pay

---

## 8. CJK Considerations

### Japanese (JA)

**Writing system**: Japanese uses three scripts simultaneously: Kanji (Chinese characters), Hiragana (native syllabary), and Katakana (used for foreign words, emphasis, onomatopoeia). Marketing copy must use the correct mix.

- Katakana for foreign brand names and loanwords: マーケティング (marketing), ブランド (brand)
- Kanji + Hiragana for native Japanese phrasing
- Character limits differ from word limits: A 280-character tweet holds roughly 140 words of meaning in Japanese vs 40-50 in English

**Honorific levels (Keigo)**: Japanese has three formality levels that fundamentally change sentence structure:
- Teineigo (丁寧語): Polite — standard for B2C marketing
- Sonkeigo (尊敬語): Respectful — for referring to the customer's actions
- Kenjougo (謙譲語): Humble — for referring to your company's actions
- Getting keigo wrong is a serious brand credibility issue. Always have a native speaker review.

**Seasonal references**: Japanese marketing is deeply tied to seasons (四季). Spring (sakura themes, new beginnings), Summer (festivals, refreshment), Autumn (harvest, warmth), Winter (year-end, gratitude). Campaigns that ignore seasonal context feel tone-deaf.

**Optimization**: Google Japan dominates search. Yahoo! Japan (powered by Google) has a separate display ad network. LINE is the dominant messaging platform (not WhatsApp or Facebook Messenger).

### Korean (KO)

**Hangul typography**: Korean uses the Hangul alphabet with syllable blocks. Ensure:
- Font supports all Hangul syllable combinations (11,172 possible blocks)
- Line height accommodates taller character blocks
- Mixed Hangul-Latin text has consistent baseline alignment

**Politeness levels**: Korean has seven speech levels. Marketing typically uses:
- Hapsyo-che (합쇼체): Formal polite — corporate, luxury, B2B
- Haeyo-che (해요체): Informal polite — most B2C marketing, friendly but respectful
- Hae-che (해체): Casual — youth brands, social media, peer-level tone
- Mixing levels within a campaign is a serious tone error.

**Platform optimization**: Naver dominates search (not Google). Kakao dominates messaging and commerce. Coupang dominates e-commerce. Optimize for these platforms first, Google second.

**Cultural notes**: Age hierarchy matters in testimonials (older endorsers carry authority). K-beauty and K-pop references resonate broadly but must feel authentic. "Made in Korea" is a strong trust signal in beauty and technology.

### Chinese (ZH)

**Simplified vs Traditional**:
- Simplified Chinese (ZH-CN): Mainland China, Singapore, Malaysia
- Traditional Chinese (ZH-TW): Taiwan, Hong Kong, Macau
- These are NOT just font variants. Vocabulary, idioms, and cultural references differ significantly. Content for Taiwan should not be Simplified Chinese with Traditional characters swapped in.

**Character counting**: Chinese uses characters, not words. One Chinese character typically conveys the meaning of 1-2 English words. A 500-word English article might translate to 800-1200 Chinese characters. Platform character limits must be recalculated.

**Platform ecosystem**:
- Search: Baidu (mainland), Google (TW/HK)
- Social: WeChat (dominant super-app), Weibo (microblogging), Xiaohongshu/RED (lifestyle/commerce), Douyin (TikTok's Chinese version)
- E-commerce: Taobao, Tmall, JD.com, Pinduoduo
- Each platform has unique content formats, character limits, and advertising systems

**Baidu SEO**: Different ranking factors than Google. Prioritizes: .cn domains, ICP filing (required for mainland hosting), Baidu Webmaster Tools verification, Baidu-specific structured data, Chinese-language backlinks.

**Regulatory**: Advertising Law of the PRC prohibits superlatives ("best", "most", "first", "number one") unless substantiated by a third-party authority. This affects all marketing copy for mainland China.

---

## 9. Brand Glossary Management

A brand glossary ensures that key terms are translated consistently across all languages and all campaigns.

### Do-Not-Translate List

Store in the brand profile:

```yaml
language:
  do_not_translate:
    - "BrandName"
    - "ProductX"
    - "ProSuite"
    - "SmartDash"
    - "AI-Powered"    # keep English in all markets where appropriate
```

The `language-router.py` script wraps these terms in placeholder tokens before sending text to translation APIs, then restores them afterward. This prevents translation engines from translating brand names or product names.

### Approved Translations

For terms that should be translated but must use a specific approved translation:

```yaml
language:
  glossary:
    "customer success":
      de: "Kundenerfolg"
      fr: "succès client"
      ja: "カスタマーサクセス"    # katakana loanword preferred over translation
      hi: "ग्राहक सफलता"
    "dashboard":
      de: "Dashboard"           # keep English loanword
      fr: "tableau de bord"
      ja: "ダッシュボード"
      hi: "डैशबोर्ड"            # transliteration preferred
```

### Glossary Maintenance

- Review glossary quarterly or when entering new markets
- When a new product or feature launches, add terms to the glossary before translation begins
- The `/digital-marketing-pro:multilingual-score` command checks glossary adherence and flags inconsistencies
- Export glossary in TBX format for use with external translation tools

---

## 10. Multilingual SEO Execution

### Localized Keyword Research

Never just translate keywords. The same concept may be searched with completely different terms in different languages.

Process:
1. Start with seed keywords in the source language
2. Translate seeds as a starting point
3. Use local keyword research tools to discover what people actually search:
   - Google Keyword Planner (set to target country)
   - Baidu Keyword Planner (for ZH-CN)
   - Naver Keyword Tool (for KO)
   - Yandex Wordstat (for RU)
4. Analyze local competitor rankings for target terms
5. Check search volume and competition in the target market (not just translated terms)
6. Build a per-language keyword map

Example: "affordable CRM software"
- DE: "CRM Software kostenlos" (free) or "günstiges CRM" (affordable) — different search intent
- JP: "CRM ツール 比較" (CRM tool comparison) — comparison intent dominates
- FR: "logiciel CRM gratuit" (free CRM software) — "gratuit" is a stronger search trigger than "abordable"

### hreflang Implementation

Every multilingual page must have hreflang tags linking all language variants:

```html
<link rel="alternate" hreflang="en-US" href="https://example.com/en-us/page" />
<link rel="alternate" hreflang="de-DE" href="https://example.com/de-de/seite" />
<link rel="alternate" hreflang="ja" href="https://example.com/ja/page" />
<link rel="alternate" hreflang="x-default" href="https://example.com/en-us/page" />
```

Rules:
- `x-default` points to the fallback page (usually en-US or a language-selector page)
- Use language-region codes where relevant (en-US vs en-GB, zh-CN vs zh-TW, pt-BR vs pt-PT)
- hreflang must be reciprocal: if page A references page B, page B must reference page A
- Use `/digital-marketing-pro:hreflang-check` to audit implementation and detect orphaned or broken references

### International Sitemaps

- Create per-language sitemaps: `sitemap-en.xml`, `sitemap-de.xml`, `sitemap-ja.xml`
- Or use a single sitemap with `xhtml:link` alternates per URL
- Set geo-targeting in Google Search Console for country-specific subdomains or subdirectories
- Submit sitemaps to local search engines: Baidu Webmaster Tools, Yandex Webmaster, Naver Search Advisor

### Search Engine-Specific Optimization

| Engine | Market | Key Differences |
|---|---|---|
| **Google** | Global default | Standard SEO best practices |
| **Baidu** | China (mainland) | Requires ICP filing, .cn domain preferred, meta keywords still used, slower to index JS-rendered content |
| **Yandex** | Russia, CIS | Behavioral factors heavily weighted, regional ranking varies by city, Yandex.Metrica integration helps |
| **Naver** | South Korea | Blog content ranks in dedicated blog section, Naver Cafe (community) content ranks, Naver Smart Store for e-commerce |

---

## 11. Quality Assurance for Translations

### Reviewer Checklist

For every translated piece before publication:

- [ ] **Meaning accuracy**: Does the translation convey the same meaning as the source?
- [ ] **Cultural appropriateness**: Are there any cultural missteps, insensitive references, or inappropriate imagery?
- [ ] **Brand voice**: Does the translation match the brand's established voice in this language?
- [ ] **Formatting**: Are dates, numbers, currencies, and measurements in the correct local format?
- [ ] **Placeholders**: Are all dynamic variables (names, numbers, URLs) intact and correctly positioned?
- [ ] **Completeness**: Is any content missing or truncated?
- [ ] **Compliance**: Are legal disclaimers, privacy notices, and regulatory text present and accurate?
- [ ] **Technical**: Do links work? Are character limits respected? Does it render correctly?

### Common Machine Translation Errors

| Error Type | Example | Languages Most Affected |
|---|---|---|
| Gender agreement | "Your account is ready. She is active." | FR, DE, ES, IT, AR, HI |
| Formality mismatch | Using informal "tu" instead of formal "vous" | FR, DE, ES, PT, KO, JA |
| False friends | "actually" translated as "actualmente" (currently) in ES | All Romance languages |
| Idiom literalization | "break a leg" translated literally | All languages |
| Word order | SVO source forced onto SOV target | JA, KO, HI, DE (verb-final clauses) |
| Honorific errors | Wrong keigo level in Japanese | JA, KO |
| Classifier omission | Missing measure words in Chinese | ZH, JA, KO, TH |
| Compound splitting | German compounds incorrectly broken into separate words | DE |

### Post-Editing Guidelines

**Light Post-Edit (PE)**: Fix only errors that block comprehension or damage brand.
- Fix: Factual errors, offensive content, broken formatting, missing translations
- Leave: Awkward but understandable phrasing, stylistic imperfections
- Use for: Internal comms, knowledge base, low-visibility content
- Speed: 5,000-8,000 words/hour

**Full Post-Edit (PE)**: Fix all errors to achieve publication quality.
- Fix: Everything in light PE plus fluency, style, brand voice, cultural fit
- The output should be indistinguishable from human-written content
- Use for: Marketing emails, blog posts, social media, product pages
- Speed: 1,500-3,000 words/hour

---

## 12. Budget Optimization

### Translation Approach Decision Matrix

| Approach | Cost per Word | Quality | Turnaround | Use For |
|---|---|---|---|---|
| **MT only** | $0.00-0.02 | Functional | Minutes | Internal comms, drafts, low-visibility content, gisting |
| **MT + Light PE** | $0.03-0.06 | Good | Hours | Product descriptions, FAQ, support articles, knowledge base |
| **MT + Full PE** | $0.06-0.10 | High | 1-2 days | Marketing emails, blog posts, social content, product pages |
| **Transcreation** | $0.15-0.30 | Premium | 3-5 days | Slogans, CTAs, headlines, emotional campaigns, brand voice |
| **Human translation** | $0.10-0.20 | High | 2-4 days | Legal, compliance, regulated content, contracts |

### Cost-Saving Strategies

1. **Tier your content**: Not everything needs transcreation. Classify content by visibility and emotional weight, then assign the appropriate approach.
2. **Invest in glossaries**: Upfront glossary creation saves money on every subsequent translation by reducing reviewer corrections.
3. **Reuse Translation Memory**: Lara Translate's TM means repeated or similar content gets cheaper over time. Prioritize consistency to maximize TM leverage.
4. **Batch translations**: Sending content in batches rather than one-off requests reduces per-unit cost across all services.
5. **Source content quality**: Spend time making source content clear and translatable. Ambiguous source text causes expensive corrections downstream.
6. **Automate quality scoring**: Use `/digital-marketing-pro:multilingual-score` to catch issues before human review, reducing reviewer time.

### ROI Tracking

Track per-language:
- Translation spend per content piece
- Performance metrics (CTR, conversion, engagement) per language
- Cost per conversion by language
- Compare MT-only vs MT+PE vs transcreation performance for similar content types
- Feed results back into the decision matrix to optimize spend allocation
