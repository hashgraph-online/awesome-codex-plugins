# Mobile UX Design

Mobile-first design is essential in 2026, with over 60% of web traffic coming from mobile devices.

---

## The Thumb Zone

### Understanding Thumb Reach

Coined by mobile UX expert Steven Hoober, the Thumb Zone defines how users interact with phones using one hand.

```
┌─────────────────────────────┐
│  HARD      │      HARD     │  ← Top corners: Avoid CTAs
│            │               │
├────────────┼───────────────┤
│            │               │
│  STRETCH   │   STRETCH     │  ← Middle: Secondary actions
│            │               │
├────────────┼───────────────┤
│            │               │
│    EASY    │     EASY      │  ← Bottom: Primary actions
│            │               │
└─────────────────────────────┘
```

### Zone Definitions

| Zone | Location | Usage |
|------|----------|-------|
| **Easy** | Bottom center/left | Primary actions, frequent navigation |
| **Stretch** | Middle, far left/right | Secondary actions |
| **Hard** | Top corners | Rarely used actions |

### Modern Device Considerations

- Screen sizes exceed 6.5 inches
- One-handed use dominates
- Bottom navigation 20-30% faster than top
- Foldable devices require flexible layouts

---

## Touch Target Sizes

### Platform Guidelines

| Platform | Minimum Size | Recommended |
|----------|--------------|-------------|
| Apple iOS | 44×44pt | 44-48pt |
| Material Design | 48×48dp | 48dp |
| WCAG 2.2 | 24×24px | 44×44px |

### Implementation

```css
/* Touch-friendly buttons */
.button {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 24px;
}

/* Tap target expansion for small visual elements */
.small-icon {
  position: relative;
  width: 24px;
  height: 24px;
}

.small-icon::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  /* Invisible but tappable */
}

/* Adequate spacing between targets */
.button-group .button + .button {
  margin-left: 8px; /* Minimum 8px */
}
```

### Touch vs. Click Considerations

```css
/* Remove touch delay on mobile */
touch-action: manipulation;

/* Prevent accidental double-tap zoom */
html {
  touch-action: manipulation;
}
```

---

## Mobile Navigation Patterns

### Bottom Navigation Bar

```html
<nav class="bottom-nav" role="navigation">
  <a href="/" class="nav-item active">
    <span class="icon">🏠</span>
    <span class="label">Home</span>
  </a>
  <a href="/search" class="nav-item">
    <span class="icon">🔍</span>
    <span class="label">Search</span>
  </a>
  <a href="/add" class="nav-item">
    <span class="icon">➕</span>
    <span class="label">Add</span>
  </a>
  <a href="/saved" class="nav-item">
    <span class="icon">❤️</span>
    <span class="label">Saved</span>
  </a>
  <a href="/profile" class="nav-item">
    <span class="icon">👤</span>
    <span class="label">Profile</span>
  </a>
</nav>

<style>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  background: white;
  padding: 8px 0;
  padding-bottom: env(safe-area-inset-bottom); /* iPhone notch */
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 64px;
  padding: 8px;
}
</style>
```

**Best Practices:**
- 3-5 items maximum
- Icons with labels (not icons alone)
- Clear active state
- Thumb-reachable position
- Consider safe areas for notched devices

### Hamburger Menu

```html
<button class="menu-toggle" aria-expanded="false" aria-controls="menu">
  <span class="sr-only">Menu</span>
  <span class="hamburger-icon"></span>
</button>

<nav id="menu" class="slide-menu" aria-hidden="true">
  <!-- Menu content -->
</nav>
```

**When to Use:**
- Many navigation items (6+)
- Secondary/utility navigation
- Space-constrained headers

**When to Avoid:**
- Primary navigation (use bottom bar)
- When discoverability is crucial
- E-commerce main categories

### Floating Action Button (FAB)

```css
.fab {
  position: fixed;
  bottom: 80px; /* Above bottom nav */
  right: 16px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent);
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}
```

**Use For:**
- Single primary action (create, compose, add)
- Actions available on every screen
- Thumb-friendly access

---

## Responsive Gestures

### Standard Mobile Gestures

```
Tap         → Select, activate
Double tap  → Zoom, like
Long press  → Context menu, drag start
Swipe       → Navigate, dismiss, reveal actions
Pinch       → Zoom in/out
Pull down   → Refresh
Edge swipe  → Back navigation
```

### Swipe Actions

```html
<!-- Swipe-to-reveal actions -->
<div class="list-item swipeable">
  <div class="content">Item content</div>
  <div class="actions hidden">
    <button class="action-edit">Edit</button>
    <button class="action-delete">Delete</button>
  </div>
</div>

<!-- Always provide alternatives (WCAG 2.5.7) -->
<button class="action-menu">•••</button>
```

### Pull-to-Refresh

```css
.pull-indicator {
  height: 0;
  transition: height 200ms;
  overflow: hidden;
}

.pulling .pull-indicator {
  height: 60px;
}

.refreshing .pull-indicator .spinner {
  animation: spin 1s linear infinite;
}
```

---

## Mobile Forms

### Keyboard Optimization

