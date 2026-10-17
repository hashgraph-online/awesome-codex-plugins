# Interaction Design

Interaction design (IxD) focuses on creating engaging interfaces with well-thought-out behaviors—how the system responds to user actions.

---

## Micro-interactions

Small, contained moments that accomplish a single task while enhancing the user experience.

### Dan Saffer's Four Components

#### 1. Trigger
What initiates the micro-interaction.

**User Triggers:**
- Click/tap
- Swipe
- Hover
- Scroll
- Voice command
- Keyboard input

**System Triggers:**
- Time-based (notification)
- Location-based
- Data changes
- Error conditions

#### 2. Rules
What happens once triggered.

```
Example: Like button
1. User taps heart icon
2. Icon changes to filled state
3. Color changes to red
4. Counter increments
5. Animation plays
6. Haptic feedback (mobile)
7. Data sent to server
```

#### 3. Feedback
How the system communicates what's happening.

**Visual:** Color, shape, position changes
**Auditory:** Sounds, voice
**Haptic:** Vibration, force feedback
**Motion:** Animation

#### 4. Loops and Modes
How the interaction changes over time or in different states.

```
Loops:
- First use vs. repeated use
- Decay over time
- Escalation

Modes:
- Light/dark mode
- Editing mode
- Offline mode
```

---

## Feedback States

### Button States

```css
/* Default state */
.button {
  background: #0066cc;
  color: white;
}

/* Hover state (desktop) */
.button:hover {
  background: #0052a3;
}

/* Focus state (keyboard navigation) */
.button:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* Active/pressed state */
.button:active {
  background: #004080;
  transform: scale(0.98);
}

/* Disabled state */
.button:disabled {
  background: #cccccc;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Loading state */
.button.loading {
  pointer-events: none;
  /* Show spinner */
}
```

### Form Field States

```css
/* Default */
.input { border: 1px solid #ccc; }

/* Focus */
.input:focus { border-color: #0066cc; box-shadow: 0 0 0 3px rgba(0,102,204,0.2); }

/* Valid */
.input:valid { border-color: #28a745; }

/* Invalid */
.input:invalid { border-color: #dc3545; }

/* Disabled */
.input:disabled { background: #f5f5f5; cursor: not-allowed; }
```

### System States

| State | Visual Indicator | User Action |
|-------|-----------------|-------------|
| Loading | Spinner, skeleton, progress bar | Wait |
| Success | Green check, confirmation message | Continue |
| Error | Red alert, error message | Correct and retry |
| Warning | Yellow/orange alert | Proceed with caution |
| Empty | Illustration, helpful message | Add content |
| Offline | Banner, cached indicator | Limited functionality |

---

## Animation Principles

### Timing

```css
/* Natural feeling durations */
.quick { transition-duration: 100ms; }   /* Hovers, immediate feedback */
.normal { transition-duration: 200ms; }  /* Standard transitions */
.smooth { transition-duration: 300ms; }  /* Panel transitions */
.slow { transition-duration: 500ms; }    /* Large/complex animations */

/* Maximum for focused attention */
.complex { animation-duration: 500ms; }  /* Don't exceed 500ms typically */
```

### Easing Functions

```css
/* Standard easing curves */
.ease-out { transition-timing-function: ease-out; }
/* Fast start, slow end - entering elements */

.ease-in { transition-timing-function: ease-in; }
/* Slow start, fast end - exiting elements */

.ease-in-out { transition-timing-function: ease-in-out; }
/* Smooth start and end - moving elements */

/* Custom bezier curves */
.bounce { transition-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55); }
```

### The 12 Principles of Animation (Disney)

Applied to UI:

