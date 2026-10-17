# Multilingual Content — Localization Guide

## Localization Readiness Checklist

### Content Readiness
- [ ] Source content is finalized (never localize a draft)
- [ ] Cultural references identified and flagged for adaptation
- [ ] Idioms, slang, and humor marked for transcreation
- [ ] Brand terms and product names that should NOT be translated are listed
- [ ] Glossary of key terms with approved translations exists
- [ ] Style guide adapted for each target locale

### Technical Readiness
- [ ] CMS supports multilingual content (separate URLs per locale)
- [ ] URL structure decided (subdomain, subdirectory, or ccTLD)
- [ ] hreflang tags implemented correctly
- [ ] Character encoding supports target languages (UTF-8)
- [ ] RTL (right-to-left) layout support for Arabic, Hebrew, Farsi, Urdu

### Legal Readiness
- [ ] Required legal disclaimers per market identified
- [ ] Privacy policy localized for each jurisdiction
- [ ] Cookie consent adapted for local regulations
- [ ] Product claims verified for legality in each market

---

## Cultural Adaptation Framework

| Dimension | What to Adapt | Example |
|-----------|-------------|---------|
| **Tone** | Formality level varies by culture | German/Japanese: more formal; US/Australian: more casual |
| **Humor** | What's funny varies enormously | Puns rarely translate; slapstick is more universal |
| **Imagery** | Visual cultural norms differ | Hand gestures, clothing, family structure in images |
| **Colors** | Color symbolism varies | White = purity (West) vs mourning (parts of Asia) |
| **Numbers** | Lucky/unlucky numbers | 4 is unlucky in China/Japan; 13 in Western cultures |
| **Dates** | Format varies | MM/DD/YYYY (US) vs DD/MM/YYYY (EU/UK) vs YYYY/MM/DD (ISO) |
| **Currency** | Local currency and formatting | $1,000.00 (US) vs 1.000,00 € (Germany) |
| **Measurement** | Imperial vs metric | US: miles, pounds, Fahrenheit. Most of world: km, kg, Celsius |
| **Names** | Name order varies | First Last (West) vs Last First (East Asia) |
| **Testimonials** | Social proof expectations differ | Some cultures prefer authority figures, others prefer peers |

---

## Translation vs Transcreation

| Approach | When to Use | Process |
|----------|-----------|---------|
| **Translation** | Technical docs, legal text, factual content | Direct translation maintaining meaning |
| **Localization** | Marketing content, UI, product descriptions | Translation + cultural/market adaptation |
| **Transcreation** | Ad copy, slogans, emotional content, campaigns | Complete creative recreation for target culture |

### Transcreation is required when:
- The content relies on wordplay, puns, or idioms
- The emotional appeal differs across cultures
- The cultural context changes the meaning
- The CTA needs to motivate differently

---

## SEO for Multilingual Content

### hreflang Implementation
```html
<link rel="alternate" hreflang="en-us" href="https://example.com/page" />
<link rel="alternate" hreflang="es-es" href="https://example.com/es/page" />
<link rel="alternate" hreflang="de-de" href="https://example.com/de/page" />
<link rel="alternate" hreflang="x-default" href="https://example.com/page" />
```

### URL Structure Options
| Option | Example | Pros | Cons |
|--------|---------|------|------|
| Subdirectory | example.com/de/ | Easy to manage, inherits domain authority | Less geo-targeting signal |
| Subdomain | de.example.com | Clear separation | May not inherit full authority |
| ccTLD | example.de | Strongest geo signal | Expensive, separate SEO per domain |

### Localized Keyword Research
- Do NOT just translate English keywords — search behavior differs by language
- Use local keyword tools (Google Keyword Planner set to target country/language)
- Check search volume for local variations
- Study local competitor content for keyword patterns

---

## RTL (Right-to-Left) Considerations

For Arabic, Hebrew, Farsi, Urdu content:
- Text alignment flips (right-aligned body text)
- Layout mirrors (navigation, sidebars, images flip horizontally)
- Numbers remain left-to-right within RTL text
- Icons with directional meaning flip (arrows, progress bars)
- Bidirectional text support for mixed LTR/RTL content
- Test thoroughly — many layouts break with RTL

---

## Quality Assurance Checklist

- [ ] Native speaker reviewed all translated content
- [ ] Brand terminology used consistently across all locales
- [ ] No machine-translation artifacts (awkward phrasing, false friends)
- [ ] Cultural references are appropriate for target audience
- [ ] All localized pages have correct hreflang tags
- [ ] Forms work with local address/phone formats
- [ ] Payment methods are relevant to the market
- [ ] Date, time, currency formatting matches locale
- [ ] Images are culturally appropriate
- [ ] Legal disclaimers are market-specific and correct
