---
name: accessibility-understandable
description: 'Use this skill when the question is whether users can *understand* the UI — predict its behavior, recover from errors, comprehend its labels and copy. Trigger when writing form labels and error messages, when designing flows with surprising state changes, when picking microcopy for the destructive moments, or when reviewing a UI that "works correctly but confuses people." Covers WCAG Principle 3 (Understandable). Sub-aspect of `accessibility`; read that first if you haven''t already.'
---

# Accessibility — Understandable

WCAG Principle 3: information and the operation of the user interface must be understandable.

The three sub-criteria, simplified:

1. **Readable** — language is identified, jargon is explained, abbreviations are expanded.
2. **Predictable** — the UI behaves consistently and changes context only when the user expects.
3. **Input assistance** — labels, instructions, error messages, and prevention of mistakes.

This sub-principle is where accessibility most overlaps with general usability — but the consequences fall hardest on users with cognitive impairments, learning disabilities, low literacy, or unfamiliarity with the language.

## 1. Readable

### Language identified

Set the document language so screen readers pronounce correctly:

```html
<html lang="en">
```

For mixed-language content, mark the exception:

```html
<p>The French word for "dog" is <span lang="fr">chien</span>.</p>
```

A screen reader switches voice/pronunciation for the marked span.

### Plain language

Write at a reading level appropriate to your audience. For consumer products, that's typically grade 8 or below. Tools (Hemingway Editor, Readable, Microsoft Word's readability stats) measure this.

Practices that improve readability:

- Short sentences (<25 words).
- Active voice ("Click Save" not "Save can be clicked").
- Familiar words (use "buy" not "procure").
- One idea per sentence.
- Paragraphs ≤ 5 sentences.

### Jargon and abbreviations

If you must use jargon or abbreviations, expand them on first use:

```html
<p>
  Single sign-on (<abbr title="Single Sign-On">SSO</abbr>) lets your team
  use one login across all tools.
</p>
```

Screen readers can announce the expansion via `<abbr title>`. Sighted users see the expansion on hover.

For specialized terms, link to a definition or glossary the first time.

### Pronunciation (rare but worth knowing)

For content where pronunciation determines meaning (poetry, languages, certain proper nouns), provide pronunciation hints. Most apps don't need this; mention it for completeness.

## 2. Predictable

### Behavior on focus and input

WCAG 3.2.1 and 3.2.2: changing the value of an input or moving focus to an element should NOT trigger an unexpected context change.

Specifically:

- A `<select>` should not auto-submit a form when a value changes.
- Focusing an input should not open a popup or navigate.
- Typing into a search field should not navigate to a result page on every keystroke.

If a context change *is* the intended behavior (typeahead search, live filter), make it expected: label the field as "Search (results filter as you type)," show results below the input, don't yank focus.

```html
<!-- Wrong: select auto-submits on change -->
<select onchange="this.form.submit()">
  <option>Country A</option>
  <option>Country B</option>
</select>

<!-- Right: select waits for explicit submit -->
<select name="country">
  <option>Country A</option>
  <option>Country B</option>
</select>
<button type="submit">Continue</button>
```

### Consistent navigation

Same navigation in the same place across pages. The "Help" link in the top-right on page A is in the top-right on page B too. Users (especially those with cognitive impairments or who navigate by spatial memory) rely on this.

If a sub-section needs additional nav, place it in a consistent location (e.g., a left sidebar that always appears in left-sidebar slot).

### Consistent identification

Same component does the same thing across the app. A button labeled "Save" always saves; doesn't sometimes mean "save and close" and sometimes mean "save and continue." If two different actions are needed, two different labels: "Save" and "Save and continue."

Same icon across the app should mean the same thing. A trash icon on one page meaning "delete," another page meaning "filter," is incoherent.

## 3. Input assistance

### Error identification

WCAG 3.3.1: when an error is detected, identify the item in error and describe the error in text.

```html
<div class="field" data-state="error">
  <label for="email">Email address</label>
  <input id="email"
         type="email"
         aria-invalid="true"
         aria-describedby="email-error" />
  <p id="email-error" class="field-error">
    <AlertIcon aria-hidden="true" />
    Please enter a valid email address (e.g., name@example.com).
  </p>
</div>
```

Three things are happening:

