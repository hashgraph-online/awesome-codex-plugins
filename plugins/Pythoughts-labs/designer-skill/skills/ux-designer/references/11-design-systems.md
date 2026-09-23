# Design Systems

A design system is a complete set of standards, documentation, and reusable components intended to manage design at scale.

---

## What is a Design System?

### Definition

A design system is the single source of truth that groups all elements that allow teams to design, realize, and develop a product.

### Components of a Design System

```
Design System
├── Foundations (Design Tokens)
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   ├── Shadows
│   └── Motion
├── Components
│   ├── Buttons
│   ├── Forms
│   ├── Cards
│   ├── Navigation
│   └── ...
├── Patterns
│   ├── Forms
│   ├── Authentication
│   ├── Search
│   └── ...
├── Guidelines
│   ├── Accessibility
│   ├── Content
│   ├── Voice & Tone
│   └── Usage
└── Documentation
    ├── Getting Started
    ├── Component APIs
    └── Contributing
```

---

## Design System vs. Related Concepts

### Style Guide

Focus on **visual elements**:
- Brand colors
- Typography
- Logo usage
- Imagery guidelines

### Pattern Library

Collection of **UI patterns**:
- Navigation patterns
- Form patterns
- Layout templates
- Interaction patterns

### Component Library

**Coded UI components**:
- Buttons, inputs, modals
- Ready-to-use code
- Framework-specific
- Documented APIs

### Design System

**All of the above, plus:**
- Governance processes
- Contribution guidelines
- Versioning
- Team workflows

---

## Design Tokens

Design tokens are the atomic values that define visual design decisions.

### Tokens as the Universal Language

By 2026 the leading framing is that design tokens are not just a theming
convenience—they are the **infrastructure layer** that makes consistency possible
across an expanding surface of platforms and modalities (web, iOS, Android, watch,
TV, voice, in-car, AR). A token is a named, platform-agnostic decision (e.g.
`color.action.primary`, `space.4`) that a build step (Style Dictionary, Tokens
Studio) compiles into CSS custom properties, Swift, Kotlin, JSON, etc.

```
Single source of truth (tokens.json)
        │  transform / build
        ├──► CSS  --color-action-primary
        ├──► iOS  Color.actionPrimary
        ├──► Android  colorActionPrimary
        └──► docs / Figma variables
```

- **One decision, many outputs** — change a token, every platform updates in sync
- **Tiered structure** — primitive (raw values) → semantic (intent) → component
- **Theming falls out for free** — light/dark, brand, density, high-contrast are
  just alternate token sets resolved at the semantic layer
- Tokens are the contract between design and engineering; treat them as versioned API

### Token Types

```css
/* Color tokens */
--color-primary: #0066cc;
--color-primary-light: #3399ff;
--color-primary-dark: #004499;
--color-background: #ffffff;
--color-text-primary: #1a1a1a;
--color-text-secondary: #666666;
--color-error: #dc3545;
--color-success: #28a745;

/* Typography tokens */
--font-family-base: 'Inter', sans-serif;
--font-family-mono: 'JetBrains Mono', monospace;
--font-size-xs: 0.75rem;
--font-size-sm: 0.875rem;
--font-size-base: 1rem;
--font-size-lg: 1.25rem;
--font-size-xl: 1.5rem;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-bold: 700;
--line-height-tight: 1.25;
--line-height-normal: 1.5;

/* Spacing tokens */
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.5rem;   /* 24px */
--space-6: 2rem;     /* 32px */
--space-8: 3rem;     /* 48px */

/* Shadow tokens */
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

/* Border radius tokens */
--radius-sm: 0.25rem;
--radius-md: 0.5rem;
--radius-lg: 1rem;
--radius-full: 9999px;

/* Animation tokens */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 400ms;
--easing-default: ease-out;
```

### Semantic Tokens

```css
/* Semantic layer on top of primitive tokens */
--color-action-primary: var(--color-primary);
--color-action-secondary: var(--color-secondary);
--color-feedback-error: var(--color-error);
--color-feedback-success: var(--color-success);
--color-surface: var(--color-background);
--color-surface-raised: var(--color-white);

/* Component-specific tokens */
--button-padding: var(--space-3) var(--space-5);
--button-radius: var(--radius-md);
--card-padding: var(--space-5);
--card-radius: var(--radius-lg);
```

