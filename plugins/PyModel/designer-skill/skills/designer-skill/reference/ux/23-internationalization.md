# Internationalization & Localization

Internationalization (**i18n**) is designing and building a product so it *can* be
adapted to different languages, regions, and cultures without re-engineering.
Localization (**l10n**) is the adaptation itself—translating strings, swapping
formats, adjusting layout. Get i18n wrong up front and every locale becomes a
rewrite; get it right and adding a language is a content task, not a code task.

> Rule of thumb: assume your UI will run right-to-left, in a language whose words
> are 40% longer than English, with dates and numbers formatted by the user's
> locale—*before* you have a single translation.

---

## RTL & Bidirectional Layout

Arabic, Hebrew, Persian, and Urdu read right-to-left (RTL). RTL is not "flip the
CSS"—it's a directional mirror of the *layout*, while some content stays unchanged.

### Use logical CSS properties, not physical ones

Physical properties (`left`, `right`, `margin-left`) hard-code LTR assumptions.
Logical properties resolve against the document/element direction automatically.

```css
/* ❌ Physical — breaks in RTL */
.card { margin-left: 16px; text-align: left; border-left: 2px solid; }

/* ✅ Logical — mirrors automatically with dir="rtl" */
.card {
  margin-inline-start: 16px;
  text-align: start;
  border-inline-start: 2px solid;
  padding-inline: 12px;      /* start + end */
  inset-inline-start: 0;     /* replaces left/right for positioning */
}
```

| Physical | Logical equivalent |
|----------|-------------------|
| `margin-left` / `margin-right` | `margin-inline-start` / `margin-inline-end` |
| `padding-left` / `padding-right` | `padding-inline-start` / `padding-inline-end` |
| `left` / `right` | `inset-inline-start` / `inset-inline-end` |
| `text-align: left` | `text-align: start` |
| `border-left` | `border-inline-start` |

### Set direction at the root, let it cascade

```html
<html lang="ar" dir="rtl">
```

Use `dir="auto"` on user-generated content fields so a single input handles either
direction based on the first strong character. For mixed-direction strings (an
English brand name inside Arabic text), rely on the Unicode Bidirectional Algorithm
and isolate embedded runs with `<bdi>` or CSS `unicode-bidi: isolate`.

### Mirror these — but not those

**Mirror** (they imply direction of reading/progress):
- Layout: navigation, sidebars, alignment, the whole grid
- Directional icons: back/forward arrows, chevrons, breadcrumb separators
- Progress bars, sliders, carousels, "next step" affordances

**Do NOT mirror** (direction is intrinsic, not reading-relative):
- Logos and brand marks
- Media playback controls (play ▶ still points "forward in time", not in reading direction)
- Clocks, musical notation, and most diagrams
- Numbers themselves (digits are written left-to-right even within RTL text)
- Checkmarks, and icons of real-world objects whose orientation is fixed

```css
/* Mirror a directional icon only */
[dir="rtl"] .icon-chevron { transform: scaleX(-1); }
/* Logo and play button: leave alone */
```

### What a mirror actually looks like

```
LTR (English)                         RTL (Arabic)
┌───────────────────────────┐         ┌───────────────────────────┐
│ [Logo]  Home  About   [☰] │         │ [☰]   About  Home  [Logo] │
├───────────────────────────┤         ├───────────────────────────┤
│ ‹ Back        Title       │         │           Title    Back › │
│                           │         │                           │
│ • List item               │         │               List item • │
│   [Avatar] Name           │         │           Name [Avatar]   │
│                  [Next ›]  │         │  [‹ Next]                 │
└───────────────────────────┘         └───────────────────────────┘
   ▶ 0:12 ──────●──── 3:45              ▶ 0:12 ──────●──── 3:45
   (media controls do NOT mirror — time still flows left→right)
```

Note: the nav, alignment, list bullets, avatars, and the Back/Next chevrons all
flip; the logo and the media scrubber do not.

---

## Text Expansion & Contraction

Translated text changes length. UI laid out tightly around English will overflow,
truncate, or wrap badly. German, Finnish, and Russian commonly run **30–40% longer**
than English; short strings can expand far more.

### IBM's rule of thumb for expansion

| English length | Expect up to |
|----------------|-------------|
| ≤ 10 chars | +100–200% |
| 11–20 chars | +80–100% |
| 21–30 chars | +60–80% |
| 31–50 chars | +40% |
| > 50 chars | +30% |

### Design for it

- **No fixed-width text containers.** Let buttons, tabs, labels, and badges grow.
- **Avoid truncation on essential UI.** A clipped menu item is a broken menu item.
- **Test with pseudo-localization** early: replace `Settings` with
  `[Ŝéttîng§ ──────]` to surface overflow and hard-coded strings before real
  translation exists.