```html
<!-- Appropriate keyboard types -->
<input type="email" inputmode="email" />
<input type="tel" inputmode="tel" />
<input type="number" inputmode="decimal" />
<input type="text" inputmode="numeric" pattern="[0-9]*" />

<!-- Prevent zoom on focus (iOS) -->
<input type="text" style="font-size: 16px;" />
```

### Form Layout

```css
/* Stack labels above inputs */
.form-field {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}

/* Full-width inputs */
.form-field input {
  width: 100%;
  padding: 12px;
  font-size: 16px; /* Prevent zoom */
}

/* Sticky submit button */
.submit-area {
  position: sticky;
  bottom: 0;
  background: white;
  padding: 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}
```

### Mobile-Specific Patterns

```html
<!-- Date picker alternatives -->
<select name="month">
  <option>January</option>
  <!-- ... -->
</select>

<!-- Stepper for quantities -->
<div class="stepper">
  <button>−</button>
  <input type="number" value="1" />
  <button>+</button>
</div>

<!-- Toggle instead of checkbox -->
<label class="toggle">
  <input type="checkbox" />
  <span class="toggle-slider"></span>
  Enable notifications
</label>
```

---

## Performance on Mobile

### Key Metrics

| Metric | Target | Impact |
|--------|--------|--------|
| First Contentful Paint | < 1.8s | User perceives loading |
| Largest Contentful Paint | < 2.5s | Main content visible |
| Time to Interactive | < 3.8s | Users can interact |
| Cumulative Layout Shift | < 0.1 | Visual stability |

### Mobile Performance Tips

```html
<!-- Lazy load images -->
<img loading="lazy" src="image.jpg" alt="" />

<!-- Preload critical resources -->
<link rel="preload" href="font.woff2" as="font" crossorigin />

<!-- Reduce JavaScript -->
<script defer src="app.js"></script>
```

```css
/* Optimize animations */
.animated {
  transform: translateZ(0);
  will-change: transform;
}

/* Reduce motion for performance/preference */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

---

## Touch Feedback

### Response Time

- **< 100ms** - Perceived as instant
- **100-300ms** - Noticeable but acceptable
- **> 300ms** - Feels sluggish

### Visual Feedback

```css
/* Touch feedback */
.button:active {
  transform: scale(0.98);
  opacity: 0.9;
}

/* Ripple effect (Material) */
.ripple {
  position: relative;
  overflow: hidden;
}

.ripple::after {
  content: '';
  position: absolute;
  background: rgba(255,255,255,0.3);
  border-radius: 50%;
  transform: scale(0);
  animation: ripple 0.6s linear;
}
```

### Haptic Feedback

```javascript
// Simple vibration
if ('vibrate' in navigator) {
  navigator.vibrate(10); // Light tap
}

// Success pattern
navigator.vibrate([10, 50, 10]);

// Error pattern
navigator.vibrate([50, 50, 50]);
```

---

## Safe Areas

### Handling Device Notches

```css
/* iPhone notch and home indicator */
.container {
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-bottom: env(safe-area-inset-bottom);
}

/* Fixed bottom elements */
.bottom-bar {
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}

/* Enable safe area support */
<meta name="viewport" content="viewport-fit=cover" />
```

---

## Orientation and Adaptation

### Responsive Layouts

```css
/* Portrait (default) */
.container {
  flex-direction: column;
}

/* Landscape */
@media (orientation: landscape) {
  .container {
    flex-direction: row;
  }

  /* Hide bottom nav, show sidebar */
  .bottom-nav {
    display: none;
  }

  .sidebar-nav {
    display: block;
  }
}
```

### Foldable Devices

```css
/* Detect foldable screen */
@media (horizontal-viewport-segments: 2) {
  /* Dual-screen layout */
  .main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: env(viewport-segment-width 0 0);
  }
}
```

---

## Common Mobile Mistakes

1. **Touch targets too small** - Use 44px minimum
2. **Important actions at top** - Place in thumb zone
3. **Too much content** - Prioritize ruthlessly
4. **Desktop forms on mobile** - Optimize for touch
5. **Ignoring safe areas** - Content hidden by notches
6. **No offline support** - Users lose connectivity
7. **Heavy animations** - Drains battery, causes jank
8. **Zoom disabled** - Accessibility violation
9. **Horizontal scrolling** - Confusing navigation
10. **Pop-ups covering content** - Interstitials annoy users

---

## Testing Checklist

- [ ] Test on real devices (not just simulators)
- [ ] Check various screen sizes
- [ ] Test in portrait and landscape
- [ ] Verify touch targets are large enough
- [ ] Test with slow network (3G)
- [ ] Check offline behavior
- [ ] Verify safe area handling
- [ ] Test form keyboard interaction
- [ ] Check gesture conflicts
- [ ] Verify haptic feedback works

---

## Sources

- [Material Design - Mobile Guidelines](https://m3.material.io/)
- [Apple HIG - iOS](https://developer.apple.com/design/human-interface-guidelines/)
- [Nielsen Norman - Mobile UX](https://www.nngroup.com/topic/mobile-usability/)
- Hoober, S. (2017). "Touch Bigger"
- [Google Web Fundamentals - Mobile](https://developers.google.com/web/fundamentals)