### Variable Fonts

A **variable font** packs an entire type family—every weight, width, and optical
size—into a single file along continuous axes, replacing the old "load 6 static
weight files" approach. This is now the default recommendation for design systems.

```css
@font-face {
  font-family: 'InterVar';
  src: url('/fonts/Inter.var.woff2') format('woff2-variations');
  font-weight: 100 900;          /* full weight range in one file */
  font-display: swap;
}

:root {
  --font-family-base: 'InterVar', sans-serif;
}

/* Use any weight on the axis, not just preset steps */
.heading { font-weight: 620; }
/* Optical sizing axis tracks the rendered size automatically */
body { font-optical-sizing: auto; }
```

**Why it matters:**
- **Performance** — one HTTP request and ~one file instead of many static weights
- **Responsive typography** — interpolate weight/width fluidly across breakpoints
  and even animate them (respecting reduced-motion); great for fluid `clamp()` scales
- **Design flexibility** — fine-grained control (e.g. weight 540) without new files
- Expose axes as tokens (`--font-weight-*`) so the system stays the single source
- Caveat: subset to needed glyphs/axes; a full variable font can be large

---

## Component Architecture

### Anatomy of a Component

```
Button Component
├── States
│   ├── Default
│   ├── Hover
│   ├── Active/Pressed
│   ├── Focus
│   ├── Disabled
│   └── Loading
├── Variants
│   ├── Primary
│   ├── Secondary
│   ├── Tertiary/Ghost
│   └── Destructive
├── Sizes
│   ├── Small
│   ├── Medium (default)
│   └── Large
├── Props/Options
│   ├── Label
│   ├── Icon (left/right)
│   ├── Full width
│   └── Type (button/submit)
└── Accessibility
    ├── Keyboard navigation
    ├── ARIA attributes
    └── Focus management
```

### Component API Design

```tsx
// Well-designed component API
interface ButtonProps {
  /** Button label */
  children: React.ReactNode;
  /** Visual style variant */
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Disabled state */
  disabled?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Full width */
  fullWidth?: boolean;
  /** Icon before label */
  iconLeft?: React.ReactNode;
  /** Icon after label */
  iconRight?: React.ReactNode;
  /** Click handler */
  onClick?: () => void;
}

// Usage
<Button variant="primary" size="lg" iconLeft={<PlusIcon />}>
  Add Item
</Button>
```

---

## Documentation Best Practices

### Component Documentation

Each component should include:

1. **Overview**
   - Description and purpose
   - When to use / when not to use

2. **Examples**
   - Interactive playground
   - Common use cases
   - Edge cases

3. **API Reference**
   - Props/parameters
   - Types
   - Default values

4. **Design Guidelines**
   - Visual specifications
   - Do's and don'ts
   - Spacing and layout

5. **Accessibility**
   - Keyboard interactions
   - Screen reader behavior
   - ARIA requirements

6. **Related Components**
   - Similar components
   - Composability patterns

### Documentation Tools

- **Storybook** - Component documentation and playground
- **Docusaurus** - Documentation websites
- **Zeroheight** - Design system documentation
- **Notion** - Lightweight documentation
- **Supernova** - Design token management

---

## Notable Design Systems

### IBM Carbon Design System

```
Open source, comprehensive
- React, Vue, Angular, Web Components
- Detailed accessibility guidelines
- Strong data visualization components
- Enterprise-focused

https://carbondesignsystem.com/
```

### Atlassian Design System

```
Product design focus
- Detailed component documentation
- Design tokens approach
- Accessibility built-in
- Confluence, Jira, Trello patterns

https://atlassian.design/
```

### Salesforce Lightning

```
Enterprise-grade
- Extensive component library
- Accessibility focused
- Mobile-responsive
- Customizable themes

https://www.lightningdesignsystem.com/
```

### Material Design (Google)

```
Platform-agnostic design language
- Comprehensive guidelines
- Motion and animation specs
- Cross-platform support
- Open-source implementations

https://m3.material.io/
```

### Apple Human Interface Guidelines