1. **Squash and Stretch** - Subtle scaling on press
2. **Anticipation** - Brief pause before action
3. **Staging** - Direct attention to important elements
4. **Straight Ahead/Pose to Pose** - Keyframe animations
5. **Follow Through/Overlapping** - Elements don't stop all at once
6. **Slow In/Slow Out** - Easing functions
7. **Arc** - Natural curved motion paths
8. **Secondary Action** - Supporting animations
9. **Timing** - Speed conveys weight and emotion
10. **Exaggeration** - Subtle emphasis (don't overdo)
11. **Solid Drawing** - 3D consistency
12. **Appeal** - Pleasing, polished animations

---

## Loading States

### Skeleton Screens

```html
<div class="card skeleton">
  <div class="skeleton-image"></div>
  <div class="skeleton-title"></div>
  <div class="skeleton-text"></div>
  <div class="skeleton-text short"></div>
</div>

<style>
.skeleton * {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

### Progress Indicators

```
Determinate (known duration):
┌──────────────────────────────────────┐
│████████████░░░░░░░░░░░░░░░  45%      │
└──────────────────────────────────────┘

Indeterminate (unknown duration):
┌──────────────────────────────────────┐
│    ████████░░░░░░                    │ (moving)
└──────────────────────────────────────┘
```

### Spinner Guidelines

- Show after 300ms delay (avoid flash for fast operations)
- Use on buttons during submission
- Disable interaction during loading
- Provide cancel option for long operations

---

## Gesture Design

### Standard Touch Gestures

| Gesture | Action | Example |
|---------|--------|---------|
| Tap | Select, activate | Button press |
| Double tap | Zoom, like | Photo zoom |
| Long press | Context menu | Delete options |
| Swipe | Navigate, dismiss | Page turn, delete |
| Pinch | Zoom | Map, photo |
| Rotate | Rotate object | Image editing |
| Drag | Move, reorder | List sorting |

### Gesture Best Practices

```
1. Provide visual affordances
   - Swipe indicators
   - Drag handles
   - Touch hints

2. Offer alternatives (WCAG 2.5.7)
   - Buttons for swipe actions
   - Menus for gestures
   - Keyboard equivalents

3. Give feedback
   - Haptic response
   - Visual confirmation
   - Sound (optional)

4. Allow undo
   - Swipe to delete → Undo button
   - Accidental gestures happen
```

---

## Transitions

### Page Transitions

```css
/* Fade transition */
.page-enter {
  opacity: 0;
}
.page-enter-active {
  opacity: 1;
  transition: opacity 200ms ease-out;
}
.page-exit {
  opacity: 1;
}
.page-exit-active {
  opacity: 0;
  transition: opacity 200ms ease-in;
}

/* Slide transition */
.page-enter {
  transform: translateX(100%);
}
.page-enter-active {
  transform: translateX(0);
  transition: transform 300ms ease-out;
}
```

### Modal Transitions

```css
/* Backdrop */
.backdrop {
  opacity: 0;
  transition: opacity 200ms ease;
}
.backdrop.open {
  opacity: 1;
}

/* Modal */
.modal {
  transform: scale(0.95);
  opacity: 0;
  transition: transform 200ms ease, opacity 200ms ease;
}
.modal.open {
  transform: scale(1);
  opacity: 1;
}
```

### Accordion/Collapse

```css
.accordion-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height 300ms ease-out;
}
.accordion-content.open {
  max-height: 500px; /* Use calculated height for best results */
}
```

---

## Reduced Motion

### Respecting User Preferences

```css
/* Check user preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Alternative: provide reduced but not eliminated motion */
@media (prefers-reduced-motion: reduce) {
  .animated {
    animation: none;
    transition: opacity 0.01ms;
  }
}
```

### When to Reduce Motion

- Vestibular disorders
- Motion sickness
- Cognitive load reduction
- Battery/performance concerns

---

## Haptic Feedback

### Mobile Haptics

```javascript
// Web Vibration API
if ('vibrate' in navigator) {
  // Single vibration (ms)
  navigator.vibrate(50);

  // Pattern: vibrate, pause, vibrate
  navigator.vibrate([50, 100, 50]);
}
```

### Haptic Patterns

| Action | Pattern | Feel |
|--------|---------|------|
| Success | Short, light | Confirmation |
| Error | Two quick pulses | Alert |
| Selection | Very short | Tactile |
| Warning | Medium, strong | Attention |

---

## 2026 Trends

### Functional Motion (motion earns its keep)
The dominant 2026 framing: motion should **guide, not flash**. Every animation must
do a job—orient the user, show cause and effect, or maintain spatial continuity—
otherwise it's decoration that adds cognitive load. Reserve flourish for moments
that matter (success, first-run delight); keep everyday transitions calm and quick.

- Use motion to **explain state change** (where did this come from / go to?)
- Use motion to **direct attention** to what just changed
- Use motion to **preserve context** across views (shared-element transitions)
- Cut motion that exists only to look impressive—calm interfaces win in 2026

### Giving Users Control Over Motion
`prefers-reduced-motion` (see [Reduced Motion](#reduced-motion) above) is the
baseline, but it's an OS-level all-or-nothing switch many users never set. Mature
products add an **explicit in-product "Reduce motion" toggle** in settings so users
can dial motion down without touching system preferences.

```
Settings → Accessibility → Motion
  ○ Full motion (default)
  ● Reduced motion   ← respects this even if OS pref is unset
  ○ Off
```

- Default to the OS preference, then let the in-app setting override it
- Persist the choice per user/device; apply it everywhere, not just key screens
- Treat "reduced" as *reduced* (instant fades) not *broken* (no feedback at all)

### AI-Driven Interactions
- Predictive UI that anticipates needs (offered, never forced)
- Personalized micro-interactions
- Adaptive animation complexity tuned to device performance

### Voice + Multimodal
- Multimodal feedback (voice confirms visual action)
- Combining voice, touch, pointer, and keyboard input
- See [24-voice-and-multimodal.md](24-voice-and-multimodal.md) for depth

---

## Common Mistakes

1. **Too much animation** - Distracting, performance issues
2. **Too fast/slow** - Feels broken or sluggish
3. **No feedback** - Users unsure if action worked
4. **Inconsistent timing** - Jarring experience
5. **Ignoring reduced motion** - Accessibility failure
6. **Blocking content** - Loading spinners over everything
7. **No cancel option** - Trapped in loading state
8. **Overusing haptics** - Annoying, drains battery

---

## Sources

- Saffer, D. (2013). "Microinteractions: Designing with Details"
- Material Design Motion Guidelines
- Apple Human Interface Guidelines - Motion
- [UXDesign.cc - Motion Design](https://uxdesign.cc/)
- [CSS Tricks - Animation](https://css-tricks.com/tag/animation/)
