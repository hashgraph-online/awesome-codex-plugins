---
title: Forms and Errors
impact: HIGH
tags: labels, validation, errors, autocomplete, authentication, captcha
wcag: 1.3.1, 1.3.5, 3.3.1, 3.3.2, 3.3.3, 3.3.7, 3.3.8
---

**Rule**: Every input has a visible, programmatically associated label; errors are identified in text, next to the field, with how to fix them; and nothing in a form depends on memory, puzzles, or retyping.

**Why**: Forms are where inaccessible products lose people completely — a screen reader user who cannot tell which field is which, or a user with a cognitive disability blocked by a puzzle at sign-in, cannot finish. WCAG requires labels or instructions (3.3.2), errors identified in text (3.3.1) with suggestions (3.3.3), input purpose declared (1.3.5), and — new in WCAG 2.2 — no re-entering information already given (3.3.7, level A) and sign-in that doesn't require a cognitive function test such as remembering or transcribing a password without help (3.3.8, level AA).

### When Building

- **Visible labels**, associated in code — `<label for>` on the web, the platform's labelled text field components on mobile. Placeholder text is not a label
- **Instructions before the field** — required fields, format, and constraints stated up front, not only after an error
- **Errors**: say what is wrong and how to fix it, next to the field, announced to screen readers (`aria-describedby` + `aria-invalid` on the web; platform guides for native); keep what the user typed; on submit, move focus to the first error or an error summary
- **Declare input purpose** — `autocomplete` on the web, content types and autofill hints on native — so browsers, password managers, and assistive tech can fill fields
- **No redundant entry** — reuse what the user already entered in the same process (shipping → billing address), or let them select it
- **Accessible sign-in** — allow paste and password managers; offer passkeys, magic links, or sign in with Apple/Google; no CAPTCHA that is the only way through (offer an alternative)
- **Group related controls** — radio groups and checkbox groups have a group label (`fieldset`/`legend` on the web)

### When Auditing

- Inputs with placeholder-only labels, or labels not associated with the input
- Errors shown only by colour, only at the top of the page, or not announced
- `onPaste` prevention on password or code fields
- Image or puzzle CAPTCHA with no alternative
- Multi-step flows asking for the same information twice

### Incorrect

```tsx
<input placeholder="Email" className={error ? "border-red" : ""} />
```

### Correct

```tsx
<label htmlFor="email">Email</label>
<input id="email" type="email" autoComplete="email"
  aria-invalid={!!error} aria-describedby={error ? "email-error" : undefined} />
{error && <p id="email-error">Enter an email address like name@example.com</p>}
```

### Alternatives

Re-entering is acceptable where it is essential — confirming a new password, or security re-authentication — as long as paste and password managers still work.