- **CJK contracts**—Chinese/Japanese/Korean are often *shorter and taller*; don't
  assume single-line height either.

### Never concatenate translated fragments

Word order differs across languages, so string-gluing produces nonsense.

```js
// ❌ Grammatically broken in most languages
const msg = "You have " + count + " new " + itemType + " messages";

// ✅ One translatable message with named placeholders + ICU plurals
t('inbox.summary', { count, itemType });
// en: "{count, plural, one {# new message} other {# new messages}}"
// de: "{count, plural, one {# neue Nachricht} other {# neue Nachrichten}}"
```

---

## Pluralization & Gender

English has two plural forms (1 / many). Many languages have more—Arabic has **six**
CLDR plural categories (zero, one, two, few, many, other); Polish and Russian have
distinct "few" vs. "many" forms. The naive `count + "s"` is wrong almost everywhere.

Use **ICU MessageFormat** (backed by CLDR plural rules), supported by `i18next`,
`react-intl`/FormatJS, `Intl.PluralRules`, and most modern libraries.

```
{count, plural,
  =0    {No items}
  one   {# item}
  few   {# items}
  many  {# items}
  other {# items}
}
```

> English resolves only to `one`/`other`; `few`/`many` (and `=0`) are listed here
> for the languages that need them (Polish, Russian, Arabic…). A locale picks the
> matching category automatically.

```js
// Pick the right category programmatically when needed
new Intl.PluralRules('pl').select(2); // → "few"
new Intl.PluralRules('en').select(2); // → "other"
```

**Gender & grammatical agreement:** adjectives, articles, and past tense can change
with the gender of a noun or the user. Use ICU `select` rather than building
sentences from parts, and avoid embedding the user's name mid-sentence where
grammar would need to agree with it.

```
{gender, select,
  female {She updated her profile}
  male   {He updated his profile}
  other  {They updated their profile}
}
```

---

## Locale-Aware Formatting

Dates, numbers, currency, and units are **locale data**, not strings. Use the
built-in `Intl` APIs (or platform equivalents) instead of hand-rolling formats.

```js
// Dates — never assume MM/DD/YYYY (that's US-only)
new Intl.DateTimeFormat('en-US').format(date); // 3/13/2026 (M/D)
new Intl.DateTimeFormat('en-GB').format(date); // 13/03/2026 (D/M)
new Intl.DateTimeFormat('ja-JP').format(date); // 2026/3/13
new Intl.DateTimeFormat('ar-EG').format(date); // ١٣‏/٣‏/٢٠٢٦

// Numbers — decimal/grouping separators vary
new Intl.NumberFormat('de-DE').format(1234567.89); // "1.234.567,89"
new Intl.NumberFormat('en-US').format(1234567.89); // "1,234,567.89"

// Currency — symbol, placement, and spacing are locale-specific
new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' })
  .format(99.5); // "99,50 €"

// Units, relative time, lists
new Intl.NumberFormat('en', { style: 'unit', unit: 'kilometer' }).format(5);
new Intl.RelativeTimeFormat('en').format(-1, 'day'); // "1 day ago"
new Intl.ListFormat('en').format(['a','b','c']); // "a, b, and c"
```

### Beyond format strings

| Concern | Watch out for |
|---------|---------------|
| **Name order** | Many cultures put family name first (China, Japan, Korea, Hungary). Don't label fields "First / Last"—use "Given / Family" and don't force a split. |
| **Address format** | Field order, postal-code position, and required fields differ; some countries have no postal codes or states. Use a flexible/freeform model. |
| **Calendars & weeks** | Week may start Sunday, Monday, or Saturday; non-Gregorian calendars exist (Islamic, Hebrew, Japanese eras). |
| **Time zones** | Store UTC, display in the user's zone; show the zone for events. |
| **Phone numbers** | Vary in length and grouping; validate per-region (libphonenumber), not with one regex. |
| **Measurement units** | Metric vs. imperial; convert, don't just relabel. |

### Forms that survive every locale

```
❌ Locale-blind form           ✅ Locale-flexible form
─────────────────────          ──────────────────────────────────
First name [______]            Given name(s)  [__________]
Last name  [______]            Family name    [__________]
                               (don't require a split; allow one
State      [__▼]               full-name field for cultures that
ZIP        [_____]             don't separate them)

                               Country        [__▼]   ← drives the rest
                               Address        [__________]
                               (reveal region/postal fields based on
                                country; some have neither)
```

- Drive address fields from the selected **country**, not a fixed US template.
- Don't mark a postal code or "state/province" as required globally—many places
  have neither.
