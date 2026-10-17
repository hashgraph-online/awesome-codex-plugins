---
name: factor-of-safety-content-stress
description: 'Use this skill when designing UI to survive content extremes — long names, big numbers, multi-line addresses, missing images, internationalized strings, dense data. Trigger when reviewing a design against worst-case content, when bug reports show layouts breaking on real data, or when picking content limits and validation rules. Sub-aspect of `factor-of-safety`; read that first.'
---

# Designing for content stress

Most designs are tested against ideal sample data: typical-length names, round numbers, well-cropped images, English. Real data is messier. Names span 1 to 100+ characters; numbers span tiny to enormous; images are missing, oversize, or wrong aspect; translations stretch UI strings 30%+. A design that handles only the typical breaks routinely on real users.

## Common content-stress vectors

### Name and identifier length

- **English names**: typically 5–20 characters. Outliers: hyphenated, multi-word, titled — up to 60+.
- **Other-script names**: Chinese names typically 2–4 characters; Spanish names with multiple surnames can exceed 50; Tamil names can be very long.
- **Email addresses**: typically 15–35 characters. RFC max: 254.
- **Account IDs / hashes**: 6–40 characters; users often need to read or copy them.

Design for the worst plausible case; truncate gracefully with tooltips for very long values.

### Numeric magnitudes

- **Currency**: $0.01 to $999,999,999.99 — 13 visible characters at full extreme.
- **Counts**: 1 to billions; consider abbreviation ("12.4M") for compact display.
- **Percentages**: -100% to 100% (or beyond for compounded growth).
- **Time durations**: seconds to years; consider unit-switching display.

A column sized for "$5,000.00" breaks for "$1,234,567.89." Size for the worst case or use abbreviated formats.

### Image content

- **Missing**: image fails to load. Show a placeholder, not broken-image icon.
- **Wrong aspect**: image doesn't match expected ratio. Crop, fit, or letterbox; choose deliberately.
- **Oversize**: image is 4MB. Lazy-load, downsample, or progressively load.
- **Mid-load**: brief moment with no image. Show skeleton or low-res preview.

### Internationalization

- **String length**: German strings are typically 30% longer than English; Russian and French similar; Chinese often 30% shorter.
- **Bidirectional**: Arabic and Hebrew run right-to-left; mixed LTR/RTL content has its own complexities.
- **Date / number format**: vary widely (covered in `chunking-numeric-and-otp`).
- **Pluralization**: English has 2 forms (cat, cats); other languages have up to 6 (Polish, Russian, Welsh).

Design with stretch room; test in worst-case languages (German for length, Arabic for direction).

### Empty states

- **Zero rows in a table**: don't show an empty grid; show an explanation.
- **Zero items in a list**: show an empty state with guidance.
- **First-run state**: no data yet; show onboarding.

Empty states are often forgotten until QA. Design them deliberately.

### Long-tail of edge cases

- **Single character of content**: a one-character name or message.
- **Whitespace-only content**: validate; reject or strip.
- **Special characters**: Unicode emojis, combining characters, RTL marks; test rendering.
- **HTML / SQL injection in user content**: sanitize at render time.

## Worked examples

### Example 1: a card layout that absorbs content variation

```html
<article class="user-card">
  <div class="avatar">
    <img src={avatarUrl} alt="" onerror="this.style.display='none'" />
    <span class="avatar-fallback">{initials}</span>
  </div>
  <div class="user-info">
    <h3 class="name">{name}</h3>
    <p class="role">{role}</p>
    <p class="email">{email}</p>
  </div>
</article>

<style>
  .user-card {
    display: grid;
    grid-template-columns: 48px 1fr;
    gap: 12px;
    padding: 16px;
    min-height: 80px;       /* margin for multi-line names */
  }
  .avatar { position: relative; width: 48px; height: 48px; }
  .avatar img { width: 100%; height: 100%; object-fit: cover; }
  .avatar-fallback { /* shown when image fails */ }
  .user-info { min-width: 0; }   /* allows truncation */
  .name {
    overflow-wrap: break-word;
    hyphens: auto;
  }
  .email {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: hsl(0 0% 45%);
  }
</style>
```

The card handles:
- Missing avatar (falls back to initials).
- Long name (wraps to 2–3 lines; card grows).
- Long email (truncates with ellipsis; full visible on hover).
- Empty role (just doesn't render).

### Example 2: a numeric column sized for the worst case

```html
<td class="amount">{currency(amount)}</td>

<style>
  .amount {
    text-align: right;
    font-variant-numeric: tabular-nums;
    width: 12ch;          /* fits "$9,999,999.99" */
  }
</style>
```

The column width accommodates the maximum-realistic value. Smaller values right-align within it.

### Example 3: handling translation stretch

```html
<button class="cta">{t('signup.cta')}</button>

<style>
  .cta {
    min-width: 120px;
    padding: 12px 24px;
    white-space: nowrap;     /* don't wrap; let it grow horizontally */
  }
  /* On narrow screens, allow wrap */
  @media (max-width: 600px) {
    .cta { white-space: normal; }
  }
</style>
```

The button accommodates German "Kostenlos anmelden" (longer than "Sign up free") without breaking the layout.

### Example 4: empty state for a list

```html
{items.length > 0
  ? <ItemList items={items} />
  : <Empty
      icon={<InboxIcon />}
      title="Your inbox is empty"
      description="When messages arrive, they'll appear here."
      action={<Button>Compose new message</Button>}
    />
}
```

Designed deliberately, not just "the list happens to be empty."

## Anti-patterns

- **Sample data only.** Designing with "John Smith" and "$50.00." Real users break the layout.
- **Fixed widths sized for typical.** A 200px name field that truncates 30% of users.
- **No empty state.** A blank table with no explanation.
- **No loading state.** A blank screen while data fetches.
- **No error state.** A blank screen when data fetch fails.
- **Translation testing only at release.** Translations expanded the UI; many surfaces need rework.
- **Over-truncation.** Names truncated to 8 characters because "they look messy otherwise." Users can't identify themselves.

## Heuristics

1. **The "stress test page" approach.** Build a page that renders every component with maximum-length and minimum-length content. Screenshot regularly; fix what breaks.
2. **The "real data" check.** Pull real samples (anonymized) from production and render them in the design. Most layouts surprise.
3. **The "longest plausible content" estimate.** For each text field, ask: what's the worst case? Design for that.
4. **The translation audit.** Render in German (long) and Arabic (RTL). What broke?

## Related sub-skills

- **`factor-of-safety`** (parent).
- **`factor-of-safety-failure-margin`** — capacity and dependency margins.
- **`chunking-numeric-and-otp`** — numeric formatting decisions.
- **`accessibility-perceivable`** — content stress is also accessibility (long content for low-vision; missing images for blind users).
