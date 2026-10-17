# Latency thresholds and feedback-state patterns

A reference complementing `feedback-loop-states-and-latency` with the empirical research and pattern catalog.

## Latency-threshold research timeline

- **Miller (1968)** "Response time in man-computer conversational transactions" — first systematic study of computer response times. Established the < 100ms / < 1s / < 10s thresholds.
- **Doherty & Thadani (1982)** "The Economic Value of Rapid Response Time" (IBM) — refined the threshold to ~400ms; demonstrated productivity correlations.
- **Card, Robertson, Mackinlay (1991)** *The Information Visualizer* — formalized thresholds for the modern HCI canon.
- **Nielsen (1993)** *Usability Engineering* — popularized the thresholds for web design.
- **Google (2020+)** Core Web Vitals — operationalized the thresholds as web performance metrics (LCP, INP, CLS).

The numbers vary slightly across studies, but the shape is consistent: under 100ms feels instant, under 1s feels responsive, under 10s keeps attention, beyond 10s requires explicit progress information.

## Modern web-performance budgets

Google's Core Web Vitals targets (passing):

- **Largest Contentful Paint (LCP)**: < 2.5s. The largest visible content rendering time.
- **Interaction to Next Paint (INP)**: < 200ms. Responsiveness to user input.
- **Cumulative Layout Shift (CLS)**: < 0.1. Visual stability — feedback shouldn't cause jumps.

Hitting these correlates with measurably better user engagement and SEO ranking.

## State-pattern catalog

### Buttons and triggers

```
Idle:     normal styling, cursor pointer
Hover:    background shift, subtle elevation
Focus:    visible focus ring
Pending:  disabled, spinner or label change
Success:  brief check icon or color flash, return to idle
Error:    error styling near the button, optional icon
Disabled: lower opacity, cursor not-allowed
```

### Form fields

```
Idle:     normal styling
Focus:    border color change, focus ring
Validating: subtle indicator (spinner in field corner)
Valid:    optional success indicator (check)
Invalid:  red border + aria-invalid + inline error message
Disabled: lower opacity, cursor not-allowed
Read-only: muted background, no focus outline activation
```

### Navigation links

```
Idle:     normal styling
Hover:    underline or color shift
Focus:    visible focus ring
Active:   current-page highlight (aria-current="page")
Visited:  optional muted color (mostly for content links)
```

### Async operations (data fetches)

```
Initial:  skeleton placeholder
Loading:  spinner or shimmer animation
Success:  content fills in, optionally with a brief fade-in
Empty:    designed empty state, not blank screen
Error:    error message + retry button
Stale:    indicator that data may be outdated
```

## Optimistic UI patterns

Optimistic UI updates the interface as if the action succeeded, then commits in the background. Effective for actions where:

- Success rate is high (> 95%).
- The action is reversible.
- Latency would otherwise be perceptible.

```js
async function archive(item) {
  const previous = items.slice();
  items = items.filter(i => i.id !== item.id);
  render();
  try {
    await api.archive(item.id);
  } catch (err) {
    items = previous;
    render();
    showToast(`Couldn't archive: ${err.message}`);
  }
}
```

The user gets instant feedback; failures are explicit but rare.

## Skeleton screens

Skeleton screens (Lucas Cobb, 2013) replace spinners for content loading. They show the page's structure with placeholder shapes that fill in as data arrives:

```html
<article class="post post--skeleton">
  <div class="title-skel"></div>
  <div class="meta-skel"></div>
  <div class="body-skel"></div>
</article>

<style>
.post--skeleton .title-skel,
.post--skeleton .meta-skel,
.post--skeleton .body-skel {
  background: linear-gradient(90deg, #eee, #f5f5f5, #eee);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer { to { background-position: -200% 0; } }
</style>
```

Skeletons measurably reduce perceived load time vs. spinners — the page feels alive even before content arrives.

## Anti-patterns

- **Spinners that hide content the user could be reading.** Use skeletons or peripheral indicators.
- **Animations that fight content.** A pulsing badge near a critical number distracts.
- **State changes without visual transitions.** Jarring jumps; users don't notice the change.
- **Inconsistent state styling across the app.** Each surface re-learns the visual language.

## Resources

- **web.dev / Core Web Vitals** documentation.
- **Material Design motion guide** — well-documented state transitions.
- **NN/g articles on response time and feedback patterns**.