- `aria-invalid="true"` flags the input as in error (assistive tech may announce).
- `aria-describedby` ties the message to the input (screen readers announce both).
- The message text is specific (says what's wrong) and actionable (offers an example).

### Labels and instructions

Every input has a programmatically associated label. The label is descriptive (not just "Field 1"). If the input requires specific format, instructions are provided alongside.

```html
<!-- Right: label, format hint, and example -->
<div class="field">
  <label for="phone">Phone number</label>
  <input id="phone"
         type="tel"
         aria-describedby="phone-help"
         placeholder="555-123-4567" />
  <p id="phone-help" class="field-help">
    Format: 555-123-4567. We use this only for delivery questions.
  </p>
</div>
```

Notes:

- `placeholder` is *not* a label — it disappears when the user starts typing. Use a real `<label>`.
- Format hints belong in adjacent text (`aria-describedby`), not just placeholder.
- Required fields should be marked both visually (asterisk) and programmatically (`required` attribute or `aria-required`).

### Error suggestion

WCAG 3.3.3 (Level AA): when the user makes an input error and the system can suggest a correction, do so.

```html
<!-- User typed "gmial.com" -->
<p class="field-error">
  Did you mean <button type="button" onclick="acceptSuggestion('gmail.com')">name@gmail.com</button>?
</p>
```

Don't auto-correct silently — that's a context change without consent. Suggest, let the user accept.

### Error prevention

WCAG 3.3.4 (Level AA, for legal/financial/data submissions): the user must be able to:

- **Reverse** the submission (a "Cancel my order" period), OR
- **Check** the submission for errors before final commit (a confirmation page), OR
- **Confirm** explicitly before final commit (a confirm dialog).

For destructive irreversible actions in product UIs (delete account, transfer ownership), this is the strong reason for `AlertDialog` confirmation, type-to-confirm patterns, and 30-day "soft delete" recovery windows.

### Help

WCAG 3.3.5 (Level AAA): context-sensitive help is available. Tooltips, inline help, "What's this?" links.

In product UIs, this lands in:

- `<FieldDescription>` next to inputs that need explanation.
- `?` icons next to settings whose function isn't obvious.
- A persistent help link or chat in chrome.

### Consistent help

WCAG 3.2.6 (Level A, 2.2): if help mechanisms are present (contact info, FAQ link, chat widget), they appear in the same location across pages.

## Worked examples

### Example 1: a credit-card form with full input assistance

```html
<form>
  <div class="field">
    <label for="cc-number">Card number</label>
    <input id="cc-number"
           type="text"
           inputmode="numeric"
           autocomplete="cc-number"
           aria-describedby="cc-help"
           required
           aria-required="true" />
    <p id="cc-help" class="field-help">
      16 digits, no spaces or dashes
    </p>
  </div>

  <div class="field">
    <label for="cc-exp">Expiration (MM/YY)</label>
    <input id="cc-exp"
           type="text"
           inputmode="numeric"
           autocomplete="cc-exp"
           placeholder="MM/YY"
           required
           aria-required="true" />
  </div>

  <div class="field">
    <label for="cc-cvc">CVC</label>
    <input id="cc-cvc"
           type="text"
           inputmode="numeric"
           autocomplete="cc-csc"
           aria-describedby="cvc-help"
           required
           aria-required="true" />
    <p id="cvc-help" class="field-help">
      3-digit code on the back of your card (4 on Amex)
    </p>
  </div>

  <button type="submit">Review order</button>
</form>
```

What's happening:

- Each field has a real label (associated via `for`/`id`).
- `inputmode="numeric"` prompts the right keyboard on mobile.
- `autocomplete` attributes let password managers and autofill help.
- Help text is associated via `aria-describedby`.
- Required is both visual (probably an asterisk from CSS) and programmatic (`required` + `aria-required`).
- Submit goes to a "Review order" page (error prevention via review step).

### Example 2: a destructive action with prevention layers

```html
<button onclick="openDeleteDialog()">Delete account</button>

<!-- Dialog: -->
<dialog open
        role="dialog"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-desc">
  <h2 id="confirm-title">Delete your account?</h2>
  <p id="confirm-desc">
    This permanently removes your account, all your projects (12), and your
    team's access (38 members). This cannot be undone.
  </p>
  <p>To confirm, type your account email below:</p>
  <input type="text" placeholder="you@example.com" id="confirm-input" />
  <button type="button">Cancel</button>
  <button type="button"
          class="destructive"
          disabled
          id="confirm-button">
    Delete account permanently
  </button>
</dialog>
```

The user must:

1. Click "Delete account" (intent).
2. Read the dialog (consequences laid out).
3. Type their email (active confirmation, error prevention).
4. Click "Delete account permanently" (final commit).

Each step is a deliberate barrier against accidental destruction.

## Anti-patterns

- **Placeholders as labels.** "Email" in placeholder text only — disappears on type, breaks for screen readers, fails on autofill.
- **Generic error messages.** "Validation failed." Doesn't say which field, doesn't say what's wrong, doesn't say how to fix.
- **Surprise context changes.** Selecting an option auto-navigates; typing in a field auto-submits. The user loses control.
- **Inconsistent labels for the same action.** "Save" here, "Submit" there, "Confirm" elsewhere.
- **No undo and no confirm for destructive actions.** Click-and-it's-gone with no recovery.
- **Jargon without explanation.** "API token rotation period" with no hover or link to explain. The technical user knows; the casual user is lost.

## Heuristics

1. **The five-error test.** Trigger 5 different validation errors. Are all of them named, located near the field, and offered a fix?
2. **The label audit.** Every form input has a `<label>` associated by `for`/`id`. No placeholder-as-label.
3. **The unexpected-change test.** Walk through a form. Does any change of input value or focus trigger a navigation, popup, or auto-submit? Each is a violation.
4. **The "stranger" test.** Show your form to someone unfamiliar with your product. Can they tell what each field wants without help text? If not, label or instruction is wrong.
5. **The grade-level check.** Run your microcopy through a readability tool. Above grade 10 for consumer? Simplify.

## Related skills

- **`accessibility`** (parent).
- **`accessibility-perceivable`**, **`accessibility-operable`**, **`accessibility-robust`** — siblings.
- **`errors`** and **`forgiveness`** (interaction) — error UX is shared between accessibility and general interaction design.
- **`feedback-loop`** (interaction) — feedback that the system received a change is part of predictability.
- **`framing`** (cognition) — error copy framing affects whether the user feels blamed or helped.
- **`mental-model`** (cognition) — predictable behavior aligns with the user's model.