- Validate phone numbers per region; store names as entered (don't force casing or
  ASCII—accept Unicode, including non-Latin scripts).

---

## Translation-Friendly UI

The UI must give translators what they need and tolerate what they produce.

- **No text baked into images.** Text in raster images can't be translated, scaled,
  or read by screen readers. Use real text over CSS, or SVG with translatable `<text>`.
- **Externalize every string.** No hard-coded user-facing text in components.
  Reference keys (`t('checkout.payNow')`), not English literals scattered in code.
- **Provide context for translators.** A key named `submit` is ambiguous—"submit a
  form" vs. "submit to authority" translate differently. Add descriptions/comments
  and, ideally, screenshots so translators see where the string appears.
- **Allow for missing translations.** New strings ship before translations land—fall
  back gracefully to a base locale, never to a blank or a raw key like
  `checkout.payNow` shown to the user.
- **Avoid idioms, humor, and culture-bound metaphors** ("hit it out of the park",
  "piece of cake")—they don't translate and waste translator effort.
- **Leave room in the layout** (see Text Expansion) and avoid embedding UI controls
  mid-sentence, which forces translators to break grammar around them.
- **Colors, icons, and imagery carry cultural meaning.** Red = danger/luck/celebration
  depending on region; a mailbox or trash-can icon may not be universally recognized.
  Prefer well-established universal icons and don't rely on one alone.

---

## Language Switching UX

- **List languages in their own name (endonyms):** "Deutsch", "Français", "日本語",
  "العربية"—not "German", "French", "Japanese", "Arabic". A user who needs another
  language can't necessarily read the current one.
- **Don't use flags to represent languages.** Languages ≠ countries: one flag can't
  represent Spanish (20+ countries) and one country may have many languages. Flags
  are also politically loaded. Use language names.
- **Detection vs. explicit choice:** you may default from `Accept-Language`/device
  locale, but always offer an explicit, easy-to-find switch and **persist** the
  user's choice (per account and/or `localStorage`/cookie). Never trap users in a
  language they didn't pick.
- **Reflect the choice in everything:** `lang`/`dir` attributes, formatting, and the
  URL/route where relevant (good for SEO: `/de/`, `hreflang` tags).
- Put the switcher somewhere conventional (header or footer) and reachable without
  understanding the current language—an icon + endonym works well.

---

## Quick Checklist

- [ ] All user-facing strings externalized (no hard-coded text)
- [ ] Logical CSS properties; layout verified in `dir="rtl"`
- [ ] Directional icons mirror; logos/media/numerals do not
- [ ] Containers tolerate 30–40%+ text expansion; no fixed-width labels/buttons
- [ ] ICU MessageFormat for plurals/gender (not `count + "s"`)
- [ ] Dates, numbers, currency, units via `Intl` / locale data
- [ ] No text baked into images
- [ ] Translator context (descriptions/screenshots) provided
- [ ] Graceful fallback for missing translations (never raw keys)
- [ ] Language switcher uses endonyms, not flags; choice persists
- [ ] Pseudo-localization run in CI to catch overflow and hard-coded strings

---

## Common Mistakes

1. **Hard-coded strings** — English literals in components; impossible to translate.
2. **Assuming LTR** — physical CSS, manual `left`/`right` everywhere; RTL breaks.
3. **Flags as languages** — wrong, ambiguous, and politically fraught.
4. **Fixed-width text containers** — translated text overflows or truncates.
5. **Concatenating fragments** — string-gluing ignores word order and grammar.
6. **English plural rules** — `count + "s"` fails in most languages.
7. **Text in images** — untranslatable, inaccessible, doesn't scale.
8. **Hard-coded date/number formats** — `MM/DD/YYYY` and `,`/`.` are locale-specific.
9. **"First name / Last name" assumptions** — name order and structure vary widely.
10. **No translation fallback** — users see blank UI or raw keys for new strings.
11. **Idioms and humor** — don't survive translation; confuse translators.
12. **No translator context** — ambiguous keys produce wrong translations.

---

## Sources

- [W3C Internationalization (i18n) Activity](https://www.w3.org/International/) — specs and best practices
- [MDN: CSS Logical Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values)
- [MDN: Intl object](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)
- [Unicode CLDR](https://cldr.unicode.org/) — locale data and plural rules
- [ICU MessageFormat](https://unicode-org.github.io/icu/userguide/format_parse/messages/) — plurals, gender, formatting
- [Material Design: Bidirectionality](https://m2.material.io/design/usability/bidirectionality.html)
- [Nielsen Norman Group: Translation & localization](https://www.nngroup.com/topic/international-users/)
- [Smashing Magazine: RTL Styling 101](https://www.smashingmagazine.com/2017/11/right-to-left-mobile-design/)
