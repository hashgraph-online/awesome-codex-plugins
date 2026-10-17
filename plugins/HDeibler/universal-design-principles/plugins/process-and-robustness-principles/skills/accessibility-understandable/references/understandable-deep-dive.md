# Understandable: standards and edge cases

A reference complementing `accessibility-understandable` SKILL.md with deeper detail on the WCAG 3.* criteria and harder cases.

## WCAG 3.* criteria summary

The Understandable principle has three guidelines.

### 3.1 Readable

- **3.1.1 Language of Page (A)** — `<html lang="...">`.
- **3.1.2 Language of Parts (AA)** — language changes within a page marked.
- **3.1.5 Reading Level (AAA)** — content at lower-secondary reading level or alternative provided.

### 3.2 Predictable

- **3.2.1 On Focus (A)** — receiving focus does not initiate context change.
- **3.2.2 On Input (A)** — changing input value does not initiate context change.
- **3.2.3 Consistent Navigation (AA)** — navigation in same order across pages.
- **3.2.4 Consistent Identification (AA)** — same components identified consistently.
- **3.2.6 Consistent Help (A, 2.2)** — help mechanisms in same location across pages.

### 3.3 Input assistance

- **3.3.1 Error Identification (A)** — errors identified in text, near the field.
- **3.3.2 Labels or Instructions (A)** — labels or instructions provided for user input.
- **3.3.3 Error Suggestion (AA)** — when system can suggest a correction, do so.
- **3.3.4 Error Prevention (AA)** — for legal/financial/data submissions: reversible, checkable, or confirmed.
- **3.3.7 Redundant Entry (A, 2.2)** — information user has already entered isn't asked again in the same session.
- **3.3.8 Accessible Authentication (Minimum) (AA, 2.2)** — authentication doesn't depend on cognitive function tests (memory, transcription, math) without alternative.

## Hard cases

### Cognitive accessibility

WCAG covers cognitive accessibility less comprehensively than visual or motor. Useful supplementary practices:

- **Use plain language.** Aim for grade 8 or below for general consumer content.
- **Front-load important information.** "Inverted pyramid" structure.
- **Provide summaries** of long content.
- **Use icons + text** for non-textual signals.
- **Avoid jargon, idioms, abbreviations** without expansion.
- **Predictable layout.** Same things in the same places.
- **Forgiving interactions.** Undo, soft-delete, recovery from mistakes.

The COGA (Cognitive and Learning Disabilities Accessibility Task Force) at W3C publishes more detailed guidance for cognitive accessibility.

### Authentication

WCAG 3.3.8 (added in 2.2) addresses a long-standing accessibility issue: many authentication mechanisms require cognitive function tests (remember a password, transcribe a code from email/SMS, solve CAPTCHA). These exclude users with cognitive impairments.

Acceptable alternatives:

- Password manager support (proper autocomplete attributes).
- WebAuthn / passkeys.
- Biometric authentication.
- Hardware tokens.
- Magic links (with care — they require email transcription if not click-through).

Avoid: forced password complexity that requires user-generated mnemonic strategies; CAPTCHAs without alternative challenges; SMS codes that must be typed out.

### Form labels and instructions

WCAG 3.3.2 requires labels or instructions, but the *quality* of labels is largely uncovered by formal criteria. Best practices:

- **Programmatically associate** every input with a label (`<label for="id">` or `aria-labelledby`).
- **Visible labels** preferred over placeholder-only.
- **Format expectations** stated near the field ("Phone: format 555-123-4567").
- **Required marking** uses both visual asterisk and `required`/`aria-required`.

### Error copy

Error messages should be:

- **Located** with the field they reference (`aria-describedby`).
- **Specific** — say what's wrong, not just "invalid."
- **Actionable** — say how to fix.
- **Non-blaming** — frame as system limitation or user-action prompt, not user fault.

Examples:

- ❌ "Email is invalid."
- ✅ "Please enter an email like name@example.com."

### Predictability and surprise

WCAG 3.2.1 and 3.2.2 prohibit context changes from focus or input change. Examples of violations:

- Selecting a radio button auto-submits the form.
- Tabbing into an input opens a popover.
- Typing in a search field navigates to a results page on every keystroke.

If context change *is* the desired behavior, label it ("Search results update as you type") and don't move focus.

## Closing

Understandable accessibility is the most usability-overlapping sub-principle — many of its requirements are good design generally. The accessibility framing makes them obligatory rather than nice-to-have, which is often what gets them prioritized.