```
Platform-specific guidance
- iOS, macOS, watchOS, tvOS
- System component integration
- Platform conventions
- Design resources (Figma, Sketch)

https://developer.apple.com/design/
```

---

## React Component Libraries (2026)

### Untitled UI React

```
- 10,000+ Figma components
- Tailwind CSS v4.1
- React Aria for accessibility
- TypeScript v5.8
- Most comprehensive free library
```

### React Aria Components (Adobe)

```
- Unstyled, accessible
- ARIA patterns built-in
- Internationalization
- Keyboard navigation
- Foundation for custom systems
```

### Radix UI

```
- Unstyled primitives
- Accessibility focused
- Composable
- Foundation for shadcn/ui
```

### shadcn/ui

```
- Copy-paste components
- Tailwind + Radix
- Full customization
- Popular for rapid prototyping
```

### Chakra UI

```
- Styled components
- Dark mode built-in
- Accessible
- Good DX
```

---

## Governance & Contribution

### Versioning

```
Semantic versioning (SemVer):
MAJOR.MINOR.PATCH

MAJOR - Breaking changes
MINOR - New features (backward compatible)
PATCH - Bug fixes

Example: 2.3.1
- Version 2 (breaking changes from v1)
- 3 new feature additions
- 1 bug fix since last minor
```

### Change Log

```markdown
## [2.3.0] - 2025-01-15

### Added
- New `Select` component
- Dark mode support for `Card`

### Changed
- Updated Button padding tokens

### Fixed
- Modal focus trap on Safari

### Deprecated
- Legacy Grid component (use CSS Grid)
```

### Contribution Model

```
Federated Model:
- Central team maintains core
- Product teams can contribute
- Review and approval process
- Clear contribution guidelines

Centralized Model:
- Dedicated DS team owns everything
- Product teams request features
- Slower but more consistent

Hybrid:
- Core components centralized
- Extensions/themes distributed
```

---

## Building a Design System

### Phases

```
Phase 1: Audit
- Inventory existing UI
- Identify inconsistencies
- Prioritize components
- Define scope

Phase 2: Foundation
- Design tokens
- Core components (button, input)
- Basic documentation
- Initial adoption

Phase 3: Expansion
- More components
- Patterns and templates
- Contribution guidelines
- Advanced documentation

Phase 4: Maturity
- Full component library
- Governance processes
- Automated testing
- Continuous improvement
```

### Success Metrics

```
Adoption:
- % of products using the system
- Component usage analytics
- Developer satisfaction

Quality:
- Accessibility audit scores
- Bug/issue counts
- Design consistency reviews

Efficiency:
- Time to build new features
- Reduced design/dev sync issues
- Code reuse metrics
```

---

## Common Pitfalls

1. **Building too much upfront** - Start small, iterate
2. **No governance** - Define ownership and processes
3. **Designer-dev disconnect** - Single source of truth
4. **Outdated documentation** - Automate where possible
5. **No adoption strategy** - Train teams, provide support
6. **Ignoring accessibility** - Build in from the start
7. **Over-engineering** - Solve current problems first
8. **No versioning** - Breaking changes break trust
9. **Component bloat** - Audit and deprecate regularly
10. **Premature abstraction** - Wait for patterns to emerge

---

## Tools Ecosystem

### Design

| Tool | Purpose |
|------|---------|
| Figma | Design and prototyping |
| Figma Tokens | Token management |
| Storybook | Component development |

### Development

| Tool | Purpose |
|------|---------|
| Style Dictionary | Token transformation |
| Chromatic | Visual testing |
| Playwright/Testing Library | Component testing |

### Documentation

| Tool | Purpose |
|------|---------|
| Storybook | Component docs |
| Supernova | DS documentation |
| Docusaurus | Website docs |

---

## Sources

- [Nielsen Norman - Design Systems 101](https://www.nngroup.com/articles/design-systems-101/)
- [Atlassian Design System](https://atlassian.design/)
- [Carbon Design System](https://carbondesignsystem.com/)
- Nathan Curtis - [EightShapes](https://eightshapes.com/)
- Brad Frost - [Atomic Design](https://atomicdesign.bradfrost.com/)
- [Design Systems Repo](https://designsystemsrepo.com/)
