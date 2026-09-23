# Accessibility & WCAG 2.2

Accessibility ensures digital products are usable by people with disabilities. Beyond ethics and inclusion, it's increasingly a legal requirement.

---

## WCAG 2.2 Overview

**Web Content Accessibility Guidelines 2.2** is the latest W3C recommendation (October 2023, updated December 2024), now also an ISO standard (ISO/IEC 40500:2025).

### Conformance Levels

| Level | Description | Requirement |
|-------|-------------|-------------|
| **A** | Minimum accessibility | Essential barriers removed |
| **AA** | Recommended standard | Most common target for compliance |
| **AAA** | Highest accessibility | Maximum inclusion (not always feasible) |

### Four Principles (POUR)

1. **Perceivable** - Information must be presentable in ways users can perceive
2. **Operable** - Interface components must be operable
3. **Understandable** - Information and operation must be understandable
4. **Robust** - Content must be robust enough for various assistive technologies

---

## New Success Criteria in WCAG 2.2

### Focus Not Obscured (Minimum) - 2.4.11 (AA)
When an element receives keyboard focus, it is not entirely hidden by other content.

```css
/* Ensure focused elements aren't covered */
.modal {
  /* Don't cover the element that triggered focus */
}

/* Sticky headers should not cover focused content */
.sticky-header {
  /* Account for header height in scroll calculations */
}
```

### Focus Not Obscured (Enhanced) - 2.4.12 (AAA)
When focused, no part of the element is hidden by author-created content.

### Focus Appearance - 2.4.13 (AAA)
Focus indicators must have sufficient size and contrast.

### Dragging Movements - 2.5.7 (AA)
Functionality using dragging can be operated with a single pointer without dragging.

```html
<!-- Provide alternative to drag-and-drop -->
<div draggable="true">Item</div>
<button>Move Up</button>
<button>Move Down</button>
```

### Target Size (Minimum) - 2.5.8 (AA)
Touch targets must be at least 24×24 CSS pixels, with exceptions for inline links, user agent controls, and essential presentations.

### Accessible Authentication (Minimum) - 3.3.8 (AA)
Authentication processes don't require cognitive function tests (like remembering passwords) unless alternatives are provided.

```
Compliant methods:
- Password managers (paste allowed)
- Email/SMS verification codes
- Biometric authentication
- OAuth/social login
```

### Accessible Authentication (Enhanced) - 3.3.9 (AAA)
No cognitive test required at all for authentication.

### Redundant Entry - 3.3.7 (A)
Don't require users to re-enter information already provided in the same session.

---

## Color and Contrast

### Contrast Requirements

| Content Type | Minimum Ratio (AA) | Enhanced (AAA) |
|--------------|-------------------|----------------|
| Normal text (< 18pt) | 4.5:1 | 7:1 |
| Large text (≥ 18pt or 14pt bold) | 3:1 | 4.5:1 |
| UI components & graphics | 3:1 | - |
| Focus indicators | 3:1 | - |

### Testing Contrast
```javascript
// Calculate contrast ratio
function getContrastRatio(l1, l2) {
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}
```

**Tools:**
- WebAIM Contrast Checker
- Stark (Figma plugin)
- Chrome DevTools accessibility panel
- axe DevTools

### Color Blindness
Approximately 8% of men and 0.5% of women have some form of color vision deficiency.

```
Never rely on color alone to convey:
- Error states (add icons, text)
- Success/failure (add icons, patterns)
- Required fields (add asterisks)
- Link differentiation (add underline)
- Data visualization (add patterns, labels)
```

---

## Keyboard Navigation

### Requirements
All functionality must be accessible via keyboard.

```html
<!-- Ensure logical tab order -->
<nav>
  <a href="/">Home</a>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
</nav>

<!-- Use tabindex appropriately -->
<div tabindex="0" role="button">Custom Button</div>
<div tabindex="-1">Programmatically focusable only</div>
<!-- Never use tabindex > 0 -->
```

### Focus Management
```css
/* Never hide focus outlines without replacement */
:focus {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* For mouse users who don't need visible focus */
:focus:not(:focus-visible) {
  outline: none;
}

:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}
```

### Keyboard Shortcuts
```
Standard expectations:
- Tab: Move to next focusable element
- Shift+Tab: Move to previous element
- Enter/Space: Activate buttons
- Arrow keys: Navigate within widgets
- Escape: Close modals/popups
```

---

## Screen Reader Compatibility

### Semantic HTML
```html
<!-- Use semantic elements -->
<header>...</header>
<nav>...</nav>
<main>...</main>
<article>...</article>
<aside>...</aside>
<footer>...</footer>

<!-- Not divs with roles -->
<div role="navigation">...</div> <!-- Less ideal -->
```

