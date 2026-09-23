# Forms & Input Design

Forms are often where users complete their goals—signing up, checking out, submitting data. Good form design directly impacts conversion rates and user satisfaction.

---

## Form Design Principles

### Key Statistics

- **81%** of users abandon forms after starting
- Reducing form fields by **20-60%** often loses no necessary data
- Multi-step forms can increase completion by **86%**

### Fundamental Principles

1. **Ask only what you need** - Every field is friction
2. **Group related fields** - Logical chunking
3. **One column is usually best** - Easier scanning
4. **Clear labels** - No placeholder-only labels
5. **Smart defaults** - Pre-fill when possible
6. **Progressive disclosure** - Show fields when relevant

---

## Labels and Placeholders

### Labels

```html
<!-- Always use labels (not just placeholders) -->
<div class="form-field">
  <label for="email">Email address</label>
  <input type="email" id="email" name="email" />
</div>

<!-- Label placement -->
<!-- Top-aligned: Best for long forms, mobile -->
<!-- Left-aligned: Good for short forms, scanning -->
<!-- Right-aligned: Avoid (harder to scan) -->
```

**Best Practices:**
- Position labels above inputs (top-aligned)
- Keep labels short and clear
- Don't end with colons (modern convention)
- Associate with `for` attribute

### Placeholders

```html
<!-- Use for hints, not labels -->
<input
  type="email"
  placeholder="you@example.com"
  aria-label="Email address"
/>

<!-- Never use as the only label -->
<!-- Disappears on focus, causing confusion -->
```

**Placeholder Guidelines:**
- Show example format, not label
- Use gray text (but not too light)
- Don't rely on it for critical info
- Disappears—users may forget what field is

---

## Input Types

### HTML5 Input Types

```html
<!-- Use appropriate types for mobile keyboards and validation -->
<input type="text" />       <!-- Default -->
<input type="email" />      <!-- Email keyboard -->
<input type="tel" />        <!-- Phone keyboard -->
<input type="number" />     <!-- Numeric keyboard -->
<input type="url" />        <!-- URL keyboard -->
<input type="password" />   <!-- Hidden characters -->
<input type="search" />     <!-- Search field -->
<input type="date" />       <!-- Date picker -->
<input type="time" />       <!-- Time picker -->
<input type="datetime-local" /> <!-- DateTime picker -->
```

### Input Attributes

```html
<input
  type="email"
  name="email"
  id="email"
  required                    <!-- Validation -->
  aria-required="true"        <!-- Accessibility -->
  autocomplete="email"        <!-- Autofill hint -->
  inputmode="email"          <!-- Keyboard hint -->
  pattern="[^@]+@[^@]+\.[^@]+" <!-- Custom validation -->
  placeholder="you@example.com"
/>
```

### Autocomplete Values

```html
<!-- Enable browser autofill -->
<input autocomplete="given-name" />    <!-- First name -->
<input autocomplete="family-name" />   <!-- Last name -->
<input autocomplete="email" />
<input autocomplete="tel" />
<input autocomplete="street-address" />
<input autocomplete="postal-code" />
<input autocomplete="cc-number" />     <!-- Credit card -->
<input autocomplete="new-password" />  <!-- For password creation -->
<input autocomplete="current-password" /> <!-- For login -->
```

---

## Validation

### Validation Timing

| Timing | Pros | Cons | Best For |
|--------|------|------|----------|
| On blur | Immediate feedback | Can feel aggressive | Most fields |
| On submit | Low friction | Delayed error discovery | Short forms |
| On input | Real-time | Annoying while typing | Password strength |
| Hybrid | Balanced | Complex to implement | Professional forms |

### Recommended Approach

```javascript
// Validate on blur (when user leaves field)
// Don't validate while typing
// Re-validate on correction

input.addEventListener('blur', validate);
input.addEventListener('input', () => {
  // Only clear errors while typing if previously invalid
  if (hasError) validate();
});
```

### Error Messages

```html
<!-- Good: Specific, actionable -->
<span class="error">
  Please enter a valid email address (e.g., name@example.com)
</span>

<!-- Bad: Vague, unhelpful -->
<span class="error">Invalid input</span>
```

**Error Message Guidelines:**
- Place near the field (below or inline)
- Use red color + icon (not color alone)
- Be specific about what's wrong
- Suggest how to fix
- Use human-friendly language
- Don't blame the user

### Visual Error Indicators

```css
.input-error {
  border-color: #dc3545;
  background-color: #fff8f8;
}

.error-message {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.error-message::before {
  content: "⚠️";
}
```

### Accessibility for Errors

```html
<div class="form-field">
  <label for="email">Email</label>
  <input
    type="email"
    id="email"
    aria-describedby="email-error"
    aria-invalid="true"
  />
  <span id="email-error" role="alert">
    Please enter a valid email address
  </span>
</div>
```

---

## Required Fields

### Marking Required Fields

```html
<!-- Visual indicator -->
<label for="name">
  Name <span class="required" aria-hidden="true">*</span>
  <span class="sr-only">(required)</span>
</label>

<!-- Alternative: Mark optional fields -->
<label for="phone">
  Phone <span class="optional">(optional)</span>
</label>
```

**Convention:**
- If most fields required: mark optional
- If most fields optional: mark required
- Use asterisk (*) for required
- Explain asterisk at form start

