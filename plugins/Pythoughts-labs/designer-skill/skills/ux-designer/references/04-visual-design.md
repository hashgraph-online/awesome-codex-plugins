# Visual Design

Visual design encompasses color theory, typography, layout, and the principles that make interfaces aesthetically pleasing and functional.

---

## Color Theory

### Color Psychology

Colors evoke specific emotions and influence user behavior.

| Color | Associations | Common Uses |
|-------|--------------|-------------|
| **Red** | Energy, urgency, passion, danger | Errors, sales, CTAs |
| **Orange** | Enthusiasm, creativity, warmth | Notifications, CTAs |
| **Yellow** | Optimism, warning, attention | Warnings, highlights |
| **Green** | Growth, success, nature, calm | Success states, eco themes |
| **Blue** | Trust, stability, professionalism | Corporate, tech, links |
| **Purple** | Luxury, creativity, mystery | Premium products |
| **Pink** | Playful, romantic, youthful | Fashion, lifestyle |
| **Black** | Sophistication, power, elegance | Luxury, fashion |
| **White** | Purity, simplicity, cleanliness | Minimalist designs |
| **Gray** | Neutral, professional, balanced | Backgrounds, borders |

### The 60-30-10 Rule

A balanced color palette distribution:

```
60% - Dominant color (backgrounds, large areas)
30% - Secondary color (supporting elements)
10% - Accent color (CTAs, highlights)
```

**Example:**
```css
:root {
  --color-dominant: #ffffff;    /* 60% - Background */
  --color-secondary: #f5f5f5;   /* 30% - Cards, sections */
  --color-accent: #0066cc;      /* 10% - Buttons, links */
}
```

### Color Harmonies

| Harmony | Description | Use Case |
|---------|-------------|----------|
| **Monochromatic** | Shades of one hue | Clean, cohesive |
| **Complementary** | Opposite on color wheel | High contrast, vibrant |
| **Analogous** | Adjacent on wheel | Harmonious, natural |
| **Triadic** | Three equidistant colors | Balanced, dynamic |
| **Split-complementary** | Base + two adjacent to complement | Vibrant but balanced |

### Contrast for Accessibility

```css
/* WCAG 2.2 Requirements */

/* Normal text (< 18pt) */
/* Minimum contrast: 4.5:1 (AA), 7:1 (AAA) */

/* Large text (≥ 18pt or 14pt bold) */
/* Minimum contrast: 3:1 (AA), 4.5:1 (AAA) */

/* UI Components */
/* Minimum contrast: 3:1 */
```

### Colorblind-Safe Design

~8% of men and ~0.5% of women have color vision deficiency.

```
Best Practices:
- Don't use color alone to convey meaning
- Add icons, patterns, or text labels
- Test with colorblind simulation tools
- Use sufficient contrast between colors
- Avoid red/green combinations for critical info
```

### Dark Mode Considerations

```css
/* Use CSS custom properties for theming */
:root {
  --bg-primary: #ffffff;
  --text-primary: #1a1a1a;
  --accent: #0066cc;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1a1a;
    --text-primary: #f5f5f5;
    --accent: #66b3ff;
  }
}

/* Reduce contrast slightly in dark mode */
/* Pure white (#fff) on black (#000) can cause eye strain */
```

---

## Typography

### Font Selection

**Categories:**
- **Sans-serif:** Clean, modern, screen-friendly (Roboto, Inter, SF Pro)
- **Serif:** Traditional, authoritative, editorial (Georgia, Merriweather)
- **Monospace:** Technical, code, data (Fira Code, JetBrains Mono)

**Guidelines:**
- Limit to 2-3 typefaces maximum
- Use web-safe fonts or system fonts for performance
- Consider font loading strategy (FOUT, FOIT)

```css
/* System font stack for performance */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
             Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
```

### Size Scale

```css
/* Type scale with 1.25 ratio (Major Third) */
:root {
  --text-xs: 0.75rem;   /* 12px - Captions */
  --text-sm: 0.875rem;  /* 14px - Small text */
  --text-base: 1rem;    /* 16px - Body (minimum) */
  --text-lg: 1.25rem;   /* 20px - Large body */
  --text-xl: 1.5rem;    /* 24px - H3 */
  --text-2xl: 2rem;     /* 32px - H2 */
  --text-3xl: 2.5rem;   /* 40px - H1 */
  --text-4xl: 3rem;     /* 48px - Display */
}
```

**Minimum sizes:**
- Body text: 16px
- Mobile body: 16px (prevents zoom on iOS)
- Small text: 12px (use sparingly)

### Line Height

```css
/* Optimal line heights */
body {
  line-height: 1.5; /* 1.4-1.6 for body text */
}

h1, h2, h3 {
  line-height: 1.2; /* Tighter for headings */
}

.compact {
  line-height: 1.3; /* UI elements, buttons */
}
```

