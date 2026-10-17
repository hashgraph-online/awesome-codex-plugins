---
name: chunking-numeric-and-otp
description: 'Use this skill when designing inputs or displays for numeric strings — phone numbers, OTP / verification codes, credit card numbers, account IDs, license keys, currency, dates, social security numbers. Trigger when picking a format for displaying numbers, designing OTP entry UIs, or formatting identifiers in tables and receipts. Sub-aspect of `chunking`; read that first.'
---

# Chunking applied to numeric strings

Numbers are the canonical chunking case. A 10-digit phone number, a 16-digit credit card, a 6-digit OTP — without chunking, these are working-memory overloads. With chunking, they're manageable.

## Standard chunkings

Conventions that have evolved across industries:

| Type | Standard chunking | Example |
|---|---|---|
| US phone | 3-3-4 | 555-867-5309 |
| International phone | varies; usually 2-3-3-2 or similar | +44 20 7946 0958 |
| Credit card | 4-4-4-4 (most) or 4-6-5 (Amex) | 4242 4242 4242 4242 |
| Social Security (US) | 3-2-4 | 123-45-6789 |
| OTP / verification | 3-3 (6-digit) or 4-4 (8-digit) | 123-456 |
| Bank account (US) | varies; often grouped with type | 110000000 → routing display |
| ISBN | 1-3-3-5-1 (ISBN-13) | 978-3-16-148410-0 |
| IP address | 4 octets separated by dots | 192.168.1.1 |
| Date (ISO) | 4-2-2 | 2026-05-02 |
| Currency | 3-digit groups | $1,234,567.89 |

When in doubt, follow the convention. Users have already learned it.

## OTP / verification code entry

The most common modern chunking case in product UI. A 6-digit code from email or SMS, entered into a verification field.

### Single field vs. chunked fields

Single field:
```html
<input type="text" inputmode="numeric" maxlength="6" pattern="\d{6}" />
```

Chunked fields (one per digit):
```html
<div class="otp-input" role="group" aria-label="Verification code">
  <input type="text" inputmode="numeric" maxlength="1" autocomplete="one-time-code" />
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
  <span class="separator" aria-hidden>—</span>
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
  <input type="text" inputmode="numeric" maxlength="1" />
</div>
```

The chunked version:

- Visually matches how the code is presented in email/SMS.
- Lets the user verify each digit's position mid-entry.
- Auto-advances focus on each digit (with JS).
- Supports paste-spread (paste into first input fills all).

The single-field version is simpler to implement and supports SMS-autofill on iOS via `autocomplete="one-time-code"`. Modern apps often offer both: a single field on mobile (where autofill is critical) and chunked on desktop.

### OTP UX details

- **Auto-advance** focus to the next digit on input.
- **Auto-back** focus to previous digit on backspace.
- **Paste support**: pasting a 6-digit string into the first input should distribute across all six.
- **`autocomplete="one-time-code"`** on at least one input enables iOS Messages autofill.
- **Numeric keyboard on mobile** via `inputmode="numeric"`.
- **Optional auto-submit** when the last digit is entered (debate: some users dislike auto-submit because it commits before they can verify).

## Phone number entry

Phone numbers vary widely by country. Patterns:

- **US-only forms**: enforce 3-3-4 with format mask or chunked inputs.
- **International forms**: use a country selector + a free-text number field; format on display rather than enforcing entry format.
- **Dual-purpose** (international users + US-heavy): use [libphonenumber](https://github.com/google/libphonenumber) or similar to validate and format dynamically.

```html
<label>
  Phone
  <div class="phone-input">
    <select name="country-code">
      <option value="+1">🇺🇸 +1</option>
      <option value="+44">🇬🇧 +44</option>
      <!-- ... -->
    </select>
    <input type="tel" name="phone" placeholder="555-867-5309" />
  </div>
</label>
```

## Credit card display

In production, never display full card numbers — show the last 4 digits chunked with masking:

```
**** **** **** 4242
```

For entry, use 4-4-4-4 chunking with auto-advance, paste support, and card-type detection:

```html
<input type="text" inputmode="numeric" autocomplete="cc-number"
       placeholder="1234 5678 9012 3456" />
```

Built-in browsers and password managers handle most of this if you use the right `autocomplete` value.

## Account IDs and identifiers

For internal IDs (account IDs, transaction IDs, session IDs):

- **Display chunked** if the user might read or transcribe them.
- **Display monospaced** so digits and letters align (`font-family: monospace; font-variant-numeric: tabular-nums;`).
- **Provide one-click copy** so users don't have to manually select.

```html
<div class="id-display">
  <span class="id-value">ws_8f3c-7a92-1b04</span>
  <button onclick="copyToClipboard('ws_8f3c-7a92-1b04')" aria-label="Copy">📋</button>
</div>
```

The chunking aids reading aloud (support calls) and verification.

## Currency

Currency should always use locale-appropriate digit grouping:

- US English: `$1,234,567.89` (3-digit groups, period decimal).
- European: `€1.234.567,89` (period grouping, comma decimal).
- Indian: `₹12,34,567.89` (mixed grouping: 2-2-3).

Use `Intl.NumberFormat` to get this right per locale:

```js
new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
  .format(1234567.89);
// "$1,234,567.89"
```

Numeric columns in tables should use `font-variant-numeric: tabular-nums` so digits align vertically.

## Anti-patterns

- **Continuous strings**: a 16-digit credit card with no chunking. Users can't verify.
- **Inconsistent chunk sizes within a context**: phone numbers shown as 3-4-3 here and 5-2-3 there. Each format is a re-learn.
- **Wrong locale grouping**: showing `1,234.56` to a German user (who reads it as 1,234.56 = roughly 1,234 plus 56/100 instead of 1234.56).
- **Missing `inputmode`**: a numeric field that opens the alphabet keyboard on mobile. Easy fix; commonly missed.
- **OTP with no auto-advance / paste support**: users tab manually between fields; if they paste, only the first field fills.
- **Unmasked credit card display**: privacy and security violation. Always mask all but the last 4.

## Heuristics

1. **The "read it aloud" test.** Try reading the chunked number aloud. If it requires re-grouping mentally, the chunking is wrong.
2. **The cross-locale check.** For currency and dates, test in at least 2–3 locales. Format mismatches are common.
3. **The clipboard / autofill check.** Does pasting the user's clipboard into your input work cleanly? Do password managers fill correctly?
4. **The mobile keyboard check.** Numeric inputs should produce numeric keyboards on mobile (`inputmode="numeric"`).

## Related sub-skills

- **`chunking`** (parent).
- **`chunking-form-grouping`** — chunking at the form-section level.
- **`legibility`** (perception) — tabular numerals for column alignment.
- **`accessibility-perceivable`** (process) — number formatting affects screen-reader pronunciation.