---

## Multi-Step Forms

### When to Use

- Long forms (7+ fields)
- Complex processes (checkout, applications)
- Collecting different types of info
- Reducing cognitive load

### Progress Indicator

```html
<nav aria-label="Form progress">
  <ol class="steps">
    <li class="completed" aria-current="false">
      <span class="step-number">1</span>
      <span class="step-label">Personal Info</span>
    </li>
    <li class="current" aria-current="step">
      <span class="step-number">2</span>
      <span class="step-label">Shipping</span>
    </li>
    <li class="upcoming" aria-current="false">
      <span class="step-number">3</span>
      <span class="step-label">Payment</span>
    </li>
  </ol>
</nav>
```

### Best Practices

- Show step count (Step 2 of 4)
- Allow going back to previous steps
- Save progress automatically
- Validate each step before proceeding
- Keep navigation visible
- Allow skipping optional sections

---

## Specific Field Patterns

### Password Fields

```html
<div class="password-field">
  <label for="password">Password</label>
  <div class="input-wrapper">
    <input
      type="password"
      id="password"
      autocomplete="new-password"
      minlength="8"
    />
    <button type="button" class="toggle-visibility">
      Show
    </button>
  </div>
  <div class="password-strength" aria-live="polite">
    <!-- Strength indicator -->
  </div>
  <ul class="password-requirements">
    <li>At least 8 characters</li>
    <li>One uppercase letter</li>
    <li>One number</li>
  </ul>
</div>
```

### Phone Numbers

```html
<input
  type="tel"
  inputmode="numeric"
  autocomplete="tel"
  placeholder="(555) 123-4567"
/>

<!-- Consider: -->
<!-- - Auto-format as user types -->
<!-- - Accept various formats -->
<!-- - Show expected format -->
```

### Credit Cards

```html
<input
  type="text"
  inputmode="numeric"
  autocomplete="cc-number"
  pattern="[\d ]{13,19}"
  placeholder="1234 5678 9012 3456"
  maxlength="19"
/>

<!-- Auto-format with spaces -->
<!-- Detect card type from number -->
<!-- Show card icon -->
```

### Addresses

```html
<input
  type="text"
  autocomplete="address-line1"
  placeholder="Street address"
/>

<!-- Consider: -->
<!-- - Address autocomplete (Google Places) -->
<!-- - Country-specific formats -->
<!-- - Postal code lookup -->
```

### Date Selection

```html
<!-- Native date picker -->
<input type="date" />

<!-- Or custom for better UX -->
<input
  type="text"
  placeholder="MM/DD/YYYY"
  inputmode="numeric"
/>

<!-- Consider: -->
<!-- - Relative dates ("Today", "Tomorrow") -->
<!-- - Date range pickers -->
<!-- - Mobile-friendly selectors -->
```

---

## Form Layout

### Single Column

```
┌─────────────────────────────┐
│ First Name                  │
├─────────────────────────────┤
│ Last Name                   │
├─────────────────────────────┤
│ Email                       │
├─────────────────────────────┤
│ [Submit]                    │
└─────────────────────────────┘

Best for: Mobile, most web forms
```

### Multi-Column (Use Sparingly)

```
┌──────────────┬──────────────┐
│ First Name   │ Last Name    │
├──────────────┴──────────────┤
│ Email                       │
├──────────────┬──────────────┤
│ City         │ State │ Zip  │
└──────────────┴──────────────┘

Use for: Related short fields
Avoid: Different topics side by side
```

### Grouping

```html
<fieldset>
  <legend>Shipping Address</legend>
  <!-- Address fields -->
</fieldset>

<fieldset>
  <legend>Billing Address</legend>
  <!-- Address fields -->
</fieldset>
```

---

## Submit Buttons

### Button Labels

```html
<!-- Specific, action-oriented -->
<button type="submit">Create Account</button>
<button type="submit">Place Order</button>
<button type="submit">Send Message</button>

<!-- Avoid generic -->
<button type="submit">Submit</button>
```

### Button States

```html
<button type="submit" disabled>
  <!-- Before form is valid -->
  Create Account
</button>

<button type="submit" class="loading">
  <span class="spinner" aria-hidden="true"></span>
  <span>Creating Account...</span>
</button>
```

### Button Placement

- Primary action on the right (or full-width on mobile)
- Cancel/back on the left
- Don't hide the submit button
- Ensure visible without scrolling

---

## Accessibility Checklist

- [ ] Labels properly associated with inputs
- [ ] Error messages linked with `aria-describedby`
- [ ] Required fields marked with `aria-required`
- [ ] Invalid fields marked with `aria-invalid`
- [ ] Errors announced with `role="alert"`
- [ ] Keyboard navigation works correctly
- [ ] Focus management on errors
- [ ] Sufficient color contrast
- [ ] Touch targets at least 44×44px

---

## Sources

- [Nielsen Norman Group - Form Design](https://www.nngroup.com/articles/web-form-design/)
- [Baymard Institute - Form Usability](https://baymard.com/blog/current-state-of-checkout-ux)
- [Luke Wroblewski - Web Form Design](https://www.lukew.com/resources/web_form_design.asp)
- [GOV.UK Design System - Forms](https://design-system.service.gov.uk/patterns/)