### Line Length

Optimal reading: **50-75 characters per line**

```css
/* Constrain line length */
.prose {
  max-width: 65ch; /* ~65 characters */
}

/* Alternatively */
.content {
  max-width: 700px;
  padding: 0 1rem;
}
```

### Text Alignment

```
Left-aligned (default):
- Best for readability
- Consistent starting point
- Recommended for body text

Center-aligned:
- Short text only (headlines, CTAs)
- Creates visual anchor

Right-aligned:
- Numbers in tables
- RTL languages
- Avoid for body text

Justified:
- Creates uneven word spacing
- Avoid for web (no hyphenation)
- WCAG discourages for accessibility
```

### Fluid Typography

```css
/* Responsive font sizes with clamp() */
h1 {
  font-size: clamp(2rem, 5vw + 1rem, 4rem);
}

body {
  font-size: clamp(1rem, 2.5vw, 1.25rem);
}
```

---

## Visual Hierarchy

### Establishing Hierarchy

1. **Size** - Larger = more important
2. **Weight** - Bolder = more important
3. **Color** - Contrast draws attention
4. **Position** - Top/left (LTR) = primary
5. **Space** - Isolation = emphasis
6. **Depth** - Shadows, layers

### Heading Hierarchy

```html
<!-- Single H1 per page -->
<h1>Page Title</h1>
  <h2>Section</h2>
    <h3>Subsection</h3>
      <h4>Detail</h4>
  <h2>Another Section</h2>
```

### Visual Weight

```css
/* Primary action - highest weight */
.btn-primary {
  background: var(--accent);
  color: white;
  font-weight: 600;
}

/* Secondary action - medium weight */
.btn-secondary {
  background: transparent;
  border: 2px solid var(--accent);
  color: var(--accent);
}

/* Tertiary action - lowest weight */
.btn-tertiary {
  background: transparent;
  color: var(--accent);
  text-decoration: underline;
}
```

---

## Whitespace and Spacing

### The Role of Whitespace

- **Breathing room** - Reduces visual clutter
- **Grouping** - Related items closer together
- **Focus** - Isolation creates emphasis
- **Readability** - Improves comprehension

### Spacing Scale

```css
/* Consistent spacing scale */
:root {
  --space-xs: 0.25rem;  /* 4px */
  --space-sm: 0.5rem;   /* 8px */
  --space-md: 1rem;     /* 16px */
  --space-lg: 1.5rem;   /* 24px */
  --space-xl: 2rem;     /* 32px */
  --space-2xl: 3rem;    /* 48px */
  --space-3xl: 4rem;    /* 64px */
}
```

### Applying Spacing

```css
/* Consistent component spacing */
.card {
  padding: var(--space-lg);
  margin-bottom: var(--space-xl);
}

/* Related items closer */
.form-field label {
  margin-bottom: var(--space-xs);
}

/* Distinct sections further */
.section + .section {
  margin-top: var(--space-3xl);
}
```

---

## Layout Principles

### Grid Systems

```css
/* CSS Grid for page layout */
.page {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-lg);
}

/* Flexbox for component layout */
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}
```

### Responsive Breakpoints

```css
/* Mobile-first breakpoints */
/* Base: Mobile (< 640px) */

@media (min-width: 640px) {
  /* Tablet portrait */
}

@media (min-width: 768px) {
  /* Tablet landscape */
}

@media (min-width: 1024px) {
  /* Desktop */
}

@media (min-width: 1280px) {
  /* Large desktop */
}
```

### Content Alignment

```css
/* Center content with max-width */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}
```

---

## 2026 Trends

### AI-Adaptive Interfaces
- Colors and layouts that adjust based on user behavior
- Personalized visual preferences
- Context-aware theming

### Warm, Soft Colors
- Moving away from stark whites
- Beige, pale pink, peach tones
- Psychologically inviting

### Fluid Design
- Dynamic, responsive everything
- Container queries
- Fluid spacing and typography

### Glassmorphism (Continued)
- Frosted glass effects
- Subtle transparency
- Depth through blur

---

## Tools and Resources

### Color
- [Coolors](https://coolors.co/) - Palette generator
- [Adobe Color](https://color.adobe.com/) - Color wheel
- [Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Typography
- [Type Scale](https://type-scale.com/) - Visual calculator
- [Fontpair](https://fontpair.co/) - Font combinations
- [Google Fonts](https://fonts.google.com/)

### Design Systems
- [Tailwind UI](https://tailwindui.com/)
- [Material Design](https://m3.material.io/)
- [Apple HIG](https://developer.apple.com/design/)

---

## Sources

- [Smashing Magazine - Color Psychology](https://www.smashingmagazine.com/)
- [Interaction Design Foundation - Typography](https://www.interaction-design.org/)
- [Practical Typography](https://practicaltypography.com/)
- [Refactoring UI](https://www.refactoringui.com/)