### ARIA (Accessible Rich Internet Applications)
```html
<!-- Labels -->
<button aria-label="Close dialog">×</button>

<!-- Descriptions -->
<input aria-describedby="password-hint" />
<p id="password-hint">Must be at least 8 characters</p>

<!-- States -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" aria-hidden="true">...</ul>

<!-- Live regions for dynamic content -->
<div aria-live="polite" aria-atomic="true">
  <!-- Updates announced to screen readers -->
</div>
```

### Image Accessibility
```html
<!-- Informative images -->
<img src="chart.png" alt="Sales increased 20% in Q4 2024" />

<!-- Decorative images -->
<img src="divider.png" alt="" role="presentation" />

<!-- Complex images -->
<figure>
  <img src="diagram.png" alt="System architecture diagram" />
  <figcaption>
    Full description of the system architecture...
  </figcaption>
</figure>
```

---

## Forms Accessibility

```html
<form>
  <!-- Always associate labels -->
  <label for="email">Email address</label>
  <input type="email" id="email" name="email"
         aria-required="true"
         aria-describedby="email-error" />
  <span id="email-error" role="alert">
    Please enter a valid email address
  </span>

  <!-- Group related fields -->
  <fieldset>
    <legend>Shipping Address</legend>
    <!-- Address fields -->
  </fieldset>

  <!-- Required field indication -->
  <label for="name">
    Name <span aria-hidden="true">*</span>
    <span class="sr-only">(required)</span>
  </label>
</form>
```

### Error Handling
```html
<!-- Announce errors -->
<div role="alert" aria-live="assertive">
  Please correct the following errors:
  <ul>
    <li><a href="#email">Email is required</a></li>
  </ul>
</div>
```

---

## Motion and Animation

### Respecting User Preferences
```css
/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Or provide opt-out */
.animation {
  animation: slide-in 0.3s ease;
}

@media (prefers-reduced-motion: reduce) {
  .animation {
    animation: none;
  }
}
```

### Auto-Playing Content
- Never auto-play video with sound
- Provide pause/stop controls for any auto-playing content
- Avoid flashing content (> 3 flashes per second can trigger seizures)

---

## Touch Accessibility

### Target Sizes (WCAG 2.2)
```css
/* Minimum 24×24px for WCAG 2.2 AA */
/* Recommended 44×44px for comfortable tapping */
.button {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 24px;
}

/* Adequate spacing between targets */
.button + .button {
  margin-left: 8px;
}
```

### Touch Alternatives
```html
<!-- Provide alternatives to complex gestures -->
<div class="carousel">
  <button aria-label="Previous slide">←</button>
  <!-- Content (also swipeable) -->
  <button aria-label="Next slide">→</button>
</div>
```

---

## Legal Requirements

Accessibility is now a hard legal obligation in major markets, not just a best
practice. The headline change is the European Accessibility Act.

### European Accessibility Act (EAA)
- **In force since:** June 28, 2025 — enforcement is active now
- **Applies to:** A broad set of digital products and services sold in the EU —
  e-commerce, banking, e-books, ticketing, transport, electronic communications,
  and consumer hardware/OS. **Reach is extraterritorial:** non-EU businesses
  (incl. US/UK companies) that sell to EU customers must comply.
- **Technical baseline:** **EN 301 549**, the harmonized EU standard, which
  references **WCAG 2.1 Level AA** as its web/app floor (and adds requirements
  beyond WCAG, e.g. for hardware and documentation).
- **Transition end:** June 28, 2030 — a limited grace window for certain
  pre-existing service contracts and self-service terminals already in use.
- **Practical takeaway:** Targeting **WCAG 2.2 AA** (covered above) meets and
  exceeds the EAA's WCAG 2.1 AA floor, so a WCAG 2.2 AA product is well-positioned
  for compliance. Verify the EN 301 549 non-web clauses if you ship hardware,
  documents, or support channels.

### Other Regulations
- **US:** ADA (case law increasingly treats websites as places of public
  accommodation), Section 508 (federal procurement, aligned to WCAG 2.0 AA)
- **EU:** Web Accessibility Directive (public-sector sites/apps, EN 301 549)
- **UK:** Equality Act 2010
- **Canada:** AODA, ACA
- **Australia:** DDA

---

## Testing Checklist

### Automated Testing
- [ ] axe DevTools
- [ ] WAVE
- [ ] Lighthouse
- [ ] Pa11y

### Manual Testing
- [ ] Keyboard-only navigation
- [ ] Screen reader testing (NVDA, VoiceOver, JAWS)
- [ ] 200% zoom level
- [ ] High contrast mode
- [ ] Reduced motion preference

### User Testing
- [ ] Include users with disabilities
- [ ] Test with assistive technologies
- [ ] Gather feedback on pain points

---

## Sources

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)
- [European Accessibility Act](https://ec.europa.eu/social/main.jsp?catId=1202) - EU directive 2019/882
- [EN 301 549](https://www.etsi.org/standards) - Harmonized EU accessibility standard
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)
- [Deque University](https://dequeuniversity.com/)
